# Reusable EPUB Framework Design

Date: 2026-05-03
Status: Approved for specification review

## Context

The project now has an `AGENTS.md` guide for producing TTS-first bilingual study EPUBs. An Animal Farm run produced a working one-off script at `scripts/build_animal_farm_custom_epub.py`, an output EPUB, and a pairing map.

That script proves the workflow is practical, but it is not a good permanent foundation. It hardcodes absolute paths, Animal Farm chapter metadata, Animal Farm companion notes, references, vocabulary entries, and output names. Recreating a full script for every book would repeat fragile mechanical work and make quality inconsistent.

## Goal

Build a reusable Python framework that handles deterministic EPUB mechanics and leaves book-specific judgment to agent-authored project files.

The framework should let a future agent:

1. Inspect source EPUBs.
2. Create or verify a chapter-level pairing map.
3. Fill a per-book companion data file.
4. Run one reusable command to build the customized EPUB.
5. Run validation checks that protect listening quality and source alignment.

## Non-Goals

The framework will not generate deep companion notes, literary analysis, historical research, or final vocabulary explanations by itself. Those remain agent-authored per book.

The first implementation will not build a GUI, database, web app, paragraph-level aligner, or fully automatic translation system.

The existing Animal Farm one-off script should be treated as prototype material, not as the final architecture. It can be mined for proven helper logic and sample content, but the reusable framework should have clean modules and tests.

## Recommended Architecture

Create a reusable package under `scripts/custom_epub/` and a small CLI entrypoint:

```text
scripts/
  build_custom_epub.py
  custom_epub/
    __init__.py
    models.py
    epub_io.py
    pairing.py
    vocabulary.py
    tts.py
    render.py
    builder.py
    templates/
      style.css
book_projects/
  animal-farm/
    project.json
    companion.json
```

The CLI should accept a project directory:

```bash
python3 scripts/build_custom_epub.py book_projects/animal-farm
```

The output should go to the path declared by `project.json`, usually under `output/<Book Name>/`.

## Responsibilities

### `models.py`

Define typed dataclasses or plain structured models for:

- Book project metadata.
- Source EPUB paths.
- Chapter pairings.
- Book companion content.
- Chapter listening brief.
- Chapter companion reference.
- Vocabulary groups.
- Chapter recap.
- Optional reference sections.

The model layer should make the expected per-book data shape obvious and testable.

### `epub_io.py`

Handle source EPUB mechanics:

- Read `META-INF/container.xml`.
- Resolve OPF path.
- Parse OPF manifest and spine.
- Locate NCX navigation where available.
- Extract flattened navigation entries.
- Extract body fragments from selected spine items.
- Clean unsafe or noisy attributes while preserving useful anchors and images.

It should avoid hardcoded root paths and should work with EPUBs that store files under different internal directories.

### `pairing.py`

Create and validate chapter-level pairing maps.

It should support:

- Loading pairings from `project.json`.
- Reporting missing, extra, uncertain, abridged, reordered, or image-only sections.
- Rendering `pairing-map.md` for the output folder.
- Refusing to silently drop frontmatter, epilogues, notes, appendices, acknowledgments, photographs, maps, indexes, or image-heavy sections.

The framework should not guess risky alignments without making the uncertainty visible.

### `vocabulary.py`

Provide helper functions for vocabulary scaffolding:

- Load `glossary/english_words.txt`.
- Find glossary words present in a chapter.
- Normalize simple English tokens.
- Optionally produce candidate lists for the agent to review.

The final explanations and priority grouping may still come from `companion.json`; the helper should reduce busywork, not replace judgment.

### `tts.py`

Protect listening quality:

- Detect raw listener-facing URLs.
- Strip or flag OCR clutter, page-number noise, repeated running headers, and symbol-heavy fragments.
- Provide text checks for long parenthetical chains and dense table-like content.
- Offer helpers to render readable source labels instead of raw URLs.

Validation should fail or warn when listener-facing sections contain raw URLs.

### `render.py`

Render XHTML pages and shared CSS:

- Title page.
- Book companion.
- Edition notes.
- Chapter listening brief.
- Chapter companion reference.
- Chinese chapter.
- Vocabulary for listening.
- English chapter.
- Chapter recap.
- Optional visual-reference sections.

Rendering should use stable section names from `AGENTS.md` so the output table of contents is predictable.

### `builder.py`

Coordinate the build:

- Load `project.json` and `companion.json`.
- Extract source content according to the pairing map.
- Render all pages.
- Assemble the EPUB with `ebooklib`.
- Write output EPUB and pairing map.
- Run final validation checks.

## Per-Book Data Files

### `project.json`

Stores deterministic project configuration:

- Book slug and display title.
- English EPUB path.
- Chinese EPUB path, if present.
- Output EPUB path.
- Pairing rows.
- Optional source sections to include, summarize, omit, or mark as visual-only.
- Metadata such as author, language, and description.

### `companion.json`

Stores agent-authored learning content:

- Book-level companion.
- Human-readable references without raw listener-facing URLs.
- Chapter listening briefs.
- Chapter companion notes.
- Vocabulary groups and explanations.
- Recaps.
- Pronunciation hints.

This separation keeps the builder reusable and keeps creative judgment visible in a reviewable file.

## Animal Farm Migration

The existing `scripts/build_animal_farm_custom_epub.py` should be used as a migration source:

- Move general EPUB parsing logic into `epub_io.py`.
- Move pairing-map rendering into `pairing.py`.
- Move CSS and XHTML rendering patterns into `render.py` and `templates/style.css`.
- Move Animal Farm metadata, chapter notes, vocabulary, recaps, and references into `book_projects/animal-farm/project.json` and `companion.json`.
- Replace the one-off script with the reusable CLI.

The Animal Farm output should be reproducible through:

```bash
python3 scripts/build_custom_epub.py book_projects/animal-farm
```

The first reusable build does not need to be byte-for-byte identical to the current prototype EPUB, but it must preserve the structure and learning intent.

## Data Flow

```text
books/<Book>/*.epub
glossary/*
book_projects/<slug>/project.json
book_projects/<slug>/companion.json
        |
        v
scripts/build_custom_epub.py
        |
        v
scripts/custom_epub/*
        |
        v
output/<Book>/pairing-map.md
output/<Book>/<Title>.epub
```

## Error Handling

The CLI should fail with clear messages when:

- Source EPUB paths do not exist.
- OPF or navigation files cannot be located.
- Pairing rows reference missing source labels or hrefs.
- Required companion content is missing for a paired chapter.
- Listener-facing content contains raw URLs.
- Output EPUB cannot be written.

It may warn, rather than fail, when:

- A chapter has no optional recap.
- Glossary candidate words are empty.
- Optional reference sections are omitted by configuration.

## Testing Strategy

Use TDD for implementation.

Add focused Python tests for:

- OPF path discovery from `container.xml`.
- Manifest, spine, and NCX navigation parsing.
- Pairing-map rendering.
- Raw URL detection in listener-facing content.
- Glossary matching.
- Loading and validating `project.json` / `companion.json`.
- Rendering expected TOC labels.

Prefer small fixture EPUB-like zip files for parser tests instead of relying only on large real book files.

Add an integration smoke test that runs the Animal Farm project build and verifies:

- The EPUB file is created.
- The pairing map is created.
- The EPUB archive contains expected chapter files.
- No raw URLs appear in listener-facing XHTML files.
- The generated table of contents includes `Book Companion`, `Chapter 1 Listening Brief`, `Chapter 1 Companion Reference`, `Chapter 1 Chinese`, `Chapter 1 Vocabulary For Listening`, `Chapter 1 English`, and `Chapter 1 Recap`.

## Documentation Updates

Update `AGENTS.md` after the framework exists:

- Agents should use the reusable framework instead of generating a fresh script.
- Agents should generate or edit per-book `project.json` and `companion.json`.
- Agents should run the builder and validation checks.
- Agents may create book-specific helper scripts only for temporary investigation, and should not treat them as final deliverables.

## Success Criteria

The framework is successful when:

- Animal Farm can be rebuilt through the reusable CLI.
- The one-off Animal Farm script is no longer needed for normal operation.
- Future books can reuse the same builder by adding per-book project files.
- Mechanical EPUB operations are covered by tests.
- TTS/no-raw-URL quality checks are enforced.
- The agent guide clearly points agents toward the reusable workflow.
