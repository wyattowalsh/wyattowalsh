# Wave RM — README stack (`M1`–`M6`)

**Lane:** RM. **Surface:** origin/`dev` Living Art section (not `main`).
**This file is the execution playbook.** Inventory evidence: [`../inventory/I01.md`](../inventory/I01.md), [`../inventory/I17.md`](../inventory/I17.md), [`../inventory/I99.md`](../inventory/I99.md) (lock corrections 1, 10, 11). Facts: intro / full-width / visible-art / per-piece-details / dropdown-copy / video-primary / video-fallback.
**No production edits while authoring this playbook.** Implementers own `M1`–`M6` later. Do not edit `scripts/`, `tests/`, `README.md`, or `task-graph.json` from this node.

README `<details>` legends here are **not** the on-SVG `#accretion-dialect` caption (Wave DIAL). Overlay ticks must not become dropdown copy.

Until K2, shipped == candidates == six. Do not shrink CI, drop styles, or treat bake-off `accepted` as known. M4–M6 assert `len(SHIPPED)` with cap 6, not a hardcoded six-name list (K3 later equals `bakeoff.json`).

ACC (`A1`–`A3`) is **parallel** after W1M (`parallelGroup: RM-ACC`). RM does not wait on dialects. GEN / VID / P0 are **after** M6 (V1 may start after M3).

---

## Lock / graph

Graph SSOT today still lists M4 files as `tests/test_readme_gfm_ux.py` only. **I99 execution truth** expands that. Same-file writers stay sequential.

| ID | Lock | File(s) | Deps | Parallel | Verify |
|---|---|---|---|---|---|
| **M1** | `L-ROS` | `scripts/art/roster.py` | W1M, I01 | after W1M; serialize vs leftover ROS on this file | each of six has title + 1–2s metaphor + repos/stars/commits/followers text |
| **M2** | `L-RS` | `scripts/readme_sections.py` **only** | M1, I17 | — | no table; art outside details; `width=100%`; one details per piece |
| **M3** | `L-README` | `README.md` | M2 | V1 may start after M3 | `rg` intro + details + `100%` on README |
| **M4** | `L-T-GFM` (+ I99 extras) | `tests/test_readme_gfm_ux.py`; **`tests/test_readme_sections.py`**; **wrap piggyback in `tests/test_profile_workflow.py` ~1128–1143** | M3 | — | invert wrap/360/no-details; expand pytest beyond `-k living_art` |
| **M5** | `L-T-GFM` | `tests/test_readme_gfm_ux.py` | M4 | — | intro has no spine list; dropdown copy; no external host |
| **M6** | `L-T-GFM` | `tests/test_readme_gfm_ux.py` | M5 | — | either `<video src=mp4>` **or** GIF+href MP4 passes; youtube/cloudinary fail |

`M4` → `M5` → `M6` share `L-T-GFM` → **sequential on the GFM file**. I99 also puts `test_readme_sections.py` on `L-T-GFM` for the wrap invert. The workflow piggyback is a **bounded M4 touch** of `L-T-WF` (no writer before S9). S9 must **not** restore wrap/360/no-details.

**V4 is not this wave** (`L-RS`, after V3). I99: V4 `files[]` = assembler only; drop `README.md` (regen is M3 / S14 on `L-README`). Fallback stays the **new stack**, not a return to 360 wrap.

**Recommended lane order:** M1 → M2 → M3 → M4 → M5 → M6. Graph is already that chain. Do not start M2 before M1 legends exist. Do not hand-edit `README.md` in M2.

---

## Target picture (what ships after M3)

From `facts.md` + grill. Inverse of today’s wrap.

| Fact | Target | Fail if |
|---|---|---|
| count | 4–6 pieces; never more than six | wrap of six thumbs forever, or >6 |
| intro | one sentence: daily timelapses of this GitHub account from creation to now, each a different visual world | intro lists repos/stars/commits/followers |
| layout | **full-width stack**: one artwork per row at maximum size, then that piece’s dropdown | wrap, thumb strip, `<table>`, CSS grid, `_gfm_two_col_imgs` |
| visible-art | GIF or video **outside** `<details>` | media nested in details; stripped `<video>` with no inner GIF |
| per-piece-details | one **collapsed** `<details>` per piece; no shared FAQ | zero details, or one “how to read these” |
| dropdown-copy | title, 1–2 sentence metaphor, then four-signal mapping | knob names only; essay; second metrics dashboard |
| video-primary | try in-repo `<video src=".github/assets/img/living-{style}.mp4">` | YouTube / Cloudinary / user-attachments / `github.com/*/assets/` |
| video-fallback | if strip or no autoplay (VID): visible GIF + **obvious** in-repo MP4 click on this stack | keep 360 wrap as “compatibility” |

Display width is **`width="100%"`** (GIFs are 400×400). Separator `sep-living.svg` already uses 100% **outside** `_living_art_section`; new 100% attrs live **inside** the section slice (hard invert of today’s `width="100%" == 0`).

Heading must stay findable: `## Living Art` **or** `<!-- ## Living Art -->`. Live README uses the comment heading. Do not add a duplicate visible H2 without updating `_normalize_section_separators`.

---

## Residue (why today’s README is the inverse)

Evidence: I01 + I17 + I99. Live tree, not a hoped-for stack.

### 1. Assembler is a private six-tuple wrap

`_rewrite_living_art_section` (`scripts/readme_sections.py:1095-1148`):

- Hardcoded six `(title, gif, alt suffix)` — **does not import** `LIVING_ART_STYLE_KEYS` or `roster.SHIPPED_STYLE_KEYS`.
- One `<p align="center">` of `width="360"` GIF posters, each `<a href="…mp4">`.
- No intro, no `<details>`, no `<video>`.
- Paths always `.github/assets/img/…`. `html.escape` on title/suffix only.
- `_gfm_two_col_imgs` emits `<table>` — **forbidden** for this section.

Shipped `README.md:68-79` matches. Metaphors exist only as **img alt**. The only README `<details>` is My Tech Stack (`:84`, `:317`), not Living Art.

S1 shrinking `SHIPPED` does **nothing** to README until M2 reads roster (I99 risk 10). S14 regen is not enough if the six-tuple stays hardcoded.

### 2. Three test files freeze wrap / 360 / no-details; one lock covers one file

| File | Lock today | Call / assert | `-k living_art`? |
|---|---|---|---|
| `tests/test_readme_gfm_ux.py` | `L-T-GFM` | `_LIVING_WRAP_RE` `{6}`; `width="360" == 6`; `width="100%" == 0`; `"<details" not in living` | three tests; **misses** `test_waka_and_blog_are_visible_not_details` `:325` |
| `tests/test_profile_workflow.py` | `L-T-WF` (S9) | piggyback in `test_finalize_applies_waka_before_readme_sections` `:1128-1143` | **no** (S9 hits `:411`, `:460`, `:849` only) |
| `tests/test_readme_sections.py` | **none** (unlocked) | `test_generate_rewrites_living_art_as_wrap_flow_grid` `:959-1021` | name has wrap, not `living_art` substring in the usual slice |

Shared helper `living_art_wrap()` (`test_readme_gfm_ux.py:152-155`) is imported by all three. Deleting it in M4 without the other two files reds helper import even if GFM `-k living_art` is green.

**I99 pick: invert in M4 (Wave RM), not S9.** M2 goes red in three files immediately. Waiting for post-K2 S9 leaves RM red. `L-T-WF` has no writer before S9, so M4 may touch the piggyback.

### 3. Video form is GIF+href only; `<video>` will probably be stripped

2026 sources (I17): profile/repo README sanitizer allowlist includes `img` / `a` / `details`, **not** `video`. Drag-drop CDN players (`user-images.githubusercontent.com`, `github.com/*/assets/`) are **external hosts** — forbidden.

There is **no** test today that mentions `<video>`, YouTube, Cloudinary, or iframe. Current tests **require** GIF+href wrap as the only legal form.

Grill: do **not** treat today’s GIF-poster-linking-to-MP4 as the designed default. M2 still **tries** `<video>` on `origin/dev`. A stripped `<video>` with **no inner GIF** blanks the gallery (`fact-visible-art`). Fallback after V2/V3 is an **allowed done state**, not a failed goal.

---

## M1 — `L-ROS` — fill legends

**File:** `scripts/art/roster.py` (created in R1). Titles may already match published labels. Metaphor + mapping after R1 are **placeholders** (often knob names: “bloom scale”, “trunk scale”). M1 replaces those with README dropdown copy.

Use `shipped_legends()` / `STYLE_LEGENDS`. Keep keys == `CANDIDATE_STYLE_KEYS` order. Do not shrink `SHIPPED`. Do not invent a seventh style.

| Must | Must not |
|---|---|
| Every key: `title`, 1–2 sentence `metaphor`, four `mapping` strings | Essay; second metrics dashboard; list the spine in a shared intro blob |
| Mapping = **that world’s picture** (align DIAL identities below) | Copy overlay glyph names or `data-accretion-*` |
| `html.escape`-safe plain text (assembler will escape) | Markdown tables inside the legend |

**Legend intent (visual identity, not knobs):**

| Key | Title | Repos | Stars | Commits | Followers |
|---|---|---|---|---|---|
| `inkgarden` | Ink Garden | plants (stem **and** canopy), one tree per repo | bloom | trunk | glints (none at 0 followers) |
| `topo` | Topography | peaks, one hill per repo | prominence / height | contour identity | settlements |
| `genetic` | Genetic Landscape | fitness peaks | peak height | generations | colonies |
| `physarum` | Physarum | nutrient nodes; network from first repo | nutrient scale | trail / vein growth | vein mass (not the spore) |
| `lenia` | Lenia | seed organisms | halo | field occupancy | spatial extent |
| `ferrofluid` | Ferrofluid | dipoles / towers, one per repo | spike height | pool / ripple mark | magnetic field |

S11 later copies these legends into `living-art-modes.mdx`. Write them once here.

**Verify:** each of six has title + metaphor + repos/stars/commits/followers text. Import `shipped_legends()` and assert `len == 6` until K2.

---

## M2 — `L-RS` — rewrite assembler (inner GIF + `<video>` try)

**File:** `scripts/readme_sections.py` only. **Not** `README.md`.

Invert `_rewrite_living_art_section`:

| Today (`:1095-1148`) | M2 |
|---|---|
| Hardcoded 6-tuple | `SHIPPED_STYLE_KEYS` + `shipped_legends()` / `legend_for` |
| One wrap `<p>` | **Stack**: artwork row, then that piece’s `<details>` |
| `width="360"` | `width="100%"` on visible media |
| No intro | One clock sentence; **must not** name repos/stars/commits/followers |
| No `<details>` | One collapsed `<details>` per piece; art **above** it |
| GIF `href` MP4 only | Emit **native `<video src=…mp4>`** first; **inner GIF+href** so a sanitizer drop does not blank art |
| Alt-only metaphors | Visible dropdown: title, metaphor, four-signal map |
| Forbids table/grid by accident of wrap | Still forbid; do **not** call `_gfm_two_col_imgs` |

**Inner-fallback sketch (try, not V4’s “obvious click” copy):**

```html
<video src=".github/assets/img/living-{style}.mp4" width="100%">
<a href=".github/assets/img/living-{style}.mp4"><img src=".github/assets/img/living-{style}.gif" width="100%" alt="…" loading="lazy"/></a>
</video>
<details>
<summary>{title}</summary>
{metaphor}
repos: … / stars: … / commits: … / followers: …
</details>
```

Do **not** set `open` on details. Do **not** put `<video>` / `<img>` inside details. Relative `.github/assets/img/living-*.{gif,mp4}` only. No `iframe`. No YouTube / Cloudinary / `user-images.githubusercontent.com` / `github.com/*/assets/` / `github.com/user-attachments/`.

Keep `section_separator_block("Living Art", "sep-living.svg")` + a heading the regex can find. Missing heading still warns and leaves content unchanged.

Living Art is **not** a marker-injected block; it is a heading-bounded rewrite. Pipeline: `generate()` → `_postprocess_static_sections` always calls this first. CLI for M3: `uv run readme generate readme-sections`.

Do **not** treat featured 360 wrap (`_render_featured_table`) as a template. Featured tests (`width="360" == 8`) stay untouched.

**Verify (graph):** no table; art outside details; width=100%; one details per piece. Unit-level `generate()` / `_rewrite_living_art_section` will still be red until M4 — that is expected. Do not dual-path the old wrap “for compatibility.”

---

## M3 — `L-README` — regenerate

Run, do not hand-edit the wrap:

```bash
uv run readme generate readme-sections
```

`README.md:68-79` must become intro + stack + details + `100%`. Neighbor order stays `config.yaml` (`Featured Projects`, `Metrics`, `Living Art`, `My Tech Stack`, `Word Clouds`). Comment heading may remain.

**Verify:** intro sentence present; `<details>` count == shipped length; living-art media `width="100%"`; no `<table>` in the section; six (until K2) in-repo gif+mp4 stems.

P0 (later) pushes this presentation to `origin/dev` for V2. README-only is enough for P0 if tracked MP4s already exist (I18). Do **not** use commit message `art: regenerate living-art assets` (loop guard). Do **not** push `main`.

V1 (`L-VID`) may write `video-check.md` **template** after M3; V2 still needs P0/M6 markup on `dev`.

---

## M4 — invert wrap tests (three files, not one)

**Replace, do not dual-path.** Graph verify `pytest -q tests/test_readme_gfm_ux.py -k living_art` is **too narrow** (I01, I05, I99).

### Files (I99)

1. `tests/test_readme_gfm_ux.py` (`L-T-GFM`)
2. `tests/test_readme_sections.py` — expand `L-T-GFM`; rewrite `test_generate_rewrites_living_art_as_wrap_flow_grid` `:959-1021`
3. Wrap piggyback in `tests/test_profile_workflow.py` `test_finalize_applies_waka_before_readme_sections` `:1128-1143` only — keep waka-before-sections asserts; invert wrap/360/no-details. Prefer splitting the discarded docstring block so waka-order and GFM layout do not share one silent contract. Do **not** take the rest of `L-T-WF` (S9).

If M4 deletes or changes `living_art_wrap` / `_LIVING_WRAP_RE`, update all importers in this node.

### Flip these asserts

| Today | After M4 |
|---|---|
| `_LIVING_WRAP_RE` `{6}` pairs in one centered `<p>` | delete or replace; stack is many blocks |
| `width="360" == 6` | `width="100%"` on living-art media; count = `len(SHIPPED)` (cap 6) |
| `width="100%" == 0` inside section | **direct invert** (separator 100% was already outside the slice) |
| `"<details" not in living` (`:214-215`, `:325`, `:1010`, `:1143`) | **required**: one `<details>` per shipped key |
| one `<p align="center">` | allow stack; still **no** single wrap of six 360 thumbs |
| `loading="lazy" == 6` | follow shipped length |
| no `<table>` / CSS grid / `<br/>` / `<sub>` | **keep** no-table / no-grid |
| `test_waka_and_blog_are_visible_not_details` `:314-323` | **keep**: no `living-` inside a details block that wraps the GIF/video |
| same test `:325` | **flip** — section *will* contain details |
| generator rewrite drops teasers / tables | keep table-stripping; expected output is the **new stack**, not wrap |

Count source: loop `SHIPPED_STYLE_KEYS` / `LIVING_ART_STYLE_KEYS` (SHIPPED after R2). Do **not** bake six literal filenames if K3 needs 4–6 from `accepted`. `_LIVING_WRAP_RE` cannot stay as the only matcher (M6).

Rename tests whose names still say wrap_flow if that keeps `-k living_art` honest — or **expand verify** (required either way):

```bash
uv run python -m pytest -q \
  tests/test_readme_gfm_ux.py \
  tests/test_readme_sections.py::test_generate_rewrites_living_art_as_wrap_flow_grid \
  tests/test_readme_gfm_ux.py::test_waka_and_blog_are_visible_not_details \
  tests/test_profile_workflow.py::test_finalize_applies_waka_before_readme_sections
```

Rename the sections test when rewriting so the name matches stack/details. Include it in M4 verify either way.

Featured `width="360" == 8` (`test_readme_gfm_ux.py:248`, `test_readme_sections.py:561`) is **not** living art. Leave it.

**S9 later:** must not restore wrap/360/no-details. S9 verify expands to the finalize test (waka-order + remaining stack asserts).

---

## M5 — intro / dropdown / host

Same `L-T-GFM` file, after M4. Facts `automatedVerification: true` for intro / dropdown / video-fallback markup.

Add tests:

- Intro present under Living Art; intro does **not** list repos, stars, commits, followers, or “four-signal spine”.
- Each shipped key: one `<details>`; title + short metaphor + four mapping phrases (from M1).
- No shared FAQ `<details>` for all styles.
- No youtube / youtu.be / cloudinary / vimeo / iframe / `user-images.githubusercontent.com` / `github.com/*/assets/` / `github.com/user-attachments/` on living-art `src`/`href`.
- Allowlist: relative `.github/assets/img/living-*.{gif,mp4}` only.

There is **no** host ban today (I17: `rg` empty). M5/M6 must add it or a regression can slip in during video-form work.

---

## M6 — both media forms legal

Today only GIF+`href` MP4 exists; no `<video>` in tests or README.

Allow **either** (XOR/OR; both together OK during the try window):

1. `<video src=".github/assets/img/living-{style}.mp4" …>` (native; may include poster / inner GIF).
2. Visible `<img src="…gif">` with obvious `<a href="…mp4">` click-through.

Fail: youtube, cloudinary, or GIF/video hidden in details. After V4, the assembler commits to one form; tests must still accept **both** so a later switch does not require a third GFM rewrite.

V4 (VID, not RM): if stripped or no autoplay → assembler = form (2) on the **full-width stack with details**. That is today’s **media**, not today’s **wrap**. I99: assembler-only; S14/M3-style regen owns `README.md`.

---

## Sequence and handoff

```text
W1M (shipped == candidates == six)
  ├─► ACC A1–A3 (parallel; not this playbook)
  └─► M1 legends (L-ROS)
        └─► M2 assembler inner GIF + <video> try (L-RS)
              └─► M3 regen README (L-README)
                    ├─► V1 template (VID, after M3; not this wave)
                    └─► M4 invert wrap in THREE test files
                          └─► M5 intro / dropdown / host
                                └─► M6 both media forms legal
                                      └─► P0 push origin/dev (not this wave)
                                            └─► V2 github.com check → V3 → maybe V4
W2M needs M6 + DIAL merge, not P0
```

Plan W2M verify (RM slice):

```bash
uv run readme generate readme-sections
uv run python -m pytest -q tests/test_readme_gfm_ux.py -k living_art
```

**I99:** that pytest slice is insufficient. Implementers use the M4 expanded command through M6, plus M6 host failures.

---

## Out of this lane

| Concern | Owner |
|---|---|
| Roster module creation / SHIPPED vs CANDIDATE split | ROS `R1`–`R5` (done before W1M) |
| On-canvas dialect unreadability | DIAL `D*1`–`D*4` |
| Shared accretion ceilings | A3 no-op unless all six share a clock |
| `video-check.md` + github.com play/strip | VID `V1`–`V4` |
| Push presentation | `P0` / `C2` on `origin/dev` only |
| GIF+MP4 regen / budgets | GEN `G1*`–`G3`; do not raise caps |
| Shrink tests / exact-six copy / workflow names | SHR after K2 |
| V4 README regen | `L-README` (S14), not V4 |
| Featured 360 wrap | not Living Art |
| `openspec/changes/prevent-living-art-repo-growth` | never this goal (S15) |
| `main` | untouched |

---

## Done when

- **M1:** six legends are README copy (title, 1–2s metaphor, four-signal map), not knob placeholders.
- **M2:** assembler iterates shipped legends; full-width stack; intro without spine list; art outside details; one details per piece; `<video src=in-repo.mp4>` with **inner GIF+href**; no table/grid/external host.
- **M3:** `README.md` regenerated from that assembler; intro + details + `100%` visible on disk.
- **M4:** wrap/360/no-details inverted in GFM **and** `test_readme_sections.py` **and** the finalize piggyback; waka `:325` flipped; art-not-inside-details kept; expanded pytest green.
- **M5:** intro / per-piece dropdown / no-external-host automated.
- **M6:** native `<video>` **or** GIF+href both legal; youtube/cloudinary fail.

Fallback remaining a wrap of six 360 GIFs still fails this wave even if V2 later chooses GIF+click.

---

## Confirm

Written: `goals/living-art-overhaul/waves/RM.md`  
No assembler, README, test, roster, workflow, or `task-graph.json` edits in this node.
