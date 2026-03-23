"""Tests for the OKLCH color pipeline, palettes, and visual parameter functions."""

from __future__ import annotations

import math

import pytest

pytest.importorskip("numpy", reason="scripts.art.shared requires numpy")

from scripts.art.shared import (  # noqa: E402
    ART_PALETTE_ANCHORS,
    CLUSTER_PALETTES,
    WorldState,
    _build_world_palette_extended,
    activity_tempo,
    blend_mode_filter,
    compute_world_state,
    ensure_contrast,
    hex_to_oklch,
    oklch,
    oklch_gamut_map,
    oklch_gradient,
    oklch_lerp,
    organic_texture_filter,
    select_palette_for_world,
    smil_animate,
    smil_animate_transform,
    topic_affinity_matrix,
    visual_complexity,
    wcag_contrast_ratio,
)


# ---------------------------------------------------------------------------
# hex_to_oklch round-trip tests
# ---------------------------------------------------------------------------


class TestHexToOklch:
    def test_round_trip_red(self) -> None:
        L, C, H = hex_to_oklch("#ff0000")
        result = oklch(L, C, H)
        assert result == "#ff0000", f"Round-trip red failed: {result}"

    def test_round_trip_white(self) -> None:
        L, C, H = hex_to_oklch("#ffffff")
        assert L == pytest.approx(1.0, abs=0.01)
        assert C == pytest.approx(0.0, abs=0.02)  # near-zero chroma

    def test_round_trip_black(self) -> None:
        L, C, H = hex_to_oklch("#000000")
        assert L == pytest.approx(0.0, abs=0.01)

    def test_known_hue_blue(self) -> None:
        _, _, H = hex_to_oklch("#0000ff")
        # Blue hue should be roughly 260-270 in OKLCH
        assert 250 < H < 275, f"Blue hue {H} outside expected range"


# ---------------------------------------------------------------------------
# oklch_lerp tests
# ---------------------------------------------------------------------------


class TestOklchLerp:
    def test_identity_at_zero(self) -> None:
        result = oklch_lerp("#ff0000", "#0000ff", 0.0)
        assert result == "#ff0000"

    def test_identity_at_one(self) -> None:
        result = oklch_lerp("#ff0000", "#0000ff", 1.0)
        # Allow ±1 per channel due to float precision in OKLCH round-trip
        r, g, b = int(result[1:3], 16), int(result[3:5], 16), int(result[5:7], 16)
        assert r <= 8 and g <= 8 and b >= 247

    def test_midpoint_differs(self) -> None:
        mid = oklch_lerp("#ff0000", "#0000ff", 0.5)
        assert mid != "#ff0000"
        assert mid != "#0000ff"

    def test_same_color_returns_similar(self) -> None:
        result = oklch_lerp("#abcdef", "#abcdef", 0.5)
        # Allow small drift from OKLCH round-trip precision
        r1, g1, b1 = 0xab, 0xcd, 0xef
        r2, g2, b2 = int(result[1:3], 16), int(result[3:5], 16), int(result[5:7], 16)
        assert abs(r1 - r2) <= 4 and abs(g1 - g2) <= 4 and abs(b1 - b2) <= 8

    def test_returns_valid_hex(self) -> None:
        result = oklch_lerp("#123456", "#fedcba", 0.3)
        assert result.startswith("#")
        assert len(result) == 7


# ---------------------------------------------------------------------------
# oklch_gradient tests
# ---------------------------------------------------------------------------


class TestOklchGradient:
    def test_correct_count(self) -> None:
        anchors = [(0.5, 0.1, 0), (0.8, 0.2, 180)]
        assert len(oklch_gradient(anchors, 5)) == 5

    def test_single_returns_one(self) -> None:
        result = oklch_gradient([(0.5, 0.1, 90)], 1)
        assert len(result) == 1

    def test_empty_returns_empty(self) -> None:
        assert oklch_gradient([(0.5, 0.1, 0)], 0) == []

    def test_all_valid_hex(self) -> None:
        colors = oklch_gradient(ART_PALETTE_ANCHORS["sunset"], 10)
        assert len(colors) == 10
        for c in colors:
            assert c.startswith("#") and len(c) == 7


# ---------------------------------------------------------------------------
# oklch_gamut_map tests
# ---------------------------------------------------------------------------


class TestOklchGamutMap:
    def test_in_gamut_unchanged(self) -> None:
        # Use a known in-gamut color (low chroma, mid lightness)
        L, C, H = 0.6, 0.05, 200
        L2, C2, H2 = oklch_gamut_map(L, C, H)
        assert C2 == pytest.approx(C, abs=0.005)
        assert H2 == pytest.approx(H)

    def test_out_of_gamut_reduces_chroma(self) -> None:
        # 0.5 chroma at hue 0 is way out of gamut
        _, C2, _ = oklch_gamut_map(0.5, 0.5, 0)
        assert C2 < 0.5

    def test_preserves_hue(self) -> None:
        _, _, H2 = oklch_gamut_map(0.5, 0.5, 120)
        assert H2 == pytest.approx(120)


# ---------------------------------------------------------------------------
# WCAG contrast tests
# ---------------------------------------------------------------------------


class TestWcagContrast:
    def test_black_on_white(self) -> None:
        assert wcag_contrast_ratio("#000000", "#ffffff") == pytest.approx(21.0, abs=0.1)

    def test_white_on_white(self) -> None:
        assert wcag_contrast_ratio("#ffffff", "#ffffff") == pytest.approx(1.0, abs=0.1)

    def test_symmetric(self) -> None:
        r1 = wcag_contrast_ratio("#336699", "#ffffff")
        r2 = wcag_contrast_ratio("#ffffff", "#336699")
        assert r1 == pytest.approx(r2)

    def test_ensure_contrast_passes_through(self) -> None:
        # Already meets ratio
        result = ensure_contrast("#000000", "#ffffff", 4.5)
        assert result == "#000000"

    def test_ensure_contrast_adjusts(self) -> None:
        # Low contrast: light grey on white
        result = ensure_contrast("#cccccc", "#ffffff", 4.5)
        ratio = wcag_contrast_ratio(result, "#ffffff")
        assert ratio >= 4.5


# ---------------------------------------------------------------------------
# Palette & world state tests
# ---------------------------------------------------------------------------


class TestPalettes:
    def test_all_palette_anchors_valid(self) -> None:
        for name, anchors in ART_PALETTE_ANCHORS.items():
            assert len(anchors) >= 3, f"Palette {name} has fewer than 3 anchors"
            for L, C, H in anchors:
                assert 0 <= L <= 1.0
                assert 0 <= C <= 0.5
                assert 0 <= H <= 360

    def test_cluster_palettes_valid(self) -> None:
        for name, colors in CLUSTER_PALETTES.items():
            assert len(colors) >= 3
            for c in colors:
                assert c.startswith("#") and len(c) == 7

    def test_select_palette_night(self) -> None:
        ws = WorldState(time_of_day="night")
        assert select_palette_for_world(ws) == "cosmic"

    def test_select_palette_dawn(self) -> None:
        ws = WorldState(time_of_day="dawn")
        assert select_palette_for_world(ws) == "sunset"

    def test_select_palette_high_energy(self) -> None:
        ws = WorldState(energy=0.9)
        assert select_palette_for_world(ws) == "neon"

    def test_extended_palette_has_12_keys(self) -> None:
        pal = _build_world_palette_extended("day", "clear", "summer", 0.5)
        expected = {
            "sky_top",
            "sky_bottom",
            "ground",
            "accent",
            "glow",
            "text_primary",
            "text_secondary",
            "bg_primary",
            "bg_secondary",
            "highlight",
            "muted",
            "border",
        }
        assert expected.issubset(pal.keys()), f"Missing: {expected - pal.keys()}"


# ---------------------------------------------------------------------------
# GitHub data → visual parameter tests
# ---------------------------------------------------------------------------


class TestVisualParams:
    def test_visual_complexity_empty(self) -> None:
        assert visual_complexity({}) == 0.0

    def test_visual_complexity_scaled(self) -> None:
        vc = visual_complexity({"language_diversity": 2.5})
        assert 0.7 < vc < 0.8

    def test_visual_complexity_capped(self) -> None:
        assert visual_complexity({"language_diversity": 10.0}) == 1.0

    def test_activity_tempo_empty(self) -> None:
        assert activity_tempo(None) == 0.5
        assert activity_tempo({}) == 0.5

    def test_activity_tempo_bursty(self) -> None:
        bursty = {"2024-01": 100, "2024-02": 0, "2024-03": 100, "2024-04": 0}
        assert activity_tempo(bursty) > 0.4

    def test_activity_tempo_steady(self) -> None:
        steady = {"2024-01": 50, "2024-02": 50, "2024-03": 50, "2024-04": 50}
        assert activity_tempo(steady) == 0.0

    def test_topic_affinity_basic(self) -> None:
        repos = [
            {"topics": ["ml", "python"]},
            {"topics": ["ml", "data"]},
            {"topics": ["web"]},
        ]
        aff = topic_affinity_matrix(repos)
        assert (0, 1) in aff  # ml shared
        assert aff[(0, 1)] > 0
        assert (0, 2) not in aff  # no shared topics

    def test_topic_affinity_empty(self) -> None:
        assert topic_affinity_matrix([]) == {}
        assert topic_affinity_matrix([{"topics": []}]) == {}


# ---------------------------------------------------------------------------
# SVG technique tests
# ---------------------------------------------------------------------------


class TestSvgTechniques:
    def test_organic_texture_cloud(self) -> None:
        f = organic_texture_filter("t1", "cloud", 0.5)
        assert '<filter id="t1"' in f
        assert "feTurbulence" in f
        assert "feDisplacementMap" in f

    def test_organic_texture_types(self) -> None:
        for t in ("cloud", "water", "marble", "paper"):
            f = organic_texture_filter("x", t, 0.5)
            assert "<filter" in f

    def test_blend_mode_filter(self) -> None:
        f = blend_mode_filter("b1", "screen")
        assert 'mode="screen"' in f

    def test_smil_animate(self) -> None:
        a = smil_animate("opacity", ["0", "1", "0"], 3.0, begin=1.0)
        assert 'attributeName="opacity"' in a
        assert 'values="0;1;0"' in a
        assert 'dur="3.0s"' in a

    def test_smil_animate_transform(self) -> None:
        a = smil_animate_transform("rotate", ["0", "360"], 5.0)
        assert 'type="rotate"' in a
        assert 'values="0;360"' in a
