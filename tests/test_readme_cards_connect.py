"""Focused tests for the dedicated connect card builder."""

from __future__ import annotations

from scripts.readme_card_types import ConnectCard, connect_to_svg
from scripts.readme_cards.connect import ConnectCardBuildInput, build_connect_card
from scripts.readme_svg import SvgCardFamily


def test_build_connect_card_maps_core_and_brand_fields() -> None:
    svg = build_connect_card(
        ConnectCardBuildInput(
            title="GitHub",
            url="https://github.com/wyattowalsh",
            icon="GH",
            icon_data_uri="data:image/svg+xml;base64,PHN2Zy8+",
            accent="181717",
            host="github.com",
            brand_icon_name="github",
        )
    )

    assert getattr(svg, "family", None) == SvgCardFamily.CONNECT.value
    assert getattr(svg, "brand_host", None) == "github.com"
    assert getattr(svg, "brand_icon_name", None) == "github"
    assert getattr(svg, "connect_variant", None) == "gh-card"
    assert svg.icon_data_uri == "data:image/svg+xml;base64,PHN2Zy8+"


def test_build_connect_card_includes_connect_composition_controls() -> None:
    svg = build_connect_card(
        ConnectCardBuildInput(
            title="GitHub",
            connect_variant="legacy",
            show_title=True,
            transparent_canvas=False,
            connect_shell_class="connect-card-shell",
            connect_brand_lockup_class="connect-brand-lockup",
            connect_accent_glow_var="--connect-accent-glow",
        )
    )

    assert getattr(svg, "connect_variant", None) == "legacy"
    assert getattr(svg, "show_title", None) is True
    assert getattr(svg, "transparent_canvas", None) is False
    assert getattr(svg, "connect_shell_class", None) == "connect-card-shell"
    assert getattr(svg, "connect_brand_lockup_class", None) == "connect-brand-lockup"
    assert getattr(svg, "connect_accent_glow_var", None) == "--connect-accent-glow"


def test_connect_to_svg_remains_compatible_with_dedicated_builder() -> None:
    card = ConnectCard(
        title="GitHub",
        kicker="Builder",
        lines=("@wyattowalsh",),
        meta=("github.com",),
        url="https://github.com/wyattowalsh",
        icon="GH",
        icon_data_uri="data:image/svg+xml;base64,PHN2Zy8+",
        accent="181717",
        host="github.com",
        handle="wyattowalsh",
        contact_type="social",
        brand_host="github.com",
        brand_icon_name="github",
        connect_variant="gh-card",
    )

    svg = connect_to_svg(card)

    assert getattr(svg, "family", None) == SvgCardFamily.CONNECT.value
    assert getattr(svg, "host", None) == "github.com"
    assert getattr(svg, "handle", None) == "wyattowalsh"
    assert getattr(svg, "contact_type", None) == "social"
    assert getattr(svg, "brand_host", None) == "github.com"
    assert getattr(svg, "brand_icon_name", None) == "github"
    assert getattr(svg, "connect_variant", None) == "gh-card"
