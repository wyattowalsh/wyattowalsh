"""Output-format contracts for shared CLI display helpers."""

from __future__ import annotations

from typing import Any

from scripts.cli import _display
from scripts.config import ProjectConfig


class _CapturingConsole:
    def __init__(self) -> None:
        self.values: list[object] = []

    def print(self, value: object) -> None:
        self.values.append(value)


def test_display_config_renders_json_syntax(monkeypatch: Any) -> None:
    console = _CapturingConsole()
    monkeypatch.setattr(_display, "console", console)

    _display.display_config(ProjectConfig(), _display.OutputFormat.JSON)

    assert len(console.values) == 1
    syntax = console.values[0]
    assert getattr(syntax, "lexer").name == "JSON"
    assert '"banner_settings"' in str(getattr(syntax, "code"))


def test_display_config_renders_yaml_syntax(monkeypatch: Any) -> None:
    console = _CapturingConsole()
    monkeypatch.setattr(_display, "console", console)

    _display.display_config(ProjectConfig(), _display.OutputFormat.YAML)

    assert len(console.values) == 1
    syntax = console.values[0]
    assert getattr(syntax, "lexer").name == "YAML"
    assert "banner_settings:" in str(getattr(syntax, "code"))
