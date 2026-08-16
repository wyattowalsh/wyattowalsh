"""Neighbor-aware section order helpers."""

from scripts.config import ReadmeSectionsSettings
from scripts.readme_sections import (
    DEFAULT_SECTION_ORDER,
    compile_section_body_re,
    section_order_from_settings,
)


def test_default_section_order() -> None:
    assert section_order_from_settings(None) == DEFAULT_SECTION_ORDER


def test_custom_section_order_preserves_known_titles() -> None:
    settings = ReadmeSectionsSettings(
        section_order=[
            "Featured Projects",
            "Metrics",
            "Living Art",
            "My Tech Stack",
            "Word Clouds",
        ]
    )
    assert section_order_from_settings(settings)[1] == "Metrics"


def test_compile_section_body_uses_neighbor() -> None:
    order = (
        "Featured Projects",
        "Metrics",
        "Living Art",
        "My Tech Stack",
        "Word Clouds",
    )
    text = (
        "## Metrics\n\nmetrics body\n\n"
        "## Living Art\n\nliving body\n\n"
        "## My Tech Stack\n\ntech body\n"
    )
    match = compile_section_body_re("Living Art", order).search(text)
    assert match is not None
    assert "living body" in match.group(0)
    assert "tech body" not in match.group(0)
