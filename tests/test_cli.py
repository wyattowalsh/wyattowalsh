import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml
from typer.testing import CliRunner

from scripts.config import ProjectConfig
from scripts.cli import DEFAULT_CONFIG_PATH, app


# Fixture for CliRunner
@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


# ------------------------------------------------------------------------------
# Tests for `config` command
# ------------------------------------------------------------------------------


@pytest.mark.skipif(app is None, reason="CLI app failed to import")
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
    with open(test_config_path, "r") as f:
        content = yaml.safe_load(f)
        assert "banner_settings" in content
        assert "qr_code_settings" in content


@pytest.mark.skipif(app is None, reason="CLI app failed to import")
def test_config_view_generated_default(runner: CliRunner, tmp_path: Path) -> None:
    """Test `config view` after generating a default."""
    test_config_path = tmp_path / "view_cfg.yaml"
    # First, generate a default config
    runner.invoke(app, ["config", "generate-default", "--path", str(test_config_path)])

    result = runner.invoke(app, ["config", "view", "--path", str(test_config_path)])
    assert result.exit_code == 0
    assert "Current project configuration" in result.stdout
    assert "banner_settings" in result.stdout  # Check for a known key


@pytest.mark.skipif(app is None, reason="CLI app failed to import")
def test_config_view_non_existent(runner: CliRunner, tmp_path: Path) -> None:
    """Test `config view` for a non-existent config file."""
    non_existent_path = tmp_path / "does_not_exist.yaml"
    result = runner.invoke(app, ["config", "view", "--path", str(non_existent_path)])
    assert result.exit_code == 0  # Command itself is okay, prints error msg
    assert "Config file not found" in result.stdout


@pytest.mark.skipif(app is None, reason="CLI app failed to import")
@patch("scripts.cli.load_config")
@patch("scripts.cli.save_config")
def test_config_save_existing(
    mock_save_config: MagicMock,
    mock_load_config: MagicMock,
    runner: CliRunner,
    tmp_path: Path,
) -> None:
    """Test `config save` for an existing config file."""
    test_config_path = tmp_path / "save_cfg.yaml"

    # Mock load_config to return a dummy ProjectConfig
    if ProjectConfig:
        mock_load_config.return_value = ProjectConfig()
    else:  # If ProjectConfig couldn't be imported
        mock_load_config.return_value = MagicMock()

    result = runner.invoke(app, ["config", "save", "--path", str(test_config_path)])

    assert result.exit_code == 0
    mock_load_config.assert_called_once_with(test_config_path)
    mock_save_config.assert_called_once()  # With what args? Depends on implementation
    assert "Configuration successfully saved" in result.stdout


@pytest.mark.skipif(app is None, reason="CLI app failed to import")
@patch("scripts.cli.save_config")
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
    if ProjectConfig:
        assert isinstance(mock_save_config.call_args[0][0], ProjectConfig)
    assert mock_save_config.call_args[0][1] == new_config_path
    assert "Configuration successfully saved" in result.stdout
    assert "default config to save" in result.stdout


# ------------------------------------------------------------------------------
# Tests for `generate banner` command
# ------------------------------------------------------------------------------


@pytest.mark.skipif(app is None, reason="CLI app failed to import")
@patch("scripts.banner.generate_banner")  # patch at the source module
@patch("scripts.cli.load_config")
def test_generate_banner_basic(
    mock_load_config: MagicMock,
    mock_generate_banner_func: MagicMock,
    runner: CliRunner,
    tmp_path: Path,
) -> None:
    """Test basic invocation of `generate banner`."""
    test_config_path = tmp_path / "banner_gen_cfg.yaml"

    # Create a dummy config file or mock load_config effectively
    if ProjectConfig:
        dummy_config = ProjectConfig(banner_settings={"title": "Test Banner"})
        with open(test_config_path, "w") as f:
            yaml.dump(dummy_config.model_dump(mode="json"), f)
        mock_load_config.return_value = dummy_config
    else:
        mock_load_config.return_value = MagicMock(
            banner_settings={"title": "Test Banner"},
            qr_code_settings={},
            v_card_data={},
        )

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


@pytest.mark.skipif(app is None, reason="CLI app failed to import")
@patch("scripts.banner.generate_banner")  # patch at the source module
@patch("scripts.cli.load_config")
def test_generate_banner_cli_overrides(
    mock_load_config: MagicMock,
    mock_generate_banner_func: MagicMock,
    runner: CliRunner,
    tmp_path: Path,
) -> None:
    """Test `generate banner` with CLI options overriding config."""
    test_config_path = tmp_path / "override_cfg.yaml"
    if ProjectConfig:
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
    else:
        mock_load_config.return_value = MagicMock(
            banner_settings={
                "title": "Config Title",
                "width": 1000,
                "height": 500,
                "optimize_with_svgo": True,
                "output_path": "config_banner.svg",
            },
            qr_code_settings={},
            v_card_data={},
        )

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


@pytest.mark.skipif(
    app is None, reason="CLI app failed to import"
)
@patch("scripts.cli.Settings")  # Mock the Settings class
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


@pytest.mark.skipif(
    app is None, reason="CLI app failed to import"
)
@patch("scripts.cli.Settings")
@patch("scripts.cli.yaml")  # Mock the yaml module as a single patch
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


@pytest.mark.skipif(
    app is None, reason="CLI app failed to import"
)
@patch("scripts.cli.Settings")
@patch("scripts.cli.yaml", None)  # Simulate PyYAML not being installed
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
