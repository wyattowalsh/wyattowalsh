"""Generative-art math helpers (phyllotaxis, flow fields)."""
from __future__ import annotations

import math

import numpy as np

# ---------------------------------------------------------------------------
# Generative-art math helpers (shared by generative.py + animated_art.py)
# ---------------------------------------------------------------------------

def phyllotaxis_points(
    n: int,
    center_x: float,
    center_y: float,
    scale: float = 12.0,
) -> list[tuple[float, float]]:
    """Compute *n* points on a golden-angle phyllotaxis spiral.

    angle_n = n * 137.508 degrees
    radius_n = sqrt(n) * scale
    """
    golden_angle = 137.508 * (math.pi / 180.0)
    pts: list[tuple[float, float]] = []
    for i in range(1, n + 1):
        r = math.sqrt(i) * scale
        theta = i * golden_angle
        x = center_x + r * math.cos(theta)
        y = center_y + r * math.sin(theta)
        pts.append((x, y))
    return pts


def flow_field_lines(
    width: int,
    height: int,
    num_lines: int,
    steps: int = 30,
    step_size: float = 4.0,
    freq: float = 0.005,
    octaves: int = 3,
    seed: int = 42,
) -> list[list[tuple[float, float]]]:
    """Generate flow-field particle traces using trigonometric noise.

    Uses a trig-based noise approximation so no external noise library
    is required.
    """
    rng = np.random.default_rng(seed)
    lines: list[list[tuple[float, float]]] = []
    for _ in range(num_lines):
        x = float(rng.uniform(0, width))
        y = float(rng.uniform(0, height))
        trail: list[tuple[float, float]] = [(x, y)]
        for _ in range(steps):
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
