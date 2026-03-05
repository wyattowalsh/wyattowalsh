"""Unit tests for the dedicated featured README card builder."""

from __future__ import annotations

import base64

from scripts.readme_card_types import featured_to_svg
from scripts.readme_cards.featured import (
    FeaturedCardBuilder,
    FeaturedCardHints,
    FeaturedRepoSnapshot,
)
from scripts.readme_svg import SvgCardFamily


def _snapshot(**overrides: object) -> FeaturedRepoSnapshot:
    payload = {
        "full_name": "wyattowalsh/riso",
        "name": "riso",
        "html_url": "https://github.com/wyattowalsh/riso",
        "description": "Composable scaffolding framework",
        "stars": 42,
        "homepage": "https://riso.dev",
        "topics": ("python", "templates"),
        "updated_at": "2026-02-01T00:00:00Z",
        "created_at": "2023-01-01T00:00:00Z",
        "forks": 7,
        "language": "Python",
        "size_kb": 2048,
        "open_graph_image_url": "https://opengraph.githubassets.com/hash/riso",
    }
    payload.update(overrides)
    return FeaturedRepoSnapshot(**payload)


def test_featured_builder_builds_rich_metadata_chips_and_lanes() -> None:
    builder = FeaturedCardBuilder()
    card = builder.build("wyattowalsh/riso", _snapshot())

    chip_labels = {chip.label.lower() for chip in card.metadata_chips}
    assert {"stars", "forks", "language", "size", "lifespan"}.issubset(chip_labels)
    assert card.metadata_lanes
    assert card.metadata_lanes[0].startswith("★ ")
    assert card.meta == card.metadata_lanes
    assert card.social_image_hint == "https://opengraph.githubassets.com/hash/riso"


def test_featured_builder_supports_hero_and_social_hint_overrides() -> None:
    builder = FeaturedCardBuilder()
    hints = FeaturedCardHints(
        hero_image="https://cdn.example.com/hero.png",
        social_image_hint="https://social.example.com/preview.png",
        accent="ABCDEF",
    )

    card = builder.build("wyattowalsh/riso", _snapshot(), hints)

    assert card.background_image == "https://cdn.example.com/hero.png"
    assert card.social_image_hint == "https://social.example.com/preview.png"
    assert card.accent == "ABCDEF"


def test_featured_builder_fallback_hero_is_deterministic_and_transparency_friendly() -> (
    None
):
    builder = FeaturedCardBuilder()
    snapshot = _snapshot(open_graph_image_url=None)

    first = builder.build("wyattowalsh/riso", snapshot)
    second = builder.build("wyattowalsh/riso", snapshot)

    assert first.background_image == second.background_image
    assert first.background_image is not None
    assert first.background_image.startswith("data:image/svg+xml;base64,")
    encoded = first.background_image.split(",", maxsplit=1)[1]
    decoded = base64.b64decode(encoded).decode("utf-8")
    assert "stop-opacity='0.36'" in decoded
    assert "<linearGradient id='bg'" in decoded
    assert first.social_image_hint == first.background_image


def test_featured_builder_handles_missing_metadata_with_compatible_defaults() -> None:
    builder = FeaturedCardBuilder()

    card = builder.build("wyattowalsh/riso", None)

    assert card.title == "riso"
    assert card.kicker == "wyattowalsh/riso"
    assert card.url == "https://github.com/wyattowalsh/riso"
    assert card.lines == builder.fallback_lines
    assert card.metadata_chips
    assert any(chip.label == "Status" for chip in card.metadata_chips)
    assert len(card.metadata_lanes) >= 2
    assert card.meta == card.metadata_lanes
    assert any("metadata missing" in lane.lower() for lane in card.metadata_lanes)
    assert card.background_image is not None
    assert card.background_image.startswith("data:image/svg+xml;base64,")


def test_featured_builder_output_stays_compatible_with_featured_adapter() -> None:
    builder = FeaturedCardBuilder()
    card = builder.build(
        "wyattowalsh/riso",
        _snapshot(),
        FeaturedCardHints(sparkline=(0.0, 5.0, 9.0)),
    )

    svg = featured_to_svg(card)

    assert getattr(svg, "family", None) == SvgCardFamily.FEATURED.value
    assert getattr(svg, "metadata_lanes", ()) == card.metadata_lanes
    assert getattr(svg, "metadata_rows", ()) == card.metadata_lanes
    assert getattr(svg, "social_image_hint", None) == card.social_image_hint
    assert getattr(svg, "open_graph_image_url", None) == card.open_graph_image_url
