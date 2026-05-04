# Teacher-Mode Book Companion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade the reusable EPUB framework so book companions and key chapter notes can carry a sharper teacher-mode structure, then migrate the Animal Farm sample to use that stronger teaching voice.

**Architecture:** Extend the `companion.json` schema with optional teacher-mode structures instead of replacing the current fields outright. Keep the listening flow and existing chapter package order intact, but let the renderer surface stronger book-level theses, rival views, and key-chapter mini lectures when those fields are present. Finish by updating `AGENTS.md`, rewriting the Animal Farm sample content into teacher mode, and rebuilding the EPUB.

**Tech Stack:** Python 3, `unittest`, `ebooklib`, JSON project content files, `scripts/custom_epub` models/render/builder modules, Markdown guide docs.

---

## File Structure

- `scripts/custom_epub/models.py`
  - Responsibility: define companion dataclasses and load `companion.json`. This is where teacher-mode data needs to be modeled and validated.
- `tests/test_models.py`
  - Responsibility: lock the JSON-loading contract so teacher-mode book sections and key-chapter mini lectures parse correctly.
- `scripts/custom_epub/render.py`
  - Responsibility: turn structured companion data into listening-friendly XHTML with labeled sections and no artifact noise.
- `tests/test_render.py`
  - Responsibility: verify teacher-mode sections render with the right headings and that key-chapter mini lectures appear only when present.
- `tests/test_builder_smoke.py`
  - Responsibility: keep end-to-end EPUB output honest, including teacher-mode book/chapter sections and the existing content-only listening constraints.
- `book_projects/animal-farm/companion.json`
  - Responsibility: the sample book’s actual companion content. This needs a real migration from generic companion text to teacher-mode material.
- `AGENTS.md`
  - Responsibility: operating manual for future agents. This must explicitly teach the new teacher-mode expectations and book-type adaptation rules.
- `output/Animal Farm/Animal Farm - Customized Bilingual Companion.epub`
  - Responsibility: rebuilt verification artifact for manual QA after the code and content migration.

### Task 1: Extend The Companion Schema For Teacher Mode

**Files:**
- Modify: `tests/test_models.py`
- Modify: `scripts/custom_epub/models.py`

- [ ] **Step 1: Write the failing model-loading test**

Add a new test to `tests/test_models.py` that proves `load_companion()` can parse teacher-mode book sections and a key-chapter mini lecture:

```python
    def test_load_companion_supports_teacher_mode_sections(self):
        with tempfile.TemporaryDirectory() as tmp:
            project_dir = Path(tmp)
            (project_dir / "companion.json").write_text(
                json.dumps(
                    {
                        "book": {
                            "companion_zh": "总导读",
                            "summary_en": "Short summary.",
                            "references": [],
                            "teacher_mode": {
                                "central_thesis": {
                                    "zh": "这本书真正关心的是革命如何丢掉自己的语言。",
                                    "en": "The book is really about how revolutions lose control of their own language.",
                                },
                                "why_it_matters": "它把政治腐化写成了日常经验。",
                                "context_frame": "要把它放回二十世纪革命政治与宣传史里去读。",
                                "strong_interpretation": "它最厉害的地方不是影射，而是模式提炼。",
                                "blind_spots": "它压缩了复杂历史，也弱化了群众内部差异。",
                                "what_to_watch": [
                                    "注意口号怎样越来越短。",
                                    "注意谁在解释现实。"
                                ],
                                "questions_to_carry": [
                                    "语言何时开始不再描述事实，而开始制造事实？",
                                    "忠诚为什么比怀疑更容易被制度利用？"
                                ],
                            },
                        },
                        "chapters": [
                            {
                                "english_label": "Chapter One",
                                "key_chapter": True,
                                "listening_brief": {
                                    "names": "Old Major",
                                    "points": ["Listen for the first political vocabulary."],
                                    "context": "Opening chapter.",
                                },
                                "companion": {
                                    "zh": "中文章节导读",
                                    "en": "English chapter summary.",
                                    "priority": "Read closely.",
                                },
                                "mini_lecture": {
                                    "chapter_thesis": "这一章建立了整本书最重要的道德词汇。",
                                    "why_pivotal": "后面的背叛都要回到这里来改写。",
                                    "deeper_interpretation": "老少校真正留下的不是计划，而是一套可被争夺的语言。",
                                    "rival_reading": "也可以把它读成一次带有怀旧色彩的政治神话奠基。",
                                    "questions_to_carry": [
                                        "理想在诞生时为什么总带着诗意？",
                                        "诗意又为什么容易被制度接管？"
                                    ],
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
                companion.book.teacher_mode.central_thesis_zh,
                "这本书真正关心的是革命如何丢掉自己的语言。",
            )
            self.assertEqual(
                companion.book.teacher_mode.questions_to_carry[0],
                "语言何时开始不再描述事实，而开始制造事实？",
            )
            self.assertTrue(companion.chapters[0].key_chapter)
            self.assertEqual(
                companion.chapters[0].mini_lecture.chapter_thesis,
                "这一章建立了整本书最重要的道德词汇。",
            )
```

- [ ] **Step 2: Run the targeted model test to verify it fails**

Run:

```bash
PYTHONPATH=scripts python3 -m unittest tests.test_models.ModelLoadingTests.test_load_companion_supports_teacher_mode_sections -v
```

Expected: `ERROR` or `FAIL` because `BookCompanion` and `CompanionChapter` do not yet expose `teacher_mode`, `key_chapter`, or `mini_lecture`.

- [ ] **Step 3: Add minimal teacher-mode dataclasses and loader support**

Update `scripts/custom_epub/models.py` with explicit dataclasses and parsing helpers:

```python
@dataclass(frozen=True)
class BookTeacherMode:
    central_thesis_zh: str
    central_thesis_en: str
    why_it_matters: str
    context_frame: str
    strong_interpretation: str
    blind_spots: str
    what_to_watch: list[str]
    questions_to_carry: list[str]


@dataclass(frozen=True)
class MiniLecture:
    chapter_thesis: str
    why_pivotal: str
    deeper_interpretation: str
    rival_reading: str
    questions_to_carry: list[str]
```

Extend the existing dataclasses:

```python
@dataclass(frozen=True)
class BookCompanion:
    companion_zh: str
    summary_en: str
    references: list[dict[str, str]]
    teacher_mode: BookTeacherMode | None = None


@dataclass(frozen=True)
class CompanionChapter:
    english_label: str
    listening_brief: ListeningBrief
    companion: ChapterCompanion
    vocabulary: dict[str, list[str]]
    recap: Recap | None
    key_chapter: bool = False
    mini_lecture: MiniLecture | None = None
```

Add a list-string helper and parse the new fields in `load_companion()`:

```python
def _require_str_list(value: Any, field_name: str) -> list[str]:
    items = _require_list(value, field_name)
    if not all(isinstance(item, str) for item in items):
        raise TypeError(f"{field_name} must be a list of strings")
    return list(items)
```

```python
        teacher_mode_data = book_data.get("teacher_mode")
        teacher_mode = None
        if teacher_mode_data is not None:
            thesis = teacher_mode_data["central_thesis"]
            teacher_mode = BookTeacherMode(
                central_thesis_zh=thesis["zh"],
                central_thesis_en=thesis["en"],
                why_it_matters=teacher_mode_data["why_it_matters"],
                context_frame=teacher_mode_data["context_frame"],
                strong_interpretation=teacher_mode_data["strong_interpretation"],
                blind_spots=teacher_mode_data["blind_spots"],
                what_to_watch=_require_str_list(
                    teacher_mode_data.get("what_to_watch", []),
                    "book.teacher_mode.what_to_watch",
                ),
                questions_to_carry=_require_str_list(
                    teacher_mode_data.get("questions_to_carry", []),
                    "book.teacher_mode.questions_to_carry",
                ),
            )
```

```python
        mini_lecture_data = row.get("mini_lecture")
        mini_lecture = None
        if mini_lecture_data is not None:
            mini_lecture = MiniLecture(
                chapter_thesis=mini_lecture_data["chapter_thesis"],
                why_pivotal=mini_lecture_data["why_pivotal"],
                deeper_interpretation=mini_lecture_data["deeper_interpretation"],
                rival_reading=mini_lecture_data["rival_reading"],
                questions_to_carry=_require_str_list(
                    mini_lecture_data.get("questions_to_carry", []),
                    "chapters[].mini_lecture.questions_to_carry",
                ),
            )
```

And wire them into `CompanionChapter(...)` and `BookCompanion(...)`.

- [ ] **Step 4: Run the model tests to verify they pass**

Run:

```bash
PYTHONPATH=scripts python3 -m unittest tests.test_models -v
```

Expected: all model tests pass, including the new teacher-mode loader coverage.

- [ ] **Step 5: Commit the schema change**

```bash
git add tests/test_models.py scripts/custom_epub/models.py
git commit -m "Add teacher-mode companion schema"
```

Expected: commit succeeds and includes only the model loader + tests.

### Task 2: Render Teacher-Mode Book Sections And Key-Chapter Mini Lectures

**Files:**
- Modify: `tests/test_render.py`
- Modify: `scripts/custom_epub/render.py`

- [ ] **Step 1: Write the failing render tests**

Add a book-companion render test that uses the new schema:

```python
    def test_render_book_companion_includes_teacher_mode_sections(self):
        companion = BookCompanion(
            companion_zh="基础导读",
            summary_en="English guide.",
            references=[],
            teacher_mode=BookTeacherMode(
                central_thesis_zh="真正的主题是语言与权力。",
                central_thesis_en="The real subject is language and power.",
                why_it_matters="它解释了理想如何被重新命名。",
                context_frame="放回革命政治史里理解。",
                strong_interpretation="最强的一点是模式而非影射。",
                blind_spots="它压缩了复杂社会差异。",
                what_to_watch=["注意口号变短。"],
                questions_to_carry=["谁在定义现实？"],
            ),
        )

        rendered = render_book_companion("Sample", companion)

        self.assertIn("Central Thesis / 核心判断", rendered)
        self.assertIn("真正的主题是语言与权力。", rendered)
        self.assertIn("The real subject is language and power.", rendered)
        self.assertIn("What this misses / 这一读法的盲点", rendered)
        self.assertIn("Questions to carry / 带着走的问题", rendered)
        self.assertNotIn("https://", rendered)
```

Add a chapter-page render test for key chapters:

```python
    def test_render_chapter_pages_includes_key_chapter_mini_lecture(self):
        chapter = CompanionChapter(
            english_label="Chapter One",
            listening_brief=ListeningBrief(
                names="Old Major",
                points=["Listen for slogans."],
                context="Opening.",
            ),
            companion=ChapterCompanion(
                zh="中文伴读",
                en="English summary.",
                priority="Read closely.",
            ),
            vocabulary={
                "Must know": ["comrade, noun, 同志。"],
                "Useful / high-value": [],
                "Specialized or context-bound": [],
            },
            recap=Recap(zh="中文回顾", en="English recap."),
            key_chapter=True,
            mini_lecture=MiniLecture(
                chapter_thesis="这一章创建了政治语言。",
                why_pivotal="后面所有背叛都从这里分叉。",
                deeper_interpretation="它在讲革命如何先靠诗意成立。",
                rival_reading="也可读成神话式开端。",
                questions_to_carry=["诗意为什么会变成命令？"],
            ),
        )

        pages = render_chapter_pages(
            1,
            "第一章",
            chapter,
            "<p>中文正文</p>",
            "<p>English text.</p>",
        )

        self.assertIn("Mini Lecture / 深入讲解", pages["companion"])
        self.assertIn("这一章创建了政治语言。", pages["companion"])
        self.assertIn("诗意为什么会变成命令？", pages["companion"])
```

- [ ] **Step 2: Run the targeted render tests to verify they fail**

Run:

```bash
PYTHONPATH=scripts python3 -m unittest \
  tests.test_render.RenderTests.test_render_book_companion_includes_teacher_mode_sections \
  tests.test_render.RenderTests.test_render_chapter_pages_includes_key_chapter_mini_lecture -v
```

Expected: `FAIL` because the renderer still ignores `teacher_mode` and `mini_lecture`.

- [ ] **Step 3: Implement the render helpers with labeled, listenable sections**

Update `scripts/custom_epub/render.py` by adding small rendering helpers:

```python
from .models import BookCompanion, CompanionChapter, BookTeacherMode, MiniLecture


def _list_items(items: list[str]) -> str:
    return "".join(f"<li>{html.escape(item)}</li>" for item in items)


def _teacher_section(title: str, content: str) -> str:
    if not content.strip():
        return ""
    return f"<h2>{html.escape(title)}</h2><div class=\"teacher-section\">{paragraphs(content)}</div>"
```

Render teacher-mode fields inside `render_book_companion()` after the base Chinese overview:

```python
    teacher_mode = companion.teacher_mode
    teacher_blocks = ""
    if teacher_mode is not None:
        teacher_blocks = f"""
<h2>Central Thesis / 核心判断</h2>
<div class="teacher-section">
  <p>{html.escape(teacher_mode.central_thesis_zh)}</p>
  <p><strong>English:</strong> {html.escape(teacher_mode.central_thesis_en)}</p>
</div>
{_teacher_section("Why this book matters / 为什么值得读", teacher_mode.why_it_matters)}
{_teacher_section("Context frame / 阅读坐标", teacher_mode.context_frame)}
{_teacher_section("My take / 我的判断", teacher_mode.strong_interpretation)}
{_teacher_section("What this misses / 这一读法的盲点", teacher_mode.blind_spots)}
<h2>What to watch / 阅读时要追踪什么</h2>
<ul>{_list_items(teacher_mode.what_to_watch)}</ul>
<h2>Questions to carry / 带着走的问题</h2>
<ul>{_list_items(teacher_mode.questions_to_carry)}</ul>
"""
```

Then include `teacher_blocks` before the existing English summary block.

Render mini lectures inside `render_chapter_pages()` only when `chapter.key_chapter` and `chapter.mini_lecture` are both present:

```python
    lecture = chapter.mini_lecture
    lecture_block = ""
    if chapter.key_chapter and lecture is not None:
        lecture_block = f"""
<h2>Mini Lecture / 深入讲解</h2>
<div class="teacher-section">
  <p><strong>Chapter thesis:</strong> {html.escape(lecture.chapter_thesis)}</p>
  <p><strong>Why it is pivotal:</strong> {html.escape(lecture.why_pivotal)}</p>
  <p><strong>Deeper interpretation:</strong> {html.escape(lecture.deeper_interpretation)}</p>
  <p><strong>Rival reading:</strong> {html.escape(lecture.rival_reading)}</p>
</div>
<h3>Questions to carry</h3>
<ul>{_list_items(lecture.questions_to_carry)}</ul>
"""
```

Insert `lecture_block` in the companion page after the reading-priority line and before the English summary.

- [ ] **Step 4: Run the render tests to verify they pass**

Run:

```bash
PYTHONPATH=scripts python3 -m unittest tests.test_render -v
```

Expected: all render tests pass, including the new teacher-mode assertions.

- [ ] **Step 5: Commit the rendering change**

```bash
git add tests/test_render.py scripts/custom_epub/render.py
git commit -m "Render teacher-mode book and chapter sections"
```

Expected: commit succeeds and includes only render code + render tests.

### Task 3: Update The Build Guardrails For Teacher Mode

**Files:**
- Modify: `tests/test_builder_smoke.py`

- [ ] **Step 1: Strengthen the smoke test fixture**

Update the fixture companion payload in `tests/test_builder_smoke.py` so it includes a small teacher-mode block and a key chapter mini lecture:

```python
                    "book": {
                        "companion_zh": "中文导读",
                        "summary_en": "English summary.",
                        "references": [{"label": "Publisher page"}],
                        "teacher_mode": {
                            "central_thesis": {
                                "zh": "这本书考察语言和权力。",
                                "en": "This book studies language and power.",
                            },
                            "why_it_matters": "它解释理想如何被权力接管。",
                            "context_frame": "放回革命政治史里理解。",
                            "strong_interpretation": "它最强的是模式，不是单纯影射。",
                            "blind_spots": "它压缩了复杂社会层次。",
                            "what_to_watch": ["注意谁在解释现实。"],
                            "questions_to_carry": ["谁在定义现实？"],
                        },
                    },
```

And in the chapter fixture:

```python
                            "key_chapter": True,
                            "mini_lecture": {
                                "chapter_thesis": "这一章建立政治词汇。",
                                "why_pivotal": "后面的背叛都从这里开始。",
                                "deeper_interpretation": "革命先靠语言成立。",
                                "rival_reading": "也可以读成神话化开端。",
                                "questions_to_carry": ["诗意为什么会变成命令？"],
                            },
```

- [ ] **Step 2: Add failing smoke assertions for teacher-mode output**

Extend `test_build_project_creates_epub_and_pairing_map_without_listening_noise` with these assertions:

```python
            self.assertIn("Central Thesis / 核心判断", xhtml)
            self.assertIn("Questions to carry / 带着走的问题", xhtml)
            self.assertIn("Mini Lecture / 深入讲解", xhtml)
            self.assertIn("谁在定义现实？", xhtml)
            self.assertIn("诗意为什么会变成命令？", xhtml)
```

- [ ] **Step 3: Run the smoke test to verify it fails before Task 2 lands**

Run:

```bash
PYTHONPATH=scripts python3 -m unittest tests.test_builder_smoke.BuilderSmokeTests.test_build_project_creates_epub_and_pairing_map_without_listening_noise -v
```

Expected: `FAIL` because the XHTML does not yet contain the teacher-mode sections.

- [ ] **Step 4: Re-run the smoke tests after Task 2**

Run:

```bash
PYTHONPATH=scripts python3 -m unittest tests.test_builder_smoke -v
```

Expected: all smoke tests pass, including the inherited-cover and listening-noise assertions.

- [ ] **Step 5: Commit the stronger end-to-end coverage**

```bash
git add tests/test_builder_smoke.py
git commit -m "Add teacher-mode EPUB smoke coverage"
```

Expected: commit succeeds and includes only `tests/test_builder_smoke.py`.

### Task 4: Migrate Animal Farm And Update The Agent Guide

**Files:**
- Modify: `book_projects/animal-farm/companion.json`
- Modify: `AGENTS.md`

- [ ] **Step 1: Rewrite the Animal Farm book companion into teacher mode**

Add a `teacher_mode` block under `book` in `book_projects/animal-farm/companion.json` with the actual sample content:

```json
"teacher_mode": {
  "central_thesis": {
    "zh": "《动物农场》最锋利的地方，不只是它影射了苏联革命，而是它把一个更普遍的政治规律写得极其可听见：革命往往不是一下子背叛自己，而是在语言、记忆和必要性的名义下，一点点失去对自身理想的控制。",
    "en": "Animal Farm matters not only as a Soviet allegory, but as a study of how revolutions slowly lose control of their own ideals through language, memory, and claims of necessity."
  },
  "why_it_matters": "它让你听见政治如何进入日常生活：先改词，再改记忆，最后让人连自己的痛苦都只能用权力给出的词来理解。",
  "context_frame": "把它放回俄国革命、斯大林主义、西班牙内战后的左翼幻灭，以及奥威尔对宣传政治的长期警惕里去读，会更容易理解它为什么短，却后劲这么重。",
  "strong_interpretation": "我会把这本书读成一部关于“政治语言如何夺走道德判断”的寓言。最可怕的不是暴力本身，而是动物越来越失去描述暴力的独立语言。",
  "blind_spots": "它的寓言形式带来力量，也带来压缩。阶级、制度、群众心理的复杂差异被高度提炼，所以它更擅长揭示模式，不擅长解释全部历史复杂性。",
  "what_to_watch": [
    "注意口号怎样越来越短，却越来越像命令。",
    "注意每次制度转折前后，谁在解释现实，谁只能接受解释。",
    "注意勤劳、忠诚、朴素这些美德，怎样一步步变成最容易被利用的资源。"
  ],
  "questions_to_carry": [
    "当一个共同体只能用统治者允许的词描述现实，它还剩下多少自我纠错能力？",
    "为什么最忠诚、最肯牺牲的人，在政治上往往最不安全？",
    "结尾的震动，究竟来自“猪变成人”，还是来自旁观者终于失去区分两者的能力？"
  ]
}
```

Keep the existing `companion_zh`, `summary_en`, and TTS-friendly pacing guidance, but make sure the new block carries the sharper thesis layer.

- [ ] **Step 2: Mark the key Animal Farm chapters and add mini lectures**

In the same `book_projects/animal-farm/companion.json`, add:

- `"key_chapter": true`
- `"mini_lecture": {...}`

for these chapters:

- `Chapter One`
- `Chapter Two`
- `Chapter Five`
- `Chapter Seven`
- `Chapter Nine`
- `Chapter Ten`

Use compact, teacher-style content. For example, for `Chapter Five`:

```json
"key_chapter": true,
"mini_lecture": {
  "chapter_thesis": "这一章真正决定的不是风车，而是农场从“还有政治争论”滑向“只剩权力命令”的瞬间。",
  "why_pivotal": "狗群驱逐雪球之后，革命仍保留会议外形，但已经失去真实的政治竞争。",
  "deeper_interpretation": "奥威尔在这里讲的不是谁辩论赢了，而是谁决定以后再也不需要靠辩论取胜。",
  "rival_reading": "也可以把这一章读成技术现代化与个人独裁纠缠在一起的寓言：未来愿景本身就可能被拿来当作夺权工具。",
  "questions_to_carry": [
    "为什么很多制度崩坏，并不是从取消口号开始，而是从垄断解释权开始？",
    "当效率、建设、未来这些词越来越响时，我们该怎样判断政治空间是否正在收缩？"
  ]
}
```

Keep the non-key chapters unchanged except for any wording needed to fit the stronger overall voice.

- [ ] **Step 3: Update `AGENTS.md` with explicit teacher-mode guidance**

Add these rules in `AGENTS.md`:

1. In `## Quality Bar`, append:

```markdown
For serious reading support, default to a teacher-level voice: sharper interpretation, stronger ideas, selective rival views, and questions that help the user think with and against the book.
```

2. In `## Book-Level Companion Standards`, after the listening-content-only paragraph, add:

```markdown
Default to teacher mode. The book-level companion should not stop at neutral summary. It should include a strong central thesis, explain why the book matters, offer a substantive interpretive frame, surface the most important blind spots or competing views, and end with sharp questions worth carrying through the reading.
```

3. In `## Chapter Companion Standards`, after the existing bullet list for the deeper companion reference, add:

```markdown
For key chapters, add a compact mini lecture. A key chapter is either a turning point or unusually rich in thematic or intellectual density. The mini lecture should state what the chapter really accomplishes, why it is pivotal, the strongest reading of what is happening under the surface, the most useful rival reading, and a few sharp questions.
```

4. Add a new subsection before `## Vocabulary For Listening`:

```markdown
## Book-Type Adaptation

Adjust teacher mode by book type.

- Fiction and literature: focus on form, symbols, moral tension, psychology, politics, and what the narrative reveals about human life.
- History, biography, and politics: focus on argument, evidence, framing, omissions, ideology, and how the author wants the reader to judge events.
- Philosophy, social thought, and theory: focus on claims, logic, assumptions, tensions, objections, and what follows if the argument is right.
- Technical and knowledge books: focus on the core model, practical insight, hidden assumptions, community disagreement, and what is genuinely essential.
```

- [ ] **Step 4: Verify the migrated content loads and rebuild Animal Farm**

Run:

```bash
PYTHONPATH=scripts python3 - <<'PY'
from pathlib import Path
from custom_epub.models import load_companion
companion = load_companion(Path("book_projects/animal-farm"))
print(companion.book.teacher_mode.central_thesis_zh[:24])
print(companion.chapters[0].mini_lecture.chapter_thesis)
PY
```

Expected: prints the opening of the new thesis and the Chapter One mini-lecture thesis.

Then rebuild:

```bash
PYTHONPATH=scripts python3 scripts/build_custom_epub.py book_projects/animal-farm
```

Expected: build succeeds and rewrites `output/Animal Farm/Animal Farm - Customized Bilingual Companion.epub`.

- [ ] **Step 5: Commit the content and guide migration**

```bash
git add book_projects/animal-farm/companion.json AGENTS.md
git commit -m "Adopt teacher-mode companion guidance"
```

Expected: commit succeeds and includes only the sample content + guide updates.

### Task 5: Full Verification And Listening-Focused QA

**Files:**
- Verify: `tests/test_models.py`
- Verify: `tests/test_render.py`
- Verify: `tests/test_builder_smoke.py`
- Verify: `output/Animal Farm/Animal Farm - Customized Bilingual Companion.epub`

- [ ] **Step 1: Run the full automated test suite**

Run:

```bash
PYTHONPATH=scripts python3 -m unittest discover -s tests -v
```

Expected: all tests pass.

- [ ] **Step 2: Verify teacher-mode text appears in the rebuilt EPUB**

Run:

```bash
python3 - <<'PY'
from pathlib import Path
from zipfile import ZipFile

epub_path = Path("output/Animal Farm/Animal Farm - Customized Bilingual Companion.epub")
with ZipFile(epub_path) as zf:
    xhtml = "\n".join(
        zf.read(name).decode("utf-8")
        for name in zf.namelist()
        if name.endswith(".xhtml")
    )

checks = [
    "Central Thesis / 核心判断",
    "Questions to carry / 带着走的问题",
    "Mini Lecture / 深入讲解",
    "为什么最忠诚、最肯牺牲的人，在政治上往往最不安全？",
]
for item in checks:
    print(item, item in xhtml)
PY
```

Expected:

```text
Central Thesis / 核心判断 True
Questions to carry / 带着走的问题 True
Mini Lecture / 深入讲解 True
为什么最忠诚、最肯牺牲的人，在政治上往往最不安全？ True
```

- [ ] **Step 3: Re-run the listening-noise guard on the rebuilt EPUB**

Run:

```bash
python3 - <<'PY'
from pathlib import Path
from zipfile import ZipFile

epub_path = Path("output/Animal Farm/Animal Farm - Customized Bilingual Companion.epub")
blocked = [
    "References For Visual Review",
    "English source text from",
    "Chinese source text from",
    "章节配对与增补说明",
]
with ZipFile(epub_path) as zf:
    xhtml = "\n".join(
        zf.read(name).decode("utf-8")
        for name in zf.namelist()
        if name.endswith(".xhtml")
    )
for item in blocked:
    print(item, item in xhtml)
PY
```

Expected:

```text
References For Visual Review False
English source text from False
Chinese source text from False
章节配对与增补说明 False
```

- [ ] **Step 4: Review the diff before wrapping up**

Run:

```bash
git status --short
git log --oneline -5
```

Expected: only the intended tracked file changes remain, and the five most recent commits correspond to the teacher-mode implementation work.

- [ ] **Step 5: Commit any final test-only touchups if needed**

If Step 4 reveals no uncommitted changes, do not create an extra commit.

If a small verification-driven test or copy fix was needed, commit it with:

```bash
git add tests/test_models.py tests/test_render.py tests/test_builder_smoke.py scripts/custom_epub/models.py scripts/custom_epub/render.py book_projects/animal-farm/companion.json AGENTS.md
git commit -m "Polish teacher-mode EPUB companion output"
```

Expected: either no extra commit is needed, or the final polish commit is tightly scoped to the teacher-mode work only.
