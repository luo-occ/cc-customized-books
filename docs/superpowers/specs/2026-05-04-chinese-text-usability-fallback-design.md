# Chinese Text Usability Fallback Design

## Goal

Fix the current `Animal Farm` bug where the Chinese chapter bodies in the customized EPUB are unusable for listening, and establish a reusable framework rule so this does not happen again for future books.

The core rule is simple:

- use Chinese source chapter text only when it is genuinely readable
- never use image-only chapter pages as listening content
- never use OCR garbage just because it exists
- when usable Chinese text is missing, fall back chapter-by-chapter to generated Chinese translation from the English chapter

## Why This Change Is Needed

The current `Animal Farm` Chinese source EPUB contains chapter XHTML files that are only scanned page images wrapped in `<img>` tags. The old logic treated “Chinese EPUB exists” as equivalent to “Chinese chapter text exists,” which is false for listening use.

That led to a broken result:

- the listening EPUB showed unusable Chinese chapter bodies
- the Chinese content was not real TTS-readable text
- the build process did not make a chapter-level usability decision before choosing the Chinese source

For this project, an image-only Chinese chapter is effectively the same as missing Chinese text.

## Usable Chinese Rule

For listening EPUBs, a Chinese source chapter counts as usable only if it contains genuinely readable text.

Not usable:

- image-only chapter pages
- scanned page XHTML that only embeds images
- OCR garbage that is effectively unreadable
- chapter bodies with no meaningful Chinese text

Usable:

- real Chinese prose or dialogue that can be read aloud naturally by TTS
- chapter text with ordinary formatting noise but readable language

If a Chinese chapter is not usable, the builder should treat that chapter as missing Chinese text for listening purposes.

## Fallback Behavior

When a chapter’s Chinese source is unusable:

1. do not use the scan image as the chapter content
2. do not use OCR garbage
3. generate a faithful, readable Chinese translation from the English chapter
4. use that translation as the Chinese chapter in the main listening EPUB

This fallback should happen at the chapter level, not only at the whole-book level.

That means a future book can mix:

- source Chinese text for readable chapters
- generated Chinese translation for unreadable or missing chapters

## Process Changes

### Chapter-Level Usability Detection

Add a check that decides whether each Chinese chapter is:

- readable text
- image-only
- unreadable OCR-like text

The builder should not assume that the presence of a Chinese EPUB means the chapter is suitable for listening.

### Translation Source Of Truth

When fallback is needed, the replacement Chinese should come from translation of the English chapter, not from scan-image extraction and not from OCR salvage.

### Metadata Location

If the project needs to record which chapters used source Chinese versus generated translation, that metadata belongs in `book_projects/<slug>/`, not in `output/`.

The final `output/` directory should remain EPUB-only.

## Immediate Fix For Animal Farm

For the current `Animal Farm` customized EPUB:

1. stop using the image-only Chinese chapter files as the main Chinese chapter bodies
2. treat all ten main Chinese chapters as unusable for listening
3. provide generated Chinese translation for those chapters
4. rebuild the EPUB so the Chinese section is real readable text again

This is both:

- an immediate bug fix for the broken `Animal Farm` output
- a reusable framework rule for future books

## Success Criteria

This change is successful when:

1. the `Animal Farm` Chinese chapters in the customized EPUB are real readable text
2. the builder no longer treats image-only Chinese chapter pages as valid listening content
3. the framework never falls back to OCR garbage
4. chapter-level Chinese fallback to translation is supported
5. `output/` still contains EPUB only
