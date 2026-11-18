# Plan — outstanding-work-closeout

Reconcile the dirty `dev` tree to the accepted facts, then fix the verified fail-open and false-doc paths. Land a cleaned dependency bump on `dev`, commit, push `dev`, and close PRs #12 and #14. Do not edit `main`, change the default branch, regenerate living-art GIFs, or regenerate the pinned banner pair.

Human gates stay open: classic PAT revoke, Actions billing lock, living-art `accepted[]`, Redis tasks 5.1–5.4, badge Camo check 3.2, and remote updater proof 9.5.

## Steps

### 1. Reconcile the dirty asset diff

Files: `.github/assets/img/generative-*.svg`, `docs/public/showcase/*` that the generator and docs still name, `docs/content/docs/workflows/index.mdx`, `scripts/banner.py`, `tests/test_banner.py`.

- Restore generative activity/community SVGs, dark variants, and the showcase files deleted in the worktree whose names the generator and docs still emit. Keep `metrics.svg`, `metrics.additional.svg`, and `metrics.extra.svg` deleted.
- Change the workflows doc so it no longer says those legacy metrics files may remain.
- Revert `BannerConfig` width and height to 1600 and 480. Leave every other banner drawing path untouched.
- Keep the coherent dirty edits: workflow default `contents: read` with finalize `contents: write`, `generate all` exiting 1 on a failed step, removal of the `config.py` `__main__` scaffold, `.env.example` X placeholders, CONTRIBUTING's `dev` PR target, `docs/vercel.json` `ignoreCommand`, and the AGENTS.md ship-dev / ST-03 / ST-04 text.
- Remove the untracked `.grok/workflows/readme-sep-cumulative.rhai` file. Its README and cumulative-snapshot work is already on `dev`.

Verify: `uv run python -m pytest tests/test_banner.py tests/test_metrics_svg.py tests/test_overhaul_fact_ids.py -q --tb=line -n0` for the size and lowlighter assertions, plus a file-exists check for the restored generative SVGs.

### 2. Fail closed on required surfaces

Files: `scripts/readme_sections.py`, `scripts/skills.py`, `scripts/cli/generate/readme_cmd.py`, `scripts/fetch_metrics.py`, `scripts/supplemental_metrics.py`, and the matching tests.

- Blog fetch errors must not replace the existing blog marker block. A feed that parses and is empty may say there are no posts.
- `generate skills` and `generate readme-sections` exit non-zero when the README is missing or their marker pair is missing.
- Supplemental generation fails when language totals or the contribution calendar are missing because collection failed. Missing Spotify, X, or WakaTime secrets omit those cards and do not fail the command.

Verify: new unit tests around the blog sentinel, missing markers, and a collector failure versus a missing secret. No live API calls.

### 3. Close the other verified behavior gaps

Files: `scripts/cli/generate/word_cloud.py`, `scripts/cli/preview.py`, `scripts/cli/generate/art.py`, `scripts/art/animate.py`, `scripts/utils.py`, `scripts/config.py`, `scripts/wakatime_readme.py`, `scripts/spotify_auth.py`, `scripts/cli/auth.py`, `.gitignore`, `.github/workflows/profile-updater.yml`, `scripts/cli/generate/all_cmd.py`.

- Pass `--renderer` through the prompt and techs helpers. A markdown run without `--output-path` must not write a non-typographic render over `wordcloud_typographic_by_topics.svg` or `wordcloud_typographic_by_languages.svg`.
- `preview skills` copies the README into the preview directory. `preview generative` uses a fixture metrics file instead of exiting only because `--metrics-path` was omitted.
- `generate animated` passes `timeline=False` for every style and exits non-zero when no metrics file is given and the profile is not `wyatt` or `prolific`.
- `generate all` runs WakaTime when `WAKATIME_API_KEY` is set and continues without failing when it is absent.
- `LOG_LEVEL` sets the Loguru console level. Honor `DEBUG_MODE` or remove it from the documented controls. Avoid the `scripts.config` circular import by reading the environment in `scripts/utils.py`.
- WakaTime project filtering keeps a name only on an exact public `owner/name` match.
- Gitignore the Spotify refresh-token output path. Reject callback hosts other than `127.0.0.1`, `localhost`, and `::1`.
- Remove the probe SVG upload step and stop passing `METRICS_TOKEN` into `lowlighter/metrics`.

Verify: focused pytest for word clouds, preview, animate, utils, wakatime, spotify auth, and `tests/test_profile_workflow.py` for the probe contract. Do not run living-art GIF generation.

### 4. Correct false docs and rules

Files: `docs/content/docs/getting-started/index.mdx`, `docs/content/docs/index.mdx`, `docs/content/docs/development/architecture.mdx`, `docs/content/docs/development/testing.mdx`, `docs/content/docs/data/fetch-history.mdx`, `docs/content/docs/data/fetch-metrics.mdx`, `docs/content/docs/cli/generate.mdx`, `docs/content/docs/cli/index.mdx`, `docs/content/docs/scripts/technologies.mdx`, `docs/content/docs/scripts/generative-art.mdx`, `docs/content/docs/scripts/living-art-modes.mdx`, `AGENTS.md`, `scripts/AGENTS.md`, `tests/AGENTS.md`, `.cursor/rules/04-local-development.mdc`, `.cursor/rules/05-python-versioning-and-dependencies.mdc`.

Replace missing modules, the wrong QR node id, the `seed_hash` import, the case-insensitive `generate` claim, the history JSON sample, the metrics cache claim, the techs-as-shields claim, the 25-solver claim, and the Python 3.10 / `requirements.txt` rule. Point the living-art style list at `scripts/art/roster.py` and mention the optional MP4 sibling. Update a line count only inside a file this step or an earlier step is already editing.

Verify: a small doc contract test, or a pytest that reads the changed docs and asserts the bad strings are gone (`scripts/word_clouds.py`, `scripts/animated_art.py`, `TestQRCodeGenerator::test_init_success`, `stars_last_30d`, `case-insensitive`).

### 5. Dependabot on dev

- Bring PR #12's Python bumps into `dev` with `uv lock`, and keep only the bumps that still resolve and pass the focused suite.
- Update Actions pins only when they are newer than `dev`. Do not downgrade `astral-sh/setup-uv` from v10.0.0.
- Do not change files on `main`.

Verify: `git diff origin/main -- .github/workflows` from `dev` shows no setup-uv downgrade. The lockfile resolves with `uv sync --locked --all-extras`.

### 6. Commit, push, and close the PRs

- Commit the reconciled work on `dev` and push `origin/dev`.
- Close #12 and #14 with a note that the cleaned bumps landed on `dev`.
- Do not push `main`, force-push, or merge those PR branches.

## Risks

- Restoring the deleted generative binaries must come from `HEAD`, not from a new render.
- Blog error handling needs a sentinel or exception. Returning `[]` cannot mean both "failed" and "empty feed."
- Loading `LOG_LEVEL` must not import `scripts.config` from `scripts/utils.py`.
- The Python lock bump can fail tests that pin dependency behavior. Drop any bump that does not resolve rather than weakening a fact.
- The manual probe becomes less diagnostic. That is the accepted privacy fact.
- The daily cron on `main` and the billing lock stay broken on purpose. Task 9.5 stays unchecked.
- `fact-dependabot-dev` is not fully automated. Closing the PRs is a `gh` check after the push.
