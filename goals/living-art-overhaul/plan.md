# Plan — living-art-overhaul (v3)

> **Facts:** [`facts.md`](./facts.md) · **Grill:** [`grill-notes.md`](./grill-notes.md)  
> **Task graph:** [`task-graph.json`](./task-graph.json) (v3, 107 nodes, per-style generate/score/QA, full catalog below)  
> **Ship surface:** `origin/dev` only. Do not update `main`.

---

## Critique of v1

v1 was a nine-step essay. That hid the real work:

- **Exact-six is a contract, not a comment.** It is asserted in `artifacts._validate_canonical_inventory`, `stage_living_art_fleet`, `test_living_art_media.py`, `test_living_art_artifact_handoff.py`, `test_living_art_contracts.py`, `test_living_art_e2e_rehearsal.py`, `test_cli.py`, `test_profile_workflow.py`, `test_overhaul_fact_ids.py`, `test_art_shared_package.py`, `AGENTS.md`, `living-art-modes.mdx`, and the workflow assembler step name. Shrinking to 4–6 is a coordinated contract change, not step 8 as a blob.
- **Six generators are six locks.** Treating “redesign dialects” as one step serializes work that can fan out across `ink_garden.py` … `ferrofluid.py`.
- **`scripts/art/**` is not one lock.** `artifacts.py`, `timelapse.py`, `accretion.py`, and each generator must not share a writer.
- **GitHub README video is likely to fail.** 2026 sources still say profile READMEs do not play `<video>` (issues/PRs can). v1 sounded hopeful. v2 still *tries* native markup on `origin/dev`, then takes the planned GIF + in-repo MP4 click-through. No external host.
- **Finalize treats GIF and MP4 differently.** GIFs go through the `:(glob).github/assets/img/living-*.gif` pathspec; MP4s use a separate `mp4s=(...)` block. Video-primary must not assume one git add covers both.
- **`openspec/changes/prevent-living-art-repo-growth` stays stale on purpose.** Out of scope. Do not edit it. Live contract + tests + `living-art-modes` are the SSOT after shrink.
- **Human bake-off is a hard barrier.** CI must not shrink until `bakeoff.json` `accepted` exists.

---

## Research notes (code + GitHub)

| Finding | Source | Plan consequence |
|---|---|---|
| README assembler is a 360px wrap, no `<details>` | `scripts/readme_sections.py` `_rewrite_living_art_section` | Rewrite; flip `test_living_art_has_no_table_css_grid_or_details` |
| GFM tests *require* six `width="360"` and *forbid* details | `tests/test_readme_gfm_ux.py` | Those tests are the first README contract to replace |
| Matrix already reads `LIVING_ART_STYLE_KEYS` | `profile-updater.yml` prepare job | After roster split, shrinking the tuple shrinks CI |
| `max-parallel: 6` is hardcoded | same workflow + `test_profile_workflow.py` | Update with shipped length |
| Inventory function is named/doc’d “exact six” | `artifacts._validate_canonical_inventory` | Change to “exact shipped” |
| CLI `--only` validates against `LIVING_ART_STYLE_KEYS` | `scripts/cli/generate/_common.py` | Candidates stay selectable; default generate = shipped |
| A1: t0 Ink Garden empty, Physarum spore-only, Ferrofluid clustered | `goals/profile-readme-overhaul/inventory/A1-frame-inspection.md` | Those three are the first dialect leaves |
| Published GIFs were never regenerated after A1 | same | GEN wave is mandatory before scoring |
| `<video>` in README still widely reported as stripped (2026) | GitHub community #173635, RepoClip 2026, GfG | Expect fallback; still do V2 on github.com |
| OpenSpec growth change still says exact-six fan-in | `openspec/changes/prevent-living-art-repo-growth/**` | Leave it; S15 asserts no diff there |

---

## Parallel teams

| Team | Lock(s) | Parallel with |
|---|---|---|
| INV | none (read) | I01–I19 |
| ROS | `L-ROS` → `L-ARTF` / `L-TL` / `L-CLI` | after I99 |
| RM | `L-ROS` (legends) → `L-RS` → `L-README` → `L-T-GFM` | ACC after W1M |
| ACC | `L-T-ACC` then `L-ACC` | RM |
| DIG…DFE | `L-IG` … `L-FE` | all six `D*1` after A3 |
| VID | `L-VID` then maybe `L-RS` | GEN after M6 / P0 |
| GEN | `L-ASSETS` | VID |
| BAK | `L-BAKE` | **human gate K2** |
| SHR | one test/docs file each (`L-T-*`, `L-DOCS-*`, `L-WF`) | S4–S12 after S2 |
| CAP | `L-GIT` | after W4M |

Same-file edits stay sequential. `D*2` all want `tests/test_art_shared_package.py` — they **serialize** on `L-T-ACC` (or collapse into one greening pass after all `D*1`). Stills (`D*3`) have no shared lock and fan out.

---

## Solution approach

Keep the shared daily spine. Split **candidates** (today’s six generators) from **shipped** (what README + CI publish). Redesign all six pictures so t0 is not empty and each of repos / stars / commits / followers moves the art. Rebuild Living Art as a full-width stack: clock sentence, visible artwork, per-piece `<details>` legend.

Emit native `<video>` once, check github.com on `dev`, then keep that form **or** fall back to GIF + MP4 click. Score, you veto, then shrink every live contract to the accepted 4–6.

Until K2, shipped == candidates == six, so existing exact-six tests stay green.

---

## Waves (see task-graph.json)

### Wave I — inventory (I01–I19, then I99)

Read-only. One explore agent per node. Merge at I99 before any write.

### Wave ROS — roster split (R1–R5 → W1M)

Add `scripts/art/roster.py`:

- `CANDIDATE_STYLE_KEYS` — generator registry / `--only`
- `SHIPPED_STYLE_KEYS` — README, CI matrix, byte budgets, docs
- legend copy: title, metaphor, four-signal mapping

Point `LIVING_ART_STYLE_KEYS` at shipped. Keep `_STYLE_REGISTRY` as candidates. Do not delete generators.

**Verify:** still six shipped; `uv run python -m pytest -q tests/test_living_art_media.py tests/test_art_shared_package.py tests/test_overhaul_fact_ids.py`.

### Wave RM + ACC (parallel after W1M)

**RM (M1–M6):** legends → `_rewrite_living_art_section` → regenerate README → replace GFM wrap tests → intro/dropdown/host tests → both media forms legal.

**ACC (A1–A3):** red tests for four-channel knob motion and t0 primary marks; shared `accretion.py` only if the clock itself must change.

**Verify:**

```bash
uv run readme generate readme-sections
uv run python -m pytest -q tests/test_readme_gfm_ux.py -k living_art
```

### Wave DIAL — six styles (Dig1…Dfe4)

| ID | File | Job |
|---|---|---|
| Dig* | `ink_garden.py` | Plants from first repo; bloom/trunk/glints = stars/commits/followers |
| Dto* | `topography.py` | Stars as readable peaks; followers as settlements |
| Dge* | `genetic_landscape.py` | Peaks = repos; height = stars; generations = commits; colonies = followers |
| Dph* | `physarum.py` | Network from first repo; not spore-only at t0 |
| Dle* | `lenia.py` | Field/extent readable without the caption |
| Dfe* | `ferrofluid.py` | Distinct towers; no collapsed same-language dipoles |

`D*1` + `D*4` own the generator. `D*3` stills are independent files. `D*2` serialize on the shared test module.

### Wave VID + GEN (after M6 / W2M)

- P0: push presentation to `origin/dev` (this goal’s ship branch).
- V2–V4: github.com check; write `video-check.md`; switch to GIF+click if stripped.
- G1–G3: render six GIF+MP4 pairs under current 120 / 400 / budget contract; contact sheet.

**Verify:** `tests/test_living_art_media.py`. No YouTube/Cloudinary.

### Wave BAK — score + veto (K1–K3)

Four equal axes. Propose 4–6. **You write `accepted`.** K3 asserts README keys == `accepted` (red until S14).

### Wave SHR — contract shrink (S1–S15 → W4M)

S1 set shipped. S2 budgets/inventory. S3 workflow comments + `max-parallel`. S4–S10 each test module on its own lock. S11–S12 docs (`living-art-modes`, `AGENTS.md`, workflows index). S13 remove retired `living-*` assets. S14 regenerate README. S15 prove OpenSpec growth change untouched.

**Verify:**

```bash
rg -n "exact-six|exact six|all six" scripts tests docs/content/docs/scripts/living-art-modes.mdx AGENTS.md .github/workflows/profile-updater.yml
uv run python -m pytest -q tests/test_living_art_media.py tests/test_living_art_artifact_handoff.py tests/test_living_art_contracts.py tests/test_living_art_e2e_rehearsal.py tests/test_cli.py tests/test_profile_workflow.py tests/test_readme_gfm_ux.py -k 'living or Living'
```

### Wave CAP — origin/dev (C1–C4)

Review, push `dev` only, manual light/dark + learnable-growth QA, close.

---

## Fact → graph

| Fact | Nodes | Auto? |
|---|---|---|
| fact-goal / fact-ship-dev | C2–C4 | no |
| fact-count | M4, S14, K3 | yes |
| fact-candidates | R1, K2 | no |
| fact-intro / full-width / visible-art / per-piece-details / dropdown-copy | M2–M5 | yes |
| fact-video-primary / fallback | M6, V2–V4 | yes (markup); play is V2 |
| fact-one-look | D*4, C3 | no |
| fact-frame-t / encoding | A1–A3, D*1–D*2 | yes |
| fact-learnable | C3 | no |
| fact-bakeoff | K1–K3 | yes (`bakeoff.json`) |
| fact-ci-roster | S1–S10, S13 | yes |
| fact-docs-contract | S11–S12 | yes |
| fact-out-scope | S15, C2 | no |

---

## Risks

- **`<video>` will probably be stripped.** Planned fallback. Not a failed goal.
- **D\*2 lock pile-up** on `test_art_shared_package.py`. Prefer one greening agent after all `D*1`, or a strict queue.
- **GEN is expensive.** Stay inside `LIVING_ART_BYTE_BUDGETS`. Do not open repo-growth.
- **Stale OpenSpec.** Historical “exact-six” remains in `prevent-living-art-repo-growth`. Live code must not wait on that change.
- **Early P0 push** publishes a six-piece stack before the jury. That is allowed (`dev` only) and required for the video check.
- **Retired assets** left in `.github/assets/img` will fail exact-directory inventory after S2. S13 is required.

---

## Open questions

None that block execution. Video form is V2, not another grill. Shipped set is K2, not guessed here.

## Task graph catalog (v3, 107 nodes)

Machine-readable copy: [`task-graph.json`](./task-graph.json).

| ID | Lane | Lock | Deps | Title |
|---|---|---|---|---|
| `I01` | INV | `—` | — | Map README _rewrite_living_art_section + GFM living-art tests |
| `I02` | INV | `—` | — | Map ALL_STYLES / LIVING_ART_STYLE_KEYS / STYLE_DIALECTS / CLI style picker |
| `I03` | INV | `—` | — | Map artifacts inventory/stage/publish/byte budgets |
| `I04` | INV | `—` | — | Map workflow prepare/generate/assemble/finalize living-art |
| `I05` | INV | `—` | — | Map test_profile_workflow + artifact_handoff exact-six assertions |
| `I06` | INV | `—` | — | Map test_cli living-art matrix |
| `I07` | INV | `—` | — | Map test_living_art_media/contracts/e2e rehearsal |
| `I08` | INV | `—` | — | Map accretion knobs + A1 unreadability leftovers |
| `I09` | INV | `—` | — | Map ink_garden generate + t0 maturity gate |
| `I10` | INV | `—` | — | Map topography generate + settlement/stars |
| `I11` | INV | `—` | — | Map genetic_landscape generate + colonies |
| `I12` | INV | `—` | — | Map physarum generate + t0 spore path |
| `I13` | INV | `—` | — | Map lenia generate + field/extent |
| `I14` | INV | `—` | — | Map ferrofluid generate + dipole clustering |
| `I15` | INV | `—` | — | Map timelapse render + _export_mp4 + published frame contract |
| `I16` | INV | `—` | — | Map living-art-modes + AGENTS + workflows docs exact-six copy |
| `I17` | INV | `—` | — | Record GitHub README video constraint (try then GIF fallback) |
| `I18` | INV | `—` | — | Map finalize GIF pathspec vs MP4 commit block |
| `I19` | INV | `—` | — | Confirm openspec prevent-living-art-repo-growth stays untouched |
| `I99` | CAP | `—` | I01,I02,I03,I04,I05,I06,I07,I08,I09,I10,I11,I12,I13,I14,I15,I16,I17,I18,I19 | Inventory merge / lock assignment |
| `R1` | ROS | `L-ROS` | I02,I99 | Add roster.py: CANDIDATE_STYLE_KEYS vs SHIPPED_STYLE_KEYS + legend copy |
| `R2` | ROS | `L-ARTF` | R1 | Point artifacts LIVING_ART_STYLE_KEYS / budgets / labels at SHIPPED |
| `R3` | ROS | `L-TL` | R1 | Keep _STYLE_REGISTRY as candidate generators; document vs SHIPPED |
| `R4` | ROS | `L-CLI` | R2 | CLI style picker uses CANDIDATE for --only, default generate uses SHIPPED |
| `R5` | TST | `L-T-MEDIA` | R2,R3,R4 | Relax ALL_STYLES == LIVING_ART_STYLE_KEYS only where shipped==candidates |
| `W1M` | CAP | `—` | R5 | Roster split accepted; shipped still six |
| `M1` | RM | `L-ROS` | W1M,I01 | Fill per-style legend copy (title, 1-2s metaphor, four-signal mapping) |
| `M2` | RM | `L-RS` | M1,I17 | Rewrite Living Art: intro + full-width stack + video-or-fallback + details |
| `M3` | RM | `L-README` | M2 | Regenerate README Living Art section |
| `M4` | RM | `L-T-GFM` | M3 | Replace wrap/360/no-details GFM tests with stack/details/count facts |
| `M5` | RM | `L-T-GFM` | M4 | Add intro-has-no-spine-list + dropdown-copy + no-external-host tests |
| `M6` | RM | `L-T-GFM` | M5 | Allow both <video src=mp4> and GIF+href MP4 as legal README forms |
| `A1` | ACC | `L-T-ACC` | W1M,I08 | Red tests: each dialect knob moves when each of 4 channels increases |
| `A2` | ACC | `L-T-ACC` | A1 | Red tests: t0 frame contains style primary mark (not empty field) |
| `A3` | ACC | `L-ACC` | A2 | Adjust shared knobs/ceilings only if all six need the same clock change |
| `Dig1` | DIG | `L-IG` | A3,I09 | Ink Garden: redesign on-canvas dialect (t0 garden empty — plants from first repo) |
| `Dig2` | DIG | `L-T-ACC` | Dig1 | Ink Garden: make t0 + channel isolation tests green |
| `Dig3` | DIG | `—` | Dig1 | Ink Garden: export t0/t1/t2 stills for bake-off |
| `Dig4` | DIG | `L-IG` | Dig1 | Ink Garden: one look contrast for GitHub light and dark |
| `Dto1` | DTO | `L-TO` | A3,I10 | Topography: redesign on-canvas dialect (stars weaker than contours — readable peaks) |
| `Dto2` | DTO | `L-T-ACC` | Dto1 | Topography: make t0 + channel isolation tests green |
| `Dto3` | DTO | `—` | Dto1 | Topography: export t0/t1/t2 stills for bake-off |
| `Dto4` | DTO | `L-TO` | Dto1 | Topography: one look contrast for GitHub light and dark |
| `Dge1` | DGE | `L-GE` | A3,I11 | Genetic Landscape: redesign on-canvas dialect (keep distinct peaks; colonies=followers) |
| `Dge2` | DGE | `L-T-ACC` | Dge1 | Genetic Landscape: make t0 + channel isolation tests green |
| `Dge3` | DGE | `—` | Dge1 | Genetic Landscape: export t0/t1/t2 stills for bake-off |
| `Dge4` | DGE | `L-GE` | Dge1 | Genetic Landscape: one look contrast for GitHub light and dark |
| `Dph1` | DPH | `L-PH` | A3,I12 | Physarum: redesign on-canvas dialect (t0 spore-only — network from first repo) |
| `Dph2` | DPH | `L-T-ACC` | Dph1 | Physarum: make t0 + channel isolation tests green |
| `Dph3` | DPH | `—` | Dph1 | Physarum: export t0/t1/t2 stills for bake-off |
| `Dph4` | DPH | `L-PH` | Dph1 | Physarum: one look contrast for GitHub light and dark |
| `Dle1` | DLE | `L-LE` | A3,I13 | Lenia: redesign on-canvas dialect (field/extent readable without caption) |
| `Dle2` | DLE | `L-T-ACC` | Dle1 | Lenia: make t0 + channel isolation tests green |
| `Dle3` | DLE | `—` | Dle1 | Lenia: export t0/t1/t2 stills for bake-off |
| `Dle4` | DLE | `L-LE` | Dle1 | Lenia: one look contrast for GitHub light and dark |
| `Dfe1` | DFE | `L-FE` | A3,I14 | Ferrofluid: redesign on-canvas dialect (break dipole clustering; towers per repo) |
| `Dfe2` | DFE | `L-T-ACC` | Dfe1 | Ferrofluid: make t0 + channel isolation tests green |
| `Dfe3` | DFE | `—` | Dfe1 | Ferrofluid: export t0/t1/t2 stills for bake-off |
| `Dfe4` | DFE | `L-FE` | Dfe1 | Ferrofluid: one look contrast for GitHub light and dark |
| `W2M` | CAP | `—` | M6,A3,Dig2,Dto2,Dge2,Dph2,Dle2,Dfe2,Dig3,Dto3,Dge3,Dph3,Dle3,Dfe3,Dig4,Dto4,Dge4,Dph4,Dle4,Dfe4 | README stack + six redesigned dialects ready |
| `V1` | VID | `L-VID` | M3,I17 | Write video-check.md template + expected GitHub strip outcome |
| `P0` | CAP | `L-GIT` | M6 | Push README presentation to origin/dev for the video check |
| `V2` | VID | `—` | P0,V1 | Check github.com origin/dev README: does <video> play/autoplay? |
| `V3` | VID | `L-VID` | V2 | Write video-check.md result |
| `V4` | VID | `L-RS` | V3 | If stripped, switch assembler to visible GIF + obvious MP4 click |
| `G1ig` | GEN | `L-ASSET-IG` | W2M,I15 | Render living-inkgarden.gif + .mp4 only |
| `G1to` | GEN | `L-ASSET-TO` | W2M,I15 | Render living-topo.gif + .mp4 only |
| `G1ge` | GEN | `L-ASSET-GE` | W2M,I15 | Render living-genetic.gif + .mp4 only |
| `G1ph` | GEN | `L-ASSET-PH` | W2M,I15 | Render living-physarum.gif + .mp4 only |
| `G1le` | GEN | `L-ASSET-LE` | W2M,I15 | Render living-lenia.gif + .mp4 only |
| `G1fe` | GEN | `L-ASSET-FE` | W2M,I15 | Render living-ferrofluid.gif + .mp4 only |
| `G1` | GEN | `—` | G1ig,G1to,G1ge,G1ph,G1le,G1fe | All six candidate GIF+MP4 pairs exist |
| `G2` | GEN | `L-T-MEDIA` | G1 | Validate regenerated fleet against byte budgets and inventory |
| `G3` | GEN | `—` | G1 | Build GIF contact sheet (first/mid/last frame) for bake-off |
| `W3M` | CAP | `—` | V4,G2,G3 | Media + video form frozen; ready to score |
| `K1ig` | BAK | `—` | W3M | Score inkgarden on striking/growth/distinct/GitHub-fit |
| `K1to` | BAK | `—` | W3M | Score topo on striking/growth/distinct/GitHub-fit |
| `K1ge` | BAK | `—` | W3M | Score genetic on striking/growth/distinct/GitHub-fit |
| `K1ph` | BAK | `—` | W3M | Score physarum on striking/growth/distinct/GitHub-fit |
| `K1le` | BAK | `—` | W3M | Score lenia on striking/growth/distinct/GitHub-fit |
| `K1fe` | BAK | `—` | W3M | Score ferrofluid on striking/growth/distinct/GitHub-fit |
| `K1` | BAK | `L-BAKE` | K1ig,K1to,K1ge,K1ph,K1le,K1fe | Merge scores; propose 4-6 in bakeoff.json |
| `K2` | BAK | `L-BAKE` | K1 | HUMAN GATE: veto/override; write accepted[] |
| `K3` | BAK | `L-T-GFM` | K2 | Test: README shipped keys == bakeoff accepted (red until shrink) |
| `S1` | SHR | `L-ROS` | K2 | Set SHIPPED_STYLE_KEYS = bakeoff accepted |
| `S2` | SHR | `L-ARTF` | S1 | Drop retired byte budgets; inventory expects SHIPPED names only |
| `S3` | SHR | `L-WF` | S2 | Rename exact-six comments; max-parallel may equal len(shipped) |
| `S4` | SHR | `L-T-MEDIA` | S2 | Rewrite exact-six media tests to exact-shipped |
| `S5` | SHR | `L-T-HAND` | S2 | Rewrite artifact handoff exact-six tests |
| `S6` | SHR | `L-T-CON` | S2 | Rewrite living-art contracts tests to shipped roster |
| `S7` | SHR | `L-T-E2E` | S2 | Rewrite e2e rehearsal counts to len(SHIPPED) |
| `S8` | SHR | `L-T-CLI` | S2 | Rewrite test_cli living-art loops to SHIPPED |
| `S9` | SHR | `L-T-WF` | S3 | Update test_profile_workflow exact-six handoff wording |
| `S10` | SHR | `L-T-IDS` | S1 | Update overhaul fact-id + shared-package ALL_STYLES assertions |
| `S11` | SHR | `L-DOCS-MODES` | S1,M1 | living-art-modes.mdx matches shipped names/files/legends |
| `S12` | SHR | `L-DOCS-WF` | S3 | AGENTS.md + workflows docs: matrix follows SHIPPED, not 'six' |
| `S13` | SHR | `L-ASSETS` | S1 | Stop generating retired living-*.gif/mp4; remove from img if present |
| `S14` | SHR | `L-README` | S1,V4 | Regenerate README from SHIPPED roster so K3 goes green |
| `S15` | SHR | `—` | S12 | Confirm openspec prevent-living-art-repo-growth was not edited |
| `W4M` | CAP | `—` | S4,S5,S6,S7,S8,S9,S10,S11,S12,S13,S14,S15,K3 | Shipped roster contracted everywhere that matters |
| `C1` | CAP | `—` | W4M | Review README + roster + dialect diffs |
| `C2` | CAP | `L-GIT` | C1 | Push origin/dev only; do not touch main |
| `C3L` | CAP | `—` | C2 | Manual QA GitHub light mode on origin/dev Living Art |
| `C3D` | CAP | `—` | C2 | Manual QA GitHub dark mode on origin/dev Living Art |
| `C3X` | CAP | `—` | C2 | Manual QA: each details opens; legend matches the picture |
| `C3` | CAP | `—` | C3L,C3D,C3X | Manual fact-one-look + fact-learnable signed |
| `C4` | CAP | `—` | C3 | Close goal: facts.md all evidenced |
