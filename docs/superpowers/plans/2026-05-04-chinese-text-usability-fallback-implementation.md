# Chinese Text Usability Fallback Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the builder use real readable Chinese text only, fall back chapter-by-chapter to agent-authored Chinese translation when the Chinese source is image-only or unreadable, and repair the current `Animal Farm` EPUB.

**Architecture:** Add a chapter-text usability check in `epub_io.py`, extend the companion schema so each chapter can carry agent-authored Chinese fallback text plus its provenance, and update the builder to choose between source Chinese and generated Chinese per chapter. Then migrate `Animal Farm` so all ten chapter Chinese bodies use generated translation instead of the image-only source pages, rebuild the EPUB, and verify the output contains real chapter prose rather than image-only markup.

**Tech Stack:** Python 3, `unittest`, `ebooklib`, `BeautifulSoup`, JSON companion data in `book_projects/`, existing `scripts/custom_epub` builder/render/model modules.

---

## File Structure

- `scripts/custom_epub/epub_io.py`
  - Responsibility: extract and analyze source chapter fragments. This is where chapter-level Chinese usability detection should live.
- `tests/test_epub_io.py`
  - Responsibility: lock the usability detector against readable text, image-only chapters, and obvious OCR-like garbage.
- `scripts/custom_epub/models.py`
  - Responsibility: load structured per-chapter Chinese fallback metadata and agent-authored translation text from `companion.json`.
- `tests/test_models.py`
  - Responsibility: verify the new chapter Chinese payload parses cleanly and rejects malformed values.
- `scripts/custom_epub/builder.py`
  - Responsibility: choose chapter Chinese content source, use generated translation when required, and stop treating image-only Chinese pages as valid listening content.
- `tests/test_builder_smoke.py`
  - Responsibility: verify builder-level fallback behavior end to end and ensure generated Chinese text appears in the EPUB when the source chapter is unusable.
- `book_projects/animal-farm/companion.json`
  - Responsibility: hold the actual chapter-level generated Chinese translations and per-chapter source mode metadata for `Animal Farm`.
- `AGENTS.md`
  - Responsibility: tell future agents never to use image-only or OCR-garbage Chinese as listening text, and to provide generated Chinese fallback instead.
- `output/Animal Farm/Animal Farm - Customized Bilingual Companion.epub`
  - Responsibility: rebuilt verification artifact containing real readable Chinese chapter bodies.

### Task 1: Add Chapter Chinese Usability Detection

**Files:**
- Modify: `tests/test_epub_io.py`
- Modify: `scripts/custom_epub/epub_io.py`

- [ ] **Step 1: Write failing usability tests**

Add these tests to `tests/test_epub_io.py`:

```python
    def test_assess_chinese_chapter_text_marks_image_only_fragment_unusable(self):
        fragment = '<p class="center"><img alt="" src="../Images/page001.jpeg"/></p>'

        usability = assess_chinese_chapter_text(fragment)

        self.assertEqual(usability.kind, "image_only")
        self.assertFalse(usability.is_usable)

    def test_assess_chinese_chapter_text_accepts_real_chinese_prose(self):
        fragment = "<div><p>动物们一齐向前冲去，谁也不再等待命令。</p></div>"

        usability = assess_chinese_chapter_text(fragment)

        self.assertEqual(usability.kind, "readable_text")
        self.assertTrue(usability.is_usable)

    def test_assess_chinese_chapter_text_rejects_ocr_garbage(self):
        fragment = "<div><p>动 物 农 场 口 号 7 诫 0 0 0 l I 1 口 口 口</p></div>"

        usability = assess_chinese_chapter_text(fragment)

        self.assertEqual(usability.kind, \"unreadable_ocr\")
        self.assertFalse(usability.is_usable)
```

Import the new helper at the top of the file:

```python
from custom_epub.epub_io import assess_chinese_chapter_text, ...
```

- [ ] **Step 2: Run the targeted tests to verify they fail**

Run:

```bash
PYTHONPATH=scripts python3 -m unittest \
  tests.test_epub_io.EpubIoTests.test_assess_chinese_chapter_text_marks_image_only_fragment_unusable \
  tests.test_epub_io.EpubIoTests.test_assess_chinese_chapter_text_accepts_real_chinese_prose \
  tests.test_epub_io.EpubIoTests.test_assess_chinese_chapter_text_rejects_ocr_garbage -v
```

Expected: `ERROR` because `assess_chinese_chapter_text` does not exist yet.

- [ ] **Step 3: Implement the detector in `epub_io.py`**

Add a small dataclass near the top of `scripts/custom_epub/epub_io.py`:

```python
@dataclass(frozen=True)
class ChapterTextUsability:
    kind: str
    is_usable: bool
```

Then add the helper:

```python
def assess_chinese_chapter_text(fragment_html: str) -> ChapterTextUsability:
    soup = BeautifulSoup(fragment_html, "html.parser")
    images = soup.find_all("img")
    visible_text = soup.get_text(" ", strip=True)

    if images and not visible_text:
        return ChapterTextUsability(kind="image_only", is_usable=False)

    chinese_chars = sum(1 for ch in visible_text if "\u4e00" <= ch <= "\u9fff")
    latin_or_digits = sum(1 for ch in visible_text if ch.isascii() and ch.isalnum())
    compact_text = "".join(ch for ch in visible_text if not ch.isspace())

    if chinese_chars >= 24:
        density = chinese_chars / max(len(compact_text), 1)
        if density >= 0.35:
            return ChapterTextUsability(kind="readable_text", is_usable=True)

    if chinese_chars > 0 and latin_or_digits > chinese_chars:
        return ChapterTextUsability(kind="unreadable_ocr", is_usable=False)

    if chinese_chars == 0:
        return ChapterTextUsability(kind="missing_text", is_usable=False)

    return ChapterTextUsability(kind="unreadable_ocr", is_usable=False)
```

This heuristic is intentionally conservative: only clearly readable Chinese passes. Questionable text fails and must be replaced by translation rather than smuggled into the listening EPUB.

- [ ] **Step 4: Run all EPUB I/O tests**

Run:

```bash
PYTHONPATH=scripts python3 -m unittest tests.test_epub_io -v
```

Expected: all EPUB I/O tests pass.

- [ ] **Step 5: Commit the usability detector**

```bash
git add tests/test_epub_io.py scripts/custom_epub/epub_io.py
git commit -m "Detect unusable Chinese chapter text"
```

Expected: commit succeeds and includes only the detector and its tests.

### Task 2: Extend The Companion Schema For Chapter-Level Chinese Fallback

**Files:**
- Modify: `tests/test_models.py`
- Modify: `scripts/custom_epub/models.py`

- [ ] **Step 1: Write the failing model test**

Add this test to `tests/test_models.py`:

```python
    def test_load_companion_supports_generated_chinese_chapter_text(self):
        with tempfile.TemporaryDirectory() as tmp:
            project_dir = Path(tmp)
            (project_dir / "companion.json").write_text(
                json.dumps(
                    {
                        "book": {
                            "companion_zh": "中文导读",
                            "summary_en": "English guide",
                            "references": [],
                        },
                        "chapters": [
                            {
                                "english_label": "Chapter One",
                                "listening_brief": {
                                    "names": "Old Major",
                                    "points": ["Listen for the speech."],
                                    "context": "Opening chapter.",
                                },
                                "companion": {
                                    "zh": "中文章节导读",
                                    "en": "English chapter summary.",
                                    "priority": "Read closely.",
                                },
                                "chinese_text": {
                                    "mode": "generated_translation",
                                    "content": "第一段中文译文。\n\n第二段中文译文。",
                                    "reason": "image_only_source",
                                },
                                "vocabulary": {
                                    "Must know": ["comrade, noun, 同志。"],
                                    "Useful / high-value": [],
                                    "Specialized or context-bound": [],
                                },
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            companion = load_companion(project_dir)

            self.assertEqual(
                companion.chapters[0].chinese_text.mode,
                "generated_translation",
            )
            self.assertEqual(
                companion.chapters[0].chinese_text.reason,
                "image_only_source",
            )
            self.assertIn("第一段中文译文", companion.chapters[0].chinese_text.content)
```

- [ ] **Step 2: Run the targeted model test to verify it fails**

Run:

```bash
PYTHONPATH=scripts python3 -m unittest tests.test_models.ModelLoadingTests.test_load_companion_supports_generated_chinese_chapter_text -v
```

Expected: `ERROR` or `FAIL` because the chapter schema does not yet include `chinese_text`.

- [ ] **Step 3: Add the new dataclass and loader support**

In `scripts/custom_epub/models.py`, add:

```python
@dataclass(frozen=True)
class ChapterChineseText:
    mode: str
    content: str
    reason: str
```

Extend `CompanionChapter`:

```python
@dataclass(frozen=True)
class CompanionChapter:
    english_label: str
    listening_brief: ListeningBrief
    companion: ChapterCompanion
    vocabulary: dict[str, list[str]]
    recap: Recap | None
    key_chapter: bool = False
    mini_lecture: MiniLecture | None = None
    chinese_text: ChapterChineseText | None = None
```

Then parse the new field inside `load_companion()`:

```python
        chinese_text_data = row.get("chinese_text")
        chinese_text = None
        if chinese_text_data is not None:
            chinese_text = ChapterChineseText(
                mode=chinese_text_data["mode"],
                content=chinese_text_data["content"],
                reason=chinese_text_data["reason"],
            )
```

And wire `chinese_text=chinese_text` into `CompanionChapter(...)`.

- [ ] **Step 4: Run all model tests**

Run:

```bash
PYTHONPATH=scripts python3 -m unittest tests.test_models -v
```

Expected: all model tests pass.

- [ ] **Step 5: Commit the schema extension**

```bash
git add tests/test_models.py scripts/custom_epub/models.py
git commit -m "Add chapter-level Chinese fallback schema"
```

Expected: commit succeeds and includes only the model change and tests.

### Task 3: Use Generated Chinese Fallback In The Builder

**Files:**
- Modify: `tests/test_builder_smoke.py`
- Modify: `scripts/custom_epub/builder.py`

- [ ] **Step 1: Write the failing builder test**

Update the image-only chapter smoke test in `tests/test_builder_smoke.py` so it expects generated Chinese text to be rendered instead of the source image:

```python
            (project_dir / "companion.json").write_text(
                json.dumps(
                    {
                        "book": {
                            "companion_zh": "中文导读",
                            "summary_en": "English summary.",
                            "references": [],
                        },
                        "chapters": [
                            {
                                "english_label": "Chapter One",
                                "listening_brief": {
                                    "names": "Name",
                                    "points": ["Listen for contrast."],
                                    "context": "Context.",
                                },
                                "companion": {
                                    "zh": "中文伴读",
                                    "en": "English companion.",
                                    "priority": "Read closely.",
                                },
                                "chinese_text": {
                                    "mode": "generated_translation",
                                    "content": "这是代理生成的中文译文。\n\n它应该出现在中文章节正文里。",
                                    "reason": "image_only_source",
                                },
                                "vocabulary": {
                                    "Must know": ["contrast, noun, 对比。"],
                                    "Useful / high-value": [],
                                    "Specialized or context-bound": [],
                                },
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
```

And change the assertions to:

```python
            self.assertNotIn("Chinese chapter '第一章' is image-only", result.warnings)
            self.assertNotIn("EPUB/assets/ch01-zh-01.png", names)
            self.assertIn("这是代理生成的中文译文。", zh_page)
            self.assertIn("它应该出现在中文章节正文里。", zh_page)
            self.assertNotIn("<img", zh_page)
```

This test should now prove the builder prefers agent-authored generated Chinese over scan-image fallback.

- [ ] **Step 2: Run the targeted builder test to verify it fails**

Run:

```bash
PYTHONPATH=scripts python3 -m unittest tests.test_builder_smoke.BuilderSmokeTests.test_build_project_embeds_assets_for_image_only_chinese_chapters -v
```

Expected: `FAIL` because the builder still emits the image-based fragment.

- [ ] **Step 3: Implement chapter-level source selection in `builder.py`**

Add a helper in `scripts/custom_epub/builder.py`:

```python
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
        f"Chinese chapter '{pairing.chinese_label or pairing.english_label}' is {usability.kind} and no generated translation is provided."
    )
```

Update imports:

```python
from .epub_io import (
    assess_chinese_chapter_text,
    extract_cover_asset,
    extract_href_fragment,
    read_container_path,
)
from .render import (
    load_css,
    paragraphs,
    render_book_companion,
    render_chapter_pages,
    section_file_names,
)
```

Then replace the current Chinese fragment block inside `build_project()` with:

```python
        chinese_fragment, chinese_resolution_warnings = _resolve_chinese_chapter_body(
            book,
            chapter,
            project,
            pairing,
            index,
        )
        warnings.extend(english_warnings)
        warnings.extend(chinese_resolution_warnings)
```

And remove the old unconditional image-warning behavior for Chinese scan pages. Once generated fallback is provided, that case is handled as valid content selection rather than a shipped warning.

- [ ] **Step 4: Run builder smoke tests**

Run:

```bash
PYTHONPATH=scripts python3 -m unittest tests.test_builder_smoke -v
```

Expected: all builder smoke tests pass, including the generated Chinese fallback test.

- [ ] **Step 5: Commit the builder fallback logic**

```bash
git add tests/test_builder_smoke.py scripts/custom_epub/builder.py
git commit -m "Fallback to generated Chinese chapter text"
```

Expected: commit succeeds and includes only the builder + smoke test changes.

### Task 4: Migrate Animal Farm To Generated Chinese Chapter Text

**Files:**
- Modify: `book_projects/animal-farm/companion.json`
- Modify: `AGENTS.md`

- [ ] **Step 1: Add chapter-level generated Chinese blocks for all ten main chapters**

For each chapter in `book_projects/animal-farm/companion.json`, add:

```json
"chinese_text": {
  "mode": "generated_translation",
  "content": "完整的、忠实且适合朗读的中文章节译文，按段落用空行分隔。",
  "reason": "image_only_source"
}
```

Apply this to:

- `Chapter One`
- `Chapter Two`
- `Chapter Three`
- `Chapter Four`
- `Chapter Five`
- `Chapter Six`
- `Chapter Seven`
- `Chapter Eight`
- `Chapter Nine`
- `Chapter Ten`

Author the Chinese text as real chapter prose, not summary notes and not OCR salvage. The translation should preserve plot, tone, argument, and narrative progression closely enough to support side-by-side listening with the English chapter.

- [ ] **Step 2: Add a validation probe for the migrated Animal Farm content**

Run:

```bash
PYTHONPATH=scripts python3 - <<'PY'
from pathlib import Path
from custom_epub.models import load_companion

companion = load_companion(Path("book_projects/animal-farm"))
for chapter in companion.chapters[:2]:
    print(chapter.english_label, chapter.chinese_text.mode, chapter.chinese_text.reason)
    print(chapter.chinese_text.content[:40])
PY
```

Expected:

```text
Chapter One generated_translation image_only_source
...
Chapter Two generated_translation image_only_source
...
```

- [ ] **Step 3: Update `AGENTS.md` with the non-OCR fallback rule**

Add this paragraph under `## Translation When Chinese Is Missing`:

```markdown
For listening EPUBs, treat image-only Chinese chapters and unreadable OCR-like Chinese chapters as missing Chinese text. Do not use scan images or OCR garbage as the main Chinese chapter body. Instead, provide faithful, readable Chinese translation from the English chapter and use that as the Chinese chapter in the listening flow.
```

And add this sentence under `## Core Workflow` after step 8:

```markdown
If a Chinese chapter exists but is unusable for listening, replace it with agent-authored Chinese translation from the English chapter rather than using scan images or OCR salvage.
```

- [ ] **Step 4: Commit the Animal Farm content migration**

```bash
git add book_projects/animal-farm/companion.json AGENTS.md
git commit -m "Use generated Chinese text for image-only chapters"
```

Expected: commit succeeds and includes only the content migration plus guidance update.

- [ ] **Step 5: Note the translation scope for reviewers**

Before moving to Task 5, add this note to the implementation review summary or PR description:

```text
Animal Farm now uses agent-authored generated Chinese chapter text for all ten main chapters because the source Chinese EPUB chapter bodies are image-only scans rather than readable text.
```

No code change is required for this step; it is an explicit review note so nobody mistakes the generated Chinese content for extracted source text.

### Task 5: Rebuild And Verify The Real Animal Farm EPUB

**Files:**
- Verify: `output/Animal Farm/Animal Farm - Customized Bilingual Companion.epub`
- Verify: `tests/test_epub_io.py`
- Verify: `tests/test_models.py`
- Verify: `tests/test_builder_smoke.py`

- [ ] **Step 1: Run the full automated test suite**

Run:

```bash
PYTHONPATH=scripts python3 -m unittest discover -s tests -v
```

Expected: all tests pass.

- [ ] **Step 2: Rebuild the real Animal Farm EPUB**

Run:

```bash
PYTHONPATH=scripts python3 scripts/build_custom_epub.py book_projects/animal-farm
```

Expected: build succeeds and writes:

- `output/Animal Farm/Animal Farm - Customized Bilingual Companion.epub`

If the old pairing-map output still exists at this point, do not expand scope here. That cleanup belongs to the separate pairing-map removal work.

- [ ] **Step 3: Verify the rebuilt Chinese chapter pages contain text, not images**

Run:

```bash
python3 - <<'PY'
from pathlib import Path
from zipfile import ZipFile

epub_path = Path("output/Animal Farm/Animal Farm - Customized Bilingual Companion.epub")
with ZipFile(epub_path) as zf:
    for name in ["EPUB/ch01-zh.xhtml", "EPUB/ch05-zh.xhtml", "EPUB/ch10-zh.xhtml"]:
        page = zf.read(name).decode("utf-8")
        print(name, "<img" in page, "English source text from" in page)
        print(page[:220])
PY
```

Expected:

```text
EPUB/ch01-zh.xhtml False False
EPUB/ch05-zh.xhtml False False
EPUB/ch10-zh.xhtml False False
```

And the page snippets should contain actual Chinese prose rather than only `<img>` tags.

- [ ] **Step 4: Verify the generated Chinese text is present as real prose**

Run:

```bash
python3 - <<'PY'
from pathlib import Path
from zipfile import ZipFile
from bs4 import BeautifulSoup

epub_path = Path("output/Animal Farm/Animal Farm - Customized Bilingual Companion.epub")
with ZipFile(epub_path) as zf:
    for name in ["EPUB/ch01-zh.xhtml", "EPUB/ch05-zh.xhtml", "EPUB/ch10-zh.xhtml"]:
        page = zf.read(name).decode("utf-8")
        soup = BeautifulSoup(page, "html.parser")
        text = soup.get_text(" ", strip=True)
        print(name, len(text), "<img" in page)
PY
```

Expected:

```text
EPUB/ch01-zh.xhtml <length greater than 400> False
EPUB/ch05-zh.xhtml <length greater than 400> False
EPUB/ch10-zh.xhtml <length greater than 400> False
```

The exact lengths may vary, but each chapter page should contain substantial Chinese text and no image tag.

- [ ] **Step 5: Commit the rebuilt EPUB if it changed**

```bash
git add "output/Animal Farm/Animal Farm - Customized Bilingual Companion.epub"
git commit -m "Rebuild Animal Farm with readable Chinese chapters"
```

Expected: commit succeeds only if the rebuilt artifact changed. If the EPUB content is byte-identical after previous commits, skip this commit.
