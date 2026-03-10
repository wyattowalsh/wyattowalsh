"""
Generative Art Prototypes v3 — Metric-Driven Variations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Shows how different GitHub profiles produce different artwork.
Each mock profile reshapes the mathematical parameters, producing
unique patterns from the same underlying algorithms.

Generates a grid comparison image showing 4 profiles x 4 art types.
"""
from __future__ import annotations

import hashlib
import math
from pathlib import Path

import numpy as np

WIDTH = 800
HEIGHT = 800
CX = WIDTH / 2
CY = HEIGHT / 2

# ---------------------------------------------------------------------------
# Mock GitHub profiles — different metric fingerprints
# ---------------------------------------------------------------------------

PROFILES = {
    "wyatt": {
        "label": "wyattowalsh",
        "stars": 42, "forks": 12, "watchers": 8,
        "followers": 85, "following": 60,
        "public_repos": 35, "orgs_count": 3,
        "contributions_last_year": 1200, "total_commits": 4800,
        "open_issues_count": 5, "network_count": 18,
    },
    "prolific": {
        "label": "Prolific OSS",
        "stars": 5200, "forks": 890, "watchers": 340,
        "followers": 12000, "following": 150,
        "public_repos": 180, "orgs_count": 8,
        "contributions_last_year": 3800, "total_commits": 42000,
        "open_issues_count": 120, "network_count": 2400,
    },
    "newcomer": {
        "label": "New Developer",
        "stars": 3, "forks": 1, "watchers": 2,
        "followers": 8, "following": 45,
        "public_repos": 6, "orgs_count": 1,
        "contributions_last_year": 180, "total_commits": 320,
        "open_issues_count": 2, "network_count": 3,
    },
    "researcher": {
        "label": "ML Researcher",
        "stars": 820, "forks": 210, "watchers": 95,
        "followers": 2400, "following": 30,
        "public_repos": 22, "orgs_count": 4,
        "contributions_last_year": 650, "total_commits": 8900,
        "open_issues_count": 35, "network_count": 480,
    },
}


# ---------------------------------------------------------------------------
# Seed utilities
# ---------------------------------------------------------------------------

def _seed_hash(metrics: dict) -> str:
    """SHA-256 digest from metrics dict — deterministic."""
    seed_str = "-".join(str(metrics.get(k, 0)) for k in sorted(metrics.keys()) if k != "label")
    return hashlib.sha256(seed_str.encode()).hexdigest()


def _hex_float(h: str, start: int, end: int) -> float:
    """Extract float [0, 1) from hex digest slice."""
    return int(h[start:end], 16) / (16 ** (end - start))


# ---------------------------------------------------------------------------
# Color utilities (OKLCH)
# ---------------------------------------------------------------------------

def _linear_to_srgb(c: float) -> float:
    return 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055


def oklch_to_hex(L: float, C: float, H: float) -> str:
    a = C * math.cos(math.radians(H))
    b = C * math.sin(math.radians(H))
    l_c = L + 0.3963377774 * a + 0.2158037573 * b
    m_c = L - 0.1055613458 * a - 0.0638541728 * b
    s_c = L - 0.0894841775 * a - 1.2914855480 * b
    l_ = l_c ** 3; m_ = m_c ** 3; s_ = s_c ** 3
    r = max(0, +4.0767416621 * l_ - 3.3077115913 * m_ + 0.2309699292 * s_)
    g = max(0, -1.2684380046 * l_ + 2.6097574011 * m_ - 0.3413193965 * s_)
    bv = max(0, -0.0041960863 * l_ - 0.7034186147 * m_ + 1.7076147010 * s_)
    r = max(0.0, min(1.0, _linear_to_srgb(r)))
    g = max(0.0, min(1.0, _linear_to_srgb(g)))
    bv = max(0.0, min(1.0, _linear_to_srgb(bv)))
    return "#{:02x}{:02x}{:02x}".format(int(r * 255), int(g * 255), int(bv * 255))


# Palette definitions — each is a list of (L, C, H) stops
PALETTES = {
    "aurora":  [(0.45, 0.15, 160), (0.55, 0.18, 175), (0.65, 0.16, 220),
                (0.60, 0.18, 280), (0.65, 0.20, 320), (0.70, 0.15, 350)],
    "nebula":  [(0.20, 0.10, 280), (0.35, 0.15, 300), (0.50, 0.18, 200),
                (0.65, 0.16, 180), (0.75, 0.14, 80),  (0.90, 0.06, 60)],
    "fire":    [(0.15, 0.12, 15),  (0.40, 0.18, 25),  (0.60, 0.20, 45),
                (0.80, 0.16, 70),  (0.92, 0.06, 85)],
    "ocean":   [(0.20, 0.08, 240), (0.35, 0.14, 220), (0.55, 0.18, 190),
                (0.70, 0.15, 170), (0.85, 0.08, 160)],
    "sacred":  [(0.30, 0.12, 45),  (0.50, 0.16, 40),  (0.65, 0.14, 35),
                (0.55, 0.16, 280), (0.45, 0.14, 300), (0.70, 0.12, 320)],
    "electric":[(0.25, 0.14, 260), (0.50, 0.20, 290), (0.70, 0.22, 310),
                (0.60, 0.18, 180), (0.80, 0.10, 150)],
    "sunset":  [(0.20, 0.10, 340), (0.45, 0.18, 10),  (0.65, 0.22, 35),
                (0.80, 0.18, 55),  (0.90, 0.08, 75)],
}

ALL_PALETTE_NAMES = list(PALETTES.keys())


def gradient_color(t: float, palette_name: str, dark: bool = True) -> str:
    """Interpolate along a named palette at position t in [0,1]."""
    stops = PALETTES.get(palette_name, PALETTES["aurora"])
    t = max(0.0, min(1.0, t))
    n = len(stops)
    idx = t * (n - 1)
    i = int(idx)
    frac = idx - i
    if i >= n - 1:
        L, C, H = stops[-1]
    else:
        L0, C0, H0 = stops[i]
        L1, C1, H1 = stops[i + 1]
        dh = H1 - H0
        if dh > 180: dh -= 360
        if dh < -180: dh += 360
        L = L0 + (L1 - L0) * frac
        C = C0 + (C1 - C0) * frac
        H = (H0 + dh * frac) % 360
    if not dark:
        L = min(L + 0.12, 0.72)
        C *= 1.25
    return oklch_to_hex(L, C, H)


# ---------------------------------------------------------------------------
# SVG helpers
# ---------------------------------------------------------------------------

def bloom_filter(fid: str = "bloom") -> str:
    return f"""<filter id="{fid}" x="-50%" y="-50%" width="200%" height="200%">
    <feGaussianBlur in="SourceGraphic" stdDeviation="1.5" result="b1"/>
    <feGaussianBlur in="SourceGraphic" stdDeviation="5" result="b2"/>
    <feGaussianBlur in="SourceGraphic" stdDeviation="12" result="b3"/>
    <feColorMatrix in="b3" type="matrix" result="bright"
      values="1.5 0 0 0 0.08
              0 1.5 0 0 0.08
              0 0 1.5 0 0.08
              0 0 0 0.5 0"/>
    <feMerge>
      <feMergeNode in="bright"/>
      <feMergeNode in="b2"/>
      <feMergeNode in="b1"/>
      <feMergeNode in="SourceGraphic"/>
    </feMerge>
  </filter>"""


# =========================================================================
# METRIC → PARAMETER MAPPINGS
# =========================================================================

def derive_maurer_params(metrics: dict) -> dict:
    """Map GitHub metrics to Maurer rose parameters."""
    h = _seed_hash(metrics)

    # Core petal count: driven by repos, constrained to aesthetically pleasing values
    good_n_values = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 13]
    n_idx = (metrics.get("public_repos", 10) + int(h[0:2], 16)) % len(good_n_values)
    primary_n = good_n_values[n_idx]

    # Step angle d: determines complexity. Primes make the best patterns.
    prime_d_values = [29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73, 79, 83, 89, 97]
    d_idx = (metrics.get("total_commits", 0) // 100 + int(h[2:4], 16)) % len(prime_d_values)
    primary_d = prime_d_values[d_idx]

    # Number of overlaid layers: orgs + hash-derived
    n_layers = max(3, min(8, metrics.get("orgs_count", 1) + 2 + int(h[4:5], 16) % 3))

    # Palette selection from hash
    palette_idx = int(h[6:8], 16) % len(ALL_PALETTE_NAMES)
    primary_palette = ALL_PALETTE_NAMES[palette_idx]

    # Hue rotation from contributions
    hue_shift = (metrics.get("contributions_last_year", 0) * 7 + int(h[8:12], 16)) % 360

    # Generate layer params — each layer has its own n, d derived from hash
    layers = []
    for i in range(n_layers):
        seg = h[12 + i * 4: 16 + i * 4] if 16 + i * 4 <= 64 else h[:4]
        ln = good_n_values[(primary_n + int(seg[0], 16)) % len(good_n_values)]
        ld = prime_d_values[(d_idx + int(seg[1:3], 16)) % len(prime_d_values)]
        lr = 340 - i * 25  # outer layers have largest radius
        lsw = 0.2 + i * 0.08  # inner layers are thicker
        lop = 0.08 + i * 0.06  # inner layers are brighter
        lpal = ALL_PALETTE_NAMES[(palette_idx + i) % len(ALL_PALETTE_NAMES)]
        lct = (hue_shift / 360 + i * 0.15) % 1.0
        layers.append((ln, ld, lr, lsw, lop, lpal, lct))

    return {
        "layers": layers,
        "primary_n": primary_n,
        "primary_d": primary_d,
        "primary_palette": primary_palette,
        "hue_shift": hue_shift,
    }


def derive_guilloche_params(metrics: dict) -> dict:
    """Map GitHub metrics to guilloché wave parameters."""
    h = _seed_hash(metrics)

    # Number of concentric wave bands: more followers = more bands
    n_bands = max(4, min(16, 4 + metrics.get("followers", 0) // 15 + int(h[0:2], 16) % 4))

    # Wave frequency range: commits drive complexity
    base_freq = max(4, min(48, 6 + metrics.get("total_commits", 0) // 800))
    freq_spread = max(2, min(10, metrics.get("public_repos", 5) // 4))

    # Spoke count
    n_spokes = max(12, min(120, 12 + metrics.get("contributions_last_year", 0) // 20))

    # Palette
    palette_idx = int(h[6:8], 16) % len(ALL_PALETTE_NAMES)
    palette = ALL_PALETTE_NAMES[palette_idx]

    # Build band configs
    bands = []
    for i in range(n_bands):
        R = 350 - i * (300 / n_bands)
        amp = 15 + (300 / n_bands) * 0.4  # amplitude proportional to band width
        seg = h[8 + i * 2: 10 + i * 2] if 10 + i * 2 <= 64 else h[:2]
        freq = base_freq + int(seg[0], 16) % freq_spread
        phase = _hex_float(h, min(10 + i * 3, 60), min(13 + i * 3, 63)) * 2 * math.pi
        sw = 0.15 + i * 0.05
        op = 0.06 + i * 0.04
        pal = ALL_PALETTE_NAMES[(palette_idx + i // 2) % len(ALL_PALETTE_NAMES)]
        ct = i / n_bands
        bands.append((R, amp, freq, phase, sw, op, pal, ct))

    return {
        "bands": bands,
        "n_spokes": n_spokes,
        "palette": palette,
    }


def derive_spirograph_params(metrics: dict) -> dict:
    """Map GitHub metrics to spirograph (hypotrochoid/epitrochoid) parameters."""
    h = _seed_hash(metrics)

    # Number of hypotrochoid layers: repos drive it
    n_hypo = max(4, min(12, 4 + metrics.get("public_repos", 5) // 5))

    # R/r ratios determine lobe count: we want aesthetically pleasing ratios
    # Small r relative to R = many lobes, large r = few lobes
    good_ratios = [(7, 2), (5, 2), (7, 3), (5, 3), (4, 3), (8, 3), (9, 4),
                   (11, 4), (8, 5), (7, 4), (10, 3), (6, 5), (9, 2), (11, 3)]

    base_ratio_idx = (metrics.get("total_commits", 0) // 500 + int(h[0:2], 16)) % len(good_ratios)

    # Symmetry rotations: more orgs = more copies
    n_rotations = max(1, min(8, metrics.get("orgs_count", 1) + int(h[2:3], 16) % 3))

    palette_idx = int(h[4:6], 16) % len(ALL_PALETTE_NAMES)

    layers = []
    for i in range(n_hypo):
        ratio_idx = (base_ratio_idx + i) % len(good_ratios)
        rn, rd = good_ratios[ratio_idx]
        scale = 340 - i * (280 / n_hypo)
        R = scale * rn / (rn + rd)  # actual R
        r = scale * rd / (rn + rd)  # actual r
        seg = h[6 + i * 3: 9 + i * 3] if 9 + i * 3 <= 64 else h[:3]
        d_offset = r * (0.5 + _hex_float(h, min(9 + i * 2, 58), min(11 + i * 2, 60)))
        sw = 0.2 + i * 0.06
        op = 0.06 + i * 0.04
        pal = ALL_PALETTE_NAMES[(palette_idx + i) % len(ALL_PALETTE_NAMES)]
        ct = (i / n_hypo + _hex_float(h, min(12 + i, 60), min(14 + i, 62)) * 0.3) % 1.0
        layers.append((R, r, d_offset, sw, op, pal, ct))

    return {
        "layers": layers,
        "n_rotations": n_rotations,
        "palette": ALL_PALETTE_NAMES[palette_idx],
    }


def derive_geobloom_params(metrics: dict) -> dict:
    """Map GitHub metrics to geometric bloom parameters."""
    h = _seed_hash(metrics)

    # Number of flower-of-life rings: more repos = more rings
    n_rings = max(1, min(4, 1 + metrics.get("public_repos", 5) // 10))

    # Petal layers
    n_petal_layers = max(3, min(8, 3 + metrics.get("orgs_count", 1) + int(h[0:1], 16) % 3))

    # Good petal counts (visually pleasing n for rose curves)
    good_petals = [3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 15, 17, 19]
    base_petal_idx = (metrics.get("contributions_last_year", 0) // 200 + int(h[2:4], 16)) % len(good_petals)

    # Framework complexity: hexagonal vs 8-fold vs 12-fold
    symmetry_order = [6, 8, 12][(metrics.get("total_commits", 0) // 1000 + int(h[4:5], 16)) % 3]

    palette_idx = int(h[6:8], 16) % len(ALL_PALETTE_NAMES)

    petal_layers = []
    for i in range(n_petal_layers):
        pidx = (base_petal_idx + i * 2) % len(good_petals)
        n_p = good_petals[pidx]
        radius = 100 + i * (260 / n_petal_layers)
        sw = 0.5 - i * 0.04
        op = 0.35 - i * 0.03
        pal = ALL_PALETTE_NAMES[(palette_idx + i) % len(ALL_PALETTE_NAMES)]
        ct = i / n_petal_layers
        petal_layers.append((n_p, radius, sw, op, pal, ct))

    return {
        "flower_r": 60 + metrics.get("followers", 0) // 40,
        "n_rings": n_rings,
        "petal_layers": petal_layers,
        "symmetry_order": symmetry_order,
        "palette": ALL_PALETTE_NAMES[palette_idx],
    }


# =========================================================================
# GENERATORS — parameterized by metrics
# =========================================================================

def generate_maurer_rose(metrics: dict, dark_mode: bool = True) -> str:
    """Generate Maurer rose SVG content driven by metrics."""
    params = derive_maurer_params(metrics)

    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" width="{WIDTH}" height="{HEIGHT}">\n']

    parts.append(f'<defs>\n  {bloom_filter()}\n')
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

    parts.append('<g filter="url(#bloom)">\n')

    # Draw Maurer rose layers
    for n, d, radius, sw, opacity, palette, ct in params["layers"]:
        pts = []
        for i in range(361):
            theta_deg = i * d
            theta = math.radians(theta_deg)
            r = radius * math.sin(n * theta)
            x = CX + r * math.cos(theta)
            y = CY + r * math.sin(theta)
            pts.append((x, y))

        path_d = f"M{pts[0][0]:.1f},{pts[0][1]:.1f}"
        for px, py in pts[1:]:
            path_d += f" L{px:.1f},{py:.1f}"
        path_d += " Z"

        color = gradient_color(ct, palette, dark_mode)
        parts.append(f'<path d="{path_d}" fill="none" stroke="{color}" '
                     f'stroke-width="{sw}" opacity="{opacity}" '
                     f'stroke-linecap="round" stroke-linejoin="round"/>\n')

    # Smooth underlying rose curves for 2-3 layers
    for i, (n, d, radius, *_rest) in enumerate(params["layers"][:3]):
        pts = []
        for j in range(3600):
            theta = j * math.pi * 2 / 3600
            r = radius * math.sin(n * theta)
            x = CX + r * math.cos(theta)
            y = CY + r * math.sin(theta)
            pts.append((x, y))
        path_d = f"M{pts[0][0]:.1f},{pts[0][1]:.1f}"
        for px, py in pts[1:]:
            path_d += f" L{px:.1f},{py:.1f}"
        path_d += " Z"
        pal = params["layers"][i][5]
        color = gradient_color(0.5, pal, dark_mode)
        parts.append(f'<path d="{path_d}" fill="none" stroke="{color}" '
                     f'stroke-width="0.5" opacity="0.25"/>\n')

    parts.append('</g>\n')

    center_color = gradient_color(0.7, params["primary_palette"], dark_mode)
    parts.append(f'<circle cx="{CX}" cy="{CY}" r="3" fill="{center_color}" opacity="0.8"/>\n')

    if dark_mode:
        parts.append(f'<rect width="{WIDTH}" height="{HEIGHT}" fill="url(#vignette)"/>\n')

    parts.append('</svg>\n')
    return "".join(parts)


def generate_guilloche(metrics: dict, dark_mode: bool = True) -> str:
    """Generate guilloché SVG content driven by metrics."""
    params = derive_guilloche_params(metrics)

    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" width="{WIDTH}" height="{HEIGHT}">\n']

    parts.append(f'<defs>\n  {bloom_filter()}\n')
    if dark_mode:
        parts.append("""  <radialGradient id="bg" cx="50%" cy="50%" r="50%">
    <stop offset="0%" stop-color="#080818"/>
    <stop offset="100%" stop-color="#020208"/>
  </radialGradient>
  <radialGradient id="vignette" cx="50%" cy="50%" r="50%">
    <stop offset="50%" stop-color="black" stop-opacity="0"/>
    <stop offset="100%" stop-color="black" stop-opacity="0.45"/>
  </radialGradient>""")
    else:
        parts.append("""  <radialGradient id="bg" cx="50%" cy="50%" r="50%">
    <stop offset="0%" stop-color="#fefefe"/>
    <stop offset="100%" stop-color="#f0eef5"/>
  </radialGradient>""")
    parts.append('\n</defs>\n')
    parts.append(f'<rect width="{WIDTH}" height="{HEIGHT}" fill="url(#bg)"/>\n')

    parts.append('<g filter="url(#bloom)">\n')

    for R, amp, freq, phase, sw, op, pal, ct in params["bands"]:
        pts = []
        for i in range(3601):
            theta = i * 2 * math.pi / 3600
            radius = R + amp * math.sin(freq * theta + phase)
            x = CX + radius * math.cos(theta)
            y = CY + radius * math.sin(theta)
            pts.append((x, y))

        path_d = f"M{pts[0][0]:.1f},{pts[0][1]:.1f}"
        for px, py in pts[1:]:
            path_d += f" L{px:.1f},{py:.1f}"

        color = gradient_color(ct, pal, dark_mode)
        parts.append(f'<path d="{path_d}" fill="none" stroke="{color}" '
                     f'stroke-width="{sw}" opacity="{op}"/>\n')

    # Radial spokes
    for i in range(params["n_spokes"]):
        theta = i * 2 * math.pi / params["n_spokes"]
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
            ct = i / params["n_spokes"]
            color = gradient_color(ct, params["palette"], dark_mode)
            parts.append(f'<path d="{path_d}" fill="none" stroke="{color}" '
                         f'stroke-width="0.15" opacity="0.06"/>\n')

    parts.append('</g>\n')

    if dark_mode:
        parts.append(f'<rect width="{WIDTH}" height="{HEIGHT}" fill="url(#vignette)"/>\n')

    parts.append('</svg>\n')
    return "".join(parts)


def generate_spirograph(metrics: dict, dark_mode: bool = True) -> str:
    """Generate spirograph SVG content driven by metrics."""
    params = derive_spirograph_params(metrics)

    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" width="{WIDTH}" height="{HEIGHT}">\n']

    parts.append(f'<defs>\n  {bloom_filter()}\n')
    if dark_mode:
        parts.append("""  <radialGradient id="bg" cx="50%" cy="50%" r="50%">
    <stop offset="0%" stop-color="#0c0414"/>
    <stop offset="100%" stop-color="#030108"/>
  </radialGradient>
  <radialGradient id="vignette" cx="50%" cy="50%" r="50%">
    <stop offset="50%" stop-color="black" stop-opacity="0"/>
    <stop offset="100%" stop-color="black" stop-opacity="0.4"/>
  </radialGradient>""")
    else:
        parts.append("""  <radialGradient id="bg" cx="50%" cy="50%" r="50%">
    <stop offset="0%" stop-color="#fefcff"/>
    <stop offset="100%" stop-color="#f3eefa"/>
  </radialGradient>""")
    parts.append('\n</defs>\n')
    parts.append(f'<rect width="{WIDTH}" height="{HEIGHT}" fill="url(#bg)"/>\n')

    parts.append('<g filter="url(#bloom)">\n')

    for R, r, d_offset, sw, op, pal, ct in params["layers"]:
        # Compute the hypotrochoid
        revolutions = max(1, int(R / math.gcd(max(1, int(R)), max(1, int(r)))))
        total_angle = revolutions * 2 * math.pi
        steps = min(14400, max(3600, revolutions * 720))

        pts = []
        for i in range(steps + 1):
            t = i * total_angle / steps
            x = CX + (R - r) * math.cos(t) + d_offset * math.cos((R - r) / max(0.01, r) * t)
            y = CY + (R - r) * math.sin(t) - d_offset * math.sin((R - r) / max(0.01, r) * t)
            pts.append((x, y))

        if len(pts) < 2:
            continue
        path_d = f"M{pts[0][0]:.1f},{pts[0][1]:.1f}"
        for px, py in pts[1:]:
            path_d += f" L{px:.1f},{py:.1f}"

        color = gradient_color(ct, pal, dark_mode)
        parts.append(f'<path d="{path_d}" fill="none" stroke="{color}" '
                     f'stroke-width="{sw}" opacity="{op}"/>\n')

    # Rotational copies of the middle layer for symmetry
    if len(params["layers"]) > 2 and params["n_rotations"] > 1:
        mid = params["layers"][len(params["layers"]) // 2]
        R, r, d_offset = mid[0], mid[1], mid[2]
        revolutions = max(1, int(R / math.gcd(max(1, int(R)), max(1, int(r)))))
        total_angle = revolutions * 2 * math.pi
        steps = min(10800, max(3600, revolutions * 720))

        base_pts = []
        for i in range(steps + 1):
            t = i * total_angle / steps
            x = CX + (R - r) * math.cos(t) + d_offset * math.cos((R - r) / max(0.01, r) * t)
            y = CY + (R - r) * math.sin(t) - d_offset * math.sin((R - r) / max(0.01, r) * t)
            base_pts.append((x, y))

        for rot in range(params["n_rotations"]):
            angle = rot * 2 * math.pi / params["n_rotations"]
            rotated = []
            for px, py in base_pts:
                dx, dy = px - CX, py - CY
                rx = CX + dx * math.cos(angle) - dy * math.sin(angle)
                ry = CY + dx * math.sin(angle) + dy * math.cos(angle)
                rotated.append((rx, ry))

            if len(rotated) < 2:
                continue
            path_d = f"M{rotated[0][0]:.1f},{rotated[0][1]:.1f}"
            for px, py in rotated[1:]:
                path_d += f" L{px:.1f},{py:.1f}"

            ct = rot / params["n_rotations"]
            color = gradient_color(ct, params["palette"], dark_mode)
            parts.append(f'<path d="{path_d}" fill="none" stroke="{color}" '
                         f'stroke-width="0.2" opacity="0.08"/>\n')

    parts.append('</g>\n')

    center_color = gradient_color(0.8, params["palette"], dark_mode)
    parts.append(f'<circle cx="{CX}" cy="{CY}" r="2" fill="{center_color}" opacity="0.7"/>\n')

    if dark_mode:
        parts.append(f'<rect width="{WIDTH}" height="{HEIGHT}" fill="url(#vignette)"/>\n')

    parts.append('</svg>\n')
    return "".join(parts)


def generate_geobloom(metrics: dict, dark_mode: bool = True) -> str:
    """Generate geometric bloom SVG content driven by metrics."""
    params = derive_geobloom_params(metrics)

    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" width="{WIDTH}" height="{HEIGHT}">\n']

    parts.append(f'<defs>\n  {bloom_filter()}\n')
    if dark_mode:
        parts.append("""  <radialGradient id="bg" cx="50%" cy="50%" r="50%">
    <stop offset="0%" stop-color="#0a0818"/>
    <stop offset="100%" stop-color="#020108"/>
  </radialGradient>
  <radialGradient id="vignette" cx="50%" cy="50%" r="50%">
    <stop offset="50%" stop-color="black" stop-opacity="0"/>
    <stop offset="100%" stop-color="black" stop-opacity="0.45"/>
  </radialGradient>""")
    else:
        parts.append("""  <radialGradient id="bg" cx="50%" cy="50%" r="50%">
    <stop offset="0%" stop-color="#fdfcff"/>
    <stop offset="100%" stop-color="#f0ecf8"/>
  </radialGradient>""")
    parts.append('\n</defs>\n')
    parts.append(f'<rect width="{WIDTH}" height="{HEIGHT}" fill="url(#bg)"/>\n')

    parts.append('<g filter="url(#bloom)">\n')

    # Flower of life circles
    flower_r = params["flower_r"]
    flower_centers = [(CX, CY)]
    for ring in range(1, params["n_rings"] + 1):
        if ring == 1:
            for i in range(6):
                angle = i * math.pi / 3
                flower_centers.append((CX + flower_r * math.cos(angle),
                                       CY + flower_r * math.sin(angle)))
        elif ring == 2:
            for i in range(6):
                angle = i * math.pi / 3 + math.pi / 6
                flower_centers.append((CX + flower_r * 1.732 * math.cos(angle),
                                       CY + flower_r * 1.732 * math.sin(angle)))
        elif ring == 3:
            for i in range(12):
                angle = i * math.pi / 6
                flower_centers.append((CX + flower_r * 2 * math.cos(angle),
                                       CY + flower_r * 2 * math.sin(angle)))
        elif ring == 4:
            for i in range(12):
                angle = i * math.pi / 6 + math.pi / 12
                flower_centers.append((CX + flower_r * 2.6 * math.cos(angle),
                                       CY + flower_r * 2.6 * math.sin(angle)))

    fc_color = gradient_color(0.3, params["palette"], dark_mode)
    for fcx, fcy in flower_centers:
        parts.append(f'<circle cx="{fcx:.1f}" cy="{fcy:.1f}" r="{flower_r}" '
                     f'fill="none" stroke="{fc_color}" stroke-width="0.3" opacity="0.12"/>\n')

    # Petal layers (rose curves)
    for n_p, radius, sw, op, pal, ct in params["petal_layers"]:
        pts = []
        for i in range(7200):
            theta = i * 2 * math.pi / 7200
            r = radius * abs(math.cos(n_p * theta / 2))
            x = CX + r * math.cos(theta)
            y = CY + r * math.sin(theta)
            pts.append((x, y))

        path_d = f"M{pts[0][0]:.1f},{pts[0][1]:.1f}"
        for px, py in pts[1:]:
            path_d += f" L{px:.1f},{py:.1f}"
        path_d += " Z"

        color = gradient_color(ct, pal, dark_mode)
        parts.append(f'<path d="{path_d}" fill="none" stroke="{color}" '
                     f'stroke-width="{sw}" opacity="{op}"/>\n')

    # Structural framework — symmetry_order determines fold
    sym = params["symmetry_order"]

    # Concentric polygons
    for cr in range(40, 380, 40):
        poly_pts = []
        for i in range(sym + 1):
            angle = i * 2 * math.pi / sym
            poly_pts.append((CX + cr * math.cos(angle), CY + cr * math.sin(angle)))
        path_d = f"M{poly_pts[0][0]:.1f},{poly_pts[0][1]:.1f}"
        for px, py in poly_pts[1:]:
            path_d += f" L{px:.1f},{py:.1f}"
        pc = gradient_color(cr / 380, params["palette"], dark_mode)
        parts.append(f'<path d="{path_d}" fill="none" stroke="{pc}" '
                     f'stroke-width="0.15" opacity="0.05"/>\n')

    # Radial lines
    for i in range(sym * 2):
        angle = i * math.pi / sym
        x2 = CX + 380 * math.cos(angle)
        y2 = CY + 380 * math.sin(angle)
        lc = gradient_color(i / (sym * 2), params["palette"], dark_mode)
        parts.append(f'<line x1="{CX}" y1="{CY}" x2="{x2:.1f}" y2="{y2:.1f}" '
                     f'stroke="{lc}" stroke-width="0.15" opacity="0.05"/>\n')

    parts.append('</g>\n')

    if dark_mode:
        parts.append(f'<rect width="{WIDTH}" height="{HEIGHT}" fill="url(#vignette)"/>\n')

    parts.append('</svg>\n')
    return "".join(parts)


# =========================================================================
# COMPARISON GRID GENERATOR
# =========================================================================

ART_TYPES = [
    ("Maurer Rose", generate_maurer_rose),
    ("Guilloché", generate_guilloche),
    ("Spirograph", generate_spirograph),
    ("Geo Bloom", generate_geobloom),
]


def generate_comparison_grid(dark_mode: bool = True) -> Path:
    """Generate a 4x4 grid: 4 profiles x 4 art types, each as a mini SVG."""
    profile_names = list(PROFILES.keys())
    n_rows = len(profile_names)
    n_cols = len(ART_TYPES)

    cell_w = WIDTH
    cell_h = HEIGHT
    label_h = 40
    header_h = 50
    margin = 10

    total_w = n_cols * cell_w + (n_cols + 1) * margin
    total_h = header_h + n_rows * (cell_h + label_h) + (n_rows + 1) * margin

    suffix = "-dark" if dark_mode else ""
    out = Path(f".github/assets/img/proto-comparison{suffix}.svg")
    out.parent.mkdir(parents=True, exist_ok=True)

    bg = "#0a0a18" if dark_mode else "#fafafe"
    text_color = "#ccccdd" if dark_mode else "#333344"

    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {total_w} {total_h}" '
             f'width="{total_w}" height="{total_h}">\n']
    parts.append(f'<rect width="{total_w}" height="{total_h}" fill="{bg}"/>\n')
    parts.append(f'<style>text {{ font-family: -apple-system, BlinkMacSystemFont, sans-serif; fill: {text_color}; }}</style>\n')

    # Column headers
    for col, (art_name, _) in enumerate(ART_TYPES):
        x = margin + col * (cell_w + margin) + cell_w / 2
        parts.append(f'<text x="{x}" y="{header_h - 15}" text-anchor="middle" '
                     f'font-size="18" font-weight="bold">{art_name}</text>\n')

    # Generate each cell
    for row, pname in enumerate(profile_names):
        metrics = PROFILES[pname]
        y_offset = header_h + row * (cell_h + label_h + margin)

        # Row label
        label_x = total_w / 2
        parts.append(f'<text x="{margin + 5}" y="{y_offset + cell_h + label_h - 10}" '
                     f'font-size="14" font-weight="bold">{metrics["label"]}</text>\n')

        # Metric summary
        summary = (f'repos={metrics["public_repos"]} stars={metrics["stars"]} '
                   f'commits={metrics["total_commits"]} followers={metrics["followers"]}')
        parts.append(f'<text x="{margin + 5}" y="{y_offset + cell_h + label_h + 5}" '
                     f'font-size="10" opacity="0.6">{summary}</text>\n')

        for col, (art_name, gen_func) in enumerate(ART_TYPES):
            x_offset = margin + col * (cell_w + margin)

            # Generate the artwork SVG content
            svg_content = gen_func(metrics, dark_mode)

            # Embed as a nested SVG
            parts.append(f'<svg x="{x_offset}" y="{y_offset}" '
                         f'width="{cell_w}" height="{cell_h}" '
                         f'viewBox="0 0 {WIDTH} {HEIGHT}">\n')
            # Strip the outer <svg> and </svg> tags from the content
            inner = svg_content
            inner = inner.replace(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" width="{WIDTH}" height="{HEIGHT}">\n', '')
            inner = inner.replace('</svg>\n', '')
            parts.append(inner)
            parts.append('</svg>\n')

            print(f"  [{pname}] {art_name} — done")

    parts.append('</svg>\n')

    svg_text = "".join(parts)
    out.write_text(svg_text, encoding="utf-8")
    print(f"\nComparison grid {'dark' if dark_mode else 'light'}: {len(svg_text)//1024} KB → {out}")
    return out


def generate_individual_files(dark_mode: bool = True) -> list[Path]:
    """Generate individual SVG files for each profile x art type combination."""
    outputs = []
    suffix = "-dark" if dark_mode else ""

    for pname, metrics in PROFILES.items():
        for art_name, gen_func in ART_TYPES:
            art_slug = art_name.lower().replace(" ", "-").replace("é", "e")
            out = Path(f".github/assets/img/proto-v3-{art_slug}-{pname}{suffix}.svg")
            out.parent.mkdir(parents=True, exist_ok=True)

            svg_content = gen_func(metrics, dark_mode)
            out.write_text(svg_content, encoding="utf-8")
            print(f"  {pname}/{art_name}: {len(svg_content)//1024} KB → {out}")
            outputs.append(out)

    return outputs


if __name__ == "__main__":
    print("Generating individual files (dark)...")
    generate_individual_files(dark_mode=True)

    print("\nGenerating comparison grid (dark)...")
    generate_comparison_grid(dark_mode=True)

    print("\nDone! Open proto-comparison-dark.svg for the side-by-side grid,")
    print("or individual proto-v3-* files for full-resolution previews.")
