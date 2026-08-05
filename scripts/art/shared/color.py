"""OKLCH / HSL color science and contrast helpers."""

from __future__ import annotations

import math

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
    l_ = lc**3
    m_ = mc**3
    s_ = sc**3
    r = max(0, 4.0767416621 * l_ - 3.3077115913 * m_ + 0.2309699292 * s_)
    g = max(0, -1.2684380046 * l_ + 2.6097574011 * m_ - 0.3413193965 * s_)
    bv = max(0, -0.0041960863 * l_ - 0.7034186147 * m_ + 1.7076147010 * s_)
    r = max(0, min(1, _linear_to_srgb(r)))
    g = max(0, min(1, _linear_to_srgb(g)))
    bv = max(0, min(1, _linear_to_srgb(bv)))
    return f"#{int(r * 255):02x}{int(g * 255):02x}{int(bv * 255):02x}"


def hsl_to_hex(h: float, s: float, lightness: float) -> str:
    """Convert HSL (all 0..1) to hex colour string."""
    import colorsys

    r, g, b = colorsys.hls_to_rgb(h, lightness, s)
    return f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}"


def lerp_color(hex1: str, hex2: str, t: float) -> str:
    """Linearly interpolate between two hex colours."""
    r1, g1, b1 = int(hex1[1:3], 16), int(hex1[3:5], 16), int(hex1[5:7], 16)
    r2, g2, b2 = int(hex2[1:3], 16), int(hex2[3:5], 16), int(hex2[5:7], 16)
    r = int(r1 + (r2 - r1) * t)
    g = int(g1 + (g2 - g1) * t)
    b = int(b1 + (b2 - b1) * t)
    return (
        f"#{max(0, min(255, r)):02x}{max(0, min(255, g)):02x}{max(0, min(255, b)):02x}"
    )


# ---------------------------------------------------------------------------
# Extended OKLCH color science (Phase 1)
# ---------------------------------------------------------------------------


def _srgb_to_linear(c: float) -> float:
    """sRGB gamma to linear transfer function (inverse of _linear_to_srgb)."""
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hex_to_oklch(hex_str: str) -> tuple[float, float, float]:
    """Convert hex color '#rrggbb' to OKLCH (L, C, H_degrees).

    L in [0,1], C ~[0,0.4], H in [0,360).
    Inverse of ``oklch()``.
    """
    r = int(hex_str[1:3], 16) / 255.0
    g = int(hex_str[3:5], 16) / 255.0
    b = int(hex_str[5:7], 16) / 255.0
    rl = _srgb_to_linear(r)
    gl = _srgb_to_linear(g)
    bl = _srgb_to_linear(b)
    l_ = 0.4122214708 * rl + 0.5363325363 * gl + 0.0514459929 * bl
    m_ = 0.2119034982 * rl + 0.6806995451 * gl + 0.1073969566 * bl
    s_ = 0.0883024619 * rl + 0.2220049256 * gl + 0.6396926125 * bl
    lc = l_ ** (1 / 3) if l_ >= 0 else 0.0
    mc = m_ ** (1 / 3) if m_ >= 0 else 0.0
    sc = s_ ** (1 / 3) if s_ >= 0 else 0.0
    L = 0.2104542553 * lc + 0.7936177850 * mc - 0.0040720468 * sc
    a = 1.9779984951 * lc - 2.4285922050 * mc + 0.4505937099 * sc
    b_val = 0.0259040371 * lc + 0.7827717662 * mc - 0.8086757660 * sc
    C = math.sqrt(a * a + b_val * b_val)
    H = math.degrees(math.atan2(b_val, a)) % 360
    return L, C, H


def oklch_gamut_map(L: float, C: float, H: float) -> tuple[float, float, float]:
    """Reduce chroma until the OKLCH triplet maps to a valid sRGB color.

    Binary-search: halves C until all RGB channels in [0, 1].
    Preserves hue and lightness — only chroma is reduced.
    """
    C * math.cos(math.radians(H))
    C * math.sin(math.radians(H))

    def _in_gamut(c_val: float) -> bool:
        ca = c_val * math.cos(math.radians(H))
        cb = c_val * math.sin(math.radians(H))
        lc = L + 0.3963377774 * ca + 0.2158037573 * cb
        mc = L - 0.1055613458 * ca - 0.0638541728 * cb
        sc = L - 0.0894841775 * ca - 1.2914855480 * cb
        l3 = lc**3
        m3 = mc**3
        s3 = sc**3
        r = 4.0767416621 * l3 - 3.3077115913 * m3 + 0.2309699292 * s3
        g = -1.2684380046 * l3 + 2.6097574011 * m3 - 0.3413193965 * s3
        bv = -0.0041960863 * l3 - 0.7034186147 * m3 + 1.7076147010 * s3
        eps = -0.001
        return (
            r >= eps
            and g >= eps
            and bv >= eps
            and r <= 1.001
            and g <= 1.001
            and bv <= 1.001
        )

    if _in_gamut(C):
        return L, C, H

    lo, hi = 0.0, C
    for _ in range(16):
        mid = (lo + hi) / 2
        if _in_gamut(mid):
            lo = mid
        else:
            hi = mid
    return L, lo, H


def oklch_lerp(hex1: str, hex2: str, t: float) -> str:
    """Perceptually uniform interpolation between two hex colors via OKLCH.

    Handles hue wrapping across the 0/360 boundary.
    *t* = 0.0 returns hex1, *t* = 1.0 returns hex2.
    """
    L1, C1, H1 = hex_to_oklch(hex1)
    L2, C2, H2 = hex_to_oklch(hex2)
    L = L1 + (L2 - L1) * t
    C = C1 + (C2 - C1) * t
    # Shortest-arc hue interpolation
    dh = H2 - H1
    if dh > 180:
        dh -= 360
    elif dh < -180:
        dh += 360
    H = (H1 + dh * t) % 360
    return oklch(L, C, H)


def oklch_gradient(anchors: list[tuple[float, float, float]], n: int) -> list[str]:
    """Generate *n* evenly-spaced hex colors along an OKLCH anchor path.

    *anchors*: list of (L, C, H) tuples defining the gradient stops.
    Uses linear interpolation with shortest-arc hue wrapping.
    """
    if n <= 0:
        return []
    if n == 1 or len(anchors) < 2:
        L, C, H = anchors[0] if anchors else (0.5, 0.0, 0)
        return [oklch(L, C, H)]
    colors: list[str] = []
    for i in range(n):
        pos = i / max(n - 1, 1) * (len(anchors) - 1)
        lo = int(pos)
        hi = min(lo + 1, len(anchors) - 1)
        frac = pos - lo
        L = anchors[lo][0] + frac * (anchors[hi][0] - anchors[lo][0])
        C = anchors[lo][1] + frac * (anchors[hi][1] - anchors[lo][1])
        dh = anchors[hi][2] - anchors[lo][2]
        if dh > 180:
            dh -= 360
        elif dh < -180:
            dh += 360
        H = (anchors[lo][2] + frac * dh) % 360
        colors.append(oklch(L, C, H))
    return colors


def wcag_contrast_ratio(hex_fg: str, hex_bg: str) -> float:
    """WCAG 2.1 contrast ratio between two hex colors. Range [1, 21]."""

    def _rel_lum(h: str) -> float:
        r = _srgb_to_linear(int(h[1:3], 16) / 255.0)
        g = _srgb_to_linear(int(h[3:5], 16) / 255.0)
        b = _srgb_to_linear(int(h[5:7], 16) / 255.0)
        return 0.2126 * r + 0.7152 * g + 0.0722 * b

    l1 = _rel_lum(hex_fg)
    l2 = _rel_lum(hex_bg)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def ensure_contrast(hex_fg: str, hex_bg: str, min_ratio: float = 4.5) -> str:
    """Adjust fg lightness in OKLCH to meet min_ratio against bg.

    Tries darkening first, then lightening if needed.
    """
    if wcag_contrast_ratio(hex_fg, hex_bg) >= min_ratio:
        return hex_fg
    L, C, H = hex_to_oklch(hex_fg)
    bg_L, _, _ = hex_to_oklch(hex_bg)
    # Try moving L away from bg_L
    for step in range(20):
        if bg_L > 0.5:
            candidate_L = max(0.0, L - step * 0.04)
        else:
            candidate_L = min(1.0, L + step * 0.04)
        candidate = oklch(candidate_L, C, H)
        if wcag_contrast_ratio(candidate, hex_bg) >= min_ratio:
            return candidate
    return hex_fg
