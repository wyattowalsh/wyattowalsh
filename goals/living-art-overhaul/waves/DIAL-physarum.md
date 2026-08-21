# Wave DIAL — Physarum (`Dph1`–`Dph4`)

**Lane:** DPH. **Style key:** `physarum`. **Family:** mycelial.
**This file is the execution playbook.** Inventory evidence: [`../inventory/I12.md`](../inventory/I12.md), I99 Dph1 brief, `scripts/art/physarum.py`.
**No production edits while authoring this playbook.** Implementers own `Dph1`–`Dph4` later.

Caption here = the on-SVG `#accretion-dialect` register (family word + four numeric glyphs). Not the README `<details>` legend (Wave RM). Vein mass and the first-repo network must read **with that register ignored**.

Until K2, shipped == candidates == six. Do not shrink CI, drop `physarum` from the roster, or raise `LIVING_ART_BYTE_BUDGETS`.

**A2 primary mark is tagged veins, not the spore.** A lone `physarum-spore` (or the existing node floor) does **not** satisfy t0.

---

## Lock / graph

| ID | Lock | File(s) | Deps | Parallel | Verify (graph) |
|---|---|---|---|---|---|
| **Dph1** | `L-PH` | `scripts/art/physarum.py` | A3, I12 | DIAL (with other `D*1`) | t0 primary mark + four-channel motion |
| **Dph2** | `L-T-ACC` | `tests/test_art_shared_package.py` **only** | Dph1 | serialize vs other `D*2` | `pytest -k physarum` |
| **Dph3** | — | `goals/living-art-overhaul/bakeoff/physarum-t{0,1,2}.svg` | Dph1 | STILL | three stills + `data-accretion-*` increase |
| **Dph4** | `L-PH` | `scripts/art/physarum.py` | Dph1 | LOOK | no dual `-dark` pair unless unreadable |

`Dph1` and `Dph4` share `L-PH` → **sequential on `physarum.py`**. `Dph2` serializes on `L-T-ACC` with Dig2/Dto2/Dge2/Dle2/Dfe2 — prefer one greening agent after all `D*1` (`plan.md`; I99 correction 9). `Dph3` has no shared lock.

**Recommended lane order:** Dph1 → Dph4 (same file, raise t0 vein/node ink on the redesigned network) → Dph3 stills (so bake-off is not spore+orphan-node) → Dph2 when `L-T-ACC` is free. Graph allows Dph3 ∥ Dph4 after Dph1; if stills land before Dph4, **re-export** them after the look lands. W2M needs Dph2 + Dph3 + Dph4.

GIF regen is **not** this wave (`G1ph` after W2M). Dph1 must still be encodable under the **2.4 MB** `living-physarum.gif` cap so G1ph cannot pass only by raising budgets (repo-growth is out of scope). Headroom today ~526 KB (I03); do not spend it on more contours.

---

## Target picture (without caption)

| Channel | Lease (keep names) | Intended on-canvas identity | Fail if you only prove |
|---|---|---|---|
| **repos** | count of food terminals (no named knob) | one `physarum-node-core` **plus connecting tagged veins** per named repo | overlay `data-accretion-repos` / core count without a graph |
| **stars** | `nutrient_scale = 0.70 + 0.80 * star_scale` | node **radius and visible ink** | `data-nutrient-scale` / `r=` that is ~2.9 px on the GIF |
| **commits** | `trail_scale = 0.72 + 0.55 * commit_scale` | tagged vein **width / density / glow** | overlay mycelial `<path>` stroke / raw `deposit_amount` |
| **followers** | `vein_gain = follower_scale` | extra hyphae / offshoots / spread — **monotone up** | `+36 * vein_gain` agents / overlay rays |

Published GIF path (must be the isolation path too):

```text
generate(metrics, seed=…, maturity=snapshot.maturity, timeline=False)
```

`timelapse.py:90-96` forces `timeline=False`. `growth_mat = mat` on that path (not 1.0). Overlay origin for physarum is **(40, 742)** bottom-left — leave it unless A3 moves every dialect.

A1 spine (reuse `_accretion_metrics` in `tests/test_living_art_media.py:1144`):

| Frame | repos / stars / commits / followers | `nutrient_scale` | `trail_scale` | `vein_gain` | `compute_maturity` (approx) |
|---|---|---|---|---|---|
| t0 | 1 / 2 / 20 / 1 | 0.841 | 0.906 | 0.116 | **≈ 0.012** |
| t1 | 2 / 24 / 400 / 18 | 1.114 | 1.087 | 0.491 | ≈ 0.25 |
| t2 | 4 / 120 / 2400 / 80 | 1.317 | 1.196 | 0.733 | higher |

Pin `star_velocity={recent_rate:0, peak_rate:0}` in isolation fixtures (I08). `_accretion_metrics` currently leaks stars into `star_velocity`.

---

## Residue (why today’s GIF is caption-only)

Evidence: I12 + I99 Dph1 brief. Live code, not the 2026-08-14 A1 stills.

### 1. `vein_fade` is zero while `growth_mat ≤ 0.05`

```1434:1436:scripts/art/physarum.py
    # ── Vein contours ─────────────────────────────────────────────
    vein_fade = _fade(0.05, 0.50)
    if vein_fade > 0 and t_max > 0:
```

`_fade(start, full)` is `(growth_mat - start) / (full - start)` clamped to `[0, 1]` (`physarum.py:864-866`). On the GIF path `growth_mat = mat`. A1-spine t0 `compute_maturity ≈ 0.0119` → **`vein_fade = 0`**. The Jones 2010 sim still runs; marching-squares contours are **never emitted**. First-repo t0 is therefore **not a transport network**.

Published kwargs (`timeline=False`, `maturity≈0.01–0.02`) match this leftover: spore + one floored node, **0 veins**.

### 2. Node floor is not the leftover

```1494:1497:scripts/art/physarum.py
    node_fade = _fade(0.10, 0.40)
    # Snapshot / GIF frames use timeline=False; existing repos stay visible.
    if not timeline_enabled:
        node_fade = max(node_fade, 0.64)
```

GIF t0 already draws `physarum-node-halo` / `-shell` / `-core` whenever a repo exists. `test_early_spine_dialects_keep_repo_accretion_readable` (`tests/test_living_art_media.py:1577-1607`) certifies **`phys_nodes[0] >= 1`**, not veins. Do **not** treat that floor as Dph1 done.

A1 still [`goals/profile-readme-overhaul/inventory/frames/physarum-t0.svg`](../../profile-readme-overhaul/inventory/frames/physarum-t0.svg) is **extra-stale** (spore-only, pre node-floor). Do not reuse it.

### 3. Vein `<path>` elements have no `data-role`

Contour emit (`physarum.py:1485-1490`) is an untagged `<path>`. Mycelial overlay always adds **one** commit Bézier `<path>` (`accretion.py:369-375`). Any count of `svg.count("<path")` includes that glyph. Dph2/A2 cannot score the network until veins are tagged `data-role="physarum-vein"` (or equivalent).

### 4. A2 mark is veins — spore is not a pass

Spore (`data-role="physarum-spore"`, `physarum.py:1410-1428`) uses `_fade(0.0, 0.05)`. Hidden at exact `maturity=0`. At t0 fade ≈ 0.24, r ≈ 2.7–3.2, opacity ≈ 0.19–0.32. I99 / I08: A2 t0 primary mark = **network-with-veins**, not overlay glyphs, **not spore**.

Empty pre-repo days (0 food sources) may stay spore-or-substrate. A2 uses **1 repo**.

### 5. Followers are non-monotonic on path count

`vein_gain` only adds agents (`n_agents + int(round(36 * vein_gain))`, `physarum.py:1251-1254`). I12 isolation with veins on: followers 1 → 90 **dropped** path count 35 → 22. Extra agents smear the trail; marching squares then yields **fewer** iso-chains. Overlay radial lines (`accretion.py:376-384`) still tick. That is caption growth, not a learnable hyphae channel.

### 6. Commits barely move visible trail after the gate

`trail_scale` multiplies `deposit_amount` (`physarum.py:1328-1330`). Invisible while `vein_fade=0`. Isolation with veins on: paths 35 → 36 — not a readable commit encoding. Dual raw `total_commits` also drives `commit_signal` → agents and `sim_steps` (`1103`, `1239`, `1275-1285`). Isolation must pin those raw leaks or Dph1 must make **tagged** stroke/glow the picture.

### 7. SMIL staging inversion (do not ignore if you touch `timeline=True`)

| Call | spore | node-cores | vein-like paths (total `<path>` − overlay) |
|---|---|---|---|
| `timeline=False`, no maturity (A1 still recipe) | 1 | **1** | **0** |
| `timeline=False, maturity=0.02` (GIF kwargs) | 1 | 1 | **0** |
| `timeline=False, maturity=0.0` | **0** | 1 | 0 |
| `timeline=True, maturity=0.02` | 1 | **0** | 0 |
| `timeline=True, maturity=0.08` | 1 | **0** | **~44** |
| `timeline=True`, no maturity | 1 | 1 | many (`growth_mat=1.0`) |

`test_physarum_explicit_maturity_with_timeline_preserves_growth_staging` (`tests/test_physarum.py:334-357`) asserts late node-cores **>** early at `maturity=0.08` vs `0.85`. That **encodes** the inversion. Ungating SMIL nodes with veins will go red there — keep `test_physarum.py` green from Dph1 (`L-PH` is the generator only).

### Tests that currently certify the leftover

| Test | What it proves | What it does not |
|---|---|---|
| `test_early_spine_dialects_keep_repo_accretion_readable` | node-core ≥ 1 at GIF t0 | **veins** |
| `test_style_dialects_make_accretion_readable` | overlay ticks t0→t2 | picture |
| `test_ink_and_physarum_knobs_track_stars_and_followers` | stars → max core `r` | followers on physarum; commits; overlay-stripped t0 |
| `test_leased_style_knobs_track_isolated_channels` | — | **physarum not included** |
| `test_physarum_explicit_maturity_with_timeline_preserves_growth_staging` | SMIL late cores > early | GIF network |
| `test_generators_prefer_render_state` (physarum) | `physarum-node-core` count > 0 | connectivity |
| `test_art_shared_package.py` today | dialect family set includes `physarum` | **no** t0 / isolation yet (A1/A2 write the red bar here) |

A test that only counts `physarum-spore` or `physarum-node-core` **passes current GIF t0**. A test that tagged veins exist at first repo **fails**.

---

## Shared constraints (all four nodes)

**Do**

- Consume today’s knobs: `nutrient_scale` / `trail_scale` / `vein_gain`. A3 is a documented no-op unless all six share a clock failure (I08/I99). Do not retune `_CHANNEL_CEILINGS`.
- Keep `generate(metrics, *, seed, maturity) -> str`. Extra kwargs `timeline` / `loop_duration` / `reveal_fraction` stay.
- Keep one food node per named repo (`select_primary_repos` already ignores `limit`; full set is intended — `test_physarum_prefers_full_repo_set_over_truncated_top_repos`).
- Keep `language_cluster` in `repo_to_canvas_position`. Do **not** rewrite `scripts/art/shared/visual.py` (I14 lock: Dfe1 stops *calling* it; helper stays).
- Leave `#accretion-dialect` in the SVG unless A3/RM ask to remove it. Dph1–Dph2 must **ignore** it, not delete it.
- Stay inside `CFG.max_elements` (25_000) and `grid_resolution=80` unless a smaller *drawn* set is required for the byte cap.
- Keep `test_physarum.py` green from Dph1 (determinism, snapshot signal modulation, SMIL staging count, full-repo cores, empty metrics).

**Do not**

- Edit `scripts/art/shared/accretion.py`, `artifacts.py` budgets, `timelapse.py`, README, workflow, OpenSpec `prevent-living-art-repo-growth`, or `main`.
- Raise `living-physarum.gif` above **2_400_000** bytes (`artifacts.py:35`).
- Trigger `_assemble_gif` **12 MB halve** (`timelapse.py:295-324`) — that breaks 400×400.
- Use `generate animated` / `animate.py` for `living-*` (writes `{style}-growth.gif` from interpolated maturity; `physarum-growth` is not the published stem).
- Reuse `goals/profile-readme-overhaul/inventory/frames/physarum-t{0,1,2}.svg` as bake-off evidence.
- Treat overlay ticks, untagged `<path>` counts, `physarum-spore`, or the 0.64 node floor as Dph1/Dph2 done.
- Ship `living-physarum-dark.gif` (unbudgeted; `_TIMELAPSE_RE` would reject it).
- Treat spore as the A2 mark.

---

## Dph1 — redesign on-canvas dialect (`L-PH`)

**Job:** veins from the **first repo** even when `growth_mat < 0.05`; tag those veins; commits and followers move **tagged** vein mass **up**; A2 mark = network, not spore. **2.4 MB** still feasible.

Graph verify: “t0 primary mark + four-channel motion.”

### Must change (picture)

1. **Ungate veins when food exists.** If `food_canvas` is non-empty, draw veins (and keep the repo node) even if `growth_mat < 0.05`. Do not wait for `_fade(0.05, 0.50)`. Spore may remain as origin. Empty / 0-repo payloads may stay spore-or-substrate.

   Direction (implementer chooses the blend, not the leftover):
   - Floor `vein_fade` on the GIF path (`not timeline_enabled`) whenever `len(food_canvas) > 0`, **or** start the vein ramp at `0.0` when food exists.
   - A guaranteed seed trail from spore → first food (or a minimum contour) is allowed if marching squares is empty at t0 — the picture must still be **hyphae**, not a brighter spore.

2. **Do not treat the node floor as done.** GIF t0 already has `physarum-node-core`. The leftover is the **missing network**. Isolation at `maturity=0.04` today: cores 2→5, still **no connecting veins**.

3. **Tag veins.** Every organism contour `<path>` gets `data-role="physarum-vein"` (ghost traces may use `physarum-vein-ghost` or the same role plus a class). Overlay commit `<path>` stays untagged. Dph2/A2 count `data-role="physarum-vein"` only.

4. **Commits must move visible trail.** `trail_scale` → deposit is invisible while gated and barely moves path count after. Width, density, and/or glow of **tagged** veins must rise with commits, isolated from overlay stroke. Prefer thicker/brighter ink over more contour levels.

5. **Followers must move hyphae monotonically.** Do **not** rely on `+36 * vein_gain` agents — that **reduced** path count (35→22). Prefer extra offshoot veins, satellites, or tagged vein opacity/count/spread that **increases** with `vein_gain`. Isolation followers 1 → 90 must never drop tagged vein mass.

6. **Stars: radius *and* ink.** Keep `nutrient_scale` on `conc` / core `r`. Raise t0 opacity/size so a 400×400 GIF shows the node (today r≈5.7 at 800 → ≈2.9 px). Stroke or fill must also move, or the radius change stays wasted.

7. **Repos grow the graph.** Isolation that grows only the repo list (stars/commits/followers scalars fixed) must increase cores **and** connecting tagged veins — not a pile of unlinked dots.

8. **SMIL staging.** If Dph1 touches `timeline=True`: `maturity=0.08` can draw veins with **zero** cores. Either ungate nodes whenever veins are drawn, **or** keep GIF-only ungate and leave `test_physarum_explicit_maturity_with_timeline_preserves_growth_staging` green. Do not edit that test from Dph1 (`L-PH` is `physarum.py` only).

9. **Exact `maturity=0` hides the spore.** First-day snapshots can be ~0.01; do not rely on the spore as the A2 primary mark.

### Byte budget (hard)

`living-physarum.gif` cap **2.4 MB**. Grid 80 is enough if early veins are **thicker/brighter, not more numerous**. Prefer:

- Keep `grid_resolution=80` and `contour_levels` in today’s band (4–10).
- Do not raise `max_elements` or flood extra iso-levels to fake density.
- Count `max_elements` before shipping denser contours.

Local smoke **before** claiming Dph1 done (does not replace G1ph):

```bash
uv run python - <<'PY'
from scripts.art.physarum import generate
# A1 t0 + commits-high + followers-high on GIF kwargs (timeline=False).
# Strip #accretion-dialect, then count data-role="physarum-vein" and node-cores.
PY
```

Optional size probe: render a **short** 400×400 GIF (e.g. 8 frames) and scale `size * 120/8` as a crude upper bound. If that projection exceeds ~2.4 MB, reduce drawn primitives — do not plan to raise the cap. Never pass `--size` that would invite the 12 MB halve.

Dph1 does **not** commit `living-physarum.gif`. Do not run full-fleet `generate living-art` without `--only`.

### Palette

Dph1 may leave the dark-blue → gold ramp (`ART_PALETTE_ANCHORS["physarum"]`, `palette.py:78-84`) as-is if Dph4 follows immediately. Do not block Dph1 on contrast polish, but **do not add a second light/dark branch**. Vein/node opacity must work on `_BG_COLOR = oklch(0.12, 0.04, 250)` *and* on GitHub light chrome at 400×400.

### Verify Dph1

Caption-blind (strip `#accretion-dialect` / `data-role="accretion-dialect"` before judging):

- [ ] t0 `1/2/20/1`, `timeline=False`: **≥1 tagged vein** and ≥1 `physarum-node-core`. Spore optional. Overlay ignored.
- [ ] `growth_mat < 0.05` (explicit `maturity=0.02` or computed ~0.01) still draws tagged veins when a repo exists.
- [ ] Commits-only: tagged vein width / mass / glow **up** — not only overlay `<path>` stroke or `deposit_amount`.
- [ ] Followers-only: tagged hyphae count or spread **up**, never down.
- [ ] Stars-only: max core `r` **and** visible ink **up**.
- [ ] Repos-only: core count **and** connecting tagged veins **up**.
- [ ] `uv run python -m pytest -q tests/test_physarum.py`
- [ ] Existing media tests still green (they are insufficient, not retired):
  `uv run python -m pytest -q tests/test_living_art_media.py -k 'physarum or early_spine or ink_and_physarum'`

Do not green Dph1 by writing Dph2 tests that still count `physarum-spore` or untagged `<path>`.

---

## Dph2 — on-canvas t0 + isolation (`L-T-ACC`)

**Job:** make A1/A2 physarum assertions green by proving the **network**, not the caption, the spore, or the node floor alone.

**File:** `tests/test_art_shared_package.py` only. Do **not** move the contract into `test_physarum.py` or `test_living_art_media.py`. Those stay as generator/regression coverage.

Graph verify: `pytest -k physarum`.

### Wait for A1/A2

A1/A2 land red/xfail on-canvas isolation in this same file (I08). Dph2 greens the **physarum** slice. If a shared D\*2 agent holds `L-T-ACC`, this playbook is that slice — still assert geometry here.

If A1/A2 are not present yet, Dph2 **adds** the physarum on-canvas tests (do not wait forever for names). Prefer sharing helpers with other dialects (overlay strip, `_accretion_metrics` clone with `star_velocity` pinned).

### Required asserts (overlay stripped)

Strip `#accretion-dialect` (and do not score overlay `data-mark-count`, untagged `<path>` totals, or `physarum-spore` as pass). Generate with `timeline=False`, no `evolution_state`.

| Case | Fixture | Pass |
|---|---|---|
| **t0 network** | `_accretion_metrics(repos=1, stars=2, commits=20, followers=1)` | ≥1 `physarum-node-core` **and** ≥1 `data-role="physarum-vein"` with visible stroke/opacity. **Spore is not the mark.** |
| **repos-only** | repo list 1 → 4; stars/commits/followers scalars **fixed** | core count **and** tagged vein connectivity **up** |
| **stars-only** | stars 8 → 180 | max core radius **and** visible ink |
| **commits-only** | same repos/stars/followers; commits 40 → 3200 (media isolation magnitudes) | tagged vein mass/width/glow **strictly up** |
| **followers-only** | followers 1 → 90 | tagged hyphae count or spread **up**, **never down** |

Suggested selectors (Dph1 should have made these real):

- network: `data-role="physarum-vein"` (`stroke-width`, opacity, path length, or bbox) — **must not** be untagged `<path>`
- terminals: `data-role="physarum-node-core"`
- do **not** pass on `data-role="physarum-spore"` alone

**Forbidden pass conditions:** overlay tick counts, raw `svg.count("<path")`, spore presence, node-core presence without veins, `data-accretion-*` only.

Keep existing media attr tests; they are a weaker regression, not this bar.

### `pytest -k physarum` blast radius

That keyword also hits `tests/test_physarum.py`, parametrized media/render-state tests, and coverage helpers — files **outside** `L-T-ACC`. Dph2 must not edit those. If they fail after Dph1, fix in **Dph1** (`physarum.py`), not here.

If Dph1 ungates SMIL nodes, `test_physarum_explicit_maturity_with_timeline_preserves_growth_staging` goes red even though that file is outside this lock — flag it; green it only if lock policy for the shared D\*2 pass explicitly allows a second file. Default: Dph1 keeps that test green.

```bash
uv run python -m pytest -q tests/test_art_shared_package.py -k physarum
uv run python -m pytest -q tests/test_physarum.py
# graph verify (wider):
uv run python -m pytest -q -k physarum
```

---

## Dph3 — bake-off stills (no lock)

**Files:**

- `goals/living-art-overhaul/bakeoff/physarum-t0.svg`
- `goals/living-art-overhaul/bakeoff/physarum-t1.svg`
- `goals/living-art-overhaul/bakeoff/physarum-t2.svg`

Create the `bakeoff/` directory if needed. **Do not** copy `goals/profile-readme-overhaul/inventory/frames/physarum-t*.svg` (spore-only, pre node-floor; published GIFs were never rebuilt after 2026-08-14).

### Export

Same spine and kwargs as A1 / published GIF:

```text
timeline=False
seed stable (e.g. "physarum-dialect")
t0: repos=1, stars=2, commits=20, followers=1
t1: 2 / 24 / 400 / 18
t2: 4 / 120 / 2400 / 80
```

Prefer `compute_maturity` (or the spine’s natural maturity) so t0 stays in the `growth_mat < 0.05` band that used to hide veins. Prefer exporting **after Dph4** so stills show GIF-readable stroke.

### Verify Dph3

- [ ] Three files exist and are well-formed SVGs (`viewBox="0 0 800 800"`).
- [ ] `data-accretion-*` (repos/stars/commits/followers or scales) **increase** t0→t2.
- [ ] Caption-blind glance: t0 is a **first-repo network** (veins, not spore-only); t1/t2 densify. Overlay may still be present; it must not be the only readable growth.
- [ ] t0 SVG contains `data-role="physarum-vein"`.
- [ ] No `living-physarum-dark` sibling implied by the stills.

Graph verify: “three stills + data-accretion attrs increase.”

---

## Dph4 — one look (`L-PH`)

**Job:** `fact-one-look` — one designed look that reads on GitHub light **and** dark. No dual `-dark` pair unless bake-off later proves unreadable.

Graph verify: “no dual `-dark` pair unless unreadable.”

### Must

- Substrate is already dark (`_BG_COLOR = oklch(0.12, 0.04, 250)` / `#000514`). Vein ramp is dark-blue → gold (`ART_PALETTE_ANCHORS["physarum"]`). Gold overlay `#d4c07a` already contrasts. **Do not invent a second theme.**
- Failure mode is **tiny / faint t0 marks**, not theme mismatch. Raise spore/node/vein opacity and stroke so a **400×400** GIF reads on white GitHub light **and** dark README chrome.
- Identity cores (`oklch` L≈0.78, language-tinted) are the bright terminals; keep them.
- One look, not a CSS `@media` pair and not `living-physarum-dark.gif`.

### Must not

- Add a second generator path or `-dark` filename.
- Move overlay origin (A3 / all-six only).
- Re-open the 0.05 vein gate if Dph1 already ungated first-repo veins — only retouch contrast/weight.
- Treat a brighter spore as the look fix.

### Verify Dph4

- [ ] t0 tagged veins + cores are readable at GIF scale on a white page and on dark chrome.
- [ ] `rg living-physarum-dark` is empty in production art paths.
- [ ] `uv run python -m pytest -q tests/test_physarum.py` (identity tint / determinism may change SVG bytes; keep those contracts).
- [ ] Re-export Dph3 stills if they were captured before this look.

---

## Sequence and handoff

```text
A3 (no-op clock) ──► Dph1 (veins from first repo, tagged, 2.4 MB feasible)
                      ├─► Dph4 (one look: thicker/brighter t0 ink, same L-PH)
                      │     └─► Dph3 (stills; re-export if Dph4 landed after)
                      └─► Dph2 (L-T-ACC queue: on-canvas tests)
W2M needs Dph2 + Dph3 + Dph4
G1ph (after W2M): --only physarum, 120 frames, 400×400, sibling MP4, ≤2.4 MB
K1ph scores the regenerated GIF, not A1 stills
```

G1ph command (later wave, not Dph*):

```bash
uv run python -m scripts.cli generate living-art \
  --profile wyattowalsh \
  --metrics-path /path/to/metrics.json \
  --history-path /path/to/history.json \
  --only physarum \
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
| `living-physarum.gif` + `.mp4` regen | `G1ph` |
| Jury score | `K1ph` |
| Roster shrink / exact-six tests | SHR after K2 |
| OpenSpec growth change | never this goal (S15) |
| `animate.py` `physarum-growth` stem | not the published contract (I15) |

---

## Done when

- **Dph1:** caption-blind t0 is a first-repo **network** (tagged veins + node), even at `growth_mat < 0.05`; commits/followers move tagged vein mass **up**; spore is not the A2 mark; 2.4 MB still plausible; `test_physarum.py` green.
- **Dph2:** `test_art_shared_package.py` asserts those geometries with overlay stripped — **not** spore / untagged `<path>` / `data-*` only; `pytest -k physarum` green without editing files outside `L-T-ACC`.
- **Dph3:** three new bake-off SVGs; accretion attrs increase; glance shows network then densify.
- **Dph4:** one dark-gold look; t0 ink survives 400×400 on light and dark GitHub chrome; no `-dark` pair.

Overlay may remain. It must not be the picture.
