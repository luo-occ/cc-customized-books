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
