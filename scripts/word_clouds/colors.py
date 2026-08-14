"""Color palettes and classification for word cloud renderers."""

from __future__ import annotations

import colorsys
import math
from collections.abc import Callable, Sequence
from typing import Literal

PaletteTokenization = Literal["none", "coarse", "strong"]
WordColorFunc = Callable[[int, int], str]

_TOKEN_COUNTS: dict[PaletteTokenization, int | None] = {
    "none": None,
    "coarse": 8,
    "strong": 4,
}

_DEFAULT_HUE = 210  # blue


def _hsl_to_css(h: float, s: float, lightness: float) -> str:
    """Convert HSL (0-360, 0-1, 0-1) to hex CSS color."""
    r, g, b = colorsys.hls_to_rgb(h / 360.0, lightness, s)
    return f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}"


def _linear_to_srgb(c: float) -> float:
    """Linear RGB to sRGB gamma transfer function."""
    return 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055


def _oklch_to_hex(L: float, C: float, H: float) -> str:
    """Convert OKLCH to hex string. L in [0,1], C ~[0,0.4], H in degrees.

    Perceptually uniform color space -- equal steps in H produce visually
    equal hue shifts, unlike HSL.
    """
    a = C * math.cos(math.radians(H))
    b = C * math.sin(math.radians(H))
    lc = L + 0.3963377774 * a + 0.2158037573 * b
    mc = L - 0.1055613458 * a - 0.0638541728 * b
    sc = L - 0.0894841775 * a - 1.2914855480 * b
    l_ = lc**3
    m_ = mc**3
    s_ = sc**3
    rv = max(0, 4.0767416621 * l_ - 3.3077115913 * m_ + 0.2309699292 * s_)
    gv = max(0, -1.2684380046 * l_ + 2.6097574011 * m_ - 0.3413193965 * s_)
    bv = max(0, -0.0041960863 * l_ - 0.7034186147 * m_ + 1.7076147010 * s_)
    rv = max(0.0, min(1.0, _linear_to_srgb(rv)))
    gv = max(0.0, min(1.0, _linear_to_srgb(gv)))
    bv = max(0.0, min(1.0, _linear_to_srgb(bv)))
    return f"#{int(rv * 255):02x}{int(gv * 255):02x}{int(bv * 255):02x}"


def _interpolate_anchors(
    t: float,
    anchors: list[tuple[float, float, float]],
) -> tuple[float, float, float]:
    """Smoothly interpolate between OKLCH anchor points.

    *anchors* is a list of (hue, chroma, lightness) tuples.
    *t* ranges from 0 to 1.
    """
    pos = t * (len(anchors) - 1)
    lo = int(pos)
    hi = min(lo + 1, len(anchors) - 1)
    frac = pos - lo
    h = anchors[lo][0] + frac * (anchors[hi][0] - anchors[lo][0])
    c = anchors[lo][1] + frac * (anchors[hi][1] - anchors[lo][1])
    lv = anchors[lo][2] + frac * (anchors[hi][2] - anchors[lo][2])
    return h, c, lv


def primary_color_func(index: int, total: int) -> str:
    lightness = 0.35 + 0.3 * (index / max(total - 1, 1))
    return _hsl_to_css(_DEFAULT_HUE, 0.85, lightness)


def analogous_color_func(index: int, total: int) -> str:
    hue = (_DEFAULT_HUE - 30 + 60 * (index / max(total - 1, 1))) % 360
    return _hsl_to_css(hue, 0.75, 0.45)


def complementary_color_func(index: int, total: int) -> str:
    hue = _DEFAULT_HUE if index % 2 == 0 else (_DEFAULT_HUE + 180) % 360
    lightness = 0.35 + 0.25 * (index / max(total - 1, 1))
    return _hsl_to_css(hue, 0.8, lightness)


def triadic_color_func(index: int, total: int) -> str:
    hue = (_DEFAULT_HUE + 120 * (index % 3)) % 360
    lightness = 0.35 + 0.25 * (index / max(total - 1, 1))
    return _hsl_to_css(hue, 0.75, lightness)


def gradient_color_func(index: int, total: int) -> str:
    """Smooth multi-hue gradient: indigo -> blue -> teal -> emerald.

    Uses OKLCH for perceptually uniform spacing across the spectrum.
    """
    t = index / max(total - 1, 1)
    hue = 280 - t * 140  # 280 (indigo) -> 140 (emerald)
    lightness = 0.58 + 0.14 * math.sin(t * math.pi)
    chroma = 0.20 + 0.05 * math.sin(t * math.pi * 2)
    return _oklch_to_hex(lightness, chroma, hue)


def neon_on_dark_func(index: int, total: int) -> str:
    """Vivid neon colors cycling through electric blue, hot pink, cyber green, amber.

    Designed for dark backgrounds -- high chroma, high lightness.
    """
    neon_anchors: list[tuple[float, float, float]] = [
        (250, 0.28, 0.72),  # electric blue
        (330, 0.30, 0.70),  # hot pink
        (155, 0.28, 0.78),  # cyber green
        (80, 0.26, 0.80),  # amber/lime
    ]
    t = index / max(total - 1, 1)
    h, c, lv = _interpolate_anchors(t, neon_anchors)
    return _oklch_to_hex(lv, c, h)


def sunset_color_func(index: int, total: int) -> str:
    """Warm sunset gradient: deep plum -> magenta -> coral -> amber -> gold.

    Rich, warm palette inspired by golden-hour sky colors with smooth
    five-stop interpolation for nuance.
    """
    sunset_anchors: list[tuple[float, float, float]] = [
        (310, 0.22, 0.48),  # deep plum
        (340, 0.26, 0.58),  # magenta rose
        (15, 0.24, 0.65),  # warm coral
        (40, 0.22, 0.72),  # amber
        (65, 0.20, 0.78),  # gold
    ]
    t = index / max(total - 1, 1)
    h, c, lv = _interpolate_anchors(t, sunset_anchors)
    return _oklch_to_hex(lv, c, h)


def rainbow_color_func(index: int, total: int) -> str:
    """Full-spectrum rainbow sweep across 360 degrees of OKLCH hue.

    Maximum color diversity with controlled lightness for readability.
    """
    t = index / max(total - 1, 1)
    hue = t * 360.0
    lightness = 0.62 + 0.10 * math.sin(t * math.pi * 2)
    chroma = 0.22 + 0.04 * math.sin(t * math.pi * 3)
    return _oklch_to_hex(lightness, chroma, hue)


def ocean_color_func(index: int, total: int) -> str:
    """Deep ocean palette: navy -> sapphire -> cerulean -> aqua -> seafoam.

    Cool-toned, sophisticated palette with high contrast against white.
    """
    ocean_anchors: list[tuple[float, float, float]] = [
        (255, 0.18, 0.38),  # deep navy
        (240, 0.22, 0.48),  # sapphire
        (220, 0.20, 0.56),  # cerulean
        (195, 0.18, 0.62),  # aqua
        (170, 0.16, 0.68),  # seafoam
    ]
    t = index / max(total - 1, 1)
    h, c, lv = _interpolate_anchors(t, ocean_anchors)
    return _oklch_to_hex(lv, c, h)


def flora_color_func(index: int, total: int) -> str:
    """Botanical palette: sage -> emerald -> chartreuse -> olive -> teal.

    Earthy, natural tones with enough contrast for readability.
    """
    flora_anchors: list[tuple[float, float, float]] = [
        (155, 0.14, 0.52),  # sage
        (145, 0.20, 0.56),  # emerald
        (120, 0.22, 0.62),  # chartreuse
        (105, 0.16, 0.50),  # olive
        (180, 0.16, 0.48),  # teal
    ]
    t = index / max(total - 1, 1)
    h, c, lv = _interpolate_anchors(t, flora_anchors)
    return _oklch_to_hex(lv, c, h)


def aurora_color_func(index: int, total: int) -> str:
    """Northern lights palette: violet -> cyan -> green -> pink -> lavender.

    Ethereal, luminous colors inspired by aurora borealis.
    """
    aurora_anchors: list[tuple[float, float, float]] = [
        (290, 0.22, 0.55),  # violet
        (200, 0.20, 0.65),  # cyan
        (150, 0.22, 0.60),  # green
        (340, 0.20, 0.62),  # pink
        (280, 0.16, 0.68),  # lavender
    ]
    t = index / max(total - 1, 1)
    h, c, lv = _interpolate_anchors(t, aurora_anchors)
    return _oklch_to_hex(lv, c, h)


def ember_color_func(index: int, total: int) -> str:
    """Warm ember palette: crimson -> burnt orange -> copper -> terracotta.

    Rich, warm tones with depth, suitable for topics/skills emphasis.
    """
    ember_anchors: list[tuple[float, float, float]] = [
        (15, 0.24, 0.48),  # crimson
        (30, 0.22, 0.56),  # burnt orange
        (45, 0.20, 0.62),  # copper
        (25, 0.18, 0.52),  # terracotta
        (5, 0.22, 0.44),  # deep red
    ]
    t = index / max(total - 1, 1)
    h, c, lv = _interpolate_anchors(t, ember_anchors)
    return _oklch_to_hex(lv, c, h)


COLOR_FUNCS = {
    "primary": primary_color_func,
    "analogous": analogous_color_func,
    "complementary": complementary_color_func,
    "triadic": triadic_color_func,
    "gradient": gradient_color_func,
    "neon": neon_on_dark_func,
    "sunset": sunset_color_func,
    "rainbow": rainbow_color_func,
    "ocean": ocean_color_func,
    "flora": flora_color_func,
    "aurora": aurora_color_func,
    "ember": ember_color_func,
}


def normalize_color_func_name(name: str) -> str:
    """Return the registry key for a public palette or function name.

    Historical callers use names such as ``primary_color_func`` while the
    renderer registry uses the shorter ``primary`` key.  Normalizing at the
    boundary keeps both spellings deterministic without duplicating entries in
    :data:`COLOR_FUNCS`.
    """

    suffix = "_color_func"
    return name[: -len(suffix)] if name.endswith(suffix) else name


def _tokenized_index(index: int, total: int, token_count: int) -> tuple[int, int]:
    """Map a word index onto a bounded, evenly-spaced palette token set."""

    effective_count = max(1, min(token_count, total))
    if effective_count == 1 or total <= 1:
        return 0, effective_count
    ratio = max(0.0, min(1.0, index / (total - 1)))
    return round(ratio * (effective_count - 1)), effective_count


def _interpolate_hex_palette(palette: Sequence[str], index: int, total: int) -> str:
    """Interpolate an RGB color between validated ``#RRGGBB`` anchors."""

    if len(palette) == 1 or total <= 1:
        return palette[0]

    ratio = max(0.0, min(1.0, index / (total - 1)))
    position = ratio * (len(palette) - 1)
    lower = int(position)
    upper = min(lower + 1, len(palette) - 1)
    fraction = position - lower
    lower_rgb = tuple(
        int(palette[lower][offset : offset + 2], 16) for offset in (1, 3, 5)
    )
    upper_rgb = tuple(
        int(palette[upper][offset : offset + 2], 16) for offset in (1, 3, 5)
    )
    channels = tuple(
        round(start + fraction * (end - start))
        for start, end in zip(lower_rgb, upper_rgb, strict=True)
    )
    return f"#{channels[0]:02x}{channels[1]:02x}{channels[2]:02x}"


def resolve_color_func(
    name: str,
    *,
    tokenization: PaletteTokenization = "coarse",
    palette_override: Sequence[str] | None = None,
) -> WordColorFunc:
    """Resolve a deterministic renderer color function.

    ``none`` retains the palette's continuous progression. ``coarse`` samples
    at most eight recurring color tokens, while ``strong`` samples at most
    four.  An explicit palette is treated as interpolation anchors for
    ``none`` and as the authoritative token set for the discrete modes.
    """

    token_count = _TOKEN_COUNTS[tokenization]
    if palette_override:
        palette = tuple(palette_override)

        def explicit_palette(index: int, total: int) -> str:
            if token_count is None:
                return _interpolate_hex_palette(palette, index, total)
            token_index, effective_count = _tokenized_index(index, total, token_count)
            return _interpolate_hex_palette(palette, token_index, effective_count)

        return explicit_palette

    base_func = COLOR_FUNCS.get(normalize_color_func_name(name), primary_color_func)
    if token_count is None:
        return base_func

    def tokenized_palette(index: int, total: int) -> str:
        token_index, effective_count = _tokenized_index(index, total, token_count)
        return base_func(token_index, effective_count)

    return tokenized_palette


GITHUB_LIGHT_BG = "#ffffff"
GITHUB_DARK_BG = "#0d1117"
AA_LARGE_TEXT_CONTRAST = 3.0

TYPOGRAPHIC_PALETTE = [
    "#2563EB",  # royal blue
    "#059669",  # emerald
    "#D97706",  # amber
    "#7C3AED",  # violet
    "#DC2626",  # crimson
    "#0891B2",  # cyan
    "#BE185D",  # rose
    "#4F46E5",  # indigo
]

# Mid-tone fills that keep WCAG AA large-text contrast on both GitHub canvases.
CLUSTER_PALETTES: dict[str, list[str]] = {
    "AI/ML": ["#7C3AED", "#8B5CF6", "#6366F1", "#A855F7", "#9333EA"],
    "Web": ["#2563EB", "#3B82F6", "#0284C7", "#4F46E5", "#0891B2"],
    "Data": ["#047857", "#059669", "#0F766E", "#0D9488", "#0E7490"],
    "DevOps": ["#B45309", "#D97706", "#C2410C", "#EA580C", "#A16207"],
    "Languages": ["#DC2626", "#EF4444", "#E11D48", "#F43F5E", "#BE185D"],
    "Tools": ["#0E7490", "#0891B2", "#0284C7", "#0F766E", "#0D9488"],
    "Security": ["#BE185D", "#EC4899", "#DB2777", "#E11D48", "#C026D3"],
    "Other": ["#6B7280", "#71717A", "#64748B", "#78716C", "#737373"],
}

DOMAIN_CLUSTERS: dict[str, set[str]] = {
    "AI/ML": {
        "ai",
        "ml",
        "machine-learning",
        "deep-learning",
        "tensorflow",
        "pytorch",
        "neural-network",
        "nlp",
        "natural-language-processing",
        "computer-vision",
        "generative-ai",
        "llm",
        "transformers",
        "artificial-intelligence",
        "chatgpt",
        "openai",
        "gpt",
        "reinforcement-learning",
        "scikit-learn",
        "keras",
        "stable-diffusion",
        "langchain",
        "huggingface",
        "ai-agents",
        "agent",
    },
    "Web": {
        "react",
        "nextjs",
        "vue",
        "angular",
        "svelte",
        "html",
        "css",
        "javascript",
        "typescript",
        "nodejs",
        "deno",
        "bun",
        "webpack",
        "vite",
        "tailwindcss",
        "bootstrap",
        "frontend",
        "backend",
        "fullstack",
        "web",
        "rest",
        "graphql",
        "api",
        "http",
        "express",
        "fastapi",
        "django",
        "flask",
        "rails",
        "nextjs",
        "remix",
        "astro",
        "nuxt",
        "gatsby",
    },
    "Data": {
        "data",
        "data-science",
        "data-analysis",
        "data-engineering",
        "data-visualization",
        "database",
        "sql",
        "nosql",
        "postgresql",
        "mongodb",
        "redis",
        "elasticsearch",
        "pandas",
        "numpy",
        "scipy",
        "matplotlib",
        "jupyter",
        "jupyter-notebook",
        "spark",
        "hadoop",
        "etl",
        "analytics",
        "big-data",
        "data-structures",
        "bioinformatics",
        "statistics",
    },
    "DevOps": {
        "devops",
        "docker",
        "kubernetes",
        "terraform",
        "ansible",
        "ci-cd",
        "continuous-integration",
        "deployment",
        "aws",
        "azure",
        "gcp",
        "cloud",
        "linux",
        "nginx",
        "monitoring",
        "logging",
        "infrastructure",
        "serverless",
        "microservices",
        "helm",
        "github-actions",
        "gitlab",
        "jenkins",
    },
    "Languages": {
        "python",
        "rust",
        "go",
        "golang",
        "java",
        "kotlin",
        "swift",
        "c",
        "c-plus-plus",
        "cpp",
        "csharp",
        "ruby",
        "php",
        "perl",
        "scala",
        "haskell",
        "elixir",
        "clojure",
        "lua",
        "zig",
        "dart",
        "r",
        "julia",
        "fortran",
        "objective-c",
        "shell",
        "bash",
        "powershell",
    },
    "Tools": {
        "git",
        "github",
        "vscode",
        "neovim",
        "vim",
        "emacs",
        "terminal",
        "cli",
        "command-line",
        "dotfiles",
        "homebrew",
        "package-manager",
        "editor",
        "ide",
        "developer-tools",
        "productivity",
        "automation",
        "testing",
        "linter",
        "formatter",
        "code-quality",
        "code-review",
    },
    "Security": {
        "security",
        "cybersecurity",
        "cryptography",
        "encryption",
        "authentication",
        "oauth",
        "hacking",
        "penetration-testing",
        "bugbounty",
        "blockchain",
        "bitcoin",
        "ethereum",
        "cryptocurrency",
        "solidity",
        "web3",
        "defi",
    },
}


def _srgb_to_linear(c: float) -> float:
    """sRGB gamma to linear transfer function (inverse of _linear_to_srgb)."""
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _hex_to_oklch(hex_str: str) -> tuple[float, float, float]:
    """Convert hex color string to OKLCH (L, C, H_degrees).

    Inverse of ``_oklch_to_hex``.  Used for perceptually-uniform hue
    rotation of existing palette colors.
    """
    r = int(hex_str[1:3], 16) / 255.0
    g = int(hex_str[3:5], 16) / 255.0
    b = int(hex_str[5:7], 16) / 255.0
    rl = _srgb_to_linear(r)
    gl = _srgb_to_linear(g)
    bl = _srgb_to_linear(b)
    # Linear RGB → LMS (cube-root space)
    l_ = 0.4122214708 * rl + 0.5363325363 * gl + 0.0514459929 * bl
    m_ = 0.2119034982 * rl + 0.6806995451 * gl + 0.1073969566 * bl
    s_ = 0.0883024619 * rl + 0.2220049256 * gl + 0.6396926125 * bl
    lc = l_ ** (1 / 3) if l_ >= 0 else 0.0
    mc = m_ ** (1 / 3) if m_ >= 0 else 0.0
    sc = s_ ** (1 / 3) if s_ >= 0 else 0.0
    # LMS → OKLab
    L = 0.2104542553 * lc + 0.7936177850 * mc - 0.0040720468 * sc
    a = 1.9779984951 * lc - 2.4285922050 * mc + 0.4505937099 * sc
    b_val = 0.0259040371 * lc + 0.7827717662 * mc - 0.8086757660 * sc
    C = math.sqrt(a * a + b_val * b_val)
    H = math.degrees(math.atan2(b_val, a)) % 360
    return L, C, H


def make_shifted_color_func(
    base_func_name: str,
    hue_offset: float,
) -> Callable[[int, int], str]:
    """Create a color function with OKLCH hue rotation applied.

    Converts each color from the base palette to OKLCH, rotates the hue
    by *hue_offset* degrees, clamps lightness and chroma for readability,
    and converts back to hex.

    Works with all palette types (OKLCH and HSL based).

    Constraints (per color-science review):
    - Lightness L clamped to [0.50, 0.82] for contrast against dark bg
    - Chroma C clamped to [0.18, 0.30] for vivid visual weight
    """
    base_func = COLOR_FUNCS.get(base_func_name, ocean_color_func)

    def shifted(index: int, total: int) -> str:
        hex_color = base_func(index, total)
        L, C, H = _hex_to_oklch(hex_color)
        H = (H + hue_offset) % 360
        L = max(0.50, min(0.82, L))
        C = max(0.18, min(0.30, C))
        return _oklch_to_hex(L, C, H)

    return shifted


def _classify_word(word: str) -> str:
    """Return the cluster name for a given word, or 'Other'."""
    lower = word.lower().strip()
    for cluster, keywords in DOMAIN_CLUSTERS.items():
        if lower in keywords:
            return cluster
    return "Other"


def _hex_to_srgb(color: str) -> tuple[float, float, float]:
    """Parse ``#rgb`` / ``#rrggbb`` into 0-1 sRGB channels."""
    value = color.removeprefix("#")
    if len(value) == 3:
        value = "".join(channel * 2 for channel in value)
    if len(value) != 6:
        raise ValueError(f"Unsupported hex color: {color}")
    red = int(value[0:2], 16) / 255
    green = int(value[2:4], 16) / 255
    blue = int(value[4:6], 16) / 255
    return (red, green, blue)


def relative_luminance(color: str) -> float:
    """WCAG relative luminance of a hex color."""

    def _channel(component: float) -> float:
        return (
            component / 12.92
            if component <= 0.04045
            else ((component + 0.055) / 1.055) ** 2.4
        )

    red, green, blue = (_channel(component) for component in _hex_to_srgb(color))
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def contrast_ratio(foreground: str, background: str) -> float:
    """WCAG contrast ratio between two hex colors."""
    lighter, darker = sorted(
        (relative_luminance(foreground), relative_luminance(background)),
        reverse=True,
    )
    return (lighter + 0.05) / (darker + 0.05)


def composite_hex(foreground: str, background: str, opacity: float) -> str:
    """Alpha-composite ``foreground`` over ``background`` and return hex."""
    clamped = max(0.0, min(1.0, float(opacity)))
    fg_red, fg_green, fg_blue = _hex_to_srgb(foreground)
    bg_red, bg_green, bg_blue = _hex_to_srgb(background)
    red = fg_red * clamped + bg_red * (1.0 - clamped)
    green = fg_green * clamped + bg_green * (1.0 - clamped)
    blue = fg_blue * clamped + bg_blue * (1.0 - clamped)
    return (
        f"#{int(round(red * 255)):02X}"
        f"{int(round(green * 255)):02X}"
        f"{int(round(blue * 255)):02X}"
    )


def github_dual_surface_contrast(color: str, *, opacity: float = 1.0) -> float:
    """Worst-case contrast of ``color`` on GitHub light and dark canvases."""
    light = composite_hex(color, GITHUB_LIGHT_BG, opacity)
    dark = composite_hex(color, GITHUB_DARK_BG, opacity)
    return min(
        contrast_ratio(light, GITHUB_LIGHT_BG),
        contrast_ratio(dark, GITHUB_DARK_BG),
    )


def is_github_dual_surface_readable(
    color: str,
    *,
    opacity: float = 1.0,
    minimum: float = AA_LARGE_TEXT_CONTRAST,
) -> bool:
    """True when ``color`` meets large-text AA on both GitHub backgrounds."""
    return github_dual_surface_contrast(color, opacity=opacity) >= minimum


def github_readable_fills() -> tuple[str, ...]:
    """Typographic + cluster fills used by the shipped bake-off winner."""
    seen: list[str] = []
    for color in (
        *TYPOGRAPHIC_PALETTE,
        *(color for colors in CLUSTER_PALETTES.values() for color in colors),
    ):
        normalized = f"#{color.removeprefix('#').upper()}"
        if normalized not in seen:
            seen.append(normalized)
    return tuple(seen)


__all__ = [
    "_DEFAULT_HUE",
    "_hsl_to_css",
    "_linear_to_srgb",
    "_oklch_to_hex",
    "_interpolate_anchors",
    "primary_color_func",
    "analogous_color_func",
    "complementary_color_func",
    "triadic_color_func",
    "gradient_color_func",
    "neon_on_dark_func",
    "sunset_color_func",
    "rainbow_color_func",
    "ocean_color_func",
    "flora_color_func",
    "aurora_color_func",
    "ember_color_func",
    "COLOR_FUNCS",
    "GITHUB_LIGHT_BG",
    "GITHUB_DARK_BG",
    "AA_LARGE_TEXT_CONTRAST",
    "TYPOGRAPHIC_PALETTE",
    "CLUSTER_PALETTES",
    "DOMAIN_CLUSTERS",
    "_classify_word",
    "_hex_to_srgb",
    "relative_luminance",
    "contrast_ratio",
    "composite_hex",
    "github_dual_surface_contrast",
    "is_github_dual_surface_readable",
    "github_readable_fills",
    "_srgb_to_linear",
    "_hex_to_oklch",
    "make_shifted_color_func",
]
