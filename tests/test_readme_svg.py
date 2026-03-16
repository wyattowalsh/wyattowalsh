"""Tests for reusable README SVG helpers."""

import re
from pathlib import Path

from scripts.readme_svg import (
    DARK_THEME,
    LANGUAGE_COLORS,
    LIGHT_THEME,
    ReadmeSvgAssetBuilder,
    SvgAssetWriter,
    SvgBlock,
    SvgBlockRenderer,
    SvgCard,
    SvgCardTheme,
    SvgRepoCardRenderer,
)


class TestSvgCardTheme:
    def test_light_theme_fields(self) -> None:
        assert LIGHT_THEME.bg == "#ffffff"
        assert LIGHT_THEME.border == "#d0d7de"
        assert LIGHT_THEME.accent == "#0969da"

    def test_dark_theme_fields(self) -> None:
        assert DARK_THEME.bg == "#0d1117"
        assert DARK_THEME.border == "#30363d"
        assert DARK_THEME.accent == "#58a6ff"

    def test_theme_is_frozen(self) -> None:
        assert SvgCardTheme.__dataclass_params__.frozen is True


class TestLanguageColors:
    def test_python_color(self) -> None:
        assert LANGUAGE_COLORS["Python"] == "#3572A5"

    def test_has_top_languages(self) -> None:
        for lang in ("JavaScript", "TypeScript", "Rust", "Go", "Java"):
            assert lang in LANGUAGE_COLORS


class TestSvgBlockRenderer:
    def test_svg_card_declares_icon_data_uri_payload_field(self) -> None:
        assert "icon_data_uri" in SvgCard.__dataclass_fields__

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
        assert "GitHub" in svg
        assert "https://github.com/wyattowalsh" in svg
        assert 'class="card-icon"' in svg
        assert 'class="card-badge"' in svg
        assert "builder" in svg

    def test_css_custom_properties_present(self) -> None:
        renderer = SvgBlockRenderer(width=480, card_height=120, padding=12)
        block = SvgBlock(
            title="Test",
            cards=(SvgCard(title="Item"),),
            columns=1,
        )
        svg = renderer.render(block)

        assert "--card-bg:" in svg
        assert "--card-border:" in svg
        assert "--title-color:" in svg
        assert "--text-color:" in svg
        assert "--meta-color:" in svg
        assert "--accent:" in svg
        assert "--link-color:" in svg

    def test_dark_mode_media_query(self) -> None:
        renderer = SvgBlockRenderer(width=480, card_height=120, padding=12)
        block = SvgBlock(
            title="Test",
            cards=(SvgCard(title="Item"),),
            columns=1,
        )
        svg = renderer.render(block)

        assert "@media (prefers-color-scheme: dark)" in svg

    def test_no_hardcoded_dark_background(self) -> None:
        renderer = SvgBlockRenderer(width=480, card_height=120, padding=12)
        block = SvgBlock(
            title="Test",
            cards=(SvgCard(title="Item"),),
            columns=1,
        )
        svg = renderer.render(block)

        assert "#0B111A" not in svg

    def test_card_uses_rx6(self) -> None:
        renderer = SvgBlockRenderer(width=480, card_height=120, padding=12)
        block = SvgBlock(
            title="Test",
            cards=(SvgCard(title="Item"),),
            columns=1,
        )
        svg = renderer.render(block)

        assert 'rx="6"' in svg

    def test_language_dot_rendered_for_lang_meta(self) -> None:
        renderer = SvgBlockRenderer(width=480, card_height=140, padding=12)
        block = SvgBlock(
            title="Featured",
            cards=(
                SvgCard(
                    title="My Repo",
                    lines=("A cool project",),
                    meta=("lang:Python", "★ 42"),
                ),
            ),
            columns=1,
        )
        svg = renderer.render(block)

        assert 'class="lang-dot"' in svg
        assert "#3572A5" in svg
        assert "Python" in svg

    def test_star_icon_rendered(self) -> None:
        renderer = SvgBlockRenderer(width=480, card_height=140, padding=12)
        block = SvgBlock(
            title="Featured",
            cards=(
                SvgCard(
                    title="Repo",
                    meta=("★ 123",),
                ),
            ),
            columns=1,
        )
        svg = renderer.render(block)

        assert "123" in svg
        # Star icon path fragment
        assert "M8 .25a" in svg

    def test_fork_icon_rendered(self) -> None:
        renderer = SvgBlockRenderer(width=480, card_height=140, padding=12)
        block = SvgBlock(
            title="Featured",
            cards=(
                SvgCard(
                    title="Repo",
                    meta=("⑂ 7",),
                ),
            ),
            columns=1,
        )
        svg = renderer.render(block)

        assert "7" in svg
        # Fork icon path fragment
        assert "M5 3.25a" in svg

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

    def test_no_section_title_text_in_output(self) -> None:
        """The outer section title should not appear as a text element."""
        renderer = SvgBlockRenderer(width=480, card_height=120, padding=12)
        block = SvgBlock(
            title="Featured",
            cards=(SvgCard(title="Item"),),
            columns=1,
        )
        svg = renderer.render(block)

        # No <text class="title"> header element
        assert 'class="title"' not in svg

    def test_font_family_in_css(self) -> None:
        renderer = SvgBlockRenderer(width=480, card_height=120, padding=12)
        block = SvgBlock(
            title="Test",
            cards=(SvgCard(title="Item"),),
            columns=1,
        )
        svg = renderer.render(block)
        assert "-apple-system" in svg
        assert "BlinkMacSystemFont" in svg


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

    def test_connect_card_pill_removed_but_clickable(self) -> None:
        renderer = SvgBlockRenderer(width=640, card_height=140, padding=16)
        card = SvgCard(
            title="Connect",
            lines=("@wyattowalsh",),
            url="https://github.com/wyattowalsh",
            icon="GH",
            accent="181717",
            badge="open-profile",
        )
        object.__setattr__(card, "icon_data_uri", "data:image/svg+xml;base64,PHN2Zy8+")
        block = SvgBlock(title="Connect", cards=(card,), columns=1)

        svg = renderer.render(block)

        assert 'class="card-pill"' not in svg
        assert "@wyattowalsh" not in svg
        assert 'href="https://github.com/wyattowalsh"' in svg

    def test_featured_card_exposes_richer_metadata_model(self) -> None:
        renderer = SvgBlockRenderer(width=480, card_height=120, padding=12)
        card = SvgCard(
            title="riso",
            lines=("Composable scaffolding framework",),
            url="https://github.com/wyattowalsh/riso",
            meta=("★ 42",),
        )
        object.__setattr__(card, "homepage", "https://riso.dev")
        object.__setattr__(card, "topics", ["python", "templates"])
        object.__setattr__(card, "updated_at", "2026-02-01T00:00:00Z")

        block = SvgBlock(title="Featured", cards=(card,), columns=1)
        svg = renderer.render(block)

        assert "https://riso.dev" in svg
        assert "python" in svg
        assert "GitHub repository" not in svg

    def test_blog_card_no_badge_and_wrapping(self) -> None:
        renderer = SvgBlockRenderer(width=480, card_height=120, padding=12)
        title = "A Very Long Blog Post Title That Would Normally Be Truncated ... update"
        card = SvgCard(title=title, lines=("w4w.dev",), url="https://w4w.dev/blog/long")
        block = SvgBlock(title="Blog", cards=(card,), columns=1)
        svg = renderer.render(block)

        # No badge rect/text rendered (CSS class definition is fine)
        assert 'class="card-badge"' not in svg.split("</style>", 1)[-1]
        assert "update" not in svg
        assert "..." not in svg
        assert "<tspan" in svg


class TestSvgRepoCardRenderer:
    def test_render_produces_valid_svg(self) -> None:
        renderer = SvgRepoCardRenderer(width=500, height=185)
        card = SvgCard(
            title="nbadb",
            kicker="wyattowalsh/nbadb",
            lines=("Data Extraction and Processing Scripts",),
            meta=("lang:Python", "★ 57", "⑂ 14"),
        )
        svg = renderer.render_card(card)

        assert svg.startswith("<svg")
        assert 'width="500"' in svg
        assert 'height="185"' in svg

    def test_light_dark_mode_css_vars(self) -> None:
        renderer = SvgRepoCardRenderer()
        card = SvgCard(title="test")
        svg = renderer.render_card(card)

        assert "--card-bg: transparent" in svg
        assert "--card-border:" in svg
        assert "--title-color:" in svg
        assert "--stat-color:" in svg
        assert "--spark-stroke:" in svg
        assert "@media (prefers-color-scheme: dark)" in svg

    def test_language_color_in_footer(self) -> None:
        renderer = SvgRepoCardRenderer()
        card = SvgCard(
            title="repo",
            meta=("lang:Python",),
        )
        svg = renderer.render_card(card)

        assert "#3572A5" in svg
        assert 'class="rc-lang-dot"' in svg

    def test_no_language_no_lang_dot(self) -> None:
        renderer = SvgRepoCardRenderer()
        card = SvgCard(title="repo", meta=())
        svg = renderer.render_card(card)

        assert 'class="rc-lang-dot"' not in svg

    def test_title_and_description_present(self) -> None:
        renderer = SvgRepoCardRenderer()
        card = SvgCard(
            title="nbadb",
            lines=("Data processing scripts",),
        )
        svg = renderer.render_card(card)

        assert "nbadb" in svg
        assert "Data processing scripts" in svg
        assert 'class="rc-title"' in svg
        assert 'class="rc-desc"' in svg

    def test_footer_language_dot_stars_forks(self) -> None:
        renderer = SvgRepoCardRenderer()
        card = SvgCard(
            title="repo",
            meta=("lang:TypeScript", "★ 123", "⑂ 45"),
        )
        svg = renderer.render_card(card)

        assert 'class="rc-lang-dot"' in svg
        assert "#3178c6" in svg
        assert "TypeScript" in svg
        assert "123" in svg
        assert "M8 .25a" in svg  # star icon path
        assert "45" in svg
        assert "M5 3.25a" in svg  # fork icon path

    def test_no_forks_omits_fork_section(self) -> None:
        renderer = SvgRepoCardRenderer()
        card = SvgCard(
            title="repo",
            meta=("lang:Python", "★ 5"),
        )
        svg = renderer.render_card(card)

        assert "M8 .25a" in svg  # star icon
        assert "M5 3.25a" not in svg  # no fork icon

    def test_long_description_word_wrapped(self) -> None:
        renderer = SvgRepoCardRenderer()
        long_desc = (
            "Data Extraction and Processing Scripts to Produce "
            "the NBA Database on Kaggle with comprehensive stats"
        )
        card = SvgCard(title="repo", lines=(long_desc,))
        svg = renderer.render_card(card)

        # Multiple desc text elements (word wrapped)
        assert svg.count('class="rc-desc"') >= 2
        # Full words visible, not mid-word truncation
        assert "Processing" in svg

    def test_word_wrap_helper(self) -> None:
        lines = SvgRepoCardRenderer._word_wrap(
            "hello world foo bar baz qux", width=12, max_lines=2,
        )
        assert len(lines) == 2
        assert lines[0] == "hello world"
        assert "\u2026" in lines[1]  # last line has ellipsis

    def test_repo_icon_present(self) -> None:
        renderer = SvgRepoCardRenderer()
        card = SvgCard(title="repo")
        svg = renderer.render_card(card)

        # Repo octicon SVG is rendered in the header
        assert 'viewBox="0 0 16 16"' in svg
        assert "M2 2.5A2.5" in svg  # REPO_ICON_PATH fragment

    def test_card_border_radius(self) -> None:
        renderer = SvgRepoCardRenderer()
        card = SvgCard(title="repo")
        svg = renderer.render_card(card)

        assert 'rx="10"' in svg

    def test_aria_label_present(self) -> None:
        renderer = SvgRepoCardRenderer()
        card = SvgCard(title="my-repo")
        svg = renderer.render_card(card)

        assert 'aria-label="my-repo"' in svg

    def test_sparkline_rendered(self) -> None:
        renderer = SvgRepoCardRenderer()
        card = SvgCard(
            title="repo",
            sparkline=(0.0, 2.0, 5.0, 8.0, 12.0),
        )
        svg = renderer.render_card(card)

        assert "sparkline-group" in svg
        assert "spark-stroke" in svg
        assert "spark-grad" in svg

    def test_no_sparkline_when_insufficient_data(self) -> None:
        renderer = SvgRepoCardRenderer()
        card = SvgCard(title="repo", sparkline=(5.0,))
        svg = renderer.render_card(card)

        assert "sparkline-group" not in svg

    def test_og_thumbnail_rendered(self) -> None:
        renderer = SvgRepoCardRenderer()
        card = SvgCard(
            title="repo",
            background_image="data:image/png;base64,iVBOR",
        )
        svg = renderer.render_card(card)

        assert 'href="data:image/png;base64,iVBOR"' in svg
        assert 'clip-path="url(#thumb-clip)"' in svg

    def test_no_thumbnail_when_no_image(self) -> None:
        renderer = SvgRepoCardRenderer()
        card = SvgCard(title="repo")
        svg = renderer.render_card(card)

        assert "thumb-clip" not in svg

    def test_language_bar_rendered(self) -> None:
        renderer = SvgRepoCardRenderer()
        card = SvgCard(
            title="repo",
            meta=("lang:Python",),
        )
        svg = renderer.render_card(card)

        # Thin colored bar above footer
        assert 'height="3"' in svg
        assert 'fill-opacity="0.5"' in svg

    def test_transparent_background(self) -> None:
        renderer = SvgRepoCardRenderer()
        card = SvgCard(title="repo")
        svg = renderer.render_card(card)

        assert "transparent" in svg
