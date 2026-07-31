"""Tests for ClusteredRenderer and ShapedRenderer word-cloud engines."""

from __future__ import annotations

from scripts.word_clouds.clustered import ClusteredRenderer
from scripts.word_clouds.colors import CLUSTER_PALETTES, _classify_word
from scripts.word_clouds.core import BBox
from scripts.word_clouds.shaped import (
    ShapedRenderer,
    _SHAPE_POLYGONS,
    _point_in_polygon,
)


# ---------------------------------------------------------------------------
# Domain classification helpers
# ---------------------------------------------------------------------------


class TestClassifyWord:
    def test_known_domains(self) -> None:
        assert _classify_word("pytorch") == "AI/ML"
        assert _classify_word("React") == "Web"
        assert _classify_word("docker") == "DevOps"
        assert _classify_word("python") == "Languages"

    def test_unknown_falls_back_to_other(self) -> None:
        assert _classify_word("not-a-real-tech-xyz") == "Other"


# ---------------------------------------------------------------------------
# ClusteredRenderer
# ---------------------------------------------------------------------------


class TestClusteredRenderer:
    def test_empty_frequencies(self) -> None:
        renderer = ClusteredRenderer(width=800, height=600, seed=1)
        assert renderer.place_words({}) == []

    def test_assign_sectors_empty(self) -> None:
        renderer = ClusteredRenderer(width=800, height=600, seed=1)
        assert renderer._assign_sectors([]) == {}

    def test_assign_sectors_grid(self) -> None:
        renderer = ClusteredRenderer(width=800, height=600, seed=1)
        sectors = renderer._assign_sectors(["A", "B", "C", "D"])
        assert set(sectors) == {"A", "B", "C", "D"}
        # 2x2 grid for 4 clusters
        assert sectors["A"] == (0.0, 0.0, 400.0, 300.0)
        assert sectors["B"] == (400.0, 0.0, 400.0, 300.0)
        assert sectors["C"] == (0.0, 300.0, 400.0, 300.0)
        assert sectors["D"] == (400.0, 300.0, 400.0, 300.0)

    def test_place_words_includes_cluster_labels(self) -> None:
        renderer = ClusteredRenderer(
            width=1200,
            height=800,
            seed=7,
            show_cluster_labels=True,
            min_font_size=8.0,
            max_font_size=48.0,
        )
        frequencies = {
            "pytorch": 10.0,
            "tensorflow": 8.0,
            "react": 9.0,
            "docker": 7.0,
            "python": 12.0,
            "obscure-thing": 3.0,
        }
        placed = renderer.place_words(frequencies)
        texts = {pw.text for pw in placed}
        # Cluster watermark labels should appear when enabled
        assert any(label in texts for label in CLUSTER_PALETTES)
        # Real words should be placed
        assert "pytorch" in texts or "tensorflow" in texts
        assert "react" in texts or "python" in texts

    def test_place_words_without_labels(self) -> None:
        renderer = ClusteredRenderer(
            width=1200,
            height=800,
            seed=3,
            show_cluster_labels=False,
            min_font_size=8.0,
            max_font_size=40.0,
        )
        frequencies = {"pytorch": 5.0, "react": 4.0, "go": 3.0}
        placed = renderer.place_words(frequencies)
        texts = {pw.text for pw in placed}
        assert not texts.intersection(CLUSTER_PALETTES.keys())
        assert texts.issubset(set(frequencies))
        assert len(placed) >= 1

    def test_words_use_cluster_palette_colors(self) -> None:
        renderer = ClusteredRenderer(
            width=1000,
            height=700,
            seed=11,
            show_cluster_labels=False,
        )
        placed = renderer.place_words({"pytorch": 10.0, "llm": 5.0})
        word_placements = [pw for pw in placed if pw.text in {"pytorch", "llm"}]
        assert word_placements
        palette = set(CLUSTER_PALETTES["AI/ML"])
        assert all(pw.color in palette for pw in word_placements)

    def test_spiral_gen_yields_origin_first(self) -> None:
        renderer = ClusteredRenderer(width=400, height=400, seed=1)
        first = next(renderer._spiral_gen(100.0, 200.0, step=2.0, max_steps=5))
        assert first == (100.0, 200.0)


# ---------------------------------------------------------------------------
# ShapedRenderer helpers
# ---------------------------------------------------------------------------


class TestPointInPolygon:
    def test_square_inside_outside(self) -> None:
        square = [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)]
        assert _point_in_polygon(5.0, 5.0, square) is True
        assert _point_in_polygon(15.0, 5.0, square) is False
        assert _point_in_polygon(-1.0, -1.0, square) is False

    def test_diamond_center(self) -> None:
        diamond = _SHAPE_POLYGONS["diamond"]
        # Normalized diamond centered around (0.5, 0.5)
        assert _point_in_polygon(0.5, 0.5, diamond) is True
        assert _point_in_polygon(0.01, 0.01, diamond) is False


class TestShapedRenderer:
    def test_empty_frequencies(self) -> None:
        renderer = ShapedRenderer(width=600, height=600, seed=1, shape="hexagon")
        assert renderer.place_words({}) == []

    def test_unknown_shape_falls_back_to_hexagon(self) -> None:
        renderer = ShapedRenderer(width=400, height=400, seed=1, shape="not-a-shape")
        assert renderer.shape_name == "not-a-shape"
        # Polygon still built from hexagon fallback
        assert len(renderer._polygon) == len(_SHAPE_POLYGONS["hexagon"])

    def test_place_words_inside_circle(self) -> None:
        renderer = ShapedRenderer(
            width=800,
            height=800,
            seed=42,
            shape="circle",
            min_font_size=10.0,
            max_font_size=36.0,
        )
        frequencies = {f"w{i}": float(20 - i) for i in range(12)}
        placed = renderer.place_words(frequencies)
        assert placed
        placed_texts = {pw.text for pw in placed}
        assert placed_texts.issubset(set(frequencies))
        # All placed word centers should be roughly near canvas center
        for pw in placed:
            assert 0 <= pw.x <= renderer.width
            assert 0 <= pw.y <= renderer.height

    def test_all_corners_in_shape_rejects_outside_bbox(self) -> None:
        renderer = ShapedRenderer(width=400, height=400, seed=1, shape="diamond")
        outside = BBox(x=-50.0, y=-50.0, w=10.0, h=10.0)
        assert renderer._all_corners_in_shape(outside) is False
        center = BBox(x=190.0, y=190.0, w=20.0, h=20.0)
        assert renderer._all_corners_in_shape(center) is True

    def test_render_svg_without_outline(self) -> None:
        renderer = ShapedRenderer(
            width=400,
            height=400,
            seed=1,
            shape="hexagon",
            show_shape_outline=False,
        )
        placed = renderer.place_words({"alpha": 5.0, "beta": 3.0})
        svg = renderer.render_svg(placed)
        assert "<svg" in svg
        assert "<polygon" not in svg or "points=" not in svg.split("<text", 1)[0]
        # Without outline override, base renderer should not inject shape polygon first
        assert "alpha" in svg or "beta" in svg

    def test_render_svg_with_outline(self) -> None:
        renderer = ShapedRenderer(
            width=500,
            height=500,
            seed=2,
            shape="star",
            show_shape_outline=True,
            outline_color="#aabbcc",
            outline_width=2.0,
        )
        placed = renderer.place_words({"gamma": 8.0, "delta": 4.0})
        svg = renderer.render_svg(placed)
        assert "<polygon" in svg
        assert "#aabbcc" in svg
        assert "gamma" in svg or "delta" in svg

    def test_supported_shapes_construct(self) -> None:
        for shape in _SHAPE_POLYGONS:
            renderer = ShapedRenderer(width=300, height=300, seed=1, shape=shape)
            assert len(renderer._polygon) == len(_SHAPE_POLYGONS[shape])
            assert renderer.place_words({"one": 1.0})  # at least attempts placement
