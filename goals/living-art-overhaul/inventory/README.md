# Wave I inventory — living-art-overhaul

Read-only CURRENT TREE notes. One file per I01–I19 plus this I99 merge. **No production edits in Wave I.** ROS (R1–R5) starts after I99; until K2, shipped == candidates == six.

| File | Title | One-line finding |
|---|---|---|
| [I01.md](./I01.md) | README assembler + GFM wrap tests | Living Art is a hardcoded six-tuple 360 wrap with no intro/`<details>`/`<video>`; three test files freeze that (GFM + workflow piggyback + unlocked `test_readme_sections.py`). |
| [I02.md](./I02.md) | Style keys / dialects / CLI picker | No `roster.py`; `--only` and default generate both use `LIVING_ART_STYLE_KEYS`; R4 must split candidates vs shipped. |
| [I03.md](./I03.md) | Artifacts inventory / stage / publish / budgets | GIF-only exact-N inventory (N = budget keys); MP4s unmanaged — leftover `living-*.mp4` are re-committed unless S13 deletes them. |
| [I04.md](./I04.md) | Workflow prepare / generate / assemble / finalize | Matrix already follows `LIVING_ART_STYLE_KEYS`; `max-parallel: 6` and “exact-six” step names stay hardcoded until S3; `dev` only, never `main`. |
| [I05.md](./I05.md) | Workflow + handoff exact-six tests | Literal `6 assets` / `max-parallel == 6` / wrap `== 6`; S5 ↛ S3 (`STAGE_STEP` is the YAML `name:`); S9 `-k living_art` misses wrap/no-details. |
| [I06.md](./I06.md) | `test_cli` living-art matrix | Loops `LIVING_ART_STYLE_KEYS` + one `only="topo"` shard; `animate.py` is a third six-list; S8 should depend on R4 if `topo` can retire. |
| [I07.md](./I07.md) | Media / contracts / e2e tests | GIF-only; G2 pytest will not prove MP4 pairs or committed byte caps; `ALL_STYLES == LIVING_ART_STYLE_KEYS` is the shrink bomb. |
| [I08.md](./I08.md) | Accretion knobs + A1 leftovers | Clock already maps four channels; unreadability is on-canvas. A3 default no-op; A1/A2 must ignore the overlay, not assert knobs only. |
| [I09.md](./I09.md) | Ink Garden + t0 gate | Live GIF draws a `tree_t≥0.34` stub; A1 empty garden is stale. Dig1: first-repo plant + bloom/trunk/glints (pin `star_velocity`). |
| [I10.md](./I10.md) | Topography + stars/settlements | Stars never enter peak height; contours + central blob dominate; settlements are ~1 px. Dto1: prominence into terrain, visible settlements. |
| [I11.md](./I11.md) | Genetic Landscape + colonies | t0 peak is faint under a 37-dot swarm; colonies are attrs not ink and weld saddles. Dge1: distinct peaks, height=stars, colonies=followers. |
| [I12.md](./I12.md) | Physarum + t0 spore | Live GIF t0 is spore+node, **no veins**. Dph1: network from first repo; tag veins; do not treat the node floor as done. |
| [I13.md](./I13.md) | Lenia + field/extent | CA mix cap 0.34 + residue hide the field; isolation is `data-*` only. Dle1: visible field/extent at 400×400 (1.2 MB cap). |
| [I14.md](./I14.md) | Ferrofluid + dipole clustering | t0 already a tower; same-language x-pack is the leftover. Dfe1: N columns, stop `language_cluster` for x; ≥36 px gap is not towers. |
| [I15.md](./I15.md) | Timelapse render + `_export_mp4` | `render_timelapse --only` is the GEN path (120 / 400 / budgets); MP4 is best-effort ffmpeg; do not use `generate animated`. |
| [I16.md](./I16.md) | Docs / AGENTS exact-six copy | Quota sentences in living-art-modes, root AGENTS, workflows index; `scripts/art/AGENTS.md` + sibling mdx will fail S12 `rg` unless assigned. |
| [I17.md](./I17.md) | GitHub README `<video>` | 2026 evidence: README strips `<video>`; try on `origin/dev` then GIF+in-repo MP4 click; no external host; inner GIF so a strip does not blank art. |
| [I18.md](./I18.md) | Finalize GIF glob vs MP4 block | One art commit, two adds: GIF `:(glob)` (deletions yes) vs `mp4s=(...)` (deletions no, leftovers re-added). Do not unify globs. |
| [I19.md](./I19.md) | OpenSpec growth change | `prevent-living-art-repo-growth` stays untouched; S15 needs unstaged **and** `--cached` / `HEAD` / porcelain / no new commits; leftover `exact-six` there is intended. |
| [I99.md](./I99.md) | Merge / lock assignment | I01–I19 complete; lock corrections assigned; ROS ready with shipped==candidates==six; `main` and OpenSpec growth change untouched. |

Until K2, do not shrink CI, tests, or inventory. After K2, live SSOT is roster + artifacts + tests + `living-art-modes` — **not** the OpenSpec growth folder.
