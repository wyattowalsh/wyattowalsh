# Wave DIAL — Genetic Landscape (`Dge1`–`Dge4`)

**Lane:** DGE. **Style key:** `genetic`. **Family:** fitness.
**This file is the execution playbook.** Inventory evidence: [`../inventory/I11.md`](../inventory/I11.md), I99 Dge1 brief, `scripts/art/genetic_landscape.py`.
**No production edits while authoring this playbook.** Implementers own `Dge1`–`Dge4` later.

Caption here = the on-SVG `#accretion-dialect` register (family word + four numeric glyphs). Not the README `<details>` legend (Wave RM). Distinct peaks, star height, generation marks, and colonies must read **with that register ignored**.

Until K2, shipped == candidates == six. Do not shrink CI, drop `genetic` from the roster, or raise `LIVING_ART_BYTE_BUDGETS`.

---

## Lock / graph

| ID | Lock | File(s) | Deps | Parallel | Verify (graph) |
|---|---|---|---|---|---|
| **Dge1** | `L-GE` | `scripts/art/genetic_landscape.py` | A3, I11 | DIAL (with other `D*1`) | t0 primary mark + four-channel motion |
| **Dge2** | `L-T-ACC` | `tests/test_art_shared_package.py` **only** | Dge1 | serialize vs other `D*2` | `pytest -k genetic` |
| **Dge3** | — | `goals/living-art-overhaul/bakeoff/genetic-t{0,1,2}.svg` | Dge1 | STILL | three stills + `data-accretion-*` increase |
| **Dge4** | `L-GE` | `scripts/art/genetic_landscape.py` | Dge1 | LOOK | no dual `-dark` pair unless unreadable |

`Dge1` and `Dge4` share `L-GE` → **sequential on `genetic_landscape.py`**. `Dge2` serializes on `L-T-ACC` with Dig2/Dto2/Dph2/Dle2/Dfe2 — prefer one greening agent after all `D*1` (`plan.md`; I99 correction 9). `Dge3` has no shared lock.

**`L-GE` vs `L-T-ACC`:** `L-GE` is the generator (`genetic_landscape.py`) for Dge1 + Dge4. `L-T-ACC` is the shared on-canvas test file (`tests/test_art_shared_package.py`) for Dge2. Do not write Dge2 asserts into `test_genetic_landscape.py` or `test_living_art_media.py`. Do not hold `L-GE` while greening Dge2.

**Do not lock / do not edit:** `scripts/art/shared/visual.py` `language_cluster` helper (I14 / I99). Genetic may **stop calling it for xy** from `genetic_landscape.py` (tint / `LANG_HUES` may stay). Do not rewrite the shared helper so ferrofluid/physarum/lenia keep their own call-site choices.

**Recommended lane order:** Dge1 → Dge4 (same file, one designed ground + raised peak/colony contrast) → Dge3 stills (I11: stills **after Dge1**; capture after Dge4 so bake-off ink is the designed look) → Dge2 when `L-T-ACC` is free. Graph allows Dge3 ∥ Dge4 after Dge1; if stills land before Dge4, **re-export** them after the look lands. W2M needs Dge2 + Dge3 + Dge4.

GIF regen is **not** this wave (`G1ge` after W2M). Dge1 must still be encodable under the **2.4 MB** `living-genetic.gif` cap so G1ge cannot pass only by raising budgets (repo-growth is out of scope). Published bytes **2_159_157** / **2_400_000** (~240 KB headroom, I03). Prefer **brighter/thicker peaks and colonies**, not more organisms or a denser grid.

---

## Target picture (without caption)

| Channel | Lease (keep names) | Intended on-canvas identity | Fail if you only prove |
|---|---|---|---|
| **repos** | hill count (no named knob) | one `genetic-peak-core` per named repo, **pairwise separated** | overlay `data-accretion-repos` / mere `data-peak-count` |
| **stars** | `peak_scale = 0.72 + 0.70 * star_scale` | **visible summit height** (core/glow radius + opacity) | dialect attr only / `CFG.peak_scale=8.0` confusion / overlay star tick |
| **commits** | `generation_gain = commit_scale` | a **tagged generation mark** (rings, stepped contour index, or trail generation) | `data-generations` / louder organism scribble |
| **followers** | `colony_gain = follower_scale` | drawn `gl-micro-colony` **ink**; **0 at 0 followers**; not saddle-fill terrain | `data-colony-count` / `data-colony-gain` / extra elevation that welds peaks |

Published GIF path (must be the isolation path too):

```text
generate(metrics, seed=…, maturity=snapshot.maturity, timeline=False)
```

`timelapse.py` forces `timeline=False`. `growth_mat = mat` on that path (not 1.0). Overlay origin for fitness is **(44, 44)** — **on the map** (`accretion.py:47`). Dge1 must **dodge the only hill**, not A3-move every dialect origin.

A1 spine (reuse `_accretion_metrics` in `tests/test_living_art_media.py:1144`):

| Frame | repos / stars / commits / followers | `peak_scale` | `generation_gain` | `colony_gain` |
|---|---|---|---|---|
| t0 | 1 / 2 / 20 / 1 | 0.844 | 0.339 | 0.116 |
| t1 | 2 / 24 / 400 / 18 | 1.083 | 0.667 | 0.491 |
| t2 | 4 / 120 / 2400 / 80 | 1.260 | 0.866 | 0.733 |

Pin `star_velocity={recent_rate:0, peak_rate:0}` in isolation fixtures (I08). `_accretion_metrics` currently leaks stars into `star_velocity`.

**Name collision (do not treat as one dial):** `CFG.peak_scale=8.0` is the per-repo `log1p(stars)` height multiplier (`genetic_landscape.py:65-80`, `:164`). Dialect `knobs["peak_scale"]` is the star lease (`accretion.py:184`). Dge1 consumes the **dialect** knob for visible height.

---

## Residue (why today’s GIF is caption-only)

Evidence: I11 + I99 Dge1 brief. Live code, not the 2026-08-14 A1 stills. t0 is **not empty** (unlike Ink Garden / Physarum leftovers): one `genetic-peak-core` already exists. The leftover is a **faint peak under a swarm**, **invisible colonies that weld terrain**, and **same-language hills that collapse** — ferrofluid-class distinctness, not an empty field.

### 1. t0 primary mark is the swarm, not the peak

A1 still [`goals/profile-readme-overhaul/inventory/frames/genetic-t0.svg`](../../profile-readme-overhaul/inventory/frames/genetic-t0.svg):

| Attr / mark | t0 |
|---|---|
| spine | 1 / 2 / 20 / 1 |
| `data-peak-count` | 1 |
| `genetic-peak-core` | 1 at (110.3, 357.7), r=4.8, **op=0.20** |
| `gl-micro-colony` | 1 at (106.4, 344.4), r=3.3, **op=0.04** |
| `data-population` | 37 |
| organism dots | **37 at op ≈ 0.29** (`pop_base=30`) |

A2 will pass if it only counts `genetic-peak-core >= 1`. A caption-blind 400×400 glance does **not**: the core is ~2.4 GIF px at 0.20 opacity; **37 dots at 0.29 out-shout it**. I99: **t0 primary mark = peak, not swarm.**

Static GIF floors (`timeline=False`): peak core `max(0.25, static_peak_signal)` → t0 ≈ 0.20; organism dots `max(0.18, static_population_signal)` → t0 ≈ 0.29 (`I11` fade table). Dots win.

### 2. Colonies are attrs, not a follower picture — and they weld peaks

```text
colony_count = min(6, 1 + int(vis<0.72) + int(vis<0.42 or density>0.7) + extra_colonies)
extra_colonies = 0 if colony_gain <= 0 else round(3.0 * colony_gain)
```

Always **≥1 colony per peak** even at `colony_gain == 0`. Drawn `gl-micro-colony` t0 opacity ≈ **0.04**. Colony Gaussians stamp elevation (`genetic_landscape.py:933-952`) that **fills saddles**. Followers also leak into `pop_count *= (1 + … + 0.55 * follower_scale)` (`336-344`). Isolation today asserts `data-colony-count` / `data-colony-gain` only (`test_leased_style_knobs_track_isolated_channels:1488-1496`) — not ink.

I99: colonies = followers (**0 at 0 followers**, **no** saddle-fill terrain).

### 3. Distinct peaks fail on the GIF contract

Plan: “keep distinct peaks.” Live GIF path:

1. **`strategy="language_cluster"`** (`791`). Same-language repos share a quadrant (`visual.py:178-208`); jitter 0.2 × 720 px ≈ ±144.
2. **`optimize_placement` is skipped** when `timelapse_contract` (`805-815`). `test_render_state_skips_set_reoptimization` **requires** that skip. Do **not** re-enable per-frame PSO — peaks would wander.
3. Colony terrain + affinity ridges (`965-1022`) + older-repo broader σ weld neighbors.
4. `crowding_scale` shrinks `sigma_grid` and spacing (`672-675`, `868-871`) but cannot un-pack a language quadrant.

`test_genetic_keeps_repo_peak_positions_stable_under_render_state` freezes `genetic-peak-core` xy — good for growth, bad if the frozen layout is packed. Distinctness must come from a **stable** visual plan (hash / reserved slots / min-distance in `repo_visual_order`), not a late overlap solver.

### 4. Stars height is weak; commits are scribble

Stars move (1) `log1p(stars) * CFG.peak_scale` (`160-164`), (2) dialect `peak_scale` × `peak_h` (`867`), (3) visibility radii (`1177-1178`). t0 core r=4.8 op=0.20. **No stars isolation test** today.

Commits: `+ 8 * generation_gain` into `generations` (`310-319`) **and** extra FBM octaves (`768-775`) **and** raw `contribution_signal` / `activity_signal`. Isolation asserts `data-generations` only. t0 already has 4 gens + 37 dots; more gens add **louder scribble**, not a readable generation mark.

### 5. Overlay sits on the only hill

Fitness strip is 248×28 at **(44, 44)** on paper `#1a1a2e` / ink `#9ec9d8`. Map pad is 40. High-contrast register can cover a NW peak. **One style** — Dge1 dodges the peak (or the strip for this generator only if a local offset exists). Do **not** A3-move every origin (I08 / I99).

### Tests that currently certify the leftover

| Test | What it proves | What it does not |
|---|---|---|
| `test_leased_style_knobs_track_isolated_channels` | followers → `data-colony-count` / `data-colony-gain`; commits → `data-generations` | stars height; `gl-micro-colony` ink; core radius/opacity; pairwise peak distance |
| `test_style_dialects_make_accretion_readable` | overlay ticks t0→t2 | picture |
| `test_genetic_landscape_static_frames_keep_all_snapshot_repo_peaks` | peak **count** | distinctness / 400×400 |
| `test_render_state_skips_set_reoptimization` | no `optimize_placement` on wrapped snapshots | a non-colliding plan |
| `test_genetic_keeps_repo_peak_positions_stable_under_render_state` | frozen xy | packed language clusters |
| `test_early_spine_dialects_keep_repo_accretion_readable` | ink/physarum/ferro | **not** genetic |
| `test_genetic_landscape_peak_profile_broadens_older_repos` | older σ wider | **fights** distinct peaks if Dge1 changes `_repo_peak_profile` |
| `test_art_shared_package.py` today | dialect family set includes `genetic` | **no** t0 / isolation yet (A1/A2 write the red bar here) |

Root SVG has `data-peak-count`, `data-population`, `data-generations`, `data-colony-gain`, `data-colony-count`. **No `data-peak-scale`.** Attrs are not Dge1 done.

---

## Shared constraints (all four nodes)

**Do**

- Consume today’s knobs: `peak_scale` / `generation_gain` / `colony_gain`. A3 is a documented no-op unless all six share a clock failure (I08/I99). Do not retune `_CHANNEL_CEILINGS`. Do not confuse `CFG.peak_scale=8.0` with the dialect knob.
- Keep `generate(metrics, *, seed, maturity) -> str`. Extra kwargs `timeline` / `loop_duration` / `reveal_fraction` stay.
- Keep one `genetic-peak-core` per named repo. `select_primary_repos` **ignores `limit`**; dense portfolios keep every peak (`test_genetic_landscape_dense_repo_snapshots_add_micro_colonies_without_omission`, 12 repos → 12 peaks).
- Leave `#accretion-dialect` in the SVG unless A3/RM ask to remove it. Dge1–Dge2 must **ignore** it, not delete it.
- Leave `test_render_state_skips_set_reoptimization` green: **no per-frame** `optimize_placement` / `optimize_palette_hues` on wrapped snapshots.
- Prefer extra `data-peak-scale` if Dge2 will key off it. Attrs are a helper, not the pass condition.
- Stay inside `CFG.max_elements=25_000` and grid **60**. Prefer **larger / more opaque** peaks and colonies over more organisms or higher `grid_resolution`.
- Keep `test_genetic_landscape.py` green from Dge1 (determinism, empty metrics SVG, snapshot extras, peak count, render-state skip). Flag `test_genetic_landscape_peak_profile_broadens_older_repos` if breadth changes — Dge2’s `pytest -k genetic` will hit it.

**Do not**

- Edit `scripts/art/shared/accretion.py`, `artifacts.py` budgets, `timelapse.py`, README, workflow, OpenSpec `prevent-living-art-repo-growth`, or `main`.
- Rewrite `scripts/art/shared/visual.py` `language_cluster` (I14). Change the **call site** in `genetic_landscape.py` if placement must leave language quadrants.
- Raise `living-genetic.gif` above **2_400_000** bytes (`artifacts.py:32`).
- Trigger `_assemble_gif` **12 MB halve** (`timelapse.py:295-324`) — that breaks 400×400.
- Use `generate animated` / `animate.py` for `living-*` (writes `{style}-growth.gif` from interpolated maturity).
- Reuse `goals/profile-readme-overhaul/inventory/frames/genetic-t{0,1,2}.svg` as bake-off evidence (faint peak + 37-dot swarm).
- Treat overlay ticks, `data-colony-*`, `data-generations`, or `genetic-peak-core >= 1` presence as Dge1/Dge2 done.
- Ship `living-genetic-dark.gif` (unbudgeted; `_TIMELAPSE_RE` would reject it).
- Hold `L-T-ACC` from Dge1. Generator edits stay on `L-GE`.

---

## Dge1 — redesign on-canvas dialect (`L-GE`)

**Job:** distinct **stable** peaks; height = **visible stars**; generations ≠ scribble; colonies = **followers** (0 at 0 followers, no saddle-fill); t0 primary mark = **peak, not swarm**; overlay does not cover the only hill; **2.4 MB** still feasible.

Graph verify: “t0 primary mark + four-channel motion.”
Graph title: “keep distinct peaks; colonies=followers.”

### Must change (picture)

1. **Peaks = repos, and stay distinct.** One core per repo is already true. Separate them under `timelapse_contract` **without** calling `optimize_placement`. Prefer a stable non-colliding plan (hash / reserved slots / min-distance in `repo_visual_order`) instead of language-quadrant packing. Same-language fixtures must not collapse into one hill. Do not let colony Gaussians or ridges weld neighbors.

2. **Height = stars, visible.** Raise t0 core/glow opacity well above the organism-dot floor. Isolated `stars` (same per-repo ratio) must move **drawn** core/glow radius and visible ink — not only `peak_h` inside a 60×60 grid that downsamples to 400×400. Optional `data-peak-scale`; the picture must move without it. Do not treat `CFG.peak_scale=8.0` as the dialect lease.

3. **Generations = commits, not louder scribble.** `+8 * generation_gain` already moves `data-generations`. Make that visible: generation rings, stepped contour index, or tagged trail generation — **not** more organism dots. Cut or pin the dual path where raw `contribution_signal` / `activity_signal` also inflate gens so A1 isolation stays monotonic when only commits move.

4. **Colonies = followers.** Drawn `gl-micro-colony` count/opacity/spread rise with `colony_gain`. **0 followers → 0 colonies** (or a single origin tick that is not a satellite bump). Remove the unconditional `1 + visibility bonuses` floor. **Do not add colony elevation** that fills saddles; colonies are marks, not terrain. Stop leaking followers into `pop_count` (`0.55 * follower_scale`).

5. **t0 primary mark is the first peak, not the swarm.** `pop_base=30` makes 37 dots at the first-repo frame. Floor population (or hide dots/trails) until commits/generations justify organisms. Peak core **out-contrasts** dots (today 0.20 vs 0.29). A count of `genetic-peak-core >= 1` already passes — that is not Dge1.

6. **Pre-repo days** (0 peaks) can stay field + overlay. A2 uses the 1-repo spine. Empty-metrics tests may stay SVG-only.

7. **Overlay origin (44, 44) must not cover the only hill.** If a peak lands NW, move **that peak** (or a genetic-local dodge), not every dialect origin. Overlay may stay; Dge1 must not need it for readable growth.

8. **Stay inside 2.4 MB** and `max_elements`. Prefer brighter/thicker peaks and colonies. Do not raise `grid_resolution` or `pop_base` to “prove” generations.

9. Leave `test_render_state_skips_set_reoptimization` green.

### Byte budget (hard)

`living-genetic.gif` cap **2.4 MB**. Published **2.16 MB** (~240 KB headroom). Organism count is the usual blow-up. Prefer:

- Keep `grid_resolution = 60`.
- Cut t0 `pop_base=30` swarm rather than adding rings **and** keeping 37 dots.
- Do not raise `contour_levels` / `pop_scale` to prove commits.

Local smoke **before** claiming Dge1 done (does not replace G1ge):

```bash
# Role / geometry sanity on the GIF kwargs path (A1 t0 + stars-high + followers-0).
uv run python - <<'PY'
from scripts.art.genetic_landscape import generate
# reuse the same spine shape as tests.test_living_art_media._accretion_metrics
# pin star_velocity; timeline=False
# assert peak core brighter than organism dots; 0 followers → 0 gl-micro-colony
# pairwise core distance on a same-language multi-repo fixture
PY
```

Optional size probe: render a **short** 400×400 GIF (e.g. 8 frames) and scale `size * 120/8` as a crude upper bound. If that projection exceeds ~2.4 MB, reduce drawn primitives — do not plan to raise the cap. Never pass `--size` that would invite the 12 MB halve.

Dge1 does **not** commit `living-genetic.gif`. Do not run full-fleet `generate living-art` without `--only`.

### Palette

Dge1 may leave world-state day/night `bg_primary` wired if Dge4 follows immediately. Do not add a second light/dark **media** branch. Peak/colony opacity must work on the current day `#edf7f8` *and* after Dge4’s single designed ground.

### Verify Dge1

Caption-blind (strip `#accretion-dialect` / `data-role="accretion-dialect"` before judging):

- [ ] t0 `1/2/20/1`, `timeline=False`: first **peak core** is the picture (opacity and radius ≫ organism dots). Not a 37-dot swarm.
- [ ] `repos=[]`: 0 `genetic-peak-core` (field + overlay OK).
- [ ] Repos-only (same-language names OK): `genetic-peak-core` **count** up **and** pairwise core distance above a floor (not one welded hill).
- [ ] Stars-only (same per-repo star **ratio**): drawn core/glow **radius and visible ink** up — not only `peak_h` / overlay tick.
- [ ] Commits-only: tagged generation mark / contour index **up**, organism-dot count **not** the proof; dual clocks do not break monotonic isolation.
- [ ] Followers-only: `gl-micro-colony` **ink** up; **0 followers → 0 colonies**; peak gaps do not collapse from colony terrain.
- [ ] Overlay at (44, 44) does not cover the sole t0 peak.
- [ ] `uv run python -m pytest -q tests/test_genetic_landscape.py tests/test_living_art_render_state.py -k genetic`
- [ ] Existing media attr tests still green (they are insufficient, not retired):
  `uv run python -m pytest -q tests/test_living_art_media.py -k 'genetic or leased_style_knobs'`

Do not green Dge1 by writing Dge2 tests that still read `data-colony-*` / `data-generations` only.

---

## Dge2 — on-canvas t0 + isolation (`L-T-ACC`)

**Job:** make A1/A2 genetic assertions green by proving the **picture**, not the caption or colony/generation attrs.

**File:** `tests/test_art_shared_package.py` only. Do **not** move the contract into `test_genetic_landscape.py` or `test_living_art_media.py`. Those stay as generator/regression coverage.

Graph verify: `pytest -k genetic`.

### Wait for A1/A2

A1/A2 land red/xfail on-canvas isolation in this same file (I08). Dge2 greens the **genetic** slice. If a shared D\*2 agent holds `L-T-ACC`, this playbook is that slice — still assert geometry here.

If A1/A2 are not present yet, Dge2 **adds** the genetic on-canvas tests (do not wait forever for names). Prefer sharing helpers with other dialects (overlay strip, `_accretion_metrics` clone with `star_velocity` pinned).

I08 expected genetic marks:

| | t0 | stars | commits | followers |
|---|---|---|---|---|
| genetic | `genetic-peak-core` **brighter than** organism dots | core/glow radius | generation mark ≠ scribble | `gl-micro-colony` ink, **0 at 0 followers** |

### Required asserts (overlay stripped)

Strip `#accretion-dialect` (and do not score `data-colony-count` / `data-colony-gain` / `data-generations` / overlay `data-mark-count` / `data-accretion-star-scale` as pass). Generate with `timeline=False`. Pin `star_velocity={recent_rate:0, peak_rate:0}`.

| Case | Fixture | Pass |
|---|---|---|
| **t0 peak not swarm** | `_accretion_metrics(repos=1, stars=2, commits=20, followers=1)` | ≥1 `genetic-peak-core` **brighter/larger than** organism dots (opacity and radius). Overlay ignored. |
| **stars-only** | stars 8 → 180; per-repo stars stay in the **same ratio** | max core/glow **radius and visible ink** up (**missing today**) |
| **commits-only** | commits 40 → 3200; followers fixed | tagged generation mark / trail generation / contour index up — **not** only `data-generations`, **not** organism-dot count |
| **followers-only** | followers 0 → 1 → 90 | `gl-micro-colony` count or opacity **0 then up**; never extra terrain that collapses peak gaps |
| **repos-only** | repo list 1 → 4; **same-language** names; stars/commits/followers scalars **fixed** | `genetic-peak-core` **count** up **and** pairwise core distance above a floor |

Suggested selectors (Dge1 should have made these real):

- repo mark: `class="genetic-peak-core"` / glow sibling; fill opacity and `r=` well above t0 leftover (0.20 / 4.8)
- stars: max core/glow `r=` (and opacity) across peaks
- commits: `data-role` generation ring / contour index / tagged trail — **not** `data-population`
- followers: `data-role="gl-micro-colony"` count/opacity; 0 nodes (or origin-only) when followers=0

**Forbidden pass conditions:** overlay ticks, `data-colony-count`, `data-colony-gain`, `data-generations`, `data-peak-count` without a distance floor, `genetic-peak-core >= 1` without beating the swarm.

Keep existing media attr tests; they are a weaker regression, not this bar.

### `pytest -k genetic` blast radius

That keyword also hits `tests/test_genetic_landscape.py`, parametrized media/render-state tests, and coverage helpers — files **outside** `L-T-ACC`. Dge2 must not edit those. If they fail after Dge1, fix in **Dge1** (`genetic_landscape.py`), not here.

If Dge1 changes `_repo_peak_profile` breadth, `test_genetic_landscape_peak_profile_broadens_older_repos` (`212-239`) may go red in the same `pytest -k genetic` pass — flag for Dge1, do not patch the generator from this lock.

```bash
uv run python -m pytest -q tests/test_art_shared_package.py -k genetic
uv run python -m pytest -q tests/test_genetic_landscape.py
# graph verify (wider):
uv run python -m pytest -q -k genetic
```

---

## Dge3 — bake-off stills (no lock)

**After Dge1** (graph deps + I11). Prefer capturing **after Dge4** so the designed ground + contrast is the bake-off look.

**Files:**

- `goals/living-art-overhaul/bakeoff/genetic-t0.svg`
- `goals/living-art-overhaul/bakeoff/genetic-t1.svg`
- `goals/living-art-overhaul/bakeoff/genetic-t2.svg`

Create the `bakeoff/` directory if needed. **Do not** copy `goals/profile-readme-overhaul/inventory/frames/genetic-t*.svg` (faint peak + 37-dot swarm; published GIFs were never rebuilt after 2026-08-14).

### Export

Same spine and kwargs as A1. Prefer `render_state` / `repo_visual_order` so peak xy matches the GIF contract.

```text
timeline=False
seed stable (e.g. "genetic-dialect")
t0: repos=1, stars=2, commits=20, followers=1
t1: 2 / 24 / 400 / 18
t2: 4 / 120 / 2400 / 80
```

### Verify Dge3

- [ ] Three files exist and are well-formed SVGs (`viewBox="0 0 800 800"`).
- [ ] `data-accretion-*` (repos/stars/commits/followers or scales) **increase** t0→t2.
- [ ] Caption-blind glance: **t0 one distinct peak** (not a swarm); t1–t2 more **separated** peaks, taller with stars, more generations, more colonies. Overlay may still be present; it must not be the only readable growth.
- [ ] Bytes are new Dge1 (or Dge1+Dge4) output — not the 2026-08-14 A1 files.
- [ ] No `living-genetic-dark` sibling implied by the stills.

Graph verify: “three stills + data-accretion attrs increase.”

---

## Dge4 — one look (`L-GE`)

**Job:** `fact-one-look` — one designed look that reads on GitHub light **and** dark. No dual `-dark` pair unless bake-off later proves unreadable.

Graph verify: “no dual `-dark` pair unless unreadable.”

Background **follows world-state** today: day ≈ `#edf7f8` (A1 stills), night `oklch(0.12, 0.03, 260)` (`palette.py:147-154`). Peaks are `oklch(0.65, 0.14, LANG_HUES[lang])` (`878`) — mid L, language-tinted. Fitness overlay is dark paper + ice ink (`#1a1a2e` / `#9ec9d8`) even on a light field.

Failure mode is **tiny / faint t0 marks** (and hour-driven light/dark field flips), not a missing `-dark` GIF. I11: pick **one** field (recommend a single designed ground, not day/night flip) and raise peak/colony contrast so 400×400 reads on white GitHub light **and** dark README chrome.

Contour stroke 0.4 at op 0.09 will vanish when downscaled; index contours (every 4th, sw=1.0) are the ones that can survive if darkened/brightened against the chosen ground.

### Must

- Freeze **one** designed ground. Do **not** add `living-genetic-dark.gif`.
- Make **peak cores, glows, and colonies** contrast against that ground on GitHub light (current t0 core op 0.20 / colony 0.04 fail at 400×400).
- Judge at **400×400** raster (GIF worker size), not only the 800 SVG.
- One look, not a CSS `@media` pair and not a night generator path.

### Must not

- Add a second generator path or `-dark` filename.
- Move overlay origin via A3 (all-six only). Genetic-local dodge of (44, 44) vs the first peak is a Dge1 leftover, not a Dge4 palette job — finish it in Dge1 if still open.
- Re-open distinct-peaks / swarm / colony-terrain if Dge1 already made the picture — only retouch color/contrast/ink weight.
- Treat “day paper on dark GitHub is fine” as Dge4 done while light-theme peaks still vanish under contours.

### Verify Dge4

- [ ] No second palette branch as a shipped media pair; one hero fill.
- [ ] t0 peak (and 1-follower colony, if drawn) remain readable on a light GitHub page at 400×400.
- [ ] `rg living-genetic-dark` is empty in production art paths.
- [ ] `uv run python -m pytest -q tests/test_genetic_landscape.py tests/test_living_art_dark_mode_contrast.py -k genetic`
- [ ] Re-export Dge3 stills if they were captured before this look.

---

## Sequence and handoff

```text
A3 (no-op clock) ──► Dge1 (distinct peaks, height=stars, colonies=followers, t0=peak not swarm, 2.4 MB feasible)
                      ├─► Dge4 (one look, same L-GE)
                      │     └─► Dge3 (stills after Dge1; re-export if Dge4 landed after)
                      └─► Dge2 (L-T-ACC queue: on-canvas tests)
W2M needs Dge2 + Dge3 + Dge4
G1ge (after W2M): --only genetic, 120 frames, 400×400, sibling MP4, ≤2.4 MB
K1ge scores the regenerated GIF, not A1 stills
```

G1ge command (later wave, not Dge*):

```bash
uv run python -m scripts.cli generate living-art \
  --profile wyattowalsh \
  --metrics-path /path/to/metrics.json \
  --history-path /path/to/history.json \
  --only genetic \
  --max-frames 120 \
  --size 400 \
  --workers 4 \
  --output-dir .github/assets/img
```

---

## Out of this lane

| Concern | Owner |
|---|---|
| README stack / `<details>` mapping copy (suggested legend: *peaks = repos; height = stars; generations = commits; colonies = followers*) | RM `M1`–`M5` |
| Shared accretion ceilings / overlay geometry for **all six** | A3 / `L-ACC` |
| `living-genetic.gif` + `.mp4` regen | `G1ge` |
| Jury score | `K1ge` |
| `animate.py` legacy `genetic-growth` name | R3 / `L-TL` (not published `living-*`) |
| Roster shrink / exact-six tests | SHR after K2 |
| OpenSpec growth change | never this goal (S15) |
| `visual.py` `language_cluster` helper rewrite | never (I14) |

---

## Done when

- **Dge1:** caption-blind distinct stable peaks (no per-frame PSO); star height visible; generations ≠ scribble; colonies = followers (0 at 0 followers, no saddle-fill); t0 peak out-contrasts the swarm; overlay does not cover the only hill; 2.4 MB still plausible; `test_genetic_landscape.py` + render-state skip green.
- **Dge2:** `test_art_shared_package.py` asserts those geometries with overlay stripped — **not** `data-colony-*` / `data-generations` only; `pytest -k genetic` green without editing files outside `L-T-ACC`.
- **Dge3:** three new bake-off SVGs **after Dge1**; accretion attrs increase; glance shows t0 one distinct peak, not a swarm.
- **Dge4:** one designed ground; peaks/colonies contrast on GitHub light; **no** `-dark` pair.

Overlay may remain. It must not be the picture.
