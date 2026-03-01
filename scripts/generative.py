"""
generative.py
~~~~~~~~~~~~~
Event-driven generative artwork for the GitHub profile.

Two independent SVG artworks, each seeded by a different dimension of
the profile's life:

- **Community Art** — Clifford Strange Attractor, orbit-density heatmap.
  Seeded by others' interactions: stars, forks, watchers, latest stargazer.
- **Activity Art** — Golden-angle Phyllotaxis spiral + Perlin flow field.
  Seeded by the owner's GitHub journey: repos, followers, commits, orgs.

Both are deterministic (same data = same art) and sensitive (one new star
= completely different pattern).
"""

from __future__ import annotations

import argparse
import colorsys
import hashlib
import json
import math
from pathlib import Path
from typing import Optional

import numpy as np
import svgwrite

from .banner import draw_clifford
from .utils import get_logger

logger = get_logger(module=__name__)

# Dimensions for generated SVGs
_WIDTH = 800
_HEIGHT = 800


def _seed_hash(seed_str: str) -> str:
    """SHA-256 hex digest of a seed string."""
    return hashlib.sha256(seed_str.encode()).hexdigest()


def _hex_slice(h: str, start: int, end: int) -> float:
    """Extract a normalized float [0, 1) from hex digest slice."""
    return int(h[start:end], 16) / (16 ** (end - start))


# ---------------------------------------------------------------------------
# Community Art — Clifford Strange Attractor
# ---------------------------------------------------------------------------

def generate_community_art(
    metrics: dict,
    dark_mode: bool = False,
    output_path: Optional[Path] = None,
) -> Path:
    """Generate community artwork seeded by others' interactions.

    The Clifford Strange Attractor parameters (a, b, c, d) are derived from
    a SHA-256 hash of the concatenated community metrics.  This makes the
    visual pattern deterministically unique for every combination of stars,
    forks, watchers, issues, and latest actors.
    """
    out = Path(output_path or f".github/assets/img/generative-community{'-dark' if dark_mode else ''}.svg")
    out.parent.mkdir(parents=True, exist_ok=True)

    seed_str = (
        f"{metrics.get('stars', 0)}-{metrics.get('forks', 0)}"
        f"-{metrics.get('watchers', 0)}-{metrics.get('open_issues_count', 0)}"
        f"-{metrics.get('network_count', 0)}"
        f"-{metrics.get('latest_stargazer', '')}"
        f"-{metrics.get('latest_fork_owner', '')}"
    )
    h = _seed_hash(seed_str)

    # Map hash slices to Clifford parameters
    a = 0.8 + _hex_slice(h, 0, 4) * 1.2
    b = 0.8 + _hex_slice(h, 4, 8) * 1.2
    c = -2.0 + _hex_slice(h, 8, 12) * 4.0
    d = -2.0 + _hex_slice(h, 12, 16) * 4.0
    grid_sz = 150
    iters = 1_000_000 + (metrics.get("network_count") or 0) * 50_000
    iters = min(iters, grid_sz * grid_sz * 60)
    hue_shift = float((metrics.get("forks", 0) * 37 + int(h[16:20], 16) % 60) % 360) / 360.0

    logger.info(
        "Community art: a={a:.3f} b={b:.3f} c={c:.3f} d={d:.3f} "
        "iters={iters} hue_shift={hue_shift}",
        a=a, b=b, c=c, d=d, iters=iters, hue_shift=hue_shift,
    )

    bg = "#0d1117" if dark_mode else "#ffffff"
    dwg = svgwrite.Drawing(
        filename=str(out),
        size=(f"{_WIDTH}px", f"{_HEIGHT}px"),
        profile="full",
    )
    dwg.add(dwg.rect(insert=(0, 0), size=(_WIDTH, _HEIGHT), fill=bg))

    group = dwg.g(id="cliffordGroup")
    dwg.add(group)

    draw_clifford(
        dwg=dwg,
        group=group,
        width=_WIDTH,
        height=_HEIGHT,
        a=a,
        b=b,
        c=c,
        d=d,
        iterations=iters,
        hue_shift=hue_shift,
        dark_mode=dark_mode,
        grid_size=grid_sz,
    )

    dwg.save(pretty=False)
    logger.info("Community art saved to {path}", path=out)
    return out


# ---------------------------------------------------------------------------
# Activity Art — Golden-angle Phyllotaxis + Flow Field
# ---------------------------------------------------------------------------

def _phyllotaxis_points(
    n: int,
    center_x: float,
    center_y: float,
    scale: float = 12.0,
) -> list[tuple[float, float]]:
    """Compute n points using golden-angle phyllotaxis.

    angle_n = n * 137.508 degrees
    radius_n = sqrt(n) * scale
    """
    golden_angle = 137.508 * (math.pi / 180.0)
    pts = []
    for i in range(1, n + 1):
        r = math.sqrt(i) * scale
        theta = i * golden_angle
        x = center_x + r * math.cos(theta)
        y = center_y + r * math.sin(theta)
        pts.append((x, y))
    return pts


def _flow_field_lines(
    width: int,
    height: int,
    num_lines: int,
    steps: int = 30,
    step_size: float = 4.0,
    freq: float = 0.005,
    octaves: int = 3,
    seed: int = 42,
) -> list[list[tuple[float, float]]]:
    """Generate flow field particle traces using simple harmonic noise.

    Uses a trigonometric noise approximation (similar to NoiseHandler fallback)
    so we don't require the noise package.
    """
    rng = np.random.default_rng(seed)
    lines = []
    for _ in range(num_lines):
        x = rng.uniform(0, width)
        y = rng.uniform(0, height)
        trail = [(x, y)]
        for _ in range(steps):
            # Simple trig-based noise → angle
            angle = 0.0
            amp = 1.0
            f = freq
            for _o in range(octaves):
                angle += amp * math.sin(x * f) * math.cos(y * f * 0.7)
                amp *= 0.5
                f *= 2.0
            angle *= math.pi * 2
            x += math.cos(angle) * step_size
            y += math.sin(angle) * step_size
            if x < 0 or x > width or y < 0 or y > height:
                break
            trail.append((x, y))
        if len(trail) > 2:
            lines.append(trail)
    return lines


def generate_activity_art(
    metrics: dict,
    dark_mode: bool = False,
    output_path: Optional[Path] = None,
) -> Path:
    """Generate activity artwork seeded by the owner's GitHub journey.

    Each of the owner's public repos becomes a dot on a golden-angle
    phyllotaxis spiral.  A flow field background adds organic texture,
    its parameters derived from follower count, org count, and commits.
    """
    out = Path(output_path or f".github/assets/img/generative-activity{'-dark' if dark_mode else ''}.svg")
    out.parent.mkdir(parents=True, exist_ok=True)

    seed_str = (
        f"{metrics.get('public_repos') or 0}-{metrics.get('followers') or 0}"
        f"-{metrics.get('orgs_count') or 0}-{metrics.get('contributions_last_year') or 0}"
        f"-{metrics.get('total_commits') or 0}-{metrics.get('following') or 0}"
    )
    h = _seed_hash(seed_str)

    n_points = max(10, metrics.get("public_repos") or 50)
    octaves = max(1, min(4, (metrics.get("followers") or 0) // 20))
    flow_mag = 1.0 + (metrics.get("orgs_count") or 0) * 0.15
    flow_freq = 0.003 + _hex_slice(h, 0, 4) * 0.007
    line_count = min(200, max(20, (metrics.get("total_commits") or 0) // 500))
    bg_intensity = min(1.0, (metrics.get("contributions_last_year") or 0) / 2000.0)

    logger.info(
        "Activity art: n_points={n} octaves={o} flow_mag={m:.2f} "
        "flow_freq={f:.4f} lines={l}",
        n=n_points, o=octaves, m=flow_mag, f=flow_freq, l=line_count,
    )

    bg = "#0d1117" if dark_mode else "#ffffff"
    dwg = svgwrite.Drawing(
        filename=str(out),
        size=(f"{_WIDTH}px", f"{_HEIGHT}px"),
        profile="full",
    )
    dwg.add(dwg.rect(insert=(0, 0), size=(_WIDTH, _HEIGHT), fill=bg))

    # --- Background: flow field ---
    flow_group = dwg.g(id="flowFieldGroup", opacity=0.25)
    dwg.add(flow_group)

    flow_seed = int(h[20:28], 16) % (2**31)
    lines = _flow_field_lines(
        _WIDTH, _HEIGHT,
        num_lines=line_count,
        freq=flow_freq,
        octaves=octaves,
        step_size=4.0 * flow_mag,
        seed=flow_seed,
    )

    # Flow line gradient
    flow_hue = (int(h[4:8], 16) % 60 + 200) % 360
    for i, trail in enumerate(lines):
        if len(trail) < 2:
            continue
        path_d = f"M{trail[0][0]:.1f},{trail[0][1]:.1f}"
        for x, y in trail[1:]:
            path_d += f" L{x:.1f},{y:.1f}"

        alpha = 0.4 + 0.3 * bg_intensity
        r, g, b = colorsys.hls_to_rgb(flow_hue / 360.0, 0.5, 0.4)
        color = f"rgb({int(r*255)},{int(g*255)},{int(b*255)})"

        flow_group.add(dwg.path(
            d=path_d,
            stroke=color,
            fill="none",
            stroke_width=0.8,
            opacity=alpha,
        ))

    # --- Foreground: phyllotaxis spiral ---
    spiral_group = dwg.g(id="phyllotaxisGroup")
    dwg.add(spiral_group)

    # Glow group for outer dots (rendered on top with filter)
    glow_group = None
    glow_threshold = int(n_points * 0.6) if n_points > 50 else n_points
    if n_points > 50:
        glow_filter = dwg.defs.add(dwg.filter(id="phyllotaxisGlow"))
        glow_filter.feGaussianBlur(in_="SourceGraphic", stdDeviation="2", result="blur")
        glow_filter.feComposite(in_="SourceGraphic", in2="blur", operator="over")
        glow_group = dwg.g(id="phyllotaxisGlowGroup")
        glow_group["filter"] = "url(#phyllotaxisGlow)"
        dwg.add(glow_group)

    # Scale factor so the spiral fits within the canvas
    max_radius = math.sqrt(n_points) * 12.0
    canvas_radius = min(_WIDTH, _HEIGHT) * 0.42
    scale = canvas_radius / max(max_radius, 1.0) * 12.0

    pts = _phyllotaxis_points(n_points, _WIDTH / 2, _HEIGHT / 2, scale=scale)

    for i, (px, py) in enumerate(pts):
        # Size: outer points are slightly larger (log scale)
        dot_r = 3.0 + math.log1p(i) * 0.8
        # Color: cycle through hues based on golden angle
        hue = ((i * 137.508) + float(int(h[8:12], 16) % 60)) % 360
        sat = 0.7
        lightness = 0.55 if not dark_mode else 0.65
        r, g, b = colorsys.hls_to_rgb(hue / 360.0, lightness, sat)
        color = f"rgb({int(r*255)},{int(g*255)},{int(b*255)})"

        circle = dwg.circle(
            center=(px, py),
            r=dot_r,
            fill=color,
            opacity=0.85,
        )

        # Outer dots get the glow filter
        if glow_group is not None and i >= glow_threshold:
            glow_group.add(circle)
        else:
            spiral_group.add(circle)

    dwg.save(pretty=False)
    logger.info("Activity art saved to {path}", path=out)
    return out


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """CLI for standalone generative art generation."""
    parser = argparse.ArgumentParser(description="Generate event-driven artwork")
    parser.add_argument("--metrics", required=True, help="Path to metrics JSON")
    parser.add_argument(
        "--type",
        choices=["community", "activity", "all"],
        default="all",
        help="Which artwork to generate",
    )
    parser.add_argument("--dark-mode", action="store_true", help="Dark mode variant")
    parser.add_argument("--output", help="Output SVG path (only for single type)")
    args = parser.parse_args()

    metrics = json.loads(Path(args.metrics).read_text())

    if args.type in ("community", "all"):
        out = Path(args.output) if args.output and args.type == "community" else None
        generate_community_art(metrics, dark_mode=args.dark_mode, output_path=out)

    if args.type in ("activity", "all"):
        out = Path(args.output) if args.output and args.type == "activity" else None
        generate_activity_art(metrics, dark_mode=args.dark_mode, output_path=out)


if __name__ == "__main__":
    main()
