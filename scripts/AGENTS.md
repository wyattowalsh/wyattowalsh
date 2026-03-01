# scripts/AGENTS.md

> Deep reference for the `scripts/` asset generation package. Parent: [../AGENTS.md](../AGENTS.md)

## Module Map

| File | Lines | Responsibility | Key Exports |
|------|-------|---------------|-------------|
| `cli.py` | 870 | Typer CLI entry point | `app`, `EntityType`, `generate()`, `config_cmd()` |
| `config.py` | 257 | Pydantic config models + YAML I/O | `ProjectConfig`, `load_config()`, `save_config()`, `BannerSettings`, `VCardDataModel`, `QRCodeSettings`, `WordCloudSettingsModel` |
| `utils.py` | 172 | Loguru + Rich setup | `get_logger()`, `create_progress()`, `console`, `get_project_root()` |
| `banner.py` | 1730 | SVG banner generator | `BannerConfig`, `generate_banner()`, `PatternType`, `NoiseHandler`, `ColorPalette` |
| `qr.py` | 253 | Artistic vCard QR code | `QRCodeGenerator` |
| `word_clouds.py` | 1585 | Word cloud generation | `WordCloudGenerator`, `WordCloudSettings`, `parse_markdown_for_word_cloud_frequencies()` |
| `techs.py` | 315 | Parse techs.md proficiency data | `Technology`, `load_technologies()`, `parse_technology_line()`, `display_technologies()` |

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

To add a new generator (e.g., `readme generate my_asset`):

1. Add enum value to `EntityType` in `cli.py`:
   ```python
   class EntityType(str, Enum):
       MY_ASSET = "my_asset"
   ```

2. Add a config model in `config.py` and attach it to `ProjectConfig`.

3. Add a branch in `generate()` command in `cli.py`:
   ```python
   elif entity == EntityType.MY_ASSET:
       from .my_module import MyGenerator
       gen = MyGenerator(cfg.my_asset_settings)
       gen.generate()
   ```

4. Add Makefile target and include in `generate` target.

## Banner (`banner.py`)

Entry: `make generate-banner` → `cli.py` → `generate_banner(BannerConfig)`

**Key classes:**
- `BannerConfig` — top-level config aggregating `ColorPalette`, `Typography`, `VisualEffects`, plus `title`, `subtitle`, `width` (1200), `height` (630), `output_path`, `optimize_with_svgo`
- `PatternType` enum — **active:** `LORENZ`, `NEURAL`, `FLOW`, `MICRO`, `AIZAWA` · **dead (no draw fn):** `REACTION`, `CLIFFORD`, `FLAME`, `PDJ`, `IKEDA`
- `NoiseHandler` — lazy Perlin noise; auto-falls-back to trig if `noise` package absent
- `ColorPalette` — primary/secondary/accent/dark-mode palette generation

**Generation sequence:**
`define_background()` → `add_glassmorphism_effect()` → `draw_lorenz()` → `draw_aizawa()` → `draw_flow_patterns()` → `draw_neural_network()` → `add_micro_details()` → `add_octocat()` → `add_title_and_subtitle()` → optional `optimize_with_svgo()` (requires `svgo` binary)

⚠️ `BannerConfig.output_path` defaults to `"./assets/img/banner.svg"` — always override via `config.yaml` to `.github/assets/img/banner.svg`.

## QR Code (`qr.py`)

Entry: `make generate-qr` → `cli.py` → `QRCodeGenerator.generate_artistic_vcard_qr()`

**System Cairo required** (macOS: `brew install cairo`). Makefile sets:
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

Entry: `make generate-word-clouds` → two invocations: `--from-topics-md` + `--from-languages-md`

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
