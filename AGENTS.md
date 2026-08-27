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
| Generate WakaTime README section | `uv run readme generate wakatime` |
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
│   │   ├── generate/    # Generate subcommands by domain (banner, qr, wc, …)
│   │   ├── config_cmd.py # Config subcommands (view, save, generate-default)
│   │   ├── settings_cmd.py # show-settings command
│   │   └── dev.py       # Dev tools (format, lint, test, clean, docs)
│   ├── quality/         # Structured quality-gate helpers + ty warning baseline
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
│   ├── wakatime_readme.py # First-party WakaTime README section collector/generator
│   ├── spotify_auth.py  # Spotify loopback auth-code helper
│   ├── skills.py        # shields.io badge generator from skills.yaml
│   ├── generative.py    # Static generative art (Clifford/Phyllotaxis)
│   ├── fetch_metrics.py # GitHub GraphQL metrics collector
│   ├── fetch_history.py # GitHub commit history collector
│   ├── _github_http.py  # Shared GitHub API HTTP helpers
│   ├── techs.py         # Parse techs.md → Technology objects
│   └── art/             # Generative / living-art subpackage (→ scripts/art/AGENTS.md)
│       ├── shared/      # Focused shared utils (compat re-export package)
│       ├── ink_garden.py # Procedural botanical SVG garden
│       ├── topography.py # Topographic contour art
│       ├── timelapse.py # Living-art style registry + GIF driver
│       ├── artifacts.py # Manifest / gallery / docs-showcase sync
│       ├── animate.py   # Multi-frame animation driver
│       └── _dev_profiles.py # Mock profiles for local animation testing
├── tests/               # pytest suite (→ tests/AGENTS.md)
├── docs/                # Fumadocs 16 on Next.js 16 dev docs site
├── .github/
│   ├── workflows/profile-updater.yml  # Single unified CI workflow
│   └── assets/img/      # Generated: banner*.svg, qr*.png, wordcloud_*.svg, living-*.gif
├── config.yaml          # Edit this to configure generation params
├── skills.yaml          # Skills badge definitions
└── pyproject.toml       # Metadata, deps, tool configs
```

**Asset pipeline** (CI: `.github/workflows/profile-updater.yml` — daily 1AM UTC, push to `main`/`master`/`dev`, manual dispatch):

Jobs upload artifacts; a single **`finalize`** job is the sole first-party git writer. Prefer `uv sync --locked` (+ extras as needed) — this repo has no `[dependency-groups]` in `pyproject.toml`.

1. **`update-starred-lists`** — `uv sync --locked` → first-party `python -m scripts.starred_lists` (one strict GraphQL traversal, transactional language/topic publication) → validated artifact `languages.md` + `topics.md`
2. **`generate-assets`** (needs starred) — `uv sync --extra qr --extra word-clouds` → `generate qr` / typographic word clouds → verify the pinned light/dark banner pair (do not regenerate) → structurally validate and upload exactly `qr.png`, the two typographic word-cloud SVGs, and the light/dark banner pair
3. **Living-art lane** — `prepare-event-art-inputs` fetches one metrics/history bundle and exports `LIVING_ART_STYLE_KEYS`; six read-only `generate-event-art` matrix children render isolated canonical GIFs; `assemble-event-art` validates the merged exact-six fleet and uploads the living-art staging artifact
4. **`generate-profile-metrics`** — `uv sync --locked` → repo-owned supplemental metrics cards (languages/habits/music/posts; no lowlighter in production; never Spotify on any Action `with:`) → metrics artifact
5. **`update-readme-wakatime`** — first-party `generate wakatime` (no `anmol098/waka-readme-stats`) → `waka-readme` artifact (`waka-section.md`); `contents: read` only
6. **`finalize`** (needs assets ∥ assembled art ∥ metrics ∥ waka) — download artifacts → apply Waka markers → `generate readme-sections` → `generate skills` → ordered commits + one push

Optional manual lane: **`probe-full-metrics`** (workflow_dispatch `metrics_probe_mode=true` only) — diagnostic `lowlighter/metrics` pin (`v3.34`); probe-only habits/activity diagnostics; `plugin_music: no`; does not update the profile.

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
`WAKATIME_API_KEY` · `METRICS_TOKEN` · `SPOTIFY_CLIENT_ID` · `SPOTIFY_CLIENT_SECRET` · `SPOTIFY_REFRESH_TOKEN` · `X_API_KEY` · `X_API_KEY_SECRET` · `X_ACCESS_TOKEN` · `X_ACCESS_TOKEN_SECRET`

## Known Issues

| ID | File | Issue | Priority |
|----|------|-------|----------|
| HR-02 | techs + word-cloud tests | **Closed** — `tests/test_techs.py` and word-cloud test modules have real coverage for `techs` + `scripts/word_clouds/` | — |
| HR-03 | `scripts/banner.py` | Monolithic (1700+ lines) — refactor candidate | P2 |
| HR-05 | `scripts/config.py` vs `scripts/word_clouds/generate.py` | **Closed** — dual models remain (YAML vs strict runtime) but bridge via `WordCloudSettingsModel.to_word_cloud_settings()` / `WordCloudSettings.from_yaml_model()` / `to_yaml_model()` | — |
| HR-08 | `.env.example` | **Closed** — root `.env.example` documents local + CI secret placeholders | — |
| HR-10 | `scripts/banner.py` | **Closed** — `BannerConfig.output_path` defaults to `.github/assets/img/banner.svg`; YAML `BannerSettings` adapts via `to_banner_config()` / `BannerConfig.from_banner_settings()` | — |

### Strategic Improvements (P3 — Future Work)

| ID | Area | Description |
|----|------|-------------|
| ST-01 | `scripts/banner.py`, `scripts/readme_svg.py` | **Closed** — banner/generative use `scripts/svg_drawing.py` string builders (svgwrite removed); readme_svg already string-based | — |
| ST-02 | Asset pipeline | **Closed** — banner SVG optimization uses the shared SVGO helper; README cards intentionally bypass it to preserve CSS media rules |
| ST-03 | Testing | Add `syrupy` snapshot testing with `SVGImageSnapshotExtension` for visual regression safety |
| ST-04 | CLI | Add local preview command (`cli preview <generator>`) for faster creative iteration |
| ST-05 | README | Cards: SVG `@media (prefers-color-scheme: dark)` (shipped). Banner keeps `<picture>`. Dual-file card `<picture>` only if media-query QA fails (F7) |
| ST-06 | `scripts/config.py` | **Closed** — native `YamlConfigSettingsSource` now loads UTF-8 YAML while direct construction remains warning-free |
| ST-07 | `scripts/config.py` | Use Pydantic v2 discriminated unions for type-safe generator config dispatch |
| ST-08 | `scripts/` | Sub-package restructure: `generators/`, `data/`, `core/` |

## Sub-file Index

| File | Load context | Contents |
|------|-------------|----------|
| [`scripts/AGENTS.md`](scripts/AGENTS.md) | When editing any script module | Module map, Pydantic patterns, per-generator reference, CLI extension guide |
| [`tests/AGENTS.md`](tests/AGENTS.md) | When writing or running tests | Run commands, coverage status, test patterns, writing guide |
| [`docs/content/docs/scripts/living-art-modes.mdx`](docs/content/docs/scripts/living-art-modes.mdx) | Living-art styles / artifact contract | Mode matrix; pairs with `scripts/art/timelapse.py` `_STYLE_REGISTRY` |
| [`docs/`](docs/) | When editing dev documentation | Fumadocs 16 on Next.js 16; `cd docs && pnpm dev` to preview |

## Common Failure Modes

| Symptom | Cause | Fix |
|---------|-------|-----|
| `FileNotFoundError: Default background SVG not found` | `icon.svg` missing | Background is optional (default=None); only set `background_svg` in config if you want a custom background |
| `ImportError: No module named 'segno'` | QR extras not installed | `uv sync --locked --extra qr` (or `--locked --all-extras`) |
| `ImportError: No module named 'wordcloud'` | word-clouds extras not installed | `uv sync --locked --extra word-clouds` (or `--locked --all-extras`) |
| `ImportError: No module named 'mealpy'` / `scipy` / `matplotlib` | science extras not installed | `uv sync --locked --extra science` (pulled by `word-clouds`; or `--locked --all-extras` for living-art CI) |
| `ValidationError` from `WordCloudSettings` | Extra keys on strict model | Remove unknown fields — `extra="forbid"` in `WordCloudSettings` (`word_clouds/generate.py`) |
| `load_config()` returns defaults silently | `config.yaml` missing or empty **locally** | Auto-creates with defaults; edit the created file. In CI (`CI` / `GITHUB_ACTIONS`) this fails closed instead |
| `generate qr` Cairo error (macOS) | Cairo not in dyld path | `export DYLD_LIBRARY_PATH=$(brew --prefix cairo)/lib:$DYLD_LIBRARY_PATH` |
| `generate qr` Cairo / cairocffi error (Linux CI) | System Cairo libs missing | `sudo apt-get update && sudo apt-get install -y libcairo2 libcairo2-dev` (plus pkg-config as needed) |
| Banner generation exits nonzero | Either the light or dark SVG failed to materialize as a non-empty file | Check `BannerConfig` / SVGO and rerun `uv run readme generate banner`; the command requires a fresh matched pair |
| `uv sync --locked` fails / resolver conflict | `uv.lock` out of date vs `pyproject.toml` | Update lock with `uv lock` (then commit both), or temporarily `uv sync --all-extras` for local-only exploration |
| Living-art GIF rasterization fails | `rsvg-convert` / librsvg missing | `sudo apt-get install -y librsvg2-bin` (matches CI `generate-event-art`) |
| `noise` module warning but continues | `noise` package absent | Expected — `NoiseHandler` falls back to trig automatically |
| Starred-list generation fails | GitHub token, GraphQL shape, pagination, or output validation failed | Export `GITHUB_TOKEN`, then run `uv run python -m scripts.starred_lists --owner <owner> --languages-output .github/assets/languages.md --topics-output .github/assets/topics.md` and inspect the bounded error |
