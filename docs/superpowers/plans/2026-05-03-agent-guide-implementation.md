# Bilingual EPUB Agent Guide Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a root `AGENTS.md` that tells future agents how to produce TTS-first bilingual study EPUBs from the books and glossary in this repository.

**Architecture:** This is a documentation-first implementation. `AGENTS.md` is the single operating manual, organized around source inspection, chapter pairing, content standards, audio/TTS rules, EPUB assembly, error handling, and final quality checks. The design spec remains the source of truth for rationale, while `AGENTS.md` becomes the practical runbook future agents read first.

**Tech Stack:** Markdown, EPUB-aware command-line inspection with `unzip`, repository search with `rg`, Git for checkpoints.

---

## File Structure

- Create: `AGENTS.md`
  - Responsibility: project-level instructions for agents producing customized bilingual study EPUBs.
  - Sections: purpose, repository layout, output contract, workflow, source pairing, content standards, TTS optimization, EPUB assembly, quality checklist, final response requirements.
- Read-only reference: `docs/superpowers/specs/2026-05-03-agent-guided-bilingual-epub-design.md`
  - Responsibility: approved design rationale and requirement source.
- Read-only inputs: `books/`
  - Responsibility: source EPUB folders, usually one folder per book with English and Chinese editions.
- Read-only inputs: `glossary/vocabulary_profile.json` and `glossary/english_words.txt`
  - Responsibility: user vocabulary calibration.

No scripts or automation files are part of this implementation. The guide may mention useful commands, but it must not claim that the workflow is fully automated.

---

### Task 1: Create Guide Skeleton And Output Contract

**Files:**
- Create: `AGENTS.md`

- [ ] **Step 1: Create the initial `AGENTS.md`**

Use `apply_patch` to create `AGENTS.md` with this content:

```markdown
# Agent Instructions

## Project Purpose

This project helps the user read English books with less friction. The user is a native Chinese speaker who often listens to books with an AI reader and wants customized EPUBs that combine Chinese support, the original English, vocabulary guidance, and deep context.

The output should help the user keep reading or listening to the English original. Do not turn the project into a summary-only replacement for the book.

## Repository Layout

- `books/`: source EPUBs grouped by book folder. Most target folders contain one English EPUB and one Chinese EPUB.
- `glossary/vocabulary_profile.json`: user reading-level profile and agent guidance.
- `glossary/english_words.txt`: one lowercase English word per line, representing known vocabulary gaps.
- `docs/superpowers/specs/2026-05-03-agent-guided-bilingual-epub-design.md`: approved design source for this guide.

Treat `books/` and `glossary/` as source inputs. Do not rewrite, rename, or delete them unless the user explicitly asks.

## Required Output

For each target book, produce a final EPUB customized for the user.

The EPUB must include:

- A substantial bilingual book companion at the top.
- Recommended book-level outside research with deep insights and readable source labels.
- Optional reading plan or pacing suggestion when the book is long, dense, or difficult.
- Chapter-level alignment only, not paragraph-level alignment.
- For each chapter or major section:
  - Chapter Listening Brief.
  - Chapter Companion Reference.
  - Chinese chapter.
  - Vocabulary For Listening.
  - English chapter.
  - Chapter Recap when useful.
- Faithful, readable Chinese translation when no Chinese source EPUB exists.
- A usable table of contents.

The default chapter order is Chinese first, English second. Vocabulary goes immediately before the English chapter.

## Quality Bar

The output should feel like a thoughtful bilingual reading tutor that is pleasant to hear aloud. It should reduce friction, preserve the original book, and avoid burying the source text under low-value notes.
```

- [ ] **Step 2: Verify the skeleton exists**

Run:

```bash
test -f AGENTS.md
```

Expected: command exits with status `0`.

- [ ] **Step 3: Verify required opening sections**

Run:

```bash
rg -n "Project Purpose|Repository Layout|Required Output|Quality Bar|Chapter Listening Brief|Vocabulary For Listening" AGENTS.md
```

Expected: output includes one match for each listed heading or required phrase.

- [ ] **Step 4: Commit Task 1**

Run:

```bash
git add AGENTS.md
git commit -m "Add bilingual EPUB agent guide skeleton"
```

Expected: commit succeeds and includes only `AGENTS.md`.

---

### Task 2: Add Source Inspection And Chapter Pairing Workflow

**Files:**
- Modify: `AGENTS.md`

- [ ] **Step 1: Add the workflow section after `## Quality Bar`**

Use `apply_patch` to append this content to `AGENTS.md`:

```markdown

## Core Workflow

Follow this workflow for every target book:

1. Inspect `books/` and identify the target book folder.
2. Detect English and Chinese EPUBs using metadata, filenames, language tags, and sampled text.
3. Extract each EPUB's table of contents and chapter files.
4. Pair chapters at chapter level only.
5. If chapter counts, chapter names, or source structures mismatch, create an explicit pairing map and surface the uncertainty.
6. Read `glossary/vocabulary_profile.json` and `glossary/english_words.txt` before selecting vocabulary.
7. Create book-level deep bilingual companion notes with outside research when helpful.
8. For each chapter, create both a concise listening brief and deeper bilingual companion notes before the Chinese chapter.
9. For each English chapter, create a learning-priority vocabulary list before the English chapter.
10. Add a short chapter recap after the English chapter when useful for retention.
11. Assemble the bilingual EPUB with a usable table of contents.
12. Run the quality checklist before finishing.

## Source Detection

Use several signals before deciding which EPUB is English and which is Chinese:

- File name and folder name.
- EPUB metadata such as `dc:language`, `dc:title`, and `dc:creator`.
- Table of contents labels.
- Sampled body text from early content files.

Example inspection commands from the current repo:

```bash
rg --files books
unzip -l "books/Animal Farm/Animal Farm (George Orwell) (z-library.sk, 1lib.sk, z-lib.sk).epub"
unzip -p "books/Animal Farm/Animal Farm (George Orwell) (z-library.sk, 1lib.sk, z-lib.sk).epub" META-INF/container.xml
unzip -p "books/Animal Farm/Animal Farm (George Orwell) (z-library.sk, 1lib.sk, z-lib.sk).epub" toc.ncx
```

If metadata and sampled text disagree, trust sampled text and explain the issue.

## Chapter Pairing Rules

Pair chapters at chapter level only. Do not attempt paragraph-by-paragraph alignment unless the user explicitly changes the requirement.

Before merging, create a pairing map with:

- English chapter title.
- English source file or table-of-contents entry.
- Chinese chapter title.
- Chinese source file or table-of-contents entry.
- Status: matched, uncertain, missing, extra, abridged, reordered, or image-only.

If source editions differ, do not silently skip material. Explain frontmatter, epilogues, notes, appendices, acknowledgments, photographs, maps, indexes, and image-heavy sections. Decide whether each should be included, summarized, converted, or flagged.

Pause and ask the user only when the mismatch changes the reading experience in a meaningful way and cannot be resolved from the sources.
```

- [ ] **Step 2: Verify workflow and pairing terms**

Run:

```bash
rg -n "Core Workflow|Source Detection|Chapter Pairing Rules|pairing map|chapter level only|unzip -l|toc.ncx" AGENTS.md
```

Expected: output includes all headings and command examples.

- [ ] **Step 3: Commit Task 2**

Run:

```bash
git add AGENTS.md
git commit -m "Document EPUB source inspection workflow"
```

Expected: commit succeeds and includes only `AGENTS.md`.

---

### Task 3: Add Companion, Vocabulary, Translation, And TTS Standards

**Files:**
- Modify: `AGENTS.md`

- [ ] **Step 1: Append content standards**

Use `apply_patch` to append this content to `AGENTS.md`:

```markdown

## Book-Level Companion Standards

The book-level companion should be substantial and bilingual. Put the main explanation in Chinese first, then add a concise English summary.

Include:

- What the book is about.
- Why the book matters.
- Author background and writing context.
- Historical, cultural, political, technical, or intellectual context.
- Major themes and tensions.
- Controversies, criticism, or competing interpretations where relevant.
- Community agreement or disagreement for technical and idea-driven books.
- A reading strategy tailored to the user.
- An optional reading schedule when the book benefits from pacing.
- Parts worth reading closely.
- Parts that can be skimmed.
- References and further reading with human-readable source labels.

Outside research is recommended by default for the book-level companion, especially for biography, history, politics, culture, technology, and idea-driven nonfiction. For modern facts, current public figures, laws, products, software, or community consensus, verify with up-to-date sources.

Do not expose raw web URLs in listener-facing text. Use labels such as `publisher page`, `author interview`, `New York Times review`, or `official documentation`. Raw URLs may exist only as hidden hyperlink targets or in a clearly marked optional visual-only reference section.

## Chapter Companion Standards

Each chapter begins with a concise listening brief and then deeper companion notes before the Chinese chapter.

The listening brief should be short and audio-friendly. Include:

- What to listen for.
- Key names and pronunciation hints.
- Two to four important ideas.
- Context needed before hearing the chapter.

The deeper companion reference should include Chinese explanation first and concise English summary second. Cover:

- What happens, or what the chapter argues.
- Why the chapter matters in the whole book.
- Context that helps comprehension.
- Key people, places, ideas, terms, or events.
- Reading priority: read closely or skim lightly.
- Difficult cultural references or disputed claims when relevant.

Mark long background explanations, detailed source notes, and dense references as optional or visual-reference material when they would interrupt listening flow.

## Vocabulary For Listening

Create a learning-priority vocabulary section immediately before each English chapter.

Use these groups:

- Must know.
- Useful / high-value.
- Specialized or context-bound.

Select vocabulary from:

- Words in `glossary/english_words.txt` that appear in the chapter.
- Likely blockers for an upper-B2/lower-C1 reader.
- High-value phrases, idioms, collocations, and specialist terms.

Write entries as readable mini-explanations instead of dense tables.

Preferred format:

```text
predicament, noun, 困境. It means a difficult or unpleasant situation. Listen for it when the author describes a person with no good options.
```

Add pronunciation help for hard names, foreign names, Chinese pinyin, technical terms, and words whose spelling may mislead TTS or the listener.

Avoid over-listing obvious words, proper names better handled in notes, and rare words that are not useful for future reading.

## Translation When Chinese Is Missing

If no Chinese EPUB is available, translate the English chapters into faithful, readable Chinese.

The translation should preserve meaning, tone, argument, and narrative flow while avoiding stiff literal Chinese. Do not freely adapt or simplify the text unless a note explains why.

## Audio And TTS Rules

Optimize the generated EPUB for AI read-aloud by default.

Use:

- Clear, complete sentences.
- Short sections with descriptive headings.
- Spoken-friendly vocabulary explanations.
- Pronunciation hints where helpful.
- Labels such as `Optional Reference` or `Detailed Background For Visual Review` for material that should be skipped during first listening.

Avoid:

- Raw URLs in listener-facing text.
- Dense Markdown-style tables.
- Symbol-heavy lists.
- Footnote clutter.
- Page numbers and running headers.
- OCR artifacts.
- Long parenthetical chains.
- Interrupting source chapters once they begin.

Add a short bilingual chapter recap after the English chapter when it helps retention.
```

- [ ] **Step 2: Verify content standards**

Run:

```bash
rg -n "Book-Level Companion Standards|Chapter Companion Standards|Vocabulary For Listening|Translation When Chinese Is Missing|Audio And TTS Rules|Do not expose raw web URLs|predicament" AGENTS.md
```

Expected: output includes all content-standard headings plus the example vocabulary entry.

- [ ] **Step 3: Commit Task 3**

Run:

```bash
git add AGENTS.md
git commit -m "Add bilingual content and TTS standards"
```

Expected: commit succeeds and includes only `AGENTS.md`.

---

### Task 4: Add EPUB Assembly, Quality Checklist, And Final Response Rules

**Files:**
- Modify: `AGENTS.md`

- [ ] **Step 1: Append EPUB assembly and checklist sections**

Use `apply_patch` to append this content to `AGENTS.md`:

```markdown

## EPUB Assembly Requirements

The final EPUB must be readable, navigable, and pleasant to listen to.

Recommended table of contents pattern:

1. Book Companion
2. Chapter 1 Listening Brief
3. Chapter 1 Companion Reference
4. Chapter 1 Chinese
5. Chapter 1 Vocabulary For Listening
6. Chapter 1 English
7. Chapter 1 Recap

Repeat the pattern for each chapter or major section. Preserve the original book order.

If EPUB tooling is unavailable, create an intermediate structured HTML or XHTML package, explain the blocker clearly, and continue aiming for EPUB as the required final deliverable.

## Error Handling

Pause and surface issues when:

- The target folder contains multiple plausible English or Chinese books.
- Metadata and sampled text disagree about language.
- The English and Chinese editions have different chapter counts.
- A Chinese edition appears abridged or reordered.
- A source EPUB has OCR errors, missing text, broken table of contents, or image-only pages.
- Notes, appendices, or indexes are too large to include naturally.

When a risk is understood, create a clear pairing or inclusion plan and proceed. Do not silently drop material or invent missing source text.

## Final Quality Checklist

Before finishing, verify:

- Correct English and Chinese source book pairing.
- Chapter count and chapter order.
- Any mismatched chapters have an explicit pairing map.
- No silent skips of frontmatter, epilogue, notes, appendices, acknowledgments, image-heavy sections, or indexes.
- Chapter listening brief and companion reference appear before the Chinese chapter.
- Chinese appears before English for each paired chapter.
- Vocabulary appears immediately before the English chapter.
- Vocabulary is prioritized for learning value and calibrated to the user's profile.
- Book-level outside research includes useful references and deep insights.
- Raw web URLs do not appear in listener-facing text.
- Generated notes, vocabulary, and references are TTS-friendly.
- Pronunciation guidance is included for hard names and terms where useful.
- Optional or visual-reference material is clearly marked as skippable during listening.
- EPUB opens successfully.
- Table of contents is usable.
- Final response gives the output path and mentions unresolved alignment or source-quality issues.

## Final Response Requirements

When a customized EPUB is produced, the final response must include:

- Output EPUB path.
- Target book folder.
- Source EPUBs used.
- Whether Chinese text came from a source EPUB or from translation.
- Any unresolved alignment or source-quality issues.
- Any sections intentionally summarized, flagged, or made optional for listening.

Keep the final response concise and practical.
```

- [ ] **Step 2: Verify checklist coverage**

Run:

```bash
rg -n "EPUB Assembly Requirements|Error Handling|Final Quality Checklist|Final Response Requirements|Raw web URLs do not appear|EPUB opens successfully|Output EPUB path" AGENTS.md
```

Expected: output includes all checklist and final-response requirements.

- [ ] **Step 3: Commit Task 4**

Run:

```bash
git add AGENTS.md
git commit -m "Add EPUB assembly quality checklist"
```

Expected: commit succeeds and includes only `AGENTS.md`.

---

### Task 5: Final Verification Against Spec

**Files:**
- Verify: `AGENTS.md`
- Read-only reference: `docs/superpowers/specs/2026-05-03-agent-guided-bilingual-epub-design.md`

- [ ] **Step 1: Check for forbidden draft-marker language**

Run:

```bash
rg -n "T[B]D|T[O]DO|F[I]XME|placeh[o]lder|fill in [l]ater|figure out [l]ater" AGENTS.md
```

Expected: no matches and exit status `1`.

- [ ] **Step 2: Check spec coverage keywords**

Run:

```bash
rg -n "chapter level|book companion|outside research|Listening Brief|Companion Reference|Vocabulary For Listening|faithful, readable Chinese|raw web URLs|TTS|quality checklist|pairing map" AGENTS.md
```

Expected: output includes all listed requirement areas.

- [ ] **Step 3: Check repository status**

Run:

```bash
git status --short
```

Expected: `books/` and `glossary/` may remain untracked source inputs. `AGENTS.md` should have no uncommitted changes after Task 4.

- [ ] **Step 4: Confirm recent commits**

Run:

```bash
git log --oneline -5
```

Expected: output includes the Task 1 through Task 4 commits above.

- [ ] **Step 5: Report completion evidence**

In the final implementation response, include:

- The path `AGENTS.md`.
- The verification commands run.
- A note that `books/` and `glossary/` were treated as inputs and not modified.

No commit is required for Task 5 unless verification reveals a necessary fix.
