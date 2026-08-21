# Wave DIAL — Ink Garden (`Dig1`–`Dig4`)

**Lane:** DIG. **Style key:** `inkgarden`. **Family:** botanical.
**This file is the execution playbook.** Inventory evidence: [`../inventory/I09.md`](../inventory/I09.md), I99 Dig1 brief, `scripts/art/ink_garden.py`.
**No production edits while authoring this playbook.** Implementers own `Dig1`–`Dig4` later.

Caption here = the on-SVG `#accretion-dialect` register (family word + four numeric glyphs). Not the README `<details>` legend (Wave RM). Plant count, bloom, trunk, and glints must read **with that register ignored**.

Until K2, shipped == candidates == six. Do not shrink CI, drop `inkgarden` from the roster, or raise `LIVING_ART_BYTE_BUDGETS`.

---

## Lock / graph

| ID | Lock | File(s) | Deps | Parallel | Verify (graph) |
|---|---|---|---|---|---|
| **Dig1** | `L-IG` | `scripts/art/ink_garden.py` | A3, I09 | DIAL (with other `D*1`) | t0 primary mark + four-channel motion |
| **Dig2** | `L-T-ACC` | `tests/test_art_shared_package.py` **only** | Dig1 | serialize vs other `D*2` | `pytest -k inkgarden` |
| **Dig3** | — | `goals/living-art-overhaul/bakeoff/inkgarden-t{0,1,2}.svg` | Dig1 | STILL | three stills + `data-accretion-*` increase |
| **Dig4** | `L-IG` | `scripts/art/ink_garden.py` | Dig1 | LOOK | no dual `-dark` pair unless unreadable |

`Dig1` and `Dig4` share `L-IG` → **sequential on `ink_garden.py`**. `Dig2` serializes on `L-T-ACC` with Dto2/Dge2/Dph2/Dle2/Dfe2 — prefer one greening agent after all `D*1` (`plan.md`; I99 correction 9). `Dig3` has no shared lock.

**Recommended lane order:** Dig1 → Dig3 (stills of the redesigned garden) → Dig4 (parchment look on the same `L-IG` file) → Dig2 when `L-T-ACC` is free. Graph allows Dig3 ∥ Dig4 after Dig1. If stills land before Dig4, **re-export** them after the parchment look lands. Do **not** wait for Dig4 to start Dig3. W2M needs Dig2 + Dig3 + Dig4.

GIF regen is **not** this wave (`G1ig` after W2M). Dig1 must still be encodable under the **7.2 MB** `living-inkgarden.gif` cap so G1ig cannot pass only by raising budgets (repo-growth is out of scope). Headroom today is **~639 KB** (~91% of cap).

---

## Target picture (without caption)

| Channel | Lease (keep names) | Intended on-canvas identity | Fail if you only prove |
|---|---|---|---|
| **repos** | count of plants (no named knob) | one `class="repo-tree"` **plant** (stem **and** canopy) per named repo | overlay `data-accretion-repos` / empty soil + ticks |
| **stars** | `bloom_scale = 0.55 + 1.85 * star_scale` | bloom **count and size** on the plant | `data-accretion-star-scale` / petal ticks |
| **commits** | `trunk_scale = 0.70 + 1.50 * commit_scale` | trunk **length and stroke** | `data-accretion-commit-scale` / ring ticks |
| **followers** | `glint_count = 0` if followers≤0 else `1 + 7 * follower_scale` | firefly / glint **count** with velocity pinned | overlay seed ticks / `star_velocity` glow |

Published GIF path (must be the isolation path too):

```text
generate(metrics, seed=…, maturity=snapshot.maturity, timeline=False)
```

`timelapse.py` forces `timeline=False`. Overlay origin for inkgarden is **(40, 742)** bottom-left — leave it unless A3 moves every dialect.

A1 spine (reuse `_accretion_metrics` in `tests/test_living_art_media.py:1144`):

| Frame | repos / stars / commits / followers | `bloom_scale` | `trunk_scale` | `glint_count` |
|---|---|---|---|---|
| t0 | 1 / 2 / 20 / 1 | 0.877 | 1.209 | 1.81 |
| t1 | 2 / 24 / 400 / 18 | 1.508 | 1.700 | 4.44 |
| t2 | 4 / 120 / 2400 / 80 | 1.98 | 2.00 | 6.13 |

Pin `star_velocity={recent_rate:0, peak_rate:0}` in isolation fixtures (I08). `_accretion_metrics` currently leaks stars into `star_velocity`.

---

## Residue (why today’s GIF is caption-only)

Evidence: I09 + I99 Dig1 brief. Live code, not the 2026-08-14 A1 stills.

### 1. A1 empty-garden still is stale — do not treat it as t0

`goals/profile-readme-overhaul/inventory/frames/inkgarden-t0.svg` (signed 2026-08-14): **0** `<g class="repo-tree">`, overlay yes, caption “t0 still sparse.” That does **not** match current `generate()`.

Live rescue (`ink_garden.py:1605-1612`):

```1605:1612:scripts/art/ink_garden.py
        # Snapshot worlds (daily spine / computed maturity) keep existing
        # repos visible; explicit maturity staging still hides later trees.
        show_existing_world = timelapse_contract or maturity is None
        if tree_t <= 0.0 or (chronological_growth and tree_t < 0.05):
            if show_existing_world or is_oldest:
                tree_t = max(tree_t, 0.34)
            else:
                continue
```

Daily GIF (`timeline=False` + `is_monotonic_timelapse_metrics`) draws ≥1 `repo-tree` whenever the snapshot has ≥1 named repo. Dig1 is **not** “add the 0.34 floor.” Dig1 is: make that first plant a **readable garden mark**, and stop treating overlay ticks as the garden.

### 2. Rescued `tree_t=0.34` fails the bloom gate on dated worlds

Chronological leaf/bloom/detail gates (`ink_garden.py:1636-1675`): default `leaf=0.20`, `bloom=0.48`, `detail=0.68` (fresh repos even later). A rescued `tree_t = 0.34` **fails bloom 0.48**, so first-repo frames on dated 2+ repo worlds are stem/soil, not flowers.

`chronological_growth = len(dated_repo_fracs) >= 2` (`:1387`). A 1-repo A1 t0 fixture is **non-chronological** and sets those gates to `0.0` (`:1660-1662`). The leftover still holds because `tree_t=0.34` shortens `main_length` / `stem_sw` (`:1744-1784`) and bloom probability stays tiny at 2 stars. On the published GIF, the day the second dated repo appears flips the garden onto the 0.48 bloom gate.

Also gated on `mat` itself (no plants required): webs `mat > 0.25`, ambient seeds `mat > 0.2`, samaras `mat > 0.35`. t0 `mat ≈ 0.012` skips all three. Those are chrome, not the primary mark.

### 3. Bloom / trunk motion is on the knob, not on the canvas

| Channel | Knob path | Live picture (I09 probe, `star_velocity=0`) |
|---|---|---|
| stars | `bloom_boost *= dialect.knobs["bloom_scale"] / 1.4` (`:1794-1814`) then `tree_t >= bloom_growth_gate` (`:2150`, `:2202`) | blooms ~0 → ~1 when stars 8 → 180. **Weak.** Tooltip height is `max(40, …)` so it does not track canopy. |
| commits | `commit_factor = dialect.knobs["trunk_scale"]` scales `main_length` (`:1744-1774`); extra `total_commits/4000` in `stem_sw` | max stroke-width 2.00 → 2.50 when commits 40 → 4000. **Weak.** |
| repos | one `class="repo-tree"` per rendered repo | **only strong garden mark today** (2 → 4 plants). |

Knobs are **not** serialized as `data-bloom-scale` / `data-trunk-scale` / `data-glint-count`. Root only has `data-accretion-*` scales. Overlay ticks already grow (`test_style_dialects_make_accretion_readable`). Knob-only tests would be green today and stall DIAL.

### 4. `glint_count` leaks `star_velocity`

```4301:4305:scripts/art/ink_garden.py
    # ── Fireflies (star velocity driven) ─────────────────────────
    star_vel = metrics.get("star_velocity", {})
    star_rate = star_vel.get("recent_rate", 0) if isinstance(star_vel, dict) else 0
    follower_glints = int(round(dialect.knobs["glint_count"]))
    n_fireflies = min(16, max(int(star_rate * 2), follower_glints))
```

A **second** layer (`firefly_elements(star_velocity)` `:4332-4344`) is stars-only and draws whenever `recent_rate > 0`. Isolation must pin `star_velocity={recent_rate:0, peak_rate:0}`. Followers 0 must draw **0** garden glints.

### 5. Night-cosmic vs parchment is a second look (Dig4, not a Dig1 blocker)

Module docstring (`ink_garden.py:12`): **“Light theme on aged paper.”** No `@media`, no `living-inkgarden-dark.gif`.

What actually ships:

- Paper fill uses `pal["bg_primary"]` (`:2922-2924`). Night commit hours (peak 21–4h, `:1228-1230`) send `select_palette_for_world` to `"cosmic"` and `_build_world_palette_extended` sets `bg_primary = oklch(0.12, 0.03, 260)` (`palette.py:102-103`, `:147-149`).
- Defs stay parchment: `lighting-color="#f8f3ea"`, vignette `#f5f0e6` → `#8a7850` (`:2787-2813`). Night bg + parchment foxing is a mixed look.
- Night chrome: 30 white sky dots + crescent moon (`:3647-3663`). Overlay family ink/paper stays `#6a5a4a` / `#f5f0e6` (`accretion.py:35-36`).

A1 spine isolation usually omits `commit_hour_distribution` (default peak hour 12 → day). Real-account GIFs can still flip to near-black. Dig4 freezes **one parchment look**. Do not add a second GIF.

### Tests that currently certify the leftover

| Test | What it proves | What it does not |
|---|---|---|
| `test_early_spine_dialects_keep_repo_accretion_readable` | `ink_plants[0] >= 1`, monotonic plant count | canopy, bloom, trunk, glints |
| `test_ink_and_physarum_knobs_track_stars_and_followers` | firefly circles grow with followers | pin `star_velocity`; bloom/trunk isolation |
| `test_maturity_zero_returns_svg` | SVG wrappers | docstring still says “blank soil”; live code draws the oldest plant |
| `test_dated_growth_prefers_older_repos_before_late_star_projects` | explicit `maturity=0.24` hides `late-hit` | daily GIF (`timelapse_contract`) |
| `test_style_dialects_make_accretion_readable` | overlay ticks t0→t2 | picture |
| `test_art_shared_package.py` today | dialect family set | **no** t0 / isolation yet (A1/A2 write the red bar here) |
| Goldens `tests/fixtures/ink_garden/{minimal_full,rich_full,rich_mid}.svg` | full/mid maturity bytes | **no t0 golden** |

---

## Shared constraints (all four nodes)

**Do**

- Consume today’s knobs: `bloom_scale` / `trunk_scale` / `glint_count`. A3 is a documented no-op unless all six share a clock failure (I08/I99). Do not retune `_CHANNEL_CEILINGS`.
- Keep `generate(metrics, *, seed, maturity) -> str`. Extra kwargs `timeline` / `loop_duration` / `reveal_fraction` stay.
- Keep plants = repos. One `class="repo-tree"` per rendered named repo. 0-repo days stay empty (account-created-before-first-repo). A2 uses **1 repo**.
- Leave `#accretion-dialect` in the SVG unless A3/RM ask to remove it. Dig1–Dig2 must **ignore** it, not delete it.
- Prefer extra `data-bloom-scale` / `data-trunk-scale` / `data-glint-count` on the SVG if A1 red tests will key off attrs. Overlay ticks are still not the garden.
- Stay inside `MAX_BLOOMS` (80), `MAX_LEAVES` (600), `MAX_ELEMENTS` (25_000). Prefer **larger / more opaque** marks over more primitives.
- Keep `test_ink_garden.py` + `test_ink_garden_timeline.py` green from Dig1 (determinism, dated-growth staging, goldens, SMIL). Refresh goldens in **Dig1** if geometry changes — they are not `L-T-ACC`.
- Species table `SPECIES` (`:89-175`) has oak/birch/conifer/shrub/wildflower/wisteria/banyan. **fern / bamboo / seedling** are special-cased and absent from `SPECIES`. Do not `SPECIES[species]` blindly.

**Do not**

- Edit `scripts/art/shared/accretion.py`, `artifacts.py` budgets, `timelapse.py`, README, workflow, OpenSpec `prevent-living-art-repo-growth`, or `main`.
- Raise `living-inkgarden.gif` above **7_200_000** bytes (`artifacts.py:33`). Tightest botanical budget; current checked-in file is 6_560_879.
- Trigger `_assemble_gif` **12 MB halve** (`timelapse.py:295-324`) — that breaks 400×400.
- Use `generate animated` / `animate.py` for `living-*` (writes `{style}-growth.gif` from interpolated maturity).
- Reuse `goals/profile-readme-overhaul/inventory/frames/inkgarden-t{0,1,2}.svg` as bake-off evidence.
- Treat overlay ticks, `data-accretion-*`, or plant-count-only as Dig1/Dig2 done.
- Ship `living-inkgarden-dark.gif` (unbudgeted; `_TIMELAPSE_RE` would reject it).
- Break `test_dated_growth_prefers_older_*` unless you also update that test: explicit `maturity=` without `cumulative_state` is **animate staging**, not the daily GIF.

---

## Dig1 — redesign on-canvas dialect (`L-IG`)

**Job:** first-repo frame is a learnable plant (stem **and** canopy); bloom / trunk / glints isolate on canvas with velocity pinned; 0-repo days stay empty; **7.2 MB** still feasible.

Graph verify: “t0 primary mark + four-channel motion.”

### Must change (picture)

1. **First named repo = visible plant.** Rescue `tree_t ≥ 0.34` is not enough while `bloom_growth_gate=0.48` (dated 2+ repo worlds) and `main_length * tree_t` stays a stub. The t0 plant must show stem **and** canopy (leaves and/or blooms) at 400×400 without reading the bottom-left strip. Do not invent a fifth channel. Do not draw fake trees on `repos=[]`.

   Direction (implementer chooses the blend, not the leftover):
   - Lower or bypass the bloom/leaf gates for the **oldest / only** snapshot plant on the GIF path (`show_existing_world`), **or** raise rescued `tree_t` / canopy scale so `tree_t >= bloom_growth_gate` for that plant.
   - Keep explicit-maturity dated-growth hiding later trees (`test_dated_growth_prefers_older_*`).

2. **Stars → blooms, not caption.** Same repos/commits/followers, `timeline=False`, `star_velocity` pinned: raising stars must increase bloom **count and/or size** on the plant (tagged bloom nodes or `_draw_bloom` output). A 0→1 bloom flicker at GIF scale is not isolation.

3. **Commits → trunk, not caption.** Same isolation: raising commits must increase trunk **length and/or stroke** by more than ~0.5 px. Today’s 2.00 → 2.50 `stem_sw` band is caption-only at 400×400.

4. **Followers → glints, velocity pinned.** `n_fireflies` must follow `glint_count`, not `max(star_rate, glint_count)`. Do not let `firefly_elements(star_velocity)` light the garden when followers are 0. 0 followers → 0 garden glints. Tag the follower layer (`id="fireflies"` may stay; add `data-role="ink-glint"` or equivalent so stars-only glow is not counted).

5. **Repos-only still moves count.** Isolation that grows only the repo list (stars/commits/followers scalars fixed) must increase `class="repo-tree"` plants. Already mostly true; keep it after canopy work.

6. **Optional knob attrs.** If A1 will key off them, emit `data-bloom-scale` / `data-trunk-scale` / `data-glint-count` on the root. Attrs are a helper, not the pass condition.

### Byte budget (hard)

`living-inkgarden.gif` cap **7.2 MB**. Current file **6.56 MB**. Prefer:

- Keep `MAX_BLOOMS=80` / `MAX_LEAVES=600` / `MAX_ELEMENTS=25000` unless a *smaller* drawn set is required.
- Make t0 canopy **bigger and darker**, not 3× more leaves on every later frame.
- Do not add a second SMIL firefly swarm or night-star field in Dig1.

Local smoke **before** claiming Dig1 done (does not replace G1ig):

```bash
# Element / role sanity on the GIF kwargs path (A1 t0 + stars-high).
uv run python - <<'PY'
from scripts.art.ink_garden import generate
# reuse the same spine shape as tests.test_living_art_media._accretion_metrics
# pin star_velocity; timeline=False; count repo-tree / blooms / trunk stroke / fireflies
PY
```

Optional size probe: render a **short** 400×400 GIF (e.g. 8 frames) and scale `size * 120/8` as a crude upper bound. If that projection exceeds ~7.2 MB, reduce drawn primitives — do not plan to raise the cap. Never pass `--size` that would invite the 12 MB halve.

Dig1 does **not** commit `living-inkgarden.gif`. Do not run full-fleet `generate living-art` without `--only`.

### Palette

Dig1 may leave night-cosmic wired if Dig4 follows on the same lock. Do not block Dig1 on the look, but **do not add a second light/dark branch**. Canopy/trunk/glint ink must work on parchment *and* on the current night fill.

### Goldens (Dig1 lock, not Dig2)

If plant geometry changes, refresh `tests/fixtures/ink_garden/{minimal_full,rich_full,rich_mid}.svg` in this node. There is **no t0 golden** — do not add one here unless it helps Dig1 verify; Dig3 owns bake-off stills.

### Verify Dig1

Caption-blind (strip `#accretion-dialect` / `data-role="accretion-dialect"` before judging):

- [ ] t0 `1/2/20/1`, `timeline=False`: ≥1 `repo-tree` with visible stem **and** canopy; not soil + overlay.
- [ ] `repos=[]`: 0 `repo-tree`.
- [ ] Stars-only: bloom count/size **up**.
- [ ] Commits-only: trunk length/stroke **up** (GIF-visible, not 0.5 px).
- [ ] Followers-only, `star_velocity` pinned: tagged glints **up**; 0 followers → 0 glints even if stars are high.
- [ ] Repos-only: `repo-tree` count **up**.
- [ ] `uv run python -m pytest -q tests/test_ink_garden.py tests/test_ink_garden_timeline.py`
- [ ] Existing media plant-count / firefly tests still green (they are insufficient, not retired):
  `uv run python -m pytest -q tests/test_living_art_media.py -k 'inkgarden or ink_and_physarum or early_spine'`

Do not green Dig1 by writing Dig2 tests that still read `data-accretion-*` only.

---

## Dig2 — on-canvas t0 + isolation (`L-T-ACC`)

**Job:** make A1/A2 inkgarden assertions green by proving the **picture**, not the caption or root attrs.

**File:** `tests/test_art_shared_package.py` only. Do **not** move the contract into `test_ink_garden.py` or `test_living_art_media.py`. Those stay as generator/regression coverage. Goldens stay a Dig1 concern.

Graph verify: `pytest -k inkgarden`.

### Wait for A1/A2

A1/A2 land red/xfail on-canvas isolation in this same file (I08). Dig2 greens the **inkgarden** slice. If a shared D\*2 agent holds `L-T-ACC`, this playbook is that slice — still assert geometry here.

If A1/A2 are not present yet, Dig2 **adds** the inkgarden on-canvas tests (do not wait forever for names). Prefer sharing helpers with other dialects (overlay strip, `_accretion_metrics` clone with `star_velocity` pinned).

### Required asserts (overlay stripped)

Strip `#accretion-dialect` (and do not score `data-accretion-*` / overlay `data-mark-count` as pass). Generate with `timeline=False`, no `evolution_state`. Pin `star_velocity={recent_rate:0, peak_rate:0}`.

| Case | Fixture | Pass |
|---|---|---|
| **t0 plant** | `_accretion_metrics(repos=1, stars=2, commits=20, followers=1)` | ≥1 `class="repo-tree"` with **visible canopy** (leaves and/or blooms above a size/opacity floor), not a bare stem. Overlay ignored. |
| **stars-only** | stars 8 → 180 | bloom **count and/or size** strictly up |
| **commits-only** | commits 40 → 3200 (media isolation magnitudes) | trunk **length and/or stroke** strictly up |
| **followers-only** | followers 0 → 1 → 90 | tagged glints 0 then **up**; stars-only glow must not count |
| **repos-only** | repo list 1 → 4; stars/commits/followers scalars **fixed** | `repo-tree` **count** up |

Suggested selectors (Dig1 should have made these real):

- repo mark: `class="repo-tree"` plus canopy geometry (leaf/bloom nodes, or tagged `data-role="ink-canopy"`)
- stars: bloom group / `_draw_bloom` output
- commits: trunk `stroke-width` / path length
- followers: `#fireflies` or `data-role="ink-glint"` with velocity pinned

**Forbidden pass conditions:** root `data-accretion-*`, overlay tick counts, `n_fireflies` driven by `star_velocity`, plant-count-only for the t0 canopy case.

Keep existing media attr / plant-count tests; they are a weaker regression, not this bar.

### `pytest -k inkgarden` blast radius

That keyword also hits `tests/test_ink_garden.py`, goldens, `test_ink_garden_timeline.py`, parametrized media/render-state tests, and coverage helpers — files **outside** `L-T-ACC`. Dig2 must not edit those. If they fail after Dig1, fix in **Dig1** (`ink_garden.py` + fixtures), not here.

```bash
uv run python -m pytest -q tests/test_art_shared_package.py -k inkgarden
uv run python -m pytest -q tests/test_ink_garden.py tests/test_ink_garden_timeline.py
# graph verify (wider):
uv run python -m pytest -q -k inkgarden
```

---

## Dig3 — bake-off stills (no lock)

**After Dig1.** Do not wait for Dig4 to start. Do **not** copy the stale A1 stills.

**Files:**

- `goals/living-art-overhaul/bakeoff/inkgarden-t0.svg`
- `goals/living-art-overhaul/bakeoff/inkgarden-t1.svg`
- `goals/living-art-overhaul/bakeoff/inkgarden-t2.svg`

Create the `bakeoff/` directory if needed. **Do not** copy `goals/profile-readme-overhaul/inventory/frames/inkgarden-t*.svg` (pre-rescue A1; published GIFs were never rebuilt after 2026-08-14).

### Export

Same spine and kwargs as A1:

```text
timeline=False
seed stable (e.g. "inkgarden-dialect")
t0: repos=1, stars=2, commits=20, followers=1
t1: 2 / 24 / 400 / 18
t2: 4 / 120 / 2400 / 80
```

Stills must show **plants at t0**, not soil + overlay. If Dig4 has already landed, export on the parchment look. If Dig4 lands later, **re-export**.

### Verify Dig3

- [ ] Three files exist and are well-formed SVGs (`viewBox="0 0 800 800"`).
- [ ] `data-accretion-*` (repos/stars/commits/followers or scales) **increase** t0→t2.
- [ ] Caption-blind glance: t0 has a plant (stem + canopy); t1/t2 add plants; blooms/trunks/glints grow. Overlay may still be present; it must not be the only readable growth.
- [ ] Bytes are new Dig1 (or Dig1+Dig4) output — not the 2026-08-14 A1 files.
- [ ] No `living-inkgarden-dark` sibling implied by the stills.

Graph verify: “three stills + data-accretion attrs increase.”

---

## Dig4 — one parchment look (`L-IG`)

**Job:** `fact-one-look` — one designed **parchment** look that reads on GitHub light **and** dark. Not night-cosmic. No dual `-dark` pair unless bake-off later proves unreadable.

Graph verify: “no dual `-dark` pair unless unreadable.”

### Must

- Freeze the module docstring look: **light theme on aged paper.** Ink (`#6a5a4a` family) on parchment (`#f5f0e6` / `#f8f3ea`), not `oklch(0.12)` cosmic ground.
- Stop night commit hours from swapping the canvas to `"cosmic"` / near-black `bg_primary` while defs stay parchment. Hard-coded `#f5f0e6` vignette/paper lighting and `pal["bg_primary"]` must **agree**.
- Drop or restyle the night-only white star field + crescent moon (`:3647-3663`) so they are not a second piece. Circadian tint may stay as a *wash* on parchment; it must not become a second designed world.
- One look, not a CSS `@media` pair and not `living-inkgarden-dark.gif`.
- Judge at **400×400** raster (GIF worker size), not only the 800 SVG. Ink-on-paper typically survives both GitHub themes; night-cosmic + parchment foxing does not.

### Must not

- Add a second generator path or `-dark` filename.
- Move overlay origin (A3 / all-six only).
- Re-open bloom/trunk/glint isolation if Dig1 already made those marks track the knobs — only retouch color/contrast/ground.
- Raise the 7.2 MB cap to pay for extra night chrome.

### Verify Dig4

- [ ] Default and night-hour payloads share the same parchment ground family (no `#010510`-class fill as the hero paper).
- [ ] Vignette / `lighting-color` / `bg_primary` agree.
- [ ] `rg living-inkgarden-dark` is empty in production art paths.
- [ ] `uv run python -m pytest -q tests/test_ink_garden.py` (palette tests may change SVG bytes; keep determinism + goldens).
- [ ] Re-export Dig3 stills if they were captured before this look.

---

## Sequence and handoff

```text
A3 (no-op clock) ──► Dig1 (picture, 7.2 MB feasible)
                      ├─► Dig3 (stills after Dig1; re-export if Dig4 landed after)
                      ├─► Dig4 (parchment one-look, same L-IG — after Dig1)
                      └─► Dig2 (L-T-ACC queue: on-canvas tests)
W2M needs Dig2 + Dig3 + Dig4
G1ig (after W2M): --only inkgarden, 120 frames, 400×400, sibling MP4, ≤7.2 MB
K1ig scores the regenerated GIF, not A1 stills
```

G1ig command (later wave, not Dig*):

```bash
uv run python -m scripts.cli generate living-art \
  --profile wyattowalsh \
  --metrics-path /path/to/metrics.json \
  --history-path /path/to/history.json \
  --only inkgarden \
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
| `living-inkgarden.gif` + `.mp4` regen | `G1ig` |
| Jury score | `K1ig` |
| Roster shrink / exact-six tests | SHR after K2 |
| OpenSpec growth change | never this goal (S15) |

---

## Done when

- **Dig1:** caption-blind first-repo plant (stem + canopy); bloom/trunk/glints isolate with `star_velocity` pinned; 0-repo empty; 7.2 MB still plausible; `test_ink_garden.py` + goldens green.
- **Dig2:** `test_art_shared_package.py` asserts those geometries with overlay stripped — **not** `data-accretion-*` only; `pytest -k inkgarden` green without editing files outside `L-T-ACC`.
- **Dig3:** three **new** bake-off SVGs after Dig1; accretion attrs increase; glance shows plants at t0. Not the 2026-08-14 A1 files.
- **Dig4:** one parchment look; night-cosmic canvas collapsed; no `-dark` pair.

Overlay may remain. It must not be the picture.
