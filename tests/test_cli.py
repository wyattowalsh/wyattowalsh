import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
import yaml
from typer.testing import CliRunner

from scripts.cli import app
from scripts.cli.generate import _wc_from_languages, _wc_from_topics, _wc_import
from scripts.config import ProjectConfig
from scripts.word_clouds import WordCloudSettings
from scripts.word_clouds.readability import LayoutReadabilitySettings


# Fixture for CliRunner
@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


class _CapturingWordCloudGenerator:
    last_settings: WordCloudSettings | None = None
    last_kwargs: dict[str, object] | None = None

    def __init__(self, base_settings: WordCloudSettings) -> None:
        type(self).last_settings = base_settings

    def generate(self, **kwargs):
        type(self).last_kwargs = kwargs
        return kwargs["output_path"]


# ------------------------------------------------------------------------------
# Tests for `config` command
# ------------------------------------------------------------------------------


def test_config_generate_default(runner: CliRunner, tmp_path: Path) -> None:
    """Test `config generate-default` command."""
    test_config_path = tmp_path / "test_cfg.yaml"
    result = runner.invoke(
        app, ["config", "generate-default", "--path", str(test_config_path)]
    )
    assert result.exit_code == 0
    assert test_config_path.exists()
    assert "Default configuration generated" in result.stdout
    # Verify content — config is saved as YAML
    with open(test_config_path) as f:
        content = yaml.safe_load(f)
        assert "banner_settings" in content
        assert "qr_code_settings" in content


def test_wc_from_topics_uses_metaheuristic_renderer_with_stable_filename(
    tmp_path: Path,
) -> None:
    topics_md = tmp_path / "topics.md"
    topics_md.write_text("- placeholder", encoding="utf-8")
    wc = SimpleNamespace(
        TOPICS_MD_PATH=topics_md,
        PROFILE_IMG_OUTPUT_DIR=tmp_path,
        parse_markdown_for_word_cloud_frequencies=lambda _: {"python": 4, "others": 2},
        WordCloudSettings=WordCloudSettings,
        WordCloudGenerator=_CapturingWordCloudGenerator,
    )

    result = _wc_from_topics(wc, None, [], 10, LayoutReadabilitySettings())

    assert result == tmp_path / "wordcloud_metaheuristic-anim_by_topics.svg"
    assert _CapturingWordCloudGenerator.last_settings is not None
    assert _CapturingWordCloudGenerator.last_settings.renderer == "metaheuristic-anim"
    assert _CapturingWordCloudGenerator.last_settings.max_words == 2
    assert _CapturingWordCloudGenerator.last_kwargs is not None
    assert _CapturingWordCloudGenerator.last_kwargs["frequencies"] == {
        "python": 4,
        "others": 2,
    }
    assert _CapturingWordCloudGenerator.last_kwargs["color_func_name"] == "ocean"


def test_wc_from_languages_uses_metaheuristic_renderer_with_stable_filename(
    tmp_path: Path,
) -> None:
    languages_md = tmp_path / "languages.md"
    languages_md.write_text("- placeholder", encoding="utf-8")
    wc = SimpleNamespace(
        LANGUAGES_MD_PATH=languages_md,
        PROFILE_IMG_OUTPUT_DIR=tmp_path,
        parse_markdown_for_word_cloud_frequencies=lambda _: {"Python": 5, "Others": 1},
        WordCloudSettings=WordCloudSettings,
        WordCloudGenerator=_CapturingWordCloudGenerator,
    )

    result = _wc_from_languages(wc, None, [], 10, LayoutReadabilitySettings())

    assert result == tmp_path / "wordcloud_metaheuristic-anim_by_languages.svg"
    assert _CapturingWordCloudGenerator.last_settings is not None
    assert _CapturingWordCloudGenerator.last_settings.renderer == "metaheuristic-anim"
    assert _CapturingWordCloudGenerator.last_settings.max_words == 2
    assert _CapturingWordCloudGenerator.last_kwargs is not None
    assert _CapturingWordCloudGenerator.last_kwargs["frequencies"] == {
        "Python": 5,
        "Others": 1,
    }
    assert _CapturingWordCloudGenerator.last_kwargs["color_func_name"] == "aurora"


def test_wc_import_exposes_word_cloud_interfaces() -> None:
    wc = _wc_import()

    assert hasattr(wc, "WordCloudSettings")
    assert hasattr(wc, "WordCloudGenerator")
    assert hasattr(wc, "parse_markdown_for_word_cloud_frequencies")


def test_config_view_generated_default(runner: CliRunner, tmp_path: Path) -> None:
    """Test `config view` after generating a default."""
    test_config_path = tmp_path / "view_cfg.yaml"
    # First, generate a default config
    runner.invoke(app, ["config", "generate-default", "--path", str(test_config_path)])

    result = runner.invoke(app, ["config", "view", "--path", str(test_config_path)])
    assert result.exit_code == 0
    assert "Current project configuration" in result.stdout
    assert "banner_settings" in result.stdout  # Check for a known key


def test_config_view_non_existent(runner: CliRunner, tmp_path: Path) -> None:
    """Test `config view` for a non-existent config file."""
    non_existent_path = tmp_path / "does_not_exist.yaml"
    result = runner.invoke(app, ["config", "view", "--path", str(non_existent_path)])
    assert result.exit_code == 1
    assert "Config file not found" in result.stdout


@patch("scripts.cli.config_cmd.load_config")
@patch("scripts.cli.config_cmd.save_config")
def test_config_save_existing(
    mock_save_config: MagicMock,
    mock_load_config: MagicMock,
    runner: CliRunner,
    tmp_path: Path,
) -> None:
    """Test `config save` for an existing config file."""
    test_config_path = tmp_path / "save_cfg.yaml"

    # Mock load_config to return a dummy ProjectConfig
    mock_load_config.return_value = ProjectConfig()

    result = runner.invoke(app, ["config", "save", "--path", str(test_config_path)])

    assert result.exit_code == 0
    mock_load_config.assert_called_once_with(test_config_path)
    mock_save_config.assert_called_once()  # With what args? Depends on implementation
    assert "Configuration successfully saved" in result.stdout


@patch("scripts.cli.config_cmd.save_config")
def test_config_save_new_default(
    mock_save_config: MagicMock, runner: CliRunner, tmp_path: Path
) -> None:
    """Test `config save` creates a new default config if one doesn't exist."""
    new_config_path = tmp_path / "new_default_cfg.yaml"
    # Ensure the file doesn't exist initially to trigger default creation path
    assert not new_config_path.exists()

    result = runner.invoke(app, ["config", "save", "--path", str(new_config_path)])

    assert result.exit_code == 0
    mock_save_config.assert_called_once()
    # The first arg to save_config should be a ProjectConfig instance
    assert isinstance(mock_save_config.call_args[0][0], ProjectConfig)
    assert mock_save_config.call_args[0][1] == new_config_path
    assert "Configuration successfully saved" in result.stdout


# ------------------------------------------------------------------------------
# Tests for `generate banner` command
# ------------------------------------------------------------------------------


@patch("scripts.banner.generate_banner")  # patch at the source module
@patch("scripts.cli.generate.load_config")
def test_generate_banner_basic(
    mock_load_config: MagicMock,
    mock_generate_banner_func: MagicMock,
    runner: CliRunner,
    tmp_path: Path,
) -> None:
    """Test basic invocation of `generate banner`."""
    test_config_path = tmp_path / "banner_gen_cfg.yaml"

    # Create a dummy config file or mock load_config effectively
    dummy_config = ProjectConfig(banner_settings={"title": "Test Banner"})
    with open(test_config_path, "w") as f:
        yaml.dump(dummy_config.model_dump(mode="json"), f)
    mock_load_config.return_value = dummy_config

    output_svg_path = tmp_path / "generated_banner.svg"

    result = runner.invoke(
        app,
        [
            "generate",
            "banner",
            "--config-path",
            str(test_config_path),
            "--output-path",
            str(output_svg_path),
        ],
    )

    assert result.exit_code == 0
    assert "SVG banner generated:" in result.stdout
    assert output_svg_path.name in result.stdout
    assert mock_generate_banner_func.called  # called once for light + once for dark
    # Check that BannerConfig was passed with correct output_path on the first call
    first_call_kwargs = mock_generate_banner_func.call_args_list[0].kwargs
    banner_config_arg = first_call_kwargs["cfg"]
    assert str(banner_config_arg.output_path) == str(output_svg_path)
    assert banner_config_arg.title == "Test Banner"  # From dummy_config


@patch("scripts.banner.generate_banner")  # patch at the source module
@patch("scripts.cli.generate.load_config")
def test_generate_banner_cli_overrides(
    mock_load_config: MagicMock,
    mock_generate_banner_func: MagicMock,
    runner: CliRunner,
    tmp_path: Path,
) -> None:
    """Test `generate banner` with CLI options overriding config."""
    test_config_path = tmp_path / "override_cfg.yaml"
    dummy_config = ProjectConfig(
        banner_settings={
            "title": "Config Title",
            "width": 1000,
            "height": 500,
            "optimize_with_svgo": True,
            "output_path": "config_banner.svg",  # Will be overridden
        }
    )
    with open(test_config_path, "w") as f:
        yaml.dump(dummy_config.model_dump(mode="json"), f)
    mock_load_config.return_value = dummy_config

    cli_output_svg_path = tmp_path / "cli_banner.svg"
    cli_title = "CLI Title"
    cli_width = 1200

    result = runner.invoke(
        app,
        [
            "generate",
            "banner",
            "--config-path",
            str(test_config_path),
            "--output-path",
            str(cli_output_svg_path),
            "--title",
            cli_title,
            "--width",
            str(cli_width),
        ],
    )

    assert result.exit_code == 0
    assert mock_generate_banner_func.called
    first_call_kwargs = mock_generate_banner_func.call_args_list[0].kwargs
    banner_config_arg = first_call_kwargs["cfg"]

    assert str(banner_config_arg.output_path) == str(
        cli_output_svg_path
    )  # CLI --output-path wins
    assert banner_config_arg.title == cli_title  # CLI --title wins
    assert banner_config_arg.width == cli_width  # CLI --width wins


# ------------------------------------------------------------------------------
# Tests for `show-settings` command
# ------------------------------------------------------------------------------


@patch("scripts.cli.settings_cmd.Settings")  # Mock the Settings class
def test_show_settings_json(mock_settings_class: MagicMock, runner: CliRunner) -> None:
    """Test `show-settings` command with JSON output (default)."""
    # Configure the mock Settings instance that will be created
    mock_settings_instance = MagicMock()
    # Simulate Pydantic's model_dump_json
    mock_settings_instance.model_dump_json.return_value = json.dumps(
        {"dummy_setting": "value", "another_setting": 123}, indent=2
    )
    mock_settings_class.return_value = mock_settings_instance

    result = runner.invoke(app, ["show-settings"])  # Default format is JSON

    assert result.exit_code == 0
    assert "Current Application Settings" in result.stdout
    assert '"dummy_setting": "value"' in result.stdout
    assert '"another_setting": 123' in result.stdout
    mock_settings_class.assert_called_once()
    mock_settings_instance.model_dump_json.assert_called_once_with(indent=2)


@patch("scripts.cli.settings_cmd.Settings")
@patch("scripts.cli._display.yaml")  # Mock the yaml module in the shared display helper
def test_show_settings_yaml(
    mock_yaml: MagicMock,
    mock_settings_class: MagicMock,
    runner: CliRunner,
) -> None:
    """Test `show-settings` command with YAML output."""
    mock_settings_instance = MagicMock()
    # Simulate Pydantic's model_dump for YAML path
    dummy_data_dict = {"dummy_setting": "value", "another_setting": 123}
    mock_settings_instance.model_dump.return_value = dummy_data_dict
    mock_settings_class.return_value = mock_settings_instance

    # Simulate yaml.dump
    mock_yaml.dump.return_value = "dummy_setting: value\nanother_setting: 123\n"

    result = runner.invoke(app, ["show-settings", "--output-format", "yaml"])

    assert result.exit_code == 0
    assert "Current Application Settings" in result.stdout
    assert "dummy_setting: value" in result.stdout
    assert "another_setting: 123" in result.stdout
    mock_settings_class.assert_called_once()
    mock_settings_instance.model_dump.assert_called_once_with(mode="python")
    mock_yaml.dump.assert_called_once_with(dummy_data_dict, indent=2, sort_keys=False)


@patch("scripts.cli.settings_cmd.Settings")
@patch("scripts.cli._display.yaml", None)  # Simulate PyYAML not being installed
def test_show_settings_yaml_fallback_to_json(
    mock_settings_class: MagicMock, runner: CliRunner, caplog
) -> None:
    """Test `show-settings` YAML fallback to JSON if PyYAML not installed."""
    mock_settings_instance = MagicMock()
    mock_settings_instance.model_dump_json.return_value = json.dumps(
        {"dummy_setting": "fallback"}, indent=2
    )
    mock_settings_class.return_value = mock_settings_instance

    result = runner.invoke(app, ["show-settings", "--output-format", "yaml"])

    assert result.exit_code == 0
    assert "Current Application Settings" in result.stdout
    assert '"dummy_setting": "fallback"' in result.stdout  # JSON output
    assert "PyYAML is not installed" in result.stdout  # console fallback msg

    # Check that model_dump_json was called due to fallback
    mock_settings_instance.model_dump_json.assert_called()


# ------------------------------------------------------------------------------
# Tests for `dev` commands
# ------------------------------------------------------------------------------


@patch("scripts.cli.dev.subprocess")
def test_dev_install(mock_subprocess: MagicMock, runner: CliRunner) -> None:
    """Test `dev install` runs uv sync."""
    mock_subprocess.run.return_value = MagicMock(returncode=0)
    result = runner.invoke(app, ["dev", "install"])
    assert result.exit_code == 0
    assert "Dependencies synced" in result.stdout
    mock_subprocess.run.assert_called_once()
    cmd = mock_subprocess.run.call_args[0][0]
    assert cmd == ["uv", "sync", "--all-groups"]


@patch("scripts.cli.dev.subprocess")
def test_dev_lint(mock_subprocess: MagicMock, runner: CliRunner) -> None:
    """Test `dev lint` runs ruff, pylint, mypy."""
    mock_subprocess.run.return_value = MagicMock(returncode=0)
    result = runner.invoke(app, ["dev", "lint"])
    assert result.exit_code == 0
    assert "All linters passed" in result.stdout
    assert mock_subprocess.run.call_count == 3  # ruff, pylint, mypy


@patch("scripts.cli.dev.subprocess")
def test_dev_format(mock_subprocess: MagicMock, runner: CliRunner) -> None:
    """Test `dev format` runs ruff check --fix and ruff format."""
    mock_subprocess.run.return_value = MagicMock(returncode=0)
    result = runner.invoke(app, ["dev", "format"])
    assert result.exit_code == 0
    assert "Formatting complete" in result.stdout
    assert mock_subprocess.run.call_count == 2  # ruff check --fix, ruff format


@patch("scripts.cli.dev.subprocess")
def test_dev_test(mock_subprocess: MagicMock, runner: CliRunner) -> None:
    """Test `dev test` installs test deps then runs pytest."""
    mock_subprocess.run.return_value = MagicMock(returncode=0)
    result = runner.invoke(app, ["dev", "test"])
    assert result.exit_code == 0
    assert mock_subprocess.run.call_count == 2  # uv sync + pytest


@patch("scripts.cli.dev.subprocess")
def test_dev_lint_failure(mock_subprocess: MagicMock, runner: CliRunner) -> None:
    """Test `dev lint` exits on linter failure."""
    mock_subprocess.run.return_value = MagicMock(returncode=1)
    result = runner.invoke(app, ["dev", "lint"])
    assert result.exit_code != 0
    assert "Command failed" in result.stdout


def test_dev_clean(runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test `dev clean` removes cache directories."""
    monkeypatch.chdir(tmp_path)
    # Create some cache dirs
    (tmp_path / ".pytest_cache").mkdir()
    (tmp_path / ".mypy_cache").mkdir()
    (tmp_path / "__pycache__").mkdir()
    (tmp_path / ".coverage").touch()

    result = runner.invoke(app, ["dev", "clean"])
    assert result.exit_code == 0
    assert "Cleaned" in result.stdout
    assert not (tmp_path / ".pytest_cache").exists()
    assert not (tmp_path / ".mypy_cache").exists()
