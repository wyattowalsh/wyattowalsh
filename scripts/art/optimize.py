"""
Art layout and color optimization using metaheuristic solvers.

Provides optimizers for:
- Tree/plant placement (ink garden) — visual balance, golden ratio, spacing
- Hill/mountain placement (topography) — natural terrain flow, overlap avoidance
- Color palette harmony — complementary, analogous, triadic harmony scoring
- Star-field layouts — uniform sky coverage
- Constellation placement — cluster cohesion with inter-cluster separation

Solvers: SA, PSO, Grey Wolf, Whale, Firefly, Flower Pollination, DE.
Use ``optimize_placement()`` as the unified dispatcher.
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


# ---------------------------------------------------------------------------
# Ported metaheuristic solvers (Grey Wolf, Whale, Firefly, Flower, DE)
# ---------------------------------------------------------------------------

_MARGIN_FRAC = 0.08


def _clamp_art(
    positions: list[tuple[float, float]], canvas_w: float, canvas_h: float,
) -> list[tuple[float, float]]:
    """Clamp positions to canvas with margin."""
    mx = canvas_w * _MARGIN_FRAC
    my = canvas_h * _MARGIN_FRAC
    return [
        (max(mx, min(canvas_w - mx, x)), max(my, min(canvas_h - my, y)))
        for x, y in positions
    ]


def _pos_to_vec(positions: list[tuple[float, float]]) -> list[float]:
    """Flatten (x, y) list to a flat vector."""
    v: list[float] = []
    for x, y in positions:
        v.extend([x, y])
    return v


def _vec_to_pos(
    v: list[float], canvas_w: float, canvas_h: float,
) -> list[tuple[float, float]]:
    """Unflatten vector to (x, y) list, clamped to canvas margins."""
    positions: list[tuple[float, float]] = []
    for i in range(0, len(v), 2):
        positions.append((v[i], v[i + 1]))
    return _clamp_art(positions, canvas_w, canvas_h)


def _random_art_positions(
    n: int, canvas_w: float, canvas_h: float, rng: random.Random,
) -> list[tuple[float, float]]:
    """Generate random positions within canvas margins."""
    mx = canvas_w * _MARGIN_FRAC
    my = canvas_h * _MARGIN_FRAC
    return [(rng.uniform(mx, canvas_w - mx), rng.uniform(my, canvas_h - my)) for _ in range(n)]


def _art_fitness(
    v: list[float],
    weights: list[float],
    canvas_w: float,
    canvas_h: float,
    min_spacing: float,
) -> float:
    """Fitness wrapper: negate cost so higher is better."""
    return -art_layout_cost(
        _vec_to_pos(v, canvas_w, canvas_h), weights, canvas_w, canvas_h, min_spacing,
    )


def _art_solve_grey_wolf(
    initial_positions: list[tuple[float, float]],
    weights: list[float],
    canvas_w: float,
    canvas_h: float,
    *,
    min_spacing: float = 80.0,
    max_iter: int = 200,
    seed: int = 42,
) -> list[tuple[float, float]]:
    """Grey Wolf Optimizer for art layout.

    Alpha/beta/delta hierarchy with linearly decreasing ``a`` (2 -> 0).
    Fast convergence for small-to-medium element counts.
    """
    n = len(initial_positions)
    if n < 2:
        return list(initial_positions)

    rng = random.Random(seed)
    pop_size = 20
    dim = n * 2

    init_vec = _pos_to_vec(initial_positions)
    wolves = [
        [init_vec[d] + rng.gauss(0, min_spacing * 0.3) for d in range(dim)]
        for _ in range(pop_size)
    ]
    fits = [_art_fitness(w, weights, canvas_w, canvas_h, min_spacing) for w in wolves]

    sorted_idx = sorted(range(pop_size), key=lambda k: fits[k], reverse=True)
    alpha_w = list(wolves[sorted_idx[0]])
    beta_w = list(wolves[sorted_idx[1]])
    delta_w = list(wolves[sorted_idx[2]])

    for it in range(max_iter):
        a = 2.0 - 2.0 * (it / max(max_iter - 1, 1))
        for i in range(pop_size):
            new_pos: list[float] = []
            for d in range(dim):
                r1, r2 = rng.random(), rng.random()
                A1 = 2 * a * r1 - a
                C1 = 2 * r2
                D_alpha = abs(C1 * alpha_w[d] - wolves[i][d])
                X1 = alpha_w[d] - A1 * D_alpha

                r1, r2 = rng.random(), rng.random()
                A2 = 2 * a * r1 - a
                C2 = 2 * r2
                D_beta = abs(C2 * beta_w[d] - wolves[i][d])
                X2 = beta_w[d] - A2 * D_beta

                r1, r2 = rng.random(), rng.random()
                A3 = 2 * a * r1 - a
                C3 = 2 * r2
                D_delta = abs(C3 * delta_w[d] - wolves[i][d])
                X3 = delta_w[d] - A3 * D_delta

                new_pos.append((X1 + X2 + X3) / 3)

            # Clamp via round-trip
            clamped = _vec_to_pos(new_pos, canvas_w, canvas_h)
            wolves[i] = _pos_to_vec(clamped)
            fits[i] = _art_fitness(wolves[i], weights, canvas_w, canvas_h, min_spacing)

        sorted_idx = sorted(range(pop_size), key=lambda k: fits[k], reverse=True)
        alpha_w = list(wolves[sorted_idx[0]])
        beta_w = list(wolves[sorted_idx[1]])
        delta_w = list(wolves[sorted_idx[2]])

    return _vec_to_pos(alpha_w, canvas_w, canvas_h)


def _art_solve_whale(
    initial_positions: list[tuple[float, float]],
    weights: list[float],
    canvas_w: float,
    canvas_h: float,
    *,
    min_spacing: float = 80.0,
    max_iter: int = 200,
    seed: int = 42,
) -> list[tuple[float, float]]:
    """Whale Optimization Algorithm for art layout.

    Combines encircling prey, random search, and spiral update.
    ``a`` decreases 2 -> 0; spiral coefficient ``b = 1``.
    Good for smooth landscape optimization.
    """
    n = len(initial_positions)
    if n < 2:
        return list(initial_positions)

    rng = random.Random(seed)
    pop_size = 20
    b_spiral = 1.0
    dim = n * 2

    init_vec = _pos_to_vec(initial_positions)
    whales = [
        [init_vec[d] + rng.gauss(0, min_spacing * 0.3) for d in range(dim)]
        for _ in range(pop_size)
    ]
    fits = [_art_fitness(w, weights, canvas_w, canvas_h, min_spacing) for w in whales]
    best_idx = max(range(pop_size), key=lambda k: fits[k])
    best_pos = list(whales[best_idx])
    best_fit = fits[best_idx]

    for it in range(max_iter):
        a = 2.0 - 2.0 * (it / max(max_iter - 1, 1))
        for i in range(pop_size):
            r_p = rng.random()
            A = 2 * a * rng.random() - a
            C = 2 * rng.random()
            l_param = rng.uniform(-1, 1)

            new_pos: list[float] = []
            if r_p < 0.5:
                if abs(A) < 1:
                    # Encircling prey
                    for d in range(dim):
                        D = abs(C * best_pos[d] - whales[i][d])
                        new_pos.append(best_pos[d] - A * D)
                else:
                    # Random search
                    rand_idx = rng.randint(0, pop_size - 1)
                    for d in range(dim):
                        D = abs(C * whales[rand_idx][d] - whales[i][d])
                        new_pos.append(whales[rand_idx][d] - A * D)
            else:
                # Spiral update
                for d in range(dim):
                    D_prime = abs(best_pos[d] - whales[i][d])
                    new_pos.append(
                        D_prime * math.exp(b_spiral * l_param)
                        * math.cos(2 * math.pi * l_param)
                        + best_pos[d]
                    )

            clamped = _vec_to_pos(new_pos, canvas_w, canvas_h)
            whales[i] = _pos_to_vec(clamped)
            fits[i] = _art_fitness(whales[i], weights, canvas_w, canvas_h, min_spacing)
            if fits[i] > best_fit:
                best_pos = list(whales[i])
                best_fit = fits[i]

    return _vec_to_pos(best_pos, canvas_w, canvas_h)


def _art_solve_firefly(
    initial_positions: list[tuple[float, float]],
    weights: list[float],
    canvas_w: float,
    canvas_h: float,
    *,
    min_spacing: float = 80.0,
    max_iter: int = 200,
    seed: int = 42,
) -> list[tuple[float, float]]:
    """Firefly Algorithm for art layout.

    Distance-based attraction: ``beta0 = 1.0``, ``gamma = 0.01``,
    ``alpha = 0.2``. Naturally suited for spatial placement since
    attraction decays with distance.
    """
    n = len(initial_positions)
    if n < 2:
        return list(initial_positions)

    rng = random.Random(seed)
    pop_size = 20
    beta0 = 1.0
    gamma = 0.01
    alpha_fa = 0.2
    dim = n * 2

    init_vec = _pos_to_vec(initial_positions)
    fireflies = [
        [init_vec[d] + rng.gauss(0, min_spacing * 0.3) for d in range(dim)]
        for _ in range(pop_size)
    ]
    brightness = [
        _art_fitness(f, weights, canvas_w, canvas_h, min_spacing) for f in fireflies
    ]

    for _ in range(max_iter):
        for i in range(pop_size):
            for j in range(pop_size):
                if brightness[j] > brightness[i]:
                    r_sq = sum(
                        (fireflies[i][d] - fireflies[j][d]) ** 2 for d in range(dim)
                    )
                    beta = beta0 * math.exp(-gamma * r_sq)
                    for d in range(dim):
                        fireflies[i][d] += (
                            beta * (fireflies[j][d] - fireflies[i][d])
                            + alpha_fa * rng.gauss(0, 1)
                        )
                    clamped = _vec_to_pos(fireflies[i], canvas_w, canvas_h)
                    fireflies[i] = _pos_to_vec(clamped)
                    brightness[i] = _art_fitness(
                        fireflies[i], weights, canvas_w, canvas_h, min_spacing,
                    )

    best_idx = max(range(pop_size), key=lambda k: brightness[k])
    return _vec_to_pos(fireflies[best_idx], canvas_w, canvas_h)


def _art_solve_flower_pollination(
    initial_positions: list[tuple[float, float]],
    weights: list[float],
    canvas_w: float,
    canvas_h: float,
    *,
    min_spacing: float = 80.0,
    max_iter: int = 200,
    seed: int = 42,
) -> list[tuple[float, float]]:
    """Flower Pollination Algorithm for art layout.

    Global pollination via Levy flights (``p = 0.8``), local pollination
    via Gaussian perturbation. Levy flights provide excellent exploration
    of the search space.
    """
    n = len(initial_positions)
    if n < 2:
        return list(initial_positions)

    rng = random.Random(seed)
    pop_size = 20
    p_switch = 0.8
    beta_levy = 1.5
    dim = n * 2

    sigma_u = (
        math.gamma(1 + beta_levy) * math.sin(math.pi * beta_levy / 2)
        / (math.gamma((1 + beta_levy) / 2) * beta_levy * 2 ** ((beta_levy - 1) / 2))
    ) ** (1 / beta_levy)

    def levy_step() -> float:
        u = rng.gauss(0, sigma_u)
        v = rng.gauss(0, 1)
        return u / (abs(v) ** (1 / beta_levy))

    init_vec = _pos_to_vec(initial_positions)
    flowers = [
        [init_vec[d] + rng.gauss(0, min_spacing * 0.3) for d in range(dim)]
        for _ in range(pop_size)
    ]
    fits = [_art_fitness(f, weights, canvas_w, canvas_h, min_spacing) for f in flowers]
    best_idx = max(range(pop_size), key=lambda k: fits[k])
    g_best = list(flowers[best_idx])

    for _ in range(max_iter):
        for i in range(pop_size):
            if rng.random() < p_switch:
                # Global pollination via Levy flight
                new_pos = [
                    flowers[i][d] + levy_step() * (g_best[d] - flowers[i][d])
                    for d in range(dim)
                ]
            else:
                # Local pollination
                j, k = rng.sample([x for x in range(pop_size) if x != i], 2)
                eps = rng.random()
                new_pos = [
                    flowers[i][d] + eps * (flowers[j][d] - flowers[k][d])
                    for d in range(dim)
                ]

            clamped = _vec_to_pos(new_pos, canvas_w, canvas_h)
            new_vec = _pos_to_vec(clamped)
            new_fit = _art_fitness(new_vec, weights, canvas_w, canvas_h, min_spacing)
            if new_fit > fits[i]:
                flowers[i] = new_vec
                fits[i] = new_fit
                if new_fit > fits[best_idx]:
                    best_idx = i
                    g_best = list(flowers[i])

    return _vec_to_pos(g_best, canvas_w, canvas_h)


def _art_solve_differential_evolution(
    initial_positions: list[tuple[float, float]],
    weights: list[float],
    canvas_w: float,
    canvas_h: float,
    *,
    min_spacing: float = 80.0,
    max_iter: int = 200,
    seed: int = 42,
) -> list[tuple[float, float]]:
    """Differential Evolution for art layout.

    Classic rand/1/bin strategy: ``F = 0.8``, ``CR = 0.9``.
    Robust general-purpose optimizer for any element count.
    """
    n = len(initial_positions)
    if n < 2:
        return list(initial_positions)

    rng = random.Random(seed)
    pop_size = 20
    F = 0.8
    CR = 0.9
    dim = n * 2

    init_vec = _pos_to_vec(initial_positions)
    pop = [
        [init_vec[d] + rng.gauss(0, min_spacing * 0.3) for d in range(dim)]
        for _ in range(pop_size)
    ]
    pop_fit = [_art_fitness(p, weights, canvas_w, canvas_h, min_spacing) for p in pop]

    for _ in range(max_iter):
        for i in range(pop_size):
            candidates = [j for j in range(pop_size) if j != i]
            a, b, c = rng.sample(candidates, 3)
            mutant = [pop[a][d] + F * (pop[b][d] - pop[c][d]) for d in range(dim)]
            j_rand = rng.randint(0, dim - 1)
            trial = [
                mutant[d] if rng.random() < CR or d == j_rand else pop[i][d]
                for d in range(dim)
            ]
            clamped = _vec_to_pos(trial, canvas_w, canvas_h)
            trial_vec = _pos_to_vec(clamped)
            trial_fit = _art_fitness(trial_vec, weights, canvas_w, canvas_h, min_spacing)
            if trial_fit >= pop_fit[i]:
                pop[i] = trial_vec
                pop_fit[i] = trial_fit

    best_idx = max(range(pop_size), key=lambda k: pop_fit[k])
    return _vec_to_pos(pop[best_idx], canvas_w, canvas_h)


# ---------------------------------------------------------------------------
# Specialized cost functions
# ---------------------------------------------------------------------------


def star_layout_cost(
    positions: list[tuple[float, float]],
    weights: list[float],
    canvas_w: float,
    canvas_h: float,
    *,
    min_spacing: float = 15.0,
) -> float:
    """Cost for star-field layouts: emphasize uniform coverage over golden ratio.

    Compared to ``art_layout_cost``, this gives much higher weight to
    whitespace uniformity (star fields should fill the sky evenly) and
    lower weight to golden-ratio alignment (stars look unnatural when
    clustered at focal points).

    Lower is better.
    """
    return (
        10.0 * _spacing_score(positions, min_spacing)
        + 3.0 * _margin_score(positions, canvas_w, canvas_h)
        + 1.0 * _visual_balance_score(positions, weights, canvas_w, canvas_h)
        + 0.5 * _golden_ratio_score(positions, canvas_w, canvas_h)
        + 8.0 * _whitespace_uniformity(positions, canvas_w, canvas_h)
    )


def constellation_layout_cost(
    positions: list[tuple[float, float]],
    cluster_ids: list[int],
    canvas_w: float,
    canvas_h: float,
    *,
    intra_spacing: float = 30.0,
    inter_spacing: float = 80.0,
) -> float:
    """Cost for constellation placement: reward intra-cluster cohesion, penalize inter-cluster overlap.

    Elements sharing the same ``cluster_id`` are attracted (penalized if
    farther than ``intra_spacing``). Elements in different clusters are
    repelled (penalized if closer than ``inter_spacing``).

    Lower is better.
    """
    n = len(positions)
    if n < 2:
        return 0.0

    intra_penalty = 0.0
    inter_penalty = 0.0
    for i in range(n):
        for j in range(i + 1, n):
            dx = positions[i][0] - positions[j][0]
            dy = positions[i][1] - positions[j][1]
            dist = math.sqrt(dx * dx + dy * dy)
            if cluster_ids[i] == cluster_ids[j]:
                # Same cluster: penalize if too far apart
                if dist > intra_spacing:
                    intra_penalty += (dist - intra_spacing) / intra_spacing
            else:
                # Different clusters: penalize if too close
                if dist < inter_spacing:
                    inter_penalty += (inter_spacing - dist) / inter_spacing

    margin_pen = _margin_score(positions, canvas_w, canvas_h)
    return 6.0 * intra_penalty + 8.0 * inter_penalty + 3.0 * margin_pen


# ---------------------------------------------------------------------------
# Unified dispatcher
# ---------------------------------------------------------------------------

_SOLVER_MAP = {
    "sa": optimize_layout_sa,
    "pso": optimize_layout_pso,
    "grey_wolf": _art_solve_grey_wolf,
    "whale": _art_solve_whale,
    "firefly": _art_solve_firefly,
    "flower": _art_solve_flower_pollination,
    "de": _art_solve_differential_evolution,
}


def optimize_placement(
    initial_positions: list[tuple[float, float]],
    weights: list[float],
    canvas_w: float,
    canvas_h: float,
    *,
    min_spacing: float = 80.0,
    solver: str = "auto",
    max_iter: int = 200,
    seed: int = 42,
) -> list[tuple[float, float]]:
    """Unified art layout optimizer.

    Parameters
    ----------
    initial_positions:
        Starting (x, y) for each element.
    weights:
        Visual weight per element (e.g. size, importance).
    canvas_w, canvas_h:
        Canvas dimensions.
    min_spacing:
        Minimum desired distance between elements.
    solver:
        Algorithm name: ``"auto"``, ``"sa"``, ``"pso"``, ``"grey_wolf"``,
        ``"firefly"``, ``"whale"``, ``"flower"``, or ``"de"``.
    max_iter:
        Maximum solver iterations.
    seed:
        RNG seed for reproducibility.

    Returns
    -------
    list[tuple[float, float]]
        Optimized positions, same length as *initial_positions*.

    Notes
    -----
    ``"auto"`` selection heuristic:

    - ``n < 8`` : SA (fast for tiny sets)
    - ``n < 50`` : Grey Wolf (fast convergence, small populations)
    - ``n >= 50``: PSO (scales well)
    """
    n = len(initial_positions)
    if n < 2:
        return list(initial_positions)

    if solver == "auto":
        if n < 8:
            solver = "sa"
        elif n < 50:
            solver = "grey_wolf"
        else:
            solver = "pso"

    fn = _SOLVER_MAP.get(solver)
    if fn is None:
        raise ValueError(
            f"Unknown solver {solver!r}. Choose from: {', '.join(sorted(_SOLVER_MAP))}"
        )

    # Map generic param names to solver-specific ones
    if solver == "sa":
        return fn(
            initial_positions, weights, canvas_w, canvas_h,
            min_spacing=min_spacing, iterations=max_iter, seed=seed,
        )
    if solver == "pso":
        return fn(
            initial_positions, weights, canvas_w, canvas_h,
            min_spacing=min_spacing, iterations=max_iter, seed=seed,
        )
    # All ported solvers share the same signature
    return fn(
        initial_positions, weights, canvas_w, canvas_h,
        min_spacing=min_spacing, max_iter=max_iter, seed=seed,
    )
