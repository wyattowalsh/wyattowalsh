# Wave DIAL — Ferrofluid (`Dfe1`–`Dfe4`)

**Lane:** DFE. **Style key:** `ferrofluid`. **Family:** magnetic.
**This file is the execution playbook.** Inventory evidence: [`../inventory/I14.md`](../inventory/I14.md), I99 Dfe1 brief, `scripts/art/ferrofluid.py`.
**No production edits while authoring this playbook.** Implementers own `Dfe1`–`Dfe4` later.

Caption here = the on-SVG `#accretion-dialect` register (family word + four numeric glyphs). Not the README `<details>` legend (Wave RM). Towers, spike height, pool mark, and leased field must read **with that register ignored**.

Until K2, shipped == candidates == six. Do not shrink CI, drop `ferrofluid` from the roster, or raise `LIVING_ART_BYTE_BUDGETS`.

---

## Lock / graph

| ID | Lock | File(s) | Deps | Parallel | Verify (graph) |
|---|---|---|---|---|---|
| **Dfe1** | `L-FE` | `scripts/art/ferrofluid.py` | A3, I14 | DIAL (with other `D*1`) | t0 primary mark + four-channel motion |
| **Dfe2** | `L-T-ACC` | `tests/test_art_shared_package.py` **only** | Dfe1 | serialize vs other `D*2` | `pytest -k ferrofluid` |
| **Dfe3** | — | `goals/living-art-overhaul/bakeoff/ferrofluid-t{0,1,2}.svg` | Dfe1 | STILL | three stills + `data-accretion-*` increase |
| **Dfe4** | `L-FE` | `scripts/art/ferrofluid.py` | Dfe1 | LOOK | no dual `-dark` pair unless unreadable |

`Dfe1` and `Dfe4` share `L-FE` → **sequential on `ferrofluid.py`**. `Dfe2` serializes on `L-T-ACC` with Dig2/Dto2/Dge2/Dph2/Dle2 — prefer one greening agent after all `D*1` (`plan.md`; I99 correction 9). `Dfe3` has no shared lock.

**`L-FE` vs `L-T-ACC`:** `L-FE` is the generator (`ferrofluid.py`) for Dfe1 + Dfe4. `L-T-ACC` is the shared on-canvas test file (`tests/test_art_shared_package.py`) for Dfe2. Do not write Dfe2 asserts into `test_ferrofluid.py` or `test_living_art_media.py`. Do not hold `L-FE` while greening Dfe2.

**Do not lock / do not edit:** `scripts/art/shared/visual.py` (I14 / I99). `language_cluster` stays for genetic / physarum / lenia. Dfe1 **stops calling it for x** from `ferrofluid.py`. Tint may still use `LANG_HUES` / `_spike_gradient_palette`.

**Recommended lane order:** Dfe1 → Dfe4 (same file, raise skyline contrast on the redesigned columns) → Dfe3 stills (so bake-off is not the 2026-08-14 left hedge) → Dfe2 when `L-T-ACC` is free. Graph allows Dfe3 ∥ Dfe4 after Dfe1; if stills land before Dfe4, **re-export** them after the look lands. W2M needs Dfe2 + Dfe3 + Dfe4.

GIF regen is **not** this wave (`G1fe` after W2M). Dfe1 must still be encodable under the **3.8 MB** `living-ferrofluid.gif` cap so G1fe cannot pass only by raising budgets (repo-growth is out of scope). Ferro sits ~91.9% of cap on published bytes (I03 / I99 risk 4) — redesign must prefer **separated columns**, not more spikes.

---

## Target picture (without caption)

| Channel | Lease (keep names) | Intended on-canvas identity | Fail if you only prove |
|---|---|---|---|
| **repos** | one tower per named repo (no named knob) | N repos ⇒ N **readable spike columns** at 400×400 | overlay `data-accretion-repos` / dipole **count** / `min(gaps) ≥ 36` |
| **stars** | `spike_scale = 0.70 + 0.80 * star_scale` | tallest column **obviously taller** | overlay star ticks / `data-spike-scale` without height geometry |
| **commits** | `ripple_gain = commit_scale` | a **visible pool mark** (ripples that survive 400×400, or a replacement) | `data-ripple-gain` / ellipse **count** at opacity ~0.09 |
| **followers** | dialect `field_gain = 0.82 + 0.30 * follower_scale` | a **leased field mark** (not magnet count, not composite soup) | product of two `field_gain`s / overlay follower ticks |

Published GIF path (must be the isolation path too):

```text
generate(metrics, seed=…, maturity=snapshot.maturity, timeline=False)
```

`timelapse.py` forces `timeline=False`. `maturity_hint = mat` on that path (not 1.0). Overlay origin for magnetic is **(516, 742)** bottom-right, below the pool — leave it unless A3 moves every dialect.

A1 spine (reuse `_accretion_metrics` in `tests/test_living_art_media.py:1144`, then **override language** for isolation — see same-language fixture):

| Frame | repos / stars / commits / followers | `star_scale` | `spike_scale` | `ripple_gain` | dialect `field_gain` |
|---|---|---|---|---|---|
| t0 | 1 / 2 / 20 / 1 | 0.177 | 0.842 | 0.339 | 0.855 |
| t1 | 2 / 24 / 400 / 18 | 0.518 | 1.114 | 0.667 | 0.967 |
| t2 | 4 / 120 / 2400 / 80 | 0.772 | 1.318 | 0.866 | 1.040 |

Pin `star_velocity={recent_rate:0, peak_rate:0}` in isolation fixtures (I08). `_accretion_metrics` currently leaks stars into `star_velocity`.

---

## Residue (why today’s GIF is a hedge, not towers)

Evidence: I14 + I99 Dfe1 brief. Live code, not the 2026-08-14 A1 stills.

**t0 is not empty.** One dipole + 17 spikes already reads as a single tower. A2 that only counts `data-role="ferro-dipole"` is green today (`tests/test_living_art_render_state.py:261-263`). Clustering is the leftover, not empty-t0.

### 1. `language_cluster` owns x — stop calling it

```911:913:scripts/art/ferrofluid.py
        rx, ry = repo_to_canvas_position(
            repo, visual_seed, WIDTH, pool_y * 0.9, strategy="language_cluster"
        )
```

`repo_to_canvas_position(..., strategy="language_cluster")` (`scripts/art/shared/visual.py:211-248`) maps language → family → quadrant. **Python and Go share x-fraction 0.25** (`_FAMILY_QUADRANT`: data `(0.25, 0.30)`, systems `(0.25, 0.70)`). Same-language repos jitter inside one quadrant (`jitter=0.15`).

`_accretion_metrics` alternates Python/Go (`tests/test_living_art_media.py:1153-1154`). That fixture **still packs the left third**. A1 t2 stills were four Pythons (`cx` 82.2 / 100.9 / 129.3 / 235.7, min gap **18.7**).

**Dfe1 must stop passing `strategy="language_cluster"` for x.** Language may still tint spikes. Do **not** rewrite `visual.py`. Genetic / physarum / lenia keep the helper.

### 2. `_spread_positions` + the 36 px test are a hedge, not columns

```70:102:scripts/art/ferrofluid.py
def _spread_positions(
    values: list[float],
    *,
    min_gap: float,
    low: float,
    high: float,
) -> list[float]:
    """Push clustered 1D positions apart without changing their order."""
```

Applied after cluster (`994-1006`) with `min_gap = max(44, WIDTH*0.055) = 44`. Order-preserving. Same-language repos remain a **contiguous pack**. 44 px on the 800 canvas is **22 px at the 400×400 GIF**. Field cells are ~13 px (`800/60`); spike bases ~8 px; superposition still merges neighbors into one ridge.

Live media test that currently **greens the leftover** (`tests/test_living_art_media.py:1609-1613`):

```1609:1613:tests/test_living_art_media.py
    t2_xs = _ferro_dipole_xs(ferro_svgs[-1])
    assert len(t2_xs) == 4
    ordered = sorted(t2_xs)
    gaps = [right - left for left, right in zip(ordered, ordered[1:])]
    assert min(gaps) >= 36.0
```

That is a **gap floor**, not tower identity. It does not check mixed-language collapse, spike-column separation, or t0→t2 count monotonicity (ink/physarum get those asserts; ferrofluid does not). **`min(gaps) ≥ 36` is not Dfe1 done.** Aim toward even columns: `~WIDTH / (n+1)` (four repos → ~160 px on the SVG, ~80 px on the GIF), or draw a **canonical tower at each dipole x** so field bleed cannot weld the skyline.

Y is not a tower axis. Dipole `y` feeds the field (`data-depth`) but spikes and dipole *circles* are drawn on the pool line (`1338`, `1427-1428`). The picture is a 1D skyline.

### 3. Nearest-dipole coloring welds close magnets

`_nearest_dipole_index` (`601-610`, used `1117`) assigns overlapping field peaks to whichever magnet is closer. Close same-language dipoles share one ridge and one hue (`LANG_HUES["Python"]=215`). Capillaries (`1186-1266`) are ~10 px stubs — they must not replace the primary spike.

### 4. Two `field_gain`s multiplied; followers are soup

```1015:1015:scripts/art/ferrofluid.py
        maturity_ramp=signals.field_gain * dialect.knobs["field_gain"],
```

- `FerrofluidSignals.field_gain` (`400-421`) is a **composite** (repos, social, build, traffic, `0.14 * follower_scale`, `0.08 * star_scale`, …) floored at 0.18.
- Dialect `field_gain` is followers-only, floored at **0.82**. t0→t2 knob is 0.855→1.040 — a **22%** bump on an already-busy field.
- `max_spikes` also adds `18 * follower_scale` (`478`).

Isolation that reads “field” on the SVG will mix channels. Followers do not add a distinct mark (no extra column, settlement, or satellite). Magnet **count** is repos — do not steal that.

### 5. Commits are near-invisible ripples

`ripple_gain` adds rings (`723-724`) and slightly raises opacity (`745-753`), capped at **0.22**, typically **~0.09–0.12**, `stroke-width=0.5`, stroke `#0c2028`. A1 “ripple mass grow” is ellipse **count** (4→10→24), not a readable pool. Isolation asserts count + `data-ripple-gain` only (`test_living_art_media.py:1525-1537`). **No** ferrofluid stars or followers branch in that test.

### 6. Empty-metrics fake ripples are not a tower

Zero repos → empty `dipoles` → `_ambient_ripple_specs` synthesizes **three fake anchors** at x-fractions 0.28 / 0.50 / 0.72 (`677-688`). That is **not** a first-repo tower. A2 must use a snapshot with ≥1 named repo. Empty-metrics SVG may stay valid (`test_ferrofluid.py:265-268`); those fake ripples must not count as t0.

### Tests that currently certify the leftover

| Test | What it proves | What it does not |
|---|---|---|
| `test_early_spine_dialects_keep_repo_accretion_readable` ferro slice | t2 dipole count==4 and `min(gaps) ≥ 36` | towers, same-language columns, spike-column separation, t0 dipole≥1 |
| `test_leased_style_knobs_track_isolated_channels` ferro slice | ripple **count** + `data-ripple-gain` | stars height, followers field mark, overlay-stripped picture |
| `test_style_dialects_make_accretion_readable` | overlay ticks t0→t2 | picture |
| `test_generators_prefer_render_state` (ferro) | `data-role="ferro-dipole"` count > 0 | column identity |
| `test_ferrofluid_dense_repo_snapshots_keep_all_dipoles_and_add_capillaries` | dipole count == `len(repos)` | spacing |
| `test_ferrofluid_nearby_snapshots_keep_dipole_x_positions_without_seed` | x stable across nearby star/follower/commit nudges | columns |
| `test_art_shared_package.py` today | dialect family set includes `ferrofluid` | **no** t0 / isolation / tower-spacing yet (A1/A2 write the red bar here) |

---

## Shared constraints (all four nodes)

**Do**

- Consume today’s knobs: `spike_scale` / `ripple_gain` / dialect `field_gain`. A3 is a documented no-op unless all six share a clock failure (I08/I99). Do not retune `_CHANNEL_CEILINGS`.
- Keep `generate(metrics, *, seed, maturity) -> str`. Extra kwargs `timeline` / `loop_duration` / `reveal_fraction` stay. Module default `timeline=True`; isolation and GIFs must pass `timeline=False`.
- Keep one dipole / tower owner per named repo (`select_primary_repos` ignores `limit`; full set is intended). Dense snapshots still keep all dipoles (`test_ferrofluid.py:290-308`).
- Keep dipole **x stable** when stars / commits / followers nudge without an explicit seed (`test_ferrofluid.py:935-950`). Do not jitter x with those channels.
- Stop calling `language_cluster` for x. Tint may stay. **Do not rewrite** `scripts/art/shared/visual.py`.
- Leave `#accretion-dialect` in the SVG unless A3/RM ask to remove it. Dfe1–Dfe2 must **ignore** it, not delete it.
- Stay inside `CFG.max_elements` (25_000) and prefer `grid_resolution=60` unless a smaller *drawn* set is required for the byte cap.
- Keep `test_ferrofluid.py` green from Dfe1 (determinism, timeline inline opacity 0.95 for rasterizers, all dipoles kept, x-stability, empty/minimal SVG).

**Do not**

- Edit `scripts/art/shared/visual.py`, `scripts/art/shared/accretion.py`, `artifacts.py` budgets, `timelapse.py`, README, workflow, OpenSpec `prevent-living-art-repo-growth`, or `main`.
- Treat `min(gaps) ≥ 36` as tower identity.
- Raise `living-ferrofluid.gif` above **3_800_000** bytes (`artifacts.py:31`).
- Trigger `_assemble_gif` **12 MB halve** (`timelapse.py:295-324`) — that breaks 400×400.
- Use `generate animated` / `animate.py` for `living-*` (writes `{style}-growth.gif` from interpolated maturity).
- Reuse `goals/profile-readme-overhaul/inventory/frames/ferrofluid-t{0,1,2}.svg` as bake-off evidence (A1 t2 gaps 18.7; published GIFs were never rebuilt after 2026-08-14).
- Treat overlay ticks, `data-ripple-gain`, `data-ripple-count`, or the 36 px floor as Dfe1/Dfe2 done.
- Ship `living-ferrofluid-dark.gif` (unbudgeted; `_TIMELAPSE_RE` would reject it).
- Count empty-metrics fake ripples (`677-688`) as the t0 primary mark.
- Let capillaries (~10 px) replace the first-repo tower.

---

## Dfe1 — redesign on-canvas dialect (`L-FE`)

**Job:** N repos ⇒ N readable columns at 400×400 **without caption**; same-language must not collapse; stars height obvious; commits a visible pool mark; followers a leased field mark; t0 stays one tower. **3.8 MB** still feasible.

Graph verify: “t0 primary mark + four-channel motion.”

### Must change (picture)

1. **Stop `language_cluster` from owning x.** Remove `strategy="language_cluster"` from the ferrofluid call site (`911-913`). Language should tint (`_spike_gradient_palette` already does). Place by **stable repo identity / visual order / even columns**.

   Direction (implementer chooses the layout, not the leftover):
   - Index-along-pool: `x = WIDTH * (i+1) / (n+1)` (or visual-order equivalent). This is the most reliable path to N columns.
   - Or `repo_to_canvas_position(..., strategy="hash")` **only if** a following columnizer still yields even, readable towers. Hash alone can re-cluster by chance.
   - `_spread_positions` at 44 px may remain as a safety net. It is **not** the done state. Raise the gap toward `~WIDTH / (n+1)` **or** suppress field bleed (per-dipole spike sets, or a canonical tower polygon at each dipole x instead of a merged grid).

   Do **not** rewrite `visual.py`. Do not jitter x with stars / commits / followers.

2. **Towers, not a 36 px floor.** Separate **spike columns** so a caption-blind 400×400 glance shows N peaks, not a left hedge. Judge spike **mass** (polygons rooted at `pool_y`), not only dipole `cx`. Nearest-dipole coloring must not weld two magnets into one ridge. For four same-language repos, expect gaps in the ~160 px SVG / ~80 px GIF league, not 36–44.

3. **Same-language must not collapse.** Isolation and Dfe2 **must** use an all-Python (or all-Go) fixture. Alternating Python/Go still shares x-fraction 0.25 today and will miss the leftover if tests only check `min-gap ≥ 36`.

4. **Keep t0 as one visible tower** from the first named repo (dipole + primary spikes, not a capillary stub). Empty-metrics fake ripples must not count. Capillaries stay secondary.

5. **Stars: height already tracks `spike_scale`; make it obvious.** Isolation that grows only stars (same repos/commits/followers, `timeline=False`) must raise **max spike height** (tip `y` farther above `pool_y`). Optional: emit `data-spike-scale` on the root so Dfe2 can cross-check, but geometry is the pass. A merged hedge that merely looks like “more metal” fails.

6. **Commits: visible pool mark.** Ripples at opacity ~0.1 / `stroke-width=0.5` are not a channel. Raise contrast / width / count so they survive 400×400, **or** pick a different on-canvas commit mark (surface agitation, brighter rings, pool texture that actually shows). Isolation today only counts ellipses — Dfe1 must make the **picture** move.

7. **Followers: leased field mark, not composite soup.** Dialect `field_gain` floor 0.82 + product with `signals.field_gain` is not a distinct picture. Give followers a visible identity (pool extent, extra field lines, glow radius, magnet **strength** — not magnet **count**). Consider renaming the **local** composite (`FerrofluidSignals.field_gain` → e.g. `mesh_gain` / `composite_ramp`) while touching this file so Dfe2 can assert the **lease**. Do not retune the shared knob formula in `accretion.py`.

8. **Repos-only still moves column count.** Isolation that grows only the repo list (stars/commits/followers scalars fixed, same-language names) must increase **column count and keep them separated**.

### Byte budget (hard)

`living-ferrofluid.gif` cap **3.8 MB**. Published file sits ~3.49 MB. Grid 60 is enough if columns are **separated**, not if spike count explodes.

Prefer:

- Keep `grid_resolution=60`.
- Do not raise `max_spikes` / `max_elements` to fake density.
- Canonical per-dipole towers (few polygons) beat a denser merged mesh.

Local smoke **before** claiming Dfe1 done (does not replace G1fe):

```bash
uv run python - <<'PY'
from scripts.art.ferrofluid import generate

# Same-language t2 spine. timeline=False is the GIF path.
repos = [
    {
        "name": f"repo-{i}",
        "language": "Python",
        "stars": max(1, 120 // max(1, 4 - i)),
        "forks": 1,
        "date": f"2024-01-{i+1:02d}T12:00:00Z",
    }
    for i in range(4)
]
svg = generate(
    {
        "label": "ferro-dial",
        "repos": repos,
        "repo_visual_order": [r["name"] for r in repos],
        "stars": 120,
        "total_commits": 2400,
        "followers": 80,
        "star_velocity": {"recent_rate": 0, "peak_rate": 0},
    },
    seed="ferro-accretion",
    timeline=False,
)
assert svg.count('data-role="ferro-dipole"') == 4
# Then measure spike-column separation at pool_y — not only dipole cx.
print(svg.count('data-role="ferro-spike"'), "spikes")
PY
```

Optional size probe: render a **short** 400×400 GIF (e.g. 8 frames) and scale `size * 120/8` as a crude upper bound. If that projection exceeds ~3.8 MB, reduce drawn primitives — do not plan to raise the cap. Never pass `--size` that would invite the 12 MB halve.

Dfe1 does **not** commit `living-ferrofluid.gif`. Do not run full-fleet `generate living-art` without `--only`.

### Palette

Dfe1 may leave the near-black pool as-is if Dfe4 follows immediately. Do not block Dfe1 on luminance, but **do not add a second light/dark branch**. Column separation must work on the current `#000105`→`#000000` ground *and* after Dfe4 raises spike / dipole / ripple ink.

### Verify Dfe1

Caption-blind (strip `#accretion-dialect` / `data-role="accretion-dialect"` before judging):

- [ ] t0 `1/2/20/1`, `timeline=False`: one **tower** (dipole + primary spikes). Fake empty-metrics ripples are not this mark.
- [ ] Same-language t2 (four Pythons): **four readable columns** at 400×400. `min(gaps) ≥ 36` is **insufficient**.
- [ ] Repos-only (same-language names; stars/commits/followers scalars fixed): column **count** up and still separated.
- [ ] Stars-only: max spike height **up** (geometry, not overlay).
- [ ] Commits-only: pool mark **visibly** denser / brighter / larger — not only `data-ripple-gain`.
- [ ] Followers-only: leased field mark **geometry** up — not the product of two `field_gain`s, not magnet count.
- [ ] Dipole x still stable: `test_ferrofluid_nearby_snapshots_keep_dipole_x_positions_without_seed`.
- [ ] `uv run python -m pytest -q tests/test_ferrofluid.py`
- [ ] Existing media attr tests still green (they are insufficient, not retired):
  `uv run python -m pytest -q tests/test_living_art_media.py -k 'ferrofluid or leased_style_knobs or early_spine'`

Do not green Dfe1 by writing Dfe2 tests that still read `data-*` or `min(gaps) ≥ 36` only.

---

## Dfe2 — on-canvas t0 + isolation (`L-T-ACC`)

**Job:** make A1/A2 ferrofluid assertions green by proving the **picture**, not the caption, ripple attrs, or 36 px floor.

**File:** `tests/test_art_shared_package.py` only. Do **not** move the contract into `test_ferrofluid.py` or `test_living_art_media.py`. Those stay as generator/regression coverage.

Graph verify: `pytest -k ferrofluid`.

### Wait for A1/A2

A1/A2 land red/xfail on-canvas isolation in this same file (I08). Dfe2 greens the **ferrofluid** slice. If a shared D\*2 agent holds `L-T-ACC`, this playbook is that slice — still assert geometry here.

If A1/A2 are not present yet, Dfe2 **adds** the ferrofluid on-canvas tests (do not wait forever for names). Prefer sharing helpers with other dialects (overlay strip, `_accretion_metrics` clone with `star_velocity` pinned **and all-Python repos**).

### Required asserts (overlay stripped)

Strip `#accretion-dialect` (and do not score `data-ripple-gain` / `data-ripple-count` / overlay `data-mark-count` / `min(gaps) ≥ 36` as pass). Generate with `timeline=False`.

**Same-language fixture is mandatory** for repos / columns. Do not rely on `_accretion_metrics`’ alternating Python/Go.

| Case | Fixture | Pass |
|---|---|---|
| **t0 tower** | `_accretion_metrics(repos=1, stars=2, commits=20, followers=1)` | ≥1 `ferro-dipole` **and** a primary spike column above a visibility floor (height + opacity). Overlay ignored. Fake 0-repo ripples fail this case. |
| **repos-only** | repo list 1 → 4, **all Python**; stars/commits/followers scalars **fixed** | dipole/tower **count** up **and** spike-column separation (even-column / `~WIDTH/(n+1)` league, not 36 px) |
| **stars-only** | stars 8 → 180 | max `ferro-spike` height (pool_y − tip y) **strictly up** |
| **commits-only** | commits 40 → 3200 (media isolation magnitudes) | pool mark **geometry or ink** up (stroke/opacity/rx), not only ellipse count / `data-ripple-gain` |
| **followers-only** | followers 1 → 90 | leased field mark **geometry** up (extent, field-line length, glow) — not magnet count, not composite `signals.field_gain` |

Suggested selectors (Dfe1 should have made these real):

- repo mark: `data-role="ferro-dipole"` at `pool_y` **plus** owner-tagged `data-role="ferro-spike"` whose `points` form a distinct column
- stars: max spike height per SVG, optionally `data-spike-scale` as a cross-check only
- commits: `data-role="ferro-ripple"` (or replacement `data-role`) with opacity / stroke that is GIF-visible
- followers: a tagged field mark that is **not** `ferro-dipole` count

**Forbidden pass conditions:** root `data-ripple-gain`, `data-ripple-count`, overlay tick counts, `min(gaps) ≥ 36` alone, dipole count without column separation, 0-repo ambient ripples as t0.

Keep existing media attr tests; they are a weaker regression, not this bar. The ≥36 px assert may stay; Dfe2 should **tighten or supersede** it here as column-separation.

### `pytest -k ferrofluid` blast radius

That keyword also hits `tests/test_ferrofluid.py`, parametrized media/render-state tests, and coverage helpers — files **outside** `L-T-ACC`. Dfe2 must not edit those. If they fail after Dfe1, fix in **Dfe1** (`ferrofluid.py`), not here. Do not break x-stability or “all dipoles kept.”

```bash
uv run python -m pytest -q tests/test_art_shared_package.py -k ferrofluid
uv run python -m pytest -q tests/test_ferrofluid.py
# graph verify (wider):
uv run python -m pytest -q -k ferrofluid
```

---

## Dfe3 — bake-off stills (no lock)

**Files:**

- `goals/living-art-overhaul/bakeoff/ferrofluid-t0.svg`
- `goals/living-art-overhaul/bakeoff/ferrofluid-t1.svg`
- `goals/living-art-overhaul/bakeoff/ferrofluid-t2.svg`

Create the `bakeoff/` directory if needed. **Do not** copy `goals/profile-readme-overhaul/inventory/frames/ferrofluid-t*.svg` (pre-spread / pre-column A1; t2 min gap 18.7; published GIFs were never rebuilt after 2026-08-14).

### Export

Same spine and kwargs as A1, **same-language repos** (all Python) so the leftover cannot hide:

```text
timeline=False
seed stable (e.g. "ferro-accretion")
t0: repos=1, stars=2, commits=20, followers=1
t1: 2 / 24 / 400 / 18
t2: 4 / 120 / 2400 / 80
```

Prefer exporting **after Dfe4** so the stills show the raised skyline ink.

### Verify Dfe3

- [ ] Three files exist and are well-formed SVGs (`viewBox="0 0 800 800"`).
- [ ] `data-accretion-*` (repos/stars/commits/followers or scales) **increase** t0→t2.
- [ ] Caption-blind glance: **one tower per repo** (t2: four columns, not a left hedge). Overlay may still be present; it must not be the only readable growth.
- [ ] t0 still: one tower, not three ambient ripples.
- [ ] No `living-ferrofluid-dark` sibling implied by the stills.

Graph verify: “three stills + data-accretion attrs increase.”

---

## Dfe4 — one look (`L-FE`)

**Job:** `fact-one-look` — one designed look that reads on GitHub light **and** dark. No dual `-dark` pair unless bake-off later proves unreadable.

Graph verify: “no dual `-dark` pair unless unreadable.”

Designed as one dark sculpture: bg `#000105`→`#000000` (`1077-1087`), metallic spikes, pool stroke opacity 0.5. Overlay cyan-on-navy (`#8ec8ff` on `#0a0c14`) is the only guaranteed contrast today. Dipole markers opacity 0.21–0.28 and ripples ~0.1 vanish on GitHub **dark** at 400×400. GitHub **light** already frames a black rectangle (one look, not a pair). No `living-ferrofluid-dark.gif` exists; keep it that way unless bake-off proves unreadability.

### Must

- Keep the near-black pool. It is already one look.
- Raise spike / dipole / ripple (or replacement pool-mark) luminance so the **skyline** survives GitHub dark at 400×400. Overlay already contrasts; **towers** must.
- One look, not a CSS `@media` pair and not `living-ferrofluid-dark.gif`.
- Judge at **400×400** raster (GIF worker size), not only the 800 SVG.

### Must not

- Add a second generator path or `-dark` filename.
- Move overlay origin (A3 / all-six only).
- Re-open `language_cluster` or the 36 px floor if Dfe1 already made columns — only retouch color/contrast.
- Treat “black rectangle on light GitHub is fine” as Dfe4 done while dipoles/ripples still sit at opacity ~0.23 / ~0.09.

### Verify Dfe4

- [ ] Background remains the near-black magnetic ground (no world-lerp mid-gray, no second theme).
- [ ] Dipole + spike ink readable on GitHub dark at 400×400 (markers well above 0.23 if they are still the magnet mark).
- [ ] `rg living-ferrofluid-dark` is empty in production art paths.
- [ ] `uv run python -m pytest -q tests/test_ferrofluid.py` (palette/language tests may change SVG bytes; keep determinism + x-stability).
- [ ] Re-export Dfe3 stills if they were captured before this look.

---

## Sequence and handoff

```text
A3 (no-op clock) ──► Dfe1 (picture, 3.8 MB feasible; stop language_cluster for x)
                      ├─► Dfe4 (one look, same L-FE)
                      │     └─► Dfe3 (stills; re-export if Dfe4 landed after)
                      └─► Dfe2 (L-T-ACC queue: on-canvas tests)
W2M needs Dfe2 + Dfe3 + Dfe4
G1fe (after W2M): --only ferrofluid, 120 frames, 400×400, sibling MP4, ≤3.8 MB
K1fe scores the regenerated GIF, not A1 stills
```

G1fe command (later wave, not Dfe*):

```bash
uv run python -m scripts.cli generate living-art \
  --profile wyattowalsh \
  --metrics-path /path/to/metrics.json \
  --history-path /path/to/history.json \
  --only ferrofluid \
  --max-frames 120 \
  --size 400 \
  --workers 4 \
  --output-dir .github/assets/img
```

---

## Out of this lane

| Concern | Owner |
|---|---|
| README stack / `<details>` mapping copy (alt does not mention towers / four channels) | RM `M1`–`M5` |
| Shared accretion ceilings / overlay geometry | A3 / `L-ACC` |
| `language_cluster` helper body | **never this lane** — helper stays; Dfe1 stops calling it for x |
| `living-ferrofluid.gif` + `.mp4` regen | `G1fe` |
| Jury score | `K1fe` |
| Roster shrink / exact-six tests | SHR after K2 |
| OpenSpec growth change | never this goal (S15) |

---

## Done when

- **Dfe1:** caption-blind N repos ⇒ N columns (same-language fixture); `language_cluster` no longer owns x; **36 px is not the bar**; stars height obvious; commits a visible pool mark; followers a leased field mark; t0 is one tower (not fake ripples); 3.8 MB still plausible; `test_ferrofluid.py` green; x-stability held.
- **Dfe2:** `test_art_shared_package.py` asserts those geometries with overlay stripped — **not** `data-ripple-*` or `min(gaps) ≥ 36` only; `pytest -k ferrofluid` green without editing files outside `L-T-ACC`.
- **Dfe3:** three new bake-off SVGs; accretion attrs increase; glance shows **one tower per repo** (t2: four columns).
- **Dfe4:** near-black one look; skyline contrasts on GitHub dark; **no** `-dark` pair.

Overlay may remain. It must not be the picture.
