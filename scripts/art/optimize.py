"""
Art layout and color optimization using metaheuristic solvers.

Provides optimizers for:
- Tree/plant placement (ink garden) — visual balance, golden ratio, spacing
- Hill/mountain placement (topography) — natural terrain flow, overlap avoidance
- Color palette harmony — complementary, analogous, triadic harmony scoring

Uses Particle Swarm Optimization (PSO) and Simulated Annealing (SA) —
fast convergence for the small solution spaces in art layout.
"""

from __future__ import annotations

import math
import random
from typing import Any

from .shared import oklch


# ---------------------------------------------------------------------------
# Cost functions
# ---------------------------------------------------------------------------


def _golden_ratio_score(
    positions: list[tuple[float, float]], w: float, h: float
) -> float:
    """Score how well positions align with golden ratio focal points.

    Returns 0.0 (perfect) to 1.0 (worst).
    The four golden ratio focal points on a canvas are at:
    (w*0.382, h*0.382), (w*0.618, h*0.382),
    (w*0.382, h*0.618), (w*0.618, h*0.618)
    """
    if not positions:
        return 0.5
    phi = 0.381966  # 1/golden_ratio^2
    focals = [
        (w * phi, h * phi),
        (w * (1 - phi), h * phi),
        (w * phi, h * (1 - phi)),
        (w * (1 - phi), h * (1 - phi)),
    ]
    total = 0.0
    for px, py in positions:
        min_d = min(math.sqrt((px - fx) ** 2 + (py - fy) ** 2) for fx, fy in focals)
        # Normalize by diagonal
        diag = math.sqrt(w * w + h * h)
        total += min_d / diag
    return total / len(positions)


def _visual_balance_score(
    positions: list[tuple[float, float]],
    weights: list[float],
    w: float,
    h: float,
) -> float:
    """Score visual balance — how close the weighted centroid is to center.

    Returns 0.0 (perfect center) to 1.0 (worst).
    """
    if not positions or not weights:
        return 0.5
    total_w = sum(weights) or 1.0
    cx = sum(px * wt for (px, _), wt in zip(positions, weights)) / total_w
    cy = sum(py * wt for (_, py), wt in zip(positions, weights)) / total_w
    dx = (cx - w / 2) / (w / 2)
    dy = (cy - h / 2) / (h / 2)
    return min(1.0, math.sqrt(dx * dx + dy * dy))


def _spacing_score(
    positions: list[tuple[float, float]],
    min_distance: float,
) -> float:
    """Penalize overlapping elements. Returns 0.0 (no overlaps) to N (overlapping).

    Counts pairs closer than min_distance.
    """
    n = len(positions)
    if n < 2:
        return 0.0
    penalty = 0.0
    for i in range(n):
        for j in range(i + 1, n):
            dx = positions[i][0] - positions[j][0]
            dy = positions[i][1] - positions[j][1]
            dist = math.sqrt(dx * dx + dy * dy)
            if dist < min_distance:
                penalty += (min_distance - dist) / min_distance
    return penalty


def _margin_score(
    positions: list[tuple[float, float]],
    w: float,
    h: float,
    margin_frac: float = 0.08,
) -> float:
    """Penalize elements too close to edges. Returns 0.0 (good) to N (bad)."""
    mx = w * margin_frac
    my = h * margin_frac
    penalty = 0.0
    for px, py in positions:
        if px < mx:
            penalty += (mx - px) / mx
        if px > w - mx:
            penalty += (px - (w - mx)) / mx
        if py < my:
            penalty += (my - py) / my
        if py > h - my:
            penalty += (py - (h - my)) / my
    return penalty


def _whitespace_uniformity(
    positions: list[tuple[float, float]],
    w: float,
    h: float,
) -> float:
    """Score how uniformly elements fill the space using grid variance.

    Returns 0.0 (perfectly uniform) to 1.0 (clustered).
    """
    if len(positions) < 3:
        return 0.0
    grid_n = 4
    cell_w = w / grid_n
    cell_h = h / grid_n
    counts = [[0] * grid_n for _ in range(grid_n)]
    for px, py in positions:
        gi = min(grid_n - 1, max(0, int(px / cell_w)))
        gj = min(grid_n - 1, max(0, int(py / cell_h)))
        counts[gj][gi] += 1
    flat = [counts[j][i] for j in range(grid_n) for i in range(grid_n)]
    mean = sum(flat) / len(flat)
    if mean == 0:
        return 1.0
    variance = sum((c - mean) ** 2 for c in flat) / len(flat)
    cv = math.sqrt(variance) / mean  # coefficient of variation
    return min(1.0, cv / 2.0)


# ---------------------------------------------------------------------------
# Art layout cost (combines all sub-scores)
# ---------------------------------------------------------------------------


def art_layout_cost(
    positions: list[tuple[float, float]],
    weights: list[float],
    canvas_w: float,
    canvas_h: float,
    min_spacing: float = 80.0,
) -> float:
    """Combined aesthetic cost for art element placement.

    Lower is better. Weights:
    - Overlap/spacing: 10.0 (critical)
    - Margin safety: 5.0
    - Visual balance: 3.0
    - Golden ratio: 2.0
    - Whitespace uniformity: 2.0
    """
    return (
        10.0 * _spacing_score(positions, min_spacing)
        + 5.0 * _margin_score(positions, canvas_w, canvas_h)
        + 3.0 * _visual_balance_score(positions, weights, canvas_w, canvas_h)
        + 2.0 * _golden_ratio_score(positions, canvas_w, canvas_h)
        + 2.0 * _whitespace_uniformity(positions, canvas_w, canvas_h)
    )


# ---------------------------------------------------------------------------
# Color harmony scoring
# ---------------------------------------------------------------------------


def _hue_distance(h1: float, h2: float) -> float:
    """Circular distance between two hues (0-360)."""
    d = abs(h1 - h2) % 360
    return min(d, 360 - d)


def color_harmony_score(hues: list[float]) -> float:
    """Score color harmony of a set of hues (0-360).

    Returns 0.0 (perfect harmony) to 1.0 (chaotic).
    Tests against known harmonious relationships:
    - Complementary (180° apart): best
    - Triadic (120° apart): great
    - Analogous (30° apart): good
    - Split-complementary (150°/210°): good
    """
    if len(hues) < 2:
        return 0.0

    harmonies = [30, 60, 120, 150, 180]
    best_score = 1.0

    for i in range(len(hues)):
        for j in range(i + 1, len(hues)):
            dist = _hue_distance(hues[i], hues[j])
            # How close is this pair to any harmonic interval?
            min_deviation = min(abs(dist - h) for h in harmonies)
            pair_score = min_deviation / 90.0  # normalize
            best_score = min(best_score, pair_score)

    return best_score


def optimize_palette_hues(
    base_hues: list[float],
    *,
    max_shift: float = 15.0,
    iterations: int = 200,
    seed: int = 42,
) -> list[float]:
    """Optimize hue values for maximum color harmony.

    Shifts each hue by up to ±max_shift degrees to find
    the most harmonious combination using simulated annealing.
    """
    n = len(base_hues)
    if n < 2:
        return list(base_hues)

    rng = random.Random(seed)
    current = list(base_hues)
    current_score = color_harmony_score(current)
    best = list(current)
    best_score = current_score

    for it in range(iterations):
        temp = 1.0 - it / max(iterations - 1, 1)
        # Perturb one random hue
        idx = rng.randint(0, n - 1)
        shift = rng.gauss(0, max_shift * temp)
        candidate = list(current)
        candidate[idx] = (base_hues[idx] + shift) % 360

        new_score = color_harmony_score(candidate)
        delta = new_score - current_score

        if delta < 0 or rng.random() < math.exp(-delta / max(temp * 0.3, 0.001)):
            current = candidate
            current_score = new_score
            if current_score < best_score:
                best = list(current)
                best_score = current_score

    return best


# ---------------------------------------------------------------------------
# Layout optimizers (PSO + SA)
# ---------------------------------------------------------------------------


def optimize_layout_pso(
    initial_positions: list[tuple[float, float]],
    weights: list[float],
    canvas_w: float,
    canvas_h: float,
    *,
    min_spacing: float = 80.0,
    iterations: int = 150,
    swarm_size: int = 15,
    seed: int = 42,
) -> list[tuple[float, float]]:
    """Optimize element positions using Particle Swarm Optimization.

    Returns optimized (x, y) positions for each element.
    Preserves relative ordering while improving aesthetic layout.
    """
    n = len(initial_positions)
    if n < 2:
        return list(initial_positions)

    rng = random.Random(seed)
    dim = n * 2
    margin_x = canvas_w * 0.08
    margin_y = canvas_h * 0.08

    def pos_to_vec(pos: list[tuple[float, float]]) -> list[float]:
        v: list[float] = []
        for x, y in pos:
            v.extend([x, y])
        return v

    def vec_to_pos(v: list[float]) -> list[tuple[float, float]]:
        result: list[tuple[float, float]] = []
        for i in range(0, len(v), 2):
            x = max(margin_x, min(canvas_w - margin_x, v[i]))
            y = max(margin_y, min(canvas_h - margin_y, v[i + 1]))
            result.append((x, y))
        return result

    def fitness(v: list[float]) -> float:
        return -art_layout_cost(vec_to_pos(v), weights, canvas_w, canvas_h, min_spacing)

    # Initialize swarm around initial positions
    init_vec = pos_to_vec(initial_positions)
    particles = []
    velocities = []
    for _ in range(swarm_size):
        p = [init_vec[d] + rng.gauss(0, min_spacing * 0.3) for d in range(dim)]
        v = [rng.gauss(0, 2.0) for _ in range(dim)]
        particles.append(p)
        velocities.append(v)

    p_best = [list(p) for p in particles]
    p_best_fit = [fitness(p) for p in particles]
    g_best_idx = max(range(swarm_size), key=lambda k: p_best_fit[k])
    g_best = list(p_best[g_best_idx])
    g_best_fit = p_best_fit[g_best_idx]

    w_start, w_end = 0.9, 0.4
    c1, c2 = 2.0, 2.0

    for it in range(iterations):
        w = w_start - (w_start - w_end) * (it / max(iterations - 1, 1))
        for i in range(swarm_size):
            for d in range(dim):
                r1, r2 = rng.random(), rng.random()
                velocities[i][d] = (
                    w * velocities[i][d]
                    + c1 * r1 * (p_best[i][d] - particles[i][d])
                    + c2 * r2 * (g_best[d] - particles[i][d])
                )
                particles[i][d] += velocities[i][d]

            fit = fitness(particles[i])
            if fit > p_best_fit[i]:
                p_best[i] = list(particles[i])
                p_best_fit[i] = fit
                if fit > g_best_fit:
                    g_best = list(particles[i])
                    g_best_fit = fit

    return vec_to_pos(g_best)


def optimize_layout_sa(
    initial_positions: list[tuple[float, float]],
    weights: list[float],
    canvas_w: float,
    canvas_h: float,
    *,
    min_spacing: float = 80.0,
    iterations: int = 300,
    seed: int = 42,
) -> list[tuple[float, float]]:
    """Optimize element positions using Simulated Annealing.

    Faster than PSO for small element counts (<10).
    """
    n = len(initial_positions)
    if n < 2:
        return list(initial_positions)

    rng = random.Random(seed)
    margin_x = canvas_w * 0.08
    margin_y = canvas_h * 0.08

    def clamp(pos: list[tuple[float, float]]) -> list[tuple[float, float]]:
        return [
            (
                max(margin_x, min(canvas_w - margin_x, x)),
                max(margin_y, min(canvas_h - margin_y, y)),
            )
            for x, y in pos
        ]

    current = clamp(list(initial_positions))
    current_cost = art_layout_cost(current, weights, canvas_w, canvas_h, min_spacing)
    best = list(current)
    best_cost = current_cost

    step_size_init = min_spacing * 0.5

    for it in range(iterations):
        temp = 1.0 - it / max(iterations - 1, 1)
        step = step_size_init * temp

        # Perturb one random element
        idx = rng.randint(0, n - 1)
        candidate = list(current)
        x, y = candidate[idx]
        candidate[idx] = (x + rng.gauss(0, step), y + rng.gauss(0, step))
        candidate = clamp(candidate)

        new_cost = art_layout_cost(candidate, weights, canvas_w, canvas_h, min_spacing)
        delta = new_cost - current_cost

        if delta < 0 or rng.random() < math.exp(-delta / max(temp * 2.0, 0.001)):
            current = candidate
            current_cost = new_cost
            if current_cost < best_cost:
                best = list(current)
                best_cost = current_cost

    return best
