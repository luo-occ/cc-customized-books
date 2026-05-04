# Listening Content-Only EPUB Refinement

## Goal

Refine the reusable EPUB framework so the main listening EPUB contains only book-learning content. Anything about source editions, pairing mechanics, references, or build provenance should stay out of the listening flow.

This change is driven by the user's actual listening experience with the Animal Farm output: material such as pairing explanations, reference sections, edition/source labels, and other artifact-oriented notes feels like noise when heard aloud.

## Core Rule

If a piece of text does not help the user understand the book itself, it should not appear in the listening EPUB.

## Main Listening Flow

The allowed listening flow is:

1. Book Companion
2. Chapter Listening Brief
3. Chapter Companion Reference
4. Chinese chapter
5. Vocabulary For Listening
6. English chapter
7. Chapter Recap

This flow remains structured and labeled, because the user wants to keep the current labeled organization for book and chapter guidance.

## Content Allowed In The Listening EPUB

Allowed content is limited to material that supports comprehension of the book:

- What the book is about
- Why the book matters
- Author background and writing context
- Historical, cultural, political, technical, or intellectual context
- Major themes and tensions
- Important controversies or interpretive disagreements
- Reading/listening strategy
- Chapter-level context, names, ideas, and reading priority
- Vocabulary explanations
- Chinese and English chapter text
- Short recaps

## Content Excluded From The Listening EPUB

The following must not appear inside the main EPUB reading/listening flow:

- Pairing maps
- References and further reading lists
- Reference labels meant only for audit or sourcing
- Source-edition notes
- Provenance text such as `English source text from ...` or `Chinese source text from ...`
- Chapter alignment diagnostics
- Inclusion/exclusion notes about frontmatter, appendices, or edition-specific materials
- Build-process explanations
- Any artifact-oriented or typography-oriented descriptions

These may still exist as sidecar outputs, but not as part of the listening EPUB content.

## Book Companion Rule

The Book Companion remains substantial and can keep labeled subsections, but every subsection must stay book-focused.

Allowed:

- Book summary
- Context and background
- Themes and tensions
- Historical or cultural framing
- Interpretive disagreements
- Listening guidance and pacing advice

Not allowed:

- `References For Visual Review`
- Pairing explanations
- Edition-handling explanations
- Build explanations
- Anything that describes how the customized EPUB was produced

The Book Companion should feel like a guide to the book, not a guide to the artifact.

## Chapter Flow Rule

Each chapter package must also remain content-only.

Allowed:

- Listening Brief
- Companion Reference
- Chinese chapter
- Vocabulary For Listening
- English chapter
- Recap

Not allowed:

- Source-edition descriptions
- Provenance labels
- Alignment confidence notes unless a real unresolved issue materially affects comprehension

If a source-quality or alignment issue matters, it should be surfaced outside the listening flow in a sidecar artifact or build report.

## Sidecar Artifact Rule

The framework should still generate non-listening artifacts where useful, especially:

- `pairing-map.md`
- Build-time warnings
- Optional alignment or inclusion notes

However, these are sidecar outputs only. They should not be rendered into the listening EPUB.

## Framework Changes

### Renderer

Update the renderer so it does not emit listening-facing reference sections or other artifact-oriented blocks.

In particular:

- Remove book-level rendered reference lists from the listening EPUB
- Do not add any source/provenance labels to chapter pages
- Keep the current labeled structure for actual learning content

### Builder

Keep generating the pairing map sidecar file, but do not inject source notes or pairing metadata into the rendered EPUB pages.

The builder may still validate source files and pairings internally. The result of that validation should stay in:

- Exceptions when the build cannot proceed
- Sidecar files
- Final build/report output

It should not become narrated listening content by default.

### Content Contract

`companion.json` remains the container for book/chapter learning content.

References may remain present in JSON for audit, future tooling, or alternate edition outputs, but the listening renderer should ignore them unless a future non-listening mode explicitly uses them.

### Agent Guide

Update `AGENTS.md` to make the default output rule explicit:

- Listening EPUBs are content-only
- References, pairing details, and source provenance belong outside the main EPUB
- Provenance text should be omitted unless the user explicitly asks for an audit/study edition

## Error Handling

If the agent discovers a meaningful source mismatch or quality problem:

- Do not narrate the issue inside the EPUB chapter flow by default
- Report it separately in sidecar files or the final response
- Only place it in the listening EPUB if the user explicitly requests an audit-oriented edition or if the issue directly changes the meaning of the book content and cannot otherwise be handled

## Testing

Add or update tests to protect this rule:

- Book companion rendering should not include reference sections in the listening EPUB
- End-to-end builder smoke tests should confirm that reference/provenance text is absent from the generated EPUB
- Pairing-map output should still be generated as a sidecar artifact

## Success Criteria

The refinement is successful when:

1. The listening EPUB contains only book-relevant learning content and source text
2. Pairing and provenance details remain available outside the EPUB
3. Book Companion and chapter guidance stay rich without sounding like build documentation
4. The Animal Farm output no longer includes the kinds of listening noise the user identified
