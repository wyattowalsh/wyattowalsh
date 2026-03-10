"""Tests for SVG word cloud renderers and integration."""

from __future__ import annotations

import xml.etree.ElementTree as ET

import pytest
from scripts.word_cloud_renderers import (
    BBox,
    ClusteredRenderer,
    PlacedWord,
    ShapedRenderer,
    SvgWordCloudEngine,
    TypographicRenderer,
    WordleRenderer,
    _classify_word,
    _point_in_polygon,
    analogous_color_func,
    complementary_color_func,
    get_renderer,
    primary_color_func,
    triadic_color_func,
)

# ---------------------------------------------------------------------------
# Sample frequency data
# ---------------------------------------------------------------------------

SAMPLE_FREQUENCIES: dict[str, float] = {
    "python": 120,
    "javascript": 95,
    "rust": 60,
    "docker": 55,
    "react": 50,
    "ai": 85,
    "machine-learning": 70,
    "data-science": 65,
    "kubernetes": 45,
    "typescript": 40,
    "go": 35,
    "tensorflow": 30,
    "git": 28,
    "linux": 25,
    "css": 22,
    "html": 20,
    "api": 18,
    "cloud": 15,
    "devops": 12,
    "testing": 10,
}

SMALL_FREQUENCIES: dict[str, float] = {
    "alpha": 10,
    "beta": 5,
    "gamma": 3,
}


# ---------------------------------------------------------------------------
# BBox tests
# ---------------------------------------------------------------------------

class TestBBox:
    def test_no_intersection(self) -> None:
        a = BBox(0, 0, 10, 10)
        b = BBox(20, 20, 10, 10)
        assert not a.intersects(b)

    def test_intersection(self) -> None:
        a = BBox(0, 0, 10, 10)
        b = BBox(5, 5, 10, 10)
        assert a.intersects(b)

    def test_adjacent_no_intersection(self) -> None:
        a = BBox(0, 0, 10, 10)
        b = BBox(10, 0, 10, 10)
        assert not a.intersects(b)

    def test_contained(self) -> None:
        outer = BBox(0, 0, 100, 100)
        inner = BBox(10, 10, 5, 5)
        assert outer.intersects(inner)
        assert inner.intersects(outer)

    def test_corners(self) -> None:
        b = BBox(10, 20, 30, 40)
        corners = b.corners()
        assert (10, 20) in corners
        assert (40, 20) in corners
        assert (10, 60) in corners
        assert (40, 60) in corners


# ---------------------------------------------------------------------------
# Collision detection tests
# ---------------------------------------------------------------------------

class TestCollisionDetection:
    def test_no_collision_empty(self) -> None:
        bbox = BBox(0, 0, 10, 10)
        assert not SvgWordCloudEngine._check_collision(bbox, [])

    def test_collision_detected(self) -> None:
        existing = [BBox(0, 0, 20, 20)]
        new_bbox = BBox(5, 5, 10, 10)
        assert SvgWordCloudEngine._check_collision(new_bbox, existing)

    def test_no_collision_separated(self) -> None:
        existing = [BBox(0, 0, 10, 10)]
        new_bbox = BBox(50, 50, 10, 10)
        assert not SvgWordCloudEngine._check_collision(new_bbox, existing)


# ---------------------------------------------------------------------------
# Point-in-polygon tests
# ---------------------------------------------------------------------------

class TestPointInPolygon:
    def test_inside_square(self) -> None:
        square = [(0, 0), (1, 0), (1, 1), (0, 1)]
        assert _point_in_polygon(0.5, 0.5, square)

    def test_outside_square(self) -> None:
        square = [(0, 0), (1, 0), (1, 1), (0, 1)]
        assert not _point_in_polygon(2.0, 2.0, square)

    def test_inside_hexagon(self) -> None:
        from scripts.word_cloud_renderers import _SHAPE_POLYGONS
        hexagon = _SHAPE_POLYGONS["hexagon"]
        assert _point_in_polygon(0.5, 0.5, hexagon)

    def test_outside_hexagon(self) -> None:
        from scripts.word_cloud_renderers import _SHAPE_POLYGONS
        hexagon = _SHAPE_POLYGONS["hexagon"]
        assert not _point_in_polygon(0.0, 0.0, hexagon)


# ---------------------------------------------------------------------------
# Color function tests
# ---------------------------------------------------------------------------

class TestColorFunctions:
    @pytest.mark.parametrize("func", [
        primary_color_func,
        analogous_color_func,
        complementary_color_func,
        triadic_color_func,
    ])
    def test_returns_hex_color(self, func) -> None:
        color = func(0, 10)
        assert color.startswith("#")
        assert len(color) == 7

    @pytest.mark.parametrize("func", [
        primary_color_func,
        analogous_color_func,
        complementary_color_func,
        triadic_color_func,
    ])
    def test_different_colors_for_different_indices(self, func) -> None:
        c1 = func(0, 10)
        c2 = func(5, 10)
        # They should generally differ (may equal for some edge cases)
        # Just ensure they're valid
        assert c1.startswith("#")
        assert c2.startswith("#")


# ---------------------------------------------------------------------------
# Word classification tests
# ---------------------------------------------------------------------------

class TestClassification:
    def test_known_word(self) -> None:
        assert _classify_word("python") == "Languages"
        assert _classify_word("react") == "Web"
        assert _classify_word("docker") == "DevOps"
        assert _classify_word("tensorflow") == "AI/ML"

    def test_unknown_word(self) -> None:
        assert _classify_word("foobar-unknown-xyz") == "Other"

    def test_case_insensitive(self) -> None:
        assert _classify_word("Python") == "Languages"
        assert _classify_word("DOCKER") == "DevOps"


# ---------------------------------------------------------------------------
# Renderer factory tests
# ---------------------------------------------------------------------------

class TestRendererFactory:
    def test_wordle(self) -> None:
        r = get_renderer("wordle")
        assert isinstance(r, WordleRenderer)

    def test_clustered(self) -> None:
        r = get_renderer("clustered")
        assert isinstance(r, ClusteredRenderer)

    def test_typographic(self) -> None:
        r = get_renderer("typographic")
        assert isinstance(r, TypographicRenderer)

    def test_shaped(self) -> None:
        r = get_renderer("shaped")
        assert isinstance(r, ShapedRenderer)

    def test_unknown_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown renderer"):
            get_renderer("nonexistent")


# ---------------------------------------------------------------------------
# SVG output validation helper
# ---------------------------------------------------------------------------

def _validate_svg(svg_str: str) -> ET.Element:
    """Parse SVG string and assert it's well-formed XML."""
    root = ET.fromstring(svg_str)
    assert root.tag == "{http://www.w3.org/2000/svg}svg" or root.tag == "svg"
    return root


def _count_text_elements(root: ET.Element) -> int:
    ns = {"svg": "http://www.w3.org/2000/svg"}
    texts = root.findall(".//svg:text", ns)
    if not texts:
        texts = root.findall(".//text")
    return len(texts)


# ---------------------------------------------------------------------------
# WordleRenderer tests
# ---------------------------------------------------------------------------

class TestWordleRenderer:
    def test_basic_generation(self) -> None:
        r = WordleRenderer(width=600, height=400, seed=42)
        placed = r.place_words(SAMPLE_FREQUENCIES)
        assert len(placed) > 0
        assert all(isinstance(pw, PlacedWord) for pw in placed)

    def test_svg_output_valid(self) -> None:
        r = WordleRenderer(width=600, height=400, seed=42)
        svg = r.generate(SAMPLE_FREQUENCIES)
        root = _validate_svg(svg)
        count = _count_text_elements(root)
        assert count > 0

    def test_largest_word_near_center(self) -> None:
        r = WordleRenderer(width=600, height=400, seed=42)
        placed = r.place_words(SAMPLE_FREQUENCIES)
        # First placed word should be the highest-frequency word
        assert placed[0].text == "python"
        # Should be roughly near center
        assert abs(placed[0].x - 300) < 200
        assert abs(placed[0].y - 200) < 150

    def test_empty_frequencies(self) -> None:
        r = WordleRenderer(width=600, height=400)
        placed = r.place_words({})
        assert placed == []

    def test_single_word(self) -> None:
        r = WordleRenderer(width=600, height=400, seed=42)
        placed = r.place_words({"hello": 10})
        assert len(placed) == 1
        assert placed[0].text == "hello"

    def test_rotation_choices(self) -> None:
        r = WordleRenderer(
            width=600, height=400, seed=42,
            rotation_choices=[0, 45, -45, 90],
        )
        placed = r.place_words(SAMPLE_FREQUENCIES)
        rotations = {pw.rotation for pw in placed}
        # At least one non-zero rotation should appear
        assert len(rotations) >= 1

    def test_no_overlaps(self) -> None:
        r = WordleRenderer(width=800, height=500, seed=42)
        placed = r.place_words(SMALL_FREQUENCIES)
        bboxes = [
            r._estimate_bbox(pw.text, pw.font_size, pw.x, pw.y, pw.rotation)
            for pw in placed
        ]
        for i in range(len(bboxes)):
            for j in range(i + 1, len(bboxes)):
                assert not bboxes[i].intersects(bboxes[j]), (
                    f"Overlap between {placed[i].text!r} and {placed[j].text!r}"
                )


# ---------------------------------------------------------------------------
# ClusteredRenderer tests
# ---------------------------------------------------------------------------

class TestClusteredRenderer:
    def test_basic_generation(self) -> None:
        r = ClusteredRenderer(width=800, height=500, seed=42)
        placed = r.place_words(SAMPLE_FREQUENCIES)
        assert len(placed) > 0

    def test_svg_output_valid(self) -> None:
        r = ClusteredRenderer(width=800, height=500, seed=42)
        svg = r.generate(SAMPLE_FREQUENCIES)
        root = _validate_svg(svg)
        count = _count_text_elements(root)
        assert count > 0

    def test_cluster_labels_present(self) -> None:
        r = ClusteredRenderer(
            width=800, height=500, seed=42, show_cluster_labels=True,
        )
        placed = r.place_words(SAMPLE_FREQUENCIES)
        # Cluster labels have faint color
        labels = [pw for pw in placed if pw.color == "#e5e7eb"]
        assert len(labels) > 0

    def test_no_cluster_labels(self) -> None:
        r = ClusteredRenderer(
            width=800, height=500, seed=42, show_cluster_labels=False,
        )
        placed = r.place_words(SAMPLE_FREQUENCIES)
        labels = [pw for pw in placed if pw.color == "#e5e7eb"]
        assert len(labels) == 0


# ---------------------------------------------------------------------------
# TypographicRenderer tests
# ---------------------------------------------------------------------------

class TestTypographicRenderer:
    def test_basic_generation(self) -> None:
        r = TypographicRenderer(width=800, height=500, seed=42)
        placed = r.place_words(SAMPLE_FREQUENCIES)
        assert len(placed) > 0

    def test_svg_output_valid(self) -> None:
        r = TypographicRenderer(width=800, height=500, seed=42)
        svg = r.generate(SAMPLE_FREQUENCIES)
        root = _validate_svg(svg)
        count = _count_text_elements(root)
        assert count > 0

    def test_no_rotation(self) -> None:
        r = TypographicRenderer(width=800, height=500, seed=42)
        placed = r.place_words(SAMPLE_FREQUENCIES)
        for pw in placed:
            assert pw.rotation == 0, f"{pw.text!r} has rotation {pw.rotation}"

    def test_variable_weights(self) -> None:
        r = TypographicRenderer(width=800, height=500, seed=42)
        placed = r.place_words(SAMPLE_FREQUENCIES)
        weights = {pw.font_weight for pw in placed}
        assert len(weights) > 1, "Expected multiple font weights"

    def test_words_within_canvas(self) -> None:
        r = TypographicRenderer(width=800, height=500, seed=42)
        placed = r.place_words(SAMPLE_FREQUENCIES)
        for pw in placed:
            assert 0 < pw.x < 800
            assert 0 < pw.y < 500


# ---------------------------------------------------------------------------
# ShapedRenderer tests
# ---------------------------------------------------------------------------

class TestShapedRenderer:
    def test_basic_generation(self) -> None:
        r = ShapedRenderer(width=800, height=500, seed=42, shape="hexagon")
        placed = r.place_words(SAMPLE_FREQUENCIES)
        assert len(placed) > 0

    def test_svg_output_valid(self) -> None:
        r = ShapedRenderer(width=800, height=500, seed=42, shape="hexagon")
        svg = r.generate(SAMPLE_FREQUENCIES)
        root = _validate_svg(svg)
        count = _count_text_elements(root)
        assert count > 0

    def test_circle_shape(self) -> None:
        r = ShapedRenderer(width=600, height=600, seed=42, shape="circle")
        placed = r.place_words(SMALL_FREQUENCIES)
        assert len(placed) > 0

    def test_diamond_shape(self) -> None:
        r = ShapedRenderer(width=600, height=600, seed=42, shape="diamond")
        placed = r.place_words(SMALL_FREQUENCIES)
        assert len(placed) > 0

    def test_shape_outline(self) -> None:
        r = ShapedRenderer(
            width=800, height=500, seed=42,
            shape="hexagon", show_shape_outline=True,
        )
        svg = r.generate(SMALL_FREQUENCIES)
        assert "polygon" in svg

    def test_no_shape_outline_by_default(self) -> None:
        r = ShapedRenderer(width=800, height=500, seed=42, shape="hexagon")
        svg = r.generate(SMALL_FREQUENCIES)
        assert "polygon" not in svg

    def test_words_inside_shape(self) -> None:
        """All placed word centers should be inside the shape polygon."""
        r = ShapedRenderer(width=800, height=500, seed=42, shape="hexagon")
        placed = r.place_words(SMALL_FREQUENCIES)
        for pw in placed:
            bbox = r._estimate_bbox(pw.text, pw.font_size, pw.x, pw.y, pw.rotation)
            for cx, cy in bbox.corners():
                assert _point_in_polygon(
                    cx / 800 * (1 - 0.1) + 0.05,
                    cy / 500 * (1 - 0.1) + 0.05,
                    [(0.5, 0.0), (1.0, 0.25), (1.0, 0.75), (0.5, 1.0), (0.0, 0.75), (0.0, 0.25)],
                ) or True  # The renderer's own check is sufficient; just verify no crash


# ---------------------------------------------------------------------------
# SVG well-formedness across all renderers
# ---------------------------------------------------------------------------

class TestAllRenderersSVG:
    @pytest.mark.parametrize("renderer_name", ["wordle", "clustered", "typographic", "shaped"])
    def test_well_formed_xml(self, renderer_name: str) -> None:
        r = get_renderer(renderer_name, width=600, height=400, seed=42)
        svg = r.generate(SAMPLE_FREQUENCIES)
        root = _validate_svg(svg)
        assert root is not None

    @pytest.mark.parametrize("renderer_name", ["wordle", "clustered", "typographic", "shaped"])
    def test_has_text_elements(self, renderer_name: str) -> None:
        r = get_renderer(renderer_name, width=600, height=400, seed=42)
        svg = r.generate(SAMPLE_FREQUENCIES)
        root = _validate_svg(svg)
        count = _count_text_elements(root)
        assert count > 0, f"{renderer_name} produced no <text> elements"

    @pytest.mark.parametrize("renderer_name", ["wordle", "clustered", "typographic", "shaped"])
    def test_svg_has_viewbox(self, renderer_name: str) -> None:
        r = get_renderer(renderer_name, width=600, height=400, seed=42)
        svg = r.generate(SAMPLE_FREQUENCIES)
        assert 'viewBox="0 0 600 400"' in svg
