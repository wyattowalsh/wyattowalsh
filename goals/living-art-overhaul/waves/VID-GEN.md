# Wave VID + GEN (`V1`–`V4`, `G1*`–`G2`)

**Lanes:** VID (github.com video check + fallback) · GEN (regenerate GIF/MP4 fleet).
**This file is the execution playbook.** Inventory evidence: [`../inventory/I99.md`](../inventory/I99.md) GEN recipe + video path, [`I15.md`](../inventory/I15.md), [`I17.md`](../inventory/I17.md), [`I18.md`](../inventory/I18.md). Graph: [`../task-graph.json`](../task-graph.json) v3. Facts: `fact-video-primary` / `fact-video-fallback` / `fact-visible-art` ([`../facts.md`](../facts.md)). Grill: do **not** treat today’s GIF-poster-linking-to-MP4 as the designed default.
**No production edits while authoring this playbook.** Implementers own `V1`–`V4` and `G1*`–`G2` later. This node does **not** write `video-check.md`, assembler, README, tests, GIFs, or MP4s.

Until K2, shipped == candidates == six. Do not shrink CI, drop a style, or raise `LIVING_ART_BYTE_BUDGETS`. **`main` is untouched.** OpenSpec `prevent-living-art-repo-growth` is untouched.

VID and GEN run **in parallel** after their gates (`P0`/`M6` vs `W2M`). They share no lock until `W3M`. Do not serialize GEN behind V2.

---

## Lock / graph

| ID | Lock | File(s) | Deps | Parallel | Verify (graph) |
|---|---|---|---|---|---|
| **V1** | `L-VID` | `goals/living-art-overhaul/video-check.md` **new** | M3, I17 | VID (with P0 after M6) | template lists play / strip / no-autoplay |
| **P0** | `L-GIT` | `.git` (CAP, not this playbook’s writer) | M6 | before V2 | `blob/dev/README.md` has Living Art stack |
| **V2** | — | github.com (no repo lock) | P0, V1 | after P0 | recorded outcome |
| **V3** | `L-VID` | `video-check.md` | V2 | after V2 | `decision = native \| gif-fallback` |
| **V4** | `L-RS` | `scripts/readme_sections.py` **only** (I99) | V3 | after V3 | legal form matches `video-check.md`; tests still pass |
| **G1ig** | `L-ASSET-IG` | `living-inkgarden.gif` + `.mp4` | W2M, I15 | GEN1 | 400×400; sibling mp4; under that style budget |
| **G1to** | `L-ASSET-TO` | `living-topo.gif` + `.mp4` | W2M, I15 | GEN1 | same |
| **G1ge** | `L-ASSET-GE` | `living-genetic.gif` + `.mp4` | W2M, I15 | GEN1 | same |
| **G1ph** | `L-ASSET-PH` | `living-physarum.gif` + `.mp4` | W2M, I15 | GEN1 | same |
| **G1le** | `L-ASSET-LE` | `living-lenia.gif` + `.mp4` | W2M, I15 | GEN1 | same |
| **G1fe** | `L-ASSET-FE` | `living-ferrofluid.gif` + `.mp4` | W2M, I15 | GEN1 | same |
| **G1** | — | merge of the six pairs | G1ig…G1fe | after GEN1 | six gif+mp4 pairs |
| **G2** | `L-T-MEDIA` | `tests/test_living_art_media.py` | G1 | after G1 | `pytest -q tests/test_living_art_media.py` **plus** committed-fleet + MP4 presence (I99) |
| **G3** | — | `goals/living-art-overhaul/bakeoff/gif-sheet.md` | G1 | ∥ G2 | six styles × 3 frames referenced |

`V1` and `V3` share `L-VID` → **sequential on `video-check.md`**. `V4` is `L-RS` (assembler). Graph `V4` `files[]` still lists `README.md` — **I99 drops it** (regen is M3 / S14 on `L-README`). Do not hold `L-README` in V4.

`G1ig`…`G1fe` may run in parallel: each `--only` one style, each lock is one gif+mp4 pair. **G2** serializes on `L-T-MEDIA` with R5 / S4 — never parallel those. **G3** has no shared lock; decode first/mid/last from the new GIFs; do not re-render.

**Recommended order**

```text
RM:  M2 (try <video> + inner GIF on the NEW stack) → M3 README → M4–M6 tests
CAP: P0 push origin/dev  (README group; never "art: regenerate living-art assets")
VID: V1 template ∥ P0 → V2 github.com → V3 decision → V4 assembler iff gif-fallback
DIAL+RM: W2M
GEN: G1ig…G1fe (--only, --max-frames 120, --size 400) → G1 → G2 committed+MP4
                                              ↘ G3 contact sheet
W3M needs V4 + G2 + G3
```

---

## Target (facts)

| Fact | Ship form |
|---|---|
| **video-primary** | Try native README `<video src=".github/assets/img/living-{style}.mp4">` on `origin/dev`. |
| **video-fallback** | Strip **or** no autoplay → visible GIF + **obvious** in-repo MP4 click. Allowed done state, not a failed goal. |
| **visible-art** | GIF/video **outside** `<details>`. A stripped `<video>` with no inner GIF blanks the gallery. |
| **no external host** | No YouTube, Cloudinary, `user-images.githubusercontent.com`, `github.com/*/assets/`, `github.com/user-attachments/`, iframe, Vimeo. Relative `.github/assets/img/living-*.{gif,mp4}` only. |
| **full-width stack** | Fallback stays the **M2 stack** (`width="100%"`, intro, per-piece `<details>`). Not a return to the 360 wrap. |

Today’s committed README (`README.md:68-79`) is already GIF poster + silent `href` MP4 at wrap 360. That is the **starting** fallback, not the designed default (grill). V4 must add **obvious** click-through on the new stack if the decision is `gif-fallback`.

Success surface is **`origin/dev` README preview**, not `github.com/wyattowalsh` (profile overview follows **default** `main`; this goal does not change `main`).

---

## VID — try then fallback (I17)

2026 sources still say profile/repo README **strips `<video>`** (GitHub sanitizer allowlist: `img`/`a`/`details`, **not** `video`; community #173635, RepoClip 2026). Drag-drop CDN players are **external hosts** — forbidden.

```text
A. In-repo HTML (what V2 must try)
   <video src=".github/assets/img/living-{style}.mp4" width="100%" …>
   Expected 2026 outcome: tag stripped (or player without autoplay).

B. GitHub editor drag-drop CDN URL
   Bare https://github.com/…/assets/… or user-images.githubusercontent.com/….mp4
   May play. External host. Forbidden.

C. Issues/PRs
   Plays. Wrong surface. Do not treat as profile-README proof.
```

Autoplay is a **second fail axis**. Even if `<video>` survived, browsers require `muted` (+ usually `playsinline`); those attributes are not in the public sanitizer list. V2 must record **play** vs **strip** vs **plays-but-no-autoplay**.

M2 (Wave RM, not this playbook) should wrap GIF+href **inside** `<video>` so a strip does not blank art. Inner fallback is not a substitute for V2/V3 recording, and is not V4’s “obvious” copy.

### V1 — write `video-check.md` template (`L-VID`)

File does **not** exist yet. Template must force one of three outcomes. Expected prior: **gif-fallback**. Native win is allowed if V2 contradicts 2026 sources.

```markdown
# Living Art README video check

- URL: https://github.com/wyattowalsh/wyattowalsh/blob/dev/README.md
- Branch: origin/dev
- Date:
- Logged-in vs logged-out:
- Desktop vs mobile (if checked):
- Markup tried: (paste <video> …)
- DOM after GitHub render: video present? / stripped?
- Autoplay (muted loop): yes / no
- Decision: native | gif-fallback   <!-- V3 fills this -->
- External hosts present: none (required)
- Screenshot note:
```

Graph verify: “template lists play / strip / no-autoplay.”

Do **not** fill the decision in V1.

### V2 — github.com check (no lock)

Not CI. Markup tests cannot prove play.

- Open https://github.com/wyattowalsh/wyattowalsh/blob/dev/README.md (and/or the `dev` tree README tab).
- Confirm P0 already pushed the M2/M3 stack (intro + `width="100%"` + per-piece `<details>` + tried `<video>`).
- Record: tag in DOM? autoplay? inner GIF still visible if stripped?
- Logged-out + mobile are extra notes if the desktop blob view is ambiguous.
- Issues/PRs playing MP4 is **not** V2 proof.

Graph verify: “recorded outcome.”

### V3 — write the decision (`L-VID`)

Same file as V1.

| Outcome | Decision |
|---|---|
| `<video>` present in DOM **and** autoplays (muted loop OK) | `native` |
| Tag stripped / not in DOM / broken media | `gif-fallback` → V4 |
| Player visible, **no** autoplay | `gif-fallback` → V4 (`fact-video-fallback`) |

Graph verify: `decision = native | gif-fallback`. “No external host” still true.

### V4 — assembler only (`L-RS`, I99)

**If `native`:** V4 is a **no-op**. Verify M6 tests still pass. Do not reopen wrap/360.

**If `gif-fallback`:** switch `_rewrite_living_art_section` to **visible GIF + obvious in-repo MP4 click** on the **NEW stack** (intro, `width="100%"`, one `<details>` per piece, art **outside** details). Not a return to six `width="360"` in one wrap. Silent `a>img` is today’s wrap, not V4 done — add visible play/watch copy (or equivalent).

| Must | Must not |
|---|---|
| `href` / `src` = `.github/assets/img/living-{style}.{mp4,gif}` | Point at `docs/public/showcase/*.mp4` (none; not pathspec’d) |
| Keep GIF bytes in the tree (inventory is still GIF-primary) | YouTube / Cloudinary / user-attachments / iframe |
| `L-RS` = `scripts/readme_sections.py` only | Edit `README.md` (M3 / S14 on `L-README`) |
| Keep finalize `mp4s=(...)` block (I18) | Unify GIF+MP4 into `:(glob)…living-*.mp4` |

Graph still lists `README.md` on V4. **I99: assembler only; S14 regen.** After V4, a later `L-README` pass (or human M3-style regen) must land the new markup on `dev` before C3 clicks.

Verify: legal form matches `video-check.md`; `uv run python -m pytest -q tests/test_readme_gfm_ux.py -k living_art` still green under M6 (both forms legal; youtube/cloudinary fail).

---

## Finalize GIF vs MP4 (I18) — VID must not “fix” this

One art commit message, **two add mechanisms** (`profile-updater.yml:1572-1586`):

1. **GIFs (required):** `:(glob).github/assets/img/living-*.gif` + showcase GIF glob + manifests/galleries. `git add -A` **does** stage GIF deletions.
2. **MP4s (optional):** `mp4s=(.github/assets/img/living-*.mp4)` appended only if `[ -e "${mp4s[0]}" ]`. Tests **forbid** `:(glob)…living-*.mp4` (`tests/test_profile_workflow.py:478-479`). Bash glob does **not** stage MP4 deletions; leftovers on disk are **re-added**.

Video-primary **must keep the `mp4s` block**. Unifying globs fails S9 and drops films when GIFs are byte-identical. Showcase has **zero** MP4s; V4 `href` stays `.github/assets/img/living-*.mp4`.

P0: README-only is enough (tracked MP4s already exist). Do **not** use commit message `art: regenerate living-art assets` (finalize loop guard). Push `origin/dev` only.

Fail-closing MP4 (assembler `if-no-files-found: error`, drop finalize `continue-on-error`) is a VID/S3 choice. It must **not** introduce `:(glob)…mp4` without rewriting S9 `:478`.

---

## GEN — published media is `render_timelapse()` (I15)

Published `living-*` is **only** `scripts/art/timelapse.py` `render_timelapse()`. Do **not** use `generate animated` / `animate.py` (those write `{style}-growth.gif` from interpolated maturity on **one** blob — not frame *t*).

Frame *t* = cumulative end-of-day world (`build_daily_snapshots` + `sample_frames` ≤ 120 + `validate_snapshot_monotonic_contract`). Seed = **final** sampled day’s `metrics_dict`. `timeline=False`. SVG 800×800 → raster **400×400**.

### G1 command (every `G1*` shard)

Hard args: **`--only`**, **`--max-frames 120`**, **`--size 400`**. Same metrics/history for all six. Partial CLI **skips** index refresh.

```bash
uv run python -m scripts.cli generate living-art \
  --profile wyattowalsh \
  --metrics-path /path/to/metrics.json \
  --history-path /path/to/history.json \
  --only inkgarden \
  --max-frames 120 \
  --size 400 \
  --workers 4 \
  --output-dir .github/assets/img
```

| `--only` | GIF | MP4 | Budget (bytes) | Lock |
|---|---|---|---:|---|
| `inkgarden` | `living-inkgarden.gif` | `living-inkgarden.mp4` | 7_200_000 | `L-ASSET-IG` |
| `topo` | `living-topo.gif` | `living-topo.mp4` | 10_000_000 | `L-ASSET-TO` |
| `genetic` | `living-genetic.gif` | `living-genetic.mp4` | 2_400_000 | `L-ASSET-GE` |
| `physarum` | `living-physarum.gif` | `living-physarum.mp4` | 2_400_000 | `L-ASSET-PH` |
| `lenia` | `living-lenia.gif` | `living-lenia.mp4` | 1_200_000 | `L-ASSET-LE` |
| `ferrofluid` | `living-ferrofluid.gif` | `living-ferrofluid.mp4` | 3_800_000 | `L-ASSET-FE` |

Total GIF budget **27_000_000**. MP4s have **no** byte budget; do not add one (repo-growth out of scope).

### Must / must not (G1)

| Must | Must not |
|---|---|
| ffmpeg on PATH (CLI will **not** fail if MP4 skipped) | Omit `--only` (regenerates all six) |
| Stay inside `LIVING_ART_BYTE_BUDGETS` | Trigger `_assemble_gif` 12 MB **halve** (breaks 400×400, `timelapse.py:295-324`) |
| GIF 400×400, 2–120 frames, ≥24 s, loop 0 | Pass rehearsal `--frames 6` / `--size 96` |
| Sibling MP4 size > 0 | Refresh manifest on a shard |
| Treat dropped frames as failed G1 | Raise caps to pass G2 |
| Same metrics/history pair as the other five | `generate animated` / `generate all` / unscoped `generate living-art` |

Preflight: `metrics.json` + `history.json` (CI: `prepare-event-art-inputs`); `rsvg-convert` and/or cairosvg; `gifsicle` optional. Postflight per style: other `living-*` files unchanged; no index refresh.

`_export_mp4` is best-effort (`timelapse.py:331-381`): yuv420p, `+faststart`, CRF 23. Missing ffmpeg / empty file → GIF still exits 0. **G1 verify checks the sibling yourself.**

G1 merge: six gif+mp4 pairs under `.github/assets/img/`.

### G2 — committed fleet + MP4 presence (`L-T-MEDIA`, I99 correction 7)

Graph verify is `pytest -q tests/test_living_art_media.py`. **That module is GIF-only today.** Zero `mp4` matches. On-disk facts check `living-*.gif` names + `n_frames > 1`, **not** `validate_living_art_byte_budgets` on committed files. G2 as “pytest this module” will **not** prove G1 pairs.

**G2 must add:**

1. Committed-fleet `validate_living_art_byte_budgets(build_living_art_manifest(img_dir))` against `.github/assets/img` (the files G1 just wrote, not only temp fixtures).
2. Assert sibling `living-{style}.mp4` exists and size > 0 for **each shipped GIF**.

Do **not** raise `LIVING_ART_BYTE_BUDGETS`. Do **not** shrink dialect parametrize to shipped. Do **not** rewrite `tuple(ALL_STYLES) == LIVING_ART_STYLE_KEYS` here (R5 / S6). Until K2 that equality stays six.

Topo / ferrofluid / inkgarden sit >91% of cap (I99 risk 4). A fat GIF can look green until this committed-fleet check lands.

### G3 — contact sheet (no lock)

`goals/living-art-overhaul/bakeoff/gif-sheet.md`. First / mid / last frame from each **new** GIF (Pillow `n_frames`). Do not re-render. Graph: six styles × 3 frames referenced. Bake-off scores the regenerated GIFs, not 2026-08-14 A1 stills.

---

## Shared constraints

**Do**

- Try `<video>` on `origin/dev`, then keep it **or** fall back. Fallback is success if recorded in `video-check.md`.
- Keep GIF inventory / stage / budgets GIF-only (I03/I15). MP4s stay unmanaged siblings.
- Keep the finalize `mp4s=` block (I18). S3 may rename exact-six **comments**; it must not unify globs.
- Push `origin/dev` only. P0/C2 never `main`.
- After K2, `--only` keys remain **candidates**; default generate / CI matrix become **shipped**. Until then G1 still uses today’s six keys.

**Do not**

- Edit `openspec/changes/prevent-living-art-repo-growth/**`.
- Edit `main`, workflow GIF/MP4 pathspec split, `artifacts.py` budgets, or `scripts/art/animate.py` for published `living-*`.
- Treat CDN / issue-upload video as native README proof.
- Ship a blank Living Art section during V2 (`fact-visible-art`).
- Rely on finalize to `git rm` retired MP4s later (S13; bash glob re-adds leftovers).
- Commit `art: regenerate living-art assets` from P0 (loop guard).

---

## Sequence and handoff

```text
M2 try <video> + inner GIF on full-width stack
  → M3 README → M4–M6 both forms legal
  → P0 origin/dev
V1 template → V2 github.com → V3 native | gif-fallback
  → V4 assembler iff gif-fallback (L-RS only; S14 regen README)

W2M (dialects + stack)
  → G1ig…G1fe parallel: --only --max-frames 120 --size 400
  → G1 six pairs
  → G2 committed budgets + MP4 siblings
  → G3 contact sheet (∥ G2)

W3M = V4 + G2 + G3  →  bake-off scores new GIFs
```

C3 must click each piece and confirm the film matches the new GIF, not a previous encode (I18 stale-film gap).

---

## Out of this wave

| Concern | Owner |
|---|---|
| Assembler first emit of `<video>` + stack + details | RM `M2` |
| Invert wrap/360/no-details tests | RM `M4` (I99: includes `test_readme_sections.py` + workflow piggyback) |
| Both media forms legal; youtube/cloudinary fail | RM `M6` |
| Push presentation to `dev` | CAP `P0` |
| Dialect redesign / stills | DIAL `D*1`–`D*4` |
| Roster shrink / leftover MP4 `git rm` | SHR `S1`–`S13` |
| README regen after shrink | `S14` (`L-README`, after V4) |
| OpenSpec growth change | never this goal (`S15`) |
| Fail-close MP4 artifact upload/download | optional VID/S3; keep `mp4s=` split |

---

## Done when

- **V1:** `video-check.md` template exists; play / strip / no-autoplay are listed; decision blank.
- **V2:** github.com `blob/dev/README.md` outcome recorded (DOM + autoplay).
- **V3:** `decision = native | gif-fallback`; no external host.
- **V4:** if fallback, assembler emits visible GIF + **obvious** in-repo MP4 click on the **stack** (not 360 wrap); `L-RS` only. If native, no-op. Tests still pass.
- **G1\* / G1:** six `living-{style}.gif` + sibling `.mp4` from `--only --max-frames 120 --size 400`; each GIF under its budget, 400×400, ≥24 s; no 12 MB halve; no index refresh on shards.
- **G2:** `tests/test_living_art_media.py` proves **committed** GIF budgets **and** MP4 siblings — today’s pytest alone is not enough.
- **G3:** contact sheet from the new GIFs, not a re-render.

W3M freezes media + video form. Scoring starts after that, on the regenerated fleet.
