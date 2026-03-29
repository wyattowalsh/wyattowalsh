"""Physarum polycephalum — slime mold transport network living art.

A slime mold grows from a central spore, explores the canvas, and connects
food sources (repos) with an efficient transport network.  Veins are
luminous yellow-gold on a dark substrate.  Simulation follows the Jones 2010
agent-based model on a low-resolution grid; rendering extracts marching-
squares iso-contours and emits pure SVG paths.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import timedelta
from typing import Any

from scipy.ndimage import uniform_filter

import numpy as np

from .shared import (
    HEIGHT,
    WIDTH,
    LANG_HUES,
    MAX_REPOS,
    Noise2D,
    ElementBudget,
    DerivedMetrics,
    ART_PALETTE_ANCHORS,
    _build_world_palette_extended,
    compute_derived_metrics,
    compute_maturity,
    compute_world_state,
    hex_frac,
    normalize_timeline_window,
    map_date_to_loop_delay,
    oklch,
    oklch_lerp,
    repo_to_canvas_position,
    select_primary_repos,
    topic_affinity_matrix,
    activity_tempo,
    visual_complexity,
    volumetric_glow_filter,
    oklch_gradient,
    seed_hash,
    contributions_monthly_to_daily_series,
    WorldState,
)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PhysarumConfig:
    """Tuning knobs for the Physarum simulation and rendering."""

    max_repos: int = 10
    max_elements: int = 25_000
    grid_resolution: int = 80
    contour_levels: int = 6
    agent_base: int = 200
    agent_scale: float = 50.0
    food_base: float = 5.0
    food_scale: float = 2.0
    sensor_angle: float = 0.4
    sensor_distance: float = 9.0
    step_size: float = 1.0
    evaporation: float = 0.05
    diffusion_kernel: int = 3
    deposit_amount: float = 5.0
    sim_steps_base: int = 80
    sim_steps_scale: float = 40.0


CFG = PhysarumConfig()

# Background substrate color (deep dark blue-black)
_BG_COLOR = oklch(0.12, 0.04, 250)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _grid_to_canvas(gx: float, gy: float, cell_w: float, cell_h: float) -> tuple[float, float]:
    """Convert grid coordinates to canvas (SVG) coordinates."""
    return gx * cell_w, gy * cell_h


def _extract_contours(
    field: np.ndarray,
    grid: int,
    level: float,
    cell_w: float,
    cell_h: float,
) -> list[list[tuple[float, float]]]:
    """Marching-squares iso-contour extraction.

    Returns a list of polyline chains (each a list of (x, y) canvas coords).
    """
    seg_list: list[tuple[tuple[float, float], tuple[float, float]]] = []
    for gy in range(grid - 1):
        for gx in range(grid - 1):
            tl = field[gy, gx]
            tr = field[gy, gx + 1]
            bl = field[gy + 1, gx]
            br = field[gy + 1, gx + 1]
            edges: list[tuple[float, float]] = []
            if (tl < level) != (tr < level):
                t = (level - tl) / (tr - tl + 1e-10)
                edges.append(_grid_to_canvas(gx + t, gy, cell_w, cell_h))
            if (bl < level) != (br < level):
                t = (level - bl) / (br - bl + 1e-10)
                edges.append(_grid_to_canvas(gx + t, gy + 1, cell_w, cell_h))
            if (tl < level) != (bl < level):
                t = (level - tl) / (bl - tl + 1e-10)
                edges.append(_grid_to_canvas(gx, gy + t, cell_w, cell_h))
            if (tr < level) != (br < level):
                t = (level - tr) / (br - tr + 1e-10)
                edges.append(_grid_to_canvas(gx + 1, gy + t, cell_w, cell_h))
            if len(edges) >= 2:
                seg_list.append((edges[0], edges[1]))

    if not seg_list:
        return []

    # Chain segments into polylines by greedy nearest-endpoint
    used = [False] * len(seg_list)
    chains: list[list[tuple[float, float]]] = []
    for start_i in range(len(seg_list)):
        if used[start_i]:
            continue
        used[start_i] = True
        chain = [seg_list[start_i][0], seg_list[start_i][1]]
        changed = True
        while changed:
            changed = False
            last = chain[-1]
            best_d, best_j, best_end = 8.0, -1, 0
            for j in range(len(seg_list)):
                if used[j]:
                    continue
                for end_idx in (0, 1):
                    pt = seg_list[j][end_idx]
                    d = math.hypot(pt[0] - last[0], pt[1] - last[1])
                    if d < best_d:
                        best_d, best_j, best_end = d, j, end_idx
            if best_j >= 0:
                used[best_j] = True
                chain.append(
                    seg_list[best_j][1 - best_end]
                    if best_end == 0
                    else seg_list[best_j][0]
                )
                changed = True
        if len(chain) >= 3:
            chains.append(chain)
    return chains


def _chaikin_smooth(
    points: list[tuple[float, float]], iterations: int = 1,
) -> list[tuple[float, float]]:
    """Chaikin corner-cutting polyline smoother."""
    if len(points) < 3 or iterations <= 0:
        return points
    smoothed = points[:]
    for _ in range(iterations):
        if len(smoothed) < 3:
            break
        nxt: list[tuple[float, float]] = [smoothed[0]]
        for i in range(len(smoothed) - 1):
            p0, p1 = smoothed[i], smoothed[i + 1]
            nxt.append((0.75 * p0[0] + 0.25 * p1[0], 0.75 * p0[1] + 0.25 * p1[1]))
            nxt.append((0.25 * p0[0] + 0.75 * p1[0], 0.25 * p0[1] + 0.75 * p1[1]))
        nxt.append(smoothed[-1])
        smoothed = nxt
    return smoothed


# ---------------------------------------------------------------------------
# Simulation (Jones 2010)
# ---------------------------------------------------------------------------


def _run_simulation(
    grid: int,
    food_sources: list[tuple[int, int, float]],
    *,
    n_agents: int,
    steps: int,
    config: PhysarumConfig,
    rng: np.random.Generator,
    evaporation_rate: float,
    speed_mult: float,
) -> np.ndarray:
    """Run the Physarum agent simulation on a grid.

    Parameters
    ----------
    grid : resolution of the square trail map.
    food_sources : list of (gx, gy, concentration) food positions.
    n_agents : number of slime-mold agent particles.
    steps : simulation steps to execute.
    config : tuning parameters.
    rng : numpy random generator.
    evaporation_rate : per-step trail decay (0-1).
    speed_mult : agent speed multiplier from activity tempo.

    Returns
    -------
    np.ndarray : trail map of shape (grid, grid).
    """
    trail = np.zeros((grid, grid), dtype=np.float64)

    # Seed initial food pheromone
    for fx, fy, conc in food_sources:
        if 0 <= fx < grid and 0 <= fy < grid:
            trail[fy, fx] += conc * 3.0

    # Agent state: positions and headings
    # Start agents from center (spore origin)
    cx, cy = grid / 2.0, grid / 2.0
    pos_x = rng.normal(cx, grid * 0.05, n_agents).astype(np.float64)
    pos_y = rng.normal(cy, grid * 0.05, n_agents).astype(np.float64)
    headings = rng.uniform(0, 2 * np.pi, n_agents).astype(np.float64)

    sa = config.sensor_angle
    sd = config.sensor_distance
    step_size = config.step_size * speed_mult
    deposit = config.deposit_amount

    for _step in range(steps):
        # 1. Food sources emit pheromone each step
        for fx, fy, conc in food_sources:
            if 0 <= fx < grid and 0 <= fy < grid:
                trail[fy, fx] += conc * 0.5

        # 2. Sense: read pheromone at 3 sensor positions per agent
        for sensor_dir, result_array in [
            (-sa, np.empty(n_agents)),
            (0.0, np.empty(n_agents)),
            (sa, np.empty(n_agents)),
        ]:
            sx = pos_x + np.cos(headings + sensor_dir) * sd
            sy = pos_y + np.sin(headings + sensor_dir) * sd
            six = np.clip(sx.astype(np.int32), 0, grid - 1)
            siy = np.clip(sy.astype(np.int32), 0, grid - 1)
            result_array[:] = trail[siy, six]
            if sensor_dir == -sa:
                sense_left = result_array.copy()
            elif sensor_dir == 0.0:
                sense_center = result_array.copy()
            else:
                sense_right = result_array.copy()

        # 3. Turn: steer toward strongest signal
        turn_left = sense_left > sense_center
        turn_right = sense_right > sense_center
        both_stronger = turn_left & turn_right

        # When both flanks > center, pick randomly
        random_choice = rng.random(n_agents) < 0.5
        headings = np.where(
            both_stronger & random_choice,
            headings - sa,
            np.where(
                both_stronger & ~random_choice,
                headings + sa,
                np.where(turn_left, headings - sa, np.where(turn_right, headings + sa, headings)),
            ),
        )

        # 4. Move forward
        pos_x += np.cos(headings) * step_size
        pos_y += np.sin(headings) * step_size

        # Wrap positions
        pos_x = pos_x % grid
        pos_y = pos_y % grid

        # 5. Deposit pheromone
        dix = np.clip(pos_x.astype(np.int32), 0, grid - 1)
        diy = np.clip(pos_y.astype(np.int32), 0, grid - 1)
        np.add.at(trail, (diy, dix), deposit)

        # 6. Diffuse (3x3 mean blur) then decay
        trail = uniform_filter(trail, size=config.diffusion_kernel, mode="wrap")
        trail *= (1.0 - evaporation_rate)

    return trail


# ---------------------------------------------------------------------------
# SVG rendering
# ---------------------------------------------------------------------------


def _path_d(points: list[tuple[float, float]]) -> str:
    """Build an SVG path ``d`` attribute from a polyline."""
    parts = [f"M{points[0][0]:.1f},{points[0][1]:.1f}"]
    for x, y in points[1:]:
        parts.append(f"L{x:.1f},{y:.1f}")
    return "".join(parts)


def generate(
    metrics: dict,
    *,
    seed: str | None = None,
    maturity: float | None = None,
    timeline: bool = True,
    loop_duration: float = 60.0,
    reveal_fraction: float = 0.93,
) -> str:
    """Generate a Physarum polycephalum transport network SVG.

    Parameters
    ----------
    metrics : GitHub profile metrics dict.
    seed : optional deterministic seed override.
    maturity : 0.0-1.0 ecosystem maturity override.
    timeline : enable CSS reveal animation.
    loop_duration : animation loop length in seconds.
    reveal_fraction : fraction of loop used for reveals.

    Returns
    -------
    str : complete SVG markup.
    """
    config = CFG
    mat = maturity if maturity is not None else compute_maturity(metrics)
    timeline_enabled = bool(timeline and loop_duration > 0)
    growth_mat = 1.0 if timeline_enabled else mat

    # ── WorldState ────────────────────────────────────────────────
    world: WorldState = compute_world_state(metrics)
    pal = _build_world_palette_extended(
        world.time_of_day, world.weather, world.season, world.energy,
    )
    complexity = visual_complexity(metrics)

    def _fade(start: float, full: float) -> float:
        """Smooth 0-1 ramp between start and full maturity."""
        return max(0.0, min(1.0, (growth_mat - start) / max(0.001, full - start)))

    # ── Deterministic seeding ─────────────────────────────────────
    h = seed_hash({"seed": seed}) if seed is not None else seed_hash(metrics)
    rng = np.random.default_rng(int(h[:8], 16))

    # ── Extract data ──────────────────────────────────────────────
    repos = metrics.get("top_repos") or metrics.get("repos") or []
    monthly = metrics.get("contributions_monthly", {})
    stars = int(metrics.get("stars", 0) or 0)
    contributions = int(metrics.get("contributions_last_year", 200) or 200)
    derived = compute_derived_metrics(metrics)

    primary_repos, _overflow = select_primary_repos(repos, limit=config.max_repos)
    tempo = activity_tempo(monthly)

    # ── Timeline window ───────────────────────────────────────────
    def _repo_date(repo: dict) -> str | None:
        for key in ("date", "created_at", "created", "pushed_at", "updated_at"):
            val = repo.get(key)
            if isinstance(val, str) and val.strip():
                return val[:10] if len(val) >= 10 else val
        return None

    timeline_window = normalize_timeline_window(
        [{"date": _repo_date(r)} for r in repos if isinstance(r, dict) and _repo_date(r)],
        {"account_created": metrics.get("account_created"), "repos": repos, "contributions_monthly": monthly},
        fallback_days=365,
    )
    daily_series = contributions_monthly_to_daily_series(monthly, reference_year=timeline_window[1].year)
    sorted_daily = sorted(daily_series.items(), key=lambda kv: kv[0])
    total_daily = sum(max(0, int(v)) for _, v in sorted_daily)

    def _date_for_activity_fraction(frac: float) -> str:
        frac = max(0.0, min(1.0, frac))
        if total_daily <= 0 or not sorted_daily:
            start, end = timeline_window
            span = max((end - start).days, 1)
            return (start + timedelta(days=int(round(frac * span)))).isoformat()
        threshold = frac * total_daily
        running = 0.0
        for day, count in sorted_daily:
            running += max(0, int(count))
            if running >= threshold:
                return day
        return sorted_daily[-1][0]

    def _timeline_style(when: str, opacity: float, cls: str = "tl-reveal") -> str:
        if not timeline_enabled:
            return f'opacity="{opacity:.2f}"'
        delay = map_date_to_loop_delay(when, timeline_window, duration=loop_duration, reveal_fraction=reveal_fraction)
        return (
            f'class="{cls}" '
            f'style="--delay:{delay:.3f}s;--to:{max(0.0, min(1.0, opacity)):.3f};'
            f'--dur:{loop_duration:.2f}s" data-delay="{delay:.3f}" data-when="{when}"'
        )

    # ── Data mappings ─────────────────────────────────────────────
    grid = config.grid_resolution
    cell_w = WIDTH / grid
    cell_h = HEIGHT / grid

    # Food sources: repos mapped to grid positions
    food_sources: list[tuple[int, int, float]] = []
    food_canvas: list[tuple[float, float, float, dict]] = []  # (cx, cy, conc, repo)
    for repo in primary_repos:
        cx, cy = repo_to_canvas_position(repo, h, strategy="language_cluster")
        repo_stars = int(repo.get("stars", 0) or 0)
        conc = config.food_base + config.food_scale * math.log1p(repo_stars)
        gx = int(min(grid - 1, max(0, cx / cell_w)))
        gy = int(min(grid - 1, max(0, cy / cell_h)))
        food_sources.append((gx, gy, conc))
        food_canvas.append((cx, cy, conc, repo))

    # Agent count from contributions
    n_agents = int(config.agent_base + config.agent_scale * math.log1p(contributions))
    n_agents = max(50, min(2000, n_agents))

    # Evaporation: high energy = slow evaporation = thicker network
    evap = config.evaporation * max(0.3, 1.0 - world.energy * 0.7)

    # Simulation steps from maturity
    sim_steps = int(config.sim_steps_base + config.sim_steps_scale * growth_mat)

    # Speed multiplier from tempo
    speed_mult = max(0.5, 0.8 + tempo * 0.6)

    # ── Run simulation ────────────────────────────────────────────
    trail = _run_simulation(
        grid,
        food_sources,
        n_agents=n_agents,
        steps=sim_steps,
        config=config,
        rng=rng,
        evaporation_rate=evap,
        speed_mult=speed_mult,
    )

    # Normalize trail to [0, 1]
    t_max = trail.max()
    if t_max > 0:
        trail /= t_max

    # ── Physarum palette ──────────────────────────────────────────
    anchors = ART_PALETTE_ANCHORS["physarum"]
    vein_colors = oklch_gradient(anchors, config.contour_levels)

    # ══════════════════════════════════════════════════════════════
    # BUILD SVG
    # ══════════════════════════════════════════════════════════════
    P: list[str] = []
    budget = ElementBudget(config.max_elements)

    P.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {WIDTH} {HEIGHT}" width="{WIDTH}" height="{HEIGHT}">'
    )

    # ── Timeline CSS ──────────────────────────────────────────────
    if timeline_enabled:
        P.append(
            "<style>"
            "@keyframes physReveal{0%{opacity:0}100%{opacity:var(--to,1)}}"
            ".tl-reveal{opacity:0;animation:physReveal .8s ease-out var(--delay,0s) both}"
            ".tl-soft{animation-duration:1.15s}"
            ".tl-crisp{animation-duration:.65s}"
            "</style>"
        )

    # ── Defs: filters ─────────────────────────────────────────────
    P.append("<defs>")
    P.append(volumetric_glow_filter("veinGlow", radius=4.0))
    P.append(volumetric_glow_filter("nodeGlow", radius=6.0))
    P.append("</defs>")

    # ── Background substrate ──────────────────────────────────────
    P.append(f'<rect width="{WIDTH}" height="{HEIGHT}" fill="{_BG_COLOR}"/>')
    budget.add(1)

    # ── Maturity 0: single spore dot ──────────────────────────────
    spore_fade = _fade(0.0, 0.05)
    if spore_fade > 0:
        spore_color = oklch(0.55, 0.14, 90)
        spore_when = _date_for_activity_fraction(0.0)
        P.append(
            f'<circle cx="{WIDTH / 2:.1f}" cy="{HEIGHT / 2:.1f}" r="{2 + spore_fade * 3:.1f}" '
            f'fill="{spore_color}" filter="url(#nodeGlow)" '
            f'{_timeline_style(spore_when, 0.8 * spore_fade, "tl-reveal tl-soft")}/>'
        )
        budget.add(1)

    # ── Ghost traces of pruned paths (maturity > 0.7) ─────────────
    ghost_fade = _fade(0.70, 1.0)
    ghost_color = oklch(0.20, 0.04, 250)

    # ── Vein contours ─────────────────────────────────────────────
    vein_fade = _fade(0.05, 0.50)
    if vein_fade > 0 and t_max > 0:
        # Compute contour thresholds spread across the trail range
        levels = [
            (i + 1) / (config.contour_levels + 1)
            for i in range(config.contour_levels)
        ]

        for li, level in enumerate(levels):
            if not budget.ok():
                break

            chains = _extract_contours(trail, grid, level, cell_w, cell_h)

            # Stroke width: thick for high concentration, thin for low
            base_sw = 0.5 + (level * 3.5) * vein_fade
            color = vein_colors[li]
            opacity = 0.3 + level * 0.55

            # Ghost traces: faint contours at lowest levels when mature
            is_ghost = li < 2 and ghost_fade > 0
            if is_ghost:
                draw_color = oklch_lerp(ghost_color, color, 0.3)
                draw_opacity = opacity * 0.25 * ghost_fade
                draw_sw = base_sw * 0.6
            else:
                draw_color = color
                draw_opacity = opacity * vein_fade
                draw_sw = base_sw

            filt = ' filter="url(#veinGlow)"' if li >= config.contour_levels // 2 else ""
            frac_for_level = 0.1 + li * 0.12
            when = _date_for_activity_fraction(min(1.0, frac_for_level))

            for chain in chains:
                if not budget.ok():
                    break
                smoothed = _chaikin_smooth(chain, iterations=1)
                pd = _path_d(smoothed)
                P.append(
                    f'<path d="{pd}" fill="none" stroke="{draw_color}" '
                    f'stroke-width="{draw_sw:.2f}" stroke-linecap="round" '
                    f'stroke-linejoin="round"{filt} '
                    f'{_timeline_style(when, draw_opacity, "tl-reveal tl-crisp")}/>'
                )
                budget.add(1)

    # ── Food source nodes ─────────────────────────────────────────
    node_fade = _fade(0.10, 0.40)
    if node_fade > 0:
        bright_gold = oklch(0.82, 0.16, 55)
        for cx, cy, conc, repo in food_canvas:
            if not budget.ok():
                break
            r = 3.0 + math.log1p(conc) * 1.5
            node_when = _repo_date(repo) or _date_for_activity_fraction(0.3)
            # Outer glow ring
            P.append(
                f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r * 1.8:.1f}" '
                f'fill="{oklch(0.55, 0.12, 60)}" filter="url(#nodeGlow)" '
                f'{_timeline_style(node_when, 0.3 * node_fade, "tl-reveal tl-soft")}/>'
            )
            budget.add(1)
            # Inner bright node
            P.append(
                f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" '
                f'fill="{bright_gold}" filter="url(#nodeGlow)" '
                f'{_timeline_style(node_when, 0.85 * node_fade, "tl-reveal tl-crisp")}/>'
            )
            budget.add(1)

            # Repo name label
            label = repo.get("name", "")
            if label and node_fade > 0.5:
                P.append(
                    f'<text x="{cx:.1f}" y="{cy + r + 8:.1f}" '
                    f'font-family="monospace" font-size="6" fill="{oklch(0.70, 0.06, 55)}" '
                    f'text-anchor="middle" '
                    f'{_timeline_style(node_when, 0.5 * node_fade, "tl-reveal tl-soft")}>'
                    f'{label}</text>'
                )
                budget.add(1)

    P.append("</svg>")
    return "\n".join(P)
