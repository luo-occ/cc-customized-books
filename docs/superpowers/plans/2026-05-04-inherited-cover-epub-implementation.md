# Inherited Cover EPUB Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make customized EPUBs inherit the original source-book cover, preferring the English EPUB and falling back to the Chinese EPUB only when the English cover cannot be extracted.

**Architecture:** Add reusable cover extraction helpers in the EPUB I/O layer, then wire the builder to attach an inherited cover with `ebooklib` while leaving the listening flow unchanged. Verify the behavior with fixture-based unit tests and a rebuilt Animal Farm artifact.

**Tech Stack:** Python 3, `unittest`, `ebooklib`, `zipfile`, `xml.etree.ElementTree`, `BeautifulSoup`, existing `scripts/custom_epub` modules.

---

## File Structure

- `scripts/custom_epub/epub_io.py`
  - Responsibility: source EPUB inspection helpers. This is where cover discovery and extraction should live.
- `tests/test_epub_io.py`
  - Responsibility: fixture-backed tests for EPUB structure parsing and cover extraction behavior.
- `scripts/custom_epub/builder.py`
  - Responsibility: final EPUB assembly. This is where inherited cover selection and attachment should be wired in.
- `tests/test_builder_smoke.py`
  - Responsibility: end-to-end builder regression coverage. This will prove the generated EPUB contains an inherited cover asset.
- `AGENTS.md`
  - Responsibility: future-agent workflow rules. This should mention that customized books inherit the source cover by default.
- `output/Animal Farm/Animal Farm - Customized Bilingual Companion.epub`
  - Responsibility: regenerated verification artifact with inherited cover.

### Task 1: Add Reusable Cover Extraction Helpers

**Files:**
- Modify: `scripts/custom_epub/epub_io.py`
- Modify: `tests/test_epub_io.py`

- [ ] **Step 1: Write failing cover extraction tests**

Extend `tests/test_epub_io.py` with two new tests and the fixture data they need.

Add a metadata-marked cover to `CONTENT_OPF`:

```python
CONTENT_OPF = """<?xml version="1.0" encoding="UTF-8"?>
<package version="2.0" unique-identifier="bookid" xmlns="http://www.idpf.org/2007/opf">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:title>Fixture Book</dc:title>
    <dc:language>en</dc:language>
    <meta name="cover" content="cover"/>
  </metadata>
  <manifest>
    <item id="ncx" href="Nav/toc.ncx" media-type="application/x-dtbncx+xml"/>
    <item id="c1" href="Text/ch1.xhtml" media-type="application/xhtml+xml"/>
    <item id="c2" href="Text/ch2.xhtml" media-type="application/xhtml+xml"/>
    <item id="cover" href="Images/cover.jpg" media-type="image/jpeg"/>
  </manifest>
  <spine toc="ncx">
    <itemref idref="cover"/>
    <itemref idref="c1"/>
    <itemref idref="c2"/>
  </spine>
</package>
"""
```

Add a fallback fixture for a frontmatter cover image:

```python
CONTENT_OPF_FRONTMATTER = """<?xml version="1.0" encoding="UTF-8"?>
<package version="2.0" unique-identifier="bookid" xmlns="http://www.idpf.org/2007/opf">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:title>Fixture Book</dc:title>
    <dc:language>en</dc:language>
  </metadata>
  <manifest>
    <item id="ncx" href="Nav/toc.ncx" media-type="application/x-dtbncx+xml"/>
    <item id="title" href="Text/titlepage.xhtml" media-type="application/xhtml+xml"/>
    <item id="c1" href="Text/ch1.xhtml" media-type="application/xhtml+xml"/>
    <item id="front-cover" href="Images/front-cover.png" media-type="image/png"/>
  </manifest>
  <spine toc="ncx">
    <itemref idref="title"/>
    <itemref idref="c1"/>
  </spine>
</package>
"""

TITLEPAGE = """<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml">
  <body>
    <div class="cover">
      <img src="../Images/front-cover.png" alt="Cover"/>
    </div>
  </body>
</html>
"""
```

Then add tests:

```python
from custom_epub.epub_io import extract_cover_asset

    def test_extract_cover_asset_uses_explicit_metadata_cover(self):
        with tempfile.TemporaryDirectory() as tmp:
            epub_path = self._build_epub(Path(tmp))
            cover = extract_cover_asset(epub_path)

            self.assertIsNotNone(cover)
            self.assertEqual(cover.href, "OPS/Images/cover.jpg")
            self.assertEqual(cover.media_type, "image/jpeg")
            self.assertEqual(cover.content, b"jpeg-bytes")

    def test_extract_cover_asset_falls_back_to_frontmatter_image(self):
        with tempfile.TemporaryDirectory() as tmp:
            epub_path = self._build_frontmatter_cover_epub(Path(tmp))
            cover = extract_cover_asset(epub_path)

            self.assertIsNotNone(cover)
            self.assertEqual(cover.href, "OPS/Images/front-cover.png")
            self.assertEqual(cover.media_type, "image/png")
            self.assertEqual(cover.content, b"png-bytes")
```

- [ ] **Step 2: Run the targeted tests to verify they fail**

Run:

```bash
PYTHONPATH=scripts python3 -m unittest tests.test_epub_io.EpubIoTests.test_extract_cover_asset_uses_explicit_metadata_cover tests.test_epub_io.EpubIoTests.test_extract_cover_asset_falls_back_to_frontmatter_image -v
```

Expected: `ImportError` or `AttributeError` because `extract_cover_asset` does not exist yet.

- [ ] **Step 3: Implement the minimal cover extraction helpers**

Update `scripts/custom_epub/epub_io.py` with a reusable cover dataclass and extractor:

```python
IMAGE_MEDIA_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
COVER_HINTS = ("cover", "cover-image", "front-cover", "titlepage")


@dataclass(frozen=True)
class CoverAsset:
    href: str
    media_type: str
    content: bytes
```

Add the main extraction entry point:

```python
def extract_cover_asset(epub_path: str | Path) -> CoverAsset | None:
    epub_path = Path(epub_path)
    with ZipFile(epub_path) as zf:
        opf_path = read_container_path(zf)
        opf_root = ET.fromstring(zf.read(opf_path))
        opf_dir = posixpath.dirname(opf_path)
        manifest = _load_manifest(opf_root, opf_dir)

        explicit_cover_id = _find_metadata_cover_id(opf_root)
        if explicit_cover_id:
            cover = _cover_from_manifest(zf, manifest, explicit_cover_id)
            if cover is not None:
                return cover

        for item_id, item in manifest.items():
            if "cover-image" in item["properties"]:
                cover = _cover_from_manifest(zf, manifest, item_id)
                if cover is not None:
                    return cover

        heuristic_cover = _find_cover_like_manifest_item(zf, manifest)
        if heuristic_cover is not None:
            return heuristic_cover

        spine = opf_root.find("opf:spine", OPF_NAMESPACES)
        if spine is not None:
            return _find_frontmatter_cover(zf, manifest, spine)
    return None
```

Add the helpers it depends on:

```python
def _load_manifest(opf_root: ET.Element, opf_dir: str) -> dict[str, dict[str, str | set[str]]]:
    manifest: dict[str, dict[str, str | set[str]]] = {}
    for item in opf_root.findall("opf:manifest/opf:item", OPF_NAMESPACES):
        item_id = item.attrib.get("id")
        href = item.attrib.get("href")
        if not item_id or not href:
            continue
        properties = set(item.attrib.get("properties", "").split())
        manifest[item_id] = {
            "href": _resolve_opf_href(opf_dir, href),
            "media_type": item.attrib.get("media-type", ""),
            "properties": properties,
        }
    return manifest


def _find_metadata_cover_id(opf_root: ET.Element) -> str | None:
    metadata = opf_root.find("opf:metadata", OPF_NAMESPACES)
    if metadata is None:
        return None
    for node in metadata.findall("opf:meta", OPF_NAMESPACES):
        if node.attrib.get("name") == "cover":
            return node.attrib.get("content")
    return None


def _cover_from_manifest(
    zf: ZipFile,
    manifest: dict[str, dict[str, str | set[str]]],
    item_id: str,
) -> CoverAsset | None:
    item = manifest.get(item_id)
    if item is None:
        return None
    media_type = str(item["media_type"])
    if media_type not in IMAGE_MEDIA_TYPES:
        return None
    href = str(item["href"])
    return CoverAsset(href=href, media_type=media_type, content=zf.read(href))


def _find_cover_like_manifest_item(
    zf: ZipFile,
    manifest: dict[str, dict[str, str | set[str]]],
) -> CoverAsset | None:
    for item_id, item in manifest.items():
        href = str(item["href"]).lower()
        media_type = str(item["media_type"])
        if media_type not in IMAGE_MEDIA_TYPES:
            continue
        if item_id.lower() in COVER_HINTS or any(hint in href for hint in COVER_HINTS):
            return CoverAsset(href=str(item["href"]), media_type=media_type, content=zf.read(str(item["href"])))
    return None


def _find_frontmatter_cover(
    zf: ZipFile,
    manifest: dict[str, dict[str, str | set[str]]],
    spine: ET.Element,
) -> CoverAsset | None:
    for itemref in spine.findall("opf:itemref", OPF_NAMESPACES):
        item_id = itemref.attrib.get("idref", "")
        item = manifest.get(item_id)
        if item is None or str(item["media_type"]) != XHTML_MEDIA_TYPE:
            continue
        href = str(item["href"])
        soup = BeautifulSoup(zf.read(href).decode("utf-8", errors="replace"), "html.parser")
        image = soup.find("img")
        if image is None or not image.get("src"):
            continue
        image_href = _resolve_relative_href(posixpath.dirname(href), image["src"])
        for manifest_item in manifest.values():
            if str(manifest_item["href"]) == image_href and str(manifest_item["media_type"]) in IMAGE_MEDIA_TYPES:
                return CoverAsset(
                    href=image_href,
                    media_type=str(manifest_item["media_type"]),
                    content=zf.read(image_href),
                )
    return None
```

- [ ] **Step 4: Run EPUB I/O tests**

Run:

```bash
PYTHONPATH=scripts python3 -m unittest tests.test_epub_io -v
```

Expected: all EPUB I/O tests pass, including the new cover tests.

- [ ] **Step 5: Commit the EPUB cover extractor**

```bash
git add scripts/custom_epub/epub_io.py tests/test_epub_io.py
git commit -m "Add reusable EPUB cover extraction"
```

Expected: commit succeeds and includes only the two files above.

### Task 2: Wire Cover Inheritance Into The Builder

**Files:**
- Modify: `scripts/custom_epub/builder.py`
- Modify: `tests/test_builder_smoke.py`

- [ ] **Step 1: Write failing builder cover assertions**

Extend `tests/test_builder_smoke.py` so the minimal fixture includes a source cover, and then assert the output EPUB contains it.

Update the test fixture helper:

```python
def make_minimal_epub(
    path: Path,
    label: str,
    href: str,
    paragraph: str,
    *,
    cover_bytes: bytes | None = None,
    cover_href: str = "Images/cover.jpg",
    include_cover_meta: bool = True,
) -> None:
    meta_cover = '<meta name="cover" content="cover"/>' if include_cover_meta else ""
    cover_manifest = (
        f'<item id="cover" href="{cover_href}" media-type="image/jpeg"/>'
        if cover_bytes is not None
        else ""
    )
    with ZipFile(path, "w") as zf:
        zf.writestr("mimetype", "application/epub+zip")
        zf.writestr(
            "META-INF/container.xml",
            """<?xml version="1.0"?>
<container xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles><rootfile full-path="OEBPS/content.opf"/></rootfiles></container>""",
        )
        zf.writestr(
            "OEBPS/content.opf",
            f"""<package xmlns="http://www.idpf.org/2007/opf" version="2.0">
<metadata>{meta_cover}</metadata>
<manifest><item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>{cover_manifest}<item id="ch1" href="{href}" media-type="application/xhtml+xml"/></manifest>
<spine toc="ncx"><itemref idref="ch1"/></spine></package>""",
        )
        ...
        if cover_bytes is not None:
            zf.writestr(f"OEBPS/{cover_href}", cover_bytes)
```

Call it with an English cover:

```python
            make_minimal_epub(
                books / "en.epub",
                "Chapter One",
                "Text/ch1.xhtml",
                "English text.",
                cover_bytes=b"english-cover",
            )
```

Then assert the output EPUB contains the inherited cover:

```python
            with ZipFile(result.output_epub) as zf:
                names = zf.namelist()
                self.assertIn("EPUB/cover.jpg", names)
                self.assertEqual(zf.read("EPUB/cover.jpg"), b"english-cover")
                package = zf.read("EPUB/content.opf").decode("utf-8")
                self.assertIn("cover.jpg", package)
```

Add a second test for Chinese fallback:

```python
    def test_build_project_falls_back_to_chinese_cover_when_english_has_none(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            books = root / "books" / "Fallback"
            project_dir = root / "book_projects" / "fallback"
            books.mkdir(parents=True)
            project_dir.mkdir(parents=True)
            make_minimal_epub(
                books / "en.epub",
                "Chapter One",
                "Text/ch1.xhtml",
                "English text.",
                cover_bytes=None,
                include_cover_meta=False,
            )
            make_minimal_epub(
                books / "zh.epub",
                "第一章",
                "Text/zh1.xhtml",
                "中文正文。",
                cover_bytes=b"chinese-cover",
            )
            ...
            result = build_project(project_dir, root)
            with ZipFile(result.output_epub) as zf:
                self.assertEqual(zf.read("EPUB/cover.jpg"), b"chinese-cover")
```

- [ ] **Step 2: Run the builder tests to verify they fail**

Run:

```bash
PYTHONPATH=scripts python3 -m unittest tests.test_builder_smoke -v
```

Expected: `FAIL` because the builder does not attach any inherited cover yet.

- [ ] **Step 3: Implement the builder cover wiring**

Update the imports in `scripts/custom_epub/builder.py`:

```python
from .epub_io import extract_cover_asset, extract_href_fragment, read_container_path
```

Add a helper:

```python
def _inherited_cover(project: BookProject) -> tuple[str, bytes] | None:
    english_cover = extract_cover_asset(project.english_epub)
    if english_cover is not None:
        return posixpath.basename(english_cover.href), english_cover.content

    if project.chinese_epub is not None:
        chinese_cover = extract_cover_asset(project.chinese_epub)
        if chinese_cover is not None:
            return posixpath.basename(chinese_cover.href), chinese_cover.content

    return None
```

Then wire it into `build_project()` after metadata and before writing the EPUB:

```python
    warnings: list[str] = []

    inherited_cover = _inherited_cover(project)
    if inherited_cover is not None:
        cover_name, cover_bytes = inherited_cover
        book.set_cover(cover_name, cover_bytes, create_page=False)
    else:
        warnings.append("No source cover could be extracted from the English or Chinese EPUB.")
```

Return the warnings list:

```python
    return BuildResult(
        output_epub=project.output_epub,
        pairing_map=project.pairing_map,
        warnings=warnings,
    )
```

- [ ] **Step 4: Run builder and full test suite**

Run:

```bash
PYTHONPATH=scripts python3 -m unittest tests.test_builder_smoke -v
PYTHONPATH=scripts python3 -m unittest discover -s tests -v
```

Expected: all tests pass, including English-preferred and Chinese-fallback cover inheritance.

- [ ] **Step 5: Commit the builder cover inheritance**

```bash
git add scripts/custom_epub/builder.py tests/test_builder_smoke.py
git commit -m "Inherit source covers in customized EPUBs"
```

Expected: commit succeeds and includes only the two files above.

### Task 3: Update The Agent Guide And Rebuild Animal Farm

**Files:**
- Modify: `AGENTS.md`
- Verify: `output/Animal Farm/Animal Farm - Customized Bilingual Companion.epub`

- [ ] **Step 1: Update the guide**

Add one explicit sentence to `AGENTS.md` under `## Reusable Framework Workflow`, after the existing paragraph about reusable mechanics:

```markdown
Customized EPUBs should inherit the source-book cover by default: prefer the English source cover, and fall back to the Chinese source cover only if the English cover cannot be extracted.
```

Do not add provenance narration to the listening-content sections.

- [ ] **Step 2: Verify the guide text**

Run:

```bash
rg -n "inherit the source-book cover|English source cover|Chinese source cover" AGENTS.md
```

Expected: one matching line with the new rule.

- [ ] **Step 3: Rebuild Animal Farm**

The worktree needs temporary access to the root `books/` directory:

```bash
ln -s /Users/luojiaxing/Code/cc-customized-books/books books
PYTHONPATH=scripts python3 scripts/build_custom_epub.py book_projects/animal-farm
unlink books
```

Expected:

```text
EPUB: /Users/luojiaxing/Code/cc-customized-books/.worktrees/reusable-epub-framework/output/Animal Farm/Animal Farm - Customized Bilingual Companion.epub
Pairing map: /Users/luojiaxing/Code/cc-customized-books/.worktrees/reusable-epub-framework/output/Animal Farm/pairing-map.md
```

- [ ] **Step 4: Verify the rebuilt EPUB contains a cover**

Run:

```bash
python3 - <<'PY'
from pathlib import Path
from zipfile import ZipFile

epub_path = Path("output/Animal Farm/Animal Farm - Customized Bilingual Companion.epub")
with ZipFile(epub_path) as zf:
    names = set(zf.namelist())
    package = zf.read("EPUB/content.opf").decode("utf-8", errors="replace")
cover_candidates = sorted(name for name in names if "cover" in name.lower())
print("cover-candidates:", cover_candidates)
print("opf-has-cover:", "cover" in package.lower())
raise SystemExit(1 if not cover_candidates else 0)
PY
```

Expected:

```text
cover-candidates: [...]
opf-has-cover: True
```

- [ ] **Step 5: Commit the guide and rebuilt artifact**

```bash
git add AGENTS.md output/Animal\ Farm/Animal\ Farm\ -\ Customized\ Bilingual\ Companion.epub
git commit -m "Preserve source covers in customized EPUBs"
```

Expected: commit succeeds and includes only the guide plus rebuilt Animal Farm EPUB.

## Self-Review

- Spec coverage:
  - English-first cover inheritance: Task 2
  - Chinese fallback: Task 2
  - Reusable extraction helpers: Task 1
  - Listening flow unchanged and no provenance narration: Task 3
  - Animal Farm rebuilt and verified: Task 3
- Placeholder scan:
  - No unfinished markers or deferred implementation notes remain.
- Type consistency:
  - All paths and function names match the current branch: `extract_cover_asset`, `build_project`, `tests.test_epub_io`, `tests.test_builder_smoke`, `AGENTS.md`.
