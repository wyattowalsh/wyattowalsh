# Wave BAK + SHR + CAP — bake-off, contract shrink, origin/`dev`

**Lanes:** BAK (`K1*`–`K3`) → SHR (`S1`–`S15` → `W4M`) → CAP (`C1`–`C4`).
**This file is the execution playbook.** Inventory evidence: [`../inventory/I99.md`](../inventory/I99.md) (lock corrections SSOT), I03–I07, I16–I19, [`../plan.md`](../plan.md), [`../task-graph.json`](../task-graph.json) v3.
**No production edits while authoring this playbook.** Implementers own BAK/SHR/CAP later. Do not start ROS/DIAL/RM/GEN from this file. Do not patch `task-graph.json` here (record I99 overrides; a later graph patch applies them).

**Ship surface:** `origin/dev` only. **`main` is untouched by this goal.** OpenSpec `openspec/changes/prevent-living-art-repo-growth/**` is untouched (I19 / S15).

Until K2, **shipped == candidates == six**. Exact-six tests stay green. After a **human** `bakeoff.json` `accepted[]`, live surfaces shrink to 4–6. CI must not shrink before that write.

---

## Hard gates (read first)

| Gate | Rule | Who |
|---|---|---|
| **K2 human `accepted[]`** | Agents **must not** invent, copy `proposed` into, or otherwise write `accepted[]`. If the key is missing, **stop**. Do not start S1. | Human only (`L-BAKE`) |
| **S5 deps += S3** | Graph today is `S5.deps = [S2]` only. **I99 override:** wait for S3. `STAGE_STEP` is the YAML `name:`. | SHR |
| **S8 deps += R4** | Graph today is `S8.deps = [S2]` only. **I99 override:** wait for R4. Keep `only="topo"` as a **candidate** shard. | SHR |
| **S13 `git rm` GIF + MP4** | Delete **both** `living-{retired}.gif` and `.mp4`. Finalize will **re-commit** leftover MP4s (I03, I18). | SHR |
| **S15 full git checks** | Empty unstaged `git diff` is **not** enough. Unstaged + cached + `HEAD` + porcelain + no new commits on the OpenSpec path. | SHR (read-only) |
| **`origin/dev` only** | P0 / C2 push `dev`. Never `main`. Never restore `main` workflow triggers. | CAP |

Loop guard: never use commit message `art: regenerate living-art assets` (I99 `L-GIT`).

---

## I99 overrides vs `task-graph.json` v3

Graph on disk is **wrong or incomplete** for these rows. This playbook is the execution SSOT until a later JSON patch. **Do not apply these as production edits in this authoring node.**

| Node | Graph today | I99 assign | Why |
|---|---|---|---|
| **K2** | write `accepted[]` (`agent: cap`) | **Human gate.** Agent proposes in K1 only. No invented `accepted[]`. | `plan.md:19`; facts bake-off; grill “You may veto or override” |
| **S5** | `deps: [S2]`, parallel `SHR-T` vs S3 | **`deps: [S2, S3]`** | `STAGE_STEP` == YAML `name:` `Stage exact-six living-art artifact` |
| **S8** | `deps: [S2]` | **`deps: [S2, R4]`** | `only="topo"` reds if S1 retires `topo` before the picker splits |
| **S13** | “remove from img if present”; verify stems == SHIPPED | **`git rm` GIF and MP4** for each retired stem; verify **both** extensions | Finalize `mp4s=(...)` re-adds leftovers; glob does not stage MP4 deletions |
| **S15** | `git diff -- openspec/… empty` | **Five required checks** (below) | Unstaged-only misses staged edits and goal-era commits |
| **S11 `files[]`** | `living-art-modes.mdx` only | **+** `ink-garden.mdx`, `topography.mdx`, `world-state.mdx` | Sibling “six-style fleet” fails S12 `rg` |
| **S12 `files[]`** | root `AGENTS.md` + `workflows/index.mdx` | **+** `scripts/art/AGENTS.md` | Live agent “exact-six, media-only workflow handoff” |
| **S9** | `pytest … -k living_art` | Expand verify; **do not** restore wrap/360/no-details | Wrap invert is **M4** (Wave RM), not S9 |
| **K3** | red until S14 | Keep; README keys == `accepted` | S14 regen is `L-README`; V4 is assembler-only (`L-RS`) |
| **W4M `rg`** | plan omits `workflows/index.mdx` | **Include** `docs/content/docs/workflows/index.mdx` | I16 / I99 |

Same-file writers stay sequential. `L-T-MEDIA` is **R5 → G2 → S4** (never parallel). `L-T-GFM` is M4–M6 then **K3** (after K2). `L-README` is M3 then **S14**. `L-ROS` is R1 → M1 → **S1**.

---

## Preconditions

Waves BAK/SHR/CAP start only after **W3M** (media + video form frozen): V4 done, G2 committed-fleet + MP4 presence (I99 correction 7), G3 contact sheet.

Also required before shrink (not this file’s job, but S1/S8 will red without them):

- **R1–R5 / W1M** — roster split; until K2, `SHIPPED == CANDIDATE ==` six.
- **R4** — `--only` ∈ `CANDIDATE_STYLE_KEYS`; default generate = `SHIPPED`; refresh iff active == SHIPPED.
- **R5** — gated equality in media / shared-package / fact-ids. **Not** contracts (`:231` → **S6**).
- **M2–M6** — full-width stack; wrap tests inverted in M4 (including `test_readme_sections.py` + workflow piggyback ~1128–1143).
- **V4** — assembler only (`L-RS`). **Do not** put `README.md` on V4. Regen is M3 / S14 (`L-README`).

Do **not** delete generators. Candidates stay selectable after shrink. Docs home showcase / `living-art-preview.html` are not a second gallery. Do not raise `LIVING_ART_BYTE_BUDGETS` (repo-growth is out of scope).

---

## Wave BAK — score + veto (`K1*`–`K3`)

Four equal axes (grill; no CI-cost axis; no extra scientific-accuracy axis): **striking**, **readable growth**, **distinct**, **GitHub-fit**. Scores 1–5. Close scores go to taste. Pretty motion that ignores account growth cannot win (`facts.md`).

### Lock / graph

| ID | Lock | File(s) | Deps | Parallel | Verify |
|---|---|---|---|---|---|
| **K1ig** … **K1fe** | — | `goals/living-art-overhaul/bakeoff/{style}.score.json` | W3M | `K1` (six-way) | four axes 1–5 |
| **K1** | `L-BAKE` | `goals/living-art-overhaul/bakeoff.json` | all K1* | after scores | four axes each; **proposed** length 4–6 |
| **K2** | `L-BAKE` | `bakeoff.json` | K1 | **human** | **`accepted` is 4–6 style keys** written by the human |
| **K3** | `L-T-GFM` | `tests/test_readme_gfm_ux.py` | K2 | before/with S14 | **fails until S14** |

Keys (candidates, order): `inkgarden`, `topo`, `genetic`, `physarum`, `lenia`, `ferrofluid`.

Evidence for scoring (do not re-render GEN in BAK): G3 `bakeoff/gif-sheet.md`; D\*3 stills under `goals/living-art-overhaul/bakeoff/` (not the 2026-08-14 A1 stills — those predate DIAL); published `living-*.gif` / `.mp4` after G1. Isolation tests are not the jury.

### K1\* — per-style scores

Write one JSON per key. Each file has the four axes (1–5 integers) plus a short rationale per axis. Do not pick winners here. Do not write `accepted`.

### K1 — merge + propose

Merge six score files into `bakeoff.json`. **Propose** a 4–6 subset (prefer fewer if a metaphor stays unreadable; never more than six). Record scores and the proposed order.

**Allowed in K1:** `proposed` (or equivalent propose field). **Forbidden in K1:** `accepted[]`. Leave `accepted` absent / empty so K2 is an explicit human write.

### K2 — HUMAN GATE (do not automate)

```text
STOP. This node is not an agent write.

1. Human reads bakeoff.json proposed + scores + contact sheet.
2. Human vetoes / overrides / accepts. Taste breaks ties.
3. Human writes accepted[] = 4–6 keys, each ∈ CANDIDATE_STYLE_KEYS,
   unique, stable order they want on the README stack.
4. Only then may S1 / K3 start.
```

| Agent must not | Human does |
|---|---|
| Fill `accepted` with `proposed` | Write `accepted[]` |
| Invent a “reasonable” 4–6 | Veto or override |
| Start S1 because scores “obviously” drop two styles | Own `fact-candidates` / `fact-bakeoff` |
| Shrink CI, drop budget rows, `git rm` media | Gate the shrink |

If `bakeoff.json` has no human `accepted[]`, **S1 is blocked**. Exact-six stays shipped.

### K3 — README keys == `accepted` (red until S14)

Add a GFM/README assertion: shipped Living Art keys in `README.md` == `bakeoff.json` `accepted`. Expected **red** from K2 until **S14** regenerates the section from `SHIPPED_STYLE_KEYS`. Do not “fix” it by editing README in K3 (`L-README` is S14). Do not restore wrap/360 tests (M4 already inverted).

---

## Wave SHR — contract shrink (`S1`–`S15` → `W4M`)

**S1 set shipped. Nothing else shrinks the live roster.** Matrix children already follow `LIVING_ART_STYLE_KEYS` (I04); after R2+S1, shrinking SHIPPED shrinks CI **without** a 4- or 5-key YAML list. Do **not** hardcode retired-out keys in the workflow.

### Recommended order (I99)

```text
K2 (human accepted[])
 ├─ K3          (red test; L-T-GFM)
 └─ S1          (SHIPPED = accepted; L-ROS)
     ├─ S10     (fact-ids + shared-package; L-T-IDS)          ∥ S11, S13, S14
     ├─ S11     (modes + sibling mdx; L-DOCS-MODES)
     ├─ S13     (git rm gif+mp4; L-ASSETS)                   ∥ S2
     ├─ S14     (README regen; L-README; needs V4)
     └─ S2      (drop retired budgets; L-ARTF)
          ├─ S3 (YAML names + max-parallel; L-WF)
          │    ├─ S5   (handoff STAGE_STEP; L-T-HAND)         **after S3**
          │    ├─ S9   (workflow tests; not wrap; L-T-WF)
          │    └─ S12  (AGENTS + workflows index + art/AGENTS; L-DOCS-WF)
          │         └─ S15 (OpenSpec untouched; full git checks)
          ├─ S4 (media exact-shipped; L-T-MEDIA)
          ├─ S6 (contracts; includes ALL_STYLES vs KEYS; L-T-CON)
          ├─ S7 (e2e len(SHIPPED); --only still candidate; L-T-E2E)
          └─ S8 (CLI loops SHIPPED; only=topo candidate; L-T-CLI)  **after R4**
```

`SHR-T` (S4–S10) and `SHR-DOC` (S11–S12) stay parallel **except** the I99 edges: **S5 after S3**, **S8 after R4**, **S9 after S3**, **S12 after S3**, **S15 after S12**.

S1→S6 red window: `test_living_art_contracts.py:224-231` stays on `L-T-CON` (not R5). Accept red until S6. Do not expand R5 into contracts.

### Per-node briefs

#### S1 — `L-ROS` — `scripts/art/roster.py`

`SHIPPED_STYLE_KEYS = tuple(bakeoff accepted)` (4–6, subset of `CANDIDATE_STYLE_KEYS`, same order as `accepted`). Do not delete candidate keys or generators. Do not invent a roster if `accepted` is missing.

Verify: `len(SHIPPED) in 4..6`; `set(SHIPPED) <= set(CANDIDATE)`.

#### S2 — `L-ARTF` — `scripts/art/artifacts.py`

Drop **retired** budget rows. Inventory / stage / publish follow SHIPPED names. Rewrite “exact six” **Python** docstrings (`artifacts.py` ~314, ~935, ~999). Keep remaining caps. **Do not** delete img files (S13). **Do not** import CANDIDATE into artifacts.

Verify: `_canonical_living_art_names() == shipped gifs`.

#### S3 — `L-WF` — `.github/workflows/profile-updater.yml`

Rename hardcoded strings (I04 / I99 correction 5):

- `max-parallel: 6` (~1046) — may equal `len(SHIPPED)` (4–6, ≤6)
- step `name:` `Stage exact-six living-art artifact` (~1180)
- step `name:` `Summarize exact-six…` (~1205)
- comment “Keep exact-six stage GIF-only” (~1194)

Leave matrix `fromJSON(…outputs.styles)` dynamic. **Do not** hardcode a 4- or 5-key YAML list. **Do not** unify GIF+MP4 globs (I18). Coordinate the stage `name:` with **S5 `STAGE_STEP`**. No compatibility shim for the old name.

Verify: matrix still from `LIVING_ART_STYLE_KEYS`; no hardcoded style-key list.

#### S4 — `L-T-MEDIA` — `tests/test_living_art_media.py`

Rewrite `total_assets == 6` / exact-six names to exact-**shipped**. **Do not** shrink `STYLE_DIALECTS` parametrize to shipped (candidates stay generators). G2 already added committed-fleet + MP4 presence; keep those on shipped stems.

Verify: `uv run python -m pytest -q tests/test_living_art_media.py`

#### S5 — `L-T-HAND` — `tests/test_living_art_artifact_handoff.py` — **deps += S3**

Update `STAGE_STEP` to the **new** YAML `name:` in the same wave as S3. Rename `test_exact_six_gif_artifact_round_trip_…` / stdout `passed: 6 assets` / “six immutable matrix uploads” to shipped. Keep `CANONICAL_NAMES = tuple(sorted(LIVING_ART_BYTE_BUDGETS))` (follows S2). Named-style shard fixtures (`topo` / `lenia`) must be keys that remain **shipped** *or* rewritten to a remaining shipped key — unlike S8’s candidate `only="topo"`.

If S5 runs before S3, lookups for `Stage exact-six living-art artifact` break (I05).

Verify: `uv run python -m pytest -q tests/test_living_art_artifact_handoff.py`

#### S6 — `L-T-CON` — `tests/test_living_art_contracts.py`

Owns `set(ALL_STYLES) == set(KEYS)` (`:224-231`). Split: equality → shipped ⊆ candidates; README/docs loops → SHIPPED; generator parametrize → CANDIDATE.

Verify: `uv run python -m pytest -q tests/test_living_art_contracts.py`

#### S7 — `L-T-E2E` — `tests/test_living_art_e2e_rehearsal.py`

Counts already `len(KEYS)`. `--only` stays candidate (`topo` / `inkgarden`).

Verify: `uv run python -m pytest -q tests/test_living_art_e2e_rehearsal.py`

#### S8 — `L-T-CLI` — `tests/test_cli.py` — **deps += R4**

Default-fleet loops stay on `LIVING_ART_STYLE_KEYS` (SHIPPED after R2+S1). **Keep `only="topo"` as candidate-shard coverage** (CI / G1 pattern). Do **not** rewrite it to “first shipped key.” Add an explicit unknown-`--only` exit 1 **in this file** (unlocked `tests/test_service_cli_coverage.py:423-424` is insufficient; I99 pick: S8 owns the assert).

If S1 retires `topo` before R4, this file reds on the partial-generate test. That is why **S8 waits on R4**.

Verify: `uv run python -m pytest -q tests/test_cli.py -k living` **and** the unknown-style case.

#### S9 — `L-T-WF` — `tests/test_profile_workflow.py`

After S3. Update `max-parallel`, job/step wording, GIF `:(glob)` vs MP4 `mp4s=(...)`. **Forbid** `:(glob)…living-*.mp4` (I18). **Must not** restore wrap/360/no-details (M4). Expand verify past `-k living_art` so `test_finalize_applies_waka_before_readme_sections` (~1120) is included (waka-order + any remaining stack asserts).

Verify: `uv run python -m pytest -q tests/test_profile_workflow.py -k living_art` **plus** the finalize/waka-order test.

#### S10 — `L-T-IDS` — `tests/test_overhaul_fact_ids.py` (+ listed `test_art_shared_package.py`)

Candidates may exceed shipped. Spine still monotonic. Serialize vs leftover R5/D\*2 writers if those locks are somehow still hot (they should be done before BAK).

#### S11 — `L-DOCS-MODES` — **I99 extra files**

- `docs/content/docs/scripts/living-art-modes.mdx`
- `docs/content/docs/scripts/ink-garden.mdx`
- `docs/content/docs/scripts/topography.mdx`
- `docs/content/docs/scripts/world-state.mdx`

After S1 + M1. Quota → shipped; legends from M1. Sibling “six-style fleet” / “six generators” otherwise fail S12 `rg`. CLI `--only` six-key list in `docs/content/docs/cli/generate.mdx` is **candidate CLI** (leave as candidates after R4; not a hyphenated `exact-six` hit).

Do not restyle `living-art-preview.html` or docs home showcase.

#### S12 — `L-DOCS-WF` — **I99 extra file**

- `AGENTS.md`
- `docs/content/docs/workflows/index.mdx`
- `scripts/art/AGENTS.md`

After S3. Matrix follows SHIPPED, not “six.” Live YAML is `dev` only; **do not restore `main` triggers** (`AGENTS.md` may still say push to `main`/`master`/`dev` — S12 fixes copy). S2 still owns `artifacts.py` docstrings; S12 owns agent copy. **Do not** “fix” OpenSpec to silence `rg`.

Extend W4M `rg` to `docs/content/docs/workflows/index.mdx`.

#### S13 — `L-ASSETS` — **`git rm` GIF and MP4**

Retired stems = `CANDIDATE_STYLE_KEYS` minus `SHIPPED_STYLE_KEYS`. For each retired stem:

```bash
git rm -- \
  ".github/assets/img/living-${STEM}.gif" \
  ".github/assets/img/living-${STEM}.mp4"
```

| Must | Must not |
|---|---|
| Delete **both** extensions for every retired stem | GIF-only delete (finalize re-commits MP4s) |
| Verify img GIF stems **and** MP4 stems == SHIPPED | Wait for finalize / publish extra-GIF unlink |
| Confirm showcase GIF stems == SHIPPED (no MP4s there today) | `git add :(glob)…living-*.mp4` |
| Human `git rm` so the index records deletions | Rely on bash glob `mp4s=(living-*.mp4)` (absent files are not staged as deletes) |

S2 without S13: leftover `living-*.gif` fail inventory. S13 GIF-only: leftover `living-*.mp4` re-added (`profile-updater.yml` ~1580–1585). Video-primary **keeps** the `mp4s` block; unifying globs fails S9.

Do not touch featured-project assets. Do not restyle showcase HTML.

Verify: `img living-*` stems == SHIPPED for **gif and mp4**.

#### S14 — `L-README` — `README.md`

`uv run readme generate readme-sections` (or the living-art slice) so the stack lists **SHIPPED** only. Greens K3. V4 must already have switched the assembler if github.com stripped `<video>` — still the **new** stack, not a return to 360 wrap.

Verify: `uv run python -m pytest -q tests/test_readme_gfm_ux.py -k living_art`

#### S15 — read-only — **full git checks** (I19 / I99)

Deps: **S12**. Lock: none. Prove `openspec/changes/prevent-living-art-repo-growth` was not edited. Leftover `rg exact-six` **inside that folder is intended**. Do not archive, reformat, or retune budgets there.

Task-graph verify (`git diff -- path` unstaged-only) is **necessary but not sufficient**.

Run from repo root. **All must be empty / print nothing:**

```bash
git diff -- openspec/changes/prevent-living-art-repo-growth
git diff --cached -- openspec/changes/prevent-living-art-repo-growth
git diff HEAD -- openspec/changes/prevent-living-art-repo-growth
git status --porcelain=v1 -uall -- openspec/changes/prevent-living-art-repo-growth
git log --oneline 2c21731be4716df7d376714db6ea6d7395a55881..HEAD \
  -- openspec/changes/prevent-living-art-repo-growth
```

I19 extras (also empty / identical):

```bash
git diff ceb6861d8be691d0da4c2009a05c4897e6ca6726 HEAD \
  -- openspec/changes/prevent-living-art-repo-growth
git ls-tree -r HEAD -- openspec/changes/prevent-living-art-repo-growth
```

Blob fingerprints must match I19 (`I19.md` table). I19 `HEAD` baseline: `2c21731be`; last historical touch: `ceb6861d8` (2026-08-13).

**Do not on S15:** edit/archive OpenSpec; `openspec archive prevent-living-art-repo-growth`; “update the spec to 4–6” so repo-wide grep is quiet.

---

## W4M — shipped roster contracted

Merge: S4, S5, S6, S7, S8, S9, S10, S11, S12, S13, S14, S15, K3.

```bash
rg -n "exact-six|exact six|all six" \
  scripts tests \
  docs/content/docs/scripts/living-art-modes.mdx \
  docs/content/docs/scripts/ink-garden.mdx \
  docs/content/docs/scripts/topography.mdx \
  docs/content/docs/scripts/world-state.mdx \
  AGENTS.md \
  docs/content/docs/workflows/index.mdx \
  .github/workflows/profile-updater.yml

uv run python -m pytest -q \
  tests/test_living_art_media.py \
  tests/test_living_art_artifact_handoff.py \
  tests/test_living_art_contracts.py \
  tests/test_living_art_e2e_rehearsal.py \
  tests/test_cli.py \
  tests/test_profile_workflow.py \
  tests/test_readme_gfm_ux.py \
  -k 'living or Living'
```

Expected leftover `exact-six` **only** under `openspec/changes/prevent-living-art-repo-growth` (and goal/inventory history if those paths are grepped). Live code + tests + `living-art-modes` are the SSOT.

Candidate `--only` lists and generator module maps may still name all six **candidates**. That is not a quota hit if they are not hyphenated `exact-six` / “all six shipped.”

---

## Wave CAP — origin/`dev` (`C1`–`C4`)

| ID | Lock | Deps | Job |
|---|---|---|---|
| **C1** | — | W4M | Review README + roster + dialect diffs |
| **C2** | `L-GIT` | C1 | **Push `origin/dev` only. Do not touch `main`.** |
| **C3L** / **C3D** / **C3X** | — | C2 | Parallel: GitHub light, dark, each `<details>` + legend vs picture |
| **C3** | — | C3L, C3D, C3X | Sign `fact-one-look` + `fact-learnable` |
| **C4** | — | C3 | Close goal: `facts.md` evidenced; `goal.md` done condition |

### C2 — `origin/dev` only

Live workflow: `on.push.branches: [dev]` only (`profile-updater.yml:13-15`). Finalize push errors unless `TARGET_BRANCH == "dev"` (`:1625-1627`). Tests: `test_fact_ship_dev_main_is_not_a_publication_target`.

| Must | Must not |
|---|---|
| Push the goal’s Living Art + roster + tests + docs to **`dev`** | Update `main` / `master` |
| Keep banner jobs **reading** `origin/main` pinned banners (unrelated, read-only) | Restore `main` as a living-art publish trigger |
| Human `git rm` already done in S13 | Rely on finalize to drop retired MP4s |
| Avoid message `art: regenerate living-art assets` | Force-push `main` |

C2 still must not touch `main` while attaching S15 empty diffs to close-out.

### C3 — manual QA on github.com `dev` README

Light + dark: one look per shipped style (no dual `-dark` GIF unless a bake-off piece was unreadable). Each piece: artwork visible (not inside `<details>`); dropdown opens; legend matches the picture (repos / stars / commits / followers). Click each MP4 if the ship form is GIF+href. No YouTube / Cloudinary / `user-images.githubusercontent.com` / `github.com/*/assets/`.

Fail-closing MP4 encode is a VID/S3 choice that must **not** introduce `:(glob)…mp4` without rewriting S9.

### C4 — close

Every accepted fact in `facts.md` holds on the origin/`dev` README preview. `automatedVerification: true` facts have checks. OpenSpec growth change still untouched. `main` unchanged.

---

## Do not (all three waves)

- Invent `bakeoff.json` `accepted[]`
- Shrink CI / inventory / README before K2
- Edit `openspec/changes/prevent-living-art-repo-growth/**`
- Touch `main`
- Unify finalize GIF pathspec with MP4 `mp4s=(...)` glob
- Put `README.md` on V4; S9 restoring wrap/360; S8 rewriting `only="topo"` to first shipped key
- Raise byte budgets (repo-growth)
- Redesign docs showcase / `living-art-preview.html`
- Delete generator modules or `CANDIDATE_STYLE_KEYS`
- Use `generate animated` / `animate.py` for published `living-*` (GEN already used `render_timelapse`)
- Production-edit this authoring node

---

## Finding

BAK scores six candidates, **you** write `accepted[]` (4–6), then SHR retargets live roster/tests/docs/CI/assets, then CAP ships **`origin/dev` only**. I99 sequencing that the graph still lacks: **S5 after S3**, **S8 after R4**, **S13 `git rm` gif+mp4**, **S15 full git checks**. OpenSpec growth change and `main` stay untouched.
