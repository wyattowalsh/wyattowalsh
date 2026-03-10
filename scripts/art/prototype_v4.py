"""
Generative Art Prototypes v4 — Chaotic / Organic / Natural
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Less symmetry, more chaos. Forms inspired by nature:
strange attractors as flowing ribbons, curl-noise fluid streams,
differential growth (coral/wrinkled edges), branching dendrites.

Each artwork is driven by GitHub metrics through seed hashing.
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
# Mock GitHub profiles
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


def _seed_hash(metrics: dict) -> str:
    seed_str = "-".join(str(metrics.get(k, 0)) for k in sorted(metrics.keys()) if k != "label")
    return hashlib.sha256(seed_str.encode()).hexdigest()


def _hf(h: str, start: int, end: int) -> float:
    return int(h[start:end], 16) / (16 ** (end - start))


# ---------------------------------------------------------------------------
# OKLCH color
# ---------------------------------------------------------------------------

def _l2s(c: float) -> float:
    return 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055

def oklch(L: float, C: float, H: float) -> str:
    a = C * math.cos(math.radians(H))
    b = C * math.sin(math.radians(H))
    lc = L + 0.3963377774 * a + 0.2158037573 * b
    mc = L - 0.1055613458 * a - 0.0638541728 * b
    sc = L - 0.0894841775 * a - 1.2914855480 * b
    l_ = lc**3; m_ = mc**3; s_ = sc**3
    r = max(0, 4.0767416621*l_ - 3.3077115913*m_ + 0.2309699292*s_)
    g = max(0, -1.2684380046*l_ + 2.6097574011*m_ - 0.3413193965*s_)
    bv = max(0, -0.0041960863*l_ - 0.7034186147*m_ + 1.7076147010*s_)
    r = max(0.0, min(1.0, _l2s(r)))
    g = max(0.0, min(1.0, _l2s(g)))
    bv = max(0.0, min(1.0, _l2s(bv)))
    return f"#{int(r*255):02x}{int(g*255):02x}{int(bv*255):02x}"

# Organic palettes — smooth gradients that evoke natural phenomena
PALETTES = {
    "bioluminescence": [
        (0.12, 0.06, 220), (0.25, 0.12, 200), (0.40, 0.18, 175),
        (0.55, 0.20, 160), (0.70, 0.16, 140), (0.85, 0.08, 120),
    ],
    "nebula": [
        (0.10, 0.08, 280), (0.25, 0.14, 300), (0.40, 0.18, 320),
        (0.55, 0.16, 200), (0.70, 0.14, 170), (0.88, 0.06, 60),
    ],
    "magma": [
        (0.08, 0.06, 0), (0.20, 0.14, 10), (0.35, 0.20, 25),
        (0.55, 0.22, 40), (0.75, 0.18, 55), (0.92, 0.06, 75),
    ],
    "aurora": [
        (0.15, 0.08, 260), (0.30, 0.14, 200), (0.50, 0.20, 160),
        (0.65, 0.18, 130), (0.75, 0.14, 100), (0.85, 0.10, 80),
    ],
    "deep_ocean": [
        (0.08, 0.05, 250), (0.18, 0.10, 230), (0.30, 0.15, 210),
        (0.45, 0.18, 195), (0.60, 0.16, 180), (0.78, 0.10, 170),
    ],
    "wildfire": [
        (0.10, 0.08, 350), (0.25, 0.16, 10), (0.45, 0.22, 25),
        (0.60, 0.20, 40), (0.78, 0.14, 55), (0.90, 0.06, 70),
    ],
    "fungal": [
        (0.12, 0.06, 30), (0.25, 0.10, 50), (0.38, 0.14, 80),
        (0.52, 0.16, 130), (0.65, 0.12, 170), (0.80, 0.08, 200),
    ],
}
PAL_NAMES = list(PALETTES.keys())

def pal_color(t: float, name: str, dark: bool = True) -> str:
    stops = PALETTES.get(name, PALETTES["nebula"])
    t = max(0.0, min(1.0, t))
    n = len(stops)
    idx = t * (n - 1)
    i = int(idx); frac = idx - i
    if i >= n - 1:
        L, C, H = stops[-1]
    else:
        L0, C0, H0 = stops[i]; L1, C1, H1 = stops[i+1]
        dh = H1 - H0
        if dh > 180: dh -= 360
        if dh < -180: dh += 360
        L = L0 + (L1-L0)*frac; C = C0 + (C1-C0)*frac
        H = (H0 + dh*frac) % 360
    if not dark:
        L = min(L + 0.15, 0.75); C *= 1.2
    return oklch(L, C, H)


def bloom_filter(fid="bloom"):
    return f"""<filter id="{fid}" x="-50%" y="-50%" width="200%" height="200%">
    <feGaussianBlur in="SourceGraphic" stdDeviation="2" result="b1"/>
    <feGaussianBlur in="SourceGraphic" stdDeviation="6" result="b2"/>
    <feGaussianBlur in="SourceGraphic" stdDeviation="14" result="b3"/>
    <feColorMatrix in="b3" type="matrix" result="bright"
      values="1.6 0 0 0 0.1  0 1.6 0 0 0.1  0 0 1.6 0 0.1  0 0 0 0.5 0"/>
    <feMerge>
      <feMergeNode in="bright"/><feMergeNode in="b2"/>
      <feMergeNode in="b1"/><feMergeNode in="SourceGraphic"/>
    </feMerge>
  </filter>"""


def svg_wrap(inner: str, dark: bool = True) -> str:
    bg1 = "#060612" if dark else "#fafafe"
    bg2 = "#020208" if dark else "#f0eef5"
    vig = ""
    if dark:
        vig = """<radialGradient id="vig" cx="50%" cy="50%" r="55%">
    <stop offset="40%" stop-color="black" stop-opacity="0"/>
    <stop offset="100%" stop-color="black" stop-opacity="0.6"/>
  </radialGradient>"""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" width="{WIDTH}" height="{HEIGHT}">
<defs>
  {bloom_filter()}
  <radialGradient id="bg" cx="50%" cy="50%" r="60%">
    <stop offset="0%" stop-color="{bg1}"/>
    <stop offset="100%" stop-color="{bg2}"/>
  </radialGradient>
  {vig}
</defs>
<rect width="{WIDTH}" height="{HEIGHT}" fill="url(#bg)"/>
{inner}
{"<rect width='" + str(WIDTH) + "' height='" + str(HEIGHT) + "' fill='url(#vig)'/>" if dark else ""}
</svg>
"""


# =========================================================================
# 1. FLOWING ATTRACTOR — Clifford/De Jong as smooth ribbon traces
# =========================================================================

def generate_flowing_attractor(metrics: dict, dark_mode: bool = True) -> str:
    """Clifford or De Jong attractor rendered as many overlapping smooth curves.
    Each curve is one trajectory — a continuous flowing ribbon, not a dot cloud."""
    h = _seed_hash(metrics)
    rng = np.random.default_rng(int(h[:8], 16))

    # Attractor parameters from metrics
    a = -2.0 + _hf(h, 0, 4) * 4.0
    b = -2.0 + _hf(h, 4, 8) * 4.0
    c = -2.0 + _hf(h, 8, 12) * 4.0
    d = -2.0 + _hf(h, 12, 16) * 4.0

    # Use De Jong if hash bit says so (different visual character)
    use_dejong = int(h[16], 16) > 7

    # Number of trace curves: more contributions = more traces
    n_traces = max(30, min(200, 30 + metrics.get("contributions_last_year", 0) // 15))
    # Steps per trace: more commits = longer traces
    steps_per = max(200, min(2000, 200 + metrics.get("total_commits", 0) // 8))

    palette_idx = int(h[17:19], 16) % len(PAL_NAMES)
    pal = PAL_NAMES[palette_idx]

    # Generate traces
    traces = []
    for t in range(n_traces):
        # Start from slightly randomized positions
        x = rng.uniform(-0.5, 0.5)
        y = rng.uniform(-0.5, 0.5)
        points = []

        for s in range(steps_per):
            if use_dejong:
                nx = math.sin(a * y) - math.cos(b * x)
                ny = math.sin(c * x) - math.cos(d * y)
            else:
                nx = math.sin(a * y) + c * math.cos(a * x)
                ny = math.sin(b * x) + d * math.cos(b * y)
            x, y = nx, ny
            # Map attractor space (~[-2.5, 2.5]) to SVG space
            sx = CX + x * 140
            sy = CY + y * 140
            if 0 <= sx <= WIDTH and 0 <= sy <= HEIGHT:
                points.append((sx, sy))

        if len(points) > 10:
            traces.append(points)

    # Render as SVG paths with varying color/opacity along trace
    parts = []
    parts.append('<g filter="url(#bloom)">\n')

    for i, pts in enumerate(traces):
        # Break each trace into segments for color variation
        seg_len = max(1, len(pts) // 5)
        for seg_idx in range(0, len(pts) - 1, seg_len):
            seg = pts[seg_idx:seg_idx + seg_len + 1]
            if len(seg) < 2:
                continue

            # Color varies along trace and across traces
            t_color = (i / n_traces + seg_idx / len(pts) * 0.3) % 1.0
            color = pal_color(t_color, pal, dark_mode)

            # Opacity: traces fade at ends
            frac_along = seg_idx / max(1, len(pts))
            opacity = 0.15 + 0.35 * math.sin(frac_along * math.pi)

            # Stroke width: thinner for outer traces
            sw = 0.3 + 0.8 * (1 - i / n_traces)

            path_d = f"M{seg[0][0]:.1f},{seg[0][1]:.1f}"
            # Use quadratic bezier for smoother curves
            for j in range(1, len(seg) - 1, 2):
                if j + 1 < len(seg):
                    path_d += f" Q{seg[j][0]:.1f},{seg[j][1]:.1f} {seg[j+1][0]:.1f},{seg[j+1][1]:.1f}"
                else:
                    path_d += f" L{seg[j][0]:.1f},{seg[j][1]:.1f}"

            parts.append(f'<path d="{path_d}" fill="none" stroke="{color}" '
                         f'stroke-width="{sw:.2f}" opacity="{opacity:.3f}" '
                         f'stroke-linecap="round" stroke-linejoin="round"/>\n')

    parts.append('</g>\n')
    return svg_wrap("".join(parts), dark_mode)


# =========================================================================
# 2. CURL NOISE FLOW — Organic fluid streams
# =========================================================================

class GradientNoise2D:
    """Simple 2D gradient noise (Perlin-like) for pure-Python use."""

    def __init__(self, seed: int = 0):
        rng = np.random.default_rng(seed)
        self.perm = rng.permutation(256).astype(np.int32)
        self.perm = np.concatenate([self.perm, self.perm])  # double for wrapping
        # Random unit gradient vectors
        angles = rng.uniform(0, 2 * np.pi, 256)
        self.grads = np.column_stack([np.cos(angles), np.sin(angles)])

    def _fade(self, t):
        return t * t * t * (t * (t * 6 - 15) + 10)

    def noise(self, x: float, y: float) -> float:
        xi = int(math.floor(x)) & 255
        yi = int(math.floor(y)) & 255
        xf = x - math.floor(x)
        yf = y - math.floor(y)

        u = self._fade(xf)
        v = self._fade(yf)

        aa = self.perm[self.perm[xi] + yi]
        ab = self.perm[self.perm[xi] + yi + 1]
        ba = self.perm[self.perm[xi + 1] + yi]
        bb = self.perm[self.perm[xi + 1] + yi + 1]

        g_aa = self.grads[aa % 256]
        g_ab = self.grads[ab % 256]
        g_ba = self.grads[ba % 256]
        g_bb = self.grads[bb % 256]

        d_aa = g_aa[0] * xf + g_aa[1] * yf
        d_ba = g_ba[0] * (xf - 1) + g_ba[1] * yf
        d_ab = g_ab[0] * xf + g_ab[1] * (yf - 1)
        d_bb = g_bb[0] * (xf - 1) + g_bb[1] * (yf - 1)

        x1 = d_aa + u * (d_ba - d_aa)
        x2 = d_ab + u * (d_bb - d_ab)
        return x1 + v * (x2 - x1)

    def fbm(self, x: float, y: float, octaves: int = 4) -> float:
        val = 0.0; amp = 1.0; freq = 1.0; total_amp = 0.0
        for _ in range(octaves):
            val += amp * self.noise(x * freq, y * freq)
            total_amp += amp
            amp *= 0.5; freq *= 2.0
        return val / total_amp


def generate_curl_flow(metrics: dict, dark_mode: bool = True) -> str:
    """Curl noise flow field — particles trace divergence-free paths through
    a noise field, creating organic swirling streams like smoke or ink in water."""
    h = _seed_hash(metrics)
    rng = np.random.default_rng(int(h[:8], 16))
    noise = GradientNoise2D(seed=int(h[8:16], 16))

    # Metrics-driven params
    n_lines = max(60, min(400, 60 + metrics.get("contributions_last_year", 0) // 5))
    steps = max(80, min(300, 80 + metrics.get("total_commits", 0) // 40))
    noise_scale = 0.003 + _hf(h, 16, 20) * 0.004  # controls swirl tightness
    octaves = max(2, min(6, 2 + metrics.get("public_repos", 5) // 8))
    step_size = 2.0 + _hf(h, 20, 24) * 2.0

    palette_idx = int(h[24:26], 16) % len(PAL_NAMES)
    pal = PAL_NAMES[palette_idx]

    eps = 0.5  # curl noise epsilon

    parts = []
    parts.append('<g filter="url(#bloom)">\n')

    for i in range(n_lines):
        # Seed points distributed organically — not grid, not uniform
        # Use a mix of random and spiral placement
        if i < n_lines * 0.3:
            # Inner spiral region
            angle = i * 2.399  # golden angle
            r = 50 + math.sqrt(i) * 15
            x = CX + r * math.cos(angle)
            y = CY + r * math.sin(angle)
        elif i < n_lines * 0.7:
            # Random scatter
            x = rng.uniform(80, WIDTH - 80)
            y = rng.uniform(80, HEIGHT - 80)
        else:
            # Edge ring
            angle = rng.uniform(0, 2 * math.pi)
            r = rng.uniform(250, 370)
            x = CX + r * math.cos(angle)
            y = CY + r * math.sin(angle)

        pts = [(x, y)]
        for s in range(steps):
            # Curl noise: take partial derivatives of noise to get divergence-free field
            nx = x * noise_scale
            ny = y * noise_scale
            # ∂N/∂y for vx, -∂N/∂x for vy (curl of scalar noise)
            n_up = noise.fbm(nx, ny + eps * noise_scale, octaves)
            n_dn = noise.fbm(nx, ny - eps * noise_scale, octaves)
            n_rt = noise.fbm(nx + eps * noise_scale, ny, octaves)
            n_lt = noise.fbm(nx - eps * noise_scale, ny, octaves)

            vx = (n_up - n_dn) / (2 * eps * noise_scale)
            vy = -(n_rt - n_lt) / (2 * eps * noise_scale)

            mag = math.sqrt(vx*vx + vy*vy) + 1e-10
            vx /= mag; vy /= mag

            x += vx * step_size
            y += vy * step_size

            if x < -20 or x > WIDTH + 20 or y < -20 or y > HEIGHT + 20:
                break
            pts.append((x, y))

        if len(pts) < 5:
            continue

        # Render as smooth curve with color gradient along length
        n_segs = max(1, len(pts) // 20)
        seg_size = len(pts) // n_segs

        for si in range(n_segs):
            seg = pts[si * seg_size: (si + 1) * seg_size + 1]
            if len(seg) < 2:
                continue

            t_color = (i / n_lines * 0.7 + si / n_segs * 0.3) % 1.0
            color = pal_color(t_color, pal, dark_mode)

            # Taper: stroke width decreases along the line
            frac = si / n_segs
            sw = 1.2 * (1 - frac * 0.7) * (0.3 + 0.7 * min(1, i / (n_lines * 0.3)))
            opacity = 0.12 + 0.30 * math.sin((frac + 0.1) * math.pi)

            path_d = f"M{seg[0][0]:.1f},{seg[0][1]:.1f}"
            for j in range(1, len(seg) - 1, 2):
                if j + 1 < len(seg):
                    path_d += f" Q{seg[j][0]:.1f},{seg[j][1]:.1f} {seg[j+1][0]:.1f},{seg[j+1][1]:.1f}"
                else:
                    path_d += f" L{seg[j][0]:.1f},{seg[j][1]:.1f}"

            parts.append(f'<path d="{path_d}" fill="none" stroke="{color}" '
                         f'stroke-width="{sw:.2f}" opacity="{opacity:.3f}" '
                         f'stroke-linecap="round"/>\n')

    parts.append('</g>\n')
    return svg_wrap("".join(parts), dark_mode)


# =========================================================================
# 3. DIFFERENTIAL GROWTH — Organic wrinkled/coral-like edges
# =========================================================================

def generate_differential_growth(metrics: dict, dark_mode: bool = True) -> str:
    """A ring that grows outward with noise perturbation, developing organic
    wrinkled edges like coral, lichen, or brain convolutions."""
    h = _seed_hash(metrics)
    rng = np.random.default_rng(int(h[:8], 16))

    # Start with a circle of points
    n_initial = max(80, min(200, 80 + metrics.get("public_repos", 10) * 3))
    growth_steps = max(80, min(350, 80 + metrics.get("contributions_last_year", 0) // 6))
    split_dist = max(2.5, min(6.0, 2.5 + metrics.get("followers", 0) / 800))
    repel_dist = split_dist * 0.9
    noise_mag = 0.8 + _hf(h, 16, 20) * 2.0
    attract_center = 0.002 + _hf(h, 20, 24) * 0.004

    palette_idx = int(h[24:26], 16) % len(PAL_NAMES)
    pal = PAL_NAMES[palette_idx]
    n_rings = max(2, min(5, 2 + metrics.get("orgs_count", 1)))

    noise = GradientNoise2D(seed=int(h[8:16], 16))

    all_rings = []

    for ring_idx in range(n_rings):
        # Each ring starts at different radius
        base_r = 30 + ring_idx * (280 / n_rings)
        points = []
        for i in range(n_initial):
            angle = i * 2 * math.pi / n_initial
            x = CX + base_r * math.cos(angle)
            y = CY + base_r * math.sin(angle)
            points.append([x, y])

        # Grow!
        ring_growth = max(10, growth_steps - ring_idx * 15)
        for step in range(ring_growth):
            n = len(points)
            if n > 4000:  # cap complexity
                break

            # Noise-based outward push
            for i in range(n):
                x, y = points[i]
                dx = x - CX
                dy = y - CY
                dist = math.sqrt(dx*dx + dy*dy) + 1e-10
                # Outward direction
                ox = dx / dist
                oy = dy / dist
                # Add noise perturbation
                nx = noise.fbm(x * 0.008 + step * 0.1, y * 0.008, 3)
                ny = noise.fbm(x * 0.008, y * 0.008 + step * 0.1, 3)
                push = noise_mag * (0.5 + 0.5 * noise.fbm(x * 0.005, y * 0.005 + ring_idx, 2))
                points[i][0] += (ox * push + nx * noise_mag * 0.5)
                points[i][1] += (oy * push + ny * noise_mag * 0.5)
                # Slight center attraction to keep it bounded
                points[i][0] -= dx * attract_center
                points[i][1] -= dy * attract_center

            # Neighbor repulsion (prevent self-intersection)
            for i in range(n):
                for di in [-2, -1, 1, 2]:
                    j = (i + di) % n
                    dx = points[i][0] - points[j][0]
                    dy = points[i][1] - points[j][1]
                    d = math.sqrt(dx*dx + dy*dy) + 1e-10
                    if d < repel_dist and abs(di) > 1:
                        force = (repel_dist - d) * 0.3
                        points[i][0] += dx / d * force
                        points[i][1] += dy / d * force

            # Edge smoothing: average with neighbors slightly
            smoothed = []
            for i in range(n):
                p = (i - 1) % n
                nx_ = (i + 1) % n
                sx = points[i][0] * 0.6 + points[p][0] * 0.2 + points[nx_][0] * 0.2
                sy = points[i][1] * 0.6 + points[p][1] * 0.2 + points[nx_][1] * 0.2
                smoothed.append([sx, sy])
            points = smoothed

            # Split long edges (add midpoints)
            new_points = []
            for i in range(n):
                new_points.append(points[i])
                j = (i + 1) % n
                dx = points[j][0] - points[i][0]
                dy = points[j][1] - points[i][1]
                d = math.sqrt(dx*dx + dy*dy)
                if d > split_dist:
                    # Insert midpoint with slight perturbation
                    mx = (points[i][0] + points[j][0]) / 2 + rng.normal(0, 0.3)
                    my = (points[i][1] + points[j][1]) / 2 + rng.normal(0, 0.3)
                    new_points.append([mx, my])
            points = new_points

        all_rings.append(points)

    # Render
    parts = []
    parts.append('<g filter="url(#bloom)">\n')

    for ring_idx, points in enumerate(all_rings):
        if len(points) < 3:
            continue

        # Color: inner rings are warmer/brighter, outer are cooler/dimmer
        t_base = ring_idx / n_rings
        color = pal_color(t_base, pal, dark_mode)
        opacity = 0.15 + 0.25 * (1 - t_base)
        sw = 0.4 + 0.8 * (1 - t_base)

        # Draw as closed path
        path_d = f"M{points[0][0]:.1f},{points[0][1]:.1f}"
        # Use quadratic beziers for organic smoothness
        for i in range(1, len(points) - 1, 2):
            if i + 1 < len(points):
                path_d += f" Q{points[i][0]:.1f},{points[i][1]:.1f} {points[i+1][0]:.1f},{points[i+1][1]:.1f}"
            else:
                path_d += f" L{points[i][0]:.1f},{points[i][1]:.1f}"
        path_d += " Z"

        parts.append(f'<path d="{path_d}" fill="none" stroke="{color}" '
                     f'stroke-width="{sw:.2f}" opacity="{opacity:.3f}" '
                     f'stroke-linecap="round" stroke-linejoin="round"/>\n')

        # Also draw a subtle filled version at very low opacity for depth
        fill_color = pal_color(t_base * 0.7, pal, dark_mode)
        parts.append(f'<path d="{path_d}" fill="{fill_color}" fill-opacity="{opacity * 0.15:.3f}" '
                     f'stroke="none"/>\n')

    parts.append('</g>\n')
    return svg_wrap("".join(parts), dark_mode)


# =========================================================================
# 4. BRANCHING DENDRITES — Neural / lightning / mycelium networks
# =========================================================================

def generate_dendrites(metrics: dict, dark_mode: bool = True) -> str:
    """Recursive branching patterns with noise perturbation —
    like neural dendrites, lightning, mycelium, or river deltas."""
    h = _seed_hash(metrics)
    rng = np.random.default_rng(int(h[:8], 16))
    noise = GradientNoise2D(seed=int(h[8:16], 16))

    # Metrics drive branching character
    n_roots = max(3, min(8, 3 + metrics.get("orgs_count", 1)))
    max_depth = max(3, min(6, 3 + metrics.get("public_repos", 5) // 10))
    branch_prob = min(0.7, 0.35 + metrics.get("contributions_last_year", 0) / 4000)
    seg_length = max(15, min(45, 15 + metrics.get("total_commits", 0) // 500))
    noise_wander = 0.3 + _hf(h, 16, 20) * 0.8
    MAX_SEGMENTS = 8000  # hard cap to prevent file size explosion

    palette_idx = int(h[20:22], 16) % len(PAL_NAMES)
    pal = PAL_NAMES[palette_idx]

    segments = []  # list of (x1, y1, x2, y2, depth, branch_id)

    def branch(x, y, angle, depth, length, branch_id):
        if depth > max_depth or length < 3 or len(segments) >= MAX_SEGMENTS:
            return

        # Number of segments in this branch
        n_segs = max(3, min(15, int(length / 4)))
        cx_, cy_ = x, y

        for s in range(n_segs):
            # Noise-perturbed direction
            n_val = noise.fbm(cx_ * 0.01 + branch_id * 0.7, cy_ * 0.01, 3)
            perturbed_angle = angle + n_val * noise_wander

            seg_l = length / n_segs * rng.uniform(0.7, 1.3)
            nx_ = cx_ + seg_l * math.cos(perturbed_angle)
            ny_ = cy_ + seg_l * math.sin(perturbed_angle)

            # Keep within bounds (soft bounce)
            if nx_ < 30: perturbed_angle = rng.uniform(-0.5, 0.5)
            if nx_ > WIDTH - 30: perturbed_angle = rng.uniform(math.pi - 0.5, math.pi + 0.5)
            if ny_ < 30: perturbed_angle = rng.uniform(0.5, math.pi - 0.5)
            if ny_ > HEIGHT - 30: perturbed_angle = rng.uniform(math.pi + 0.5, 2 * math.pi - 0.5)
            nx_ = cx_ + seg_l * math.cos(perturbed_angle)
            ny_ = cy_ + seg_l * math.sin(perturbed_angle)

            segments.append((cx_, cy_, nx_, ny_, depth, branch_id))
            cx_, cy_ = nx_, ny_
            angle = perturbed_angle  # continue in perturbed direction

            # Branching decision
            if len(segments) < MAX_SEGMENTS and rng.random() < branch_prob * (1 - depth / max_depth) * 0.5:
                fork_angle = rng.uniform(0.3, 1.2) * rng.choice([-1, 1])
                new_length = length * rng.uniform(0.5, 0.75)
                branch(cx_, cy_, angle + fork_angle, depth + 1, new_length, branch_id + rng.integers(100))

        # Terminal branches: try to fork (capped)
        if depth < max_depth - 1 and len(segments) < MAX_SEGMENTS and rng.random() < branch_prob:
            n_forks = rng.integers(1, 3)
            for _ in range(n_forks):
                if len(segments) >= MAX_SEGMENTS:
                    break
                fork_angle = rng.uniform(0.2, 1.0) * rng.choice([-1, 1])
                new_length = length * rng.uniform(0.4, 0.65)
                branch(cx_, cy_, angle + fork_angle, depth + 1, new_length, branch_id + rng.integers(100))

    # Seed roots from around center, pointing outward
    for i in range(n_roots):
        angle = i * 2 * math.pi / n_roots + rng.uniform(-0.3, 0.3)
        start_r = rng.uniform(20, 60)
        sx = CX + start_r * math.cos(angle)
        sy = CY + start_r * math.sin(angle)
        branch(sx, sy, angle, 0, seg_length * (3 + rng.uniform(0, 2)), i * 17)

    # Render
    parts = []
    parts.append('<g filter="url(#bloom)">\n')

    for x1, y1, x2, y2, depth, bid in segments:
        # Color: depth determines color position, branch_id adds variety
        t_color = (depth / max_depth * 0.6 + (bid % 100) / 100 * 0.4) % 1.0
        color = pal_color(t_color, pal, dark_mode)

        # Thicker at root, thinner at tips
        sw = max(0.2, 2.5 * (1 - depth / max_depth) ** 1.5)
        opacity = max(0.08, 0.5 * (1 - depth / max_depth * 0.6))

        # Draw as slightly curved line (midpoint offset for organic feel)
        mx = (x1 + x2) / 2 + rng.uniform(-2, 2)
        my = (y1 + y2) / 2 + rng.uniform(-2, 2)
        path_d = f"M{x1:.1f},{y1:.1f} Q{mx:.1f},{my:.1f} {x2:.1f},{y2:.1f}"

        parts.append(f'<path d="{path_d}" fill="none" stroke="{color}" '
                     f'stroke-width="{sw:.2f}" opacity="{opacity:.3f}" '
                     f'stroke-linecap="round"/>\n')

    # Add glowing nodes at branch points
    branch_points = {}
    for x1, y1, x2, y2, depth, bid in segments:
        key = (round(x1, 0), round(y1, 0))
        if key not in branch_points:
            branch_points[key] = depth
        key2 = (round(x2, 0), round(y2, 0))
        if key2 not in branch_points:
            branch_points[key2] = depth

    for (bx, by), depth in branch_points.items():
        if depth < 2:  # only glow at root/early branch points
            r = max(1, 3 * (1 - depth / max_depth))
            color = pal_color(0.8, pal, dark_mode)
            parts.append(f'<circle cx="{bx}" cy="{by}" r="{r:.1f}" '
                         f'fill="{color}" opacity="0.3"/>\n')

    parts.append('</g>\n')
    return svg_wrap("".join(parts), dark_mode)


# =========================================================================
# Main
# =========================================================================

ART_TYPES = [
    ("attractor", "Flowing Attractor", generate_flowing_attractor),
    ("curlflow", "Curl Flow", generate_curl_flow),
    ("diffgrowth", "Differential Growth", generate_differential_growth),
    ("dendrites", "Dendrites", generate_dendrites),
]


if __name__ == "__main__":
    out_dir = Path(".github/assets/img")
    out_dir.mkdir(parents=True, exist_ok=True)

    for pname, metrics in PROFILES.items():
        print(f"\n--- {metrics['label']} ---")
        for slug, label, gen_func in ART_TYPES:
            svg = gen_func(metrics, dark_mode=True)
            out = out_dir / f"proto-v4-{slug}-{pname}-dark.svg"
            out.write_text(svg, encoding="utf-8")
            print(f"  {label}: {len(svg)//1024} KB → {out}")

    print("\nDone! Open proto-v4-* files in browser.")
