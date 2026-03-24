# Living Art Release Checklist

Use this checklist when promoting living-art changes that touch render logic, preview/export behavior, docs, or workflow handling.

## Preflight

- Confirm the branch only changes intended living-art surfaces or approved release collateral.
- Confirm `metrics.json` and `history.json` fixtures used for review are representative, not degenerate smoke data.
- Confirm the README still links GIF previews to their richer SVG sources.

## Validation

- Run `uv run pytest tests/test_living_art_dark_mode_contrast.py tests/test_living_art_e2e_rehearsal.py`.
- Run any focused living-art regressions needed for the touched generator or CLI surface.
- If workflow logic changed, validate the YAML structure and inspect the job graph for unchanged upstream/downstream dependencies.

## Artifact review

- Review `inkgarden-growth-animated.svg` and `topo-growth-animated.svg` for staged reveal integrity.
- Review `inkgarden-growth.gif` and `topo-growth.gif` for GitHub-safe playback.
- Review any generated `living-*.gif` timelapses only if the release changed export behavior.
- Check output sizes for obvious regressions before merging.

## Docs and communication

- Confirm [docs/content/docs/scripts/topography.mdx](../docs/content/docs/scripts/topography.mdx) matches the current mapping and static-export semantics.
- Confirm [docs/content/docs/scripts/world-state.mdx](../docs/content/docs/scripts/world-state.mdx) matches the current shared signal model.
- Confirm [docs/content/docs/scripts/living-art-modes.mdx](../docs/content/docs/scripts/living-art-modes.mdx) matches the current preview/export contract.

## Merge gate

- Merge only after tests, docs, artifact review, and workflow inspection all pass.
- If any preview artifact is readable only in the SVG source but not in the flattened GIF, treat that as a blocker.
