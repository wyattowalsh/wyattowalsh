# Plan — profile-readme-overhaul

> **Facts:** [`facts.md`](./facts.md) · **Grill:** [`grill-notes.md`](./grill-notes.md)  
> **Task graph:** [`task-graph.json`](./task-graph.json) (v2, 107 nodes, file locks, per-plugin / per-style / per-renderer leaves)  
> **Ship surface:** origin/`dev` only. Do not update `main` unless the maintainer later asks.

---

## Critique of v1 (why this revision)

v1 was a 12-step linear essay. That under-specified parallelism, hid the real file-lock conflicts (`profile-updater.yml`, `readme_sections.py`, `supplemental_metrics.py`), and treated living-art / badge QA / word-cloud bake-off as single steps. Plannotator asked for a hyperfine graph optimized for subagent teams. v2 adds locks, waves, and one owner per lock.

---

## Parallel teams

| Team | Lock | Parallel with |
|------|------|----------------|
| INV | none (read) | all I01–I13 |
| BAN | `L-BAN-ASSET` then `L-WF` | RM/BDG/WC/ART reads in Wave 1 |
| RM | `L-RS` then `L-SM` then `L-WF` | BAN after B2 releases `L-WF` |
| LL | `L-WF` → `L-MSVG` | HAB, BDG, WAKA module, WC bake-off |
| HAB | `L-SM` | not SPOT (same lock) |
| SPOT | `L-SM` after HAB | BLOG, ART, view chip |
| WAKA | `L-WAKA` then `L-RS` | BLOG waits on `L-RS` |
| BDG | `L-SK` | almost everything |
| WC | `L-WC` | almost everything |
| ART | `L-ART` | almost everything |
| CAP | `L-GIT` | after reviews |

Same-file edits stay sequential. Independent dirs fan out.

---

## Solution approach

Pin the header to the exact `main` banner pair. Treat lowlighter as the dense GitHub-native instrument cluster (every plugin that can render cleanly; never music/tweets/activity). Redesign first-party surfaces that lowlighter should not own: habits (custom story), Spotify (hero + extras), WakaTime (SVG), blog strip, word clouds, living-art GIFs, view-counter chip, and tech-stack shields. Remove the duplicate GitHub feed card and the “200+ technologies” summary. Verify on the `dev` README preview.

Work in this order so CI contracts, README markers, and visual spikes do not fight:

1. Stop the banner from regenerating; lock tests to `main` bytes.
2. Delete feed widget + “200+” copy (small README/contract churn).
3. Fix and maximize lowlighter (languages, extra card, habits plugin, limits).
4. Redesign first-party habits and Spotify.
5. Replace Waka markdown with a first-party SVG and un-collapse it.
6. Restyle badges + homepage links; bake-off word clouds; redesign blog + view chip.
7. Sample living-art frames and redesign the shared daily growth spine.
8. Push only `dev`; visually accept `blob/dev/README.md`.

---

## Steps

### 0. Pin header banners to `main`

**Touch:** `.github/workflows/profile-updater.yml` (`generate-assets` / finalize allowlist), `tests/test_profile_workflow.py`, optionally `scripts/cli/generate/banner.py` (local generate may remain for designers; CI must not overwrite the pair).

**Do:** `git show origin/main:.github/assets/img/banner.svg` and `banner-dark.svg` → write those exact bytes onto `dev`. Stop the updater from running `generate banner` (copy committed pair or skip the step). Add a test that CI does not invoke banner generation, and a hash assertion against the pinned `main` blobs.

**Verify:** `sha256sum` both files equals `origin/main`. `rg "generate banner" .github/workflows/profile-updater.yml` is empty (or only a documented local/dev path). `uv run python -m pytest -q tests/test_profile_workflow.py -k banner`.

### 1. Remove the GitHub-feed widget

**Touch:** `scripts/readme_sections.py` (`_SUPPLEMENTAL_METRICS_ASSETS`), `scripts/supplemental_metrics.py`, `scripts/cli/generate/readme_cmd.py`, `.github/workflows/profile-updater.yml` (artifact lists), `README.md` via generate, tests in `tests/test_readme_sections.py`, `tests/test_supplemental_metrics.py`, `tests/test_profile_workflow.py`.

**Do:** Stop emitting `metrics-activity.svg`. Delete the README `<img>` for the activity feed. Keep `plugin_activity: no`. Do not delete GitHub’s native feed below the profile README.

**Verify:** `rg metrics-activity README.md scripts/readme_sections.py` has no live embed. Focused pytest modules above green.

### 2. Remove “200+ technologies” and any summary blurb

**Touch:** `scripts/readme_sections.py` (`_TECH_STACK_TEASER_RE`, summary HTML), `tests/test_readme_sections.py`, `tests/test_readme_gfm_ux.py`, composition scorer in `goals/gh-profile-readme-e2e/composition/score_readme_layout.py` if it requires `View full stack`.

**Do:** Tech stack stays in `<details>`. `<summary>` is a bare label (e.g. `Tech Stack`) — no count, no “honest” replacement sentence. Update regexes that currently require `View full stack (200+ technologies)`.

**Verify:** `rg "200\\+ technologies" README.md scripts tests` is empty (ignore historical goal candidates if needed). Regenerated README summary has no extra copy. `uv run python -m pytest -q tests/test_readme_sections.py tests/test_readme_gfm_ux.py`.

### 3. Maximize and repair lowlighter

**Touch:** `.github/workflows/profile-updater.yml` production `Personal metrics` / additional / extra jobs; `scripts/metrics_svg.py`; `tests/test_profile_workflow.py`; `tests/test_metrics_svg.py` if present.

**Do:**
- Primary: `plugin_habits: yes`; raise `plugin_calendar_limit`; `plugin_languages_threshold: 0%`; raise topics/stars/people limits; keep `plugin_music/tweets/activity: no`.
- Extra: keep reactions + followup; reject stub/error SVGs in `metrics_svg` validate/recover (the black “will be regenerated” bar is a failure, not a ship).
- Isolate retries of `lines` / `achievements` / `gists` onto extra or a fourth artifact only if validate passes.
- Confirm `METRICS_TOKEN` is required for languages/stargazers/traffic; document if a token rotate is needed (do not print secrets).

**Verify:** Workflow tests assert habits on, activity/music/tweets off, extra validate fails on stub markers. After a `dev` updater run: `metrics.svg` shows a languages panel; `metrics.extra.svg` is a real card (not 401-byte stub).

### 4. Redesign first-party habits

**Touch:** `scripts/supplemental_metrics.py` (`_render_habits_card`), `scripts/readme_svg.py` if new primitives are needed, `tests/test_supplemental_metrics.py`.

**Do:** Keep focus repos, peak hour, designed streaks, and a richer layout. Do not clone lowlighter’s facts/charts/language mix. Dark mode via SVG `@media`.

**Verify:** Snapshot/marker tests for required copy (`Coding habits`) plus new unique fields. Visual check of `metrics-habits.svg` vs `metrics.svg` habits panel — different jobs.

### 5. Redesign Spotify widget

**Touch:** `scripts/supplemental_metrics.py` (music card), Spotify fetch helpers, `metrics-music.svg`, tests.

**Do:** Recent-listens hero (color/type/tracks). Compact extras only if they stay beautiful. Never pass Spotify into lowlighter `with:`.

**Verify:** `plugin_music: no` still in workflow tests. Music card still generates when refresh token exists; extras omitted cleanly when data is thin.

### 6. First-party WakaTime SVG

**Touch:** `scripts/wakatime_readme.py` (today markdown-only, `WAKATIME_STATS_RANGE = last_7_days`), new renderer (e.g. `scripts/wakatime_svg.py` or `readme_svg` cards), `.github/workflows/profile-updater.yml` (`update-readme-wakatime`, finalize apply), `README.md` markers, tests.

**Do:** Fetch weekly + yearly + all-time if the API allows. Render a visible SVG (not `<details>`). Include languages, professional editors, Mac/iOS/watch, coding categories, totals, heatmap if available. Filter private project names (allowlist / public-repo match), file paths, heartbeats, leisure/social/health/shopping/entertainment apps. Keep first-party path (no anmol098).

**Verify:** Marker tests no longer require the old text dump (`This Week I Spent My Time On` in a fenced block). Privacy tests reject banned categories/names. `rg anmol098` stays empty. Regenerated README shows an open Waka `<img>`.

### 7. Tech-stack shields

**Touch:** `skills.yaml`, `scripts/skills.py`, `scripts/config.py` (`SkillEntry.url`), `tests/` for skills, docs if the public contract changes.

**Do:** Keep GitHub-camo-safe URLs. Evaluate modern stacks (shields.io, shieldscn, simple-icons retro) and use whatever still renders on github.com. Prefer retro/throwback icons at badge size. Every skill gets a homepage `url`. Exhaustive render QA (HEAD/camo, icon present, URL length `< MAX_SHIELDS_BADGE_URL_LENGTH`).

**Verify:** `uv run python -m pytest -q tests/test_skills.py` (or equivalent). Script or test that every generated `<a href>` is non-empty http(s) and every badge URL is below 4000 chars. Manual/automated check on `github.com/.../blob/dev/README.md` that sampled (ideally all) shields render with the right icon.

### 8. Word-cloud bake-off

**Touch:** `scripts/word_clouds/` (`generate.py`, renderers), `languages.md` / `topics.md` inputs, `.github/workflows/profile-updater.yml` (currently typographic pair), `tests/` word-cloud modules.

**Do:** Build topics + langs from starred-repo volume. Run `wordle` / `clustered` / `typographic` / `shaped` / `metaheuristic-anim` plus a new candidate if none encode volume. Score volume fidelity, GitHub readability, light/dark. Ship exactly two SVGs.

**Verify:** Tests that parsed counts drive font size/weight. Workflow still uploads exactly two word-cloud SVGs. Visual compare on `blob/dev`.

### 9. Blog strip

**Touch:** `scripts/readme_sections.py` (blog fetch + SVG cards), `scripts/readme_svg.py`, README blog markers, tests.

**Do:** Un-collapse Latest Blog Posts. 4–5 RSS cards from w4w.dev with title, date, one-line hook, link.

**Verify:** README has no `<details>` around `README:BLOG_POSTS`. Tests assert date + hook fields. Feed failure still fails closed or keeps last good cards (match existing error policy).

### 10. View counter

**Touch:** README footer (komarev URL), possibly `scripts/readme_sections.py` if footer is generated.

**Do:** Keep an incrementing public count. Restyle to match new badges. Do not stand up a new backend unless a one-file drop-in on an already-deployed host is obviously trivial (this repo has none today).

**Verify:** Footer still has a live count URL. Style matches badge family. No new service in `.github/workflows` unless the trivial-host spike is documented and accepted.

### 11. Living-art growth spine

**Touch:** `scripts/art/daily_snapshots.py`, `scripts/art/timelapse.py`, per-style modules (`ink_garden.py`, `topography.py`, `genetic_landscape.py`, `physarum.py`, `lenia.py`, `ferrofluid.py`), `tests/test_living_art_media.py`, docs `living-art-modes.mdx`.

**Do:** Confirm one daily spine from account creation → now (`validate_snapshot_monotonic_contract` already exists). Sample many sequential (not necessarily adjacent) frames per style. Redesign encodings so accretion of repos/stars/commits/followers is readable; styles may differ visually, not by using a different clock.

**Verify:** Monotonic contract tests stay green. Artifact contract remains exact-six GIFs. Human frame-contact sheet (checked into the goal dir or a temp gallery) before shipping new GIFs on `dev`.

### 12. Assure on `dev` only

**Touch:** none on `main`. Push `dev` when the maintainer asks during `/goal` execution (this setup does not push).

**Verify:** `git rev-parse --abbrev-ref HEAD` work stays on `dev`. `git merge-base --is-ancestor HEAD origin/main` is not used as a promotion step. Visual pass: `https://github.com/wyattowalsh/wyattowalsh/blob/dev/README.md`.

---

## Design thesis

| Dial | Choice |
|------|--------|
| Density | Maximal data, designed hierarchy |
| Ship | origin/`dev` preview only |
| Header | Exact `main` banner bytes; CI does not regenerate |
| Lowlighter | Every clean GitHub-native plugin; music/tweets/activity off |
| Habits | Both surfaces; split by job |
| Waka | Visible first-party SVG; public-safe + professional filter |
| Art | One daily spine; six dialects; inspect frames |
| Clouds | Bake-off; exactly two; size = star volume |
| Tech stack | `<details>` with a bare summary; modern camo-safe shields + homepage links |
| Blog | Visible 4–5 RSS cards |
| Views | Restyle incrementer; no new backend |

## Task graph (v2)

See [`task-graph.json`](./task-graph.json) (107 nodes). Hyperfine leaves: 19 plugin classify nodes (`L1.*`), 10 renderer×cloud scores (`C1.*`), 6 frame-sample + 6 sequential style redesigns (`A1.*` / `AR2.*`), 6 badge-audit batches (`K1.b*`).

Critical path:

`I99 → B2 → R1 → R3 → R5 → W1M → L2 → L3 → H1 → WK2 → WK3 → W2M → S1 → BL1 → AR2.ferrofluid → W3M → T1 → G-DEV → P1 → P2`

Waves:

- **I:** 13 parallel explores.
- **W1:** pin banners; delete feed + 200+ copy; start badge/cloud/art/lowlighter research.
- **W2:** lowlighter maximal + stub rejection; first-party habits; badge fill; Waka SVG; cloud bake-off.
- **W3:** Spotify (after habits); blog strip (after Waka on `L-RS`); view chip; living-art redesign + frame inspection.
- **W4:** three review agents in parallel; focused tests; commits; **push `dev` only**.

`/goal` execution should dispatch one subagent per node in a `parallelGroup`, then merge. Do not run two writers on the same lock.

---

## Risks

- **`METRICS_TOKEN` scope.** Languages / extra / stargazers / traffic still fail closed without a valid classic PAT. Plugin config alone will not fix the stub if the token is dead — rotate out of band, never paste the secret.
- **lowlighter `plugin_habits`.** Previously disabled because upstream emitted inline errors. Re-enable behind validate/recover; keep first-party habits even if the plugin has to drop back to off.
- **Waka mobile categories.** iOS/watch will try to publish non-dev apps; the privacy filter must be tested with real payloads, not only fixtures.
- **Banner pin vs local `generate banner`.** Designers can still generate locally; CI must not commit a new pair.
- **Word-cloud bake-off time.** Cap candidates; do not ship six public clouds.
- **Living-art cost.** Full 120-frame fleet is the long pole; inspect frames on a reduced grid first, then one production render.
- **`dev` updater overwrite.** Finalize will rewrite generated README/assets; pin/banner skip and new contracts must live in the workflow or the next push will undo them.

---

## Out of scope (unless later asked)

- Updating `main` / the live github.com/wyattowalsh profile
- Featured-project cards, QR, Connect badges (except if a marker rewrite forces a touch)
- New view-counter infrastructure
- Reintroducing anmol098 or Spotify-on-lowlighter
