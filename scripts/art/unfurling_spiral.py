"""
Unfurling Spiral — Animated Activity Art
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Phyllotaxis spiral grows from a single seed; flow-field lines draw
themselves as contributions build.  Language-colored dots with
probabilistic palette, contribution-aware temporal easing, tapered
flow field lines, connecting arcs, heartbeat pulse propagation.

Produces a 30-second looping CSS-animated SVG safe for ``<img>``
embedding in a GitHub README (CSS ``@keyframes`` + SMIL ``<animate>``).

Public API::

    generate(history, dark_mode, output_path, duration) -> Path
"""

from __future__ import annotations

import math
import random
from pathlib import Path

from ..utils import get_logger
from .shared import (
    LANG_HUES,
    WorldState,
    compute_world_state,
    flow_field_lines,
    oklch,
    phyllotaxis_points,
    svg_footer,
    svg_header,
    volumetric_glow_filter,
)

logger = get_logger(module=__name__)

# ---------------------------------------------------------------------------
# Canvas constants
# ---------------------------------------------------------------------------
_WIDTH = 800
_HEIGHT = 800


# ---------------------------------------------------------------------------
# Continuous parameter mapping (replaces SHA-256)
# ---------------------------------------------------------------------------


def _continuous_activity_params(metrics: dict) -> dict:
    """Continuous parameter derivation for activity art."""

    def _norm(val: float, hi: float) -> float:
        return min(1.0, math.log1p(val) / math.log1p(hi))

    repos = metrics.get("public_repos", 0) or 0
    followers = metrics.get("followers", 0) or 0
    orgs = metrics.get("orgs_count", 0) or 0
    contribs = metrics.get("contributions_last_year", 0) or 0
    commits = metrics.get("total_commits", 0) or 0
    following = metrics.get("following", 0) or 0

    return {
        "octaves": max(1, min(4, int(1 + _norm(followers, 1000) * 3))),
        "flow_mag": 1.0 + min(1.5, orgs * 0.15),
        "flow_freq": 0.003 + _norm(following, 500) * 0.007,
        "line_count": max(15, min(120, int(15 + _norm(commits, 50000) * 105))),
        "bg_intensity": _norm(contribs, 2000),
        "flow_seed": (repos * 7919 + followers * 6271 + commits) % (2**31),
        "flow_hue_base": int(200 + _norm(repos, 200) * 60) % 360,
    }


# ---------------------------------------------------------------------------
# Contribution-aware temporal easing
# ---------------------------------------------------------------------------


def _contribution_aware_easing(
    index: int,
    total: int,
    duration: float,
    contributions_monthly: dict,
) -> float:
    """Map dot appearance to contribution intensity over time."""
    if total <= 1:
        return 0.0

    months = sorted(contributions_monthly.items())
    if not months:
        return _fallback_easing(index, total, duration)

    counts = [v for _, v in months]
    cumulative: list[int] = []
    running = 0
    for c in counts:
        running += c
        cumulative.append(running)
    total_contribs = cumulative[-1] or 1

    target = (index / (total - 1)) * total_contribs

    for mi, cum in enumerate(cumulative):
        if cum >= target:
            prev = cumulative[mi - 1] if mi > 0 else 0
            within = (target - prev) / max(counts[mi], 1)
            month_frac = (mi + within) / len(months)
            return round(month_frac * duration * 0.95, 3)

    return round(duration * 0.95, 3)


def _fallback_easing(index: int, total: int, duration: float) -> float:
    """Generic temporal easing when no contribution data available."""
    if total <= 1:
        return 0.0
    frac = index / (total - 1)
    if frac < 0.1:
        t = (frac / 0.1) ** 0.5 * 0.17
    elif frac < 0.7:
        mid = (frac - 0.1) / 0.6
        t = 0.17 + mid * 0.5
    else:
        end = (frac - 0.7) / 0.3
        t = 0.67 + (1.0 - (1.0 - end) ** 2) * 0.33
    return round(t * duration * 0.95, 3)


# ---------------------------------------------------------------------------
# Language palette builder
# ---------------------------------------------------------------------------


def _build_language_palette(
    metrics: dict,
    n_points: int,
) -> list[tuple[str, float, float]]:
    """Build (color_hex, chroma, size_mult) list for each dot from language distribution.

    Returns list of (oklch_hex_color, chroma_value, size_multiplier) tuples.
    The *size_multiplier* scales each spiral dot so that dominant languages
    produce visibly larger points (0.7 -- 2.2 range).
    """
    lang_bytes = metrics.get("languages", {})
    if not lang_bytes:
        # Fallback: neutral palette
        return [(oklch(0.55, 0.04, 200), 0.04, 1.0)] * n_points

    total_bytes = sum(lang_bytes.values()) or 1
    # Sort by proportion descending
    sorted_langs = sorted(lang_bytes.items(), key=lambda x: -x[1])

    # Build distribution -- each language gets proportional slots
    # Size multiplier creates a visible "pie-chart spiral" encoding:
    #   dominant language → 1.5x radius, minor languages → 0.6x radius
    max_proportion = sorted_langs[0][1] / total_bytes if sorted_langs else 0.5
    lang_slots: list[tuple[str, float]] = []
    for lang, byte_count in sorted_langs:
        n = max(1, round(byte_count / total_bytes * n_points))
        proportion = byte_count / total_bytes
        # Scale from 0.6 (minor) to 1.5 (dominant) based on proportion
        size_mult = 0.6 + (proportion / max(max_proportion, 0.01)) * 0.9
        lang_slots.extend([(lang, size_mult)] * n)
    # Pad or trim to n_points
    while len(lang_slots) < n_points:
        lang_slots.append((sorted_langs[0][0], 1.0))
    lang_slots = lang_slots[:n_points]

    result: list[tuple[str, float, float]] = []
    for lang, size_mult in lang_slots:
        hue = LANG_HUES.get(lang, 200)
        # Top language gets high chroma, others moderate
        is_top = lang == sorted_langs[0][0]
        C = 0.16 if is_top else 0.10
        L = 0.55
        result.append((oklch(L, C, hue), C, size_mult))

    return result


# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------

_ACTIVITY_CSS = """\
<style>
  @keyframes dotAppear{{
    0%{{r:0;opacity:0;fill:white}}
    8%{{opacity:1;fill:white}}
    25%{{opacity:.95}}
    50%{{opacity:.92}}
    100%{{opacity:.90}}
  }}
  @keyframes dotShimmer{{
    0%,100%{{opacity:.90}}
    50%{{opacity:.65}}
  }}
  @keyframes pulse{{
    0%,100%{{opacity:.7;r:{pulse_r1}}}
    50%{{opacity:1;r:{pulse_r2}}}
  }}
  @keyframes flowDraw{{
    0%{{stroke-dashoffset:var(--len,500)}}
    100%{{stroke-dashoffset:0}}
  }}
  @keyframes flowPulse{{
    0%,100%{{opacity:0.65}}
    50%{{opacity:0.45}}
  }}
  @keyframes glowIn{{
    0%{{opacity:0}}
    100%{{opacity:1}}
  }}
  @keyframes arcFill{{
    0%{{stroke-dashoffset:{arc_len}}}
    100%{{stroke-dashoffset:0}}
  }}
  @keyframes bgRadial{{
    0%{{r:0%;opacity:0}}
    100%{{r:70%;opacity:.25}}
  }}
  .fd{{fill:none;animation:flowDraw var(--dur,4s) ease-in-out var(--del,0s) both}}
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
) -> tuple[str, int, int]:
    snapshot_progress = _clamp_snapshot_progress(snapshot_progress)
    snapshot_mode = snapshot_progress is not None
    progress_time = duration * (snapshot_progress or 0.0)

    metrics = history.get("current_metrics", {})
    repos = history.get("repos", [])
    contributions_monthly = history.get("contributions_monthly", {})

    # ------------------------------------------------------------------
    # 1. Continuous parameters (replaces SHA-256)
    # ------------------------------------------------------------------
    params = _continuous_activity_params(metrics)
    octaves = params["octaves"]
    flow_mag = params["flow_mag"]
    flow_freq = params["flow_freq"]
    line_count = params["line_count"]
    bg_intensity = params["bg_intensity"]
    flow_seed = params["flow_seed"]
    flow_hue_base = params["flow_hue_base"]

    n_points = max(30, len(repos) or metrics.get("public_repos") or 50)
    n_points = min(n_points, 250)

    logger.info(
        "Unfurling Spiral: n_points={n} lines={l} octaves={o} dark={dm}",
        n=n_points,
        l=line_count,
        o=octaves,
        dm=dark_mode,
    )

    # ------------------------------------------------------------------
    # 2. Compute geometry
    # ------------------------------------------------------------------
    max_radius = math.sqrt(n_points) * 12.0
    canvas_radius = min(_WIDTH, _HEIGHT) * 0.40
    scale = canvas_radius / max(max_radius, 1.0) * 12.0
    pts = phyllotaxis_points(n_points, _WIDTH / 2, _HEIGHT / 2, scale=scale)

    # Star velocity -> emission intensity multiplier
    star_vel = history.get("star_velocity") or metrics.get("star_velocity", {})
    vel_rate = star_vel.get("recent_rate", 0) if isinstance(star_vel, dict) else 0
    emission_mult = 1.0 + min(1.0, vel_rate * 0.15)  # up to 2x

    lines = flow_field_lines(
        _WIDTH,
        _HEIGHT,
        num_lines=int(line_count * emission_mult),
        freq=flow_freq,
        octaves=octaves,
        step_size=4.0 * flow_mag,
        seed=flow_seed,
    )

    delays = [
        _contribution_aware_easing(i, n_points, duration, contributions_monthly)
        for i in range(n_points)
    ]

    palette = _build_language_palette(metrics, n_points)

    # ------------------------------------------------------------------
    # 3. Build SVG
    # ------------------------------------------------------------------
    if dark_mode:
        bg_color = "#0a0d14"
        bg_radial_color = "#1a1540"
        text_color = "rgba(255,255,255,0.4)"
        arc_bg_color = "rgba(255,255,255,0.08)"
        arc_fg_color = "#7c6ef0"
        ripple_color = "rgba(180,160,255,0.5)"
        conn_opacity = 0.22
    else:
        bg_color = "#f5f5fa"
        bg_radial_color = "#c8b8e0"
        text_color = "rgba(0,0,0,0.3)"
        arc_bg_color = "rgba(0,0,0,0.10)"
        arc_fg_color = "#6c5ce7"
        ripple_color = "rgba(100,80,200,0.55)"
        conn_opacity = 0.18

    arc_cx = _WIDTH // 2
    arc_cy = _HEIGHT - 30
    arc_r = _WIDTH // 2 - 50
    arc_len = round(math.pi * arc_r, 1)

    base_r = max(4.0, min(7.0, 160.0 / math.sqrt(max(n_points, 1))))
    pulse_r1 = round(base_r + 1, 1)
    pulse_r2 = round(base_r + 3, 1)

    css = _ACTIVITY_CSS.format(
        pulse_r1=pulse_r1,
        pulse_r2=pulse_r2,
        arc_len=arc_len,
    )

    parts: list[str] = []
    parts.append(svg_header(_WIDTH, _HEIGHT))

    parts.append("<defs>\n")
    parts.append(
        '<filter id="spiralGlow" x="-50%" y="-50%" width="200%" height="200%">'
        '<feGaussianBlur in="SourceGraphic" stdDeviation="3" result="b"/>'
        '<feComposite in="SourceGraphic" in2="b" operator="over"/>'
        "</filter>\n"
    )
    avg_monthly = (
        sum(contributions_monthly.values()) / max(len(contributions_monthly), 1)
        if contributions_monthly
        else 50
    )
    pulse_period = round(max(3.0, 8.0 - min(5.0, avg_monthly / 100)), 1)
    if snapshot_mode:
        radial_extent = max(5.0, 75.0 * (snapshot_progress or 0.0))
        radial_opacity = round(0.25 + ((snapshot_progress or 0.0) * 0.15), 3)
        parts.append(
            f'<radialGradient id="bgRad" cx="50%" cy="50%" r="{radial_extent:.1f}%">\n'
            f'  <stop offset="0%" stop-color="{bg_radial_color}" stop-opacity="{radial_opacity}"/>\n'
            f'  <stop offset="100%" stop-color="{bg_color}" stop-opacity="0"/>\n'
            f"</radialGradient>\n"
        )
    else:
        parts.append(
            f'<radialGradient id="bgRad" cx="50%" cy="50%" r="0%">\n'
            f'  <stop offset="0%" stop-color="{bg_radial_color}" stop-opacity="0.35">\n'
            f'    <animate attributeName="stop-opacity" values="0.35;0.50;0.35" '
            f'dur="{pulse_period}s" repeatCount="indefinite"/>\n'
            f"  </stop>\n"
            f'  <stop offset="100%" stop-color="{bg_color}" stop-opacity="0"/>\n'
            f'  <animate attributeName="r" from="0%" to="75%" dur="{duration}s" fill="freeze"/>\n'
            f"</radialGradient>\n"
        )
    parts.append("</defs>\n")

    if not snapshot_mode:
        parts.append(css)

    parts.append(f'<rect width="{_WIDTH}" height="{_HEIGHT}" fill="{bg_color}"/>\n')
    parts.append(f'<rect width="{_WIDTH}" height="{_HEIGHT}" fill="url(#bgRad)"/>\n')

    # ---- Layer 1: Flow-field lines (tapered, language-colored) ----
    center_x, center_y = _WIDTH / 2, _HEIGHT / 2

    lang_bytes = metrics.get("languages", {})
    top_lang_hues = [
        LANG_HUES.get(lang, 200)
        for lang, _ in sorted(lang_bytes.items(), key=lambda x: -x[1])[:3]
    ]
    if not top_lang_hues:
        top_lang_hues = [flow_hue_base]

    if snapshot_mode:
        parts.append('<g id="flowField" opacity="0.65">\n')
    else:
        parts.append(
            '<g id="flowField" opacity="0.65"'
            ' style="animation:flowPulse 8s ease-in-out 5s infinite">\n'
        )
    for li, trail in enumerate(lines):
        if len(trail) < 2:
            continue
        path_d = f"M{trail[0][0]:.1f},{trail[0][1]:.1f}"
        for px, py in trail[1:]:
            path_d += f" L{px:.1f},{py:.1f}"

        trail_len = sum(
            math.sqrt(
                (trail[ti][0] - trail[ti - 1][0]) ** 2
                + (trail[ti][1] - trail[ti - 1][1]) ** 2
            )
            for ti in range(1, len(trail))
        )
        trail_len_rounded = round(trail_len, 0)

        avg_dist = sum(
            math.sqrt((p[0] - center_x) ** 2 + (p[1] - center_y) ** 2) for p in trail
        ) / len(trail)
        dist_frac = min(1.0, avg_dist / (canvas_radius * 1.2))
        alpha = round(0.30 + 0.40 * dist_frac * bg_intensity, 2)

        fl_hue = top_lang_hues[li % len(top_lang_hues)]
        fl_color = oklch(0.50 if dark_mode else 0.42, 0.08, fl_hue)

        fl_delay = round((li / max(len(lines), 1)) * duration * 0.6, 2)
        fl_dur = round(duration * 0.35 + (li % 5) * 0.5, 1)

        sw_start = 2.8
        sw_end = 0.8
        sw_avg = round((sw_start + sw_end) / 2, 1)

        if snapshot_mode:
            if progress_time < fl_delay:
                continue
            line_progress = min(1.0, (progress_time - fl_delay) / max(fl_dur, 0.1))
            dash_offset = round(trail_len_rounded * (1.0 - line_progress), 1)
            parts.append(
                f'<path d="{path_d}" stroke="{fl_color}" stroke-width="{sw_avg}" '
                f'opacity="{alpha}" stroke-linecap="round" '
                f'stroke-dasharray="{trail_len_rounded}" stroke-dashoffset="{dash_offset}" fill="none"/>\n'
            )
        else:
            parts.append(
                f'<path class="fd" d="{path_d}" stroke="{fl_color}" stroke-width="{sw_avg}" '
                f'opacity="{alpha}" stroke-linecap="round" '
                f'stroke-dasharray="{trail_len_rounded}" '
                f'style="--len:{trail_len_rounded};--dur:{fl_dur}s;--del:{fl_delay}s"/>\n'
            )
    parts.append("</g>\n")

    # ---- Layer 2: Variable ripple rings (SMIL per ring) ----
    parts.append('<g id="ripples">\n')
    for i in range(n_points):
        px, py = pts[i]
        d = delays[i]
        ripple_max_r = round(30 + 30 * (1 - i / max(n_points - 1, 1)), 0)
        ripple_dur = round(1.0 + 1.0 * (1 - i / max(n_points - 1, 1)), 1)
        ripple_cycle = round(ripple_dur + 4.0 + (i % 5) * 1.5, 1)
        if snapshot_mode:
            if progress_time < d:
                continue
            ripple_progress = min(1.0, (progress_time - d) / max(ripple_dur, 0.1))
            opacity = round(0.55 * max(0.0, 1.0 - ripple_progress), 3)
            parts.append(
                f'<circle cx="{px:.1f}" cy="{py:.1f}" r="{ripple_max_r * ripple_progress:.1f}" fill="none" '
                f'stroke="{ripple_color}" stroke-width="1.8" opacity="{opacity}"/>\n'
            )
        else:
            parts.append(
                f'<circle cx="{px:.1f}" cy="{py:.1f}" r="0" fill="none" '
                f'stroke="{ripple_color}" stroke-width="1.8" opacity="0">\n'
                f'  <animate attributeName="r" values="0;{ripple_max_r};0" '
                f'dur="{ripple_cycle}s" begin="{d:.2f}s" repeatCount="indefinite"/>\n'
                f'  <animate attributeName="opacity" values="0;0.55;0" '
                f'dur="{ripple_cycle}s" begin="{d:.2f}s" repeatCount="indefinite"/>\n'
                f"</circle>\n"
            )
    parts.append("</g>\n")

    # ---- Layer 3: Connecting arcs between sequential dots ----
    max_connections = min(150, n_points - 1)
    parts.append(f'<g id="connections" opacity="{conn_opacity}">\n')
    for i in range(max_connections):
        x1, y1 = pts[i]
        x2, y2 = pts[i + 1]
        length = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
        if length < 0.5:
            continue
        d = delays[i]
        color, _, _ = palette[i]
        arc_cycle = round(2.5 + (i % 4) * 0.8, 1)
        if snapshot_mode:
            if progress_time < d:
                continue
            connection_progress = min(1.0, (progress_time - d) / max(arc_cycle, 0.1))
            dash_offset = round(length * (1.0 - connection_progress), 1)
            parts.append(
                f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                f'stroke="{color}" stroke-width="1.4" stroke-dasharray="{length:.0f}" '
                f'stroke-dashoffset="{dash_offset}"/>\n'
            )
        else:
            parts.append(
                f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                f'stroke="{color}" stroke-width="1.4" '
                f'stroke-dasharray="{length:.0f}" stroke-dashoffset="{length:.0f}">\n'
                f'  <animate attributeName="stroke-dashoffset" values="{length:.0f};0;{length:.0f}" '
                f'dur="{arc_cycle}s" begin="{d:.2f}s" repeatCount="indefinite"/>\n'
                f"</line>\n"
            )
    parts.append("</g>\n")

    # ---- Layer 4: Phyllotaxis dots (language-colored, byte-proportional sizes) ----
    glow_threshold = int(n_points * 0.65)
    parts.append('<g id="spiral">\n')
    glow_parts: list[str] = []

    for i, (px, py) in enumerate(pts):
        color, _, size_mult = palette[i]
        dot_r = round((base_r + math.log1p(i) * 0.7) * size_mult, 2)
        d = delays[i]
        appear_dur = round(max(0.8, 1.5 - i * 0.003), 2)

        shimmer_dur = round(4.0 + (i * 0.7) % 5.0, 1)
        shimmer_delay = round(d + appear_dur + 0.5, 2)
        if snapshot_mode:
            if progress_time < d:
                continue
            dot_progress = min(1.0, (progress_time - d) / max(appear_dur, 0.1))
            elem = (
                f'<circle cx="{px:.1f}" cy="{py:.1f}" r="{dot_r * (0.4 + (0.6 * dot_progress)):.2f}" '
                f'fill="{color}" opacity="{dot_progress:.3f}"/>\n'
            )
        else:
            elem = (
                f'<circle cx="{px:.1f}" cy="{py:.1f}" r="{dot_r}" fill="{color}" '
                f'opacity="0" '
                f'style="animation:dotAppear {appear_dur}s ease-out {d:.2f}s both,'
                f'dotShimmer {shimmer_dur}s ease-in-out {shimmer_delay}s infinite"/>\n'
            )

        if i >= glow_threshold:
            glow_parts.append(elem)
        else:
            parts.append(elem)

    parts.append("</g>\n")

    if glow_parts:
        parts.append('<g id="spiralGlow" filter="url(#spiralGlow)">\n')
        parts.extend(glow_parts)
        parts.append("</g>\n")

    # ── Topic connection arcs with labels ────────────────────────
    topic_clusters = metrics.get("topic_clusters", {})
    top_topics = (
        list(topic_clusters.keys())[:5] if isinstance(topic_clusters, dict) else []
    )

    if top_topics:
        # Use enriched repos from metrics (they carry topics), fall back to timeline repos
        enriched_repos = metrics.get("repos", repos)
        # Map repos to their spiral point indices
        repo_indices: dict[str, int] = {}
        for ri, repo in enumerate(enriched_repos[:n_points]):
            rname = repo.get("name", "") if isinstance(repo, dict) else ""
            if rname:
                repo_indices[rname] = ri

        parts.append('<g id="topic-arcs">\n')
        for ti_topic, topic in enumerate(top_topics):
            # Derive arc color from the topic's primary language hue
            cluster_info = topic_clusters.get(topic, {})
            primary_lang = (
                cluster_info.get("primary_language", "")
                if isinstance(cluster_info, dict)
                else ""
            )
            topic_hue = LANG_HUES.get(primary_lang, 200 + ti_topic * 30)
            arc_color = oklch(0.60 if dark_mode else 0.45, 0.10, topic_hue)

            # Find all repos with this topic
            matching: list[int] = []
            for repo in enriched_repos[:n_points]:
                if not isinstance(repo, dict):
                    continue
                if topic in (repo.get("topics") or []):
                    idx = repo_indices.get(repo.get("name", ""))
                    if idx is not None and idx < len(pts):
                        matching.append(idx)

            if len(matching) >= 2:
                # Collect midpoints for label placement
                mid_xs: list[float] = []
                mid_ys: list[float] = []

                # Draw curved connections between matching points
                for mi in range(len(matching) - 1):
                    p1 = pts[matching[mi]]
                    p2 = pts[matching[mi + 1]]
                    # Quadratic bezier with control point offset toward center
                    mx = (p1[0] + p2[0]) / 2
                    my = (p1[1] + p2[1]) / 2
                    # Pull control point toward center for nice arc
                    cx_pt = mx + (_WIDTH / 2 - mx) * 0.3
                    cy_pt = my + (_HEIGHT / 2 - my) * 0.3
                    mid_xs.append(mx)
                    mid_ys.append(my)
                    parts.append(
                        f'<path d="M{p1[0]:.0f},{p1[1]:.0f} Q{cx_pt:.0f},{cy_pt:.0f} {p2[0]:.0f},{p2[1]:.0f}" '
                        f'fill="none" stroke="{arc_color}" stroke-width="0.4" opacity="0.12"/>\n'
                    )

                # Label at the centroid of arc midpoints
                if mid_xs:
                    label_x = sum(mid_xs) / len(mid_xs)
                    label_y = sum(mid_ys) / len(mid_ys)
                    label_color = oklch(0.70 if dark_mode else 0.35, 0.06, topic_hue)
                    parts.append(
                        f'<text x="{label_x:.0f}" y="{label_y:.0f}" '
                        f'text-anchor="middle" font-size="6" '
                        f'font-family="monospace" fill="{label_color}" '
                        f'opacity="0.4">{topic}</text>\n'
                    )
        parts.append("</g>\n")

    # ── Streak pulse rings (golden glow for active, grey dashed for broken) ──
    streaks = history.get("contribution_streaks") or metrics.get(
        "contribution_streaks", {}
    )
    streak_months = (
        streaks.get("current_streak_months", 0) if isinstance(streaks, dict) else 0
    )
    streak_active = (
        streaks.get("streak_active", False) if isinstance(streaks, dict) else False
    )

    if streak_months > 0:
        n_rings = min(12, streak_months)
        # Golden stroke for active, grey dashed for broken
        ring_color = "#d4af37" if streak_active else "#888888"
        dash_attr = '' if streak_active else ' stroke-dasharray="3,5"'
        # Add volumetric glow filter for golden rings
        if streak_active:
            parts.append(f"<defs>{volumetric_glow_filter('streakGlow', radius=1.5)}</defs>\n")
        parts.append(
            f'<g id="streak-rings"'
            f'{" filter=" + chr(34) + "url(#streakGlow)" + chr(34) if streak_active else ""}>\n'
        )
        for ri in range(n_rings):
            radius = 30 + ri * 25
            # Opacity decreasing outward: 0.3 → 0.05
            opacity = round(0.3 - ri * (0.25 / max(n_rings - 1, 1)), 3)
            if opacity < 0.02:
                break

            if snapshot_mode:
                if (snapshot_progress or 0) > 0.3:
                    parts.append(
                        f'<circle cx="{_WIDTH / 2}" cy="{_HEIGHT / 2}" r="{radius}" '
                        f'fill="none" stroke="{ring_color}" stroke-width="0.8" '
                        f'opacity="{opacity:.3f}"{dash_attr}/>\n'
                    )
            else:
                pulse_dur = round(4 + ri * 0.5, 1)
                delay = round(ri * 1.2, 1)
                parts.append(
                    f'<circle cx="{_WIDTH / 2}" cy="{_HEIGHT / 2}" r="{radius}" '
                    f'fill="none" stroke="{ring_color}" stroke-width="0.8" opacity="0"{dash_attr}>\n'
                    f'  <animate attributeName="opacity" values="0;{opacity:.3f};{opacity:.3f};0" '
                    f'dur="{pulse_dur}s" begin="{delay}s" repeatCount="indefinite"/>\n'
                    f'  <animate attributeName="r" values="{radius};{radius + 5};{radius}" '
                    f'dur="{pulse_dur}s" begin="{delay}s" repeatCount="indefinite"/>\n'
                    f"</circle>\n"
                )
        parts.append("</g>\n")

    # ── DNA Helix Overlay (Code Review Cross-Pollination) ──────
    review_count = metrics.get("pr_review_count", 0) or 0
    if review_count > 0 and len(pts) > 5:
        helix_color = "#8080c0"
        helix_opacity = round(0.08 + min(0.04, review_count * 0.0005), 3)
        # Two intertwined spiral paths offset by 180 degrees
        # Use the same phyllotaxis center but with offset angles
        helix_n = min(len(pts), 80)
        helix_scale = scale * 0.95  # slightly smaller than main spiral
        golden_angle = math.pi * (3.0 - math.sqrt(5.0))

        strand_a: list[tuple[float, float]] = []
        strand_b: list[tuple[float, float]] = []
        for hi in range(helix_n):
            r_h = math.sqrt(hi) * 12.0 * helix_scale / max(math.sqrt(n_points) * 12.0, 1.0)
            theta = hi * golden_angle
            # Strand A: original angle
            strand_a.append((
                _WIDTH / 2 + r_h * math.cos(theta),
                _HEIGHT / 2 + r_h * math.sin(theta),
            ))
            # Strand B: offset by pi (180 degrees)
            strand_b.append((
                _WIDTH / 2 + r_h * math.cos(theta + math.pi),
                _HEIGHT / 2 + r_h * math.sin(theta + math.pi),
            ))

        parts.append(f'<g id="dna-helix" opacity="{helix_opacity}">\n')

        # Draw strand A
        if len(strand_a) >= 2:
            path_a = f"M{strand_a[0][0]:.1f},{strand_a[0][1]:.1f}"
            for sx, sy in strand_a[1:]:
                path_a += f" L{sx:.1f},{sy:.1f}"
            parts.append(
                f'<path d="{path_a}" fill="none" stroke="{helix_color}" '
                f'stroke-width="0.3" stroke-linecap="round"/>\n'
            )

        # Draw strand B
        if len(strand_b) >= 2:
            path_b = f"M{strand_b[0][0]:.1f},{strand_b[0][1]:.1f}"
            for sx, sy in strand_b[1:]:
                path_b += f" L{sx:.1f},{sy:.1f}"
            parts.append(
                f'<path d="{path_b}" fill="none" stroke="{helix_color}" '
                f'stroke-width="0.3" stroke-linecap="round"/>\n'
            )

        # Draw connecting rungs — density proportional to review count
        rung_interval = max(2, 20 - min(15, review_count // 5))
        rung_color = oklch(0.60 if dark_mode else 0.45, 0.08, 260)
        for hi in range(0, min(len(strand_a), len(strand_b)), rung_interval):
            parts.append(
                f'<line x1="{strand_a[hi][0]:.1f}" y1="{strand_a[hi][1]:.1f}" '
                f'x2="{strand_b[hi][0]:.1f}" y2="{strand_b[hi][1]:.1f}" '
                f'stroke="{rung_color}" stroke-width="0.2" opacity="0.12"/>\n'
            )
        parts.append("</g>\n")

    # ── Fibonacci Golden Ratio Overlay ────────────────────────
    # Subtle mathematical beauty: golden spiral curve + golden rectangles
    phi = (1 + math.sqrt(5)) / 2  # golden ratio ≈ 1.618
    gold_color = "#d4af37"

    parts.append('<g id="golden-overlay">\n')

    # Golden spiral: r = phi^(theta / (pi/2)), scaled to canvas
    golden_pts: list[tuple[float, float]] = []
    max_theta = 6 * math.pi  # ~3 full turns
    spiral_scale = canvas_radius / (phi ** (max_theta / (math.pi / 2)))
    for step in range(200):
        theta = (step / 199) * max_theta
        r_golden = spiral_scale * (phi ** (theta / (math.pi / 2)))
        gx = _WIDTH / 2 + r_golden * math.cos(theta)
        gy = _HEIGHT / 2 - r_golden * math.sin(theta)
        if 0 <= gx <= _WIDTH and 0 <= gy <= _HEIGHT:
            golden_pts.append((gx, gy))

    if len(golden_pts) >= 2:
        gpath = f"M{golden_pts[0][0]:.1f},{golden_pts[0][1]:.1f}"
        for gx, gy in golden_pts[1:]:
            gpath += f" L{gx:.1f},{gy:.1f}"
        parts.append(
            f'<path d="{gpath}" fill="none" stroke="{gold_color}" '
            f'stroke-width="0.5" opacity="0.06" stroke-linecap="round"/>\n'
        )

    # Golden rectangles: 3 nested subdivisions from center
    rect_w = canvas_radius * 1.6
    rect_h = rect_w / phi
    for gi in range(3):
        shrink = phi ** gi
        rw = rect_w / shrink
        rh = rw / phi
        rx = _WIDTH / 2 - rw / 2
        ry = _HEIGHT / 2 - rh / 2
        parts.append(
            f'<rect x="{rx:.1f}" y="{ry:.1f}" width="{rw:.1f}" height="{rh:.1f}" '
            f'fill="none" stroke="{gold_color}" stroke-width="0.3" opacity="0.04"/>\n'
        )

    parts.append("</g>\n")

    # ---- Layer 5: Heartbeat pulse with outward propagation ----
    if pts:
        fx, fy = pts[0]
        first_delay = delays[0] + 1.5
        pulse_color, _, _ = palette[0]
        if snapshot_mode:
            if progress_time >= delays[0]:
                pulse_progress = min(1.0, max(0.0, (progress_time - delays[0]) / 1.5))
                pulse_radius = pulse_r1 + ((pulse_r2 - pulse_r1) * pulse_progress)
                parts.append(
                    f'<circle cx="{fx:.1f}" cy="{fy:.1f}" r="{pulse_radius:.2f}" fill="{pulse_color}" '
                    f'opacity="0.8"/>\n'
                )
        else:
            parts.append(
                f'<circle cx="{fx:.1f}" cy="{fy:.1f}" r="{pulse_r1}" fill="{pulse_color}" '
                f'opacity="0" '
                f'style="animation:dotAppear 1.5s ease-out {delays[0]:.2f}s both, '
                f'pulse 2.5s cubic-bezier(0.22,0.61,0.36,1) {first_delay:.1f}s infinite"/>\n'
            )

    # ---- Layer 6: Timeline arc ----
    arc_path = (
        f"M{arc_cx - arc_r},{arc_cy} A{arc_r},{arc_r} 0 0 1 {arc_cx + arc_r},{arc_cy}"
    )
    parts.append(
        f'<path d="{arc_path}" fill="none" stroke="{arc_bg_color}" stroke-width="3"/>\n'
    )
    if snapshot_mode:
        dash_offset = round(arc_len * (1.0 - (snapshot_progress or 0.0)), 1)
        parts.append(
            f'<path d="{arc_path}" fill="none" stroke="{arc_fg_color}" stroke-width="3" '
            f'stroke-dasharray="{arc_len}" stroke-dashoffset="{dash_offset}" opacity="0.7"/>\n'
        )
    else:
        parts.append(
            f'<path d="{arc_path}" fill="none" stroke="{arc_fg_color}" stroke-width="3" '
            f'stroke-dasharray="{arc_len}" stroke-dashoffset="{arc_len}" opacity="0.7">\n'
            f'  <animate attributeName="stroke-dashoffset" from="{arc_len}" to="0" '
            f'dur="{duration}s" fill="freeze"/>\n'
            f"</path>\n"
        )

    repo_dates = [r.get("date", "") for r in repos if r.get("date")]
    account_created = history.get("account_created")
    if repo_dates:
        min_year = int(repo_dates[0][:4]) if len(repo_dates[0]) >= 4 else 2020
        max_year = int(repo_dates[-1][:4]) if len(repo_dates[-1]) >= 4 else 2025
    elif account_created and len(account_created) >= 4:
        min_year = int(account_created[:4])
        max_year = 2026
    else:
        min_year, max_year = 2020, 2026

    year_span = max(max_year - min_year, 1)
    for yr in range(min_year, max_year + 1):
        frac = (yr - min_year) / year_span
        angle = math.pi * (1 - frac)
        tx = arc_cx + arc_r * math.cos(angle)
        ty = arc_cy - arc_r * math.sin(angle)
        parts.append(
            f'<circle cx="{tx:.1f}" cy="{ty:.1f}" r="2" fill="{arc_fg_color}" opacity="0.5"/>\n'
        )
        label_y = ty + 12
        parts.append(
            f'<text x="{tx:.1f}" y="{label_y:.1f}" text-anchor="middle" '
            f'font-size="7" font-family="monospace" fill="{text_color}">{yr}</text>\n'
        )

    parts.append(svg_footer())
    return "".join(parts), n_points, len(lines)


def render_svg(
    history: dict,
    dark_mode: bool = False,
    duration: float = 60.0,
    snapshot_progress: float | None = None,
) -> str:
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
    """Generate the *Unfurling Spiral* activity artwork."""
    suffix = "-dark" if dark_mode else ""
    out = Path(output_path or f".github/assets/img/animated-activity{suffix}.svg")
    out.parent.mkdir(parents=True, exist_ok=True)
    svg_text, n_points, line_count = _render_svg(
        history,
        dark_mode=dark_mode,
        duration=duration,
    )
    out.write_text(svg_text, encoding="utf-8")

    size_kb = len(svg_text.encode("utf-8")) / 1024
    logger.info(
        "Unfurling Spiral saved: {path} ({pts} dots, {lines} flow lines, {kb:.0f} KB)",
        path=out,
        pts=n_points,
        lines=line_count,
        kb=size_kb,
    )
    return out
