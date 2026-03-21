"""
Shared utilities for generative art prototypes.
Noise, color science, hash utilities, profiles, constants,
and common math helpers used by generative/animated art.
"""
from __future__ import annotations

import calendar
import hashlib
import math
import re
from datetime import date as dt_date
from datetime import datetime
from datetime import timedelta
from typing import Any
from typing import Mapping
from typing import Sequence

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


_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_YYYY_MM_RE = re.compile(r"^\d{4}-\d{2}$")
_MONTH_ONLY_RE = re.compile(r"^\d{1,2}$")


def _as_date(value: Any) -> dt_date | None:
    """Convert common date representations into ``datetime.date``."""
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, dt_date):
        return value
    if not isinstance(value, str):
        return None
    s = value.strip()
    if not s:
        return None
    if _ISO_DATE_RE.match(s):
        try:
            return dt_date.fromisoformat(s)
        except ValueError:
            return None
    if _YYYY_MM_RE.match(s):
        try:
            year, month = map(int, s.split("-"))
            return dt_date(year, month, 1)
        except ValueError:
            return None
    if "T" in s:
        try:
            return datetime.fromisoformat(s.replace("Z", "+00:00")).date()
        except ValueError:
            return None
    return None


def normalize_timeline_window(
    dated_events: Sequence[Any] | None = None,
    history: Mapping[str, Any] | None = None,
    *,
    fallback_days: int = 365,
    now: dt_date | None = None,
) -> tuple[dt_date, dt_date]:
    """Infer a normalized [start, end] window from history and dated events."""
    observed: list[dt_date] = []
    if dated_events:
        for event in dated_events:
            if isinstance(event, Mapping):
                parsed = _as_date(event.get("date"))
            else:
                parsed = _as_date(event)
            if parsed:
                observed.append(parsed)

    if history:
        for key in ("account_created",):
            parsed = _as_date(history.get(key))
            if parsed:
                observed.append(parsed)
        for collection in ("repos", "stars", "forks"):
            for item in history.get(collection, []) or []:
                if isinstance(item, Mapping):
                    parsed = _as_date(item.get("date"))
                    if parsed:
                        observed.append(parsed)
        for month_key in (history.get("contributions_monthly", {}) or {}).keys():
            parsed = _as_date(month_key)
            if parsed:
                observed.append(parsed)

    if observed:
        start = min(observed)
        end = max(observed)
        return (start, end if end >= start else start)

    today = now or dt_date.today()
    safe_days = max(int(fallback_days), 1)
    return today - timedelta(days=safe_days), today


def map_date_to_loop_delay(
    when: Any,
    window: tuple[dt_date, dt_date],
    *,
    duration: float,
    reveal_fraction: float = 0.93,
    easing_power: float = 1.0,
) -> float:
    """Map a real date into a loop delay in seconds, clamped to timeline window."""
    start, end = window
    if end < start:
        start, end = end, start
    parsed = _as_date(when)
    if parsed is None:
        parsed = start
    clamped = min(max(parsed, start), end)
    span_days = max((end - start).days, 1)
    frac = (clamped - start).days / span_days
    eased = frac ** max(easing_power, 0.01)
    reveal_end = max(duration, 0.0) * max(min(reveal_fraction, 1.0), 0.0)
    return round(eased * reveal_end, 3)


def _iter_months(start_year: int, start_month: int, end_year: int, end_month: int) -> list[tuple[int, int]]:
    """Yield (year, month) inclusive between start and end."""
    out: list[tuple[int, int]] = []
    year, month = start_year, start_month
    while (year, month) <= (end_year, end_month):
        out.append((year, month))
        month += 1
        if month > 12:
            month = 1
            year += 1
    return out


def _distribute_monthly_count(year: int, month: int, count: int) -> list[int]:
    """Deterministically spread monthly counts across month days."""
    days_in_month = calendar.monthrange(year, month)[1]
    count = max(int(count), 0)
    if count == 0:
        return [0] * days_in_month

    base, remainder = divmod(count, days_in_month)
    daily = [base] * days_in_month
    if remainder == 0:
        return daily

    seed = int(hashlib.sha256(f"{year:04d}-{month:02d}".encode()).hexdigest()[:8], 16)
    start = seed % days_in_month
    step = max(1, days_in_month // remainder)
    used: set[int] = set()
    idx = start
    for _ in range(remainder):
        while idx in used:
            idx = (idx + 1) % days_in_month
        used.add(idx)
        daily[idx] += 1
        idx = (idx + step) % days_in_month
    return daily


def contributions_monthly_to_daily_series(
    contributions_monthly: Mapping[str, int] | None,
    *,
    reference_year: int | None = None,
) -> dict[str, int]:
    """Expand monthly contribution buckets into deterministic per-day series."""
    if not contributions_monthly:
        return {}

    ref_year = reference_year or dt_date.today().year
    month_counts: dict[tuple[int, int], int] = {}
    for key, value in contributions_monthly.items():
        k = str(key).strip()
        if _YYYY_MM_RE.match(k):
            year, month = map(int, k.split("-"))
        elif _MONTH_ONLY_RE.match(k):
            month = int(k)
            year = ref_year
        else:
            continue
        if not (1 <= month <= 12):
            continue
        month_counts[(year, month)] = max(0, int(value or 0))

    if not month_counts:
        return {}

    (start_y, start_m) = min(month_counts.keys())
    (end_y, end_m) = max(month_counts.keys())
    daily: dict[str, int] = {}
    for year, month in _iter_months(start_y, start_m, end_y, end_m):
        distributed = _distribute_monthly_count(year, month, month_counts.get((year, month), 0))
        for day, count in enumerate(distributed, start=1):
            iso = dt_date(year, month, day).isoformat()
            daily[iso] = count
    return daily

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


# ---------------------------------------------------------------------------
# SVG helpers (shared by animated art modules)
# ---------------------------------------------------------------------------

def xml_escape(s: str) -> str:
    """Escape XML special characters."""
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def svg_header(width: int, height: int) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}">\n'
    )


def svg_footer() -> str:
    return "</svg>\n"


def hsl_to_hex(h: float, s: float, lightness: float) -> str:
    """Convert HSL (all 0..1) to hex colour string."""
    import colorsys
    r, g, b = colorsys.hls_to_rgb(h, lightness, s)
    return "#{:02x}{:02x}{:02x}".format(int(r * 255), int(g * 255), int(b * 255))


def lerp_color(hex1: str, hex2: str, t: float) -> str:
    """Linearly interpolate between two hex colours."""
    r1, g1, b1 = int(hex1[1:3], 16), int(hex1[3:5], 16), int(hex1[5:7], 16)
    r2, g2, b2 = int(hex2[1:3], 16), int(hex2[3:5], 16), int(hex2[5:7], 16)
    r = int(r1 + (r2 - r1) * t)
    g = int(g1 + (g2 - g1) * t)
    b = int(b1 + (b2 - b1) * t)
    return "#{:02x}{:02x}{:02x}".format(
        max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b))
    )
