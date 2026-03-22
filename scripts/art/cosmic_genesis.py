"""
Cosmic Genesis — Animated Community Art
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Clifford attractor density field revealed progressively as stars/forks
accumulate.  Deep-space starfield backdrop with depth layers, nebula wisps,
milestone ring-bursts with poetic labels, contribution particle emission,
OKLCH color science, and calendar-proportional reveal timing.

Produces a 30-second looping CSS-animated SVG safe for ``<img>`` embedding
in a GitHub README (CSS ``@keyframes`` + SMIL ``<animate>``).

Public API::

    generate(history, dark_mode, output_path, duration) -> Path
"""

from __future__ import annotations

import math
import random
from datetime import date as dt_date
from pathlib import Path

import numpy as np

from ..utils import get_logger
from .shared import (
    LANG_HUES,
    oklch,
    svg_footer,
    svg_header,
)

logger = get_logger(module=__name__)

# ---------------------------------------------------------------------------
# Canvas constants
# ---------------------------------------------------------------------------
_WIDTH = 800
_HEIGHT = 800

# ---------------------------------------------------------------------------
# Clifford attractor math
# ---------------------------------------------------------------------------


def _compute_clifford(
    a: float,
    b: float,
    c: float,
    d: float,
    iterations: int,
    grid_size: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Run the Clifford attractor and return (density, first_hit) grids."""
    x, y = 0.1, 0.1
    density = np.zeros((grid_size, grid_size), dtype=np.float64)
    first_hit = np.full((grid_size, grid_size), -1, dtype=np.int64)
    coord_min, coord_max = -3.0, 3.0
    coord_range = coord_max - coord_min

    for i in range(iterations):
        x_new = math.sin(a * y) + c * math.cos(a * x)
        y_new = math.sin(b * x) + d * math.cos(b * y)
        x, y = x_new, y_new
        gx = int((x - coord_min) / coord_range * (grid_size - 1))
        gy = int((y - coord_min) / coord_range * (grid_size - 1))
        if 0 <= gx < grid_size and 0 <= gy < grid_size:
            if density[gy, gx] == 0:
                first_hit[gy, gx] = i
            density[gy, gx] += 1.0

    return density, first_hit


# ---------------------------------------------------------------------------
# Continuous parameter mapping (replaces SHA-256)
# ---------------------------------------------------------------------------


def _continuous_attractor_params(
    metrics: dict,
) -> tuple[float, float, float, float, float]:
    """Map metrics continuously to curated Clifford attractor parameter space.

    Returns (a, b, c, d, hue_shift).  The parameter region a,b in [1.5, 2.0]
    and c,d in [-1.5, 0.5] reliably produces dense, structured attractors
    per Paul Bourke's catalog.
    """

    def _norm(val: float, hi: float = 5000) -> float:
        return min(1.0, math.log1p(val) / math.log1p(hi))

    stars = metrics.get("stars", 0)
    forks = metrics.get("forks", 0)
    watchers = metrics.get("watchers", 0)
    network = metrics.get("network_count", 0)

    s = _norm(stars, 5000)
    f = _norm(forks, 1000)
    w = _norm(watchers, 500)
    n = _norm(network, 3000)

    # Wider parameter range for denser attractors at all profile sizes.
    # Base values (1.7, 1.7, -1.3, -1.3) produce rich structure even at zero metrics.
    a = 1.7 + s * 0.4  # [1.7, 2.1]
    b = 1.7 + f * 0.4  # [1.7, 2.1]
    c = -1.3 + n * 1.6  # [-1.3, 0.3]
    d = -1.3 + w * 1.6  # [-1.3, 0.3]

    ratio = forks / max(stars, 1)
    hue_shift = min(1.0, ratio * 2.0)

    return a, b, c, d, hue_shift


# ---------------------------------------------------------------------------
# Calendar-proportional timeline mapping
# ---------------------------------------------------------------------------


def _map_to_timeline_chronological(
    first_hit: np.ndarray,
    events: list[dict],
    total_duration: float,
) -> dict[tuple[int, int], float]:
    """Map cells to animation delays proportional to calendar dates."""
    reveal_end = total_duration * 0.93

    dates: list[str] = [e.get("date", "") for e in events]
    dates = [d for d in dates if d and len(d) >= 10]

    ordinals: list[int] = []
    for d in dates:
        try:
            ordinals.append(dt_date.fromisoformat(d[:10]).toordinal())
        except (ValueError, IndexError):
            continue

    # Collect populated cells sorted by iteration
    hits: list[tuple[int, int, int]] = []
    rows, cols = first_hit.shape
    for r in range(rows):
        for c in range(cols):
            it = int(first_hit[r, c])
            if it >= 0:
                hits.append((it, r, c))
    if not hits:
        return {}
    hits.sort(key=lambda x: x[0])
    n_cells = len(hits)

    # Fallback to rank-based if insufficient date data
    if len(ordinals) < 2:
        mapping: dict[tuple[int, int], float] = {}
        for rank, (_it, r, c) in enumerate(hits):
            frac = rank / max(n_cells - 1, 1)
            t = frac**0.8 * reveal_end
            mapping[(r, c)] = round(t, 3)
        return mapping

    min_ord, max_ord = ordinals[0], ordinals[-1]
    span = max(max_ord - min_ord, 1)
    n_events = len(ordinals)
    mapping = {}

    for rank, (_it, r, c) in enumerate(hits):
        event_idx = min(int(rank / n_cells * n_events), n_events - 1)
        frac = (ordinals[event_idx] - min_ord) / span
        t = frac**0.85 * reveal_end
        mapping[(r, c)] = round(t, 3)

    return mapping


# ---------------------------------------------------------------------------
# OKLCH color with chroma bloom
# ---------------------------------------------------------------------------


def _density_color_oklch(
    val: float,
    time_frac: float,
    hue_shift: float,
) -> str:
    """OKLCH color ramp: violet → teal → amber → gold with chroma bloom."""
    if time_frac < 0.25:
        t = time_frac / 0.25
        L = 0.20 + 0.12 * t + 0.18 * val
        C = 0.04 + 0.10 * val * t  # chroma blooms with time
        H = 280 - t * 30 + hue_shift * 20
    elif time_frac < 0.55:
        t = (time_frac - 0.25) / 0.30
        L = 0.30 + 0.22 * t + 0.20 * val
        C = 0.09 + 0.12 * val
        H = 250 - t * 80 + hue_shift * 15
    elif time_frac < 0.85:
        t = (time_frac - 0.55) / 0.30
        L = 0.45 + 0.22 * t + 0.18 * val
        C = 0.14 + 0.12 * val
        H = 50 - t * 10 + hue_shift * 10
    else:
        t = (time_frac - 0.85) / 0.15
        L = 0.72 + 0.18 * t
        C = 0.14 * (1.0 - t * 0.6)
        H = 75 + hue_shift * 5

    return oklch(L, C, H)


# ---------------------------------------------------------------------------
# Milestone helpers
# ---------------------------------------------------------------------------

_MILESTONE_LABELS = {
    10: "first sparks",
    25: "gathering light",
    50: "constellation forming",
    100: "a hundred points of light",
    250: "the community takes shape",
    500: "gravity wells deepen",
    1000: "a thousand voices",
    2500: "the galaxy remembers",
    5000: "cosmic resonance",
}


def _milestone_indices(events: list) -> list[tuple[int, float]]:
    """Return (milestone_value, fractional_position) pairs."""
    thresholds = [10, 25, 50, 100, 250, 500, 1000, 2500, 5000, 10000]
    n = len(events)
    results: list[tuple[int, float]] = []
    for th in thresholds:
        if th <= n:
            results.append((th, th / max(n, 1)))
    return results


# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------

_COMMUNITY_CSS = """\
<style>
  .cr{{animation:cellReveal 1.2s ease-out both,cellBreathe var(--br,7s) ease-in-out var(--bd,2s) infinite}}
  @keyframes cellReveal{{from{{opacity:0}}to{{opacity:var(--o,0.8)}}}}
  @keyframes cellBreathe{{
    0%,100%{{opacity:var(--o,0.8)}}
    50%{{opacity:calc(var(--o,0.8) * 0.6)}}
  }}
  @keyframes twinkle{{0%,100%{{opacity:.15}}50%{{opacity:.85}}}}
  @keyframes milestonePulse{{
    0%{{r:5;opacity:.8;stroke-width:2}}
    50%{{r:50;opacity:0;stroke-width:.3}}
    100%{{r:5;opacity:0;stroke-width:2}}
  }}
  @keyframes zoomOut{{
    0%{{transform:scale(1.45) translate(-15.5%,-15.5%)}}
    100%{{transform:scale(1) translate(0,0)}}
  }}
  @keyframes timelineFill{{from{{width:0}}to{{width:100%}}}}
  @keyframes bgWarm1{{from{{stop-color:{bg_from1}}}to{{stop-color:{bg_to1}}}}}
  @keyframes bgWarm2{{from{{stop-color:{bg_from2}}}to{{stop-color:{bg_to2}}}}}
  @keyframes densityFlash{{
    0%,85%{{opacity:0}}
    92%{{opacity:.35}}
    100%{{opacity:0}}
  }}
  @keyframes labelFade{{
    0%{{opacity:0}}8%{{opacity:0.6}}35%{{opacity:0.6}}100%{{opacity:0}}
  }}
  .zoom-wrap{{
    animation:zoomOut {dur_s} ease-in-out both;
    transform-origin:center center;
  }}
</style>
"""


# =========================================================================
#  GENERATE
# =========================================================================


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
    snapshot_progress = _clamp_snapshot_progress(snapshot_progress)
    snapshot_mode = snapshot_progress is not None
    progress_time = duration * (snapshot_progress or 0.0)

    metrics = history.get("current_metrics", {})
    stars_events = history.get("stars", [])
    forks_events = history.get("forks", [])
    all_events = sorted(
        [{"date": e.get("date", ""), "kind": "star"} for e in stars_events]
        + [{"date": e.get("date", ""), "kind": "fork"} for e in forks_events],
        key=lambda e: e.get("date", ""),
    )

    # ------------------------------------------------------------------
    # 1. Continuous attractor parameters (replaces SHA-256)
    # ------------------------------------------------------------------
    a, b, c, d, hue_shift = _continuous_attractor_params(metrics)

    grid_sz = 100
    star_vel = metrics.get("star_velocity", {})
    vel_rate = star_vel.get("recent_rate", 0) if isinstance(star_vel, dict) else 0
    vel_boost = int(vel_rate * 100_000)  # up to 1M extra for high velocity
    iters = 2_000_000 + (metrics.get("network_count") or 0) * 30_000 + vel_boost
    iters = min(iters, grid_sz * grid_sz * 200)

    logger.info(
        "Cosmic Genesis: a={a:.3f} b={b:.3f} c={c:.3f} d={d:.3f} "
        "grid={g} iters={i} dark={dm}",
        a=a,
        b=b,
        c=c,
        d=d,
        g=grid_sz,
        i=iters,
        dm=dark_mode,
    )

    # ------------------------------------------------------------------
    # 2. Compute attractor
    # ------------------------------------------------------------------
    density, first_hit = _compute_clifford(a, b, c, d, iters, grid_sz)
    max_density = density.max()
    if max_density <= 0:
        return svg_header(_WIDTH, _HEIGHT) + svg_footer(), 0

    norm = np.log1p(density) / np.log1p(max_density)

    # ------------------------------------------------------------------
    # 3. Calendar-proportional cell reveal
    # ------------------------------------------------------------------
    timeline = _map_to_timeline_chronological(first_hit, all_events, duration)
    max_delay = max(timeline.values()) if timeline else duration * 0.9

    # ------------------------------------------------------------------
    # 4. Build SVG
    # ------------------------------------------------------------------
    dur_s = f"{duration}s"
    pixel_w = round(_WIDTH / grid_sz, 2)
    pixel_h = round(_HEIGHT / grid_sz, 2)

    # Background colours
    if dark_mode:
        bg_from1, bg_to1 = "#05080f", "#12081e"
        bg_from2, bg_to2 = "#080e1a", "#1a0e2e"
        star_colors = [
            oklch(0.90, 0.02, 220),
            oklch(0.85, 0.01, 50),
            "#ffffff",
        ]
        timeline_bg = "rgba(255,255,255,0.08)"
        timeline_fg = "#7c6ef0"
        text_color = "rgba(255,255,255,0.5)"
        milestone_stroke = "rgba(150,130,255,0.7)"
    else:
        bg_from1, bg_to1 = "#f0f2f8", "#e8e0f0"
        bg_from2, bg_to2 = "#e8eef5", "#ddd0e8"
        star_colors = [
            oklch(0.45, 0.02, 260),
            oklch(0.50, 0.01, 50),
            "#444466",
        ]
        timeline_bg = "rgba(0,0,0,0.06)"
        timeline_fg = "#6c5ce7"
        text_color = "rgba(0,0,0,0.35)"
        milestone_stroke = "rgba(100,80,200,0.6)"

    css = _COMMUNITY_CSS.format(
        bg_from1=bg_from1,
        bg_to1=bg_to1,
        bg_from2=bg_from2,
        bg_to2=bg_to2,
        dur_s=dur_s,
    )

    parts: list[str] = []
    parts.append(svg_header(_WIDTH, _HEIGHT))
    parts.append("<defs>\n")

    # Radial gradient for deep-space background
    if snapshot_mode:
        bg_stop_1 = bg_to1 if (snapshot_progress or 0.0) >= 0.65 else bg_from1
        bg_stop_2 = bg_to2 if (snapshot_progress or 0.0) >= 0.65 else bg_from2
        parts.append(
            f'<radialGradient id="bgGrad" cx="50%" cy="50%" r="70%">\n'
            f'  <stop offset="0%" stop-color="{bg_stop_1}"/>\n'
            f'  <stop offset="100%" stop-color="{bg_stop_2}"/>\n'
            f"</radialGradient>\n"
        )
    else:
        parts.append(
            f'<radialGradient id="bgGrad" cx="50%" cy="50%" r="70%">\n'
            f'  <stop offset="0%" stop-color="{bg_from1}">\n'
            f'    <animate attributeName="stop-color" values="{bg_from1};{bg_to1};{bg_from1}" '
            f'dur="{dur_s}" repeatCount="indefinite"/>\n'
            f"  </stop>\n"
            f'  <stop offset="100%" stop-color="{bg_from2}">\n'
            f'    <animate attributeName="stop-color" values="{bg_from2};{bg_to2};{bg_from2}" '
            f'dur="{dur_s}" repeatCount="indefinite"/>\n'
            f"  </stop>\n"
            f"</radialGradient>\n"
        )

    # Glow filter for milestone rings
    parts.append(
        '<filter id="glow"><feGaussianBlur in="SourceGraphic" stdDeviation="3" '
        'result="b"/><feComposite in="SourceGraphic" in2="b" operator="over"/></filter>\n'
    )
    # Nebula blur filter
    parts.append('<filter id="nebBlur"><feGaussianBlur stdDeviation="40"/></filter>\n')
    parts.append("</defs>\n")

    if not snapshot_mode:
        parts.append(css)

    # Background rect
    parts.append(f'<rect width="{_WIDTH}" height="{_HEIGHT}" fill="url(#bgGrad)"/>\n')

    # ---- Layer 1: Three-depth starfield ----
    star_seed = (metrics.get("stars", 0) * 7919 + metrics.get("forks", 0) * 6271) % (
        2**31
    )
    rng = random.Random(star_seed)

    if dark_mode:
        star_layers = [
            (60, 0.3, 0.6, 0.05, 0.15, 4.0, 8.0, [star_colors[2]]),
            (50, 0.6, 1.2, 0.15, 0.35, 2.0, 5.0, [star_colors[2]]),
            (25, 1.2, 2.0, 0.30, 0.60, 1.5, 3.0, star_colors[:2]),
        ]
    else:
        star_layers = [
            (60, 0.4, 0.8, 0.25, 0.45, 4.0, 8.0, [star_colors[2]]),
            (50, 0.8, 1.5, 0.40, 0.60, 2.0, 5.0, [star_colors[2]]),
            (25, 1.5, 2.5, 0.55, 0.80, 1.5, 3.0, star_colors[:2]),
        ]

    parts.append('<g id="starfield">\n')
    for count, r_lo, r_hi, op_lo, op_hi, tw_lo, tw_hi, colors in star_layers:
        for _ in range(count):
            sx = rng.uniform(10, _WIDTH - 10)
            sy = rng.uniform(10, _HEIGHT - 30)
            sr = round(rng.uniform(r_lo, r_hi), 1)
            tw_dur = round(rng.uniform(tw_lo, tw_hi), 1)
            tw_delay = round(rng.uniform(0, duration), 1)
            opacity = round(rng.uniform(op_lo, op_hi), 2)
            color = rng.choice(colors)
            if snapshot_mode:
                parts.append(
                    f'<circle cx="{sx:.0f}" cy="{sy:.0f}" r="{sr}" fill="{color}" '
                    f'opacity="{opacity}"/>\n'
                )
            else:
                parts.append(
                    f'<circle cx="{sx:.0f}" cy="{sy:.0f}" r="{sr}" fill="{color}" '
                    f'opacity="{opacity}" '
                    f'style="animation:twinkle {tw_dur}s ease-in-out {tw_delay}s infinite"/>\n'
                )
    parts.append("</g>\n")

    # ---- Layer 1b: Topic Constellations ----
    topic_clusters = metrics.get("topic_clusters", {})
    top_topics = list(topic_clusters.keys())[:6]
    if top_topics:
        parts.append('<g id="constellations">\n')
        constellation_rng = random.Random((star_seed + 42) % (2**31))

        for ci, topic in enumerate(top_topics):
            # Each constellation = cluster of 3-5 bright stars connected by lines
            n_points = min(5, max(3, topic_clusters.get(topic, 1)))
            base_x = 80 + constellation_rng.uniform(0, _WIDTH - 160)
            base_y = 80 + constellation_rng.uniform(0, _HEIGHT - 200)

            points = [(base_x, base_y)]
            for _ in range(n_points - 1):
                px = points[-1][0] + constellation_rng.uniform(-50, 50)
                py = points[-1][1] + constellation_rng.uniform(-50, 50)
                px = max(30, min(_WIDTH - 30, px))
                py = max(30, min(_HEIGHT - 50, py))
                points.append((px, py))

            # Connecting lines (faint)
            line_color = oklch(0.6 if dark_mode else 0.4, 0.04, 220)
            for i in range(len(points) - 1):
                x1, y1 = points[i]
                x2, y2 = points[i + 1]
                if snapshot_mode:
                    parts.append(
                        f'<line x1="{x1:.0f}" y1="{y1:.0f}" x2="{x2:.0f}" y2="{y2:.0f}" '
                        f'stroke="{line_color}" stroke-width="0.5" opacity="0.3"/>\n'
                    )
                else:
                    fade_dur = round(duration * 0.8 + ci * 2)
                    parts.append(
                        f'<line x1="{x1:.0f}" y1="{y1:.0f}" x2="{x2:.0f}" y2="{y2:.0f}" '
                        f'stroke="{line_color}" stroke-width="0.5" opacity="0">\n'
                        f'  <animate attributeName="opacity" values="0;0.3;0.3;0" '
                        f'dur="{fade_dur}s" begin="{ci * 3}s" repeatCount="indefinite"/>\n'
                        f'</line>\n'
                    )

            # Constellation stars (brighter than background stars)
            for px, py in points:
                star_color = oklch(0.85 if dark_mode else 0.55, 0.03, 200)
                if snapshot_mode:
                    parts.append(
                        f'<circle cx="{px:.0f}" cy="{py:.0f}" r="1.8" '
                        f'fill="{star_color}" opacity="0.6"/>\n'
                    )
                else:
                    parts.append(
                        f'<circle cx="{px:.0f}" cy="{py:.0f}" r="1.8" '
                        f'fill="{star_color}" opacity="0.6" '
                        f'style="animation:twinkle 3s ease-in-out {constellation_rng.uniform(0, 5):.1f}s infinite"/>\n'
                    )

            # Constellation label
            label_x, label_y = points[0]
            label_color = "rgba(255,255,255,0.25)" if dark_mode else "rgba(0,0,0,0.2)"
            name = topic.replace("-", " ").title()
            parts.append(
                f'<text x="{label_x:.0f}" y="{label_y - 8:.0f}" '
                f'font-family="Georgia,serif" font-size="6" font-style="italic" '
                f'fill="{label_color}" text-anchor="middle">{name}</text>\n'
            )

        parts.append('</g>\n')

    # ---- Layer 2: Nebula wisps (language-colored) ----
    langs = metrics.get("languages", {})
    diversity = metrics.get("language_diversity", 1.0) or 1.0
    n_nebula_langs = max(3, min(8, int(diversity * 2)))
    top_langs = sorted(langs.items(), key=lambda x: x[1], reverse=True)[:n_nebula_langs]
    nebula_hues = [LANG_HUES.get(lang, 200) for lang, _ in top_langs]
    if not nebula_hues:
        nebula_hues = [280, 200, 50]

    parts.append('<g id="nebula">\n')
    for i, hue in enumerate(nebula_hues * 3):
        nx = rng.uniform(100, 700)
        ny = rng.uniform(100, 700)
        rx = rng.uniform(120, 250)
        ry = rng.uniform(80, 180)
        drift_x = rng.uniform(-30, 30)
        nebula_color = oklch(0.30 if dark_mode else 0.45, 0.18 if dark_mode else 0.25, hue)
        neb_dur = round(rng.uniform(20, 30))
        neb_opacity = "0.12" if dark_mode else "0.20"
        if snapshot_mode:
            current_x = nx + drift_x * (snapshot_progress or 0.0) * 0.5
            parts.append(
                f'<ellipse cx="{current_x:.0f}" cy="{ny:.0f}" rx="{rx:.0f}" ry="{ry:.0f}" '
                f'fill="{nebula_color}" opacity="{neb_opacity}" filter="url(#nebBlur)"/>\n'
            )
        else:
            parts.append(
                f'<ellipse cx="{nx:.0f}" cy="{ny:.0f}" rx="{rx:.0f}" ry="{ry:.0f}" '
                f'fill="{nebula_color}" opacity="{neb_opacity}" filter="url(#nebBlur)">\n'
                f'  <animate attributeName="cx" values="{nx:.0f};{nx + drift_x:.0f};{nx:.0f}" '
                f'dur="{neb_dur}s" repeatCount="indefinite"/>\n'
                f"</ellipse>\n"
            )
    parts.append("</g>\n")

    # ---- Layer 2b: PR Merge Aurora ----
    recent_prs = metrics.get("recent_merged_prs", [])
    if recent_prs and isinstance(recent_prs, list):
        parts.append('<g id="aurora" opacity="0.15">\n')
        for pi, pr in enumerate(recent_prs[:8]):
            # Aurora band position and color from PR's repo language
            repo_name = pr.get("repo_name", "")
            adds = pr.get("additions", 0) or 0
            dels = pr.get("deletions", 0) or 0
            band_width = min(200, max(30, (adds + dels) * 0.3))

            # Hue from repo name hash for variety
            pr_hue = (hash(repo_name) % 120) + 120  # greens and blues
            aurora_color = oklch(0.45 if dark_mode else 0.55, 0.2, pr_hue)

            # Arc across upper portion of canvas
            cx = _WIDTH / 2
            cy = -100 - pi * 40
            rx = 300 + pi * 30
            ry = 200 + pi * 20

            if snapshot_mode:
                if (snapshot_progress or 0) > pi / max(len(recent_prs), 1):
                    parts.append(
                        f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" '
                        f'fill="none" stroke="{aurora_color}" stroke-width="{band_width:.0f}" '
                        f'opacity="0.12" filter="url(#nebBlur)"/>\n'
                    )
            else:
                shimmer_dur = round(15 + pi * 3, 1)
                parts.append(
                    f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" '
                    f'fill="none" stroke="{aurora_color}" stroke-width="{band_width:.0f}" '
                    f'opacity="0" filter="url(#nebBlur)">\n'
                    f'  <animate attributeName="opacity" values="0;0.12;0.08;0.12;0" '
                    f'dur="{shimmer_dur}s" begin="{pi * 2}s" repeatCount="indefinite"/>\n'
                    f'</ellipse>\n'
                )
        parts.append('</g>\n')

    # ---- Layer 3: Contribution particles ----
    contributions_monthly = history.get("contributions_monthly", {})
    months_sorted = sorted(contributions_monthly.items())
    if months_sorted:
        counts = [v for _, v in months_sorted]
        median_count = sorted(counts)[len(counts) // 2] if counts else 1

        parts.append('<g id="particles">\n')
        for idx, (_month, count) in enumerate(months_sorted):
            if count <= median_count * 0.5:
                continue
            t_frac = idx / max(len(months_sorted) - 1, 1)
            t_sec = t_frac * duration * 0.93

            n_particles = min(4, max(1, count // max(median_count, 1)))
            for _ in range(n_particles):
                angle = rng.uniform(0, 2 * math.pi)
                end_r = rng.uniform(80, 300)
                end_x = _WIDTH / 2 + end_r * math.cos(angle)
                end_y = _HEIGHT / 2 + end_r * math.sin(angle)
                p_dur = round(rng.uniform(3.0, 6.0), 1)
                p_color = oklch(0.7, 0.12, 60) if dark_mode else oklch(0.5, 0.10, 60)
                cycle_dur = round(p_dur + rng.uniform(4.0, 8.0), 1)
                if snapshot_mode:
                    if progress_time < t_sec:
                        continue
                    particle_progress = min(1.0, (progress_time - t_sec) / max(p_dur, 0.1))
                    current_x = (_WIDTH / 2) + (end_x - (_WIDTH / 2)) * particle_progress
                    current_y = (_HEIGHT / 2) + (end_y - (_HEIGHT / 2)) * particle_progress
                    opacity = round(0.7 * max(0.2, 1.0 - (particle_progress * 0.4)), 3)
                    parts.append(
                        f'<circle cx="{current_x:.0f}" cy="{current_y:.0f}" r="1.2" '
                        f'fill="{p_color}" opacity="{opacity}"/>\n'
                    )
                else:
                    parts.append(
                        f'<circle cx="{_WIDTH / 2}" cy="{_HEIGHT / 2}" r="1.2" '
                        f'fill="{p_color}" opacity="0">\n'
                        f'  <animate attributeName="cx" values="{_WIDTH / 2};{end_x:.0f};{_WIDTH / 2}" '
                        f'dur="{cycle_dur}s" begin="{t_sec:.1f}s" repeatCount="indefinite"/>\n'
                        f'  <animate attributeName="cy" values="{_HEIGHT / 2};{end_y:.0f};{_HEIGHT / 2}" '
                        f'dur="{cycle_dur}s" begin="{t_sec:.1f}s" repeatCount="indefinite"/>\n'
                        f'  <animate attributeName="opacity" values="0;0.7;0.7;0" '
                        f'dur="{cycle_dur}s" begin="{t_sec:.1f}s" repeatCount="indefinite"/>\n'
                        f"</circle>\n"
                    )
        parts.append("</g>\n")

    # ---- Layer 3b: Gist Comets ----
    n_gists = metrics.get("public_gists", 0) or 0
    n_comets = min(6, n_gists // 5)
    if n_comets > 0:
        parts.append('<g id="comets">\n')
        for ci in range(n_comets):
            # Comet trajectory: diagonal across the field
            start_x = rng.uniform(0, _WIDTH * 0.3)
            start_y = rng.uniform(0, _HEIGHT * 0.3)
            end_x = rng.uniform(_WIDTH * 0.7, _WIDTH)
            end_y = rng.uniform(_HEIGHT * 0.5, _HEIGHT * 0.9)
            comet_dur = round(rng.uniform(8, 15), 1)
            comet_delay = round(rng.uniform(0, duration * 0.7), 1)

            tail_color = oklch(0.75 if dark_mode else 0.55, 0.12, 55)
            head_color = oklch(0.90 if dark_mode else 0.65, 0.08, 50)

            if snapshot_mode:
                prog = snapshot_progress or 0
                if prog > comet_delay / max(duration, 1):
                    comet_frac = min(1, (prog - comet_delay / max(duration, 1)) * 3)
                    cx = start_x + (end_x - start_x) * comet_frac
                    cy = start_y + (end_y - start_y) * comet_frac
                    parts.append(
                        f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="2" '
                        f'fill="{head_color}" opacity="0.7"/>\n'
                    )
            else:
                parts.append(
                    f'<circle cx="{start_x:.0f}" cy="{start_y:.0f}" r="2" '
                    f'fill="{head_color}" opacity="0">\n'
                    f'  <animate attributeName="cx" values="{start_x:.0f};{end_x:.0f}" '
                    f'dur="{comet_dur}s" begin="{comet_delay}s" repeatCount="indefinite"/>\n'
                    f'  <animate attributeName="cy" values="{start_y:.0f};{end_y:.0f}" '
                    f'dur="{comet_dur}s" begin="{comet_delay}s" repeatCount="indefinite"/>\n'
                    f'  <animate attributeName="opacity" values="0;0.8;0.8;0" '
                    f'dur="{comet_dur}s" begin="{comet_delay}s" repeatCount="indefinite"/>\n'
                    f'</circle>\n'
                )
        parts.append('</g>\n')

    # ---- Layer 4: Zoom wrapper for attractor reveal ----
    if snapshot_mode:
        scale = 1.08 - (0.08 * (snapshot_progress or 0.0))
        parts.append(
            '<g class="zoom-wrap" '
            f'transform="translate({_WIDTH / 2:.0f} {_HEIGHT / 2:.0f}) scale({scale:.3f}) '
            f'translate({-_WIDTH / 2:.0f} {-_HEIGHT / 2:.0f})">\n'
        )
    else:
        parts.append('<g class="zoom-wrap">\n')

    # ---- Layer 4a: Attractor cells as soft circles with jitter ----
    threshold = 0.02
    cell_count = 0
    parts.append('<g id="attractor">\n')
    for row in range(grid_sz):
        for col in range(grid_sz):
            val = float(norm[row, col])
            if val < threshold:
                continue

            delay = timeline.get((row, col), max_delay * 0.9)
            time_frac = delay / max(max_delay, 0.001)
            color = _density_color_oklch(val, time_frac, hue_shift)

            alpha = round(val * (0.96 if dark_mode else 0.95), 3)
            cx = round(
                col * pixel_w + pixel_w / 2 + math.sin(row * 0.7 + col * 1.3) * 1.5, 1
            )
            cy = round(
                row * pixel_h + pixel_h / 2 + math.cos(row * 1.1 + col * 0.9) * 1.5, 1
            )
            r = round(3.5 + val * 3.5, 1)
            breathe_dur = round(5.0 + (row * 0.3 + col * 0.7) % 6.0, 1)
            breathe_delay = round(delay + 1.5, 2)
            if snapshot_mode:
                if progress_time < delay:
                    continue
                reveal_progress = min(1.0, (progress_time - delay) / 1.2)
                parts.append(
                    f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{color}" '
                    f'opacity="{round(alpha * reveal_progress, 3)}"/>\n'
                )
            else:
                parts.append(
                    f'<circle class="cr" cx="{cx}" cy="{cy}" r="{r}" '
                    f'fill="{color}" '
                    f'style="--o:{alpha};--br:{breathe_dur}s;--bd:{breathe_delay}s;'
                    f'animation-delay:{delay:.2f}s"/>\n'
                )
            cell_count += 1

    parts.append("</g>\n")

    # ---- Layer 4b: Shaped density flash (follows attractor density) ----
    if snapshot_mode:
        flash_progress = max(0.0, min(1.0, ((snapshot_progress or 0.0) - 0.85) / 0.15))
        if flash_progress > 0:
            parts.append('<g id="densityFlash">\n')
            for row in range(grid_sz):
                for col in range(grid_sz):
                    val = float(norm[row, col])
                    if val < 0.5:
                        continue
                    flash_alpha = round((val - 0.5) * 2.0 * 0.35 * flash_progress, 3)
                    cx = round(col * pixel_w + pixel_w / 2, 1)
                    cy = round(row * pixel_h + pixel_h / 2, 1)
                    r = round(3.5 + val * 3.5, 1)
                    parts.append(
                        f'<circle cx="{cx}" cy="{cy}" r="{r}" '
                        f'fill="white" opacity="{flash_alpha}"/>\n'
                    )
            parts.append("</g>\n")
    else:
        parts.append(
            f'<g id="densityFlash" style="animation:densityFlash {dur_s} ease-in-out both">\n'
        )
        for row in range(grid_sz):
            for col in range(grid_sz):
                val = float(norm[row, col])
                if val < 0.5:
                    continue
                flash_alpha = round((val - 0.5) * 2.0 * 0.35, 3)
                cx = round(col * pixel_w + pixel_w / 2, 1)
                cy = round(row * pixel_h + pixel_h / 2, 1)
                r = round(3.5 + val * 3.5, 1)
                parts.append(
                    f'<circle cx="{cx}" cy="{cy}" r="{r}" '
                    f'fill="white" opacity="{flash_alpha}"/>\n'
                )
        parts.append("</g>\n")
    parts.append("</g>\n")

    # ---- Layer 5: Milestone pulse rings with poetic labels ----
    milestones = _milestone_indices(all_events)
    if milestones:
        parts.append('<g id="milestones" filter="url(#glow)">\n')
        for val, frac in milestones:
            ms_delay = round(math.sqrt(frac) * duration * 0.93, 2)
            mx = _WIDTH // 2 + rng.randint(-60, 60)
            my = _HEIGHT // 2 + rng.randint(-60, 60)
            pulse_period = round(3.0 + frac * 4.0, 1)
            label = _MILESTONE_LABELS.get(val, "")
            if snapshot_mode:
                if progress_time < ms_delay:
                    continue
                milestone_progress = min(1.0, (progress_time - ms_delay) / 2.5)
                ring_r = round(5 + (24 * milestone_progress), 1)
                ring_opacity = round(0.8 * max(0.35, 1.0 - (milestone_progress * 0.5)), 3)
                parts.append(
                    f'<circle cx="{mx}" cy="{my}" r="{ring_r}" fill="none" '
                    f'stroke="{milestone_stroke}" stroke-width="2" opacity="{ring_opacity}"/>\n'
                )
                if label and milestone_progress >= 0.25:
                    parts.append(
                        f'<text x="{mx}" y="{my + 18}" text-anchor="middle" '
                        f'font-size="8" font-family="monospace" fill="{text_color}" '
                        f'opacity="0.6">{label}</text>\n'
                    )
            else:
                parts.append(
                    f'<circle cx="{mx}" cy="{my}" r="5" fill="none" '
                    f'stroke="{milestone_stroke}" stroke-width="2" opacity="0.8" '
                    f'style="animation:milestonePulse {pulse_period}s ease-out {ms_delay}s infinite"/>\n'
                )
                if label:
                    parts.append(
                        f'<text x="{mx}" y="{my + 18}" text-anchor="middle" '
                        f'font-size="8" font-family="monospace" fill="{text_color}" '
                        f'opacity="0" style="animation:labelFade 4s ease-out {ms_delay}s both">'
                        f"{label}</text>\n"
                    )
        parts.append("</g>\n")

    # ---- Layer 6: Timeline bar at bottom ----
    bar_y = _HEIGHT - 16
    bar_h = 4
    bar_w = _WIDTH - 80
    bar_x = 40
    parts.append(
        f'<rect x="{bar_x}" y="{bar_y}" width="{bar_w}" height="{bar_h}" '
        f'rx="2" fill="{timeline_bg}"/>\n'
    )
    if snapshot_mode:
        parts.append(
            f'<rect x="{bar_x}" y="{bar_y}" width="{round(bar_w * (snapshot_progress or 0.0), 1)}" '
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

    account_created = history.get("account_created")
    all_dates = [e.get("date", "") for e in all_events]
    all_dates = [d for d in all_dates if d]
    if all_dates:
        min_year = int(all_dates[0][:4]) if len(all_dates[0]) >= 4 else 2020
        max_year = int(all_dates[-1][:4]) if len(all_dates[-1]) >= 4 else 2025
    elif account_created and len(account_created) >= 4:
        min_year = int(account_created[:4])
        max_year = 2026
    else:
        min_year, max_year = 2020, 2026

    year_span = max(max_year - min_year, 1)
    for yr in range(min_year, max_year + 1):
        tick_x = round(bar_x + (yr - min_year) / year_span * bar_w, 1)
        parts.append(
            f'<line x1="{tick_x}" y1="{bar_y - 2}" x2="{tick_x}" y2="{bar_y + bar_h + 2}" '
            f'stroke="{text_color}" stroke-width="1"/>\n'
        )
        parts.append(
            f'<text x="{tick_x}" y="{bar_y - 5}" text-anchor="middle" '
            f'font-size="7" font-family="monospace" fill="{text_color}">{yr}</text>\n'
        )

    parts.append(svg_footer())
    return "".join(parts), cell_count


def render_svg(
    history: dict,
    dark_mode: bool = False,
    duration: float = 60.0,
    snapshot_progress: float | None = None,
) -> str:
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
    """Generate the *Cosmic Genesis* community artwork."""
    suffix = "-dark" if dark_mode else ""
    out = Path(output_path or f".github/assets/img/animated-community{suffix}.svg")
    out.parent.mkdir(parents=True, exist_ok=True)
    svg_text, cell_count = _render_svg(history, dark_mode=dark_mode, duration=duration)
    out.write_text(svg_text, encoding="utf-8")

    size_kb = len(svg_text.encode("utf-8")) / 1024
    logger.info(
        "Cosmic Genesis saved: {path} ({cells} cells, {kb:.0f} KB)",
        path=out,
        cells=cell_count,
        kb=size_kb,
    )
    return out
