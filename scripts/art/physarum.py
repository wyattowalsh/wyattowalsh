"""Physarum polycephalum — slime mold transport network living art.

A slime mold grows from a food-biased spore, explores the canvas, and connects
food sources (repos) with an efficient transport network.  Veins are
luminous yellow-gold on a dark substrate.  Simulation follows the Jones 2010
agent-based model on a low-resolution grid; rendering extracts marching-
squares iso-contours and emits pure SVG paths.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date as dt_date
from datetime import datetime, timedelta
from typing import Any

import numpy as np
from scipy.ndimage import uniform_filter

from .shared import (
    ART_PALETTE_ANCHORS,
    HEIGHT,
    LANG_HUES,
    WIDTH,
    ElementBudget,
    WorldState,
    _build_world_palette_extended,
    activity_tempo,
    compute_derived_metrics,
    compute_maturity,
    compute_world_state,
    contributions_monthly_to_daily_series,
    map_date_to_loop_delay,
    normalize_timeline_window,
    oklch,
    oklch_gradient,
    oklch_lerp,
    repo_to_canvas_position,
    seed_hash,
    select_primary_repos,
    topic_affinity_matrix,
    visual_complexity,
    volumetric_glow_filter,
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


@dataclass(frozen=True)
class PhysarumIdentityPalette:
    """Language/topic-driven identity colors for nodes and local veins."""

    hue: float
    topic_signal: float
    node_halo: str
    node_shell: str
    node_core: str
    label_color: str
    vein_tint: str
    language: str | None
    dominant_topic: str | None


@dataclass(frozen=True)
class PhysarumGrowthOrigin:
    """Resolved starting locus for the organism."""

    x: float
    y: float
    spread: float
    dominance: float


@dataclass(frozen=True)
class PhysarumIdentityNode:
    """Canvas-space node used to tint nearby veins."""

    x: float
    y: float
    conc: float
    identity: PhysarumIdentityPalette


# Background substrate color (deep dark blue-black)
_BG_COLOR = oklch(0.12, 0.04, 250)
_TOPIC_HUE_GROUPS: tuple[tuple[set[str], float], ...] = (
    (
        {
            "ai",
            "agent",
            "agents",
            "llm",
            "ml",
            "model",
            "neural",
            "nlp",
            "vision",
        },
        318.0,
    ),
    (
        {
            "analytics",
            "art",
            "creative",
            "graphics",
            "rendering",
            "simulation",
            "viz",
            "visualization",
        },
        276.0,
    ),
    (
        {
            "api",
            "css",
            "frontend",
            "html",
            "next",
            "react",
            "svelte",
            "vue",
            "web",
        },
        48.0,
    ),
    (
        {
            "automation",
            "cli",
            "devops",
            "docker",
            "infra",
            "kubernetes",
            "ops",
            "terraform",
            "tooling",
        },
        186.0,
    ),
    (
        {
            "auth",
            "compliance",
            "crypto",
            "security",
        },
        8.0,
    ),
    (
        {
            "backend",
            "compiler",
            "db",
            "distributed",
            "performance",
            "systems",
        },
        146.0,
    ),
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _grid_to_canvas(
    gx: float, gy: float, cell_w: float, cell_h: float
) -> tuple[float, float]:
    """Convert grid coordinates to canvas (SVG) coordinates."""
    return gx * cell_w, gy * cell_h


def _coerce_nonnegative_int(value: Any) -> int:
    """Best-effort int coercion for snapshot counters and bands."""
    try:
        return max(0, int(value or 0))
    except (TypeError, ValueError):
        return 0


def _repo_topics(repo: dict[str, Any], *, limit: int = 3) -> list[str]:
    """Return a stable, cleaned topic list for repo identity styling."""
    topics: list[str] = []
    for raw_topic in repo.get("topics") or []:
        topic = str(raw_topic).strip().lower().replace("_", "-")
        if topic and topic not in topics:
            topics.append(topic)
        if len(topics) >= limit:
            break
    return topics


def _circular_hue_mean(samples: list[tuple[float, float]]) -> float:
    """Average hue angles while respecting wrap-around."""
    if not samples:
        return 155.0

    vec_x = sum(
        math.cos(math.radians(hue)) * weight for hue, weight in samples if weight > 0
    )
    vec_y = sum(
        math.sin(math.radians(hue)) * weight for hue, weight in samples if weight > 0
    )
    if abs(vec_x) < 1e-9 and abs(vec_y) < 1e-9:
        return samples[0][0] % 360.0
    return math.degrees(math.atan2(vec_y, vec_x)) % 360.0


def _topic_hue(topic: str) -> float:
    """Resolve a topic into a semantically-biased hue with deterministic fallback."""
    normalized = topic.strip().lower().replace("_", "-")
    if not normalized:
        return 155.0

    tokens = {normalized, *[part for part in normalized.split("-") if part]}
    for keywords, hue in _TOPIC_HUE_GROUPS:
        if tokens & keywords:
            return hue

    digest = seed_hash({"topic": normalized})
    return (int(digest[:6], 16) / 0xFFFFFF) * 360.0


def _repo_identity_palette(repo: dict[str, Any]) -> PhysarumIdentityPalette:
    """Build identity colors that blend language anchors with topic accents."""
    language_raw = repo.get("language")
    language = str(language_raw).strip() if language_raw else None
    topics = _repo_topics(repo)
    topic_signal = min(1.0, len(topics) / 3.0)

    hue_samples: list[tuple[float, float]] = [
        (float(LANG_HUES.get(language, 155)), 1.15 if language else 0.7),
    ]
    hue_samples.extend((_topic_hue(topic), 0.45) for topic in topics)
    hue = _circular_hue_mean(hue_samples)

    return PhysarumIdentityPalette(
        hue=hue,
        topic_signal=topic_signal,
        node_halo=oklch(
            0.46 + 0.06 * topic_signal,
            0.10 + 0.04 * topic_signal,
            (hue - 10.0) % 360.0,
        ),
        node_shell=oklch(
            0.62 + 0.05 * topic_signal,
            0.12 + 0.03 * topic_signal,
            (hue + 12.0) % 360.0,
        ),
        node_core=oklch(
            0.78 + 0.05 * topic_signal,
            0.14 + 0.05 * topic_signal,
            (hue + 4.0) % 360.0,
        ),
        label_color=oklch(
            0.76 + 0.03 * topic_signal,
            0.07 + 0.03 * topic_signal,
            hue,
        ),
        vein_tint=oklch(
            0.66 + 0.03 * topic_signal,
            0.13 + 0.04 * topic_signal,
            hue,
        ),
        language=language,
        dominant_topic=topics[0] if topics else None,
    )


def _resolve_growth_origin(
    sources: list[tuple[float, float, float]],
    *,
    span: float,
    fallback: tuple[float, float],
) -> PhysarumGrowthOrigin:
    """Bias the organism origin toward weighted, cluster-aware food centroids."""
    valid_sources = [
        (float(x), float(y), float(weight)) for x, y, weight in sources if weight > 0
    ]
    if not valid_sources:
        return PhysarumGrowthOrigin(
            x=fallback[0],
            y=fallback[1],
            spread=max(1.5, span * 0.05),
            dominance=0.0,
        )

    total_weight = sum(weight for _x, _y, weight in valid_sources)
    weighted_x = sum(x * weight for x, _y, weight in valid_sources) / max(
        total_weight,
        1e-6,
    )
    weighted_y = sum(y * weight for _x, y, weight in valid_sources) / max(
        total_weight,
        1e-6,
    )

    cluster_radius = max(span * 0.16, 5.0)
    raw_clusters: list[list[tuple[float, float, float]]] = []
    for x, y, weight in sorted(valid_sources, key=lambda item: item[2], reverse=True):
        best_idx = -1
        best_dist = float("inf")
        for idx, cluster in enumerate(raw_clusters):
            cluster_weight = sum(item[2] for item in cluster)
            cluster_x = sum(item[0] * item[2] for item in cluster) / max(
                cluster_weight,
                1e-6,
            )
            cluster_y = sum(item[1] * item[2] for item in cluster) / max(
                cluster_weight,
                1e-6,
            )
            dist = math.hypot(x - cluster_x, y - cluster_y)
            if dist <= cluster_radius and dist < best_dist:
                best_dist = dist
                best_idx = idx
        if best_idx >= 0:
            raw_clusters[best_idx].append((x, y, weight))
        else:
            raw_clusters.append([(x, y, weight)])

    clusters: list[dict[str, float]] = []
    total_score = 0.0
    for cluster in raw_clusters:
        cluster_weight = sum(item[2] for item in cluster)
        cluster_x = sum(item[0] * item[2] for item in cluster) / max(
            cluster_weight, 1e-6
        )
        cluster_y = sum(item[1] * item[2] for item in cluster) / max(
            cluster_weight, 1e-6
        )
        spread = sum(
            math.hypot(item[0] - cluster_x, item[1] - cluster_y) * item[2]
            for item in cluster
        ) / max(cluster_weight, 1e-6)
        score = cluster_weight * (1.0 + 0.12 * min(len(cluster) - 1, 4))
        clusters.append(
            {
                "x": cluster_x,
                "y": cluster_y,
                "spread": spread,
                "score": score,
                "members": float(len(cluster)),
            }
        )
        total_score += score

    dominant_cluster = max(clusters, key=lambda cluster: cluster["score"])
    dominance = dominant_cluster["score"] / max(total_score, 1e-6)
    member_share = dominant_cluster["members"] / max(1.0, float(len(valid_sources)))
    cluster_bias = min(0.82, max(0.35, 0.28 + 0.42 * dominance + 0.12 * member_share))
    origin_x = weighted_x * (1.0 - cluster_bias) + dominant_cluster["x"] * cluster_bias
    origin_y = weighted_y * (1.0 - cluster_bias) + dominant_cluster["y"] * cluster_bias
    weighted_spread = sum(
        math.hypot(x - origin_x, y - origin_y) * weight
        for x, y, weight in valid_sources
    ) / max(total_weight, 1e-6)
    spread = max(
        span * 0.025,
        min(
            span * 0.11,
            dominant_cluster["spread"] * 0.65
            + weighted_spread * (0.18 + 0.22 * (1.0 - dominance))
            + span * 0.02,
        ),
    )
    return PhysarumGrowthOrigin(
        x=origin_x,
        y=origin_y,
        spread=spread,
        dominance=dominance,
    )


def _identity_influence(
    x: float,
    y: float,
    nodes: list[PhysarumIdentityNode],
) -> tuple[PhysarumIdentityNode | None, float]:
    """Return the dominant identity node and confidence at a canvas sample point."""
    if not nodes:
        return None, 0.0

    influences: list[tuple[float, PhysarumIdentityNode]] = []
    total = 0.0
    for node in nodes:
        distance = math.hypot(x - node.x, y - node.y)
        score = (0.35 + math.log1p(node.conc)) / (
            ((max(distance, 1.0) / 120.0) ** 1.35) + 1.0
        )
        influences.append((score, node))
        total += score

    if total <= 0.0:
        return None, 0.0

    dominant_score, dominant_node = max(influences, key=lambda item: item[0])
    return dominant_node, dominant_score / total


def _resolve_vein_style(
    points: list[tuple[float, float]],
    base_color: str,
    nodes: list[PhysarumIdentityNode],
) -> tuple[str, float]:
    """Tint local veins toward the nearest node identity and boost readability."""
    if not points or not nodes:
        return base_color, 0.0

    center_x = sum(point[0] for point in points) / len(points)
    center_y = sum(point[1] for point in points) / len(points)
    dominant_node, strength = _identity_influence(center_x, center_y, nodes)
    if dominant_node is None:
        return base_color, 0.0

    tint_mix = min(
        0.72,
        0.20 + 0.30 * strength + 0.18 * dominant_node.identity.topic_signal,
    )
    visibility = min(
        1.0,
        0.55 * strength + 0.45 * dominant_node.identity.topic_signal,
    )
    return oklch_lerp(
        base_color, dominant_node.identity.vein_tint, tint_mix
    ), visibility


def _repo_recency_bands(repos: object) -> dict[str, int]:
    """Return stable recency bands, falling back to repo ages when absent."""
    bands = {"fresh": 0, "recent": 0, "established": 0, "legacy": 0}
    if not isinstance(repos, list):
        return bands

    for repo in repos:
        if not isinstance(repo, dict):
            continue
        age_months = _coerce_nonnegative_int(repo.get("age_months", 0))
        if age_months <= 3:
            bands["fresh"] += 1
        elif age_months <= 12:
            bands["recent"] += 1
        elif age_months <= 36:
            bands["established"] += 1
        else:
            bands["legacy"] += 1
    return bands


def _commit_hour_focus(commit_hours: object) -> tuple[float, float]:
    """Return circadian focus [0, 1] and weighted peak hour [0, 24)."""
    if not isinstance(commit_hours, dict):
        return 0.0, 12.0

    hours: dict[int, float] = {}
    for raw_hour, raw_count in commit_hours.items():
        try:
            hour = int(raw_hour)
            count = float(raw_count)
        except (TypeError, ValueError):
            continue
        if 0 <= hour <= 23 and count > 0:
            hours[hour] = hours.get(hour, 0.0) + count

    if not hours:
        return 0.0, 12.0

    total = sum(hours.values())
    vec_x = sum(
        math.cos(2 * math.pi * hour / 24.0) * weight for hour, weight in hours.items()
    )
    vec_y = sum(
        math.sin(2 * math.pi * hour / 24.0) * weight for hour, weight in hours.items()
    )
    focus = min(1.0, max(0.0, math.hypot(vec_x, vec_y) / max(total, 1e-6)))

    if abs(vec_x) < 1e-9 and abs(vec_y) < 1e-9:
        return focus, 12.0

    mean_angle = math.atan2(vec_y, vec_x)
    if mean_angle < 0:
        mean_angle += 2 * math.pi
    return focus, mean_angle * 24.0 / (2 * math.pi)


def _summarize_recent_pr_activity(
    recent_merged_prs: object,
) -> tuple[float, float, dict[str, float]]:
    """Return merge tempo/burst and per-repo emphasis from merged PRs."""
    if not isinstance(recent_merged_prs, list):
        return 0.0, 0.0, {}

    parsed: list[tuple[datetime, float]] = []
    repo_boosts: dict[str, float] = {}

    for pr in recent_merged_prs:
        if not isinstance(pr, dict):
            continue

        merged_at_raw = pr.get("merged_at") or pr.get("mergedAt") or pr.get("date")
        if not isinstance(merged_at_raw, str) or not merged_at_raw.strip():
            continue
        try:
            merged_at = datetime.fromisoformat(merged_at_raw.replace("Z", "+00:00"))
        except ValueError:
            continue

        additions = _coerce_nonnegative_int(pr.get("additions", 0))
        deletions = _coerce_nonnegative_int(pr.get("deletions", 0))
        delta_weight = 1.0 + min(0.5, math.log1p(additions + deletions) * 0.08)
        parsed.append((merged_at, delta_weight))

        repo_name = str(pr.get("repo_name") or "").strip().casefold()
        if repo_name:
            repo_boosts[repo_name] = min(
                0.6,
                repo_boosts.get(repo_name, 0.0) + 0.10 * delta_weight,
            )

    if not parsed:
        return 0.0, 0.0, repo_boosts

    parsed.sort(key=lambda item: item[0])
    density = min(1.0, len(parsed) / 6.0)
    delta_mean = sum(weight for _merged_at, weight in parsed) / len(parsed)

    if len(parsed) == 1:
        tempo = density
    else:
        gaps = [
            max(1.0, (curr[0] - prev[0]).total_seconds() / 86400.0)
            for prev, curr in zip(parsed, parsed[1:])
        ]
        mean_gap = sum(gaps) / len(gaps)
        tempo = min(1.0, 18.0 / max(mean_gap, 1.0))

    burst = min(
        1.0,
        density * 0.55 + tempo * 0.35 + min(0.10, max(0.0, delta_mean - 1.0) * 0.20),
    )
    return tempo, burst, repo_boosts


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
    points: list[tuple[float, float]],
    iterations: int = 1,
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
    deposit_amount: float,
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
    deposit_amount : pheromone amount deposited per step.

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
    origin = _resolve_growth_origin(
        [(float(fx), float(fy), float(conc)) for fx, fy, conc in food_sources],
        span=float(grid),
        fallback=(grid / 2.0, grid / 2.0),
    )
    pos_x = rng.normal(origin.x, origin.spread, n_agents).astype(np.float64)
    pos_y = rng.normal(origin.y, origin.spread, n_agents).astype(np.float64)
    headings = rng.uniform(0, 2 * np.pi, n_agents).astype(np.float64)

    sa = config.sensor_angle
    sd = config.sensor_distance
    step_size = config.step_size * speed_mult
    deposit = deposit_amount

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
                np.where(
                    turn_left,
                    headings - sa,
                    np.where(turn_right, headings + sa, headings),
                ),
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
        trail *= 1.0 - evaporation_rate

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
    _pal = _build_world_palette_extended(
        world.time_of_day,
        world.weather,
        world.season,
        world.energy,
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
    daily = metrics.get("contributions_daily", {})
    stars = _coerce_nonnegative_int(metrics.get("stars", 0))
    contributions = _coerce_nonnegative_int(metrics.get("contributions_last_year", 200))
    total_commits = _coerce_nonnegative_int(metrics.get("total_commits", 0))
    total_prs = _coerce_nonnegative_int(
        metrics.get("total_prs", 0) or len(metrics.get("recent_merged_prs") or []),
    )
    total_issues = _coerce_nonnegative_int(
        metrics.get("total_issues", 0) or metrics.get("open_issues_count", 0) or 0,
    )
    release_count = len(metrics.get("releases") or [])
    streaks = metrics.get("contribution_streaks") or {}
    streak_current = _coerce_nonnegative_int(
        streaks.get("current_streak_months", streaks.get("current", 0))
        if isinstance(streaks, dict)
        else 0,
    )
    streak_longest = _coerce_nonnegative_int(
        streaks.get("longest_streak_months", 0) if isinstance(streaks, dict) else 0,
    )
    streak_active = (
        bool(streaks.get("streak_active", False))
        if isinstance(streaks, dict)
        else False
    )
    streak_signal = min(1.0, streak_current / (12.0 if streak_active else 24.0))
    derived = compute_derived_metrics(metrics)

    primary_repos, _overflow = select_primary_repos(repos, limit=config.max_repos)
    tempo = activity_tempo(monthly)
    pr_tempo, pr_burst, repo_pr_boosts = _summarize_recent_pr_activity(
        metrics.get("recent_merged_prs"),
    )
    issue_stats = metrics.get("issue_stats") or {}
    issue_open = _coerce_nonnegative_int(
        issue_stats.get("open_count", metrics.get("open_issues_count", 0))
        if isinstance(issue_stats, dict)
        else 0,
    )
    issue_closed = _coerce_nonnegative_int(
        issue_stats.get("closed_count", 0) if isinstance(issue_stats, dict) else 0,
    )
    issue_volume = issue_open + issue_closed
    issue_pressure = issue_open / issue_volume if issue_volume else 0.0
    issue_resolution = issue_closed / issue_volume if issue_volume else 0.0
    commit_focus, peak_hour = _commit_hour_focus(
        metrics.get("commit_hour_distribution", {}),
    )
    nocturnal_bias = 1.0 if peak_hour < 6.0 or peak_hour >= 20.0 else 0.0
    raw_recency_bands = metrics.get("repo_recency_bands")
    repo_recency_bands = (
        {
            band: _coerce_nonnegative_int(raw_recency_bands.get(band, 0))
            for band in ("fresh", "recent", "established", "legacy")
        }
        if isinstance(raw_recency_bands, dict)
        else _repo_recency_bands(primary_repos)
    )

    # ── Timeline window ───────────────────────────────────────────
    def _repo_date(repo: dict) -> str | None:
        for key in ("date", "created_at", "created", "pushed_at", "updated_at"):
            val = repo.get(key)
            if isinstance(val, str) and val.strip():
                return val[:10] if len(val) >= 10 else val
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
            "contributions_monthly": monthly,
            "contributions_daily": daily,
        },
        fallback_days=365,
    )

    daily_series: dict[str, int] = {}
    if isinstance(daily, dict):
        for raw_day, raw_count in daily.items():
            day = str(raw_day).strip()
            if len(day) >= 10:
                day = day[:10]
            try:
                dt_date.fromisoformat(day)
                count = int(raw_count or 0)
            except ValueError:
                continue
            except TypeError:
                continue
            daily_series[day] = max(0, count)
    if not daily_series:
        daily_series = contributions_monthly_to_daily_series(
            monthly,
            reference_year=timeline_window[1].year,
        )
    sorted_daily = sorted(daily_series.items(), key=lambda kv: kv[0])
    total_daily = sum(max(0, int(v)) for _, v in sorted_daily)

    def _collection_len(value: Any) -> int:
        if isinstance(value, (dict, list, tuple, set)):
            return len(value)
        return 0

    def _repo_age_days(repo: dict[str, Any]) -> float:
        age_days = repo.get("age_days")
        if isinstance(age_days, int | float):
            return max(0.0, float(age_days))
        age_months = repo.get("age_months")
        if isinstance(age_months, int | float):
            return max(0.0, float(age_months) * 30.0)
        when = _repo_date(repo)
        if not when:
            return 0.0
        try:
            return max(
                0.0,
                float((timeline_window[1] - dt_date.fromisoformat(when)).days),
            )
        except ValueError:
            return 0.0

    def _repo_age_signal(repo: dict[str, Any]) -> float:
        age_days = _repo_age_days(repo)
        matured = 1.0 - math.exp(-age_days / 75.0)
        return max(0.20, min(1.0, matured))

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

    # ── Data mappings ─────────────────────────────────────────────
    grid = config.grid_resolution
    cell_w = WIDTH / grid
    cell_h = HEIGHT / grid
    repo_count = len(primary_repos)
    fresh_repos = _coerce_nonnegative_int(repo_recency_bands.get("fresh"))
    recent_repos = _coerce_nonnegative_int(repo_recency_bands.get("recent"))
    established_repos = _coerce_nonnegative_int(
        repo_recency_bands.get("established"),
    ) + _coerce_nonnegative_int(repo_recency_bands.get("legacy"))
    repo_band_total = max(1, fresh_repos + recent_repos + established_repos)
    fresh_share = (fresh_repos + recent_repos) / repo_band_total
    legacy_share = (
        _coerce_nonnegative_int(repo_recency_bands.get("legacy")) / repo_band_total
    )
    language_count = max(
        derived.language_count,
        _collection_len(metrics.get("languages")),
    )
    topic_diversity = max(
        derived.topic_diversity,
        _collection_len(metrics.get("topic_clusters")),
    )
    activity_total = max(contributions, total_daily)
    activity_signal = math.log1p(max(activity_total, 0))
    commit_signal = math.log1p(max(total_commits, 0))
    ecosystem_signal = math.log1p(
        max(stars, 0)
        + derived.total_forks
        + repo_count * 4
        + fresh_repos
        + established_repos * 2
        + max(0, total_commits) * 0.08
    )
    collaboration_signal = (
        math.log1p(
            release_count * 3
            + total_prs * 0.4
            + total_issues * 0.2
            + streak_current * 0.7
        )
        + pr_burst
        + commit_focus * 0.6
    )
    diversity_signal = (
        1.0 + 0.18 * complexity + 0.05 * language_count + 0.03 * topic_diversity
    )

    # Food sources: repos mapped to grid positions
    affinities = topic_affinity_matrix(primary_repos)
    affinity_boosts = [1.0 for _ in primary_repos]
    for (left, right), affinity in affinities.items():
        boost = 0.25 * max(0.0, min(1.0, affinity))
        affinity_boosts[left] += boost
        affinity_boosts[right] += boost

    food_sources: list[tuple[int, int, float]] = []
    food_canvas: list[dict[str, Any]] = []
    for index, repo in enumerate(primary_repos):
        cx, cy = repo_to_canvas_position(repo, h, strategy="language_cluster")
        repo_stars = _coerce_nonnegative_int(repo.get("stars", 0))
        age_months = _coerce_nonnegative_int(repo.get("age_months", 0))
        age_signal = _repo_age_signal(repo)
        affinity_signal = min(1.65, affinity_boosts[index])
        repo_name = str(repo.get("name") or "").strip().casefold()
        pr_signal = 1.0 + repo_pr_boosts.get(repo_name, 0.0)
        if age_months <= 3:
            recency_mult = 1.24
        elif age_months <= 12:
            recency_mult = 1.12
        elif age_months <= 36:
            recency_mult = 1.04
        else:
            recency_mult = 0.92
        activity_mult = 1.0 + 0.04 * commit_focus + 0.06 * streak_signal
        conc = (
            (
                config.food_base * (0.20 + 0.80 * age_signal)
                + config.food_scale
                * math.log1p(repo_stars + 1)
                * (0.85 + 0.35 * age_signal)
            )
            * affinity_signal
            * pr_signal
            * recency_mult
            * activity_mult
        )
        gx = int(min(grid - 1, max(0, cx / cell_w)))
        gy = int(min(grid - 1, max(0, cy / cell_h)))
        identity = _repo_identity_palette(repo)
        food_sources.append((gx, gy, conc))
        food_canvas.append(
            {
                "cx": cx,
                "cy": cy,
                "conc": conc,
                "repo": repo,
                "identity": identity,
            }
        )

    # Agent count from cumulative snapshot state
    n_agents = int(
        config.agent_base * 0.04
        + config.agent_scale
        * (
            0.36 * growth_mat
            + 0.16 * activity_signal
            + 0.12 * commit_signal
            + 0.20 * ecosystem_signal
        )
        + 4.0 * collaboration_signal
        + 3.0 * min(repo_count, config.max_repos)
    )
    n_agents = int(
        n_agents
        * diversity_signal
        * (1.0 + 0.18 * streak_signal + 0.12 * pr_burst + 0.08 * fresh_share),
    )
    min_agents = 12 if activity_total <= 3 and repo_count == 0 else 24
    n_agents = max(min_agents, min(2000, n_agents))

    # Evaporation: high energy = slow evaporation = thicker network
    stability_signal = min(
        1.0,
        release_count * 0.06
        + streak_current * 0.015
        + streak_longest * 0.006
        + established_repos * 0.02
        + issue_resolution * 0.18
        + pr_burst * 0.22
        + repo_count * 0.01,
    )
    evap = (
        config.evaporation
        * max(0.28, 1.0 - world.energy * 0.55)
        * (1.0 - 0.15 * stability_signal)
        * (1.0 + issue_pressure * 0.25 + legacy_share * 0.06 - streak_signal * 0.10)
    )
    evap = max(config.evaporation * 0.35, min(config.evaporation * 1.5, evap))

    # Simulation steps from maturity and cumulative project signals
    sim_steps = int(
        config.sim_steps_base * (0.15 + 0.45 * growth_mat)
        + config.sim_steps_scale
        * (
            0.10 * activity_signal
            + 0.07 * commit_signal
            + 0.08 * math.log1p(repo_count + release_count * 2 + total_prs * 0.18)
            + 0.04 * complexity
        )
    )
    sim_steps = max(12, min(240, sim_steps))

    # Speed and deposition from activity tempo and collaboration cadence
    speed_mult = max(
        0.45,
        0.68
        + tempo * 0.30
        + pr_tempo * 0.22
        + commit_focus * 0.16
        + nocturnal_bias * 0.04
        + min(0.2, streak_current / 40.0),
    )
    contour_levels = int(
        max(
            4,
            min(
                10,
                config.contour_levels
                + round(
                    commit_focus * 2.0
                    + pr_burst * 1.8
                    + fresh_share * 1.6
                    + streak_signal * 1.2
                    - issue_pressure * 1.4,
                ),
            ),
        ),
    )
    deposit_scale = min(
        1.5,
        max(
            0.55,
            0.55
            + 0.15 * min(activity_signal, 5.0)
            + 0.07 * min(collaboration_signal, 4.0)
            + 0.12 * pr_burst
            + 0.06 * commit_focus
            + 0.06 * min(topic_diversity, 6),
        ),
    )
    deposit_amount = config.deposit_amount * deposit_scale

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
        deposit_amount=deposit_amount,
    )

    # Normalize trail to [0, 1]
    t_max = trail.max()
    if t_max > 0:
        trail /= t_max

    # ── Physarum palette ──────────────────────────────────────────
    anchors = ART_PALETTE_ANCHORS["physarum"]
    vein_colors = oklch_gradient(anchors, contour_levels)
    identity_nodes = [
        PhysarumIdentityNode(
            x=float(node["cx"]),
            y=float(node["cy"]),
            conc=float(node["conc"]),
            identity=node["identity"],
        )
        for node in food_canvas
    ]
    origin = _resolve_growth_origin(
        [
            (float(node["cx"]), float(node["cy"]), float(node["conc"]))
            for node in food_canvas
        ],
        span=float(min(WIDTH, HEIGHT)),
        fallback=(WIDTH / 2.0, HEIGHT / 2.0),
    )
    origin_identity_node, origin_identity_strength = _identity_influence(
        origin.x,
        origin.y,
        identity_nodes,
    )

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
            ".tl-reveal{opacity:0;"
            "animation:physReveal .8s ease-out var(--delay,0s) both}"
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
        if origin_identity_node is not None:
            spore_color = oklch_lerp(
                spore_color,
                origin_identity_node.identity.node_core,
                min(0.70, 0.32 + 0.28 * origin_identity_strength),
            )
        spore_when = _date_for_activity_fraction(0.0)
        P.append(
            '<circle data-role="physarum-spore" '
            f'cx="{origin.x:.1f}" cy="{origin.y:.1f}" '
            f'r="{2 + spore_fade * 3:.1f}" '
            f'fill="{spore_color}" filter="url(#nodeGlow)" '
            f"{_timeline_style(spore_when, 0.8 * spore_fade, 'tl-reveal tl-soft')}/>"
        )
        budget.add(1)

    # ── Ghost traces of pruned paths (maturity > 0.7) ─────────────
    ghost_fade = _fade(0.70, 1.0)
    ghost_color = oklch(0.20, 0.04, 250)

    # ── Vein contours ─────────────────────────────────────────────
    vein_fade = _fade(0.05, 0.50)
    if vein_fade > 0 and t_max > 0:
        # Compute contour thresholds spread across the trail range
        levels = [(i + 1) / (contour_levels + 1) for i in range(contour_levels)]

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

            filt = ' filter="url(#veinGlow)"' if li >= contour_levels // 2 else ""
            frac_for_level = 0.1 + li * 0.12
            when = _date_for_activity_fraction(min(1.0, frac_for_level))

            for chain in chains:
                if not budget.ok():
                    break
                smoothed = _chaikin_smooth(chain, iterations=1)
                pd = _path_d(smoothed)
                chain_color = draw_color
                chain_opacity = draw_opacity
                chain_sw = draw_sw
                if not is_ghost:
                    chain_color, identity_visibility = _resolve_vein_style(
                        smoothed,
                        chain_color,
                        identity_nodes,
                    )
                    chain_opacity = min(
                        0.96,
                        chain_opacity * (1.0 + 0.18 * identity_visibility),
                    )
                    chain_sw *= 1.0 + 0.10 * identity_visibility
                P.append(
                    f'<path d="{pd}" fill="none" stroke="{chain_color}" '
                    f'stroke-width="{chain_sw:.2f}" stroke-linecap="round" '
                    f'stroke-linejoin="round"{filt} '
                    f"{_timeline_style(when, chain_opacity, 'tl-reveal tl-crisp')}/>"
                )
                budget.add(1)

    # ── Food source nodes ─────────────────────────────────────────
    node_fade = _fade(0.10, 0.40)
    if node_fade > 0:
        for node in food_canvas:
            if not budget.ok():
                break
            cx = float(node["cx"])
            cy = float(node["cy"])
            conc = float(node["conc"])
            repo = node["repo"]
            identity: PhysarumIdentityPalette = node["identity"]
            identity_visibility = min(
                1.0,
                0.45 * identity.topic_signal + 0.20 * min(1.0, math.log1p(conc) / 4.0),
            )
            r = 3.0 + math.log1p(conc) * (1.35 + 0.30 * identity_visibility)
            node_when = _repo_date(repo) or _date_for_activity_fraction(0.3)
            language = identity.language or "unknown"
            halo_opacity = (0.24 + 0.18 * identity_visibility) * node_fade
            core_opacity = (0.76 + 0.18 * identity_visibility) * node_fade
            shell_opacity = (0.34 + 0.16 * identity_visibility) * node_fade
            halo_radius = r * (1.85 + 0.18 * identity.topic_signal)
            shell_width = 0.8 + 0.5 * identity.topic_signal
            # Outer glow ring
            P.append(
                f'<circle data-role="physarum-node-halo" data-language="{language}" '
                f'cx="{cx:.1f}" cy="{cy:.1f}" r="{halo_radius:.1f}" '
                f'fill="{identity.node_halo}" filter="url(#nodeGlow)" '
                f"{_timeline_style(node_when, halo_opacity, 'tl-reveal tl-soft')}/>"
            )
            budget.add(1)
            if not budget.ok():
                break
            P.append(
                f'<circle data-role="physarum-node-shell" data-language="{language}" '
                f'cx="{cx:.1f}" cy="{cy:.1f}" r="{r * 1.28:.1f}" fill="none" '
                f'stroke="{identity.node_shell}" stroke-width="{shell_width:.2f}" '
                f"{_timeline_style(node_when, shell_opacity, 'tl-reveal tl-soft')}/>"
            )
            budget.add(1)
            # Inner bright node
            P.append(
                f'<circle data-role="physarum-node-core" data-language="{language}" '
                f'cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" '
                f'fill="{identity.node_core}" filter="url(#nodeGlow)" '
                f"{_timeline_style(node_when, core_opacity, 'tl-reveal tl-crisp')}"
                "/>"
            )
            budget.add(1)

            # Repo name label
            label = repo.get("name", "")
            if label and node_fade > 0.5:
                label_timeline = _timeline_style(
                    node_when, 0.5 * node_fade, "tl-reveal tl-soft"
                )
                P.append(
                    f'<text x="{cx:.1f}" y="{cy + r + 8:.1f}" '
                    'font-family="monospace" font-size="6" '
                    f'fill="{identity.label_color}" '
                    f'text-anchor="middle" '
                    f"{label_timeline}"
                    ">"
                    f"{label}</text>"
                )
                budget.add(1)

    P.append("</svg>")
    return "\n".join(P)
