"""Syrupy SVG snapshot tests for key generators (banner + readme_svg).

Uses ``SVGImageSnapshotExtension`` so each assertion stores a standalone ``.svg``
file under ``__snapshots__/``. Banner generation is seeded for determinism;
readme SVG helpers are pure/deterministic given fixed card inputs.
"""

from __future__ import annotations

import re
from pathlib import Path
from unittest.mock import patch

from scripts.banner import BannerConfig, Point3DModel, generate_banner
from scripts.readme_svg import (
    SvgBlock,
    SvgBlockRenderer,
    SvgBlogCardRenderer,
    SvgCard,
    SvgCardFamily,
    SvgConnectCardRenderer,
    SvgRepoCardRenderer,
)

BANNER_SNAPSHOT_SEED = 42

# Platform float noise (macOS vs Linux) can perturb long path coordinates by
# ~1e-9 while structure stays identical. Normalize before snapshot compare.
_FLOAT_RE = re.compile(r"(-?\d+\.\d{6,})")


def _normalize_svg_floats(svg: str, *, digits: int = 6) -> str:
    """Round long decimal literals so cross-platform banner snapshots stay stable."""

    def _round(match: re.Match[str]) -> str:
        value = float(match.group(1))
        return f"{value:.{digits}f}".rstrip("0").rstrip(".") or "0"

    return _FLOAT_RE.sub(_round, svg)


def _write_drawing_via_tostring(
    self, pretty: bool = False, filename: str | Path | None = None
) -> None:
    """``Drawing.save`` workaround: ``svg_drawing.Path`` shadows ``pathlib.Path``."""
    from pathlib import Path as FsPath

    target = FsPath(filename or self.filename or "drawing.svg")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(self.tostring(pretty=pretty), encoding="utf-8")


def _render_seeded_banner_svg(
    output_path: Path, *, seed: int = BANNER_SNAPSHOT_SEED
) -> str:
    """Render a compact, seeded banner SVG suitable for snapshotting."""
    cfg = BannerConfig(
        title="Snapshot",
        subtitle="Deterministic",
        width=320,
        height=96,
        pattern_density=0.05,
        layer_count=1,
        fibonacci_steps=[1],
        optimize_with_svgo=False,
        output_path=str(output_path),
        seed=seed,
        make_responsive=False,
    )
    aizawa = [Point3DModel(x=0.01 * i, y=0.02 * i, z=0.005 * i) for i in range(25)]
    lorenz = [(0.01 * i, 0.02 * i, 0.005 * i) for i in range(40)]
    neural = (
        [(0.1, 0.2, 0.5), (0.4, 0.6, 0.8), (0.7, 0.3, 0.4)],
        [(0, 1, 0.5), (1, 2, 0.3)],
    )
    with (
        patch("scripts.banner.Drawing.save", _write_drawing_via_tostring),
        # ``Drawing.text`` is shadowed by ``Element.text``; skip title until fixed.
        patch("scripts.banner.add_title_and_subtitle"),
        patch("scripts.banner.add_octocat"),
        patch("scripts.banner.generate_aizawa", return_value=aizawa),
        patch("scripts.banner.generate_lorenz", return_value=lorenz),
        patch("scripts.banner.generate_neural_network", return_value=neural),
    ):
        generate_banner(cfg, seed=seed)
    return output_path.read_text(encoding="utf-8")


class TestBannerSvgSnapshots:
    def test_seeded_banner_matches_snapshot(self, snapshot_svg, tmp_path: Path) -> None:
        svg = _render_seeded_banner_svg(
            tmp_path / "banner.svg", seed=BANNER_SNAPSHOT_SEED
        )
        assert svg.lstrip().startswith("<?xml") or svg.lstrip().startswith("<svg")
        # Compare normalized form so macOS/Linux float noise does not flake CI.
        assert _normalize_svg_floats(svg) == snapshot_svg

    def test_seeded_banner_is_deterministic(self, tmp_path: Path) -> None:
        first = _render_seeded_banner_svg(tmp_path / "a.svg", seed=BANNER_SNAPSHOT_SEED)
        second = _render_seeded_banner_svg(
            tmp_path / "b.svg", seed=BANNER_SNAPSHOT_SEED
        )
        assert _normalize_svg_floats(first) == _normalize_svg_floats(second)


class TestReadmeSvgSnapshots:
    def test_block_renderer_connect_snapshot(self, snapshot_svg) -> None:
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
                    accent="181717",
                ),
                SvgCard(
                    title="LinkedIn",
                    lines=("https://linkedin.com/in/wyattowalsh",),
                    meta=("badge #0A66C2",),
                    accent="0A66C2",
                ),
            ),
            columns=2,
        )
        assert renderer.render(block) == snapshot_svg

    def test_repo_card_renderer_snapshot(self, snapshot_svg) -> None:
        renderer = SvgRepoCardRenderer(width=500, height=185)
        card = SvgCard(
            title="nbadb",
            kicker="wyattowalsh/nbadb",
            lines=("Data Extraction and Processing Scripts",),
            meta=("lang:Python", "★ 57", "⑂ 14", "Updated 2 days ago"),
            sparkline=(0.0, 2.0, 5.0, 8.0, 12.0),
            languages={"Python": 8000, "Shell": 2000},
            license_spdx="MIT",
        )
        assert renderer.render_card(card) == snapshot_svg

    def test_blog_card_renderer_snapshot(self, snapshot_svg) -> None:
        renderer = SvgBlogCardRenderer(width=480, height=150)
        card = SvgCard(
            title="Shipping syrupy SVG snapshots",
            lines=("Deterministic visual regression for README cards.",),
            meta=("2026-07-31", "w4w.dev"),
            url="https://w4w.dev/blog/syrupy-svg",
        )
        assert renderer.render_card(card) == snapshot_svg

    def test_connect_card_renderer_snapshot(self, snapshot_svg) -> None:
        renderer = SvgConnectCardRenderer(width=140, height=130)
        card = SvgCard(
            title="GitHub",
            icon="GH",
            icon_data_uri="data:image/svg+xml;base64,PHN2Zy8+",
            kicker="CODE",
            badge="Builder",
            accent="181717",
            url="https://github.com/wyattowalsh",
        )
        assert renderer.render_card(card) == snapshot_svg

    def test_featured_block_with_title_snapshot(self, snapshot_svg) -> None:
        renderer = SvgBlockRenderer(width=480, card_height=120, padding=12)
        block = SvgBlock(
            title="Featured",
            cards=(
                SvgCard(
                    title="riso",
                    lines=("Composable scaffolding framework",),
                    url="https://github.com/wyattowalsh/riso",
                    meta=("lang:Python", "★ 42"),
                ),
            ),
            columns=1,
            family=SvgCardFamily.FEATURED,
            show_title=True,
            transparent_canvas=False,
        )
        assert renderer.render(block) == snapshot_svg
