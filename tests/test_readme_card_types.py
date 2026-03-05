"""Contract and adapter tests for family-specific README card types."""

from __future__ import annotations

from scripts.readme_card_types import (
    BlogCard,
    BlogWrapHints,
    ConnectCard,
    FeaturedCard,
    FeaturedMetadataChip,
    blog_to_svg,
    connect_to_svg,
    featured_to_svg,
)
from scripts.readme_svg import SvgCardFamily


def test_connect_adapter_preserves_brand_and_icon_contract_fields() -> None:
    card = ConnectCard(
        title="GitHub",
        url="https://github.com/wyattowalsh",
        icon="GH",
        icon_data_uri="data:image/svg+xml;base64,PHN2Zy8+",
        accent="181717",
        brand_host="github.com",
        brand_icon_name="github",
        connect_variant="gh-card",
    )

    svg = connect_to_svg(card)

    assert getattr(svg, "family", None) == SvgCardFamily.CONNECT.value
    assert getattr(svg, "brand_host", None) == "github.com"
    assert getattr(svg, "brand_icon_name", None) == "github"
    assert getattr(svg, "connect_variant", None) == "gh-card"
    assert svg.icon_data_uri == "data:image/svg+xml;base64,PHN2Zy8+"


def test_featured_adapter_preserves_metadata_lanes_chips_and_social_image_hint() -> (
    None
):
    card = FeaturedCard(
        title="riso",
        url="https://github.com/wyattowalsh/riso",
        homepage="riso.dev",
        topics=("python", "templates"),
        created_at="2023-01-01T00:00:00Z",
        updated_at="2026-02-01T00:00:00Z",
        forks=7,
        language="Python",
        size_kb=2048,
        metadata_chips=(
            FeaturedMetadataChip(label="Stars", value="42"),
            FeaturedMetadataChip(label="Language", value="Python"),
        ),
        metadata_lanes=("★ 42 · Python", "Forks 7 · 2.0 MB"),
        social_image_hint="https://opengraph.githubassets.com/hash/riso",
    )

    svg = featured_to_svg(card)

    chips = getattr(svg, "metadata_chips", ())
    assert chips == (
        {"label": "Stars", "value": "42"},
        {"label": "Language", "value": "Python"},
    )
    assert getattr(svg, "metadata_lanes", ()) == ("★ 42 · Python", "Forks 7 · 2.0 MB")
    assert getattr(svg, "metadata_rows", ()) == ("★ 42 · Python", "Forks 7 · 2.0 MB")
    assert getattr(svg, "social_image_hint", None) == (
        "https://opengraph.githubassets.com/hash/riso"
    )
    assert getattr(svg, "family", None) == SvgCardFamily.FEATURED.value


def test_blog_adapter_maps_hero_and_wrapping_contract_fields() -> None:
    card = BlogCard(
        title="Readable copy for cards",
        url="https://w4w.dev/blog/readable-copy",
        lines=("Summary copy",),
        host="w4w.dev",
        published="2026-03-01",
        summary="Summary copy",
        hero_image="https://w4w.dev/hero.png",
        wrap_hints=BlogWrapHints(
            wrap_title_with_tspan=True,
            title_wrap_chars=48,
            title_max_lines=2,
            wrap_lines_with_tspan=True,
            line_wrap_chars=72,
            max_lines=5,
        ),
    )

    svg = blog_to_svg(card)

    assert svg.background_image == "https://w4w.dev/hero.png"
    assert getattr(svg, "hero_image", None) == "https://w4w.dev/hero.png"
    assert getattr(svg, "wrap_title_with_tspan", None) is True
    assert getattr(svg, "line_wrap_chars", None) == 72
    assert getattr(svg, "family", None) == SvgCardFamily.BLOG.value
