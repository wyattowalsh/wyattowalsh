"""Focused tests for the isolated blog card builder."""

from __future__ import annotations

from scripts.readme_svg import SvgCardFamily
from scripts.readme_cards.blog import (
    BlogCardBuilder,
    BlogCardMetadata,
    BlogCardPost,
    metadata_from_mapping,
)


def test_blog_builder_composes_hero_first_clutter_free_readable_card() -> None:
    builder = BlogCardBuilder()
    post = BlogCardPost(
        title="A Very Long Blog Post Title ... update With Better Copy Hygiene",
        url="https://w4w.dev/blog/hero-first",
    )
    metadata = BlogCardMetadata(
        summary=(
            "Readable Readable Readable Readable Readable Readable Readable "
            "Readable Readable Readable Readable Readable TAIL-MARKER-123"
        ),
        published="2026-03-01T12:34:56Z",
        host="w4w.dev",
        hero_image="img/hero.png",
    )

    card = builder.build_card(post=post, metadata=metadata)

    assert card.kicker is None
    assert card.badge is None
    assert card.title == "A Very Long Blog Post Title With Better Copy Hygiene"
    assert "TAIL-MARKER-123" in " ".join(card.lines)
    assert card.meta == ("w4w.dev", "Published 2026-03-01")
    assert card.accent == "F59E0B"
    assert card.background_image == "https://w4w.dev/blog/img/hero.png"
    assert card.hero_image == "https://w4w.dev/blog/img/hero.png"
    assert card.wrap_hints is not None
    assert card.wrap_hints.wrap_title_with_tspan is True
    assert card.wrap_hints.line_wrap_chars == 72
    assert card.wrap_hints.max_lines == 5


def test_blog_builder_rejects_unsafe_hero_images() -> None:
    builder = BlogCardBuilder()
    card = builder.build_card(
        post=BlogCardPost(title="Security", url="https://w4w.dev/blog/security"),
        metadata=BlogCardMetadata(hero_image="http://127.0.0.1/secret.png"),
    )

    assert card.background_image is None
    assert card.hero_image is None


def test_blog_builder_adapts_to_svg_with_blog_family_and_wrap_hints() -> None:
    builder = BlogCardBuilder()
    post = BlogCardPost(title="SVG Adaptation", url="https://github.com/blog/post")
    metadata = metadata_from_mapping(
        {
            "summary": "Summary copy",
            "host": "github.com",
            "hero_image": "//images.example.com/post.png",
        }
    )

    svg = builder.build_svg_card(post=post, metadata=metadata)

    assert getattr(svg, "family", None) == SvgCardFamily.BLOG.value
    assert svg.background_image == "https://images.example.com/post.png"
    assert getattr(svg, "hero_image", None) == "https://images.example.com/post.png"
    assert getattr(svg, "wrap_title_with_tspan", None) is True
    assert getattr(svg, "line_wrap_chars", None) == 72
    assert svg.badge is None
    assert svg.kicker is None


def test_metadata_adapter_coerces_optional_text_values() -> None:
    metadata = metadata_from_mapping(
        {
            "summary": "  Summary  ",
            "published": 20260301,
            "host": "",
            "hero_image": None,
        }
    )

    assert metadata.summary == "Summary"
    assert metadata.published == "20260301"
    assert metadata.host is None
    assert metadata.hero_image is None
