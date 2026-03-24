"""
Turing Patterns — Animated Community Art
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Gray-Scott reaction-diffusion simulation on an N x N grid producing organic
Turing patterns (spots, stripes, labyrinths, mitosis).  GitHub profile data
drives the simulation parameters — feed rate from language diversity, kill
rate from star velocity, grid resolution from total stars, and iteration
count from account age.

Each repository seeds a circular perturbation zone on the grid; language
hues color a Voronoi region so the final pattern blends the developer's
language palette into the emergent structure.

Produces a CSS-animated SVG safe for ``<img>`` embedding in a GitHub
README.

Public API::

    render_svg(history, dark_mode, duration, snapshot_progress) -> str
    generate(history, dark_mode, output_path, duration) -> Path
"""

from __future__ import annotations

import math
import random
from datetime import date as dt_date
from html import escape
from pathlib import Path

import numpy as np

from ..utils import get_logger
from .shared import (
    LANG_HUES,
    _build_world_palette_extended,
    activity_tempo,
    compute_world_state,
    oklch,
    select_palette_for_world,
    svg_footer,
    svg_header,
    visual_complexity,
    volumetric_glow_filter,
)

logger = get_logger(module=__name__)

# ---------------------------------------------------------------------------
# Canvas constants
# ---------------------------------------------------------------------------
_WIDTH = 800
_HEIGHT = 800

# ---------------------------------------------------------------------------
# Reaction-diffusion simulation
# ---------------------------------------------------------------------------


def _laplacian(grid: np.ndarray) -> np.ndarray:
    """Discrete Laplacian via 3x3 weighted kernel on a toroidal grid.

    Kernel weights:
        0.05  0.20  0.05
        0.20 -1.00  0.20
        0.05  0.20  0.05
    """
    return (
        0.05 * np.roll(np.roll(grid, 1, 0), 1, 1)
        + 0.20 * np.roll(grid, 1, 0)
        + 0.05 * np.roll(np.roll(grid, 1, 0), -1, 1)
        + 0.20 * np.roll(grid, 1, 1)
        + 0.20 * np.roll(grid, -1, 1)
        + 0.05 * np.roll(np.roll(grid, -1, 0), 1, 1)
        + 0.20 * np.roll(grid, -1, 0)
        + 0.05 * np.roll(np.roll(grid, -1, 0), -1, 1)
        - 1.0 * grid
    )


def _simulate_gray_scott(
    N: int,
    seed_positions: list[tuple[int, int, float]],
    feed: float,
    kill: float,
    n_steps: int,
    rng_seed: int = 42,
    *,
    noise_amp: float = 0.02,
    v_seed_intensity: float = 1.0,
    f_grid: np.ndarray | None = None,
    k_grid: np.ndarray | None = None,
    pr_flow_bias_quadrant: int | None = None,
    defect_positions: list[tuple[int, int]] | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Run Gray-Scott reaction-diffusion and return (U, V, first_hit).

    *seed_positions*: list of (row, col, radius) for initial V-perturbation.
    *first_hit*: iteration when V first exceeds 0.15 at each cell (-1 = never).

    Extended parameters (all degrade gracefully to defaults):
      *noise_amp*: amplitude of symmetry-breaking noise on V.
      *v_seed_intensity*: V value when seeding repo positions (0.5-1.0).
      *f_grid* / *k_grid*: per-cell feed/kill rate arrays (Voronoi topic regions).
      *pr_flow_bias_quadrant*: if set (0-3), bias seed positions toward that quadrant.
      *defect_positions*: extra V-blob nucleation points from open issues.
    """
    Du = 0.16
    Dv = 0.08

    # Clamp v_seed_intensity
    v_seed = min(1.0, max(0.5, v_seed_intensity))

    U = np.ones((N, N), dtype=np.float64)
    V = np.zeros((N, N), dtype=np.float64)
    first_hit = np.full((N, N), -1, dtype=np.int64)

    rng = np.random.default_rng(rng_seed)
    yy, xx = np.mgrid[0:N, 0:N]

    # --- PR flow bias: shift seed positions toward a quadrant ---
    biased_seeds = list(seed_positions)
    if pr_flow_bias_quadrant is not None and biased_seeds:
        qr_offset = [(-N // 8, -N // 8), (-N // 8, N // 8),
                      (N // 8, -N // 8), (N // 8, N // 8)]
        dr, dc = qr_offset[pr_flow_bias_quadrant % 4]
        biased_seeds = [
            (max(2, min(N - 3, r + dr // 2)),
             max(2, min(N - 3, c + dc // 2)),
             rad)
            for r, c, rad in biased_seeds
        ]

    # Seed perturbation zones (with v_seed_intensity)
    for ry, rx, radius in biased_seeds:
        mask = (xx - rx) ** 2 + (yy - ry) ** 2 < radius**2
        V[mask] = v_seed
        U[mask] = 0.5

    # Fallback: guarantee at least some seeds via random blobs
    if not biased_seeds or np.sum(V > 0) < 5:
        n_fallback = max(3, 6 - len(biased_seeds))
        for _ in range(n_fallback):
            cy = int(rng.integers(N // 4, 3 * N // 4))
            cx = int(rng.integers(N // 4, 3 * N // 4))
            r = int(rng.integers(2, max(3, N // 15)))
            mask = (xx - cx) ** 2 + (yy - cy) ** 2 < r**2
            V[mask] = v_seed
            U[mask] = 0.5

    # --- Defect perturbations: extra nucleation points from open issues ---
    if defect_positions:
        for dy, dx in defect_positions:
            if 0 <= dy < N and 0 <= dx < N:
                r_def = max(1, N // 40)
                mask = (xx - dx) ** 2 + (yy - dy) ** 2 < r_def**2
                V[mask] = v_seed * 0.8
                U[mask] = 0.5

    # Add small noise to break symmetry (amplitude driven by data)
    V += rng.uniform(0, noise_amp, (N, N))
    U = np.clip(U, 0, 1)

    # Record initial first_hit
    first_hit[V > 0.15] = 0

    # Use per-cell f/k grids if provided, else broadcast scalar
    use_fk_grids = f_grid is not None and k_grid is not None

    # Simulate
    report_interval = max(1, n_steps // 5)
    for step in range(1, n_steps + 1):
        lap_U = _laplacian(U)
        lap_V = _laplacian(V)
        uvv = U * V * V
        if use_fk_grids:
            U += Du * lap_U - uvv + f_grid * (1.0 - U)
            V += Dv * lap_V + uvv - (f_grid + k_grid) * V
        else:
            U += Du * lap_U - uvv + feed * (1.0 - U)
            V += Dv * lap_V + uvv - (feed + kill) * V
        np.clip(U, 0, 1, out=U)
        np.clip(V, 0, 1, out=V)

        # Track first-hit
        newly_hit = (V > 0.15) & (first_hit < 0)
        first_hit[newly_hit] = step

        if step % report_interval == 0:
            logger.debug(
                "RD step {step}/{total} — V mean={vm:.4f} max={vx:.4f}",
                step=step,
                total=n_steps,
                vm=float(V.mean()),
                vx=float(V.max()),
            )

    return U, V, first_hit


# ---------------------------------------------------------------------------
# Data extraction helpers
# ---------------------------------------------------------------------------


def _parse_account_age_days(history: dict) -> int:
    """Parse account_created to age in days; default 365."""
    acct = history.get("account_created", "")
    if not acct:
        return 365
    try:
        if isinstance(acct, str):
            created = dt_date.fromisoformat(acct[:10])
        else:
            created = acct
        return max(1, (dt_date.today() - created).days)
    except (ValueError, TypeError):
        return 365


def _repo_grid_positions(
    history: dict,
    metrics: dict,
    N: int,
    rng: random.Random,
    topic_lookup: dict[str, tuple[str, int, float]] | None = None,
) -> list[tuple[int, int, float, float]]:
    """Map repos onto the N x N grid. Returns [(row, col, radius, hue), ...]."""
    repos = metrics.get("repos", []) or history.get("repos", []) or []
    positions: list[tuple[int, int, float, float]] = []
    margin = max(2, N // 10)

    for i, repo in enumerate(repos[:30]):
        lang = repo.get("language")
        hue = float(LANG_HUES.get(lang, LANG_HUES.get(None, 155)))
        stars = repo.get("stars", 0) or 0
        # Deterministic position from repo name hash
        name = repo.get("name", f"repo-{i}")
        h = hash(name) & 0x7FFFFFFF
        row = margin + (h % (N - 2 * margin))
        col = margin + ((h >> 8) % (N - 2 * margin))
        radius = max(2.0, min(N / 8, 2.0 + math.log1p(stars) * 0.8))
        if topic_lookup:
            _topic_name, _topic_count, topic_signal = _repo_topic_signal(
                repo, topic_lookup
            )
            radius *= 1.0 + topic_signal * 0.35
        positions.append((row, col, radius, hue))

    return positions


def _build_voronoi_hue_map(
    N: int,
    repo_positions: list[tuple[int, int, float, float]],
    default_hue: float = 155.0,
) -> np.ndarray:
    """Assign each grid cell a hue from the nearest repo (Voronoi partition)."""
    hue_map = np.full((N, N), default_hue, dtype=np.float64)
    if not repo_positions:
        return hue_map

    # Vectorized nearest-repo assignment
    yy, xx = np.mgrid[0:N, 0:N]
    min_dist = np.full((N, N), np.inf, dtype=np.float64)

    for row, col, _radius, hue in repo_positions:
        # Toroidal distance
        dy = np.minimum(np.abs(yy - row), N - np.abs(yy - row)).astype(np.float64)
        dx = np.minimum(np.abs(xx - col), N - np.abs(xx - col)).astype(np.float64)
        dist = dy * dy + dx * dx
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
    repo: dict,
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


# ---------------------------------------------------------------------------
# SVG rendering
# ---------------------------------------------------------------------------

_CSS_TEMPLATE = """\
<style>
  .c{{animation:cellReveal 1.2s ease-out both}}
  @keyframes cellReveal{{from{{opacity:0}}to{{opacity:var(--o,0.8)}}}}
  @keyframes timelineFill{{from{{width:0}}to{{width:100%}}}}
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
) -> tuple[str, int]:
    """Core render function; returns (svg_string, cell_count)."""
    snapshot_progress = _clamp_snapshot_progress(snapshot_progress)
    snapshot_mode = snapshot_progress is not None

    metrics = history.get("current_metrics", {})
    repos = metrics.get("repos", []) or history.get("repos", []) or []

    # ------------------------------------------------------------------
    # World-state palette
    # ------------------------------------------------------------------
    ws = compute_world_state(metrics)
    pal = _build_world_palette_extended(
        ws.time_of_day,
        ws.weather,
        ws.season,
        ws.energy,
    )
    palette_name = select_palette_for_world(ws)
    complexity = visual_complexity(metrics)
    tempo = activity_tempo(history.get("contributions_monthly"))

    # ------------------------------------------------------------------
    # Simulation parameters from GitHub data
    # ------------------------------------------------------------------
    total_stars = metrics.get("stars", 0) or 0
    network_count = metrics.get("network_count", 0) or 0

    # #9 — network_count → Grid density boost
    N = min(120, max(60, 60 + total_stars // 10 + network_count // 100))

    # Feed rate from language diversity / complexity [0.025, 0.060]
    feed = 0.025 + 0.035 * complexity

    # Kill rate from star velocity [0.055, 0.065]
    star_vel = metrics.get("star_velocity", {})
    vel_rate = star_vel.get("recent_rate", 0) if isinstance(star_vel, dict) else 0
    kill = 0.055 + min(0.010, vel_rate * 0.002)

    # Iteration count from account age
    age_days = _parse_account_age_days(history)
    n_steps = min(5000, max(1500, age_days * 2))

    # Deterministic RNG seed
    rng_seed = (total_stars * 7919 + (metrics.get("forks", 0) or 0) * 6271) % (2**31)
    rng = random.Random(rng_seed)

    # ------------------------------------------------------------------
    # New data reads for enhanced mappings
    # ------------------------------------------------------------------
    followers = metrics.get("followers", 0) or 0
    total_commits = metrics.get("total_commits", 0) or 0
    contributions = metrics.get("contributions_last_year", 0) or 0
    topic_clusters = metrics.get("topic_clusters", {}) or {}
    top_topic_entries = _top_topic_entries(topic_clusters)
    topic_lookup = {
        topic.lower(): (topic, count, signal)
        for topic, count, signal in top_topic_entries
    }
    commit_hours = metrics.get("commit_hour_distribution", {}) or {}
    releases = metrics.get("releases", []) or []
    recent_merged_prs = metrics.get("recent_merged_prs", []) or []
    streaks = metrics.get("contribution_streaks", {}) or {}
    total_issues = (
        metrics.get("total_issues", 0)
        or metrics.get("open_issues_count", 0)
        or 0
    )
    public_gists = metrics.get("public_gists", 0) or 0

    # #2 — total_commits → Noise perturbation amplitude
    noise_amp = 0.02 + min(0.05, total_commits / 50000)

    # #8 — contribution_streaks → Pattern stability
    streak_active = (
        streaks.get("streak_active", False) if isinstance(streaks, dict) else False
    )
    if streak_active:
        noise_amp *= 0.7  # active streak → more ordered
    elif streaks and not streak_active:
        noise_amp *= 1.2  # broken streak → more chaotic

    # #3 — contributions_last_year → V-seed intensity
    v_seed_intensity = 0.5 + min(0.5, contributions / 2000)

    # #7 — recent_merged_prs → Flow bias in V-seed placement
    pr_count = len(recent_merged_prs) if isinstance(recent_merged_prs, list) else 0
    pr_flow_bias_quadrant: int | None = None
    if pr_count > 0:
        pr_flow_bias_quadrant = pr_count % 4

    # Repo positions on the grid
    repo_positions = _repo_grid_positions(
        history,
        metrics,
        N,
        rng,
        topic_lookup=topic_lookup,
    )
    seed_positions = [(r, c, rad) for r, c, rad, _h in repo_positions]
    repo_annotations: list[dict[str, float | int | str]] = []
    for repo, (row, col, radius, hue) in zip(
        repos[: len(repo_positions)], repo_positions, strict=False
    ):
        topic_label, topic_count, topic_signal = _repo_topic_signal(repo, topic_lookup)
        if topic_signal <= 0:
            continue
        repo_annotations.append(
            {
                "row": row,
                "col": col,
                "radius": radius,
                "hue": hue,
                "label": topic_label,
                "count": topic_count,
                "signal": topic_signal,
            }
        )

    # #10 — total_issues → Defect perturbations (extra nucleation points)
    defect_positions: list[tuple[int, int]] = []
    if total_issues > 0:
        defect_rng = random.Random(rng_seed + 9999)
        n_defects = min(15, total_issues)
        for _ in range(n_defects):
            dy = defect_rng.randint(2, N - 3)
            dx = defect_rng.randint(2, N - 3)
            defect_positions.append((dy, dx))

    # #4 — topic_clusters → Multi-region f/k variation (Voronoi regions)
    f_grid: np.ndarray | None = None
    k_grid: np.ndarray | None = None
    if repo_annotations:
        f_grid = np.full((N, N), feed, dtype=np.float64)
        k_grid = np.full((N, N), kill, dtype=np.float64)
        yy_topic, xx_topic = np.mgrid[0:N, 0:N]
        for annotation in repo_annotations[:5]:
            row = float(annotation["row"])
            col = float(annotation["col"])
            signal = float(annotation["signal"])
            sigma = max(3.5, float(annotation["radius"]) * 1.8)
            dy = np.minimum(
                np.abs(yy_topic - row), N - np.abs(yy_topic - row)
            ).astype(np.float64)
            dx = np.minimum(
                np.abs(xx_topic - col), N - np.abs(xx_topic - col)
            ).astype(np.float64)
            influence = np.exp(-(dx * dx + dy * dy) / (2 * sigma * sigma))
            f_grid += (signal - 0.45) * 0.003 * influence
            k_grid += (0.55 - signal) * 0.002 * influence

    logger.info(
        "Turing RD: N={N} feed={f:.4f} kill={k:.4f} steps={s} "
        "repos={nr} dark={dm} palette={pal} complexity={cx:.2f} tempo={tp:.2f}",
        N=N,
        f=feed,
        k=kill,
        s=n_steps,
        nr=len(repo_positions),
        dm=dark_mode,
        pal=palette_name,
        cx=complexity,
        tp=tempo,
    )

    # ------------------------------------------------------------------
    # Run simulation
    # ------------------------------------------------------------------
    if snapshot_mode:
        effective_steps = max(1, int(n_steps * (snapshot_progress or 0.0)))
    else:
        effective_steps = n_steps

    U, V, first_hit = _simulate_gray_scott(
        N,
        seed_positions,
        feed,
        kill,
        effective_steps,
        rng_seed=rng_seed,
        noise_amp=noise_amp,
        v_seed_intensity=v_seed_intensity,
        f_grid=f_grid,
        k_grid=k_grid,
        pr_flow_bias_quadrant=pr_flow_bias_quadrant,
        defect_positions=defect_positions,
    )

    # Voronoi hue map
    voronoi_hue = _build_voronoi_hue_map(N, repo_positions)

    # ------------------------------------------------------------------
    # Compute reveal delays (animated mode only)
    # ------------------------------------------------------------------
    max_first_hit = int(first_hit.max()) if first_hit.max() > 0 else 1
    reveal_end = duration * 0.93

    # ------------------------------------------------------------------
    # Build SVG
    # ------------------------------------------------------------------
    dur_s = f"{duration}s"
    cell_size = _WIDTH / N

    # Background colours
    if dark_mode:
        bg_color = pal["bg_primary"]
        timeline_bg = "rgba(255,255,255,0.08)"
        timeline_fg = pal["accent"]
        text_color = "rgba(255,255,255,0.5)"
    else:
        bg_color = pal["bg_primary"]
        timeline_bg = "rgba(0,0,0,0.06)"
        timeline_fg = pal["accent"]
        text_color = "rgba(0,0,0,0.35)"

    parts: list[str] = []
    parts.append(svg_header(_WIDTH, _HEIGHT))

    if not snapshot_mode:
        parts.append(_CSS_TEMPLATE)

    # Background
    parts.append(f'<rect width="{_WIDTH}" height="{_HEIGHT}" fill="{bg_color}"/>\n')

    # ------------------------------------------------------------------
    # SVG defs — #1 border glow filter (followers-driven)
    # ------------------------------------------------------------------
    if followers > 0:
        parts.append("<defs>\n")
        parts.append(volumetric_glow_filter("borderGlow", radius=4.0))
        parts.append("\n</defs>\n")

    # ------------------------------------------------------------------
    # Render grid cells
    # ------------------------------------------------------------------
    cell_count = 0
    v_threshold = 0.05  # minimum V to render

    # Pre-compute all cell strings in batches for performance
    rects: list[str] = []
    for y in range(N):
        for x in range(N):
            v_val = float(V[y, x])
            if v_val < v_threshold:
                continue

            hue = float(voronoi_hue[y, x])

            if dark_mode:
                lightness = 0.08 + 0.65 * v_val
                chroma = 0.03 + 0.22 * v_val
            else:
                lightness = 0.95 - 0.65 * v_val
                chroma = 0.03 + 0.22 * v_val

            color = oklch(lightness, chroma, hue)
            opacity = round(min(0.95, 0.15 + 0.80 * v_val), 3)

            px = round(x * cell_size, 2)
            py = round(y * cell_size, 2)
            cs = round(cell_size, 2)

            if snapshot_mode:
                rects.append(
                    f'<rect x="{px}" y="{py}" width="{cs}" height="{cs}" '
                    f'fill="{color}" opacity="{opacity}"/>\n'
                )
            else:
                # Compute reveal delay from first_hit
                fh = int(first_hit[y, x])
                if fh < 0:
                    delay = reveal_end * 0.95
                else:
                    delay = round((fh / max_first_hit) * reveal_end, 3)

                rects.append(
                    f'<rect class="c" x="{px}" y="{py}" width="{cs}" '
                    f'height="{cs}" fill="{color}" '
                    f'style="--o:{opacity};animation-delay:{delay:.2f}s"/>\n'
                )
            cell_count += 1

    parts.append('<g id="turing-pattern">\n')
    parts.extend(rects)
    parts.append("</g>\n")

    if repo_annotations:
        parts.append('<g id="topic-constellations">\n')
        for annotation in sorted(
            repo_annotations,
            key=lambda item: (-int(item["count"]), str(item["label"])),
        )[:3]:
            cx_const = round(float(annotation["col"]) * (_WIDTH / N), 2)
            cy_const = round(float(annotation["row"]) * (_HEIGHT / N), 2)
            signal = float(annotation["signal"])
            count = int(annotation["count"])
            ring_r = round(
                max(12.0, float(annotation["radius"]) * (_WIDTH / N) * (1.0 + signal)),
                1,
            )
            ring_color = oklch(
                0.72 if dark_mode else 0.42,
                0.14,
                float(annotation["hue"]),
            )
            topic_name = escape(f'{str(annotation["label"]).title()} Field')
            noun = "repo" if count == 1 else "repos"
            topic_note = escape(f"{count} linked {noun}")
            parts.append(
                f'<circle cx="{cx_const}" cy="{cy_const}" r="{ring_r}" fill="none" '
                f'stroke="{ring_color}" stroke-width="1.1" opacity="0.48"/>\n'
            )
            parts.append(
                f'<text x="{cx_const}" y="{cy_const - ring_r - 6:.1f}" '
                f'text-anchor="middle" '
                f'font-size="8.2" font-family="Georgia,serif" font-style="italic" '
                f'fill="{pal["text_secondary"]}" paint-order="stroke fill" '
                f'stroke="{bg_color}" stroke-width="2.2" stroke-linejoin="round">'
                f'{topic_name}</text>\n'
            )
            parts.append(
                f'<text x="{cx_const}" y="{cy_const - ring_r + 3:.1f}" '
                f'text-anchor="middle" '
                f'font-size="5.1" font-family="Georgia,serif" letter-spacing="0.7" '
                f'fill="{pal["muted"]}" paint-order="stroke fill" '
                f'stroke="{bg_color}" stroke-width="1.7" stroke-linejoin="round">'
                f'{topic_note}</text>\n'
            )
        parts.append("</g>\n")

    # ------------------------------------------------------------------
    # #1 — followers → Grid border glow
    # ------------------------------------------------------------------
    if followers > 0:
        glow_intensity = min(1.0, followers / 500)
        glow_opacity = round(0.15 + 0.55 * glow_intensity, 3)
        glow_color = pal["accent"]
        parts.append(
            f'<rect x="4" y="4" width="{_WIDTH - 8}" height="{_HEIGHT - 8}" '
            f'rx="6" ry="6" fill="none" stroke="{glow_color}" '
            f'stroke-width="{round(1.5 + 2.5 * glow_intensity, 2)}" '
            f'opacity="{glow_opacity}" filter="url(#borderGlow)"/>\n'
        )

    # ------------------------------------------------------------------
    # #6 — releases → Shockwave rings
    # ------------------------------------------------------------------
    if releases and repo_positions:
        n_rings = min(5, len(releases) if isinstance(releases, list) else 0)
        if n_rings > 0:
            ring_color = pal.get("highlight", pal["accent"])
            for ri in range(n_rings):
                # Place ring at a repo position (cycle through available)
                rp = repo_positions[ri % len(repo_positions)]
                cx_ring = round(rp[1] * (_WIDTH / N), 2)
                cy_ring = round(rp[0] * (_HEIGHT / N), 2)
                ring_r = round(15 + ri * 12, 1)
                ring_opacity = round(0.30 - ri * 0.03, 2)
                ring_opacity = max(0.15, ring_opacity)
                parts.append(
                    f'<circle cx="{cx_ring}" cy="{cy_ring}" r="{ring_r}" '
                    f'fill="none" stroke="{ring_color}" stroke-width="1.2" '
                    f'opacity="{ring_opacity}"/>\n'
                )

    # ------------------------------------------------------------------
    # #5 — commit_hour_distribution → Circadian gradient overlay
    # ------------------------------------------------------------------
    if commit_hours and isinstance(commit_hours, dict):
        tod = ws.time_of_day
        # Dawn=warm overlay, night=cool overlay, day/golden=neutral
        if tod == "dawn":
            circ_color = pal.get("warm", pal["accent"])
        elif tod == "night":
            circ_color = pal.get("cool", pal.get("secondary", pal["accent"]))
        elif tod == "golden":
            circ_color = pal.get("warm", pal["accent"])
        else:
            circ_color = pal.get("muted", pal["accent"])

        circ_opacity = round(0.06 + 0.04 * min(1.0, len(commit_hours) / 24), 3)
        parts.append(
            f'<defs><radialGradient id="circadianGrad" cx="50%" cy="50%" r="70%">\n'
            f'  <stop offset="0%" stop-color="{circ_color}" '
            f'stop-opacity="{circ_opacity}"/>\n'
            f'  <stop offset="100%" stop-color="{circ_color}" stop-opacity="0"/>\n'
            f'</radialGradient></defs>\n'
            f'<rect width="{_WIDTH}" height="{_HEIGHT}" fill="url(#circadianGrad)"/>\n'
        )

    # ------------------------------------------------------------------
    # #11 — public_gists → Accent dots
    # ------------------------------------------------------------------
    if public_gists > 0:
        n_dots = min(public_gists, 10)
        dot_color = pal.get("highlight", pal["accent"])
        dot_rng = random.Random(rng_seed + 7777)
        for di in range(n_dots):
            dx = round(dot_rng.uniform(20, _WIDTH - 20), 2)
            dy = round(dot_rng.uniform(20, _HEIGHT - 40), 2)
            dot_r = round(dot_rng.uniform(2.0, 4.5), 2)
            dot_opacity = round(dot_rng.uniform(0.3, 0.7), 2)
            parts.append(
                f'<circle cx="{dx}" cy="{dy}" r="{dot_r}" '
                f'fill="{dot_color}" opacity="{dot_opacity}"/>\n'
            )

    # ------------------------------------------------------------------
    # Timeline bar at bottom
    # ------------------------------------------------------------------
    bar_y = _HEIGHT - 16
    bar_h = 4
    bar_w = _WIDTH - 80
    bar_x = 40

    parts.append(
        f'<rect x="{bar_x}" y="{bar_y}" width="{bar_w}" height="{bar_h}" '
        f'rx="2" fill="{timeline_bg}"/>\n'
    )
    if snapshot_mode:
        fill_w = round(bar_w * (snapshot_progress or 0.0), 1)
        parts.append(
            f'<rect x="{bar_x}" y="{bar_y}" width="{fill_w}" '
            f'height="{bar_h}" rx="2" fill="{timeline_fg}" opacity="0.8"/>\n'
        )
    else:
        parts.append(
            f'<rect x="{bar_x}" y="{bar_y}" width="0" height="{bar_h}" rx="2" '
            f'fill="{timeline_fg}" opacity="0.8">\n'
            f'  <animate attributeName="width" from="0" to="{bar_w}" '
            f'dur="{dur_s}" fill="freeze"/>\n'
            f"</rect>\n"
        )

    # Year tick marks
    account_created = history.get("account_created", "")
    stars_events = history.get("stars", []) or []
    forks_events = history.get("forks", []) or []
    all_dates = sorted(
        [e.get("date", "") for e in stars_events]
        + [e.get("date", "") for e in forks_events],
    )
    all_dates = [d for d in all_dates if d and len(d) >= 4]

    if all_dates:
        min_year = int(all_dates[0][:4])
        max_year = int(all_dates[-1][:4])
    elif account_created and len(account_created) >= 4:
        min_year = int(account_created[:4])
        max_year = dt_date.today().year
    else:
        min_year, max_year = 2020, dt_date.today().year

    year_span = max(max_year - min_year, 1)
    for yr in range(min_year, max_year + 1):
        tick_x = round(bar_x + (yr - min_year) / year_span * bar_w, 1)
        parts.append(
            f'<line x1="{tick_x}" y1="{bar_y - 2}" x2="{tick_x}" '
            f'y2="{bar_y + bar_h + 2}" stroke="{text_color}" stroke-width="1"/>\n'
        )
        parts.append(
            f'<text x="{tick_x}" y="{bar_y - 5}" text-anchor="middle" '
            f'font-size="7" font-family="monospace" fill="{text_color}">{yr}</text>\n'
        )

    parts.append(svg_footer())
    return "".join(parts), cell_count


# =========================================================================
#  PUBLIC API
# =========================================================================


def render_svg(
    history: dict,
    dark_mode: bool = False,
    duration: float = 60.0,
    snapshot_progress: float | None = None,
) -> str:
    """Return SVG string."""
    svg_text, _ = _render_svg(
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
    out = Path(output_path or f".github/assets/img/animated-community{suffix}.svg")
    out.parent.mkdir(parents=True, exist_ok=True)
    svg_text, cell_count = _render_svg(history, dark_mode=dark_mode, duration=duration)
    out.write_text(svg_text, encoding="utf-8")

    size_kb = len(svg_text.encode("utf-8")) / 1024
    logger.info(
        "Turing Patterns saved: {path} ({cells} cells, {kb:.0f} KB)",
        path=out,
        cells=cell_count,
        kb=size_kb,
    )
    return out
