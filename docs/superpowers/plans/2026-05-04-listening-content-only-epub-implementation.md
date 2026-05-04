# Listening Content-Only EPUB Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove listening-noise metadata from the main EPUB flow so the customized book talks only about the book itself, while keeping pairing maps and similar audit material as sidecar outputs.

**Architecture:** Keep the current reusable framework structure. Tighten the renderer so book-level reference lists are not emitted into the listening EPUB, tighten smoke/render tests so they guard against future regressions, scrub the Animal Farm companion content so it no longer narrates pairing/additional-material notes, and update `AGENTS.md` so future agents default to content-only listening editions.

**Tech Stack:** Python 3, `unittest`, `ebooklib`, existing `scripts/custom_epub` renderer/builder modules, JSON project content files, Markdown guide docs.

---

## File Structure

- `scripts/custom_epub/render.py`
  - Responsibility: render listening-facing XHTML pages. This is where book companion output must stop emitting references or artifact-oriented blocks.
- `tests/test_render.py`
  - Responsibility: lock the renderer contract so book companion output is content-only.
- `tests/test_builder_smoke.py`
  - Responsibility: verify the generated EPUB does not include reference/provenance noise in listener-facing XHTML, while still producing sidecar pairing output.
- `book_projects/animal-farm/companion.json`
  - Responsibility: Animal Farm book/chapter learning content. This needs a content-only cleanup in the book companion text.
- `AGENTS.md`
  - Responsibility: agent operating manual. This must explicitly instruct future agents to keep the listening EPUB content-only and move audit/reference material outside the main EPUB.
- `output/Animal Farm/Animal Farm - Customized Bilingual Companion.epub`
  - Responsibility: regenerated verification artifact.
- `output/Animal Farm/pairing-map.md`
  - Responsibility: sidecar artifact that should remain available outside the listening EPUB.

### Task 1: Lock The Content-Only Renderer Contract

**Files:**
- Modify: `tests/test_render.py`
- Modify: `scripts/custom_epub/render.py`

- [ ] **Step 1: Write the failing renderer assertion**

Update `tests/test_render.py` so the book companion test proves that reference material is not rendered into the listening EPUB:

```python
    def test_render_book_companion_omits_reference_section_from_listening_epub(self):
        companion = BookCompanion(
            companion_zh="中文导读",
            summary_en="English guide.",
            references=[
                {
                    "label": "Publisher page",
                    "url": "https://example.com/publisher",
                }
            ],
        )

        rendered = render_book_companion("Sample", companion)

        self.assertIn("Book Companion", rendered)
        self.assertIn("中文导读", rendered)
        self.assertIn("English Summary", rendered)
        self.assertNotIn("References For Visual Review", rendered)
        self.assertNotIn("Publisher page", rendered)
        self.assertNotIn("https://example.com/publisher", rendered)
```

Replace the older `test_render_book_companion_uses_labels_not_raw_urls` with this stricter version.

- [ ] **Step 2: Run the targeted render test to verify it fails**

Run:

```bash
PYTHONPATH=scripts python3 -m unittest tests.test_render.RenderTests.test_render_book_companion_omits_reference_section_from_listening_epub -v
```

Expected: `FAIL` because `render_book_companion()` still emits `References For Visual Review` and the reference label.

- [ ] **Step 3: Write the minimal renderer change**

Update `scripts/custom_epub/render.py` so `render_book_companion()` no longer renders any reference list:

```python
def render_book_companion(title: str, companion: BookCompanion) -> str:
    return html_page(
        "Book Companion",
        f"""
<p class="eyebrow">Book Companion</p>
<h1>{html.escape(title)} / Book Companion</h1>
{paragraphs(companion.companion_zh)}
<h2>English Summary</h2>
<div class="english-summary"><p>{html.escape(companion.summary_en)}</p></div>
""",
    )
```

Do not remove the labeled structure. Only remove the listening-facing reference block.

- [ ] **Step 4: Run render tests to verify they pass**

Run:

```bash
PYTHONPATH=scripts python3 -m unittest tests.test_render -v
```

Expected: all render tests pass.

- [ ] **Step 5: Commit the renderer contract change**

```bash
git add tests/test_render.py scripts/custom_epub/render.py
git commit -m "Remove references from listening book companion"
```

Expected: commit succeeds and includes only the two files above.

### Task 2: Strengthen End-To-End Listening-Noise Guards

**Files:**
- Modify: `tests/test_builder_smoke.py`

- [ ] **Step 1: Write stricter failing smoke assertions**

Extend `tests/test_builder_smoke.py` so the generated EPUB must not contain reference or provenance noise in listener-facing XHTML:

```python
            self.assertIn("Chapter 1 Listening Brief", xhtml)
            self.assertIn("Chapter 1 Companion Reference", xhtml)
            self.assertNotIn("https://", xhtml)
            self.assertNotIn("References For Visual Review", xhtml)
            self.assertNotIn("Publisher page", xhtml)
            self.assertNotIn("English source text from", xhtml)
            self.assertNotIn("Chinese source text from", xhtml)
```

Also keep the sidecar requirement explicit:

```python
            pairing_map_text = result.pairing_map.read_text(encoding="utf-8")
            self.assertIn("# Sample Pairing Map", pairing_map_text)
```

- [ ] **Step 2: Run the smoke test to verify it fails**

Run:

```bash
PYTHONPATH=scripts python3 -m unittest tests.test_builder_smoke -v
```

Expected: `FAIL` because the renderer currently places reference content into `book-companion.xhtml`.

- [ ] **Step 3: Re-run the smoke test after Task 1 changes**

Run:

```bash
PYTHONPATH=scripts python3 -m unittest tests.test_builder_smoke -v
```

Expected: `PASS` once the renderer no longer emits the reference section.

- [ ] **Step 4: Run the full suite**

Run:

```bash
PYTHONPATH=scripts python3 -m unittest discover -s tests -v
```

Expected: all tests pass.

- [ ] **Step 5: Commit the stronger smoke guard**

```bash
git add tests/test_builder_smoke.py
git commit -m "Add content-only listening EPUB smoke checks"
```

Expected: commit succeeds and includes only `tests/test_builder_smoke.py`.

### Task 3: Scrub Animal Farm Book Companion Content

**Files:**
- Modify: `book_projects/animal-farm/companion.json`

- [ ] **Step 1: Remove book-level build/artifact narration**

Edit the `book.companion_zh` field in `book_projects/animal-farm/companion.json` so it no longer includes the artifact-oriented section:

```text
章节配对与增补说明
中文源本另含《译本序》和《动物农场》乌克兰文版序。二者都保留为可跳过的参考材料。中文版权信息页只含出版元数据，因此不放进听读主流程。
```

The revised `companion_zh` should end after the pacing/listening guidance and should remain entirely about the book itself.

- [ ] **Step 2: Verify the JSON still loads**

Run:

```bash
PYTHONPATH=scripts python3 - <<'PY'
from pathlib import Path
from custom_epub.models import load_companion
companion = load_companion(Path("book_projects/animal-farm"))
print(companion.book.companion_zh.splitlines()[-1])
PY
```

Expected: the last printed line is the final pacing/listening sentence, not `章节配对与增补说明`.

- [ ] **Step 3: Commit the content scrub**

```bash
git add book_projects/animal-farm/companion.json
git commit -m "Remove listening-noise notes from Animal Farm companion"
```

Expected: commit succeeds and includes only `book_projects/animal-farm/companion.json`.

### Task 4: Update Agent Guidance And Rebuild Animal Farm

**Files:**
- Modify: `AGENTS.md`
- Verify: `output/Animal Farm/Animal Farm - Customized Bilingual Companion.epub`
- Verify: `output/Animal Farm/pairing-map.md`

- [ ] **Step 1: Update the guide to make content-only listening explicit**

Adjust `AGENTS.md` in these sections:

1. In `## Required Output`, change the book-level bullet from:

```markdown
- Recommended book-level outside research with deep insights and readable source labels.
```

to:

```markdown
- Recommended book-level outside research with deep insights that stay focused on the book itself.
```

2. In `## Book-Level Companion Standards`, replace:

```markdown
- References and further reading with human-readable source labels.
```

with:

```markdown
- Listening-focused guidance that stays on the book itself rather than the artifact.
```

3. Immediately after the sentence `The book-level companion should be substantial and bilingual. Put the main explanation in Chinese first, then add a concise English summary.`, add:

```markdown
For listening EPUBs, keep the Book Companion content-only. Do not include references lists, pairing explanations, edition-handling notes, provenance notes, or build-process explanations inside the main EPUB.
```

4. In `## Chapter Companion Standards`, after the paragraph that describes the deeper companion reference, add:

```markdown
Do not add source-edition descriptions or provenance text such as `English source text from ...` or `Chinese source text from ...` inside the chapter flow unless the user explicitly asks for an audit/study edition.
```

5. In `## Reusable Framework Workflow`, after the four-step list, add:

```markdown
The main listening EPUB should contain only book-relevant learning content and source text. Pairing maps, references, edition notes, and provenance details belong in sidecar artifacts or final reports, not in the listening flow.
```

- [ ] **Step 2: Rebuild the Animal Farm EPUB**

The worktree needs access to the root `books/` inputs. Create a temporary symlink, build, then remove it:

```bash
ln -s /Users/luojiaxing/Code/cc-customized-books/books books
PYTHONPATH=scripts python3 scripts/build_custom_epub.py book_projects/animal-farm
unlink books
```

Expected build output:

```text
EPUB: /Users/luojiaxing/Code/cc-customized-books/.worktrees/reusable-epub-framework/output/Animal Farm/Animal Farm - Customized Bilingual Companion.epub
Pairing map: /Users/luojiaxing/Code/cc-customized-books/.worktrees/reusable-epub-framework/output/Animal Farm/pairing-map.md
```

- [ ] **Step 3: Verify the EPUB contains no listening-noise reference/provenance text**

Run:

```bash
python3 - <<'PY'
import re
from pathlib import Path
from zipfile import ZipFile
from bs4 import BeautifulSoup

epub_path = Path("output/Animal Farm/Animal Farm - Customized Bilingual Companion.epub")
forbidden = [
    "References For Visual Review",
    "Publisher page",
    "章节配对与增补说明",
    "English source text from",
    "Chinese source text from",
]
hits = {}
with ZipFile(epub_path) as zf:
    for name in zf.namelist():
        if name.endswith(".xhtml"):
            text = zf.read(name).decode("utf-8", errors="replace")
            visible = BeautifulSoup(text, "html.parser").get_text(" ", strip=True)
            matched = [item for item in forbidden if item in visible]
            if matched:
                hits[name] = matched
print(hits)
raise SystemExit(1 if hits else 0)
PY
```

Expected: prints `{}` and exits `0`.

- [ ] **Step 4: Verify the sidecar pairing map still exists**

Run:

```bash
python3 - <<'PY'
from pathlib import Path
path = Path("output/Animal Farm/pairing-map.md")
print(path.exists(), path.read_text(encoding="utf-8").splitlines()[0])
PY
```

Expected:

```text
True # Animal Farm / 动物农场 - Customized Bilingual Companion Edition Pairing Map
```

- [ ] **Step 5: Commit the guide update and rebuilt artifacts**

```bash
git add AGENTS.md output/Animal\ Farm/pairing-map.md output/Animal\ Farm/Animal\ Farm\ -\ Customized\ Bilingual\ Companion.epub
git commit -m "Make listening EPUB output content-only"
```

Expected: commit succeeds and includes the guide plus regenerated Animal Farm artifacts.

## Self-Review

- Spec coverage:
  - Renderer no longer emits book-level references: Task 1
  - Builder smoke test protects content-only contract: Task 2
  - Animal Farm companion stops narrating pairing/additional-material notes: Task 3
  - Agent guide explicitly instructs content-only listening editions: Task 4
  - Sidecar pairing map remains available: Tasks 2 and 4
- Placeholder scan:
  - No unfinished placeholder markers or deferred implementation notes remain.
- Type consistency:
  - All function names and file paths match the current branch: `render_book_companion`, `build_project`, `tests.test_render`, `tests.test_builder_smoke`, `book_projects/animal-farm/companion.json`.
