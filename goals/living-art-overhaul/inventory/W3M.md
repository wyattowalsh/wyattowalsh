# W3M — Media + video form frozen; ready to score

**Date:** 2026-08-20  
**Status:** complete  
**Lane:** CAP (Wave VID+GEN merge). **`main` untouched. OpenSpec growth change untouched.** **No `accepted[]`.** This marker does **not** start BAK `K1*`, SHR `S1`, or a GEN re-render. **No commit.**  
**Deps:** V4, G1ig, G1to, G1ge, G1ph, G1le, G1fe, G1, G2, G3.  
**Inputs:** `W2M.md`, `I99.md`, `goals/living-art-overhaul/video-check.md`, `goals/living-art-overhaul/bakeoff/gif-sheet.md`, `tests/test_living_art_media.py`.

Until K2, **`SHIPPED_STYLE_KEYS` is `CANDIDATE_STYLE_KEYS`** (same six, same order). Exact-six tests stay green. Do not shrink. **No `accepted[]`.**

---

## Finding

Wave VID + GEN are merged for scoring. GitHub blob Preview **strips `<video>`**; VID froze **gif-fallback**. README on `origin/dev` is the full-width stack: visible GIF + Watch (MP4), art outside `<details>`. Preview smoke **PASS** (six GIFs visible, zero rendered `<video>`).

The published fleet is six `living-{style}.gif` + sibling `.mp4` at `.github/assets/img/` (400×400, 120 frames, ≥24 s). Each GIF sits under `LIVING_ART_BYTE_BUDGETS` after encode / generator fit. Caps were **not** raised. G2 asserts committed GIF budgets **and** non-empty MP4 siblings. G3 indexes frames **0 / 60 / 119** on those GIFs.

Shipped is still six. Scoring starts after this marker. Agents must not write `bakeoff.json` `accepted[]`.

W3M sentence: **Media + video form frozen; ready to score.**

---

## Check tree (this resume)

| Node | Lock | Result |
|---|---|---|
| **V1** | `L-VID` | **Done.** `goals/living-art-overhaul/video-check.md` exists; play / strip / no-autoplay listed. |
| **V2** | `—` | **Done.** github.com `blob/dev/README.md` Preview: `<video>` **stripped** from the rendered DOM (`article.markdown-body` `video` count **0**). |
| **V3** | `L-VID` | **Done.** `decision = gif-fallback`. No external host. |
| **V4** | `L-RS` | **Done.** Assembler is visible full-width GIF + Watch (MP4) on the M2 stack (`scripts/readme_sections.py`). README on `origin/dev` matches. Preview smoke **PASS** (six GIFs visible). |
| **G1ig** | `L-ASSET-IG` | **Done.** `living-inkgarden.gif` + `.mp4` |
| **G1to** | `L-ASSET-TO` | **Done.** `living-topo.gif` + `.mp4` |
| **G1ge** | `L-ASSET-GE` | **Done.** `living-genetic.gif` + `.mp4` |
| **G1ph** | `L-ASSET-PH` | **Done.** `living-physarum.gif` + `.mp4` |
| **G1le** | `L-ASSET-LE` | **Done.** `living-lenia.gif` + `.mp4` |
| **G1fe** | `L-ASSET-FE` | **Done.** `living-ferrofluid.gif` + `.mp4` |
| **G1** | `—` | **Done.** Six GIF+MP4 pairs at `.github/assets/img/`. 400×400, 120 frames, runtime ≥24 s. Under `LIVING_ART_BYTE_BUDGETS`. Caps not raised. No `_assemble_gif` 12 MB halve. |
| **G2** | `L-T-MEDIA` | **Done.** `test_committed_living_art_fleet_meets_byte_budgets_and_mp4_siblings` in `tests/test_living_art_media.py` (I99 correction 7). |
| **G3** | `—` | **Done.** `goals/living-art-overhaul/bakeoff/gif-sheet.md` — six styles × frames **0 / 60 / 119**. No re-render. |

Six keys (order): `inkgarden`, `topo`, `genetic`, `physarum`, `lenia`, `ferrofluid`.

---

## G1 fleet (on disk)

All under `.github/assets/img/`. GIF contract from G3 decode (Pillow): **400×400**, **120** frames, loop **0**, runtime **29 660 ms** (≥ `LIVING_ART_MIN_RUNTIME_MS` 24 000). MP4 siblings have **no** byte budget.

| Style | GIF | MP4 | GIF bytes | Budget | % of cap |
|---|---|---|---:|---:|---:|
| inkgarden | `living-inkgarden.gif` | `living-inkgarden.mp4` | 6 973 318 | 7 200 000 | 96.85% |
| topo | `living-topo.gif` | `living-topo.mp4` | 8 605 147 | 10 000 000 | 86.05% |
| genetic | `living-genetic.gif` | `living-genetic.mp4` | 1 106 783 | 2 400 000 | 46.12% |
| physarum | `living-physarum.gif` | `living-physarum.mp4` | 2 163 996 | 2 400 000 | 90.17% |
| lenia | `living-lenia.gif` | `living-lenia.mp4` | 855 793 | 1 200 000 | 71.32% |
| ferrofluid | `living-ferrofluid.gif` | `living-ferrofluid.mp4` | 3 613 585 | 3 800 000 | 95.09% |
| **fleet total** | | | **23 318 622** | **27 000 000** | **86.37%** |

Tightest: inkgarden, ferrofluid, physarum. Caps unchanged in `scripts/art/artifacts.py`.

G3 seeks (all six, `n_frames == 120`): first **0**, mid **60**, last **119**. Sheet is the bake-off still graph for this fleet, not `bakeoff/{style}-t{0,1,2}.svg` and not 2026-08-14 A1 stills.

---

## Verify (W3M gate)

VID (`video-check.md`, 2026-08-20):

```text
decision = gif-fallback
blob Preview: <video> stripped (0 in article.markdown-body)
origin/dev README: full-width GIF + Watch (MP4)
Post-regen Preview smoke: PASS — 6 GIFs visible, 0 <video>, 6 Watch MP4 links
```

G2 (I99 correction 7):

```text
tests/test_living_art_media.py::test_committed_living_art_fleet_meets_byte_budgets_and_mp4_siblings
validate_living_art_byte_budgets(build_living_art_manifest(img_dir))
sibling living-{style}.mp4 exists and is non-empty for each SHIPPED key
```

G3 graph: **six styles × 3 frames referenced** (18 cells). No extra frame PNGs.

`bakeoff.json` `accepted[]` is **absent**. Do not invent it here.

---

## Live wiring (after W3M)

| Surface | Follows | Path |
|---|---|---|
| Media form | **gif-fallback** (VID frozen) | visible GIF + Watch MP4; legal tests still accept `<video>` |
| README stack | shipped six, full-width, details legends | `scripts/readme_sections.py` + `README.md` on `origin/dev` |
| Published GIFs | G1 fleet, 400×400 / 120 / ≥24 s | `.github/assets/img/living-{style}.gif` |
| Published MP4s | unmanaged siblings (I03 / I18) | `.github/assets/img/living-{style}.mp4` |
| Byte budgets | six GIF rows, caps **not** raised | `scripts/art/artifacts.py` `LIVING_ART_BYTE_BUDGETS` |
| Committed-fleet test | GIF budgets + MP4 presence | `tests/test_living_art_media.py` G2 |
| Contact sheet | frames 0 / 60 / 119 | `goals/living-art-overhaul/bakeoff/gif-sheet.md` |
| Dialect stills | t0/t1/t2 × six (DIAL, not G1 rasters) | `goals/living-art-overhaul/bakeoff/{style}-t{0,1,2}.svg` |
| Roster | shipped == candidates == six | `scripts/art/roster.py` until K2 |
| `accepted[]` | **absent** | BAK `K2` human gate — **not this node** |

---

## Next (after this marker)

**BAK K1 scoring is next. Do not start it from this file.** Do **not** write `bakeoff.json` `accepted[]`. Do **not** start `S1`. Do **not** re-render GEN.

| Node | Lock | Parallel |
|---|---|---|
| **K1ig** | `—` | ∥ K1to…K1fe |
| **K1to** | `—` | ∥ |
| **K1ge** | `—` | ∥ |
| **K1ph** | `—` | ∥ |
| **K1le** | `—` | ∥ |
| **K1fe** | `—` | ∥ |
| **K1** | `L-BAKE` | after the six scores — **`proposed` only** |
| **K2** | `L-BAKE` | **human** `accepted[]` |
| **K3** | `L-T-GFM` | after K2; red until S14 |

Score on G3 `gif-sheet.md` + D\*3 stills + the G1 GIFs/MP4s. Four axes: striking, readable growth, distinct, GitHub-fit. Isolation tests are not the jury.

---

## Leftover (not this merge)

1. **Genetic GIF-path `min(colony_count, 1)`** leftover vs `test_leased_style_knobs_track_isolated_channels`. Sibling may still be fixing `scripts/art/genetic_landscape.py`. **Not closed here.**
2. **GIFs / G2 test / `gif-sheet.md` are not necessarily committed yet.** On-disk + test presence is this gate; git write is not.
3. **K1–K3** bake-off score + human `accepted[]`. This file must **not** write `accepted[]`. Agents must not invent `accepted`.
4. **S1→S15** shrink stays blocked until K2. Shipped remains six.
5. **OpenSpec** `prevent-living-art-repo-growth` leftover `exact-six` is intended (S15).
6. **C3** (later CAP) must click each piece and confirm the film matches this G1 encode, not a previous one (I18 stale-film gap).
7. `main` stays untouched.
