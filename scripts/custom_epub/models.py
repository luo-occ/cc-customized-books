from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Pairing:
    english_label: str
    english_href: str
    chinese_label: str | None
    chinese_href: str | None
    status: str


@dataclass(frozen=True)
class OptionalSection:
    title: str
    source: str
    href: str
    action: str
    language: str
    intro: str


@dataclass(frozen=True)
class BookProject:
    project_dir: Path
    repo_root: Path
    slug: str
    title: str
    author: str
    language: str
    description: str
    english_epub: Path
    chinese_epub: Path | None
    output_epub: Path
    pairing_map: Path
    pairings: list[Pairing]
    optional_sections: list[OptionalSection]


@dataclass(frozen=True)
class BookCompanion:
    companion_zh: str
    summary_en: str
    references: list[dict[str, str]]


@dataclass(frozen=True)
class ListeningBrief:
    names: str
    points: list[str]
    context: str


@dataclass(frozen=True)
class ChapterCompanion:
    zh: str
    en: str
    priority: str


@dataclass(frozen=True)
class Recap:
    zh: str
    en: str


@dataclass(frozen=True)
class CompanionChapter:
    english_label: str
    listening_brief: ListeningBrief
    companion: ChapterCompanion
    vocabulary: dict[str, list[str]]
    recap: Recap | None


@dataclass(frozen=True)
class CompanionData:
    book: BookCompanion
    chapters: list[CompanionChapter]


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _resolve(repo_root: Path, value: str | None) -> Path | None:
    if value is None:
        return None
    path = Path(value)
    if path.is_absolute():
        return path
    return repo_root / path


def _require_list(value: Any, field_name: str) -> list[Any]:
    if not isinstance(value, list):
        raise TypeError(f"{field_name} must be a list")
    return value


def load_book_project(project_dir: Path, repo_root: Path | None = None) -> BookProject:
    project_dir = project_dir.resolve()
    repo_root = (
        repo_root.resolve()
        if repo_root is not None
        else project_dir.parent.parent.resolve()
    )
    data = _read_json(project_dir / "project.json")

    pairings = [
        Pairing(
            english_label=row["english_label"],
            english_href=row["english_href"],
            chinese_label=row.get("chinese_label"),
            chinese_href=row.get("chinese_href"),
            status=row["status"],
        )
        for row in data.get("pairings", [])
    ]

    optional_sections = [
        OptionalSection(
            title=row["title"],
            source=row["source"],
            href=row["href"],
            action=row["action"],
            language=row.get("language", "en"),
            intro=row.get("intro", ""),
        )
        for row in data.get("optional_sections", [])
    ]

    return BookProject(
        project_dir=project_dir,
        repo_root=repo_root,
        slug=data["slug"],
        title=data["title"],
        author=data["author"],
        language=data.get("language", "en"),
        description=data.get("description", ""),
        english_epub=_resolve(repo_root, data["sources"]["english"]),
        chinese_epub=_resolve(repo_root, data["sources"].get("chinese")),
        output_epub=_resolve(repo_root, data["output"]["epub"]),
        pairing_map=_resolve(repo_root, data["output"]["pairing_map"]),
        pairings=pairings,
        optional_sections=optional_sections,
    )


def load_companion(project_dir: Path) -> CompanionData:
    data = _read_json(project_dir / "companion.json")
    book_data = data["book"]
    chapters = []
    for row in data["chapters"]:
        brief = row["listening_brief"]
        companion = row["companion"]
        recap_data = row.get("recap")
        chapters.append(
            CompanionChapter(
                english_label=row["english_label"],
                listening_brief=ListeningBrief(
                    names=brief.get("names", ""),
                    points=list(
                        _require_list(
                            brief.get("points", []), "listening_brief.points"
                        )
                    ),
                    context=brief.get("context", ""),
                ),
                companion=ChapterCompanion(
                    zh=companion["zh"],
                    en=companion["en"],
                    priority=companion.get("priority", ""),
                ),
                vocabulary={
                    key: list(_require_list(value, f"vocabulary bucket '{key}'"))
                    for key, value in row.get("vocabulary", {}).items()
                },
                recap=Recap(zh=recap_data["zh"], en=recap_data["en"])
                if recap_data
                else None,
            )
        )
    return CompanionData(
        book=BookCompanion(
            companion_zh=book_data["companion_zh"],
            summary_en=book_data["summary_en"],
            references=list(book_data.get("references", [])),
        ),
        chapters=chapters,
    )
