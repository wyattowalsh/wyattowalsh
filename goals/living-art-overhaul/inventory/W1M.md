# W1M — Roster split accepted; shipped still six

**Date:** 2026-08-18  
**Status:** complete  
**Lane:** CAP (Wave ROS merge). **No commit / push / branch switch. `main` untouched. OpenSpec growth change untouched.**  
**Deps:** R1 (pre-existing), R2, R3, R4, R5.  
**Inputs:** `I99.md`, `scripts/art/roster.py`, ROS verify below.

Until K2, **`SHIPPED_STYLE_KEYS` is `CANDIDATE_STYLE_KEYS`** (same six, same order). Exact-six tests stay green. Do not shrink. Do not delete generators.

---

## Finding

Wave ROS is merged. Candidate vs shipped is a real alias split, not four copied six-lists. Published inventory / CI keys / default generate follow **SHIPPED**. Generator registry / module `--only` / Typer `--only` follow **CANDIDATE**. Equality `ALL_STYLES == KEYS` is gated so S1 can shrink shipped without immediately bombing media / shared-package / fact-ids. Contracts `set(ALL_STYLES) == set(KEYS)` remains **S6**.

W1M sentence: **Roster split accepted; shipped still six.**

---

## Check tree (this resume)

| Node | Lock | Result |
|---|---|---|
| **R1** | `L-ROS` | **Skipped — already present.** `scripts/art/roster.py` exists with tuple constants, legend slots, `_validate_roster()`. |
| **R2** | `L-ARTF` | **Done.** `LIVING_ART_STYLE_KEYS is SHIPPED_STYLE_KEYS`. Labels from `STYLE_LEGENDS[k].title`. Regex follows shipped. All six budget rows kept. No `CANDIDATE` import in artifacts. |
| **R3** | `L-TL` | **Done.** `ALL_STYLES = list(CANDIDATE_STYLE_KEYS)`; `_STYLE_REGISTRY` built from candidates. `animate.py` `all_generators` from `CANDIDATE_STYLE_KEYS` (`{style}-growth`). Module `--only` stays lax. |
| **R4** | `L-CLI` | **Done.** `--only` ∈ `CANDIDATE_STYLE_KEYS`; default generate = `SHIPPED_STYLE_KEYS`; refresh iff active == SHIPPED. Unknown → `typer.Exit(1)`. Animated help/validation on candidates; animated default still all candidates (not the picker). |
| **R5** | `L-T-MEDIA` (+ listed shared-package / fact-ids) | **Done.** Gated invariant in the three R5 files. Dialects stay on candidates. `test_living_art_contracts.py` **not** edited (S6). `test_cli.py` **not** edited (S8). |

---

## Verify (ROS gate)

Import identity (2026-08-18):

```text
ROS verify ok
CANDIDATE ('inkgarden', 'topo', 'genetic', 'physarum', 'lenia', 'ferrofluid')
SHIPPED   ('inkgarden', 'topo', 'genetic', 'physarum', 'lenia', 'ferrofluid')
KEYS is SHIPPED True
ALL_STYLES ['inkgarden', 'topo', 'genetic', 'physarum', 'lenia', 'ferrofluid']
gated equal True
```

Unknown `--only not-a-style` still exits 1. `_selected_living_art_styles(None) == SHIPPED`. `_selected_living_art_styles("topo") == ("topo",)`.

R5 `pytest` on the three modules: living-art roster asserts green on six. Two residual failures in `test_overhaul_fact_ids.py` are **pre-existing** (typographic `rotate(`, `metrics.extra.svg` gauges) — not ROS.

R4 extra: `tests/test_cli.py -k living` + `test_common_helpers_success_and_guards` — 11 passed.

---

## Live wiring (after ROS)

| Surface | Follows | Path |
|---|---|---|
| Candidate keys | `CANDIDATE_STYLE_KEYS` | `scripts/art/roster.py` |
| Shipped keys | `SHIPPED_STYLE_KEYS` (`= CANDIDATE` until S1) | same |
| `LIVING_ART_STYLE_KEYS` / labels / `_TIMELAPSE_RE` | SHIPPED | `scripts/art/artifacts.py` |
| Byte budgets | still all six rows | `artifacts.py` (S2 drops retired) |
| `_STYLE_REGISTRY` / `ALL_STYLES` | CANDIDATE | `scripts/art/timelapse.py` |
| `animate.all_generators` | CANDIDATE, `{style}-growth` | `scripts/art/animate.py` |
| Typer `--only` + help | CANDIDATE | `scripts/cli/generate/_common.py`, `art.py` |
| Default `generate living-art` / `generate all` | SHIPPED | `_selected_living_art_styles(None)` |
| Index refresh | iff active == SHIPPED | `_common.py` |
| Module `python -m scripts.art.timelapse --only` | lax skip+warn | R3 documented; not Typer-equivalent |
| README assembler | **still hardcoded six-tuple** | `readme_sections.py` — **M2** |
| `STYLE_DIALECTS` | candidates | `accretion.py`; R5 keeps that |
| `set(ALL_STYLES) == set(KEYS)` in contracts | **ungated** | `tests/test_living_art_contracts.py:231` — **S6** |

Six keys (order): `inkgarden`, `topo`, `genetic`, `physarum`, `lenia`, `ferrofluid`.

---

## R5 invariant now encoded

In `test_living_art_media.py`, `test_art_shared_package.py`, `test_overhaul_fact_ids.py`:

- `set(SHIPPED) <= set(CANDIDATE)`
- `tuple(ALL_STYLES) == CANDIDATE`
- `LIVING_ART_STYLE_KEYS == SHIPPED`
- `tuple(ALL_STYLES) == KEYS` **only while** shipped == candidates
- Published GIF / README loops in those files use **SHIPPED**
- Dialect identity / family count uses **CANDIDATE**

Do **not** shrink dialect parametrize. Do **not** treat `total_assets == 6` as R5 (S4).

---

## Next (after this marker)

Independent locks, fan:

| Node | Lock | Parallel |
|---|---|---|
| **M1** | `L-ROS` `scripts/art/roster.py` | ∥ A1 |
| **A1** | `L-T-ACC` `tests/test_art_shared_package.py` | ∥ M1 |
| **A2** | `L-T-ACC` (after A1) | ∥ M2 after M1 |
| **A3** | `L-ACC` **default no-op** (after A2) | |
| **M2** | `L-RS` assembler only (after M1; not `README.md`) | |
| **M3** | `L-README` regen (after M2) | |
| **M4→M6** | `L-T-GFM` plus I99 extras: `tests/test_readme_sections.py` + wrap piggyback in `tests/test_profile_workflow.py` ~1128–1143 | sequential |

Until K2: shipped remains six. No DIAL shrink. No OpenSpec edits. No `main`. No commit/push.

---

## Leftover (not this merge)

1. **S1→S6 red window** on `test_living_art_contracts.py:231`.
2. **S8** still owns unknown-`--only` explicit assert in `test_cli.py`; coverage file is not `L-T-CLI`.
3. **README assembler** ignores roster until M2.
4. **A1/A2** on-canvas tests not started (this node).
5. Docs `AGENTS.md` / `scripts/art/AGENTS.md` still call timelapse the published SSOT — **S12**.
6. Pre-existing fact-id residuals (wordcloud rotate / extra.svg) are not ROS.
