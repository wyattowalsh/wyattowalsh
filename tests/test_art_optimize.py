"""Tests for scripts.art.optimize — layout and color metaheuristics."""

from __future__ import annotations

import pytest

from scripts.art.optimize import (
    _SOLVER_MAP,
    _golden_ratio_score,
    _hue_distance,
    _margin_score,
    _spacing_score,
    _visual_balance_score,
    _whitespace_uniformity,
    art_layout_cost,
    color_harmony_score,
    constellation_layout_cost,
    optimize_layout_pso,
    optimize_layout_sa,
    optimize_palette_hues,
    optimize_placement,
    star_layout_cost,
)

# ---------------------------------------------------------------------------
# Cost / scoring helpers
# ---------------------------------------------------------------------------


class TestScoringHelpers:
    def test_golden_ratio_empty(self) -> None:
        assert _golden_ratio_score([], 100.0, 100.0) == 0.5

    def test_golden_ratio_at_focal(self) -> None:
        phi = 0.381966
        positions = [(100.0 * phi, 100.0 * phi)]
        score = _golden_ratio_score(positions, 100.0, 100.0)
        assert score == pytest.approx(0.0, abs=1e-9)

    def test_visual_balance_centered(self) -> None:
        positions = [(50.0, 50.0), (50.0, 50.0)]
        weights = [1.0, 1.0]
        assert _visual_balance_score(positions, weights, 100.0, 100.0) == pytest.approx(
            0.0, abs=1e-9
        )

    def test_visual_balance_empty(self) -> None:
        assert _visual_balance_score([], [], 100.0, 100.0) == 0.5

    def test_spacing_no_overlap(self) -> None:
        positions = [(0.0, 0.0), (100.0, 0.0)]
        assert _spacing_score(positions, min_distance=50.0) == 0.0

    def test_spacing_overlap_penalty(self) -> None:
        positions = [(0.0, 0.0), (10.0, 0.0)]
        penalty = _spacing_score(positions, min_distance=50.0)
        assert penalty > 0.0

    def test_spacing_single_point(self) -> None:
        assert _spacing_score([(1.0, 1.0)], 10.0) == 0.0

    def test_margin_inside_safe(self) -> None:
        assert _margin_score([(50.0, 50.0)], 100.0, 100.0, margin_frac=0.08) == 0.0

    def test_margin_near_edge(self) -> None:
        penalty = _margin_score([(1.0, 50.0)], 100.0, 100.0, margin_frac=0.08)
        assert penalty > 0.0

    def test_whitespace_uniformity_sparse(self) -> None:
        assert _whitespace_uniformity([(10.0, 10.0), (20.0, 20.0)], 100.0, 100.0) == 0.0

    def test_whitespace_clustered(self) -> None:
        # All points in one cell → high coefficient of variation
        positions = [(5.0, 5.0), (6.0, 6.0), (7.0, 7.0), (8.0, 8.0)]
        score = _whitespace_uniformity(positions, 100.0, 100.0)
        assert score > 0.0


class TestArtLayoutCost:
    def test_lower_cost_for_spread_layout(self) -> None:
        canvas = 400.0
        weights = [1.0, 1.0, 1.0, 1.0]
        clustered = [(200.0, 200.0)] * 4
        spread = [
            (80.0, 80.0),
            (320.0, 80.0),
            (80.0, 320.0),
            (320.0, 320.0),
        ]
        assert art_layout_cost(spread, weights, canvas, canvas, min_spacing=60.0) < (
            art_layout_cost(clustered, weights, canvas, canvas, min_spacing=60.0)
        )


class TestColorHarmony:
    def test_hue_distance_wraps(self) -> None:
        assert _hue_distance(10.0, 350.0) == pytest.approx(20.0)
        assert _hue_distance(0.0, 180.0) == pytest.approx(180.0)

    def test_single_hue_perfect(self) -> None:
        assert color_harmony_score([120.0]) == 0.0

    def test_complementary_better_than_near_duplicate(self) -> None:
        complementary = color_harmony_score([0.0, 180.0])
        near_dup = color_harmony_score([0.0, 5.0])
        assert complementary < near_dup

    def test_optimize_palette_single_hue_noop(self) -> None:
        assert optimize_palette_hues([42.0]) == [42.0]

    def test_optimize_palette_improves_or_equals(self) -> None:
        base = [0.0, 10.0, 20.0]
        optimized = optimize_palette_hues(base, iterations=80, seed=7)
        assert len(optimized) == 3
        assert color_harmony_score(optimized) <= color_harmony_score(base) + 1e-9


# ---------------------------------------------------------------------------
# Layout optimizers
# ---------------------------------------------------------------------------


class TestLayoutOptimizers:
    def test_pso_passthrough_single(self) -> None:
        positions = [(10.0, 20.0)]
        assert optimize_layout_pso(positions, [1.0], 200.0, 200.0) == positions

    def test_sa_passthrough_single(self) -> None:
        positions = [(10.0, 20.0)]
        assert optimize_layout_sa(positions, [1.0], 200.0, 200.0) == positions

    def test_pso_returns_same_length(self) -> None:
        initial = [(50.0, 50.0), (60.0, 60.0), (150.0, 150.0)]
        weights = [1.0, 1.0, 2.0]
        result = optimize_layout_pso(
            initial,
            weights,
            300.0,
            300.0,
            iterations=20,
            swarm_size=5,
            seed=1,
            min_spacing=40.0,
        )
        assert len(result) == 3
        for x, y in result:
            assert 0.0 <= x <= 300.0
            assert 0.0 <= y <= 300.0

    def test_sa_returns_same_length(self) -> None:
        initial = [(40.0, 40.0), (80.0, 200.0), (220.0, 100.0)]
        weights = [1.0, 1.5, 1.0]
        result = optimize_layout_sa(
            initial,
            weights,
            300.0,
            300.0,
            iterations=40,
            seed=2,
            min_spacing=40.0,
        )
        assert len(result) == 3


# ---------------------------------------------------------------------------
# Specialized costs
# ---------------------------------------------------------------------------


class TestSpecializedCosts:
    def test_star_layout_cost_finite(self) -> None:
        positions = [(20.0, 20.0), (80.0, 80.0), (40.0, 90.0)]
        cost = star_layout_cost(positions, [1.0, 1.0, 1.0], 100.0, 100.0)
        assert cost >= 0.0

    def test_constellation_empty_pairs(self) -> None:
        assert constellation_layout_cost([(1.0, 1.0)], [0], 100.0, 100.0) == 0.0

    def test_constellation_rewards_cohesion(self) -> None:
        # Same cluster far apart → higher cost than close together
        far = [(10.0, 10.0), (90.0, 90.0)]
        near = [(40.0, 40.0), (50.0, 50.0)]
        ids = [0, 0]
        assert constellation_layout_cost(near, ids, 100.0, 100.0) < (
            constellation_layout_cost(far, ids, 100.0, 100.0)
        )


# ---------------------------------------------------------------------------
# Unified dispatcher
# ---------------------------------------------------------------------------


class TestOptimizePlacement:
    def test_passthrough_under_two(self) -> None:
        assert optimize_placement([(1.0, 2.0)], [1.0], 100.0, 100.0) == [(1.0, 2.0)]

    def test_auto_selects_sa_for_small_n(self) -> None:
        initial = [(30.0, 30.0), (70.0, 80.0), (120.0, 40.0)]
        result = optimize_placement(
            initial,
            [1.0, 1.0, 1.0],
            200.0,
            200.0,
            solver="auto",
            max_iter=25,
            seed=3,
        )
        assert len(result) == 3

    def test_explicit_solvers(self) -> None:
        initial = [(40.0, 40.0), (160.0, 160.0), (80.0, 140.0), (140.0, 60.0)]
        weights = [1.0, 1.0, 1.0, 1.0]
        for solver in ("sa", "pso", "grey_wolf", "firefly", "whale", "flower", "de"):
            assert solver in _SOLVER_MAP
            result = optimize_placement(
                initial,
                weights,
                220.0,
                220.0,
                solver=solver,
                max_iter=15,
                seed=9,
                min_spacing=30.0,
            )
            assert len(result) == len(initial)

    def test_unknown_solver_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown solver"):
            optimize_placement(
                [(10.0, 10.0), (20.0, 20.0)],
                [1.0, 1.0],
                100.0,
                100.0,
                solver="not-real",
            )

    def test_auto_grey_wolf_band(self) -> None:
        # n in [8, 50) → grey_wolf path
        n = 10
        initial = [
            (float(i * 15 % 180 + 20), float(i * 11 % 180 + 20)) for i in range(n)
        ]
        weights = [1.0] * n
        result = optimize_placement(
            initial,
            weights,
            220.0,
            220.0,
            solver="auto",
            max_iter=10,
            seed=4,
        )
        assert len(result) == n
