"""SVG-native word cloud renderers.

Four canonical SOTA approaches for generating word clouds as pure SVG:
  - WordleRenderer: classic Wordle spiral placement (Viegas & Wattenberg 2008)
  - ClusteredRenderer: semantic clustering + per-cluster Wordle placement
  - TypographicRenderer: editorial baseline-grid typography
  - ShapedRenderer: words packed inside a shape boundary

Visual enhancements:
  - OKLCH perceptually uniform color palettes (ocean, flora, sunset, aurora, etc.)
  - Power-law font sizing with exponent tuning for visual hierarchy
  - Multi-layer glow/shadow filters for depth and dimensionality
  - Font weight variation tied to frequency for typographic hierarchy
  - Curated rotation angles biased toward readability
  - Modern font stacks with system font fallbacks
  - Subtle background treatments with radial gradients
  - Opacity modulation for atmospheric depth
"""

from __future__ import annotations

import colorsys
import math
import random
import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
from dataclasses import dataclass

from .utils import get_logger

logger = get_logger(module=__name__)

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class PlacedWord:
    """A word that has been assigned a position in the SVG canvas."""

    text: str
    x: float
    y: float
    font_size: float
    rotation: float  # degrees
    color: str  # CSS color string
    font_weight: int = 400
    font_family: str = "Inter, 'Segoe UI', system-ui, -apple-system, sans-serif"
    opacity: float = 1.0


@dataclass(slots=True)
class BBox:
    """Axis-aligned bounding box."""

    x: float
    y: float
    w: float
    h: float

    @property
    def x2(self) -> float:
        return self.x + self.w

    @property
    def y2(self) -> float:
        return self.y + self.h

    def intersects(self, other: BBox) -> bool:
        return not (
            self.x2 <= other.x
            or other.x2 <= self.x
            or self.y2 <= other.y
            or other.y2 <= self.y
        )

    def corners(self) -> list[tuple[float, float]]:
        return [
            (self.x, self.y),
            (self.x2, self.y),
            (self.x, self.y2),
            (self.x2, self.y2),
        ]


# ---------------------------------------------------------------------------
# Color palettes
# ---------------------------------------------------------------------------

_DEFAULT_HUE = 210  # blue

# -- Modern font stack -------------------------------------------------------
# Prioritizes Inter (widely available, excellent for UI/data-viz), then
# system UI fonts, then generic sans-serif.
FONT_STACK = "Inter, 'Segoe UI', system-ui, -apple-system, sans-serif"
FONT_STACK_MONO = "'JetBrains Mono', 'Fira Code', 'SF Mono', 'Cascadia Code', monospace"

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
    l_ = lc ** 3
    m_ = mc ** 3
    s_ = sc ** 3
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


# -- Original (legacy) color functions --------------------------------------

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


# -- OKLCH-based color functions (perceptually uniform) ----------------------

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
    neon_anchors = [
        (250, 0.28, 0.72),   # electric blue
        (330, 0.30, 0.70),   # hot pink
        (155, 0.28, 0.78),   # cyber green
        (80, 0.26, 0.80),    # amber/lime
    ]
    t = index / max(total - 1, 1)
    h, c, lv = _interpolate_anchors(t, neon_anchors)
    return _oklch_to_hex(lv, c, h)


def sunset_color_func(index: int, total: int) -> str:
    """Warm sunset gradient: deep plum -> magenta -> coral -> amber -> gold.

    Rich, warm palette inspired by golden-hour sky colors with smooth
    five-stop interpolation for nuance.
    """
    sunset_anchors = [
        (310, 0.22, 0.48),   # deep plum
        (340, 0.26, 0.58),   # magenta rose
        (15,  0.24, 0.65),   # warm coral
        (40,  0.22, 0.72),   # amber
        (65,  0.20, 0.78),   # gold
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
    ocean_anchors = [
        (255, 0.18, 0.38),   # deep navy
        (240, 0.22, 0.48),   # sapphire
        (220, 0.20, 0.56),   # cerulean
        (195, 0.18, 0.62),   # aqua
        (170, 0.16, 0.68),   # seafoam
    ]
    t = index / max(total - 1, 1)
    h, c, lv = _interpolate_anchors(t, ocean_anchors)
    return _oklch_to_hex(lv, c, h)


def flora_color_func(index: int, total: int) -> str:
    """Botanical palette: sage -> emerald -> chartreuse -> olive -> teal.

    Earthy, natural tones with enough contrast for readability.
    """
    flora_anchors = [
        (155, 0.14, 0.52),   # sage
        (145, 0.20, 0.56),   # emerald
        (120, 0.22, 0.62),   # chartreuse
        (105, 0.16, 0.50),   # olive
        (180, 0.16, 0.48),   # teal
    ]
    t = index / max(total - 1, 1)
    h, c, lv = _interpolate_anchors(t, flora_anchors)
    return _oklch_to_hex(lv, c, h)


def aurora_color_func(index: int, total: int) -> str:
    """Northern lights palette: violet -> cyan -> green -> pink -> lavender.

    Ethereal, luminous colors inspired by aurora borealis.
    """
    aurora_anchors = [
        (290, 0.22, 0.55),   # violet
        (200, 0.20, 0.65),   # cyan
        (150, 0.22, 0.60),   # green
        (340, 0.20, 0.62),   # pink
        (280, 0.16, 0.68),   # lavender
    ]
    t = index / max(total - 1, 1)
    h, c, lv = _interpolate_anchors(t, aurora_anchors)
    return _oklch_to_hex(lv, c, h)


def ember_color_func(index: int, total: int) -> str:
    """Warm ember palette: crimson -> burnt orange -> copper -> terracotta.

    Rich, warm tones with depth, suitable for topics/skills emphasis.
    """
    ember_anchors = [
        (15, 0.24, 0.48),    # crimson
        (30, 0.22, 0.56),    # burnt orange
        (45, 0.20, 0.62),    # copper
        (25, 0.18, 0.52),    # terracotta
        (5, 0.22, 0.44),     # deep red
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

# Curated palette for the typographic renderer -- higher contrast, balanced hues
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

# Cluster-specific palettes (hue families) -- refined for cohesion and contrast
CLUSTER_PALETTES: dict[str, list[str]] = {
    "AI/ML": ["#6D28D9", "#7C3AED", "#8B5CF6", "#A78BFA", "#5B21B6"],
    "Web": ["#1D4ED8", "#2563EB", "#3B82F6", "#60A5FA", "#1E40AF"],
    "Data": ["#047857", "#059669", "#10B981", "#34D399", "#065F46"],
    "DevOps": ["#B45309", "#D97706", "#F59E0B", "#FBBF24", "#92400E"],
    "Languages": ["#B91C1C", "#DC2626", "#EF4444", "#F87171", "#991B1B"],
    "Tools": ["#0E7490", "#0891B2", "#06B6D4", "#22D3EE", "#155E75"],
    "Security": ["#9D174D", "#BE185D", "#EC4899", "#F472B6", "#831843"],
    "Other": ["#374151", "#4B5563", "#6B7280", "#9CA3AF", "#1F2937"],
}

# Semantic clusters for technology keywords
DOMAIN_CLUSTERS: dict[str, set[str]] = {
    "AI/ML": {
        "ai", "ml", "machine-learning", "deep-learning", "tensorflow",
        "pytorch", "neural-network", "nlp", "natural-language-processing",
        "computer-vision", "generative-ai", "llm", "transformers",
        "artificial-intelligence", "chatgpt", "openai", "gpt",
        "reinforcement-learning", "scikit-learn", "keras", "stable-diffusion",
        "langchain", "huggingface", "ai-agents", "agent",
    },
    "Web": {
        "react", "nextjs", "vue", "angular", "svelte", "html", "css",
        "javascript", "typescript", "nodejs", "deno", "bun", "webpack",
        "vite", "tailwindcss", "bootstrap", "frontend", "backend",
        "fullstack", "web", "rest", "graphql", "api", "http", "express",
        "fastapi", "django", "flask", "rails", "nextjs", "remix",
        "astro", "nuxt", "gatsby",
    },
    "Data": {
        "data", "data-science", "data-analysis", "data-engineering",
        "data-visualization", "database", "sql", "nosql", "postgresql",
        "mongodb", "redis", "elasticsearch", "pandas", "numpy", "scipy",
        "matplotlib", "jupyter", "jupyter-notebook", "spark", "hadoop",
        "etl", "analytics", "big-data", "data-structures",
        "bioinformatics", "statistics",
    },
    "DevOps": {
        "devops", "docker", "kubernetes", "terraform", "ansible",
        "ci-cd", "continuous-integration", "deployment", "aws", "azure",
        "gcp", "cloud", "linux", "nginx", "monitoring", "logging",
        "infrastructure", "serverless", "microservices", "helm",
        "github-actions", "gitlab", "jenkins",
    },
    "Languages": {
        "python", "rust", "go", "golang", "java", "kotlin", "swift",
        "c", "c-plus-plus", "cpp", "csharp", "ruby", "php", "perl",
        "scala", "haskell", "elixir", "clojure", "lua", "zig", "dart",
        "r", "julia", "fortran", "objective-c", "shell", "bash",
        "powershell",
    },
    "Tools": {
        "git", "github", "vscode", "neovim", "vim", "emacs", "terminal",
        "cli", "command-line", "dotfiles", "homebrew", "package-manager",
        "editor", "ide", "developer-tools", "productivity", "automation",
        "testing", "linter", "formatter", "code-quality", "code-review",
    },
    "Security": {
        "security", "cybersecurity", "cryptography", "encryption",
        "authentication", "oauth", "hacking", "penetration-testing",
        "bugbounty", "blockchain", "bitcoin", "ethereum", "cryptocurrency",
        "solidity", "web3", "defi",
    },
}


def _classify_word(word: str) -> str:
    """Return the cluster name for a given word, or 'Other'."""
    lower = word.lower().strip()
    for cluster, keywords in DOMAIN_CLUSTERS.items():
        if lower in keywords:
            return cluster
    return "Other"


# ---------------------------------------------------------------------------
# Font resolution
# ---------------------------------------------------------------------------

def resolve_preferred_wordcloud_font_path() -> str | None:
    """Try to find Monaspace Neon or Montserrat; return path or None."""
    import subprocess

    for font_name in ("MonaspaceNeon", "Monaspace Neon", "Montserrat"):
        try:
            result = subprocess.run(
                ["fc-list", f":family={font_name}", "file"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0 and result.stdout.strip():
                path = result.stdout.strip().split(":")[0].strip()
                if path:
                    return path
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue
    return None


# ---------------------------------------------------------------------------
# Base engine
# ---------------------------------------------------------------------------

class SvgWordCloudEngine(ABC):
    """Abstract base for SVG word cloud renderers."""

    def __init__(
        self,
        width: int = 800,
        height: int = 500,
        font_family: str = FONT_STACK,
        color_func_name: str = "gradient",
        seed: int | None = 42,
        padding: float = 2.0,
        min_font_size: float = 7.0,
        max_font_size: float = 72.0,
    ) -> None:
        self.width = width
        self.height = height
        self.font_family = font_family
        self.color_func = COLOR_FUNCS.get(color_func_name, primary_color_func)
        self.color_func_name = color_func_name
        self.seed = seed
        self.padding = padding
        self.min_font_size = min_font_size
        self.max_font_size = max_font_size
        self._rng = random.Random(seed)

    # -- Frequency scaling --------------------------------------------------

    def _frequency_to_size(
        self,
        freq: float,
        min_freq: float,
        max_freq: float,
    ) -> float:
        """Map a frequency value to a font size using power-law scaling.

        Uses exponent 0.5 (square root) to create a strong visual hierarchy
        where the top words are substantially larger, while mid-range words
        remain clearly readable. This produces a more dramatic and visually
        appealing size contrast than linear scaling.
        """
        if max_freq == min_freq:
            return (self.min_font_size + self.max_font_size) / 2
        t = (freq - min_freq) / (max_freq - min_freq)
        t_scaled = t ** 0.5
        return self.min_font_size + t_scaled * (self.max_font_size - self.min_font_size)

    def _frequency_to_weight(
        self,
        freq: float,
        min_freq: float,
        max_freq: float,
    ) -> int:
        """Map frequency to font-weight for visual hierarchy.

        Top-frequency words get bold (700-800), mid-range get medium (500),
        low-frequency get regular (400). Steps of 100.
        """
        if max_freq == min_freq:
            return 500
        t = (freq - min_freq) / (max_freq - min_freq)
        # Non-linear: emphasize boldness at the top end
        raw = 400 + (t ** 0.6) * 400  # 400 -> 800
        return int(round(raw / 100)) * 100

    def _frequency_to_opacity(
        self,
        freq: float,
        min_freq: float,
        max_freq: float,
    ) -> float:
        """Map frequency to opacity for atmospheric depth.

        Highest-frequency words are fully opaque; lowest get slightly
        transparent (0.65) to create a sense of depth without losing
        readability.
        """
        if max_freq == min_freq:
            return 1.0
        t = (freq - min_freq) / (max_freq - min_freq)
        return 0.65 + 0.35 * (t ** 0.4)

    # -- BBox estimation ----------------------------------------------------

    @staticmethod
    def _estimate_text_width(text: str, font_size: float, proportional: bool = True) -> float:
        """Heuristic text width based on character count and font size."""
        ratio = 0.55 if proportional else 0.60
        return len(text) * font_size * ratio

    @staticmethod
    def _estimate_text_height(font_size: float) -> float:
        return font_size * 1.2

    def _estimate_bbox(
        self,
        text: str,
        font_size: float,
        x: float,
        y: float,
        rotation: float = 0,
    ) -> BBox:
        """Compute the AABB for placed text, accounting for rotation.

        Handles arbitrary rotation angles by computing the rotated bounding
        box envelope, not just axis-aligned 90-degree swaps.
        """
        w = self._estimate_text_width(text, font_size)
        h = self._estimate_text_height(font_size)
        if rotation != 0:
            rad = math.radians(abs(rotation))
            cos_a = abs(math.cos(rad))
            sin_a = abs(math.sin(rad))
            rw = w * cos_a + h * sin_a
            rh = w * sin_a + h * cos_a
            w, h = rw, rh
        return BBox(x - w / 2, y - h / 2, w + self.padding, h + self.padding)

    # -- Collision detection ------------------------------------------------

    @staticmethod
    def _check_collision(bbox: BBox, placed_bboxes: list[BBox]) -> bool:
        """Return True if *bbox* overlaps any already-placed bbox."""
        for pb in placed_bboxes:
            if bbox.intersects(pb):
                return True
        return False

    def _in_bounds(self, bbox: BBox) -> bool:
        """Return True if bbox is fully inside the canvas."""
        return (
            bbox.x >= 0
            and bbox.y >= 0
            and bbox.x2 <= self.width
            and bbox.y2 <= self.height
        )

    # -- SVG rendering ------------------------------------------------------

    @staticmethod
    def _add_glow_filter(root: ET.Element) -> ET.Element:
        """Add SVG filter definitions to the root element.

        Creates two filters:
        - ``wc-glow``: soft colored glow behind the top 20% of words, giving
          them a luminous halo effect that suggests importance and depth.
        - ``wc-shadow``: subtle drop shadow for secondary words, adding a
          gentle lift off the background.

        Returns the <defs> element so callers can append additional definitions.
        """
        defs = ET.SubElement(root, "defs")

        # Primary glow for large/important words
        filt = ET.SubElement(
            defs, "filter",
            id="wc-glow",
            x="-30%", y="-30%",
            width="160%", height="160%",
        )
        # Layer 1: soft outer glow
        ET.SubElement(
            filt, "feGaussianBlur",
            attrib={"in": "SourceGraphic", "stdDeviation": "2.5", "result": "glow1"},
        )
        # Layer 2: tighter inner glow for crispness
        ET.SubElement(
            filt, "feGaussianBlur",
            attrib={"in": "SourceGraphic", "stdDeviation": "0.8", "result": "glow2"},
        )
        merge = ET.SubElement(filt, "feMerge")
        ET.SubElement(merge, "feMergeNode", attrib={"in": "glow1"})
        ET.SubElement(merge, "feMergeNode", attrib={"in": "glow2"})
        ET.SubElement(merge, "feMergeNode", attrib={"in": "SourceGraphic"})

        # Subtle drop shadow for mid-tier words
        shadow_filt = ET.SubElement(
            defs, "filter",
            id="wc-shadow",
            x="-10%", y="-10%",
            width="120%", height="120%",
        )
        ET.SubElement(
            shadow_filt, "feDropShadow",
            attrib={
                "dx": "0", "dy": "1",
                "stdDeviation": "0.5",
                "flood-color": "#00000020",
            },
        )

        return defs

    def _glow_size_threshold(self, placed_words: list[PlacedWord]) -> float:
        """Return the font size threshold above which glow is applied (top 20%)."""
        if not placed_words:
            return float("inf")
        sizes = sorted((pw.font_size for pw in placed_words), reverse=True)
        cutoff_idx = max(1, int(len(sizes) * 0.2))
        return sizes[min(cutoff_idx, len(sizes) - 1)]

    def render_svg(self, placed_words: list[PlacedWord]) -> str:
        """Render placed words into a polished SVG with layered visual effects.

        Visual hierarchy is achieved through four tiers:
        - **Tier 1** (top ~10%): glow filter + bold weight + letter-spacing
        - **Tier 2** (top ~30%): drop shadow + semi-bold weight
        - **Tier 3** (middle): standard rendering, medium weight
        - **Tier 4** (smallest): reduced opacity for atmospheric depth
        """
        root = ET.Element(
            "svg",
            xmlns="http://www.w3.org/2000/svg",
            width=str(self.width),
            height=str(self.height),
            viewBox=f"0 0 {self.width} {self.height}",
        )

        # Add filter definitions
        defs = self._add_glow_filter(root)

        # Soft radial vignette background -- white center fading to a very
        # faint cool gray at the edges, providing subtle depth without
        # competing with the words.
        radial = ET.SubElement(
            defs, "radialGradient",
            id="wc-bg-grad",
            cx="50%", cy="50%", r="75%",
        )
        ET.SubElement(radial, "stop", offset="0%", attrib={
            "stop-color": "#fafbfc", "stop-opacity": "1",
        })
        ET.SubElement(radial, "stop", offset="100%", attrib={
            "stop-color": "#f0f1f3", "stop-opacity": "1",
        })

        # Background rect
        ET.SubElement(
            root,
            "rect",
            width=str(self.width),
            height=str(self.height),
            fill="url(#wc-bg-grad)",
        )

        # Compute tier thresholds from placed word sizes
        glow_threshold = self._glow_size_threshold(placed_words)

        # Top ~10% for letter-spacing / tier-1 treatment
        tier1_threshold = float("inf")
        # Top ~30% for shadow / tier-2 treatment
        tier2_threshold = float("inf")
        if placed_words:
            sizes = sorted((pw.font_size for pw in placed_words), reverse=True)
            t1_idx = max(1, int(len(sizes) * 0.10))
            tier1_threshold = sizes[min(t1_idx, len(sizes) - 1)]
            t2_idx = max(1, int(len(sizes) * 0.30))
            tier2_threshold = sizes[min(t2_idx, len(sizes) - 1)]

        for pw in placed_words:
            attrs: dict[str, str] = {
                "x": f"{pw.x:.1f}",
                "y": f"{pw.y:.1f}",
                "font-size": f"{pw.font_size:.1f}",
                "fill": pw.color,
                "font-family": pw.font_family or self.font_family,
                "font-weight": str(pw.font_weight),
                "text-anchor": "middle",
                "dominant-baseline": "central",
            }

            # Opacity for atmospheric depth
            if pw.opacity < 1.0:
                attrs["opacity"] = f"{pw.opacity:.2f}"

            if pw.rotation != 0:
                attrs["transform"] = (
                    f"rotate({pw.rotation:.1f},{pw.x:.1f},{pw.y:.1f})"
                )

            # Tier 1: largest words get luminous glow + generous letter-spacing
            if pw.font_size >= glow_threshold:
                attrs["filter"] = "url(#wc-glow)"
            # Tier 2: mid-large words get subtle drop shadow
            elif pw.font_size >= tier2_threshold:
                attrs["filter"] = "url(#wc-shadow)"

            # Letter-spacing scales with font size for top words
            if pw.font_size >= tier1_threshold:
                spacing = max(0.5, pw.font_size * 0.02)
                attrs["letter-spacing"] = f"{spacing:.1f}"

            elem = ET.SubElement(root, "text", attrib=attrs)
            elem.text = pw.text

        ET.indent(root)
        return ET.tostring(root, encoding="unicode", xml_declaration=False)

    # -- Public interface ---------------------------------------------------

    @abstractmethod
    def place_words(
        self,
        frequencies: dict[str, float],
    ) -> list[PlacedWord]:
        """Place words on the canvas and return their positions."""
        ...

    def generate(self, frequencies: dict[str, float]) -> str:
        """Full pipeline: place words then render SVG."""
        placed = self.place_words(frequencies)
        return self.render_svg(placed)


# ---------------------------------------------------------------------------
# Approach A: Wordle renderer
# ---------------------------------------------------------------------------

class WordleRenderer(SvgWordCloudEngine):
    """Classic Wordle spiral-placement algorithm.

    Words are placed largest-first, spiraling outward from the center until
    a collision-free position is found.

    Enhanced with:
    - Slight random rotation angles (-15 to +15 degrees) for organic variety
    - Tighter spiral step for denser packing
    - Power-law font sizing (inherited from base)
    """

    def __init__(
        self,
        *,
        rotation_choices: list[float] | None = None,
        spiral_tightness: float = 0.5,
        allow_angled: bool = True,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        # Rotation strongly biased toward horizontal for readability,
        # with occasional 90-degree and subtle tilts for organic variety.
        # Avoids extreme angles (45, -45) that hurt legibility.
        if rotation_choices is not None:
            self.rotation_choices = rotation_choices
        elif allow_angled:
            self.rotation_choices = [0, 0, 0, 0, 0, 0, 90, 90, -8, 8, -5, 5]
        else:
            self.rotation_choices = [0, 90]
        self.spiral_tightness = spiral_tightness

    def _spiral_positions(
        self,
        cx: float,
        cy: float,
        step_size: float,
        max_steps: int = 10000,
    ):
        """Yield (x, y) along an Archimedean spiral.

        ``spiral_tightness`` controls the angular step: smaller values sample
        more densely (more candidate positions per revolution) for tighter
        packing.  The radial expansion ``b`` is scaled so the spiral always
        reaches the canvas diagonal within *max_steps*.
        """
        angular_step = self.spiral_tightness * 0.1  # 0.5*0.1 = 0.05
        # Ensure the spiral can reach every corner of the canvas
        max_theta = max_steps * angular_step
        canvas_diag = math.hypot(self.width, self.height) / 2
        b = max(step_size * 0.3, canvas_diag / max(max_theta, 1.0))
        for i in range(max_steps):
            theta = i * angular_step
            r = b * theta
            x = cx + r * math.cos(theta)
            y = cy + r * math.sin(theta)
            yield x, y

    def place_words(
        self,
        frequencies: dict[str, float],
    ) -> list[PlacedWord]:
        if not frequencies:
            return []

        sorted_words = sorted(frequencies.items(), key=lambda kv: kv[1], reverse=True)
        min_freq = min(frequencies.values())
        max_freq = max(frequencies.values())
        total = len(sorted_words)
        cx, cy = self.width / 2, self.height / 2

        # Golden angle dispersion — adjacent words get maximally contrasting hues
        _GOLDEN_ANGLE_FRAC = (math.sqrt(5) - 1) / 2  # ~0.618

        placed: list[PlacedWord] = []
        placed_bboxes: list[BBox] = []
        _ABSOLUTE_MIN_FONT = 4.0

        for idx, (word, freq) in enumerate(sorted_words):
            font_size = self._frequency_to_size(freq, min_freq, max_freq)
            font_weight = self._frequency_to_weight(freq, min_freq, max_freq)
            opacity = self._frequency_to_opacity(freq, min_freq, max_freq)
            # Large words stay horizontal for readability; smaller ones get rotation
            if font_size > (self.min_font_size + self.max_font_size) * 0.6:
                rotation = self._rng.choice([0, 0, 0, 0, 90])
            else:
                rotation = self._rng.choice(self.rotation_choices)
            color_idx = int(((idx * _GOLDEN_ANGLE_FRAC) % 1.0) * total)
            color = self.color_func(color_idx, total)

            step = max(0.8, font_size * 0.08)
            found = False
            for x, y in self._spiral_positions(cx, cy, step):
                bbox = self._estimate_bbox(word, font_size, x, y, rotation)
                if self._in_bounds(bbox) and not self._check_collision(bbox, placed_bboxes):
                    placed.append(
                        PlacedWord(
                            text=word,
                            x=x,
                            y=y,
                            font_size=font_size,
                            rotation=rotation,
                            color=color,
                            font_weight=font_weight,
                            font_family=self.font_family,
                            opacity=opacity,
                        )
                    )
                    placed_bboxes.append(bbox)
                    found = True
                    break

            if not found:
                # Try with progressively reduced font size as fallback
                for scale in (0.7, 0.5, 0.35, 0.25, 0.15):
                    reduced = font_size * scale
                    if reduced < _ABSOLUTE_MIN_FONT:
                        break
                    for x, y in self._spiral_positions(cx, cy, max(0.8, reduced * 0.08)):
                        bbox = self._estimate_bbox(word, reduced, x, y, 0)
                        if self._in_bounds(bbox) and not self._check_collision(bbox, placed_bboxes):
                            placed.append(
                                PlacedWord(
                                    text=word,
                                    x=x,
                                    y=y,
                                    font_size=reduced,
                                    rotation=0,
                                    color=color,
                                    font_weight=font_weight,
                                    font_family=self.font_family,
                                    opacity=opacity,
                                )
                            )
                            placed_bboxes.append(bbox)
                            found = True
                            break
                    if found:
                        break

            # Grid-scan final fallback -- guarantees placement
            if not found:
                grid_size = _ABSOLUTE_MIN_FONT
                for gy in range(0, int(self.height), int(grid_size * 2)):
                    if found:
                        break
                    for gx in range(0, int(self.width), int(grid_size * 2)):
                        bbox = self._estimate_bbox(word, grid_size, gx, gy, 0)
                        if self._in_bounds(bbox) and not self._check_collision(bbox, placed_bboxes):
                            placed.append(
                                PlacedWord(
                                    text=word,
                                    x=gx,
                                    y=gy,
                                    font_size=grid_size,
                                    rotation=0,
                                    color=color,
                                    font_weight=400,
                                    font_family=self.font_family,
                                    opacity=0.6,
                                )
                            )
                            placed_bboxes.append(bbox)
                            found = True
                            break

        if total > 0:
            fill_ratio = len(placed) / total
            if fill_ratio < 1.0:
                logger.warning(
                    "WordleRenderer: placed %d/%d words (%.0f%%).",
                    len(placed), total, fill_ratio * 100,
                )

        return placed


# ---------------------------------------------------------------------------
# Approach B: Clustered renderer
# ---------------------------------------------------------------------------

class ClusteredRenderer(SvgWordCloudEngine):
    """Semantic clustering with per-cluster Wordle placement.

    Words are grouped by domain (AI/ML, Web, Data, DevOps, Languages, Tools,
    Security, Other), each cluster gets a canvas region, and within each
    region a Wordle spiral places the words.
    """

    def __init__(
        self,
        *,
        show_cluster_labels: bool = True,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.show_cluster_labels = show_cluster_labels

    def _assign_sectors(
        self, cluster_names: list[str],
    ) -> dict[str, tuple[float, float, float, float]]:
        """Partition the canvas into rectangular regions for each cluster.

        Returns {cluster_name: (x, y, w, h)}.
        """
        n = len(cluster_names)
        if n == 0:
            return {}

        # Determine grid layout
        cols = math.ceil(math.sqrt(n))
        rows = math.ceil(n / cols)
        cell_w = self.width / cols
        cell_h = self.height / rows

        sectors: dict[str, tuple[float, float, float, float]] = {}
        for i, name in enumerate(cluster_names):
            r = i // cols
            c = i % cols
            sectors[name] = (c * cell_w, r * cell_h, cell_w, cell_h)
        return sectors

    def place_words(
        self,
        frequencies: dict[str, float],
    ) -> list[PlacedWord]:
        if not frequencies:
            return []

        # Classify words into clusters
        clusters: dict[str, dict[str, float]] = {}
        for word, freq in frequencies.items():
            cluster = _classify_word(word)
            clusters.setdefault(cluster, {})[word] = freq

        # Sort clusters by total weight (largest first)
        sorted_clusters = sorted(
            clusters.keys(),
            key=lambda c: sum(clusters[c].values()),
            reverse=True,
        )
        sectors = self._assign_sectors(sorted_clusters)

        all_freqs = list(frequencies.values())
        min_freq = min(all_freqs)
        max_freq = max(all_freqs)

        placed: list[PlacedWord] = []
        placed_bboxes: list[BBox] = []

        for cluster_name in sorted_clusters:
            sx, sy, sw, sh = sectors[cluster_name]
            cx, cy = sx + sw / 2, sy + sh / 2
            palette = CLUSTER_PALETTES.get(cluster_name, CLUSTER_PALETTES["Other"])

            # Optional faint cluster label -- rendered as a watermark behind words
            if self.show_cluster_labels:
                label_size = min(sw, sh) * 0.16
                placed.append(
                    PlacedWord(
                        text=cluster_name,
                        x=cx,
                        y=cy,
                        font_size=label_size,
                        rotation=0,
                        color="#e8eaed",  # very faint gray watermark
                        font_weight=200,
                        font_family=self.font_family,
                        opacity=0.5,
                    )
                )

            sorted_words = sorted(
                clusters[cluster_name].items(), key=lambda kv: kv[1], reverse=True
            )

            for local_idx, (word, freq) in enumerate(sorted_words):
                font_size = self._frequency_to_size(freq, min_freq, max_freq)
                font_weight = self._frequency_to_weight(freq, min_freq, max_freq)
                opacity = self._frequency_to_opacity(freq, min_freq, max_freq)
                # Scale font down slightly so words fit in their sector
                font_size = min(font_size, sh * 0.4, sw * 0.3)
                if font_size < self.min_font_size:
                    font_size = self.min_font_size

                color = palette[local_idx % len(palette)]
                rotation = self._rng.choice([0, 0, 0, 0, 90])  # strong horizontal bias

                step = max(1.0, font_size * 0.12)
                found = False
                for x, y in self._spiral_gen(cx, cy, step):
                    bbox = self._estimate_bbox(word, font_size, x, y, rotation)
                    # Must stay within sector and not collide
                    if (
                        bbox.x >= sx
                        and bbox.y >= sy
                        and bbox.x2 <= sx + sw
                        and bbox.y2 <= sy + sh
                        and not self._check_collision(bbox, placed_bboxes)
                    ):
                        placed.append(
                            PlacedWord(
                                text=word,
                                x=x,
                                y=y,
                                font_size=font_size,
                                rotation=rotation,
                                color=color,
                                font_weight=font_weight,
                                font_family=self.font_family,
                                opacity=opacity,
                            )
                        )
                        placed_bboxes.append(bbox)
                        found = True
                        break

                if not found:
                    # Try smaller size
                    reduced = font_size * 0.5
                    if reduced >= self.min_font_size:
                        for x, y in self._spiral_gen(cx, cy, max(1.0, reduced * 0.12)):
                            bbox = self._estimate_bbox(word, reduced, x, y, 0)
                            if (
                                bbox.x >= sx
                                and bbox.y >= sy
                                and bbox.x2 <= sx + sw
                                and bbox.y2 <= sy + sh
                                and not self._check_collision(bbox, placed_bboxes)
                            ):
                                placed.append(
                                    PlacedWord(
                                        text=word,
                                        x=x,
                                        y=y,
                                        font_size=reduced,
                                        rotation=0,
                                        color=color,
                                        font_weight=font_weight,
                                        font_family=self.font_family,
                                        opacity=opacity,
                                    )
                                )
                                placed_bboxes.append(bbox)
                                break

        return placed

    def _spiral_gen(
        self, cx: float, cy: float, step: float, max_steps: int = 1500,
    ):
        """Yield positions along an Archimedean spiral."""
        b = step
        for i in range(max_steps):
            theta = i * 0.1
            r = b * theta
            yield cx + r * math.cos(theta), cy + r * math.sin(theta)


# ---------------------------------------------------------------------------
# Approach C: Typographic renderer
# ---------------------------------------------------------------------------

class TypographicRenderer(SvgWordCloudEngine):
    """Editorial baseline-grid typography.

    Words flow left-to-right on a baseline grid with variable font weights.
    Horizontal only (no rotation) for maximum readability.
    """

    def __init__(
        self,
        *,
        palette: list[str] | None = None,
        line_spacing: float = 1.4,
        margin: float = 28.0,
        weight_range: tuple[int, int] = (300, 800),
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.palette = palette or list(TYPOGRAPHIC_PALETTE)
        self.line_spacing = line_spacing
        self.margin = margin
        self.weight_range = weight_range

    def _freq_to_weight(self, freq: float, min_freq: float, max_freq: float) -> int:
        """Map frequency to font-weight (100-900 in steps of 100)."""
        if max_freq == min_freq:
            return 500
        t = (freq - min_freq) / (max_freq - min_freq)
        raw = self.weight_range[0] + t * (self.weight_range[1] - self.weight_range[0])
        return int(round(raw / 100)) * 100

    def place_words(
        self,
        frequencies: dict[str, float],
    ) -> list[PlacedWord]:
        if not frequencies:
            return []

        # Sort by frequency descending so important words come first
        sorted_words = sorted(frequencies.items(), key=lambda kv: kv[1], reverse=True)
        min_freq = min(frequencies.values())
        max_freq = max(frequencies.values())

        placed: list[PlacedWord] = []
        cursor_x = self.margin
        cursor_y = self.margin + self.max_font_size * 0.6
        line_max_h = 0.0

        for idx, (word, freq) in enumerate(sorted_words):
            font_size = self._frequency_to_size(freq, min_freq, max_freq)
            weight = self._freq_to_weight(freq, min_freq, max_freq)
            opacity = self._frequency_to_opacity(freq, min_freq, max_freq)
            color = self.palette[idx % len(self.palette)]
            word_w = self._estimate_text_width(word, font_size)
            word_h = self._estimate_text_height(font_size) * self.line_spacing

            # Word wrapping
            if cursor_x + word_w + self.margin > self.width:
                cursor_x = self.margin
                cursor_y += line_max_h
                line_max_h = 0.0

            # Out of vertical space
            if cursor_y + word_h / 2 > self.height - self.margin:
                break

            line_max_h = max(line_max_h, word_h)

            placed.append(
                PlacedWord(
                    text=word,
                    x=cursor_x + word_w / 2,
                    y=cursor_y,
                    font_size=font_size,
                    rotation=0,
                    color=color,
                    font_weight=weight,
                    font_family=self.font_family,
                    opacity=opacity,
                )
            )

            cursor_x += word_w + font_size * 0.5  # slightly more generous word gap

        return placed


# ---------------------------------------------------------------------------
# Approach D: Shaped renderer
# ---------------------------------------------------------------------------

# Built-in shapes as normalized polygons (0-1 coordinate space)
_SHAPE_POLYGONS: dict[str, list[tuple[float, float]]] = {
    "hexagon": [
        (0.5, 0.0),
        (1.0, 0.25),
        (1.0, 0.75),
        (0.5, 1.0),
        (0.0, 0.75),
        (0.0, 0.25),
    ],
    "circle": [
        (0.5 + 0.5 * math.cos(2 * math.pi * i / 36), 0.5 + 0.5 * math.sin(2 * math.pi * i / 36))
        for i in range(36)
    ],
    "rounded-rect": [
        # Approximate rounded rectangle with 8 segments per corner
        *[
            (0.15 - 0.15 * math.cos(math.pi / 2 * i / 4),
             0.15 - 0.15 * math.sin(math.pi / 2 * i / 4))
            for i in range(5)
        ],
        *[
            (0.85 + 0.15 * math.sin(math.pi / 2 * i / 4),
             0.15 - 0.15 * math.cos(math.pi / 2 * i / 4))
            for i in range(5)
        ],
        *[
            (0.85 + 0.15 * math.cos(math.pi / 2 * i / 4),
             0.85 + 0.15 * math.sin(math.pi / 2 * i / 4))
            for i in range(5)
        ],
        *[
            (0.15 - 0.15 * math.sin(math.pi / 2 * i / 4),
             0.85 + 0.15 * math.cos(math.pi / 2 * i / 4))
            for i in range(5)
        ],
    ],
    "diamond": [
        (0.5, 0.0),
        (1.0, 0.5),
        (0.5, 1.0),
        (0.0, 0.5),
    ],
    "star": [
        (0.5, 0.0),
        (0.6, 0.35),
        (1.0, 0.35),
        (0.68, 0.57),
        (0.79, 0.91),
        (0.5, 0.7),
        (0.21, 0.91),
        (0.32, 0.57),
        (0.0, 0.35),
        (0.4, 0.35),
    ],
}


def _point_in_polygon(
    px: float, py: float, polygon: list[tuple[float, float]]
) -> bool:
    """Ray-casting point-in-polygon test."""
    n = len(polygon)
    inside = False
    j = n - 1
    for i in range(n):
        xi, yi = polygon[i]
        xj, yj = polygon[j]
        if ((yi > py) != (yj > py)) and (px < (xj - xi) * (py - yi) / (yj - yi) + xi):
            inside = not inside
        j = i
    return inside


class ShapedRenderer(SvgWordCloudEngine):
    """Words packed inside a shape boundary.

    Largest words go at the center; smaller words fill the edges.
    Shape options: hexagon, circle, rounded-rect, diamond, star.
    """

    def __init__(
        self,
        *,
        shape: str = "hexagon",
        show_shape_outline: bool = False,
        outline_color: str = "#d1d5db",
        outline_width: float = 1.5,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.shape_name = shape
        self.show_shape_outline = show_shape_outline
        self.outline_color = outline_color
        self.outline_width = outline_width

        # Scale normalized polygon to canvas with a small margin
        margin_frac = 0.05
        raw = _SHAPE_POLYGONS.get(shape, _SHAPE_POLYGONS["hexagon"])
        self._polygon = [
            (
                margin_frac * self.width + x * self.width * (1 - 2 * margin_frac),
                margin_frac * self.height + y * self.height * (1 - 2 * margin_frac),
            )
            for x, y in raw
        ]

    def _all_corners_in_shape(self, bbox: BBox) -> bool:
        """Check that all 4 bbox corners are inside the shape polygon."""
        for cx, cy in bbox.corners():
            if not _point_in_polygon(cx, cy, self._polygon):
                return False
        return True

    def place_words(
        self,
        frequencies: dict[str, float],
    ) -> list[PlacedWord]:
        if not frequencies:
            return []

        sorted_words = sorted(frequencies.items(), key=lambda kv: kv[1], reverse=True)
        min_freq = min(frequencies.values())
        max_freq = max(frequencies.values())
        total = len(sorted_words)
        cx, cy = self.width / 2, self.height / 2

        placed: list[PlacedWord] = []
        placed_bboxes: list[BBox] = []

        for idx, (word, freq) in enumerate(sorted_words):
            font_size = self._frequency_to_size(freq, min_freq, max_freq)
            font_weight = self._frequency_to_weight(freq, min_freq, max_freq)
            opacity = self._frequency_to_opacity(freq, min_freq, max_freq)
            rotation = self._rng.choice([0, 0, 0, 0, 90])  # strong horizontal bias
            color = self.color_func(idx, total)

            step = max(1.0, font_size * 0.12)
            found = False
            for x, y in self._spiral_gen(cx, cy, step):
                bbox = self._estimate_bbox(word, font_size, x, y, rotation)
                if (
                    self._all_corners_in_shape(bbox)
                    and not self._check_collision(bbox, placed_bboxes)
                ):
                    placed.append(
                        PlacedWord(
                            text=word,
                            x=x,
                            y=y,
                            font_size=font_size,
                            rotation=rotation,
                            color=color,
                            font_weight=font_weight,
                            font_family=self.font_family,
                            opacity=opacity,
                        )
                    )
                    placed_bboxes.append(bbox)
                    found = True
                    break

            if not found:
                for scale in (0.6, 0.4):
                    reduced = font_size * scale
                    if reduced < self.min_font_size:
                        break
                    for x, y in self._spiral_gen(cx, cy, max(1.0, reduced * 0.12)):
                        bbox = self._estimate_bbox(word, reduced, x, y, 0)
                        if (
                            self._all_corners_in_shape(bbox)
                            and not self._check_collision(bbox, placed_bboxes)
                        ):
                            placed.append(
                                PlacedWord(
                                    text=word,
                                    x=x,
                                    y=y,
                                    font_size=reduced,
                                    rotation=0,
                                    color=color,
                                    font_weight=font_weight,
                                    font_family=self.font_family,
                                    opacity=opacity,
                                )
                            )
                            placed_bboxes.append(bbox)
                            found = True
                            break
                    if found:
                        break

        return placed

    def render_svg(self, placed_words: list[PlacedWord]) -> str:
        """Override to optionally include the shape outline and glow filter."""
        if not self.show_shape_outline:
            return super().render_svg(placed_words)

        # Build the SVG with the polygon element included
        root = ET.Element(
            "svg",
            xmlns="http://www.w3.org/2000/svg",
            width=str(self.width),
            height=str(self.height),
            viewBox=f"0 0 {self.width} {self.height}",
        )

        # Filters and background
        defs = self._add_glow_filter(root)
        radial = ET.SubElement(
            defs, "radialGradient",
            id="wc-bg-grad",
            cx="50%", cy="50%", r="75%",
        )
        ET.SubElement(radial, "stop", offset="0%", attrib={
            "stop-color": "#fafbfc", "stop-opacity": "1",
        })
        ET.SubElement(radial, "stop", offset="100%", attrib={
            "stop-color": "#f0f1f3", "stop-opacity": "1",
        })
        ET.SubElement(
            root, "rect",
            width=str(self.width), height=str(self.height),
            fill="url(#wc-bg-grad)",
        )

        glow_threshold = self._glow_size_threshold(placed_words)

        # Tier thresholds
        tier1_threshold = float("inf")
        tier2_threshold = float("inf")
        if placed_words:
            sizes = sorted((pw.font_size for pw in placed_words), reverse=True)
            t1_idx = max(1, int(len(sizes) * 0.10))
            tier1_threshold = sizes[min(t1_idx, len(sizes) - 1)]
            t2_idx = max(1, int(len(sizes) * 0.30))
            tier2_threshold = sizes[min(t2_idx, len(sizes) - 1)]

        # Shape outline polygon
        points_str = " ".join(f"{x:.1f},{y:.1f}" for x, y in self._polygon)
        ET.SubElement(
            root, "polygon",
            points=points_str,
            fill="none",
            stroke=self.outline_color,
        ).set("stroke-width", str(self.outline_width))

        # Text elements with full visual hierarchy
        for pw in placed_words:
            attrs: dict[str, str] = {
                "x": f"{pw.x:.1f}",
                "y": f"{pw.y:.1f}",
                "font-size": f"{pw.font_size:.1f}",
                "fill": pw.color,
                "font-family": pw.font_family or self.font_family,
                "font-weight": str(pw.font_weight),
                "text-anchor": "middle",
                "dominant-baseline": "central",
            }
            if pw.opacity < 1.0:
                attrs["opacity"] = f"{pw.opacity:.2f}"
            if pw.rotation != 0:
                attrs["transform"] = (
                    f"rotate({pw.rotation:.1f},{pw.x:.1f},{pw.y:.1f})"
                )
            if pw.font_size >= glow_threshold:
                attrs["filter"] = "url(#wc-glow)"
            elif pw.font_size >= tier2_threshold:
                attrs["filter"] = "url(#wc-shadow)"
            if pw.font_size >= tier1_threshold:
                spacing = max(0.5, pw.font_size * 0.02)
                attrs["letter-spacing"] = f"{spacing:.1f}"
            elem = ET.SubElement(root, "text", attrib=attrs)
            elem.text = pw.text

        ET.indent(root)
        return ET.tostring(root, encoding="unicode", xml_declaration=False)

    def _spiral_gen(
        self, cx: float, cy: float, step: float, max_steps: int = 2000,
    ):
        b = step
        for i in range(max_steps):
            theta = i * 0.1
            r = b * theta
            yield cx + r * math.cos(theta), cy + r * math.sin(theta)


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

RENDERERS: dict[str, type[SvgWordCloudEngine]] = {
    "wordle": WordleRenderer,
    "clustered": ClusteredRenderer,
    "typographic": TypographicRenderer,
    "shaped": ShapedRenderer,
}


def get_renderer(name: str, **kwargs) -> SvgWordCloudEngine:
    """Factory: create a renderer by name."""
    cls = RENDERERS.get(name)
    if cls is None:
        raise ValueError(
            f"Unknown renderer {name!r}. Choose from: {', '.join(RENDERERS)}"
        )
    return cls(**kwargs)
