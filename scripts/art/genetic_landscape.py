"""
Genetic Landscape — Evolutionary fitness landscape generative art.

GitHub repos become fitness peaks on a terrain. A population of organisms
evolves on the landscape, adapting to peaks over generations tied to maturity.
Contour lines reveal terrain shape; colored organisms cluster near peaks.
"""

# ruff: noqa: E501

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import timedelta
from typing import Any

import numpy as np

from .optimize import optimize_placement, optimize_palette_hues
from .shared import (
    HEIGHT,
    LANG_HUES,
    MAX_REPOS,
    WIDTH,
    DerivedMetrics,
    ElementBudget,
    Noise2D,
    WorldState,
    _build_world_palette_extended,
    activity_tempo,
    atmospheric_haze_filter,
    compute_derived_metrics,
    compute_maturity,
    compute_world_state,
    hex_frac,
    map_date_to_loop_delay,
    normalize_timeline_window,
    oklch,
    oklch_gradient,
    oklch_lerp,
    organic_texture_filter,
    repo_to_canvas_position,
    repo_visibility_score,
    seed_hash,
    select_palette_for_world,
    select_primary_repos,
    topic_affinity_matrix,
    visual_complexity,
)

# ── Margins ──────────────────────────────────────────────────────────────

_PAD = 40
_MAP_L, _MAP_T = _PAD, _PAD
_MAP_R, _MAP_B = WIDTH - _PAD, HEIGHT - _PAD
_MAP_W = _MAP_R - _MAP_L
_MAP_H = _MAP_B - _MAP_T


# ── Config ───────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class GeneticLandscapeConfig:
    """Tunable parameters for the genetic landscape artwork."""

    max_repos: int = 10
    max_elements: int = 25000
    grid_resolution: int = 60
    contour_levels: int = 12
    peak_scale: float = 8.0
    pop_base: int = 30
    pop_scale: float = 15.0
    speciation_scale: float = 0.5
    trail_opacity: float = 0.3


CFG = GeneticLandscapeConfig()


# ── Grid helpers ─────────────────────────────────────────────────────────


def _grid_to_canvas(
    gx: float, gy: float, cell_w: float, cell_h: float
) -> tuple[float, float]:
    """Convert grid coordinates to canvas pixel coordinates."""
    return _MAP_L + gx * cell_w, _MAP_T + gy * cell_h


def _gaussian(x: float, y: float, cx: float, cy: float, sigma: float) -> float:
    """2D Gaussian bump centered at (cx, cy)."""
    dx = x - cx
    dy = y - cy
    return math.exp(-(dx * dx + dy * dy) / (2.0 * sigma * sigma))


# ── Marching squares contour extraction ──────────────────────────────────


def _extract_contours(
    elevation: np.ndarray,
    grid: int,
    level: float,
    cell_w: float,
    cell_h: float,
) -> list[list[tuple[float, float]]]:
    """Extract iso-contour polylines at *level* using marching squares."""
    segments: list[tuple[tuple[float, float], tuple[float, float]]] = []
    for gy in range(grid - 1):
        for gx in range(grid - 1):
            tl = float(elevation[gy, gx])
            tr = float(elevation[gy, gx + 1])
            bl = float(elevation[gy + 1, gx])
            br = float(elevation[gy + 1, gx + 1])
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
                segments.append((edges[0], edges[1]))

    if not segments:
        return []

    # Chain segments into polylines
    used = [False] * len(segments)
    chains: list[list[tuple[float, float]]] = []
    for si in range(len(segments)):
        if used[si]:
            continue
        used[si] = True
        chain = [segments[si][0], segments[si][1]]
        changed = True
        while changed:
            changed = False
            last = chain[-1]
            best_d, best_j, best_end = 8.0, -1, 0
            for j in range(len(segments)):
                if used[j]:
                    continue
                for end_idx in (0, 1):
                    pt = segments[j][end_idx]
                    d = math.hypot(pt[0] - last[0], pt[1] - last[1])
                    if d < best_d:
                        best_d, best_j, best_end = d, j, end_idx
            if best_j >= 0:
                used[best_j] = True
                chain.append(
                    segments[best_j][1 - best_end]
                    if best_end == 0
                    else segments[best_j][0]
                )
                changed = True
        if len(chain) >= 3:
            chains.append(chain)
    return chains


# ── Organism simulation ──────────────────────────────────────────────────


def _simulate_population(
    peaks: list[tuple[float, float, float]],
    elevation: np.ndarray,
    grid: int,
    cell_w: float,
    cell_h: float,
    rng: np.random.Generator,
    pop_count: int,
    generations: int,
    mutation_rate: float,
) -> list[tuple[float, float, list[tuple[float, float]]]]:
    """Simulate organisms evolving on the fitness landscape.

    Returns list of (x, y, trail) for each surviving organism.
    """
    if pop_count <= 0 or not peaks:
        return []

    # Initialize population randomly within canvas bounds
    xs = rng.uniform(_MAP_L + 10, _MAP_R - 10, pop_count).astype(np.float64)
    ys = rng.uniform(_MAP_T + 10, _MAP_B - 10, pop_count).astype(np.float64)
    trails: list[list[tuple[float, float]]] = [
        [(float(xs[i]), float(ys[i]))] for i in range(pop_count)
    ]

    # Pre-compute peak positions for fitness evaluation
    peak_xs = np.array([p[0] for p in peaks])
    peak_ys = np.array([p[1] for p in peaks])
    peak_heights = np.array([p[2] for p in peaks])

    for _gen in range(generations):
        # Evaluate fitness: proximity to weighted peaks
        fitness = np.zeros(pop_count)
        for pi in range(len(peaks)):
            dist = np.sqrt((xs - peak_xs[pi]) ** 2 + (ys - peak_ys[pi]) ** 2)
            fitness += peak_heights[pi] / (1.0 + dist * 0.01)

        # Selection: keep top 60%, replace bottom 40% with offspring
        cutoff = max(1, int(pop_count * 0.6))
        order = np.argsort(-fitness)
        survivors = order[:cutoff]

        # Repopulate from survivors
        for idx in order[cutoff:]:
            parent = survivors[rng.integers(0, cutoff)]
            xs[idx] = xs[parent] + rng.normal(0, mutation_rate * _MAP_W * 0.05)
            ys[idx] = ys[parent] + rng.normal(0, mutation_rate * _MAP_H * 0.05)

        # Mutate all organisms slightly (gradient ascent + noise)
        xs += rng.normal(0, mutation_rate * 3.0, pop_count)
        ys += rng.normal(0, mutation_rate * 3.0, pop_count)

        # Clamp to canvas
        np.clip(xs, _MAP_L + 5, _MAP_R - 5, out=xs)
        np.clip(ys, _MAP_T + 5, _MAP_B - 5, out=ys)

        # Record trail
        for i in range(pop_count):
            trails[i].append((float(xs[i]), float(ys[i])))

    return [(float(xs[i]), float(ys[i]), trails[i]) for i in range(pop_count)]


# ── Main generate ────────────────────────────────────────────────────────


def generate(
    metrics: dict,
    *,
    seed: str | None = None,
    maturity: float | None = None,
    timeline: bool = True,
    loop_duration: float = 60.0,
    reveal_fraction: float = 0.93,
) -> str:
    """Render an evolutionary fitness landscape as SVG.

    Parameters
    ----------
    metrics:
        GitHub metrics dict (repos, stars, contributions, etc.).
    seed:
        Optional deterministic seed string.
    maturity:
        Override ecosystem maturity (0.0-1.0). Auto-computed if *None*.
    timeline:
        Enable CSS reveal animation keyed to repo creation dates.
    loop_duration:
        Total animation loop length in seconds.
    reveal_fraction:
        Fraction of loop_duration used for the reveal phase.
    """
    mat = maturity if maturity is not None else compute_maturity(metrics)
    timeline_enabled = bool(timeline and loop_duration > 0)
    growth_mat = 1.0 if timeline_enabled else mat

    # ── WorldState: coherent atmosphere across all artworks ────────
    world: WorldState = compute_world_state(metrics)

    # ── OKLCH palette & complexity ────────────────────────────────
    select_palette_for_world(world)
    pal = _build_world_palette_extended(
        world.time_of_day,
        world.weather,
        world.season,
        world.energy,
    )
    complexity = visual_complexity(metrics)

    def _fade(start: float, full: float) -> float:
        """Smooth 0-1 ramp between start and full maturity."""
        return max(0.0, min(1.0, (growth_mat - start) / max(0.001, full - start)))

    h = seed_hash({"seed": seed}) if seed is not None else seed_hash(metrics)
    rng = np.random.default_rng(int(h[:8], 16))
    noise = Noise2D(seed=int(h[8:16], 16))

    repos = metrics.get("repos", [])
    primary_repos, _overflow = select_primary_repos(repos, limit=CFG.max_repos)
    derived: DerivedMetrics = compute_derived_metrics(metrics)
    tempo = activity_tempo(metrics.get("contributions_monthly"))
    affinities = topic_affinity_matrix(primary_repos)

    # ── Timeline window ───────────────────────────────────────────
    def _repo_date(repo: dict) -> str | None:
        for key in ("date", "created_at", "pushed_at", "updated_at"):
            val = repo.get(key)
            if isinstance(val, str) and len(val) >= 10:
                return val[:10]
        return None

    timeline_window = normalize_timeline_window(
        [
            {"date": _repo_date(r)}
            for r in repos
            if isinstance(r, dict) and _repo_date(r)
        ],
        {
            "account_created": metrics.get("account_created"),
            "repos": repos,
            "contributions_monthly": metrics.get("contributions_monthly", {}),
        },
        fallback_days=365,
    )

    def _timeline_style(when: str, opacity: float, cls: str = "tl-reveal") -> str:
        if not timeline_enabled:
            return f'opacity="{opacity:.2f}"'
        delay = map_date_to_loop_delay(
            when,
            timeline_window,
            duration=loop_duration,
            reveal_fraction=reveal_fraction,
        )
        return (
            f'class="{cls}" '
            f'style="--delay:{delay:.3f}s;--to:{max(0.0, min(1.0, opacity)):.3f};'
            f'--dur:{loop_duration:.2f}s" data-delay="{delay:.3f}" data-when="{when}"'
        )

    budget = ElementBudget(CFG.max_elements)

    # ── Build elevation grid ──────────────────────────────────────
    grid = CFG.grid_resolution
    cell_w = _MAP_W / grid
    cell_h = _MAP_H / grid
    elevation = np.zeros((grid, grid), dtype=np.float64)

    # Base terrain noise (contributions drive octave count)
    total_commits = metrics.get("total_commits", 500)
    terrain_oct = max(2, min(5, 2 + total_commits // 8000))
    for gy in range(grid):
        for gx in range(grid):
            elevation[gy, gx] = (
                noise.fbm(gx / grid * 4.0, gy / grid * 4.0, terrain_oct) * 0.04
            )

    # ── Repo peaks ────────────────────────────────────────────────
    # Get initial positions via shared utility
    initial_positions = [
        repo_to_canvas_position(
            r, h, _MAP_W, _MAP_H, strategy="language_cluster", jitter=0.2
        )
        for r in primary_repos
    ]
    # Remap from (0..MAP_W, 0..MAP_H) to canvas coords
    initial_positions = [(_MAP_L + x, _MAP_T + y) for x, y in initial_positions]
    weights = [math.log1p(r.get("stars", 0)) + 1.0 for r in primary_repos]

    # Optimize placement to avoid overlap
    if len(initial_positions) >= 2:
        optimized_positions = optimize_placement(
            initial_positions,
            weights,
            float(WIDTH),
            float(HEIGHT),
            min_spacing=70.0,
            seed=int(h[:8], 16),
        )
    else:
        optimized_positions = list(initial_positions)

    # Optimize palette hues for harmony
    base_hues = [float(LANG_HUES.get(r.get("language"), 155)) for r in primary_repos]
    if len(base_hues) >= 2:
        opt_hues = optimize_palette_hues(base_hues, seed=int(h[:8], 16))
    else:
        opt_hues = list(base_hues)

    # Add Gaussian peaks to elevation
    peaks: list[
        tuple[float, float, float, str, dict]
    ] = []  # (cx, cy, height, color, repo)
    repo_count_visible = max(1, int(len(primary_repos) * _fade(0.0, 0.5)))

    for ri in range(min(repo_count_visible, len(primary_repos))):
        repo = primary_repos[ri]
        px, py = (
            optimized_positions[ri]
            if ri < len(optimized_positions)
            else (_MAP_L + _MAP_W / 2, _MAP_T + _MAP_H / 2)
        )
        stars = repo.get("stars", 0)
        peak_h = math.log1p(stars) * CFG.peak_scale
        hue = opt_hues[ri] if ri < len(opt_hues) else 155.0
        color = oklch(0.65, 0.14, hue)
        sigma_grid = max(3.0, 2.0 + math.log1p(stars) * 0.8)

        # Convert canvas position to grid position
        gpx = (px - _MAP_L) / cell_w
        gpy = (py - _MAP_T) / cell_h

        for gy in range(grid):
            for gx in range(grid):
                elevation[gy, gx] += peak_h * _gaussian(gx, gy, gpx, gpy, sigma_grid)

        peaks.append((px, py, peak_h, color, repo))

    # Add saddle ridges between topic-related repos
    ridge_fade = _fade(0.3, 0.7)
    if ridge_fade > 0:
        for (i, j), affinity in affinities.items():
            if i >= len(peaks) or j >= len(peaks):
                continue
            p1 = peaks[i]
            p2 = peaks[j]
            gx1, gy1 = (p1[0] - _MAP_L) / cell_w, (p1[1] - _MAP_T) / cell_h
            gx2, gy2 = (p2[0] - _MAP_L) / cell_w, (p2[1] - _MAP_T) / cell_h
            ridge_h = min(p1[2], p2[2]) * affinity * 0.3 * ridge_fade
            for gy in range(grid):
                for gx in range(grid):
                    # Distance to line segment between peaks
                    dx, dy = gx2 - gx1, gy2 - gy1
                    seg_len_sq = dx * dx + dy * dy
                    if seg_len_sq < 0.01:
                        continue
                    t = max(
                        0.0, min(1.0, ((gx - gx1) * dx + (gy - gy1) * dy) / seg_len_sq)
                    )
                    proj_x = gx1 + t * dx
                    proj_y = gy1 + t * dy
                    dist = math.hypot(gx - proj_x, gy - proj_y)
                    elevation[gy, gx] += ridge_h * math.exp(-dist * dist / 8.0)

    # Normalize elevation for contour extraction
    e_min = float(elevation.min())
    e_max = float(elevation.max())
    e_range = max(e_max - e_min, 0.001)

    # ── Organism simulation ───────────────────────────────────────
    generations = max(1, int(mat * 20))
    pop_count = int(CFG.pop_base + mat * CFG.pop_scale)
    mutation_rate = max(0.1, 1.0 - mat * 0.6) * (0.5 + tempo * 0.5)

    peak_data = [(p[0], p[1], p[2]) for p in peaks]
    organisms = _simulate_population(
        peak_data,
        elevation,
        grid,
        cell_w,
        cell_h,
        rng,
        pop_count,
        generations,
        mutation_rate,
    )

    # ── SVG output ────────────────────────────────────────────────
    P: list[str] = []
    P.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" '
        f'width="{WIDTH}" height="{HEIGHT}" '
        f'data-maturity="{mat:.3f}" data-tempo="{tempo:.3f}">'
    )

    if timeline_enabled:
        P.append(
            "<style>"
            "@keyframes glReveal{0%{opacity:0}100%{opacity:var(--to,1)}}"
            ".tl-reveal{opacity:0;animation:glReveal .8s ease-out var(--delay,0s) both}"
            ".tl-soft{animation-duration:1.15s}"
            "</style>"
        )

    P.append("<defs>")
    P.append(atmospheric_haze_filter("glHaze", intensity=0.3))
    P.append(
        organic_texture_filter("glTexture", "cloud", intensity=0.2, seed=int(h[:4], 16))
    )
    P.append("</defs>")

    # ── Background ────────────────────────────────────────────────
    bg = pal.get("bg_primary", pal.get("sky_top", "#1a1a2e"))
    P.append(f'<rect width="{WIDTH}" height="{HEIGHT}" fill="{bg}"/>')
    budget.add(1)

    # Subtle texture overlay
    P.append(
        f'<rect width="{WIDTH}" height="{HEIGHT}" filter="url(#glTexture)" opacity="0.08"/>'
    )
    budget.add(1)

    # ── Contour lines ─────────────────────────────────────────────
    contour_colors = oklch_gradient(
        [(0.35, 0.04, 220), (0.50, 0.06, 180), (0.65, 0.08, 140), (0.80, 0.10, 80)],
        CFG.contour_levels,
    )

    contour_fade = _fade(0.05, 0.4)
    start_date = timeline_window[0].isoformat()
    for li in range(CFG.contour_levels):
        if not budget.ok():
            break
        level = e_min + (li + 1) * e_range / (CFG.contour_levels + 1)
        chains = _extract_contours(elevation, grid, level, cell_w, cell_h)
        is_index = li % 4 == 3
        sw = 1.0 if is_index else 0.4
        color = contour_colors[li % len(contour_colors)]
        opacity = (0.6 if is_index else 0.35) * contour_fade

        contour_frac = (li + 1) / (CFG.contour_levels + 1)
        contour_when = (
            timeline_window[0]
            + timedelta(
                days=int(
                    contour_frac
                    * max((timeline_window[1] - timeline_window[0]).days, 1)
                )
            )
        ).isoformat()

        for chain in chains:
            if not budget.ok():
                break
            if len(chain) < 3:
                continue
            d = f"M{chain[0][0]:.1f},{chain[0][1]:.1f}"
            for pt in chain[1:]:
                d += f"L{pt[0]:.1f},{pt[1]:.1f}"
            P.append(
                f'<path d="{d}" fill="none" stroke="{color}" '
                f'stroke-width="{sw:.2f}" stroke-linecap="round" stroke-linejoin="round" '
                f"{_timeline_style(contour_when, opacity)}/>"
            )
            budget.add(1)

    # ── Peak markers & glow ───────────────────────────────────────
    peak_fade = _fade(0.15, 0.6)
    for pi, (px, py, ph, color, repo) in enumerate(peaks):
        if not budget.ok():
            break
        peak_when = _repo_date(repo) or start_date
        r_glow = max(8.0, min(40.0, ph * 1.5))
        r_core = max(3.0, min(12.0, ph * 0.5))

        # Glow
        P.append(
            f'<circle cx="{px:.1f}" cy="{py:.1f}" r="{r_glow:.1f}" '
            f'fill="{color}" filter="url(#glHaze)" '
            f"{_timeline_style(peak_when, 0.25 * peak_fade)}/>"
        )
        budget.add(1)

        # Core
        P.append(
            f'<circle cx="{px:.1f}" cy="{py:.1f}" r="{r_core:.1f}" '
            f'fill="{color}" '
            f"{_timeline_style(peak_when, 0.8 * peak_fade)}/>"
        )
        budget.add(1)

    # ── Organism trails ───────────────────────────────────────────
    trail_fade = _fade(0.3, 0.8)
    if trail_fade > 0 and organisms:
        # Assign organisms to nearest peak for coloring
        for ox, oy, trail in organisms:
            if not budget.ok() or len(trail) < 3:
                continue
            # Find nearest peak
            best_pi = 0
            best_dist = float("inf")
            for pi, (px, py, _, _, _) in enumerate(peaks):
                d = math.hypot(ox - px, oy - py)
                if d < best_dist:
                    best_dist = d
                    best_pi = pi

            trail_color = peaks[best_pi][3] if peaks else pal.get("accent", "#888888")
            # Thin trail path
            td = f"M{trail[0][0]:.1f},{trail[0][1]:.1f}"
            step = max(1, len(trail) // 8)
            for ti in range(step, len(trail), step):
                td += f"L{trail[ti][0]:.1f},{trail[ti][1]:.1f}"
            P.append(
                f'<path d="{td}" fill="none" stroke="{trail_color}" '
                f'stroke-width="0.4" stroke-linecap="round" '
                f'opacity="{CFG.trail_opacity * trail_fade:.3f}"/>'
            )
            budget.add(1)

    # ── Organism dots ─────────────────────────────────────────────
    org_fade = _fade(0.15, 0.5)
    if org_fade > 0 and organisms:
        mid_date = (
            timeline_window[0]
            + timedelta(
                days=max((timeline_window[1] - timeline_window[0]).days, 1) // 2
            )
        ).isoformat()

        for ox, oy, trail in organisms:
            if not budget.ok():
                break
            # Nearest peak for color
            best_pi = 0
            best_dist = float("inf")
            for pi, (px, py, _, _, _) in enumerate(peaks):
                d = math.hypot(ox - px, oy - py)
                if d < best_dist:
                    best_dist = d
                    best_pi = pi

            dot_color = peaks[best_pi][3] if peaks else "#aaaaaa"
            r = 1.2 + rng.uniform(0, 0.8)
            P.append(
                f'<circle cx="{ox:.1f}" cy="{oy:.1f}" r="{r:.1f}" '
                f'fill="{dot_color}" '
                f"{_timeline_style(mid_date, 0.7 * org_fade, 'tl-reveal tl-soft')}/>"
            )
            budget.add(1)

    # ── Annotations (repo names near peaks at high maturity) ──────
    label_fade = _fade(0.6, 0.95)
    if label_fade > 0:
        text_color = pal.get("text_primary", pal.get("accent", "#cccccc"))
        for pi, (px, py, ph, color, repo) in enumerate(peaks):
            if not budget.ok():
                break
            name = repo.get("name", "")
            if not name:
                continue
            peak_when = _repo_date(repo) or start_date
            # Truncate long names
            label = name[:18] + ("\u2026" if len(name) > 18 else "")
            stars = repo.get("stars", 0)
            lang = repo.get("language", "")

            # Position label above peak
            lx = px
            ly = py - max(6.0, ph * 0.5) - 6
            ly = max(_MAP_T + 10, ly)

            # Background halo for readability
            P.append(
                f'<text x="{lx:.0f}" y="{ly:.0f}" '
                f'font-family="monospace" font-size="7" text-anchor="middle" '
                f'fill="{bg}" stroke="{bg}" stroke-width="2.5" stroke-linejoin="round" '
                f'paint-order="stroke fill" '
                f"{_timeline_style(peak_when, 0.6 * label_fade, 'tl-reveal tl-soft')}>"
                f"{label}</text>"
            )
            budget.add(1)
            # Foreground text
            P.append(
                f'<text x="{lx:.0f}" y="{ly:.0f}" '
                f'font-family="monospace" font-size="7" text-anchor="middle" '
                f'fill="{color}" '
                f"{_timeline_style(peak_when, 0.85 * label_fade, 'tl-reveal tl-soft')}>"
                f"{label}</text>"
            )
            budget.add(1)

            # Star count sub-label
            if stars > 0:
                P.append(
                    f'<text x="{lx:.0f}" y="{ly + 9:.0f}" '
                    f'font-family="monospace" font-size="5" text-anchor="middle" '
                    f'fill="{text_color}" '
                    f"{_timeline_style(peak_when, 0.5 * label_fade, 'tl-reveal tl-soft')}>"
                    f"\u2605 {stars}</text>"
                )
                budget.add(1)

    P.append("</svg>")
    return "\n".join(P)
