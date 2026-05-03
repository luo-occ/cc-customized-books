# Reusable EPUB Framework Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a reusable Python framework and CLI that turns per-book project files into TTS-first bilingual study EPUBs, starting with Animal Farm as the migrated example.

**Architecture:** Split the former one-off Animal Farm script into focused modules under `scripts/custom_epub/`: data loading, EPUB parsing, pairing, vocabulary helpers, TTS validation, rendering, and build orchestration. Keep creative book-specific material in `book_projects/<slug>/project.json` and `companion.json`; the CLI reads those files and produces `output/<Book>/pairing-map.md` plus the final EPUB. Use Python standard-library `unittest` for TDD so the project does not need a new test dependency.

**Tech Stack:** Python 3, `ebooklib`, BeautifulSoup (`bs4`), `lxml`, `zipfile`, `xml.etree.ElementTree`, JSON, `unittest`, `rg`, Git.

---

## File Structure

- Create: `scripts/build_custom_epub.py`
  - CLI entrypoint: accepts one project directory and calls `custom_epub.builder.build_project`.
- Create: `scripts/custom_epub/__init__.py`
  - Package marker and version string.
- Create: `scripts/custom_epub/models.py`
  - Dataclasses and JSON loaders for project config and companion content.
- Create: `scripts/custom_epub/epub_io.py`
  - EPUB container, OPF, spine, NCX, and body-fragment extraction helpers.
- Create: `scripts/custom_epub/pairing.py`
  - Pairing validation and `pairing-map.md` rendering.
- Create: `scripts/custom_epub/vocabulary.py`
  - Glossary loading, tokenization, and candidate matching.
- Create: `scripts/custom_epub/tts.py`
  - Raw URL detection and listener-facing text validation.
- Create: `scripts/custom_epub/render.py`
  - XHTML page rendering and shared section names.
- Create: `scripts/custom_epub/builder.py`
  - Project build orchestration and EPUB writing.
- Create: `scripts/custom_epub/templates/style.css`
  - Shared output CSS migrated from the prototype.
- Create: `book_projects/animal-farm/project.json`
  - Animal Farm deterministic source/output/pairing configuration.
- Create: `book_projects/animal-farm/companion.json`
  - Animal Farm companion content migrated from `scripts/build_animal_farm_custom_epub.py`.
- Modify: `AGENTS.md`
  - Point agents to the reusable framework instead of generating final one-off scripts.
- Tests:
  - `tests/test_models.py`
  - `tests/test_epub_io.py`
  - `tests/test_pairing.py`
  - `tests/test_vocabulary.py`
  - `tests/test_tts.py`
  - `tests/test_render.py`
  - `tests/test_builder_smoke.py`

The existing `scripts/build_animal_farm_custom_epub.py` remains available as migration source during implementation. After the reusable Animal Farm build passes, remove it from normal workflow by leaving it unreferenced or deleting it if it is tracked by the implementation branch.

---

### Task 1: Models And Project Loading

**Files:**
- Create: `scripts/custom_epub/__init__.py`
- Create: `scripts/custom_epub/models.py`
- Create: `tests/test_models.py`

- [ ] **Step 1: Write failing model-loading tests**

Create `tests/test_models.py`:

```python
import json
import tempfile
import unittest
from pathlib import Path

from custom_epub.models import load_book_project, load_companion


class ModelLoadingTests(unittest.TestCase):
    def test_load_book_project_resolves_paths_relative_to_repo_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project_dir = root / "book_projects" / "sample"
            project_dir.mkdir(parents=True)
            (project_dir / "project.json").write_text(json.dumps({
                "slug": "sample",
                "title": "Sample Book",
                "author": "Author Name",
                "language": "en",
                "description": "A sample bilingual project.",
                "sources": {
                    "english": "books/Sample/en.epub",
                    "chinese": "books/Sample/zh.epub"
                },
                "output": {
                    "epub": "output/Sample/Sample.epub",
                    "pairing_map": "output/Sample/pairing-map.md"
                },
                "pairings": [
                    {
                        "english_label": "Chapter One",
                        "english_href": "Text/ch1.xhtml",
                        "chinese_label": "第一章",
                        "chinese_href": "Text/zh1.xhtml",
                        "status": "matched"
                    }
                ],
                "optional_sections": [
                    {
                        "title": "Optional Preface",
                        "source": "Chinese preface",
                        "href": "Text/preface.xhtml",
                        "action": "visual-only",
                        "language": "zh",
                        "intro": "Skip during first listening."
                    }
                ]
            }), encoding="utf-8")

            project = load_book_project(project_dir, root)

            self.assertEqual(project.slug, "sample")
            self.assertEqual(project.title, "Sample Book")
            self.assertEqual(project.english_epub, root / "books/Sample/en.epub")
            self.assertEqual(project.chinese_epub, root / "books/Sample/zh.epub")
            self.assertEqual(project.output_epub, root / "output/Sample/Sample.epub")
            self.assertEqual(project.pairings[0].status, "matched")
            self.assertEqual(project.optional_sections[0].action, "visual-only")

    def test_load_companion_requires_book_and_chapters(self):
        with tempfile.TemporaryDirectory() as tmp:
            project_dir = Path(tmp)
            (project_dir / "companion.json").write_text(json.dumps({
                "book": {
                    "companion_zh": "中文导读",
                    "summary_en": "English guide",
                    "references": [{"label": "Publisher page"}]
                },
                "chapters": [
                    {
                        "english_label": "Chapter One",
                        "listening_brief": {
                            "names": "Old Major",
                            "points": ["Listen for the speech."],
                            "context": "Opening chapter."
                        },
                        "companion": {
                            "zh": "中文章节导读",
                            "en": "English chapter summary.",
                            "priority": "Read closely."
                        },
                        "vocabulary": {
                            "Must know": ["comrade, noun, 同志。A political address."],
                            "Useful / high-value": [],
                            "Specialized or context-bound": []
                        },
                        "recap": {
                            "zh": "中文回顾",
                            "en": "English recap."
                        }
                    }
                ]
            }), encoding="utf-8")

            companion = load_companion(project_dir)

            self.assertEqual(companion.book.companion_zh, "中文导读")
            self.assertEqual(companion.chapters[0].english_label, "Chapter One")
            self.assertEqual(companion.chapters[0].vocabulary["Must know"][0].split(",", 1)[0], "comrade")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests and verify they fail for missing module**

Run:

```bash
PYTHONPATH=scripts python3 -m unittest tests.test_models -v
```

Expected: fails with `ModuleNotFoundError` or import errors for `custom_epub.models`.

- [ ] **Step 3: Implement model dataclasses and loaders**

Create `scripts/custom_epub/__init__.py`:

```python
"""Reusable custom EPUB framework."""

__version__ = "0.1.0"
```

Create `scripts/custom_epub/models.py`:

```python
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


def load_book_project(project_dir: Path, repo_root: Path | None = None) -> BookProject:
    project_dir = project_dir.resolve()
    repo_root = repo_root.resolve() if repo_root is not None else Path.cwd().resolve()
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
                    points=list(brief.get("points", [])),
                    context=brief.get("context", ""),
                ),
                companion=ChapterCompanion(
                    zh=companion["zh"],
                    en=companion["en"],
                    priority=companion.get("priority", ""),
                ),
                vocabulary={key: list(value) for key, value in row.get("vocabulary", {}).items()},
                recap=Recap(zh=recap_data["zh"], en=recap_data["en"]) if recap_data else None,
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
```

- [ ] **Step 4: Run model tests and verify they pass**

Run:

```bash
PYTHONPATH=scripts python3 -m unittest tests.test_models -v
```

Expected: two passing tests.

- [ ] **Step 5: Commit Task 1**

Run:

```bash
git add scripts/custom_epub/__init__.py scripts/custom_epub/models.py tests/test_models.py
git commit -m "Add reusable EPUB project models"
```

Expected: commit succeeds and includes only these three files.

---

### Task 2: EPUB Parsing Helpers

**Files:**
- Create: `scripts/custom_epub/epub_io.py`
- Create: `tests/test_epub_io.py`

- [ ] **Step 1: Write failing EPUB parser tests**

Create `tests/test_epub_io.py`:

```python
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

from custom_epub.epub_io import clean_body_fragment, load_epub_structure, read_container_path


def make_epub_fixture(path: Path) -> None:
    with ZipFile(path, "w") as zf:
        zf.writestr("META-INF/container.xml", """<?xml version="1.0"?>
<container xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>""")
        zf.writestr("OEBPS/content.opf", """<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="2.0">
  <manifest>
    <item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>
    <item id="ch1" href="Text/ch1.xhtml" media-type="application/xhtml+xml"/>
    <item id="ch2" href="Text/ch2.xhtml" media-type="application/xhtml+xml"/>
  </manifest>
  <spine toc="ncx">
    <itemref idref="ch1"/>
    <itemref idref="ch2"/>
  </spine>
</package>""")
        zf.writestr("OEBPS/toc.ncx", """<?xml version="1.0" encoding="utf-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/">
  <navMap>
    <navPoint id="n1" playOrder="1"><navLabel><text>Chapter One</text></navLabel><content src="Text/ch1.xhtml"/></navPoint>
    <navPoint id="n2" playOrder="2"><navLabel><text>Chapter Two</text></navLabel><content src="Text/ch2.xhtml"/></navPoint>
  </navMap>
</ncx>""")
        zf.writestr("OEBPS/Text/ch1.xhtml", """<html xmlns="http://www.w3.org/1999/xhtml"><body><h1>Chapter One</h1><p class="x" onclick="bad()">Hello <a href="note.xhtml">note</a>.</p><script>bad()</script></body></html>""")
        zf.writestr("OEBPS/Text/ch2.xhtml", """<html xmlns="http://www.w3.org/1999/xhtml"><body><h1>Chapter Two</h1><p>Second.</p></body></html>""")


class EpubIoTests(unittest.TestCase):
    def test_read_container_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            epub_path = Path(tmp) / "sample.epub"
            make_epub_fixture(epub_path)
            with ZipFile(epub_path) as zf:
                self.assertEqual(read_container_path(zf), "OEBPS/content.opf")

    def test_load_epub_structure_reads_spine_and_nav(self):
        with tempfile.TemporaryDirectory() as tmp:
            epub_path = Path(tmp) / "sample.epub"
            make_epub_fixture(epub_path)
            structure = load_epub_structure(epub_path)

            self.assertEqual(structure.spine, ["OEBPS/Text/ch1.xhtml", "OEBPS/Text/ch2.xhtml"])
            self.assertEqual([entry.label for entry in structure.nav], ["Chapter One", "Chapter Two"])
            self.assertEqual(structure.nav[0].href, "OEBPS/Text/ch1.xhtml")

    def test_clean_body_fragment_removes_scripts_and_unsafe_attrs(self):
        raw = b'<html><body><p class="x" onclick="bad()">Hi <a href="x.html" style="color:red">link</a></p><script>bad()</script></body></html>'
        fragment = clean_body_fragment(raw)

        self.assertIn("<p>Hi", fragment)
        self.assertIn('<a href="x.html">link</a>', fragment)
        self.assertNotIn("onclick", fragment)
        self.assertNotIn("<script", fragment)
        self.assertNotIn("style=", fragment)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests and verify they fail for missing parser module**

Run:

```bash
PYTHONPATH=scripts python3 -m unittest tests.test_epub_io -v
```

Expected: fails because `custom_epub.epub_io` is missing.

- [ ] **Step 3: Implement EPUB parser helpers**

Create `scripts/custom_epub/epub_io.py`:

```python
from __future__ import annotations

import posixpath
from dataclasses import dataclass
from pathlib import Path
from zipfile import ZipFile
from xml.etree import ElementTree as ET

from bs4 import BeautifulSoup


OPF_NS = {"opf": "http://www.idpf.org/2007/opf"}
CONTAINER_NS = {"c": "urn:oasis:names:tc:opendocument:xmlns:container"}
NCX_NS = {"n": "http://www.daisy.org/z3986/2005/ncx/"}


@dataclass(frozen=True)
class NavEntry:
    label: str
    href: str


@dataclass(frozen=True)
class EpubStructure:
    opf_path: str
    spine: list[str]
    nav: list[NavEntry]


def read_container_path(zf: ZipFile) -> str:
    root = ET.fromstring(zf.read("META-INF/container.xml"))
    node = root.find(".//c:rootfile", CONTAINER_NS)
    if node is None:
        raise RuntimeError("Could not locate OPF path from META-INF/container.xml")
    return node.attrib["full-path"]


def _flatten_navpoints(parent: ET.Element) -> list[ET.Element]:
    nodes: list[ET.Element] = []
    for nav in parent.findall("n:navPoint", NCX_NS):
        nodes.append(nav)
        nodes.extend(_flatten_navpoints(nav))
    return nodes


def load_epub_structure(epub_path: Path) -> EpubStructure:
    with ZipFile(epub_path) as zf:
        opf_path = read_container_path(zf)
        opf_dir = posixpath.dirname(opf_path)
        opf_root = ET.fromstring(zf.read(opf_path))

        manifest: dict[str, str] = {}
        media_types: dict[str, str] = {}
        for item in opf_root.findall(".//opf:manifest/opf:item", OPF_NS):
            item_id = item.attrib["id"]
            href = posixpath.normpath(posixpath.join(opf_dir, item.attrib["href"]))
            manifest[item_id] = href
            media_types[item_id] = item.attrib.get("media-type", "")

        spine: list[str] = []
        for itemref in opf_root.findall(".//opf:spine/opf:itemref", OPF_NS):
            item_id = itemref.attrib["idref"]
            if media_types.get(item_id) == "application/xhtml+xml":
                spine.append(manifest[item_id])

        spine_node = opf_root.find(".//opf:spine", OPF_NS)
        toc_id = spine_node.attrib.get("toc") if spine_node is not None else None
        ncx_path = manifest.get(toc_id) if toc_id else None
        if ncx_path is None:
            for item_id, media_type in media_types.items():
                if media_type == "application/x-dtbncx+xml":
                    ncx_path = manifest[item_id]
                    break
        if ncx_path is None:
            raise RuntimeError(f"Could not locate NCX navigation in {epub_path}")

        ncx_root = ET.fromstring(zf.read(ncx_path))
        nav_map = ncx_root.find(".//n:navMap", NCX_NS)
        nav: list[NavEntry] = []
        if nav_map is not None:
            for navpoint in _flatten_navpoints(nav_map):
                label_node = navpoint.find("n:navLabel/n:text", NCX_NS)
                content_node = navpoint.find("n:content", NCX_NS)
                if label_node is None or content_node is None:
                    continue
                label = "".join(label_node.itertext()).strip()
                src = content_node.attrib["src"].split("#", 1)[0]
                href = posixpath.normpath(posixpath.join(posixpath.dirname(ncx_path), src))
                nav.append(NavEntry(label=label, href=href))

    return EpubStructure(opf_path=opf_path, spine=spine, nav=nav)


def clean_body_fragment(raw: bytes) -> str:
    text = raw.decode("utf-8")
    parser = "lxml-xml" if text.lstrip().startswith("<?xml") else "lxml"
    soup = BeautifulSoup(text, parser)
    body = soup.find("body")
    if body is None:
        return ""
    for tag in body.find_all(["script", "style"]):
        tag.decompose()
    for tag in body.find_all(True):
        attrs: dict[str, str] = {}
        if tag.name == "a" and tag.get("href"):
            attrs["href"] = tag["href"]
        if tag.name == "img" and tag.get("src"):
            attrs["src"] = tag["src"]
            if tag.get("alt"):
                attrs["alt"] = tag["alt"]
        tag.attrs = attrs
    return "".join(str(child) for child in body.contents).strip()


def extract_href_fragment(epub_path: Path, href: str) -> str:
    with ZipFile(epub_path) as zf:
        return clean_body_fragment(zf.read(href))
```

- [ ] **Step 4: Run EPUB parser tests**

Run:

```bash
PYTHONPATH=scripts python3 -m unittest tests.test_epub_io -v
```

Expected: three passing tests.

- [ ] **Step 5: Run model and parser tests together**

Run:

```bash
PYTHONPATH=scripts python3 -m unittest tests.test_models tests.test_epub_io -v
```

Expected: five passing tests.

- [ ] **Step 6: Commit Task 2**

Run:

```bash
git add scripts/custom_epub/epub_io.py tests/test_epub_io.py
git commit -m "Add EPUB structure parsing helpers"
```

Expected: commit succeeds and includes only these two files.

---

### Task 3: Pairing, Vocabulary, And TTS Helpers

**Files:**
- Create: `scripts/custom_epub/pairing.py`
- Create: `scripts/custom_epub/vocabulary.py`
- Create: `scripts/custom_epub/tts.py`
- Create: `tests/test_pairing.py`
- Create: `tests/test_vocabulary.py`
- Create: `tests/test_tts.py`

- [ ] **Step 1: Write failing helper tests**

Create `tests/test_pairing.py`:

```python
import unittest

from custom_epub.models import Pairing
from custom_epub.pairing import render_pairing_map, validate_pairings


class PairingTests(unittest.TestCase):
    def test_render_pairing_map_includes_rows_and_source_notes(self):
        rows = [Pairing("Chapter One", "en/ch1.xhtml", "第一章", "zh/ch1.xhtml", "matched")]
        markdown = render_pairing_map("Sample", rows, ["Chinese preface is visual-only."])

        self.assertIn("# Sample Pairing Map", markdown)
        self.assertIn("| Chapter One | `en/ch1.xhtml` | 第一章 | `zh/ch1.xhtml` | matched |", markdown)
        self.assertIn("Chinese preface is visual-only.", markdown)

    def test_validate_pairings_rejects_missing_english_href(self):
        rows = [Pairing("Chapter One", "missing.xhtml", "第一章", "zh/ch1.xhtml", "matched")]
        errors = validate_pairings(rows, {"en/ch1.xhtml"}, {"zh/ch1.xhtml"})

        self.assertEqual(errors, ["Chapter One references missing English href missing.xhtml"])


if __name__ == "__main__":
    unittest.main()
```

Create `tests/test_vocabulary.py`:

```python
import tempfile
import unittest
from pathlib import Path

from custom_epub.vocabulary import find_glossary_matches, load_glossary_words, tokenize_english


class VocabularyTests(unittest.TestCase):
    def test_load_glossary_words_ignores_blank_lines(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "words.txt"
            path.write_text("tyranny\\n\\ncomrade\\n", encoding="utf-8")
            self.assertEqual(load_glossary_words(path), {"tyranny", "comrade"})

    def test_find_glossary_matches_tokenizes_case_insensitively(self):
        words = {"tyranny", "comrade", "windmill"}
        text = "Comrades spoke against tyranny near the windmill."
        self.assertEqual(find_glossary_matches(text, words), ["comrade", "tyranny", "windmill"])

    def test_tokenize_english_handles_apostrophes(self):
        self.assertEqual(tokenize_english("Animal's farm isn't quiet."), ["animal", "s", "farm", "isn", "t", "quiet"])


if __name__ == "__main__":
    unittest.main()
```

Create `tests/test_tts.py`:

```python
import unittest

from custom_epub.tts import find_raw_urls, validate_listener_text


class TtsTests(unittest.TestCase):
    def test_find_raw_urls_detects_http_and_www(self):
        text = "Read https://example.com and www.example.org for more."
        self.assertEqual(find_raw_urls(text), ["https://example.com", "www.example.org"])

    def test_validate_listener_text_reports_raw_urls(self):
        errors = validate_listener_text("Book Companion", "See https://example.com.")
        self.assertEqual(errors, ["Book Companion contains raw listener-facing URL: https://example.com"])

    def test_validate_listener_text_allows_source_labels(self):
        self.assertEqual(validate_listener_text("Book Companion", "Source: publisher page."), [])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run helper tests and verify they fail for missing modules**

Run:

```bash
PYTHONPATH=scripts python3 -m unittest tests.test_pairing tests.test_vocabulary tests.test_tts -v
```

Expected: fails because `pairing`, `vocabulary`, and `tts` modules are missing.

- [ ] **Step 3: Implement helpers**

Create `scripts/custom_epub/pairing.py`:

```python
from __future__ import annotations

from .models import Pairing


def validate_pairings(pairings: list[Pairing], english_hrefs: set[str], chinese_hrefs: set[str]) -> list[str]:
    errors: list[str] = []
    for row in pairings:
        if row.english_href not in english_hrefs:
            errors.append(f"{row.english_label} references missing English href {row.english_href}")
        if row.chinese_href and row.chinese_href not in chinese_hrefs:
            errors.append(f"{row.english_label} references missing Chinese href {row.chinese_href}")
    return errors


def render_pairing_map(title: str, rows: list[Pairing], source_notes: list[str]) -> str:
    lines = [
        f"# {title} Pairing Map",
        "",
        "| English chapter | English source | Chinese chapter | Chinese source | Status |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        chinese_label = row.chinese_label or ""
        chinese_href = f"`{row.chinese_href}`" if row.chinese_href else ""
        lines.append(f"| {row.english_label} | `{row.english_href}` | {chinese_label} | {chinese_href} | {row.status} |")
    if source_notes:
        lines.extend(["", "## Source inclusion notes", ""])
        lines.extend(f"- {note}" for note in source_notes)
    return "\n".join(lines) + "\n"
```

Create `scripts/custom_epub/vocabulary.py`:

```python
from __future__ import annotations

import re
from pathlib import Path


TOKEN_RE = re.compile(r"[A-Za-z]+")


def load_glossary_words(path: Path) -> set[str]:
    return {line.strip().lower() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()}


def tokenize_english(text: str) -> list[str]:
    return [match.group(0).lower() for match in TOKEN_RE.finditer(text)]


def find_glossary_matches(text: str, glossary_words: set[str]) -> list[str]:
    tokens = set(tokenize_english(text))
    return sorted(tokens & glossary_words)
```

Create `scripts/custom_epub/tts.py`:

```python
from __future__ import annotations

import re


RAW_URL_RE = re.compile(r"https?://[^\s<>)]+|www\.[^\s<>)]+")


def find_raw_urls(text: str) -> list[str]:
    return RAW_URL_RE.findall(text)


def validate_listener_text(section_name: str, text: str) -> list[str]:
    return [f"{section_name} contains raw listener-facing URL: {url}" for url in find_raw_urls(text)]
```

- [ ] **Step 4: Run helper tests**

Run:

```bash
PYTHONPATH=scripts python3 -m unittest tests.test_pairing tests.test_vocabulary tests.test_tts -v
```

Expected: seven passing tests.

- [ ] **Step 5: Run all current unit tests**

Run:

```bash
PYTHONPATH=scripts python3 -m unittest discover -s tests -v
```

Expected: twelve passing tests.

- [ ] **Step 6: Commit Task 3**

Run:

```bash
git add scripts/custom_epub/pairing.py scripts/custom_epub/vocabulary.py scripts/custom_epub/tts.py tests/test_pairing.py tests/test_vocabulary.py tests/test_tts.py
git commit -m "Add pairing vocabulary and TTS helpers"
```

Expected: commit succeeds and includes only these six files.

---

### Task 4: Rendering Layer

**Files:**
- Create: `scripts/custom_epub/render.py`
- Create: `scripts/custom_epub/templates/style.css`
- Create: `tests/test_render.py`

- [ ] **Step 1: Write failing render tests**

Create `tests/test_render.py`:

```python
import unittest

from custom_epub.models import BookCompanion, ChapterCompanion, CompanionChapter, ListeningBrief, Recap
from custom_epub.render import render_book_companion, render_chapter_pages, section_file_names


class RenderTests(unittest.TestCase):
    def test_section_file_names_are_stable(self):
        names = section_file_names(1)
        self.assertEqual(names["brief"], "ch01-brief.xhtml")
        self.assertEqual(names["companion"], "ch01-companion.xhtml")
        self.assertEqual(names["zh"], "ch01-zh.xhtml")
        self.assertEqual(names["vocab"], "ch01-vocab.xhtml")
        self.assertEqual(names["en"], "ch01-en.xhtml")
        self.assertEqual(names["recap"], "ch01-recap.xhtml")

    def test_render_book_companion_uses_labels_not_raw_urls(self):
        companion = BookCompanion(
            companion_zh="中文导读",
            summary_en="English guide.",
            references=[{"label": "Publisher page"}],
        )
        html = render_book_companion("Sample", companion)

        self.assertIn("Book Companion", html)
        self.assertIn("中文导读", html)
        self.assertIn("Publisher page", html)
        self.assertNotIn("http", html)

    def test_render_chapter_pages_has_expected_titles(self):
        chapter = CompanionChapter(
            english_label="Chapter One",
            listening_brief=ListeningBrief(names="Old Major", points=["Listen for slogans."], context="Opening."),
            companion=ChapterCompanion(zh="中文伴读", en="English summary.", priority="Read closely."),
            vocabulary={"Must know": ["comrade, noun, 同志。"], "Useful / high-value": [], "Specialized or context-bound": []},
            recap=Recap(zh="中文回顾", en="English recap."),
        )
        pages = render_chapter_pages(1, "第一章", chapter, "<p>中文正文</p>", "<p>English text.</p>")

        self.assertIn("Chapter 1 Listening Brief", pages["brief"])
        self.assertIn("Chapter 1 Companion Reference", pages["companion"])
        self.assertIn("Chapter 1 Chinese", pages["zh"])
        self.assertIn("Chapter 1 Vocabulary For Listening", pages["vocab"])
        self.assertIn("Chapter 1 English", pages["en"])
        self.assertIn("Chapter 1 Recap", pages["recap"])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run render tests and verify failure**

Run:

```bash
PYTHONPATH=scripts python3 -m unittest tests.test_render -v
```

Expected: fails because `custom_epub.render` is missing.

- [ ] **Step 3: Implement render helpers and CSS**

Create `scripts/custom_epub/templates/style.css` by moving the CSS rules from `scripts/build_animal_farm_custom_epub.py` into this file. Keep the same class names used by the prototype: `title-page`, `eyebrow`, `optional-label`, `source-note`, `panel`, `priority`, `english-summary`, `source-text`, and `recap`.

Create `scripts/custom_epub/render.py`:

```python
from __future__ import annotations

import html
from importlib import resources

from .models import BookCompanion, CompanionChapter


def load_css() -> str:
    return resources.files("custom_epub.templates").joinpath("style.css").read_text(encoding="utf-8")


def html_page(title: str, body: str) -> str:
    return f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
  <title>{html.escape(title)}</title>
  <link href="style/main.css" rel="stylesheet" type="text/css"/>
</head>
<body>
{body}
</body>
</html>"""


def section_file_names(chapter_num: int) -> dict[str, str]:
    prefix = f"ch{chapter_num:02d}"
    return {
        "brief": f"{prefix}-brief.xhtml",
        "companion": f"{prefix}-companion.xhtml",
        "zh": f"{prefix}-zh.xhtml",
        "vocab": f"{prefix}-vocab.xhtml",
        "en": f"{prefix}-en.xhtml",
        "recap": f"{prefix}-recap.xhtml",
    }


def paragraphs(text: str) -> str:
    return "".join(f"<p>{html.escape(part)}</p>" for part in text.split("\n\n") if part.strip())


def render_book_companion(title: str, companion: BookCompanion) -> str:
    references = "".join(f"<li>{html.escape(ref['label'])}</li>" for ref in companion.references)
    return html_page(
        "Book Companion",
        f"""
<p class="eyebrow">Book Companion</p>
<h1>{html.escape(title)} / Book Companion</h1>
{paragraphs(companion.companion_zh)}
<h2>English Summary</h2>
<div class="english-summary"><p>{html.escape(companion.summary_en)}</p></div>
<h2>References For Visual Review</h2>
<ul>{references}</ul>
""",
    )


def render_chapter_pages(chapter_num: int, chinese_label: str, chapter: CompanionChapter, chinese_fragment: str, english_fragment: str) -> dict[str, str]:
    names = section_file_names(chapter_num)
    point_items = "".join(f"<li>{html.escape(point)}</li>" for point in chapter.listening_brief.points)
    vocab_sections = []
    for heading in ["Must know", "Useful / high-value", "Specialized or context-bound"]:
        items = "".join(f"<p>{html.escape(item)}</p>" for item in chapter.vocabulary.get(heading, []))
        vocab_sections.append(f"<h2>{html.escape(heading)}</h2>{items}")
    recap = chapter.recap
    return {
        "brief": html_page(
            f"Chapter {chapter_num} Listening Brief",
            f"""
<p class="eyebrow">Chapter {chapter_num} Listening Brief</p>
<h1>Chapter {chapter_num} Listening Brief / {html.escape(chinese_label)} 听前提示</h1>
<div class="panel"><p><strong>Names:</strong> {html.escape(chapter.listening_brief.names)}</p><p>{html.escape(chapter.listening_brief.context)}</p></div>
<h2>What to listen for</h2>
<ul>{point_items}</ul>
""",
        ),
        "companion": html_page(
            f"Chapter {chapter_num} Companion Reference",
            f"""
<p class="eyebrow">Chapter {chapter_num} Companion Reference</p>
<h1>Chapter {chapter_num} Companion Reference / {html.escape(chinese_label)} 伴读参考</h1>
{paragraphs(chapter.companion.zh)}
<p class="priority">Reading priority: {html.escape(chapter.companion.priority)}</p>
<h2>English Summary</h2>
<div class="english-summary"><p>{html.escape(chapter.companion.en)}</p></div>
""",
        ),
        "zh": html_page(
            f"Chapter {chapter_num} Chinese",
            f"<h1>Chapter {chapter_num} Chinese / {html.escape(chinese_label)}</h1><div class=\"source-text\">{chinese_fragment}</div>",
        ),
        "vocab": html_page(
            f"Chapter {chapter_num} Vocabulary For Listening",
            f"<p class=\"eyebrow\">Chapter {chapter_num} Vocabulary For Listening</p><h1>Chapter {chapter_num} Vocabulary For Listening</h1>{''.join(vocab_sections)}",
        ),
        "en": html_page(
            f"Chapter {chapter_num} English",
            f"<h1>Chapter {chapter_num} English / {html.escape(chapter.english_label)}</h1><div class=\"source-text\">{english_fragment}</div>",
        ),
        "recap": html_page(
            f"Chapter {chapter_num} Recap",
            f"<p class=\"eyebrow\">Chapter {chapter_num} Recap</p><h1>Chapter {chapter_num} Recap</h1><div class=\"recap\"><p>{html.escape(recap.zh if recap else '')}</p><p><strong>English:</strong> {html.escape(recap.en if recap else '')}</p></div>",
        ),
    }
```

- [ ] **Step 4: Run render tests**

Run:

```bash
PYTHONPATH=scripts python3 -m unittest tests.test_render -v
```

Expected: three passing tests.

- [ ] **Step 5: Run all current unit tests**

Run:

```bash
PYTHONPATH=scripts python3 -m unittest discover -s tests -v
```

Expected: fifteen passing tests.

- [ ] **Step 6: Commit Task 4**

Run:

```bash
git add scripts/custom_epub/render.py scripts/custom_epub/templates/style.css tests/test_render.py
git commit -m "Add XHTML rendering layer"
```

Expected: commit succeeds and includes only these three files.

---

### Task 5: Builder And CLI

**Files:**
- Create: `scripts/custom_epub/builder.py`
- Create: `scripts/build_custom_epub.py`
- Create: `tests/test_builder_smoke.py`

- [ ] **Step 1: Write failing builder smoke test**

Create `tests/test_builder_smoke.py`:

```python
import json
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

from custom_epub.builder import build_project


def make_minimal_epub(path: Path, label: str, href: str, paragraph: str) -> None:
    with ZipFile(path, "w") as zf:
        zf.writestr("mimetype", "application/epub+zip")
        zf.writestr("META-INF/container.xml", """<?xml version="1.0"?>
<container xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles><rootfile full-path="OEBPS/content.opf"/></rootfiles></container>""")
        zf.writestr("OEBPS/content.opf", f"""<package xmlns="http://www.idpf.org/2007/opf" version="2.0">
<manifest><item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/><item id="ch1" href="{href}" media-type="application/xhtml+xml"/></manifest>
<spine toc="ncx"><itemref idref="ch1"/></spine></package>""")
        zf.writestr("OEBPS/toc.ncx", f"""<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/"><navMap><navPoint id="n1"><navLabel><text>{label}</text></navLabel><content src="{href}"/></navPoint></navMap></ncx>""")
        zf.writestr(f"OEBPS/{href}", f"<html><body><h1>{label}</h1><p>{paragraph}</p></body></html>")


class BuilderSmokeTests(unittest.TestCase):
    def test_build_project_creates_epub_and_pairing_map_without_raw_urls(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            books = root / "books" / "Sample"
            project_dir = root / "book_projects" / "sample"
            books.mkdir(parents=True)
            project_dir.mkdir(parents=True)
            make_minimal_epub(books / "en.epub", "Chapter One", "Text/ch1.xhtml", "English text.")
            make_minimal_epub(books / "zh.epub", "第一章", "Text/zh1.xhtml", "中文正文。")
            (project_dir / "project.json").write_text(json.dumps({
                "slug": "sample",
                "title": "Sample",
                "author": "Author",
                "language": "en",
                "description": "Sample build.",
                "sources": {"english": "books/Sample/en.epub", "chinese": "books/Sample/zh.epub"},
                "output": {"epub": "output/Sample/Sample.epub", "pairing_map": "output/Sample/pairing-map.md"},
                "pairings": [{"english_label": "Chapter One", "english_href": "OEBPS/Text/ch1.xhtml", "chinese_label": "第一章", "chinese_href": "OEBPS/Text/zh1.xhtml", "status": "matched"}],
                "optional_sections": []
            }), encoding="utf-8")
            (project_dir / "companion.json").write_text(json.dumps({
                "book": {"companion_zh": "中文导读", "summary_en": "English summary.", "references": [{"label": "Publisher page"}]},
                "chapters": [{
                    "english_label": "Chapter One",
                    "listening_brief": {"names": "Name", "points": ["Listen for contrast."], "context": "Context."},
                    "companion": {"zh": "中文伴读", "en": "English companion.", "priority": "Read closely."},
                    "vocabulary": {"Must know": ["contrast, noun, 对比。"], "Useful / high-value": [], "Specialized or context-bound": []},
                    "recap": {"zh": "中文回顾", "en": "English recap."}
                }]
            }), encoding="utf-8")

            result = build_project(project_dir, root)

            self.assertTrue(result.output_epub.exists())
            self.assertTrue(result.pairing_map.exists())
            with ZipFile(result.output_epub) as zf:
                names = zf.namelist()
                self.assertIn("EPUB/book-companion.xhtml", names)
                self.assertIn("EPUB/ch01-brief.xhtml", names)
                self.assertIn("EPUB/ch01-vocab.xhtml", names)
                xhtml = "\n".join(zf.read(name).decode("utf-8") for name in names if name.endswith(".xhtml"))
            self.assertIn("Chapter 1 Listening Brief", xhtml)
            self.assertIn("Chapter 1 Companion Reference", xhtml)
            self.assertNotIn("https://", xhtml)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run builder smoke test and verify failure**

Run:

```bash
PYTHONPATH=scripts python3 -m unittest tests.test_builder_smoke -v
```

Expected: fails because `custom_epub.builder` is missing.

- [ ] **Step 3: Implement builder and CLI**

Create `scripts/custom_epub/builder.py`:

```python
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from zipfile import ZipFile

from ebooklib import epub

from .epub_io import extract_href_fragment
from .models import BookProject, CompanionData, load_book_project, load_companion
from .pairing import render_pairing_map, validate_pairings
from .render import load_css, render_book_companion, render_chapter_pages
from .tts import validate_listener_text


@dataclass(frozen=True)
class BuildResult:
    output_epub: Path
    pairing_map: Path
    warnings: list[str]


def _add_html(book: epub.EpubBook, file_name: str, title: str, content: str, lang: str = "en") -> epub.EpubHtml:
    item = epub.EpubHtml(file_name=file_name, title=title, lang=lang)
    item.content = content
    item.add_item(book.get_item_with_id("style_main"))
    book.add_item(item)
    return item


def _listener_text_errors(companion: CompanionData) -> list[str]:
    errors: list[str] = []
    errors.extend(validate_listener_text("Book Companion", companion.book.companion_zh))
    errors.extend(validate_listener_text("Book English Summary", companion.book.summary_en))
    for chapter in companion.chapters:
        errors.extend(validate_listener_text(chapter.english_label, chapter.listening_brief.context))
        errors.extend(validate_listener_text(chapter.english_label, chapter.companion.zh))
        errors.extend(validate_listener_text(chapter.english_label, chapter.companion.en))
        for items in chapter.vocabulary.values():
            for item in items:
                errors.extend(validate_listener_text(chapter.english_label, item))
    return errors


def _epub_hrefs(epub_path: Path) -> set[str]:
    with ZipFile(epub_path) as zf:
        return set(zf.namelist())


def build_project(project_dir: Path, repo_root: Path | None = None) -> BuildResult:
    repo_root = repo_root or Path.cwd()
    project = load_book_project(project_dir, repo_root)
    companion = load_companion(project_dir)

    if not project.english_epub.exists():
        raise FileNotFoundError(project.english_epub)
    if project.chinese_epub is not None and not project.chinese_epub.exists():
        raise FileNotFoundError(project.chinese_epub)

    listener_errors = _listener_text_errors(companion)
    if listener_errors:
        raise ValueError("; ".join(listener_errors))

    english_hrefs = _epub_hrefs(project.english_epub)
    chinese_hrefs = _epub_hrefs(project.chinese_epub) if project.chinese_epub else set()
    pairing_errors = validate_pairings(project.pairings, english_hrefs, chinese_hrefs)
    if pairing_errors:
        raise ValueError("; ".join(pairing_errors))

    chapter_by_label = {chapter.english_label: chapter for chapter in companion.chapters}
    source_notes = [f"{section.title}: {section.action}" for section in project.optional_sections]
    project.pairing_map.parent.mkdir(parents=True, exist_ok=True)
    project.pairing_map.write_text(render_pairing_map(project.title, project.pairings, source_notes), encoding="utf-8")

    book = epub.EpubBook()
    book.set_identifier(project.slug)
    book.set_title(project.title)
    book.set_language(project.language)
    book.add_author(project.author)
    if project.description:
        book.add_metadata("DC", "description", project.description)

    css_item = epub.EpubItem(uid="style_main", file_name="style/main.css", media_type="text/css", content=load_css().encode("utf-8"))
    book.add_item(css_item)

    pages = []
    pages.append(_add_html(book, "book-companion.xhtml", "Book Companion", render_book_companion(project.title, companion.book), "zh"))

    for index, pairing in enumerate(project.pairings, start=1):
        chapter = chapter_by_label.get(pairing.english_label)
        if chapter is None:
            raise ValueError(f"Missing companion chapter for {pairing.english_label}")
        english_fragment = extract_href_fragment(project.english_epub, pairing.english_href)
        chinese_fragment = ""
        if project.chinese_epub is not None and pairing.chinese_href:
            chinese_fragment = extract_href_fragment(project.chinese_epub, pairing.chinese_href)
        rendered = render_chapter_pages(index, pairing.chinese_label or pairing.english_label, chapter, chinese_fragment, english_fragment)
        pages.extend([
            _add_html(book, f"ch{index:02d}-brief.xhtml", f"Chapter {index} Listening Brief", rendered["brief"], "zh"),
            _add_html(book, f"ch{index:02d}-companion.xhtml", f"Chapter {index} Companion Reference", rendered["companion"], "zh"),
            _add_html(book, f"ch{index:02d}-zh.xhtml", f"Chapter {index} Chinese", rendered["zh"], "zh"),
            _add_html(book, f"ch{index:02d}-vocab.xhtml", f"Chapter {index} Vocabulary For Listening", rendered["vocab"], "en"),
            _add_html(book, f"ch{index:02d}-en.xhtml", f"Chapter {index} English", rendered["en"], "en"),
            _add_html(book, f"ch{index:02d}-recap.xhtml", f"Chapter {index} Recap", rendered["recap"], "zh"),
        ])

    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.toc = tuple(pages)
    book.spine = ["nav"] + pages

    project.output_epub.parent.mkdir(parents=True, exist_ok=True)
    epub.write_epub(str(project.output_epub), book, {})
    return BuildResult(output_epub=project.output_epub, pairing_map=project.pairing_map, warnings=[])
```

Create `scripts/build_custom_epub.py`:

```python
#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from custom_epub.builder import build_project


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a customized bilingual study EPUB.")
    parser.add_argument("project_dir", type=Path, help="Path to a book project directory containing project.json and companion.json")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd(), help="Repository root used to resolve relative paths")
    args = parser.parse_args()

    result = build_project(args.project_dir, args.repo_root)
    print(f"EPUB: {result.output_epub}")
    print(f"Pairing map: {result.pairing_map}")
    for warning in result.warnings:
        print(f"Warning: {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run builder smoke test**

Run:

```bash
PYTHONPATH=scripts python3 -m unittest tests.test_builder_smoke -v
```

Expected: one passing test.

- [ ] **Step 5: Run all current tests**

Run:

```bash
PYTHONPATH=scripts python3 -m unittest discover -s tests -v
```

Expected: sixteen passing tests.

- [ ] **Step 6: Commit Task 5**

Run:

```bash
git add scripts/custom_epub/builder.py scripts/build_custom_epub.py tests/test_builder_smoke.py
git commit -m "Add reusable EPUB builder CLI"
```

Expected: commit succeeds and includes only these three files.

---

### Task 6: Migrate Animal Farm Project Files

**Files:**
- Create: `book_projects/animal-farm/project.json`
- Create: `book_projects/animal-farm/companion.json`

- [ ] **Step 1: Create Animal Farm `project.json`**

Create `book_projects/animal-farm/project.json` with source paths, output paths, ten chapter pairings from `output/Animal Farm/pairing-map.md`, and optional source-section notes for the Chinese translator preface and Ukrainian-edition preface.

Use this exact structure and preserve the current source filenames:

```json
{
  "slug": "animal-farm",
  "title": "Animal Farm / 动物农场 - Customized Bilingual Companion Edition",
  "author": "George Orwell",
  "language": "en",
  "description": "Customized bilingual Animal Farm EPUB with chapter briefs, companion notes, vocabulary support, and optional Chinese edition references.",
  "sources": {
    "english": "books/Animal Farm/Animal Farm (George Orwell) (z-library.sk, 1lib.sk, z-lib.sk).epub",
    "chinese": "books/Animal Farm/动物农场 ([英]乔治·奥威尔) (z-library.sk, 1lib.sk, z-lib.sk).epub"
  },
  "output": {
    "epub": "output/Animal Farm/Animal Farm - Customized Bilingual Companion.epub",
    "pairing_map": "output/Animal Farm/pairing-map.md"
  },
  "pairings": [
    {"english_label": "Chapter One", "english_href": "index_split_003.html", "chinese_label": "第一章", "chinese_href": "OEBPS/Text/part0003.xhtml", "status": "matched"},
    {"english_label": "Chapter Two", "english_href": "index_split_004.html", "chinese_label": "第二章", "chinese_href": "OEBPS/Text/part0005.xhtml", "status": "matched"},
    {"english_label": "Chapter Three", "english_href": "index_split_005.html", "chinese_label": "第三章", "chinese_href": "OEBPS/Text/part0007.xhtml", "status": "matched"},
    {"english_label": "Chapter Four", "english_href": "index_split_006.html", "chinese_label": "第四章", "chinese_href": "OEBPS/Text/part0009.xhtml", "status": "matched"},
    {"english_label": "Chapter Five", "english_href": "index_split_007.html", "chinese_label": "第五章", "chinese_href": "OEBPS/Text/part0011.xhtml", "status": "matched"},
    {"english_label": "Chapter Six", "english_href": "index_split_008.html", "chinese_label": "第六章", "chinese_href": "OEBPS/Text/part0013.xhtml", "status": "matched"},
    {"english_label": "Chapter Seven", "english_href": "index_split_009.html", "chinese_label": "第七章", "chinese_href": "OEBPS/Text/part0015.xhtml", "status": "matched"},
    {"english_label": "Chapter Eight", "english_href": "index_split_010.html", "chinese_label": "第八章", "chinese_href": "OEBPS/Text/part0017.xhtml", "status": "matched"},
    {"english_label": "Chapter Nine", "english_href": "index_split_011.html", "chinese_label": "第九章", "chinese_href": "OEBPS/Text/part0019.xhtml", "status": "matched"},
    {"english_label": "Chapter Ten", "english_href": "index_split_012.html", "chinese_label": "第十章", "chinese_href": "OEBPS/Text/part0021.xhtml", "status": "matched"}
  ],
  "optional_sections": [
    {"title": "Chinese Translator Preface", "source": "Chinese edition frontmatter", "href": "OEBPS/Text/part0001.xhtml", "action": "visual-only", "language": "zh", "intro": "This preface belongs to the Chinese edition rather than Orwell's main narrative. It can add context, but it can be skipped during a first listening pass."},
    {"title": "Ukrainian Edition Preface", "source": "Chinese edition appendix", "href": "OEBPS/Text/part0023.xhtml", "action": "visual-only", "language": "zh", "intro": "This appendix is relevant to Orwell's political intent, but it sits outside the main ten-chapter novel."}
  ]
}
```

- [ ] **Step 2: Create Animal Farm `companion.json`**

Create `book_projects/animal-farm/companion.json` by migrating the existing data from `scripts/build_animal_farm_custom_epub.py`:

- Book-level companion text from the prototype's `render_book_companion` function.
- Reference labels from `REFERENCES`, using only the human-readable labels in listener-facing JSON.
- Ten chapter entries from the prototype `CHAPTERS` list.
- For each chapter, map:
  - `title_en` to `english_label`.
  - `names`, `listening_points`, and `context` to `listening_brief`.
  - `companion_zh`, `companion_en`, and `priority` to `companion`.
  - `vocab` to `vocabulary`.
  - `recap_zh` and `recap_en` to `recap`.

Use valid UTF-8 JSON. Preserve the Chinese and English learning content from the prototype.

- [ ] **Step 3: Validate JSON loads**

Run:

```bash
PYTHONPATH=scripts python3 - <<'PY'
from pathlib import Path
from custom_epub.models import load_book_project, load_companion
project = load_book_project(Path("book_projects/animal-farm"), Path.cwd())
companion = load_companion(Path("book_projects/animal-farm"))
print(project.slug, len(project.pairings), len(companion.chapters))
PY
```

Expected output:

```text
animal-farm 10 10
```

- [ ] **Step 4: Run all current tests**

Run:

```bash
PYTHONPATH=scripts python3 -m unittest discover -s tests -v
```

Expected: all current tests pass.

- [ ] **Step 5: Commit Task 6**

Run:

```bash
git add book_projects/animal-farm/project.json book_projects/animal-farm/companion.json
git commit -m "Add Animal Farm reusable project files"
```

Expected: commit succeeds and includes only the two Animal Farm project files.

---

### Task 7: Animal Farm Integration Build And Guide Update

**Files:**
- Modify: `AGENTS.md`
- Optionally delete: `scripts/build_animal_farm_custom_epub.py` if it is tracked in the implementation branch.
- Verify output: `output/Animal Farm/Animal Farm - Customized Bilingual Companion.epub`
- Verify output: `output/Animal Farm/pairing-map.md`

- [ ] **Step 1: Run the reusable Animal Farm build**

Run:

```bash
PYTHONPATH=scripts python3 scripts/build_custom_epub.py book_projects/animal-farm
```

Expected output includes:

```text
EPUB: /Users/luojiaxing/Code/cc-customized-books/output/Animal Farm/Animal Farm - Customized Bilingual Companion.epub
Pairing map: /Users/luojiaxing/Code/cc-customized-books/output/Animal Farm/pairing-map.md
```

- [ ] **Step 2: Verify generated EPUB archive contains expected files**

Run:

```bash
python3 - <<'PY'
from pathlib import Path
from zipfile import ZipFile
epub_path = Path("output/Animal Farm/Animal Farm - Customized Bilingual Companion.epub")
with ZipFile(epub_path) as zf:
    names = set(zf.namelist())
required = {
    "EPUB/book-companion.xhtml",
    "EPUB/ch01-brief.xhtml",
    "EPUB/ch01-companion.xhtml",
    "EPUB/ch01-zh.xhtml",
    "EPUB/ch01-vocab.xhtml",
    "EPUB/ch01-en.xhtml",
    "EPUB/ch01-recap.xhtml",
}
missing = sorted(required - names)
print("missing:", missing)
raise SystemExit(1 if missing else 0)
PY
```

Expected output:

```text
missing: []
```

- [ ] **Step 3: Verify no raw URLs in listener-facing XHTML**

Run:

```bash
python3 - <<'PY'
import re
from pathlib import Path
from zipfile import ZipFile
epub_path = Path("output/Animal Farm/Animal Farm - Customized Bilingual Companion.epub")
pattern = re.compile(r"https?://|www\\.")
hits = []
with ZipFile(epub_path) as zf:
    for name in zf.namelist():
        if name.endswith(".xhtml"):
            text = zf.read(name).decode("utf-8", errors="replace")
            if pattern.search(text):
                hits.append(name)
print("raw-url-files:", hits)
raise SystemExit(1 if hits else 0)
PY
```

Expected output:

```text
raw-url-files: []
```

- [ ] **Step 4: Update `AGENTS.md` to point to the reusable framework**

Add a new section after `## Core Workflow`:

```markdown
## Reusable Framework Workflow

Use the reusable framework for final EPUB builds instead of generating a new one-off script for each book.

For each book:

1. Create or update `book_projects/<slug>/project.json` with source EPUB paths, output paths, pairings, and optional source-section decisions.
2. Create or update `book_projects/<slug>/companion.json` with book companion notes, chapter listening briefs, chapter companion references, vocabulary, recaps, and pronunciation help.
3. Run `PYTHONPATH=scripts python3 scripts/build_custom_epub.py book_projects/<slug>`.
4. Verify the generated EPUB and pairing map under `output/<Book Name>/`.

Book-specific helper scripts may be used for temporary investigation, but they should not be the final deliverable. Preserve reusable mechanics in `scripts/custom_epub/` and book-specific judgment in `book_projects/<slug>/`.
```

- [ ] **Step 5: Verify AGENTS update**

Run:

```bash
rg -n "Reusable Framework Workflow|scripts/build_custom_epub.py|book_projects/<slug>|one-off script" AGENTS.md
```

Expected: output includes all listed phrases.

- [ ] **Step 6: Run all tests and Animal Farm smoke checks**

Run:

```bash
PYTHONPATH=scripts python3 -m unittest discover -s tests -v
PYTHONPATH=scripts python3 scripts/build_custom_epub.py book_projects/animal-farm
```

Expected: all tests pass, and the build command writes the EPUB and pairing map.

- [ ] **Step 7: Commit Task 7**

Run:

```bash
git add AGENTS.md output/Animal\ Farm/pairing-map.md output/Animal\ Farm/Animal\ Farm\ -\ Customized\ Bilingual\ Companion.epub
git add -u scripts/build_animal_farm_custom_epub.py
git commit -m "Wire Animal Farm through reusable EPUB builder"
```

Expected: commit succeeds. If `scripts/build_animal_farm_custom_epub.py` was never tracked, `git add -u` stages nothing for it; that is acceptable.

---

### Task 8: Final Verification

**Files:**
- Verify: `scripts/custom_epub/*`
- Verify: `scripts/build_custom_epub.py`
- Verify: `book_projects/animal-farm/*`
- Verify: `AGENTS.md`
- Verify: `output/Animal Farm/*`

- [ ] **Step 1: Run full unit test suite**

Run:

```bash
PYTHONPATH=scripts python3 -m unittest discover -s tests -v
```

Expected: all tests pass.

- [ ] **Step 2: Rebuild Animal Farm**

Run:

```bash
PYTHONPATH=scripts python3 scripts/build_custom_epub.py book_projects/animal-farm
```

Expected: command exits `0` and prints the EPUB and pairing map paths.

- [ ] **Step 3: Verify no raw listener-facing URLs**

Run:

```bash
python3 - <<'PY'
import re
from pathlib import Path
from zipfile import ZipFile
epub_path = Path("output/Animal Farm/Animal Farm - Customized Bilingual Companion.epub")
pattern = re.compile(r"https?://|www\\.")
hits = []
with ZipFile(epub_path) as zf:
    for name in zf.namelist():
        if name.endswith(".xhtml"):
            text = zf.read(name).decode("utf-8", errors="replace")
            if pattern.search(text):
                hits.append(name)
print("raw-url-files:", hits)
raise SystemExit(1 if hits else 0)
PY
```

Expected:

```text
raw-url-files: []
```

- [ ] **Step 4: Verify guide and plan language**

Run:

```bash
rg -n "Reusable Framework Workflow|build_custom_epub.py|companion.json|project.json" AGENTS.md
rg -n "T[B]D|T[O]DO|F[I]XME|placeh[o]lder|fill in [l]ater|figure out [l]ater" scripts book_projects tests AGENTS.md
```

Expected: first command finds reusable-framework instructions; second command has no matches and exits `1`.

- [ ] **Step 5: Inspect git status**

Run:

```bash
git status --short
```

Expected: only intentional generated output or source inputs remain staged/untracked. No unexpected edits outside the framework, tests, Animal Farm project files, output, and AGENTS guide.

- [ ] **Step 6: Final response evidence**

In the implementation final response, include:

- Framework entrypoint: `scripts/build_custom_epub.py`.
- Project example: `book_projects/animal-farm/`.
- Output EPUB path.
- Pairing map path.
- Test command and result.
- Raw-URL validation result.
- Note whether the prototype script was retained or removed.
