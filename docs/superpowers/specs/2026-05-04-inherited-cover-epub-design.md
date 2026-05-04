# Inherited Cover EPUB Refinement

## Goal

Refine the reusable EPUB framework so customized books inherit a real source-book cover instead of shipping with a newly generated shell that loses the original cover identity.

The customized EPUB should keep the original book’s visual identity while preserving the existing listening-first reading flow.

## Core Rule

Every customized EPUB should inherit a real cover image from the source book rather than inventing a new one.

Default behavior:

1. Try to extract the cover from the English source EPUB.
2. If that fails, fall back to the Chinese source EPUB.
3. Embed that image as the customized EPUB cover.

This is a book-identity rule, not a content or narration rule.

## Cover Detection Strategy

Real EPUBs do not all store covers the same way, so the framework should use a small best-effort detection sequence while still keeping behavior deterministic.

Recommended detection order:

1. Check EPUB metadata or manifest for an item explicitly marked as cover.
2. Check common cover-related ids, properties, and href names such as `cover`, `cover-image`, `cover.jpeg`, `cover.jpg`, `cover.png`, or similar variants.
3. If that fails, inspect early frontmatter documents for a dominant `<img>` that appears to be the visual cover.

Once found:

- Extract the original image bytes
- Preserve the original media type when possible
- Register the image as the output EPUB cover

The framework should not redesign or regenerate the cover.

## Process Changes

### EPUB I/O Layer

Add reusable helpers for cover extraction so cover logic stays separate from build orchestration.

The I/O layer should be responsible for:

- discovering the cover candidate
- reading the image bytes
- returning the cover asset path, media type, and bytes

### Builder

The builder should resolve the inherited cover before final EPUB writing.

Behavior:

1. Try English EPUB cover extraction
2. If no English cover is found, try Chinese EPUB cover extraction
3. If a cover is found, attach it to the generated EPUB
4. If no cover is found at all, continue building without failing, but surface a warning

This keeps the output robust while making cover inheritance the default.

### Tests

Add fixture-based tests that prove:

- English cover is preferred when available
- Chinese cover is used only as fallback
- The generated EPUB includes a registered cover asset

These tests should stay small and mechanical.

## Output Behavior

This refinement changes only the visual cover asset.

It should not:

- add a new narrated cover page
- add book-companion notes about where the cover came from
- add source or edition notes into the listening flow
- redesign the artwork

The result should simply open like the customized book naturally inherited the original cover.

## Error Handling

If cover extraction fails:

- do not fail the entire build by default
- continue the EPUB build
- surface the missing-cover condition as a warning or reportable build detail

This is lower severity than missing chapter content or broken pairings.

## Success Criteria

The refinement is successful when:

1. Customized EPUBs preserve the source-book visual identity
2. English cover is used by default when present
3. Chinese cover is used only as fallback
4. The listening flow remains unchanged
5. No cover provenance text leaks into the EPUB content
