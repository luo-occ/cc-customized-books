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
