# Wave DIAL — Topography (`Dto1`–`Dto4`)

**Lane:** DTO. **Style key:** `topo`. **Family:** cartographic.
**This file is the execution playbook.** Inventory evidence: [`../inventory/I10.md`](../inventory/I10.md), I99 Dto1 brief, `scripts/art/topography.py`.
**No production edits while authoring this playbook.** Implementers own `Dto1`–`Dto4` later.

Caption here = the on-SVG `#accretion-dialect` register (family word + four numeric glyphs). Not the README `<details>` legend (Wave RM). Peaks and settlements must read **with that register ignored**.

Until K2, shipped == candidates == six. Do not shrink CI, drop `topo` from the roster, or raise `LIVING_ART_BYTE_BUDGETS`.

---

## Lock / graph

| ID | Lock | File(s) | Deps | Parallel | Verify (graph) |
|---|---|---|---|---|---|
| **Dto1** | `L-TO` | `scripts/art/topography.py` | A3, I10 | DIAL (with other `D*1`) | t0 primary mark + four-channel motion |
| **Dto2** | `L-T-ACC` | `tests/test_art_shared_package.py` **only** | Dto1 | serialize vs other `D*2` | `pytest -k topo` |
| **Dto3** | — | `goals/living-art-overhaul/bakeoff/topo-t{0,1,2}.svg` | Dto1 | STILL | three stills + `data-accretion-*` increase |
| **Dto4** | `L-TO` | `scripts/art/topography.py` | Dto1 | LOOK | no dual `-dark` pair unless unreadable |

`Dto1` and `Dto4` share `L-TO` → **sequential on `topography.py`**. `Dto2` serializes on `L-T-ACC` with Dig2/Dge2/Dph2/Dle2/Dfe2 — prefer one greening agent after all `D*1` (`plan.md`; I99 correction 9). `Dto3` has no shared lock.

**`L-TO` vs `L-T-ACC`:** `L-TO` is the generator (`topography.py`) for Dto1 + Dto4. `L-T-ACC` is the shared on-canvas test file (`tests/test_art_shared_package.py`) for Dto2. Do not write Dto2 asserts into `test_topography_timeline.py` or `test_living_art_media.py`. Do not hold `L-TO` while greening Dto2.

**Recommended lane order:** Dto1 → Dto4 (same file, one look on the redesigned map) → Dto3 stills (I10: stills **after Dto1**; capture after Dto4 so bake-off ink is the designed cream-paper contrast) → Dto2 when `L-T-ACC` is free. Graph allows Dto3 ∥ Dto4 after Dto1; if stills land before Dto4, **re-export** them after the look lands. W2M needs Dto2 + Dto3 + Dto4.

GIF regen is **not** this wave (`G1to` after W2M). Dto1 must still be encodable under the **10 MB** `living-topo.gif` cap so G1to cannot pass only by raising budgets (repo-growth is out of scope). Topo is already the largest budget of the six and sits >91% of cap on published bytes (I03 / I99 risk 4) — redesign must prefer **stronger ink**, not more contour paths.

---

## Target picture (without caption)

| Channel | Lease (keep names) | Intended on-canvas identity | Fail if you only prove |
|---|---|---|---|
| **repos** | hill count (no named knob) | one Gaussian + `data-role="repo-peak"` per named repo | overlay `data-accretion-repos` / mere `class="repo-peak"` presence |
| **stars** | `prominence_scale = 0.70 + 0.90 * star_scale` | **summit height** (terrain) **and** landmark ink | marker `r=` only / overlay `data-accretion-star-scale` |
| **commits** | `contour_gain = 0.35 + 0.65 * commit_scale` | contour **mass / stroke hierarchy** with a commit identity | `n_levels` formula / denser brown lines that erase peaks |
| **followers** | `settlement_gain = follower_scale` | **geometry-visible** settlement (size, fill, opacity) | `data-settlement-gain/scale/count/tier` |

Published GIF path (must be the isolation path too):

```text
generate(metrics, seed=…, maturity=snapshot.maturity, timeline=False)
```

`timelapse.py` forces `timeline=False`. `growth_mat = mat` on that path (not 1.0). Overlay origin for cartographic is **(58, 708)** in the bottom margin — leave it unless A3 moves every dialect.

A1 spine (reuse `_accretion_metrics` in `tests/test_living_art_media.py:1144`):

| Frame | repos / stars / commits / followers | `star_scale` | `prominence_scale` | `commit_scale` | `contour_gain` | `settlement_gain` | tier |
|---|---|---|---|---|---|---|---|
| t0 | 1 / 2 / 20 / 1 | 0.177 | 0.859 | 0.339 | 0.570 | 0.116 | outpost |
| t1 | 2 / 24 / 400 / 18 | 0.518 | 1.166 | 0.667 | 0.784 | 0.491 | outpost |
| t2 | 4 / 120 / 2400 / 80 | 0.771 | 1.394 | 0.866 | 0.913 | 0.733 | village |

Pin `star_velocity={recent_rate:0, peak_rate:0}` in isolation fixtures (I08). `_accretion_metrics` currently leaks stars into `star_velocity`.

---

## Residue (why today’s GIF is caption-only)

Evidence: I10 + I99 Dto1 brief. Live code, not the 2026-08-14 A1 stills. t0 is **not empty** (unlike Ink Garden / Physarum leftovers): one `repo-peak` plus a sub-pixel outpost already exist. The leftover is **stars weaker than contours**, a taller anonymous center blob, and settlements that vanish at 400×400.

### 1. `prominence_scale` never enters terrain

```1194:1200:scripts/art/topography.py
        # Stars -> peak height RELATIVE to this profile's range
        star_frac = (
            (repo_stars - min_stars) / max(1, max_stars - min_stars)
            if max_stars > min_stars
            else 0.5
        )
        peak_h = 0.15 + star_frac * 0.6
```

`prominence_scale` only fattens landmark circles (`2752-2766`: `+ 3.4 * prominence_scale`, or `+ 2.4 *` if `star_frac>0.7`, then `* marker_scale`). Isolating total stars with a proportional per-repo split keeps min–max `star_frac` at 0 and 1, so `peak_h` is **unchanged**. Relative hills stay the same height when every repo’s stars scale together. Root SVG does **not** emit `data-prominence-scale`.

### 2. Central blob beats the first hill

```1432:1444:scripts/art/topography.py
    # ── 4. Central peak (always prominent, scaled to profile) ──────
    # Central peak is always the tallest — height relative to repo count
    central_height = 0.45 + 0.25 * min(1.0, len(repos) / max(1, len(repos) + 2))
    ...
            central_contribution = central_height * math.exp(
                -(dx * dx + dy * dy) / (2 * central_sigma * central_sigma)
            )
            elevation[gy, gx] += central_contribution
```

t0 central height **0.533** vs single-repo `peak_h=0.45` (`star_frac` defaults to 0.5). Contours ring the center. First-repo world reads as an anonymous hill, not that repo’s peak. Empty-metrics still draw noise + this blob.

### 3. Contours own the map; followers leak into the commit channel

```2198:2206:scripts/art/topography.py
    _base_n_levels = max(
        10,
        min(
            44,
            10 + int(round(18 * dialect.knobs["contour_gain"])) + int(followers // 10),
        ),
    )
    n_levels = int(_base_n_levels * (0.8 + 0.4 * complexity))
```

A1 `n_levels` base (before complexity): t0 `10+10+0=20`; t1 `10+14+1=25`; t2 `10+16+8=34`. Index contours always `contour_fade=1.0`, stroke 1.2 / op 0.7 (`2222-2230`) — they never fade. Landmark fill opacity is `0.65 * static_signal` (`2765`) → **0.07–0.14** on early/newest peaks. Extra levels are more of the same brown lines, not a new commit identity. Stale `topography.mdx` still teaches followers → contour density; dialect + plan teach followers → settlements. **Both** are in the live generator (`2203` vs `2939`).

### 4. Settlements are sub-pixel and inherit the host peak’s static signal

Host = **starriest** repo, then `sy+15` (`2942-2945`). The `#settlement-symbol` group uses that peak’s `_timeline_style` (`2952`). On the A1 spine the starriest repo is also the newest, so t1/t2 group opacity stays **0.103** no matter how large `settlement_gain` gets.

t0 outpost: **`r=0.8`** fill op 0.3, group op **0.202** → effective ~0.06. Extra marks `r=1.2–2.2`. Labels only for village+ (25 followers). `_settlement_scale_tier` stays `outpost` until 25 followers — A1 t1 (18) never leaves the faintest glyph. Media isolation asserts `data-settlement-scale/count/gain` only.

### 5. t0 primary mark exists in the DOM and fails at 400×400

A1 t0 still: 1 `repo-peak` at (573.3, 244.8), circle `r=5.1` opacity **0.138**, title “★2 · summit”; settlement `r=0.8`. Index contours + hypsometric fill already cover the map. Overlay at (58, 708) is the only high-contrast region. Static `timeline=False` keeps every `repo-peak` in the DOM even at `maturity=0.08` (`test_topography_static_mode_keeps_all_repo_landmarks_accretively_visible`) — **presence**, not a visibility floor.

### Tests that currently certify the leftover

| Test | What it proves | What it does not |
|---|---|---|
| `test_leased_style_knobs_track_isolated_channels` | followers → `data-settlement-scale/count/gain` | peak `r=`, elevation, `prominence_scale`, contour path count, settlement **geometry/opacity** |
| `test_style_dialects_make_accretion_readable` | overlay ticks t0→t2 | picture |
| `test_topography_static_mode_keeps_all_repo_landmarks_accretively_visible` | `repo-peak` nodes present at low maturity | opacity / 400×400 |
| `test_generators_prefer_render_state` (topo) | `class="repo-peak"` count | visibility vs contours |
| `test_living_art_dark_mode_contrast` | ≥3 high-contrast colors vs `sky_top` | peak-vs-contour or GIF raster |
| `test_early_spine_dialects_keep_repo_accretion_readable` | ink/physarum/ferro | **not** topo |
| `test_art_shared_package.py` today | dialect family set includes `topo` | **no** t0 / isolation yet (A1/A2 write the red bar here) |

Root SVG does not emit `data-prominence-scale` or `data-contour-gain`. Isolation of stars/commits has no topo `data-*` today. That is not a license to treat attrs as Dto1 done — Dto1 must change the **picture**.

---

## Shared constraints (all four nodes)

**Do**

- Consume today’s knobs: `prominence_scale` / `contour_gain` / `settlement_gain`. A3 is a documented no-op unless all six share a clock failure (I08/I99). Do not retune `_CHANNEL_CEILINGS`.
- Keep `generate(metrics, *, seed, maturity) -> str`. Extra kwargs `chrome_maturity` / `timeline` / `loop_duration` / `reveal_fraction` stay.
- Keep one hill + `data-role="repo-peak"` per named repo. No `select_primary_repos` / `MAX_REPOS=10` cap — dense portfolios keep every peak (`test_topography_timeline.py:340-367`).
- Keep production grid **200** (tests patch to 48). Prefer stronger ink over a denser grid.
- Leave `#accretion-dialect` in the SVG unless A3/RM ask to remove it. Dto1–Dto2 must **ignore** it, not delete it.
- Keep `test_topography_timeline.py` green from Dto1 (static landmark presence, chronology, river/release, settlement **tier string** for 260 followers → `"town"`, grid 200).
- Keep cream-paper cartographic as **one** designed surface. Dto4 polishes contrast; it does not add a night pair.

**Do not**

- Edit `scripts/art/shared/accretion.py`, `artifacts.py` budgets, `timelapse.py`, README, workflow, OpenSpec `prevent-living-art-repo-growth`, or `main`.
- Raise `living-topo.gif` above **10_000_000** bytes (`artifacts.py:36`). Largest of the six; already tight.
- Trigger `_assemble_gif` **12 MB halve** (`timelapse.py:295-324`) — that breaks 400×400.
- Use `generate animated` / `animate.py` for `living-*` (writes `{style}-growth.gif` from interpolated maturity).
- Reuse `goals/profile-readme-overhaul/inventory/frames/topo-t{0,1,2}.svg` as bake-off evidence.
- Treat overlay ticks, `data-settlement-gain`, `data-settlement-count`, `class="repo-peak"` presence, or `n_levels` as Dto1/Dto2 done.
- Ship `living-topo-dark.gif` (unbudgeted; `_TIMELAPSE_RE` would reject it; `test_living_art_media.py:435-448` already forbids it).
- Hold `L-T-ACC` from Dto1. Generator edits stay on `L-TO`.

---

## Dto1 — redesign on-canvas dialect (`L-TO`)

**Job:** stars as **readable peaks**; followers as **visible settlements**; t0 hill survives 400×400; **10 MB** still feasible.

Graph verify: “t0 primary mark + four-channel motion.”

### Must change (picture)

1. **Put `prominence_scale` into terrain.** Multiply `peak_h` (and/or a global relief gain) by the leased knob so isolating `stars` raises summits even when per-repo `star_frac` is unchanged. Do not leave stars as marker radius only (`1194-1200` vs `2752-2766`). Marker size may still move; it is not the star channel.

2. **Stop the central blob from beating star hills at t0** (`1432-1455`). First-repo world must read as that repo’s peak, not a taller anonymous center. Scale central height down, bind it to stars/commits, or drop it for the four-channel picture. Empty-metrics may keep a quiet noise floor; they must not mint a taller-than-repo blob that wins the first hill.

3. **Give contours a commit identity that does not erase peaks.** Index-stroke-always-on (`2223`) is why A1 called stars weaker. Lower index weight, or reserve heavy index lines for high `contour_gain`, and **remove `followers//10` from `n_levels`** (`2203`) so followers stop leaking into the commit channel. Commits-only must increase contour **mass or stroke hierarchy**, not drown summits.

4. **Settlements must be visible at 1 follower and must grow in geometry.** t0 `r=0.8` / effective op ~0.06 is not a town. Raise outpost/hamlet size and fill; do **not** multiply the whole `#settlement-symbol` by the host peak’s `static_signal` (`2952`). Spread extra marks as a settlement field, not 1–2 px dots at `r=1.2`. Geometry must survive **400×400** (half the 800 SVG). Aim for outpost radius well above 1 GIF pixel after raster (several SVG px at 800, opaque enough vs hypsometric fill).

5. **t0 primary mark must survive 400×400 raster.** Keep one repo hill at first-repo t0, but peak fill/stroke well above 0.14 and larger than contour stroke. Settlement mark similarly above the overlay. Do not require the register. A count of `class="repo-peak"` already passes today — that is not Dto1.

6. **Repos remain hill count** (already). Isolation must still move when only `repos` increases (not covered by `test_leased_style_knobs_track_isolated_channels` today). Newest-peak opacity 0.07 must not make extra hills invisible.

7. **Stay inside 10 MB** and grid 200. Prefer stronger ink over more contour paths. Do not bump `TOPOGRAPHY_GRID_SIZE` to buy smoother hills.

8. Overlay may stay. Dto1 can leave the register but must not need it.

### Byte budget (hard)

`living-topo.gif` cap **10 MB**. Contour path count is the usual blow-up. Prefer:

- Keep `TOPOGRAPHY_GRID_SIZE = 200`.
- Do not raise `n_levels` to “prove” commits — hierarchy / weight / color, not 44 brown polylines.
- Avoid extra decorative layers (hachures, trails, marsh stamps) as the dialect fix.

Local smoke **before** claiming Dto1 done (does not replace G1to):

```bash
# Role / geometry sanity on the GIF kwargs path (A1 t0 + stars-high + followers-high).
uv run python - <<'PY'
from scripts.art.topography import generate
# reuse the same spine shape as tests.test_living_art_media._accretion_metrics
PY
```

Optional size probe: render a **short** 400×400 GIF (e.g. 8 frames) and scale `size * 120/8` as a crude upper bound. If that projection exceeds ~10 MB, reduce drawn primitives — do not plan to raise the cap. Never pass `--size` that would invite the 12 MB halve.

Dto1 does **not** commit `living-topo.gif`. Do not run full-fleet `generate living-art` without `--only`.

### Palette

Dto1 may leave cream hypsometric paper (`_TOPO_STOPS`, `pal["bg_primary"]`) as-is if Dto4 follows immediately. Do not add a second light/dark branch. Peak/settlement opacity must work on the current cream ground *and* after Dto4 contrast retouch.

### Verify Dto1

Caption-blind (strip `#accretion-dialect` / `data-role="accretion-dialect"` before judging):

- [ ] t0 `1/2/20/1`, `timeline=False`: first **repo hill** is the tallest readable landform (not the central blob); peak fill/stroke ≫ 0.14.
- [ ] t0 settlement at 1 follower is geometry-visible at 400×400 (radius ≫ 0.8 SVG px; group opacity not host `static_signal` ~0.10).
- [ ] Stars-only (same per-repo star **ratio**): summit height **and** landmark ink **up** — not only marker `r=`.
- [ ] Commits-only: contour mass / index hierarchy **up** **without** `followers//10` in `n_levels`; peaks still readable.
- [ ] Followers-only: settlement **count and geometry/opacity** up — not only `data-settlement-gain`.
- [ ] Repos-only: `repo-peak` **count** up and extra hills ink-visible.
- [ ] `uv run python -m pytest -q tests/test_topography_timeline.py`
- [ ] Existing media attr tests still green (they are insufficient, not retired):
  `uv run python -m pytest -q tests/test_living_art_media.py -k 'topo or leased_style_knobs or topography'`

Do not green Dto1 by writing Dto2 tests that still read `data-*` only.

---

## Dto2 — on-canvas t0 + isolation (`L-T-ACC`)

**Job:** make A1/A2 topo assertions green by proving the **picture**, not the caption or settlement attrs.

**File:** `tests/test_art_shared_package.py` only. Do **not** move the contract into `test_topography_timeline.py` or `test_living_art_media.py`. Those stay as generator/regression coverage.

Graph verify: `pytest -k topo`.

### Wait for A1/A2

A1/A2 land red/xfail on-canvas isolation in this same file (I08). Dto2 greens the **topo** slice. If a shared D\*2 agent holds `L-T-ACC`, this playbook is that slice — still assert geometry here.

If A1/A2 are not present yet, Dto2 **adds** the topo on-canvas tests (do not wait forever for names). Prefer sharing helpers with other dialects (overlay strip, `_accretion_metrics` clone with `star_velocity` pinned).

### Required asserts (overlay stripped)

Strip `#accretion-dialect` (and do not score `data-settlement-gain` / `data-settlement-count` / `data-settlement-scale` / overlay `data-mark-count` / `data-accretion-star-scale` as pass). Generate with `timeline=False`.

| Case | Fixture | Pass |
|---|---|---|
| **t0 hill + outpost** | `_accretion_metrics(repos=1, stars=2, commits=20, followers=1)` | ≥1 `repo-peak` above a visibility floor (**radius and opacity**, not mere presence); settlement mark present and **larger than ~1 px** when followers≥1. Overlay ignored. Central blob must not out-height the repo hill. |
| **stars-only** | stars 8 → 180; per-repo stars stay in the **same ratio** | summit height / landmark radius **and** visible ink up |
| **commits-only** | commits 40 → 3200; followers fixed | contour mass / stroke hierarchy up **without** follower leakage (same follower count → `n_levels` must not imply `followers//10`) |
| **followers-only** | followers 1 → 90 | settlement **count and geometry/opacity** up, not `data-settlement-gain` alone |
| **repos-only** | repo list 1 → 4; stars/commits/followers scalars **fixed** | `repo-peak` **count** up |

Suggested selectors (Dto1 should have made these real):

- repo mark: `data-role="repo-peak"` / `class="repo-peak"` with fill/stroke opacity and `r=` well above t0 leftover (0.138 / 5.1)
- terrain: elevation encoded in peak marker title is not enough — prefer a `data-*` on the peak or a measurable summit vs map-center height if Dto1 adds one; otherwise compare landmark size **and** that map-center anonymous peak is gone or shorter
- settlement: `#settlement-symbol` / `data-role="topo-settlement-mark"` radius, fill opacity, **group** opacity not tied to host `static_signal`

**Forbidden pass conditions:** overlay ticks, `data-settlement-gain`, `data-settlement-count`, `data-settlement-scale`, `data-settlement-tier` string only, `class="repo-peak"` count without a visibility floor.

Keep existing media attr tests; they are a weaker regression, not this bar.

### `pytest -k topo` blast radius

That keyword also hits `tests/test_topography_timeline.py`, parametrized media/render-state tests, and coverage helpers — files **outside** `L-T-ACC`. Dto2 must not edit those. If they fail after Dto1, fix in **Dto1** (`topography.py`), not here.

```bash
uv run python -m pytest -q tests/test_art_shared_package.py -k topo
uv run python -m pytest -q tests/test_topography_timeline.py
# graph verify (wider):
uv run python -m pytest -q -k topo
```

---

## Dto3 — bake-off stills (no lock)

**After Dto1** (graph deps + I10). Prefer capturing **after Dto4** so cream-paper contrast is the designed look.

**Files:**

- `goals/living-art-overhaul/bakeoff/topo-t0.svg`
- `goals/living-art-overhaul/bakeoff/topo-t1.svg`
- `goals/living-art-overhaul/bakeoff/topo-t2.svg`

Create the `bakeoff/` directory if needed. **Do not** copy `goals/profile-readme-overhaul/inventory/frames/topo-t*.svg` (pre-regen A1; published GIFs were never rebuilt after 2026-08-14).

### Export

Same spine and kwargs as A1:

```text
timeline=False
seed stable (e.g. "topo-dialect")
t0: repos=1, stars=2, commits=20, followers=1
t1: 2 / 24 / 400 / 18
t2: 4 / 120 / 2400 / 80
```

### Verify Dto3

- [ ] Three files exist and are well-formed SVGs (`viewBox="0 0 800 800"`).
- [ ] `data-accretion-*` (repos/stars/commits/followers or scales) **increase** t0→t2.
- [ ] Caption-blind glance: **rising peaks** plus a **growing settlement**, not just denser brown contours. Overlay may still be present; it must not be the only readable growth.
- [ ] t0 still: first hill beats any remaining central blob; outpost is more than a speck.
- [ ] No `living-topo-dark` sibling implied by the stills.

Graph verify: “three stills + data-accretion attrs increase.”

---

## Dto4 — one look (`L-TO`)

**Job:** `fact-one-look` — one designed look that reads on GitHub light **and** dark. No dual `-dark` pair unless bake-off later proves unreadable.

Graph verify: “no dual `-dark` pair unless unreadable.”

Cream hypsometric paper is **already** one designed surface (`topography.py:1-8` “Light theme on cream paper”). GitHub **dark** sees a cream card (usually fine). GitHub **light** plus dense brown contours plus 0.07-opacity newest landmarks is the readability risk — not a missing `-dark` GIF.

### Must

- Keep the cream-paper cartographic look. Do **not** add `living-topo-dark.gif`.
- Make **peaks and settlements** contrast against the hypsometric fill on GitHub light (current 0.07-opacity newest landmarks fail).
- Judge at **400×400** raster (GIF worker size), not only the 800 SVG.
- One look, not a CSS `@media` pair and not a night generator path.

### Must not

- Add a second generator path or `-dark` filename.
- Move overlay origin (A3 / all-six only).
- Re-open `prominence_scale` / central blob / `followers//10` if Dto1 already made the picture — only retouch color/contrast/ink weight.
- Treat “cream on dark GitHub is fine” as Dto4 done while light-theme peaks still vanish.

### Verify Dto4

- [ ] No second palette branch; cream paper remains the hero fill.
- [ ] Newest / low-`static_signal` peaks and the 1-follower outpost remain readable on a light GitHub page at 400×400.
- [ ] `rg living-topo-dark` is empty in production art paths.
- [ ] `uv run python -m pytest -q tests/test_topography_timeline.py tests/test_living_art_dark_mode_contrast.py -k topo`
- [ ] Re-export Dto3 stills if they were captured before this look.

---

## Sequence and handoff

```text
A3 (no-op clock) ──► Dto1 (picture, 10 MB feasible)
                      ├─► Dto4 (one look, same L-TO)
                      │     └─► Dto3 (stills after Dto1; re-export if Dto4 landed after)
                      └─► Dto2 (L-T-ACC queue: on-canvas tests)
W2M needs Dto2 + Dto3 + Dto4
G1to (after W2M): --only topo, 120 frames, 400×400, sibling MP4, ≤10 MB
K1to scores the regenerated GIF, not A1 stills
```

G1to command (later wave, not Dto*):

```bash
uv run python -m scripts.cli generate living-art \
  --profile wyattowalsh \
  --metrics-path /path/to/metrics.json \
  --history-path /path/to/history.json \
  --only topo \
  --max-frames 120 \
  --size 400 \
  --workers 4 \
  --output-dir .github/assets/img
```

---

## Out of this lane

| Concern | Owner |
|---|---|
| README stack / `<details>` mapping copy (alt does not mention peaks/settlements) | RM `M1`–`M5` |
| Shared accretion ceilings / overlay geometry | A3 / `L-ACC` |
| `living-topo.gif` + `.mp4` regen | `G1to` |
| Jury score | `K1to` |
| Stale `topography.mdx` followers → contour density sentence | Dto1 may fix the generator mapping; docs copy is S11 / `L-DOCS-MODES` |
| Roster shrink / exact-six tests | SHR after K2 |
| OpenSpec growth change | never this goal (S15) |

---

## Done when

- **Dto1:** caption-blind `prominence_scale` raises terrain; central blob no longer beats the first hill; contours commit-identify without follower leak; settlements are geometry-visible at 1 follower and at 400×400; 10 MB still plausible; `test_topography_timeline.py` green.
- **Dto2:** `test_art_shared_package.py` asserts those geometries with overlay stripped — **not** `data-settlement-*` only; `pytest -k topo` green without editing files outside `L-T-ACC`.
- **Dto3:** three new bake-off SVGs **after Dto1**; accretion attrs increase; glance shows rising peaks + growing settlement.
- **Dto4:** cream-paper one look; peaks/settlements contrast on GitHub light; **no** `-dark` pair.

Overlay may remain. It must not be the picture.
