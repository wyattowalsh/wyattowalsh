# Living Art Release Checklist

Use this checklist when promoting living-art changes that touch render logic, timelapse/export behavior, docs, or workflow handling.

## Preflight

- Confirm the branch only changes intended living-art surfaces or approved release collateral.
- Confirm `metrics.json` and `history.json` fixtures used for review are representative, not degenerate smoke data.
- Confirm README and docs describe the current timelapse-only contract (`living-*.gif` + manifest/preview) rather than legacy `*-growth*` outputs.

## Validation

- Run `uv run pytest tests/test_living_art_dark_mode_contrast.py tests/test_living_art_e2e_rehearsal.py`.
- Run any focused living-art regressions needed for the touched generator or CLI surface.
- If workflow logic changed, validate the YAML structure and inspect the job graph for unchanged upstream/downstream dependencies.

## Artifact review

- Review the generated `living-*.gif` timelapses for playback integrity.
- Review `living-art-preview.html` and `living-art-manifest.json` together so the indexed surface matches the files on disk.
- Check output sizes for obvious regressions before merging.

## Docs and communication

- Confirm [docs/content/docs/scripts/topography.mdx](../docs/content/docs/scripts/topography.mdx) matches the current mapping and static-export semantics.
- Confirm [docs/content/docs/scripts/world-state.mdx](../docs/content/docs/scripts/world-state.mdx) matches the current shared signal model.
- Confirm [docs/content/docs/scripts/living-art-modes.mdx](../docs/content/docs/scripts/living-art-modes.mdx) matches the current timelapse/index contract.
- Confirm [docs/content/docs/data/fetch-history.mdx](../docs/content/docs/data/fetch-history.mdx) still explains the history dependency truthfully.

## Merge gate

- Merge only after tests, docs, artifact review, and workflow inspection all pass.
- If any canonical timelapse GIF is unreadable, missing from the preview gallery, or misrepresented in docs/workflow text, treat that as a blocker.
