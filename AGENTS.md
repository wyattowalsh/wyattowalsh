# AGENTS.md

> GitHub profile automation — generates SVG banners, QR codes, word clouds, generative art, skills badges, and dynamic README sections for [wyattowalsh](https://github.com/wyattowalsh/wyattowalsh). Python 3.13+ · uv · Typer · Pydantic v2 · Loguru · pytest

## Quick Reference

| Task | Command |
|------|---------|
| Install all deps | `uv sync --all-groups` |
| Format | `uv run readme dev format` |
| Lint | `uv run readme dev lint` |
| Test | `uv run readme dev test` |
| Generate banner | `uv run readme generate banner` |
| Generate QR code | `uv run readme generate qr` |
| Generate word clouds | `uv run readme generate word-cloud` |
| Generate all assets | `uv run readme generate all` |
| Generate skills badges | `uv run readme generate skills` |
| Generate README sections | `uv run readme generate readme-sections` |
| Serve docs locally (Fumadocs) | `uv run readme dev docs` |
| Clean artifacts | `uv run readme dev clean` |
| Update deps | `uv run readme dev update-deps` |
| CLI help | `uv run readme --help` |

**Package manager:** `uv` exclusively — never `pip install` or `poetry`.
**Python:** 3.13+ (enforced in `pyproject.toml`).
**CLI:** `uv run readme <cmd>` or `uv run python -m scripts.cli <cmd>`.

## Architecture

```text
wyattowalsh/
├── scripts/              # Asset generation package (→ scripts/AGENTS.md)
│   ├── cli/             # Typer CLI package — `readme` entry point
│   │   ├── _app.py      # Root app, --version, sub-app registration
│   │   ├── generate.py  # Generate subcommands (banner, qr, word-cloud, …)
│   │   ├── config_cmd.py # Config subcommands (view, save, generate-default)
│   │   ├── settings_cmd.py # show-settings command
│   │   └── dev.py       # Dev tools (format, lint, test, clean, docs)
│   ├── config.py        # Pydantic models + load_config() / save_config()
│   ├── utils.py         # get_logger(), create_progress(), console
│   ├── banner.py        # SVG banner — Lorenz attractor, flow fields
│   ├── qr.py            # Artistic vCard QR code — segno + Cairo
│   ├── word_clouds/     # Word cloud subpackage — generation + renderers
│   │   ├── generate.py  # Generation pipeline, CLI, settings
│   │   ├── core.py      # PlacedWord, BBox, font constants
│   │   ├── colors.py    # OKLCH palettes, domain clustering
│   │   ├── engine.py    # SvgWordCloudEngine base class
│   │   ├── solvers.py   # 25 metaheuristic optimization solvers
│   │   ├── wordle.py    # WordleRenderer
│   │   ├── clustered.py # ClusteredRenderer
│   │   ├── typographic.py # TypographicRenderer
│   │   ├── shaped.py    # ShapedRenderer
│   │   └── metaheuristic.py # MetaheuristicAnimRenderer + registry
│   ├── readme_sections.py # README dynamic section assembler
│   ├── readme_svg.py    # SVG rendering helpers for README components
│   ├── skills.py        # shields.io badge generator from skills.yaml
│   ├── generative.py    # Static generative art (Clifford/Phyllotaxis)
│   ├── animated_art.py  # CSS-animated SVGs from commit history
│   ├── fetch_metrics.py # GitHub GraphQL metrics collector
│   ├── fetch_history.py # GitHub commit history collector
│   ├── _github_http.py  # Shared GitHub API HTTP helpers
│   ├── techs.py         # Parse techs.md → Technology objects
│   └── art/             # Generative art subpackage
│       ├── shared.py    # Noise, color, math utilities
│       ├── ink_garden.py # Procedural botanical SVG garden
│       ├── _dev_profiles.py # Mock profiles for local animation testing
│       ├── animate.py   # Multi-frame animation driver
│       └── topography.py # Topographic contour art
├── tests/               # pytest suite (→ tests/AGENTS.md)
├── docs/                # Fumadocs (Next.js 15) dev docs site
├── .github/
│   ├── workflows/profile-updater.yml  # Single unified CI workflow
│   └── assets/img/      # Generated: banner.svg, qr.png, wordcloud_*.svg
├── config.yaml          # Edit this to configure generation params
├── skills.yaml          # Skills badge definitions
└── pyproject.toml       # Metadata, deps, tool configs
```

**Asset pipeline** (CI: daily 1AM UTC, push to main/master, manual dispatch):

1. `uv run starred` CLI → `.github/assets/languages.md` + `.github/assets/topics.md`
2. `readme generate word-cloud --techs-path topics.md` → `wordcloud_by_topic.svg`
3. `readme generate word-cloud --techs-path languages.md` → `wordcloud_by_language.svg`
4. `readme generate qr` → `qr.png`
5. `readme generate banner` → `banner.svg`
6. `readme generate skills` → skills badges in README
7. `stefanzweifel/git-auto-commit-action@v5` auto-commits changed assets

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
`ProjectConfig` → `BannerSettings` · `VCardDataModel` · `QRCodeSettings` · `WordCloudSettingsModel` · `SkillsSettings` · `ReadmeSvgSettings` · `ReadmeSectionsSettings`

| Variable | Required? | Purpose |
|----------|-----------|---------|
| `LOG_LEVEL` | No (default: `INFO`) | Console log verbosity |
| `DEBUG_MODE` | No (default: `false`) | Verbose debug output |

CI secrets (GitHub Actions only — not needed locally):
`WAKATIME_API_KEY` · `GH_TOKEN` · `METRICS_TOKEN` · `SPOTIFY_CLIENT_ID` · `SPOTIFY_CLIENT_SECRET` · `SPOTIFY_REFRESH_TOKEN` · `TWITTER_TOKEN`

## Known Issues

| ID | File | Issue | Priority |
|----|------|-------|----------|
| HR-02 | `tests/test_techs.py`, `tests/test_word_clouds.py` | Both empty — zero coverage for `techs.py` and `word_clouds.py` | P1 |
| HR-03 | `scripts/banner.py` | Monolithic (1700+ lines) — refactor candidate | P2 |
| HR-05 | `scripts/config.py` vs `scripts/word_clouds.py` | Two word-cloud config models: `WordCloudSettingsModel` (config.py) and `WordCloudSettings` (word_clouds.py, strict `extra="forbid"`) — easy to confuse | P2 |
| HR-08 | repo root | No `.env.example` for local dev vars or CI secrets | P2 |
| HR-10 | `scripts/banner.py` | `BannerConfig.output_path` defaults to `./assets/img/banner.svg`, not `.github/assets/img/banner.svg` — always override via `config.yaml` | P3 |

### Strategic Improvements (P3 — Future Work)

| ID | Area | Description |
|----|------|-------------|
| ST-01 | `scripts/banner.py`, `scripts/readme_svg.py` | Plan migration from `svgwrite` (UNMAINTAINED) to `svg.py` (type-safe, actively maintained) |
| ST-02 | Asset pipeline | Add SVG optimization post-processing via `scour` (~48% size reduction) or `npx svgo --multipass` |
| ST-03 | Testing | Add `syrupy` snapshot testing with `SVGImageSnapshotExtension` for visual regression safety |
| ST-04 | CLI | Add local preview command (`cli preview <generator>`) for faster creative iteration |
| ST-05 | README | Add light/dark mode SVG variants using `<picture>` + `prefers-color-scheme` |
| ST-06 | `scripts/config.py` | Switch to native `YamlConfigSettingsSource` from `pydantic-settings` |
| ST-07 | `scripts/config.py` | Use Pydantic v2 discriminated unions for type-safe generator config dispatch |
| ST-08 | `scripts/` | Sub-package restructure: `generators/`, `data/`, `core/` |
| ST-09 | `scripts/banner.py`, `scripts/animated_art.py` | Extract duplicate Clifford attractor to shared `art/shared.py` utility |

## Sub-file Index

| File | Load context | Contents |
|------|-------------|----------|
| [`scripts/AGENTS.md`](scripts/AGENTS.md) | When editing any script module | Module map, Pydantic patterns, per-generator reference, CLI extension guide |
| [`tests/AGENTS.md`](tests/AGENTS.md) | When writing or running tests | Run commands, coverage status, test patterns, writing guide |
| [`docs/`](docs/) | When editing dev documentation | Fumadocs (Next.js 15) site; `cd docs && pnpm dev` to preview |

## Common Failure Modes

| Symptom | Cause | Fix |
|---------|-------|-----|
| `FileNotFoundError: Default background SVG not found` | `icon.svg` missing | Background is optional (default=None); only set `background_svg` in config if you want a custom background |
| `ImportError: No module named 'segno'` | QR extras not installed | `uv sync --extra qr` |
| `ImportError: No module named 'wordcloud'` | word-clouds extras not installed | `uv sync --extra word-clouds` |
| `ValidationError` from `WordCloudSettings` | Extra keys on strict model | Remove unknown fields — `extra="forbid"` in `WordCloudSettings` |
| `load_config()` returns defaults silently | `config.yaml` missing or empty | Auto-creates with defaults; edit the created file |
| `generate qr` Cairo error | Cairo not in dyld path (macOS) | `export DYLD_LIBRARY_PATH=$(brew --prefix cairo)/lib:$DYLD_LIBRARY_PATH` |
| `noise` module warning but continues | `noise` package absent | Expected — `NoiseHandler` falls back to trig automatically |
| `starred` command not found | script-tools not installed or command not run through `uv` | `uv sync --extra script-tools` then `uv run starred ...` |
