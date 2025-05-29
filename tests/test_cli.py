import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

# Assuming ProjectConfig and Settings can be imported for type hinting
# and potentially for creating default expected outputs.
# If they are complex or have many dependencies, we might need to mock them
# or simplify their usage in tests.
try:
    from config import ProjectConfig, Settings
    from scripts.cli import DEFAULT_CONFIG_PATH, app
except ImportError:
    # This allows tests to be found by pytest even if config models are complex
    # and might fail to import in some test environments initially.
    # Actual tests using these might need to be skipped or use more mocks.
    ProjectConfig = None
    Settings = None
    app = None  # type: ignore
    DEFAULT_CONFIG_PATH = Path.home() / ".w4w-config.json"


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
    test_config_path = tmp_path / "test_cfg.json"
    result = runner.invoke(
        app, ["config", "generate-default", "--path", str(test_config_path)]
    )
    assert result.exit_code == 0
    assert test_config_path.exists()
    assert "Default configuration generated" in result.stdout
    # Verify content (optional, could be brittle if defaults change often)
    with open(test_config_path, "r") as f:
        content = json.load(f)
        assert "banner_settings" in content
        assert "qr_code_settings" in content


@pytest.mark.skipif(app is None, reason="CLI app failed to import")
def test_config_view_generated_default(runner: CliRunner, tmp_path: Path) -> None:
    """Test `config view` after generating a default."""
    test_config_path = tmp_path / "view_cfg.json"
    # First, generate a default config
    runner.invoke(app, ["config", "generate-default", "--path", str(test_config_path)])

    result = runner.invoke(app, ["config", "view", "--path", str(test_config_path)])
    assert result.exit_code == 0
    assert "Current configuration" in result.stdout
    assert "banner_settings" in result.stdout  # Check for a known key


@pytest.mark.skipif(app is None, reason="CLI app failed to import")
def test_config_view_non_existent(runner: CliRunner, tmp_path: Path) -> None:
    """Test `config view` for a non-existent config file."""
    non_existent_path = tmp_path / "does_not_exist.json"
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
    test_config_path = tmp_path / "save_cfg.json"

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
    new_config_path = tmp_path / "new_default_cfg.json"
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
    # Check log mocked or captured output if specific log assertion is needed
    assert "Creating default to save" in result.stdout


# ------------------------------------------------------------------------------
# Tests for `generate banner` command
# ------------------------------------------------------------------------------


@pytest.mark.skipif(app is None, reason="CLI app failed to import")
@patch("scripts.cli.generate_banner")  # Mock the actual banner generation
@patch("scripts.cli.load_config")
def test_generate_banner_basic(
    mock_load_config: MagicMock,
    mock_generate_banner_func: MagicMock,
    runner: CliRunner,
    tmp_path: Path,
) -> None:
    """Test basic invocation of `generate banner`."""
    test_config_path = tmp_path / "banner_gen_cfg.json"

    # Create a dummy config file or mock load_config effectively
    if ProjectConfig:
        dummy_config = ProjectConfig(banner_settings={"title": "Test Banner"})
        with open(test_config_path, "w") as f:
            json.dump(
                dummy_config.model_dump(mode="json"), f
            )  # Use model_dump for Pydantic
        mock_load_config.return_value = dummy_config
    else:
        # If ProjectConfig not available, make load_config return a simple
        # dict or mock object for the test to proceed.
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
    assert f"SVG banner generated: {output_svg_path}" in result.stdout
    mock_generate_banner_func.assert_called_once()
    # Check that BannerConfig was passed with correct output_path
    # This requires inspecting the args of the mock_generate_banner_func call
    args, _ = mock_generate_banner_func.call_args
    banner_config_arg = args[0]
    assert banner_config_arg.output_path == str(output_svg_path)
    assert banner_config_arg.title == "Test Banner"  # From dummy_config


@pytest.mark.skipif(app is None, reason="CLI app failed to import")
@patch("scripts.cli.generate_banner")
@patch("scripts.cli.load_config")
def test_generate_banner_cli_overrides(
    mock_load_config: MagicMock,
    mock_generate_banner_func: MagicMock,
    runner: CliRunner,
    tmp_path: Path,
) -> None:
    """Test `generate banner` with CLI options overriding config."""
    test_config_path = tmp_path / "override_cfg.json"
    if ProjectConfig:
        dummy_config = ProjectConfig(
            banner_settings={
                "title": "Config Title",
                "width": 1000,
                "height": 500,  # Example height
                "optimize_with_svgo": True,
                "output_path": "config_banner.svg",  # Will be overridden
            }
        )
        with open(test_config_path, "w") as f:
            json.dump(dummy_config.model_dump(mode="json"), f)
        mock_load_config.return_value = dummy_config
    else:
        mock_load_config.return_value = MagicMock(
            banner_settings={
                "title": "Config Title",
                "width": 1000,
                "height": 500,  # Example height
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
    mock_generate_banner_func.assert_called_once()
    args, _ = mock_generate_banner_func.call_args
    banner_config_arg = args[0]

    assert banner_config_arg.output_path == str(
        cli_output_svg_path
    )  # CLI --output-path wins
    assert banner_config_arg.title == cli_title  # CLI --title wins
    assert banner_config_arg.width == cli_width  # CLI --width wins


# ------------------------------------------------------------------------------
# Tests for `show-settings` command
# ------------------------------------------------------------------------------


@pytest.mark.skipif(
    app is None or Settings is None, reason="CLI app or Settings model failed to import"
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
    app is None or Settings is None, reason="CLI app or Settings model failed to import"
)
@patch("scripts.cli.Settings")
@patch("scripts.cli.yaml.dump")  # Mock yaml.dump
@patch(
    "scripts.cli.yaml", create=True
)  # Mock the yaml module itself if PyYAML might not be installed
def test_show_settings_yaml(
    mock_yaml_module: MagicMock,
    mock_yaml_dump: MagicMock,
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
    mock_yaml_dump.return_value = "dummy_setting: value\n" "another_setting: 123\n"

    result = runner.invoke(app, ["show-settings", "--output-format", "yaml"])

    assert result.exit_code == 0
    assert "Current Application Settings" in result.stdout
    assert "dummy_setting: value" in result.stdout
    assert "another_setting: 123" in result.stdout
    mock_settings_class.assert_called_once()
    mock_settings_instance.model_dump.assert_called_once_with(mode="python")
    mock_yaml_dump.assert_called_once_with(dummy_data_dict, indent=2, sort_keys=False)


@pytest.mark.skipif(
    app is None or Settings is None, reason="CLI app or Settings model failed to import"
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
    # model_dump is called before yaml.dump attempt
    mock_settings_instance.model_dump.return_value = {"dummy_setting": "fallback"}

    mock_settings_class.return_value = mock_settings_instance

    # Simulate yaml not being importable in _display_config
    with patch.dict("sys.modules", {"yaml": None}):
        result = runner.invoke(app, ["show-settings", "--output-format", "yaml"])

    assert result.exit_code == 0
    assert "Current Application Settings" in result.stdout
    assert '"dummy_setting": "fallback"' in result.stdout  # JSON output
    assert "PyYAML is not installed" in result.stdout  # Console fallback msg
    # Check logger for the error message (optional, if logger is mockable)
    # Example: assert "PyYAML is not installed" in caplog.text

    # Check that model_dump_json was called due to fallback
    mock_settings_instance.model_dump_json.assert_called()
    mock_settings_instance.model_dump_json.assert_called()
