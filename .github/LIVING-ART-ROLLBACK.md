# Living Art Rollback Checklist

Use this when a living-art change causes unreadable previews, oversized artifacts, workflow failures, or signal-model regressions.

## Trigger conditions

- GIF previews render incorrectly or stop updating.
- Source SVGs regress visually or lose expected motion.
- Workflow runs stop producing one or more living-art outputs.
- Dark scenes lose readable contrast.
- Artifact size spikes enough to make README or workflow inspection impractical.

## Immediate actions

- Identify the last known-good commit for living-art outputs and workflow behavior.
- Compare the failing branch against the last known-good release for: render logic, CLI behavior, workflow staging, and docs promises.
- Preserve the failing workflow logs or staged artifact bundle before reverting.

## Rollback path

- Revert the smallest living-art change set that restores preview and source outputs.
- Restore the previous workflow artifact/staging behavior if the breakage is in CI rather than rendering.
- Re-run `uv run pytest tests/test_living_art_dark_mode_contrast.py tests/test_living_art_e2e_rehearsal.py` after the revert.
- Regenerate the living-art assets from the restored code path before re-merging.

## Post-rollback review

- Document whether the failure came from signal mapping, export flattening, dark-mode readability, or workflow handling.
- Update the release checklist if the failure exposed a missing gate.
- Keep the docs accurate: if a mode or export path is temporarily unavailable, remove or amend the claim before shipping again.
