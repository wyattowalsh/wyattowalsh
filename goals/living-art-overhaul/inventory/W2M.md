# W2M — README stack + six redesigned dialects ready

**Date:** 2026-08-20  
**Status:** complete  
**Lane:** CAP (Wave RM+DIAL merge). **`main` untouched. OpenSpec growth change untouched.** Leftover DIAL closeout (GIF-path plant ungate, last D\*2 xfails, Dig1 goldens) ships on `origin/dev` with this marker. **GEN GIFs/MP4s are not this node.**  
**Deps:** M6, A3, Dig2, Dto2, Dge2, Dph2, Dle2, Dfe2, Dig3, Dto3, Dge3, Dph3, Dle3, Dfe3, Dig4, Dto4, Dge4, Dph4, Dle4, Dfe4.  
**Inputs:** `W1M.md`, `I99.md`, DIAL playbooks, `goals/living-art-overhaul/bakeoff/*-t{0,1,2}.svg`, `video-check.md`.

Until K2, **`SHIPPED_STYLE_KEYS` is `CANDIDATE_STYLE_KEYS`** (same six, same order). Exact-six tests stay green. Do not shrink. **No `accepted[]`.**

---

## Finding

Wave RM + DIAL are merged. The README Living Art surface is the full-width stack (intro, `width="100%"`, art outside `<details>`, one details per piece). All six on-canvas dialects are redesigned: t0 carries a primary mark, four channels move the picture, and each style keeps one look (no dual `-dark` pair). Shared accretion clock stayed a **no-op**. Isolation tests on `tests/test_art_shared_package.py` are green with **zero xfail**. Bake-off stills for every style exist at t0/t1/t2 with monotonic `data-accretion-*`.

VID already chose **gif-fallback** on `origin/dev` (`c1d142e71` assembler, `cac367b61` README, `b53c41e89` Preview smoke). This marker does **not** start GEN.

W2M sentence: **README stack + six redesigned dialects ready.**

---

## Check tree (this resume)

| Node | Lock | Result |
|---|---|---|
| **M6** | `L-T-GFM` | **Done.** Native `<video src=mp4>` **and** visible GIF+href MP4 are both legal (`tests/test_readme_gfm_ux.py`). YouTube / Cloudinary / iframe fail. |
| **A3** | `L-ACC` | **Done — default no-op.** `0b14f327d` froze `scripts/art/shared/accretion.py`. Unreadability was on-canvas; ceilings/leases unchanged. |
| **Dig1** | `L-IG` | **Done.** `e1fc82520` plus leftover GIF-path ungate: later plants stay visible on snapshot / `timeline=False` worlds (`scripts/art/ink_garden.py`). Plants from first repo; bloom / trunk / glints = stars / commits / followers. |
| **Dto1** | `L-TO` | **Done.** Stars as readable peaks; followers as settlements (`scripts/art/topography.py`). |
| **Dge1** | `L-GE` | **Done.** Distinct peaks; height = stars; generations = commits; colonies = followers (`scripts/art/genetic_landscape.py`). |
| **Dph1** | `L-PH` | **Done.** Network from first repo; t0 is not spore-only (`scripts/art/physarum.py`). |
| **Dle1** | `L-LE` | **Done.** Field / extent readable without the caption (`scripts/art/lenia.py`). |
| **Dfe1** | `L-FE` | **Done.** Distinct towers; same-language dipoles no longer collapse (`scripts/art/ferrofluid.py`). |
| **D\*2** | `L-T-ACC` | **Done (serialized).** `tests/test_art_shared_package.py` — **69 passed, 0 xfail.** `_XFAIL_UNTIL_DSTAR1` removed; all six styles parametrize t0 + four-channel isolation. |
| **Dig2** | `L-T-ACC` | **Done.** Ink Garden isolation green (shared module). |
| **Dto2** | `L-T-ACC` | **Done.** Topography isolation green. |
| **Dge2** | `L-T-ACC` | **Done.** Genetic isolation green (tagged organisms / generation marks). |
| **Dph2** | `L-T-ACC` | **Done.** Physarum isolation green (vein mass). |
| **Dle2** | `L-T-ACC` | **Done.** Lenia isolation green. |
| **Dfe2** | `L-T-ACC` | **Done.** Ferrofluid isolation green (same-language columns at 160 / 320 / 480 / 640). |
| **Dig3** | `—` | **Done.** `goals/living-art-overhaul/bakeoff/inkgarden-t{0,1,2}.svg` |
| **Dto3** | `—` | **Done.** `goals/living-art-overhaul/bakeoff/topo-t{0,1,2}.svg` |
| **Dge3** | `—` | **Done.** `goals/living-art-overhaul/bakeoff/genetic-t{0,1,2}.svg` |
| **Dph3** | `—` | **Done.** `goals/living-art-overhaul/bakeoff/physarum-t{0,1,2}.svg` |
| **Dle3** | `—` | **Done.** `goals/living-art-overhaul/bakeoff/lenia-t{0,1,2}.svg` |
| **Dfe3** | `—` | **Done.** `goals/living-art-overhaul/bakeoff/ferrofluid-t{0,1,2}.svg` |
| **Dig4** | `L-IG` | **Done.** One parchment look (aged paper). No `living-inkgarden-dark`. |
| **Dto4** | `L-TO` | **Done.** One cream hypsometric look. No `living-topo-dark`. |
| **Dge4** | `L-GE` | **Done.** One designed ground. No `living-genetic-dark`. |
| **Dph4** | `L-PH` | **Done.** One dark substrate + gold veins. No `living-physarum-dark`. |
| **Dle4** | `L-LE` | **Done.** One near-black luminous field. No `living-lenia-dark`. |
| **Dfe4** | `L-FE` | **Done.** One near-black pool sculpture. No `living-ferrofluid-dark`. |

Six keys (order): `inkgarden`, `topo`, `genetic`, `physarum`, `lenia`, `ferrofluid`.

---

## Stills paths (D\*3)

All under `goals/living-art-overhaul/bakeoff/`. `data-accretion-{repos,stars,commits,followers}` increase t0 → t1 → t2.

| Style | t0 | t1 | t2 |
|---|---|---|---|
| inkgarden | `inkgarden-t0.svg` | `inkgarden-t1.svg` | `inkgarden-t2.svg` |
| topo | `topo-t0.svg` | `topo-t1.svg` | `topo-t2.svg` |
| genetic | `genetic-t0.svg` | `genetic-t1.svg` | `genetic-t2.svg` |
| physarum | `physarum-t0.svg` | `physarum-t1.svg` | `physarum-t2.svg` |
| lenia | `lenia-t0.svg` | `lenia-t1.svg` | `lenia-t2.svg` |
| ferrofluid | `ferrofluid-t0.svg` | `ferrofluid-t1.svg` | `ferrofluid-t2.svg` |

Accretion (all six): t0 `1 / 2 / 20 / 1` · t1 `2 / 24 / 400 / 18` · t2 `4 / 120 / 2400 / 80`.

t0 primary marks in those stills include `ink-canopy` / `ink-trunk`, `repo-peak` + `topo-settlement-mark`, `genetic-peak-core`, `physarum-vein` (not spore-only), `lenia-field`, `ferro-dipole` / `ferro-spike`.

---

## Verify (W2M gate)

D\*2 (2026-08-20):

```text
uv run python -m pytest -q tests/test_art_shared_package.py
69 passed, 0 xfail
```

VID already gif-fallback (not this file’s job):

```text
decision = gif-fallback
origin/dev: c1d142e71 assembler, cac367b61 README, b53c41e89 Preview smoke
blob Preview: 6 GIFs visible, 0 <video>, 6 Watch MP4 links
```

No production `living-*-dark.gif` under `.github/assets/img`. `rg living-topo-dark` remains a **rejection** fixture in `tests/test_living_art_media.py`, not a shipped asset.

RM slice (already on `origin/dev`): `generate readme-sections` + `pytest -q tests/test_readme_gfm_ux.py -k living_art`.

---

## Live wiring (after W2M)

| Surface | Follows | Path |
|---|---|---|
| README stack | shipped six, full-width, details legends | `scripts/readme_sections.py` + `README.md` |
| Media form | **gif-fallback** (VID done) | visible GIF + Watch MP4; legal tests still accept `<video>` |
| Dialects | six redesigned generators | `ink_garden.py` · `topography.py` · `genetic_landscape.py` · `physarum.py` · `lenia.py` · `ferrofluid.py` |
| Shared clock | frozen no-op | `scripts/art/shared/accretion.py` |
| Isolation tests | all six, no xfail | `tests/test_art_shared_package.py` |
| Dig1 goldens | full / mid maturity | `tests/fixtures/ink_garden/{minimal_full,rich_full,rich_mid}.svg` |
| Bake-off stills | t0/t1/t2 × six | `goals/living-art-overhaul/bakeoff/` |
| Roster | shipped == candidates == six | `scripts/art/roster.py` until K2 |
| `accepted[]` | **absent** | BAK `K2` human gate — not this node |
| Published GIFs/MP4s | **stale vs dialects** | GEN `G1ig`…`G1fe` after this marker |

---

## Next (after this marker)

**GEN is next. Do not start it from this file.** VID is already gif-fallback; do not re-run V2–V4 unless Preview regresses.

| Node | Lock | Parallel |
|---|---|---|
| **G1ig** | `L-ASSET-IG` | ∥ G1to…G1fe |
| **G1to** | `L-ASSET-TO` | ∥ |
| **G1ge** | `L-ASSET-GE` | ∥ |
| **G1ph** | `L-ASSET-PH` | ∥ |
| **G1le** | `L-ASSET-LE` | ∥ |
| **G1fe** | `L-ASSET-FE` | ∥ |
| **G1** | `—` | after the six pairs |
| **G2** | `L-T-MEDIA` | after G1 |
| **G3** | `—` | ∥ G2 (contact sheet from new GIFs) |
| **W3M** | `—` | after V4 (already done) + G2 + G3 |

GEN recipe: `render_timelapse --only <style> --max-frames 120 --size 400`; sibling MP4; stay inside `LIVING_ART_BYTE_BUDGETS`. Do not use `generate animated`. Do not raise caps. Do not commit with `art: regenerate living-art assets`.

---

## Leftover (not this merge)

1. **GEN** published `living-*.gif` / `.mp4` still predate the redesigned dialects.
2. **K1–K3** bake-off score + human `accepted[]`. Agents must not invent `accepted`.
3. **S1→S15** shrink stays blocked until K2. Shipped remains six.
4. **OpenSpec** `prevent-living-art-repo-growth` leftover `exact-six` is intended (S15).
5. Idle dirt out of this goal: featured cards / showcase, `goals/profile-readme-overhaul/**`, `scripts/utils.py`, `tech-test.svg`.
6. `main` stays untouched.

```
