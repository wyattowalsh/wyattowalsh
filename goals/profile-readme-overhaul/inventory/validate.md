# Validate — focused pytest + rg gates

**Date:** 2026-08-14  
**Branch:** `dev` (`dev...origin/dev`)  
**Write lease:** this file only  
**Status:** pytest green; banner / production-plugin gates pass; `anmol098` literal not empty in `scripts/`

No test paths skipped. `tests/test_metrics_svg.py` exists and was included.

---

## 1. Focused pytest

```bash
uv run python -m pytest -q tests/test_profile_workflow.py tests/test_readme_sections.py tests/test_readme_gfm_ux.py tests/test_supplemental_metrics.py tests/test_wakatime_svg.py tests/test_wakatime_readme.py tests/test_skills.py tests/test_word_clouds.py tests/test_living_art_media.py tests/test_metrics_svg.py -q --tb=line
```

| Field | Value |
|---|---|
| Exit code | **0** |
| Result | `============================= 367 passed in 18.19s =============================` |
| Failures | none |
| Platform | darwin, python 3.13.14 |
| Workers | 10 (xdist LoadScheduling); pytest-benchmark auto-disabled |

Included modules (all present):

- `tests/test_profile_workflow.py`
- `tests/test_readme_sections.py`
- `tests/test_readme_gfm_ux.py`
- `tests/test_supplemental_metrics.py`
- `tests/test_wakatime_svg.py`
- `tests/test_wakatime_readme.py`
- `tests/test_skills.py`
- `tests/test_word_clouds.py`
- `tests/test_living_art_media.py`
- `tests/test_metrics_svg.py` (added because the file exists)

---

## 2. `rg` gates

`rg` exit **1** = no matches. Exit **0** = matches printed.

### 2.1 `generate banner` absent from updater

```bash
rg "generate banner" .github/workflows/profile-updater.yml
```

| Field | Value |
|---|---|
| Exit code | **1** |
| Output | empty |
| Verdict | **PASS** — CI does not invoke `generate banner` |

### 2.2 `anmol098` absent from `scripts/`

```bash
rg "anmol098" scripts/
```

| Field | Value |
|---|---|
| Exit code | **0** |
| Hits | 2 (both `scripts/wakatime_svg.py`) |

```
scripts/wakatime_svg.py:``@media (prefers-color-scheme: dark)``. Does not use anmol098.
scripts/wakatime_svg.py:    """Render a public-safe WakaTime card (no anmol098, no file paths)."""
```

Literal-string gate **does not pass** (`rg` is not empty). These are denial comments / a docstring, not an import or Action pin.

```bash
rg -n "uses:.*anmol098|anmol098/waka" scripts/ .github/workflows/profile-updater.yml
```

| Field | Value |
|---|---|
| Exit code | **1** |
| Output | empty |
| Verdict | no `anmol098` Action / `uses:` / `anmol098/waka` invocation |

### 2.3 `plugin_music: no` on production

```bash
rg "plugin_music:" .github/workflows/profile-updater.yml
```

| Field | Value |
|---|---|
| Exit code | **0** |
| Hits | 6, every one is `plugin_music: no` |

Production (`generate-profile-metrics`):

| Step | Line | Value |
|---|---|---|
| Personal metrics | 755 | `plugin_music: no` |
| Personal metrics (additional) | 796 | `plugin_music: no` |
| Personal metrics (extra / overflow) | 839 | `plugin_music: no` |

Probe-only job (`Probe Full Metrics Surface`) also sets `plugin_music: no` at lines 122, 152, 184.

Verdict: **PASS** — no production (or probe) lowlighter `with:` enables music.

### 2.4 Related production plugin locks (same file)

```bash
rg "plugin_tweets:" .github/workflows/profile-updater.yml
```

Exit **0** — four hits, all `plugin_tweets: no` (probe 164; production 757, 808, 843).

```bash
rg "plugin_activity:" .github/workflows/profile-updater.yml
```

Exit **0** — four hits:

| Step | Line | Value |
|---|---|---|
| Probe full additional metrics | 154 | `plugin_activity: yes` (probe-only; comment: production stays off) |
| Personal metrics | 756 | `plugin_activity: no` |
| Personal metrics (additional) | 797 | `plugin_activity: no` |
| Personal metrics (extra / overflow) | 840 | `plugin_activity: no` |

Verdict: **PASS** — production `plugin_activity` stays `no`.

---

## 3. Summary

| Check | Exit | Result |
|---|---|---|
| Focused pytest (10 modules, 367 tests) | 0 | PASS |
| `rg "generate banner"` updater | 1 (empty) | PASS |
| `rg "anmol098" scripts/` | 0 (2 comment hits) | STRING PRESENT |
| `rg` anmol098 Action / `uses:` | 1 (empty) | PASS (no usage) |
| Production `plugin_music:` | 0 (all `no`) | PASS |
| Production `plugin_tweets:` | 0 (all `no`) | PASS |
| Production `plugin_activity:` | 0 (`no` ×3; probe `yes` ×1) | PASS |

Do not treat the two `scripts/wakatime_svg.py` comments as a usage regression. They fail a strict empty-`rg` reading of “anmol098 absent from scripts/”. This file is record-only; those comments were not edited (outside write lease).
