"""Tests for reusable README SVG helpers."""

import re
from pathlib import Path

from scripts.readme_svg import (
    ReadmeSvgAssetBuilder,
    SvgAssetWriter,
    SvgBlock,
    SvgBlockRenderer,
    SvgCard,
)


class TestSvgBlockRenderer:
    def test_svg_card_declares_icon_data_uri_payload_field(self) -> None:
        assert "icon_data_uri" in SvgCard.__dataclass_fields__

    def test_render_supports_image_icon_chip_with_monogram_fallback(self) -> None:
        renderer = SvgBlockRenderer(width=640, card_height=140, padding=16)
        with_image = SvgCard(
            title="GitHub",
            lines=("https://github.com/wyattowalsh",),
            url="https://github.com/wyattowalsh",
            icon="GH",
            accent="181717",
        )
        object.__setattr__(
            with_image,
            "icon_data_uri",
            "data:image/svg+xml;base64,PHN2Zy8+",
        )
        fallback_only = SvgCard(
            title="Kaggle",
            lines=("https://kaggle.com/wyattowalsh",),
            icon="KG",
            accent="20BEFF",
        )
        block = SvgBlock(
            title="Connect",
            cards=(with_image, fallback_only),
            columns=2,
        )

        svg = renderer.render(block)

        assert 'class="card-icon-image"' in svg
        assert 'href="data:image/svg+xml;base64,PHN2Zy8+"' in svg
        assert ">KG</text>" in svg

    def test_render_outputs_svg_markup(self) -> None:
        renderer = SvgBlockRenderer(width=640, card_height=140, padding=16)
        block = SvgBlock(
            title="Connect",
            cards=(
                SvgCard(
                    title="GitHub",
                    lines=("https://github.com/wyattowalsh",),
                    meta=("badge #181717",),
                    url="https://github.com/wyattowalsh",
                    icon="GH",
                    badge="builder",
                ),
                SvgCard(
                    title="LinkedIn",
                    lines=("https://linkedin.com/in/wyattowalsh",),
                    meta=("badge #0A66C2",),
                ),
            ),
            columns=2,
        )

        svg = renderer.render(block)

        assert svg.startswith("<svg")
        assert "Connect" in svg
        assert "GitHub" in svg
        assert "https://github.com/wyattowalsh" in svg
        assert 'class="card-icon"' in svg
        assert 'class="card-badge"' in svg
        assert "builder" in svg

    def test_render_includes_background_and_sparkline(self) -> None:
        renderer = SvgBlockRenderer(width=480, card_height=160, padding=18)
        block = SvgBlock(
            title="Visuals",
            cards=(
                SvgCard(
                    title="Repo",
                    lines=("Background preview",),
                    meta=("★ 42",),
                    background_image="https://example.com/opengraph.png",
                    sparkline=(0.0, 1.0, 3.0, 4.0),
                ),
            ),
            columns=1,
        )

        svg = renderer.render(block)

        assert 'href="https://example.com/opengraph.png"' in svg
        assert 'class="sparkline"' in svg

    def test_render_uses_stronger_readability_defaults_for_image_cards(self) -> None:
        renderer = SvgBlockRenderer(width=480, card_height=160, padding=18)
        block = SvgBlock(
            title="Visuals",
            cards=(
                SvgCard(
                    title="Repo",
                    lines=("Background preview",),
                    meta=("★ 42",),
                    background_image="https://example.com/opengraph.png",
                    badge="Featured Project",
                ),
            ),
            columns=1,
        )

        svg = renderer.render(block)
        image_opacity_match = re.search(
            r'<image[^>]+opacity="([0-9.]+)"', svg
        )
        top_gradient_match = re.search(
            r'<stop offset="0%" stop-color="#0B111A" stop-opacity="([0-9.]+)"',
            svg,
        )
        badge_opacity_match = re.search(
            r'height="24" rx="12" fill="[^"]+" fill-opacity="([0-9.]+)"',
            svg,
        )
        badge_fill_match = re.search(r"\.card-badge \{ fill: ([^;]+);", svg)

        assert image_opacity_match is not None
        assert top_gradient_match is not None
        assert badge_opacity_match is not None
        assert badge_fill_match is not None
        assert float(image_opacity_match.group(1)) < 0.52
        assert float(top_gradient_match.group(1)) > 0.12
        assert float(badge_opacity_match.group(1)) > 0.32
        assert badge_fill_match.group(1).strip() == "#FFFFFF"

    def test_render_uses_stable_unique_clip_ids(self) -> None:
        renderer = SvgBlockRenderer(width=640, card_height=160, padding=16)
        block = SvgBlock(
            title="Visuals",
            cards=(
                SvgCard(
                    title="Repo",
                    lines=("Preview",),
                    background_image="https://example.com/a.png",
                ),
                SvgCard(
                    title="Repo",
                    lines=("Preview",),
                    background_image="https://example.com/b.png",
                ),
            ),
            columns=2,
        )

        first_svg = renderer.render(block)
        second_svg = renderer.render(block)

        first_ids = re.findall(r'<clipPath id="([^"]+)"', first_svg)
        second_ids = re.findall(r'<clipPath id="([^"]+)"', second_svg)

        assert first_svg == second_svg
        assert first_ids == ["clip-0", "clip-1"]
        assert first_ids == second_ids
        assert len(set(first_ids)) == len(first_ids)

    def test_render_outputs_individual_card_groups(self) -> None:
        renderer = SvgBlockRenderer(width=640, card_height=160, padding=16)
        block = SvgBlock(
            title="Latest Blog Posts",
            cards=(
                SvgCard(title="Post One", lines=("w4w.dev",)),
                SvgCard(title="Post Two", lines=("w4w.dev",)),
            ),
            columns=1,
        )

        svg = renderer.render(block)

        assert svg.count('class="card"') == 2

class TestSvgAssetWriter:
    def test_write_sanitizes_filename(self, tmp_path: Path) -> None:
        writer = SvgAssetWriter(output_dir=tmp_path)

        output_path = writer.write(
            asset_name="featured projects",
            svg_content="<svg />",
        )

        assert output_path == tmp_path / "featured-projects.svg"
        assert output_path.read_text(encoding="utf-8") == "<svg />"


class TestReadmeSvgAssetBuilder:
    def test_render_and_write_creates_svg_asset(self, tmp_path: Path) -> None:
        builder = ReadmeSvgAssetBuilder(
            output_dir=tmp_path,
            renderer=SvgBlockRenderer(width=480, card_height=120, padding=12),
        )

        output_path = builder.render_and_write(
            asset_name="blog/posts",
            block=SvgBlock(
                title="Latest Blog Posts",
                cards=(SvgCard(title="First Post", lines=("w4w.dev",)),),
                columns=1,
            ),
        )

        content = output_path.read_text(encoding="utf-8")
        assert output_path == tmp_path / "blog-posts.svg"
        assert "Latest Blog Posts" in content
        assert "First Post" in content

    def test_write_raw_uses_existing_markup(self, tmp_path: Path) -> None:
        builder = ReadmeSvgAssetBuilder(
            output_dir=tmp_path,
            renderer=SvgBlockRenderer(width=360, card_height=100, padding=8),
        )

        svg_markup = "<svg><text>Inline Render</text></svg>"
        output_path = builder.write_raw(asset_name="inline", svg_content=svg_markup)

        assert output_path == tmp_path / "inline.svg"
        assert output_path.read_text(encoding="utf-8") == svg_markup
