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
