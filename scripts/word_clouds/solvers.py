"""Metaheuristic optimization solvers for word cloud placement."""

from __future__ import annotations

import math
import random

from .core import BBox
from .readability import DEFAULT_LAYOUT_READABILITY_POLICY, coerce_layout_readability_policy

# ---------------------------------------------------------------------------
# Metaheuristic aesthetic cost function
# ---------------------------------------------------------------------------

# Rotation choices biased toward horizontal for readability
_META_ROTATIONS = list(DEFAULT_LAYOUT_READABILITY_POLICY.standard_rotations)
_ACTIVE_LAYOUT_READABILITY = DEFAULT_LAYOUT_READABILITY_POLICY


def configure_layout_readability(layout_readability: object | None = None):
    """Set the active readability policy for solver helpers and workers."""

    global _ACTIVE_LAYOUT_READABILITY
    _ACTIVE_LAYOUT_READABILITY = coerce_layout_readability_policy(layout_readability)
    return _ACTIVE_LAYOUT_READABILITY


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
    layout_readability: object | None = None,
) -> float:
    """Evaluate the aesthetic quality of a word placement solution.

    Returns a scalar cost (lower is better) combining:
    1. Overlap penalty (weight 10.0)
    2. Packing density (weight 3.0)
    3. Visual balance (weight 2.0)
    4. Whitespace uniformity (weight 2.0)
    5. Reading flow (weight 1.5)
    6. Golden ratio harmony (weight 1.0)
    7. Size gradient (weight 1.0)

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
    aesthetic = (
        3.0 * packing
        + 2.0 * balance
        + 2.0 * uniformity
        + policy.reading_flow_weight * reading_flow
        + 1.0 * landscape
        + 1.0 * size_gradient
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
    for _ in range(n):
        x = rng.uniform(margin_x, canvas_w - margin_x)
        y = rng.uniform(margin_y, canvas_h - margin_y)
        rot = _ACTIVE_LAYOUT_READABILITY.choose_rotation(rng)
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
    layout_readability: object | None = None,
) -> float:
    """Return fitness (higher is better) = negative cost."""
    return -_aesthetic_cost(sol, sizes, canvas_w, canvas_h, texts, layout_readability)


# ---------------------------------------------------------------------------
# 25 Metaheuristic solvers
# ---------------------------------------------------------------------------

def _solve_harmony_search(
    n_words: int, sizes: list[float], canvas_w: float, canvas_h: float,
    max_iter: int, rng: random.Random, texts: list[str] | None = None,
) -> list[tuple[float, float, float]]:
    """Harmony Search: HMS=20, HMCR=0.9, PAR=0.3, shrinking bandwidth."""
    hms = 20
    hmcr = 0.9
    par = 0.3
    bw_init = min(canvas_w, canvas_h) * 0.3
    bw_final = min(canvas_w, canvas_h) * 0.01

    # Initialize harmony memory
    hm = [_random_solution(n_words, canvas_w, canvas_h, rng) for _ in range(hms)]
    hm_fit = [_eval_fitness(s, sizes, canvas_w, canvas_h, texts) for s in hm]

    for it in range(max_iter):
        bw = bw_init - (bw_init - bw_final) * (it / max(max_iter - 1, 1))
        new_harmony: list[tuple[float, float, float]] = []
        for i in range(n_words):
            if rng.random() < hmcr:
                # Memory consideration
                idx = rng.randint(0, hms - 1)
                x, y, rot = hm[idx][i]
                if rng.random() < par:
                    x += rng.gauss(0, bw)
                    y += rng.gauss(0, bw)
                    rot = _ACTIVE_LAYOUT_READABILITY.choose_rotation(rng)
            else:
                x = rng.uniform(canvas_w * 0.05, canvas_w * 0.95)
                y = rng.uniform(canvas_h * 0.05, canvas_h * 0.95)
                rot = _ACTIVE_LAYOUT_READABILITY.choose_rotation(rng)
            new_harmony.append((x, y, float(rot)))
        new_harmony = _clamp_solution(new_harmony, canvas_w, canvas_h)
        new_fit = _eval_fitness(new_harmony, sizes, canvas_w, canvas_h, texts)
        worst_idx = min(range(hms), key=lambda k: hm_fit[k])
        if new_fit > hm_fit[worst_idx]:
            hm[worst_idx] = new_harmony
            hm_fit[worst_idx] = new_fit

    best_idx = max(range(hms), key=lambda k: hm_fit[k])
    return hm[best_idx]


def _solve_simulated_annealing(
    n_words: int, sizes: list[float], canvas_w: float, canvas_h: float,
    max_iter: int, rng: random.Random, texts: list[str] | None = None,
) -> list[tuple[float, float, float]]:
    """Simulated Annealing: T_init=100, T_min=0.01, alpha=0.995."""
    t_init = 100.0
    t_min = 0.01
    alpha = 0.995

    current = _random_solution(n_words, canvas_w, canvas_h, rng)
    current_cost = _aesthetic_cost(current, sizes, canvas_w, canvas_h, texts)
    best = list(current)
    best_cost = current_cost
    temp = t_init

    for _ in range(max_iter):
        if temp < t_min:
            break
        # Perturb: move 1-3 random words
        neighbor = list(current)
        n_perturb = rng.randint(1, min(3, n_words))
        for _ in range(n_perturb):
            idx = rng.randint(0, n_words - 1)
            x, y, rot = neighbor[idx]
            x += rng.gauss(0, canvas_w * 0.05)
            y += rng.gauss(0, canvas_h * 0.05)
            rot = _ACTIVE_LAYOUT_READABILITY.choose_rotation(rng)
            neighbor[idx] = (x, y, float(rot))
        neighbor = _clamp_solution(neighbor, canvas_w, canvas_h)
        neighbor_cost = _aesthetic_cost(neighbor, sizes, canvas_w, canvas_h, texts)

        delta = neighbor_cost - current_cost
        if delta < 0 or rng.random() < math.exp(-delta / max(temp, 1e-10)):
            current = neighbor
            current_cost = neighbor_cost
            if current_cost < best_cost:
                best = list(current)
                best_cost = current_cost
        temp *= alpha

    return best


def _solve_particle_swarm(
    n_words: int, sizes: list[float], canvas_w: float, canvas_h: float,
    max_iter: int, rng: random.Random, texts: list[str] | None = None,
) -> list[tuple[float, float, float]]:
    """Particle Swarm Optimization: w=0.7->0.4, c1=c2=1.5."""
    pop_size = 20
    c1, c2 = 1.5, 1.5
    dim = n_words * 3  # x, y, rot per word

    def sol_to_vec(sol: list[tuple[float, float, float]]) -> list[float]:
        v: list[float] = []
        for x, y, r in sol:
            v.extend([x, y, r])
        return v

    def vec_to_sol(v: list[float]) -> list[tuple[float, float, float]]:
        s: list[tuple[float, float, float]] = []
        for i in range(0, len(v), 3):
            s.append((v[i], v[i + 1], v[i + 2]))
        return _clamp_solution(s, canvas_w, canvas_h)

    # Initialize
    particles = [sol_to_vec(_random_solution(n_words, canvas_w, canvas_h, rng)) for _ in range(pop_size)]
    velocities = [[rng.gauss(0, canvas_w * 0.02) for _ in range(dim)] for _ in range(pop_size)]
    p_best = [list(p) for p in particles]
    p_best_fit = [_eval_fitness(vec_to_sol(p), sizes, canvas_w, canvas_h, texts) for p in particles]
    g_best_idx = max(range(pop_size), key=lambda k: p_best_fit[k])
    g_best = list(p_best[g_best_idx])
    g_best_fit = p_best_fit[g_best_idx]

    v_max = canvas_w * 0.1

    for it in range(max_iter):
        w = 0.7 - 0.3 * (it / max(max_iter - 1, 1))
        for i in range(pop_size):
            for d in range(dim):
                r1, r2 = rng.random(), rng.random()
                velocities[i][d] = (
                    w * velocities[i][d]
                    + c1 * r1 * (p_best[i][d] - particles[i][d])
                    + c2 * r2 * (g_best[d] - particles[i][d])
                )
                velocities[i][d] = max(-v_max, min(v_max, velocities[i][d]))
                particles[i][d] += velocities[i][d]

            sol = vec_to_sol(particles[i])
            particles[i] = sol_to_vec(sol)
            fit = _eval_fitness(sol, sizes, canvas_w, canvas_h, texts)
            if fit > p_best_fit[i]:
                p_best[i] = list(particles[i])
                p_best_fit[i] = fit
                if fit > g_best_fit:
                    g_best = list(particles[i])
                    g_best_fit = fit

    return vec_to_sol(g_best)


def _solve_differential_evolution(
    n_words: int, sizes: list[float], canvas_w: float, canvas_h: float,
    max_iter: int, rng: random.Random, texts: list[str] | None = None,
) -> list[tuple[float, float, float]]:
    """Differential Evolution: F=0.8, CR=0.9, rand/1/bin."""
    pop_size = 20
    F = 0.8
    CR = 0.9
    dim = n_words * 3

    def sol_to_vec(sol: list[tuple[float, float, float]]) -> list[float]:
        v: list[float] = []
        for x, y, r in sol:
            v.extend([x, y, r])
        return v

    def vec_to_sol(v: list[float]) -> list[tuple[float, float, float]]:
        s: list[tuple[float, float, float]] = []
        for i in range(0, len(v), 3):
            s.append((v[i], v[i + 1], v[i + 2]))
        return _clamp_solution(s, canvas_w, canvas_h)

    pop = [sol_to_vec(_random_solution(n_words, canvas_w, canvas_h, rng)) for _ in range(pop_size)]
    pop_fit = [_eval_fitness(vec_to_sol(p), sizes, canvas_w, canvas_h, texts) for p in pop]

    for _ in range(max_iter):
        for i in range(pop_size):
            # Select 3 distinct random indices != i
            candidates = [j for j in range(pop_size) if j != i]
            a, b, c = rng.sample(candidates, 3)
            # Mutant
            mutant = [pop[a][d] + F * (pop[b][d] - pop[c][d]) for d in range(dim)]
            # Crossover
            j_rand = rng.randint(0, dim - 1)
            trial = [mutant[d] if rng.random() < CR or d == j_rand else pop[i][d] for d in range(dim)]
            trial_sol = vec_to_sol(trial)
            trial_fit = _eval_fitness(trial_sol, sizes, canvas_w, canvas_h, texts)
            if trial_fit >= pop_fit[i]:
                pop[i] = sol_to_vec(trial_sol)
                pop_fit[i] = trial_fit

    best_idx = max(range(pop_size), key=lambda k: pop_fit[k])
    return vec_to_sol(pop[best_idx])


def _solve_ant_colony(
    n_words: int, sizes: list[float], canvas_w: float, canvas_h: float,
    max_iter: int, rng: random.Random, texts: list[str] | None = None,
) -> list[tuple[float, float, float]]:
    """Ant Colony Optimization: pheromone grid 10x10, rho=0.5."""
    grid_size = 10
    n_ants = 20
    rho = 0.5
    alpha_p = 1.0
    beta_p = 2.0

    # Pheromone grid per word: grid_size x grid_size
    pheromone = [[[1.0] * grid_size for _ in range(grid_size)] for _ in range(n_words)]
    best_sol: list[tuple[float, float, float]] | None = None
    best_fit = float("-inf")

    cell_w = canvas_w / grid_size
    cell_h = canvas_h / grid_size

    for _ in range(max_iter):
        ant_solutions: list[list[tuple[float, float, float]]] = []
        ant_fits: list[float] = []

        for _ in range(n_ants):
            sol: list[tuple[float, float, float]] = []
            for w in range(n_words):
                # Build probability from pheromone
                probs: list[float] = []
                cells: list[tuple[int, int]] = []
                for gi in range(grid_size):
                    for gj in range(grid_size):
                        tau = pheromone[w][gi][gj] ** alpha_p
                        # Heuristic: prefer center
                        cx_cell = (gj + 0.5) * cell_w
                        cy_cell = (gi + 0.5) * cell_h
                        dist = math.hypot(cx_cell - canvas_w / 2, cy_cell - canvas_h / 2) + 1.0
                        eta = (1.0 / dist) ** beta_p
                        probs.append(tau * eta)
                        cells.append((gi, gj))
                total_p = sum(probs)
                if total_p <= 0:
                    chosen = rng.randint(0, len(cells) - 1)
                else:
                    r = rng.random() * total_p
                    cum = 0.0
                    chosen = 0
                    for ci, p in enumerate(probs):
                        cum += p
                        if cum >= r:
                            chosen = ci
                            break
                gi, gj = cells[chosen]
                x = (gj + rng.random()) * cell_w
                y = (gi + rng.random()) * cell_h
                rot = _ACTIVE_LAYOUT_READABILITY.choose_rotation(rng)
                sol.append((x, y, float(rot)))

            sol = _clamp_solution(sol, canvas_w, canvas_h)
            fit = _eval_fitness(sol, sizes, canvas_w, canvas_h, texts)
            ant_solutions.append(sol)
            ant_fits.append(fit)

            if fit > best_fit:
                best_fit = fit
                best_sol = list(sol)

        # Evaporate
        for w in range(n_words):
            for gi in range(grid_size):
                for gj in range(grid_size):
                    pheromone[w][gi][gj] *= (1 - rho)

        # Deposit: best ant deposits more
        if ant_fits:
            best_ant = max(range(n_ants), key=lambda k: ant_fits[k])
            deposit = max(0.1, 1.0 + ant_fits[best_ant])
            for w in range(n_words):
                x, y, _ = ant_solutions[best_ant][w]
                gj = min(grid_size - 1, max(0, int(x / cell_w)))
                gi = min(grid_size - 1, max(0, int(y / cell_h)))
                pheromone[w][gi][gj] += deposit

    return best_sol if best_sol is not None else _random_solution(n_words, canvas_w, canvas_h, rng)


def _solve_firefly(
    n_words: int, sizes: list[float], canvas_w: float, canvas_h: float,
    max_iter: int, rng: random.Random, texts: list[str] | None = None,
) -> list[tuple[float, float, float]]:
    """Firefly Algorithm: beta0=1.0, gamma=0.01, alpha=0.2."""
    pop_size = 20
    beta0 = 1.0
    gamma = 0.01
    alpha_fa = 0.2

    dim = n_words * 3

    def sol_to_vec(sol: list[tuple[float, float, float]]) -> list[float]:
        v: list[float] = []
        for x, y, r in sol:
            v.extend([x, y, r])
        return v

    def vec_to_sol(v: list[float]) -> list[tuple[float, float, float]]:
        s: list[tuple[float, float, float]] = []
        for i in range(0, len(v), 3):
            s.append((v[i], v[i + 1], v[i + 2]))
        return _clamp_solution(s, canvas_w, canvas_h)

    fireflies = [sol_to_vec(_random_solution(n_words, canvas_w, canvas_h, rng)) for _ in range(pop_size)]
    brightness = [_eval_fitness(vec_to_sol(f), sizes, canvas_w, canvas_h, texts) for f in fireflies]

    for _ in range(max_iter):
        for i in range(pop_size):
            for j in range(pop_size):
                if brightness[j] > brightness[i]:
                    # Distance
                    r_sq = sum((fireflies[i][d] - fireflies[j][d]) ** 2 for d in range(dim))
                    beta = beta0 * math.exp(-gamma * r_sq)
                    for d in range(dim):
                        fireflies[i][d] += beta * (fireflies[j][d] - fireflies[i][d]) + alpha_fa * rng.gauss(0, 1)
                    sol = vec_to_sol(fireflies[i])
                    fireflies[i] = sol_to_vec(sol)
                    brightness[i] = _eval_fitness(sol, sizes, canvas_w, canvas_h, texts)

    best_idx = max(range(pop_size), key=lambda k: brightness[k])
    return vec_to_sol(fireflies[best_idx])


def _solve_cuckoo_search(
    n_words: int, sizes: list[float], canvas_w: float, canvas_h: float,
    max_iter: int, rng: random.Random, texts: list[str] | None = None,
) -> list[tuple[float, float, float]]:
    """Cuckoo Search: pa=0.25, Levy flights beta=1.5 (Mantegna)."""
    pop_size = 20
    pa = 0.25
    beta_levy = 1.5

    # Mantegna's algorithm constants
    sigma_u = (
        math.gamma(1 + beta_levy) * math.sin(math.pi * beta_levy / 2)
        / (math.gamma((1 + beta_levy) / 2) * beta_levy * 2 ** ((beta_levy - 1) / 2))
    ) ** (1 / beta_levy)
    sigma_v = 1.0

    dim = n_words * 3

    def sol_to_vec(sol: list[tuple[float, float, float]]) -> list[float]:
        v: list[float] = []
        for x, y, r in sol:
            v.extend([x, y, r])
        return v

    def vec_to_sol(v: list[float]) -> list[tuple[float, float, float]]:
        s: list[tuple[float, float, float]] = []
        for i in range(0, len(v), 3):
            s.append((v[i], v[i + 1], v[i + 2]))
        return _clamp_solution(s, canvas_w, canvas_h)

    def levy_step() -> float:
        u = rng.gauss(0, sigma_u)
        v = rng.gauss(0, sigma_v)
        return u / (abs(v) ** (1 / beta_levy))

    nests = [sol_to_vec(_random_solution(n_words, canvas_w, canvas_h, rng)) for _ in range(pop_size)]
    fits = [_eval_fitness(vec_to_sol(n_), sizes, canvas_w, canvas_h, texts) for n_ in nests]

    for _ in range(max_iter):
        # Generate new solution via Levy flight
        i = rng.randint(0, pop_size - 1)
        new_nest = [nests[i][d] + levy_step() * canvas_w * 0.01 for d in range(dim)]
        new_sol = vec_to_sol(new_nest)
        new_fit = _eval_fitness(new_sol, sizes, canvas_w, canvas_h, texts)
        j = rng.randint(0, pop_size - 1)
        if new_fit > fits[j]:
            nests[j] = sol_to_vec(new_sol)
            fits[j] = new_fit

        # Abandon worst fraction
        sorted_idx = sorted(range(pop_size), key=lambda k: fits[k])
        n_abandon = max(1, int(pa * pop_size))
        for k in range(n_abandon):
            idx = sorted_idx[k]
            nests[idx] = sol_to_vec(_random_solution(n_words, canvas_w, canvas_h, rng))
            fits[idx] = _eval_fitness(vec_to_sol(nests[idx]), sizes, canvas_w, canvas_h, texts)

    best_idx = max(range(pop_size), key=lambda k: fits[k])
    return vec_to_sol(nests[best_idx])


def _solve_bat(
    n_words: int, sizes: list[float], canvas_w: float, canvas_h: float,
    max_iter: int, rng: random.Random, texts: list[str] | None = None,
) -> list[tuple[float, float, float]]:
    """Bat Algorithm: f_min=0, f_max=2, A=0.5->0, r=0->0.9."""
    pop_size = 20
    f_min, f_max = 0.0, 2.0
    dim = n_words * 3

    def sol_to_vec(sol: list[tuple[float, float, float]]) -> list[float]:
        v: list[float] = []
        for x, y, r in sol:
            v.extend([x, y, r])
        return v

    def vec_to_sol(v: list[float]) -> list[tuple[float, float, float]]:
        s: list[tuple[float, float, float]] = []
        for i in range(0, len(v), 3):
            s.append((v[i], v[i + 1], v[i + 2]))
        return _clamp_solution(s, canvas_w, canvas_h)

    bats = [sol_to_vec(_random_solution(n_words, canvas_w, canvas_h, rng)) for _ in range(pop_size)]
    velocities = [[0.0] * dim for _ in range(pop_size)]
    freqs = [0.0] * pop_size
    fits = [_eval_fitness(vec_to_sol(b), sizes, canvas_w, canvas_h, texts) for b in bats]
    loudness = [0.5] * pop_size
    pulse_rate_init = [0.0] * pop_size
    pulse_rate = [0.0] * pop_size

    g_best_idx = max(range(pop_size), key=lambda k: fits[k])
    g_best = list(bats[g_best_idx])
    g_best_fit = fits[g_best_idx]

    for it in range(max_iter):
        for i in range(pop_size):
            freqs[i] = f_min + (f_max - f_min) * rng.random()
            for d in range(dim):
                velocities[i][d] += (bats[i][d] - g_best[d]) * freqs[i]
            new_pos = [bats[i][d] + velocities[i][d] for d in range(dim)]

            # Local search
            if rng.random() > pulse_rate[i]:
                avg_loud = sum(loudness) / pop_size
                new_pos = [g_best[d] + avg_loud * rng.gauss(0, 1) for d in range(dim)]

            new_sol = vec_to_sol(new_pos)
            new_fit = _eval_fitness(new_sol, sizes, canvas_w, canvas_h, texts)

            if new_fit > fits[i] and rng.random() < loudness[i]:
                bats[i] = sol_to_vec(new_sol)
                fits[i] = new_fit
                loudness[i] *= 0.9
                pulse_rate[i] = pulse_rate_init[i] * (1 - math.exp(-0.9 * it))

            if new_fit > g_best_fit:
                g_best = sol_to_vec(new_sol)
                g_best_fit = new_fit

    return vec_to_sol(g_best)


def _solve_grey_wolf(
    n_words: int, sizes: list[float], canvas_w: float, canvas_h: float,
    max_iter: int, rng: random.Random, texts: list[str] | None = None,
) -> list[tuple[float, float, float]]:
    """Grey Wolf Optimizer: alpha/beta/delta hierarchy, a=2->0."""
    pop_size = 20
    dim = n_words * 3

    def sol_to_vec(sol: list[tuple[float, float, float]]) -> list[float]:
        v: list[float] = []
        for x, y, r in sol:
            v.extend([x, y, r])
        return v

    def vec_to_sol(v: list[float]) -> list[tuple[float, float, float]]:
        s: list[tuple[float, float, float]] = []
        for i in range(0, len(v), 3):
            s.append((v[i], v[i + 1], v[i + 2]))
        return _clamp_solution(s, canvas_w, canvas_h)

    wolves = [sol_to_vec(_random_solution(n_words, canvas_w, canvas_h, rng)) for _ in range(pop_size)]
    fits = [_eval_fitness(vec_to_sol(w), sizes, canvas_w, canvas_h, texts) for w in wolves]

    sorted_idx = sorted(range(pop_size), key=lambda k: fits[k], reverse=True)
    alpha_w, beta_w, delta_w = [list(wolves[sorted_idx[i]]) for i in range(3)]

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

            sol = vec_to_sol(new_pos)
            wolves[i] = sol_to_vec(sol)
            fits[i] = _eval_fitness(sol, sizes, canvas_w, canvas_h, texts)

        sorted_idx = sorted(range(pop_size), key=lambda k: fits[k], reverse=True)
        alpha_w = list(wolves[sorted_idx[0]])
        beta_w = list(wolves[sorted_idx[1]])
        delta_w = list(wolves[sorted_idx[2]])

    return vec_to_sol(alpha_w)


def _solve_whale(
    n_words: int, sizes: list[float], canvas_w: float, canvas_h: float,
    max_iter: int, rng: random.Random, texts: list[str] | None = None,
) -> list[tuple[float, float, float]]:
    """Whale Optimization: a=2->0, spiral with b=1, 50% encircling vs spiral."""
    pop_size = 20
    b_spiral = 1.0
    dim = n_words * 3

    def sol_to_vec(sol: list[tuple[float, float, float]]) -> list[float]:
        v: list[float] = []
        for x, y, r in sol:
            v.extend([x, y, r])
        return v

    def vec_to_sol(v: list[float]) -> list[tuple[float, float, float]]:
        s: list[tuple[float, float, float]] = []
        for i in range(0, len(v), 3):
            s.append((v[i], v[i + 1], v[i + 2]))
        return _clamp_solution(s, canvas_w, canvas_h)

    whales = [sol_to_vec(_random_solution(n_words, canvas_w, canvas_h, rng)) for _ in range(pop_size)]
    fits = [_eval_fitness(vec_to_sol(w), sizes, canvas_w, canvas_h, texts) for w in whales]
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
                # Spiral
                for d in range(dim):
                    D_prime = abs(best_pos[d] - whales[i][d])
                    new_pos.append(
                        D_prime * math.exp(b_spiral * l_param) * math.cos(2 * math.pi * l_param)
                        + best_pos[d]
                    )

            sol = vec_to_sol(new_pos)
            whales[i] = sol_to_vec(sol)
            fits[i] = _eval_fitness(sol, sizes, canvas_w, canvas_h, texts)
            if fits[i] > best_fit:
                best_pos = list(whales[i])
                best_fit = fits[i]

    return vec_to_sol(best_pos)


def _solve_gravitational_search(
    n_words: int, sizes: list[float], canvas_w: float, canvas_h: float,
    max_iter: int, rng: random.Random, texts: list[str] | None = None,
) -> list[tuple[float, float, float]]:
    """Gravitational Search: G=100->0.01 exponential decay."""
    pop_size = 20
    G_init = 100.0
    dim = n_words * 3

    def sol_to_vec(sol: list[tuple[float, float, float]]) -> list[float]:
        v: list[float] = []
        for x, y, r in sol:
            v.extend([x, y, r])
        return v

    def vec_to_sol(v: list[float]) -> list[tuple[float, float, float]]:
        s: list[tuple[float, float, float]] = []
        for i in range(0, len(v), 3):
            s.append((v[i], v[i + 1], v[i + 2]))
        return _clamp_solution(s, canvas_w, canvas_h)

    agents = [sol_to_vec(_random_solution(n_words, canvas_w, canvas_h, rng)) for _ in range(pop_size)]
    velocities = [[0.0] * dim for _ in range(pop_size)]
    fits = [_eval_fitness(vec_to_sol(a), sizes, canvas_w, canvas_h, texts) for a in agents]

    for it in range(max_iter):
        G = G_init * math.exp(-20 * it / max(max_iter, 1))

        worst = min(fits)
        best = max(fits)
        span = best - worst if best != worst else 1.0

        # Compute masses
        masses = [(fits[i] - worst) / span for i in range(pop_size)]
        total_mass = sum(masses)
        if total_mass > 0:
            masses = [m / total_mass for m in masses]
        else:
            masses = [1.0 / pop_size] * pop_size

        # Only top k agents exert force
        k_best = max(2, int(pop_size * (1 - it / max(max_iter, 1))))
        sorted_idx = sorted(range(pop_size), key=lambda j: fits[j], reverse=True)
        active = set(sorted_idx[:k_best])

        for i in range(pop_size):
            force = [0.0] * dim
            for j in active:
                if i == j:
                    continue
                r = math.sqrt(sum((agents[i][d] - agents[j][d]) ** 2 for d in range(dim))) + 1e-10
                for d in range(dim):
                    force[d] += rng.random() * G * masses[j] * (agents[j][d] - agents[i][d]) / r

            mi = masses[i] if masses[i] > 0 else 1e-10
            for d in range(dim):
                velocities[i][d] = rng.random() * velocities[i][d] + force[d] / mi
                agents[i][d] += velocities[i][d]

            sol = vec_to_sol(agents[i])
            agents[i] = sol_to_vec(sol)
            fits[i] = _eval_fitness(sol, sizes, canvas_w, canvas_h, texts)

    best_idx = max(range(pop_size), key=lambda k: fits[k])
    return vec_to_sol(agents[best_idx])


def _solve_flower_pollination(
    n_words: int, sizes: list[float], canvas_w: float, canvas_h: float,
    max_iter: int, rng: random.Random, texts: list[str] | None = None,
) -> list[tuple[float, float, float]]:
    """Flower Pollination: p=0.8 switch, Levy for global, gaussian for local."""
    pop_size = 20
    p_switch = 0.8
    beta_levy = 1.5
    dim = n_words * 3

    sigma_u = (
        math.gamma(1 + beta_levy) * math.sin(math.pi * beta_levy / 2)
        / (math.gamma((1 + beta_levy) / 2) * beta_levy * 2 ** ((beta_levy - 1) / 2))
    ) ** (1 / beta_levy)

    def sol_to_vec(sol: list[tuple[float, float, float]]) -> list[float]:
        v: list[float] = []
        for x, y, r in sol:
            v.extend([x, y, r])
        return v

    def vec_to_sol(v: list[float]) -> list[tuple[float, float, float]]:
        s: list[tuple[float, float, float]] = []
        for i in range(0, len(v), 3):
            s.append((v[i], v[i + 1], v[i + 2]))
        return _clamp_solution(s, canvas_w, canvas_h)

    def levy_step() -> float:
        u = rng.gauss(0, sigma_u)
        v = rng.gauss(0, 1)
        return u / (abs(v) ** (1 / beta_levy))

    flowers = [sol_to_vec(_random_solution(n_words, canvas_w, canvas_h, rng)) for _ in range(pop_size)]
    fits = [_eval_fitness(vec_to_sol(f), sizes, canvas_w, canvas_h, texts) for f in flowers]
    best_idx = max(range(pop_size), key=lambda k: fits[k])
    g_best = list(flowers[best_idx])

    for _ in range(max_iter):
        for i in range(pop_size):
            if rng.random() < p_switch:
                # Global pollination via Levy
                new_pos = [flowers[i][d] + levy_step() * (g_best[d] - flowers[i][d]) for d in range(dim)]
            else:
                # Local pollination
                j, k = rng.sample([x for x in range(pop_size) if x != i], 2)
                eps = rng.random()
                new_pos = [flowers[i][d] + eps * (flowers[j][d] - flowers[k][d]) for d in range(dim)]

            new_sol = vec_to_sol(new_pos)
            new_fit = _eval_fitness(new_sol, sizes, canvas_w, canvas_h, texts)
            if new_fit > fits[i]:
                flowers[i] = sol_to_vec(new_sol)
                fits[i] = new_fit
                if new_fit > fits[best_idx]:
                    best_idx = i
                    g_best = list(flowers[i])

    return vec_to_sol(g_best)


def _solve_moth_flame(
    n_words: int, sizes: list[float], canvas_w: float, canvas_h: float,
    max_iter: int, rng: random.Random, texts: list[str] | None = None,
) -> list[tuple[float, float, float]]:
    """Moth-Flame Optimization: logarithmic spiral, flames decrease n->1."""
    pop_size = 20
    dim = n_words * 3

    def sol_to_vec(sol: list[tuple[float, float, float]]) -> list[float]:
        v: list[float] = []
        for x, y, r in sol:
            v.extend([x, y, r])
        return v

    def vec_to_sol(v: list[float]) -> list[tuple[float, float, float]]:
        s: list[tuple[float, float, float]] = []
        for i in range(0, len(v), 3):
            s.append((v[i], v[i + 1], v[i + 2]))
        return _clamp_solution(s, canvas_w, canvas_h)

    moths = [sol_to_vec(_random_solution(n_words, canvas_w, canvas_h, rng)) for _ in range(pop_size)]
    fits = [_eval_fitness(vec_to_sol(m), sizes, canvas_w, canvas_h, texts) for m in moths]

    sorted_idx = sorted(range(pop_size), key=lambda k: fits[k], reverse=True)
    flames = [list(moths[sorted_idx[i]]) for i in range(pop_size)]
    flame_fits = [fits[sorted_idx[i]] for i in range(pop_size)]

    for it in range(max_iter):
        n_flames = max(1, int(pop_size - it * (pop_size - 1) / max(max_iter, 1)))
        for i in range(pop_size):
            flame_idx = min(i, n_flames - 1)
            t_param = rng.uniform(-1, 1)
            b_param = 1.0
            new_pos: list[float] = []
            for d in range(dim):
                D = abs(flames[flame_idx][d] - moths[i][d])
                new_pos.append(
                    D * math.exp(b_param * t_param) * math.cos(2 * math.pi * t_param)
                    + flames[flame_idx][d]
                )
            sol = vec_to_sol(new_pos)
            moths[i] = sol_to_vec(sol)
            fits[i] = _eval_fitness(sol, sizes, canvas_w, canvas_h, texts)

        # Update flames
        all_combined = list(range(pop_size))
        all_combined.sort(key=lambda k: fits[k], reverse=True)
        for rank, k in enumerate(all_combined[:pop_size]):
            if fits[k] > flame_fits[rank]:
                flames[rank] = list(moths[k])
                flame_fits[rank] = fits[k]

    best_idx = max(range(pop_size), key=lambda k: flame_fits[k])
    return vec_to_sol(flames[best_idx])


def _solve_salp_swarm(
    n_words: int, sizes: list[float], canvas_w: float, canvas_h: float,
    max_iter: int, rng: random.Random, texts: list[str] | None = None,
) -> list[tuple[float, float, float]]:
    """Salp Swarm: c1=2*exp(-(4t/T)^2), leader/follower chain."""
    pop_size = 20
    dim = n_words * 3

    def sol_to_vec(sol: list[tuple[float, float, float]]) -> list[float]:
        v: list[float] = []
        for x, y, r in sol:
            v.extend([x, y, r])
        return v

    def vec_to_sol(v: list[float]) -> list[tuple[float, float, float]]:
        s: list[tuple[float, float, float]] = []
        for i in range(0, len(v), 3):
            s.append((v[i], v[i + 1], v[i + 2]))
        return _clamp_solution(s, canvas_w, canvas_h)

    salps = [sol_to_vec(_random_solution(n_words, canvas_w, canvas_h, rng)) for _ in range(pop_size)]
    fits = [_eval_fitness(vec_to_sol(s), sizes, canvas_w, canvas_h, texts) for s in salps]
    best_idx = max(range(pop_size), key=lambda k: fits[k])
    food = list(salps[best_idx])

    ub = [canvas_w * 0.95] * dim
    lb = [canvas_w * 0.05] * dim
    for d in range(dim):
        if d % 3 == 1:
            ub[d] = canvas_h * 0.95
            lb[d] = canvas_h * 0.05
        elif d % 3 == 2:
            ub[d] = 90.0
            lb[d] = -8.0

    for it in range(max_iter):
        c1 = 2 * math.exp(-(4 * it / max(max_iter, 1)) ** 2)
        for i in range(pop_size):
            if i == 0:
                # Leader
                for d in range(dim):
                    c2, c3 = rng.random(), rng.random()
                    if c3 < 0.5:
                        salps[i][d] = food[d] + c1 * ((ub[d] - lb[d]) * c2 + lb[d])
                    else:
                        salps[i][d] = food[d] - c1 * ((ub[d] - lb[d]) * c2 + lb[d])
            else:
                # Follower
                for d in range(dim):
                    salps[i][d] = (salps[i][d] + salps[i - 1][d]) / 2

            sol = vec_to_sol(salps[i])
            salps[i] = sol_to_vec(sol)
            fits[i] = _eval_fitness(sol, sizes, canvas_w, canvas_h, texts)
            if fits[i] > fits[best_idx]:
                best_idx = i
                food = list(salps[i])

    return vec_to_sol(food)


def _solve_sine_cosine(
    n_words: int, sizes: list[float], canvas_w: float, canvas_h: float,
    max_iter: int, rng: random.Random, texts: list[str] | None = None,
) -> list[tuple[float, float, float]]:
    """Sine Cosine Algorithm: a=2->0, r1 sinusoidal update."""
    pop_size = 20
    dim = n_words * 3

    def sol_to_vec(sol: list[tuple[float, float, float]]) -> list[float]:
        v: list[float] = []
        for x, y, r in sol:
            v.extend([x, y, r])
        return v

    def vec_to_sol(v: list[float]) -> list[tuple[float, float, float]]:
        s: list[tuple[float, float, float]] = []
        for i in range(0, len(v), 3):
            s.append((v[i], v[i + 1], v[i + 2]))
        return _clamp_solution(s, canvas_w, canvas_h)

    agents = [sol_to_vec(_random_solution(n_words, canvas_w, canvas_h, rng)) for _ in range(pop_size)]
    fits = [_eval_fitness(vec_to_sol(a), sizes, canvas_w, canvas_h, texts) for a in agents]
    best_idx = max(range(pop_size), key=lambda k: fits[k])
    dest = list(agents[best_idx])

    for it in range(max_iter):
        a_param = 2.0 * (1 - it / max(max_iter, 1))
        for i in range(pop_size):
            r1 = a_param
            r2 = 2 * math.pi * rng.random()
            r3 = 2 * rng.random()
            r4 = rng.random()

            new_pos: list[float] = []
            for d in range(dim):
                if r4 < 0.5:
                    new_pos.append(agents[i][d] + r1 * math.sin(r2) * abs(r3 * dest[d] - agents[i][d]))
                else:
                    new_pos.append(agents[i][d] + r1 * math.cos(r2) * abs(r3 * dest[d] - agents[i][d]))

            sol = vec_to_sol(new_pos)
            agents[i] = sol_to_vec(sol)
            fits[i] = _eval_fitness(sol, sizes, canvas_w, canvas_h, texts)
            if fits[i] > fits[best_idx]:
                best_idx = i
                dest = list(agents[i])

    return vec_to_sol(dest)


def _solve_teaching_learning(
    n_words: int, sizes: list[float], canvas_w: float, canvas_h: float,
    max_iter: int, rng: random.Random, texts: list[str] | None = None,
) -> list[tuple[float, float, float]]:
    """Teaching-Learning-Based Optimization: teacher + learner phases."""
    pop_size = 20
    dim = n_words * 3

    def sol_to_vec(sol: list[tuple[float, float, float]]) -> list[float]:
        v: list[float] = []
        for x, y, r in sol:
            v.extend([x, y, r])
        return v

    def vec_to_sol(v: list[float]) -> list[tuple[float, float, float]]:
        s: list[tuple[float, float, float]] = []
        for i in range(0, len(v), 3):
            s.append((v[i], v[i + 1], v[i + 2]))
        return _clamp_solution(s, canvas_w, canvas_h)

    learners = [sol_to_vec(_random_solution(n_words, canvas_w, canvas_h, rng)) for _ in range(pop_size)]
    fits = [_eval_fitness(vec_to_sol(l), sizes, canvas_w, canvas_h, texts) for l in learners]

    for _ in range(max_iter):
        # Find teacher (best)
        teacher_idx = max(range(pop_size), key=lambda k: fits[k])
        teacher = learners[teacher_idx]

        # Compute mean
        mean_pos = [sum(learners[j][d] for j in range(pop_size)) / pop_size for d in range(dim)]

        # Teacher phase
        for i in range(pop_size):
            tf = rng.choice([1, 2])
            new_pos = [learners[i][d] + rng.random() * (teacher[d] - tf * mean_pos[d]) for d in range(dim)]
            new_sol = vec_to_sol(new_pos)
            new_fit = _eval_fitness(new_sol, sizes, canvas_w, canvas_h, texts)
            if new_fit > fits[i]:
                learners[i] = sol_to_vec(new_sol)
                fits[i] = new_fit

        # Learner phase
        for i in range(pop_size):
            j = rng.randint(0, pop_size - 1)
            while j == i:
                j = rng.randint(0, pop_size - 1)
            if fits[i] > fits[j]:
                new_pos = [learners[i][d] + rng.random() * (learners[i][d] - learners[j][d]) for d in range(dim)]
            else:
                new_pos = [learners[i][d] + rng.random() * (learners[j][d] - learners[i][d]) for d in range(dim)]
            new_sol = vec_to_sol(new_pos)
            new_fit = _eval_fitness(new_sol, sizes, canvas_w, canvas_h, texts)
            if new_fit > fits[i]:
                learners[i] = sol_to_vec(new_sol)
                fits[i] = new_fit

    best_idx = max(range(pop_size), key=lambda k: fits[k])
    return vec_to_sol(learners[best_idx])


def _solve_jaya(
    n_words: int, sizes: list[float], canvas_w: float, canvas_h: float,
    max_iter: int, rng: random.Random, texts: list[str] | None = None,
) -> list[tuple[float, float, float]]:
    """Jaya Algorithm: move toward best, away from worst. Zero hyperparameters."""
    pop_size = 20
    dim = n_words * 3

    def sol_to_vec(sol: list[tuple[float, float, float]]) -> list[float]:
        v: list[float] = []
        for x, y, r in sol:
            v.extend([x, y, r])
        return v

    def vec_to_sol(v: list[float]) -> list[tuple[float, float, float]]:
        s: list[tuple[float, float, float]] = []
        for i in range(0, len(v), 3):
            s.append((v[i], v[i + 1], v[i + 2]))
        return _clamp_solution(s, canvas_w, canvas_h)

    pop = [sol_to_vec(_random_solution(n_words, canvas_w, canvas_h, rng)) for _ in range(pop_size)]
    fits = [_eval_fitness(vec_to_sol(p), sizes, canvas_w, canvas_h, texts) for p in pop]

    for _ in range(max_iter):
        best_idx = max(range(pop_size), key=lambda k: fits[k])
        worst_idx = min(range(pop_size), key=lambda k: fits[k])
        best_p = pop[best_idx]
        worst_p = pop[worst_idx]

        for i in range(pop_size):
            r1, r2 = rng.random(), rng.random()
            new_pos = [
                pop[i][d]
                + r1 * (best_p[d] - abs(pop[i][d]))
                - r2 * (worst_p[d] - abs(pop[i][d]))
                for d in range(dim)
            ]
            new_sol = vec_to_sol(new_pos)
            new_fit = _eval_fitness(new_sol, sizes, canvas_w, canvas_h, texts)
            if new_fit > fits[i]:
                pop[i] = sol_to_vec(new_sol)
                fits[i] = new_fit

    best_idx = max(range(pop_size), key=lambda k: fits[k])
    return vec_to_sol(pop[best_idx])


def _solve_water_cycle(
    n_words: int, sizes: list[float], canvas_w: float, canvas_h: float,
    max_iter: int, rng: random.Random, texts: list[str] | None = None,
) -> list[tuple[float, float, float]]:
    """Water Cycle Algorithm: N_sr=4 (rivers+sea), evap_rate=0.01."""
    pop_size = 20
    n_sr = 4
    evap_rate = 0.01
    dim = n_words * 3

    def sol_to_vec(sol: list[tuple[float, float, float]]) -> list[float]:
        v: list[float] = []
        for x, y, r in sol:
            v.extend([x, y, r])
        return v

    def vec_to_sol(v: list[float]) -> list[tuple[float, float, float]]:
        s: list[tuple[float, float, float]] = []
        for i in range(0, len(v), 3):
            s.append((v[i], v[i + 1], v[i + 2]))
        return _clamp_solution(s, canvas_w, canvas_h)

    streams = [sol_to_vec(_random_solution(n_words, canvas_w, canvas_h, rng)) for _ in range(pop_size)]
    fits = [_eval_fitness(vec_to_sol(s), sizes, canvas_w, canvas_h, texts) for s in streams]

    sorted_idx = sorted(range(pop_size), key=lambda k: fits[k], reverse=True)
    # sea = index 0, rivers = indices 1..n_sr-1, streams = rest
    sea_idx = sorted_idx[0]

    for _ in range(max_iter):
        for i in range(pop_size):
            if i == sea_idx:
                continue
            # Flow toward sea or a river
            target = sea_idx if i >= n_sr else sea_idx
            if i < n_sr and i != sea_idx:
                target = sea_idx
            new_pos = [streams[i][d] + rng.random() * 2 * (streams[target][d] - streams[i][d]) for d in range(dim)]
            new_sol = vec_to_sol(new_pos)
            new_fit = _eval_fitness(new_sol, sizes, canvas_w, canvas_h, texts)
            if new_fit > fits[i]:
                streams[i] = sol_to_vec(new_sol)
                fits[i] = new_fit

        # Evaporation + rain
        for i in range(n_sr, pop_size):
            dist = math.sqrt(sum((streams[i][d] - streams[sea_idx][d]) ** 2 for d in range(dim)))
            if dist < evap_rate * canvas_w:
                streams[i] = sol_to_vec(_random_solution(n_words, canvas_w, canvas_h, rng))
                fits[i] = _eval_fitness(vec_to_sol(streams[i]), sizes, canvas_w, canvas_h, texts)

        # Update sea
        sea_idx = max(range(pop_size), key=lambda k: fits[k])

    return vec_to_sol(streams[sea_idx])


def _solve_biogeography(
    n_words: int, sizes: list[float], canvas_w: float, canvas_h: float,
    max_iter: int, rng: random.Random, texts: list[str] | None = None,
) -> list[tuple[float, float, float]]:
    """Biogeography-Based Optimization: immigration/emigration curves + mutation."""
    pop_size = 20
    dim = n_words * 3
    mutation_rate = 0.05

    def sol_to_vec(sol: list[tuple[float, float, float]]) -> list[float]:
        v: list[float] = []
        for x, y, r in sol:
            v.extend([x, y, r])
        return v

    def vec_to_sol(v: list[float]) -> list[tuple[float, float, float]]:
        s: list[tuple[float, float, float]] = []
        for i in range(0, len(v), 3):
            s.append((v[i], v[i + 1], v[i + 2]))
        return _clamp_solution(s, canvas_w, canvas_h)

    habitats = [sol_to_vec(_random_solution(n_words, canvas_w, canvas_h, rng)) for _ in range(pop_size)]
    fits = [_eval_fitness(vec_to_sol(h), sizes, canvas_w, canvas_h, texts) for h in habitats]

    for _ in range(max_iter):
        sorted_idx = sorted(range(pop_size), key=lambda k: fits[k], reverse=True)
        # Immigration/emigration rates linear
        lambdas = [1.0 - rank / pop_size for rank in range(pop_size)]  # immigration
        mus = [rank / pop_size for rank in range(pop_size)]  # emigration

        new_habitats = [list(h) for h in habitats]
        for idx_rank, i in enumerate(sorted_idx):
            for d in range(dim):
                if rng.random() < lambdas[idx_rank]:
                    # Immigration: pick emigrating habitat
                    # Roulette on emigration rates
                    total_mu = sum(mus)
                    r = rng.random() * total_mu
                    cum = 0.0
                    donor = sorted_idx[0]
                    for r_idx, j in enumerate(sorted_idx):
                        cum += mus[r_idx]
                        if cum >= r:
                            donor = j
                            break
                    new_habitats[i][d] = habitats[donor][d]

                # Mutation
                if rng.random() < mutation_rate:
                    if d % 3 == 0:
                        new_habitats[i][d] = rng.uniform(canvas_w * 0.05, canvas_w * 0.95)
                    elif d % 3 == 1:
                        new_habitats[i][d] = rng.uniform(canvas_h * 0.05, canvas_h * 0.95)
                    else:
                        new_habitats[i][d] = _ACTIVE_LAYOUT_READABILITY.choose_rotation(rng)

        for i in range(pop_size):
            sol = vec_to_sol(new_habitats[i])
            new_fit = _eval_fitness(sol, sizes, canvas_w, canvas_h, texts)
            if new_fit > fits[i]:
                habitats[i] = sol_to_vec(sol)
                fits[i] = new_fit

    best_idx = max(range(pop_size), key=lambda k: fits[k])
    return vec_to_sol(habitats[best_idx])


def _solve_artificial_bee_colony(
    n_words: int, sizes: list[float], canvas_w: float, canvas_h: float,
    max_iter: int, rng: random.Random, texts: list[str] | None = None,
) -> list[tuple[float, float, float]]:
    """Artificial Bee Colony: employed->onlooker->scout, limit=n_words*5."""
    pop_size = 20
    limit = n_words * 5
    dim = n_words * 3

    def sol_to_vec(sol: list[tuple[float, float, float]]) -> list[float]:
        v: list[float] = []
        for x, y, r in sol:
            v.extend([x, y, r])
        return v

    def vec_to_sol(v: list[float]) -> list[tuple[float, float, float]]:
        s: list[tuple[float, float, float]] = []
        for i in range(0, len(v), 3):
            s.append((v[i], v[i + 1], v[i + 2]))
        return _clamp_solution(s, canvas_w, canvas_h)

    food_sources = [sol_to_vec(_random_solution(n_words, canvas_w, canvas_h, rng)) for _ in range(pop_size)]
    fits = [_eval_fitness(vec_to_sol(f), sizes, canvas_w, canvas_h, texts) for f in food_sources]
    trials = [0] * pop_size

    for _ in range(max_iter):
        # Employed bee phase
        for i in range(pop_size):
            k = rng.randint(0, pop_size - 1)
            while k == i:
                k = rng.randint(0, pop_size - 1)
            d_idx = rng.randint(0, dim - 1)
            new_pos = list(food_sources[i])
            phi = rng.uniform(-1, 1)
            new_pos[d_idx] = food_sources[i][d_idx] + phi * (food_sources[i][d_idx] - food_sources[k][d_idx])
            new_sol = vec_to_sol(new_pos)
            new_fit = _eval_fitness(new_sol, sizes, canvas_w, canvas_h, texts)
            if new_fit > fits[i]:
                food_sources[i] = sol_to_vec(new_sol)
                fits[i] = new_fit
                trials[i] = 0
            else:
                trials[i] += 1

        # Onlooker bee phase (roulette wheel)
        min_fit = min(fits)
        adjusted = [f - min_fit + 1e-10 for f in fits]
        total_fit = sum(adjusted)
        for _ in range(pop_size):
            # Select food source
            r = rng.random() * total_fit
            cum = 0.0
            selected = 0
            for j in range(pop_size):
                cum += adjusted[j]
                if cum >= r:
                    selected = j
                    break

            k = rng.randint(0, pop_size - 1)
            while k == selected:
                k = rng.randint(0, pop_size - 1)
            d_idx = rng.randint(0, dim - 1)
            new_pos = list(food_sources[selected])
            phi = rng.uniform(-1, 1)
            new_pos[d_idx] = food_sources[selected][d_idx] + phi * (food_sources[selected][d_idx] - food_sources[k][d_idx])
            new_sol = vec_to_sol(new_pos)
            new_fit = _eval_fitness(new_sol, sizes, canvas_w, canvas_h, texts)
            if new_fit > fits[selected]:
                food_sources[selected] = sol_to_vec(new_sol)
                fits[selected] = new_fit
                trials[selected] = 0
            else:
                trials[selected] += 1

        # Scout bee phase
        for i in range(pop_size):
            if trials[i] > limit:
                food_sources[i] = sol_to_vec(_random_solution(n_words, canvas_w, canvas_h, rng))
                fits[i] = _eval_fitness(vec_to_sol(food_sources[i]), sizes, canvas_w, canvas_h, texts)
                trials[i] = 0

    best_idx = max(range(pop_size), key=lambda k: fits[k])
    return vec_to_sol(food_sources[best_idx])


def _solve_tabu_search(
    n_words: int, sizes: list[float], canvas_w: float, canvas_h: float,
    max_iter: int, rng: random.Random, texts: list[str] | None = None,
) -> list[tuple[float, float, float]]:
    """Tabu Search: neighborhood perturbation, tabu list size=20, aspiration."""
    tabu_size = 20
    dim = n_words * 3

    def sol_to_vec(sol: list[tuple[float, float, float]]) -> list[float]:
        v: list[float] = []
        for x, y, r in sol:
            v.extend([x, y, r])
        return v

    def vec_to_sol(v: list[float]) -> list[tuple[float, float, float]]:
        s: list[tuple[float, float, float]] = []
        for i in range(0, len(v), 3):
            s.append((v[i], v[i + 1], v[i + 2]))
        return _clamp_solution(s, canvas_w, canvas_h)

    def sol_hash(sol: list[tuple[float, float, float]]) -> int:
        return hash(tuple(round(v, 1) for pos in sol for v in pos))

    current = _random_solution(n_words, canvas_w, canvas_h, rng)
    current_fit = _eval_fitness(current, sizes, canvas_w, canvas_h, texts)
    best = list(current)
    best_fit = current_fit
    tabu_list: list[int] = []

    for _ in range(max_iter):
        # Generate neighborhood
        neighbors: list[list[tuple[float, float, float]]] = []
        n_neighbors = 10
        for _ in range(n_neighbors):
            neighbor = list(current)
            n_perturb = rng.randint(1, min(3, n_words))
            for _ in range(n_perturb):
                idx = rng.randint(0, n_words - 1)
                x, y, rot = neighbor[idx]
                x += rng.gauss(0, canvas_w * 0.08)
                y += rng.gauss(0, canvas_h * 0.08)
                rot = _ACTIVE_LAYOUT_READABILITY.choose_rotation(rng)
                neighbor[idx] = (x, y, float(rot))
            neighbors.append(_clamp_solution(neighbor, canvas_w, canvas_h))

        # Pick best non-tabu neighbor (or aspiration)
        best_neighbor = None
        best_neighbor_fit = float("-inf")
        for nb in neighbors:
            nb_fit = _eval_fitness(nb, sizes, canvas_w, canvas_h, texts)
            h = sol_hash(nb)
            if h not in tabu_list or nb_fit > best_fit:  # aspiration
                if nb_fit > best_neighbor_fit:
                    best_neighbor = nb
                    best_neighbor_fit = nb_fit

        if best_neighbor is not None:
            current = best_neighbor
            current_fit = best_neighbor_fit
            tabu_list.append(sol_hash(current))
            if len(tabu_list) > tabu_size:
                tabu_list.pop(0)
            if current_fit > best_fit:
                best = list(current)
                best_fit = current_fit

    return best


def _solve_cultural(
    n_words: int, sizes: list[float], canvas_w: float, canvas_h: float,
    max_iter: int, rng: random.Random, texts: list[str] | None = None,
) -> list[tuple[float, float, float]]:
    """Cultural Algorithm: belief space with normative knowledge, acceptance=0.2."""
    pop_size = 20
    acceptance_rate = 0.2
    dim = n_words * 3

    def sol_to_vec(sol: list[tuple[float, float, float]]) -> list[float]:
        v: list[float] = []
        for x, y, r in sol:
            v.extend([x, y, r])
        return v

    def vec_to_sol(v: list[float]) -> list[tuple[float, float, float]]:
        s: list[tuple[float, float, float]] = []
        for i in range(0, len(v), 3):
            s.append((v[i], v[i + 1], v[i + 2]))
        return _clamp_solution(s, canvas_w, canvas_h)

    pop = [sol_to_vec(_random_solution(n_words, canvas_w, canvas_h, rng)) for _ in range(pop_size)]
    fits = [_eval_fitness(vec_to_sol(p), sizes, canvas_w, canvas_h, texts) for p in pop]

    # Belief space: min/max bounds per dimension from best individuals
    belief_min = [min(pop[i][d] for i in range(pop_size)) for d in range(dim)]
    belief_max = [max(pop[i][d] for i in range(pop_size)) for d in range(dim)]

    for _ in range(max_iter):
        # Accept top fraction into belief space
        sorted_idx = sorted(range(pop_size), key=lambda k: fits[k], reverse=True)
        n_accept = max(1, int(acceptance_rate * pop_size))
        accepted = sorted_idx[:n_accept]

        # Update belief space
        for d in range(dim):
            vals = [pop[i][d] for i in accepted]
            belief_min[d] = min(vals)
            belief_max[d] = max(vals)

        # Influence: generate new population using belief space
        for i in range(pop_size):
            new_pos: list[float] = []
            for d in range(dim):
                span = belief_max[d] - belief_min[d]
                if span < 1e-6:
                    span = canvas_w * 0.1 if d % 3 == 0 else canvas_h * 0.1 if d % 3 == 1 else 20.0
                new_val = pop[i][d] + rng.uniform(-1, 1) * span * 0.3
                new_pos.append(new_val)
            new_sol = vec_to_sol(new_pos)
            new_fit = _eval_fitness(new_sol, sizes, canvas_w, canvas_h, texts)
            if new_fit > fits[i]:
                pop[i] = sol_to_vec(new_sol)
                fits[i] = new_fit

    best_idx = max(range(pop_size), key=lambda k: fits[k])
    return vec_to_sol(pop[best_idx])


def _solve_invasive_weed(
    n_words: int, sizes: list[float], canvas_w: float, canvas_h: float,
    max_iter: int, rng: random.Random, texts: list[str] | None = None,
) -> list[tuple[float, float, float]]:
    """Invasive Weed Optimization: seeds=5 initial, max_seeds=5, sigma decay."""
    initial_pop = 5
    max_pop = 20
    max_seeds = 5
    sigma_init = min(canvas_w, canvas_h) / 4
    sigma_final = min(canvas_w, canvas_h) / 40
    dim = n_words * 3

    def sol_to_vec(sol: list[tuple[float, float, float]]) -> list[float]:
        v: list[float] = []
        for x, y, r in sol:
            v.extend([x, y, r])
        return v

    def vec_to_sol(v: list[float]) -> list[tuple[float, float, float]]:
        s: list[tuple[float, float, float]] = []
        for i in range(0, len(v), 3):
            s.append((v[i], v[i + 1], v[i + 2]))
        return _clamp_solution(s, canvas_w, canvas_h)

    weeds = [sol_to_vec(_random_solution(n_words, canvas_w, canvas_h, rng)) for _ in range(initial_pop)]
    fits = [_eval_fitness(vec_to_sol(w), sizes, canvas_w, canvas_h, texts) for w in weeds]

    for it in range(max_iter):
        sigma = sigma_init - (sigma_init - sigma_final) * ((it / max(max_iter - 1, 1)) ** 2)

        # Seed production
        if len(fits) > 0:
            min_fit = min(fits)
            max_fit = max(fits)
            span = max_fit - min_fit if max_fit != min_fit else 1.0

        new_weeds: list[list[float]] = []
        new_fits: list[float] = []
        for i in range(len(weeds)):
            n_seeds = max(1, int(1 + (fits[i] - min_fit) / span * (max_seeds - 1)))
            for _ in range(n_seeds):
                child = [weeds[i][d] + rng.gauss(0, sigma) for d in range(dim)]
                child_sol = vec_to_sol(child)
                child_fit = _eval_fitness(child_sol, sizes, canvas_w, canvas_h, texts)
                new_weeds.append(sol_to_vec(child_sol))
                new_fits.append(child_fit)

        weeds.extend(new_weeds)
        fits.extend(new_fits)

        # Competitive exclusion: keep top max_pop
        if len(weeds) > max_pop:
            sorted_idx = sorted(range(len(weeds)), key=lambda k: fits[k], reverse=True)
            weeds = [weeds[sorted_idx[i]] for i in range(max_pop)]
            fits = [fits[sorted_idx[i]] for i in range(max_pop)]

    best_idx = max(range(len(weeds)), key=lambda k: fits[k])
    return vec_to_sol(weeds[best_idx])


def _solve_charged_system_search(
    n_words: int, sizes: list[float], canvas_w: float, canvas_h: float,
    max_iter: int, rng: random.Random, texts: list[str] | None = None,
) -> list[tuple[float, float, float]]:
    """Charged System Search: ka=0.1, charged memory ratio=0.1."""
    pop_size = 20
    ka = 0.1
    dim = n_words * 3

    def sol_to_vec(sol: list[tuple[float, float, float]]) -> list[float]:
        v: list[float] = []
        for x, y, r in sol:
            v.extend([x, y, r])
        return v

    def vec_to_sol(v: list[float]) -> list[tuple[float, float, float]]:
        s: list[tuple[float, float, float]] = []
        for i in range(0, len(v), 3):
            s.append((v[i], v[i + 1], v[i + 2]))
        return _clamp_solution(s, canvas_w, canvas_h)

    particles = [sol_to_vec(_random_solution(n_words, canvas_w, canvas_h, rng)) for _ in range(pop_size)]
    velocities = [[0.0] * dim for _ in range(pop_size)]
    fits = [_eval_fitness(vec_to_sol(p), sizes, canvas_w, canvas_h, texts) for p in particles]

    for it in range(max_iter):
        worst = min(fits)
        best = max(fits)
        span = best - worst if best != worst else 1.0

        # Charge magnitude proportional to fitness
        charges = [(fits[i] - worst) / span for i in range(pop_size)]

        # Separation distance for charged memory
        all_dists: list[float] = []
        for i in range(pop_size):
            for j in range(i + 1, pop_size):
                d_ij = math.sqrt(sum((particles[i][d] - particles[j][d]) ** 2 for d in range(dim))) + 1e-10
                all_dists.append(d_ij)
        r_a = max(all_dists) * 0.1 if all_dists else canvas_w * 0.1

        for i in range(pop_size):
            force = [0.0] * dim
            for j in range(pop_size):
                if i == j:
                    continue
                r_ij = math.sqrt(sum((particles[i][d] - particles[j][d]) ** 2 for d in range(dim))) + 1e-10
                if r_ij < r_a:
                    for d_idx in range(dim):
                        force[d_idx] += charges[j] * (particles[j][d_idx] - particles[i][d_idx]) / (r_ij ** 3) * (r_ij)
                else:
                    for d_idx in range(dim):
                        force[d_idx] += charges[j] * (particles[j][d_idx] - particles[i][d_idx]) / (r_ij ** 2)

            for d_idx in range(dim):
                velocities[i][d_idx] = rng.random() * velocities[i][d_idx] + ka * force[d_idx]
                particles[i][d_idx] += velocities[i][d_idx]

            sol = vec_to_sol(particles[i])
            particles[i] = sol_to_vec(sol)
            fits[i] = _eval_fitness(sol, sizes, canvas_w, canvas_h, texts)

    best_idx = max(range(pop_size), key=lambda k: fits[k])
    return vec_to_sol(particles[best_idx])


def _solve_stochastic_fractal_search(
    n_words: int, sizes: list[float], canvas_w: float, canvas_h: float,
    max_iter: int, rng: random.Random, texts: list[str] | None = None,
) -> list[tuple[float, float, float]]:
    """Stochastic Fractal Search: gaussian walks at 2 scales."""
    pop_size = 20
    dim = n_words * 3

    def sol_to_vec(sol: list[tuple[float, float, float]]) -> list[float]:
        v: list[float] = []
        for x, y, r in sol:
            v.extend([x, y, r])
        return v

    def vec_to_sol(v: list[float]) -> list[tuple[float, float, float]]:
        s: list[tuple[float, float, float]] = []
        for i in range(0, len(v), 3):
            s.append((v[i], v[i + 1], v[i + 2]))
        return _clamp_solution(s, canvas_w, canvas_h)

    points = [sol_to_vec(_random_solution(n_words, canvas_w, canvas_h, rng)) for _ in range(pop_size)]
    fits = [_eval_fitness(vec_to_sol(p), sizes, canvas_w, canvas_h, texts) for p in points]
    best_idx = max(range(pop_size), key=lambda k: fits[k])
    g_best = list(points[best_idx])
    g_best_fit = fits[best_idx]

    for it in range(max_iter):
        # Diffusion process: two gaussian walks
        sigma_global = canvas_w * 0.1 * (1 - it / max(max_iter, 1))
        sigma_local = canvas_w * 0.02 * (1 - it / max(max_iter, 1))

        for i in range(pop_size):
            # Global diffusion
            new_global = [points[i][d] + rng.gauss(0, sigma_global) for d in range(dim)]
            sol_g = vec_to_sol(new_global)
            fit_g = _eval_fitness(sol_g, sizes, canvas_w, canvas_h, texts)

            # Local exploitation
            new_local = [points[i][d] + rng.gauss(0, sigma_local) * (g_best[d] - points[i][d]) for d in range(dim)]
            sol_l = vec_to_sol(new_local)
            fit_l = _eval_fitness(sol_l, sizes, canvas_w, canvas_h, texts)

            # Keep the best of the three
            candidates = [(points[i], fits[i]), (sol_to_vec(sol_g), fit_g), (sol_to_vec(sol_l), fit_l)]
            best_c = max(candidates, key=lambda c: c[1])
            points[i] = list(best_c[0])
            fits[i] = best_c[1]

            if fits[i] > g_best_fit:
                g_best = list(points[i])
                g_best_fit = fits[i]

        # Update: random replacement of worst with mutated best
        worst_idx = min(range(pop_size), key=lambda k: fits[k])
        if rng.random() < 0.1:
            new_pt = [g_best[d] + rng.gauss(0, sigma_local * 2) for d in range(dim)]
            sol_new = vec_to_sol(new_pt)
            fit_new = _eval_fitness(sol_new, sizes, canvas_w, canvas_h, texts)
            if fit_new > fits[worst_idx]:
                points[worst_idx] = sol_to_vec(sol_new)
                fits[worst_idx] = fit_new

    return vec_to_sol(g_best)


# ---------------------------------------------------------------------------
# Solver registry
# ---------------------------------------------------------------------------

_META_SOLVERS: dict[str, callable] = {
    "Harmony Search": _solve_harmony_search,
    "Simulated Annealing": _solve_simulated_annealing,
    "Particle Swarm": _solve_particle_swarm,
    "Differential Evolution": _solve_differential_evolution,
    "Ant Colony": _solve_ant_colony,
    "Firefly": _solve_firefly,
    "Cuckoo Search": _solve_cuckoo_search,
    "Bat Algorithm": _solve_bat,
    "Grey Wolf": _solve_grey_wolf,
    "Whale Optimization": _solve_whale,
    "Gravitational Search": _solve_gravitational_search,
    "Flower Pollination": _solve_flower_pollination,
    "Moth-Flame": _solve_moth_flame,
    "Salp Swarm": _solve_salp_swarm,
    "Sine Cosine": _solve_sine_cosine,
    "Teaching-Learning": _solve_teaching_learning,
    "Jaya": _solve_jaya,
    "Water Cycle": _solve_water_cycle,
    "Biogeography-Based": _solve_biogeography,
    "Artificial Bee Colony": _solve_artificial_bee_colony,
    "Tabu Search": _solve_tabu_search,
    "Cultural Algorithm": _solve_cultural,
    "Invasive Weed": _solve_invasive_weed,
    "Charged System Search": _solve_charged_system_search,
    "Stochastic Fractal Search": _solve_stochastic_fractal_search,
}
