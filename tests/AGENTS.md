# tests/AGENTS.md

> Test suite reference for `wyattowalsh`. Parent: [../AGENTS.md](../AGENTS.md)

## Run Commands

```bash
# Full suite (parallel, all plugins from pyproject.toml)
uv run readme dev test

# Direct equivalent
uv run python -m pytest

# No parallelism (for debugging failures)
uv run python -m pytest -n 0 -v

# Single file
uv run python -m pytest tests/test_banner.py -v

# Single test
uv run python -m pytest tests/test_qr.py::TestQRCodeGenerator::test_init_success -v

# Terminal coverage summary (in addition to HTML report)
uv run python -m pytest --cov=./scripts --cov-report=term-missing

# Skip integration tests requiring Cairo
uv run python -m pytest -m "not integration"
```

**Output locations:** `logs/report.html` (HTML report) · `logs/coverage/` (coverage HTML) · `logs/.coverage` (data) · `logs/pytest-logs.txt` (log file)

## pytest Config (from `pyproject.toml`)

Key `addopts` flags decoded:

| Flag | Effect |
|------|--------|
| `-n auto` | Parallel via pytest-xdist (all CPU cores) |
| `--verbose` | Full test names |
| `--hypothesis-show-statistics` | Hypothesis strategy stats after run |
| `--html=logs/report.html --self-contained-html` | Standalone HTML report |
| `--emoji` | Emoji pass/fail indicators |
| `--instafail` | Print failures immediately |
| `--cov=./scripts --cov-append` | Coverage for `scripts/` |
| `--cov-report html:logs/coverage` | HTML coverage report |
| `timeout = 500` | 500s per test (for Cairo/image integration tests) |

`required_plugins`: pytest-sugar, pytest-html, pytest-emoji, pytest-icdiff, pytest-instafail, pytest-timeout, pytest-benchmark, pytest-cov (all must be installed or pytest refuses to run).

## Coverage Status

| Module | Lines | Test File | Status |
|--------|-------|-----------|--------|
| `scripts/banner.py` | 1730 | `test_banner.py` | ✅ Covered |
| `scripts/qr.py` | 253 | `test_qr.py` | ✅ Covered |
| `scripts/cli/` | — | `test_cli.py` | ✅ Covered (CLI refactored to package) |
| `scripts/utils.py` | 172 | `test_utils.py` | ✅ Covered |
| `scripts/config.py` | 257 | (indirect via CLI + QR tests) | ⚠️ Indirect only |
| `scripts/techs.py` | 315 | `test_techs.py` | ❌ Empty — zero coverage |
| `scripts/word_clouds.py` | 1585 | `test_word_clouds.py` | ❌ Empty — zero coverage |
| `scripts/art/ink_garden.py` | 2027 | `test_ink_garden.py` | ✅ Smoke + golden file regression tests |
| `scripts/fetch_metrics.py` | — | `test_fetch_metrics.py` | ✅ New — unit tests for metrics collection |
| Living art media outputs | — | `test_living_art_media.py` | ⏭️ Skipped — requires pre-generated artifacts |
| Blog card contracts | — | `test_card_contracts_blog_red.py` | 🔴 RED — unimplemented features |
| README GFM UX | — | `test_readme_gfm_ux.py` | ⏭️ Skipped — requires full pipeline |
| `scripts/readme_sections.py` | — | `test_readme_sections.py` | ✅ Covered |
| `scripts/readme_svg.py` | — | `test_readme_svg.py` | ✅ Covered |
| `scripts/skills.py` | — | `test_skills.py` | ✅ Covered |
| Word cloud features | — | `test_word_clouds_red.py` | 🔴 RED — unimplemented (xfail) |

## Test File Patterns

### `test_banner.py`
- Fixture: `default_banner_config: BannerConfig`
- Imports from `scripts.banner`: all generation functions + `BannerConfig`, `ColorPalette`, `NoiseHandler`, `PatternType`, `Point3DModel`
- Pattern: patches `svgwrite.Drawing` with `MagicMock`; uses `tmp_path` for file output tests

### `test_qr.py`
- Fixtures: `mock_project_root(tmp_path)` — creates `.github/assets/img/icon.svg`; `default_vcard_data: VCardDataModel`; `qr_generator: QRCodeGenerator`
- Cairo detection gate:
  ```python
  try:
      import cairocffi; cairocffi.cairo_version_string(); cairo_available = True
  except Exception:
      cairo_available = False
  ```
  Integration tests: `@pytest.mark.skipif(not cairo_available, reason="Cairo not available")`
- Tests: init errors (`FileNotFoundError`, `OSError`), vCard string construction, error correction validation, segno + `to_artistic` call chain

### `test_cli.py`
- Uses `typer.testing.CliRunner`
- Imports `app` from `scripts.cli` (now a package)
- Pattern: `result = runner.invoke(app, ["generate", "banner"]); assert result.exit_code == 0`

### `test_utils.py`
- **Critical:** `reset_loguru_handlers` autouse fixture removes Loguru sinks before each test — required because `scripts/utils.py` calls `loguru_logger.remove()` at import time
- Uses `importlib.reload(scripts.utils)` to re-trigger module-level Loguru setup
- Uses `pytest-mock` (`MockerFixture`) for patching Settings

## Writing New Tests

### Core rules
```python
# ✅ Always tmp_path for file I/O
def test_something(tmp_path):
    out = tmp_path / "result.png"
    ...

# ✅ No shared mutable state — tests run parallel with -n auto

# ✅ mock_project_root pattern for tests needing real asset files
@pytest.fixture
def mock_project_root(tmp_path, monkeypatch):
    img_dir = tmp_path / ".github" / "assets" / "img"
    img_dir.mkdir(parents=True)
    (img_dir / "icon.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg"/>')
    monkeypatch.chdir(tmp_path)
    return tmp_path
```

### Adding tests for `test_techs.py`
```python
from scripts.techs import Technology, load_technologies, parse_technology_line

SAMPLE_MD = "## Languages\n- Python (Level: 5) - Primary\n- Go (Level: 3)\n"

def test_parse_valid_line():
    result = parse_technology_line("- Python (Level: 5) - Primary", "Languages")
    assert result is not None
    assert result.name == "Python"
    assert result.level == 5
    assert result.notes == "Primary"

def test_level_constraint_enforced():
    with pytest.raises(ValidationError):
        Technology(name="X", level=6)  # ge=1, le=5

def test_load_technologies(tmp_path):
    md = tmp_path / "techs.md"
    md.write_text(SAMPLE_MD)
    techs = load_technologies(md)
    assert len(techs) == 2
    assert techs[0].category == "Languages"
```

### Adding tests for `test_word_clouds.py`
```python
from scripts.word_clouds import (
    WordCloudGenerator, WordCloudSettings,
    parse_markdown_for_word_cloud_frequencies,
)
from unittest.mock import patch, MagicMock

def test_parse_frequencies(tmp_path):
    md = tmp_path / "topics.md"
    md.write_text("- Python\n- JavaScript\n- Go\n")
    freqs = parse_markdown_for_word_cloud_frequencies(md)
    assert "Python" in freqs

def test_parse_frequencies_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        parse_markdown_for_word_cloud_frequencies(tmp_path / "missing.md")

def test_word_cloud_settings_rejects_unknown():
    with pytest.raises(ValidationError):
        WordCloudSettings(nonexistent_key="value")  # extra="forbid"

def test_generate_mocked(tmp_path):
    settings = WordCloudSettings(output_dir=str(tmp_path), output_filename="out.png")
    with patch("scripts.word_clouds.WordCloud") as mock_wc:
        mock_img = MagicMock()
        mock_wc.return_value.generate_from_text.return_value = mock_img
        gen = WordCloudGenerator(settings)
        gen.generate(text_input="Python Go TypeScript Cloud")
```

### Hypothesis (property-based) — good candidates
```python
from hypothesis import given, strategies as st
from scripts.techs import parse_technology_line
from scripts.techs import Technology

@given(st.text(min_size=1))
def test_parse_technology_line_never_crashes(line):
    # Pure function — must never raise, only return None or Technology
    result = parse_technology_line(line, "Test")
    assert result is None or isinstance(result, Technology)
```

### pytest-benchmark — for generation performance
```python
def test_banner_generation_perf(benchmark, default_banner_config, tmp_path):
    default_banner_config.output_path = str(tmp_path / "banner.svg")
    benchmark(generate_banner, default_banner_config)
```
