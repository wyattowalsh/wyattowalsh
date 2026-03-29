"""Metaheuristic optimization solvers for word cloud placement.

Provides a generic mealpy wrapper that supports ALL ~213 mealpy optimizers
instead of 25 hand-rolled solvers. The domain-specific cost function and
helpers are preserved exactly as before.
"""

from __future__ import annotations

import logging
import math
import random
from collections.abc import Callable

import numpy as np
from mealpy import FloatVar

from .core import BBox
from .readability import (
    DEFAULT_LAYOUT_READABILITY_POLICY,
    LayoutReadabilityPolicy,
    LayoutReadabilitySettings,
    coerce_layout_readability_policy,
)
from ..utils import get_logger

# Suppress ALL mealpy console logging
logging.getLogger("mealpy").setLevel(logging.CRITICAL)

logger = get_logger(module=__name__)

LayoutReadabilityConfig = LayoutReadabilityPolicy | LayoutReadabilitySettings | dict[str, object] | None

# ---------------------------------------------------------------------------
# Metaheuristic aesthetic cost function
# ---------------------------------------------------------------------------

# NOTE: These module-level globals are safe because _run_solver (in metaheuristic.py)
# runs in ProcessPoolExecutor (separate processes with isolated memory).
# Do NOT switch to ThreadPoolExecutor without refactoring to pass state explicitly.

# Rotation choices biased toward horizontal for readability
_META_ROTATIONS = list(DEFAULT_LAYOUT_READABILITY_POLICY.standard_rotations)
_ACTIVE_LAYOUT_READABILITY = DEFAULT_LAYOUT_READABILITY_POLICY
_ACTIVE_WORD_SIZES: tuple[float, ...] = ()
_ACTIVE_MIN_FONT_SIZE = 0.0
_ACTIVE_MAX_FONT_SIZE = 0.0


def configure_layout_readability(
    layout_readability: LayoutReadabilityConfig = None,
    *,
    word_sizes: list[float] | tuple[float, ...] | None = None,
):
    """Set the active readability policy for solver helpers and workers."""

    global _ACTIVE_LAYOUT_READABILITY
    global _ACTIVE_WORD_SIZES
    global _ACTIVE_MIN_FONT_SIZE
    global _ACTIVE_MAX_FONT_SIZE

    _ACTIVE_LAYOUT_READABILITY = coerce_layout_readability_policy(layout_readability)
    _ACTIVE_WORD_SIZES = tuple(word_sizes or ())
    if _ACTIVE_WORD_SIZES:
        _ACTIVE_MIN_FONT_SIZE = min(_ACTIVE_WORD_SIZES)
        _ACTIVE_MAX_FONT_SIZE = max(_ACTIVE_WORD_SIZES)
    else:
        _ACTIVE_MIN_FONT_SIZE = 0.0
        _ACTIVE_MAX_FONT_SIZE = 0.0
    return _ACTIVE_LAYOUT_READABILITY


def _rotation_for_font_size(rng: random.Random, font_size: float) -> float:
    """Choose a rotation that respects the active large-word policy."""

    if _ACTIVE_MAX_FONT_SIZE <= _ACTIVE_MIN_FONT_SIZE:
        return _ACTIVE_LAYOUT_READABILITY.choose_rotation(rng)

    is_large_word = _ACTIVE_LAYOUT_READABILITY.is_large_word(
        font_size,
        _ACTIVE_MIN_FONT_SIZE,
        _ACTIVE_MAX_FONT_SIZE,
    )
    return _ACTIVE_LAYOUT_READABILITY.choose_rotation(rng, is_large_word=is_large_word)


def _clamped_population_size(pop_size: int | None, default: int = 20) -> int:
    """Normalize optional population-size overrides for solver families."""

    if pop_size is None:
        return default
    return max(1, int(pop_size))


def _rotation_readability_penalty(rotation: float) -> float:
    """Map rotation into a readability penalty.

    Horizontal text is ideal, subtle tilts are cheap, and vertical words are
    penalized the most because they slow scanning in landscape layouts.
    """

    abs_rotation = abs(rotation)
    if abs_rotation == 0:
        return 0.0
    if abs_rotation <= 10.0:
        return min(1.0, (abs_rotation / 10.0) * 0.2)
    if abs_rotation >= 80.0:
        return 1.0
    return min(1.0, abs_rotation / 90.0)


def _landscape_aspect_penalty(hull_w: float, hull_h: float, target_aspect_ratio: float, landscape_bias_weight: float) -> float:
    """Prefer broader, landscape-friendly hulls instead of portrait stacks."""

    if hull_w <= 0 or hull_h <= 0:
        return 1.0

    aspect = hull_w / hull_h
    target_penalty = min(1.0, abs(aspect - target_aspect_ratio) / max(target_aspect_ratio, 1.0))
    if aspect >= 1.0:
        return target_penalty

    portrait_penalty = min(1.0, 1.0 - aspect)
    return min(1.0, target_penalty + portrait_penalty * landscape_bias_weight)


def _estimate_word_bbox(
    text: str, font_size: float, x: float, y: float, rotation: float,
    padding: float = 2.0,
) -> BBox:
    """Estimate AABB for a word at (x, y) with given rotation."""
    w = len(text) * font_size * 0.55
    h = font_size * 1.2
    if rotation != 0:
        rad = math.radians(abs(rotation))
        cos_a = abs(math.cos(rad))
        sin_a = abs(math.sin(rad))
        rw = w * cos_a + h * sin_a
        rh = w * sin_a + h * cos_a
        w, h = rw, rh
    return BBox(x - w / 2, y - h / 2, w + padding, h + padding)


def _aesthetic_cost(
    positions: list[tuple[float, float, float]],
    sizes: list[float],
    canvas_w: float,
    canvas_h: float,
    texts: list[str] | None = None,
    layout_readability: LayoutReadabilityConfig = None,
    cost_weights: dict[str, float] | None = None,
) -> float:
    """Evaluate the aesthetic quality of a word placement solution.

    Returns a scalar cost (lower is better) combining:
    1. Overlap penalty (hard constraint)
    2. Packing density (weight 3.0)
    3. Visual balance (weight 2.0)
    4. Whitespace uniformity (weight 2.0)
    5. Reading flow (weight = policy.reading_flow_weight)
    6. Landscape aspect preference (weight 1.0)
    7. Size gradient (weight 1.0)

    Overlap and out-of-bounds penalties are treated as hard constraints with a
    large multiplier so all solver families search for feasible layouts first.

    Uses spatial grid hashing for O(n) overlap detection and approximate NN.
    """
    n = len(positions)
    policy = (
        coerce_layout_readability_policy(layout_readability)
        if layout_readability is not None
        else _ACTIVE_LAYOUT_READABILITY
    )
    if n == 0:
        return 0.0

    canvas_area = canvas_w * canvas_h
    if canvas_area <= 0:
        return float("inf")

    # Build bounding boxes as flat arrays for cache-friendly access
    _texts = texts or ["W" * 6] * n
    # Pre-compute bbox data as flat lists: bx, by, bw, bh, bx2, by2
    bx = [0.0] * n
    by = [0.0] * n
    bw = [0.0] * n
    bh = [0.0] * n
    bx2 = [0.0] * n
    by2 = [0.0] * n
    for i in range(n):
        x, y, rot = positions[i]
        w = len(_texts[i]) * sizes[i] * 0.55
        h = sizes[i] * 1.2
        if rot != 0:
            rad = math.radians(abs(rot))
            cos_a = abs(math.cos(rad))
            sin_a = abs(math.sin(rad))
            w, h = w * cos_a + h * sin_a, w * sin_a + h * cos_a
        bx[i] = x - w / 2
        by[i] = y - h / 2
        bw[i] = w + 2.0
        bh[i] = h + 2.0
        bx2[i] = bx[i] + bw[i]
        by2[i] = by[i] + bh[i]

    # --- Spatial grid for O(n) overlap detection and NN search ---------------
    # Cell size = max bbox dimension to guarantee overlaps only in adjacent cells
    max_dim = 0.0
    for i in range(n):
        d = bw[i] if bw[i] > bh[i] else bh[i]
        if d > max_dim:
            max_dim = d
    cell_size = max(max_dim, 1.0)

    grid: dict[tuple[int, int], list[int]] = {}
    cx_arr = [0.0] * n  # center x
    cy_arr = [0.0] * n  # center y
    for i in range(n):
        cx_arr[i] = positions[i][0]
        cy_arr[i] = positions[i][1]
        gx = int(cx_arr[i] / cell_size)
        gy = int(cy_arr[i] / cell_size)
        key = (gx, gy)
        if key in grid:
            grid[key].append(i)
        else:
            grid[key] = [i]

    # 1. Overlap penalty via grid (check only neighboring cells)
    overlap_area = 0.0
    _seen: set[tuple[int, int]] = set()
    for i in range(n):
        gx = int(cx_arr[i] / cell_size)
        gy = int(cy_arr[i] / cell_size)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                nbr = grid.get((gx + dx, gy + dy))
                if nbr is None:
                    continue
                for j in nbr:
                    if j <= i:
                        continue
                    pair = (i, j)
                    if pair in _seen:
                        continue
                    _seen.add(pair)
                    # AABB overlap test (inlined for speed)
                    if bx2[i] > bx[j] and bx2[j] > bx[i] and by2[i] > by[j] and by2[j] > by[i]:
                        ox = min(bx2[i], bx2[j]) - max(bx[i], bx[j])
                        oy = min(by2[i], by2[j]) - max(by[i], by[j])
                        if ox > 0 and oy > 0:
                            overlap_area += ox * oy
    overlap_norm = min(1.0, overlap_area / canvas_area)

    # 1b. Out-of-bounds penalty — words must stay fully on canvas
    oob_area = 0.0
    for i in range(n):
        left_oob = max(0.0, -bx[i])
        top_oob = max(0.0, -by[i])
        right_oob = max(0.0, bx2[i] - canvas_w)
        bottom_oob = max(0.0, by2[i] - canvas_h)
        oob_area += (left_oob + right_oob) * bh[i] + (top_oob + bottom_oob) * bw[i]
    oob_norm = min(1.0, oob_area / canvas_area)

    # 2. Packing density
    total_bbox_area = 0.0
    min_x = bx[0]
    max_x2 = bx2[0]
    min_y = by[0]
    max_y2 = by2[0]
    for i in range(n):
        total_bbox_area += bw[i] * bh[i]
        if bx[i] < min_x:
            min_x = bx[i]
        if bx2[i] > max_x2:
            max_x2 = bx2[i]
        if by[i] < min_y:
            min_y = by[i]
        if by2[i] > max_y2:
            max_y2 = by2[i]
    hull_w = max_x2 - min_x
    hull_h = max_y2 - min_y
    hull_area = max(hull_w * hull_h, 1.0)
    packing = 1.0 - min(1.0, total_bbox_area / hull_area)

    # 3. Visual balance
    total_weight = 0.0
    wx_sum = 0.0
    wy_sum = 0.0
    for i in range(n):
        area = bw[i] * bh[i]
        wx_sum += cx_arr[i] * area
        wy_sum += cy_arr[i] * area
        total_weight += area
    if total_weight > 0:
        centroid_x = wx_sum / total_weight
        centroid_y = wy_sum / total_weight
    else:
        centroid_x, centroid_y = canvas_w / 2, canvas_h / 2
    max_d = math.hypot(canvas_w / 2, canvas_h / 2)
    balance = min(1.0, math.hypot(centroid_x - canvas_w / 2, centroid_y - canvas_h / 2) / max(max_d, 1.0))

    # 4. Whitespace uniformity via grid-based approximate NN (O(n) amortized)
    nn_dists: list[float] = []
    _hypot = math.hypot
    for i in range(n):
        gx = int(cx_arr[i] / cell_size)
        gy = int(cy_arr[i] / cell_size)
        min_d = float("inf")
        # Search expanding rings: 0, 1, then 2 if still inf
        for ring in range(3):
            for dx in range(-ring, ring + 1):
                for dy in range(-ring, ring + 1):
                    if ring > 0 and abs(dx) < ring and abs(dy) < ring:
                        continue  # skip inner cells already checked
                    nbr = grid.get((gx + dx, gy + dy))
                    if nbr is None:
                        continue
                    for j in nbr:
                        if j == i:
                            continue
                        d = _hypot(cx_arr[i] - cx_arr[j], cy_arr[i] - cy_arr[j])
                        if d < min_d:
                            min_d = d
            if min_d < float("inf"):
                break  # found a neighbor, no need to expand further
        if min_d < float("inf"):
            nn_dists.append(min_d)
    if len(nn_dists) > 1:
        mean_nn = sum(nn_dists) / len(nn_dists)
        var_nn = sum((d - mean_nn) ** 2 for d in nn_dists) / len(nn_dists)
        uniformity = min(1.0, var_nn / max(mean_nn ** 2, 1.0))
    else:
        uniformity = 0.0

    # 5. Reading flow
    max_size = max(sizes) if sizes else 1.0
    flow_penalty = 0.0
    for i in range(n):
        flow_penalty += (sizes[i] / max(max_size, 1.0)) * _rotation_readability_penalty(
            positions[i][2]
        )
    reading_flow = min(1.0, flow_penalty / max(n, 1))

    # 6. Landscape-friendly aspect ratio
    landscape = _landscape_aspect_penalty(
        hull_w,
        hull_h,
        policy.target_aspect_ratio,
        policy.landscape_bias_weight,
    )

    # 7. Size gradient
    center_x, center_y = canvas_w / 2, canvas_h / 2
    max_possible_dist = math.hypot(canvas_w / 2, canvas_h / 2)
    gradient_penalty = 0.0
    for i in range(n):
        gradient_penalty += (sizes[i] / max(max_size, 1.0)) * (
            _hypot(positions[i][0] - center_x, positions[i][1] - center_y)
            / max(max_possible_dist, 1.0)
        )
    size_gradient = min(1.0, gradient_penalty / max(n, 1))

    # Weighted sum — overlap and out-of-bounds are hard constraints
    # (1000x penalty) so metaheuristic solvers are forced to find
    # zero-overlap, fully-on-canvas solutions.
    hard_violations = overlap_norm + oob_norm
    w = cost_weights or {}
    aesthetic = (
        w.get("packing", 3.0) * packing
        + w.get("balance", 2.0) * balance
        + w.get("uniformity", 2.0) * uniformity
        + w.get("reading_flow", policy.reading_flow_weight) * reading_flow
        + w.get("landscape", 1.0) * landscape
        + w.get("size_gradient", 1.0) * size_gradient
    )
    if hard_violations > 0:
        return 1000.0 * hard_violations + aesthetic
    return aesthetic


# ---------------------------------------------------------------------------
# Metaheuristic solver helpers
# ---------------------------------------------------------------------------

def _random_solution(
    n: int, canvas_w: float, canvas_h: float, rng: random.Random,
) -> list[tuple[float, float, float]]:
    """Generate a random placement solution."""
    margin_x = canvas_w * 0.15
    margin_y = canvas_h * 0.15
    sol: list[tuple[float, float, float]] = []
    for index in range(n):
        x = rng.uniform(margin_x, canvas_w - margin_x)
        y = rng.uniform(margin_y, canvas_h - margin_y)
        font_size = (
            _ACTIVE_WORD_SIZES[index]
            if index < len(_ACTIVE_WORD_SIZES)
            else _ACTIVE_MAX_FONT_SIZE
        )
        rot = _rotation_for_font_size(rng, font_size)
        sol.append((x, y, float(rot)))
    return sol


def _clamp_solution(
    sol: list[tuple[float, float, float]], canvas_w: float, canvas_h: float,
) -> list[tuple[float, float, float]]:
    """Clamp positions to canvas bounds and rotations to valid set."""
    mx, my = canvas_w * 0.15, canvas_h * 0.15
    result: list[tuple[float, float, float]] = []
    for x, y, rot in sol:
        x = max(mx, min(canvas_w - mx, x))
        y = max(my, min(canvas_h - my, y))
        rot = _ACTIVE_LAYOUT_READABILITY.snap_rotation(rot)
        result.append((x, y, rot))
    return result


def _eval_fitness(
    sol: list[tuple[float, float, float]],
    sizes: list[float],
    canvas_w: float,
    canvas_h: float,
    texts: list[str] | None = None,
    layout_readability: LayoutReadabilityConfig = None,
    cost_weights: dict[str, float] | None = None,
) -> float:
    """Return fitness (higher is better) = negative cost."""
    return -_aesthetic_cost(sol, sizes, canvas_w, canvas_h, texts, layout_readability, cost_weights)


# ---------------------------------------------------------------------------
# Generic mealpy solver wrapper
# ---------------------------------------------------------------------------

def _mealpy_solve(
    optimizer_class: type,
    n_words: int,
    sizes: list[float],
    canvas_w: float,
    canvas_h: float,
    max_iter: int,
    rng: random.Random,
    texts: list[str] | None = None,
    pop_size: int | None = None,
    cost_weights: dict[str, float] | None = None,
) -> list[tuple[float, float, float]]:
    """Run any mealpy optimizer on the word-cloud placement problem.

    Builds a continuous optimization problem with ``n_words * 3`` dimensions
    (x, y, rotation per word), delegates to the mealpy optimizer, and converts
    the result back to the standard ``list[tuple[float, float, float]]`` format.
    """
    # Adaptive pop_size: scale with dimensionality for meaningful coverage
    default_pop = max(20, min(3 * n_words, 100))
    pop_size = max(_clamped_population_size(pop_size, default=default_pop), 2)
    dim = n_words * 3

    # Bounds: x in [15%..85%] canvas, y in [15%..85%] canvas, rot from policy
    margin_x = canvas_w * 0.15
    margin_y = canvas_h * 0.15
    rot_choices = _ACTIVE_LAYOUT_READABILITY.standard_rotations
    rot_min = float(min(rot_choices)) - 1.0 if rot_choices else -90.0
    rot_max = float(max(rot_choices)) + 1.0 if rot_choices else 90.0

    lb: list[float] = []
    ub: list[float] = []
    for _ in range(n_words):
        lb.extend([margin_x, margin_y, rot_min])
        ub.extend([canvas_w - margin_x, canvas_h - margin_y, rot_max])

    bounds = FloatVar(lb=lb, ub=ub)

    # Objective: snap rotations to valid values BEFORE evaluating cost
    # so the solver optimizes the actual rendered output, not a continuous proxy.
    def obj_func(solution: np.ndarray) -> float:
        sol_tuples: list[tuple[float, float, float]] = []
        for i in range(0, dim, 3):
            x, y, rot = float(solution[i]), float(solution[i + 1]), float(solution[i + 2])
            rot = _ACTIVE_LAYOUT_READABILITY.snap_rotation(rot)
            sol_tuples.append((x, y, rot))
        sol_tuples = _clamp_solution(sol_tuples, canvas_w, canvas_h)
        return _aesthetic_cost(sol_tuples, sizes, canvas_w, canvas_h, texts, cost_weights=cost_weights)

    problem = {
        "bounds": bounds,
        "minmax": "min",
        "obj_func": obj_func,
        "log_to": "none",
    }

    try:
        model = optimizer_class(epoch=max_iter, pop_size=pop_size)
        seed = rng.randint(0, 2**31 - 1)
        result = model.solve(problem, seed=seed)

        # Convert flat solution back to tuples
        best_vec = result.solution
        sol_tuples: list[tuple[float, float, float]] = []
        for i in range(0, dim, 3):
            sol_tuples.append((float(best_vec[i]), float(best_vec[i + 1]), float(best_vec[i + 2])))
        return _clamp_solution(sol_tuples, canvas_w, canvas_h)
    except (RuntimeError, ValueError, TypeError) as exc:
        logger.debug(
            "Solver {} failed, falling back to random: {}",
            optimizer_class.__name__, exc,
        )
        return _random_solution(n_words, canvas_w, canvas_h, rng)


# ---------------------------------------------------------------------------
# Solver factory and registry
# ---------------------------------------------------------------------------

def _make_mealpy_solver(optimizer_class: type) -> Callable[..., list[tuple[float, float, float]]]:
    """Create a solver function wrapping a specific mealpy optimizer class."""

    def solver(
        n_words: int,
        sizes: list[float],
        canvas_w: float,
        canvas_h: float,
        max_iter: int,
        rng: random.Random,
        texts: list[str] | None = None,
        pop_size: int | None = None,
        cost_weights: dict[str, float] | None = None,
    ) -> list[tuple[float, float, float]]:
        return _mealpy_solve(
            optimizer_class, n_words, sizes, canvas_w, canvas_h,
            max_iter, rng, texts, pop_size, cost_weights,
        )

    solver.__name__ = f"_solve_{optimizer_class.__name__}"
    solver.__doc__ = f"mealpy wrapper: {optimizer_class.__name__}"
    return solver


# Optimizers excluded via empirical benchmarking on word-cloud placement.
# These either crash (triggering random fallback), produce degenerate layouts,
# or consistently rank in the bottom 15% across problem sizes.
_EXCLUDED_OPTIMIZERS: frozenset[str] = frozenset({
    # Fallback-only (0ms, cost=random): solver errors caught internally
    "DevCHIO", "DevSARO", "ImprovedBSO", "ImprovedTLO", "OCRO",
    "OriginalBSA", "OriginalBSO", "OriginalCEM", "OriginalCHIO",
    "OriginalEHO", "OriginalIWO", "OriginalMA", "OriginalSARO", "SwarmHC",
    # Degenerate layouts (cost >= 16): worst possible quality
    "BaseGA", "DevGSKA", "MultiGA", "OppoTWO", "OriginalBFO",
    "OriginalGSKA", "SingleGA",
    # Poor performers (cost 7-12): well below median
    "DevFOA", "OriginalFOA", "OriginalHBO", "OriginalSBO", "WhaleFOA",
    # Bottom of viable range with better alternatives in same family
    "OriginalBMO", "OriginalCA", "OriginalCDO", "OriginalFOX",
    "OriginalPFA", "OriginalSSDO", "SwarmSA",
})


# Build the registry dynamically from all mealpy optimizers.
# Suppress stdout during get_all_optimizers() as it prints a line per optimizer.
def _build_solver_registry() -> dict[str, Callable[..., list[tuple[float, float, float]]]]:
    from mealpy import get_all_optimizers

    all_optimizers = get_all_optimizers(verbose=False)

    registry: dict[str, Callable[..., list[tuple[float, float, float]]]] = {}
    for name, cls in all_optimizers.items():
        if name not in _EXCLUDED_OPTIMIZERS:
            registry[name] = _make_mealpy_solver(cls)
    return registry


_META_SOLVERS: dict[str, Callable[..., list[tuple[float, float, float]]]] = _build_solver_registry()
