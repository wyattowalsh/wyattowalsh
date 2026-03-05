from pathlib import Path
from typing import Any

from typer.testing import CliRunner

from scripts.cli import app
from scripts.config import (
    ProjectConfig,
    ReadmeSectionsSettings,
    ReadmeSvgCardStyleSettings,
    ReadmeSvgFamilyCardStyles,
    ReadmeSvgSettings,
)


def _install_readme_generator_stub(monkeypatch) -> dict[str, Any]:
    captured: dict[str, Any] = {}

    class DummyReadmeSectionGenerator:
        def __init__(self, settings: ReadmeSectionsSettings) -> None:
            captured["settings"] = settings

        def generate(self) -> Path:
            settings: ReadmeSectionsSettings = captured["settings"]
            return Path(settings.readme_path)

    monkeypatch.setattr(
        "scripts.readme_sections.ReadmeSectionGenerator",
        DummyReadmeSectionGenerator,
    )
    return captured


def test_generate_readme_preserves_configured_card_styles(
    monkeypatch, tmp_path: Path
) -> None:
    base_readme = tmp_path / "README.md"
    base_readme.write_text("", encoding="utf-8")

    config = ProjectConfig(
        readme_sections_settings=ReadmeSectionsSettings(
            readme_path=str(base_readme),
            svg=ReadmeSvgSettings(
                enabled=True,
                output_dir=str(tmp_path / "svg"),
                card_styles=ReadmeSvgFamilyCardStyles(
                    connect=ReadmeSvgCardStyleSettings(
                        variant="legacy",
                        transparent_canvas=False,
                        show_title=True,
                    )
                ),
            ),
        )
    )

    monkeypatch.setattr("scripts.cli.load_config", lambda _path: config)
    captured = _install_readme_generator_stub(monkeypatch)
    output_readme = tmp_path / "README.out.md"

    result = CliRunner().invoke(
        app,
        [
            "generate",
            "readme",
            "--config-path",
            str(tmp_path / "config.yaml"),
            "--output-path",
            str(output_readme),
        ],
    )

    assert result.exit_code == 0
    settings: ReadmeSectionsSettings = captured["settings"]
    assert settings.readme_path == str(output_readme)
    assert settings.svg.card_styles.connect.variant == "legacy"
    assert settings.svg.card_styles.connect.transparent_canvas is False
    assert settings.svg.card_styles.connect.show_title is True


def test_generate_readme_applies_card_style_cli_overrides(
    monkeypatch, tmp_path: Path
) -> None:
    base_readme = tmp_path / "README.md"
    base_readme.write_text("", encoding="utf-8")
    config = ProjectConfig(
        readme_sections_settings=ReadmeSectionsSettings(
            readme_path=str(base_readme),
            svg=ReadmeSvgSettings(enabled=True, output_dir=str(tmp_path / "svg")),
        )
    )

    monkeypatch.setattr("scripts.cli.load_config", lambda _path: config)
    captured = _install_readme_generator_stub(monkeypatch)

    result = CliRunner().invoke(
        app,
        [
            "generate",
            "readme",
            "--config-path",
            str(tmp_path / "config.yaml"),
            "--readme-connect-card-variant",
            "legacy",
            "--no-readme-connect-card-transparent-canvas",
            "--readme-connect-card-show-title",
        ],
    )

    assert result.exit_code == 0
    settings: ReadmeSectionsSettings = captured["settings"]
    assert settings.svg.card_styles.connect.variant == "legacy"
    assert settings.svg.card_styles.connect.transparent_canvas is False
    assert settings.svg.card_styles.connect.show_title is True
