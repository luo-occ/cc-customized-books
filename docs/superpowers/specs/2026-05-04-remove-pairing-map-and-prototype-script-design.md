# Remove Pairing Map And Prototype Script Design

## Goal

Clean up the repository so it reflects the real reusable pipeline:

- remove the old one-off `scripts/build_animal_farm_custom_epub.py` prototype
- stop generating `pairing-map.md`
- remove the tracked `output/Animal Farm/pairing-map.md`
- keep chapter pairing validation inside the framework, but make it an internal check rather than a user-facing artifact
- keep `output/` for final user-facing EPUBs only

## Why This Change

The project has already moved from a one-off Animal Farm script to a reusable EPUB framework with `book_projects/<slug>/` content files. The leftover prototype script and pairing-map artifact now create the wrong mental model:

- the prototype script suggests there are still two pipelines
- the pairing-map file makes `output/` look like a debug folder instead of a user-facing deliverable folder

The user wants the repository to stay focused on one reusable process and one meaningful output.

## Cleanup Scope

### Remove Prototype Script

Delete:

- `scripts/build_animal_farm_custom_epub.py`

It is no longer part of the supported workflow and should not remain in the repository.

### Remove Pairing Map Output

Delete:

- `output/Animal Farm/pairing-map.md`

And stop generating pairing-map files in future builds.

### Keep Pairing Validation, Remove Pairing Artifact

The framework should still:

- validate that English and Chinese chapter pairings point to valid source hrefs
- fail clearly when pairings are invalid or inconsistent

But it should no longer:

- write a pairing map file to disk
- expose pairing-map output as part of the normal build result
- report a pairing-map path in CLI output

## Code And Config Changes

### Project Config

Remove `output.pairing_map` from `book_projects/<slug>/project.json`.

### Model Layer

Remove `pairing_map` from `BookProject`.

### Builder

Keep `validate_pairings(...)`, but remove:

- pairing-map directory creation
- pairing-map markdown rendering
- pairing-map path from `BuildResult`

### CLI

`scripts/build_custom_epub.py` should print only the final EPUB path.

## Test Changes

Update tests so they no longer require:

- `pairing_map` in fixture project configs
- `result.pairing_map.exists()`
- pairing-map content assertions

Tests should continue to verify:

- pairing validation still runs
- EPUB build still succeeds
- listener-facing output stays clean

## Documentation Changes

Update `AGENTS.md` and other project docs so they no longer describe pairing maps as generated output files.

They may still describe explicit chapter pairing decisions as an internal workflow step, but not as a required sidecar artifact.

## Output Behavior After Cleanup

After this change:

- `output/<Book>/` should contain the customized EPUB only
- no pairing-map markdown file should be generated
- invalid pairings should still fail clearly
- no one-off Animal Farm build script should remain in the repository

## Success Criteria

This cleanup is successful when:

1. `scripts/build_animal_farm_custom_epub.py` is gone
2. `output/Animal Farm/pairing-map.md` is gone
3. The reusable builder no longer writes pairing-map files
4. The CLI reports only the EPUB output path
5. Tests pass after the cleanup
6. The project still validates chapter pairings before building
