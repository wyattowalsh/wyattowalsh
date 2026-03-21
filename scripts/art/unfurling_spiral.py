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
from pathlib import Path

from ..utils import get_logger
from .shared import (
    LANG_HUES,
    flow_field_lines,
    oklch,
    phyllotaxis_points,
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
) -> list[tuple[str, float]]:
    """Build (color_hex, chroma) list for each dot from language distribution.

    Returns list of (oklch_hex_color, chroma_value) tuples.
    """
    lang_bytes = metrics.get("languages", {})
    if not lang_bytes:
        # Fallback: neutral palette
        return [(oklch(0.55, 0.04, 200), 0.04)] * n_points

    total_bytes = sum(lang_bytes.values()) or 1
    # Sort by proportion descending
    sorted_langs = sorted(lang_bytes.items(), key=lambda x: -x[1])

    # Build distribution
    lang_slots: list[str] = []
    for lang, byte_count in sorted_langs:
        n = max(1, round(byte_count / total_bytes * n_points))
        lang_slots.extend([lang] * n)
    # Pad or trim to n_points
    while len(lang_slots) < n_points:
        lang_slots.append(sorted_langs[0][0])
    lang_slots = lang_slots[:n_points]

    result: list[tuple[str, float]] = []
    for lang in lang_slots:
        hue = LANG_HUES.get(lang, 200)
        # Top language gets high chroma, others moderate
        is_top = lang == sorted_langs[0][0]
        C = 0.16 if is_top else 0.10
        L = 0.55
        result.append((oklch(L, C, hue), C))

    return result


# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------

_ACTIVITY_CSS = """\
<style>
  @keyframes dotAppear{{
    0%{{r:0;opacity:0;fill:white}}
    8%{{opacity:1;fill:white}}
    25%{{opacity:.9}}
    50%{{opacity:.88}}
    100%{{opacity:.85}}
  }}
  @keyframes pulse{{
    0%,100%{{opacity:.7;r:{pulse_r1}}}
    50%{{opacity:1;r:{pulse_r2}}}
  }}
  @keyframes flowDraw{{
    0%{{stroke-dashoffset:var(--len,500)}}
    100%{{stroke-dashoffset:0}}
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


def generate(
    history: dict,
    dark_mode: bool = False,
    output_path: Path | None = None,
    duration: float = 30.0,
) -> Path:
    """Generate the *Unfurling Spiral* activity artwork."""
    metrics = history.get("current_metrics", {})
    repos = history.get("repos", [])
    contributions_monthly = history.get("contributions_monthly", {})

    suffix = "-dark" if dark_mode else ""
    out = Path(output_path or f".github/assets/img/animated-activity{suffix}.svg")
    out.parent.mkdir(parents=True, exist_ok=True)

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

    n_points = max(10, len(repos) or metrics.get("public_repos") or 50)
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

    lines = flow_field_lines(
        _WIDTH,
        _HEIGHT,
        num_lines=line_count,
        freq=flow_freq,
        octaves=octaves,
        step_size=4.0 * flow_mag,
        seed=flow_seed,
    )

    # Contribution-aware timing
    delays = [
        _contribution_aware_easing(i, n_points, duration, contributions_monthly)
        for i in range(n_points)
    ]

    # Language palette
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
        conn_opacity = 0.15
    else:
        bg_color = "#f5f5fa"
        bg_radial_color = "#d8d0e8"
        text_color = "rgba(0,0,0,0.3)"
        arc_bg_color = "rgba(0,0,0,0.06)"
        arc_fg_color = "#6c5ce7"
        ripple_color = "rgba(100,80,200,0.45)"
        conn_opacity = 0.10

    # Timeline arc geometry
    arc_cx = _WIDTH // 2
    arc_cy = _HEIGHT - 30
    arc_r = _WIDTH // 2 - 50
    arc_len = round(math.pi * arc_r, 1)

    # Dot sizes
    base_r = max(2.0, min(5.0, 120.0 / math.sqrt(max(n_points, 1))))
    pulse_r1 = round(base_r + 1, 1)
    pulse_r2 = round(base_r + 3, 1)

    css = _ACTIVITY_CSS.format(
        pulse_r1=pulse_r1,
        pulse_r2=pulse_r2,
        arc_len=arc_len,
    )

    parts: list[str] = []
    parts.append(svg_header(_WIDTH, _HEIGHT))

    # Defs
    parts.append("<defs>\n")
    parts.append(
        '<filter id="spiralGlow" x="-50%" y="-50%" width="200%" height="200%">'
        '<feGaussianBlur in="SourceGraphic" stdDeviation="3" result="b"/>'
        '<feComposite in="SourceGraphic" in2="b" operator="over"/>'
        "</filter>\n"
    )
    # Breathing radial gradient
    avg_monthly = (
        sum(contributions_monthly.values()) / max(len(contributions_monthly), 1)
        if contributions_monthly
        else 50
    )
    pulse_period = round(max(3.0, 8.0 - min(5.0, avg_monthly / 100)), 1)
    parts.append(
        f'<radialGradient id="bgRad" cx="50%" cy="50%" r="0%">\n'
        f'  <stop offset="0%" stop-color="{bg_radial_color}" stop-opacity="0.25">\n'
        f'    <animate attributeName="stop-opacity" values="0.25;0.40;0.25" '
        f'dur="{pulse_period}s" repeatCount="indefinite"/>\n'
        f"  </stop>\n"
        f'  <stop offset="100%" stop-color="{bg_color}" stop-opacity="0"/>\n'
        f'  <animate attributeName="r" from="0%" to="75%" dur="{duration}s" fill="freeze"/>\n'
        f"</radialGradient>\n"
    )
    parts.append("</defs>\n")

    # CSS
    parts.append(css)

    # Background
    parts.append(f'<rect width="{_WIDTH}" height="{_HEIGHT}" fill="{bg_color}"/>\n')
    parts.append(f'<rect width="{_WIDTH}" height="{_HEIGHT}" fill="url(#bgRad)"/>\n')

    # ---- Layer 1: Flow-field lines (tapered, language-colored) ----
    center_x, center_y = _WIDTH / 2, _HEIGHT / 2

    # Build nebula hues from top languages
    lang_bytes = metrics.get("languages", {})
    top_lang_hues = [
        LANG_HUES.get(lang, 200)
        for lang, _ in sorted(lang_bytes.items(), key=lambda x: -x[1])[:3]
    ]
    if not top_lang_hues:
        top_lang_hues = [flow_hue_base]

    parts.append('<g id="flowField" opacity="0.40">\n')
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

        # Radial opacity modulation
        avg_dist = sum(
            math.sqrt((p[0] - center_x) ** 2 + (p[1] - center_y) ** 2) for p in trail
        ) / len(trail)
        dist_frac = min(1.0, avg_dist / (canvas_radius * 1.2))
        alpha = round(0.20 + 0.35 * dist_frac * bg_intensity, 2)

        # Language-spectrum hue
        fl_hue = top_lang_hues[li % len(top_lang_hues)]
        fl_color = oklch(0.50 if dark_mode else 0.42, 0.08, fl_hue)

        fl_delay = round((li / max(len(lines), 1)) * duration * 0.6, 2)
        fl_dur = round(duration * 0.35 + (li % 5) * 0.5, 1)

        # Tapered stroke using gradient along path
        # SVG workaround: use stroke-width that's slightly larger
        sw_start = 1.5
        sw_end = 0.3
        sw_avg = round((sw_start + sw_end) / 2, 1)

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
        # Older repos get bigger ripples
        ripple_max_r = round(20 + 30 * (1 - i / max(n_points - 1, 1)), 0)
        ripple_dur = round(1.0 + 1.0 * (1 - i / max(n_points - 1, 1)), 1)
        parts.append(
            f'<circle cx="{px:.1f}" cy="{py:.1f}" r="0" fill="none" '
            f'stroke="{ripple_color}" stroke-width="1.8" opacity="0">\n'
            f'  <animate attributeName="r" from="0" to="{ripple_max_r}" '
            f'dur="{ripple_dur}s" begin="{d:.2f}s" fill="freeze"/>\n'
            f'  <animate attributeName="opacity" values="0.55;0" '
            f'dur="{ripple_dur}s" begin="{d:.2f}s" fill="freeze"/>\n'
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
        color, _ = palette[i]
        parts.append(
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="{color}" stroke-width="0.5" '
            f'stroke-dasharray="{length:.0f}" stroke-dashoffset="{length:.0f}">\n'
            f'  <animate attributeName="stroke-dashoffset" from="{length:.0f}" to="0" '
            f'dur="0.8s" begin="{d:.2f}s" fill="freeze"/>\n'
            f"</line>\n"
        )
    parts.append("</g>\n")

    # ---- Layer 4: Phyllotaxis dots (language-colored) ----
    glow_threshold = int(n_points * 0.65)
    parts.append('<g id="spiral">\n')
    glow_parts: list[str] = []

    for i, (px, py) in enumerate(pts):
        dot_r = round(base_r + math.log1p(i) * 0.5, 2)
        color, _ = palette[i]
        d = delays[i]
        appear_dur = round(max(0.8, 1.5 - i * 0.003), 2)

        elem = (
            f'<circle cx="{px:.1f}" cy="{py:.1f}" r="{dot_r}" fill="{color}" '
            f'opacity="0" '
            f'style="animation:dotAppear {appear_dur}s ease-out {d:.2f}s both"/>\n'
        )

        if i >= glow_threshold:
            glow_parts.append(elem)
        else:
            parts.append(elem)

    parts.append("</g>\n")

    # Glow group for outer dots
    if glow_parts:
        parts.append('<g id="spiralGlow" filter="url(#spiralGlow)">\n')
        parts.extend(glow_parts)
        parts.append("</g>\n")

    # ---- Layer 5: Heartbeat pulse with outward propagation ----
    if pts:
        fx, fy = pts[0]
        first_delay = delays[0] + 1.5
        pulse_color, _ = palette[0]
        # First dot: cardiac rhythm pulse
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
    parts.append(
        f'<path d="{arc_path}" fill="none" stroke="{arc_fg_color}" stroke-width="3" '
        f'stroke-dasharray="{arc_len}" stroke-dashoffset="{arc_len}" opacity="0.7">\n'
        f'  <animate attributeName="stroke-dashoffset" from="{arc_len}" to="0" '
        f'dur="{duration}s" fill="freeze"/>\n'
        f"</path>\n"
    )

    # Year marks on arc
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

    svg_text = "".join(parts)
    out.write_text(svg_text, encoding="utf-8")

    size_kb = len(svg_text.encode("utf-8")) / 1024
    logger.info(
        "Unfurling Spiral saved: {path} ({pts} dots, {lines} flow lines, {kb:.0f} KB)",
        path=out,
        pts=n_points,
        lines=len(lines),
        kb=size_kb,
    )
    return out
