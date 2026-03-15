"""
animated_art.py
~~~~~~~~~~~~~~~
CSS-animated SVG generators that tell the story of a GitHub profile's
growth over time.  Two artworks are produced:

- **Cosmic Genesis** (community art) -- Clifford attractor density grid
  revealed progressively as stars/forks accumulate.  Deep-space starfield
  backdrop, milestone ring-bursts, zooming viewport, warming color ramp.

- **Unfurling Spiral** (activity art) -- Phyllotaxis spiral grows from a
  single seed; flow-field lines draw themselves as contributions build.
  Dramatic dot entrances with ripple rings, heartbeat pulse on the first
  repo, glow buildup on outer nodes.

Both produce 30-second looping CSS-animated SVGs safe for embedding via
``<img>`` in a GitHub README (no JavaScript, no SMIL -- pure CSS
``@keyframes`` inside ``<style>``).

Public API (consumed by downstream orchestration agents)::

    generate_animated_community_art(history, dark_mode, output_path, duration) -> Path
    generate_animated_activity_art(history, dark_mode, output_path, duration)  -> Path

CLI::

    uv run python -m scripts.animated_art --history path.json --type all --duration 30
"""

from __future__ import annotations

import argparse
import colorsys
import hashlib
import json
import math
import random
from pathlib import Path
from typing import Optional

import numpy as np

from .art.shared import phyllotaxis_points, flow_field_lines
from .utils import get_logger

logger = get_logger(module=__name__)

# ---------------------------------------------------------------------------
# Canvas constants
# ---------------------------------------------------------------------------
_WIDTH = 800
_HEIGHT = 800

# ---------------------------------------------------------------------------
# Shared seed helpers (mirrors scripts/generative.py)
# ---------------------------------------------------------------------------

def _seed_hash(seed_str: str) -> str:
    """SHA-256 hex digest of a seed string."""
    return hashlib.sha256(seed_str.encode()).hexdigest()


def _hex_slice(h: str, start: int, end: int) -> float:
    """Extract a normalised float [0, 1) from hex digest slice."""
    return int(h[start:end], 16) / (16 ** (end - start))


# ---------------------------------------------------------------------------
# Clifford attractor math (inlined to avoid coupling with banner rendering)
# ---------------------------------------------------------------------------

def _compute_clifford(
    a: float,
    b: float,
    c: float,
    d: float,
    iterations: int,
    grid_size: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Run the Clifford attractor and return (density, first_hit) grids.

    The Clifford system::

        x_{n+1} = sin(a * y_n) + c * cos(a * x_n)
        y_{n+1} = sin(b * x_n) + d * cos(b * y_n)

    Returns
    -------
    density : ndarray (grid_size, grid_size)
        Hit counts per cell, raw (unnormalised).
    first_hit : ndarray (grid_size, grid_size) dtype int64
        Iteration index when cell was first populated; -1 if never hit.
    """
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
# Timeline / easing helpers
# ---------------------------------------------------------------------------

def _map_to_timeline(
    first_hit: np.ndarray,
    events: list[dict],
    total_duration: float,
) -> dict[tuple[int, int], float]:
    """Map grid-cell first-hit iterations to animation-delay seconds.

    Uses **rank-based (percentile) normalization** so that cells are evenly
    distributed across the animation timeline regardless of the iteration
    distribution's skew.  The Clifford attractor fills 90%+ of its
    structure in early iterations; without rank normalisation, nearly all
    cells would cluster at time ≈ 0 and the planned colour evolution
    (indigo → teal → orange → white-gold) would be invisible.
    """
    reveal_duration = total_duration * 0.93  # leave 7 % for final flash

    # Collect all populated cells
    hits: list[tuple[int, int, int]] = []  # (iteration, row, col)
    rows, cols = first_hit.shape
    for r in range(rows):
        for c in range(cols):
            it = int(first_hit[r, c])
            if it >= 0:
                hits.append((it, r, c))

    if not hits:
        return {}

    # Sort by iteration → assign rank-based fraction (0..1)
    hits.sort(key=lambda x: x[0])
    n = len(hits)
    mapping: dict[tuple[int, int], float] = {}
    for rank, (_it, r, c) in enumerate(hits):
        frac = rank / max(n - 1, 1)  # percentile: 0..1
        # Slight front-loading (exponent < 1) keeps early reveal snappy
        t = frac ** 0.8 * reveal_duration
        mapping[(r, c)] = round(t, 3)

    return mapping


def _temporal_easing(index: int, total: int, duration: float) -> float:
    """Non-linear mapping for spiral-dot appearance times.

    - First 5 repos: slow reveal (first ~17 % of duration)
    - Middle repos: accelerating
    - Final repos: decelerate for dramatic finish
    """
    if total <= 1:
        return 0.0
    frac = index / (total - 1)  # 0..1

    # Piecewise cubic bezier approximation
    if frac < 0.1:
        # Slow start
        t = (frac / 0.1) ** 0.5 * 0.17
    elif frac < 0.7:
        # Accelerating middle
        mid = (frac - 0.1) / 0.6
        t = 0.17 + mid * 0.5
    else:
        # Decelerating finish
        end = (frac - 0.7) / 0.3
        t = 0.67 + (1.0 - (1.0 - end) ** 2) * 0.33

    return round(t * duration * 0.95, 3)  # 95 % of duration for reveals


def _milestone_indices(events: list) -> list[tuple[int, float]]:
    """Return (milestone_value, fractional_position) pairs.

    Milestones at 10, 25, 50, 100, 250, 500, 1000, 2500, 5000, ...
    """
    thresholds = [10, 25, 50, 100, 250, 500, 1000, 2500, 5000, 10000]
    n = len(events)
    results: list[tuple[int, float]] = []
    for th in thresholds:
        if th <= n:
            results.append((th, th / max(n, 1)))
    return results


# ---------------------------------------------------------------------------
# Color utilities
# ---------------------------------------------------------------------------

def _hsl_to_hex(h: float, s: float, lightness: float) -> str:
    """Convert HSL (all 0..1) to hex colour string."""
    r, g, b = colorsys.hls_to_rgb(h, lightness, s)
    return "#{:02x}{:02x}{:02x}".format(int(r * 255), int(g * 255), int(b * 255))


def _lerp_color(hex1: str, hex2: str, t: float) -> str:
    """Linearly interpolate between two hex colours."""
    r1, g1, b1 = int(hex1[1:3], 16), int(hex1[3:5], 16), int(hex1[5:7], 16)
    r2, g2, b2 = int(hex2[1:3], 16), int(hex2[3:5], 16), int(hex2[5:7], 16)
    r = int(r1 + (r2 - r1) * t)
    g = int(g1 + (g2 - g1) * t)
    b = int(b1 + (b2 - b1) * t)
    return "#{:02x}{:02x}{:02x}".format(
        max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b))
    )


def _density_color(val: float, hue_shift: float, time_frac: float) -> str:
    """Map normalised density + temporal fraction to a colour.

    Color evolution over the 30-second reveal:
      0.0-0.33  deep indigo / purple  (early community)
      0.33-0.67 teal / cyan           (growing)
      0.67-0.93 orange / amber        (thriving)
      0.93-1.0  final density flash to bright white-gold
    """
    if time_frac < 0.33:
        # Deep indigo -> purple
        base_hue = (0.72 + hue_shift * 0.1) % 1.0
        sat = 0.75 + 0.2 * val
        lit = 0.12 + 0.22 * val
    elif time_frac < 0.67:
        # Teal -> cyan
        local_t = (time_frac - 0.33) / 0.34
        base_hue = (0.72 - local_t * 0.22 + hue_shift * 0.1) % 1.0
        sat = 0.7 + 0.25 * val
        lit = 0.18 + 0.28 * val
    elif time_frac < 0.93:
        # Orange -> amber
        local_t = (time_frac - 0.67) / 0.26
        base_hue = (0.08 + hue_shift * 0.05 + local_t * 0.02) % 1.0
        sat = 0.85 + 0.1 * val
        lit = 0.30 + 0.30 * val
    else:
        # Final flash -- bright white-gold
        base_hue = (0.10 + hue_shift * 0.03) % 1.0
        sat = 0.6 * (1.0 - val * 0.5)
        lit = 0.55 + 0.40 * val

    return _hsl_to_hex(base_hue, sat, lit)


# ---------------------------------------------------------------------------
# XML / SVG helpers (hand-written to keep filesize minimal)
# ---------------------------------------------------------------------------

def _xml_escape(s: str) -> str:
    """Escape XML special characters."""
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def _svg_header(width: int, height: int) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}">\n'
    )


def _svg_footer() -> str:
    return "</svg>\n"


# =========================================================================
#  1. COSMIC GENESIS -- Animated Community Art
# =========================================================================

_COMMUNITY_CSS = """\
<style>
  .cr{animation:cellReveal 0.8s ease-out both}
  @keyframes cellReveal{from{opacity:0}to{opacity:var(--o,0.8)}}
  @keyframes twinkle{0%,100%{opacity:.15}50%{opacity:.85}}
  @keyframes milestonePulse{
    0%{r:5;opacity:.8;stroke-width:2}
    100%{r:50;opacity:0;stroke-width:.3}
  }
  @keyframes zoomOut{
    0%{transform:scale(1.45) translate(-15.5%,-15.5%)}
    100%{transform:scale(1) translate(0,0)}
  }
  @keyframes timelineFill{from{width:0}to{width:100%}}
  @keyframes bgWarm1{from{stop-color:BGFROM}to{stop-color:BGTO}}
  @keyframes bgWarm2{from{stop-color:BG2FROM}to{stop-color:BG2TO}}
  @keyframes densityFlash{
    0%,90%{opacity:0}
    95%{opacity:.35}
    100%{opacity:0}
  }
  .zoom-wrap{
    animation:zoomOut DURMS ease-in-out both;
    transform-origin:center center;
  }
</style>
"""


def generate_animated_community_art(
    history: dict,
    dark_mode: bool = False,
    output_path: Optional[Path] = None,
    duration: float = 30.0,
) -> Path:
    """Generate the *Cosmic Genesis* community artwork.

    Parameters
    ----------
    history : dict
        Decoded ``history.json`` with keys ``stars``, ``forks``, ``repos``,
        ``contributions_monthly``, ``current_metrics``, ``account_created``.
    dark_mode : bool
        Produce a dark-background variant when *True*.
    output_path : Path | None
        Explicit output path; auto-derived if *None*.
    duration : float
        Total animation duration in seconds (default 30).

    Returns
    -------
    Path
        The path to the written SVG file.
    """
    metrics = history.get("current_metrics", {})
    stars_events = history.get("stars", [])
    forks_events = history.get("forks", [])
    all_events = sorted(
        [{"date": e.get("date", ""), "kind": "star"} for e in stars_events]
        + [{"date": e.get("date", ""), "kind": "fork"} for e in forks_events],
        key=lambda e: e.get("date", ""),
    )

    suffix = "-dark" if dark_mode else ""
    out = Path(output_path or f".github/assets/img/animated-community{suffix}.svg")
    out.parent.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # 1. Derive Clifford parameters (same seed derivation as generative.py)
    # ------------------------------------------------------------------
    seed_str = (
        f"{metrics.get('stars', 0)}-{metrics.get('forks', 0)}"
        f"-{metrics.get('watchers', 0)}-{metrics.get('open_issues_count', 0)}"
        f"-{metrics.get('network_count', 0)}"
        f"-{metrics.get('latest_stargazer', '')}"
        f"-{metrics.get('latest_fork_owner', '')}"
    )
    h = _seed_hash(seed_str)

    a = 0.8 + _hex_slice(h, 0, 4) * 1.2
    b = 0.8 + _hex_slice(h, 4, 8) * 1.2
    c = -2.0 + _hex_slice(h, 8, 12) * 4.0
    d = -2.0 + _hex_slice(h, 12, 16) * 4.0
    hue_shift = float((metrics.get("forks", 0) * 37 + int(h[16:20], 16) % 60) % 360) / 360.0

    grid_sz = 100  # balance between detail and file-size
    iters = 800_000 + (metrics.get("network_count") or 0) * 30_000
    iters = min(iters, grid_sz * grid_sz * 50)

    logger.info(
        "Animated community art: a={a:.3f} b={b:.3f} c={c:.3f} d={d:.3f} "
        "grid={g} iters={i} dark={dm}",
        a=a, b=b, c=c, d=d, g=grid_sz, i=iters, dm=dark_mode,
    )

    # ------------------------------------------------------------------
    # 2. Compute attractor
    # ------------------------------------------------------------------
    density, first_hit = _compute_clifford(a, b, c, d, iters, grid_sz)
    max_density = density.max()
    if max_density <= 0:
        logger.warning("Clifford attractor produced empty grid -- writing blank SVG")
        out.write_text(_svg_header(_WIDTH, _HEIGHT) + _svg_footer(), encoding="utf-8")
        return out

    norm = np.log1p(density) / np.log1p(max_density)

    # ------------------------------------------------------------------
    # 3. Map cells to animation delays
    # ------------------------------------------------------------------
    timeline = _map_to_timeline(first_hit, all_events, duration)
    max_delay = max(timeline.values()) if timeline else duration * 0.9

    # ------------------------------------------------------------------
    # 4. Build SVG string
    # ------------------------------------------------------------------
    dur_s = f"{duration}s"
    pixel_w = round(_WIDTH / grid_sz, 2)
    pixel_h = round(_HEIGHT / grid_sz, 2)

    # Background colours
    if dark_mode:
        bg_from1, bg_to1 = "#05080f", "#12081e"
        bg_from2, bg_to2 = "#080e1a", "#1a0e2e"
        star_color = "#ffffff"
        timeline_bg = "rgba(255,255,255,0.08)"
        timeline_fg = "#7c6ef0"
        text_color = "rgba(255,255,255,0.5)"
        milestone_stroke = "rgba(150,130,255,0.7)"
    else:
        bg_from1, bg_to1 = "#f0f2f8", "#e8e0f0"
        bg_from2, bg_to2 = "#e8eef5", "#ddd0e8"
        star_color = "#444466"
        timeline_bg = "rgba(0,0,0,0.06)"
        timeline_fg = "#6c5ce7"
        text_color = "rgba(0,0,0,0.35)"
        milestone_stroke = "rgba(100,80,200,0.6)"

    css = _COMMUNITY_CSS.replace("BGFROM", bg_from1).replace("BGTO", bg_to1)
    css = css.replace("BG2FROM", bg_from2).replace("BG2TO", bg_to2)
    css = css.replace("DURMS", dur_s)

    parts: list[str] = []
    parts.append(_svg_header(_WIDTH, _HEIGHT))
    parts.append("<defs>\n")

    # Radial gradient for deep-space background
    parts.append(
        f'<radialGradient id="bgGrad" cx="50%" cy="50%" r="70%">\n'
        f'  <stop offset="0%" stop-color="{bg_from1}">\n'
        f'    <animate attributeName="stop-color" values="{bg_from1};{bg_to1};{bg_from1}" '
        f'dur="{dur_s}" repeatCount="indefinite"/>\n'
        f'  </stop>\n'
        f'  <stop offset="100%" stop-color="{bg_from2}">\n'
        f'    <animate attributeName="stop-color" values="{bg_from2};{bg_to2};{bg_from2}" '
        f'dur="{dur_s}" repeatCount="indefinite"/>\n'
        f'  </stop>\n'
        f'</radialGradient>\n'
    )

    # Glow filter for milestone rings
    parts.append(
        '<filter id="glow"><feGaussianBlur in="SourceGraphic" stdDeviation="3" '
        'result="b"/><feComposite in="SourceGraphic" in2="b" operator="over"/></filter>\n'
    )
    parts.append("</defs>\n")

    # CSS
    parts.append(css)

    # Background rect
    parts.append(f'<rect width="{_WIDTH}" height="{_HEIGHT}" fill="url(#bgGrad)"/>\n')

    # ---- Layer 1: Star-field twinkle ----
    rng = random.Random(int(h[28:36], 16))
    n_stars = 90
    parts.append('<g id="starfield">\n')
    for i in range(n_stars):
        sx = rng.uniform(10, _WIDTH - 10)
        sy = rng.uniform(10, _HEIGHT - 30)
        sr = round(rng.uniform(0.4, 1.4), 1)
        twinkle_dur = round(rng.uniform(2.0, 6.0), 1)
        twinkle_delay = round(rng.uniform(0, duration), 1)
        opacity_base = round(rng.uniform(0.1, 0.5), 2)
        parts.append(
            f'<circle cx="{sx:.0f}" cy="{sy:.0f}" r="{sr}" fill="{star_color}" '
            f'opacity="{opacity_base}" '
            f'style="animation:twinkle {twinkle_dur}s ease-in-out {twinkle_delay}s infinite"/>\n'
        )
    parts.append("</g>\n")

    # ---- Layer 2: Zoom wrapper for attractor reveal ----
    parts.append('<g class="zoom-wrap">\n')

    # ---- Layer 2a: Attractor cells with staggered reveal ----
    threshold = 0.03
    cell_count = 0
    parts.append('<g id="attractor">\n')
    for row in range(grid_sz):
        for col in range(grid_sz):
            val = float(norm[row, col])
            if val < threshold:
                continue

            delay = timeline.get((row, col), max_delay * 0.9)
            time_frac = delay / max(max_delay, 0.001)
            color = _density_color(val, hue_shift, time_frac)

            alpha = round(val * (0.92 if dark_mode else 0.82), 3)
            x = round(col * pixel_w, 1)
            y = round(row * pixel_h, 1)

            parts.append(
                f'<rect class="cr" x="{x}" y="{y}" '
                f'width="{pixel_w + 0.5:.1f}" height="{pixel_h + 0.5:.1f}" '
                f'fill="{color}" '
                f'style="--o:{alpha};animation-delay:{delay:.2f}s"/>\n'
            )
            cell_count += 1

    parts.append("</g>\n")

    # ---- Layer 2b: Density flash overlay (at ~28-30s) ----
    parts.append(
        f'<rect width="{_WIDTH}" height="{_HEIGHT}" fill="white" opacity="0" '
        f'style="animation:densityFlash {dur_s} ease-in-out both"/>\n'
    )
    parts.append("</g>\n")  # close zoom-wrap

    # ---- Layer 3: Milestone pulse rings ----
    milestones = _milestone_indices(all_events)
    if milestones:
        parts.append('<g id="milestones" filter="url(#glow)">\n')
        for val, frac in milestones:
            ms_delay = round(math.sqrt(frac) * duration * 0.93, 2)
            # Position ring at centre with slight random offset
            mx = _WIDTH // 2 + rng.randint(-40, 40)
            my = _HEIGHT // 2 + rng.randint(-40, 40)
            parts.append(
                f'<circle cx="{mx}" cy="{my}" r="5" fill="none" '
                f'stroke="{milestone_stroke}" stroke-width="2" opacity="0.8" '
                f'style="animation:milestonePulse 2s ease-out {ms_delay}s both"/>\n'
            )
        parts.append("</g>\n")

    # ---- Layer 4: Timeline bar at bottom ----
    bar_y = _HEIGHT - 16
    bar_h = 4
    bar_w = _WIDTH - 80
    bar_x = 40
    parts.append(f'<rect x="{bar_x}" y="{bar_y}" width="{bar_w}" height="{bar_h}" '
                 f'rx="2" fill="{timeline_bg}"/>\n')
    parts.append(
        f'<rect x="{bar_x}" y="{bar_y}" width="0" height="{bar_h}" rx="2" '
        f'fill="{timeline_fg}" opacity="0.8">\n'
        f'  <animate attributeName="width" from="0" to="{bar_w}" '
        f'dur="{dur_s}" fill="freeze"/>\n'
        f'</rect>\n'
    )

    # Year tick marks on timeline
    history.get("repos", [])
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

    parts.append(_svg_footer())

    svg_text = "".join(parts)
    out.write_text(svg_text, encoding="utf-8")

    size_kb = len(svg_text.encode("utf-8")) / 1024
    logger.info(
        "Animated community art saved: {path} ({cells} cells, {kb:.0f} KB)",
        path=out, cells=cell_count, kb=size_kb,
    )
    return out


# =========================================================================
#  2. UNFURLING SPIRAL -- Animated Activity Art
# =========================================================================

_ACTIVITY_CSS = """\
<style>
  @keyframes dotAppear{
    0%{r:0;opacity:0;fill:white}
    8%{opacity:1;fill:white}
    25%{opacity:.9}
    50%{opacity:.88}
    100%{opacity:.85}
  }
  @keyframes pulse{
    0%,100%{opacity:.7;r:PULSE_R1}
    50%{opacity:1;r:PULSE_R2}
  }
  @keyframes ripple{
    0%{r:0;opacity:.55;stroke-width:1.8}
    100%{r:35;opacity:0;stroke-width:.3}
  }
  @keyframes flowDraw{
    0%{stroke-dashoffset:var(--len,500)}
    100%{stroke-dashoffset:0}
  }
  @keyframes glowIn{
    0%{opacity:0}
    100%{opacity:1}
  }
  @keyframes arcFill{
    0%{stroke-dashoffset:ARC_LEN}
    100%{stroke-dashoffset:0}
  }
  @keyframes bgRadial{
    0%{r:0%;opacity:0}
    100%{r:70%;opacity:.25}
  }
  .fd{fill:none;animation:flowDraw var(--dur,4s) ease-in-out var(--del,0s) both}
</style>
"""


def generate_animated_activity_art(
    history: dict,
    dark_mode: bool = False,
    output_path: Optional[Path] = None,
    duration: float = 30.0,
) -> Path:
    """Generate the *Unfurling Spiral* activity artwork.

    Parameters
    ----------
    history : dict
        Decoded ``history.json``.
    dark_mode : bool
        Produce a dark-background variant when *True*.
    output_path : Path | None
        Explicit output path; auto-derived if *None*.
    duration : float
        Total animation duration in seconds (default 30).

    Returns
    -------
    Path
        The path to the written SVG file.
    """
    metrics = history.get("current_metrics", {})
    repos = history.get("repos", [])

    suffix = "-dark" if dark_mode else ""
    out = Path(output_path or f".github/assets/img/animated-activity{suffix}.svg")
    out.parent.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # 1. Derive parameters (mirrors generative.py activity art)
    # ------------------------------------------------------------------
    seed_str = (
        f"{metrics.get('public_repos') or 0}-{metrics.get('followers') or 0}"
        f"-{metrics.get('orgs_count') or 0}-{metrics.get('contributions_last_year') or 0}"
        f"-{metrics.get('total_commits') or 0}-{metrics.get('following') or 0}"
    )
    h = _seed_hash(seed_str)

    n_points = max(10, len(repos) or metrics.get("public_repos") or 50)
    # Cap at 250 to keep SVG size reasonable
    n_points = min(n_points, 250)
    octaves = max(1, min(4, (metrics.get("followers") or 0) // 20))
    flow_mag = 1.0 + (metrics.get("orgs_count") or 0) * 0.15
    flow_freq = 0.003 + _hex_slice(h, 0, 4) * 0.007
    line_count = min(120, max(15, (metrics.get("total_commits") or 0) // 500))
    bg_intensity = min(1.0, (metrics.get("contributions_last_year") or 0) / 2000.0)
    flow_seed = int(h[20:28], 16) % (2**31)

    logger.info(
        "Animated activity art: n_points={n} lines={l} octaves={o} dark={dm}",
        n=n_points, l=line_count, o=octaves, dm=dark_mode,
    )

    # ------------------------------------------------------------------
    # 2. Compute geometry
    # ------------------------------------------------------------------
    # Phyllotaxis spiral
    max_radius = math.sqrt(n_points) * 12.0
    canvas_radius = min(_WIDTH, _HEIGHT) * 0.40
    scale = canvas_radius / max(max_radius, 1.0) * 12.0
    pts = phyllotaxis_points(n_points, _WIDTH / 2, _HEIGHT / 2, scale=scale)

    # Flow field
    lines = flow_field_lines(
        _WIDTH, _HEIGHT,
        num_lines=line_count,
        freq=flow_freq,
        octaves=octaves,
        step_size=4.0 * flow_mag,
        seed=flow_seed,
    )

    # Temporal mapping for each dot
    delays = [_temporal_easing(i, n_points, duration) for i in range(n_points)]

    # ------------------------------------------------------------------
    # 3. Build SVG
    # ------------------------------------------------------------------
    # Colours
    if dark_mode:
        bg_color = "#0a0d14"
        bg_radial_color = "#1a1540"
        flow_hue_base = (int(h[4:8], 16) % 60 + 200) % 360
        text_color = "rgba(255,255,255,0.4)"
        arc_bg_color = "rgba(255,255,255,0.08)"
        arc_fg_color = "#7c6ef0"
        ripple_color = "rgba(180,160,255,0.5)"
    else:
        bg_color = "#f5f5fa"
        bg_radial_color = "#d8d0e8"
        flow_hue_base = (int(h[4:8], 16) % 60 + 200) % 360
        text_color = "rgba(0,0,0,0.3)"
        arc_bg_color = "rgba(0,0,0,0.06)"
        arc_fg_color = "#6c5ce7"
        ripple_color = "rgba(100,80,200,0.45)"

    # Timeline arc geometry (semicircle at bottom)
    arc_cx = _WIDTH // 2
    arc_cy = _HEIGHT - 30
    arc_r = _WIDTH // 2 - 50
    arc_len = round(math.pi * arc_r, 1)  # semicircle length

    # Dot sizes
    base_r = max(2.0, min(5.0, 120.0 / math.sqrt(max(n_points, 1))))
    pulse_r1 = round(base_r + 1, 1)
    pulse_r2 = round(base_r + 3, 1)

    css = _ACTIVITY_CSS.replace("ARC_LEN", str(arc_len))
    css = css.replace("PULSE_R1", str(pulse_r1))
    css = css.replace("PULSE_R2", str(pulse_r2))

    parts: list[str] = []
    parts.append(_svg_header(_WIDTH, _HEIGHT))

    # Defs: filters and gradients
    parts.append("<defs>\n")
    # Glow filter for outer dots
    parts.append(
        '<filter id="spiralGlow" x="-50%" y="-50%" width="200%" height="200%">'
        '<feGaussianBlur in="SourceGraphic" stdDeviation="3" result="b"/>'
        '<feComposite in="SourceGraphic" in2="b" operator="over"/>'
        '</filter>\n'
    )
    # Radial gradient for emerging background
    parts.append(
        f'<radialGradient id="bgRad" cx="50%" cy="50%" r="0%">\n'
        f'  <stop offset="0%" stop-color="{bg_radial_color}" stop-opacity="0.35"/>\n'
        f'  <stop offset="100%" stop-color="{bg_color}" stop-opacity="0"/>\n'
        f'  <animate attributeName="r" from="0%" to="75%" dur="{duration}s" fill="freeze"/>\n'
        f'</radialGradient>\n'
    )
    parts.append("</defs>\n")

    # CSS
    parts.append(css)

    # Background
    parts.append(f'<rect width="{_WIDTH}" height="{_HEIGHT}" fill="{bg_color}"/>\n')
    # Emerging radial gradient
    parts.append(f'<rect width="{_WIDTH}" height="{_HEIGHT}" fill="url(#bgRad)"/>\n')

    # ---- Layer 1: Flow-field lines (draw themselves) ----
    parts.append('<g id="flowField" opacity="0.22">\n')
    for li, trail in enumerate(lines):
        if len(trail) < 2:
            continue
        # Build SVG path
        path_d = f"M{trail[0][0]:.1f},{trail[0][1]:.1f}"
        for px, py in trail[1:]:
            path_d += f" L{px:.1f},{py:.1f}"

        # Approximate path length for stroke-dasharray
        trail_len = 0.0
        for ti in range(1, len(trail)):
            dx = trail[ti][0] - trail[ti - 1][0]
            dy = trail[ti][1] - trail[ti - 1][1]
            trail_len += math.sqrt(dx * dx + dy * dy)
        trail_len_rounded = round(trail_len, 0)

        # Flow line colour
        fl_hue = (flow_hue_base + li * 3) % 360
        fl_sat = 0.4
        fl_light = 0.55 if dark_mode else 0.45
        r, g, b = colorsys.hls_to_rgb(fl_hue / 360.0, fl_light, fl_sat)
        fl_color = f"rgb({int(r*255)},{int(g*255)},{int(b*255)})"

        # Stagger flow line animation across the duration
        fl_delay = round((li / max(len(lines), 1)) * duration * 0.6, 2)
        fl_dur = round(duration * 0.35 + (li % 5) * 0.5, 1)
        alpha = round(0.35 + 0.25 * bg_intensity, 2)

        parts.append(
            f'<path class="fd" d="{path_d}" stroke="{fl_color}" stroke-width="0.8" '
            f'opacity="{alpha}" '
            f'stroke-dasharray="{trail_len_rounded}" '
            f'style="--len:{trail_len_rounded};--dur:{fl_dur}s;--del:{fl_delay}s"/>\n'
        )
    parts.append("</g>\n")

    # ---- Layer 2: Ripple rings (one per dot) ----
    parts.append('<g id="ripples">\n')
    for i in range(n_points):
        px, py = pts[i]
        d = delays[i]
        parts.append(
            f'<circle cx="{px:.1f}" cy="{py:.1f}" r="0" fill="none" '
            f'stroke="{ripple_color}" stroke-width="1.8" opacity="0" '
            f'style="animation:ripple 1.5s ease-out {d:.2f}s both"/>\n'
        )
    parts.append("</g>\n")

    # ---- Layer 3: Phyllotaxis dots ----
    glow_threshold = int(n_points * 0.65)
    parts.append('<g id="spiral">\n')
    glow_parts: list[str] = []

    for i, (px, py) in enumerate(pts):
        dot_r = round(base_r + math.log1p(i) * 0.5, 2)
        # Colour: golden-angle hue cycling
        hue = ((i * 137.508) + float(int(h[8:12], 16) % 60)) % 360
        sat = 0.7
        lightness = 0.55 if not dark_mode else 0.65
        r_c, g_c, b_c = colorsys.hls_to_rgb(hue / 360.0, lightness, sat)
        color = f"rgb({int(r_c*255)},{int(g_c*255)},{int(b_c*255)})"

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

    # ---- Layer 4: Heartbeat pulse on first dot ----
    if pts:
        fx, fy = pts[0]
        # First dot: continuous subtle pulse after it appears
        first_delay = delays[0] + 1.5  # start pulsing after appear animation
        hue0 = (137.508 + float(int(h[8:12], 16) % 60)) % 360
        r0, g0, b0 = colorsys.hls_to_rgb(hue0 / 360.0, 0.6, 0.8)
        pulse_color = f"rgb({int(r0*255)},{int(g0*255)},{int(b0*255)})"
        parts.append(
            f'<circle cx="{fx:.1f}" cy="{fy:.1f}" r="{pulse_r1}" fill="{pulse_color}" '
            f'opacity="0" '
            f'style="animation:dotAppear 1.5s ease-out {delays[0]:.2f}s both, '
            f'pulse 2.5s ease-in-out {first_delay:.1f}s infinite"/>\n'
        )

    # ---- Layer 5: Timeline arc (semicircle at bottom) ----
    # Background arc
    arc_path = (
        f"M{arc_cx - arc_r},{arc_cy} "
        f"A{arc_r},{arc_r} 0 0 1 {arc_cx + arc_r},{arc_cy}"
    )
    parts.append(
        f'<path d="{arc_path}" fill="none" stroke="{arc_bg_color}" stroke-width="3"/>\n'
    )
    # Animated fill arc
    parts.append(
        f'<path d="{arc_path}" fill="none" stroke="{arc_fg_color}" stroke-width="3" '
        f'stroke-dasharray="{arc_len}" stroke-dashoffset="{arc_len}" opacity="0.7">\n'
        f'  <animate attributeName="stroke-dashoffset" from="{arc_len}" to="0" '
        f'dur="{duration}s" fill="freeze"/>\n'
        f'</path>\n'
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
        angle = math.pi * (1 - frac)  # left to right along semicircle
        tx = arc_cx + arc_r * math.cos(angle)
        ty = arc_cy - arc_r * math.sin(angle)
        parts.append(
            f'<circle cx="{tx:.1f}" cy="{ty:.1f}" r="2" fill="{arc_fg_color}" opacity="0.5"/>\n'
        )
        # Year label
        label_y = ty + 12
        parts.append(
            f'<text x="{tx:.1f}" y="{label_y:.1f}" text-anchor="middle" '
            f'font-size="7" font-family="monospace" fill="{text_color}">{yr}</text>\n'
        )

    parts.append(_svg_footer())

    svg_text = "".join(parts)
    out.write_text(svg_text, encoding="utf-8")

    size_kb = len(svg_text.encode("utf-8")) / 1024
    logger.info(
        "Animated activity art saved: {path} ({pts} dots, {lines} flow lines, {kb:.0f} KB)",
        path=out, pts=n_points, lines=len(lines), kb=size_kb,
    )
    return out


# =========================================================================
#  CLI entry point
# =========================================================================

def main() -> None:
    """CLI for standalone animated art generation."""
    parser = argparse.ArgumentParser(description="Generate animated historical artwork")
    parser.add_argument("--history", required=True, help="Path to history JSON")
    parser.add_argument(
        "--type",
        choices=["community", "activity", "all"],
        default="all",
        help="Which artwork to generate",
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=30.0,
        help="Animation duration in seconds",
    )
    parser.add_argument("--dark-mode", action="store_true", help="Dark mode variant")
    parser.add_argument("--output", help="Output SVG path (single type only)")
    args = parser.parse_args()

    history = json.loads(Path(args.history).read_text(encoding="utf-8"))

    if args.type in ("community", "all"):
        for dark in ([True, False] if args.type == "all" else [args.dark_mode]):
            out = Path(args.output) if args.output and args.type == "community" else None
            p = generate_animated_community_art(
                history, dark_mode=dark, output_path=out, duration=args.duration,
            )
            logger.info("Wrote {path}", path=p)

    if args.type in ("activity", "all"):
        for dark in ([True, False] if args.type == "all" else [args.dark_mode]):
            out = Path(args.output) if args.output and args.type == "activity" else None
            p = generate_animated_activity_art(
                history, dark_mode=dark, output_path=out, duration=args.duration,
            )
            logger.info("Wrote {path}", path=p)


if __name__ == "__main__":
    main()
