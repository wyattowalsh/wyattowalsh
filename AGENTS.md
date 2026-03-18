# AGENTS.md

> GitHub profile automation — generates SVG banners, QR codes, and word clouds for [wyattowalsh](https://github.com/wyattowalsh/wyattowalsh). Python 3.13+ · uv · Typer · Pydantic v2 · Loguru · pytest

## Quick Reference

| Task | Command |
|------|---------|
| Install all deps | `uv sync --all-groups` |
| Format | `make format` |
| Lint | `make lint` |
| Test | `make test` |
| Generate banner | `make generate-banner` |
| Generate QR code | `make generate-qr` |
| Generate word clouds | `make generate-word-clouds` |
| Generate all assets | `make generate` |
| Lint + test + generate | `make all` |
| Serve docs locally (Fumadocs) | `cd docs && pnpm dev` |
| Clean artifacts | `make clean` |
| CLI help | `uv run readme --help` |

**Package manager:** `uv` exclusively — never `pip install` or `poetry`.
**Python:** 3.13+ (enforced in `pyproject.toml`).
**CLI:** `uv run readme <cmd>` or `uv run python -m scripts.cli <cmd>`.

## Architecture

```
wyattowalsh/
├── scripts/              # Asset generation package (→ scripts/AGENTS.md)
│   ├── cli.py           # Typer app — `readme` entry point
│   ├── config.py        # Pydantic models + load_config() / save_config()
│   ├── utils.py         # get_logger(), create_progress(), console
│   ├── banner.py        # SVG banner — Lorenz attractor, flow fields (1730 lines)
│   ├── qr.py            # Artistic vCard QR code — segno + Cairo
│   ├── word_clouds.py   # Word cloud generator — multiple input modes (1585 lines)
│   └── techs.py         # Parse techs.md → Technology objects
├── tests/               # pytest suite (→ tests/AGENTS.md)
├── docs/                # Fumadocs (Next.js 15) dev docs site
├── .github/
│   ├── workflows/profile-updater.yml  # Single unified CI workflow (5 jobs)
│   └── assets/img/      # Generated: banner.svg, qr.png, wordcloud_*.svg
├── config.yaml          # Edit this to configure generation params
├── pyproject.toml       # Metadata, deps, tool configs
├── Makefile             # Task runner
└── techs.md             # Tech stack with proficiency levels (1–5)
```

**Asset pipeline** (CI: daily 1AM UTC, push to main/master, manual dispatch):
1. `starred` CLI → `.github/assets/languages.md` + `.github/assets/topics.md`
2. `generate word_cloud --from-topics-md` → `wordcloud_by_topic.svg`
3. `generate word_cloud --from-languages-md` → `wordcloud_by_language.svg`
4. `generate qr_code` → `qr.png`
5. `generate banner` → `banner.svg`
6. `stefanzweifel/git-auto-commit-action@v5` auto-commits changed assets

## Core Conventions

- **Package manager:** `uv` only. `uv add <pkg>` to add; `uv sync --all-groups` to install; never `pip`.
- **Logging:** `from .utils import get_logger; logger = get_logger(module=__name__)` — never `print()` or stdlib `logging`.
- **Imports:** relative within `scripts/` (`from .config import ProjectConfig`, not `from config import ...`).
- **Types:** Pydantic v2 models for all config/data. `mypy` enforces `disallow_untyped_defs = true`.

| ❌ Anti-pattern | ✅ Correct |
|----------------|-----------|
| `pip install pkg` | `uv add pkg` |
| `print("msg")` | `logger.info("msg")` |
| `from config import X` | `from .config import X` |
| Bare `except:` | `except SpecificError as e:` |
| String paths | `Path(__file__).resolve().parent.parent / "subdir"` |
| New models in script files | Add to `scripts/config.py` |

## Configuration

Edit `config.yaml` (project root) to configure all generators. Load via:
```python
from scripts.config import load_config
cfg = load_config()  # auto-creates defaults if missing
```

**Model hierarchy** (`scripts/config.py`):
`ProjectConfig` → `BannerSettings` · `VCardDataModel` · `QRCodeSettings` · `WordCloudSettingsModel`

| Variable | Required? | Purpose |
|----------|-----------|---------|
| `LOG_LEVEL` | No (default: `INFO`) | Console log verbosity |
| `DEBUG_MODE` | No (default: `false`) | Verbose debug output |

CI secrets (GitHub Actions only — not needed locally):
`WAKATIME_API_KEY` · `GH_TOKEN` · `METRICS_TOKEN` · `SPOTIFY_CLIENT_ID` · `SPOTIFY_CLIENT_SECRET` · `SPOTIFY_REFRESH_TOKEN` · `TWITTER_TOKEN`

## Known Issues

| ID | File | Issue | Priority |
|----|------|-------|----------|
| HR-01 | `tests/test_cli.py` | `from config import ProjectConfig` → should be `from scripts.config import ProjectConfig`; guard silently skips all CLI tests | P1 |
| HR-02 | `tests/test_techs.py`, `tests/test_word_clouds.py` | Both empty — zero coverage for `techs.py` (315 lines) and `word_clouds.py` (1585 lines) | P1 |
| HR-03 | `scripts/banner.py`, `scripts/word_clouds.py` | Monolithic (1730 / 1585 lines) — refactor candidates | P2 |
| HR-04 | `scripts/banner.py` | `PatternType` defines `REACTION`, `CLIFFORD`, `FLAME`, `PDJ`, `IKEDA` — no draw functions exist (dead code) | P2 |
| HR-05 | `scripts/config.py` vs `scripts/word_clouds.py` | Two word-cloud config models: `WordCloudSettingsModel` (config.py) and `WordCloudSettings` (word_clouds.py, strict `extra="forbid"`) — easy to confuse | P2 |
| HR-08 | repo root | No `.env.example` for local dev vars or CI secrets | P2 |
| HR-09 | `tests/temp.py` | Stray empty file — delete it | P3 |
| HR-10 | `scripts/banner.py` | `BannerConfig.output_path` defaults to `./assets/img/banner.svg`, not `.github/assets/img/banner.svg` — always override via `config.yaml` | P3 |
| HR-11 | `Makefile` `test` | Uses `uv pip install -e ".[test]"` in addition to `uv sync` (bypasses lockfile) | P3 |
| HR-12 | `Makefile` `update-deps` | Uses `uv pip compile` — wrong; should be `uv lock --upgrade` | P3 |

## Sub-file Index

| File | Load context | Contents |
|------|-------------|----------|
| [`scripts/AGENTS.md`](scripts/AGENTS.md) | When editing any script module | Module map, Pydantic patterns, per-generator reference, CLI extension guide |
| [`tests/AGENTS.md`](tests/AGENTS.md) | When writing or running tests | Run commands, coverage status, test patterns, writing guide |

## Common Failure Modes

| Symptom | Cause | Fix |
|---------|-------|-----|
| `FileNotFoundError: Default background SVG not found` | `icon.svg` missing | Background is optional (default=None); only set `background_svg` in config if you want a custom background |
| `ImportError: No module named 'segno'` | QR extras not installed | `uv pip install -e ".[qr]"` |
| `ImportError: No module named 'wordcloud'` | word-clouds extras not installed | `uv pip install -e ".[word-clouds]"` |
| `ValidationError` from `WordCloudSettings` | Extra keys on strict model | Remove unknown fields — `extra="forbid"` in `WordCloudSettings` |
| `load_config()` returns defaults silently | `config.yaml` missing or empty | Auto-creates with defaults; edit the created file |
| `make generate-qr` Cairo error | Cairo not in dyld path (macOS) | `export DYLD_LIBRARY_PATH=$(brew --prefix cairo)/lib:$DYLD_LIBRARY_PATH` |
| `noise` module warning but continues | `noise` package absent | Expected — `NoiseHandler` falls back to trig automatically |
| `starred` command not found | script-tools not installed | `uv pip install -e ".[script-tools]"` |
