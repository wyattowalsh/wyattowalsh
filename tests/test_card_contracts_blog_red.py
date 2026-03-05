"""RED contracts for prettier transparent blog cards."""

from __future__ import annotations

import re

from scripts.readme_svg import SvgBlock, SvgBlockRenderer, SvgCard, SvgCardFamily


def _render_blog_card_svg(card: SvgCard) -> str:
    renderer = SvgBlockRenderer(width=920, card_height=220, padding=20)
    return renderer.render(
        SvgBlock(
            title="Latest Blog Posts",
            cards=(card,),
            columns=1,
            family=SvgCardFamily.BLOG,
            show_title=False,
            transparent_canvas=True,
        )
    )


def test_blog_transparent_surface_contract_red() -> None:
    svg = _render_blog_card_svg(
        SvgCard(
            title="Transparent semantics",
            lines=("Body copy",),
            url="https://w4w.dev/blog/transparent-semantics",
        )
    )

    shell = re.search(r'fill="#0F172A" fill-opacity="([0-9.]+)" stroke=', svg)

    assert '<rect width="100%" height="100%"' not in svg
    assert shell is not None
    assert float(shell.group(1)) <= 0.24


def test_blog_clutterless_top_right_contract_red() -> None:
    svg = _render_blog_card_svg(
        SvgCard(
            title="No top-right clutter",
            kicker="BLOG",
            lines=("Summary copy",),
            url="https://w4w.dev/blog/no-clutter",
            badge="Read post",
        )
    )

    assert 'class="card-kicker"' not in svg
    assert 'class="card-badge"' not in svg


def test_blog_wrapped_copy_without_forced_truncation_contract_red() -> None:
    long_copy = " ".join(["Readable"] * 140) + " TAIL-MARKER-123"
    svg = _render_blog_card_svg(
        SvgCard(
            title="Readable wrapped copy",
            lines=(long_copy,),
            url="https://w4w.dev/blog/wrapped-copy",
        )
    )

    assert "…" not in svg
    assert "TAIL-MARKER-123" in svg


def test_blog_hero_first_media_contract_red() -> None:
    svg = _render_blog_card_svg(
        SvgCard(
            title="Hero-first card",
            lines=("Summary",),
            url="https://w4w.dev/blog/hero-first",
            background_image="https://example.com/hero.jpg",
            icon="BL",
            icon_data_uri="data:image/svg+xml;base64,PHN2Zy8+",
        )
    )

    assert 'preserveAspectRatio="xMidYMid slice"' in svg
    assert 'class="card-icon-image"' not in svg
    assert 'class="card-icon"' not in svg
