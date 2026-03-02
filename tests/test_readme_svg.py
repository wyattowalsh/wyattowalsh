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
