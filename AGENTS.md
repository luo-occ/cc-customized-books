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
- Recommended book-level outside research with deep insights that stay focused on the book itself.
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
For serious reading support, default to a teacher-level voice: sharper interpretation, stronger ideas, selective rival views, and questions that help the user think with and against the book.

"Teacher-level" is enforced concretely, not aspirationally. Every interpretive claim must pass the Depth Tests. No banned generic moves survive into the final draft. The draft does not ship until the Sharper Critic Pass converges. These are gates, not encouragements.

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
11. Run the Sharper Critic Pass on every interpretive claim before assembly. See the Sharper Critic Pass section.
12. Assemble the bilingual EPUB with a usable table of contents.
13. Run the quality checklist before finishing.

## Reusable Framework Workflow

Use the reusable framework for final EPUB builds instead of generating a new one-off script for each book.

For each book:

1. Create or update `book_projects/<slug>/project.json` with source EPUB paths, output paths, pairings, and optional source-section decisions.
2. Create or update `book_projects/<slug>/companion.json` with book companion notes, chapter listening briefs, chapter companion references, vocabulary, recaps, and pronunciation help.
3. Run the Sharper Critic Pass on `companion.json` before building. See the Sharper Critic Pass section.
4. Run `PYTHONPATH=scripts python3 scripts/build_custom_epub.py book_projects/<slug>`.
5. Verify the generated EPUB and pairing map under `output/<Book Name>/`.

The main listening EPUB should contain only book-relevant learning content and source text. Pairing maps, references, edition notes, and provenance details belong in sidecar artifacts or final reports, not in the listening flow.

Book-specific helper scripts may be used for temporary investigation, but they should not be the final deliverable. Preserve reusable mechanics in `scripts/custom_epub/` and book-specific judgment in `book_projects/<slug>/`.
Customized EPUBs should inherit the source-book cover by default: prefer the English source cover, and fall back to the Chinese source cover only if the English cover cannot be extracted.

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

## Book-Level Companion Standards

The book-level companion should be substantial and bilingual. Put the main explanation in Chinese first, then add a concise English summary.

For listening EPUBs, keep the Book Companion content-only. Do not include references lists, pairing explanations, edition-handling notes, provenance notes, or build-process explanations inside the main EPUB.

Default to teacher mode. The book-level companion should not stop at neutral summary. It should include a strong central thesis, explain why the book matters, offer a substantive interpretive frame, surface the most important blind spots or competing views, and end with sharp questions worth carrying through the reading.

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
- Listening-focused guidance that stays on the book itself rather than the artifact.

Outside research is recommended by default for the book-level companion, especially for biography, history, politics, culture, technology, and idea-driven nonfiction. For modern facts, current public figures, laws, products, software, or community consensus, verify with up-to-date sources.

Do not expose raw web URLs in listener-facing text. Use labels such as `publisher page`, `author interview`, `New York Times review`, or `official documentation`. Raw URLs may exist only as hidden hyperlink targets or in a clearly marked optional visual-only reference section.

Every claim inside `companion_zh`, `summary_en`, and every field under `teacher_mode` must pass the Depth Tests. Apply the per-field standards listed in that section.

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

For key chapters, add a compact mini lecture. A key chapter is either a turning point or unusually rich in thematic or intellectual density. The mini lecture should state what the chapter really accomplishes, why it is pivotal, the strongest reading of what is happening under the surface, the most useful rival reading, and a few sharp questions.

Do not add source-edition descriptions or provenance text such as `English source text from ...` or `Chinese source text from ...` inside the chapter flow unless the user explicitly asks for an audit/study edition.

Mark long background explanations, detailed source notes, and dense references as optional or visual-reference material when they would interrupt listening flow.

Every claim inside `listening_brief.points`, `companion.zh`, `companion.en`, and every field under `mini_lecture` must pass the Depth Tests. Apply the per-field standards listed in that section.

## Depth Tests

Every interpretive claim — in the book-level companion, in any `teacher_mode` field, in any `mini_lecture` field, in `listening_brief.points`, in `companion.zh` body, in `recap` — must pass these five tests. If a claim fails any test, anchor it or cut it.

1. **Anchor test.** The claim names at least one specific scene, phrase, sentence, song, repetition, or pattern from this particular book. Bare abstractions ("political language", "moral consciousness", "the politics of memory") fail until you say *which* phrase, *which* scene, *which* repetition. If the same sentence could appear unchanged in a companion for 1984, Darkness at Noon, or any other allegory, it has no anchor.

2. **Stakes test.** The claim commits to something a serious critic could disagree with. If you can swap the claim for its plausible opposite and it still sounds reasonable as criticism, the claim is too soft. A `strong_interpretation` no working critic would push back on is not a strong interpretation; it is a paraphrase of the consensus.

3. **Non-obvious test.** A reader who has read two reviews of this book should still learn something here. Consensus criticism ("Orwell shows how power corrupts", "this book is about totalitarianism") does not earn its space.

4. **Compression test.** The claim can be paraphrased in one tight sentence without losing what is load-bearing. If you cannot compress it, it is fog dressed as depth.

5. **Removable-sentence test.** Cut any sentence. If the reader loses nothing measurable — no new image, no new claim, no new question they could not have asked before — cut it.

### Banned generic moves

These patterns produce filler. Refuse them when drafting; cut them when reviewing.

- **Abstract noun without textual instance.** Replace "the politics of memory" with the specific phrase, song, or commandment being remembered, edited, or banned. Replace "moral language" with the specific words the book actually fights over.
- **Rival reading the author would endorse.** A rival reading must be a reading the original author would *resist*. "也可以从怀旧角度读" / "it can also be read as..." is almost always a hedge, not a rival. Test: would the author push back? If no, it is not a rival reading. Real rival readings make a different claim about what the book is doing — not the same claim in softer vocabulary.
- **Question answerable without the book.** "Why are loyal people politically unsafe?" is a political-theory question. "Boxer says 'I will work harder' — at which appearance does the phrase stop belonging to him?" is a question this book answers. If an educated reader who has not opened the book can attempt the question, sharpen it.
- **Listening point that names a theme.** "Listen for how the revolution begins" is a summary instruction. "Listen for the first phrase Squealer repeats verbatim — that repetition is the moment language stops belonging to the animals" names a moment. Each `listening_brief.points` entry should point at a specific phrase, scene, or repetition.
- **"Why this matters" as gravity, not stakes.** "It teaches us how power works" is true of every political book. State the specific thing *this* book can teach that another cannot.
- **Chapter thesis = plot paraphrase.** A `chapter_thesis` states what this chapter does *to the book*, not what happens *inside* the chapter. "Establishes the founding ideology" is summary. "Plants the four phrases the next nine chapters will fight over" is a thesis.
- **Blind spots as boilerplate.** "Allegory compresses complexity" is true of every allegory. Name what *this* book misses that a *specific* alternative text or tradition gets right, and why the omission matters.

### Per-field standards

- `central_thesis`: one sentence; the strongest claim about the book this companion commits to. Must pass anchor + stakes.
- `strong_interpretation`: the reading you would defend in a graduate seminar against the standard reading. Must pass stakes — someone serious would argue back.
- `blind_spots`: must name something this book misses that a *specific* alternative tradition or text gets right. No generic "allegory compresses complexity."
- `rival_reading`: a reading the author would resist. Test: would the author push back? If no, it is not a rival.
- `chapter_thesis`: what the chapter does to the book, not what happens inside it.
- `why_pivotal`: must specify which later moment loses meaning if the reader does not hear this one.
- `deeper_interpretation`: must anchor at least one specific moment, line, or repetition. No claim that is only a general thesis floating above the chapter.
- `questions_to_carry`: each question must be one the text answers, refuses to answer, or makes harder. A reader who has not opened the book cannot attempt it.
- `what_to_watch` / `listening_brief.points`: each entry names a specific phrase, scene, repetition, or pattern to notice — not a theme to track.

## Sharper Critic Pass

This pass is mandatory before EPUB assembly. It is the discipline that makes the Depth Tests bite.

Procedure:

1. Re-read every interpretive claim in the draft `companion.json` as if you were a literary or political critic who has taught this book for twenty years. Cover: book-level `companion_zh`, `summary_en`, every field under `teacher_mode`, every field under each chapter's `mini_lecture`, every `listening_brief.points` entry, every `companion.zh` and `companion.en` body, every `recap`.

2. For each claim, run the five Depth Tests. Mark every failure with the named test it fails. Be specific: not "this is weak", but "this fails the anchor test — no scene named" or "this fails the stakes test — Orwell would agree".

3. For each marked failure, choose one:
   - **Anchor.** Add the specific phrase, scene, line, or repetition the claim hangs on.
   - **Sharpen.** Rewrite to a load-bearing claim that earns its space — something a serious critic would have to argue against.
   - **Cut.** If the claim cannot be anchored or sharpened without rewriting it into a different claim, delete the sentence.

4. After revising, re-read the draft as the critic. Ask: would another serious reader of this book read this revision and think "yes, but you didn't earn that"? If yes, anchor harder or cut.

5. Iterate. The draft does not ship until two conditions hold simultaneously:
   - A pass produces fewer cuts than the previous pass (the draft is converging).
   - At least one rival reading in the book-level `teacher_mode` would make the author push back, not nod.

Refuse to skip this pass. Refuse to declare convergence on the first pass. A first pass that produces no cuts means the pass was not honest, not that the draft was already sharp.

Operating questions to use while running the pass:

- Which sentences could I cut without losing anything a reader will notice? Cut those.
- Which claims could appear unchanged in a companion for a different book by the same author? Anchor or cut.
- Which "rival readings" would the author cheerfully endorse? Replace with a reading the author would resist.
- Which questions could be asked by someone who has only read reviews of the book? Sharpen until the question requires the text.
- Which interpretations sound like the consensus of educated readers? Either commit to a stronger claim or cut the sentence.

## Book-Type Adaptation

Adjust teacher mode by book type.

- Fiction and literature: focus on form, symbols, moral tension, psychology, politics, and what the narrative reveals about human life.
- History, biography, and politics: focus on argument, evidence, framing, omissions, ideology, and how the author wants the reader to judge events.
- Philosophy, social thought, and theory: focus on claims, logic, assumptions, tensions, objections, and what follows if the argument is right.
- Technical and knowledge books: focus on the core model, practical insight, hidden assumptions, community disagreement, and what is genuinely essential.

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
- Every interpretive claim — book-level companion, every `teacher_mode` field, every key-chapter `mini_lecture` field, every `listening_brief.points` entry, every `companion.zh` body — passes the five Depth Tests.
- No banned generic moves remain in the final draft.
- At least one rival reading in the book-level `teacher_mode` genuinely disagrees with the main interpretation; the author would push back on it, not nod.
- The Sharper Critic Pass has been run, converged, and produced fewer cuts in its final iteration than its first.

## Final Response Requirements

When a customized EPUB is produced, the final response must include:

- Output EPUB path.
- Target book folder.
- Source EPUBs used.
- Whether Chinese text came from a source EPUB or from translation.
- Any unresolved alignment or source-quality issues.
- Any sections intentionally summarized, flagged, or made optional for listening.

Keep the final response concise and practical.
