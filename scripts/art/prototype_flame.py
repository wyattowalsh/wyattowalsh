"""
Fractal Flame Garden — Prototype
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
IFS chaos game with nonlinear variations producing Electric Sheep-style
alien flower/flame structures.

- 8000+ points via weighted random transform selection
- 6 nonlinear variations: sinusoidal, spherical, swirl, horseshoe, polar, handkerchief
- Flame palette: black → deep red → orange → yellow → white
- 2-tier bloom filter (subtle all + intense brightest 10%)
- Optional symmetry
- Density grid for background glow
"""
from __future__ import annotations

import hashlib
import math
import random
from pathlib import Path

import numpy as np

# ---------------------------------------------------------------------------
# OKLCH color math (same as nebula prototype)
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


# ---------------------------------------------------------------------------
# Flame palette
# ---------------------------------------------------------------------------

def flame_color(color_idx: float, dark_mode: bool = True) -> str:
    """Map color index [0, 1] to flame palette via OKLCH."""
    if dark_mode:
        stops = [
            (0.0,  "#1a0000"),  # Near black red
            (0.12, "#4a0000"),  # Deep crimson
            (0.25, "#8b0000"),  # Dark red
            (0.38, "#cc2200"),  # Red
            (0.50, "#e65100"),  # Deep orange
            (0.62, "#f57c00"),  # Orange
            (0.75, "#ffab00"),  # Amber
            (0.87, "#ffd54f"),  # Yellow
            (1.0,  "#fff8e1"),  # Near white
        ]
    else:
        stops = [
            (0.0,  "#fce4ec"),  # Lightest pink
            (0.15, "#ef9a9a"),  # Light red
            (0.30, "#e57373"),  # Red
            (0.45, "#ef5350"),  # Deep red
            (0.60, "#d84315"),  # Deep orange
            (0.75, "#bf360c"),  # Brown-red
            (0.90, "#4e342e"),  # Dark brown
            (1.0,  "#1a0000"),  # Near black
        ]

    for i in range(len(stops) - 1):
        t0, c0 = stops[i]
        t1, c1 = stops[i + 1]
        if t0 <= color_idx <= t1:
            local_t = (color_idx - t0) / (t1 - t0)
            return oklch_lerp(c0, c1, local_t)
    return stops[-1][1]


# ---------------------------------------------------------------------------
# IFS Nonlinear Variations
# ---------------------------------------------------------------------------

def _var_linear(x: float, y: float) -> tuple[float, float]:
    return x, y

def _var_sinusoidal(x: float, y: float) -> tuple[float, float]:
    return math.sin(x), math.sin(y)

def _var_spherical(x: float, y: float) -> tuple[float, float]:
    r2 = x * x + y * y + 1e-10
    return x / r2, y / r2

def _var_swirl(x: float, y: float) -> tuple[float, float]:
    r2 = x * x + y * y
    sr, cr = math.sin(r2), math.cos(r2)
    return x * sr - y * cr, x * cr + y * sr

def _var_horseshoe(x: float, y: float) -> tuple[float, float]:
    r = math.sqrt(x * x + y * y) + 1e-10
    return (x - y) * (x + y) / r, 2 * x * y / r

def _var_polar(x: float, y: float) -> tuple[float, float]:
    r = math.sqrt(x * x + y * y)
    theta = math.atan2(y, x)
    return theta / math.pi, r - 1

def _var_handkerchief(x: float, y: float) -> tuple[float, float]:
    r = math.sqrt(x * x + y * y)
    theta = math.atan2(y, x)
    return r * math.sin(theta + r), r * math.cos(theta - r)

VARIATIONS = {
    "linear": _var_linear,
    "sinusoidal": _var_sinusoidal,
    "spherical": _var_spherical,
    "swirl": _var_swirl,
    "horseshoe": _var_horseshoe,
    "polar": _var_polar,
    "handkerchief": _var_handkerchief,
}

VAR_NAMES = list(VARIATIONS.keys())


# ---------------------------------------------------------------------------
# Fractal Flame computation
# ---------------------------------------------------------------------------

def compute_flame(
    transforms: list[dict],
    num_points: int = 10000,
    warmup: int = 30,
    symmetry: int = 1,
    seed: int = 42,
) -> list[dict]:
    """Run the chaos game with nonlinear variations.

    Each transform: {a, b, c, d, e, f, variation, color_idx, weight}

    Returns list of {x, y, color_idx} points.
    """
    rng = np.random.default_rng(seed)
    weights = np.array([t["weight"] for t in transforms])
    weights /= weights.sum()

    x, y = float(rng.uniform(-0.5, 0.5)), float(rng.uniform(-0.5, 0.5))
    color_idx = 0.5
    points: list[dict] = []

    for i in range(warmup + num_points):
        # Select transform
        ti = int(rng.choice(len(transforms), p=weights))
        t = transforms[ti]

        # Affine
        x_new = t["a"] * x + t["b"] * y + t["e"]
        y_new = t["c"] * x + t["d"] * y + t["f"]

        # Variation
        var_fn = VARIATIONS[t["variation"]]
        x_new, y_new = var_fn(x_new, y_new)

        # Color blending
        color_idx = (color_idx + t["color_idx"]) * 0.5

        x, y = x_new, y_new

        if i >= warmup and math.isfinite(x) and math.isfinite(y):
            points.append({"x": x, "y": y, "color_idx": color_idx})

            # Apply symmetry
            if symmetry >= 2:
                for s in range(1, symmetry):
                    angle = 2 * math.pi * s / symmetry
                    rx = x * math.cos(angle) - y * math.sin(angle)
                    ry = x * math.sin(angle) + y * math.cos(angle)
                    points.append({"x": rx, "y": ry, "color_idx": color_idx})

    return points


def derive_transforms(h: str, n_transforms: int) -> list[dict]:
    """Derive IFS transforms from a hash string."""
    transforms = []
    for i in range(n_transforms):
        offset = i * 14  # 14 hex chars per transform
        s = h[offset:offset + 14]
        if len(s) < 14:
            s = h[:14]  # wrap around

        # Affine coefficients in [-1.2, 1.2]
        a = -1.2 + int(s[0:2], 16) / 255 * 2.4
        b = -1.2 + int(s[2:4], 16) / 255 * 2.4
        c = -1.2 + int(s[4:6], 16) / 255 * 2.4
        d = -1.2 + int(s[6:8], 16) / 255 * 2.4
        e = -0.5 + int(s[8:10], 16) / 255 * 1.0
        f = -0.5 + int(s[10:12], 16) / 255 * 1.0

        # Variation type
        var_idx = int(s[12], 16) % len(VAR_NAMES)
        variation = VAR_NAMES[var_idx]

        # Color index
        color_idx = int(s[13], 16) / 15.0

        # Weight (all equal for now)
        weight = 1.0

        transforms.append({
            "a": a, "b": b, "c": c, "d": d, "e": e, "f": f,
            "variation": variation,
            "color_idx": color_idx,
            "weight": weight,
        })

    return transforms


# ---------------------------------------------------------------------------
# SVG generation
# ---------------------------------------------------------------------------

WIDTH = 800
HEIGHT = 800


def generate_flame(dark_mode: bool = True, output_path: Path | None = None) -> Path:
    suffix = "-dark" if dark_mode else ""
    out = Path(output_path or f".github/assets/img/proto-flame{suffix}.svg")
    out.parent.mkdir(parents=True, exist_ok=True)

    # Seed
    seed_str = "flame-42-15-8-3-22"
    h = hashlib.sha256(seed_str.encode()).hexdigest()
    h2 = hashlib.sha256((seed_str + "-extra").encode()).hexdigest()
    full_hash = h + h2  # 128 hex chars

    # Derive transforms (4 transforms)
    n_transforms = 4
    transforms = derive_transforms(full_hash, n_transforms)

    for i, t in enumerate(transforms):
        print(f"  Transform {i}: var={t['variation']}, a={t['a']:.2f} b={t['b']:.2f} "
              f"c={t['c']:.2f} d={t['d']:.2f} e={t['e']:.2f} f={t['f']:.2f} "
              f"color={t['color_idx']:.2f}")

    # Symmetry
    symmetry = 3  # 3-fold for this prototype
    num_raw = 12000
    points = compute_flame(transforms, num_points=num_raw, symmetry=symmetry,
                           seed=int(h[48:56], 16) % (2**31))

    print(f"  Generated {len(points)} points (with {symmetry}-fold symmetry)")

    # Filter out extreme outliers
    if points:
        xs = [p["x"] for p in points if math.isfinite(p["x"])]
        ys = [p["y"] for p in points if math.isfinite(p["y"])]
        if xs and ys:
            # Use percentile-based bounds
            xs_arr = np.array(xs)
            ys_arr = np.array(ys)
            x_lo, x_hi = float(np.percentile(xs_arr, 1)), float(np.percentile(xs_arr, 99))
            y_lo, y_hi = float(np.percentile(ys_arr, 1)), float(np.percentile(ys_arr, 99))

            # Add padding
            x_range = max(x_hi - x_lo, 0.1)
            y_range = max(y_hi - y_lo, 0.1)
            x_lo -= x_range * 0.05
            x_hi += x_range * 0.05
            y_lo -= y_range * 0.05
            y_hi += y_range * 0.05

            # Make square (use larger dimension)
            max_range = max(x_hi - x_lo, y_hi - y_lo)
            cx = (x_lo + x_hi) / 2
            cy = (y_lo + y_hi) / 2
            x_lo = cx - max_range / 2
            x_hi = cx + max_range / 2
            y_lo = cy - max_range / 2
            y_hi = cy + max_range / 2
        else:
            x_lo, x_hi, y_lo, y_hi = -2, 2, -2, 2
    else:
        x_lo, x_hi, y_lo, y_hi = -2, 2, -2, 2

    # Map points to canvas coords
    margin = 40
    eff_w = WIDTH - 2 * margin
    eff_h = HEIGHT - 2 * margin

    mapped: list[dict] = []
    for p in points:
        px = p["x"]
        py = p["y"]
        if not (math.isfinite(px) and math.isfinite(py)):
            continue
        if px < x_lo or px > x_hi or py < y_lo or py > y_hi:
            continue
        sx = margin + (px - x_lo) / (x_hi - x_lo) * eff_w
        sy = margin + (py - y_lo) / (y_hi - y_lo) * eff_h
        mapped.append({"x": sx, "y": sy, "color_idx": p["color_idx"]})

    print(f"  Mapped {len(mapped)} points to canvas")

    # Compute density grid for background glow
    grid_sz = 100
    density = np.zeros((grid_sz, grid_sz), dtype=np.float64)
    for p in mapped:
        gx = int((p["x"] - margin) / eff_w * (grid_sz - 1))
        gy = int((p["y"] - margin) / eff_h * (grid_sz - 1))
        if 0 <= gx < grid_sz and 0 <= gy < grid_sz:
            density[gy, gx] += 1.0
    max_d = density.max()
    if max_d > 0:
        norm_density = np.log1p(density) / np.log1p(max_d)
    else:
        norm_density = density

    # Build SVG
    parts: list[str] = []
    parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" '
                 f'width="{WIDTH}" height="{HEIGHT}">\n')

    bg = "#050005" if dark_mode else "#faf5f0"
    bg2 = "#150818" if dark_mode else "#f0e8e0"

    parts.append(f"""<defs>
  <!-- Bloom filter -->
  <filter id="bloom" x="-50%" y="-50%" width="200%" height="200%">
    <feGaussianBlur in="SourceGraphic" stdDeviation="2" result="b1"/>
    <feGaussianBlur in="SourceGraphic" stdDeviation="5" result="b2"/>
    <feGaussianBlur in="SourceGraphic" stdDeviation="12" result="b3"/>
    <feColorMatrix in="b3" type="matrix" result="bright3"
      values="1.2 0 0 0 0.04
              0 1.2 0 0 0.04
              0 0 1.2 0 0.04
              0 0 0 0.45 0"/>
    <feMerge>
      <feMergeNode in="bright3"/>
      <feMergeNode in="b2"/>
      <feMergeNode in="b1"/>
      <feMergeNode in="SourceGraphic"/>
    </feMerge>
  </filter>

  <!-- Intense glow for brightest points -->
  <filter id="hotBloom" x="-80%" y="-80%" width="260%" height="260%">
    <feGaussianBlur in="SourceGraphic" stdDeviation="3" result="hb1"/>
    <feGaussianBlur in="SourceGraphic" stdDeviation="8" result="hb2"/>
    <feColorMatrix in="hb2" type="matrix" result="warm"
      values="1.5 0.2 0 0 0.1
              0.1 1.3 0 0 0.05
              0 0 1.0 0 0
              0 0 0 0.6 0"/>
    <feBlend in="SourceGraphic" in2="warm" mode="screen" result="screened"/>
    <feMerge>
      <feMergeNode in="hb1"/>
      <feMergeNode in="screened"/>
    </feMerge>
  </filter>

  <!-- Background warmth -->
  <radialGradient id="bgGrad" cx="50%" cy="50%" r="60%">
    <stop offset="0%" stop-color="{bg2}"/>
    <stop offset="100%" stop-color="{bg}"/>
  </radialGradient>

  <!-- Vignette -->
  <radialGradient id="vignette" cx="50%" cy="50%" r="50%">
    <stop offset="55%" stop-color="black" stop-opacity="0"/>
    <stop offset="100%" stop-color="black" stop-opacity="{'0.6' if dark_mode else '0'}"/>
  </radialGradient>
</defs>
""")

    # Background
    parts.append(f'<rect width="{WIDTH}" height="{HEIGHT}" fill="url(#bgGrad)"/>\n')

    # Density glow layer (background wash)
    pixel_w = eff_w / grid_sz
    pixel_h = eff_h / grid_sz
    glow_threshold = 0.15
    parts.append('<g id="densityGlow" opacity="0.4">\n')
    for row in range(grid_sz):
        for col in range(grid_sz):
            val = float(norm_density[row, col])
            if val < glow_threshold:
                continue
            cx = margin + col * pixel_w + pixel_w / 2
            cy = margin + row * pixel_h + pixel_h / 2
            r = round(pixel_w * 0.8 + val * pixel_w * 1.5, 1)
            color = flame_color(0.3 + val * 0.4, dark_mode)
            alpha = round(val * 0.35, 2)
            parts.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r}" '
                         f'fill="{color}" opacity="{alpha}"/>\n')
    parts.append('</g>\n')

    # Main particle layer with bloom
    parts.append('<g id="particles" filter="url(#bloom)">\n')
    for p in mapped:
        color = flame_color(p["color_idx"], dark_mode)
        r = round(0.4 + p["color_idx"] * 1.2, 1)
        alpha = round(0.5 + p["color_idx"] * 0.4, 2)
        parts.append(f'<circle cx="{p["x"]:.1f}" cy="{p["y"]:.1f}" r="{r}" '
                     f'fill="{color}" opacity="{alpha}"/>\n')
    parts.append('</g>\n')

    # Hot spots (brightest 15% by color index)
    hot_threshold = 0.7
    hot_points = [p for p in mapped if p["color_idx"] > hot_threshold]
    if hot_points:
        parts.append('<g id="hotSpots" filter="url(#hotBloom)">\n')
        for p in hot_points:
            color = flame_color(p["color_idx"], dark_mode)
            r = round(0.8 + (p["color_idx"] - hot_threshold) * 3.0, 1)
            parts.append(f'<circle cx="{p["x"]:.1f}" cy="{p["y"]:.1f}" r="{r}" '
                         f'fill="{color}" opacity="0.85"/>\n')
        parts.append('</g>\n')

    # Vignette
    if dark_mode:
        parts.append(f'<rect width="{WIDTH}" height="{HEIGHT}" fill="url(#vignette)"/>\n')

    parts.append('</svg>\n')

    svg_text = "".join(parts)
    out.write_text(svg_text, encoding="utf-8")

    size_kb = len(svg_text.encode("utf-8")) / 1024
    print(f"Fractal Flame {'dark' if dark_mode else 'light'}: "
          f"{len(mapped)} particles, {len(hot_points)} hot spots, "
          f"{size_kb:.0f} KB → {out}")
    return out


if __name__ == "__main__":
    generate_flame(dark_mode=True)
    generate_flame(dark_mode=False)
    print("Done! Open the SVGs in a browser to review.")
