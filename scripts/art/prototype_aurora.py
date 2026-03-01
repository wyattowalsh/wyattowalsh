"""
Aurora Borealis — Prototype
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Damped harmonograph (Lissajous) curves rendered as shimmering aurora curtains.

- Multiple overlapping traces with moire interference
- Aurora palette: green → teal → violet → pink (OKLCH)
- 3-pass bloom for light-bleeding effect
- feTurbulence aurora curtain background
- Starfield behind
- Chromatic aberration on traces
"""
from __future__ import annotations

import hashlib
import math
import random
from pathlib import Path

import numpy as np

# ---------------------------------------------------------------------------
# OKLCH color math
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
    r = +4.0767416621 * l_ - 3.3077115913 * m_ + 0.2309699292 * s_
    g = -1.2684380046 * l_ + 2.6097574011 * m_ - 0.3413193965 * s_
    b_val = -0.0041960863 * l_ - 0.7034186147 * m_ + 1.7076147010 * s_
    r = max(0.0, min(1.0, _linear_to_srgb(max(0, r))))
    g = max(0.0, min(1.0, _linear_to_srgb(max(0, g))))
    b_val = max(0.0, min(1.0, _linear_to_srgb(max(0, b_val))))
    return "#{:02x}{:02x}{:02x}".format(int(r * 255), int(g * 255), int(b_val * 255))

def hex_to_oklch(h: str) -> tuple[float, float, float]:
    r = _srgb_to_linear(int(h[1:3], 16) / 255)
    g = _srgb_to_linear(int(h[3:5], 16) / 255)
    b = _srgb_to_linear(int(h[5:7], 16) / 255)
    l_ = 0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b
    m_ = 0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b
    s_ = 0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b
    l_c = l_ ** (1/3) if l_ >= 0 else -((-l_) ** (1/3))
    m_c = m_ ** (1/3) if m_ >= 0 else -((-m_) ** (1/3))
    s_c = s_ ** (1/3) if s_ >= 0 else -((-s_) ** (1/3))
    L = 0.2104542553 * l_c + 0.7936177850 * m_c - 0.0040720468 * s_c
    a = 1.9779984951 * l_c - 2.4285922050 * m_c + 0.4505937099 * s_c
    bb = 0.0259040371 * l_c + 0.7827717662 * m_c - 0.8086757660 * s_c
    C = math.sqrt(a * a + bb * bb)
    H = math.degrees(math.atan2(bb, a)) % 360
    return (L, C, H)

def oklch_lerp(hex1: str, hex2: str, t: float) -> str:
    L1, C1, H1 = hex_to_oklch(hex1)
    L2, C2, H2 = hex_to_oklch(hex2)
    dh = H2 - H1
    if dh > 180: dh -= 360
    if dh < -180: dh += 360
    L = L1 + (L2 - L1) * t
    C = C1 + (C2 - C1) * t
    H = (H1 + dh * t) % 360
    return oklch_to_hex(L, C, H)


def aurora_color(t: float, dark_mode: bool = True) -> str:
    """Map [0,1] to aurora palette: green → teal → cyan → violet → pink."""
    if dark_mode:
        stops = [
            (0.0,  "#064e3b"),  # Deep emerald
            (0.15, "#059669"),  # Green
            (0.30, "#14b8a6"),  # Teal
            (0.45, "#06b6d4"),  # Cyan
            (0.60, "#818cf8"),  # Indigo
            (0.75, "#a78bfa"),  # Violet
            (0.90, "#e879f9"),  # Pink
            (1.0,  "#f0abfc"),  # Light pink
        ]
    else:
        stops = [
            (0.0,  "#047857"),  # Dark green
            (0.15, "#0d9488"),  # Teal
            (0.30, "#0891b2"),  # Cyan
            (0.45, "#6366f1"),  # Indigo
            (0.60, "#7c3aed"),  # Violet
            (0.75, "#a855f7"),  # Purple
            (0.90, "#d946ef"),  # Fuchsia
            (1.0,  "#ec4899"),  # Pink
        ]
    for i in range(len(stops) - 1):
        t0, c0 = stops[i]
        t1, c1 = stops[i + 1]
        if t0 <= t <= t1:
            local_t = (t - t0) / (t1 - t0)
            return oklch_lerp(c0, c1, local_t)
    return stops[-1][1]


# ---------------------------------------------------------------------------
# Harmonograph
# ---------------------------------------------------------------------------

def harmonograph_trace(
    freq_x: float, freq_y: float,
    phase_x: float, phase_y: float,
    decay_x: float, decay_y: float,
    amplitude_x: float = 330.0, amplitude_y: float = 330.0,
    duration: float = 80.0, dt: float = 0.015,
) -> list[tuple[float, float]]:
    """Generate a damped Lissajous / harmonograph trace."""
    points = []
    t = 0.0
    cx, cy = 400.0, 400.0
    while t < duration:
        x = cx + amplitude_x * math.sin(freq_x * t + phase_x) * math.exp(-decay_x * t)
        y = cy + amplitude_y * math.sin(freq_y * t + phase_y) * math.exp(-decay_y * t)
        points.append((x, y))
        t += dt
    return points


def catmull_rom_to_svg(points: list[tuple[float, float]], tension: float = 0.5) -> str:
    """Convert points to a smooth SVG path using Catmull-Rom → cubic Bezier."""
    if len(points) < 2:
        return ""

    # Start with moveTo
    path = f"M{points[0][0]:.1f},{points[0][1]:.1f}"

    for i in range(len(points) - 1):
        p0 = points[max(0, i - 1)]
        p1 = points[i]
        p2 = points[min(len(points) - 1, i + 1)]
        p3 = points[min(len(points) - 1, i + 2)]

        # Catmull-Rom to cubic Bezier control points
        cp1x = p1[0] + (p2[0] - p0[0]) / (6 * tension)
        cp1y = p1[1] + (p2[1] - p0[1]) / (6 * tension)
        cp2x = p2[0] - (p3[0] - p1[0]) / (6 * tension)
        cp2y = p2[1] - (p3[1] - p1[1]) / (6 * tension)

        path += f" C{cp1x:.1f},{cp1y:.1f} {cp2x:.1f},{cp2y:.1f} {p2[0]:.1f},{p2[1]:.1f}"

    return path


# ---------------------------------------------------------------------------
# SVG generation
# ---------------------------------------------------------------------------

WIDTH = 800
HEIGHT = 800


def generate_aurora(dark_mode: bool = True, output_path: Path | None = None) -> Path:
    suffix = "-dark" if dark_mode else ""
    out = Path(output_path or f".github/assets/img/proto-aurora{suffix}.svg")
    out.parent.mkdir(parents=True, exist_ok=True)

    seed_str = "aurora-42-200-15-8"
    h = hashlib.sha256(seed_str.encode()).hexdigest()

    def hex_slice(start: int, end: int) -> float:
        return int(h[start:end], 16) / (16 ** (end - start))

    # Generate multiple harmonograph traces
    n_traces = 8
    traces: list[tuple[list[tuple[float, float]], float]] = []  # (points, color_t)

    # Frequency ratios that produce beautiful patterns
    freq_ratios = [
        (2.01, 3.0), (3.0, 2.01), (3.0, 4.01), (5.0, 4.01),
        (2.0, 3.01), (4.01, 3.0), (5.01, 3.0), (3.01, 5.0),
    ]

    for i in range(n_traces):
        fx, fy = freq_ratios[i % len(freq_ratios)]
        # Add slight detuning from seed
        fx += hex_slice(i * 4, i * 4 + 2) * 0.04 - 0.02
        fy += hex_slice(i * 4 + 2, i * 4 + 4) * 0.04 - 0.02

        px = hex_slice(i * 3, i * 3 + 2) * math.pi * 2
        py = hex_slice(i * 3 + 1, i * 3 + 3) * math.pi * 2

        # Decay rate
        dx = 0.008 + hex_slice(i * 2, i * 2 + 2) * 0.015
        dy = 0.008 + hex_slice(i * 2 + 1, i * 2 + 3) * 0.015

        # Amplitude variation
        amp_x = 280 + hex_slice(i * 5, i * 5 + 2) * 80
        amp_y = 280 + hex_slice(i * 5 + 2, i * 5 + 4) * 80

        pts = harmonograph_trace(fx, fy, px, py, dx, dy,
                                 amplitude_x=amp_x, amplitude_y=amp_y,
                                 duration=60 + i * 10, dt=0.012)

        color_t = i / max(n_traces - 1, 1)
        traces.append((pts, color_t))

    print(f"  Generated {n_traces} harmonograph traces")

    # Build SVG
    parts: list[str] = []
    parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" '
                 f'width="{WIDTH}" height="{HEIGHT}">\n')

    if dark_mode:
        bg1, bg2 = "#020817", "#0c1e3a"
        star_color = "#ffffff"
    else:
        bg1, bg2 = "#f0f9ff", "#e0e7ff"
        star_color = "#6366f1"

    parts.append(f"""<defs>
  <!-- Aurora bloom -->
  <filter id="auroraBloom" x="-40%" y="-40%" width="180%" height="180%">
    <feGaussianBlur in="SourceGraphic" stdDeviation="2" result="b1"/>
    <feGaussianBlur in="SourceGraphic" stdDeviation="6" result="b2"/>
    <feGaussianBlur in="SourceGraphic" stdDeviation="15" result="b3"/>
    <feColorMatrix in="b3" type="matrix" result="bright3"
      values="1.3 0 0 0 0.05
              0 1.3 0 0 0.05
              0 0 1.3 0 0.05
              0 0 0 0.5 0"/>
    <feMerge>
      <feMergeNode in="bright3"/>
      <feMergeNode in="b2"/>
      <feMergeNode in="b1"/>
      <feMergeNode in="SourceGraphic"/>
    </feMerge>
  </filter>

  <!-- Chromatic aberration -->
  <filter id="chromatic" x="-5%" y="-5%" width="110%" height="110%">
    <!-- Red channel shifted right -->
    <feColorMatrix in="SourceGraphic" type="matrix" result="red"
      values="1 0 0 0 0
              0 0 0 0 0
              0 0 0 0 0
              0 0 0 1 0"/>
    <feOffset in="red" dx="1.5" dy="0" result="redShift"/>
    <!-- Blue channel shifted left -->
    <feColorMatrix in="SourceGraphic" type="matrix" result="blue"
      values="0 0 0 0 0
              0 0 0 0 0
              0 0 1 0 0
              0 0 0 1 0"/>
    <feOffset in="blue" dx="-1.5" dy="0" result="blueShift"/>
    <!-- Green stays -->
    <feColorMatrix in="SourceGraphic" type="matrix" result="green"
      values="0 0 0 0 0
              0 1 0 0 0
              0 0 0 0 0
              0 0 0 1 0"/>
    <!-- Blend: screen mode to combine -->
    <feBlend in="redShift" in2="green" mode="screen" result="rg"/>
    <feBlend in="rg" in2="blueShift" mode="screen"/>
  </filter>

  <!-- Aurora curtain turbulence -->
  <filter id="auroraCurtain" x="0" y="0" width="100%" height="100%"
          filterUnits="objectBoundingBox" primitiveUnits="userSpaceOnUse">
    <feTurbulence type="turbulence" baseFrequency="0.008 0.03"
                  numOctaves="3" seed="77" result="waves"/>
    <feColorMatrix in="waves" type="matrix" result="coloredWaves"
      values="0 0.3 0 0 0
              0.15 0.5 0 0 0.08
              0 0.2 0.4 0 0.12
              0 0 0 0.4 0"/>
  </filter>

  <!-- Star glow -->
  <filter id="starGlow" x="-100%" y="-100%" width="300%" height="300%">
    <feGaussianBlur in="SourceGraphic" stdDeviation="1" result="sg"/>
    <feMerge>
      <feMergeNode in="sg"/>
      <feMergeNode in="SourceGraphic"/>
    </feMerge>
  </filter>

  <!-- Background gradient -->
  <linearGradient id="bgGrad" x1="0%" y1="0%" x2="0%" y2="100%">
    <stop offset="0%" stop-color="{bg1}"/>
    <stop offset="60%" stop-color="{bg2}"/>
    <stop offset="100%" stop-color="{bg1}"/>
  </linearGradient>

  <!-- Vignette -->
  <radialGradient id="vignette" cx="50%" cy="50%" r="50%">
    <stop offset="60%" stop-color="black" stop-opacity="0"/>
    <stop offset="100%" stop-color="black" stop-opacity="{'0.4' if dark_mode else '0'}"/>
  </radialGradient>
</defs>
""")

    # Background
    parts.append(f'<rect width="{WIDTH}" height="{HEIGHT}" fill="url(#bgGrad)"/>\n')

    # Aurora curtain background
    if dark_mode:
        parts.append(f'<rect width="{WIDTH}" height="{HEIGHT}" filter="url(#auroraCurtain)" opacity="0.35"/>\n')
    else:
        parts.append(f'<rect width="{WIDTH}" height="{HEIGHT}" filter="url(#auroraCurtain)" opacity="0.15"/>\n')

    # Starfield
    rng = random.Random(int(h[28:36], 16))
    parts.append('<g id="starfield">\n')
    for _ in range(100):
        sx = rng.uniform(5, WIDTH - 5)
        sy = rng.uniform(5, HEIGHT - 5)
        sr = round(rng.uniform(0.3, 1.1), 1)
        opacity = round(rng.uniform(0.1, 0.5), 2)
        parts.append(f'<circle cx="{sx:.0f}" cy="{sy:.0f}" r="{sr}" '
                     f'fill="{star_color}" opacity="{opacity}"/>\n')
    parts.append('</g>\n')

    # Harmonograph traces with bloom
    parts.append('<g id="traces" filter="url(#auroraBloom)">\n')

    for trace_idx, (pts, color_t) in enumerate(traces):
        if len(pts) < 10:
            continue

        # Subsample for smoother rendering (every 3rd point)
        subsampled = pts[::3]
        svg_path = catmull_rom_to_svg(subsampled)
        if not svg_path:
            continue

        color = aurora_color(color_t, dark_mode)

        # Compute approximate path length
        total_len = 0.0
        for j in range(1, len(subsampled)):
            dx = subsampled[j][0] - subsampled[j-1][0]
            dy = subsampled[j][1] - subsampled[j-1][1]
            total_len += math.sqrt(dx*dx + dy*dy)

        # Stroke width varies by trace
        sw = round(1.0 + (1 - color_t) * 1.5, 1)
        opacity = round(0.3 + (1 - abs(color_t - 0.5) * 2) * 0.4, 2)

        parts.append(f'<path d="{svg_path}" fill="none" stroke="{color}" '
                     f'stroke-width="{sw}" opacity="{opacity}" '
                     f'stroke-linecap="round" stroke-linejoin="round"/>\n')

    parts.append('</g>\n')

    # Chromatic aberration layer (duplicate of traces, very faint)
    parts.append('<g id="chromatic" filter="url(#chromatic)" opacity="0.25">\n')
    for trace_idx, (pts, color_t) in enumerate(traces):
        if len(pts) < 10:
            continue
        subsampled = pts[::5]  # Sparser for the aberration layer
        svg_path = catmull_rom_to_svg(subsampled)
        if not svg_path:
            continue
        color = aurora_color(color_t, dark_mode)
        parts.append(f'<path d="{svg_path}" fill="none" stroke="{color}" '
                     f'stroke-width="2" opacity="0.4" stroke-linecap="round"/>\n')
    parts.append('</g>\n')

    # Vignette
    if dark_mode:
        parts.append(f'<rect width="{WIDTH}" height="{HEIGHT}" fill="url(#vignette)"/>\n')

    parts.append('</svg>\n')

    svg_text = "".join(parts)
    out.write_text(svg_text, encoding="utf-8")

    size_kb = len(svg_text.encode("utf-8")) / 1024
    print(f"Aurora {'dark' if dark_mode else 'light'}: "
          f"{n_traces} traces, {size_kb:.0f} KB → {out}")
    return out


if __name__ == "__main__":
    generate_aurora(dark_mode=True)
    generate_aurora(dark_mode=False)
    print("Done! Open the SVGs in a browser to review.")
