"""Neighbor-aware section order helpers."""

from scripts.config import ReadmeSectionsSettings
from scripts.readme_sections import (
    DEFAULT_SECTION_ORDER,
    compile_section_body_re,
    section_order_from_settings,
)


def test_default_section_order() -> None:
    assert section_order_from_settings(None) == DEFAULT_SECTION_ORDER
    assert tuple(ReadmeSectionsSettings().section_order) == DEFAULT_SECTION_ORDER


def test_custom_section_order_preserves_known_titles() -> None:
    settings = ReadmeSectionsSettings(
        section_order=[
            "Featured Projects",
            "My Tech Stack",
            "Metrics",
            "Word Clouds",
        ]
    )
    assert section_order_from_settings(settings) == tuple(settings.section_order)


def test_compile_section_body_uses_neighbor() -> None:
    text = (
        "## Featured Projects\n\nprojects body\n\n"
        "## Metrics\n\nmetrics body\n\n"
        "## My Tech Stack\n\ntech body\n"
    )
    match = compile_section_body_re("Metrics", DEFAULT_SECTION_ORDER).search(text)
    assert match is not None
    assert "metrics body" in match.group(0)
    assert "tech body" not in match.group(0)


def test_compile_section_body_includes_word_cloud_h3s() -> None:
    text = (
        "## Word Clouds\n\n"
        "### Topics\n\n"
        "topics body\n\n"
        "### Languages\n\n"
        "languages body\n\n"
        "## Latest Blog Posts\n\n"
        "blog body\n"
    )
    match = compile_section_body_re("Word Clouds", DEFAULT_SECTION_ORDER).search(text)
    assert match is not None
    body = match.group(0)
    assert "### Topics" in body
    assert "### Languages" in body
    assert "topics body" in body
    assert "languages body" in body
    assert "Latest Blog Posts" not in body
    assert "blog body" not in body
