"""
Shared utilities for generative art prototypes.
Noise, color science, hash utilities, profiles, constants,
and common math helpers used by generative/animated art.
"""
from __future__ import annotations

import hashlib
import math

import numpy as np

# Canvas
WIDTH = 800
HEIGHT = 800
CX = WIDTH / 2
CY = HEIGHT / 2

# Language → hue mapping
LANG_HUES = {
    "Python": 215, "JavaScript": 48, "TypeScript": 220, "Java": 8,
    "C++": 285, "C": 255, "Go": 178, "Rust": 22, "Ruby": 348,
    "Shell": 118, "HTML": 28, "CSS": 198, "Jupyter Notebook": 168, None: 155,
}

# PROFILES moved to _dev_profiles.py


# ---------------------------------------------------------------------------
# Ecosystem maturity score
# ---------------------------------------------------------------------------

def _smoothstep(t: float) -> float:
    """Hermite ease-in-out: slow start, accelerate in middle, slow finish."""
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def compute_maturity(m: dict) -> float:
    """0.0 = brand new account, 1.0 = massively prolific.

    Uses a smoothstep (Hermite ease-in-out) curve so that newcomers see
    visible growth quickly and prolific accounts asymptote gracefully.
    """
    def _log(val: float, lo: float, hi: float) -> float:
        val = max(lo, min(hi, val))
        return math.log(val / lo) / math.log(hi / lo)

    repos = m.get("repos", [])
    max_age = max((r.get("age_months", 0) for r in repos), default=0)
    raw = (
        0.20 * _log(m.get("total_commits", 1), 10, 50000)
        + 0.15 * _log(m.get("stars", 1), 1, 5000)
        + 0.15 * _log(m.get("contributions_last_year", 1), 10, 4000)
        + 0.12 * _log(m.get("followers", 1), 1, 10000)
        + 0.10 * _log(max(1, len(repos)), 1, 15)
        + 0.10 * _log(max(1, max_age), 1, 120)
        + 0.10 * _log(m.get("forks", 1), 1, 1000)
        + 0.08 * _log(m.get("network_count", 1), 1, 3000)
    )
    return _smoothstep(raw)


# ---------------------------------------------------------------------------
# Hash utilities
# ---------------------------------------------------------------------------

def make_radial_gradient(gid: str, cx: str, cy: str, r: str,
                         stops: list[tuple[str, str, float]]) -> str:
    """Build SVG radialGradient element. stops: [(offset, color, opacity), ...]"""
    s = "".join(f'<stop offset="{o}" stop-color="{c}" stop-opacity="{a:.3f}"/>' for o, c, a in stops)
    return f'<radialGradient id="{gid}" cx="{cx}" cy="{cy}" r="{r}">{s}</radialGradient>'


def make_linear_gradient(gid: str, x1: str, y1: str, x2: str, y2: str,
                         stops: list[tuple[str, str, float]]) -> str:
    """Build SVG linearGradient element. stops: [(offset, color, opacity), ...]"""
    s = "".join(f'<stop offset="{o}" stop-color="{c}" stop-opacity="{a:.3f}"/>' for o, c, a in stops)
    return f'<linearGradient id="{gid}" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}">{s}</linearGradient>'


def parse_cli_args(argv: list[str], extra_keys: dict[str, type] | None = None) -> dict[str, str | int | bool | None]:
    """Parse common CLI args: --profile, --only, plus extras.

    Boolean flags (type=bool) are standalone (no value argument).
    """
    result: dict[str, str | int | bool | None] = {"profile": None, "only": None}
    keys: dict[str, tuple[str, type]] = {"--profile": ("profile", str), "--only": ("only", str)}
    if extra_keys:
        keys.update({f"--{k}": (k, v) for k, v in extra_keys.items()})
    i = 0
    while i < len(argv):
        if argv[i] in keys:
            name, typ = keys[argv[i]]
            if typ is bool:
                result[name] = True
                i += 1
            elif i + 1 < len(argv):
                result[name] = typ(argv[i + 1])
                i += 2
            else:
                import sys
                print(f"Warning: flag {argv[i]} has no value, ignoring", file=sys.stderr)
                i += 1
        else:
            i += 1
    return result


def seed_hash(m: dict) -> str:
    """Deterministic SHA-256 hex digest from metrics dict."""
    s = "-".join(
        str(m.get(k, 0))
        for k in sorted(m.keys())
        if k not in ("label", "repos", "contributions_monthly")
    )
    return hashlib.sha256(s.encode()).hexdigest()


def hex_frac(h: str, a: int, b: int) -> float:
    """Extract a 0-1 float from hex slice h[a:b]."""
    return int(h[a:b], 16) / (16 ** (b - a))


def _seed_hash(seed_str: str) -> str:
    """SHA-256 hex digest of a seed string."""
    return hashlib.sha256(seed_str.encode()).hexdigest()


def _hex_slice(h: str, start: int, end: int) -> float:
    """Extract a normalized float [0, 1) from hex digest slice."""
    return int(h[start:end], 16) / (16 ** (end - start))


# ---------------------------------------------------------------------------
# OKLCH color science (pure Python, no deps)
# ---------------------------------------------------------------------------

def _linear_to_srgb(c: float) -> float:
    return 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055


def oklch(L: float, C: float, H: float) -> str:
    """Convert OKLCH to hex string. L in [0,1], C ~[0,0.4], H in degrees."""
    a = C * math.cos(math.radians(H))
    b = C * math.sin(math.radians(H))
    lc = L + 0.3963377774 * a + 0.2158037573 * b
    mc = L - 0.1055613458 * a - 0.0638541728 * b
    sc = L - 0.0894841775 * a - 1.2914855480 * b
    l_ = lc ** 3
    m_ = mc ** 3
    s_ = sc ** 3
    r = max(0, 4.0767416621 * l_ - 3.3077115913 * m_ + 0.2309699292 * s_)
    g = max(0, -1.2684380046 * l_ + 2.6097574011 * m_ - 0.3413193965 * s_)
    bv = max(0, -0.0041960863 * l_ - 0.7034186147 * m_ + 1.7076147010 * s_)
    r = max(0, min(1, _linear_to_srgb(r)))
    g = max(0, min(1, _linear_to_srgb(g)))
    bv = max(0, min(1, _linear_to_srgb(bv)))
    return f"#{int(r * 255):02x}{int(g * 255):02x}{int(bv * 255):02x}"


# ---------------------------------------------------------------------------
# Gradient noise (Perlin-like)
# ---------------------------------------------------------------------------

class Noise2D:
    """2D gradient noise with fBm support."""

    def __init__(self, seed: int = 0):
        rng = np.random.default_rng(seed)
        self.perm = np.tile(rng.permutation(256).astype(np.int32), 2)
        a = rng.uniform(0, 2 * np.pi, 256)
        self.grads = np.column_stack([np.cos(a), np.sin(a)])

    @staticmethod
    def _fade(t: float) -> float:
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
        ga = self.grads[aa % 256]
        gb = self.grads[ab % 256]
        gc = self.grads[ba % 256]
        gd = self.grads[bb % 256]
        x1 = (ga[0] * xf + ga[1] * yf) + u * ((gc[0] * (xf - 1) + gc[1] * yf) - (ga[0] * xf + ga[1] * yf))
        x2 = (gb[0] * xf + gb[1] * (yf - 1)) + u * ((gd[0] * (xf - 1) + gd[1] * (yf - 1)) - (gb[0] * xf + gb[1] * (yf - 1)))
        return x1 + v * (x2 - x1)

    def fbm(self, x: float, y: float, octaves: int = 4) -> float:
        val = 0.0
        amp = 1.0
        freq = 1.0
        total = 0.0
        for _ in range(octaves):
            val += amp * self.noise(x * freq, y * freq)
            total += amp
            amp *= 0.5
            freq *= 2
        return val / total


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

