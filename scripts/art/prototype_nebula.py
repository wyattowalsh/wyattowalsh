"""
Nebula Genesis — Prototype
~~~~~~~~~~~~~~~~~~~~~~~~~~
Clifford attractor rendered as luminous particles with:
- 5000+ smooth circles (not grid rectangles)
- 3-pass cinematic bloom SVG filter
- Nebula feTurbulence background
- Multi-layer depth (far blur, mid, foreground hot spots)
- OKLCH perceptually uniform color mapping
- Starfield with twinkle
"""
from __future__ import annotations

import hashlib
import math
import random
from pathlib import Path

import numpy as np

# ---------------------------------------------------------------------------
# OKLCH color math (pure Python, no deps)
# ---------------------------------------------------------------------------

def _srgb_to_linear(c: float) -> float:
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

def _linear_to_srgb(c: float) -> float:
    return 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055

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

def density_color(val: float, hue_shift: float = 0.0, dark_mode: bool = True) -> str:
    """Map normalized density [0,1] to OKLCH color.

    Palette: deep indigo → violet → teal → amber → white-gold
    """
    # Multi-stop gradient
    stops = [
        (0.0,  "#0f0a2e"),   # Deep void
        (0.15, "#2d1b69"),   # Indigo
        (0.30, "#581c87"),   # Purple
        (0.45, "#0e7490"),   # Teal
        (0.60, "#06b6d4"),   # Cyan
        (0.75, "#d97706"),   # Amber
        (0.88, "#fbbf24"),   # Gold
        (1.0,  "#fef3c7"),   # White-gold
    ]

    if not dark_mode:
        stops = [
            (0.0,  "#c4b5fd"),   # Light violet
            (0.15, "#8b5cf6"),   # Purple
            (0.30, "#6d28d9"),   # Deep purple
            (0.45, "#0891b2"),   # Teal
            (0.60, "#0e7490"),   # Deep teal
            (0.75, "#b45309"),   # Dark amber
            (0.88, "#92400e"),   # Deep amber
            (1.0,  "#451a03"),   # Deep brown
        ]

    # Find surrounding stops
    for i in range(len(stops) - 1):
        t0, c0 = stops[i]
        t1, c1 = stops[i + 1]
        if t0 <= val <= t1:
            local_t = (val - t0) / (t1 - t0)
            return oklch_lerp(c0, c1, local_t)

    return stops[-1][1]


# ---------------------------------------------------------------------------
# Clifford attractor
# ---------------------------------------------------------------------------

def compute_clifford(
    a: float, b: float, c: float, d: float,
    iterations: int, grid_size: int,
) -> tuple[np.ndarray, list[tuple[float, float]]]:
    """Run Clifford attractor, return density grid and raw point samples."""
    x, y = 0.1, 0.1
    density = np.zeros((grid_size, grid_size), dtype=np.float64)
    coord_min, coord_max = -3.0, 3.0
    coord_range = coord_max - coord_min

    # Sample some points for particle rendering
    sample_interval = max(1, iterations // 6000)
    sampled_points: list[tuple[float, float, int, int]] = []  # (x_px, y_px, gx, gy)

    width, height = 800, 800

    for i in range(iterations):
        x_new = math.sin(a * y) + c * math.cos(a * x)
        y_new = math.sin(b * x) + d * math.cos(b * y)
        x, y = x_new, y_new

        gx = int((x - coord_min) / coord_range * (grid_size - 1))
        gy = int((y - coord_min) / coord_range * (grid_size - 1))

        if 0 <= gx < grid_size and 0 <= gy < grid_size:
            density[gy, gx] += 1.0

            if i % sample_interval == 0:
                px = (x - coord_min) / coord_range * width
                py = (y - coord_min) / coord_range * height
                sampled_points.append((px, py, gx, gy))

    return density, sampled_points


# ---------------------------------------------------------------------------
# SVG generation
# ---------------------------------------------------------------------------

WIDTH = 800
HEIGHT = 800

def _svg_filters_dark() -> str:
    return """<defs>
  <!-- 3-pass cinematic bloom -->
  <filter id="bloom" x="-50%" y="-50%" width="200%" height="200%">
    <feGaussianBlur in="SourceGraphic" stdDeviation="2" result="b1"/>
    <feGaussianBlur in="SourceGraphic" stdDeviation="6" result="b2"/>
    <feGaussianBlur in="SourceGraphic" stdDeviation="14" result="b3"/>
    <feColorMatrix in="b3" type="matrix" result="bright3"
      values="1.3 0 0 0 0.06
              0 1.3 0 0 0.06
              0 0 1.3 0 0.06
              0 0 0 0.5 0"/>
    <feColorMatrix in="b2" type="matrix" result="bright2"
      values="1.15 0 0 0 0.03
              0 1.15 0 0 0.03
              0 0 1.15 0 0.03
              0 0 0 0.7 0"/>
    <feMerge>
      <feMergeNode in="bright3"/>
      <feMergeNode in="bright2"/>
      <feMergeNode in="b1"/>
      <feMergeNode in="SourceGraphic"/>
    </feMerge>
  </filter>

  <!-- Hot glow for densest particles -->
  <filter id="hotGlow" x="-60%" y="-60%" width="220%" height="220%">
    <feGaussianBlur in="SourceGraphic" stdDeviation="4" result="glow"/>
    <feColorMatrix in="glow" type="matrix" result="warmGlow"
      values="1.4 0.1 0 0 0.08
              0.1 1.2 0 0 0.04
              0 0 1.0 0 0.02
              0 0 0 0.8 0"/>
    <feBlend in="SourceGraphic" in2="warmGlow" mode="screen"/>
  </filter>

  <!-- Nebula background texture -->
  <filter id="nebula" x="0" y="0" width="100%" height="100%"
          filterUnits="objectBoundingBox" primitiveUnits="userSpaceOnUse">
    <feTurbulence type="fractalNoise" baseFrequency="0.003 0.004"
                  numOctaves="5" seed="42" result="clouds1"/>
    <feTurbulence type="fractalNoise" baseFrequency="0.012 0.009"
                  numOctaves="3" seed="137" result="clouds2"/>
    <feColorMatrix in="clouds1" type="matrix" result="tinted1"
      values="0.15 0 0 0 0.02
              0 0.06 0 0 0.01
              0 0 0.30 0 0.06
              0 0 0 0.65 0"/>
    <feColorMatrix in="clouds2" type="matrix" result="tinted2"
      values="0 0 0 0 0
              0 0.18 0.05 0 0.03
              0 0.05 0.22 0 0.06
              0 0 0 0.35 0"/>
    <feBlend in="tinted1" in2="tinted2" mode="screen"/>
  </filter>

  <!-- Depth-of-field for background layer -->
  <filter id="dofFar" x="-10%" y="-10%" width="120%" height="120%">
    <feGaussianBlur in="SourceGraphic" stdDeviation="2.5"/>
    <feColorMatrix type="saturate" values="0.65"/>
  </filter>

  <!-- Subtle star glow -->
  <filter id="starGlow" x="-100%" y="-100%" width="300%" height="300%">
    <feGaussianBlur in="SourceGraphic" stdDeviation="1.5" result="sg"/>
    <feMerge>
      <feMergeNode in="sg"/>
      <feMergeNode in="SourceGraphic"/>
    </feMerge>
  </filter>

  <!-- Background radial gradient -->
  <radialGradient id="bgGrad" cx="50%" cy="50%" r="70%">
    <stop offset="0%" stop-color="#0a0515"/>
    <stop offset="50%" stop-color="#070310"/>
    <stop offset="100%" stop-color="#020108"/>
  </radialGradient>

  <!-- Vignette gradient -->
  <radialGradient id="vignette" cx="50%" cy="50%" r="50%">
    <stop offset="60%" stop-color="black" stop-opacity="0"/>
    <stop offset="100%" stop-color="black" stop-opacity="0.5"/>
  </radialGradient>
</defs>
"""


def _svg_filters_light() -> str:
    return """<defs>
  <!-- 3-pass cinematic bloom (light mode) -->
  <filter id="bloom" x="-50%" y="-50%" width="200%" height="200%">
    <feGaussianBlur in="SourceGraphic" stdDeviation="2" result="b1"/>
    <feGaussianBlur in="SourceGraphic" stdDeviation="5" result="b2"/>
    <feGaussianBlur in="SourceGraphic" stdDeviation="12" result="b3"/>
    <feColorMatrix in="b3" type="matrix" result="bright3"
      values="1.0 0 0 0 0
              0 1.0 0 0 0
              0 0 1.0 0 0
              0 0 0 0.4 0"/>
    <feMerge>
      <feMergeNode in="bright3"/>
      <feMergeNode in="b2"/>
      <feMergeNode in="b1"/>
      <feMergeNode in="SourceGraphic"/>
    </feMerge>
  </filter>

  <!-- Hot glow for densest particles (light mode - darker, more saturated) -->
  <filter id="hotGlow" x="-60%" y="-60%" width="220%" height="220%">
    <feGaussianBlur in="SourceGraphic" stdDeviation="3" result="glow"/>
    <feColorMatrix in="glow" type="matrix" result="warmGlow"
      values="1.2 0 0 0 0
              0 1.0 0 0 0
              0 0 0.9 0 0
              0 0 0 0.6 0"/>
    <feBlend in="SourceGraphic" in2="warmGlow" mode="multiply"/>
  </filter>

  <!-- Nebula background (light mode - pale, ethereal) -->
  <filter id="nebula" x="0" y="0" width="100%" height="100%"
          filterUnits="objectBoundingBox" primitiveUnits="userSpaceOnUse">
    <feTurbulence type="fractalNoise" baseFrequency="0.004 0.005"
                  numOctaves="4" seed="42" result="clouds1"/>
    <feColorMatrix in="clouds1" type="matrix" result="tinted1"
      values="0.06 0 0.04 0 0.90
              0 0.04 0.06 0 0.88
              0.04 0 0.10 0 0.92
              0 0 0 0.25 0"/>
  </filter>

  <!-- Depth-of-field for background -->
  <filter id="dofFar" x="-10%" y="-10%" width="120%" height="120%">
    <feGaussianBlur in="SourceGraphic" stdDeviation="2"/>
    <feColorMatrix type="saturate" values="0.7"/>
  </filter>

  <!-- Background radial gradient (light) -->
  <radialGradient id="bgGrad" cx="50%" cy="50%" r="70%">
    <stop offset="0%" stop-color="#f5f0ff"/>
    <stop offset="50%" stop-color="#ede9fe"/>
    <stop offset="100%" stop-color="#e8e0f0"/>
  </radialGradient>

  <!-- Vignette -->
  <radialGradient id="vignette" cx="50%" cy="50%" r="50%">
    <stop offset="70%" stop-color="white" stop-opacity="0"/>
    <stop offset="100%" stop-color="#c4b5fd" stop-opacity="0.15"/>
  </radialGradient>
</defs>
"""


def generate_nebula(dark_mode: bool = True, output_path: Path | None = None) -> Path:
    suffix = "-dark" if dark_mode else ""
    out = Path(output_path or f".github/assets/img/proto-nebula{suffix}.svg")
    out.parent.mkdir(parents=True, exist_ok=True)

    # Seed from mock metrics
    seed_str = "42-15-8-3-22-octocat-contributor"
    h = hashlib.sha256(seed_str.encode()).hexdigest()

    def hex_slice(start: int, end: int) -> float:
        return int(h[start:end], 16) / (16 ** (end - start))

    # Clifford parameters
    a = 0.8 + hex_slice(0, 4) * 1.4
    b = 0.8 + hex_slice(4, 8) * 1.4
    c = -2.0 + hex_slice(8, 12) * 4.0
    d = -2.0 + hex_slice(12, 16) * 4.0
    hue_shift = hex_slice(16, 20)

    print(f"Clifford params: a={a:.3f} b={b:.3f} c={c:.3f} d={d:.3f}")

    # Compute attractor
    grid_sz = 200
    iters = 1_500_000
    density, sampled = compute_clifford(a, b, c, d, iters, grid_sz)

    max_density = density.max()
    if max_density <= 0:
        out.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" width="{WIDTH}" height="{HEIGHT}"><rect width="{WIDTH}" height="{HEIGHT}" fill="black"/></svg>')
        return out

    norm = np.log1p(density) / np.log1p(max_density)

    # Build SVG
    parts: list[str] = []
    parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" width="{WIDTH}" height="{HEIGHT}">\n')

    # Filters and defs
    parts.append(_svg_filters_dark() if dark_mode else _svg_filters_light())

    # Background
    parts.append(f'<rect width="{WIDTH}" height="{HEIGHT}" fill="url(#bgGrad)"/>\n')

    # Nebula layer
    parts.append(f'<rect width="{WIDTH}" height="{HEIGHT}" filter="url(#nebula)" opacity="0.6"/>\n')

    # Starfield layer
    rng = random.Random(int(h[28:36], 16))
    star_color = "#ffffff" if dark_mode else "#6366f1"
    parts.append('<g id="starfield">\n')
    for _ in range(120):
        sx = rng.uniform(5, WIDTH - 5)
        sy = rng.uniform(5, HEIGHT - 5)
        sr = round(rng.uniform(0.3, 1.2), 1)
        opacity = round(rng.uniform(0.1, 0.6), 2)
        parts.append(
            f'<circle cx="{sx:.0f}" cy="{sy:.0f}" r="{sr}" '
            f'fill="{star_color}" opacity="{opacity}"/>\n'
        )
    parts.append('</g>\n')

    # --- Attractor particles ---
    # Layer 1: Background particles (all, with depth-of-field blur)
    parts.append('<g id="attractorFar" filter="url(#dofFar)" opacity="0.5">\n')

    pixel_w = WIDTH / grid_sz
    pixel_h = HEIGHT / grid_sz

    # Render density as circles at grid centers (for background wash)
    threshold = 0.04
    bg_count = 0
    for row in range(grid_sz):
        for col in range(grid_sz):
            val = float(norm[row, col])
            if val < threshold:
                continue
            cx = round(col * pixel_w + pixel_w / 2, 1)
            cy = round(row * pixel_h + pixel_h / 2, 1)
            r = round(0.8 + val * 2.5, 1)
            alpha = round(val * 0.4, 2)
            color = density_color(val * 0.6, hue_shift, dark_mode)  # Shift toward cooler for bg
            parts.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{color}" opacity="{alpha}"/>\n')
            bg_count += 1
    parts.append('</g>\n')

    # Layer 2: Mid-ground particles (sampled points, bloom)
    parts.append('<g id="attractorMid" filter="url(#bloom)">\n')
    mid_count = 0
    for px, py, gx, gy in sampled:
        if 0 <= gy < grid_sz and 0 <= gx < grid_sz:
            val = float(norm[gy, gx])
        else:
            continue
        if val < 0.08:
            continue

        r = round(0.5 + val * 2.0, 1)
        alpha = round(0.3 + val * 0.55, 2)
        color = density_color(val, hue_shift, dark_mode)
        parts.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="{r}" fill="{color}" opacity="{alpha}"/>\n')
        mid_count += 1
    parts.append('</g>\n')

    # Layer 3: Hot spots (high density only, with hot glow)
    parts.append('<g id="attractorHot" filter="url(#hotGlow)">\n')
    hot_count = 0
    hot_threshold = 0.65
    for px, py, gx, gy in sampled:
        if 0 <= gy < grid_sz and 0 <= gx < grid_sz:
            val = float(norm[gy, gx])
        else:
            continue
        if val < hot_threshold:
            continue

        r = round(1.0 + (val - hot_threshold) / (1.0 - hot_threshold) * 3.0, 1)
        alpha = round(0.6 + val * 0.35, 2)
        color = density_color(val, hue_shift, dark_mode)
        parts.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="{r}" fill="{color}" opacity="{alpha}"/>\n')
        hot_count += 1
    parts.append('</g>\n')

    # Vignette overlay
    parts.append(f'<rect width="{WIDTH}" height="{HEIGHT}" fill="url(#vignette)"/>\n')

    parts.append('</svg>\n')

    svg_text = "".join(parts)
    out.write_text(svg_text, encoding="utf-8")

    size_kb = len(svg_text.encode("utf-8")) / 1024
    print(f"Nebula Genesis {'dark' if dark_mode else 'light'}: "
          f"{bg_count} bg + {mid_count} mid + {hot_count} hot particles, "
          f"{size_kb:.0f} KB → {out}")
    return out


if __name__ == "__main__":
    generate_nebula(dark_mode=True)
    generate_nebula(dark_mode=False)
    print("Done! Open the SVGs in a browser to review.")
