# Agent-Guided Bilingual Study EPUB Design

Date: 2026-05-03
Status: Approved for specification review

## Context

This project helps the user read English books with less friction. The user is a native Chinese speaker who enjoys reading English originals but sometimes needs to compare Chinese and English editions. The project should guide future agents to produce customized EPUBs that keep the original English useful while adding Chinese support, vocabulary help, and deeper context.

The current repository contains:

- Paired English and Chinese EPUBs under `books/` for several books.
- A vocabulary profile at `glossary/vocabulary_profile.json`.
- A word list at `glossary/english_words.txt`.

The vocabulary profile estimates the user's reading level around upper-B2/lower-C1, with uneven but ambitious reading exposure. Future agents should use that profile as calibration guidance, not as an exact test result.

## Goals

Create a project-level agent operating guide, centered on `AGENTS.md`, that instructs future agents how to turn a book folder into a customized bilingual EPUB.

The output EPUB for each book should include:

- A substantial book-level bilingual companion section at the top.
- Recommended book-level outside research by default, especially for biography, history, politics, culture, technology, and idea-driven nonfiction.
- Deep book-level insights: author context, historical and cultural background, key themes, controversies or competing interpretations, why the book matters, what to read closely, what can be skimmed, and useful references.
- An optional reading plan when it would help, especially for long, dense, or difficult books.
- For each chapter: bilingual companion notes before the Chinese chapter, the Chinese chapter first, a learning-priority vocabulary section before the English chapter, then the English chapter second.
- Faithful, readable Chinese translation when no Chinese source EPUB exists.
- Audio/TTS-first structure and prose, because the user will usually listen to the output book with an AI reader.
- A final EPUB file as the required deliverable.

The EPUB should reduce the effort of reading English originals. It should not replace the English book, flatten the author's voice, or overload the reader with low-value notes.

Because the user usually listens to the book, the EPUB should prioritize listening flow. Deep notes should remain available, but they should not make the first-pass audio experience exhausting.

## Non-Goals

This first project is not a full automation pipeline. It should not require building a complete EPUB parser, chapter aligner, translation engine, or web application. The primary deliverable is a strong guide for agents.

The guide may mention useful tooling and intermediate formats, but it should not promise that every book can be processed automatically. Agents must use judgment when EPUB structure, chapter counts, frontmatter, images, notes, or appendices do not align cleanly.

## Recommended Approach

Use an `AGENTS.md` operating manual plus a quality checklist.

This balances flexibility and reliability. A manual-only guide would be too dependent on agent discipline. Templates would improve consistency but could become rigid across different genres. A guide plus checklist gives future agents room to adapt while making the important checks explicit.

## Workflow

The `AGENTS.md` guide should tell future agents to follow this workflow:

1. Inspect `books/` and identify the target book folder.
2. Detect English and Chinese EPUBs using metadata, filenames, language tags, and sampled text.
3. Extract each EPUB's table of contents and chapter files.
4. Pair chapters at chapter level only.
5. If chapter counts, chapter names, or source structures mismatch, create an explicit pairing map and surface the uncertainty instead of guessing silently.
6. Read `glossary/vocabulary_profile.json` and `glossary/english_words.txt` to calibrate vocabulary selection.
7. Create book-level deep bilingual companion notes, using outside research and references by default when helpful.
8. For each chapter, create both a concise listening brief and deeper bilingual companion notes before the Chinese chapter.
9. For each English chapter, create a learning-priority vocabulary list before the English chapter, written in a TTS-friendly style.
10. Add a short chapter recap after the English chapter when useful for retention.
11. Assemble the bilingual EPUB with a usable table of contents.
12. Run the quality checklist before finishing.

## Content Standards

### Book-Level Companion

The book-level companion should be substantial and bilingual. The main explanation should be in Chinese, followed by a concise English summary.

It should include:

- What the book is about.
- Why the book matters.
- Author background and writing context.
- Historical, cultural, political, technical, or intellectual context needed to understand the book.
- Major themes and tensions.
- Controversies, criticism, or competing interpretations where relevant.
- Community agreement or disagreement for technical and idea-driven books.
- A reading strategy tailored to the user.
- An optional reading schedule or pacing suggestion when the book is long, dense, or benefits from staged reading.
- Parts worth reading closely.
- Parts that can be skimmed.
- References and further reading.

Outside research is recommended by default for the book-level companion. Agents should prefer reputable sources and cite concise references. For modern facts, current public figures, laws, products, software, or community consensus, agents must verify with up-to-date sources.

Reader-facing text should not expose raw web URLs. If references are included in the EPUB, use human-readable source titles, publication names, author names, or short citation labels. Raw URLs may be preserved only as hidden hyperlink targets or in an optional visual-only references section that is clearly marked as skippable during listening.

### Chapter Companion

Each chapter should begin with a concise listening brief and companion notes before the Chinese chapter.

The listening brief is optimized for audio. It should be shorter than the deep notes and tell the user what to listen for: key names, 2-4 important ideas, pronunciation hints, and any context needed before hearing the chapter.

Chapter notes should be deep but not bloated. They should include Chinese explanation first and a concise English summary second.

They should cover:

- What happens, or what the chapter argues.
- Why the chapter matters in the whole book.
- Context that helps comprehension.
- Key people, places, ideas, terms, or events.
- Reading priority: read closely or skim lightly.
- Difficult cultural references or disputed claims when relevant.

Chapter notes should usually rely on the book and the book-level research. They should use additional outside research only when a chapter contains confusing, important, disputed, or context-heavy material.

Long background explanations, detailed source notes, and dense references should be marked as optional or visual-reference material when they would interrupt listening flow.

### Vocabulary

The vocabulary section appears immediately before the English chapter.

It should be a learning-priority list, not an exhaustive dump. Agents should combine:

- Words from `glossary/english_words.txt` found in the chapter.
- Likely blockers for an upper-B2/lower-C1 reader.
- High-value phrases, idioms, collocations, or specialist terms.

The vocabulary should be grouped into:

- Must know.
- Useful / high-value.
- Specialized or context-bound.

Each vocabulary item should include the English word or phrase, part of speech when useful, Chinese meaning, a short explanation, and a short example phrase from or close to the chapter when possible.

Agents should avoid over-listing obvious words, proper names that are better explained in context notes, and rare words that are not useful for future reading.

For audio quality, vocabulary entries should be written as readable mini-explanations instead of dense tables. Example format: `predicament, noun, 困境. It means a difficult or unpleasant situation. Listen for it when the author describes a person with no good options.`

Pronunciation help should be added for hard names, foreign names, technical terms, and words whose spelling may mislead TTS or the listener.

### Audio/TTS Optimization

The generated EPUB should be optimized for AI read-aloud by default.

Agents should:

- Use clear, complete sentences in generated notes.
- Prefer short sections with descriptive headings.
- Avoid raw URLs in all listener-facing text.
- Avoid dense Markdown-style tables, symbol-heavy lists, footnote clutter, page numbers, running headers, OCR artifacts, and long parenthetical chains.
- Replace visible URLs with readable source labels, such as `New York Times review`, `author interview`, or `publisher page`.
- Put detailed references, raw citation data, and visual-only material in clearly marked optional sections.
- Add pronunciation hints for difficult names, Chinese pinyin, historical figures, technical vocabulary, and unusual English words.
- Mark skippable sections with labels such as `Optional Reference` or `Detailed Background For Visual Review`.
- Keep source chapters uninterrupted once they begin, unless a note is essential for comprehension.
- Add a short bilingual chapter recap after the English chapter when useful.

The preferred chapter structure for listening is:

1. Chapter Listening Brief
2. Chapter Companion Reference
3. Chinese Chapter
4. Vocabulary For Listening
5. English Chapter
6. Chapter Recap

### Translation When Chinese Is Missing

If no Chinese EPUB is available, the agent should translate the English chapters into faithful, readable Chinese.

The translation should preserve meaning, tone, argument, and narrative flow while avoiding stiff literal Chinese. It should not freely adapt or simplify the text unless a note explains why.

## EPUB Structure

The final EPUB should be readable and navigable. It should preserve the original book order and include a clear table of contents.

Recommended table of contents pattern:

1. Book Companion
2. Chapter 1 Listening Brief
3. Chapter 1 Companion Reference
4. Chapter 1 Chinese
5. Chapter 1 Vocabulary For Listening
6. Chapter 1 English
7. Chapter 1 Recap

The same pattern should repeat for each chapter or major section. Frontmatter, epilogue, notes, appendices, acknowledgments, image-heavy sections, and indexes should not be silently skipped. The agent should decide how to include, summarize, or flag them.

## Quality Checklist

Before finishing, the agent must verify:

- Correct English and Chinese source book pairing.
- Chapter count and chapter order.
- Any mismatched chapters have an explicit pairing map.
- No silent skips of frontmatter, epilogue, notes, appendices, acknowledgments, image-heavy sections, or indexes.
- Chapter notes are bilingual and placed before the Chinese chapter.
- Chinese appears before English for each paired chapter.
- Vocabulary appears immediately before the English chapter.
- Vocabulary is prioritized for learning value and calibrated to the user's profile.
- Book-level outside research includes useful references and deep insights.
- Raw web URLs do not appear in listener-facing text.
- Generated notes, vocabulary, and references are TTS-friendly.
- Pronunciation guidance is included for hard names and terms where useful.
- Chapter notes are helpful without burying the source text.
- Optional or visual-reference material is clearly marked as skippable during listening.
- EPUB opens successfully.
- Table of contents is usable.
- Final response gives the output path and mentions unresolved alignment or source-quality issues.

If EPUB tooling is unavailable, the agent should create an intermediate structured HTML/XHTML package, explain the blocker clearly, and continue aiming for EPUB as the required final output.

## Error Handling And Judgment

Agents should pause and surface issues when:

- The target folder contains multiple plausible English or Chinese books.
- Metadata and sampled text disagree about language.
- The English and Chinese editions have different chapter counts.
- A Chinese edition appears abridged or reordered.
- A source EPUB has OCR errors, missing text, broken table of contents, or image-only pages.
- Notes, appendices, or indexes are too large to include naturally.

The default response should be to create a clear pairing or inclusion plan, then proceed only when the risk is understood. Agents should not silently drop material or invent missing source text.

## Testing And Verification

Because the first deliverable is a guide, verification should focus on the guide's completeness and future usability:

- Confirm `AGENTS.md` describes the full workflow from source inspection to EPUB output.
- Confirm the quality checklist covers pairing, chapter order, vocabulary placement, context notes, references, and EPUB validation.
- Confirm the guide reflects the user's choices: chapter-level alignment, deep bilingual companion notes, learning-priority vocabulary, faithful readable translation, TTS-first listening flow, no raw listener-facing URLs, and an agent-guide-first project shape.
- Confirm instructions are concrete enough for another agent to follow without rereading this design discussion.

Implementation can later add scripts or templates, but those are outside this first design unless the user explicitly expands scope.
