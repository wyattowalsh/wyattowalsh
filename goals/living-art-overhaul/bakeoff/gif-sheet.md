# G3 GIF contact sheet (G1 fleet)

Decoded **2026-08-20** from the on-disk G1 GIFs. **No re-render.** Pillow `Image.n_frames` + `Image.seek(i)`. This sheet is the bake-off still graph for the regenerated fleet, not the 2026-08-14 A1 SVGs and not `bakeoff/{style}-t{0,1,2}.svg` (DIAL stills).

Graph verify: **six styles × 3 frames referenced** (18 cells). No extra frame PNGs — GitHub cannot pin a GIF frame, so each cell names a **Pillow 0-based index** on the relative GIF.

## Decode rule

For each GIF:

| Slot | Index |
|---|---|
| first | `0` |
| mid | `n_frames // 2` |
| last | `n_frames - 1` |

Every G1 GIF has `n_frames == 120`, so the indices are **0 / 60 / 119** on all six.

```python
from PIL import Image

im = Image.open(".github/assets/img/living-inkgarden.gif")
assert im.n_frames == 120
im.seek(0)    # first
im.seek(60)   # mid
im.seek(119)  # last
```

Paths below are relative to this file (`goals/living-art-overhaul/bakeoff/`). Repo-root equivalents: `.github/assets/img/living-{style}.gif`.

## Six × three

| Style | GIF | First | Mid | Last |
|---|---|---:|---:|---:|
| `inkgarden` (Ink Garden) | [living-inkgarden.gif](../../../.github/assets/img/living-inkgarden.gif) | **0** | **60** | **119** |
| `topo` (Topography) | [living-topo.gif](../../../.github/assets/img/living-topo.gif) | **0** | **60** | **119** |
| `genetic` (Genetic Landscape) | [living-genetic.gif](../../../.github/assets/img/living-genetic.gif) | **0** | **60** | **119** |
| `physarum` (Physarum) | [living-physarum.gif](../../../.github/assets/img/living-physarum.gif) | **0** | **60** | **119** |
| `lenia` (Lenia) | [living-lenia.gif](../../../.github/assets/img/living-lenia.gif) | **0** | **60** | **119** |
| `ferrofluid` (Ferrofluid) | [living-ferrofluid.gif](../../../.github/assets/img/living-ferrofluid.gif) | **0** | **60** | **119** |

Per-cell references (same GIFs, explicit seeks):

| Style | First | Mid | Last |
|---|---|---|---|
| inkgarden | [living-inkgarden.gif](../../../.github/assets/img/living-inkgarden.gif) `seek(0)` | [living-inkgarden.gif](../../../.github/assets/img/living-inkgarden.gif) `seek(60)` | [living-inkgarden.gif](../../../.github/assets/img/living-inkgarden.gif) `seek(119)` |
| topo | [living-topo.gif](../../../.github/assets/img/living-topo.gif) `seek(0)` | [living-topo.gif](../../../.github/assets/img/living-topo.gif) `seek(60)` | [living-topo.gif](../../../.github/assets/img/living-topo.gif) `seek(119)` |
| genetic | [living-genetic.gif](../../../.github/assets/img/living-genetic.gif) `seek(0)` | [living-genetic.gif](../../../.github/assets/img/living-genetic.gif) `seek(60)` | [living-genetic.gif](../../../.github/assets/img/living-genetic.gif) `seek(119)` |
| physarum | [living-physarum.gif](../../../.github/assets/img/living-physarum.gif) `seek(0)` | [living-physarum.gif](../../../.github/assets/img/living-physarum.gif) `seek(60)` | [living-physarum.gif](../../../.github/assets/img/living-physarum.gif) `seek(119)` |
| lenia | [living-lenia.gif](../../../.github/assets/img/living-lenia.gif) `seek(0)` | [living-lenia.gif](../../../.github/assets/img/living-lenia.gif) `seek(60)` | [living-lenia.gif](../../../.github/assets/img/living-lenia.gif) `seek(119)` |
| ferrofluid | [living-ferrofluid.gif](../../../.github/assets/img/living-ferrofluid.gif) `seek(0)` | [living-ferrofluid.gif](../../../.github/assets/img/living-ferrofluid.gif) `seek(60)` | [living-ferrofluid.gif](../../../.github/assets/img/living-ferrofluid.gif) `seek(119)` |

## Contract (Pillow, not a re-render)

All six: **400×400**, **120** frames, **loop 0**, runtime **29 660 ms** (first frame 260 ms, mid 220 ms, last hold 3 000 ms). Unique duration values: 220 / 260 / 3 000 ms. Meets `LIVING_ART_CANONICAL_DIMENSIONS`, `LIVING_ART_MAX_FRAME_COUNT` (120), `LIVING_ART_CANONICAL_LOOP` (0), `LIVING_ART_MIN_RUNTIME_MS` (24 000).

## Bytes vs `LIVING_ART_BYTE_BUDGETS`

Caps from `scripts/art/artifacts.py` (`LIVING_ART_BYTE_BUDGETS` / `LIVING_ART_TOTAL_BYTE_BUDGET`). MP4 siblings have no budget.

| GIF | Bytes | Budget | Headroom | % of cap |
|---|---:|---:|---:|---:|
| [living-inkgarden.gif](../../../.github/assets/img/living-inkgarden.gif) | 6 973 318 | 7 200 000 | 226 682 | 96.85% |
| [living-topo.gif](../../../.github/assets/img/living-topo.gif) | 8 605 147 | 10 000 000 | 1 394 853 | 86.05% |
| [living-genetic.gif](../../../.github/assets/img/living-genetic.gif) | 1 106 783 | 2 400 000 | 1 293 217 | 46.12% |
| [living-physarum.gif](../../../.github/assets/img/living-physarum.gif) | 2 163 996 | 2 400 000 | 236 004 | 90.17% |
| [living-lenia.gif](../../../.github/assets/img/living-lenia.gif) | 855 793 | 1 200 000 | 344 207 | 71.32% |
| [living-ferrofluid.gif](../../../.github/assets/img/living-ferrofluid.gif) | 3 613 585 | 3 800 000 | 186 415 | 95.09% |
| **fleet total** | **23 318 622** | **27 000 000** | **3 681 378** | **86.37%** |

All six are under cap. Tightest: inkgarden, ferrofluid, physarum.

## Mean RGB at the three seeks

After `seek(i)` then `convert("RGBA")` (same seek path as `_gif_fingerprint` in `scripts/art/_gif_optimize.py`). Approximate mean RGB; not a score.

| Style | Frame 0 | Frame 60 | Frame 119 |
|---|---|---|---|
| inkgarden | 194.2, 186.6, 170.4 | 156.4, 157.9, 137.1 | 149.1, 155.7, 135.6 |
| topo | 216.3, 229.6, 224.5 | 188.2, 212.4, 189.5 | 203.1, 213.2, 202.1 |
| genetic | 4.2, 14.2, 24.3 | 6.2, 18.8, 27.4 | 26.4, 59.5, 54.1 |
| physarum | 0.3, 5.2, 20.0 | 8.9, 13.1, 24.1 | 32.6, 39.6, 41.7 |
| lenia | 1.1, 0.2, 11.2 | 5.7, 7.4, 16.2 | 9.9, 14.0, 19.9 |
| ferrofluid | 0.3, 0.7, 3.0 | 13.1, 39.4, 43.3 | 24.7, 67.4, 70.9 |

Dark styles (genetic / physarum / lenia / ferrofluid) brighten 0 → 60 → 119. Ink Garden and Topography start parchment-light and fill (mean RGB drops, then topo rebounds slightly on the last hold).

## Out of this sheet

- No generator edits, no tests, no G2.
- Do not treat `goals/profile-readme-overhaul/inventory/frames/` (A1, 2026-08-14) as this fleet.
- Do not treat `bakeoff/{style}-t{0,1,2}.svg` as GIF frames; those are dialect stills for DIAL, not G1 rasters.
- Scoring (`K1*`) starts after W3M; this file only indexes the three seeks.
