"""Physarum Network — agent-based slime-mold activity art.

Repos are food sources; thousands of virtual agents navigate between them,
depositing chemoattractant trails that diffuse/decay into organic filaments.
CSS-animated SVG safe for ``<img>`` embedding (no JS).
"""

# ruff: noqa: E501

from __future__ import annotations

import math
from html import escape
from pathlib import Path
from typing import Any

import numpy as np

from ..utils import get_logger
from .optimize import optimize_placement
from .shared import (
    HEIGHT,
    LANG_HUES,
    WIDTH,
    _build_world_palette_extended,
    compute_world_state,
    oklch,
    svg_footer,
    svg_header,
    volumetric_glow_filter,
)

logger = get_logger(module=__name__)
_WIDTH, _HEIGHT = WIDTH, HEIGHT

try:
    from scipy.ndimage import uniform_filter as _scipy_uniform_filter

    def _diffuse(grid: np.ndarray, size: int = 3) -> np.ndarray:
        return _scipy_uniform_filter(grid, size=size)

except ImportError:  # pragma: no cover

    def _diffuse(grid: np.ndarray, size: int = 3) -> np.ndarray:
        """Box blur via numpy rolling (fallback when scipy unavailable)."""
        result = np.zeros_like(grid)
        half = size // 2
        for dy in range(-half, half + 1):
            for dx in range(-half, half + 1):
                result += np.roll(np.roll(grid, dy, axis=0), dx, axis=1)
        return result / (size * size)


def _voronoi_hue_map(
    G: int,
    food_positions: list[tuple[int, int, float]],
) -> np.ndarray:
    """Assign each grid cell the OKLCH hue of its nearest food source."""
    hue_map = np.full((G, G), 155.0, dtype=np.float64)
    if not food_positions:
        return hue_map
    yy, xx = np.mgrid[:G, :G]
    min_dist = np.full((G, G), np.inf)
    for fx, fy, hue in food_positions:
        dx = (xx - fx + G / 2) % G - G / 2  # toroidal distance
        dy = (yy - fy + G / 2) % G - G / 2
        dist = dx * dx + dy * dy
        closer = dist < min_dist
        hue_map[closer] = hue
        min_dist[closer] = dist[closer]
    return hue_map


def _top_topic_entries(
    topic_clusters: dict[str, int], *, limit: int = 5
) -> list[tuple[str, int, float]]:
    """Return normalized topic counts sorted by strength."""
    cleaned: list[tuple[str, int]] = []
    for topic, count in topic_clusters.items():
        normalized = str(topic).strip().replace("-", " ")
        if not normalized:
            continue
        cleaned.append((normalized, max(1, int(count or 0))))

    cleaned.sort(key=lambda item: (-item[1], item[0].lower()))
    if not cleaned:
        return []

    max_count = cleaned[0][1]
    return [
        (topic, count, count / max_count)
        for topic, count in cleaned[:limit]
    ]


def _repo_topic_signal(
    repo: dict[str, Any],
    topic_lookup: dict[str, tuple[str, int, float]],
) -> tuple[str, int, float]:
    """Return the strongest normalized topic signal attached to a repo."""
    best_topic = ""
    best_count = 0
    best_signal = 0.0
    for topic in repo.get("topics") or []:
        normalized = str(topic).strip().replace("-", " ").lower()
        if not normalized:
            continue
        entry = topic_lookup.get(normalized)
        if entry is None:
            continue
        topic_name, topic_count, topic_signal = entry
        if topic_signal > best_signal or (
            topic_signal == best_signal and topic_count > best_count
        ):
            best_topic = topic_name
            best_count = topic_count
            best_signal = topic_signal
    return best_topic, best_count, best_signal


def _run_physarum(
    G: int,
    N_agents: int,
    n_steps: int,
    food_positions: list[tuple[int, int, float]],
    sensor_angle: float,
    decay: float,
    rng: np.random.Generator,
    *,
    following: int = 0,
    total_commits: int = 0,
    burstiness_freq: float = 0.0,
    releases: list[dict] | None = None,
    obstacle_cells: list[tuple[int, int]] | None = None,
    spawn_clusters: list[tuple[float, float]] | None = None,
) -> tuple[np.ndarray, list[tuple[np.ndarray, np.ndarray]], np.ndarray]:
    """Run Physarum simulation. Returns (trail, path_record, first_hit)."""
    # --- Item 2: following → sensor distance scaling ---
    sensor_dist = 9.0 + min(6.0, following * 0.03)

    turn_speed = 0.3
    move_speed = 1.0

    # --- Item 3: total_commits → trail deposit amount ---
    deposit = 0.3 + min(0.7, total_commits / 10000)

    # Trail map
    trail = np.zeros((G, G), dtype=np.float64)

    # --- Item 8: total_issues → obstacle cells (dead zones) ---
    obstacle_mask = np.zeros((G, G), dtype=bool)
    if obstacle_cells:
        obs_radius = max(2, G // 80)
        yy_obs, xx_obs = np.ogrid[:G, :G]
        for ox, oy in obstacle_cells:
            omask = ((xx_obs - ox) ** 2 + (yy_obs - oy) ** 2) < obs_radius**2
            obstacle_mask[omask] = True

    # Seed food sources
    food_radius = max(3, G // 40)
    yy, xx = np.ogrid[:G, :G]
    for fx, fy, strength in food_positions:
        mask = ((xx - fx) ** 2 + (yy - fy) ** 2) < food_radius**2
        trail[mask] += max(1.0, strength)

    # Perlin-like noise seeding for sparse data visibility
    noise_x = np.linspace(0, 4 * np.pi, G)
    noise_y = np.linspace(0, 4 * np.pi, G)
    nx, ny = np.meshgrid(noise_x, noise_y)
    noise = (
        0.15 * (np.sin(nx * 1.3 + ny * 0.7) * np.cos(nx * 0.9 - ny * 1.1) + 1.0) / 2.0
    )
    trail += noise

    # --- Item 10: orgs_count → multi-colony spawn ---
    if spawn_clusters and len(spawn_clusters) > 1:
        # Distribute agents among spawn clusters
        n_clusters = len(spawn_clusters)
        agents_per_cluster = N_agents // n_clusters
        ax_parts, ay_parts = [], []
        for ci, (cx, cy) in enumerate(spawn_clusters):
            n_this = agents_per_cluster if ci < n_clusters - 1 else N_agents - agents_per_cluster * (n_clusters - 1)
            spread = G // 10
            ax_parts.append(rng.normal(cx, spread, n_this).astype(np.float64) % G)
            ay_parts.append(rng.normal(cy, spread, n_this).astype(np.float64) % G)
        ax = np.concatenate(ax_parts)
        ay = np.concatenate(ay_parts)
    else:
        # Default: uniform random spawn
        ax = rng.uniform(0, G, N_agents).astype(np.float64)
        ay = rng.uniform(0, G, N_agents).astype(np.float64)
    angles = rng.uniform(0, 2 * np.pi, N_agents)

    # Record subset
    record_n = min(150, N_agents)
    path_record: list[tuple[np.ndarray, np.ndarray]] = []

    # First-hit tracker
    first_hit = np.full((G, G), -1, dtype=np.int32)
    hit_threshold = 0.3

    # --- Item 6: releases → spore burst events ---
    # Pre-compute burst schedule: map each release to a simulation step
    burst_events: dict[int, list[tuple[int, int]]] = {}
    if releases:
        capped_releases = releases[:5]
        for ri, _rel in enumerate(capped_releases):
            # Distribute burst steps evenly across the simulation
            burst_step = max(1, (ri + 1) * n_steps // (len(capped_releases) + 1))
            # Find nearest food source for this burst
            if food_positions:
                fp_idx = ri % len(food_positions)
                bx, by = food_positions[fp_idx][0], food_positions[fp_idx][1]
            else:
                bx, by = G // 2, G // 2
            burst_events[burst_step] = burst_events.get(burst_step, [])
            burst_events[burst_step].append((bx, by))

    for step in range(n_steps):
        # --- Item 6: spawn burst agents at release steps ---
        if step in burst_events:
            for bx, by in burst_events[step]:
                n_burst = rng.integers(20, 51)
                burst_ax = rng.normal(bx, 5.0, n_burst).astype(np.float64) % G
                burst_ay = rng.normal(by, 5.0, n_burst).astype(np.float64) % G
                burst_angles = rng.uniform(0, 2 * np.pi, n_burst)
                ax = np.concatenate([ax, burst_ax])
                ay = np.concatenate([ay, burst_ay])
                angles = np.concatenate([angles, burst_angles])
                N_agents = len(ax)

        # --- Item 5: commit_hour_distribution → speed variation ---
        if burstiness_freq > 0:
            speed_factor = 1.0 + 0.2 * math.sin(step * burstiness_freq)
        else:
            speed_factor = 1.0
        effective_speed = move_speed * speed_factor

        # Sensor positions
        sl_x = (ax + np.cos(angles - sensor_angle) * sensor_dist) % G
        sl_y = (ay + np.sin(angles - sensor_angle) * sensor_dist) % G
        sc_x = (ax + np.cos(angles) * sensor_dist) % G
        sc_y = (ay + np.sin(angles) * sensor_dist) % G
        sr_x = (ax + np.cos(angles + sensor_angle) * sensor_dist) % G
        sr_y = (ay + np.sin(angles + sensor_angle) * sensor_dist) % G

        # Sample trail (nearest-neighbor)
        sl = trail[sl_y.astype(np.intp) % G, sl_x.astype(np.intp) % G]
        sc = trail[sc_y.astype(np.intp) % G, sc_x.astype(np.intp) % G]
        sr = trail[sr_y.astype(np.intp) % G, sr_x.astype(np.intp) % G]

        # Rotate toward strongest signal
        turn_left = sl > sc
        turn_right = sr > sc
        both = turn_left & turn_right
        rand_turn = np.where(rng.random(N_agents) > 0.5, turn_speed, -turn_speed)
        angles = np.where(
            both,
            angles + rand_turn,
            np.where(
                turn_left & ~turn_right,
                angles - turn_speed,
                np.where(turn_right & ~turn_left, angles + turn_speed, angles),
            ),
        )

        # Move (toroidal wrap) — Item 5: apply effective_speed
        ax = (ax + np.cos(angles) * effective_speed) % G
        ay = (ay + np.sin(angles) * effective_speed) % G

        # --- Item 8: bounce agents off obstacle cells ---
        if obstacle_cells:
            ix_check = ax.astype(np.intp) % G
            iy_check = ay.astype(np.intp) % G
            in_obstacle = obstacle_mask[iy_check, ix_check]
            if np.any(in_obstacle):
                # Reverse direction and move back
                angles[in_obstacle] += np.pi
                ax[in_obstacle] = (ax[in_obstacle] + np.cos(angles[in_obstacle]) * effective_speed * 2) % G
                ay[in_obstacle] = (ay[in_obstacle] + np.sin(angles[in_obstacle]) * effective_speed * 2) % G

        # Deposit
        ix = ax.astype(np.intp) % G
        iy = ay.astype(np.intp) % G
        np.add.at(trail, (iy, ix), deposit)

        # --- Item 8: enforce obstacle dead zones (trail always zero) ---
        if obstacle_cells:
            trail[obstacle_mask] = 0.0

        # Diffuse + decay
        trail = _diffuse(trail, size=3) * decay

        # Track first-hit
        newly_hit = (trail > hit_threshold) & (first_hit < 0)
        first_hit[newly_hit] = step

        # Record subset paths every 5 steps
        if step % 5 == 0:
            path_record.append((ax[:record_n].copy(), ay[:record_n].copy()))

    return trail, path_record, first_hit


def _place_food_sources(
    repos: list[dict[str, Any]],
    metrics: dict[str, Any],
    G: int,
    rng: np.random.Generator,
) -> list[tuple[int, int, float]]:
    """Map repos to grid positions with language hues and star-based strength."""
    lang_bytes = metrics.get("languages", {})
    sorted_langs = sorted(lang_bytes.items(), key=lambda x: -x[1]) if lang_bytes else []
    top_lang = sorted_langs[0][0] if sorted_langs else None

    margin = G // 10
    usable = G - 2 * margin

    if not repos:
        # Sparse fallback: scatter a few food sources
        n_fallback = max(3, min(8, metrics.get("public_repos", 5) or 5))
        positions = []
        for _ in range(n_fallback):
            fx = int(rng.integers(margin, margin + usable))
            fy = int(rng.integers(margin, margin + usable))
            hue = LANG_HUES.get(top_lang, 155)
            positions.append((fx, fy, hue))
        return positions

    # Use optimize_placement for a nice spread
    initial = [
        (rng.uniform(margin, margin + usable), rng.uniform(margin, margin + usable))
        for _ in repos
    ]
    weights = [max(1.0, (r.get("stars", 0) or 0) + 1) for r in repos]
    placed = optimize_placement(
        initial,
        weights,
        float(G),
        float(G),
        min_spacing=max(15.0, usable / (len(repos) ** 0.5 + 1)),
        max_iter=100,
        seed=42,
    )

    positions = []
    for i, (px, py) in enumerate(placed):
        repo = repos[i] if i < len(repos) else {}
        lang = repo.get("language") or top_lang
        hue = LANG_HUES.get(lang, 155)
        positions.append((int(px) % G, int(py) % G, hue))

    return positions


_PHYSARUM_CSS = """\
<style>
.tc{{animation:trailReveal .8s ease-out both}}
@keyframes trailReveal{{from{{opacity:0}}to{{opacity:var(--o,.7)}}}}
.fp{{stroke-dasharray:var(--len);stroke-dashoffset:var(--len);animation:filamentDraw 4s ease-in-out var(--del,0s) both}}
@keyframes filamentDraw{{to{{stroke-dashoffset:0}}}}
.food-glow{{animation:foodPulse 3s ease-in-out infinite alternate}}
@keyframes foodPulse{{0%{{opacity:.6}}100%{{opacity:1}}}}
</style>
"""


def _clamp_snapshot_progress(snapshot_progress: float | None) -> float | None:
    if snapshot_progress is None:
        return None
    return max(0.0, min(1.0, snapshot_progress))


def _render_svg(
    history: dict,
    dark_mode: bool = False,
    duration: float = 60.0,
    snapshot_progress: float | None = None,
) -> tuple[str, int, int]:
    snapshot_progress = _clamp_snapshot_progress(snapshot_progress)
    snapshot_mode = snapshot_progress is not None

    metrics = history.get("current_metrics", {})
    repos_raw = history.get("repos", [])
    repos = metrics.get("repos", repos_raw) or repos_raw

    # ------------------------------------------------------------------
    # Simulation parameters from data
    # ------------------------------------------------------------------
    # --- Item 7: network_count → grid resolution boost ---
    network_count = metrics.get("network_count", 0) or 0
    G = min(500, max(300, 300 + network_count // 50)) if network_count > 0 else 400

    ws = compute_world_state(metrics)
    pal = _build_world_palette_extended(
        ws.time_of_day, ws.weather, ws.season, ws.energy
    )
    contributions = metrics.get("contributions_last_year", 0) or 0
    N_agents = min(3000, max(500, 500 + contributions * 2))

    n_steps = min(500, max(150, 150 + contributions // 50))

    pr_reviews = metrics.get("pr_review_count", 0) or 0
    sensor_angle = 0.3 + min(0.4, pr_reviews * 0.02)

    streaks = metrics.get("contribution_streaks", {})
    streak_active = (
        streaks.get("streak_active", False) if isinstance(streaks, dict) else False
    )
    decay = 0.98 if streak_active else 0.95

    rng = np.random.default_rng(42)

    # --- Item 2: following (passed to _run_physarum) ---
    following = metrics.get("following", 0) or 0

    # --- Item 3: total_commits (passed to _run_physarum) ---
    total_commits = metrics.get("total_commits", 0) or 0

    # --- Item 5: commit_hour_distribution → burstiness frequency ---
    commit_hours = metrics.get("commit_hour_distribution") or {}
    burstiness_freq = 0.0
    if commit_hours and isinstance(commit_hours, dict):
        hour_vals = [int(v) for v in commit_hours.values() if v]
        if hour_vals:
            mean_h = sum(hour_vals) / len(hour_vals)
            variance_h = sum((v - mean_h) ** 2 for v in hour_vals) / len(hour_vals)
            burstiness_freq = min(0.5, (variance_h ** 0.5) / max(1.0, mean_h) * 0.1)

    # --- Item 6: releases (passed to _run_physarum) ---
    releases_data = metrics.get("releases") or []
    if not isinstance(releases_data, list):
        releases_data = []

    # --- Item 8: total_issues → obstacle cells ---
    total_issues = metrics.get("total_issues", 0) or 0
    obstacle_cells: list[tuple[int, int]] = []
    if total_issues > 0:
        n_obstacles = min(10, total_issues)
        margin_obs = G // 8
        for _ in range(n_obstacles):
            ox = int(rng.integers(margin_obs, G - margin_obs))
            oy = int(rng.integers(margin_obs, G - margin_obs))
            obstacle_cells.append((ox, oy))

    # --- Item 10: orgs_count → multi-colony spawn clusters ---
    orgs_count = metrics.get("orgs_count", 0) or 0
    spawn_clusters: list[tuple[float, float]] | None = None
    if orgs_count > 1:
        n_clusters = min(5, orgs_count)
        spawn_clusters = []
        for ci in range(n_clusters):
            angle_c = 2 * math.pi * ci / n_clusters
            radius_c = G * 0.25
            cx = G / 2 + radius_c * math.cos(angle_c)
            cy = G / 2 + radius_c * math.sin(angle_c)
            spawn_clusters.append((cx, cy))

    logger.info(
        "Physarum Network: agents={a} steps={s} sensor={sa:.2f} decay={d} dk={dm}",
        a=N_agents,
        s=n_steps,
        sa=sensor_angle,
        d=decay,
        dm=dark_mode,
    )

    # ------------------------------------------------------------------
    # Food sources (repos as attractors)
    # ------------------------------------------------------------------
    food_positions = _place_food_sources(repos, metrics, G, rng)

    # --- Item 4: topic_clusters → multi-species food attractiveness ---
    topic_clusters = metrics.get("topic_clusters") or {}
    top_topic_entries = _top_topic_entries(topic_clusters)
    topic_lookup = {
        topic.lower(): (topic, count, signal)
        for topic, count, signal in top_topic_entries
    }

    # Separate food data for rendering: (grid_x, grid_y, hue, strength)
    food_render: list[tuple[int, int, float, float]] = []
    food_annotations: list[dict[str, float | int | str]] = []
    for i, (fx, fy, hue) in enumerate(food_positions):
        repo = repos[i] if i < len(repos) and isinstance(repos[i], dict) else {}
        star_count = max(1.0, (repo.get("stars", 0) or 0) * 0.3)
        topic_label, topic_count, topic_signal = _repo_topic_signal(repo, topic_lookup)
        food_strength = star_count * (1 + 0.45 * topic_signal)
        food_render.append((fx, fy, hue, food_strength))
        if topic_signal > 0:
            food_annotations.append(
                {
                    "x": fx,
                    "y": fy,
                    "hue": hue,
                    "label": topic_label,
                    "count": topic_count,
                    "signal": topic_signal,
                    "strength": food_strength,
                }
            )

    # Build strength list for simulation
    food_sim = [(fx, fy, s) for fx, fy, _h, s in food_render]

    # Voronoi hue map
    food_hue_list = [(fx, fy, hue) for fx, fy, hue, _s in food_render]
    voronoi_hue = _voronoi_hue_map(G, food_hue_list)

    # ------------------------------------------------------------------
    # Run simulation
    # ------------------------------------------------------------------
    effective_steps = n_steps
    if snapshot_mode:
        effective_steps = max(1, int(n_steps * (snapshot_progress or 0.0)))

    trail, path_record, first_hit = _run_physarum(
        G,
        N_agents,
        effective_steps,
        food_sim,
        sensor_angle,
        decay,
        rng,
        following=following,
        total_commits=total_commits,
        burstiness_freq=burstiness_freq,
        releases=releases_data,
        obstacle_cells=obstacle_cells if obstacle_cells else None,
        spawn_clusters=spawn_clusters,
    )

    # ------------------------------------------------------------------
    # Palette
    # ------------------------------------------------------------------
    # --- Item 11: traffic_views_14d → background luminosity ---
    traffic_views = metrics.get("traffic_views_14d", 0) or 0
    bg_boost = min(0.05, traffic_views / 10000) if traffic_views > 0 else 0.0

    if dark_mode:
        bg_color = pal["bg_secondary"]
        text_color = "rgba(255,255,255,0.4)"
    else:
        bg_color = pal["bg_primary"]
        text_color = "rgba(0,0,0,0.3)"

    # Apply background luminosity boost from traffic
    if bg_boost > 0:
        # Parse the bg_color hex and lighten it slightly
        try:
            _bg = bg_color.lstrip("#")
            _r = min(255, int(_bg[0:2], 16) + int(bg_boost * 255))
            _g = min(255, int(_bg[2:4], 16) + int(bg_boost * 255))
            _b = min(255, int(_bg[4:6], 16) + int(bg_boost * 255))
            bg_color = f"#{_r:02x}{_g:02x}{_b:02x}"
        except (ValueError, IndexError):
            pass  # graceful degradation

    # ------------------------------------------------------------------
    # Build SVG
    # ------------------------------------------------------------------
    parts: list[str] = []
    parts.append(svg_header(_WIDTH, _HEIGHT))
    parts.append("<defs>\n")

    # --- Item 9: watchers → trail glow intensity ---
    watchers = metrics.get("watchers", 0) or 0
    glow_radius = 2.0 + min(3.0, watchers * 0.05) if watchers > 0 else 4.0
    parts.append(volumetric_glow_filter("foodGlow", radius=glow_radius))

    parts.append("\n</defs>\n")

    if not snapshot_mode:
        parts.append(_PHYSARUM_CSS)

    parts.append(f'<rect width="{_WIDTH}" height="{_HEIGHT}" fill="{bg_color}"/>\n')

    # ==================================================================
    # Layer 1 — Trail density grid (80x80 downsampled)
    # ==================================================================
    grid_cells = 80
    block = G // grid_cells
    # Reshape and average
    trail_clipped = trail[: grid_cells * block, : grid_cells * block]
    downsampled = trail_clipped.reshape(grid_cells, block, grid_cells, block).mean(
        axis=(1, 3)
    )
    max_val = downsampled.max() or 1.0

    cell_size = _WIDTH / grid_cells  # = 10

    # Downsample first_hit for animation delays
    if not snapshot_mode:
        fh_clipped = first_hit[: grid_cells * block, : grid_cells * block].astype(
            np.float64
        )
        fh_clipped[fh_clipped < 0] = np.nan
        import warnings
        with warnings.catch_warnings(), np.errstate(all="ignore"):
            warnings.simplefilter("ignore", RuntimeWarning)
            fh_down = np.nanmin(
                fh_clipped.reshape(grid_cells, block, grid_cells, block),
                axis=(1, 3),
            )
        fh_max = np.nanmax(fh_down) if not np.all(np.isnan(fh_down)) else 1.0

    parts.append('<g id="trail-grid">\n')
    for y in range(grid_cells):
        for x in range(grid_cells):
            density = downsampled[y, x] / max_val
            if density < 0.01:
                continue
            hue = float(voronoi_hue[y * block, x * block])
            if dark_mode:
                L = 0.05 + 0.75 * density
                C = 0.02 + 0.20 * density
            else:
                L = 0.98 - 0.70 * density
                C = 0.02 + 0.20 * density
            color = oklch(L, C, hue)
            opacity = min(0.95, 0.1 + 0.85 * density)

            rx = x * cell_size
            ry = y * cell_size

            if snapshot_mode:
                parts.append(
                    f'<rect x="{rx:.1f}" y="{ry:.1f}" '
                    f'width="{cell_size:.1f}" height="{cell_size:.1f}" '
                    f'fill="{color}" opacity="{opacity:.3f}"/>\n'
                )
            else:
                # Animation delay from first_hit
                fh_val = fh_down[y, x] if not np.isnan(fh_down[y, x]) else fh_max
                delay = round(fh_val / max(fh_max, 1) * duration * 0.8, 2)
                parts.append(
                    f'<rect class="tc" x="{rx:.1f}" y="{ry:.1f}" '
                    f'width="{cell_size:.1f}" height="{cell_size:.1f}" '
                    f'fill="{color}" style="--o:{opacity:.3f};animation-delay:{delay}s"/>\n'
                )
    parts.append("</g>\n")

    # ==================================================================
    # Layer 1b — Observer particles (Item 1: followers)
    # ==================================================================
    followers = metrics.get("followers", 0) or 0
    if followers > 0:
        n_observers = min(followers // 25, 20)
        if n_observers > 0 and food_render:
            muted_color = pal.get("muted", oklch(0.55, 0.06, 175))
            scale_obs = _WIDTH / G
            parts.append('<g id="observer-particles">\n')
            for oi in range(n_observers):
                # Place near a food source with slight offset
                fi = oi % len(food_render)
                ofx, ofy = food_render[fi][0], food_render[fi][1]
                drift_x = (ofx + rng.uniform(-15, 15)) * scale_obs
                drift_y = (ofy + rng.uniform(-15, 15)) * scale_obs
                drift_x = max(0, min(_WIDTH, drift_x))
                drift_y = max(0, min(_HEIGHT, drift_y))
                parts.append(
                    f'<circle cx="{drift_x:.1f}" cy="{drift_y:.1f}" r="2" '
                    f'fill="{muted_color}" opacity="0.15"/>\n'
                )
            parts.append("</g>\n")

    # ==================================================================
    # Layer 2 — Agent filament paths (~100-150 paths)
    # ==================================================================
    n_filaments = min(150, len(path_record[0][0]) if path_record else 0)
    if path_record and n_filaments > 0:
        parts.append('<g id="filaments">\n')
        scale_factor = _WIDTH / G
        lang_bytes = metrics.get("languages", {})
        sorted_langs = (
            sorted(lang_bytes.items(), key=lambda x: -x[1]) if lang_bytes else []
        )
        n_languages = max(1, len(sorted_langs))

        for ai in range(n_filaments):
            points = [
                (
                    float(path_record[s][0][ai]) * scale_factor,
                    float(path_record[s][1][ai]) * scale_factor,
                )
                for s in range(len(path_record))
            ]
            if len(points) < 2:
                continue
            d_str = f"M{points[0][0]:.1f},{points[0][1]:.1f}"
            path_len = 0.0
            for pi in range(1, len(points)):
                d_str += f" L{points[pi][0]:.1f},{points[pi][1]:.1f}"
                dx = points[pi][0] - points[pi - 1][0]
                dy = points[pi][1] - points[pi - 1][1]
                path_len += math.sqrt(dx * dx + dy * dy)

            # Color from language species
            species_idx = ai % n_languages
            if sorted_langs:
                lang_name = sorted_langs[species_idx][0]
                hue = LANG_HUES.get(lang_name, 155)
            else:
                hue = 155
            color = oklch(0.65 if dark_mode else 0.50, 0.12, hue)
            path_len_int = max(1, int(path_len))

            if snapshot_mode:
                parts.append(
                    f'<path d="{d_str}" stroke="{color}" stroke-width="0.5" '
                    f'opacity="0.3" fill="none"/>\n'
                )
            else:
                delay = round(ai / n_filaments * duration * 0.3, 2)
                parts.append(
                    f'<path class="fp" d="{d_str}" stroke="{color}" '
                    f'stroke-width="0.5" opacity="0.3" fill="none" '
                    f'style="--len:{path_len_int};--del:{delay}s"/>\n'
                )
        parts.append("</g>\n")

    # ==================================================================
    # Layer 3 — Food source markers (glowing circles)
    # ==================================================================
    parts.append('<g id="food-sources" filter="url(#foodGlow)">\n')
    scale_factor = _WIDTH / G
    for fx, fy, hue, strength in food_render:
        sx = fx * scale_factor
        sy = fy * scale_factor
        r = max(3.0, min(8.0, 3.0 + strength * 0.5))
        color = oklch(0.70 if dark_mode else 0.55, 0.18, hue)
        cls = ' class="food-glow"' if not snapshot_mode else ""
        parts.append(
            f'<circle{cls} cx="{sx:.1f}" cy="{sy:.1f}" r="{r:.1f}" '
            f'fill="{color}" opacity="0.8"/>\n'
        )
    parts.append("</g>\n")

    if food_annotations:
        parts.append('<g id="topic-nexuses">\n')
        for annotation in sorted(
            food_annotations,
            key=lambda item: (-int(item["count"]), str(item["label"])),
        )[:3]:
            sx = float(annotation["x"]) * scale_factor
            sy = float(annotation["y"]) * scale_factor
            count = int(annotation["count"])
            ring_r = round(max(14.0, 12.0 + float(annotation["strength"]) * 0.8), 1)
            ring_color = oklch(
                0.72 if dark_mode else 0.44,
                0.15,
                float(annotation["hue"]),
            )
            topic_name = escape(f'{str(annotation["label"]).title()} Nexus')
            noun = "repo" if count == 1 else "repos"
            topic_note = escape(f"{count} linked {noun}")
            parts.append(
                f'<circle cx="{sx:.1f}" cy="{sy:.1f}" r="{ring_r}" fill="none" '
                f'stroke="{ring_color}" stroke-width="1.0" opacity="0.45"/>\n'
            )
            parts.append(
                f'<text x="{sx:.1f}" y="{sy - ring_r - 5:.1f}" text-anchor="middle" '
                f'font-size="8.0" font-family="Georgia,serif" font-style="italic" '
                f'fill="{pal["text_secondary"]}" paint-order="stroke fill" '
                f'stroke="{bg_color}" stroke-width="2.1" stroke-linejoin="round">'
                f'{topic_name}</text>\n'
            )
            parts.append(
                f'<text x="{sx:.1f}" y="{sy - ring_r + 4:.1f}" text-anchor="middle" '
                f'font-size="5.0" font-family="Georgia,serif" letter-spacing="0.7" '
                f'fill="{pal["muted"]}" paint-order="stroke fill" '
                f'stroke="{bg_color}" stroke-width="1.7" stroke-linejoin="round">'
                f'{topic_note}</text>\n'
            )
        parts.append("</g>\n")

    # ==================================================================
    # Layer 4 — Timeline progress bar
    # ==================================================================
    bar_y = _HEIGHT - 16
    bar_x = 50
    bar_w = _WIDTH - 100
    bar_h = 4
    bar_bg = "rgba(255,255,255,0.1)" if dark_mode else "rgba(0,0,0,0.08)"
    bar_fg = pal.get("accent", oklch(0.65, 0.14, 145))
    parts.append(
        f'<rect x="{bar_x}" y="{bar_y}" width="{bar_w}" height="{bar_h}" '
        f'rx="2" fill="{bar_bg}"/>\n'
    )

    repo_dates = [
        r.get("date", "") for r in repos_raw if isinstance(r, dict) and r.get("date")
    ]
    account_created = history.get("account_created")
    if repo_dates:
        min_year = int(repo_dates[0][:4]) if len(repo_dates[0]) >= 4 else 2020
        max_year = int(repo_dates[-1][:4]) if len(repo_dates[-1]) >= 4 else 2025
    elif account_created and len(str(account_created)) >= 4:
        min_year = int(str(account_created)[:4])
        max_year = 2026
    else:
        min_year, max_year = 2020, 2026

    if snapshot_mode:
        fill_w = round(bar_w * (snapshot_progress or 0.0), 1)
        parts.append(
            f'<rect x="{bar_x}" y="{bar_y}" width="{fill_w}" height="{bar_h}" '
            f'rx="2" fill="{bar_fg}" opacity="0.7"/>\n'
        )
    else:
        parts.append(
            f'<rect x="{bar_x}" y="{bar_y}" width="0" height="{bar_h}" '
            f'rx="2" fill="{bar_fg}" opacity="0.7">\n'
            f'  <animate attributeName="width" from="0" to="{bar_w}" '
            f'dur="{duration}s" fill="freeze"/>\n'
            f"</rect>\n"
        )

    # Year labels along bar
    year_span = max(max_year - min_year, 1)
    for yr in range(min_year, max_year + 1):
        frac = (yr - min_year) / year_span
        tx = bar_x + frac * bar_w
        parts.append(
            f'<text x="{tx:.1f}" y="{bar_y - 3}" text-anchor="middle" '
            f'font-size="6" font-family="monospace" fill="{text_color}">{yr}</text>\n'
        )

    parts.append(svg_footer())

    n_cells = int(np.sum(downsampled > 0.01 * max_val))
    return "".join(parts), n_cells, n_filaments


def render_svg(
    history: dict,
    dark_mode: bool = False,
    duration: float = 60.0,
    snapshot_progress: float | None = None,
) -> str:
    """Return SVG string."""
    svg_text, _, _ = _render_svg(
        history,
        dark_mode=dark_mode,
        duration=duration,
        snapshot_progress=snapshot_progress,
    )
    return svg_text


def generate(
    history: dict,
    dark_mode: bool = False,
    output_path: Path | None = None,
    duration: float = 60.0,
) -> Path:
    """Generate the artwork and write to file. Returns path."""
    suffix = "-dark" if dark_mode else ""
    out = Path(output_path or f".github/assets/img/animated-activity{suffix}.svg")
    out.parent.mkdir(parents=True, exist_ok=True)
    svg_text, n_cells, n_filaments = _render_svg(
        history,
        dark_mode=dark_mode,
        duration=duration,
    )
    out.write_text(svg_text, encoding="utf-8")

    size_kb = len(svg_text.encode("utf-8")) / 1024
    logger.info(
        "Physarum Network saved: {path} ({cells} trail cells, {fils} filaments, {kb:.0f} KB)",
        path=out,
        cells=n_cells,
        fils=n_filaments,
        kb=size_kb,
    )
    return out
