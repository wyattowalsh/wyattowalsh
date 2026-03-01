"""
Generative Art Prototypes v2 — Actually Beautiful
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Focus on inherently stunning mathematical forms with symmetry,
structure, and intentional aesthetic design.

Concepts:
1. Maurer Rose — connect vertices of a rose curve with lines.
   Creates intricate star/mandala patterns with natural rotational symmetry.
2. Guilloché — overlapping sinusoidal waves swept radially,
   like the engraving on currency. Moiré interference creates depth.
3. Spirograph Mandala — layered hypotrochoid/epitrochoid curves
   with golden ratio proportions and radial symmetry.
4. Geometric Bloom — sacred geometry seed-of-life base with
   generative parametric petals growing outward.
"""
from __future__ import annotations

import hashlib
import math
import random
from pathlib import Path

import numpy as np

WIDTH = 800
HEIGHT = 800
CX = WIDTH / 2
CY = HEIGHT / 2

# ---------------------------------------------------------------------------
# Color utilities
# ---------------------------------------------------------------------------

def _srgb_to_linear(c: float) -> float:
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

def _linear_to_srgb(c: float) -> float:
    return 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055

def oklch_to_hex(L: float, C: float, H: float) -> str:
    a = C * math.cos(math.radians(H))
    b = C * math.sin(math.radians(H))
    l_c = L + 0.3963377774 * a + 0.2158037573 * b
    m_c = L - 0.1055613458 * a - 0.0638541728 * b
    s_c = L - 0.0894841775 * a - 1.2914855480 * b
    l_ = l_c ** 3
    m_ = m_c ** 3
    s_ = s_c ** 3
    r = max(0, +4.0767416621 * l_ - 3.3077115913 * m_ + 0.2309699292 * s_)
    g = max(0, -1.2684380046 * l_ + 2.6097574011 * m_ - 0.3413193965 * s_)
    b_val = max(0, -0.0041960863 * l_ - 0.7034186147 * m_ + 1.7076147010 * s_)
    r = max(0.0, min(1.0, _linear_to_srgb(r)))
    g = max(0.0, min(1.0, _linear_to_srgb(g)))
    b_val = max(0.0, min(1.0, _linear_to_srgb(b_val)))
    return "#{:02x}{:02x}{:02x}".format(int(r * 255), int(g * 255), int(b_val * 255))


def gradient_color(t: float, palette: str = "aurora", dark: bool = True) -> str:
    """Get color at position t ∈ [0,1] from a curated gradient."""
    palettes = {
        "aurora": [
            (0.0, 0.45, 0.15, 160),   # Deep emerald
            (0.2, 0.55, 0.18, 175),   # Teal
            (0.4, 0.65, 0.16, 220),   # Blue
            (0.6, 0.60, 0.18, 280),   # Violet
            (0.8, 0.65, 0.20, 320),   # Magenta
            (1.0, 0.70, 0.15, 350),   # Pink
        ],
        "nebula": [
            (0.0, 0.20, 0.10, 280),   # Deep indigo
            (0.2, 0.35, 0.15, 300),   # Purple
            (0.4, 0.50, 0.18, 200),   # Teal
            (0.6, 0.65, 0.16, 180),   # Cyan
            (0.8, 0.75, 0.14, 80),    # Gold
            (1.0, 0.90, 0.06, 60),    # Warm white
        ],
        "fire": [
            (0.0, 0.15, 0.12, 15),    # Deep crimson
            (0.25, 0.40, 0.18, 25),   # Red
            (0.5, 0.60, 0.20, 45),    # Orange
            (0.75, 0.80, 0.16, 70),   # Amber
            (1.0, 0.92, 0.06, 85),    # Yellow-white
        ],
        "ocean": [
            (0.0, 0.20, 0.08, 240),   # Deep navy
            (0.25, 0.35, 0.14, 220),  # Blue
            (0.5, 0.55, 0.18, 190),   # Teal
            (0.75, 0.70, 0.15, 170),  # Cyan
            (1.0, 0.85, 0.08, 160),   # Mint
        ],
        "sacred": [
            (0.0, 0.30, 0.12, 45),    # Gold-brown
            (0.2, 0.50, 0.16, 40),    # Gold
            (0.4, 0.65, 0.14, 35),    # Bright gold
            (0.6, 0.55, 0.16, 280),   # Purple
            (0.8, 0.45, 0.14, 300),   # Deep violet
            (1.0, 0.70, 0.12, 320),   # Rose
        ],
    }

    stops = palettes.get(palette, palettes["aurora"])

    # Adjust for light mode
    if not dark:
        stops = [(s[0], min(s[1] + 0.1, 0.7), s[2] * 1.3, s[3]) for s in stops]

    for i in range(len(stops) - 1):
        t0, L0, C0, H0 = stops[i]
        t1, L1, C1, H1 = stops[i + 1]
        if t0 <= t <= t1:
            lt = (t - t0) / (t1 - t0)
            L = L0 + (L1 - L0) * lt
            C = C0 + (C1 - C0) * lt
            dh = H1 - H0
            if dh > 180: dh -= 360
            if dh < -180: dh += 360
            H = (H0 + dh * lt) % 360
            return oklch_to_hex(L, C, H)

    return oklch_to_hex(stops[-1][1], stops[-1][2], stops[-1][3])


# ---------------------------------------------------------------------------
# SVG helpers
# ---------------------------------------------------------------------------

def svg_header() -> str:
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" width="{WIDTH}" height="{HEIGHT}">\n'

def svg_footer() -> str:
    return '</svg>\n'

def bloom_filter(filter_id: str = "bloom") -> str:
    return f"""<filter id="{filter_id}" x="-50%" y="-50%" width="200%" height="200%">
    <feGaussianBlur in="SourceGraphic" stdDeviation="1.5" result="b1"/>
    <feGaussianBlur in="SourceGraphic" stdDeviation="4" result="b2"/>
    <feGaussianBlur in="SourceGraphic" stdDeviation="10" result="b3"/>
    <feColorMatrix in="b3" type="matrix" result="bright"
      values="1.4 0 0 0 0.06
              0 1.4 0 0 0.06
              0 0 1.4 0 0.06
              0 0 0 0.45 0"/>
    <feMerge>
      <feMergeNode in="bright"/>
      <feMergeNode in="b2"/>
      <feMergeNode in="b1"/>
      <feMergeNode in="SourceGraphic"/>
    </feMerge>
  </filter>"""


# =========================================================================
# 1. MAURER ROSE — Intricate star/mandala patterns
# =========================================================================

def maurer_rose_points(n: int, d: int, radius: float = 340.0,
                       num_points: int = 361) -> list[tuple[float, float]]:
    """Generate Maurer rose vertices.

    Rose curve: r = sin(n * θ)
    Maurer rose: connect points at θ = 0°, d°, 2d°, ...
    """
    pts = []
    for i in range(num_points):
        theta_deg = i * d
        theta = math.radians(theta_deg)
        r = radius * math.sin(n * theta)
        x = CX + r * math.cos(theta)
        y = CY + r * math.sin(theta)
        pts.append((x, y))
    return pts


def generate_maurer_rose(dark_mode: bool = True) -> Path:
    """Generate a Maurer rose mandala with multiple layered roses."""
    suffix = "-dark" if dark_mode else ""
    out = Path(f".github/assets/img/proto-maurer{suffix}.svg")
    out.parent.mkdir(parents=True, exist_ok=True)

    bg = "#050510" if dark_mode else "#fafafe"

    parts = [svg_header()]
    parts.append(f'<defs>\n  {bloom_filter()}\n')

    # Radial gradient background
    if dark_mode:
        parts.append("""  <radialGradient id="bg" cx="50%" cy="50%" r="50%">
    <stop offset="0%" stop-color="#0a0a20"/>
    <stop offset="100%" stop-color="#020208"/>
  </radialGradient>
  <radialGradient id="vignette" cx="50%" cy="50%" r="50%">
    <stop offset="50%" stop-color="black" stop-opacity="0"/>
    <stop offset="100%" stop-color="black" stop-opacity="0.5"/>
  </radialGradient>""")
    else:
        parts.append("""  <radialGradient id="bg" cx="50%" cy="50%" r="50%">
    <stop offset="0%" stop-color="#fdfcff"/>
    <stop offset="100%" stop-color="#f0eef8"/>
  </radialGradient>""")

    parts.append('\n</defs>\n')
    parts.append(f'<rect width="{WIDTH}" height="{HEIGHT}" fill="url(#bg)"/>\n')

    # Multiple layered Maurer roses with different parameters
    # These (n, d) pairs are known to produce stunning patterns
    layers = [
        # (n, d, radius, stroke_width, opacity, palette, palette_offset)
        (6, 71, 340, 0.3, 0.12, "nebula", 0.0),     # Outer whisper
        (4, 51, 300, 0.4, 0.18, "aurora", 0.0),      # Mid structure
        (5, 97, 280, 0.5, 0.25, "sacred", 0.1),      # Inner complexity
        (7, 29, 320, 0.35, 0.20, "ocean", 0.0),      # Geometric web
        (3, 47, 260, 0.6, 0.35, "nebula", 0.3),      # Core pattern
        (2, 39, 200, 0.8, 0.50, "fire", 0.0),        # Inner fire
    ]

    # Bloom group for all roses
    parts.append('<g filter="url(#bloom)">\n')

    for n, d, radius, sw, opacity, palette, p_offset in layers:
        pts = maurer_rose_points(n, d, radius)

        # Build the path
        path_d = f"M{pts[0][0]:.1f},{pts[0][1]:.1f}"
        for px, py in pts[1:]:
            path_d += f" L{px:.1f},{py:.1f}"
        path_d += " Z"

        # Color varies along the path length
        # Use gradient via stroke
        color = gradient_color(0.3 + p_offset, palette, dark_mode)
        parts.append(f'<path d="{path_d}" fill="none" stroke="{color}" '
                     f'stroke-width="{sw}" opacity="{opacity}" '
                     f'stroke-linecap="round" stroke-linejoin="round"/>\n')

    # Also draw the underlying rose curves (smooth) for structure
    rose_params = [(6, 340, "nebula", 0.3), (3, 260, "sacred", 0.6), (2, 200, "fire", 0.8)]
    for n, radius, palette, p_offset in rose_params:
        pts = []
        for i in range(3600):
            theta = i * math.pi * 2 / 3600
            r = radius * math.sin(n * theta)
            x = CX + r * math.cos(theta)
            y = CY + r * math.sin(theta)
            pts.append((x, y))

        path_d = f"M{pts[0][0]:.1f},{pts[0][1]:.1f}"
        for px, py in pts[1:]:
            path_d += f" L{px:.1f},{py:.1f}"
        path_d += " Z"

        color = gradient_color(p_offset, palette, dark_mode)
        parts.append(f'<path d="{path_d}" fill="none" stroke="{color}" '
                     f'stroke-width="0.6" opacity="0.4" '
                     f'stroke-linecap="round"/>\n')

    parts.append('</g>\n')

    # Center focal point
    center_color = gradient_color(0.5, "fire", dark_mode)
    parts.append(f'<circle cx="{CX}" cy="{CY}" r="3" fill="{center_color}" opacity="0.8"/>\n')

    if dark_mode:
        parts.append(f'<rect width="{WIDTH}" height="{HEIGHT}" fill="url(#vignette)"/>\n')

    parts.append(svg_footer())

    svg_text = "".join(parts)
    out.write_text(svg_text, encoding="utf-8")
    print(f"Maurer Rose {'dark' if dark_mode else 'light'}: {len(svg_text)//1024} KB → {out}")
    return out


# =========================================================================
# 2. GUILLOCHÉ — Currency-style engraved wave patterns
# =========================================================================

def guilloche_wave(
    cx: float, cy: float,
    R: float,  # Major radius
    r: float,  # Wave amplitude
    n_waves: int,  # Number of oscillations per revolution
    phase: float = 0.0,
    steps: int = 3600,
) -> list[tuple[float, float]]:
    """Generate a guilloché wave: a circle modulated by sinusoidal oscillation."""
    pts = []
    for i in range(steps + 1):
        theta = i * 2 * math.pi / steps
        radius = R + r * math.sin(n_waves * theta + phase)
        x = cx + radius * math.cos(theta)
        y = cy + radius * math.sin(theta)
        pts.append((x, y))
    return pts


def generate_guilloche(dark_mode: bool = True) -> Path:
    suffix = "-dark" if dark_mode else ""
    out = Path(f".github/assets/img/proto-guilloche{suffix}.svg")
    out.parent.mkdir(parents=True, exist_ok=True)

    parts = [svg_header()]

    if dark_mode:
        parts.append(f"""<defs>
  {bloom_filter()}
  <radialGradient id="bg" cx="50%" cy="50%" r="50%">
    <stop offset="0%" stop-color="#080818"/>
    <stop offset="100%" stop-color="#020208"/>
  </radialGradient>
  <radialGradient id="vignette" cx="50%" cy="50%" r="50%">
    <stop offset="50%" stop-color="black" stop-opacity="0"/>
    <stop offset="100%" stop-color="black" stop-opacity="0.45"/>
  </radialGradient>
</defs>\n""")
    else:
        parts.append(f"""<defs>
  {bloom_filter()}
  <radialGradient id="bg" cx="50%" cy="50%" r="50%">
    <stop offset="0%" stop-color="#fefefe"/>
    <stop offset="100%" stop-color="#f0eef5"/>
  </radialGradient>
</defs>\n""")

    parts.append(f'<rect width="{WIDTH}" height="{HEIGHT}" fill="url(#bg)"/>\n')

    # Multiple overlapping guilloché layers
    # Outer to inner, each with different wave counts creating moiré
    layers = [
        # (R, amplitude, n_waves, phase, sw, opacity, palette, color_t)
        (350, 30, 36, 0.0,   0.25, 0.10, "ocean", 0.1),
        (340, 25, 37, 0.3,   0.25, 0.12, "ocean", 0.2),
        (320, 35, 24, 0.0,   0.30, 0.14, "aurora", 0.0),
        (310, 30, 25, 0.5,   0.30, 0.16, "aurora", 0.15),
        (280, 40, 18, 0.0,   0.35, 0.18, "nebula", 0.1),
        (270, 35, 19, 0.7,   0.35, 0.20, "nebula", 0.25),
        (240, 30, 12, 0.0,   0.40, 0.25, "sacred", 0.0),
        (230, 25, 13, 1.0,   0.40, 0.28, "sacred", 0.2),
        (190, 25, 8,  0.0,   0.50, 0.32, "fire", 0.1),
        (180, 20, 9,  1.2,   0.50, 0.35, "fire", 0.3),
        (140, 20, 6,  0.0,   0.60, 0.40, "nebula", 0.5),
        (130, 15, 7,  0.8,   0.60, 0.45, "nebula", 0.6),
        (90,  15, 5,  0.0,   0.70, 0.50, "fire", 0.6),
        (80,  12, 4,  1.5,   0.70, 0.55, "fire", 0.8),
    ]

    parts.append('<g filter="url(#bloom)">\n')

    for R, amp, n_w, phase, sw, opacity, palette, ct in layers:
        pts = guilloche_wave(CX, CY, R, amp, n_w, phase)

        path_d = f"M{pts[0][0]:.1f},{pts[0][1]:.1f}"
        for px, py in pts[1:]:
            path_d += f" L{px:.1f},{py:.1f}"

        color = gradient_color(ct, palette, dark_mode)
        parts.append(f'<path d="{path_d}" fill="none" stroke="{color}" '
                     f'stroke-width="{sw}" opacity="{opacity}"/>\n')

    # Add straight-line radial guilloché spokes
    n_spokes = 72
    for i in range(n_spokes):
        theta = i * 2 * math.pi / n_spokes
        # Each spoke is a wavy line from center to edge
        spoke_pts = []
        for r in range(20, 370, 2):
            wave = 3 * math.sin(r * 0.08 + theta * 5)
            x = CX + (r + wave) * math.cos(theta)
            y = CY + (r + wave) * math.sin(theta)
            spoke_pts.append((x, y))

        if len(spoke_pts) > 1:
            path_d = f"M{spoke_pts[0][0]:.1f},{spoke_pts[0][1]:.1f}"
            for px, py in spoke_pts[1:]:
                path_d += f" L{px:.1f},{py:.1f}"

            ct = (i / n_spokes) % 1.0
            color = gradient_color(ct, "aurora", dark_mode)
            parts.append(f'<path d="{path_d}" fill="none" stroke="{color}" '
                         f'stroke-width="0.15" opacity="0.08"/>\n')

    parts.append('</g>\n')

    if dark_mode:
        parts.append(f'<rect width="{WIDTH}" height="{HEIGHT}" fill="url(#vignette)"/>\n')

    parts.append(svg_footer())

    svg_text = "".join(parts)
    out.write_text(svg_text, encoding="utf-8")
    print(f"Guilloché {'dark' if dark_mode else 'light'}: {len(svg_text)//1024} KB → {out}")
    return out


# =========================================================================
# 3. SPIROGRAPH MANDALA — Layered hypotrochoid/epitrochoid
# =========================================================================

def hypotrochoid(
    R: float, r: float, d_offset: float,
    steps: int = 7200,
) -> list[tuple[float, float]]:
    """Hypotrochoid: smaller circle rolling inside larger.

    x = (R-r)*cos(t) + d*cos((R-r)/r * t)
    y = (R-r)*sin(t) - d*sin((R-r)/r * t)
    """
    pts = []
    # Number of full rotations needed for the curve to close
    # lcm(R, r) / r rotations of the small circle
    revolutions = max(1, int(R / math.gcd(int(R), int(r))))
    total_angle = revolutions * 2 * math.pi

    for i in range(steps + 1):
        t = i * total_angle / steps
        x = CX + (R - r) * math.cos(t) + d_offset * math.cos((R - r) / r * t)
        y = CY + (R - r) * math.sin(t) - d_offset * math.sin((R - r) / r * t)
        pts.append((x, y))

    return pts


def epitrochoid(
    R: float, r: float, d_offset: float,
    steps: int = 7200,
) -> list[tuple[float, float]]:
    """Epitrochoid: smaller circle rolling outside larger."""
    pts = []
    revolutions = max(1, int(R / math.gcd(int(R), int(r))))
    total_angle = revolutions * 2 * math.pi

    for i in range(steps + 1):
        t = i * total_angle / steps
        x = CX + (R + r) * math.cos(t) - d_offset * math.cos((R + r) / r * t)
        y = CY + (R + r) * math.sin(t) - d_offset * math.sin((R + r) / r * t)
        pts.append((x, y))

    return pts


def generate_spirograph(dark_mode: bool = True) -> Path:
    suffix = "-dark" if dark_mode else ""
    out = Path(f".github/assets/img/proto-spirograph{suffix}.svg")
    out.parent.mkdir(parents=True, exist_ok=True)

    parts = [svg_header()]

    if dark_mode:
        parts.append(f"""<defs>
  {bloom_filter()}
  <radialGradient id="bg" cx="50%" cy="50%" r="50%">
    <stop offset="0%" stop-color="#0c0414"/>
    <stop offset="100%" stop-color="#030108"/>
  </radialGradient>
  <radialGradient id="vignette" cx="50%" cy="50%" r="50%">
    <stop offset="50%" stop-color="black" stop-opacity="0"/>
    <stop offset="100%" stop-color="black" stop-opacity="0.4"/>
  </radialGradient>
</defs>\n""")
    else:
        parts.append(f"""<defs>
  {bloom_filter()}
  <radialGradient id="bg" cx="50%" cy="50%" r="60%">
    <stop offset="0%" stop-color="#fefcff"/>
    <stop offset="100%" stop-color="#f3eefa"/>
  </radialGradient>
</defs>\n""")

    parts.append(f'<rect width="{WIDTH}" height="{HEIGHT}" fill="url(#bg)"/>\n')

    # Layered spirograph curves (outer to inner)
    # (R, r, d, scale, sw, opacity, palette, color_t)
    hypo_layers = [
        (210, 70, 130, 1.0, 0.25, 0.12, "nebula", 0.0),    # 3-lobed
        (175, 35, 100, 1.0, 0.30, 0.18, "aurora", 0.1),     # 5-lobed
        (200, 50, 120, 1.0, 0.25, 0.15, "ocean", 0.2),      # 4-lobed
        (150, 30, 90,  1.0, 0.35, 0.22, "sacred", 0.0),     # 5-lobed
        (180, 60, 95,  1.0, 0.30, 0.20, "nebula", 0.4),     # 3-lobed
        (120, 24, 72,  1.0, 0.40, 0.28, "fire", 0.2),       # 5-lobed
        (100, 33, 60,  1.0, 0.45, 0.32, "aurora", 0.5),     # ~3-lobed
        (80,  20, 50,  1.0, 0.50, 0.38, "sacred", 0.5),     # 4-lobed
        (60,  15, 38,  1.0, 0.55, 0.42, "nebula", 0.7),     # 4-lobed
        (45,  9,  28,  1.0, 0.60, 0.50, "fire", 0.7),       # 5-lobed
    ]

    epi_layers = [
        (60,  20, 30,  1.0, 0.20, 0.08, "ocean", 0.0),     # Outer frame
        (45,  15, 22,  1.0, 0.25, 0.12, "aurora", 0.3),     # Mid frame
    ]

    parts.append('<g filter="url(#bloom)">\n')

    # Epitrochoid layers (outer decorative frame)
    for R, r, d, scale, sw, opacity, palette, ct in epi_layers:
        pts = epitrochoid(R, r, d)
        if len(pts) < 2:
            continue
        path_d = f"M{pts[0][0]:.1f},{pts[0][1]:.1f}"
        for px, py in pts[1:]:
            path_d += f" L{px:.1f},{py:.1f}"
        color = gradient_color(ct, palette, dark_mode)
        parts.append(f'<path d="{path_d}" fill="none" stroke="{color}" '
                     f'stroke-width="{sw}" opacity="{opacity}"/>\n')

    # Hypotrochoid layers (main mandala)
    for R, r, d, scale, sw, opacity, palette, ct in hypo_layers:
        pts = hypotrochoid(R, r, d)
        if len(pts) < 2:
            continue
        path_d = f"M{pts[0][0]:.1f},{pts[0][1]:.1f}"
        for px, py in pts[1:]:
            path_d += f" L{px:.1f},{py:.1f}"
        color = gradient_color(ct, palette, dark_mode)
        parts.append(f'<path d="{path_d}" fill="none" stroke="{color}" '
                     f'stroke-width="{sw}" opacity="{opacity}"/>\n')

    # Add rotated copies of a single spirograph for extra density
    base_pts = hypotrochoid(140, 42, 85)
    for rot in range(6):
        angle = rot * math.pi / 3  # 60° increments
        rotated = []
        for px, py in base_pts:
            dx, dy = px - CX, py - CY
            rx = CX + dx * math.cos(angle) - dy * math.sin(angle)
            ry = CY + dx * math.sin(angle) + dy * math.cos(angle)
            rotated.append((rx, ry))

        path_d = f"M{rotated[0][0]:.1f},{rotated[0][1]:.1f}"
        for px, py in rotated[1:]:
            path_d += f" L{px:.1f},{py:.1f}"

        ct = rot / 6
        color = gradient_color(ct, "aurora", dark_mode)
        parts.append(f'<path d="{path_d}" fill="none" stroke="{color}" '
                     f'stroke-width="0.2" opacity="0.10"/>\n')

    parts.append('</g>\n')

    # Center ornament
    center_color = gradient_color(0.8, "fire", dark_mode)
    parts.append(f'<circle cx="{CX}" cy="{CY}" r="2" fill="{center_color}" opacity="0.7"/>\n')

    if dark_mode:
        parts.append(f'<rect width="{WIDTH}" height="{HEIGHT}" fill="url(#vignette)"/>\n')

    parts.append(svg_footer())

    svg_text = "".join(parts)
    out.write_text(svg_text, encoding="utf-8")
    print(f"Spirograph {'dark' if dark_mode else 'light'}: {len(svg_text)//1024} KB → {out}")
    return out


# =========================================================================
# 4. GEOMETRIC BLOOM — Sacred geometry with generative petals
# =========================================================================

def generate_geometric_bloom(dark_mode: bool = True) -> Path:
    """Sacred geometry base (flower of life circles) with
    parametric petal curves growing outward."""
    suffix = "-dark" if dark_mode else ""
    out = Path(f".github/assets/img/proto-geobloom{suffix}.svg")
    out.parent.mkdir(parents=True, exist_ok=True)

    parts = [svg_header()]

    if dark_mode:
        parts.append(f"""<defs>
  {bloom_filter()}
  {bloom_filter("bloom2")}
  <radialGradient id="bg" cx="50%" cy="50%" r="50%">
    <stop offset="0%" stop-color="#0a0818"/>
    <stop offset="100%" stop-color="#020108"/>
  </radialGradient>
  <radialGradient id="vignette" cx="50%" cy="50%" r="50%">
    <stop offset="50%" stop-color="black" stop-opacity="0"/>
    <stop offset="100%" stop-color="black" stop-opacity="0.45"/>
  </radialGradient>
</defs>\n""")
    else:
        parts.append(f"""<defs>
  {bloom_filter()}
  <radialGradient id="bg" cx="50%" cy="50%" r="50%">
    <stop offset="0%" stop-color="#fdfcff"/>
    <stop offset="100%" stop-color="#f0ecf8"/>
  </radialGradient>
</defs>\n""")

    parts.append(f'<rect width="{WIDTH}" height="{HEIGHT}" fill="url(#bg)"/>\n')

    parts.append('<g filter="url(#bloom)">\n')

    # --- Layer 1: Flower of Life circles ---
    flower_r = 80
    # Ring 1: center + 6 around
    flower_centers = [(CX, CY)]
    for i in range(6):
        angle = i * math.pi / 3
        flower_centers.append((CX + flower_r * math.cos(angle),
                              CY + flower_r * math.sin(angle)))
    # Ring 2: 6 more on the outer ring
    for i in range(6):
        angle = i * math.pi / 3 + math.pi / 6
        flower_centers.append((CX + flower_r * 1.732 * math.cos(angle),
                              CY + flower_r * 1.732 * math.sin(angle)))
    # Ring 3
    for i in range(12):
        angle = i * math.pi / 6
        flower_centers.append((CX + flower_r * 2 * math.cos(angle),
                              CY + flower_r * 2 * math.sin(angle)))

    fc_color = gradient_color(0.3, "sacred", dark_mode)
    for fcx, fcy in flower_centers:
        parts.append(f'<circle cx="{fcx:.1f}" cy="{fcy:.1f}" r="{flower_r}" '
                     f'fill="none" stroke="{fc_color}" stroke-width="0.3" opacity="0.12"/>\n')

    # --- Layer 2: Generative petal curves (rose curves at various radii) ---
    # Multi-petal rose curves at increasing radii
    petal_configs = [
        (5, 120, 0.5, 0.30, "aurora", 0.0),
        (7, 160, 0.4, 0.25, "nebula", 0.2),
        (8, 200, 0.35, 0.20, "ocean", 0.1),
        (11, 250, 0.3, 0.18, "aurora", 0.4),
        (13, 300, 0.25, 0.15, "nebula", 0.5),
        (17, 350, 0.2, 0.10, "sacred", 0.3),
    ]

    for n_petals, radius, sw, opacity, palette, ct in petal_configs:
        pts = []
        for i in range(7200):
            theta = i * 2 * math.pi / 7200
            r = radius * abs(math.cos(n_petals * theta / 2))
            x = CX + r * math.cos(theta)
            y = CY + r * math.sin(theta)
            pts.append((x, y))

        path_d = f"M{pts[0][0]:.1f},{pts[0][1]:.1f}"
        for px, py in pts[1:]:
            path_d += f" L{px:.1f},{py:.1f}"
        path_d += " Z"

        color = gradient_color(ct, palette, dark_mode)
        parts.append(f'<path d="{path_d}" fill="none" stroke="{color}" '
                     f'stroke-width="{sw}" opacity="{opacity}"/>\n')

    # --- Layer 3: Geometric framework lines ---
    # Hexagonal grid lines for structure
    hex_r_values = [80, 160, 240, 320]
    for hr in hex_r_values:
        hex_pts = []
        for i in range(7):
            angle = i * math.pi / 3
            hex_pts.append((CX + hr * math.cos(angle), CY + hr * math.sin(angle)))
        path_d = f"M{hex_pts[0][0]:.1f},{hex_pts[0][1]:.1f}"
        for px, py in hex_pts[1:]:
            path_d += f" L{px:.1f},{py:.1f}"
        hc = gradient_color(0.4, "sacred", dark_mode)
        parts.append(f'<path d="{path_d}" fill="none" stroke="{hc}" '
                     f'stroke-width="0.2" opacity="0.06"/>\n')

    # Concentric circles
    for cr in range(40, 380, 40):
        cc = gradient_color(cr / 380, "ocean", dark_mode)
        parts.append(f'<circle cx="{CX}" cy="{CY}" r="{cr}" fill="none" '
                     f'stroke="{cc}" stroke-width="0.15" opacity="0.05"/>\n')

    # Radial lines (12-fold)
    for i in range(12):
        angle = i * math.pi / 6
        x2 = CX + 380 * math.cos(angle)
        y2 = CY + 380 * math.sin(angle)
        lc = gradient_color(i / 12, "aurora", dark_mode)
        parts.append(f'<line x1="{CX}" y1="{CY}" x2="{x2:.1f}" y2="{y2:.1f}" '
                     f'stroke="{lc}" stroke-width="0.15" opacity="0.05"/>\n')

    parts.append('</g>\n')

    if dark_mode:
        parts.append(f'<rect width="{WIDTH}" height="{HEIGHT}" fill="url(#vignette)"/>\n')

    parts.append(svg_footer())

    svg_text = "".join(parts)
    out.write_text(svg_text, encoding="utf-8")
    print(f"Geometric Bloom {'dark' if dark_mode else 'light'}: {len(svg_text)//1024} KB → {out}")
    return out


# =========================================================================
# Main
# =========================================================================

if __name__ == "__main__":
    generate_maurer_rose(dark_mode=True)
    generate_maurer_rose(dark_mode=False)
    generate_guilloche(dark_mode=True)
    generate_guilloche(dark_mode=False)
    generate_spirograph(dark_mode=True)
    generate_spirograph(dark_mode=False)
    generate_geometric_bloom(dark_mode=True)
    generate_geometric_bloom(dark_mode=False)
    print("\nDone! Open the proto-* SVGs in a browser to compare.")
