from __future__ import annotations

from dataclasses import dataclass
import mimetypes
import posixpath
from pathlib import Path
from zipfile import ZipFile

from bs4 import BeautifulSoup
from ebooklib import epub

from .epub_io import (
    assess_chinese_chapter_text,
    extract_cover_asset,
    extract_href_fragment,
    read_container_path,
)
from .models import CompanionData, load_book_project, load_companion
from .pairing import render_pairing_map, validate_pairings
from .render import (
    load_css,
    paragraphs,
    render_book_companion,
    render_chapter_pages,
    section_file_names,
)
from .tts import validate_listener_text


@dataclass(frozen=True)
class BuildResult:
    output_epub: Path
    pairing_map: Path
    warnings: list[str]


def _add_xhtml_item(
    book: epub.EpubBook,
    css_item: epub.EpubItem,
    file_name: str,
    title: str,
    content: str,
    language: str,
) -> epub.EpubHtml:
    item = epub.EpubHtml(file_name=file_name, title=title, lang=language)
    item.content = content.encode("utf-8")
    item.add_item(css_item)
    book.add_item(item)
    return item


def _listener_text_errors(companion: CompanionData) -> list[str]:
    errors: list[str] = []
    errors.extend(validate_listener_text("Book Companion", companion.book.companion_zh))
    errors.extend(validate_listener_text("Book English Summary", companion.book.summary_en))
    for reference in companion.book.references:
        label = reference.get("label", "")
        if label:
            errors.extend(validate_listener_text("Book Reference Label", label))

    for chapter in companion.chapters:
        section = chapter.english_label
        errors.extend(validate_listener_text(f"{section} names", chapter.listening_brief.names))
        for point in chapter.listening_brief.points:
            errors.extend(validate_listener_text(f"{section} listening brief", point))
        errors.extend(
            validate_listener_text(f"{section} listening context", chapter.listening_brief.context)
        )
        errors.extend(validate_listener_text(f"{section} companion zh", chapter.companion.zh))
        errors.extend(validate_listener_text(f"{section} companion en", chapter.companion.en))
        errors.extend(
            validate_listener_text(f"{section} reading priority", chapter.companion.priority)
        )
        for bucket_name, items in chapter.vocabulary.items():
            for item in items:
                errors.extend(validate_listener_text(f"{section} vocabulary {bucket_name}", item))
        if chapter.recap is not None:
            errors.extend(validate_listener_text(f"{section} recap zh", chapter.recap.zh))
            errors.extend(validate_listener_text(f"{section} recap en", chapter.recap.en))
    return errors


def _epub_member_names(epub_path: Path) -> set[str]:
    with ZipFile(epub_path) as zf:
        return set(zf.namelist())


def _normalize_extract_href(epub_path: Path, href: str) -> str:
    path_part, fragment_sep, fragment = href.partition("#")
    with ZipFile(epub_path) as zf:
        opf_dir = posixpath.dirname(read_container_path(zf))

    normalized = path_part
    prefix = f"{opf_dir}/" if opf_dir else ""
    if prefix and path_part.startswith(prefix):
        normalized = path_part[len(prefix) :]

    if fragment_sep:
        return f"{normalized}#{fragment}"
    return normalized


def _extract_fragment(epub_path: Path, href: str) -> str:
    return extract_href_fragment(epub_path, _normalize_extract_href(epub_path, href))


def _prepare_fragment(
    book: epub.EpubBook,
    epub_path: Path,
    href: str,
    *,
    asset_prefix: str,
    warning_label: str,
) -> tuple[str, list[str]]:
    normalized_href = _normalize_extract_href(epub_path, href)
    fragment_html = extract_href_fragment(epub_path, normalized_href)
    document_href = normalized_href.split("#", 1)[0]
    document_dir = posixpath.dirname(document_href)
    warnings: list[str] = []

    with ZipFile(epub_path) as zf:
        opf_dir = posixpath.dirname(read_container_path(zf))
        soup = BeautifulSoup(fragment_html, "html.parser")
        images = soup.find_all("img")
        for index, image in enumerate(images, start=1):
            src = image.get("src", "").strip()
            if not src or src.startswith(("data:", "http://", "https://")):
                continue
            source_href = posixpath.normpath(posixpath.join(document_dir, src))
            source_member = (
                posixpath.normpath(posixpath.join(opf_dir, source_href))
                if opf_dir
                else source_href
            )
            suffix = Path(source_href).suffix or ".bin"
            target_name = f"assets/{asset_prefix}-{index:02d}{suffix}"
            media_type = mimetypes.guess_type(source_href)[0] or "application/octet-stream"
            book.add_item(
                epub.EpubItem(
                    uid=f"{asset_prefix}_asset_{index}",
                    file_name=target_name,
                    media_type=media_type,
                    content=zf.read(source_member),
                )
            )
            image["src"] = target_name

        has_visible_text = bool(soup.get_text(" ", strip=True))
        if images and not has_visible_text:
            warnings.append(
                f"{warning_label} is image-only in the source EPUB; TTS will not read it."
            )

        return str(soup), warnings


def _resolve_chinese_chapter_body(
    book: epub.EpubBook,
    chapter,
    project,
    pairing,
    index: int,
) -> tuple[str, list[str]]:
    generated = chapter.chinese_text
    if generated is not None and generated.mode == "generated_translation":
        return paragraphs(generated.content), []

    if project.chinese_epub is None or not pairing.chinese_href:
        if generated is not None:
            return paragraphs(generated.content), []
        raise ValueError(f"Missing usable Chinese chapter for {pairing.english_label}")

    chinese_fragment, chinese_warnings = _prepare_fragment(
        book,
        project.chinese_epub,
        pairing.chinese_href,
        asset_prefix=f"ch{index:02d}-zh",
        warning_label=f"Chinese chapter '{pairing.chinese_label or pairing.english_label}'",
    )

    usability = assess_chinese_chapter_text(chinese_fragment)
    if usability.is_usable:
        return chinese_fragment, []

    if generated is not None and generated.mode == "generated_translation":
        return paragraphs(generated.content), []

    raise ValueError(
        f"Chinese chapter '{pairing.chinese_label or pairing.english_label}' is "
        f"{usability.kind} and no generated translation is provided."
    )


def build_project(project_dir: Path, repo_root: Path | None = None) -> BuildResult:
    resolved_project_dir = Path(project_dir).resolve()
    resolved_repo_root = Path(repo_root).resolve() if repo_root is not None else None
    project = load_book_project(resolved_project_dir, resolved_repo_root)
    companion = load_companion(resolved_project_dir)

    if not project.english_epub.exists():
        raise FileNotFoundError(project.english_epub)
    if project.chinese_epub is not None and not project.chinese_epub.exists():
        raise FileNotFoundError(project.chinese_epub)

    listener_errors = _listener_text_errors(companion)
    if listener_errors:
        raise ValueError("; ".join(listener_errors))

    english_hrefs = _epub_member_names(project.english_epub)
    chinese_hrefs = (
        _epub_member_names(project.chinese_epub)
        if project.chinese_epub is not None
        else set()
    )
    pairing_errors = validate_pairings(project.pairings, english_hrefs, chinese_hrefs)
    if pairing_errors:
        raise ValueError("; ".join(pairing_errors))

    chapter_by_label = {chapter.english_label: chapter for chapter in companion.chapters}
    source_notes = [f"{section.title}: {section.action}" for section in project.optional_sections]
    project.pairing_map.parent.mkdir(parents=True, exist_ok=True)
    project.pairing_map.write_text(
        render_pairing_map(project.title, project.pairings, source_notes),
        encoding="utf-8",
    )

    book = epub.EpubBook()
    book.set_identifier(project.slug)
    book.set_title(project.title)
    book.set_language(project.language)
    book.add_author(project.author)
    if project.description:
        book.add_metadata("DC", "description", project.description)
    warnings: list[str] = []

    cover_asset = extract_cover_asset(project.english_epub)
    cover_source = project.english_epub
    if cover_asset is None and project.chinese_epub is not None:
        cover_asset = extract_cover_asset(project.chinese_epub)
        cover_source = project.chinese_epub
    if cover_asset is not None:
        book.set_cover(
            _normalize_extract_href(cover_source, cover_asset.href),
            cover_asset.content,
            create_page=False,
        )
    else:
        warnings.append("No extractable cover found in English or Chinese source EPUBs.")

    css_item = epub.EpubItem(
        uid="style_main",
        file_name="style/main.css",
        media_type="text/css",
        content=load_css().encode("utf-8"),
    )
    book.add_item(css_item)

    pages: list[epub.EpubHtml] = [
        _add_xhtml_item(
            book,
            css_item,
            "book-companion.xhtml",
            "Book Companion",
            render_book_companion(project.title, companion.book),
            "zh",
        )
    ]

    for index, pairing in enumerate(project.pairings, start=1):
        chapter = chapter_by_label.get(pairing.english_label)
        if chapter is None:
            raise ValueError(f"Missing companion chapter for {pairing.english_label}")

        file_names = section_file_names(index)
        english_fragment, english_warnings = _prepare_fragment(
            book,
            project.english_epub,
            pairing.english_href,
            asset_prefix=f"ch{index:02d}-en",
            warning_label=f"English chapter '{pairing.english_label}'",
        )
        chinese_fragment, chinese_resolution_warnings = _resolve_chinese_chapter_body(
            book,
            chapter,
            project,
            pairing,
            index,
        )
        warnings.extend(english_warnings)
        warnings.extend(chinese_resolution_warnings)

        rendered_pages = render_chapter_pages(
            index,
            pairing.chinese_label or pairing.english_label,
            chapter,
            chinese_fragment,
            english_fragment,
        )
        pages.extend(
            [
                _add_xhtml_item(
                    book,
                    css_item,
                    file_names["brief"],
                    f"Chapter {index} Listening Brief",
                    rendered_pages["brief"],
                    "zh",
                ),
                _add_xhtml_item(
                    book,
                    css_item,
                    file_names["companion"],
                    f"Chapter {index} Companion Reference",
                    rendered_pages["companion"],
                    "zh",
                ),
                _add_xhtml_item(
                    book,
                    css_item,
                    file_names["zh"],
                    f"Chapter {index} Chinese",
                    rendered_pages["zh"],
                    "zh",
                ),
                _add_xhtml_item(
                    book,
                    css_item,
                    file_names["vocab"],
                    f"Chapter {index} Vocabulary For Listening",
                    rendered_pages["vocab"],
                    "en",
                ),
                _add_xhtml_item(
                    book,
                    css_item,
                    file_names["en"],
                    f"Chapter {index} English",
                    rendered_pages["en"],
                    "en",
                ),
                _add_xhtml_item(
                    book,
                    css_item,
                    file_names["recap"],
                    f"Chapter {index} Recap",
                    rendered_pages["recap"],
                    "zh",
                ),
            ]
        )

    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.toc = tuple(pages)
    book.spine = ["nav", *pages]

    project.output_epub.parent.mkdir(parents=True, exist_ok=True)
    epub.write_epub(str(project.output_epub), book, {})

    return BuildResult(
        output_epub=project.output_epub,
        pairing_map=project.pairing_map,
        warnings=warnings,
    )
