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
from datetime import date, timedelta
from typing import Any

import numpy as np

from .optimize import optimize_palette_hues, optimize_placement
from .shared import (
    HEIGHT,
    LANG_HUES,
    WIDTH,
    ElementBudget,
    Noise2D,
    WorldState,
    _build_world_palette_extended,
    activity_tempo,
    atmospheric_haze_filter,
    compute_maturity,
    compute_world_state,
    contributions_monthly_to_daily_series,
    hex_frac,
    map_date_to_loop_delay,
    normalize_timeline_window,
    oklch,
    oklch_gradient,
    order_repos_for_visual_plan,
    organic_texture_filter,
    repo_to_canvas_position,
    repo_visibility_score,
    seed_hash,
    select_palette_for_world,
    select_primary_repos,
    topic_affinity_matrix,
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


@dataclass(frozen=True)
class _LandscapeDynamics:
    """Deterministic simulation controls derived from GitHub snapshot signals."""

    generations: int
    pop_count: int
    mutation_rate: float
    ridge_intensity: float


def _as_non_negative_int(value: Any) -> int:
    """Coerce scalar-like values into a safe non-negative integer."""
    try:
        return max(0, int(value or 0))
    except (TypeError, ValueError):
        return 0


def _as_non_negative_float(value: Any) -> float:
    """Coerce scalar-like values into a safe non-negative float."""
    try:
        return max(0.0, float(value or 0.0))
    except (TypeError, ValueError):
        return 0.0


def _dense_repo_signal(repo_count: int, *, baseline: int) -> float:
    """Return a soft repo-density signal that keeps rising beyond the baseline."""
    if repo_count <= 0:
        return 0.0
    return min(1.0, math.log1p(repo_count) / math.log1p(max(2, baseline * 4)))


def _repo_growth_profile(metrics: dict[str, Any]) -> tuple[float, float]:
    """Return growth and legacy shares from recency bands or repo ages."""
    recency_bands = metrics.get("repo_recency_bands")
    if isinstance(recency_bands, dict) and any(recency_bands.values()):
        total = sum(_as_non_negative_int(value) for value in recency_bands.values())
        if total > 0:
            growth_share = (
                _as_non_negative_int(recency_bands.get("fresh", 0))
                + _as_non_negative_int(recency_bands.get("recent", 0))
            ) / total
            legacy_share = _as_non_negative_int(recency_bands.get("legacy", 0)) / total
            return growth_share, legacy_share

    repos = metrics.get("repos", [])
    ages = [
        _as_non_negative_int(repo.get("age_months", 0))
        for repo in repos
        if isinstance(repo, dict)
    ]
    ages = [age for age in ages if age > 0]
    if not ages:
        return 0.0, 0.0
    growth_weights = [max(0.0, 1.0 - age / 24.0) for age in ages]
    legacy_weights = [min(1.0, age / 48.0) for age in ages]
    return (
        sum(growth_weights) / len(growth_weights),
        sum(legacy_weights) / len(legacy_weights),
    )


def _repo_establishment_signal(repo: dict[str, Any], *, max_repo_age: int) -> float:
    """Estimate how much settled terrain a repo should imprint on the map."""
    age_months = _as_non_negative_int(repo.get("age_months", 0))
    if age_months <= 0:
        return 0.0
    absolute_age = min(1.0, age_months / 48.0)
    relative_age = age_months / max(1, max_repo_age)
    return min(1.0, absolute_age * 0.65 + relative_age * 0.35)


def _repo_peak_profile(
    repo: dict[str, Any], *, max_repo_age: int
) -> tuple[float, float, float, float]:
    """Return peak height plus narrow and broad terrain envelopes for a repo."""
    stars = _as_non_negative_int(repo.get("stars", 0))
    prominence = math.log1p(stars)
    establishedness = _repo_establishment_signal(repo, max_repo_age=max_repo_age)

    peak_h = max(1.6, prominence * CFG.peak_scale)
    sigma_grid = max(3.2, 2.4 + prominence * 0.65 + establishedness * 4.0)
    terrace_height = peak_h * (0.12 + establishedness * 0.38)
    terrace_sigma = sigma_grid * (1.9 + establishedness * 0.8)
    return peak_h, sigma_grid, terrace_height, terrace_sigma


def _derive_landscape_dynamics(
    metrics: dict[str, Any],
    *,
    maturity: float,
    tempo: float,
) -> _LandscapeDynamics:
    """Map cumulative GitHub activity signals onto simulation parameters."""
    streaks = metrics.get("contribution_streaks", {})
    current_streak = (
        _as_non_negative_int(streaks.get("current_streak_months", 0))
        if isinstance(streaks, dict)
        else 0
    )
    longest_streak = (
        max(
            current_streak,
            _as_non_negative_int(streaks.get("longest_streak_months", current_streak)),
        )
        if isinstance(streaks, dict)
        else current_streak
    )
    streak_signal = current_streak / max(1, longest_streak)
    streak_active = (
        bool(streaks.get("streak_active", False))
        if isinstance(streaks, dict)
        else False
    )

    star_velocity = metrics.get("star_velocity", {})
    recent_rate = (
        _as_non_negative_float(star_velocity.get("recent_rate", 0.0))
        if isinstance(star_velocity, dict)
        else 0.0
    )
    peak_rate = (
        max(1.0, _as_non_negative_float(star_velocity.get("peak_rate", 0.0)))
        if isinstance(star_velocity, dict)
        else 1.0
    )
    star_signal = min(1.0, recent_rate / peak_rate)
    trend = (
        str(star_velocity.get("trend", "stable") or "stable").lower()
        if isinstance(star_velocity, dict)
        else "stable"
    )
    if trend == "rising":
        star_signal = (star_signal + 1.0) / 2.0
    elif trend == "falling":
        star_signal /= 2.0

    recent_merged_prs = metrics.get("recent_merged_prs", [])
    releases = metrics.get("releases", [])
    repo_total = max(
        1,
        sum(
            _as_non_negative_int(value)
            for value in (metrics.get("repo_recency_bands") or {}).values()
        )
        or len(metrics.get("repos", []))
        or 1,
    )
    pr_signal = (
        min(1.0, len(recent_merged_prs) / repo_total)
        if isinstance(recent_merged_prs, list)
        else 0.0
    )
    release_signal = (
        len(releases) / max(1, len(recent_merged_prs) + len(releases))
        if isinstance(releases, list) and isinstance(recent_merged_prs, list)
        else 0.0
    )

    issue_stats = metrics.get("issue_stats", {})
    open_issues = (
        _as_non_negative_int(
            issue_stats.get("open_count", metrics.get("open_issues_count", 0))
        )
        if isinstance(issue_stats, dict)
        else _as_non_negative_int(metrics.get("open_issues_count", 0))
    )
    closed_issues = (
        _as_non_negative_int(issue_stats.get("closed_count", 0))
        if isinstance(issue_stats, dict)
        else 0
    )
    issue_resolution = closed_issues / max(1, open_issues + closed_issues)

    growth_share, legacy_share = _repo_growth_profile(metrics)
    repos = metrics.get("repos", [])
    repo_count = len(repos) if isinstance(repos, list) else 0
    repo_signal = _dense_repo_signal(repo_count, baseline=CFG.max_repos)

    raw_daily = metrics.get("contributions_daily", {})
    if isinstance(raw_daily, dict) and raw_daily:
        daily_counts = [_as_non_negative_int(value) for value in raw_daily.values()]
        contribution_total = sum(daily_counts)
        active_day_ratio = sum(1 for count in daily_counts if count > 0) / max(
            1, len(daily_counts)
        )
    else:
        contribution_total = _as_non_negative_int(
            metrics.get("contributions_last_year", 0)
        )
        monthly = metrics.get("contributions_monthly", {})
        if isinstance(monthly, dict) and monthly:
            monthly_counts = [_as_non_negative_int(value) for value in monthly.values()]
            active_day_ratio = sum(1 for count in monthly_counts if count > 0) / max(
                1, len(monthly_counts)
            )
        else:
            active_day_ratio = 0.0
    contribution_signal = min(
        1.0,
        math.log1p(contribution_total) / math.log1p(2400.0),
    )

    traffic_total = sum(
        _as_non_negative_int(metrics.get(key, 0))
        for key in (
            "traffic_views_14d",
            "traffic_unique_visitors_14d",
            "traffic_clones_14d",
            "traffic_unique_cloners_14d",
        )
    )
    traffic_signal = min(1.0, math.log1p(traffic_total) / math.log1p(12000.0))

    activity_parts = [
        max(maturity, streak_signal),
        star_signal,
        growth_share,
        pr_signal,
        contribution_signal,
        active_day_ratio,
    ]
    activity_signal = sum(activity_parts) / len(activity_parts)
    stability_parts = [issue_resolution, release_signal, 1.0 - legacy_share]
    stability_signal = sum(stability_parts) / len(stability_parts)

    base_generations = max(1, int(maturity * 20))
    generations = max(
        1,
        int(
            round(
                base_generations * (1.0 + activity_signal + contribution_signal * 0.35)
            )
        ),
    )

    base_pop_count = CFG.pop_base + maturity * CFG.pop_scale
    pop_signal = (
        sum(
            [
                growth_share,
                pr_signal,
                release_signal,
                contribution_signal,
                repo_signal,
                traffic_signal,
            ]
        )
        / 6.0
    )
    pop_count = max(6, int(round(base_pop_count * (1.0 + pop_signal))))

    base_mutation = max(0.1, 1.0 - maturity * 0.6) * (0.5 + tempo * 0.5)
    mutation_rate = max(
        0.08,
        min(1.2, base_mutation * (1.0 + activity_signal - stability_signal)),
    )

    ridge_signal = (
        sum(
            [
                growth_share,
                pr_signal,
                release_signal,
                issue_resolution,
                contribution_signal,
            ]
        )
        / 5.0
    )
    ridge_intensity = (
        1.0 + ridge_signal + (streak_signal if streak_active else 0.0) / 4.0
    )

    return _LandscapeDynamics(
        generations=generations,
        pop_count=pop_count,
        mutation_rate=mutation_rate,
        ridge_intensity=ridge_intensity,
    )


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

    # Pre-compute peak positions for fitness evaluation
    peak_xs = np.array([p[0] for p in peaks], dtype=np.float64)
    peak_ys = np.array([p[1] for p in peaks], dtype=np.float64)
    peak_heights = np.array([p[2] for p in peaks], dtype=np.float64)
    peak_weight_sum = float(peak_heights.sum())
    peak_probs = (
        peak_heights / peak_weight_sum
        if peak_weight_sum > 0
        else np.full(len(peaks), 1.0 / len(peaks), dtype=np.float64)
    )

    terrain = elevation.astype(np.float64, copy=True)
    terrain -= float(terrain.min())
    terrain_max = float(terrain.max())
    if terrain_max > 0:
        terrain /= terrain_max
    flat_terrain = terrain.ravel()
    if flat_terrain.size and float(flat_terrain.sum()) > 0.0:
        terrain_probs = flat_terrain / float(flat_terrain.sum())
        terrain_indices = rng.choice(flat_terrain.size, size=pop_count, p=terrain_probs)
        terrain_gys, terrain_gxs = np.divmod(terrain_indices, grid)
        terrain_xs = _MAP_L + (terrain_gxs.astype(np.float64) + 0.5) * cell_w
        terrain_ys = _MAP_T + (terrain_gys.astype(np.float64) + 0.5) * cell_h
    else:
        terrain_xs = rng.uniform(_MAP_L + 10, _MAP_R - 10, pop_count).astype(np.float64)
        terrain_ys = rng.uniform(_MAP_T + 10, _MAP_B - 10, pop_count).astype(np.float64)

    anchor_indices = rng.choice(len(peaks), size=pop_count, p=peak_probs)
    anchor_xs = peak_xs[anchor_indices]
    anchor_ys = peak_ys[anchor_indices]
    spawn_focus = 0.68 + 0.18 / (1.0 + generations / 10.0)
    spawn_noise = max(6.0, min(_MAP_W, _MAP_H) * (0.012 + mutation_rate * 0.01))

    xs = (
        spawn_focus * anchor_xs
        + (1.0 - spawn_focus) * terrain_xs
        + rng.normal(0.0, spawn_noise, pop_count)
    )
    ys = (
        spawn_focus * anchor_ys
        + (1.0 - spawn_focus) * terrain_ys
        + rng.normal(0.0, spawn_noise, pop_count)
    )
    np.clip(xs, _MAP_L + 5, _MAP_R - 5, out=xs)
    np.clip(ys, _MAP_T + 5, _MAP_B - 5, out=ys)
    trails: list[list[tuple[float, float]]] = [
        [(float(xs[i]), float(ys[i]))] for i in range(pop_count)
    ]

    if grid >= 2:
        terrain_grad_y, terrain_grad_x = np.gradient(terrain)
    else:
        terrain_grad_y = np.zeros_like(terrain)
        terrain_grad_x = np.zeros_like(terrain)
    terrain_bonus_scale = max(1.5, float(peak_heights.mean()) * 0.45)
    gradient_gain = 0.45 + min(0.25, terrain_bonus_scale * 0.03)

    for _gen in range(generations):
        gx_idx = np.clip(((xs - _MAP_L) / cell_w).astype(int), 0, grid - 1)
        gy_idx = np.clip(((ys - _MAP_T) / cell_h).astype(int), 0, grid - 1)

        # Evaluate fitness: proximity to weighted peaks
        fitness = terrain[gy_idx, gx_idx] * terrain_bonus_scale
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

        # Mutate all organisms slightly (terrain-following drift + noise)
        gx_idx = np.clip(((xs - _MAP_L) / cell_w).astype(int), 0, grid - 1)
        gy_idx = np.clip(((ys - _MAP_T) / cell_h).astype(int), 0, grid - 1)
        grad_x = np.asarray(terrain_grad_x)[gy_idx, gx_idx]
        grad_y = np.asarray(terrain_grad_y)[gy_idx, gx_idx]
        xs += grad_x * cell_w * gradient_gain
        ys += grad_y * cell_h * gradient_gain
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

    def _fade(start: float, full: float) -> float:
        """Smooth 0-1 ramp between start and full maturity."""
        return max(0.0, min(1.0, (growth_mat - start) / max(0.001, full - start)))

    h = seed_hash({"seed": seed}) if seed is not None else seed_hash(metrics)
    rng = np.random.default_rng(int(h[:8], 16))
    noise = Noise2D(seed=int(h[8:16], 16))

    raw_repos = metrics.get("repos", [])
    preferred_repo_names = metrics.get("repo_visual_order")
    repos = order_repos_for_visual_plan(
        list(raw_repos) if isinstance(raw_repos, list) else [],
        preferred_names=(
            preferred_repo_names
            if isinstance(preferred_repo_names, (list, tuple))
            else None
        ),
    )
    primary_repos, _overflow = select_primary_repos(repos, limit=CFG.max_repos)
    tempo = activity_tempo(metrics.get("contributions_monthly"))
    affinities = topic_affinity_matrix(primary_repos)
    dynamics = _derive_landscape_dynamics(metrics, maturity=mat, tempo=tempo)
    repo_density_signal = _dense_repo_signal(len(primary_repos), baseline=CFG.max_repos)
    visibility_scores = [repo_visibility_score(repo) for repo in primary_repos]
    visibility_max = max(visibility_scores, default=1.0)
    visibility_min = min(visibility_scores, default=0.0)
    visibility_span = max(0.001, visibility_max - visibility_min)
    visibility_norms = [
        (
            0.18 + 0.82 * ((score - visibility_min) / visibility_span)
            if len(visibility_scores) > 1
            else 1.0
        )
        for score in visibility_scores
    ]
    crowding_scale = max(
        0.42,
        1.0 / math.sqrt(max(1.0, len(primary_repos) / max(1, CFG.max_repos))),
    )

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
            "contributions_daily": metrics.get("contributions_daily", {}),
        },
        fallback_days=365,
        now=date(2000, 1, 1),
    )

    raw_daily = metrics.get("contributions_daily", {})
    if isinstance(raw_daily, dict) and raw_daily:
        daily_series = {
            str(day)[:10]: _as_non_negative_int(value)
            for day, value in raw_daily.items()
            if isinstance(day, str) and len(day) >= 10
        }
        daily_series = dict(sorted(daily_series.items()))
    else:
        daily_series = contributions_monthly_to_daily_series(
            metrics.get("contributions_monthly", {}),
            reference_year=timeline_window[1].year,
        )
    sorted_daily = sorted(daily_series.items(), key=lambda kv: kv[0])
    total_daily = sum(_as_non_negative_int(value) for _, value in sorted_daily)

    def _date_for_activity_fraction(frac: float) -> str:
        frac = max(0.0, min(1.0, frac))
        if total_daily <= 0 or not sorted_daily:
            span = max((timeline_window[1] - timeline_window[0]).days, 1)
            return (
                timeline_window[0] + timedelta(days=int(round(frac * span)))
            ).isoformat()
        if frac <= 0.0:
            for day, value in sorted_daily:
                if _as_non_negative_int(value) > 0:
                    return day
            return sorted_daily[0][0]
        threshold = frac * total_daily
        running = 0.0
        for day, value in sorted_daily:
            running += _as_non_negative_int(value)
            if running >= threshold:
                return day
        return sorted_daily[-1][0]

    activity_midpoint = _date_for_activity_fraction(0.5)

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

    # Base terrain noise follows cumulative activity so early snapshots stay smoother.
    total_commits = _as_non_negative_int(metrics.get("total_commits", 0))
    activity_total = max(
        total_daily,
        _as_non_negative_int(metrics.get("contributions_last_year", 0)),
    )
    terrain_oct = max(
        2,
        min(5, 2 + max(total_commits // 16000, activity_total // 900)),
    )
    terrain_amp = 0.018 + min(
        0.028,
        math.log1p(max(activity_total, 1)) / math.log1p(2400.0) * 0.028,
    )
    for gy in range(grid):
        for gx in range(grid):
            elevation[gy, gx] = (
                noise.fbm(gx / grid * 4.0, gy / grid * 4.0, terrain_oct) * terrain_amp
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
    weights = [
        math.log1p(max(1, _as_non_negative_int(r.get("stars", 0))))
        + 0.9
        + 0.7 * visibility_norms[index]
        for index, r in enumerate(primary_repos)
    ]

    # Optimize placement to avoid overlap
    if len(initial_positions) >= 2:
        optimized_positions = optimize_placement(
            initial_positions,
            weights,
            float(WIDTH),
            float(HEIGHT),
            min_spacing=70.0 * crowding_scale,
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
    micro_colonies: list[dict[str, Any]] = []
    repo_count_visible = len(primary_repos)
    max_repo_age = max(
        (
            _as_non_negative_int(repo.get("age_months", 0))
            for repo in primary_repos
            if isinstance(repo, dict)
        ),
        default=0,
    )
    labeled_peak_indices: set[int] = set()
    if primary_repos:
        ranked_peak_indices = sorted(
            range(len(primary_repos)),
            key=lambda idx: (
                visibility_scores[idx],
                _as_non_negative_int(primary_repos[idx].get("stars", 0)),
                -_as_non_negative_int(primary_repos[idx].get("age_months", 0)),
            ),
            reverse=True,
        )
        label_limit = max(
            4,
            min(8, int(round(math.sqrt(len(primary_repos)) * 2.0))),
        )
        labeled_peak_indices = set(ranked_peak_indices[:label_limit])

    for ri in range(min(repo_count_visible, len(primary_repos))):
        repo = primary_repos[ri]
        px, py = (
            optimized_positions[ri]
            if ri < len(optimized_positions)
            else (_MAP_L + _MAP_W / 2, _MAP_T + _MAP_H / 2)
        )
        peak_h, sigma_grid, terrace_height, terrace_sigma = _repo_peak_profile(
            repo,
            max_repo_age=max_repo_age,
        )
        visibility = visibility_norms[ri] if ri < len(visibility_norms) else 1.0
        peak_h *= 0.58 + 0.72 * visibility
        sigma_grid = max(
            1.6,
            sigma_grid * (0.74 + 0.42 * visibility) * (crowding_scale**0.45),
        )
        terrace_height *= 0.62 + 0.74 * visibility
        terrace_sigma = max(
            1.8,
            terrace_sigma * (0.82 + 0.30 * (1.0 - visibility)) * (crowding_scale**0.25),
        )
        hue = opt_hues[ri] if ri < len(opt_hues) else 155.0
        color = oklch(0.65, 0.14, hue)

        # Convert canvas position to grid position
        gpx = (px - _MAP_L) / cell_w
        gpy = (py - _MAP_T) / cell_h

        for gy in range(grid):
            for gx in range(grid):
                elevation[gy, gx] += peak_h * _gaussian(gx, gy, gpx, gpy, sigma_grid)
                elevation[gy, gx] += terrace_height * _gaussian(
                    gx,
                    gy,
                    gpx,
                    gpy,
                    terrace_sigma,
                )

        peaks.append((px, py, peak_h, color, repo))

        colony_hash = seed_hash(
            {"seed": h, "repo": repo.get("name", ""), "layer": "gl-micro-colony"}
        )
        colony_count = min(
            3,
            1
            + int(visibility < 0.72)
            + int(visibility < 0.42 or repo_density_signal > 0.7),
        )
        for colony_idx in range(colony_count):
            angle = (
                2.0
                * math.pi
                * (
                    hex_frac(colony_hash, colony_idx * 4, colony_idx * 4 + 4)
                    + colony_idx / max(1, colony_count)
                )
            )
            offset = (
                12.0
                + 10.0 * colony_idx
                + 18.0 * (1.0 - visibility)
                + 10.0 * repo_density_signal
            ) * crowding_scale
            colony_x = max(
                _MAP_L + 8.0,
                min(_MAP_R - 8.0, px + math.cos(angle) * offset),
            )
            colony_y = max(
                _MAP_T + 8.0,
                min(_MAP_B - 8.0, py + math.sin(angle) * offset),
            )
            colony_height = (
                peak_h * (0.10 + 0.08 * (1.0 - visibility)) * (1.0 - 0.14 * colony_idx)
            )
            colony_sigma = max(1.1, sigma_grid * (0.32 + 0.08 * colony_idx))
            colony_gpx = (colony_x - _MAP_L) / cell_w
            colony_gpy = (colony_y - _MAP_T) / cell_h
            for gy in range(grid):
                for gx in range(grid):
                    elevation[gy, gx] += colony_height * _gaussian(
                        gx,
                        gy,
                        colony_gpx,
                        colony_gpy,
                        colony_sigma,
                    )
            micro_colonies.append(
                {
                    "x": colony_x,
                    "y": colony_y,
                    "height": colony_height,
                    "color": color,
                    "repo": repo,
                    "owner_index": ri,
                    "visibility": visibility,
                }
            )

    # Add saddle ridges between topic-related repos
    ridge_fade = (
        _fade(0.3, 0.7)
        if timeline_enabled
        else min(1.0, 0.2 + max(0.0, dynamics.ridge_intensity - 1.0) * 0.45)
    )
    if ridge_fade > 0:
        affinity_pairs = sorted(
            affinities.items(),
            key=lambda item: (
                item[1]
                * (visibility_norms[item[0][0]] + visibility_norms[item[0][1]])
                * 0.5,
                -abs(item[0][0] - item[0][1]),
            ),
            reverse=True,
        )
        ridge_pair_limit = max(CFG.max_repos, int(round(len(primary_repos) * 1.5)))
        for (i, j), affinity in affinity_pairs[:ridge_pair_limit]:
            if i >= len(peaks) or j >= len(peaks):
                continue
            p1 = peaks[i]
            p2 = peaks[j]
            gx1, gy1 = (p1[0] - _MAP_L) / cell_w, (p1[1] - _MAP_T) / cell_h
            gx2, gy2 = (p2[0] - _MAP_L) / cell_w, (p2[1] - _MAP_T) / cell_h
            ridge_h = (
                min(p1[2], p2[2])
                * affinity
                * 0.3
                * ridge_fade
                * dynamics.ridge_intensity
                * (0.72 + 0.28 * ((visibility_norms[i] + visibility_norms[j]) * 0.5))
            )
            ridge_sigma = max(
                5.0,
                8.0
                * (
                    0.72
                    + 0.18 * repo_density_signal
                    + 0.10 * (1.0 - min(visibility_norms[i], visibility_norms[j]))
                ),
            )
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
                    elevation[gy, gx] += ridge_h * math.exp(
                        -(dist * dist) / ridge_sigma
                    )

    # Normalize elevation for contour extraction
    e_min = float(elevation.min())
    e_max = float(elevation.max())
    e_range = max(e_max - e_min, 0.001)

    # ── Organism simulation ───────────────────────────────────────
    generations = dynamics.generations
    pop_count = dynamics.pop_count
    mutation_rate = dynamics.mutation_rate

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

    total_repo_stars = sum(
        _as_non_negative_int(repo.get("stars", 0))
        for repo in primary_repos
        if isinstance(repo, dict)
    )
    static_contour_signal = min(
        1.0,
        (math.log1p(max(activity_total, 1)) / math.log1p(2400.0)) * 0.7
        + repo_density_signal * 0.3,
    )
    static_peak_signal = min(
        1.0,
        (math.log1p(max(total_repo_stars, 1)) / math.log1p(4000.0)) * 0.65
        + _dense_repo_signal(len(peaks), baseline=CFG.max_repos) * 0.35,
    )
    static_population_signal = min(
        1.0,
        (pop_count / max(1.0, CFG.pop_base + CFG.pop_scale * 2.0)) * 0.6
        + (generations / 40.0) * 0.4,
    )

    # ── SVG output ────────────────────────────────────────────────
    P: list[str] = []
    P.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" '
        f'width="{WIDTH}" height="{HEIGHT}" '
        f'data-maturity="{mat:.3f}" data-tempo="{tempo:.3f}" '
        f'data-peak-count="{len(peaks)}" data-population="{pop_count}" '
        f'data-generations="{generations}" data-activity-midpoint="{activity_midpoint}" '
        f'data-activity-signal="{static_contour_signal:.3f}" '
        f'data-population-signal="{static_population_signal:.3f}">'
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

    contour_fade = (
        _fade(0.05, 0.4) if timeline_enabled else max(0.18, static_contour_signal)
    )
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
        contour_when = _date_for_activity_fraction(contour_frac)

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
    peak_fade = _fade(0.15, 0.6) if timeline_enabled else max(0.25, static_peak_signal)
    colony_fade = (
        _fade(0.10, 0.55) if timeline_enabled else max(0.16, static_peak_signal * 0.72)
    )
    if colony_fade > 0:
        for colony in micro_colonies:
            if not budget.ok():
                break
            colony_when = _repo_date(colony["repo"]) or start_date
            colony_visibility = float(colony["visibility"])
            colony_radius = 1.3 + 2.2 * colony_visibility
            colony_opacity = (0.10 + 0.18 * colony_visibility) * colony_fade
            P.append(
                f'<circle data-role="gl-micro-colony" '
                f'data-owner-index="{int(colony["owner_index"])}" '
                f'cx="{float(colony["x"]):.1f}" cy="{float(colony["y"]):.1f}" '
                f'r="{colony_radius:.1f}" fill="{colony["color"]}" '
                f'filter="url(#glHaze)" '
                f"{_timeline_style(colony_when, colony_opacity, 'tl-reveal tl-soft')}/>"
            )
            budget.add(1)
    for pi, (px, py, ph, color, repo) in enumerate(peaks):
        if not budget.ok():
            break
        peak_when = _repo_date(repo) or start_date
        peak_visibility = visibility_norms[pi] if pi < len(visibility_norms) else 1.0
        r_glow = max(5.5, min(40.0, ph * (1.05 + 0.40 * peak_visibility)))
        r_core = max(2.2, min(12.0, ph * (0.28 + 0.22 * peak_visibility)))

        # Glow
        P.append(
            f'<circle cx="{px:.1f}" cy="{py:.1f}" r="{r_glow:.1f}" '
            f'fill="{color}" filter="url(#glHaze)" '
            f"{_timeline_style(peak_when, (0.12 + 0.18 * peak_visibility) * peak_fade)}/>"
        )
        budget.add(1)

        # Core
        P.append(
            f'<circle cx="{px:.1f}" cy="{py:.1f}" r="{r_core:.1f}" '
            f'fill="{color}" '
            f"{_timeline_style(peak_when, (0.45 + 0.35 * peak_visibility) * peak_fade)}/>"
        )
        budget.add(1)

    # ── Organism trails ───────────────────────────────────────────
    trail_fade = (
        _fade(0.3, 0.8) if timeline_enabled else max(0.12, static_population_signal)
    )
    if trail_fade > 0 and organisms:
        # Assign organisms to nearest peak for coloring
        for ox, oy, trail in organisms:
            if not budget.ok() or len(trail) < 3:
                continue
            # Find nearest peak
            best_pi = 0
            best_dist = float("inf")
            for pi, (px, py, _, _, _) in enumerate(peaks):
                dist_to_peak = math.hypot(ox - px, oy - py)
                if dist_to_peak < best_dist:
                    best_dist = dist_to_peak
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
    org_fade = (
        _fade(0.15, 0.5) if timeline_enabled else max(0.18, static_population_signal)
    )
    if org_fade > 0 and organisms:
        mid_date = activity_midpoint

        for ox, oy, trail in organisms:
            if not budget.ok():
                break
            # Nearest peak for color
            best_pi = 0
            best_dist = float("inf")
            for pi, (px, py, _, _, _) in enumerate(peaks):
                dist_to_peak = math.hypot(ox - px, oy - py)
                if dist_to_peak < best_dist:
                    best_dist = dist_to_peak
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
    label_fade = (
        _fade(0.6, 0.95)
        if timeline_enabled
        else max(0.0, min(1.0, static_peak_signal * 0.85 - 0.2))
    )
    if label_fade > 0:
        text_color = pal.get("text_primary", pal.get("accent", "#cccccc"))
        for pi, (px, py, ph, color, repo) in enumerate(peaks):
            if not budget.ok():
                break
            if pi not in labeled_peak_indices:
                continue
            name = repo.get("name", "")
            if not name:
                continue
            peak_when = _repo_date(repo) or start_date
            # Truncate long names
            label = name[:18] + ("\u2026" if len(name) > 18 else "")
            stars = repo.get("stars", 0)

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
