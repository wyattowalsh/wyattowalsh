"""
Topography Ultimate — Full cartographic illustration generative art.

Dense contour lines with index contours, hillshade, river systems,
vegetation/marsh symbols, trails, compass rose, coordinate grid,
elevation profile cross-section, legend, spot heights, hachures.

Light theme on cream paper.
"""

# ruff: noqa: E501

from __future__ import annotations

import math
from datetime import date, timedelta

import numpy as np

from .optimize import optimize_layout_pso, optimize_palette_hues
from .shared import (
    HEIGHT,
    LANG_HUES,
    WIDTH,
    Noise2D,
    WorldState,
    _build_world_palette_extended,
    atmospheric_haze_filter,
    compute_maturity,
    compute_world_state,
    contributions_monthly_to_daily_series,
    hex_frac,
    make_radial_gradient,
    map_date_to_loop_delay,
    normalize_timeline_window,
    oklch,
    oklch_gradient,
    oklch_lerp,
    order_repos_for_visual_plan,
    organic_texture_filter,
    seed_hash,
    select_palette_for_world,
    visual_complexity,
)

# Map margins
MAP_L, MAP_T = 60, 60
MAP_R, MAP_B = WIDTH - 60, HEIGHT - 110
MAP_W = MAP_R - MAP_L
MAP_H = MAP_B - MAP_T

# Language → terrain character: (noise_freq, amplitude_multiplier)
LANG_TERRAIN: dict[str | None, tuple[float, float]] = {
    "Python": (8.0, 0.04),
    "Jupyter Notebook": (8.0, 0.04),
    "JavaScript": (16.0, 0.06),
    "TypeScript": (16.0, 0.06),
    "HTML": (16.0, 0.05),
    "CSS": (16.0, 0.05),
    "Rust": (12.0, 0.08),
    "Go": (12.0, 0.07),
    "C": (12.0, 0.08),
    "C++": (12.0, 0.08),
    "Shell": (5.0, 0.03),
    "Ruby": (10.0, 0.05),
    "Java": (10.0, 0.05),
    None: (10.0, 0.05),
}

# Language → biome type: (vegetation_pattern, biome_color_tint)
# Maps programming languages to cartographic biome metaphors
LANG_BIOME: dict[str | None, tuple[str, str]] = {
    "Python": ("forest", "#2a6a2e"),  # dense forest / green
    "Jupyter Notebook": ("forest", "#3a7a3e"),
    "JavaScript": ("grassland", "#8a9a3a"),  # open grassland / yellow-green
    "TypeScript": ("grassland", "#7a8a4a"),
    "HTML": ("savanna", "#b0a050"),  # savanna / warm
    "CSS": ("savanna", "#a09848"),
    "Rust": ("rocky", "#8a7060"),  # rocky peaks / brown
    "Go": ("alpine", "#6a8a7a"),  # alpine meadow / blue-green
    "C": ("rocky", "#7a6a5a"),
    "C++": ("rocky", "#8a7a6a"),
    "Shell": ("scrubland", "#7a8a5a"),  # dry scrubland
    "Ruby": ("tropical", "#4a8a3a"),  # tropical / vivid green
    "Java": ("woodland", "#5a7a4a"),  # deciduous woodland
    None: ("mixed", "#6a7a5a"),
}


def _grid_to_map(gx: float, gy: float, cell_w: float, cell_h: float):
    return MAP_L + gx * cell_w, MAP_T + gy * cell_h


# Precomputed once at module level — oklch() is pure, args are constants
# Pure OKLCH ramp: lightness marches 0.45→0.95, hue blue(240)→green(140)→brown(50)→gray(200)
_TOPO_STOPS = [
    (0.00, oklch(0.40, 0.14, 240)),  # deep water — dark blue
    (0.06, oklch(0.48, 0.12, 230)),  # shallow water — lighter blue
    (0.10, oklch(0.52, 0.15, 180)),  # shoreline — blue-green transition
    (0.16, oklch(0.55, 0.22, 140)),  # lowland — green
    (0.22, oklch(0.58, 0.20, 120)),  # low hills — yellow-green
    (0.30, oklch(0.62, 0.18, 100)),  # mid-hills — warm green
    (0.38, oklch(0.66, 0.15, 90)),  # mid-elevation — olive
    (0.46, oklch(0.70, 0.13, 75)),  # upper mid — warm tan
    (0.54, oklch(0.73, 0.11, 65)),  # highlands — light tan
    (0.62, oklch(0.76, 0.10, 55)),  # high terrain — warm brown
    (0.70, oklch(0.79, 0.08, 50)),  # upper highlands — pale brown
    (0.78, oklch(0.82, 0.07, 60)),  # sub-alpine — light brown
    (0.86, oklch(0.85, 0.05, 100)),  # alpine — pale olive-gray
    (0.92, oklch(0.88, 0.03, 200)),  # near-summit — cool gray
    (0.96, oklch(0.91, 0.02, 200)),  # summit ridge — light gray
    (1.00, oklch(0.93, 0.01, 200)),  # snow peaks — near-white gray
]


def _topo_color(e: float) -> str:
    # Swiss warm-humid hypsometric ramp (Imhof-inspired)
    # Uses oklch_lerp for perceptually uniform interpolation between OKLCH-defined stops
    stops = _TOPO_STOPS
    for i in range(len(stops) - 1):
        if e <= stops[i + 1][0]:
            t = (e - stops[i][0]) / max(0.001, stops[i + 1][0] - stops[i][0])
            return oklch_lerp(stops[i][1], stops[i + 1][1], t)
    return stops[-1][1]


def _extract_contours(elevation, grid, level, cell_w, cell_h):
    seg_list = []
    for gy in range(grid - 1):
        for gx in range(grid - 1):
            tl = elevation[gy, gx]
            tr = elevation[gy, gx + 1]
            bl = elevation[gy + 1, gx]
            br = elevation[gy + 1, gx + 1]
            edges = []
            if (tl < level) != (tr < level):
                t = (level - tl) / (tr - tl + 1e-10)
                edges.append(_grid_to_map(gx + t, gy, cell_w, cell_h))
            if (bl < level) != (br < level):
                t = (level - bl) / (br - bl + 1e-10)
                edges.append(_grid_to_map(gx + t, gy + 1, cell_w, cell_h))
            if (tl < level) != (bl < level):
                t = (level - tl) / (bl - tl + 1e-10)
                edges.append(_grid_to_map(gx, gy + t, cell_w, cell_h))
            if (tr < level) != (br < level):
                t = (level - tr) / (br - tr + 1e-10)
                edges.append(_grid_to_map(gx + 1, gy + t, cell_w, cell_h))
            if len(edges) >= 2:
                seg_list.append((edges[0], edges[1]))

    if not seg_list:
        return []

    used = [False] * len(seg_list)
    chains = []
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
                for end_idx in [0, 1]:
                    pt = seg_list[j][end_idx]
                    d = math.sqrt((pt[0] - last[0]) ** 2 + (pt[1] - last[1]) ** 2)
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


def _point_to_segment_distance(px: float, py: float, p1: tuple, p2: tuple) -> float:
    """Compute the minimum distance from point (px, py) to line segment p1-p2."""
    x1, y1 = p1
    x2, y2 = p2
    dx = x2 - x1
    dy = y2 - y1
    len_sq = dx * dx + dy * dy
    if len_sq < 1e-12:
        return math.sqrt((px - x1) ** 2 + (py - y1) ** 2)
    t = max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / len_sq))
    proj_x = x1 + t * dx
    proj_y = y1 + t * dy
    return math.sqrt((px - proj_x) ** 2 + (py - proj_y) ** 2)


def _chaikin_smooth(
    points: list[tuple[float, float]], iterations: int = 1, closed: bool = False
) -> list[tuple[float, float]]:
    """Deterministic polyline smoothing for less angular contour and river curves."""
    if len(points) < 3 or iterations <= 0:
        return points
    smoothed = points[:]
    for _ in range(iterations):
        if len(smoothed) < 3:
            break
        nxt: list[tuple[float, float]] = []
        if not closed:
            nxt.append(smoothed[0])
        seg_count = len(smoothed) if closed else len(smoothed) - 1
        for i in range(seg_count):
            p0 = smoothed[i]
            p1 = smoothed[(i + 1) % len(smoothed)]
            qx = 0.75 * p0[0] + 0.25 * p1[0]
            qy = 0.75 * p0[1] + 0.25 * p1[1]
            rx = 0.25 * p0[0] + 0.75 * p1[0]
            ry = 0.25 * p0[1] + 0.75 * p1[1]
            nxt.append((qx, qy))
            nxt.append((rx, ry))
        if not closed:
            nxt.append(smoothed[-1])
        smoothed = nxt
    return smoothed


def _normalize_hour_distribution(commit_hours: object) -> dict[int, float]:
    hours: dict[int, float] = {}
    if not isinstance(commit_hours, dict):
        return hours
    for raw_hour, raw_count in commit_hours.items():
        try:
            hour = int(raw_hour)
            count = float(raw_count)
        except (TypeError, ValueError):
            continue
        if 0 <= hour <= 23 and count > 0:
            hours[hour] = hours.get(hour, 0.0) + count
    return hours


def _commit_hour_hillshade_profile(commit_hours: object) -> dict[str, float]:
    hours = _normalize_hour_distribution(commit_hours)
    if not hours:
        return {
            "peak_hour": 12.0,
            "focus": 0.35,
            "sun_azimuth": 315.0,
            "sun_altitude": 32.0,
            "secondary_azimuth": 36.0,
            "secondary_altitude": 18.0,
            "primary_weight": 0.68,
        }

    total = sum(hours.values())
    vec_x = sum(
        math.cos(2 * math.pi * hour / 24.0) * weight for hour, weight in hours.items()
    )
    vec_y = sum(
        math.sin(2 * math.pi * hour / 24.0) * weight for hour, weight in hours.items()
    )
    focus = min(1.0, max(0.0, math.hypot(vec_x, vec_y) / max(total, 1e-6)))
    if abs(vec_x) < 1e-9 and abs(vec_y) < 1e-9:
        peak_hour = 12.0
    else:
        mean_angle = math.atan2(vec_y, vec_x)
        if mean_angle < 0:
            mean_angle += 2 * math.pi
        peak_hour = mean_angle * 24.0 / (2 * math.pi)

    day_strength = max(0.0, math.cos((peak_hour - 12.0) * math.pi / 12.0))
    sun_azimuth = (peak_hour / 24.0) * 360.0
    sun_altitude = 14.0 + 20.0 * day_strength + 24.0 * focus
    secondary_azimuth = (sun_azimuth + 95.0 + 25.0 * (1.0 - focus)) % 360.0
    secondary_altitude = max(8.0, sun_altitude * (0.42 + 0.16 * (1.0 - day_strength)))
    return {
        "peak_hour": peak_hour,
        "focus": focus,
        "sun_azimuth": sun_azimuth,
        "sun_altitude": sun_altitude,
        "secondary_azimuth": secondary_azimuth,
        "secondary_altitude": secondary_altitude,
        "primary_weight": 0.54 + 0.26 * focus,
    }


def _settlement_scale_tier(followers_count: int | float) -> tuple[str, str]:
    followers = max(0, int(followers_count or 0))
    if followers >= 1000:
        return "capital", "Capital"
    if followers >= 500:
        return "city", "City"
    if followers >= 200:
        return "town", "Town"
    if followers >= 75:
        return "village", "Village"
    if followers >= 25:
        return "hamlet", "Hamlet"
    if followers > 0:
        return "outpost", "Outpost"
    return "none", "Unsettled"


def _river_flow_profile(star_velocity: object) -> dict[str, str | float]:
    recent_rate = 0.0
    peak_rate = 0.0
    trend = "steady"
    if isinstance(star_velocity, dict):
        try:
            recent_rate = max(0.0, float(star_velocity.get("recent_rate", 0.0) or 0.0))
        except (TypeError, ValueError):
            recent_rate = 0.0
        try:
            peak_rate = max(0.0, float(star_velocity.get("peak_rate", 0.0) or 0.0))
        except (TypeError, ValueError):
            peak_rate = 0.0
        trend = str(star_velocity.get("trend", "steady") or "steady").lower()

    velocity_norm = min(1.0, max(recent_rate, peak_rate * 0.7) / 12.0)
    if trend == "rising":
        velocity_norm = min(1.0, velocity_norm + 0.08)
    elif trend == "falling":
        velocity_norm = max(0.0, velocity_norm - 0.05)

    if velocity_norm >= 0.75:
        tier = "torrent"
    elif velocity_norm >= 0.45:
        tier = "swift"
    elif velocity_norm >= 0.20:
        tier = "run"
    else:
        tier = "still"

    return {
        "tier": tier,
        "velocity_norm": velocity_norm,
        "width_scale": 1.0 + 0.9 * velocity_norm,
        "current_opacity": 0.04 + 0.24 * velocity_norm,
        "current_ratio": 0.16 + 0.12 * velocity_norm,
        "dash": max(1.4, 2.8 - 1.2 * velocity_norm),
        "gap": 2.2 + 1.6 * (1.0 - velocity_norm),
    }


def _repo_recency_landscape_profile(
    repos: object, timeline_window: tuple[date, date]
) -> dict[str, str | float]:
    if not isinstance(repos, list) or not repos:
        return {
            "band": "balanced",
            "mean_recency": 0.5,
            "legacy_share": 0.0,
            "recent_share": 0.0,
        }

    start, end = timeline_window
    span_days = max(1, end.toordinal() - start.toordinal())
    recencies: list[float] = []
    legacy_count = 0
    recent_count = 0

    for repo in repos:
        if not isinstance(repo, dict):
            continue

        repo_day: date | None = None
        for key in ("date", "created_at", "created", "pushed_at", "updated_at"):
            raw = repo.get(key)
            if not isinstance(raw, str) or not raw.strip():
                continue
            try:
                repo_day = date.fromisoformat(raw[:10])
            except ValueError:
                repo_day = None
            if repo_day is not None:
                break

        if repo_day is None:
            try:
                age_months = float(repo.get("age_months", 0) or 0.0)
            except (TypeError, ValueError):
                age_months = 0.0
            if age_months > 0:
                repo_day = end - timedelta(days=int(age_months * 30.4))

        if repo_day is None:
            continue

        recency = max(
            0.0,
            min(1.0, (repo_day.toordinal() - start.toordinal()) / span_days),
        )
        recencies.append(recency)
        if recency <= 0.34:
            legacy_count += 1
        elif recency >= 0.66:
            recent_count += 1

    if not recencies:
        return {
            "band": "balanced",
            "mean_recency": 0.5,
            "legacy_share": 0.0,
            "recent_share": 0.0,
        }

    mean_recency = sum(recencies) / len(recencies)
    legacy_share = legacy_count / len(recencies)
    recent_share = recent_count / len(recencies)

    if mean_recency <= 0.38 and recent_share <= 0.25:
        band = "legacy"
    elif mean_recency >= 0.62 and recent_share >= 0.34:
        band = "recent"
    else:
        band = "balanced"

    return {
        "band": band,
        "mean_recency": mean_recency,
        "legacy_share": legacy_share,
        "recent_share": recent_share,
    }


def _polyline_distance(
    px: float, py: float, points: list[tuple[float, float]]
) -> float:
    if len(points) < 2:
        return float("inf")
    return min(
        _point_to_segment_distance(px, py, start, end)
        for start, end in zip(points, points[1:], strict=False)
    )


def _choose_label_anchor(
    anchor_x: float,
    anchor_y: float,
    candidates: list[tuple[float, float]],
    blocked_paths: list[list[tuple[float, float]]],
) -> tuple[float, float, float]:
    best_choice: tuple[float, float, float] | None = None
    best_score = -float("inf")
    for dx, dy in candidates:
        lx = anchor_x + dx
        ly = anchor_y + dy
        if not (MAP_L + 6 <= lx <= MAP_R - 6 and MAP_T + 6 <= ly <= MAP_B - 6):
            continue
        clearance = min(
            (
                _polyline_distance(lx, ly, path)
                for path in blocked_paths
                if len(path) >= 2
            ),
            default=36.0,
        )
        edge_buffer = min(lx - MAP_L, MAP_R - lx, ly - MAP_T, MAP_B - ly)
        score = clearance + edge_buffer * 0.15 - (abs(dx) + abs(dy)) * 0.05
        if score > best_score:
            best_choice = (lx, ly, clearance)
            best_score = score

    if best_choice is not None:
        return best_choice

    dx, dy = candidates[0]
    lx = max(MAP_L + 6, min(MAP_R - 6, anchor_x + dx))
    ly = max(MAP_T + 6, min(MAP_B - 6, anchor_y + dy))
    clearance = min(
        (_polyline_distance(lx, ly, path) for path in blocked_paths if len(path) >= 2),
        default=36.0,
    )
    return lx, ly, clearance


def generate(
    metrics: dict,
    *,
    seed: str | None = None,
    maturity: float | None = None,
    chrome_maturity: float | None = None,
    timeline: bool = True,
    loop_duration: float = 60.0,
    reveal_fraction: float = 0.93,
) -> str:
    mat = maturity if maturity is not None else compute_maturity(metrics)
    chrome_mat = chrome_maturity if chrome_maturity is not None else mat
    timeline_enabled = bool(timeline and loop_duration > 0)
    growth_mat = 1.0 if timeline_enabled else mat
    chrome_mat = 1.0 if timeline_enabled else chrome_mat

    # ── WorldState: coherent atmosphere across all artworks ────────
    world: WorldState = compute_world_state(metrics)

    # ── OKLCH palette & complexity (Phase 4d) ─────────────────────
    select_palette_for_world(world)
    pal = _build_world_palette_extended(
        world.time_of_day,
        world.weather,
        world.season,
        world.energy,
    )
    complexity = visual_complexity(metrics)

    def _fade(start: float, full: float) -> float:
        """Smooth 0→1 ramp between start and full maturity."""
        return max(0.0, min(1.0, (growth_mat - start) / max(0.001, full - start)))

    def _sample_ranked_indices(length: int, limit: int) -> list[int]:
        if length <= 0 or limit <= 0:
            return []
        if length <= limit:
            return list(range(length))
        if limit == 1:
            return [0]
        return sorted(
            {
                int(round(step * (length - 1) / max(1, limit - 1)))
                for step in range(limit)
            }
        )

    h = seed_hash({"seed": seed}) if seed is not None else seed_hash(metrics)
    rng = np.random.default_rng(int(h[:8], 16))
    noise = Noise2D(seed=int(h[8:16], 16))
    noise2 = Noise2D(seed=int(h[16:24], 16))

    monthly = metrics.get("contributions_monthly", {})
    raw_repos = metrics.get("repos", [])
    preferred_repo_names: list[str] = []
    seen_repo_names: set[str] = set()
    for source in (
        metrics.get("repo_visual_order"),
        metrics.get("canonical_primary_repo_names"),
    ):
        if not isinstance(source, list | tuple):
            continue
        for raw_name in source:
            repo_name = str(raw_name).strip() if isinstance(raw_name, str) else ""
            if not repo_name or repo_name in seen_repo_names:
                continue
            seen_repo_names.add(repo_name)
            preferred_repo_names.append(repo_name)
    repos = order_repos_for_visual_plan(
        [
            repo
            for repo in (raw_repos if isinstance(raw_repos, list | tuple) else [])
            if isinstance(repo, dict)
        ],
        preferred_names=preferred_repo_names or None,
    )
    total_commits = metrics.get("total_commits", 500)
    followers = metrics.get("followers", 10)
    contributions = metrics.get("contributions_last_year", 200)
    forks = metrics.get("forks", 0)
    stars = metrics.get("stars", 0)
    total_issues_raw = metrics.get("total_issues", 0)
    recent_merged_prs = metrics.get("recent_merged_prs", [])
    releases = metrics.get("releases", [])
    commit_hour_profile = _commit_hour_hillshade_profile(
        metrics.get("commit_hour_distribution", {})
    )
    river_flow_profile = _river_flow_profile(metrics.get("star_velocity", {}))
    settlement_tier, settlement_title = _settlement_scale_tier(followers)
    metrics.get("network_count", 0)
    try:
        issue_pressure = min(1.0, max(0.0, float(total_issues_raw or 0.0) / 36.0))
    except (TypeError, ValueError):
        issue_pressure = 0.0

    def _history_day(value: object) -> date | None:
        if isinstance(value, date):
            return value
        if not isinstance(value, str):
            return None
        raw = value.strip()
        if not raw:
            return None
        try:
            return date.fromisoformat(raw[:10])
        except ValueError:
            return None

    repo_day_cache: dict[tuple[int, int | None], date | None] = {}

    def _repo_day(repo: dict, *, fallback_end: date | None = None) -> date | None:
        cache_key = (
            id(repo),
            fallback_end.toordinal() if fallback_end is not None else None,
        )
        if cache_key in repo_day_cache:
            return repo_day_cache[cache_key]

        repo_day: date | None = None
        for key in ("date", "created_at", "created", "pushed_at", "updated_at"):
            repo_day = _history_day(repo.get(key))
            if repo_day is not None:
                break

        if repo_day is None and fallback_end is not None:
            try:
                age_months = float(repo.get("age_months", 0) or 0.0)
            except (TypeError, ValueError):
                age_months = 0.0
            if age_months > 0:
                repo_day = fallback_end - timedelta(days=int(age_months * 30.4))

        repo_day_cache[cache_key] = repo_day
        return repo_day

    def _repo_date(repo: dict, *, fallback_end: date | None = None) -> str | None:
        repo_day = _repo_day(repo, fallback_end=fallback_end)
        return repo_day.isoformat() if repo_day is not None else None

    def _release_day(release: object) -> date | None:
        if not isinstance(release, dict):
            return None
        for key in ("published_at", "released_at", "date", "created_at"):
            release_day = _history_day(release.get(key))
            if release_day is not None:
                return release_day
        return None

    def _release_date(release: object) -> str | None:
        release_day = _release_day(release)
        return release_day.isoformat() if release_day is not None else None

    def _merged_pr_day(pr: object) -> date | None:
        if not isinstance(pr, dict):
            return None
        for key in ("merged_at", "closed_at", "date", "created_at"):
            pr_day = _history_day(pr.get(key))
            if pr_day is not None:
                return pr_day
        return None

    def _merged_pr_date(pr: object) -> str | None:
        pr_day = _merged_pr_day(pr)
        return pr_day.isoformat() if pr_day is not None else None

    deterministic_history_now = date(2024, 1, 1)

    explicit_history_window = normalize_timeline_window(
        [
            {"date": when}
            for when in (
                [
                    _repo_date(repo)
                    for repo in repos
                    if isinstance(repo, dict) and _repo_date(repo)
                ]
                + [
                    _release_date(release)
                    for release in releases
                    if _release_date(release)
                ]
                + [
                    _merged_pr_date(pr)
                    for pr in recent_merged_prs
                    if _merged_pr_date(pr)
                ]
            )
            if when
        ],
        {
            "account_created": metrics.get("account_created"),
            "contributions_monthly": monthly,
            "contributions_daily": metrics.get("contributions_daily", {}),
        },
        fallback_days=365,
        now=deterministic_history_now,
    )
    repo_age_anchor = max(explicit_history_window[1], deterministic_history_now)

    timeline_window = normalize_timeline_window(
        [
            {"date": when}
            for when in (
                [
                    _repo_date(repo, fallback_end=repo_age_anchor)
                    for repo in repos
                    if isinstance(repo, dict)
                    and _repo_date(repo, fallback_end=repo_age_anchor)
                ]
                + [
                    _release_date(release)
                    for release in releases
                    if _release_date(release)
                ]
                + [
                    _merged_pr_date(pr)
                    for pr in recent_merged_prs
                    if _merged_pr_date(pr)
                ]
            )
            if when
        ],
        {
            "account_created": metrics.get("account_created"),
            "repos": repos,
            "contributions_monthly": monthly,
            "contributions_daily": metrics.get("contributions_daily", {}),
        },
        fallback_days=365,
        now=deterministic_history_now,
    )
    repos_for_recency = []
    for repo in repos:
        if not isinstance(repo, dict):
            continue
        repo_for_recency = dict(repo)
        if not _history_day(repo_for_recency.get("date")):
            resolved_repo_when = _repo_date(
                repo_for_recency, fallback_end=repo_age_anchor
            )
            if resolved_repo_when is not None:
                repo_for_recency["date"] = resolved_repo_when
        repos_for_recency.append(repo_for_recency)
    repo_timeline_window = normalize_timeline_window(
        [
            {"date": _repo_date(repo, fallback_end=repo_age_anchor)}
            for repo in repos
            if isinstance(repo, dict) and _repo_date(repo, fallback_end=repo_age_anchor)
        ],
        {
            "account_created": metrics.get("account_created"),
            "repos": repos,
            "contributions_monthly": monthly,
            "contributions_daily": metrics.get("contributions_daily", {}),
        },
        fallback_days=365,
        now=deterministic_history_now,
    )
    repo_recency_profile = _repo_recency_landscape_profile(
        repos_for_recency, repo_timeline_window
    )
    contour_roughness = min(
        1.0,
        max(
            0.0,
            float(repo_recency_profile["mean_recency"]) * 0.72 + issue_pressure * 0.48,
        ),
    )
    contour_smooth_normal = (
        2 if contour_roughness < 0.22 else 1 if contour_roughness < 0.74 else 0
    )
    contour_smooth_index = (
        3 if contour_roughness < 0.14 else 2 if contour_roughness < 0.68 else 1
    )
    foothill_density = min(
        1.0,
        max(
            0.0,
            issue_pressure * 0.55 + float(repo_recency_profile["recent_share"]) * 0.65,
        ),
    )
    foothill_count = (
        0 if foothill_density <= 0.08 else 1 + int(round(foothill_density * 3.0))
    )
    foothill_span_end = 0.30 + float(repo_recency_profile["legacy_share"]) * 0.06
    foothill_levels = [
        0.12 + (idx + 1) * (foothill_span_end - 0.12) / (foothill_count + 1)
        for idx in range(foothill_count)
    ]
    daily_series = contributions_monthly_to_daily_series(
        monthly,
        reference_year=timeline_window[1].year,
    )
    activity_series_mode = "monthly" if daily_series else "none"
    raw_daily_series = metrics.get("contributions_daily", {})
    parsed_daily_series: dict[str, int] = {}
    if isinstance(raw_daily_series, dict):
        for raw_day, raw_count in sorted(raw_daily_series.items()):
            parsed_day = _history_day(raw_day)
            if parsed_day is None:
                continue
            try:
                parsed_daily_series[parsed_day.isoformat()] = max(
                    0, int(raw_count or 0)
                )
            except (TypeError, ValueError):
                continue
    if parsed_daily_series:
        if daily_series:
            daily_series.update(parsed_daily_series)
            activity_series_mode = "hybrid"
        else:
            daily_series = parsed_daily_series
            activity_series_mode = "daily"
    sorted_daily = sorted(daily_series.items(), key=lambda kv: kv[0])
    total_daily = sum(max(0, int(v)) for _, v in sorted_daily)

    def _date_for_activity_fraction(frac: float) -> str:
        frac = max(0.0, min(1.0, frac))
        if total_daily <= 0 or not sorted_daily:
            start, end = timeline_window
            span = max((end - start).days, 1)
            day_offset = int(round(frac * span))
            return (start + timedelta(days=day_offset)).isoformat()
        threshold = frac * total_daily
        running = 0.0
        for day, count in sorted_daily:
            running += max(0, int(count))
            if running >= threshold:
                return day
        return sorted_daily[-1][0]

    def _month_key_date(month_key: str, idx: int) -> str:
        mk = str(month_key).strip()
        if len(mk) == 7 and mk[4] == "-":
            return f"{mk}-01"
        if mk.isdigit():
            month_n = max(1, min(12, int(mk)))
            return f"{timeline_window[1].year:04d}-{month_n:02d}-01"
        approx_month = 1 + (idx % 12)
        return f"{timeline_window[1].year:04d}-{approx_month:02d}-01"

    static_accretion_floor = 0.18
    static_accretion_span = 0.14 + min(0.18, len(repos) / 72.0)

    def _static_accretion_signal(
        when: str | None,
        *,
        window: tuple[date, date] | None = None,
    ) -> float:
        if timeline_enabled:
            return 1.0
        active_window = window or timeline_window
        when_day = _history_day(when) or active_window[0]
        timeline_span_days = max(1, (active_window[1] - active_window[0]).days)
        reveal_frac = max(
            0.0,
            min(1.0, (when_day - active_window[0]).days / timeline_span_days),
        )
        local_progress = max(
            0.0,
            min(1.0, (mat - reveal_frac) / max(0.05, static_accretion_span)),
        )
        eased = local_progress * local_progress * (3.0 - 2.0 * local_progress)
        base_signal = max(
            0.08,
            static_accretion_floor * (1.0 - 0.40 * reveal_frac),
        )
        return base_signal + (1.0 - base_signal) * eased

    def _timeline_style(
        when: str,
        opacity: float,
        cls: str = "tl-reveal",
        *,
        window: tuple[date, date] | None = None,
    ) -> str:
        active_window = window or timeline_window
        if not timeline_enabled:
            static_signal = _static_accretion_signal(when, window=active_window)
            return (
                f'opacity="{max(0.03, opacity * static_signal):.3f}" '
                f'data-static-accretion="{static_signal:.3f}"'
            )
        delay = map_date_to_loop_delay(
            when,
            active_window,
            duration=loop_duration,
            reveal_fraction=reveal_fraction,
        )
        return (
            f'class="{cls}" '
            f'style="--delay:{delay:.3f}s;--to:{max(0.0, min(1.0, opacity)):.3f};'
            f'--dur:{loop_duration:.2f}s" data-delay="{delay:.3f}" data-when="{when}"'
        )

    def _repo_when(repo: dict) -> str | None:
        return _repo_date(repo, fallback_end=repo_age_anchor)

    def _later_when(*when_values: object) -> str:
        parsed_days = [
            day for value in when_values if (day := _history_day(value)) is not None
        ]
        if not parsed_days:
            return timeline_window[0].isoformat()
        return max(parsed_days).isoformat()

    timeline_start_day, timeline_end_day = timeline_window
    timeline_start_ord = timeline_start_day.toordinal()
    timeline_end_ord = timeline_end_day.toordinal()
    central_peak_day = (
        _history_day(_date_for_activity_fraction(0.58)) or timeline_start_day
    )
    river_carve_day = (
        _history_day(
            _date_for_activity_fraction(
                min(0.82, 0.44 + float(river_flow_profile["velocity_norm"]) * 0.22)
            )
        )
        or central_peak_day
    )

    grid = 200
    elevation = np.zeros((grid, grid))
    base_birth_weight = 0.035
    terrain_birth_mass = np.full((grid, grid), base_birth_weight, dtype=float)
    terrain_birth_ord = np.full(
        (grid, grid),
        float(timeline_start_ord) * base_birth_weight,
        dtype=float,
    )
    terrain_feature_mass = np.zeros((grid, grid), dtype=float)
    terrain_birth_first = np.full((grid, grid), float(timeline_end_ord), dtype=float)
    terrain_birth_latest = np.full((grid, grid), float(timeline_start_ord), dtype=float)

    # ── 1. Subtle base terrain noise ───────────────────────────────
    terrain_oct = max(3, min(7, 3 + total_commits // 6000))
    for gy in range(grid):
        for gx in range(grid):
            base_terrain = noise.fbm(gx / grid * 6, gy / grid * 6, terrain_oct) * 0.08
            macro_relief = (
                noise2.fbm(gx / grid * 2.2 + 13.0, gy / grid * 2.2 + 7.0, 3) * 0.06
            )
            ridge_field = (
                abs(noise2.fbm(gx / grid * 9.0 + 91.0, gy / grid * 9.0 + 37.0, 2))
                * 0.02
            )
            elevation[gy, gx] = base_terrain + macro_relief + ridge_field

    # ── 2. Repos as PRIMARY terrain features (distinct hills) ──────
    # Relative scaling: normalize to this profile's own data range
    all_stars = [r.get("stars", 0) for r in repos] if repos else [1]
    all_ages = [r.get("age_months", 6) for r in repos] if repos else [6]
    max_stars = max(1, max(all_stars))
    min_stars = min(all_stars)
    max_age = max(6, max(all_ages))
    min_age = min(all_ages)

    # ── 2a. Compute initial repo hill positions (hash + repulsion) ──
    repo_positions = []
    for ri, repo in enumerate(repos):
        # Organic position: hash-seeded with repulsion to avoid overlap
        a_idx = (ri * 4) % 56
        (ri * 4 + 4) % 56
        hx = hex_frac(h, a_idx, min(a_idx + 4, 64))
        c_idx = (ri * 4 + 2) % 56
        (ri * 4 + 6) % 56
        hy = hex_frac(h, c_idx, min(c_idx + 4, 64))
        rcx = 0.15 + hx * 0.7
        rcy = 0.15 + hy * 0.7

        # Push apart from existing hills (simple repulsion)
        min_sep = 0.12
        for _ in range(4):
            for px, py, _ in repo_positions:
                ddx, ddy = rcx - px, rcy - py
                d = math.sqrt(ddx * ddx + ddy * ddy)
                if 0.001 < d < min_sep:
                    push = (min_sep - d) * 0.6
                    rcx += ddx / d * push
                    rcy += ddy / d * push
            rcx = max(0.12, min(0.88, rcx))
            rcy = max(0.12, min(0.88, rcy))

        repo_positions.append((rcx, rcy, repo))

    # ── 2b. Optimize hill positions with PSO ──
    if len(repo_positions) >= 2:
        # Extract positions and weights for optimizer
        raw_positions = [
            (rp[0] * MAP_W + MAP_L, rp[1] * MAP_H + MAP_T) for rp in repo_positions
        ]
        hill_weights = [max(1, rp[2].get("stars", 0)) for rp in repo_positions]

        optimized = optimize_layout_pso(
            raw_positions,
            hill_weights,
            MAP_W,
            MAP_H,
            min_spacing=MAP_W / max(len(repo_positions) + 1, 2) * 0.6,
            iterations=100,
            swarm_size=12,
            seed=int(h[:8], 16),
        )

        # Convert back to normalized coordinates and update repo_positions
        repo_positions = [
            ((opt[0] - MAP_L) / MAP_W, (opt[1] - MAP_T) / MAP_H, rp[2])
            for opt, rp in zip(optimized, repo_positions)
        ]
        # Clamp to valid range
        repo_positions = [
            (max(0.08, min(0.92, rp[0])), max(0.08, min(0.92, rp[1])), rp[2])
            for rp in repo_positions
        ]

    # ── 2c. Optimize language terrain hues for color harmony ──
    terrain_hues = [LANG_HUES.get(rp[2].get("language"), 155) for rp in repo_positions]
    if len(terrain_hues) >= 2:
        terrain_hues = optimize_palette_hues(
            terrain_hues,
            max_shift=10.0,
            iterations=100,
            seed=int(h[:8], 16),
        )

    # ── 2d. Apply elevation from optimized positions ──
    for ri, (rcx, rcy, repo) in enumerate(repo_positions):
        repo_stars = repo.get("stars", 0)
        age = repo.get("age_months", 6)
        repo_when_day = (
            _repo_day(repo, fallback_end=repo_age_anchor) or timeline_start_day
        )
        repo_when_ord = repo_when_day.toordinal()

        # Stars -> peak height RELATIVE to this profile's range
        star_frac = (
            (repo_stars - min_stars) / max(1, max_stars - min_stars)
            if max_stars > min_stars
            else 0.5
        )
        peak_h = 0.15 + star_frac * 0.6

        # Age -> hill width RELATIVE to this profile's range
        age_frac = (
            (age - min_age) / max(1, max_age - min_age) if max_age > min_age else 0.5
        )
        sigma = 0.03 + age_frac * 0.08

        # Language-specific terrain texture on this hill
        lang = repo.get("language")
        lang_seed = int(seed_hash({"language": str(lang)})[:4], 16)
        tex_freq, tex_amp = LANG_TERRAIN.get(lang, (10.0, 0.05))

        y_lo = max(0, int((rcy - 3 * sigma) * grid))
        y_hi = min(grid, int((rcy + 3 * sigma) * grid) + 1)
        x_lo = max(0, int((rcx - 3 * sigma) * grid))
        x_hi = min(grid, int((rcx + 3 * sigma) * grid) + 1)
        for gy in range(y_lo, y_hi):
            for gx in range(x_lo, x_hi):
                fx, fy = gx / grid, gy / grid
                dx, dy = fx - rcx, fy - rcy
                base_gaussian = peak_h * math.exp(
                    -(dx * dx + dy * dy) / (2 * sigma * sigma)
                )
                # Language-specific texture frequency and amplitude
                texture = (
                    noise.noise(fx * tex_freq + lang_seed, fy * tex_freq)
                    * tex_amp
                    * base_gaussian
                )
                ridge_tex = (
                    abs(
                        noise2.noise(
                            (fx + lang_seed * 1e-4) * (tex_freq * 0.7),
                            fy * (tex_freq * 0.9),
                        )
                    )
                    * 0.018
                )
                repo_contribution = base_gaussian + texture + ridge_tex * base_gaussian
                elevation[gy, gx] += repo_contribution
                repo_birth_weight = (
                    base_gaussian + abs(texture) + ridge_tex * max(base_gaussian, 0.0)
                )
                if repo_birth_weight > 1e-6:
                    terrain_birth_mass[gy, gx] += repo_birth_weight
                    terrain_birth_ord[gy, gx] += repo_birth_weight * repo_when_ord
                    terrain_feature_mass[gy, gx] += repo_birth_weight
                    terrain_birth_first[gy, gx] = min(
                        terrain_birth_first[gy, gx], float(repo_when_ord)
                    )
                    terrain_birth_latest[gy, gx] = max(
                        terrain_birth_latest[gy, gx], float(repo_when_ord)
                    )

    # ── Place names from topic clusters ──
    topic_clusters = metrics.get("topic_clusters", {})
    top_topic_entries = [
        (topic, count)
        for _index, topic, count in sorted(
            (
                (index, str(topic).strip(), max(1, int(count or 0)))
                for index, (topic, count) in enumerate(topic_clusters.items())
                if str(topic).strip()
            ),
            key=lambda item: (-item[2], item[0]),
        )
    ]

    def _topic_to_place_name(topic: str, elev_val: float) -> str:
        """Convert a topic to a cartographic-style place name."""
        name = topic.replace("-", " ").title()
        if elev_val > 0.7:
            return f"Mt. {name}"
        if elev_val < 0.15:
            return f"{name} Lake"
        if elev_val < 0.3:
            return f"{name} Valley"
        return f"{name} Pass"

    def _topic_cluster_note(count: int) -> str:
        noun = "repo" if count == 1 else "repos"
        return f"{count} linked {noun}"

    def _feature_kind_from_elevation(elev_val: float) -> str:
        if elev_val > 0.7:
            return "mountain"
        if elev_val < 0.15:
            return "lake"
        if elev_val < 0.3:
            return "valley"
        return "pass"

    def _escape_attr(value: object) -> str:
        return (
            str(value)
            .replace("&", "&amp;")
            .replace('"', "&quot;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )

    def _repo_topic_keys(repo: dict) -> set[str]:
        return {
            topic_text.casefold()
            for raw_topic in repo.get("topics") or []
            if (topic_text := str(raw_topic).strip())
        }

    repo_terrain_points: list[tuple[float, float, dict, float]] = []
    topic_repo_positions: dict[str, list[tuple[float, float, dict, float]]] = {}
    for rcx, rcy, repo in repo_positions:
        gx_i = min(grid - 1, max(0, int(rcx * grid)))
        gy_i = min(grid - 1, max(0, int(rcy * grid)))
        repo_elev = float(elevation[gy_i, gx_i])
        repo_sample = (rcx, rcy, repo, repo_elev)
        repo_terrain_points.append(repo_sample)
        for topic_key in _repo_topic_keys(repo):
            topic_repo_positions.setdefault(topic_key, []).append(repo_sample)

    def _pick_topic_host(
        topic: str, rank: int
    ) -> tuple[tuple[float, float, dict, float] | None, bool]:
        direct_candidates = topic_repo_positions.get(str(topic).strip().casefold(), [])
        candidates = direct_candidates or repo_terrain_points
        if not candidates:
            return None, False
        if rank == 0:
            selected = max(
                candidates,
                key=lambda item: (
                    item[3],
                    item[2].get("stars", 0),
                    -item[2].get("age_months", 0),
                ),
            )
        elif rank == 1:
            selected = min(
                candidates,
                key=lambda item: (
                    item[3],
                    -item[2].get("stars", 0),
                    item[2].get("age_months", 0),
                ),
            )
        elif rank == 2:
            selected = min(
                candidates,
                key=lambda item: (
                    abs(item[3] - 0.24),
                    abs(item[3] - 0.18),
                    -item[2].get("stars", 0),
                ),
            )
        else:
            selected = max(
                candidates,
                key=lambda item: (
                    item[2].get("stars", 0),
                    item[3],
                    -item[2].get("age_months", 0),
                ),
            )
        return selected, bool(direct_candidates)

    topic_feature_specs: list[dict[str, object]] = []
    for topic_rank, (topic, topic_count) in enumerate(top_topic_entries):
        host, matched_topic = _pick_topic_host(topic, topic_rank)
        if host is None:
            continue
        rcx, rcy, repo, repo_elev = host
        topic_feature_specs.append(
            {
                "topic": topic,
                "count": topic_count,
                "rank": topic_rank,
                "matched_topic": matched_topic,
                "rcx": rcx,
                "rcy": rcy,
                "repo": repo,
                "elev": repo_elev,
            }
        )

    # ── 3. Ridgeline backbone from monthly contributions ───────────
    max_m = max(monthly.values()) if monthly else 100
    months_sorted = sorted(monthly.keys())
    if len(months_sorted) >= 2:
        ridge_r = 0.2
        for i in range(len(months_sorted) - 1):
            j = i + 1
            mkey1, mkey2 = months_sorted[i], months_sorted[j]
            intensity = (monthly[mkey1] + monthly[mkey2]) / (2 * max(1, max_m))
            angle1 = -math.pi / 2 + i * 2 * math.pi / len(months_sorted)
            angle2 = -math.pi / 2 + j * 2 * math.pi / len(months_sorted)
            p1 = (0.5 + ridge_r * math.cos(angle1), 0.5 + ridge_r * math.sin(angle1))
            p2 = (0.5 + ridge_r * math.cos(angle2), 0.5 + ridge_r * math.sin(angle2))
            ridge_height = intensity * 0.18
            ridge_width = 0.025
            ridge_day = _history_day(_month_key_date(mkey2, j)) or timeline_start_day
            ridge_ord = ridge_day.toordinal()
            # Bounding box for the ridge segment
            min_rx = min(p1[0], p2[0]) - 3 * ridge_width
            max_rx = max(p1[0], p2[0]) + 3 * ridge_width
            min_ry = min(p1[1], p2[1]) - 3 * ridge_width
            max_ry = max(p1[1], p2[1]) + 3 * ridge_width
            y_lo = max(0, int(min_ry * grid))
            y_hi = min(grid, int(max_ry * grid) + 1)
            x_lo = max(0, int(min_rx * grid))
            x_hi = min(grid, int(max_rx * grid) + 1)
            for gy in range(y_lo, y_hi):
                for gx in range(x_lo, x_hi):
                    fx, fy = gx / grid, gy / grid
                    d = _point_to_segment_distance(fx, fy, p1, p2)
                    ridge_contribution = ridge_height * math.exp(
                        -(d * d) / (2 * ridge_width * ridge_width)
                    )
                    elevation[gy, gx] += ridge_contribution
                    if ridge_contribution > 1e-6:
                        ridge_birth_weight = ridge_contribution * 1.15
                        terrain_birth_mass[gy, gx] += ridge_birth_weight
                        terrain_birth_ord[gy, gx] += ridge_birth_weight * ridge_ord
                        terrain_feature_mass[gy, gx] += ridge_birth_weight
                        terrain_birth_first[gy, gx] = min(
                            terrain_birth_first[gy, gx], float(ridge_ord)
                        )
                        terrain_birth_latest[gy, gx] = max(
                            terrain_birth_latest[gy, gx], float(ridge_ord)
                        )

    # ── 4. Central peak (always prominent, scaled to profile) ──────
    # Central peak is always the tallest — height relative to repo count
    central_height = 0.45 + 0.25 * min(1.0, len(repos) / max(1, len(repos) + 2))
    central_sigma = 0.06 + 0.04 * min(1.0, len(repos) / 12)
    central_peak_ord = central_peak_day.toordinal()
    for gy in range(grid):
        for gx in range(grid):
            fx, fy = gx / grid, gy / grid
            dx, dy = fx - 0.5, fy - 0.5
            central_contribution = central_height * math.exp(
                -(dx * dx + dy * dy) / (2 * central_sigma * central_sigma)
            )
            elevation[gy, gx] += central_contribution
            if central_contribution > 1e-6:
                central_birth_weight = central_contribution * 0.82
                terrain_birth_mass[gy, gx] += central_birth_weight
                terrain_birth_ord[gy, gx] += central_birth_weight * central_peak_ord
                terrain_feature_mass[gy, gx] += central_birth_weight
                terrain_birth_first[gy, gx] = min(
                    terrain_birth_first[gy, gx], float(central_peak_ord)
                )
                terrain_birth_latest[gy, gx] = max(
                    terrain_birth_latest[gy, gx], float(central_peak_ord)
                )

    # ── 5. River valleys from saddle points between major peaks ────
    n_rivers = max(2, min(10, 2 + forks // 4 + len(repo_positions) // 10))
    river_paths = []
    # Sample prominence bands across the full ordered repo set so newer/secondary
    # repos can accrete new tributary basins without hiding older terrain.
    sorted_repos = sorted(
        repo_positions, key=lambda rp: rp[2].get("stars", 0), reverse=True
    )
    peak_source_limit = min(
        len(sorted_repos),
        max(5, min(12, 4 + len(sorted_repos) // 2)),
    )
    peak_sources = [
        sorted_repos[idx]
        for idx in _sample_ranked_indices(len(sorted_repos), peak_source_limit)
    ]
    river_starts = []
    if len(peak_sources) >= 2:
        strongest_peak = peak_sources[0]
        for pi in range(len(peak_sources) - 1):
            left_peak = peak_sources[pi]
            right_peak = peak_sources[pi + 1]
            river_starts.append(
                (
                    (left_peak[0] + right_peak[0]) / 2,
                    (left_peak[1] + right_peak[1]) / 2,
                )
            )
        if len(peak_sources) >= 4:
            accent_step = max(2, len(peak_sources) // max(2, n_rivers - 1))
            for accent_index in range(accent_step, len(peak_sources), accent_step):
                accent_peak = peak_sources[accent_index]
                river_starts.append(
                    (
                        (strongest_peak[0] + accent_peak[0]) / 2,
                        (strongest_peak[1] + accent_peak[1]) / 2,
                    )
                )
        deduped_river_starts: list[tuple[float, float]] = []
        seen_river_starts: set[tuple[int, int]] = set()
        for mid_x, mid_y in river_starts:
            rounded_key = (int(round(mid_x * 1000)), int(round(mid_y * 1000)))
            if rounded_key in seen_river_starts:
                continue
            seen_river_starts.add(rounded_key)
            deduped_river_starts.append((mid_x, mid_y))
        river_starts = deduped_river_starts[:n_rivers]
    else:
        # Fallback: random starts if not enough peaks
        for rvi in range(n_rivers):
            river_starts.append(
                (0.5 + rng.uniform(-0.3, 0.3), 0.5 + rng.uniform(-0.3, 0.3))
            )

    # Pad with random starts if we need more rivers
    while len(river_starts) < n_rivers:
        river_starts.append(
            (0.5 + rng.uniform(-0.3, 0.3), 0.5 + rng.uniform(-0.3, 0.3))
        )

    for rvi in range(n_rivers):
        rx, ry = river_starts[rvi]
        rpts = [(rx, ry)]
        river_carve_ord = river_carve_day.toordinal()
        for _ in range(80):
            gxi = min(grid - 2, max(1, int(rx * grid)))
            gyi = min(grid - 2, max(1, int(ry * grid)))
            dedx = (elevation[gyi, gxi + 1] - elevation[gyi, gxi - 1]) / 2
            dedy = (elevation[gyi + 1, gxi] - elevation[gyi - 1, gxi]) / 2
            nv = noise2.noise(rx * 8 + rvi * 10, ry * 8) * 0.3
            rx += -dedx * 0.9 + nv * 0.022
            ry += -dedy * 0.9 + noise2.noise(rx * 5, ry * 5 + rvi * 5) * 0.022
            rx = max(0.02, min(0.98, rx))
            ry = max(0.02, min(0.98, ry))
            rpts.append((rx, ry))
            gxi2 = min(grid - 1, max(0, int(rx * grid)))
            gyi2 = min(grid - 1, max(0, int(ry * grid)))
            for dy in range(-2, 3):
                for dx2 in range(-2, 3):
                    yi = min(grid - 1, max(0, gyi2 + dy))
                    xi = min(grid - 1, max(0, gxi2 + dx2))
                    d = math.sqrt(dy * dy + dx2 * dx2)
                    if d < 3:
                        elevation[yi, xi] -= 0.03 * (1 - d / 3)
                        river_birth_weight = 0.015 * (1 - d / 3)
                        terrain_birth_mass[yi, xi] += river_birth_weight
                        terrain_birth_ord[yi, xi] += (
                            river_birth_weight * river_carve_ord
                        )
                        terrain_feature_mass[yi, xi] += river_birth_weight
                        terrain_birth_first[yi, xi] = min(
                            terrain_birth_first[yi, xi], float(river_carve_ord)
                        )
                        terrain_birth_latest[yi, xi] = max(
                            terrain_birth_latest[yi, xi], float(river_carve_ord)
                        )
        main_path = _chaikin_smooth(rpts, iterations=2)
        river_paths.append(main_path)

        # Tributaries: branch from upper reaches and merge downstream.
        trib_count = min(
            5,
            1
            + (1 if forks > 20 else 0)
            + (1 if contributions > 1200 else 0)
            + len(repo_positions) // 10,
        )
        branch_origin_max = max(6, len(main_path) // 3)
        tributary_limit = min(5, trib_count)
        for tbi in range(tributary_limit):
            bidx = 3 + int((tbi + 1) * branch_origin_max / (tributary_limit + 1))
            if bidx >= len(main_path):
                continue
            brx, bry = main_path[bidx]
            tpts = [(brx, bry)]
            for _ in range(24):
                gxi = min(grid - 2, max(1, int(brx * grid)))
                gyi = min(grid - 2, max(1, int(bry * grid)))
                dedx = (elevation[gyi, gxi + 1] - elevation[gyi, gxi - 1]) / 2
                dedy = (elevation[gyi + 1, gxi] - elevation[gyi - 1, gxi]) / 2
                nudge = noise2.noise(
                    brx * 12 + 17 * (tbi + 1), bry * 12 + 11 * (rvi + 1)
                )
                brx += -dedx * 0.55 + nudge * 0.012
                bry += (
                    -dedy * 0.55 + noise2.noise(brx * 7, bry * 7 + 9 * (tbi + 1)) * 0.01
                )
                brx = max(0.02, min(0.98, brx))
                bry = max(0.02, min(0.98, bry))
                tpts.append((brx, bry))
            river_paths.append(_chaikin_smooth(tpts, iterations=1))

    # Normalize
    e_min, e_max = elevation.min(), elevation.max()
    if e_max > e_min:
        elevation = (elevation - e_min) / (e_max - e_min)

    # Domain warp for organic contour feel
    warp_noise = Noise2D(seed=int(h[24:32], 16))
    warped = np.zeros_like(elevation)
    warped_birth_mass = np.zeros_like(terrain_birth_mass)
    warped_birth_ord = np.zeros_like(terrain_birth_ord)
    warped_feature_mass = np.zeros_like(terrain_feature_mass)
    warped_birth_first = np.zeros_like(terrain_birth_first)
    warped_birth_latest = np.zeros_like(terrain_birth_latest)
    for gy in range(grid):
        for gx in range(grid):
            wx = warp_noise.fbm(gx / 40, gy / 40, 2) * 2.5
            wy = warp_noise.fbm(gx / 40 + 50, gy / 40 + 50, 2) * 2.5
            sx = max(0, min(grid - 1, gx + wx))
            sy = max(0, min(grid - 1, gy + wy))
            x0, y0 = int(sx), int(sy)
            x1_, y1_ = min(x0 + 1, grid - 1), min(y0 + 1, grid - 1)
            fx, fy = sx - x0, sy - y0
            warped[gy, gx] = (
                elevation[y0, x0] * (1 - fx) * (1 - fy)
                + elevation[y0, x1_] * fx * (1 - fy)
                + elevation[y1_, x0] * (1 - fx) * fy
                + elevation[y1_, x1_] * fx * fy
            )
            warped_birth_mass[gy, gx] = (
                terrain_birth_mass[y0, x0] * (1 - fx) * (1 - fy)
                + terrain_birth_mass[y0, x1_] * fx * (1 - fy)
                + terrain_birth_mass[y1_, x0] * (1 - fx) * fy
                + terrain_birth_mass[y1_, x1_] * fx * fy
            )
            warped_birth_ord[gy, gx] = (
                terrain_birth_ord[y0, x0] * (1 - fx) * (1 - fy)
                + terrain_birth_ord[y0, x1_] * fx * (1 - fy)
                + terrain_birth_ord[y1_, x0] * (1 - fx) * fy
                + terrain_birth_ord[y1_, x1_] * fx * fy
            )
            warped_feature_mass[gy, gx] = (
                terrain_feature_mass[y0, x0] * (1 - fx) * (1 - fy)
                + terrain_feature_mass[y0, x1_] * fx * (1 - fy)
                + terrain_feature_mass[y1_, x0] * (1 - fx) * fy
                + terrain_feature_mass[y1_, x1_] * fx * fy
            )
            warped_birth_first[gy, gx] = (
                terrain_birth_first[y0, x0] * (1 - fx) * (1 - fy)
                + terrain_birth_first[y0, x1_] * fx * (1 - fy)
                + terrain_birth_first[y1_, x0] * (1 - fx) * fy
                + terrain_birth_first[y1_, x1_] * fx * fy
            )
            warped_birth_latest[gy, gx] = max(
                terrain_birth_latest[y0, x0],
                terrain_birth_latest[y0, x1_],
                terrain_birth_latest[y1_, x0],
                terrain_birth_latest[y1_, x1_],
            )
    elevation = warped
    terrain_birth_mass = warped_birth_mass
    terrain_birth_ord = warped_birth_ord
    terrain_feature_mass = warped_feature_mass
    terrain_birth_first = warped_birth_first
    terrain_birth_latest = warped_birth_latest

    cell_w = MAP_W / grid
    cell_h = MAP_H / grid

    # Hillshade
    hillshade = np.zeros((grid, grid))
    relief = np.zeros((grid, grid))
    sun_az = math.radians(commit_hour_profile["sun_azimuth"])
    sun_alt = math.radians(commit_hour_profile["sun_altitude"])
    sun_az2 = math.radians(commit_hour_profile["secondary_azimuth"])
    sun_alt2 = math.radians(commit_hour_profile["secondary_altitude"])
    hillshade_primary_weight = commit_hour_profile["primary_weight"]
    hillshade_secondary_weight = 1.0 - hillshade_primary_weight
    hillshade_slope_scale = 4.2 + commit_hour_profile["focus"] * 2.4
    for gy in range(1, grid - 1):
        for gx in range(1, grid - 1):
            dzdx = (elevation[gy, gx + 1] - elevation[gy, gx - 1]) / 2
            dzdy = (elevation[gy + 1, gx] - elevation[gy - 1, gx]) / 2
            slope = math.atan(math.sqrt(dzdx**2 + dzdy**2) * hillshade_slope_scale)
            aspect = math.atan2(-dzdy, dzdx)
            hs = math.cos(sun_alt) * math.cos(slope) + math.sin(sun_alt) * math.sin(
                slope
            ) * math.cos(sun_az - aspect)
            hs2 = math.cos(sun_alt2) * math.cos(slope) + math.sin(sun_alt2) * math.sin(
                slope
            ) * math.cos(sun_az2 - aspect)
            hillshade[gy, gx] = max(
                0,
                min(
                    1,
                    hillshade_primary_weight * ((hs + 1) / 2)
                    + hillshade_secondary_weight * ((hs2 + 1) / 2),
                ),
            )
            curvature = abs(
                elevation[gy, gx + 1]
                + elevation[gy, gx - 1]
                + elevation[gy + 1, gx]
                + elevation[gy - 1, gx]
                - 4 * elevation[gy, gx]
            )
            relief[gy, gx] = max(
                0.0,
                min(1.0, curvature * 18.0 + math.sqrt(dzdx * dzdx + dzdy * dzdy) * 6.0),
            )

    terrain_birth_field = np.where(
        terrain_feature_mass > 1e-6,
        terrain_birth_latest,
        float(timeline_start_ord),
    )

    def _when_from_ordinal(raw_ordinal: float) -> str:
        clamped = max(
            timeline_start_ord,
            min(timeline_end_ord, int(round(raw_ordinal))),
        )
        return date.fromordinal(clamped).isoformat()

    def _birth_when_at_grid(gx: int, gy: int) -> str:
        grid_x = min(grid - 1, max(0, int(gx)))
        grid_y = min(grid - 1, max(0, int(gy)))
        return _when_from_ordinal(float(terrain_birth_field[grid_y, grid_x]))

    def _birth_when_at_map(mx: float, my: float) -> str:
        gx = int(round((mx - MAP_L) / max(cell_w, 1e-6)))
        gy = int(round((my - MAP_T) / max(cell_h, 1e-6)))
        return _birth_when_at_grid(gx, gy)

    def _birth_when_at_norm(nx: float, ny: float) -> str:
        return _birth_when_at_grid(int(round(nx * grid)), int(round(ny * grid)))

    def _chain_birth_when(points: list[tuple[float, float]]) -> str:
        if not points:
            return timeline_start_day.isoformat()
        ordinals = [
            int(
                round(
                    terrain_birth_field[
                        min(
                            grid - 1,
                            max(0, int(round((py - MAP_T) / max(cell_h, 1e-6)))),
                        ),
                        min(
                            grid - 1,
                            max(0, int(round((px - MAP_L) / max(cell_w, 1e-6)))),
                        ),
                    ]
                )
            )
            for px, py in points
        ]
        ordinals.sort()
        ordinal_index = min(len(ordinals) - 1, int(round((len(ordinals) - 1) * 0.65)))
        return _when_from_ordinal(float(ordinals[ordinal_index]))

    # ══════════════════════════════════════════════════════════════
    # BUILD SVG
    # ══════════════════════════════════════════════════════════════
    P = []
    P.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" width="{WIDTH}" height="{HEIGHT}" '
        f'data-peak-commit-hour="{commit_hour_profile["peak_hour"]:.2f}" '
        f'data-sun-azimuth="{commit_hour_profile["sun_azimuth"]:.1f}" '
        f'data-sun-altitude="{commit_hour_profile["sun_altitude"]:.1f}" '
        f'data-flow-tier="{river_flow_profile["tier"]}" '
        f'data-settlement-tier="{settlement_tier}" '
        f'data-activity-series="{activity_series_mode}" '
        f'data-central-rise-date="{central_peak_day.isoformat()}" '
        f'data-river-carve-date="{river_carve_day.isoformat()}" '
        f'data-timeline-start="{timeline_start_day.isoformat()}" '
        f'data-timeline-end="{timeline_end_day.isoformat()}">'
    )
    if timeline_enabled:
        P.append(
            "<style>"
            "@keyframes topoReveal{0%{opacity:0}100%{opacity:var(--to,1)}}"
            ".tl-reveal{opacity:0;animation:topoReveal .8s ease-out var(--delay,0s) both}"
            ".tl-soft{animation-duration:1.15s}"
            ".tl-crisp{animation-duration:.65s}"
            "</style>"
        )

    P.append("<defs>")
    # Organic paper texture (OKLCH pipeline)
    P.append(organic_texture_filter("topoTexture", "paper", intensity=0.3))
    # Paper texture filter (retained for backward compatibility)
    P.append("""<filter id="paper" x="0%" y="0%" width="100%" height="100%"
    color-interpolation-filters="linearRGB">
    <feTurbulence type="fractalNoise" baseFrequency="0.04" numOctaves="5"
      seed="2" stitchTiles="stitch" result="noise"/>
    <feDiffuseLighting in="noise" lighting-color="#ffffff" surfaceScale="1.2" result="lit">
      <feDistantLight azimuth="45" elevation="55"/>
    </feDiffuseLighting>
    <feComposite operator="in" in="lit" in2="SourceGraphic"/>
  </filter>""")
    # Vegetation patterns
    P.append("""<pattern id="trees" width="18" height="16" patternUnits="userSpaceOnUse">
    <circle cx="5" cy="6" r="3" fill="none" stroke="#3a6a1e" stroke-width="0.6" opacity="0.28"/>
    <line x1="5" y1="9" x2="5" y2="13" stroke="#4a5a2a" stroke-width="0.45" opacity="0.2"/>
    <circle cx="14" cy="4" r="2.2" fill="none" stroke="#3a6a1e" stroke-width="0.5" opacity="0.25"/>
    <line x1="14" y1="6.2" x2="14" y2="10" stroke="#4a5a2a" stroke-width="0.4" opacity="0.18"/>
    <circle cx="9" cy="11" r="1.8" fill="none" stroke="#3a6a1e" stroke-width="0.45" opacity="0.22"/>
    <line x1="9" y1="12.8" x2="9" y2="15" stroke="#4a5a2a" stroke-width="0.35" opacity="0.15"/>
  </pattern>""")
    P.append("""<pattern id="marsh" width="14" height="10" patternUnits="userSpaceOnUse">
    <line x1="2" y1="7" x2="2" y2="2" stroke="#5b92c7" stroke-width="0.35" opacity="0.2"/>
    <line x1="1" y1="3" x2="3" y2="3" stroke="#5b92c7" stroke-width="0.3" opacity="0.15"/>
    <line x1="7" y1="7" x2="7" y2="3" stroke="#5b92c7" stroke-width="0.35" opacity="0.2"/>
    <line x1="6" y1="4" x2="8" y2="4" stroke="#5b92c7" stroke-width="0.3" opacity="0.15"/>
    <line x1="12" y1="7" x2="12" y2="2" stroke="#5b92c7" stroke-width="0.35" opacity="0.2"/>
    <line x1="11" y1="3" x2="13" y2="3" stroke="#5b92c7" stroke-width="0.3" opacity="0.15"/>
    <line x1="0" y1="8" x2="14" y2="8" stroke="#5b92c7" stroke-width="0.2" opacity="0.1"/>
  </pattern>""")
    P.append("""<pattern id="waves" width="24" height="8" patternUnits="userSpaceOnUse">
    <path d="M0,4 Q6,1 12,4 Q18,7 24,4" fill="none" stroke="#5b92c7" stroke-width="0.35" opacity="0.18"/>
    <path d="M0,7 Q6,4 12,7 Q18,10 24,7" fill="none" stroke="#5b92c7" stroke-width="0.25" opacity="0.10"/>
  </pattern>""")
    # Rock scree pattern for high elevations
    P.append("""<pattern id="scree" width="10" height="10" patternUnits="userSpaceOnUse">
    <path d="M2,3 L3,1 L4,3Z" fill="none" stroke="#8a7a6a" stroke-width="0.3" opacity="0.15"/>
    <path d="M7,7 L8,5 L9,7Z" fill="none" stroke="#8a7a6a" stroke-width="0.3" opacity="0.12"/>
    <circle cx="5" cy="8" r="0.4" fill="#8a7a6a" opacity="0.10"/>
  </pattern>""")
    # Biome-specific vegetation patterns (language → cartographic vegetation type)
    # Forest biome — dense deciduous canopy with stippling (Python, Ruby, etc.)
    P.append("""<pattern id="biome_forest" width="16" height="14" patternUnits="userSpaceOnUse">
    <circle cx="4" cy="5" r="3.5" fill="none" stroke="#2a6a2e" stroke-width="0.5" opacity="0.16"/>
    <circle cx="12" cy="4" r="2.8" fill="none" stroke="#3a7a3e" stroke-width="0.45" opacity="0.14"/>
    <circle cx="8" cy="10" r="2.5" fill="none" stroke="#2a6a2e" stroke-width="0.4" opacity="0.12"/>
    <circle cx="4" cy="5" r="1.2" fill="#2a6a2e" opacity="0.06"/>
    <circle cx="12" cy="4" r="0.9" fill="#3a7a3e" opacity="0.05"/>
  </pattern>""")
    # Grassland biome — open tufts and stipples (JavaScript, TypeScript)
    P.append("""<pattern id="biome_grassland" width="12" height="10" patternUnits="userSpaceOnUse">
    <line x1="3" y1="8" x2="3" y2="4" stroke="#8a9a3a" stroke-width="0.3" opacity="0.14"/>
    <line x1="2" y1="5" x2="4" y2="4" stroke="#8a9a3a" stroke-width="0.25" opacity="0.10"/>
    <line x1="9" y1="7" x2="9" y2="3.5" stroke="#7a8a4a" stroke-width="0.3" opacity="0.12"/>
    <line x1="8" y1="4.5" x2="10" y2="3.5" stroke="#7a8a4a" stroke-width="0.25" opacity="0.10"/>
    <circle cx="6" cy="6" r="0.3" fill="#8a9a3a" opacity="0.10"/>
  </pattern>""")
    # Alpine biome — sparse dots and tiny flower marks (Go)
    P.append("""<pattern id="biome_alpine" width="14" height="12" patternUnits="userSpaceOnUse">
    <circle cx="3" cy="4" r="0.5" fill="#6a8a7a" opacity="0.12"/>
    <circle cx="10" cy="3" r="0.4" fill="#6a8a7a" opacity="0.10"/>
    <circle cx="7" cy="8" r="0.6" fill="#7a9a8a" opacity="0.10"/>
    <circle cx="12" cy="10" r="0.3" fill="#6a8a7a" opacity="0.08"/>
    <path d="M5,9 L5.5,7.5 L6,9" fill="none" stroke="#6a8a7a" stroke-width="0.2" opacity="0.10"/>
  </pattern>""")
    # Rocky biome — cross-hatching for bare rock (Rust, C, C++)
    P.append("""<pattern id="biome_rocky" width="10" height="10" patternUnits="userSpaceOnUse">
    <line x1="0" y1="0" x2="10" y2="10" stroke="#8a7060" stroke-width="0.2" opacity="0.10"/>
    <line x1="10" y1="0" x2="0" y2="10" stroke="#7a6a5a" stroke-width="0.2" opacity="0.08"/>
    <path d="M3,2 L4,0.5 L5,2Z" fill="none" stroke="#8a7a6a" stroke-width="0.25" opacity="0.10"/>
  </pattern>""")
    # Scrubland biome — sparse low vegetation (Shell)
    P.append("""<pattern id="biome_scrubland" width="16" height="12" patternUnits="userSpaceOnUse">
    <circle cx="4" cy="7" r="1.8" fill="none" stroke="#7a8a5a" stroke-width="0.35" opacity="0.12"/>
    <circle cx="12" cy="5" r="1.4" fill="none" stroke="#7a8a5a" stroke-width="0.3" opacity="0.10"/>
    <circle cx="8" cy="10" r="0.5" fill="#7a8a5a" opacity="0.08"/>
  </pattern>""")
    # Vignette — dark edge framing
    P.append(
        make_radial_gradient(
            "vigTopo",
            "50%",
            "48%",
            "65%",
            [
                ("0%", "#000000", 0.0),
                ("55%", "#000000", 0.0),
                ("85%", "#1a120a", 0.12),
                ("100%", "#100a04", 0.1 + chrome_mat * 0.25),
            ],
        )
    )
    # River flow arrow marker (used when recent_merged_prs present)
    P.append(
        f'<marker id="riverArrow" viewBox="0 0 6 6" refX="3" refY="3" '
        f'markerWidth="4" markerHeight="4" orient="auto">'
        f'<path d="M0,1 L5,3 L0,5" fill="{oklch(0.48, 0.12, 240)}" opacity="0.4"/>'
        f"</marker>"
    )
    # Valley fog / atmospheric haze filter (WorldState-driven)
    P.append(atmospheric_haze_filter("valleyFog", intensity=0.4))
    P.append("</defs>")

    # ── CSS for interactive hover tooltips (works in direct SVG view) ──
    P.append("<style>")
    P.append(".repo-peak{cursor:pointer}")
    P.append(".repo-peak:hover{filter:brightness(1.1)}")
    P.append("</style>")

    # Background with paper texture
    P.append(f'<rect width="{WIDTH}" height="{HEIGHT}" fill="{pal["bg_primary"]}"/>')
    P.append(
        f'<rect width="{WIDTH}" height="{HEIGHT}" fill="{pal["bg_primary"]}" filter="url(#paper)" opacity="0.5"/>'
    )

    # ── Elevation fill + hillshade ────────────────────────────────
    fill_step = 2
    for gy in range(0, grid, fill_step):
        for gx in range(0, grid, fill_step):
            e = elevation[gy, gx]
            hs = hillshade[min(gy, grid - 1), min(gx, grid - 1)]
            c = _topo_color(e)
            r_c = int(c[1:3], 16)
            g_c = int(c[3:5], 16)
            b_c = int(c[5:7], 16)
            sf = 0.30 + hs * 0.95
            rf = relief[min(gy, grid - 1), min(gx, grid - 1)]
            sf *= 0.94 + rf * 0.26
            r_c = max(0, min(255, int(r_c * sf)))
            g_c = max(0, min(255, int(g_c * sf)))
            b_c = max(0, min(255, int(b_c * sf)))
            mx, my = _grid_to_map(gx, gy, cell_w, cell_h)
            elev_op = min(0.9, 0.40 + growth_mat * 1.5)
            elev_when = _birth_when_at_grid(gx, gy)
            P.append(
                f'<rect x="{mx:.1f}" y="{my:.1f}" width="{cell_w * fill_step + 0.5:.1f}" height="{cell_h * fill_step + 0.5:.1f}" '
                f'fill="#{r_c:02x}{g_c:02x}{b_c:02x}" {_timeline_style(elev_when, elev_op, "tl-reveal tl-soft")}/>'
            )

    # ── Water + vegetation overlays ───────────────────────────────
    # Biome type → SVG pattern id mapping
    _BIOME_PATTERN: dict[str, str] = {
        "forest": "biome_forest",
        "grassland": "biome_grassland",
        "alpine": "biome_alpine",
        "rocky": "biome_rocky",
        "scrubland": "biome_scrubland",
        "savanna": "biome_grassland",
        "tropical": "biome_forest",
        "woodland": "biome_forest",
        "mixed": "trees",
    }

    for gy in range(0, grid, 3):
        for gx in range(0, grid, 3):
            e = elevation[min(gy, grid - 1), min(gx, grid - 1)]
            if e < 0.12:
                mx, my = _grid_to_map(gx, gy, cell_w, cell_h)
                P.append(
                    f'<rect x="{mx:.1f}" y="{my:.1f}" width="{cell_w * 3 + 0.5:.1f}" height="{cell_h * 3 + 0.5:.1f}" fill="url(#waves)" opacity="0.5"/>'
                )
    for gy in range(0, grid, 6):
        for gx in range(0, grid, 6):
            e = elevation[min(gy, grid - 1), min(gx, grid - 1)]
            mx, my = _grid_to_map(gx, gy, cell_w, cell_h)
            sw, sh = cell_w * 6, cell_h * 6
            fx_norm, fy_norm = gx / grid, gy / grid

            if 0.10 < e < 0.93:
                # Find nearest repo peak to determine biome-specific vegetation
                nearest_biome = "mixed"
                nearest_dist = float("inf")
                for rpx, rpy, rrepo in repo_positions:
                    d = math.sqrt((fx_norm - rpx) ** 2 + (fy_norm - rpy) ** 2)
                    if d < nearest_dist:
                        nearest_dist = d
                        lang = rrepo.get("language")
                        nearest_biome = LANG_BIOME.get(lang, LANG_BIOME[None])[0]

                # Elevation-correlated biome placement:
                #   forest only below 0.6, rocky only above 0.7, alpine only above 0.6,
                #   grassland/savanna in mid-range (0.3-0.7)
                _elev_ok = {
                    "forest": e < 0.6,
                    "woodland": e < 0.6,
                    "tropical": e < 0.6,
                    "rocky": e > 0.7,
                    "alpine": e > 0.6,
                    "grassland": 0.3 < e < 0.7,
                    "savanna": 0.3 < e < 0.7,
                    "scrubland": 0.2 < e < 0.6,
                    "mixed": 0.15 < e < 0.7,
                }
                biome_fits_elevation = _elev_ok.get(nearest_biome, True)

                if 0.10 < e < 0.20:
                    # Low wetland: marsh overlay
                    marsh_op = 0.4 * _fade(0.10, 0.30)
                    if marsh_op > 0:
                        marsh_when = _birth_when_at_grid(gx, gy)
                        P.append(
                            f'<rect x="{mx:.1f}" y="{my:.1f}" width="{sw:.1f}" height="{sh:.1f}" fill="url(#marsh)" {_timeline_style(marsh_when, marsh_op)}/>'
                        )
                elif 0.80 < e < 0.93:
                    # High elevation: scree overlay
                    scree_op = 0.4 * _fade(0.15, 0.40)
                    if scree_op > 0:
                        scree_when = _birth_when_at_grid(gx, gy)
                        P.append(
                            f'<rect x="{mx:.1f}" y="{my:.1f}" width="{sw:.1f}" height="{sh:.1f}" fill="url(#scree)" {_timeline_style(scree_when, scree_op)}/>'
                        )
                elif 0.20 < e < 0.80 and biome_fits_elevation:
                    # Use biome-specific pattern if close to a repo peak and elevation matches
                    pattern_id = (
                        _BIOME_PATTERN.get(nearest_biome, "trees")
                        if nearest_dist < 0.25
                        else "trees"
                    )
                    tree_op = 0.5 * _fade(0.05, 0.25) * (0.7 + 0.6 * complexity)
                    # Proximity boost: closer to repo = denser vegetation
                    if nearest_dist < 0.15:
                        tree_op *= 1.0 + 0.4 * (1.0 - nearest_dist / 0.15)
                    if tree_op > 0:
                        tree_when = _birth_when_at_grid(gx, gy)
                        P.append(
                            f'<rect x="{mx:.1f}" y="{my:.1f}" width="{sw:.1f}" height="{sh:.1f}" fill="url(#{pattern_id})" {_timeline_style(tree_when, min(0.6, tree_op))}/>'
                        )

    # ── Lakes/ponds in low-lying depressions ────────────────────────
    lake_fade = _fade(0.15, 0.40)
    if lake_fade > 0:
        lake_spots = []
        for gy_lk in range(4, grid - 4, 10):
            for gx_lk in range(4, grid - 4, 10):
                e = elevation[gy_lk, gx_lk]
                if e < 0.08:
                    is_basin = all(
                        elevation[
                            min(grid - 1, max(0, gy_lk + dy_l)),
                            min(grid - 1, max(0, gx_lk + dx_l)),
                        ]
                        >= e - 0.02
                        for dy_l in range(-3, 4, 2)
                        for dx_l in range(-3, 4, 2)
                    )
                    if is_basin:
                        mx_lk, my_lk = _grid_to_map(gx_lk, gy_lk, cell_w, cell_h)
                        lake_spots.append((mx_lk, my_lk))
        for lk_x, lk_y in lake_spots[:3]:
            lr = 6 + rng.uniform(0, 10)
            lry = lr * rng.uniform(0.55, 0.85)
            la = rng.uniform(-15, 15)
            lake_when = _birth_when_at_map(lk_x, lk_y)
            P.append(
                f'<ellipse cx="{lk_x:.1f}" cy="{lk_y:.1f}" rx="{lr:.1f}" ry="{lry:.1f}" '
                f'fill="#90c8e8" stroke="#4a82b7" stroke-width="0.5" '
                f'transform="rotate({la:.0f},{lk_x:.0f},{lk_y:.0f})" '
                f"{_timeline_style(lake_when, 0.45 * lake_fade)}/>"
            )
            # Bathymetric contour rings
            for ring_i in range(1, 3):
                rf = 1 - ring_i * 0.3
                P.append(
                    f'<ellipse cx="{lk_x:.1f}" cy="{lk_y:.1f}" rx="{lr * rf:.1f}" ry="{lry * rf:.1f}" '
                    f'fill="none" stroke="#5b92c7" stroke-width="0.2" '
                    f'transform="rotate({la:.0f},{lk_x:.0f},{lk_y:.0f})" '
                    f"{_timeline_style(lake_when, 0.12, 'tl-reveal tl-crisp')}/>"
                )

    # ── Rivers (widening downstream, fade in gradually) ───────────
    # Data mapping: activity (contributions) -> river flow volume
    river_width_boost = float(river_flow_profile["width_scale"])
    # Data mapping 3: recent_merged_prs → river width enhancement
    _recent_merged_prs = recent_merged_prs
    if isinstance(_recent_merged_prs, list) and len(_recent_merged_prs) > 0:
        _pr_river_scale = 1.0 + min(0.5, len(_recent_merged_prs) * 0.05)
    else:
        _pr_river_scale = 1.0
    activity_flow = (
        min(2.0, 1.0 + contributions / 1500.0) * river_width_boost * _pr_river_scale
    )
    river_fade = _fade(0.03, 0.15)
    rlabel_fade = _fade(0.15, 0.35)
    # Desaturated OKLCH blue for rivers
    river_color = oklch(0.48, 0.12, 240)
    river_shadow_color = oklch(0.35, 0.10, 240)
    river_highlight_color = oklch(0.68, 0.08, 225)
    river_current_opacity = float(river_flow_profile["current_opacity"])
    river_current_ratio = float(river_flow_profile["current_ratio"])
    river_current_dash = float(river_flow_profile["dash"])
    river_current_gap = float(river_flow_profile["gap"])
    if river_fade > 0:
        P.append(
            f'<g id="river-system" data-flow-tier="{river_flow_profile["tier"]}" '
            f'data-width-scale="{activity_flow:.2f}">'
        )
    for rvi, rpts in enumerate(river_paths if river_fade > 0 else []):
        if len(rpts) < 3:
            continue
        # Draw river in segments with width varying by downstream distance
        # Width: 0.3px at start → 1.2px at end, scaled by activity
        n_seg = len(rpts) - 1
        for j in range(0, n_seg - 1, 2):
            frac = j / max(1, n_seg)
            sw_r = (0.5 + frac * 1.2) * activity_flow
            op_r = (0.45 + frac * 0.3) * river_fade
            x1r = MAP_L + rpts[j][0] * MAP_W
            y1r = MAP_T + rpts[j][1] * MAP_H
            if j + 2 < len(rpts):
                x2r = MAP_L + rpts[j + 1][0] * MAP_W
                y2r = MAP_T + rpts[j + 1][1] * MAP_H
                x3r = MAP_L + rpts[j + 2][0] * MAP_W
                y3r = MAP_T + rpts[j + 2][1] * MAP_H
                # Shadow-side darkening stroke offset 0.5px
                seg_when = _later_when(
                    _birth_when_at_norm(rpts[j + 1][0], rpts[j + 1][1]),
                    river_carve_day.isoformat(),
                )
                P.append(
                    f'<path d="M{x1r + 0.5:.1f},{y1r + 0.5:.1f} Q{x2r + 0.5:.1f},{y2r + 0.5:.1f} {x3r + 0.5:.1f},{y3r + 0.5:.1f}" '
                    f'fill="none" stroke="{river_shadow_color}" stroke-width="{sw_r * 0.85:.2f}" {_timeline_style(seg_when, op_r * 0.45, "tl-reveal tl-crisp")} stroke-linecap="round"/>'
                )
                P.append(
                    f'<path d="M{x1r:.1f},{y1r:.1f} Q{x2r:.1f},{y2r:.1f} {x3r:.1f},{y3r:.1f}" '
                    f'fill="none" stroke="{river_color}" stroke-width="{sw_r:.2f}" {_timeline_style(seg_when, op_r, "tl-reveal tl-crisp")} stroke-linecap="round"/>'
                )
                P.append(
                    f'<path d="M{x1r - 0.25:.1f},{y1r - 0.25:.1f} Q{x2r - 0.25:.1f},{y2r - 0.25:.1f} {x3r - 0.25:.1f},{y3r - 0.25:.1f}" '
                    f'fill="none" stroke="{river_highlight_color}" stroke-width="{max(0.18, sw_r * 0.28):.2f}" {_timeline_style(seg_when, op_r * 0.35, "tl-reveal tl-crisp")} stroke-linecap="round"/>'
                )
                if river_current_opacity > 0.08:
                    P.append(
                        f'<path d="M{x1r:.1f},{y1r:.1f} Q{x2r:.1f},{y2r:.1f} {x3r:.1f},{y3r:.1f}" '
                        f'fill="none" stroke="{river_highlight_color}" stroke-width="{max(0.14, sw_r * river_current_ratio):.2f}" '
                        f"{_timeline_style(seg_when, op_r * river_current_opacity, 'tl-reveal tl-crisp')} "
                        f'stroke-dasharray="{river_current_dash:.2f} {river_current_gap:.2f}" stroke-linecap="round"/>'
                    )
            else:
                x2r = MAP_L + rpts[j + 1][0] * MAP_W
                y2r = MAP_T + rpts[j + 1][1] * MAP_H
                # Shadow-side darkening stroke offset 0.5px
                seg_when = _later_when(
                    _birth_when_at_norm(rpts[j + 1][0], rpts[j + 1][1]),
                    river_carve_day.isoformat(),
                )
                P.append(
                    f'<line x1="{x1r + 0.5:.1f}" y1="{y1r + 0.5:.1f}" x2="{x2r + 0.5:.1f}" y2="{y2r + 0.5:.1f}" '
                    f'stroke="{river_shadow_color}" stroke-width="{sw_r * 0.85:.2f}" {_timeline_style(seg_when, op_r * 0.45, "tl-reveal tl-crisp")} stroke-linecap="round"/>'
                )
                P.append(
                    f'<line x1="{x1r:.1f}" y1="{y1r:.1f}" x2="{x2r:.1f}" y2="{y2r:.1f}" '
                    f'stroke="{river_color}" stroke-width="{sw_r:.2f}" {_timeline_style(seg_when, op_r, "tl-reveal tl-crisp")} stroke-linecap="round"/>'
                )
                P.append(
                    f'<line x1="{x1r - 0.25:.1f}" y1="{y1r - 0.25:.1f}" x2="{x2r - 0.25:.1f}" y2="{y2r - 0.25:.1f}" '
                    f'stroke="{river_highlight_color}" stroke-width="{max(0.18, sw_r * 0.28):.2f}" {_timeline_style(seg_when, op_r * 0.35, "tl-reveal tl-crisp")} stroke-linecap="round"/>'
                )
                if river_current_opacity > 0.08:
                    P.append(
                        f'<line x1="{x1r:.1f}" y1="{y1r:.1f}" x2="{x2r:.1f}" y2="{y2r:.1f}" '
                        f'stroke="{river_highlight_color}" stroke-width="{max(0.14, sw_r * river_current_ratio):.2f}" '
                        f"{_timeline_style(seg_when, op_r * river_current_opacity, 'tl-reveal tl-crisp')} "
                        f'stroke-dasharray="{river_current_dash:.2f} {river_current_gap:.2f}" stroke-linecap="round"/>'
                    )
        if len(rpts) > 10 and rlabel_fade > 0:
            mid = len(rpts) // 4
            # Build guide path from river points for textPath
            guide_end = min(mid + 5, len(rpts))
            guide_pts = rpts[mid:guide_end]
            if len(guide_pts) >= 2:
                guide_d = f"M{MAP_L + guide_pts[0][0] * MAP_W:.0f},{MAP_T + guide_pts[0][1] * MAP_H:.0f}"
                for gp in guide_pts[1:]:
                    guide_d += (
                        f" L{MAP_L + gp[0] * MAP_W:.0f},{MAP_T + gp[1] * MAP_H:.0f}"
                    )
                P.append(
                    f'<path id="rv{rvi}" d="{guide_d}" fill="none" stroke="none"/>'
                )
                # Halo
                P.append(
                    f'<text font-family="Georgia,serif" font-size="6.5" fill="#f5f0e8" '
                    f'opacity="{0.5 * rlabel_fade:.2f}" font-style="italic" '
                    f'stroke="#f5f0e8" stroke-width="2.5" stroke-linejoin="round">'
                    f'<textPath href="#rv{rvi}" startOffset="50%" text-anchor="middle">R. {rvi + 1}</textPath></text>'
                )
                # Label
                P.append(
                    f'<text font-family="Georgia,serif" font-size="6.5" fill="#1a4f8a" '
                    f'opacity="{0.5 * rlabel_fade:.2f}" font-style="italic">'
                    f'<textPath href="#rv{rvi}" startOffset="50%" text-anchor="middle">R. {rvi + 1}</textPath></text>'
                )

    # ── Data mapping 3 (cont.): arrow markers along rivers for merged PRs ──
    if (
        isinstance(_recent_merged_prs, list)
        and len(_recent_merged_prs) > 0
        and river_fade > 0
    ):
        for rvi_a, rpts_a in enumerate(river_paths):
            if len(rpts_a) < 10:
                continue
            # Place arrows at 1/4, 1/2, 3/4 along each main river
            for arrow_frac in [0.25, 0.5, 0.75]:
                ai = min(len(rpts_a) - 2, int(arrow_frac * len(rpts_a)))
                ax1 = MAP_L + rpts_a[ai][0] * MAP_W
                ay1 = MAP_T + rpts_a[ai][1] * MAP_H
                ax2 = MAP_L + rpts_a[ai + 1][0] * MAP_W
                ay2 = MAP_T + rpts_a[ai + 1][1] * MAP_H
                P.append(
                    f'<line x1="{ax1:.1f}" y1="{ay1:.1f}" x2="{ax2:.1f}" y2="{ay2:.1f}" '
                    f'stroke="{river_color}" stroke-width="0.6" opacity="{0.35 * river_fade:.2f}" '
                    f'marker-end="url(#riverArrow)"/>'
                )
    if river_fade > 0:
        P.append("</g>")

    # ── Contour lines (warm brown, Swiss style — OKLCH gradient) ──
    # Scale contour density by visual complexity
    _base_n_levels = max(24, min(40, 18 + followers // 6))
    n_levels = int(_base_n_levels * (0.8 + 0.4 * complexity))
    # OKLCH-derived contour colors from palette
    _contour_index_c = oklch_lerp(pal["accent"], pal["text_primary"], 0.6)
    _contour_normal_c = oklch_lerp(pal["accent"], pal["muted"], 0.4)
    levels = [i / n_levels for i in range(1, n_levels)]
    P.append(
        f'<g id="topography-contours" data-recency-band="{repo_recency_profile["band"]}" '
        f'data-recency-mean="{float(repo_recency_profile["mean_recency"]):.3f}" '
        f'data-contour-roughness="{contour_roughness:.3f}" '
        f'data-contour-smoothing-normal="{contour_smooth_normal}" '
        f'data-contour-smoothing-index="{contour_smooth_index}" '
        f'data-foothill-density="{foothill_density:.3f}" '
        f'data-foothill-count="{foothill_count}" '
        f'data-issue-pressure="{issue_pressure:.3f}">'
    )
    for li, level in enumerate(levels):
        is_index = li % 5 == 0
        contour_fade = 1.0 if is_index else _fade(0.03, 0.15)
        if contour_fade <= 0:
            continue
        chains = _extract_contours(elevation, grid, level, cell_w, cell_h)
        # Contour hierarchy: every 5th level (index) gets heavier stroke
        sw = 1.2 if is_index else 0.5
        sc = _contour_index_c if is_index else _contour_normal_c
        op = (0.7 if is_index else 0.35) * contour_fade
        for chain in chains:
            if len(chain) < 2:
                continue
            smooth_chain = _chaikin_smooth(
                chain,
                iterations=contour_smooth_index if is_index else contour_smooth_normal,
            )
            pd = f"M{smooth_chain[0][0]:.1f},{smooth_chain[0][1]:.1f}"
            for j in range(1, len(smooth_chain) - 1, 2):
                if j + 1 < len(smooth_chain):
                    pd += f" Q{smooth_chain[j][0]:.1f},{smooth_chain[j][1]:.1f} {smooth_chain[j + 1][0]:.1f},{smooth_chain[j + 1][1]:.1f}"
                else:
                    pd += f" L{smooth_chain[j][0]:.1f},{smooth_chain[j][1]:.1f}"
            contour_when = _chain_birth_when(smooth_chain)
            P.append(
                f'<path d="{pd}" fill="none" stroke="{sc}" stroke-width="{sw}" {_timeline_style(contour_when, op)} '
                f'stroke-linecap="round" stroke-linejoin="round"/>'
            )
            if is_index:
                P.append(
                    f'<path d="{pd}" fill="none" stroke="{oklch_lerp(_contour_index_c, pal["text_primary"], 0.5)}" stroke-width="{max(0.4, sw * 0.55):.2f}" '
                    f'{_timeline_style(contour_when, op * 0.45, "tl-reveal tl-crisp")} stroke-linecap="round" stroke-linejoin="round"/>'
                )
        # Elevation labels on index contours showing meters
        clabel_fade = _fade(0.10, 0.30)
        if is_index and chains and clabel_fade > 0:
            longest = _chaikin_smooth(max(chains, key=len), iterations=1)
            mid_i = len(longest) // 2
            mid = longest[mid_i]
            # Compute rotation angle along contour for label
            if mid_i + 1 < len(longest):
                nxt = longest[mid_i + 1]
                label_angle = math.degrees(math.atan2(nxt[1] - mid[1], nxt[0] - mid[0]))
            else:
                label_angle = 0
            elev = f"{int(level * 1000)}m"
            P.append(
                f'<text x="{mid[0]:.0f}" y="{mid[1] + 1:.0f}" font-family="monospace" font-size="5.5" '
                f'fill="{oklch_lerp(_contour_index_c, pal["text_primary"], 0.4)}" opacity="{0.7 * clabel_fade:.2f}" text-anchor="middle" '
                f'stroke="rgba(245,240,232,0.8)" stroke-width="2.5" stroke-linejoin="round" paint-order="stroke fill" '
                f'transform="rotate({label_angle:.0f},{mid[0]:.0f},{mid[1]:.0f})">{elev}</text>'
            )

    foothill_fade = _fade(0.04, 0.18)
    if foothill_levels and foothill_fade > 0:
        foothill_color = oklch_lerp(_contour_normal_c, pal["bg_primary"], 0.35)
        foothill_width = 0.38 + foothill_density * 0.18
        foothill_opacity = (0.12 + foothill_density * 0.18) * foothill_fade
        foothill_smooth = max(1, contour_smooth_normal + 1)
        for foothill_level in foothill_levels:
            foothill_chains = _extract_contours(
                elevation, grid, foothill_level, cell_w, cell_h
            )
            for chain in foothill_chains:
                if len(chain) < 2:
                    continue
                smooth_chain = _chaikin_smooth(chain, iterations=foothill_smooth)
                foothill_when = _chain_birth_when(smooth_chain)
                pd = f"M{smooth_chain[0][0]:.1f},{smooth_chain[0][1]:.1f}"
                for j in range(1, len(smooth_chain) - 1, 2):
                    if j + 1 < len(smooth_chain):
                        pd += (
                            f" Q{smooth_chain[j][0]:.1f},{smooth_chain[j][1]:.1f} "
                            f"{smooth_chain[j + 1][0]:.1f},{smooth_chain[j + 1][1]:.1f}"
                        )
                    else:
                        pd += f" L{smooth_chain[j][0]:.1f},{smooth_chain[j][1]:.1f}"
                P.append(
                    f'<path d="{pd}" fill="none" stroke="{foothill_color}" '
                    f'stroke-width="{foothill_width:.2f}" '
                    f'data-band="{repo_recency_profile["band"]}" '
                    f"{_timeline_style(foothill_when, foothill_opacity, 'foothill-contour tl-reveal tl-soft')} "
                    f'stroke-linecap="round" stroke-linejoin="round"/>'
                )
    P.append("</g>")

    # ── Hachures on steep slopes ──────────────────────────────────
    hachure_fade = _fade(0.10, 0.30)
    if hachure_fade > 0:
        for gy in range(2, grid - 2, 3):
            for gx in range(2, grid - 2, 3):
                e = elevation[gy, gx]
                dzdx = abs(
                    elevation[gy, min(gx + 1, grid - 1)] - elevation[gy, max(gx - 1, 0)]
                )
                dzdy = abs(
                    elevation[min(gy + 1, grid - 1), gx] - elevation[max(gy - 1, 0), gx]
                )
                slope = math.sqrt(dzdx**2 + dzdy**2)
                if slope > 0.03 and 0.50 < e < 0.93:
                    mx, my = _grid_to_map(gx, gy, cell_w, cell_h)
                    aspect = math.atan2(-dzdy, dzdx)
                    hlen = min(6, slope * 45)
                    op_h = min(0.3, slope * 3.5) * hachure_fade
                    hachure_when = _birth_when_at_grid(gx, gy)
                    P.append(
                        f'<line x1="{mx:.1f}" y1="{my:.1f}" x2="{mx + hlen * math.cos(aspect):.1f}" '
                        f'y2="{my + hlen * math.sin(aspect):.1f}" stroke="#7a5a3a" stroke-width="0.3" '
                        f"{_timeline_style(hachure_when, op_h, 'tl-reveal tl-crisp')}/>"
                    )

    # ── Snow/ice at highest peaks ──────────────────────────────────
    snow_fade = _fade(0.25, 0.50)
    if snow_fade > 0:
        for gy in range(0, grid, 4):
            for gx in range(0, grid, 4):
                e = elevation[min(gy, grid - 1), min(gx, grid - 1)]
                if e > 0.93:
                    mx, my = _grid_to_map(gx, gy, cell_w, cell_h)
                    snow_when = _birth_when_at_grid(gx, gy)
                    for _ in range(4):
                        sx = mx + rng.uniform(0, cell_w * 3)
                        sy = my + rng.uniform(0, cell_h * 3)
                        P.append(
                            f'<circle cx="{sx:.1f}" cy="{sy:.1f}" r="{rng.uniform(0.3, 0.8):.1f}" '
                            f'fill="#f5f4f2" {_timeline_style(snow_when, 0.25, "tl-reveal tl-crisp")}/>'
                        )
                        if rng.random() > 0.5:
                            P.append(
                                f'<line x1="{sx:.1f}" y1="{sy:.1f}" x2="{sx + rng.uniform(-1.5, 1.5):.1f}" '
                                f'y2="{sy + rng.uniform(-1.5, 1.5):.1f}" stroke="#d0ccc0" stroke-width="0.2" '
                                f"{_timeline_style(snow_when, 0.15, 'tl-reveal tl-crisp')}/>"
                            )

    # ── Cloud/mist wisps (atmospheric suggestion) ─────────────────
    cloud_fade = _fade(0.10, 0.30)
    if cloud_fade > 0:
        for _ in range(int(cloud_fade * 8)):
            cx_cl = rng.uniform(MAP_L + 30, MAP_R - 30)
            cy_cl = rng.uniform(MAP_T + 10, MAP_T + MAP_H * 0.35)
            cw_cl = rng.uniform(25, 70)
            ch_cl = rng.uniform(3, 8)
            # Wispy curve
            cp1x = cx_cl - cw_cl * 0.4
            cp1y = cy_cl - ch_cl * rng.uniform(0.5, 1.2)
            cp2x = cx_cl + cw_cl * 0.4
            cp2y = cy_cl - ch_cl * rng.uniform(0.3, 0.9)
            P.append(
                f'<path d="M{cx_cl - cw_cl * 0.5:.1f},{cy_cl:.1f} '
                f"Q{cp1x:.1f},{cp1y:.1f} {cx_cl:.1f},{cy_cl - ch_cl * 0.6:.1f} "
                f'Q{cp2x:.1f},{cp2y:.1f} {cx_cl + cw_cl * 0.5:.1f},{cy_cl:.1f}" '
                f'fill="none" stroke="#b8b4a8" stroke-width="{rng.uniform(0.4, 0.9):.2f}" '
                f'opacity="{rng.uniform(0.08, 0.16):.2f}" stroke-linecap="round"/>'
            )
            # Secondary parallel wisp
            P.append(
                f'<path d="M{cx_cl - cw_cl * 0.35:.1f},{cy_cl + 2:.1f} '
                f'Q{cx_cl:.1f},{cy_cl - ch_cl * 0.3:.1f} {cx_cl + cw_cl * 0.35:.1f},{cy_cl + 1.5:.1f}" '
                f'fill="none" stroke="#d0ccc0" stroke-width="{rng.uniform(0.2, 0.4):.2f}" '
                f'opacity="{rng.uniform(0.04, 0.07):.2f}" stroke-linecap="round"/>'
            )

    # ── Spot heights (stars -> peak prominence with summit markers) ─
    # Data mapping: more stars = more prominent peaks shown
    star_prominence = min(2.5, 1.0 + stars / 100.0)
    spots = []
    for gy in range(3, grid - 3, 8):
        for gx in range(3, grid - 3, 8):
            e = elevation[gy, gx]
            if e > 0.5 and all(
                elevation[gy + dy, gx + dx] <= e
                for dy in range(-2, 3)
                for dx in range(-2, 3)
                if (dy, dx) != (0, 0)
            ):
                spots.append((*_grid_to_map(gx, gy, cell_w, cell_h), e))
    spots_sorted = sorted(spots, key=lambda s: s[2], reverse=True)
    spot_budget = 18 + min(12, len(repo_positions))
    n_spots = (
        min(len(spots_sorted), max(1, round(spot_budget * star_prominence)))
        if timeline_enabled
        else max(1, round(max(0.18, mat) * spot_budget * star_prominence))
    )
    P.append('<g id="spot-heights">')
    for si_spot, (sx, sy, se) in enumerate(spots_sorted[:n_spots]):
        spot_when = _birth_when_at_map(sx, sy)
        # Top 3 peaks get larger summit markers when stars are high
        if si_spot < 3 and stars > 20:
            # Summit cross marker
            cross_sz = 4.5 + star_prominence
            P.append(
                f'<line x1="{sx:.0f}" y1="{sy - cross_sz:.0f}" x2="{sx:.0f}" y2="{sy + cross_sz:.0f}" '
                f'stroke="#4a3a2a" stroke-width="1.0" {_timeline_style(spot_when, 0.55, "tl-reveal tl-crisp")}/>'
            )
            P.append(
                f'<line x1="{sx - cross_sz:.0f}" y1="{sy:.0f}" x2="{sx + cross_sz:.0f}" y2="{sy:.0f}" '
                f'stroke="#4a3a2a" stroke-width="1.0" {_timeline_style(spot_when, 0.55, "tl-reveal tl-crisp")}/>'
            )
            # Bold summit label
            P.append(
                f'<text x="{sx + 7:.0f}" y="{sy + 2:.0f}" font-family="monospace" font-size="6" '
                f'fill="#2a1a0a" font-weight="bold" {_timeline_style(spot_when, 0.6, "tl-reveal tl-crisp")}>{int(se * 1000)}</text>'
            )
        else:
            P.append(
                f'<polygon points="{sx:.0f},{sy - 4:.0f} {sx - 4:.0f},{sy + 4:.0f} {sx + 4:.0f},{sy + 4:.0f}" '
                f'fill="none" stroke="#4a3a2a" stroke-width="0.7" {_timeline_style(spot_when, 0.5, "tl-reveal tl-crisp")}/>'
            )
            P.append(
                f'<text x="{sx + 6:.0f}" y="{sy + 2:.0f}" font-family="monospace" font-size="5.5" fill="#4a3a2a" '
                f"{_timeline_style(spot_when, 0.5, 'tl-reveal tl-crisp')}>{int(se * 1000)}</text>"
            )
    P.append("</g>")

    # ── Survey benchmarks at secondary peaks ──────────────────────
    bm_fade = _fade(0.25, 0.50)
    if bm_fade > 0:
        bm_max = min(6, max(1, round((2 + len(repo_positions) / 8) * bm_fade)))
        bm_count = 0
        bm_scan_end = min(len(spots_sorted), 4 + bm_max * 4)
        for sx, sy, se in spots_sorted[3:bm_scan_end]:
            if se > 0.6 and bm_count < bm_max:
                bm_when = _birth_when_at_map(sx, sy)
                # BM symbol: circle with horizontal line through it
                P.append(
                    f'<circle cx="{sx:.0f}" cy="{sy:.0f}" r="3" fill="none" '
                    f'stroke="#4a3a2a" stroke-width="0.7" {_timeline_style(bm_when, 0.45, "tl-reveal tl-crisp")}/>'
                )
                P.append(
                    f'<line x1="{sx - 4:.0f}" y1="{sy:.0f}" x2="{sx + 4:.0f}" y2="{sy:.0f}" '
                    f'stroke="#4a3a2a" stroke-width="0.5" {_timeline_style(bm_when, 0.45, "tl-reveal tl-crisp")}/>'
                )
                P.append(
                    f'<text x="{sx + 6:.0f}" y="{sy + 1:.0f}" font-family="monospace" font-size="4.5" '
                    f'fill="#4a3a2a" {_timeline_style(bm_when, 0.45, "tl-reveal tl-crisp")}>BM {int(se * 1000)}</text>'
                )
                bm_count += 1

    # ── Spring labels at river sources ──────────────────────────────
    spring_fade = _fade(0.20, 0.45)
    if spring_fade > 0:
        for rvi, rpts in enumerate(river_paths):
            if len(rpts) > 3:
                sx_r, sy_r = MAP_L + rpts[0][0] * MAP_W, MAP_T + rpts[0][1] * MAP_H
                spring_when = _later_when(
                    _birth_when_at_norm(rpts[0][0], rpts[0][1]),
                    river_carve_day.isoformat(),
                )
                P.append(
                    f'<circle cx="{sx_r:.0f}" cy="{sy_r:.0f}" r="2" fill="#a8d4f0" '
                    f'stroke="#5b92c7" stroke-width="0.3" {_timeline_style(spring_when, 0.3, "tl-reveal tl-soft")}/>'
                )
                P.append(
                    f'<text x="{sx_r + 4:.0f}" y="{sy_r + 1:.0f}" font-family="Georgia,serif" '
                    f'font-size="4" fill="#1a4f8a" font-style="italic" {_timeline_style(spring_when, 0.3, "tl-reveal tl-soft")}>Spr.</text>'
                )

    river_map_paths = [
        [(MAP_L + px * MAP_W, MAP_T + py * MAP_H) for px, py in rpts]
        for rpts in river_paths
        if len(rpts) >= 2
    ]

    # ── Chronological trail (oldest → newest → center) ────────────
    chrono = sorted(
        repo_positions,
        key=lambda rp: (
            _repo_day(rp[2], fallback_end=repo_age_anchor) or timeline_start_day,
            str(rp[2].get("name", "")),
        ),
    )
    waypoints = [(rcx, rcy) for rcx, rcy, _ in chrono]
    waypoints.append((0.5, 0.5))  # end at profile center
    trail_map_path = [(MAP_L + wx * MAP_W, MAP_T + wy * MAP_H) for wx, wy in waypoints]

    if len(waypoints) >= 2:
        trail_when = (
            _repo_when(chrono[0][2]) if chrono else _date_for_activity_fraction(0.2)
        )
        P.append(
            f'<g id="chronology-trail" data-repo-count="{len(chrono)}" '
            'data-cumulative="true">'
        )
        for wi in range(len(waypoints) - 1):
            x1m = MAP_L + waypoints[wi][0] * MAP_W
            y1m = MAP_T + waypoints[wi][1] * MAP_H
            x2m = MAP_L + waypoints[wi + 1][0] * MAP_W
            y2m = MAP_T + waypoints[wi + 1][1] * MAP_H
            cx = (x1m + x2m) / 2 + rng.uniform(-15, 15)
            cy = (y1m + y2m) / 2 + rng.uniform(-15, 15)
            trail_segment = (
                f"M{x1m:.1f},{y1m:.1f} Q{cx:.1f},{cy:.1f} {x2m:.1f},{y2m:.1f}"
            )
            segment_repo_index = min(wi + 1, len(chrono) - 1) if chrono else 0
            segment_when = (
                _repo_when(chrono[segment_repo_index][2]) if chrono else trail_when
            ) or trail_when
            if chrono and wi >= len(chrono) - 1:
                segment_when = _later_when(segment_when, central_peak_day.isoformat())
            P.append(
                f'<path d="{trail_segment}" fill="none" stroke="rgba(255,255,255,0.35)" stroke-width="2.5" '
                f'{_timeline_style(segment_when, 0.35, window=repo_timeline_window)} stroke-linecap="round"/>'
            )
            P.append(
                f'<path d="{trail_segment}" fill="none" stroke="{pal["accent"]}" stroke-width="0.8" '
                f'{_timeline_style(segment_when, 0.35, window=repo_timeline_window)} stroke-dasharray="5 2.5" stroke-linecap="round"/>'
            )

        # Diamond milestone markers with age labels
        for wi, (wx, wy, wrepo) in enumerate(chrono):
            mx_w = MAP_L + wx * MAP_W
            my_w = MAP_T + wy * MAP_H
            age_m = wrepo.get("age_months", 0)
            age_label = f"{age_m // 12}y" if age_m >= 12 else f"{age_m}mo"
            dy_off = 14
            ds = 2.5  # diamond half-size
            milestone_when = _repo_when(wrepo) or _date_for_activity_fraction(
                min(1.0, wi / max(1, len(chrono)))
            )
            P.append(
                f'<polygon points="{mx_w:.0f},{my_w + dy_off - ds:.0f} {mx_w + ds:.0f},{my_w + dy_off:.0f} '
                f'{mx_w:.0f},{my_w + dy_off + ds:.0f} {mx_w - ds:.0f},{my_w + dy_off:.0f}" '
                f'fill="{pal["accent"]}" {_timeline_style(milestone_when, 0.35, window=repo_timeline_window)} stroke="{oklch_lerp(pal["accent"], pal["text_primary"], 0.5)}" stroke-width="0.3"/>'
            )
            P.append(
                f'<text x="{mx_w + 5:.0f}" y="{my_w + dy_off + 1:.0f}" font-family="Georgia,serif" '
                f'font-size="4.5" fill="{pal["text_secondary"]}" {_timeline_style(milestone_when, 0.4, window=repo_timeline_window)} font-style="italic" '
                f'stroke="rgba(245,240,232,0.6)" stroke-width="1.5" stroke-linejoin="round" paint-order="stroke fill"'
                f">{age_label}</text>"
            )
        P.append("</g>")

    label_obstacles = river_map_paths[:]
    if len(trail_map_path) >= 2:
        label_obstacles.append(trail_map_path)

    promoted_topic_limit = min(
        len(topic_feature_specs),
        4 if len(topic_feature_specs) >= 4 and len(repos) >= 6 else 3,
    )

    def _label_span_points(
        text: str,
        x: float,
        y: float,
        anchor: str,
        font_size: float,
    ) -> list[tuple[float, float]]:
        span = max(10.0, len(text) * font_size * 0.34)
        if anchor == "middle":
            return [(x - span * 0.5, y), (x + span * 0.5, y)]
        if anchor == "end":
            return [(x - span, y), (x, y)]
        return [(x, y), (x + span, y)]

    def _render_topic_feature(
        *,
        topic: str,
        topic_count: int,
        rank: int,
        rcx: float,
        rcy: float,
        repo: dict,
        elev_val: float,
        matched_topic: bool,
        place_name: str,
        feature_kind: str,
        candidates: list[tuple[float, float]],
        label_size: float,
        note_size: float,
        label_color: str,
        note_color: str,
        leader_color: str,
    ) -> None:
        mx_tp = MAP_L + rcx * MAP_W
        my_tp = MAP_T + rcy * MAP_H
        topic_when = _repo_when(repo) or _birth_when_at_map(mx_tp, my_tp)
        topic_x, topic_y, clearance = _choose_label_anchor(
            mx_tp,
            my_tp,
            candidates,
            label_obstacles,
        )
        topic_anchor = "middle"
        if topic_x > mx_tp + 3:
            topic_anchor = "start"
        elif topic_x < mx_tp - 3:
            topic_anchor = "end"
        note_y = topic_y + 8
        if note_y > MAP_B - 6:
            note_y = topic_y - 8
        elif note_y < MAP_T + 6:
            note_y = topic_y + 8
        leader_y = topic_y - 4 if note_y > topic_y else topic_y + 4
        leader_mid_x = (mx_tp + topic_x) / 2
        leader_mid_y = (my_tp + leader_y) / 2
        leader_distance = math.hypot(topic_x - mx_tp, leader_y - my_tp)
        cluster_note = _topic_cluster_note(topic_count)

        P.append(
            f'<g class="topic-feature{" topic-feature-promoted" if rank < promoted_topic_limit else ""}" '
            f'data-topic="{_escape_attr(topic)}" '
            f'data-topic-rank="{rank}" '
            f'data-repo="{_escape_attr(repo.get("name", ""))}" '
            f'data-topic-count="{int(topic_count)}" '
            f'data-feature-kind="{feature_kind}" '
            f'data-topic-match="{"direct" if matched_topic else "fallback"}" '
            f'data-feature-elevation="{elev_val:.3f}" '
            f'data-anchor-clearance="{clearance:.1f}">'
        )
        if leader_distance >= 10:
            P.append(
                f'<path class="topic-feature-leader" '
                f'd="M{mx_tp:.1f},{my_tp:.1f} Q{leader_mid_x:.1f},{leader_mid_y - 2.0:.1f} {topic_x:.1f},{leader_y:.1f}" '
                f'fill="none" stroke="{leader_color}" stroke-width="0.55" '
                f'stroke-linecap="round" stroke-dasharray="1.8 1.6" '
                f"{_timeline_style(topic_when, 0.52, 'tl-reveal tl-soft', window=repo_timeline_window)}/>"
            )
            label_obstacles.append(
                [(mx_tp, my_tp), (leader_mid_x, leader_mid_y), (topic_x, leader_y)]
            )
        P.append(
            f'<text x="{topic_x:.0f}" y="{topic_y:.0f}" '
            f'font-family="Georgia, serif" font-size="{label_size:.1f}" font-style="italic" '
            f'fill="#f5f0e8" text-anchor="{topic_anchor}" '
            f'stroke="#f5f0e8" stroke-width="2.1" stroke-linejoin="round" paint-order="stroke fill" '
            f"{_timeline_style(topic_when, 0.65, window=repo_timeline_window)}>"
            f"{place_name}</text>"
        )
        P.append(
            f'<text x="{topic_x:.0f}" y="{topic_y:.0f}" '
            f'font-family="Georgia, serif" font-size="{label_size:.1f}" font-style="italic" '
            f'fill="{label_color}" text-anchor="{topic_anchor}" '
            f"{_timeline_style(topic_when, 0.65, window=repo_timeline_window)}>"
            f"{place_name}</text>"
        )
        P.append(
            f'<text x="{topic_x:.0f}" y="{note_y:.0f}" '
            f'font-family="Georgia, serif" font-size="{note_size:.1f}" letter-spacing="0.8" '
            f'font-variant="small-caps" fill="#f5f0e8" text-anchor="{topic_anchor}" '
            f'stroke="#f5f0e8" stroke-width="1.6" stroke-linejoin="round" paint-order="stroke fill" '
            f"{_timeline_style(topic_when, 0.48, 'tl-reveal tl-soft', window=repo_timeline_window)}>"
            f"{cluster_note}</text>"
        )
        P.append(
            f'<text x="{topic_x:.0f}" y="{note_y:.0f}" '
            f'font-family="Georgia, serif" font-size="{note_size:.1f}" letter-spacing="0.8" '
            f'font-variant="small-caps" fill="{note_color}" text-anchor="{topic_anchor}" '
            f"{_timeline_style(topic_when, 0.48, 'tl-reveal tl-soft', window=repo_timeline_window)}>"
            f"{cluster_note}</text>"
        )
        P.append("</g>")

    # ── Repo landmarks ────────────────────────────────────────────
    for idx_rp, (rcx, rcy, repo) in enumerate(repo_positions):
        lx = MAP_L + rcx * MAP_W
        ly = MAP_T + rcy * MAP_H
        repo_stars = repo.get("stars", 0)
        name = repo.get("name", "")
        repo_lang = repo.get("language", "")
        hue = (
            terrain_hues[idx_rp]
            if idx_rp < len(terrain_hues)
            else LANG_HUES.get(repo.get("language"), 160)
        )
        mc = oklch(0.45, 0.18, hue)
        # Relative marker size: top-star repo gets biggest marker
        star_frac = (
            (repo_stars - min_stars) / max(1, max_stars - min_stars)
            if max_stars > min_stars
            else 0.5
        )
        # Lookup elevation at repo position for tooltip
        _gxi = min(grid - 1, max(0, int(rcx * grid)))
        _gyi = min(grid - 1, max(0, int(rcy * grid)))
        _elev = float(elevation[_gyi, _gxi])
        _elev_label = (
            "summit"
            if _elev > 0.7
            else "ridge"
            if _elev > 0.5
            else "highland"
            if _elev > 0.3
            else "valley"
            if _elev < 0.15
            else "lowland"
        )
        _tt_lang = repo_lang or "?"
        _tt_text = (
            f"{name} \u00b7 {_tt_lang} \u00b7 \u2605{repo_stars} \u00b7 {_elev_label}"
        )
        _tt_text = (
            _tt_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        )
        repo_when = _repo_when(repo) or _birth_when_at_map(lx, ly)
        repo_signal = _static_accretion_signal(repo_when, window=repo_timeline_window)
        label_x, label_y, _ = _choose_label_anchor(
            lx,
            ly,
            [(10, -8), (10, 5), (-10, -8), (-10, 5), (0, -14), (0, 15)],
            label_obstacles,
        )
        label_anchor = "middle"
        if label_x > lx + 2:
            label_anchor = "start"
        elif label_x < lx - 2:
            label_anchor = "end"
        detail_dir = -1 if label_y < ly else 1
        marker_scale = 0.62 + 0.38 * repo_signal
        label_size = max(4.9, 6.5 - max(0, len(repo_positions) - 12) * 0.08)
        label_size *= 0.82 + 0.18 * repo_signal
        detail_size = max(4.0, label_size - 1.5)
        P.append(
            f'<g class="repo-peak" data-repo="{_escape_attr(name)}" '
            f'data-visual-order="{idx_rp}" data-reveal-date="{repo_when}" '
            f'data-static-signal="{repo_signal:.3f}">'
        )
        P.append(f"<title>{_tt_text}</title>")
        if star_frac > 0.7:
            bs = (4 + int(star_frac * 4)) * marker_scale
            P.append(
                f'<rect x="{lx - bs:.1f}" y="{ly - bs:.1f}" width="{bs * 2:.1f}" height="{bs * 2:.1f}" '
                f'fill="{mc}" {_timeline_style(repo_when, 0.5, window=repo_timeline_window)} stroke="#3a2a1a" stroke-width="0.4"/>'
            )
        else:
            mr = (2.5 + star_frac * 5) * marker_scale
            P.append(
                f'<circle cx="{lx:.0f}" cy="{ly:.0f}" r="{mr:.1f}" fill="{mc}" {_timeline_style(repo_when, 0.65, window=repo_timeline_window)} stroke="#fff" stroke-width="0.5"/>'
            )
        P.append(
            f'<text x="{label_x:.0f}" y="{label_y:.0f}" font-family="Georgia,serif" font-size="{label_size:.2f}" '
            f'fill="#2c1a0e" text-anchor="{label_anchor}" {_timeline_style(repo_when, 0.65, window=repo_timeline_window)} font-weight="bold" '
            f'stroke="rgba(245,240,232,0.75)" stroke-width="2.5" stroke-linejoin="round" paint-order="stroke fill">{name}</text>'
        )
        label_obstacles.append(
            _label_span_points(str(name), label_x, label_y, label_anchor, label_size)
        )
        show_detail_note = repo_stars > 0 and (
            len(repo_positions) <= 14 or star_frac >= 0.55 or repo_signal >= 0.72
        )
        if show_detail_note:
            P.append(
                f'<text x="{label_x:.0f}" y="{label_y + 7 * detail_dir:.0f}" font-family="Georgia,serif" font-size="{detail_size:.2f}" '
                f'fill="#5c3a1e" text-anchor="{label_anchor}" {_timeline_style(repo_when, 0.45, window=repo_timeline_window)} font-variant="small-caps" '
                f'stroke="rgba(245,240,232,0.6)" stroke-width="2" stroke-linejoin="round" paint-order="stroke fill"'
                f">{repo_stars} stars</text>"
            )
            label_obstacles.append(
                _label_span_points(
                    f"{repo_stars} stars",
                    label_x,
                    label_y + 7 * detail_dir,
                    label_anchor,
                    detail_size,
                )
            )
        P.append("</g>")

    # ── Topic place names ──────────────────────────────────────
    for topic_spec in topic_feature_specs[promoted_topic_limit:]:
        topic_rank = int(topic_spec["rank"])
        secondary_rank = max(0, topic_rank - promoted_topic_limit)
        _render_topic_feature(
            topic=str(topic_spec["topic"]),
            topic_count=int(topic_spec["count"]),
            rank=topic_rank,
            rcx=float(topic_spec["rcx"]),
            rcy=float(topic_spec["rcy"]),
            repo=topic_spec["repo"],
            elev_val=float(topic_spec["elev"]),
            matched_topic=bool(topic_spec["matched_topic"]),
            place_name=_topic_to_place_name(
                str(topic_spec["topic"]), float(topic_spec["elev"])
            ),
            feature_kind=_feature_kind_from_elevation(float(topic_spec["elev"])),
            candidates=[
                (0, -24),
                (24, -18),
                (-24, -18),
                (28, 8),
                (-28, 8),
                (0, 24),
                (30, 18),
                (-30, 18),
            ],
            label_size=max(
                5.0,
                7.5
                + min(2.0, max(0, int(topic_spec["count"]) - 1) * 0.6)
                - secondary_rank * 0.22,
            ),
            note_size=max(3.8, 5.1 - secondary_rank * 0.12),
            label_color=oklch(0.35, 0.02, 30),
            note_color=pal["muted"],
            leader_color=oklch_lerp(
                pal["border"],
                pal["text_secondary"],
                min(0.75, secondary_rank * 0.08),
            ),
        )

    # ── Named geographic features from topics (hosted by topic-carrying repos) ──
    if topic_feature_specs:
        _feature_color = oklch(0.30, 0.03, 30)
        promoted_feature_specs = [
            (
                "mountain",
                lambda topic: f"Mt. {topic.replace('-', ' ').title()}",
                [
                    (0, -30),
                    (26, -24),
                    (-26, -24),
                    (32, -10),
                    (-32, -10),
                    (26, 10),
                    (-26, 10),
                ],
                9.0,
                5.3,
                _feature_color,
                pal["muted"],
            ),
            (
                "lake",
                lambda topic: f"{topic.replace('-', ' ').title()} Lake",
                [
                    (0, 30),
                    (24, 24),
                    (-24, 24),
                    (30, 10),
                    (-30, 10),
                    (0, -22),
                ],
                8.0,
                5.0,
                "#1a4f8a",
                "#4a82b7",
            ),
            (
                "valley",
                lambda topic: f"{topic.replace('-', ' ').title()} Valley",
                [
                    (0, 28),
                    (24, 20),
                    (-24, 20),
                    (30, 8),
                    (-30, 8),
                    (0, -24),
                ],
                8.0,
                5.0,
                _feature_color,
                pal["muted"],
            ),
            (
                "pass",
                lambda topic: f"{topic.replace('-', ' ').title()} Pass",
                [
                    (0, -26),
                    (24, -10),
                    (-24, -10),
                    (28, 10),
                    (-28, 10),
                    (0, 22),
                ],
                7.6,
                4.8,
                oklch_lerp(_feature_color, pal["accent"], 0.35),
                pal["text_secondary"],
            ),
        ]
        for topic_spec in topic_feature_specs[:promoted_topic_limit]:
            (
                feature_kind,
                feature_label,
                candidates,
                label_size,
                note_size,
                label_color,
                note_color,
            ) = promoted_feature_specs[int(topic_spec["rank"])]
            _render_topic_feature(
                topic=str(topic_spec["topic"]),
                topic_count=int(topic_spec["count"]),
                rank=int(topic_spec["rank"]),
                rcx=float(topic_spec["rcx"]),
                rcy=float(topic_spec["rcy"]),
                repo=topic_spec["repo"],
                elev_val=float(topic_spec["elev"]),
                matched_topic=bool(topic_spec["matched_topic"]),
                place_name=feature_label(str(topic_spec["topic"])),
                feature_kind=feature_kind,
                candidates=candidates,
                label_size=label_size,
                note_size=note_size,
                label_color=label_color,
                note_color=note_color,
                leader_color=oklch_lerp(label_color, pal["border"], 0.45),
            )

    # ── Settlement symbol (followers-driven cartographic markers) ──
    followers_count = metrics.get("followers", 0) or 0
    if followers_count > 0 and repo_positions:
        # Place settlement near center of map at the most prominent repo
        best = max(repo_positions, key=lambda rp: rp[2].get("stars", 0))
        sx_s, sy_s = MAP_L + best[0] * MAP_W, MAP_T + best[1] * MAP_H
        settle_cy = sy_s + 15
        settle_color = pal["text_secondary"]
        settlement_when = _repo_when(best[2]) or _date_for_activity_fraction(0.42)
        P.append(
            f'<g id="settlement-symbol" data-tier="{settlement_tier}" data-followers="{int(followers_count)}" '
            f"{_timeline_style(settlement_when, 0.95, 'tl-reveal tl-soft')}>"
        )

        if settlement_tier == "capital":
            # Capital: 5-point star symbol
            _star_r_out, _star_r_in = 7, 3.2
            _star_pts = []
            for _si in range(10):
                _a = math.radians(-90 + _si * 36)
                _r = _star_r_out if _si % 2 == 0 else _star_r_in
                _star_pts.append(
                    f"{sx_s + _r * math.cos(_a):.1f},{settle_cy + _r * math.sin(_a):.1f}"
                )
            P.append(
                f'<polygon points="{" ".join(_star_pts)}" fill="{settle_color}" opacity="0.6"/>'
            )
        elif settlement_tier == "city":
            # City: double circle
            P.append(
                f'<circle cx="{sx_s:.0f}" cy="{settle_cy:.0f}" r="5" fill="none" stroke="{settle_color}" stroke-width="1" opacity="0.5"/>'
            )
            P.append(
                f'<circle cx="{sx_s:.0f}" cy="{settle_cy:.0f}" r="2.5" fill="{settle_color}" opacity="0.5"/>'
            )
        elif settlement_tier == "town":
            # Town: filled circle
            P.append(
                f'<circle cx="{sx_s:.0f}" cy="{settle_cy:.0f}" r="3" fill="{settle_color}" opacity="0.5"/>'
            )
        elif settlement_tier == "village":
            P.append(
                f'<circle cx="{sx_s:.0f}" cy="{settle_cy:.0f}" r="2.4" fill="{settle_color}" opacity="0.45"/>'
            )
            P.append(
                f'<circle cx="{sx_s:.0f}" cy="{settle_cy:.0f}" r="4.2" fill="none" stroke="{settle_color}" stroke-width="0.5" opacity="0.35"/>'
            )
        elif settlement_tier == "hamlet":
            # Hamlet: small dot
            P.append(
                f'<circle cx="{sx_s:.0f}" cy="{settle_cy:.0f}" r="1.5" fill="{settle_color}" opacity="0.4"/>'
            )
        else:
            # Outpost: faint dot
            P.append(
                f'<circle cx="{sx_s:.0f}" cy="{settle_cy:.0f}" r="1" fill="{settle_color}" opacity="0.3"/>'
            )

        if settlement_tier in {"capital", "city", "town", "village"}:
            settle_x, settle_y, _ = _choose_label_anchor(
                sx_s,
                settle_cy,
                [(0, 14), (11, 6), (-11, 6), (11, -8), (-11, -8)],
                label_obstacles,
            )
            settle_anchor = "middle"
            if settle_x > sx_s + 2:
                settle_anchor = "start"
            elif settle_x < sx_s - 2:
                settle_anchor = "end"
            P.append(
                f'<text x="{settle_x:.0f}" y="{settle_y:.0f}" font-family="Georgia, serif" font-size="6.2" '
                f'font-weight="bold" fill="{settle_color}" text-anchor="{settle_anchor}" opacity="0.55" '
                f'stroke="rgba(245,240,232,0.7)" stroke-width="2" stroke-linejoin="round" paint-order="stroke fill">{metrics.get("label", "")}</text>'
            )
        P.append("</g>")

    # ── Portfolio footprint inset ─────────────────────────────────
    if repo_positions:
        inset_x = MAP_L + 12
        inset_y = MAP_T + 12
        inset_w = 92
        inset_h = 56
        mini_x = inset_x + 6
        mini_y = inset_y + 16
        mini_w = 34
        mini_h = 26
        footprint_when = _date_for_activity_fraction(0.6)
        P.append(
            f'<g id="portfolio-footprint" data-settlement-tier="{settlement_tier}" '
            f'data-flow-tier="{river_flow_profile["tier"]}" data-repos="{len(repo_positions)}" '
            f"{_timeline_style(footprint_when, 0.95, 'tl-reveal tl-soft')}>"
        )
        P.append(
            f'<rect x="{inset_x}" y="{inset_y}" width="{inset_w}" height="{inset_h}" '
            f'fill="{pal["bg_primary"]}" stroke="{pal["border"]}" stroke-width="0.7" rx="2" opacity="0.92"/>'
        )
        P.append(
            f'<text x="{inset_x + 6}" y="{inset_y + 10}" font-family="Georgia,serif" font-size="5.8" '
            f'fill="{pal["text_primary"]}" font-weight="bold" opacity="0.62" letter-spacing="0.8">Footprint</text>'
        )
        P.append(
            f'<rect x="{mini_x}" y="{mini_y}" width="{mini_w}" height="{mini_h}" fill="none" '
            f'stroke="{pal["text_secondary"]}" stroke-width="0.45" opacity="0.45"/>'
        )
        if len(trail_map_path) >= 2:
            mini_d = ""
            for point_i, (tx_i, ty_i) in enumerate(trail_map_path):
                px_i = mini_x + ((tx_i - MAP_L) / MAP_W) * mini_w
                py_i = mini_y + ((ty_i - MAP_T) / MAP_H) * mini_h
                cmd = "M" if point_i == 0 else " L"
                mini_d += f"{cmd}{px_i:.1f},{py_i:.1f}"
            P.append(
                f'<path d="{mini_d}" fill="none" stroke="{pal["accent"]}" stroke-width="0.6" '
                f'opacity="0.32" stroke-dasharray="2 1"/>'
            )
        for rcx_fp, rcy_fp, repo_fp in repo_positions:
            fp_x = mini_x + rcx_fp * mini_w
            fp_y = mini_y + rcy_fp * mini_h
            repo_when = _repo_when(repo_fp) or footprint_when
            fp_signal = _static_accretion_signal(repo_when, window=repo_timeline_window)
            fp_r = (
                0.55
                + min(
                    1.0,
                    repo_fp.get("stars", 0) / max(1, max_stars) * 1.15,
                )
            ) * (0.75 + 0.25 * fp_signal)
            fp_cls = 'class="footprint-repo"' if not timeline_enabled else ""
            P.append(
                f'<circle {fp_cls} data-repo="{_escape_attr(repo_fp.get("name", ""))}" '
                f'cx="{fp_x:.1f}" cy="{fp_y:.1f}" r="{fp_r:.1f}" '
                f'fill="{oklch_lerp(pal["highlight"], pal["accent"], min(1.0, fp_signal * 0.55))}" '
                f"{_timeline_style(repo_when, 0.32 + 0.28 * fp_signal, 'footprint-repo tl-reveal tl-soft', window=repo_timeline_window)}/>"
            )
        P.append(
            f'<circle cx="{mini_x + mini_w / 2:.1f}" cy="{mini_y + mini_h / 2:.1f}" r="1.4" fill="{pal["accent"]}" opacity="0.55"/>'
        )
        inset_text_x = inset_x + 46
        P.append(
            f'<text x="{inset_text_x}" y="{inset_y + 22}" font-family="monospace" font-size="4.6" '
            f'fill="{pal["text_secondary"]}" opacity="0.62">{len(repo_positions)} repos</text>'
        )
        P.append(
            f'<text x="{inset_text_x}" y="{inset_y + 31}" font-family="monospace" font-size="4.6" '
            f'fill="{pal["text_secondary"]}" opacity="0.62">{settlement_title} reach</text>'
        )
        P.append(
            f'<text x="{inset_text_x}" y="{inset_y + 40}" font-family="monospace" font-size="4.6" '
            f'fill="{pal["text_secondary"]}" opacity="0.62">{stars} stars</text>'
        )
        P.append("</g>")

    # ── Contribution streak trail (WorldState-aware) ──────────
    streaks = metrics.get("contribution_streaks", {})
    streak_len = (
        streaks.get("current_streak_months", 0) if isinstance(streaks, dict) else 0
    )
    streak_active = (
        streaks.get("streak_active", False) if isinstance(streaks, dict) else False
    )

    if streak_len > 0 and repo_positions:
        # Trail connects repo hills in order of creation
        trail_repos = sorted(
            repo_positions,
            key=lambda rp: (
                _repo_day(rp[2], fallback_end=repo_age_anchor) or timeline_start_day,
                str(rp[2].get("name", "")),
            ),
        )
        n_trail = min(streak_len, len(trail_repos))
        if n_trail >= 2:
            trail_points = []
            for ti_s in range(n_trail):
                tx_s = MAP_L + trail_repos[ti_s][0] * MAP_W
                ty_s = MAP_T + trail_repos[ti_s][1] * MAP_H
                trail_points.append(f"{tx_s:.0f},{ty_s:.0f}")
            trail_d_s = "M" + " L".join(trail_points)
            # Active: dashed red; Broken: grey dashed
            trail_color = (
                oklch(0.48, 0.16, 22) if streak_active else oklch(0.62, 0.03, 200)
            )
            dash_style = (
                ' stroke-dasharray="4,3"'
                if streak_active
                else ' stroke-dasharray="3,4"'
            )
            _trail_opacity = 0.6 if streak_active else 0.35
            # White casing for contrast
            P.append(
                f'<path d="{trail_d_s}" fill="none" stroke="rgba(255,255,255,0.3)" '
                f'stroke-width="2.2" stroke-linecap="round" opacity="{_trail_opacity}"/>'
            )
            P.append(
                f'<path d="{trail_d_s}" fill="none" stroke="{trail_color}" '
                f'stroke-width="1.2"{dash_style} opacity="{_trail_opacity}" stroke-linecap="round"/>'
            )
            # Blaze markers: small rectangles every few peaks (cartographic trail blazes)
            _blaze_interval = max(2, n_trail // 4)
            for ti_s in range(0, n_trail, _blaze_interval):
                bx_s = MAP_L + trail_repos[ti_s][0] * MAP_W
                by_s = MAP_T + trail_repos[ti_s][1] * MAP_H
                if streak_active:
                    # Red rectangular blaze (painted trail markers)
                    P.append(
                        f'<rect x="{bx_s - 1.5:.0f}" y="{by_s - 3:.0f}" width="3" height="5" '
                        f'fill="{trail_color}" rx="0.5" opacity="0.55"/>'
                    )
                else:
                    # Faded grey blaze
                    P.append(
                        f'<rect x="{bx_s - 1:.0f}" y="{by_s - 2:.0f}" width="2" height="3.5" '
                        f'fill="{trail_color}" rx="0.3" opacity="0.3"/>'
                    )

    # ── Watershed ridge lines (dashed, connecting peaks) ──────────
    ridge_fade = _fade(0.30, 0.55)
    if ridge_fade > 0 and len(sorted_repos) >= 2:
        ridge_source_limit = min(
            len(sorted_repos),
            max(4, min(8, 3 + len(sorted_repos) // 4)),
        )
        ridge_sources = [
            sorted_repos[idx]
            for idx in _sample_ranked_indices(len(sorted_repos), ridge_source_limit)
        ]
        for pi_w in range(max(0, len(ridge_sources) - 1)):
            r1 = ridge_sources[pi_w]
            r2 = ridge_sources[pi_w + 1]
            x1_w = MAP_L + r1[0] * MAP_W
            y1_w = MAP_T + r1[1] * MAP_H
            x2_w = MAP_L + r2[0] * MAP_W
            y2_w = MAP_T + r2[1] * MAP_H
            # Sinuous ridge line
            cx_w = (x1_w + x2_w) / 2 + rng.uniform(-10, 10)
            cy_w = (y1_w + y2_w) / 2 + rng.uniform(-10, 10)
            P.append(
                f'<path d="M{x1_w:.1f},{y1_w:.1f} Q{cx_w:.1f},{cy_w:.1f} {x2_w:.1f},{y2_w:.1f}" '
                f'fill="none" stroke="{oklch_lerp(pal["accent"], pal["highlight"], 0.4)}" stroke-width="0.4" opacity="0.12" '
                f'stroke-dasharray="3 2 1 2" stroke-linecap="round"/>'
            )

    # Center marker
    cx_m, cy_m = MAP_L + MAP_W / 2, MAP_T + MAP_H / 2
    P.append(
        f'<circle cx="{cx_m:.0f}" cy="{cy_m:.0f}" r="6" fill="none" stroke="{pal["highlight"]}" stroke-width="1.5" opacity="0.5"/>'
    )
    P.append(
        f'<circle cx="{cx_m:.0f}" cy="{cy_m:.0f}" r="2.5" fill="{pal["highlight"]}" opacity="0.65"/>'
    )
    P.append(
        f'<text x="{cx_m + 10:.0f}" y="{cy_m + 3:.0f}" font-family="Georgia,serif" font-size="9" '
        f'fill="#1a1a1a" font-weight="bold" opacity="0.65" letter-spacing="0.5" '
        f'stroke="rgba(245,240,232,0.8)" stroke-width="3" stroke-linejoin="round" paint-order="stroke fill"'
        f">{metrics.get('label', '')}</text>"
    )

    # ── Month markers ─────────────────────────────────────────────
    month_fade = _fade(0.05, 0.20)
    if month_fade > 0:
        month_labels = [
            "Jan",
            "Feb",
            "Mar",
            "Apr",
            "May",
            "Jun",
            "Jul",
            "Aug",
            "Sep",
            "Oct",
            "Nov",
            "Dec",
        ]
        for mi, mkey in enumerate(months_sorted):
            angle = -math.pi / 2 + mi * 2 * math.pi / max(1, len(months_sorted))
            lx = max(
                MAP_L - 20,
                min(MAP_R + 20, MAP_L + MAP_W / 2 + (MAP_W / 2 + 10) * math.cos(angle)),
            )
            ly = max(
                MAP_T - 20,
                min(MAP_B + 20, MAP_T + MAP_H / 2 + (MAP_H / 2 + 10) * math.sin(angle)),
            )
            mn = int(mkey) - 1 if mkey.isdigit() else mi
            m_op = (0.25 + monthly[mkey] / max(1, max_m) * 0.45) * month_fade
            month_when = _month_key_date(mkey, mi)
            P.append(
                f'<text x="{lx:.0f}" y="{ly:.0f}" text-anchor="middle" dominant-baseline="central" '
                f'font-family="Georgia,serif" font-size="7" fill="{pal["text_secondary"]}" '
                f"{_timeline_style(month_when, m_op)}>{month_labels[mn % 12]}</text>"
            )

    # ── Compass rose — complexity controlled by chrome_mat ──────────
    ccx, ccy, cr = MAP_R - 45, MAP_T + 45, 32
    if chrome_mat < 0.2:
        P.append(
            f'<polygon points="{ccx},{ccy - cr + 4} {ccx - 5},{ccy} {ccx + 5},{ccy}" '
            f'fill="#2c2c2c" opacity="0.35"/>'
        )
        P.append(
            f'<text x="{ccx}" y="{ccy - cr - 2}" text-anchor="middle" '
            f'font-family="Georgia,serif" font-size="8" fill="#2c1a0e" opacity="0.5" font-weight="bold">N</text>'
        )
    else:
        card_len = cr - 4
        card_w = 5
        for label, dx, dy in [("N", 0, -1), ("E", 1, 0), ("S", 0, 1), ("W", -1, 0)]:
            px, py = -dy, dx
            tip_x = ccx + dx * card_len
            tip_y = ccy + dy * card_len
            P.append(
                f'<polygon points="{ccx},{ccy} {ccx + px * card_w},{ccy + py * card_w} {tip_x},{tip_y}" '
                f'fill="#1a1a1a" opacity="0.5" stroke="#0a0a0a" stroke-width="0.3"/>'
            )
            P.append(
                f'<polygon points="{ccx},{ccy} {ccx - px * card_w},{ccy - py * card_w} {tip_x},{tip_y}" '
                f'fill="#f0eeea" opacity="0.65" stroke="#2c2c2c" stroke-width="0.4"/>'
            )
            lbl_d = cr + 7
            fsz = "8" if label == "N" else "6.5"
            fw = "bold" if label == "N" else "normal"
            P.append(
                f'<text x="{ccx + dx * lbl_d:.0f}" y="{ccy + dy * lbl_d:.0f}" text-anchor="middle" '
                f'dominant-baseline="central" font-family="Georgia,serif" font-size="{fsz}" fill="#2c1a0e" opacity="0.5" '
                f'font-weight="{fw}" stroke="rgba(245,240,232,0.7)" stroke-width="2" stroke-linejoin="round" paint-order="stroke fill"'
                f">{label}</text>"
            )
        if chrome_mat >= 0.5:
            P.append(
                f'<circle cx="{ccx}" cy="{ccy}" r="{cr + 2}" fill="none" stroke="#2c2c2c" stroke-width="0.8" opacity="0.35"/>'
            )
            ic_len = card_len * 0.5
            ic_w = 3
            for dx, dy in [(1, -1), (1, 1), (-1, 1), (-1, -1)]:
                d = math.sqrt(2)
                ndx, ndy = dx / d, dy / d
                px, py = -ndy, ndx
                tip_x = ccx + ndx * ic_len
                tip_y = ccy + ndy * ic_len
                P.append(
                    f'<polygon points="{ccx},{ccy} {ccx + px * ic_w},{ccy + py * ic_w} {tip_x},{tip_y}" '
                    f'fill="#2c2c2c" opacity="0.2"/>'
                )
                P.append(
                    f'<polygon points="{ccx},{ccy} {ccx - px * ic_w},{ccy - py * ic_w} {tip_x},{tip_y}" '
                    f'fill="#f0eeea" opacity="0.3" stroke="#2c2c2c" stroke-width="0.2"/>'
                )
        if chrome_mat > 0.75:
            # Decorative double-ring border for 16-point compass
            P.append(
                f'<circle cx="{ccx}" cy="{ccy}" r="{cr + 4}" fill="none" stroke="#2c2c2c" stroke-width="0.3" opacity="0.2"/>'
            )
            P.append(
                f'<circle cx="{ccx}" cy="{ccy}" r="{cr - 1}" fill="none" stroke="#2c2c2c" stroke-width="0.4" opacity="0.25"/>'
            )
            # 16-point tick marks (every 22.5 degrees)
            sixteen_labels = [
                "N",
                "NNE",
                "NE",
                "ENE",
                "E",
                "ESE",
                "SE",
                "SSE",
                "S",
                "SSW",
                "SW",
                "WSW",
                "W",
                "WNW",
                "NW",
                "NNW",
            ]
            for ti, deg in enumerate(range(0, 360, 22)):
                # Approximate: 0, 22.5, 45, 67.5, ... (use 22 to step through 16)
                actual_deg = ti * 22.5
                rad = math.radians(actual_deg)
                is_cardinal = ti % 4 == 0
                is_intercardinal = ti % 2 == 0 and not is_cardinal
                if is_cardinal:
                    r_in, r_out, sw_t = cr - 2, cr + 3, 0.6
                elif is_intercardinal:
                    r_in, r_out, sw_t = cr - 1, cr + 2, 0.4
                else:
                    r_in, r_out, sw_t = cr, cr + 1.5, 0.25
                P.append(
                    f'<line x1="{ccx + r_in * math.sin(rad):.1f}" y1="{ccy - r_in * math.cos(rad):.1f}" '
                    f'x2="{ccx + r_out * math.sin(rad):.1f}" y2="{ccy - r_out * math.cos(rad):.1f}" '
                    f'stroke="#2c2c2c" stroke-width="{sw_t}" opacity="0.3"/>'
                )
                # Secondary direction labels (NE, SE, etc.) in smaller text
                if is_intercardinal and ti < 16:
                    lbl_r = cr + 6
                    lbl = sixteen_labels[ti]
                    P.append(
                        f'<text x="{ccx + lbl_r * math.sin(rad):.0f}" y="{ccy - lbl_r * math.cos(rad):.0f}" '
                        f'text-anchor="middle" dominant-baseline="central" font-family="Georgia,serif" '
                        f'font-size="3.5" fill="#5a4a3a" opacity="0.3">{lbl}</text>'
                    )
            decl = 3 + int(hex_frac(h, 48, 50) * 12)
            P.append(
                f'<text x="{ccx:.0f}" y="{ccy + cr + 14:.0f}" text-anchor="middle" '
                f'font-family="Georgia,serif" font-size="3.5" fill="#5a4a3a" opacity="0.3" '
                f'font-style="italic">MN {decl}\u00b0E</text>'
            )
        P.append(
            f'<circle cx="{ccx}" cy="{ccy}" r="4" fill="#f0eeea" stroke="#1a1a1a" stroke-width="0.8" opacity="0.6"/>'
        )
        P.append(
            f'<circle cx="{ccx}" cy="{ccy}" r="1.8" fill="#1a1a1a" opacity="0.55"/>'
        )

    # ── Neatline & Frame — complexity controlled by chrome_mat ──────
    if chrome_mat < 0.2:
        P.append(
            f'<rect x="{MAP_L - 1}" y="{MAP_T - 1}" width="{MAP_W + 2}" height="{MAP_H + 2}" '
            f'fill="none" stroke="#1a1a1a" stroke-width="0.8" opacity="0.5"/>'
        )
    else:
        P.append(
            f'<rect x="{MAP_L - 8}" y="{MAP_T - 8}" width="{MAP_W + 16}" height="{MAP_H + 16}" '
            f'fill="none" stroke="#1a1a1a" stroke-width="2.5" rx="1" opacity="0.55"/>'
        )
        P.append(
            f'<rect x="{MAP_L - 1}" y="{MAP_T - 1}" width="{MAP_W + 2}" height="{MAP_H + 2}" '
            f'fill="none" stroke="#1a1a1a" stroke-width="0.7" opacity="0.45"/>'
        )
        if chrome_mat >= 0.45:
            # + Alternating B&W border segments + grid lines
            n_ticks = 20
            bw = 6  # border width between neatlines
            for i in range(n_ticks):
                frac = i / n_ticks
                frac_next = (i + 1) / n_ticks
                fill_t = "#1a1a1a" if i % 2 == 0 else "#f5f0e8"
                op_t = 0.3 if i % 2 == 0 else 0.5
                # Top edge
                P.append(
                    f'<rect x="{MAP_L + frac * MAP_W:.1f}" y="{MAP_T - 7:.0f}" '
                    f'width="{(frac_next - frac) * MAP_W:.1f}" height="{bw}" fill="{fill_t}" opacity="{op_t}"/>'
                )
                # Bottom edge
                P.append(
                    f'<rect x="{MAP_L + frac * MAP_W:.1f}" y="{MAP_B + 1:.0f}" '
                    f'width="{(frac_next - frac) * MAP_W:.1f}" height="{bw}" fill="{fill_t}" opacity="{op_t}"/>'
                )
                # Left edge
                P.append(
                    f'<rect x="{MAP_L - 7:.0f}" y="{MAP_T + frac * MAP_H:.1f}" '
                    f'width="{bw}" height="{(frac_next - frac) * MAP_H:.1f}" fill="{fill_t}" opacity="{op_t}"/>'
                )
                # Right edge
                P.append(
                    f'<rect x="{MAP_R + 1:.0f}" y="{MAP_T + frac * MAP_H:.1f}" '
                    f'width="{bw}" height="{(frac_next - frac) * MAP_H:.1f}" fill="{fill_t}" opacity="{op_t}"/>'
                )
            # Interior grid lines
            for i in range(1, 10):
                gx_l = MAP_L + i * MAP_W / 10
                gy_l = MAP_T + i * MAP_H / 10
                P.append(
                    f'<line x1="{gx_l:.0f}" y1="{MAP_T}" x2="{gx_l:.0f}" y2="{MAP_B}" stroke="#8a8868" stroke-width="0.3" opacity="0.20"/>'
                )
                P.append(
                    f'<line x1="{MAP_L}" y1="{gy_l:.0f}" x2="{MAP_R}" y2="{gy_l:.0f}" stroke="#8a8868" stroke-width="0.3" opacity="0.20"/>'
                )
        if chrome_mat > 0.7:
            # + Coordinate tick labels
            base_lon = 120 + int(h[40:42], 16) % 30
            base_lat = 35 + int(h[42:44], 16) % 20
            for i in range(0, 11, 2):
                frac = i / 10
                # Bottom edge longitude labels
                tx = MAP_L + frac * MAP_W
                lon_min = int(hex_frac(h, (i * 2) % 56, (i * 2 + 2) % 56 + 2) * 59)
                P.append(
                    f'<text x="{tx:.0f}" y="{MAP_B + 16:.0f}" text-anchor="middle" '
                    f'font-family="monospace" font-size="4" fill="#5a4a3a" opacity="0.3">'
                    f"{base_lon + i}\u00b0{lon_min:02d}\u2032E</text>"
                )
                # Left edge latitude labels
                ty = MAP_T + frac * MAP_H
                lat_min = int(
                    hex_frac(h, (i * 2 + 10) % 56, (i * 2 + 12) % 56 + 2) * 59
                )
                P.append(
                    f'<text x="{MAP_L - 11:.0f}" y="{ty + 1:.0f}" text-anchor="end" '
                    f'font-family="monospace" font-size="4" fill="#5a4a3a" opacity="0.3">'
                    f"{base_lat + 10 - i}\u00b0{lat_min:02d}\u2032N</text>"
                )

    # ── Scale bar — chrome_mat controlled ──────────────────────────
    if chrome_mat > 0.2:
        sb_x, sb_y, sb_w = MAP_L + 10, MAP_B + 25, 100
        P.append(
            f'<line x1="{sb_x}" y1="{sb_y}" x2="{sb_x + sb_w}" y2="{sb_y}" stroke="#3a2a1a" stroke-width="1.5"/>'
        )
        for tx_sb in [sb_x, sb_x + sb_w, sb_x + sb_w // 2]:
            P.append(
                f'<line x1="{tx_sb}" y1="{sb_y - 4}" x2="{tx_sb}" y2="{sb_y + 4}" stroke="#3a2a1a" stroke-width="0.7"/>'
            )
        if chrome_mat > 0.4:
            P.append(
                f'<rect x="{sb_x}" y="{sb_y - 1.5}" width="{sb_w // 4}" height="3" fill="#5a4a3a" opacity="0.5"/>'
            )
            P.append(
                f'<rect x="{sb_x + sb_w // 2}" y="{sb_y - 1.5}" width="{sb_w // 4}" height="3" fill="#5a4a3a" opacity="0.5"/>'
            )
        P.append(
            f'<text x="{sb_x + sb_w // 2}" y="{sb_y - 6}" text-anchor="middle" font-family="Georgia,serif" font-size="6" fill="#5a4a3a" opacity="0.5">{contributions} contributions</text>'
        )

    # ── Profile cross-section — chrome_mat controlled ──────────────
    if chrome_mat > 0.3:
        # Reference line on map (A—A')
        prof_ref_y = MAP_T + MAP_H / 2
        if chrome_mat > 0.6:
            P.append(
                f'<line x1="{MAP_L}" y1="{prof_ref_y:.0f}" x2="{MAP_R}" y2="{prof_ref_y:.0f}" '
                f'stroke="#7a5a3a" stroke-width="0.5" opacity="0.15" stroke-dasharray="6 3"/>'
            )
            P.append(
                f'<text x="{MAP_L - 3:.0f}" y="{prof_ref_y + 2:.0f}" text-anchor="end" '
                f'font-family="Georgia,serif" font-size="6" fill="#7a5a3a" opacity="0.35" font-weight="bold">A</text>'
            )
            P.append(
                f'<text x="{MAP_R + 3:.0f}" y="{prof_ref_y + 2:.0f}" text-anchor="start" '
                f'font-family="Georgia,serif" font-size="6" fill="#7a5a3a" opacity="0.35" font-weight="bold">A\u2032</text>'
            )

        # Elevation profile
        prof_x, prof_y, prof_w, prof_h = MAP_L + 150, MAP_B + 20, MAP_W - 160, 30
        P.append(
            f'<rect x="{prof_x}" y="{prof_y}" width="{prof_w}" height="{prof_h}" fill="#f5f0e8" stroke="#7a6a4a" stroke-width="0.4" opacity="0.4" rx="1"/>'
        )
        P.append(
            f'<text x="{prof_x}" y="{prof_y - 3}" font-family="Georgia,serif" font-size="5.5" fill="#5c3a1e" opacity="0.45" '
            f'font-variant="small-caps" letter-spacing="0.5">Cross-section A\u2013A\u2032</text>'
        )
        mid_row = grid // 2
        prof_pts = []
        for pi in range(0, grid, 2):
            px_p = prof_x + (pi / grid) * prof_w
            py_p = prof_y + prof_h - elevation[mid_row, pi] * prof_h * 0.85
            prof_pts.append(f"{px_p:.1f},{py_p:.1f}")
        P.append(
            f'<path d="M{prof_x},{prof_y + prof_h} L{" L".join(prof_pts)} L{prof_x + prof_w},{prof_y + prof_h} Z" '
            f'fill="#94bf8b" opacity="0.2"/>'
        )
        P.append(
            f'<polyline points="{" ".join(prof_pts)}" fill="none" stroke="#7a5a3a" stroke-width="0.6" opacity="0.45"/>'
        )
        P.append(
            f'<line x1="{prof_x}" y1="{prof_y + prof_h}" x2="{prof_x + prof_w}" y2="{prof_y + prof_h}" '
            f'stroke="#7a6a4a" stroke-width="0.3" opacity="0.3"/>'
        )
        if chrome_mat > 0.5:
            for et in range(0, 4):
                et_y = prof_y + prof_h - (et / 3) * prof_h * 0.85
                P.append(
                    f'<line x1="{prof_x - 2}" y1="{et_y:.1f}" x2="{prof_x}" y2="{et_y:.1f}" '
                    f'stroke="#7a6a4a" stroke-width="0.25" opacity="0.3"/>'
                )
                P.append(
                    f'<text x="{prof_x - 3}" y="{et_y + 1.5:.1f}" text-anchor="end" '
                    f'font-family="monospace" font-size="3" fill="#7a6a4a" opacity="0.3">{int(et * 330)}</text>'
                )
            P.append(
                f'<text x="{prof_x}" y="{prof_y + prof_h + 7}" font-family="Georgia,serif" '
                f'font-size="4.5" fill="#7a5a3a" opacity="0.35" font-weight="bold">A</text>'
            )
            P.append(
                f'<text x="{prof_x + prof_w}" y="{prof_y + prof_h + 7}" text-anchor="end" '
                f'font-family="Georgia,serif" font-size="4.5" fill="#7a5a3a" opacity="0.35" font-weight="bold">A\u2032</text>'
            )

    # ── Legend (entry count scales with chrome_mat) ────────────────
    leg_x, leg_y = MAP_R - 125, MAP_B + 15
    n_legend_entries = 1 + int(chrome_mat * 4)
    entries = [
        ("circle", pal["highlight"], "Profile center"),
        ("line", oklch_lerp(pal["accent"], pal["muted"], 0.3), "River / lake"),
        ("dash", pal["accent"], "Timeline trail"),
        ("contour", _contour_index_c, "Contour (index)"),
        ("bm", pal["text_secondary"], "Benchmark"),
    ][:n_legend_entries]
    leg_w, leg_h = 115, 14 + len(entries) * 5.5 + (22 if chrome_mat > 0.5 else 0)
    P.append(
        f'<rect x="{leg_x}" y="{leg_y}" width="{leg_w}" height="{leg_h}" '
        f'fill="{pal["bg_primary"]}" stroke="{pal["text_primary"]}" stroke-width="0.8" rx="1.5" opacity="0.95"/>'
    )
    P.append(
        f'<rect x="{leg_x + 2}" y="{leg_y + 2}" width="{leg_w - 4}" height="{leg_h - 4}" '
        f'fill="none" stroke="{pal["border"]}" stroke-width="0.4" rx="0.5" opacity="0.5"/>'
    )
    P.append(
        f'<text x="{leg_x + leg_w / 2:.0f}" y="{leg_y + 10}" text-anchor="middle" '
        f'font-family="Georgia,serif" font-size="6.5" fill="{pal["text_primary"]}" font-weight="bold" opacity="0.6" '
        f'letter-spacing="1.5" font-variant="small-caps">Legend</text>'
    )
    if chrome_mat > 0.5:
        ramp_x, ramp_y, ramp_w = leg_x + 6, leg_y + 14, 60
        # OKLCH hypsometric ramp for elevation legend
        ramp_colors = oklch_gradient(
            [
                (0.65, 0.10, 220),
                (0.60, 0.12, 145),
                (0.70, 0.10, 110),
                (0.80, 0.06, 80),
                (0.75, 0.08, 50),
                (0.70, 0.08, 40),
                (0.85, 0.03, 60),
                (0.92, 0.01, 200),
            ],
            8,
        )
        seg_w = ramp_w / len(ramp_colors)
        for ci, rc in enumerate(ramp_colors):
            P.append(
                f'<rect x="{ramp_x + ci * seg_w:.1f}" y="{ramp_y}" width="{seg_w + 0.5:.1f}" height="5" fill="{rc}" opacity="0.7"/>'
            )
        P.append(
            f'<rect x="{ramp_x}" y="{ramp_y}" width="{ramp_w}" height="5" fill="none" stroke="{pal["text_secondary"]}" stroke-width="0.3" opacity="0.4"/>'
        )
        P.append(
            f'<text x="{ramp_x}" y="{ramp_y + 10}" font-family="monospace" font-size="3.5" fill="{pal["text_secondary"]}" opacity="0.4">Low</text>'
        )
        P.append(
            f'<text x="{ramp_x + ramp_w}" y="{ramp_y + 10}" text-anchor="end" font-family="monospace" font-size="3.5" fill="{pal["text_secondary"]}" opacity="0.4">High</text>'
        )
    entry_offset = (14 + 16) if chrome_mat > 0.5 else 14
    for li_l, (shape, color, text) in enumerate(entries):
        iy = leg_y + entry_offset + li_l * 5.5
        ix = leg_x + 8
        if shape == "circle":
            P.append(
                f'<circle cx="{ix}" cy="{iy}" r="1.8" fill="{color}" opacity="0.55"/>'
            )
        elif shape == "line":
            P.append(
                f'<line x1="{ix - 4}" y1="{iy}" x2="{ix + 4}" y2="{iy}" stroke="{color}" stroke-width="1.2" opacity="0.5" stroke-linecap="round"/>'
            )
        elif shape == "dash":
            P.append(
                f'<line x1="{ix - 4}" y1="{iy}" x2="{ix + 4}" y2="{iy}" stroke="{color}" stroke-width="0.7" opacity="0.4" stroke-dasharray="2 1" stroke-linecap="round"/>'
            )
        elif shape == "contour":
            P.append(
                f'<line x1="{ix - 4}" y1="{iy}" x2="{ix + 4}" y2="{iy}" stroke="{color}" stroke-width="0.8" opacity="0.5" stroke-linecap="round"/>'
            )
        elif shape == "bm":
            P.append(
                f'<circle cx="{ix}" cy="{iy}" r="1.5" fill="none" stroke="{color}" stroke-width="0.4" opacity="0.4"/>'
            )
            P.append(
                f'<line x1="{ix - 2}" y1="{iy}" x2="{ix + 2}" y2="{iy}" stroke="{color}" stroke-width="0.3" opacity="0.4"/>'
            )
        P.append(
            f'<text x="{ix + 7}" y="{iy + 1.5}" font-family="Georgia,serif" font-size="4.5" fill="{pal["text_primary"]}" opacity="0.45">{text}</text>'
        )

    # ── Weather indicator (WorldState-driven) ──
    wx_w, wy_w = MAP_R - 40, MAP_T + 15
    if world.weather == "clear":
        # Sun symbol
        sun_color = oklch(0.80, 0.15, 70)
        P.append(
            f'<circle cx="{wx_w}" cy="{wy_w}" r="6" fill="{sun_color}" opacity="0.8"/>'
        )
        for ray_i in range(8):
            a = ray_i * math.pi / 4
            P.append(
                f'<line x1="{wx_w + 8 * math.cos(a):.1f}" y1="{wy_w + 8 * math.sin(a):.1f}" '
                f'x2="{wx_w + 11 * math.cos(a):.1f}" y2="{wy_w + 11 * math.sin(a):.1f}" '
                f'stroke="{sun_color}" stroke-width="1" opacity="0.6"/>'
            )
    elif world.weather == "cloudy":
        # Cloud shape
        cloud_color = oklch(0.7, 0.03, 220)
        P.append(
            f'<ellipse cx="{wx_w}" cy="{wy_w}" rx="9" ry="4.5" fill="{cloud_color}" opacity="0.45"/>'
        )
        P.append(
            f'<ellipse cx="{wx_w - 5}" cy="{wy_w + 1}" rx="6" ry="3.5" fill="{cloud_color}" opacity="0.35"/>'
        )
        P.append(
            f'<ellipse cx="{wx_w + 4}" cy="{wy_w + 1}" rx="5" ry="3" fill="{cloud_color}" opacity="0.35"/>'
        )
    elif world.weather == "rainy":
        # Cloud + rain lines
        rain_cloud = oklch(0.58, 0.04, 230)
        P.append(
            f'<ellipse cx="{wx_w}" cy="{wy_w}" rx="9" ry="4.5" fill="{rain_cloud}" opacity="0.5"/>'
        )
        P.append(
            f'<ellipse cx="{wx_w - 4}" cy="{wy_w + 1}" rx="6" ry="3.5" fill="{rain_cloud}" opacity="0.4"/>'
        )
        rain_line_color = oklch(0.55, 0.10, 230)
        for _ri in range(4):
            _rx = wx_w - 5 + _ri * 3.5
            P.append(
                f'<line x1="{_rx:.1f}" y1="{wy_w + 5}" x2="{_rx - 1:.1f}" y2="{wy_w + 10}" '
                f'stroke="{rain_line_color}" stroke-width="0.6" opacity="0.5" stroke-linecap="round"/>'
            )
    elif world.weather == "stormy":
        # Cloud + lightning zigzag
        storm_color = oklch(0.50, 0.05, 240)
        P.append(
            f'<ellipse cx="{wx_w}" cy="{wy_w}" rx="10" ry="5" fill="{storm_color}" opacity="0.55"/>'
        )
        P.append(
            f'<ellipse cx="{wx_w - 5}" cy="{wy_w + 2}" rx="7" ry="4" fill="{storm_color}" opacity="0.45"/>'
        )
        # Lightning zigzag
        bolt_color = oklch(0.85, 0.18, 60)
        P.append(
            f'<path d="M{wx_w},{wy_w + 5} l-2,4 3,0 -2,4" '
            f'stroke="{bolt_color}" stroke-width="1.2" fill="none" opacity="0.8" stroke-linecap="round"/>'
        )

    # ── Tiered title cartouche ────────────────────────────────────
    cart_x, cart_y = MAP_L - 5, HEIGHT - 52
    cart_w = 260
    if chrome_mat < 0.2:
        # Simple text-only
        P.append(
            f'<text x="{cart_x + 130}" y="{cart_y + 20}" text-anchor="middle" '
            f'font-family="Georgia,serif" font-size="10" fill="#1a1a1a" font-weight="bold" opacity="0.5" '
            f'letter-spacing="1">Topographic Survey</text>'
        )
        P.append(
            f'<text x="{cart_x + 130}" y="{cart_y + 32}" text-anchor="middle" '
            f'font-family="Georgia,serif" font-size="7" fill="#3a2a1a" opacity="0.4" '
            f'font-style="italic">{metrics.get("label", "")}</text>'
        )
    else:
        cart_h = 44
        P.append(
            f'<rect x="{cart_x}" y="{cart_y}" width="{cart_w}" height="{cart_h}" '
            f'fill="{pal["bg_primary"]}" stroke="{pal["text_primary"]}" stroke-width="1.5" opacity="0.95" rx="1"/>'
        )
        if chrome_mat > 0.3:
            P.append(
                f'<rect x="{cart_x + 3}" y="{cart_y + 3}" width="{cart_w - 6}" height="{cart_h - 6}" '
                f'fill="none" stroke="{pal["text_secondary"]}" stroke-width="0.3" opacity="0.3" rx="0.5"/>'
            )
        P.append(
            f'<text x="{cart_x + cart_w / 2:.0f}" y="{cart_y + 16}" text-anchor="middle" '
            f'font-family="Georgia,serif" font-size="12" fill="{pal["text_primary"]}" font-weight="bold" opacity="0.7" '
            f'letter-spacing="1.5">Topographic Survey</text>'
        )
        P.append(
            f'<text x="{cart_x + cart_w / 2:.0f}" y="{cart_y + 27}" text-anchor="middle" '
            f'font-family="Georgia,serif" font-size="8.5" fill="{pal["text_primary"]}" opacity="0.6" '
            f'font-style="italic">{metrics.get("label", "")}</text>'
        )
        if chrome_mat > 0.4:
            P.append(
                f'<line x1="{cart_x + 10}" y1="{cart_y + 31}" x2="{cart_x + cart_w - 10}" y2="{cart_y + 31}" '
                f'stroke="{pal["text_secondary"]}" stroke-width="0.4" opacity="0.2"/>'
            )
            P.append(
                f'<text x="{cart_x + cart_w / 2:.0f}" y="{cart_y + 39}" text-anchor="middle" '
                f'font-family="Georgia,serif" font-size="5.5" fill="{pal["text_secondary"]}" opacity="0.4" letter-spacing="0.3">'
                f"{len(repos)} repositories  \u00b7  {contributions} contributions  \u00b7  {stars} stars</text>"
            )

    # ── Survey datum note (only chrome_mat > 0.6) ─────────────────
    if chrome_mat > 0.6:
        P.append(
            f'<text x="{MAP_R}" y="{HEIGHT - 8}" text-anchor="end" '
            f'font-family="Georgia,serif" font-size="3.5" fill="#8a7a6a" opacity="0.25" '
            f'font-style="italic">Datum: WGS 84  \u00b7  Contour interval: variable  \u00b7  '
            f"Projection: Mercator</text>"
        )

    # ── Cloud shadows (large faint elliptical overlays) ──────────
    cloud_shadow_noise = Noise2D(seed=int(h[8:16], 16) ^ 0xBEEF)
    for cs_i in range(3):
        # Deterministic placement from seed hash
        cs_frac_x = hex_frac(h, (cs_i * 6) % 56, (cs_i * 6 + 4) % 56 + 2)
        cs_frac_y = hex_frac(h, (cs_i * 6 + 2) % 56, (cs_i * 6 + 6) % 56 + 2)
        cs_cx = MAP_L + cs_frac_x * MAP_W
        cs_cy = MAP_T + cs_frac_y * MAP_H
        # Large organic ellipse — use noise for slight shape distortion
        cs_rx = 40 + cloud_shadow_noise.noise(cs_i * 3.7, 0.5) * 25 + 30
        cs_ry = 25 + cloud_shadow_noise.noise(0.5, cs_i * 3.7) * 15 + 20
        cs_angle = cloud_shadow_noise.noise(cs_i * 2.1, cs_i * 1.3) * 30
        cs_opacity = 0.07 + (cs_i % 2) * 0.04  # 0.07, 0.11, 0.07
        P.append(
            f'<ellipse cx="{cs_cx:.1f}" cy="{cs_cy:.1f}" rx="{cs_rx:.1f}" ry="{cs_ry:.1f}" '
            f'fill="#1a2a3a" opacity="{cs_opacity:.3f}" '
            f'transform="rotate({cs_angle:.1f},{cs_cx:.1f},{cs_cy:.1f})"/>'
        )

    # ── Valley fog / atmospheric haze (WorldState energy-driven) ──
    if world.energy < 0.7:
        fog_opacity = (1.0 - world.energy) * 0.15
        # Find low-elevation valley positions for fog ellipses
        _fog_spots: list[tuple[float, float]] = []
        for _fgy in range(10, grid - 10, 25):
            for _fgx in range(10, grid - 10, 25):
                _fe = elevation[_fgy, _fgx]
                if _fe < 0.25:
                    _fmx, _fmy = _grid_to_map(_fgx, _fgy, cell_w, cell_h)
                    _fog_spots.append((_fmx, _fmy))
        # Place 2-3 fog ellipses at the lowest valley positions
        _fog_spots_sorted = sorted(
            _fog_spots,
            key=lambda fp: elevation[
                min(grid - 1, max(0, int((fp[1] - MAP_T) / cell_h))),
                min(grid - 1, max(0, int((fp[0] - MAP_L) / cell_w))),
            ],
        )
        for _fi, (_ffx, _ffy) in enumerate(_fog_spots_sorted[:3]):
            _fog_rx = 60 + rng.uniform(0, 40)
            _fog_ry = 15 + rng.uniform(0, 10)
            _fog_angle = rng.uniform(-20, 20)
            P.append(
                f'<ellipse cx="{_ffx:.1f}" cy="{_ffy:.1f}" rx="{_fog_rx:.1f}" ry="{_fog_ry:.1f}" '
                f'fill="{pal["muted"]}" opacity="{fog_opacity:.3f}" filter="url(#valleyFog)" '
                f'transform="rotate({_fog_angle:.1f},{_ffx:.1f},{_ffy:.1f})"/>'
            )

    # ══════════════════════════════════════════════════════════════
    # NEW DATA MAPPINGS (additive visual enhancements)
    # ══════════════════════════════════════════════════════════════

    # ── Data mapping 1: releases → flag symbols on peaks ──────────
    _releases = releases
    _release_flag_sites = list(spots_sorted)
    if not _release_flag_sites and repo_positions:
        _release_flag_sites = sorted(
            [
                (
                    MAP_L + rp[0] * MAP_W,
                    MAP_T + rp[1] * MAP_H,
                    float(
                        elevation[
                            min(grid - 1, max(0, int(rp[1] * grid))),
                            min(grid - 1, max(0, int(rp[0] * grid))),
                        ]
                    ),
                )
                for rp in repo_positions
            ],
            key=lambda site: site[2],
            reverse=True,
        )
    if isinstance(_releases, list) and len(_releases) > 0 and _release_flag_sites:
        _n_flags = min(5, len(_releases))
        for _fi_flag in range(_n_flags):
            if _fi_flag < len(_release_flag_sites):
                _flag_x, _flag_y, _flag_e = _release_flag_sites[_fi_flag]
                _flag_h = 8  # flag pole height
                _flag_color = pal["highlight"]
                _release_date_value = _release_date(_releases[_fi_flag])
                _release_when = _later_when(
                    _release_date_value or _birth_when_at_map(_flag_x, _flag_y),
                    _birth_when_at_map(_flag_x, _flag_y),
                )
                P.append(
                    f'<g class="release-flag" data-release-date="{_release_date_value or _release_when}" '
                    f'data-release-reveal-date="{_release_when}" '
                    f"{_timeline_style(_release_when, 0.95, 'tl-reveal tl-soft')}>"
                )
                # Flag pole (vertical line)
                P.append(
                    f'<line x1="{_flag_x:.1f}" y1="{_flag_y:.1f}" '
                    f'x2="{_flag_x:.1f}" y2="{_flag_y - _flag_h:.1f}" '
                    f'stroke="{_flag_color}" stroke-width="0.6" opacity="0.55"/>'
                )
                # Flag triangle at top
                _ftx = _flag_x
                _fty = _flag_y - _flag_h
                P.append(
                    f'<polygon points="{_ftx:.1f},{_fty:.1f} '
                    f"{_ftx + 5:.1f},{_fty + 2:.1f} "
                    f'{_ftx:.1f},{_fty + 4:.1f}" '
                    f'fill="{_flag_color}" opacity="0.50"/>'
                )
                P.append("</g>")

    # ── Data mapping 2: commit_hour_distribution → sun/moon in legend ─
    _commit_hours = metrics.get("commit_hour_distribution", {})
    if isinstance(_commit_hours, dict) and len(_commit_hours) > 0:
        # Determine peak commit hour
        _peak_hour = max(_commit_hours, key=lambda k: _commit_hours.get(k, 0))
        try:
            _peak_h_int = int(_peak_hour)
        except (ValueError, TypeError):
            _peak_h_int = 12
        # Position in upper-right area of legend box
        _sun_moon_x = leg_x + leg_w - 14
        _sun_moon_y = leg_y + 10
        if 6 <= _peak_h_int <= 18:
            # Daytime: draw small sun (circle + rays)
            _sun_c = oklch(0.80, 0.15, 70)
            P.append(
                f'<circle cx="{_sun_moon_x}" cy="{_sun_moon_y}" r="3" '
                f'fill="{_sun_c}" opacity="0.6"/>'
            )
            for _ray_i in range(6):
                _ra = _ray_i * math.pi / 3
                P.append(
                    f'<line x1="{_sun_moon_x + 4 * math.cos(_ra):.1f}" '
                    f'y1="{_sun_moon_y + 4 * math.sin(_ra):.1f}" '
                    f'x2="{_sun_moon_x + 5.5 * math.cos(_ra):.1f}" '
                    f'y2="{_sun_moon_y + 5.5 * math.sin(_ra):.1f}" '
                    f'stroke="{_sun_c}" stroke-width="0.5" opacity="0.45"/>'
                )
        else:
            # Nighttime: draw crescent moon
            _moon_c = oklch(0.80, 0.08, 220)
            P.append(
                f'<circle cx="{_sun_moon_x}" cy="{_sun_moon_y}" r="3.5" '
                f'fill="{_moon_c}" opacity="0.5"/>'
            )
            # Overlap circle to create crescent shape
            P.append(
                f'<circle cx="{_sun_moon_x + 1.5}" cy="{_sun_moon_y - 0.5}" r="3" '
                f'fill="{pal["bg_primary"]}" opacity="0.55"/>'
            )

    # ── Data mapping 4: total_prs → road/path density ─────────────
    _total_prs = metrics.get("total_prs", 0)
    if isinstance(_total_prs, int | float) and _total_prs > 10 and repo_positions:
        _n_paths = min(
            8,
            max(2, int(_total_prs) // 20 + len(repo_positions) // 12),
        )
        _merged_pr_dates = sorted(
            _merged_pr_date(pr)
            for pr in _recent_merged_prs
            if _merged_pr_date(pr) is not None
        )
        # Find settlement position (same logic as settlement symbol)
        _settle_rp = max(repo_positions, key=lambda rp: rp[2].get("stars", 0))
        _settle_mx = MAP_L + _settle_rp[0] * MAP_W
        _settle_my = MAP_T + _settle_rp[1] * MAP_H
        # Connect settlement to nearby repo peaks
        _path_targets = sorted(
            repo_positions,
            key=lambda rp: math.sqrt(
                (rp[0] - _settle_rp[0]) ** 2 + (rp[1] - _settle_rp[1]) ** 2
            ),
        )
        _path_targets = _path_targets[1:]
        sampled_path_targets = [
            _path_targets[idx]
            for idx in _sample_ranked_indices(
                len(_path_targets), min(_n_paths, len(_path_targets))
            )
        ]
        for _pi_path, _trp in enumerate(sampled_path_targets):
            _tx_path = MAP_L + _trp[0] * MAP_W
            _ty_path = MAP_T + _trp[1] * MAP_H
            _path_when = (
                _merged_pr_dates[min(_pi_path, len(_merged_pr_dates) - 1)]
                if _merged_pr_dates
                else _repo_when(_trp[2]) or _birth_when_at_map(_tx_path, _ty_path)
            )
            P.append(
                f'<line x1="{_settle_mx:.1f}" y1="{_settle_my:.1f}" '
                f'x2="{_tx_path:.1f}" y2="{_ty_path:.1f}" '
                f'stroke="{pal["text_secondary"]}" stroke-width="0.5" '
                f'stroke-dasharray="3,3" stroke-linecap="round" '
                f"{_timeline_style(_path_when, 0.15, 'tl-reveal tl-soft')}/>"
            )

    # ── Data mapping 5: total_issues → scree/rough terrain markers ─
    _total_issues = metrics.get("total_issues", 0)
    if isinstance(_total_issues, int | float) and _total_issues > 0:
        _n_scree = min(8, int(_total_issues))
        _scree_color = pal["muted"]
        # Find low-elevation areas for scree placement
        _low_spots: list[tuple[float, float]] = []
        for _sgy in range(5, grid - 5, 15):
            for _sgx in range(5, grid - 5, 15):
                _se = elevation[_sgy, _sgx]
                if _se < 0.30:
                    _smx, _smy = _grid_to_map(_sgx, _sgy, cell_w, cell_h)
                    _low_spots.append((_smx, _smy))
        # Deterministic selection from low spots
        _scree_rng = np.random.default_rng(int(h[:6], 16) ^ 0xCAFE)
        if _low_spots:
            _scree_indices = _scree_rng.choice(
                len(_low_spots), size=min(_n_scree, len(_low_spots)), replace=False
            )
            for _si_scree in _scree_indices:
                _scx, _scy = _low_spots[_si_scree]
                # Cluster of 3-5 tiny dots/marks
                _n_dots = 3 + int(_scree_rng.integers(0, 3))
                for _di in range(_n_dots):
                    _dx_s = _scree_rng.uniform(-4, 4)
                    _dy_s = _scree_rng.uniform(-4, 4)
                    _dr_s = _scree_rng.uniform(0.3, 0.7)
                    P.append(
                        f'<circle cx="{_scx + _dx_s:.1f}" cy="{_scy + _dy_s:.1f}" '
                        f'r="{_dr_s:.1f}" fill="{_scree_color}" opacity="0.20"/>'
                    )

    # ── Data mapping 6: following → compass rose detail ────────────
    _following = metrics.get("following", 0)
    if isinstance(_following, int | float) and _following > 20:
        # Add inner ring and extra detail points to the existing compass rose
        # The compass rose is at (ccx, ccy) with radius cr
        # Add an ornate inner ring
        _inner_r = cr * 0.45
        P.append(
            f'<circle cx="{ccx}" cy="{ccy}" r="{_inner_r:.1f}" '
            f'fill="none" stroke="#2c2c2c" stroke-width="0.5" opacity="0.25"/>'
        )
        # Add 8 secondary tick marks between the main points at inner ring
        for _ci_rose in range(8):
            _rose_a = math.radians(_ci_rose * 45 + 22.5)
            _r_in_rose = _inner_r - 2
            _r_out_rose = _inner_r + 2
            P.append(
                f'<line x1="{ccx + _r_in_rose * math.sin(_rose_a):.1f}" '
                f'y1="{ccy - _r_in_rose * math.cos(_rose_a):.1f}" '
                f'x2="{ccx + _r_out_rose * math.sin(_rose_a):.1f}" '
                f'y2="{ccy - _r_out_rose * math.cos(_rose_a):.1f}" '
                f'stroke="#2c2c2c" stroke-width="0.3" opacity="0.20"/>'
            )
        # Small decorative diamond at compass center
        _cd = 2.5
        P.append(
            f'<polygon points="{ccx},{ccy - _cd} {ccx + _cd},{ccy} '
            f'{ccx},{ccy + _cd} {ccx - _cd},{ccy}" '
            f'fill="none" stroke="#2c2c2c" stroke-width="0.4" opacity="0.20"/>'
        )

    # ── Data mapping 7: orgs_count → territory borders ────────────
    _orgs_count = metrics.get("orgs_count", 0)
    if isinstance(_orgs_count, int | float) and _orgs_count > 0:
        _n_territories = min(4, int(_orgs_count))
        _border_color = pal["border"]
        # Divide map into quadrants for territory borders
        _quadrants = [
            (MAP_L, MAP_T, MAP_W / 2, MAP_H / 2),  # top-left
            (MAP_L + MAP_W / 2, MAP_T, MAP_W / 2, MAP_H / 2),  # top-right
            (MAP_L, MAP_T + MAP_H / 2, MAP_W / 2, MAP_H / 2),  # bottom-left
            (
                MAP_L + MAP_W / 2,
                MAP_T + MAP_H / 2,
                MAP_W / 2,
                MAP_H / 2,
            ),  # bottom-right
        ]
        for _qi in range(_n_territories):
            _qx, _qy, _qw, _qh = _quadrants[_qi]
            # Inset slightly so borders don't overlap the neatline
            _inset = 6
            P.append(
                f'<rect x="{_qx + _inset:.1f}" y="{_qy + _inset:.1f}" '
                f'width="{_qw - 2 * _inset:.1f}" height="{_qh - 2 * _inset:.1f}" '
                f'fill="none" stroke="{_border_color}" stroke-width="0.8" '
                f'stroke-dasharray="8,4" opacity="0.15" rx="2"/>'
            )

    # ── Data mapping 8: public_gists → map annotations ────────────
    _public_gists = metrics.get("public_gists", 0)
    if isinstance(_public_gists, int | float) and _public_gists > 0:
        _n_annotations = min(6, int(_public_gists))
        _anno_labels = [
            "Here be code",
            "Notes",
            "Sketch",
            "Fragments",
            "Draft",
            "Marginalia",
        ]
        _anno_rng = np.random.default_rng(int(h[4:10], 16) ^ 0xBEAD)
        for _ai_gist in range(_n_annotations):
            # Deterministic positions spread across the map
            _ax_frac = 0.1 + (_ai_gist * 0.17) % 0.8
            _ay_frac = 0.15 + ((_ai_gist * 0.23 + 0.1) % 0.7)
            _ax = MAP_L + _ax_frac * MAP_W + _anno_rng.uniform(-15, 15)
            _ay = MAP_T + _ay_frac * MAP_H + _anno_rng.uniform(-10, 10)
            # Clamp within map bounds
            _ax = max(MAP_L + 10, min(MAP_R - 30, _ax))
            _ay = max(MAP_T + 10, min(MAP_B - 10, _ay))
            _anno_text = _anno_labels[_ai_gist % len(_anno_labels)]
            P.append(
                f'<text x="{_ax:.1f}" y="{_ay:.1f}" '
                f'font-family="Georgia,serif" font-size="6" font-style="italic" '
                f'fill="{pal["text_secondary"]}" opacity="0.30">{_anno_text}</text>'
            )

    # ── Data mapping 9: traffic_views_14d → legend visitor count ──
    _traffic_views = metrics.get("traffic_views_14d", 0)
    if isinstance(_traffic_views, int | float) and _traffic_views > 0:
        # Add visitor count text in the legend area, below existing entries
        _vis_y = leg_y + leg_h - 4
        P.append(
            f'<text x="{leg_x + leg_w / 2:.0f}" y="{_vis_y:.0f}" '
            f'text-anchor="middle" font-family="Georgia,serif" font-size="4" '
            f'fill="{pal["text_secondary"]}" opacity="0.35" font-style="italic">'
            f"Visitors: {int(_traffic_views)}</text>"
        )

    # ── Data mapping 10: watchers → watchtower symbols ────────────
    _watchers = metrics.get("watchers", 0)
    if isinstance(_watchers, int | float) and _watchers > 0:
        _n_towers = min(3, int(_watchers) // 10)
        _tower_color = pal["text_secondary"]
        # Place towers at high-elevation spots
        for _ti_tower in range(_n_towers):
            if _ti_tower < len(spots_sorted):
                # Use high-elevation spots, offset from flags
                _tower_idx = min(
                    len(spots_sorted) - 1,
                    _ti_tower
                    + min(
                        5,
                        len(_releases)
                        if isinstance(metrics.get("releases", []), list)
                        else 0,
                    ),
                )
                _twx, _twy, _twe = spots_sorted[_tower_idx]
                # Tower body (thin rectangle)
                _tw_w, _tw_h = 3, 8
                P.append(
                    f'<rect x="{_twx - _tw_w / 2:.1f}" y="{_twy - _tw_h:.1f}" '
                    f'width="{_tw_w}" height="{_tw_h}" '
                    f'fill="{_tower_color}" opacity="0.35" rx="0.3"/>'
                )
                # Tower roof (triangle)
                P.append(
                    f'<polygon points="{_twx - _tw_w:.1f},{_twy - _tw_h:.1f} '
                    f"{_twx:.1f},{_twy - _tw_h - 4:.1f} "
                    f'{_twx + _tw_w:.1f},{_twy - _tw_h:.1f}" '
                    f'fill="{_tower_color}" opacity="0.30"/>'
                )
                # Small window
                P.append(
                    f'<rect x="{_twx - 0.5:.1f}" y="{_twy - _tw_h + 2:.1f}" '
                    f'width="1" height="1.5" fill="{pal["bg_primary"]}" opacity="0.4"/>'
                )

    # ── Foxing / age spots (scaled by mat) ────────────────────────
    for _ in range(int(mat * 8)):
        fx_a = rng.uniform(10, WIDTH - 10)
        fy_a = rng.uniform(10, HEIGHT - 10)
        fr_a = rng.uniform(1.5, 5)
        P.append(
            f'<circle cx="{fx_a:.0f}" cy="{fy_a:.0f}" r="{fr_a:.1f}" '
            f'fill="#d0c0a0" opacity="{rng.uniform(0.03, 0.07):.3f}"/>'
        )

    P.append(f'<rect width="{WIDTH}" height="{HEIGHT}" fill="url(#vigTopo)"/>')

    P.append("</svg>")
    return "\n".join(P)
