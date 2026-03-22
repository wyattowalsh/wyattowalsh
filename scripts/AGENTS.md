# scripts/AGENTS.md

> Deep reference for the `scripts/` asset generation package. Parent: [../AGENTS.md](../AGENTS.md)

## Module Map

| File | Lines | Responsibility | Key Exports |
|------|-------|---------------|-------------|
| `_github_http.py` | 39 | Shared GitHub API HTTP helpers (no heavy deps) | `_headers()`, `_graphql()` |
| `animated_art.py` | 960 | CSS-animated SVG story-art (Cosmic Genesis + Unfurling Spiral) driven by historical data | `generate_animated_community_art()`, `generate_animated_activity_art()` |
| `banner.py` | 1730 | SVG banner generator | `BannerConfig`, `generate_banner()`, `NoiseHandler`, `ColorPalette` |
| `banner_patterns.py` | 46 | `PatternType` enum extracted from `banner.py` (zero heavy deps) | `PatternType` |
| `cli/` | — | Typer CLI package (see submodules below) | `app`, `DEFAULT_CONFIG_PATH` |
| `cli/__init__.py` | 9 | Package init; re-exports `app` and `DEFAULT_CONFIG_PATH` | `app`, `DEFAULT_CONFIG_PATH` |
| `cli/__main__.py` | 6 | Enables `python -m scripts.cli` | — |
| `cli/_app.py` | 60 | Root Typer app, `--version` callback, sub-app registration | `app` |
| `cli/_display.py` | 55 | Shared display helpers: `OutputFormat` enum, `display_config()` | `OutputFormat`, `display_config()` |
| `cli/config_cmd.py` | 165 | Config subcommands: `view`, `save`, `generate-default` | `config_app` |
| `cli/settings_cmd.py` | 45 | `show-settings` command | `show_settings()` |
| `cli/generate.py` | 1334 | Generate subcommands: `banner`, `qr`, `word-cloud`, `skills`, `generative`, `animated`, `readme-sections`, `all` | `generate_app` |
| `cli/dev.py` | 185 | Dev tools (replaces Makefile): `install`, `format`, `lint`, `test`, `clean`, `docs`, `update-deps` | `dev_app` |
| `config.py` | 257 | Pydantic config models + YAML I/O | `ProjectConfig`, `load_config()`, `save_config()`, `BannerSettings`, `VCardDataModel`, `QRCodeSettings`, `WordCloudSettingsModel` |
| `fetch_history.py` | 332 | GitHub contribution-history collector with Link-header pagination (REST + GraphQL) | `collect_history()` |
| `fetch_metrics.py` | 283 | GitHub REST + GraphQL metrics collector; outputs flat JSON dict | `collect()` |
| `generative.py` | 277 | Static generative art (Clifford attractor + Phyllotaxis/flow-field) seeded by profile metrics | `generate_community_art()`, `generate_activity_art()` |
| `qr.py` | 253 | Artistic vCard QR code | `QRCodeGenerator` |
| `readme_sections.py` | 1548 | README dynamic section generators (badges, project cards, blog posts); orchestrates all section content | `generate_readme_sections()`, `ReadmeSectionsSettings` |
| `readme_svg.py` | 1330 | Reusable SVG rendering helpers for README components (cards, charts, blocks) | `SvgCard`, `SvgBlock`, `SvgBlockRenderer`, `SvgRepoCardRenderer`, `SvgBlogCardRenderer`, `SvgConnectCardRenderer`, `ReadmeSvgAssetBuilder`, `SvgAssetWriter` |
| `skills.py` | 153 | shields.io badge HTML generator from `SkillsSettings`; injects between README comment markers | `SkillsBadgeGenerator` |
| `techs.py` | 315 | Parse techs.md proficiency data | `Technology`, `load_technologies()`, `parse_technology_line()`, `display_technologies()` |
| `utils.py` | 172 | Loguru + Rich setup | `get_logger()`, `create_progress()`, `console` |
| `word_clouds/` | — | Word cloud subpackage — generation pipeline + SVG renderers | — |
| `word_clouds/generate.py` | 402 | Generation pipeline, CLI, settings, markdown parsing | `WordCloudGenerator`, `WordCloudSettings`, `parse_markdown_for_word_cloud_frequencies()` |
| `word_clouds/core.py` | 78 | Shared data types and font constants | `PlacedWord`, `BBox`, `FONT_STACK` |
| `word_clouds/colors.py` | 473 | OKLCH color palettes and domain clustering | `COLOR_FUNCS`, `_classify_word()` |
| `word_clouds/engine.py` | 352 | Abstract base SVG renderer | `SvgWordCloudEngine` |
| `word_clouds/solvers.py` | 1828 | 25 metaheuristic optimization solvers + aesthetic cost function | `_META_SOLVERS`, `_aesthetic_cost()` |
| `word_clouds/wordle.py` | 200 | Classic Wordle spiral placement | `WordleRenderer` |
| `word_clouds/clustered.py` | 195 | Semantic clustering layout | `ClusteredRenderer` |
| `word_clouds/typographic.py` | 93 | Editorial baseline-grid layout | `TypographicRenderer` |
| `word_clouds/shaped.py` | 319 | Shape-constrained placement | `ShapedRenderer` |
| `word_clouds/metaheuristic.py` | 499 | 25-frame animated renderer + registry | `MetaheuristicAnimRenderer`, `RENDERERS`, `get_renderer()` |
| `art/shared.py` | ~276 | Shared noise/color/math utilities for generative art | `Noise2D`, `oklch()`, `seed_hash()`, `compute_maturity()`, `make_radial_gradient()`, `make_linear_gradient()`, `parse_cli_args()` |
| `art/ink_garden.py` | 2027 | Procedural botanical SVG garden — species-classified trees, leaves, blooms, insects, webs | `generate(metrics, *, seed, maturity) -> str` |
| `art/_dev_profiles.py` | 64 | Mock GitHub profiles for local animation testing | `PROFILES` |
| `art/animate.py` | — | Multi-frame animation driver; calls `ink_garden.generate()` per maturity step | (see module docstring) |
| `art/topography.py` | 1170 | Topographic contour generative art — hillshade, rivers, contour lines, compass rose | `generate(metrics, *, seed, maturity) -> str` |

Always use **relative imports** within `scripts/`:
```python
from .config import ProjectConfig, load_config
from .utils import get_logger
```

## Pydantic v2 Patterns

All models use Pydantic v2:

```python
from pydantic import BaseModel, Field, ConfigDict
from pydantic_settings import BaseSettings, SettingsConfigDict

# YAML-backed settings — use BaseSettings with extra="ignore"
class ProjectConfig(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")  # silently drops unknown keys
    banner_settings: Optional[BannerSettings] = None

# Strict data models — use BaseModel with extra="forbid"
class WordCloudSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")  # raises ValidationError on unknown keys
    width: int = Field(default=800, ge=100)

# Serialization
cfg.model_dump(mode="python")           # Python-native types (for YAML)
cfg.model_dump(exclude_unset=True)      # Only user-set fields (for merging)
cfg.model_dump_json(indent=2)           # JSON string (for display)
```

⚠️ **Two distinct word-cloud config models — do not confuse:**
- `WordCloudSettingsModel` in `config.py` — top-level YAML config, part of `ProjectConfig`
- `WordCloudSettings` in `word_clouds.py` — internal generator config, `extra="forbid"`

## Logging Pattern

```python
from .utils import get_logger

logger = get_logger(module=__name__)  # bind module context

logger.info("Generated banner at {path}", path=output_path)
logger.debug("Config dump: {cfg}", cfg=cfg.model_dump())
logger.warning("Cairo not available, falling back")
logger.error("Generation failed: {e}", exc_info=True)
```

**Sinks** (configured in `utils.py`): Rich console (INFO+) · `logs/text/{date}.log` (10MB rotation, 10d) · `logs/json/{date}.json` (10MB rotation, 10d).

⚠️ `utils.py` calls `loguru_logger.remove()` at module import time. Importing any `scripts.*` module resets all Loguru handlers. Do not add file I/O, network calls, or subprocess calls to `utils.py` — it is imported by every other module.

## CLI Extension Guide

To add a new generator (e.g., `readme generate my-asset`):

1. Add a config model in `config.py` and attach it to `ProjectConfig`.

2. Add a new command function in `cli/generate.py`:
   ```python
   @generate_app.command(name="my-asset", help="Generate my asset.")
   def my_asset(
       config_path: Annotated[Optional[Path], typer.Option("--config-path", ...)] = None,
   ) -> None:
       from ..my_module import MyGenerator
       proj_config = _load_project_config(config_path)
       gen = MyGenerator(proj_config.my_asset_settings)
       gen.generate()
   ```

3. Optionally add the call to the `all_assets()` command in `cli/generate.py`.

To add a dev tool, add a command to `cli/dev.py`.

## Banner (`banner.py`)

Entry: `uv run readme generate banner` → `cli/generate.py:banner()` → `generate_banner(BannerConfig)`

**Key classes:**
- `BannerConfig` — top-level config aggregating `ColorPalette`, `Typography`, `VisualEffects`, plus `title`, `subtitle`, `width` (1200), `height` (630), `output_path`, `optimize_with_svgo`
- `PatternType` enum — **active:** `LORENZ`, `NEURAL`, `FLOW`, `MICRO`, `AIZAWA`, `CLIFFORD` · **dead (no draw fn):** `REACTION`, `FLAME`, `PDJ`, `IKEDA`
- `NoiseHandler` — lazy Perlin noise; auto-falls-back to trig if `noise` package absent
- `ColorPalette` — primary/secondary/accent/dark-mode palette generation

**Generation sequence:**
`define_background()` → `add_glassmorphism_effect()` → `draw_lorenz()` → `draw_aizawa()` → `draw_flow_patterns()` → `draw_neural_network()` → `add_micro_details()` → `add_octocat()` → `add_title_and_subtitle()` → optional `optimize_with_svgo()` (requires `svgo` binary)

⚠️ `BannerConfig.output_path` defaults to `"./assets/img/banner.svg"` — always override via `config.yaml` to `.github/assets/img/banner.svg`.

## QR Code (`qr.py`)

Entry: `uv run readme generate qr` → `cli/generate.py:qr()` → `QRCodeGenerator.generate_artistic_vcard_qr()`

**System Cairo required** (macOS: `brew install cairo`). Set before running:

```bash
export DYLD_LIBRARY_PATH=$(brew --prefix cairo)/lib:$DYLD_LIBRARY_PATH
```

**`QRCodeGenerator.__init__(default_background_path, default_output_dir, default_scale)`:**
- Raises `FileNotFoundError` if background SVG does not exist
- Default background: `.github/assets/img/icon.svg` (must exist before generation)
- Raises `OSError` if output directory cannot be created

**`generate_artistic_vcard_qr(vcard_details, output_filename, error_correction, scale, background_path)`:**
1. Builds vCard 3.0 string from `VCardDataModel` (supports `X-ABLabel` for URL items)
2. `segno.make(payload, error=error_correction, micro=False)`
3. `qrcode.to_artistic(background=str(bg_path), target=str(output_path), scale=scale)`
4. Returns `Path` to generated PNG
- Valid error correction: `"L"`, `"M"`, `"Q"`, `"H"`

## Word Clouds (`word_clouds.py`)

Entry: `uv run readme generate word-cloud --from-topics-md` / `--from-languages-md`

**Module-level path constants:**
```python
PROFILE_IMG_OUTPUT_DIR = Path(".github/assets/img")
TOPICS_MD_PATH         = Path(".github/assets/topics.md")
LANGUAGES_MD_PATH      = Path(".github/assets/languages.md")
DEFAULT_FONT_PATH      = Path(".github/assets/fonts/Montserrat-ExtraBold.ttf")
DEFAULT_MASK_PATH      = Path(".github/assets/img/icon.svg")
```

**Key API:**
- `parse_markdown_for_word_cloud_frequencies(md_file_path) -> Dict[str, float]` — parses Markdown list items into term frequency counts; raises `FileNotFoundError` on missing file
- `primary_color_func`, `analogous_color_func`, `complementary_color_func`, `triadic_color_func` — color theory functions for `WordCloud(color_func=...)`
- `WordCloudGenerator(settings: WordCloudSettings).generate(text_input=None, frequencies=None) -> Optional[Path]`
- `WordCloudSettings(BaseModel)` — strict `extra="forbid"`, 40+ configurable params

## Techs (`techs.py`)

Parses structured `techs.md` with proficiency levels 1–5.

**Expected `techs.md` format:**
```markdown
## Programming Languages
- Python (Level: 5) - Primary language
- Go (Level: 3)

## Cloud & DevOps
- Docker (Level: 4)
```

**`Technology(BaseModel)`:** `name: str`, `level: int` (Pydantic `ge=1, le=5`), `category: Optional[str]`, `notes: Optional[str]`

**API:** `load_technologies(path) -> List[Technology]` · `parse_technology_line(line, category) -> Optional[Technology]` · `display_technologies(techs)` → Rich Table

⚠️ `topics.md` and `languages.md` (generated by `starred`) use a **different Markdown format** — parsed by `parse_markdown_for_word_cloud_frequencies()`, not `load_technologies()`.

## Adding Dependencies

```bash
# Runtime dependency
uv add <package>

# Edit pyproject.toml [project.optional-dependencies] then sync
uv sync --all-groups

# Install single extra locally (bypasses lockfile — dev only)
uv pip install -e ".[qr]"

# Never use:
pip install <package>
```

After any `pyproject.toml` change, always commit both `pyproject.toml` and `uv.lock` together.
