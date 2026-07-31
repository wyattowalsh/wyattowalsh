# AGENTS.md

> GitHub profile automation — generates SVG banners, QR codes, word clouds, generative art, skills badges, and dynamic README sections for [wyattowalsh](https://github.com/wyattowalsh/wyattowalsh). Python 3.13+ · uv · Typer · Pydantic v2 · Loguru · pytest

## Quick Reference

| Task | Command |
|------|---------|
| Install all deps | `uv sync --locked --all-extras` |
| Format | `uv run readme dev format` |
| Lint | `uv run readme dev lint` |
| Test | `uv run readme dev test` |
| Generate banner | `uv run readme generate banner` |
| Generate QR code | `uv run readme generate qr` |
| Generate word clouds | `uv run readme generate word-cloud` |
| Generate all assets | `uv run readme generate all` |
| Generate skills badges | `uv run readme generate skills` |
| Generate supplemental metrics cards | `uv run readme generate supplemental-metrics` |
| Mint Spotify refresh token | `uv run readme auth spotify-refresh-token` |
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
│   │   ├── auth.py      # Auth helpers (Spotify refresh token bootstrap)
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
│   ├── supplemental_metrics.py # Repo-owned supplemental metrics cards
│   ├── spotify_auth.py  # Spotify loopback auth-code helper
│   ├── skills.py        # shields.io badge generator from skills.yaml
│   ├── generative.py    # Static generative art (Clifford/Phyllotaxis)
│   ├── fetch_metrics.py # GitHub GraphQL metrics collector
│   ├── fetch_history.py # GitHub commit history collector
│   ├── _github_http.py  # Shared GitHub API HTTP helpers
│   ├── techs.py         # Parse techs.md → Technology objects
│   └── art/             # Generative / living-art subpackage
│       ├── shared.py    # Noise, color, math utilities
│       ├── ink_garden.py # Procedural botanical SVG garden
│       ├── topography.py # Topographic contour art
│       ├── timelapse.py # Living-art style registry + GIF driver
│       ├── artifacts.py # Manifest / gallery / docs-showcase sync
│       ├── animate.py   # Multi-frame animation driver
│       └── _dev_profiles.py # Mock profiles for local animation testing
├── tests/               # pytest suite (→ tests/AGENTS.md)
├── docs/                # Fumadocs (Next.js 15) dev docs site
├── .github/
│   ├── workflows/profile-updater.yml  # Single unified CI workflow
│   └── assets/img/      # Generated: banner*.svg, qr*.png, wordcloud_*.svg, living-*.gif
├── config.yaml          # Edit this to configure generation params
├── skills.yaml          # Skills badge definitions
└── pyproject.toml       # Metadata, deps, tool configs
```

**Asset pipeline** (CI: `.github/workflows/profile-updater.yml` — daily 1AM UTC, push to `main`/`master`/`dev`, manual dispatch):

Jobs (not a single linear script; each job commits its own owned files). Prefer `uv sync --locked` (+ extras as needed) — this repo has no `[dependency-groups]` in `pyproject.toml`.

1. **`update-starred-lists`** — `uv sync --extra script-tools` → `uv run starred` → commits `.github/assets/languages.md` + `.github/assets/topics.md`
2. **`generate-assets`** (needs starred) — `uv sync --extra qr --extra word-clouds` → `generate qr` → typographic word clouds (`--from-topics-md`, `--from-languages-md`) → commits `qr*.png`, `wordcloud_*.svg`, `banner*.svg` globs. **Intended CI (C1a):** also run `uv run python -m scripts.cli generate banner --config-path config.yaml` so light+dark banners are produced in-job (today that step is still local-only / pending wire-up).
3. **`generate-event-art`** (needs starred) — `uv sync --locked` + `librsvg2-bin` → `fetch_metrics` / `fetch_history` → `generate living-art` → commits living-art GIFs/manifest/preview (+ docs showcase mirrors)
4. **`generate-profile-metrics`** — `uv sync --locked` → lowlighter metrics SVGs (`metrics.svg` / `metrics.additional.svg` / `metrics.extra.svg`, + validation/recovery) → repo-owned supplemental metrics cards (habits/activity/music/posts; never Spotify on lowlighter `with:`)
5. **`update-readme-wakatime`** (needs event-art) — WakaTime README block
6. **`update-skills`** (needs wakatime + metrics) — `uv sync --locked` → `generate readme-sections` → `generate skills` → commits `README.md` + `.github/assets/img/readme/*.svg`

Optional manual lane: **`probe-full-metrics`** (workflow_dispatch `metrics_probe_mode=true` only) — same lowlighter pin as prod; probe-only habits/activity diagnostics; `plugin_music: no`; does not update the profile.

Living-art style map (SSOT): `scripts/art/timelapse.py` (`_STYLE_REGISTRY` / `ALL_STYLES`) · human-readable matrix: [`docs/content/docs/scripts/living-art-modes.mdx`](docs/content/docs/scripts/living-art-modes.mdx)

## Core Conventions

- **Package manager:** `uv` only. `uv add <pkg>` to add; `uv sync --locked --all-extras` to install all extras; never `pip`.
- **Logging:** `from .utils import get_logger; logger = get_logger(module=__name__)` — never `print()` or stdlib `logging`.
- **Imports:** relative within `scripts/` (`from .config import ProjectConfig`, not `from config import ...`).
- **Types:** Pydantic v2 models for all config/data. Use `ty` for type checking.

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
`WAKATIME_API_KEY` · `GH_TOKEN` · `METRICS_TOKEN` · `SPOTIFY_CLIENT_ID` · `SPOTIFY_CLIENT_SECRET` · `SPOTIFY_REFRESH_TOKEN` · `X_API_KEY` · `X_API_KEY_SECRET` · `X_ACCESS_TOKEN` · `X_ACCESS_TOKEN_SECRET`

## Known Issues

| ID | File | Issue | Priority |
|----|------|-------|----------|
| HR-02 | techs + word-cloud tests | **Closed** — `tests/test_techs.py` and word-cloud test modules have real coverage for `techs` + `scripts/word_clouds/` | — |
| HR-03 | `scripts/banner.py` | Monolithic (1700+ lines) — refactor candidate | P2 |
| HR-05 | `scripts/config.py` vs `scripts/word_clouds/generate.py` | Two WC config models — do not mix: YAML/`ProjectConfig` uses `WordCloudSettingsModel` (`scripts/config.py`); generator/CLI uses strict `WordCloudSettings` (`scripts/word_clouds/generate.py`, `extra="forbid"`) | P2 |
| HR-08 | `.env.example` | **Closed** — root `.env.example` documents local + CI secret placeholders | — |
| HR-10 | `scripts/banner.py` | `BannerConfig.output_path` defaults to `./assets/img/banner.svg`, not `.github/assets/img/banner.svg` — always override via `config.yaml` | P3 |

### Strategic Improvements (P3 — Future Work)

| ID | Area | Description |
|----|------|-------------|
| ST-01 | `scripts/banner.py`, `scripts/readme_svg.py` | Plan migration from `svgwrite` (UNMAINTAINED) to `svg.py` (type-safe, actively maintained) |
| ST-02 | Asset pipeline | Add SVG optimization post-processing via `scour` (~48% size reduction) or `npx svgo --multipass` |
| ST-03 | Testing | Add `syrupy` snapshot testing with `SVGImageSnapshotExtension` for visual regression safety |
| ST-04 | CLI | Add local preview command (`cli preview <generator>`) for faster creative iteration |
| ST-05 | README | Cards: SVG `@media (prefers-color-scheme: dark)` (shipped). Banner keeps `<picture>`. Dual-file card `<picture>` only if media-query QA fails (F7) |
| ST-06 | `scripts/config.py` | Switch to native `YamlConfigSettingsSource` from `pydantic-settings` |
| ST-07 | `scripts/config.py` | Use Pydantic v2 discriminated unions for type-safe generator config dispatch |
| ST-08 | `scripts/` | Sub-package restructure: `generators/`, `data/`, `core/` |

## Sub-file Index

| File | Load context | Contents |
|------|-------------|----------|
| [`scripts/AGENTS.md`](scripts/AGENTS.md) | When editing any script module | Module map, Pydantic patterns, per-generator reference, CLI extension guide |
| [`tests/AGENTS.md`](tests/AGENTS.md) | When writing or running tests | Run commands, coverage status, test patterns, writing guide |
| [`docs/content/docs/scripts/living-art-modes.mdx`](docs/content/docs/scripts/living-art-modes.mdx) | Living-art styles / artifact contract | Mode matrix; pairs with `scripts/art/timelapse.py` `_STYLE_REGISTRY` |
| [`docs/`](docs/) | When editing dev documentation | Fumadocs (Next.js 15) site; `cd docs && pnpm dev` to preview |

## Common Failure Modes

| Symptom | Cause | Fix |
|---------|-------|-----|
| `FileNotFoundError: Default background SVG not found` | `icon.svg` missing | Background is optional (default=None); only set `background_svg` in config if you want a custom background |
| `ImportError: No module named 'segno'` | QR extras not installed | `uv sync --locked --extra qr` (or `--locked --all-extras`) |
| `ImportError: No module named 'wordcloud'` | word-clouds extras not installed | `uv sync --locked --extra word-clouds` (or `--locked --all-extras`) |
| `ValidationError` from `WordCloudSettings` | Extra keys on strict model | Remove unknown fields — `extra="forbid"` in `WordCloudSettings` (`word_clouds/generate.py`) |
| `load_config()` returns defaults silently | `config.yaml` missing or empty | Auto-creates with defaults; edit the created file |
| `generate qr` Cairo error (macOS) | Cairo not in dyld path | `export DYLD_LIBRARY_PATH=$(brew --prefix cairo)/lib:$DYLD_LIBRARY_PATH` |
| `generate qr` Cairo / cairocffi error (Linux CI) | System Cairo libs missing | `sudo apt-get update && sudo apt-get install -y libcairo2 libcairo2-dev` (plus pkg-config as needed) |
| Dark banner missing / yellow warning only | `banner-dark.svg` generation failed after light succeeded | Re-run `uv run readme generate banner`; check `BannerConfig` / SVGO; light `banner.svg` is still valid |
| `uv sync --locked` fails / resolver conflict | `uv.lock` out of date vs `pyproject.toml` | Update lock with `uv lock` (then commit both), or temporarily `uv sync --all-extras` for local-only exploration |
| Living-art GIF rasterization fails | `rsvg-convert` / librsvg missing | `sudo apt-get install -y librsvg2-bin` (matches CI `generate-event-art`) |
| `noise` module warning but continues | `noise` package absent | Expected — `NoiseHandler` falls back to trig automatically |
| `starred` command not found | script-tools not installed or command not run through `uv` | `uv sync --locked --extra script-tools` then `uv run starred ...` |
