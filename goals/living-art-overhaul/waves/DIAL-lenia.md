# Wave DIAL — Lenia (`Dle1`–`Dle4`)

**Lane:** DLE. **Style key:** `lenia`. **Family:** morphogenetic.
**This file is the execution playbook.** Inventory evidence: [`../inventory/I13.md`](../inventory/I13.md), I99 Dle1 brief, `scripts/art/lenia.py`.
**No production edits while authoring this playbook.** Implementers own `Dle1`–`Dle4` later.

Caption here = the on-SVG `#accretion-dialect` register (family word + four numeric glyphs). Not the README `<details>` legend (Wave RM). Field occupancy and satellite extent must read **with that register ignored**.

Until K2, shipped == candidates == six. Do not shrink CI, drop `lenia` from the roster, or raise `LIVING_ART_BYTE_BUDGETS`.

---

## Lock / graph

| ID | Lock | File(s) | Deps | Parallel | Verify (graph) |
|---|---|---|---|---|---|
| **Dle1** | `L-LE` | `scripts/art/lenia.py` | A3, I13 | DIAL (with other `D*1`) | t0 primary mark + four-channel motion |
| **Dle2** | `L-T-ACC` | `tests/test_art_shared_package.py` **only** | Dle1 | serialize vs other `D*2` | `pytest -k lenia` |
| **Dle3** | — | `goals/living-art-overhaul/bakeoff/lenia-t{0,1,2}.svg` | Dle1 | STILL | three stills + `data-accretion-*` increase |
| **Dle4** | `L-LE` | `scripts/art/lenia.py` | Dle1 | LOOK | no dual `-dark` pair unless unreadable |

`Dle1` and `Dle4` share `L-LE` → **sequential on `lenia.py`**. `Dle2` serializes on `L-T-ACC` with Dig2/Dto2/Dge2/Dph2/Dfe2 — prefer one greening agent after all `D*1` (`plan.md`; I99 correction 9). `Dle3` has no shared lock.

**`L-LE` vs `L-T-ACC`:** `L-LE` is the generator (`lenia.py`) for Dle1 + Dle4. `L-T-ACC` is the shared on-canvas test file (`tests/test_art_shared_package.py`) for Dle2. Do not write Dle2 asserts into `test_lenia.py` or `test_living_art_media.py`. Do not hold `L-LE` while greening Dle2.

**Recommended lane order:** Dle1 → Dle4 (same file, one look on the redesigned field) → Dle3 stills (so bake-off is not muddy gray) → Dle2 when `L-T-ACC` is free. Graph allows Dle3 ∥ Dle4 after Dle1; if stills land before Dle4, **re-export** them after the look lands. W2M needs Dle2 + Dle3 + Dle4.

GIF regen is **not** this wave (`G1le` after W2M). Dle1 must still be encodable under the **1.2 MB** `living-lenia.gif` cap so G1le cannot pass only by raising budgets (repo-growth is out of scope).

---

## Target picture (without caption)

| Channel | Lease (keep names) | Intended on-canvas identity | Fail if you only prove |
|---|---|---|---|
| **repos** | count of organisms (no named knob) | one `kind="repo"` seed / organism per named repo | overlay `data-accretion-repos` |
| **stars** | `halo_scale = 0.75 + 0.70 * star_scale` | halo **radius and visible ink** | `data-halo-scale` / `r=` with opacity ~0.03 |
| **commits** | `field_gain = commit_scale` | **field occupancy / luminance** grows | `data-field-gain` / `data-simulation-mix` / `data-sim-steps` |
| **followers** | `extent_gain = follower_scale` | satellites **spread** (distance, distinct ink) | `data-extent-gain` / `data-satellite-count` |

Published GIF path (must be the isolation path too):

```text
generate(metrics, seed=…, maturity=snapshot.maturity, timeline=False)
```

`timelapse.py` forces `timeline=False`. `growth_mat = mat` on that path (not 1.0). Overlay origin for lenia is **(516, 36)** top-right — leave it unless A3 moves every dialect.

A1 spine (reuse `_accretion_metrics` in `tests/test_living_art_media.py:1144`):

| Frame | repos / stars / commits / followers | `field_gain` | `extent_gain` | `halo_scale` |
|---|---|---|---|---|
| t0 | 1 / 2 / 20 / 1 | 0.339 | 0.116 | 0.874 |
| t1 | 2 / 24 / 400 / 18 | 0.667 | 0.491 | 1.112 |
| t2 | 4 / 120 / 2400 / 80 | 0.866 | 0.733 | 1.290 |

Pin `star_velocity={recent_rate:0, peak_rate:0}` in isolation fixtures (I08). `_accretion_metrics` currently leaks stars into `star_velocity`.

---

## Residue (why today’s GIF is caption-only)

Evidence: I13 + I99 Dle1 brief. Live code, not the 2026-08-14 A1 stills.

### 1. `simulation_mix` cap then residue `max()` kills the CA

```1937:1953:scripts/art/lenia.py
    residue_gain = min(
        1.0,
        0.55
        + 0.35 * dynamics.activity_drive
        + 0.15 * dynamics.repo_density
        + 0.10 * dynamics.release_energy,
    )
    seed_residue = np.clip(seed_field * residue_gain, 0.0, 1.0)
    simulation_mix = min(
        0.34,
        0.05
        + 0.10 * dynamics.activity_drive
        + 0.04 * dynamics.recent_flux
        + 0.03 * dynamics.release_energy
        + 0.16 * field_gain,
    )
    field = np.maximum(seed_residue, np.clip(field * simulation_mix, 0.0, 1.0))
```

Even `field_gain = 1.0` cannot exceed mix **0.34**. t0 mix on the A1 spine is **0.110**; t2 is **0.277**. `np.maximum` then keeps seed blobs wherever they outshine the crushed CA. Cell count tracks **repo seeds**, not a filling field. Core pass `v ≥ 0.65` (`lenia.py:764-766`) is **empty on t0, t1, and t2**.

`field_gain` also adds sim steps (`+10 * field_gain` in `_derive_dynamics`, `+ int(round(16 * field_gain))` at generate). Those extra steps are wasted while mix ≤ 0.34.

### 2. Field has no SVG identity

Organism circles (`lenia.py:754-757`) have **no `data-role`**. Media isolation asserts root `data-field-gain` / `data-simulation-mix` / `data-sim-steps` only (`tests/test_living_art_media.py:1509-1517`). That will stay green if Dle1 never changes the picture.

### 3. Extent hugs the host at GIF-invisible opacity

Satellites already exist at 1 follower (t0 count **2**). Forced extras (`lenia.py:1608-1638`):

- `extent_radius = 0.85 + 1.10 * extent_gain` → t0 **0.98**, t2 **1.66**
- `sat_distance = max(2, int(round((2.2 + extra_idx) * extent_radius)))` → **2 cells** at t0

Grid is 50; cell is 16 px on the 800 SVG and **8 px on the 400 GIF**. Two cells = 16 px of “territory.” Halo/orbit opacity **0.007–0.036**. Isolation asserts `data-satellite-count` + `data-extent-gain` only (`:1518-1522`).

### 4. t0 organism exists but does not survive 400×400 as a readable mark

t0 (A1 still / live generate): 1 repo halo at (152, 296), **r=18.5, opacity 0.031**; 9 unlabeled cells opacity **0.107–0.152**. `_fade_ramp` residue floor is **0.12** (`lenia.py:803-817`; `test_lenia_static_low_maturity_keeps_seed_residue_visible`). A count of `lenia-seed-halo` passes; a caption-blind GIF glance fails.

Halo opacity (`:633-635`) is `(0.06 + 0.06 * visibility + 0.05 * amplitude) * _fade_ramp(...)`. At GIF maturity ≈ 0.01 that product is ~0.03.

### 5. Designed look is unused (Dle4, not a Dle1 blocker)

`_BIO_RAMP` and `_BG_COLOR = oklch(0.08, 0.04, 280)` (`lenia.py:157-167`) are **never referenced**. Live palette is world-lerp muddy gray (`#677c7c` / `#798d8d`) + amber/rose blobs. Overlay cyan-on-navy is the only high-contrast region.

### Tests that currently certify the leftover

| Test | What it proves | What it does not |
|---|---|---|
| `test_leased_style_knobs_track_isolated_channels` | attrs + repo-halo `r=` | occupancy, satellite **distance**, halo **ink**, overlay-stripped t0 |
| `test_style_dialects_make_accretion_readable` | overlay ticks t0→t2 | picture |
| `test_generators_prefer_render_state` (lenia) | `data-role="lenia-seed-halo"` count > 0 | visibility |
| `test_lenia_static_low_maturity_keeps_seed_residue_visible` | `max(opacity) ≥ 0.12` | GIF-readable organism |
| `test_art_shared_package.py` today | dialect family set | **no** t0 / isolation yet (A1/A2 write the red bar here) |

`test_early_spine_dialects_keep_repo_accretion_readable` covers ink/physarum/ferro **not** lenia.

---

## Shared constraints (all four nodes)

**Do**

- Consume today’s knobs: `halo_scale` / `field_gain` / `extent_gain`. A3 is a documented no-op unless all six share a clock failure (I08/I99). Do not retune `_CHANNEL_CEILINGS`.
- Keep `generate(metrics, *, seed, maturity) -> str`. Extra kwargs `timeline` / `loop_duration` / `reveal_fraction` stay.
- Keep one organism per named repo (`_augment_primary_repos` still ignores `limit`; full set is intended).
- Keep `language_cluster` usage in `_semantic_repo_positions`. Do **not** rewrite `scripts/art/shared/visual.py` (I14 lock: Dfe1 stops *calling* it; helper stays).
- Leave `#accretion-dialect` in the SVG unless A3/RM ask to remove it. Dle1–Dle2 must **ignore** it, not delete it.
- Stay inside `CFG.max_elements` (25_000) and `grid_resolution=50` unless a smaller *drawn* set is required for the byte cap.
- Keep `test_lenia.py` green from Dle1 (determinism, timeline inline opacity, residue `≥ 0.12`, full-repo halo count, language mix).

**Do not**

- Edit `scripts/art/shared/accretion.py`, `artifacts.py` budgets, `timelapse.py`, README, workflow, OpenSpec `prevent-living-art-repo-growth`, or `main`.
- Raise `living-lenia.gif` above **1_200_000** bytes (`artifacts.py:34`). Tightest of the six.
- Trigger `_assemble_gif` **12 MB halve** (`timelapse.py:295-324`) — that breaks 400×400.
- Use `generate animated` / `animate.py` for `living-*` (writes `{style}-growth.gif` from interpolated maturity).
- Reuse `goals/profile-readme-overhaul/inventory/frames/lenia-t{0,1,2}.svg` as bake-off evidence.
- Treat overlay ticks, `data-field-gain`, `data-extent-gain`, `data-simulation-mix`, or `data-satellite-count` as Dle1/Dle2 done.
- Ship `living-lenia-dark.gif` (unbudgeted; `_TIMELAPSE_RE` would reject it).
- Hold `L-T-ACC` from Dle1. Generator edits stay on `L-LE`.

---

## Dle1 — redesign on-canvas dialect (`L-LE`)

**Job:** field occupancy and satellite extent visible **without caption**; t0 organism survives 400×400; **1.2 MB** still feasible.

Graph verify: “t0 primary mark + four-channel motion.”

### Must change (picture)

1. **Stop residue from hiding the CA.** Remove or raise the `min(0.34, …)` cap. Do not composite as `max(seed_residue, field * mix)` if that leaves t2 looking like dim seeds. Residue is a **low-maturity / low-commit floor**, not a mask that wins after simulation. After the change, a commits-only pair (same repos/stars/followers, `timeline=False`) must increase **occupied mass or luminance**, not only mix/steps attrs.

   Direction (implementer chooses the blend, not the leftover):
   - Let the simulated field be the picture when `field_gain` rises.
   - Keep a visible seed organism at t0 / `maturity≈0` so `test_lenia_static_low_maturity_keeps_seed_residue_visible` stays true (`max(opacity) ≥ 0.12` is a floor, not the target).

2. **Give field a visible identity.** Tag organism cells (`data-role="lenia-organism"` or equivalent on a field group). Lower or scale the core threshold so cores can fire when occupancy is high (`v ≥ 0.65` never fires through t2 today). Occupancy may be brighter/larger cells, a filled density path, or a subsampled grid — **not** thousands of new circles if that blows 1.2 MB.

3. **Give extent a visible identity.** Satellites may keep existing from the first follower. They must **spread** at GIF scale: distance in cells that is obvious at 8 px/cell (aim for tens of GIF pixels, not 16). Distinct color from repo hosts. Opacity in the same league as the organism (not 0.007). Forced satellites (`:1608`) must not hug the host. Nutrient orbits are secondary, not the extent mark.

4. **t0 primary mark at 400×400.** One-repo A1 spine still draws a creature (halo **and** field cells). Halo/cell opacity well above the 0.12 residue floor — enough that a 400 raster shows a blob without reading the top-right strip. Empty / 0-repo payloads may stay a hash fallback seed (`:1698-1714`); A2 uses **1 repo**.

5. **Repos-only still moves count.** Isolation that grows only the repo list (stars/commits/followers scalars fixed) must increase repo-kind organisms. Not covered by today’s media isolation test.

6. **Stars: radius *and* ink.** Keep `halo_scale` on repo halo `r`. Stroke or fill opacity must also move, or the radius change stays wasted at GIF scale.

### Byte budget (hard)

`living-lenia.gif` cap **1.2 MB**. Grid 50 is enough if cells are **brighter, not more numerous**. Prefer:

- Keep `grid_resolution=50`.
- Do not emit one SVG circle per occupied cell if occupancy fills the grid — merge, subsample, or use a small number of blobs/paths.
- Count `max_elements` before shipping a dense field.

Local smoke **before** claiming Dle1 done (does not replace G1le):

```bash
# Element / role sanity on the GIF kwargs path (A1 t0 + commits-high).
uv run python - <<'PY'
from scripts.art.lenia import generate
# reuse the same spine shape as tests.test_living_art_media._accretion_metrics
PY
```

Optional size probe: render a **short** 400×400 GIF (e.g. 8 frames) and scale `size * 120/8` as a crude upper bound. If that projection exceeds ~1.2 MB, reduce drawn primitives — do not plan to raise the cap. Never pass `--size` that would invite the 12 MB halve.

Dle1 does **not** commit `living-lenia.gif`. Do not run full-fleet `generate living-art` without `--only`.

### Palette

Dle1 may leave `_BIO_RAMP` / `_BG_COLOR` unwired if Dle4 follows immediately. Do not block Dle1 on the look, but **do not add a second light/dark branch**. Opacity/occupancy must work on the current muddy ground *and* on the intended dark ground.

### Verify Dle1

Caption-blind (strip `#accretion-dialect` / `data-role="accretion-dialect"` before judging):

- [ ] t0 `1/2/20/1`, `timeline=False`: organism visible (halo + field ink), opacity ≫ 0.03.
- [ ] Commits-only: occupied field mass or luminance **up** (cell `data-role` count, bbox area, or mean field) — not only `data-field-gain`.
- [ ] Followers-only: satellite **spread** (mean/max distance from host, or bbox of `data-kind="satellite"`) **up** — not only `data-satellite-count`.
- [ ] Stars-only: repo halo `r` **and** visible ink **up**.
- [ ] Repos-only: repo organism count **up**.
- [ ] `uv run python -m pytest -q tests/test_lenia.py`
- [ ] Existing media attr tests still green (they are insufficient, not retired):
  `uv run python -m pytest -q tests/test_living_art_media.py -k 'lenia or leased_style_knobs'`

Do not green Dle1 by writing Dle2 tests that still read `data-*` only.

---

## Dle2 — on-canvas t0 + isolation (`L-T-ACC`)

**Job:** make A1/A2 lenia assertions green by proving the **picture**, not the caption or root attrs.

**File:** `tests/test_art_shared_package.py` only. Do **not** move the contract into `test_lenia.py` or `test_living_art_media.py`. Those stay as generator/regression coverage.

Graph verify: `pytest -k lenia`.

### Wait for A1/A2

A1/A2 land red/xfail on-canvas isolation in this same file (I08). Dle2 greens the **lenia** slice. If a shared D\*2 agent holds `L-T-ACC`, this playbook is that slice — still assert geometry here.

If A1/A2 are not present yet, Dle2 **adds** the lenia on-canvas tests (do not wait forever for names). Prefer sharing helpers with other dialects (overlay strip, `_accretion_metrics` clone with `star_velocity` pinned).

### Required asserts (overlay stripped)

Strip `#accretion-dialect` (and do not score `data-field-gain` / `data-extent-gain` / `data-simulation-mix` / `data-satellite-count` / overlay `data-mark-count` as pass). Generate with `timeline=False`, no `evolution_state`.

| Case | Fixture | Pass |
|---|---|---|
| **t0 creature** | `_accretion_metrics(repos=1, stars=2, commits=20, followers=1)` | ≥1 repo seed/organism **above a visibility floor** (opacity and size, not mere presence). Overlay ignored. |
| **commits-only** | same repos/stars/followers; commits 40 → 3200 (media isolation magnitudes) | occupied field mass / tagged cell count / bbox area **strictly up** |
| **followers-only** | followers 1 → 90 | satellite **geometry** spread (distance or bbox), not count attr alone |
| **stars-only** | stars 8 → 180 | halo radius **and** visible ink |
| **repos-only** | repo list 1 → 4; stars/commits/followers scalars **fixed** | repo-kind organism **count** up |

Suggested selectors (Dle1 should have made these real):

- repo mark: `data-role="lenia-seed-halo"` + `data-kind="repo"` with `opacity=` / inline style opacity
- field: `data-role="lenia-organism"` (or tagged field group) — **must not** be unlabeled `<circle>` only
- extent: `data-kind="satellite"` positions vs host; require a min GIF-scale gap that grows with followers

**Forbidden pass conditions:** root `data-field-gain`, `data-extent-gain`, `data-simulation-mix`, `data-sim-steps`, `data-satellite-count`, overlay tick counts.

Keep existing media attr tests; they are a weaker regression, not this bar.

### `pytest -k lenia` blast radius

That keyword also hits `tests/test_lenia.py`, parametrized media/render-state tests, and coverage helpers — files **outside** `L-T-ACC`. Dle2 must not edit those. If they fail after Dle1, fix in **Dle1** (`lenia.py`), not here.

```bash
uv run python -m pytest -q tests/test_art_shared_package.py -k lenia
uv run python -m pytest -q tests/test_lenia.py
# graph verify (wider):
uv run python -m pytest -q -k lenia
```

---

## Dle3 — bake-off stills (no lock)

**Files:**

- `goals/living-art-overhaul/bakeoff/lenia-t0.svg`
- `goals/living-art-overhaul/bakeoff/lenia-t1.svg`
- `goals/living-art-overhaul/bakeoff/lenia-t2.svg`

Create the `bakeoff/` directory if needed. **Do not** copy `goals/profile-readme-overhaul/inventory/frames/lenia-t*.svg` (pre-regen A1; published GIFs were never rebuilt after 2026-08-14).

### Export

Same spine and kwargs as A1:

```text
timeline=False
seed stable (e.g. "lenia-dialect")
t0: repos=1, stars=2, commits=20, followers=1
t1: 2 / 24 / 400 / 18
t2: 4 / 120 / 2400 / 80
```

Prefer exporting **after Dle4** so the stills show the dark morphogenetic ground.

### Verify Dle3

- [ ] Three files exist and are well-formed SVGs (`viewBox="0 0 800 800"`).
- [ ] `data-accretion-*` (repos/stars/commits/followers or scales) **increase** t0→t2.
- [ ] Caption-blind glance: field **fills** (occupancy/luminance) and extent **spreads** (satellites leave the host). Overlay may still be present; it must not be the only readable growth.
- [ ] No `living-lenia-dark` sibling implied by the stills.

Graph verify: “three stills + data-accretion attrs increase.”

---

## Dle4 — one look (`L-LE`)

**Job:** `fact-one-look` — one designed look that reads on GitHub light **and** dark. No dual `-dark` pair unless bake-off later proves unreadable.

Graph verify: “no dual `-dark` pair unless unreadable.”

### Must

- Wire or replace unused `_BIO_RAMP` / `_BG_COLOR` (`lenia.py:157-167`). Intended: near-black field `oklch(0.08, 0.04, 280)`, luminous deep blue → cyan → green → white-green organisms.
- Stop living on mid-gray `#677c7c` + amber 0.15 blobs as the designed look. Overlay already contrasts; the **field** must.
- One look, not a CSS `@media` pair and not `living-lenia-dark.gif`.
- Judge at **400×400** raster (GIF worker size), not only the 800 SVG. Luminous-on-dark typically survives both GitHub themes; muddy gray does not.

### Must not

- Add a second generator path or `-dark` filename.
- Move overlay origin (A3 / all-six only).
- Re-open mix/residue if Dle1 already made occupancy track `field_gain` — only retouch color/contrast.

### Verify Dle4

- [ ] `_BIO_RAMP` or `_BG_COLOR` (or a documented successor) is referenced from `_build_lenia_palette` / `_field_to_color`.
- [ ] Background is the dark morphogenetic ground, not world-lerp mid-gray as the hero fill.
- [ ] `rg living-lenia-dark` is empty in production art paths.
- [ ] `uv run python -m pytest -q tests/test_lenia.py` (palette/language tests may change SVG bytes; keep determinism).
- [ ] Re-export Dle3 stills if they were captured before this look.

---

## Sequence and handoff

```text
A3 (no-op clock) ──► Dle1 (picture, 1.2 MB feasible)
                      ├─► Dle4 (one look, same L-LE)
                      │     └─► Dle3 (stills; re-export if Dle4 landed after)
                      └─► Dle2 (L-T-ACC queue: on-canvas tests)
W2M needs Dle2 + Dle3 + Dle4
G1le (after W2M): --only lenia, 120 frames, 400×400, sibling MP4, ≤1.2 MB
K1le scores the regenerated GIF, not A1 stills
```

G1le command (later wave, not Dle*):

```bash
uv run python -m scripts.cli generate living-art \
  --profile wyattowalsh \
  --metrics-path /path/to/metrics.json \
  --history-path /path/to/history.json \
  --only lenia \
  --max-frames 120 \
  --size 400 \
  --workers 4 \
  --output-dir .github/assets/img
```

---

## Out of this lane

| Concern | Owner |
|---|---|
| README stack / `<details>` mapping copy | RM `M1`–`M5` |
| Shared accretion ceilings / overlay geometry | A3 / `L-ACC` |
| `living-lenia.gif` + `.mp4` regen | `G1le` |
| Jury score | `K1le` |
| Roster shrink / exact-six tests | SHR after K2 |
| OpenSpec growth change | never this goal (S15) |

---

## Done when

- **Dle1:** caption-blind field occupancy tracks commits; satellite extent spreads with followers; t0 creature readable at 400×400; 1.2 MB still plausible; `test_lenia.py` green.
- **Dle2:** `test_art_shared_package.py` asserts those geometries with overlay stripped — **not** `data-*` only; `pytest -k lenia` green without editing files outside `L-T-ACC`.
- **Dle3:** three new bake-off SVGs; accretion attrs increase; glance shows field + extent.
- **Dle4:** unused bioluminescent ground is the look; no `-dark` pair.

Overlay may remain. It must not be the picture.
