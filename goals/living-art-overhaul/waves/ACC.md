# Wave ACC — Shared accretion (`A1`–`A3`)

**Lane:** ACC. **Locks:** `L-T-ACC` then `L-ACC`. Parallel with RM after **W1M**.
**This file is the execution playbook.** Inventory evidence: [`../inventory/I08.md`](../inventory/I08.md), [`../inventory/I99.md`](../inventory/I99.md) correction 9 + lock table.
**No production edits while authoring this playbook.** Implementers own `A1`–`A3` later. This wave does **not** redesign a generator.

Caption here = the on-SVG `#accretion-dialect` register (family word + four numeric glyphs). Not the README `<details>` legend (Wave RM). A1 on-canvas isolation and A2 t0 marks must read **with that register stripped**. Overlay ticks already grow (`test_style_dialects_make_accretion_readable`). Overlay-yes is not growth-readable.

Until K2, shipped == candidates == six. Do not shrink CI, drop a dialect, retune `_CHANNEL_CEILINGS`, or raise `LIVING_ART_BYTE_BUDGETS`.

---

## Lock / graph

| ID | Lock | File(s) | Deps | Parallel | Verify (graph) |
|---|---|---|---|---|---|
| **A1** | `L-T-ACC` | `tests/test_art_shared_package.py` **only** | W1M, I08 | RM-ACC (with M1–M6) | “new tests fail or skip until dialects ship” |
| **A2** | `L-T-ACC` | same file | A1 | sequential on `L-T-ACC` | “t0 plant/contour/peak/vein/creature/spike asserted” |
| **A3** | `L-ACC` | `scripts/art/shared/accretion.py` | A2 | after A2 | “monotonic contract + extract_accretion_channels still hold” |

`A1` and `A2` share `L-T-ACC` → **sequential on `tests/test_art_shared_package.py`**. `A3` is a **documented no-op** unless all six need the same clock (I08 + I09–I14; I99 correction 9). Do **not** move the contract into `tests/test_living_art_media.py`. Existing media tests stay as regression; they are not the red bar.

**`D*2` serialize on `L-T-ACC` after `D*1`.** Dig2 / Dto2 / Dge2 / Dph2 / Dle2 / Dfe2 all write this same file. Prefer **one greening agent after all `D*1`** (`plan.md`; I99 risk 3). Do not start `D*2` during ACC. Do not hold `L-T-ACC` past A2 if DIAL `D*1` is ready — A3 uses `L-ACC`, not the test lock.

**Recommended lane order:** A1 (two-layer tests) → A2 (t0 marks, overlay stripped) → A3 (no-op clock) → six `D*1` in parallel → one `D*2` greening pass.

Published GIF path (must be the isolation path too):

```text
generate(metrics, seed=…, maturity=snapshot.maturity, timeline=False)
```

`timelapse.py` forces `timeline=False`. Isolation fixtures: pin `star_velocity={recent_rate:0, peak_rate:0}`, no `evolution_state` / `render_state` unless the test is specifically about the envelope.

A1 spine (reuse `_accretion_metrics` in `tests/test_living_art_media.py:1144`, **then force velocity to zero** — that helper currently leaks stars into `star_velocity`):

| Frame | repos / stars / commits / followers |
|---|---|
| t0 | 1 / 2 / 20 / 1 |
| t1 | 2 / 24 / 400 / 18 |
| t2 | 4 / 120 / 2400 / 80 |

---

## Target (without caption)

Four-signal spine is already extracted and log-normalized (`accretion.py`: repos 36 / stars 500 / commits 8000 / followers 400). Dialects lease stars / commits / followers onto named knobs. **Repos have no named knob** — count of primary marks is the repo encoding.

| Channel | Shared clock | Intended picture (all six) | Fail if you only prove |
|---|---|---|---|
| **repos** | `channels.repos` + overlay `mark_count("repos")` | count of primary marks (plant / peak / peak-core / network / organism / tower) | overlay ticks / `data-accretion-repos` |
| **stars** | `star_scale` → per-style lease | bloom / summit / core radius / node r / halo / spike height | overlay star ticks / knob dict only |
| **commits** | `commit_scale` → per-style lease | trunk / contour identity / generations / vein mass / field occupancy / ripples | overlay commit ticks / `data-*` only |
| **followers** | `follower_scale` → per-style lease | glints / settlements / colonies / vein spread / extent / leased field | overlay follower ticks / composite soup |

Do **not** require overlay `data-mark-count` as the pass condition for on-canvas isolation.

Suggested primary-mark selectors (A2 + A1 layer 2; overlay ignored):

| Style | t0 / repos mark | stars | commits | followers |
|---|---|---|---|---|
| inkgarden | `class="repo-tree"` with visible canopy | blooms | trunk stroke/length | fireflies with velocity pinned |
| topo | `data-role="repo-peak"` | summit / `prominence` geometry | contour identity **without** `followers//10` | settlement geometry, not 1 px |
| genetic | `genetic-peak-core` **brighter than** organism dots | core/glow radius | generation mark ≠ scribble | `gl-micro-colony` ink, 0 at 0 followers |
| physarum | node-core **and** tagged veins | max core r | vein width/mass | vein spread **non-decreasing** |
| lenia | `lenia-seed-halo` / organism op above GIF floor | halo r **and** ink | field occupancy | satellite **spread** |
| ferrofluid | `ferro-dipole` / canonical tower | max spike height | visible ripples (or replacement) | leased field mark, not composite soup |

Same-language ferro fixture (all Python) for repos isolation — I14: alternating Py/Go still shares x-fraction 0.25.

---

## Residue (why knob-only A1 would stall DIAL)

Evidence: I08 + I99 correction 9. Live `generate()`, not the 2026-08-14 A1 stills. Published `living-*.gif` were **not** regenerated after those stills (I15). Do not reuse them as bake-off evidence (`D*3`).

| Style | A1 caption leftover | Live t0 vs leftover | A2 mark (overlay stripped) |
|---|---|---|---|
| **inkgarden** | t0 empty garden | Live GIF path already draws ≥1 `repo-tree` at `tree_t≥0.34`; bloom gate 0.48 still hides canopy | visible **plant** (stem **and** canopy) |
| **topo** | stars weaker than contours | Not empty: `repo-peak` + sub-pixel outpost; `prominence_scale` never enters `peak_h` | visible **repo-peak**, not the anonymous central blob |
| **genetic** | overlay + peaks; colonies on t2 | Not empty: 1 peak under a 37-dot swarm; colonies op ~0.04 | **peak core** brighter than swarm |
| **physarum** | t0 spore-only | Live GIF: spore **+ node**, **0 veins** (`growth_mat≈0.01 < 0.05`) | **network** (node **and** veins) — **not spore** |
| **lenia** | overlay + seeds | Seed exists; halo op ~0.03; CA killed by `simulation_mix≤0.34` | visible **organism**, not overlay |
| **ferrofluid** | same-language clustering | t0 **already has a tower** (1 dipole, 17 spikes). Clustering is Dfe1, not empty-t0 | t0: one **tower**. Do **not** encode clustering in A2 |

Plan research named three leftovers (empty garden / spore / clustered). A1 tests must cover **all six**, not only those three. Topo / genetic / lenia already have t0 marks that fail as **learnable channels** once the overlay is ignored.

`test_art_shared_package.py` today (`:69-101`): extract 2/24/400/18; `star_scale∈(0,1)`; `STYLE_DIALECTS` keys `== ALL_STYLES` exact six; six families. **No** log monotonicity, mark_count, knob isolation, unknown-style, t0 generate, or repo-count fallbacks.

Leaks A1 isolation **must pin**:

- Ink `glint_count` vs `star_velocity` fireflies.
- Topo `n_levels += followers//10` — commits isolation must freeze followers.
- Genetic `pop_count` includes follower_scale — followers leak into the swarm.
- Ferro `signals.field_gain` includes follower_scale **and** star_scale **and** dialect `field_gain`.

---

## Shared constraints (A1–A3)

**Do**

- Write A1/A2 in `tests/test_art_shared_package.py` only so `D*2` serialize on `L-T-ACC`.
- Strip `#accretion-dialect` (and `data-role="accretion-dialect"`) before scoring the picture. Leave the overlay **in the SVG** unless A3/RM ask to remove it.
- Pin `star_velocity={recent_rate:0, peak_rate:0}`. `timeline=False`. No `evolution_state`.
- Keep existing `test_accretion_channels_and_style_dialects_stay_distinct` green through A3. Until K2, keep six keys / six families.
- Clock unit tests stay **green now** and through A3. On-canvas layer is **red or `pytest.xfail` / skip until `D*1`**, then `D*2` greens.
- Prefer cloning `_accretion_metrics` into this file (or importing and overriding velocity) rather than inventing a third spine.

**Do not**

- Edit generators (`ink_garden.py` … `ferrofluid.py`), `artifacts.py` budgets, `timelapse.py`, README, workflow, OpenSpec `prevent-living-art-repo-growth`, or `main`.
- Clone overlay readability into A1 (`test_style_dialects_make_accretion_readable` already covers t0→t2 ticks for all six).
- Treat knob-dict isolation as the A1 done bar. That layer is **green today** for stars/commits/followers and would stall DIAL.
- Move overlay origins (only genetic origin is on-map at **(44, 44)** → Dge1 dodges the peak; A3 moves origins only if **all six** collide).
- Add a fourth named repo knob to every dialect unless A1 cannot express repos-only without it. Prefer **not to**.
- Green A1 by asserting `data-accretion-*` / overlay `data-mark-count`.
- Start `D*2` or hold `L-T-ACC` for dialect greening during this wave.
- Rewrite `language_cluster` in `visual.py` (I14: Dfe1 stops **calling** it).
- Treat ferro empty-metrics fake ripples as a t0 mark (I14). A2 uses **1 repo**.
- Reuse 2026-08-14 A1 stills as the pass condition.

---

## A1 — on-canvas isolation, overlay stripped (`L-T-ACC`)

**Job:** each of four channels moves the **picture** (and the leased knob). Graph title says “knob”; I08/I99 forbid knob-only. Verify: “new tests fail or skip until dialects ship.”

Write **two layers** in `tests/test_art_shared_package.py`:

### Layer 1 — clock unit tests (green now, keep green through A3)

- `extract_accretion_channels` on the A1 spine and on fallbacks (`top_repos`, `public_repos`, unnamed dicts, list-valued `stars` → 0).
- `accretion_log_scale`: 0→0, monotonic, ceiling→1, above ceiling clamps.
- `channel_mark_count`: 0→0, first unit ≥1.
- `build_style_dialect` unknown style → `KeyError`.
- Per-style **knob dict** isolation: increase one of stars/commits/followers, assert the leased knob **strictly increases** and the other two leased knobs **do not**.
- **Repos have no knob.** Assert `channels.repos` / overlay `mark_count("repos")` move, and that **no** stars/commits/followers knob moves when only the repo list grows (same stars/commits/followers scalars).
- Ink: `glint_count == 0` at 0 followers.

This layer does **not** satisfy graph verify by itself.

### Layer 2 — on-canvas isolation (red / xfail / skip until `D*1`)

Parametrize **all six** styles. Fixture = A1 spine clone with **`star_velocity` forced `{recent_rate:0, peak_rate:0}`**, `timeline=False`, no `evolution_state`. For each channel, generate low vs high **one channel only**, **strip `#accretion-dialect`**, assert the **picture** mark from the selector table. Repos-only must move **count of primary marks**.

Do **not** score overlay `data-mark-count` or root `data-accretion-*` as pass.

| Case | Isolation | Pass (overlay stripped) |
|---|---|---|
| **repos-only** | repo list grows; stars/commits/followers scalars **fixed** | count of primary marks **up** |
| **stars-only** | stars up; other scalars fixed | style stars mark **up** (geometry, not caption) |
| **commits-only** | commits up; freeze followers (topo `n_levels` leak) | style commits mark **up** |
| **followers-only** | followers 0 → high; velocity pinned | style followers mark **up**; 0 followers → 0 of that mark where the lease hard-zeros (ink glints) |

Ferro repos-only: **same-language** (all Python) fixture so N repos ⇒ N columns is the leftover Dfe1 must hit.

If a helper import from `test_living_art_media.py` is painful, copy the spine shape — do not add A1 cases to that file (`L-T-MEDIA` is R5/G2/S4).

### Verify A1

```bash
uv run python -m pytest -q tests/test_art_shared_package.py
```

- [ ] Layer 1 green.
- [ ] Layer 2 **fails or xfail/skip** for on-canvas isolation until `D*1` (all six). Knob-only must not be the only new asserts.
- [ ] Overlay strip is in the on-canvas helper (parse SVG, drop `#accretion-dialect`, then count marks).
- [ ] `test_accretion_channels_and_style_dialects_stay_distinct` still green.
- [ ] `tests/test_living_art_media.py` overlay tests untouched and still green (do not run as A1’s bar).

Graph verify is the **red/skip** on-canvas layer, not a fully green module.

---

## A2 — t0 primary marks, overlay stripped (`L-T-ACC`)

**Job:** t0 is not an empty field once `#accretion-dialect` is ignored. Graph verify: “t0 plant/contour/peak/vein/creature/spike asserted.”

Same spine t0: `_accretion_metrics(repos=1, stars=2, commits=20, followers=1)`, `timeline=False`, velocity pinned.

Map verify wording → styles: plant=ink, contour/peak=topo+genetic, vein=physarum **network**, creature=lenia, spike=ferro.

| Style | Pass today if you only count | Fail if you require the plan leftover |
|---|---|---|
| inkgarden | live `repo-tree≥1` (stale A1 SVG would fail) | readable plant at 400×400 (bloom/canopy) |
| topo | `repo-peak≥1` | peak ink > contour / no taller anonymous center |
| genetic | `genetic-peak-core≥1` | peak > swarm |
| physarum | `physarum-node-core≥1` (live); spore-only still fails | veins present — **this is the leftover** |
| lenia | seed/organism count≥1 | opacity/size at GIF scale |
| ferrofluid | `ferro-dipole≥1` + spikes | t0 is already a tower; do **not** encode clustering here |

Counting overlay glyphs must not satisfy this. Empty / 0-repo payloads may stay blank (account-created-before-first-repo). A2 uses **1 repo**. Ferro empty-metrics fake ripples must not count.

A2 may `xfail` the leftover geometries (physarum veins, ink canopy, lenia opacity, genetic peak>swarm, topo peak vs blob) until `D*1`. Ferro t0 tower should **pass today** if the assert is “one tower exists,” not “N columns.”

### Verify A2

```bash
uv run python -m pytest -q tests/test_art_shared_package.py
```

- [ ] t0 generate for all six, overlay stripped.
- [ ] Physarum assert is **veins** (tagged `data-role="physarum-vein"` or equivalent), not spore.
- [ ] Ferro t0 is a tower; clustering is out of A2.
- [ ] 0-repo is not used as the t0 case.
- [ ] Sequential on `L-T-ACC` after A1 (same file, one writer).

---

## A3 — documented no-op (`L-ACC`)

**Job:** adjust shared knobs/ceilings **only if all six need the same clock change**. I09–I14 are **unanimous**: redesign in the generator; keep lease names; do not retune `_CHANNEL_CEILINGS` in `D*1`.

**Default A3: documented no-op.** Leave `scripts/art/shared/accretion.py` untouched except maybe a comment and/or exporting `_CHANNEL_CEILINGS` if A1 clock tests need them. That still satisfies “only if all six need the same clock change.”

**Allowed A3 changes** (all six, same formula) — do **not** take these unless A1 on-canvas + real-account numbers prove a **shared** bottleneck:

- Raise/lower `_CHANNEL_CEILINGS` if the **real account saturates** the log band for every style (mock `wyatt` profile is stars 42 / commits 4800 / followers 85 / repos 35 — commits already 0.95 of 8000; stars 0.29 of 500). Only then.
- Change `accretion_log_scale` / `channel_mark_count` if every overlay **and** every knob is judged too compressed at first-unit growth.
- Add a **fourth named repo knob to every dialect** if A1 cannot express repos-only without it. Prefer **not to**.
- Shared overlay geometry if **all six** registers hide the picture (only genetic origin is on-map today → Dge1).

### Must not change in A3

| Surface | Why |
|---|---|
| `ACCRETION_CHANNELS` order/names | README legends + overlay + facts spine |
| `STYLE_DIALECTS` keys | Roster / `ALL_STYLES` (ROS / S1 later). Families stay 1:1 with styles. |
| Extract key mapping (`stars`, `total_commits`, `followers`, repo list) | Must match snapshot `metrics_dict` |
| Per-style **knob names** (`bloom_scale`, …) | Docs + generator reads. One-style retune = `D*1`. |
| Per-style **floors** (ink `glint_count` zero; ferro `field_gain` 0.82) | Not a shared clock. Ferro compression is Dfe1. |
| `compute_maturity` / fade gates | Maturity is why t0 looks empty; `D*1` ungates **marks**, not the calendar. |
| `validate_snapshot_monotonic_contract` / `sample_frames` | Daily spine (`L-TL`) |
| `resolve_render_metrics` / `evolution_state` | Envelope (`metrics.py`) |
| `dialect_group_markup` as the **picture** | Do not “fix” unreadability by enlarging the caption. Overlay may stay. |
| `language_cluster` in `visual.py` | Shared helper; Dfe1 stops calling it. |
| `test_living_art_media.py` overlay tests | Stay green; not the A1 file. |
| OpenSpec `prevent-living-art-repo-growth` | Out of scope (I19 / S15). |

If A3 is a no-op, generators still consume today’s knobs. That is intended. `D*1` all depend on A3 so the clock is frozen before picture work.

### Verify A3

```bash
uv run python -m pytest -q tests/test_art_shared_package.py
# snapshots, not accretion.py — only if A3 actually touched the clock:
uv run python -m pytest -q tests/test_living_art_media.py -k shared_daily_spine
```

- [ ] Default path: **no** functional diff in `accretion.py` (comment / export of ceilings OK).
- [ ] `test_accretion_channels_and_style_dialects_stay_distinct` + A1 layer 1 still hold.
- [ ] Extract key names still match `daily_snapshots` cumulative fields.
- [ ] Do **not** retune ferro `field_gain` 0.82 or ink `glint_count` here.

If A3 is a no-op, graph verify is: clock tests still green + extract still holds. Record the no-op in the node report so DIAL does not wait on a clock rewrite.

---

## `D*2` serialize on `L-T-ACC` (after this wave)

Not ACC work. Recorded so A1/A2 do not paint the file into a corner.

| Node | After | Job on `tests/test_art_shared_package.py` |
|---|---|---|
| Dig2 | Dig1 | green inkgarden t0 + isolation |
| Dto2 | Dto1 | green topo |
| Dge2 | Dge1 | green genetic |
| Dph2 | Dph1 | green physarum (veins) |
| Dle2 | Dle1 | green lenia |
| Dfe2 | Dfe1 | green ferro (columns, not t0-empty) |

Prefer **one greening agent after all `D*1`**. `pytest -k <style>` also hits generator modules / goldens **outside** `L-T-ACC` (I09 ink fixtures; I12 SMIL staging). `D*2` must not edit those — fix in `D*1`.

S10 later rewrites the exact-six `ALL_STYLES` assert (`:91-98`) when shipped shrinks. Until K2, keep six. R5 does **not** own this file for shrink equality (I99: contracts `:231` → S6; this file’s six-key assert stays until S10).

---

## Sequence and handoff

```text
W1M (shipped == candidates == six)
  ├─► RM (M1–M6)                    ∥  ACC
  └─► A1 (L-T-ACC: clock green + on-canvas red/xfail, overlay stripped)
        └─► A2 (L-T-ACC: t0 marks, overlay stripped)
              └─► A3 (L-ACC: documented no-op)
                    └─► Dig1…Dfe1 in parallel (generators; consume today’s knobs)
                          └─► D*2 serialize on L-T-ACC (one greening pass preferred)
```

W2M needs A3 **and** all `D*2` / `D*3` / `D*4`. ACC alone does not unlock GEN.

---

## Out of this lane

| Concern | Owner |
|---|---|
| README stack / `<details>` mapping copy | RM `M1`–`M6` |
| Generator picture redesign | Dig1…Dfe1 |
| Greening A1/A2 on-canvas asserts | `D*2` on `L-T-ACC` |
| Bake-off stills | `D*3` (new files; not 2026-08-14 A1) |
| One look per style | `D*4` |
| `living-*.gif` + `.mp4` regen | `G1*` |
| Overlay origin for genetic only | Dge1 (not A3) |
| Ferro `language_cluster` x-pack | Dfe1 (do not edit `visual.py`) |
| Roster shrink / exact-six tests | SHR after K2 |
| OpenSpec growth change | never this goal (S15) |
| `main` | never this goal |

---

## Done when

- **A1:** two layers in `tests/test_art_shared_package.py`. Clock unit tests green. On-canvas isolation parametrizes all six, **strips `#accretion-dialect`**, pins `star_velocity`, `timeline=False`; repos-only moves **count of primary marks**. Layer 2 fails or xfail/skip until dialects ship — **not** knob-only green.
- **A2:** t0 `1/2/20/1` asserts plant / peak / peak-core / **veins** / organism / tower with overlay ignored. Physarum ≠ spore. Ferro ≠ clustering. 1 repo, not 0.
- **A3:** documented no-op on `L-ACC` unless all six share a clock failure (they do not). Lease names and ceilings stay. `D*1` may start after this node even if `accretion.py` is byte-identical.
- **`D*2`:** not done here; they serialize later on the same test file. Prefer one greening agent after all `D*1`.

Overlay may remain. It must not be the picture.
