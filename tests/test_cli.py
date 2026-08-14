import json
import tomllib
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, call, patch

import pytest
import typer
import yaml
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name
from PIL import Image
from typer.testing import CliRunner

import scripts.cli.generate as generate_cmd
import scripts.cli.generate._common as generate_common
from scripts.art.artifacts import LIVING_ART_STYLE_KEYS
from scripts.cli import app
from scripts.cli.generate import _wc_from_languages, _wc_from_topics, _wc_import
from scripts.config import ProjectConfig, QRCodeSettings
from scripts.word_clouds import WordCloudSettings
from scripts.word_clouds.readability import LayoutReadabilitySettings


def _make_valid_png() -> bytes:
    output = BytesIO()
    Image.new("RGB", (2, 2), color=(15, 90, 180)).save(output, format="PNG")
    return output.getvalue()


_VALID_PNG = _make_valid_png()


# Fixture for CliRunner
@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


def _requirements_by_name(requirements: list[str]) -> dict[str, set[str]]:
    """Return normalized requirement names mapped to their aggregated extras."""
    result: dict[str, set[str]] = {}
    for requirement_text in requirements:
        requirement = Requirement(requirement_text)
        name = str(canonicalize_name(requirement.name))
        result.setdefault(name, set()).update(
            str(canonicalize_name(extra)) for extra in requirement.extras
        )
    return result


def _write_mock_banner(*, cfg: object) -> None:
    """Emulate the banner generator's successful file-publication contract."""
    output = Path(str(getattr(cfg, "output_path")))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("<svg/>", encoding="utf-8")


def test_refresh_living_art_artifacts_mirrors_docs_showcase(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    output_dir = tmp_path / ".github" / "assets" / "img"
    showcase_dir = tmp_path / "docs" / "public" / "showcase"
    output_dir.mkdir(parents=True)
    showcase_dir.mkdir(parents=True)

    for style in LIVING_ART_STYLE_KEYS:
        frames = [
            Image.new("RGB", (400, 400), color=(20, 40, 60)),
            Image.new("RGB", (400, 400), color=(60, 40, 20)),
        ]
        frames[0].save(
            output_dir / f"living-{style}.gif",
            format="GIF",
            save_all=True,
            append_images=frames[1:],
            duration=[12_000, 12_000],
            loop=0,
        )

    generate_cmd._refresh_living_art_artifacts(output_dir)

    assert (output_dir / "living-art-manifest.json").exists()
    assert (output_dir / "living-art-preview.html").exists()
    for style in LIVING_ART_STYLE_KEYS:
        assert (showcase_dir / f"living-{style}.gif").exists()
    assert (showcase_dir / "living-art-manifest.json").exists()
    assert (showcase_dir / "living-art-preview.html").exists()


def _living_art_input_paths(tmp_path: Path) -> tuple[Path, Path]:
    metrics_path = tmp_path / "metrics.json"
    history_path = tmp_path / "history.json"
    metrics_path.write_text("{}", encoding="utf-8")
    history_path.write_text("{}", encoding="utf-8")
    return metrics_path, history_path


def _run_living_art_generation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    outputs: list[Path],
) -> None:
    metrics_path, history_path = _living_art_input_paths(tmp_path)
    monkeypatch.setattr(
        "scripts.art.timelapse.render_timelapse",
        lambda *_args, **_kwargs: outputs,
    )
    monkeypatch.setattr(
        generate_common,
        "_refresh_living_art_artifacts",
        MagicMock(),
    )

    generate_common._generate_living_art_timelapse(
        profile="wyattowalsh",
        metrics_path=metrics_path,
        history_path=history_path,
        only=None,
        max_frames=120,
        size=400,
        workers=1,
        output_dir=outputs[0].parent if outputs else tmp_path / "img",
    )


def test_living_art_generation_fails_when_a_requested_style_is_skipped(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output_dir = tmp_path / "img"
    output_dir.mkdir()
    outputs = []
    for style in LIVING_ART_STYLE_KEYS[:-1]:
        output = output_dir / f"living-{style}.gif"
        output.write_bytes(b"fresh")
        outputs.append(output)

    with pytest.raises(typer.Exit) as error:
        _run_living_art_generation(tmp_path, monkeypatch, outputs)

    assert error.value.exit_code == 1


def test_living_art_generation_fails_when_no_frames_are_rendered(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with pytest.raises(typer.Exit) as error:
        _run_living_art_generation(tmp_path, monkeypatch, [])

    assert error.value.exit_code == 1


def test_preexisting_stale_living_art_cannot_mask_a_skipped_style(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output_dir = tmp_path / "img"
    output_dir.mkdir()
    stale_outputs = []
    for style in LIVING_ART_STYLE_KEYS:
        output = output_dir / f"living-{style}.gif"
        output.write_bytes(b"stale")
        stale_outputs.append(output)

    returned_outputs = stale_outputs[:-1]
    returned_outputs[0].write_bytes(b"fresh")

    with pytest.raises(typer.Exit) as error:
        _run_living_art_generation(tmp_path, monkeypatch, returned_outputs)

    assert error.value.exit_code == 1


def test_partial_living_art_generation_never_refreshes_stale_fleet_index(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A one-style shard must not publish an index from stale peer GIFs."""
    output_dir = tmp_path / "isolated-style"
    output_dir.mkdir()
    for style in LIVING_ART_STYLE_KEYS:
        (output_dir / f"living-{style}.gif").write_bytes(b"stale")
    selected_output = output_dir / "living-topo.gif"
    selected_output.write_bytes(b"fresh")
    metrics_path, history_path = _living_art_input_paths(tmp_path)
    captured: dict[str, object] = {}

    def _render(*_args: object, **kwargs: object) -> list[Path]:
        captured.update(kwargs)
        return [selected_output]

    refresh = MagicMock()
    monkeypatch.setattr("scripts.art.timelapse.render_timelapse", _render)
    monkeypatch.setattr(generate_common, "_refresh_living_art_artifacts", refresh)

    outputs = generate_common._generate_living_art_timelapse(
        profile="wyattowalsh",
        metrics_path=metrics_path,
        history_path=history_path,
        only="topo",
        max_frames=120,
        size=400,
        workers=2,
        output_dir=output_dir,
    )

    assert outputs == [selected_output]
    assert captured["output_dir"] == output_dir
    assert captured["styles"] == ["topo"]
    refresh.assert_not_called()


def test_full_living_art_generation_refreshes_requested_output_directory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output_dir = tmp_path / "canonical-fleet"
    output_dir.mkdir()
    outputs = []
    for style in LIVING_ART_STYLE_KEYS:
        output = output_dir / f"living-{style}.gif"
        output.write_bytes(b"fresh")
        outputs.append(output)
    metrics_path, history_path = _living_art_input_paths(tmp_path)
    monkeypatch.setattr(
        "scripts.art.timelapse.render_timelapse",
        lambda *_args, **_kwargs: outputs,
    )
    refresh = MagicMock()
    monkeypatch.setattr(generate_common, "_refresh_living_art_artifacts", refresh)

    generate_common._generate_living_art_timelapse(
        profile="wyattowalsh",
        metrics_path=metrics_path,
        history_path=history_path,
        only=None,
        max_frames=120,
        size=400,
        workers=2,
        output_dir=output_dir,
    )

    refresh.assert_called_once_with(output_dir)


@pytest.mark.parametrize("command", ["living-art", "timelapse"])
def test_living_art_commands_forward_custom_output_directory(
    command: str,
    runner: CliRunner,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}
    monkeypatch.setattr(
        "scripts.cli.generate.art._load_project_config",
        lambda _path: ProjectConfig(),
    )
    monkeypatch.setattr(
        "scripts.cli.generate.art._generate_living_art_timelapse",
        lambda **kwargs: captured.update(kwargs),
    )
    output_dir = tmp_path / command

    result = runner.invoke(
        app,
        [
            "generate",
            command,
            "--metrics-path",
            str(tmp_path / "metrics.json"),
            "--history-path",
            str(tmp_path / "history.json"),
            "--output-dir",
            str(output_dir),
        ],
    )

    assert result.exit_code == 0, result.stdout
    assert captured["output_dir"] == output_dir


@patch("scripts.qr.QRCodeGenerator")
@patch("scripts.cli.generate.load_config")
def test_generate_qr_cli_requires_fresh_valid_png(
    mock_load_config: MagicMock,
    mock_qr_generator: MagicMock,
    runner: CliRunner,
    tmp_path: Path,
) -> None:
    """The QR command reports success only after validating the exact target."""
    mock_load_config.return_value = ProjectConfig()
    output_path = tmp_path / "fresh.png"

    def _generate(**_kwargs: object) -> Path:
        output_path.write_bytes(_VALID_PNG)
        return output_path

    mock_qr_generator.return_value.generate_artistic_vcard_qr.side_effect = _generate

    result = runner.invoke(
        app,
        ["generate", "qr", "--output-path", str(output_path)],
    )

    assert result.exit_code == 0, result.stdout
    assert "QR code generated:" in result.stdout
    assert output_path.name in result.stdout
    assert output_path.read_bytes() == _VALID_PNG


@patch("scripts.qr.QRCodeGenerator")
@patch("scripts.cli.generate.load_config")
def test_generate_qr_cli_noop_cannot_reuse_stale_png(
    mock_load_config: MagicMock,
    mock_qr_generator: MagicMock,
    runner: CliRunner,
    tmp_path: Path,
) -> None:
    """A mocked/no-op renderer cannot make a prior QR appear successful."""
    mock_load_config.return_value = ProjectConfig()
    output_path = tmp_path / "stale.png"
    output_path.write_bytes(_VALID_PNG)
    mock_qr_generator.return_value.generate_artistic_vcard_qr.return_value = output_path

    result = runner.invoke(
        app,
        ["generate", "qr", "--output-path", str(output_path)],
    )

    assert result.exit_code == 1
    assert "QR renderer did not create an output" in result.stdout
    assert "QR code generated:" not in result.stdout
    assert not output_path.exists()


@patch("scripts.qr.QRCodeGenerator")
@patch("scripts.cli.generate.load_config")
def test_generate_qr_cli_failure_removes_partial_target(
    mock_load_config: MagicMock,
    mock_qr_generator: MagicMock,
    runner: CliRunner,
    tmp_path: Path,
) -> None:
    """The command cleans partial bytes left by a failing renderer backend."""
    mock_load_config.return_value = ProjectConfig()
    output_path = tmp_path / "partial.png"

    def _generate(**_kwargs: object) -> Path:
        output_path.write_bytes(b"partial")
        raise OSError("save failed")

    mock_qr_generator.return_value.generate_artistic_vcard_qr.side_effect = _generate

    result = runner.invoke(
        app,
        ["generate", "qr", "--output-path", str(output_path)],
    )

    assert result.exit_code == 1
    assert "QR generation failed: save failed" in result.stdout
    assert "QR code generated:" not in result.stdout
    assert not output_path.exists()


@patch("scripts.qr.QRCodeGenerator")
@patch("scripts.cli.generate.load_config")
def test_generate_qr_cli_rejects_signature_only_png(
    mock_load_config: MagicMock,
    mock_qr_generator: MagicMock,
    runner: CliRunner,
    tmp_path: Path,
) -> None:
    mock_load_config.return_value = ProjectConfig()
    output_path = tmp_path / "invalid.png"

    def _generate(**_kwargs: object) -> Path:
        output_path.write_bytes(b"\x89PNG\r\n\x1a\nnot-a-real-png")
        return output_path

    mock_qr_generator.return_value.generate_artistic_vcard_qr.side_effect = _generate

    result = runner.invoke(
        app,
        ["generate", "qr", "--output-path", str(output_path)],
    )

    assert result.exit_code == 1
    assert "created an invalid PNG" in result.stdout
    assert "QR code generated:" not in result.stdout
    assert not output_path.exists()


@pytest.mark.parametrize(
    "unsafe_filename",
    ["../victim.png", "nested/victim.png", r"..\victim.png", "victim.jpg"],
)
@patch("scripts.qr.QRCodeGenerator")
@patch("scripts.cli.generate.load_config")
def test_generate_qr_cli_rejects_unsafe_config_filename_before_mutation(
    mock_load_config: MagicMock,
    mock_qr_generator: MagicMock,
    runner: CliRunner,
    tmp_path: Path,
    unsafe_filename: str,
) -> None:
    output_dir = tmp_path / "outputs"
    output_dir.mkdir()
    victim = tmp_path / "victim.png"
    victim.write_bytes(b"preserve me")
    mock_load_config.return_value = ProjectConfig(
        qr_code_settings=QRCodeSettings(
            output_dir=str(output_dir),
            output_filename=unsafe_filename,
        )
    )

    result = runner.invoke(app, ["generate", "qr"])

    assert result.exit_code == 1
    assert "must be a bare .png filename" in result.stdout
    assert victim.read_bytes() == b"preserve me"
    mock_qr_generator.assert_not_called()


@patch("scripts.qr.QRCodeGenerator")
@patch("scripts.cli.generate.load_config")
def test_generate_qr_cli_rejects_non_png_output_path_before_mutation(
    mock_load_config: MagicMock,
    mock_qr_generator: MagicMock,
    runner: CliRunner,
    tmp_path: Path,
) -> None:
    mock_load_config.return_value = ProjectConfig()
    victim = tmp_path / "victim.txt"
    victim.write_bytes(b"preserve me")

    result = runner.invoke(
        app,
        ["generate", "qr", "--output-path", str(victim)],
    )

    assert result.exit_code == 1
    assert "must be a bare .png filename" in result.stdout
    assert victim.read_bytes() == b"preserve me"
    mock_qr_generator.assert_not_called()


class _CapturingWordCloudGenerator:
    last_settings: WordCloudSettings | None = None
    last_kwargs: dict[str, object] | None = None

    def __init__(self, base_settings: WordCloudSettings) -> None:
        type(self).last_settings = base_settings

    def generate(self, **kwargs):
        type(self).last_kwargs = kwargs
        output = Path(kwargs["output_path"])
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text("<svg/>", encoding="utf-8")
        return output


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


def test_wc_from_topics_uses_typographic_renderer_with_stable_filename(
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

    assert result == tmp_path / "wordcloud_typographic_by_topics.svg"
    assert _CapturingWordCloudGenerator.last_settings is not None
    assert _CapturingWordCloudGenerator.last_settings.renderer == "typographic"
    assert _CapturingWordCloudGenerator.last_settings.max_words == 2
    assert _CapturingWordCloudGenerator.last_kwargs is not None
    assert _CapturingWordCloudGenerator.last_kwargs["frequencies"] == {
        "python": 4,
        "others": 2,
    }
    assert _CapturingWordCloudGenerator.last_kwargs["color_func_name"] == "ocean"


def test_wc_from_languages_uses_typographic_renderer_with_stable_filename(
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

    assert result == tmp_path / "wordcloud_typographic_by_languages.svg"
    assert _CapturingWordCloudGenerator.last_settings is not None
    assert _CapturingWordCloudGenerator.last_settings.renderer == "typographic"
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


@patch("scripts.cli.auth.mint_spotify_refresh_token")
def test_auth_spotify_refresh_token_writes_file_without_echoing_secret(
    mock_mint_refresh_token: MagicMock,
    runner: CliRunner,
    tmp_path: Path,
) -> None:
    mock_mint_refresh_token.return_value = (
        "refresh-token-12345",
        "https://accounts.spotify.com/authorize?...",
    )
    output_path = tmp_path / "spotify_refresh_token.txt"

    result = runner.invoke(
        app,
        [
            "auth",
            "spotify-refresh-token",
            "--client-id",
            "client-id",
            "--client-secret",
            "client-secret",
            "--no-open-browser",
            "--output",
            str(output_path),
        ],
    )

    assert result.exit_code == 0
    assert output_path.read_text(encoding="utf-8") == "refresh-token-12345\n"
    assert "refresh-token-12345" not in result.stdout
    assert "Masked preview:" in result.stdout
    assert str(output_path) in result.stdout


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
    mock_generate_banner_func.side_effect = _write_mock_banner
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
    # Rich may soft-wrap long absolute paths; compare on the unwrapped stream.
    stdout_unwrapped = result.stdout.replace("\n", "")
    assert output_svg_path.name in stdout_unwrapped
    assert mock_generate_banner_func.called  # called once for light + once for dark
    # Check that BannerConfig was passed with correct output_path on the first call
    first_call_kwargs = mock_generate_banner_func.call_args_list[0].kwargs
    banner_config_arg = first_call_kwargs["cfg"]
    assert str(banner_config_arg.output_path) == str(output_svg_path)
    assert banner_config_arg.title == "Test Banner"  # From dummy_config
    assert banner_config_arg.seed == 0  # BannerSettings default


@patch("scripts.banner.generate_banner")
@patch("scripts.cli.generate.load_config")
def test_generate_banner_dark_variant_succeeds_with_output_path(
    mock_load_config: MagicMock,
    mock_generate_banner_func: MagicMock,
    runner: CliRunner,
    tmp_path: Path,
) -> None:
    """Dark banner must succeed when CLI provides --output-path (no double-kwarg)."""
    mock_generate_banner_func.side_effect = _write_mock_banner
    test_config_path = tmp_path / "banner_dark_cfg.yaml"
    dummy_config = ProjectConfig(banner_settings={"title": "Dark Pair"})
    with open(test_config_path, "w") as f:
        yaml.dump(dummy_config.model_dump(mode="json"), f)
    mock_load_config.return_value = dummy_config

    output_svg_path = tmp_path / "pair_banner.svg"
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
    assert "Dark SVG banner generated:" in result.stdout
    assert "Dark banner generation failed" not in result.stdout
    assert mock_generate_banner_func.call_count == 2
    light_cfg = mock_generate_banner_func.call_args_list[0].kwargs["cfg"]
    dark_cfg = mock_generate_banner_func.call_args_list[1].kwargs["cfg"]
    assert str(light_cfg.output_path) == str(output_svg_path)
    assert str(dark_cfg.output_path) == str(tmp_path / "pair_banner-dark.svg")
    assert dark_cfg.dark_mode is True
    assert light_cfg.dark_mode is False


@patch("scripts.banner.generate_banner")  # patch at the source module
@patch("scripts.cli.generate.load_config")
def test_generate_banner_cli_seed_override(
    mock_load_config: MagicMock,
    mock_generate_banner_func: MagicMock,
    runner: CliRunner,
    tmp_path: Path,
) -> None:
    """Test `generate banner --seed` overrides config default."""
    mock_generate_banner_func.side_effect = _write_mock_banner
    test_config_path = tmp_path / "banner_seed_cfg.yaml"
    dummy_config = ProjectConfig(banner_settings={"title": "Seeded", "seed": 0})
    with open(test_config_path, "w") as f:
        yaml.dump(dummy_config.model_dump(mode="json"), f)
    mock_load_config.return_value = dummy_config

    result = runner.invoke(
        app,
        [
            "generate",
            "banner",
            "--config-path",
            str(test_config_path),
            "--output-path",
            str(tmp_path / "seeded.svg"),
            "--seed",
            "42",
        ],
    )

    assert result.exit_code == 0
    first_call_kwargs = mock_generate_banner_func.call_args_list[0].kwargs
    assert first_call_kwargs["cfg"].seed == 42


@patch("scripts.banner.generate_banner")  # patch at the source module
@patch("scripts.cli.generate.load_config")
def test_generate_banner_cli_overrides(
    mock_load_config: MagicMock,
    mock_generate_banner_func: MagicMock,
    runner: CliRunner,
    tmp_path: Path,
) -> None:
    """Test `generate banner` with CLI options overriding config."""
    mock_generate_banner_func.side_effect = _write_mock_banner
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


@patch("scripts.banner.generate_banner")
@patch("scripts.cli.generate.load_config")
def test_generate_banner_dark_variant_failure_exits_nonzero(
    mock_load_config: MagicMock,
    mock_generate_banner_func: MagicMock,
    runner: CliRunner,
    tmp_path: Path,
) -> None:
    """The paired banner command fails when its required dark variant fails."""
    mock_load_config.return_value = ProjectConfig()

    def _generate_or_fail(*, cfg: object) -> None:
        if getattr(cfg, "dark_mode"):
            raise OSError("dark write failed")
        _write_mock_banner(cfg=cfg)

    mock_generate_banner_func.side_effect = _generate_or_fail
    output = tmp_path / "pair.svg"

    result = runner.invoke(app, ["generate", "banner", "--output-path", str(output)])

    assert result.exit_code == 1
    assert "Banner generation failed: dark write failed" in result.stdout
    assert "Dark SVG banner generated:" not in result.stdout
    assert mock_generate_banner_func.call_count == 2
    assert not output.exists()


@patch("scripts.banner.generate_banner")
@patch("scripts.cli.generate.load_config")
def test_generate_banner_stale_dark_output_cannot_mask_noop_generation(
    mock_load_config: MagicMock,
    mock_generate_banner_func: MagicMock,
    runner: CliRunner,
    tmp_path: Path,
) -> None:
    """A stale dark SVG is removed and cannot satisfy post-generation checks."""
    mock_load_config.return_value = ProjectConfig()
    output = tmp_path / "pair.svg"
    dark_output = tmp_path / "pair-dark.svg"
    dark_output.write_text("stale", encoding="utf-8")

    def _generate_light_only(*, cfg: object) -> None:
        if not getattr(cfg, "dark_mode"):
            _write_mock_banner(cfg=cfg)

    mock_generate_banner_func.side_effect = _generate_light_only

    result = runner.invoke(app, ["generate", "banner", "--output-path", str(output)])

    assert result.exit_code == 1
    assert "Banner generator did not create" in result.stdout
    assert "did not create an output" in result.stdout
    assert "Dark SVG banner generated:" not in result.stdout
    assert not output.exists()
    assert not dark_output.exists()


@pytest.mark.parametrize("publication", ["malformed", "symlink", "directory"])
@patch("scripts.banner.generate_banner")
@patch("scripts.cli.generate.load_config")
def test_generate_banner_cli_rejects_invalid_dark_publication(
    mock_load_config: MagicMock,
    mock_generate_banner_func: MagicMock,
    publication: str,
    runner: CliRunner,
    tmp_path: Path,
) -> None:
    """Both paired targets are removed unless both are parseable SVG files."""
    mock_load_config.return_value = ProjectConfig()
    output = tmp_path / "pair.svg"
    dark_output = tmp_path / "pair-dark.svg"
    symlink_target = tmp_path / "actual.svg"
    symlink_target.write_text("<svg/>", encoding="utf-8")

    def _generate(*, cfg: object) -> None:
        target = Path(str(getattr(cfg, "output_path")))
        if not getattr(cfg, "dark_mode"):
            target.write_text("<svg/>", encoding="utf-8")
        elif publication == "malformed":
            target.write_text("not svg", encoding="utf-8")
        elif publication == "symlink":
            target.symlink_to(symlink_target)
        else:
            target.mkdir()

    mock_generate_banner_func.side_effect = _generate

    result = runner.invoke(app, ["generate", "banner", "--output-path", str(output)])

    assert result.exit_code == 1
    assert "Banner generation failed" in result.stdout
    assert "Dark SVG banner generated:" not in result.stdout
    assert not output.exists()
    assert not dark_output.exists()
    assert symlink_target.read_text(encoding="utf-8") == "<svg/>"


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
    assert cmd == ["uv", "sync", "--locked", "--all-extras"]


def test_dev_extra_contract_covers_lint_and_test_targets() -> None:
    """Test lint/test extras include optional deps needed by the dev wrappers."""
    pyproject = tomllib.loads(
        (Path(__file__).resolve().parents[1] / "pyproject.toml").read_text()
    )
    project = pyproject["project"]
    optional_deps = project["optional-dependencies"]
    core = _requirements_by_name(project["dependencies"])
    lint = _requirements_by_name(optional_deps["lint"])
    test = _requirements_by_name(optional_deps["test"])
    science = _requirements_by_name(optional_deps["science"])
    word_clouds = _requirements_by_name(optional_deps["word-clouds"])

    assert {"qr", "word-clouds"} <= lint["readme"]
    assert {"qr", "word-clouds"} <= test["readme"]
    assert {"matplotlib", "mealpy", "scipy"} <= science.keys()
    assert "science" in word_clouds["readme"]
    assert {"matplotlib", "mealpy", "scipy"}.isdisjoint(core)


@patch("scripts.cli.dev.subprocess")
def test_dev_update_deps_is_only_upgrade_path(
    mock_subprocess: MagicMock, runner: CliRunner
) -> None:
    """Test `dev update-deps` upgrades the lock rather than doing a sync."""
    mock_subprocess.run.return_value = MagicMock(returncode=0)
    result = runner.invoke(app, ["dev", "update-deps"])
    assert result.exit_code == 0
    assert "Lockfile updated" in result.stdout
    mock_subprocess.run.assert_called_once_with(
        ["uv", "lock", "--upgrade"],
        cwd=None,
    )


@patch("scripts.cli.dev.subprocess")
def test_dev_lint(mock_subprocess: MagicMock, runner: CliRunner) -> None:
    """Test `dev lint` runs ruff, pylint (score-gated), and gated ty."""
    mock_subprocess.run.return_value = MagicMock(returncode=0)
    result = runner.invoke(app, ["dev", "lint"])
    assert result.exit_code == 0
    assert "All linters passed" in result.stdout
    assert mock_subprocess.run.call_args_list == [
        call(["uv", "sync", "--locked", "--inexact", "--extra", "lint"], cwd=None),
        call(
            ["uv", "run", "--", "python", "-m", "ruff", "check", "scripts", "tests"],
            cwd=None,
        ),
        call(
            [
                "uv",
                "run",
                "--",
                "python",
                "-m",
                "pylint",
                "--fail-under=8.0",
                "scripts",
                "tests",
            ],
            cwd=None,
        ),
        call(
            ["uv", "run", "--", "python", "-m", "scripts.quality.ty_ratchet"],
            cwd=None,
        ),
    ]


@patch("scripts.cli.dev.subprocess")
def test_dev_format(mock_subprocess: MagicMock, runner: CliRunner) -> None:
    """Test `dev format` runs ruff check --fix and ruff format."""
    mock_subprocess.run.return_value = MagicMock(returncode=0)
    result = runner.invoke(app, ["dev", "format"])
    assert result.exit_code == 0
    assert "Formatting complete" in result.stdout
    assert mock_subprocess.run.call_args_list == [
        call(
            ["uv", "sync", "--locked", "--inexact", "--extra", "format"],
            cwd=None,
        ),
        call(
            [
                "uv",
                "run",
                "--",
                "python",
                "-m",
                "ruff",
                "check",
                "--fix",
                "scripts",
                "tests",
            ],
            cwd=None,
        ),
        call(
            ["uv", "run", "--", "python", "-m", "ruff", "format", "scripts", "tests"],
            cwd=None,
        ),
    ]


@patch("scripts.cli.dev.subprocess")
def test_dev_test(
    mock_subprocess: MagicMock, runner: CliRunner, tmp_path: Path
) -> None:
    """Test `dev test` installs test deps then runs pytest."""
    mock_subprocess.run.return_value = MagicMock(returncode=0)
    report_dir = tmp_path / "reports"
    result = runner.invoke(app, ["dev", "test", "--report-dir", str(report_dir)])
    assert result.exit_code == 0
    assert mock_subprocess.run.call_args_list[0] == call(
        ["uv", "sync", "--locked", "--inexact", "--extra", "test"], cwd=None
    )
    pytest_call = mock_subprocess.run.call_args_list[1]
    assert pytest_call.args[0] == [
        "uv",
        "run",
        "--",
        "python",
        "-m",
        "pytest",
        "--cov-report",
        "term",
        "--cov-report",
        f"html:{report_dir / 'coverage'}",
        "--html",
        str(report_dir / "report.html"),
        "--self-contained-html",
        "--junitxml",
        str(report_dir / "junit.xml"),
        "--log-file",
        str(report_dir / "pytest.log"),
    ]
    assert pytest_call.kwargs["cwd"] is None
    assert pytest_call.kwargs["env"]["COVERAGE_FILE"] == str(report_dir / ".coverage")


@patch("scripts.cli.dev.subprocess")
def test_dev_test_option_passthrough(
    mock_subprocess: MagicMock, runner: CliRunner, tmp_path: Path
) -> None:
    """Test `dev test` forwards pytest selection flags."""
    mock_subprocess.run.return_value = MagicMock(returncode=0)
    result = runner.invoke(
        app,
        [
            "dev",
            "test",
            "--no-coverage",
            "-k",
            "dev",
            "-m",
            "slow",
            "--report-dir",
            str(tmp_path),
        ],
    )
    assert result.exit_code == 0
    assert mock_subprocess.run.call_args_list[0] == call(
        ["uv", "sync", "--locked", "--inexact", "--extra", "test"], cwd=None
    )
    pytest_call = mock_subprocess.run.call_args_list[1]
    assert pytest_call.args[0] == [
        "uv",
        "run",
        "--",
        "python",
        "-m",
        "pytest",
        "--no-cov",
        "--html",
        str(tmp_path / "report.html"),
        "--self-contained-html",
        "--junitxml",
        str(tmp_path / "junit.xml"),
        "--log-file",
        str(tmp_path / "pytest.log"),
        "-k",
        "dev",
        "-m",
        "slow",
    ]
    assert pytest_call.kwargs["env"]["COVERAGE_FILE"] == str(tmp_path / ".coverage")


@patch("scripts.cli.dev.subprocess")
def test_dev_test_sync_failure(mock_subprocess: MagicMock, runner: CliRunner) -> None:
    """Test `dev test` exits if dependency sync fails."""
    mock_subprocess.run.return_value = MagicMock(returncode=2)
    result = runner.invoke(app, ["dev", "test"])
    assert result.exit_code == 2
    assert "Command failed" in result.stdout
    mock_subprocess.run.assert_called_once_with(
        ["uv", "sync", "--locked", "--inexact", "--extra", "test"],
        cwd=None,
    )


@patch("scripts.cli.dev.subprocess")
def test_dev_lint_failure(mock_subprocess: MagicMock, runner: CliRunner) -> None:
    """Test `dev lint` exits on linter failure."""
    mock_subprocess.run.side_effect = [
        MagicMock(returncode=0),
        MagicMock(returncode=1),
    ]
    result = runner.invoke(app, ["dev", "lint"])
    assert result.exit_code != 0
    assert "Command failed" in result.stdout


@patch("scripts.cli.dev.subprocess")
def test_dev_lint_ty_failure(mock_subprocess: MagicMock, runner: CliRunner) -> None:
    """A configured ty error fails the lint gate."""
    mock_subprocess.run.side_effect = [
        MagicMock(returncode=0),
        MagicMock(returncode=0),
        MagicMock(returncode=0),
        MagicMock(returncode=1),
    ]
    result = runner.invoke(app, ["dev", "lint"])
    assert result.exit_code == 1
    assert "Command failed" in result.stdout
    assert "All linters passed" not in result.stdout
    assert mock_subprocess.run.call_args_list[-1] == call(
        ["uv", "run", "--", "python", "-m", "scripts.quality.ty_ratchet"],
        cwd=None,
    )


def test_dev_clean(
    runner: CliRunner,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test `dev clean` removes cache directories."""
    monkeypatch.chdir(tmp_path)
    # Create some cache dirs
    (tmp_path / ".pytest_cache").mkdir()
    (tmp_path / "__pycache__").mkdir()
    (tmp_path / ".coverage").touch()

    result = runner.invoke(app, ["dev", "clean"])
    assert result.exit_code == 0
    assert "Cleaned" in result.stdout
    assert not (tmp_path / ".pytest_cache").exists()


def test_generate_all_passes_metrics_and_history_to_living_art(
    runner: CliRunner,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    metrics_path = tmp_path / "metrics.json"
    history_path = tmp_path / "history.json"
    metrics_path.write_text("{}", encoding="utf-8")
    history_path.write_text("{}", encoding="utf-8")

    monkeypatch.setattr(generate_cmd, "banner", lambda **_kwargs: None)
    monkeypatch.setattr(generate_cmd, "qr", lambda **_kwargs: None)
    monkeypatch.setattr(generate_cmd, "word_cloud", lambda **_kwargs: None)
    monkeypatch.setattr(generate_cmd, "skills", lambda **_kwargs: None)
    monkeypatch.setattr(generate_cmd, "readme_sections", lambda **_kwargs: None)
    monkeypatch.setattr(generate_cmd, "generative_art", lambda **_kwargs: None)
    monkeypatch.setattr(generate_cmd, "animated", lambda **_kwargs: None, raising=False)

    captured: dict[str, Path | str | None] = {}

    def _stub_living_art(
        *,
        config_path: Path | None = None,
        metrics_path: Path | None = None,
        history_path: Path | None = None,
        **_kwargs,
    ) -> None:
        captured["config_path"] = config_path
        captured["metrics_path"] = metrics_path
        captured["history_path"] = history_path
        captured["profile"] = _kwargs.get("profile")

    monkeypatch.setattr(generate_cmd, "living_art", _stub_living_art)

    result = runner.invoke(
        app,
        [
            "generate",
            "all",
            "--metrics-path",
            str(metrics_path),
            "--history-path",
            str(history_path),
        ],
    )

    assert result.exit_code == 0, result.stdout
    assert captured["metrics_path"] == metrics_path
    assert captured["history_path"] == history_path
    assert captured["profile"] == "wyattowalsh"


def test_generate_all_passes_metrics_and_history_to_animated_art(
    runner: CliRunner,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    metrics_path = tmp_path / "metrics.json"
    history_path = tmp_path / "history.json"
    metrics_path.write_text("{}", encoding="utf-8")
    history_path.write_text("{}", encoding="utf-8")

    monkeypatch.setattr(generate_cmd, "banner", lambda **_kwargs: None)
    monkeypatch.setattr(generate_cmd, "qr", lambda **_kwargs: None)
    monkeypatch.setattr(generate_cmd, "word_cloud", lambda **_kwargs: None)
    monkeypatch.setattr(generate_cmd, "skills", lambda **_kwargs: None)
    monkeypatch.setattr(generate_cmd, "readme_sections", lambda **_kwargs: None)
    monkeypatch.setattr(generate_cmd, "generative_art", lambda **_kwargs: None)
    monkeypatch.setattr(generate_cmd, "living_art", lambda **_kwargs: None)

    captured: dict[str, Path | str | None] = {}

    def _stub_animated(
        *,
        config_path: Path | None = None,
        metrics_path: Path | None = None,
        history_path: Path | None = None,
        **_kwargs,
    ) -> None:
        captured["config_path"] = config_path
        captured["metrics_path"] = metrics_path
        captured["history_path"] = history_path
        captured["profile"] = _kwargs.get("profile")

    monkeypatch.setattr(generate_cmd, "animated", _stub_animated, raising=False)

    result = runner.invoke(
        app,
        [
            "generate",
            "all",
            "--metrics-path",
            str(metrics_path),
            "--history-path",
            str(history_path),
        ],
    )

    assert result.exit_code == 0, result.stdout
    assert captured["metrics_path"] == metrics_path
    assert captured["history_path"] == history_path
    assert captured["profile"] == "wyattowalsh"


def test_generate_all_passes_profile_to_living_art(
    runner: CliRunner,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    metrics_path = tmp_path / "metrics.json"
    history_path = tmp_path / "history.json"
    metrics_path.write_text("{}", encoding="utf-8")
    history_path.write_text("{}", encoding="utf-8")

    monkeypatch.setattr(generate_cmd, "banner", lambda **_kwargs: None)
    monkeypatch.setattr(generate_cmd, "qr", lambda **_kwargs: None)
    monkeypatch.setattr(generate_cmd, "word_cloud", lambda **_kwargs: None)
    monkeypatch.setattr(generate_cmd, "skills", lambda **_kwargs: None)
    monkeypatch.setattr(generate_cmd, "readme_sections", lambda **_kwargs: None)
    monkeypatch.setattr(generate_cmd, "generative_art", lambda **_kwargs: None)
    monkeypatch.setattr(generate_cmd, "animated", lambda **_kwargs: None, raising=False)

    captured: dict[str, str | None] = {}

    def _stub_living_art(**_kwargs) -> None:
        captured["profile"] = _kwargs.get("profile")

    monkeypatch.setattr(generate_cmd, "living_art", _stub_living_art)

    result = runner.invoke(
        app,
        [
            "generate",
            "all",
            "--profile",
            "octocat",
            "--metrics-path",
            str(metrics_path),
            "--history-path",
            str(history_path),
        ],
    )

    assert result.exit_code == 0, result.stdout
    assert captured["profile"] == "octocat"


def test_generate_animated_invokes_compat_module(
    runner: CliRunner,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    metrics_path = tmp_path / "metrics.json"
    history_path = tmp_path / "history.json"
    metrics_path.write_text("{}", encoding="utf-8")
    history_path.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(generate_cmd, "load_config", lambda _path: ProjectConfig())

    captured: dict[str, object] = {}

    import scripts.art.animate as animate_module

    def _stub_main() -> None:
        captured["argv"] = generate_cmd.sys.argv[:]
        captured["cwd"] = Path.cwd()

    monkeypatch.setattr(animate_module, "main", _stub_main)

    result = runner.invoke(
        app,
        [
            "generate",
            "animated",
            "--profile",
            "octocat",
            "--metrics-path",
            str(metrics_path),
            "--history-path",
            str(history_path),
        ],
    )

    assert result.exit_code == 0, result.stdout
    assert captured["cwd"] == Path(__file__).resolve().parents[1]
    assert captured["argv"] == [
        "animate",
        "--profile",
        "octocat",
        "--frames",
        "7",
        "--size",
        "400",
        "--svg",
        "--metrics-path",
        str(metrics_path),
        "--history-path",
        str(history_path),
    ]


def test_generate_all_skips_living_art_when_required_inputs_missing(
    runner: CliRunner,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(generate_cmd, "banner", lambda **_kwargs: None)
    monkeypatch.setattr(generate_cmd, "qr", lambda **_kwargs: None)
    monkeypatch.setattr(generate_cmd, "word_cloud", lambda **_kwargs: None)
    monkeypatch.setattr(generate_cmd, "skills", lambda **_kwargs: None)
    monkeypatch.setattr(generate_cmd, "readme_sections", lambda **_kwargs: None)
    monkeypatch.setattr(generate_cmd, "generative_art", lambda **_kwargs: None)
    monkeypatch.setattr(generate_cmd, "animated", lambda **_kwargs: None, raising=False)

    called = {"living_art": False}

    def _stub_living_art(**_kwargs) -> None:
        called["living_art"] = True

    monkeypatch.setattr(generate_cmd, "living_art", _stub_living_art)

    result = runner.invoke(app, ["generate", "all"])

    assert result.exit_code == 0, result.stdout
    assert called["living_art"] is False
    assert "Skipping living art" in result.stdout
