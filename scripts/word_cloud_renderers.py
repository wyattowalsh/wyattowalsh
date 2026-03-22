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
# Metaheuristic aesthetic cost function
# ---------------------------------------------------------------------------

# Rotation choices biased toward horizontal for readability
_META_ROTATIONS = [0, 0, 0, 0, 90, -8, 8]


def _estimate_word_bbox(
    text: str, font_size: float, x: float, y: float, rotation: float,
    padding: float = 2.0,
) -> BBox:
    """Estimate AABB for a word at (x, y) with given rotation."""
    w = len(text) * font_size * 0.55
    h = font_size * 1.2
    if rotation != 0:
        rad = math.radians(abs(rotation))
        cos_a = abs(math.cos(rad))
        sin_a = abs(math.sin(rad))
        rw = w * cos_a + h * sin_a
        rh = w * sin_a + h * cos_a
        w, h = rw, rh
    return BBox(x - w / 2, y - h / 2, w + padding, h + padding)


def _aesthetic_cost(
    positions: list[tuple[float, float, float]],
    sizes: list[float],
    canvas_w: float,
    canvas_h: float,
    texts: list[str] | None = None,
) -> float:
    """Evaluate the aesthetic quality of a word placement solution.

    Returns a scalar cost (lower is better) combining:
    1. Overlap penalty (weight 10.0)
    2. Packing density (weight 3.0)
    3. Visual balance (weight 2.0)
    4. Whitespace uniformity (weight 2.0)
    5. Reading flow (weight 1.5)
    6. Golden ratio harmony (weight 1.0)
    7. Size gradient (weight 1.0)
    """
    n = len(positions)
    if n == 0:
        return 0.0

    canvas_area = canvas_w * canvas_h
    if canvas_area <= 0:
        return float("inf")

    # Build bounding boxes
    bboxes: list[BBox] = []
    _texts = texts or ["W" * 6] * n
    for i in range(n):
        x, y, rot = positions[i]
        bboxes.append(_estimate_word_bbox(_texts[i], sizes[i], x, y, rot))

    # 1. Overlap penalty: sum of AABB intersection areas / canvas area
    overlap_area = 0.0
    for i in range(n):
        for j in range(i + 1, n):
            bi, bj = bboxes[i], bboxes[j]
            if bi.intersects(bj):
                ox = max(0.0, min(bi.x2, bj.x2) - max(bi.x, bj.x))
                oy = max(0.0, min(bi.y2, bj.y2) - max(bi.y, bj.y))
                overlap_area += ox * oy
    overlap_norm = min(1.0, overlap_area / canvas_area)

    # 2. Packing density: total bbox area / convex hull area approximation
    total_bbox_area = sum(b.w * b.h for b in bboxes)
    all_x = [b.x for b in bboxes] + [b.x2 for b in bboxes]
    all_y = [b.y for b in bboxes] + [b.y2 for b in bboxes]
    hull_w = max(all_x) - min(all_x) if all_x else 1.0
    hull_h = max(all_y) - min(all_y) if all_y else 1.0
    hull_area = max(hull_w * hull_h, 1.0)
    packing = 1.0 - min(1.0, total_bbox_area / hull_area)

    # 3. Visual balance: distance of area-weighted centroid from center
    total_weight = 0.0
    wx_sum = 0.0
    wy_sum = 0.0
    for i in range(n):
        area = bboxes[i].w * bboxes[i].h
        cx_i = positions[i][0]
        cy_i = positions[i][1]
        wx_sum += cx_i * area
        wy_sum += cy_i * area
        total_weight += area
    if total_weight > 0:
        centroid_x = wx_sum / total_weight
        centroid_y = wy_sum / total_weight
    else:
        centroid_x, centroid_y = canvas_w / 2, canvas_h / 2
    max_dist = math.hypot(canvas_w / 2, canvas_h / 2)
    balance_dist = math.hypot(centroid_x - canvas_w / 2, centroid_y - canvas_h / 2)
    balance = min(1.0, balance_dist / max(max_dist, 1.0))

    # 4. Whitespace uniformity: variance of nearest-neighbor distances / mean
    centers = [(positions[i][0], positions[i][1]) for i in range(n)]
    nn_dists: list[float] = []
    for i in range(n):
        min_d = float("inf")
        for j in range(n):
            if i == j:
                continue
            d = math.hypot(centers[i][0] - centers[j][0], centers[i][1] - centers[j][1])
            if d < min_d:
                min_d = d
        if min_d < float("inf"):
            nn_dists.append(min_d)
    if nn_dists and len(nn_dists) > 1:
        mean_nn = sum(nn_dists) / len(nn_dists)
        var_nn = sum((d - mean_nn) ** 2 for d in nn_dists) / len(nn_dists)
        uniformity = min(1.0, var_nn / max(mean_nn ** 2, 1.0))
    else:
        uniformity = 0.0

    # 5. Reading flow: penalize large words at extreme rotations
    max_size = max(sizes) if sizes else 1.0
    flow_penalty = 0.0
    for i in range(n):
        size_ratio = sizes[i] / max(max_size, 1.0)
        rot_severity = abs(positions[i][2]) / 90.0
        flow_penalty += size_ratio * rot_severity
    reading_flow = min(1.0, flow_penalty / max(n, 1))

    # 6. Golden ratio harmony: closeness of bounding envelope to phi
    phi = 1.618033988749895
    if hull_h > 0:
        aspect = hull_w / hull_h
        if aspect < 1.0 and aspect > 0:
            aspect = 1.0 / aspect
    else:
        aspect = 1.0
    golden = min(1.0, abs(aspect - phi) / phi)

    # 7. Size gradient: large words should be near center
    center_x, center_y = canvas_w / 2, canvas_h / 2
    max_possible_dist = math.hypot(canvas_w / 2, canvas_h / 2)
    gradient_penalty = 0.0
    for i in range(n):
        size_ratio = sizes[i] / max(max_size, 1.0)
        dist_from_center = math.hypot(
            positions[i][0] - center_x, positions[i][1] - center_y
        )
        dist_ratio = dist_from_center / max(max_possible_dist, 1.0)
        # Large words far from center = bad
        gradient_penalty += size_ratio * dist_ratio
    size_gradient = min(1.0, gradient_penalty / max(n, 1))

    # Weighted sum
    cost = (
        10.0 * overlap_norm
        + 3.0 * packing
        + 2.0 * balance
        + 2.0 * uniformity
        + 1.5 * reading_flow
        + 1.0 * golden
        + 1.0 * size_gradient
    )
    return cost


# ---------------------------------------------------------------------------
# Metaheuristic solver helpers
# ---------------------------------------------------------------------------

def _random_solution(
    n: int, canvas_w: float, canvas_h: float, rng: random.Random,
) -> list[tuple[float, float, float]]:
    """Generate a random placement solution."""
    margin_x = canvas_w * 0.05
    margin_y = canvas_h * 0.05
    sol: list[tuple[float, float, float]] = []
    for _ in range(n):
        x = rng.uniform(margin_x, canvas_w - margin_x)
        y = rng.uniform(margin_y, canvas_h - margin_y)
        rot = rng.choice(_META_ROTATIONS)
        sol.append((x, y, float(rot)))
    return sol


def _clamp_solution(
    sol: list[tuple[float, float, float]], canvas_w: float, canvas_h: float,
) -> list[tuple[float, float, float]]:
    """Clamp positions to canvas bounds and rotations to valid set."""
    mx, my = canvas_w * 0.05, canvas_h * 0.05
    result: list[tuple[float, float, float]] = []
    for x, y, rot in sol:
        x = max(mx, min(canvas_w - mx, x))
        y = max(my, min(canvas_h - my, y))
        # Snap rotation to nearest valid
        valid_rots = [0.0, 90.0, -8.0, 8.0]
        rot = min(valid_rots, key=lambda r: abs(r - rot))
        result.append((x, y, rot))
    return result


def _eval_fitness(
    sol: list[tuple[float, float, float]],
    sizes: list[float],
    canvas_w: float,
    canvas_h: float,
    texts: list[str] | None = None,
) -> float:
    """Return fitness (higher is better) = negative cost."""
    return -_aesthetic_cost(sol, sizes, canvas_w, canvas_h, texts)


# ---------------------------------------------------------------------------
# 25 Metaheuristic solvers
# ---------------------------------------------------------------------------

def _solve_harmony_search(
    n_words: int, sizes: list[float], canvas_w: float, canvas_h: float,
    max_iter: int, rng: random.Random, texts: list[str] | None = None,
) -> list[tuple[float, float, float]]:
    """Harmony Search: HMS=20, HMCR=0.9, PAR=0.3, shrinking bandwidth."""
    hms = 20
    hmcr = 0.9
    par = 0.3
    bw_init = min(canvas_w, canvas_h) * 0.3
    bw_final = min(canvas_w, canvas_h) * 0.01

    # Initialize harmony memory
    hm = [_random_solution(n_words, canvas_w, canvas_h, rng) for _ in range(hms)]
    hm_fit = [_eval_fitness(s, sizes, canvas_w, canvas_h, texts) for s in hm]

    for it in range(max_iter):
        bw = bw_init - (bw_init - bw_final) * (it / max(max_iter - 1, 1))
        new_harmony: list[tuple[float, float, float]] = []
        for i in range(n_words):
            if rng.random() < hmcr:
                # Memory consideration
                idx = rng.randint(0, hms - 1)
                x, y, rot = hm[idx][i]
                if rng.random() < par:
                    x += rng.gauss(0, bw)
                    y += rng.gauss(0, bw)
                    rot = rng.choice(_META_ROTATIONS)
            else:
                x = rng.uniform(canvas_w * 0.05, canvas_w * 0.95)
                y = rng.uniform(canvas_h * 0.05, canvas_h * 0.95)
                rot = rng.choice(_META_ROTATIONS)
            new_harmony.append((x, y, float(rot)))
        new_harmony = _clamp_solution(new_harmony, canvas_w, canvas_h)
        new_fit = _eval_fitness(new_harmony, sizes, canvas_w, canvas_h, texts)
        worst_idx = min(range(hms), key=lambda k: hm_fit[k])
        if new_fit > hm_fit[worst_idx]:
            hm[worst_idx] = new_harmony
            hm_fit[worst_idx] = new_fit

    best_idx = max(range(hms), key=lambda k: hm_fit[k])
    return hm[best_idx]


def _solve_simulated_annealing(
    n_words: int, sizes: list[float], canvas_w: float, canvas_h: float,
    max_iter: int, rng: random.Random, texts: list[str] | None = None,
) -> list[tuple[float, float, float]]:
    """Simulated Annealing: T_init=100, T_min=0.01, alpha=0.995."""
    t_init = 100.0
    t_min = 0.01
    alpha = 0.995

    current = _random_solution(n_words, canvas_w, canvas_h, rng)
    current_cost = _aesthetic_cost(current, sizes, canvas_w, canvas_h, texts)
    best = list(current)
    best_cost = current_cost
    temp = t_init

    for _ in range(max_iter):
        if temp < t_min:
            break
        # Perturb: move 1-3 random words
        neighbor = list(current)
        n_perturb = rng.randint(1, min(3, n_words))
        for _ in range(n_perturb):
            idx = rng.randint(0, n_words - 1)
            x, y, rot = neighbor[idx]
            x += rng.gauss(0, canvas_w * 0.05)
            y += rng.gauss(0, canvas_h * 0.05)
            rot = rng.choice(_META_ROTATIONS)
            neighbor[idx] = (x, y, float(rot))
        neighbor = _clamp_solution(neighbor, canvas_w, canvas_h)
        neighbor_cost = _aesthetic_cost(neighbor, sizes, canvas_w, canvas_h, texts)

        delta = neighbor_cost - current_cost
        if delta < 0 or rng.random() < math.exp(-delta / max(temp, 1e-10)):
            current = neighbor
            current_cost = neighbor_cost
            if current_cost < best_cost:
                best = list(current)
                best_cost = current_cost
        temp *= alpha

    return best


def _solve_particle_swarm(
    n_words: int, sizes: list[float], canvas_w: float, canvas_h: float,
    max_iter: int, rng: random.Random, texts: list[str] | None = None,
) -> list[tuple[float, float, float]]:
    """Particle Swarm Optimization: w=0.7->0.4, c1=c2=1.5."""
    pop_size = 20
    c1, c2 = 1.5, 1.5
    dim = n_words * 3  # x, y, rot per word

    def sol_to_vec(sol: list[tuple[float, float, float]]) -> list[float]:
        v: list[float] = []
        for x, y, r in sol:
            v.extend([x, y, r])
        return v

    def vec_to_sol(v: list[float]) -> list[tuple[float, float, float]]:
        s: list[tuple[float, float, float]] = []
        for i in range(0, len(v), 3):
            s.append((v[i], v[i + 1], v[i + 2]))
        return _clamp_solution(s, canvas_w, canvas_h)

    # Initialize
    particles = [sol_to_vec(_random_solution(n_words, canvas_w, canvas_h, rng)) for _ in range(pop_size)]
    velocities = [[rng.gauss(0, canvas_w * 0.02) for _ in range(dim)] for _ in range(pop_size)]
    p_best = [list(p) for p in particles]
    p_best_fit = [_eval_fitness(vec_to_sol(p), sizes, canvas_w, canvas_h, texts) for p in particles]
    g_best_idx = max(range(pop_size), key=lambda k: p_best_fit[k])
    g_best = list(p_best[g_best_idx])
    g_best_fit = p_best_fit[g_best_idx]

    v_max = canvas_w * 0.1

    for it in range(max_iter):
        w = 0.7 - 0.3 * (it / max(max_iter - 1, 1))
        for i in range(pop_size):
            for d in range(dim):
                r1, r2 = rng.random(), rng.random()
                velocities[i][d] = (
                    w * velocities[i][d]
                    + c1 * r1 * (p_best[i][d] - particles[i][d])
                    + c2 * r2 * (g_best[d] - particles[i][d])
                )
                velocities[i][d] = max(-v_max, min(v_max, velocities[i][d]))
                particles[i][d] += velocities[i][d]

            sol = vec_to_sol(particles[i])
            particles[i] = sol_to_vec(sol)
            fit = _eval_fitness(sol, sizes, canvas_w, canvas_h, texts)
            if fit > p_best_fit[i]:
                p_best[i] = list(particles[i])
                p_best_fit[i] = fit
                if fit > g_best_fit:
                    g_best = list(particles[i])
                    g_best_fit = fit

    return vec_to_sol(g_best)


def _solve_differential_evolution(
    n_words: int, sizes: list[float], canvas_w: float, canvas_h: float,
    max_iter: int, rng: random.Random, texts: list[str] | None = None,
) -> list[tuple[float, float, float]]:
    """Differential Evolution: F=0.8, CR=0.9, rand/1/bin."""
    pop_size = 20
    F = 0.8
    CR = 0.9
    dim = n_words * 3

    def sol_to_vec(sol: list[tuple[float, float, float]]) -> list[float]:
        v: list[float] = []
        for x, y, r in sol:
            v.extend([x, y, r])
        return v

    def vec_to_sol(v: list[float]) -> list[tuple[float, float, float]]:
        s: list[tuple[float, float, float]] = []
        for i in range(0, len(v), 3):
            s.append((v[i], v[i + 1], v[i + 2]))
        return _clamp_solution(s, canvas_w, canvas_h)

    pop = [sol_to_vec(_random_solution(n_words, canvas_w, canvas_h, rng)) for _ in range(pop_size)]
    pop_fit = [_eval_fitness(vec_to_sol(p), sizes, canvas_w, canvas_h, texts) for p in pop]

    for _ in range(max_iter):
        for i in range(pop_size):
            # Select 3 distinct random indices != i
            candidates = [j for j in range(pop_size) if j != i]
            a, b, c = rng.sample(candidates, 3)
            # Mutant
            mutant = [pop[a][d] + F * (pop[b][d] - pop[c][d]) for d in range(dim)]
            # Crossover
            j_rand = rng.randint(0, dim - 1)
            trial = [mutant[d] if rng.random() < CR or d == j_rand else pop[i][d] for d in range(dim)]
            trial_sol = vec_to_sol(trial)
            trial_fit = _eval_fitness(trial_sol, sizes, canvas_w, canvas_h, texts)
            if trial_fit >= pop_fit[i]:
                pop[i] = sol_to_vec(trial_sol)
                pop_fit[i] = trial_fit

    best_idx = max(range(pop_size), key=lambda k: pop_fit[k])
    return vec_to_sol(pop[best_idx])


def _solve_ant_colony(
    n_words: int, sizes: list[float], canvas_w: float, canvas_h: float,
    max_iter: int, rng: random.Random, texts: list[str] | None = None,
) -> list[tuple[float, float, float]]:
    """Ant Colony Optimization: pheromone grid 10x10, rho=0.5."""
    grid_size = 10
    n_ants = 20
    rho = 0.5
    alpha_p = 1.0
    beta_p = 2.0

    # Pheromone grid per word: grid_size x grid_size
    pheromone = [[[1.0] * grid_size for _ in range(grid_size)] for _ in range(n_words)]
    best_sol: list[tuple[float, float, float]] | None = None
    best_fit = float("-inf")

    cell_w = canvas_w / grid_size
    cell_h = canvas_h / grid_size

    for _ in range(max_iter):
        ant_solutions: list[list[tuple[float, float, float]]] = []
        ant_fits: list[float] = []

        for _ in range(n_ants):
            sol: list[tuple[float, float, float]] = []
            for w in range(n_words):
                # Build probability from pheromone
                probs: list[float] = []
                cells: list[tuple[int, int]] = []
                for gi in range(grid_size):
                    for gj in range(grid_size):
                        tau = pheromone[w][gi][gj] ** alpha_p
                        # Heuristic: prefer center
                        cx_cell = (gj + 0.5) * cell_w
                        cy_cell = (gi + 0.5) * cell_h
                        dist = math.hypot(cx_cell - canvas_w / 2, cy_cell - canvas_h / 2) + 1.0
                        eta = (1.0 / dist) ** beta_p
                        probs.append(tau * eta)
                        cells.append((gi, gj))
                total_p = sum(probs)
                if total_p <= 0:
                    chosen = rng.randint(0, len(cells) - 1)
                else:
                    r = rng.random() * total_p
                    cum = 0.0
                    chosen = 0
                    for ci, p in enumerate(probs):
                        cum += p
                        if cum >= r:
                            chosen = ci
                            break
                gi, gj = cells[chosen]
                x = (gj + rng.random()) * cell_w
                y = (gi + rng.random()) * cell_h
                rot = rng.choice(_META_ROTATIONS)
                sol.append((x, y, float(rot)))

            sol = _clamp_solution(sol, canvas_w, canvas_h)
            fit = _eval_fitness(sol, sizes, canvas_w, canvas_h, texts)
            ant_solutions.append(sol)
            ant_fits.append(fit)

            if fit > best_fit:
                best_fit = fit
                best_sol = list(sol)

        # Evaporate
        for w in range(n_words):
            for gi in range(grid_size):
                for gj in range(grid_size):
                    pheromone[w][gi][gj] *= (1 - rho)

        # Deposit: best ant deposits more
        if ant_fits:
            best_ant = max(range(n_ants), key=lambda k: ant_fits[k])
            deposit = max(0.1, 1.0 + ant_fits[best_ant])
            for w in range(n_words):
                x, y, _ = ant_solutions[best_ant][w]
                gj = min(grid_size - 1, max(0, int(x / cell_w)))
                gi = min(grid_size - 1, max(0, int(y / cell_h)))
                pheromone[w][gi][gj] += deposit

    return best_sol if best_sol is not None else _random_solution(n_words, canvas_w, canvas_h, rng)


def _solve_firefly(
    n_words: int, sizes: list[float], canvas_w: float, canvas_h: float,
    max_iter: int, rng: random.Random, texts: list[str] | None = None,
) -> list[tuple[float, float, float]]:
    """Firefly Algorithm: beta0=1.0, gamma=0.01, alpha=0.2."""
    pop_size = 20
    beta0 = 1.0
    gamma = 0.01
    alpha_fa = 0.2

    dim = n_words * 3

    def sol_to_vec(sol: list[tuple[float, float, float]]) -> list[float]:
        v: list[float] = []
        for x, y, r in sol:
            v.extend([x, y, r])
        return v

    def vec_to_sol(v: list[float]) -> list[tuple[float, float, float]]:
        s: list[tuple[float, float, float]] = []
        for i in range(0, len(v), 3):
            s.append((v[i], v[i + 1], v[i + 2]))
        return _clamp_solution(s, canvas_w, canvas_h)

    fireflies = [sol_to_vec(_random_solution(n_words, canvas_w, canvas_h, rng)) for _ in range(pop_size)]
    brightness = [_eval_fitness(vec_to_sol(f), sizes, canvas_w, canvas_h, texts) for f in fireflies]

    for _ in range(max_iter):
        for i in range(pop_size):
            for j in range(pop_size):
                if brightness[j] > brightness[i]:
                    # Distance
                    r_sq = sum((fireflies[i][d] - fireflies[j][d]) ** 2 for d in range(dim))
                    beta = beta0 * math.exp(-gamma * r_sq)
                    for d in range(dim):
                        fireflies[i][d] += beta * (fireflies[j][d] - fireflies[i][d]) + alpha_fa * rng.gauss(0, 1)
                    sol = vec_to_sol(fireflies[i])
                    fireflies[i] = sol_to_vec(sol)
                    brightness[i] = _eval_fitness(sol, sizes, canvas_w, canvas_h, texts)

    best_idx = max(range(pop_size), key=lambda k: brightness[k])
    return vec_to_sol(fireflies[best_idx])


def _solve_cuckoo_search(
    n_words: int, sizes: list[float], canvas_w: float, canvas_h: float,
    max_iter: int, rng: random.Random, texts: list[str] | None = None,
) -> list[tuple[float, float, float]]:
    """Cuckoo Search: pa=0.25, Levy flights beta=1.5 (Mantegna)."""
    pop_size = 20
    pa = 0.25
    beta_levy = 1.5

    # Mantegna's algorithm constants
    sigma_u = (
        math.gamma(1 + beta_levy) * math.sin(math.pi * beta_levy / 2)
        / (math.gamma((1 + beta_levy) / 2) * beta_levy * 2 ** ((beta_levy - 1) / 2))
    ) ** (1 / beta_levy)
    sigma_v = 1.0

    dim = n_words * 3

    def sol_to_vec(sol: list[tuple[float, float, float]]) -> list[float]:
        v: list[float] = []
        for x, y, r in sol:
            v.extend([x, y, r])
        return v

    def vec_to_sol(v: list[float]) -> list[tuple[float, float, float]]:
        s: list[tuple[float, float, float]] = []
        for i in range(0, len(v), 3):
            s.append((v[i], v[i + 1], v[i + 2]))
        return _clamp_solution(s, canvas_w, canvas_h)

    def levy_step() -> float:
        u = rng.gauss(0, sigma_u)
        v = rng.gauss(0, sigma_v)
        return u / (abs(v) ** (1 / beta_levy))

    nests = [sol_to_vec(_random_solution(n_words, canvas_w, canvas_h, rng)) for _ in range(pop_size)]
    fits = [_eval_fitness(vec_to_sol(n_), sizes, canvas_w, canvas_h, texts) for n_ in nests]

    for _ in range(max_iter):
        # Generate new solution via Levy flight
        i = rng.randint(0, pop_size - 1)
        new_nest = [nests[i][d] + levy_step() * canvas_w * 0.01 for d in range(dim)]
        new_sol = vec_to_sol(new_nest)
        new_fit = _eval_fitness(new_sol, sizes, canvas_w, canvas_h, texts)
        j = rng.randint(0, pop_size - 1)
        if new_fit > fits[j]:
            nests[j] = sol_to_vec(new_sol)
            fits[j] = new_fit

        # Abandon worst fraction
        sorted_idx = sorted(range(pop_size), key=lambda k: fits[k])
        n_abandon = max(1, int(pa * pop_size))
        for k in range(n_abandon):
            idx = sorted_idx[k]
            nests[idx] = sol_to_vec(_random_solution(n_words, canvas_w, canvas_h, rng))
            fits[idx] = _eval_fitness(vec_to_sol(nests[idx]), sizes, canvas_w, canvas_h, texts)

    best_idx = max(range(pop_size), key=lambda k: fits[k])
    return vec_to_sol(nests[best_idx])


def _solve_bat(
    n_words: int, sizes: list[float], canvas_w: float, canvas_h: float,
    max_iter: int, rng: random.Random, texts: list[str] | None = None,
) -> list[tuple[float, float, float]]:
    """Bat Algorithm: f_min=0, f_max=2, A=0.5->0, r=0->0.9."""
    pop_size = 20
    f_min, f_max = 0.0, 2.0
    dim = n_words * 3

    def sol_to_vec(sol: list[tuple[float, float, float]]) -> list[float]:
        v: list[float] = []
        for x, y, r in sol:
            v.extend([x, y, r])
        return v

    def vec_to_sol(v: list[float]) -> list[tuple[float, float, float]]:
        s: list[tuple[float, float, float]] = []
        for i in range(0, len(v), 3):
            s.append((v[i], v[i + 1], v[i + 2]))
        return _clamp_solution(s, canvas_w, canvas_h)

    bats = [sol_to_vec(_random_solution(n_words, canvas_w, canvas_h, rng)) for _ in range(pop_size)]
    velocities = [[0.0] * dim for _ in range(pop_size)]
    freqs = [0.0] * pop_size
    fits = [_eval_fitness(vec_to_sol(b), sizes, canvas_w, canvas_h, texts) for b in bats]
    loudness = [0.5] * pop_size
    pulse_rate_init = [0.0] * pop_size
    pulse_rate = [0.0] * pop_size

    g_best_idx = max(range(pop_size), key=lambda k: fits[k])
    g_best = list(bats[g_best_idx])
    g_best_fit = fits[g_best_idx]

    for it in range(max_iter):
        for i in range(pop_size):
            freqs[i] = f_min + (f_max - f_min) * rng.random()
            for d in range(dim):
                velocities[i][d] += (bats[i][d] - g_best[d]) * freqs[i]
            new_pos = [bats[i][d] + velocities[i][d] for d in range(dim)]

            # Local search
            if rng.random() > pulse_rate[i]:
                avg_loud = sum(loudness) / pop_size
                new_pos = [g_best[d] + avg_loud * rng.gauss(0, 1) for d in range(dim)]

            new_sol = vec_to_sol(new_pos)
            new_fit = _eval_fitness(new_sol, sizes, canvas_w, canvas_h, texts)

            if new_fit > fits[i] and rng.random() < loudness[i]:
                bats[i] = sol_to_vec(new_sol)
                fits[i] = new_fit
                loudness[i] *= 0.9
                pulse_rate[i] = pulse_rate_init[i] * (1 - math.exp(-0.9 * it))

            if new_fit > g_best_fit:
                g_best = sol_to_vec(new_sol)
                g_best_fit = new_fit

    return vec_to_sol(g_best)


def _solve_grey_wolf(
    n_words: int, sizes: list[float], canvas_w: float, canvas_h: float,
    max_iter: int, rng: random.Random, texts: list[str] | None = None,
) -> list[tuple[float, float, float]]:
    """Grey Wolf Optimizer: alpha/beta/delta hierarchy, a=2->0."""
    pop_size = 20
    dim = n_words * 3

    def sol_to_vec(sol: list[tuple[float, float, float]]) -> list[float]:
        v: list[float] = []
        for x, y, r in sol:
            v.extend([x, y, r])
        return v

    def vec_to_sol(v: list[float]) -> list[tuple[float, float, float]]:
        s: list[tuple[float, float, float]] = []
        for i in range(0, len(v), 3):
            s.append((v[i], v[i + 1], v[i + 2]))
        return _clamp_solution(s, canvas_w, canvas_h)

    wolves = [sol_to_vec(_random_solution(n_words, canvas_w, canvas_h, rng)) for _ in range(pop_size)]
    fits = [_eval_fitness(vec_to_sol(w), sizes, canvas_w, canvas_h, texts) for w in wolves]

    sorted_idx = sorted(range(pop_size), key=lambda k: fits[k], reverse=True)
    alpha_w, beta_w, delta_w = [list(wolves[sorted_idx[i]]) for i in range(3)]

    for it in range(max_iter):
        a = 2.0 - 2.0 * (it / max(max_iter - 1, 1))
        for i in range(pop_size):
            new_pos: list[float] = []
            for d in range(dim):
                r1, r2 = rng.random(), rng.random()
                A1 = 2 * a * r1 - a
                C1 = 2 * r2
                D_alpha = abs(C1 * alpha_w[d] - wolves[i][d])
                X1 = alpha_w[d] - A1 * D_alpha

                r1, r2 = rng.random(), rng.random()
                A2 = 2 * a * r1 - a
                C2 = 2 * r2
                D_beta = abs(C2 * beta_w[d] - wolves[i][d])
                X2 = beta_w[d] - A2 * D_beta

                r1, r2 = rng.random(), rng.random()
                A3 = 2 * a * r1 - a
                C3 = 2 * r2
                D_delta = abs(C3 * delta_w[d] - wolves[i][d])
                X3 = delta_w[d] - A3 * D_delta

                new_pos.append((X1 + X2 + X3) / 3)

            sol = vec_to_sol(new_pos)
            wolves[i] = sol_to_vec(sol)
            fits[i] = _eval_fitness(sol, sizes, canvas_w, canvas_h, texts)

        sorted_idx = sorted(range(pop_size), key=lambda k: fits[k], reverse=True)
        alpha_w = list(wolves[sorted_idx[0]])
        beta_w = list(wolves[sorted_idx[1]])
        delta_w = list(wolves[sorted_idx[2]])

    return vec_to_sol(alpha_w)


def _solve_whale(
    n_words: int, sizes: list[float], canvas_w: float, canvas_h: float,
    max_iter: int, rng: random.Random, texts: list[str] | None = None,
) -> list[tuple[float, float, float]]:
    """Whale Optimization: a=2->0, spiral with b=1, 50% encircling vs spiral."""
    pop_size = 20
    b_spiral = 1.0
    dim = n_words * 3

    def sol_to_vec(sol: list[tuple[float, float, float]]) -> list[float]:
        v: list[float] = []
        for x, y, r in sol:
            v.extend([x, y, r])
        return v

    def vec_to_sol(v: list[float]) -> list[tuple[float, float, float]]:
        s: list[tuple[float, float, float]] = []
        for i in range(0, len(v), 3):
            s.append((v[i], v[i + 1], v[i + 2]))
        return _clamp_solution(s, canvas_w, canvas_h)

    whales = [sol_to_vec(_random_solution(n_words, canvas_w, canvas_h, rng)) for _ in range(pop_size)]
    fits = [_eval_fitness(vec_to_sol(w), sizes, canvas_w, canvas_h, texts) for w in whales]
    best_idx = max(range(pop_size), key=lambda k: fits[k])
    best_pos = list(whales[best_idx])
    best_fit = fits[best_idx]

    for it in range(max_iter):
        a = 2.0 - 2.0 * (it / max(max_iter - 1, 1))
        for i in range(pop_size):
            r_p = rng.random()
            A = 2 * a * rng.random() - a
            C = 2 * rng.random()
            l_param = rng.uniform(-1, 1)

            new_pos: list[float] = []
            if r_p < 0.5:
                if abs(A) < 1:
                    # Encircling prey
                    for d in range(dim):
                        D = abs(C * best_pos[d] - whales[i][d])
                        new_pos.append(best_pos[d] - A * D)
                else:
                    # Random search
                    rand_idx = rng.randint(0, pop_size - 1)
                    for d in range(dim):
                        D = abs(C * whales[rand_idx][d] - whales[i][d])
                        new_pos.append(whales[rand_idx][d] - A * D)
            else:
                # Spiral
                for d in range(dim):
                    D_prime = abs(best_pos[d] - whales[i][d])
                    new_pos.append(
                        D_prime * math.exp(b_spiral * l_param) * math.cos(2 * math.pi * l_param)
                        + best_pos[d]
                    )

            sol = vec_to_sol(new_pos)
            whales[i] = sol_to_vec(sol)
            fits[i] = _eval_fitness(sol, sizes, canvas_w, canvas_h, texts)
            if fits[i] > best_fit:
                best_pos = list(whales[i])
                best_fit = fits[i]

    return vec_to_sol(best_pos)


def _solve_gravitational_search(
    n_words: int, sizes: list[float], canvas_w: float, canvas_h: float,
    max_iter: int, rng: random.Random, texts: list[str] | None = None,
) -> list[tuple[float, float, float]]:
    """Gravitational Search: G=100->0.01 exponential decay."""
    pop_size = 20
    G_init = 100.0
    dim = n_words * 3

    def sol_to_vec(sol: list[tuple[float, float, float]]) -> list[float]:
        v: list[float] = []
        for x, y, r in sol:
            v.extend([x, y, r])
        return v

    def vec_to_sol(v: list[float]) -> list[tuple[float, float, float]]:
        s: list[tuple[float, float, float]] = []
        for i in range(0, len(v), 3):
            s.append((v[i], v[i + 1], v[i + 2]))
        return _clamp_solution(s, canvas_w, canvas_h)

    agents = [sol_to_vec(_random_solution(n_words, canvas_w, canvas_h, rng)) for _ in range(pop_size)]
    velocities = [[0.0] * dim for _ in range(pop_size)]
    fits = [_eval_fitness(vec_to_sol(a), sizes, canvas_w, canvas_h, texts) for a in agents]

    for it in range(max_iter):
        G = G_init * math.exp(-20 * it / max(max_iter, 1))

        worst = min(fits)
        best = max(fits)
        span = best - worst if best != worst else 1.0

        # Compute masses
        masses = [(fits[i] - worst) / span for i in range(pop_size)]
        total_mass = sum(masses)
        if total_mass > 0:
            masses = [m / total_mass for m in masses]
        else:
            masses = [1.0 / pop_size] * pop_size

        # Only top k agents exert force
        k_best = max(2, int(pop_size * (1 - it / max(max_iter, 1))))
        sorted_idx = sorted(range(pop_size), key=lambda j: fits[j], reverse=True)
        active = set(sorted_idx[:k_best])

        for i in range(pop_size):
            force = [0.0] * dim
            for j in active:
                if i == j:
                    continue
                r = math.sqrt(sum((agents[i][d] - agents[j][d]) ** 2 for d in range(dim))) + 1e-10
                for d in range(dim):
                    force[d] += rng.random() * G * masses[j] * (agents[j][d] - agents[i][d]) / r

            mi = masses[i] if masses[i] > 0 else 1e-10
            for d in range(dim):
                velocities[i][d] = rng.random() * velocities[i][d] + force[d] / mi
                agents[i][d] += velocities[i][d]

            sol = vec_to_sol(agents[i])
            agents[i] = sol_to_vec(sol)
            fits[i] = _eval_fitness(sol, sizes, canvas_w, canvas_h, texts)

    best_idx = max(range(pop_size), key=lambda k: fits[k])
    return vec_to_sol(agents[best_idx])


def _solve_flower_pollination(
    n_words: int, sizes: list[float], canvas_w: float, canvas_h: float,
    max_iter: int, rng: random.Random, texts: list[str] | None = None,
) -> list[tuple[float, float, float]]:
    """Flower Pollination: p=0.8 switch, Levy for global, gaussian for local."""
    pop_size = 20
    p_switch = 0.8
    beta_levy = 1.5
    dim = n_words * 3

    sigma_u = (
        math.gamma(1 + beta_levy) * math.sin(math.pi * beta_levy / 2)
        / (math.gamma((1 + beta_levy) / 2) * beta_levy * 2 ** ((beta_levy - 1) / 2))
    ) ** (1 / beta_levy)

    def sol_to_vec(sol: list[tuple[float, float, float]]) -> list[float]:
        v: list[float] = []
        for x, y, r in sol:
            v.extend([x, y, r])
        return v

    def vec_to_sol(v: list[float]) -> list[tuple[float, float, float]]:
        s: list[tuple[float, float, float]] = []
        for i in range(0, len(v), 3):
            s.append((v[i], v[i + 1], v[i + 2]))
        return _clamp_solution(s, canvas_w, canvas_h)

    def levy_step() -> float:
        u = rng.gauss(0, sigma_u)
        v = rng.gauss(0, 1)
        return u / (abs(v) ** (1 / beta_levy))

    flowers = [sol_to_vec(_random_solution(n_words, canvas_w, canvas_h, rng)) for _ in range(pop_size)]
    fits = [_eval_fitness(vec_to_sol(f), sizes, canvas_w, canvas_h, texts) for f in flowers]
    best_idx = max(range(pop_size), key=lambda k: fits[k])
    g_best = list(flowers[best_idx])

    for _ in range(max_iter):
        for i in range(pop_size):
            if rng.random() < p_switch:
                # Global pollination via Levy
                new_pos = [flowers[i][d] + levy_step() * (g_best[d] - flowers[i][d]) for d in range(dim)]
            else:
                # Local pollination
                j, k = rng.sample([x for x in range(pop_size) if x != i], 2)
                eps = rng.random()
                new_pos = [flowers[i][d] + eps * (flowers[j][d] - flowers[k][d]) for d in range(dim)]

            new_sol = vec_to_sol(new_pos)
            new_fit = _eval_fitness(new_sol, sizes, canvas_w, canvas_h, texts)
            if new_fit > fits[i]:
                flowers[i] = sol_to_vec(new_sol)
                fits[i] = new_fit
                if new_fit > fits[best_idx]:
                    best_idx = i
                    g_best = list(flowers[i])

    return vec_to_sol(g_best)


def _solve_moth_flame(
    n_words: int, sizes: list[float], canvas_w: float, canvas_h: float,
    max_iter: int, rng: random.Random, texts: list[str] | None = None,
) -> list[tuple[float, float, float]]:
    """Moth-Flame Optimization: logarithmic spiral, flames decrease n->1."""
    pop_size = 20
    dim = n_words * 3

    def sol_to_vec(sol: list[tuple[float, float, float]]) -> list[float]:
        v: list[float] = []
        for x, y, r in sol:
            v.extend([x, y, r])
        return v

    def vec_to_sol(v: list[float]) -> list[tuple[float, float, float]]:
        s: list[tuple[float, float, float]] = []
        for i in range(0, len(v), 3):
            s.append((v[i], v[i + 1], v[i + 2]))
        return _clamp_solution(s, canvas_w, canvas_h)

    moths = [sol_to_vec(_random_solution(n_words, canvas_w, canvas_h, rng)) for _ in range(pop_size)]
    fits = [_eval_fitness(vec_to_sol(m), sizes, canvas_w, canvas_h, texts) for m in moths]

    sorted_idx = sorted(range(pop_size), key=lambda k: fits[k], reverse=True)
    flames = [list(moths[sorted_idx[i]]) for i in range(pop_size)]
    flame_fits = [fits[sorted_idx[i]] for i in range(pop_size)]

    for it in range(max_iter):
        n_flames = max(1, int(pop_size - it * (pop_size - 1) / max(max_iter, 1)))
        for i in range(pop_size):
            flame_idx = min(i, n_flames - 1)
            t_param = rng.uniform(-1, 1)
            b_param = 1.0
            new_pos: list[float] = []
            for d in range(dim):
                D = abs(flames[flame_idx][d] - moths[i][d])
                new_pos.append(
                    D * math.exp(b_param * t_param) * math.cos(2 * math.pi * t_param)
                    + flames[flame_idx][d]
                )
            sol = vec_to_sol(new_pos)
            moths[i] = sol_to_vec(sol)
            fits[i] = _eval_fitness(sol, sizes, canvas_w, canvas_h, texts)

        # Update flames
        all_combined = list(range(pop_size))
        all_combined.sort(key=lambda k: fits[k], reverse=True)
        for rank, k in enumerate(all_combined[:pop_size]):
            if fits[k] > flame_fits[rank]:
                flames[rank] = list(moths[k])
                flame_fits[rank] = fits[k]

    best_idx = max(range(pop_size), key=lambda k: flame_fits[k])
    return vec_to_sol(flames[best_idx])


def _solve_salp_swarm(
    n_words: int, sizes: list[float], canvas_w: float, canvas_h: float,
    max_iter: int, rng: random.Random, texts: list[str] | None = None,
) -> list[tuple[float, float, float]]:
    """Salp Swarm: c1=2*exp(-(4t/T)^2), leader/follower chain."""
    pop_size = 20
    dim = n_words * 3

    def sol_to_vec(sol: list[tuple[float, float, float]]) -> list[float]:
        v: list[float] = []
        for x, y, r in sol:
            v.extend([x, y, r])
        return v

    def vec_to_sol(v: list[float]) -> list[tuple[float, float, float]]:
        s: list[tuple[float, float, float]] = []
        for i in range(0, len(v), 3):
            s.append((v[i], v[i + 1], v[i + 2]))
        return _clamp_solution(s, canvas_w, canvas_h)

    salps = [sol_to_vec(_random_solution(n_words, canvas_w, canvas_h, rng)) for _ in range(pop_size)]
    fits = [_eval_fitness(vec_to_sol(s), sizes, canvas_w, canvas_h, texts) for s in salps]
    best_idx = max(range(pop_size), key=lambda k: fits[k])
    food = list(salps[best_idx])

    ub = [canvas_w * 0.95] * dim
    lb = [canvas_w * 0.05] * dim
    for d in range(dim):
        if d % 3 == 1:
            ub[d] = canvas_h * 0.95
            lb[d] = canvas_h * 0.05
        elif d % 3 == 2:
            ub[d] = 90.0
            lb[d] = -8.0

    for it in range(max_iter):
        c1 = 2 * math.exp(-(4 * it / max(max_iter, 1)) ** 2)
        for i in range(pop_size):
            if i == 0:
                # Leader
                for d in range(dim):
                    c2, c3 = rng.random(), rng.random()
                    if c3 < 0.5:
                        salps[i][d] = food[d] + c1 * ((ub[d] - lb[d]) * c2 + lb[d])
                    else:
                        salps[i][d] = food[d] - c1 * ((ub[d] - lb[d]) * c2 + lb[d])
            else:
                # Follower
                for d in range(dim):
                    salps[i][d] = (salps[i][d] + salps[i - 1][d]) / 2

            sol = vec_to_sol(salps[i])
            salps[i] = sol_to_vec(sol)
            fits[i] = _eval_fitness(sol, sizes, canvas_w, canvas_h, texts)
            if fits[i] > fits[best_idx]:
                best_idx = i
                food = list(salps[i])

    return vec_to_sol(food)


def _solve_sine_cosine(
    n_words: int, sizes: list[float], canvas_w: float, canvas_h: float,
    max_iter: int, rng: random.Random, texts: list[str] | None = None,
) -> list[tuple[float, float, float]]:
    """Sine Cosine Algorithm: a=2->0, r1 sinusoidal update."""
    pop_size = 20
    dim = n_words * 3

    def sol_to_vec(sol: list[tuple[float, float, float]]) -> list[float]:
        v: list[float] = []
        for x, y, r in sol:
            v.extend([x, y, r])
        return v

    def vec_to_sol(v: list[float]) -> list[tuple[float, float, float]]:
        s: list[tuple[float, float, float]] = []
        for i in range(0, len(v), 3):
            s.append((v[i], v[i + 1], v[i + 2]))
        return _clamp_solution(s, canvas_w, canvas_h)

    agents = [sol_to_vec(_random_solution(n_words, canvas_w, canvas_h, rng)) for _ in range(pop_size)]
    fits = [_eval_fitness(vec_to_sol(a), sizes, canvas_w, canvas_h, texts) for a in agents]
    best_idx = max(range(pop_size), key=lambda k: fits[k])
    dest = list(agents[best_idx])

    for it in range(max_iter):
        a_param = 2.0 * (1 - it / max(max_iter, 1))
        for i in range(pop_size):
            r1 = a_param
            r2 = 2 * math.pi * rng.random()
            r3 = 2 * rng.random()
            r4 = rng.random()

            new_pos: list[float] = []
            for d in range(dim):
                if r4 < 0.5:
                    new_pos.append(agents[i][d] + r1 * math.sin(r2) * abs(r3 * dest[d] - agents[i][d]))
                else:
                    new_pos.append(agents[i][d] + r1 * math.cos(r2) * abs(r3 * dest[d] - agents[i][d]))

            sol = vec_to_sol(new_pos)
            agents[i] = sol_to_vec(sol)
            fits[i] = _eval_fitness(sol, sizes, canvas_w, canvas_h, texts)
            if fits[i] > fits[best_idx]:
                best_idx = i
                dest = list(agents[i])

    return vec_to_sol(dest)


def _solve_teaching_learning(
    n_words: int, sizes: list[float], canvas_w: float, canvas_h: float,
    max_iter: int, rng: random.Random, texts: list[str] | None = None,
) -> list[tuple[float, float, float]]:
    """Teaching-Learning-Based Optimization: teacher + learner phases."""
    pop_size = 20
    dim = n_words * 3

    def sol_to_vec(sol: list[tuple[float, float, float]]) -> list[float]:
        v: list[float] = []
        for x, y, r in sol:
            v.extend([x, y, r])
        return v

    def vec_to_sol(v: list[float]) -> list[tuple[float, float, float]]:
        s: list[tuple[float, float, float]] = []
        for i in range(0, len(v), 3):
            s.append((v[i], v[i + 1], v[i + 2]))
        return _clamp_solution(s, canvas_w, canvas_h)

    learners = [sol_to_vec(_random_solution(n_words, canvas_w, canvas_h, rng)) for _ in range(pop_size)]
    fits = [_eval_fitness(vec_to_sol(l), sizes, canvas_w, canvas_h, texts) for l in learners]

    for _ in range(max_iter):
        # Find teacher (best)
        teacher_idx = max(range(pop_size), key=lambda k: fits[k])
        teacher = learners[teacher_idx]

        # Compute mean
        mean_pos = [sum(learners[j][d] for j in range(pop_size)) / pop_size for d in range(dim)]

        # Teacher phase
        for i in range(pop_size):
            tf = rng.choice([1, 2])
            new_pos = [learners[i][d] + rng.random() * (teacher[d] - tf * mean_pos[d]) for d in range(dim)]
            new_sol = vec_to_sol(new_pos)
            new_fit = _eval_fitness(new_sol, sizes, canvas_w, canvas_h, texts)
            if new_fit > fits[i]:
                learners[i] = sol_to_vec(new_sol)
                fits[i] = new_fit

        # Learner phase
        for i in range(pop_size):
            j = rng.randint(0, pop_size - 1)
            while j == i:
                j = rng.randint(0, pop_size - 1)
            if fits[i] > fits[j]:
                new_pos = [learners[i][d] + rng.random() * (learners[i][d] - learners[j][d]) for d in range(dim)]
            else:
                new_pos = [learners[i][d] + rng.random() * (learners[j][d] - learners[i][d]) for d in range(dim)]
            new_sol = vec_to_sol(new_pos)
            new_fit = _eval_fitness(new_sol, sizes, canvas_w, canvas_h, texts)
            if new_fit > fits[i]:
                learners[i] = sol_to_vec(new_sol)
                fits[i] = new_fit

    best_idx = max(range(pop_size), key=lambda k: fits[k])
    return vec_to_sol(learners[best_idx])


def _solve_jaya(
    n_words: int, sizes: list[float], canvas_w: float, canvas_h: float,
    max_iter: int, rng: random.Random, texts: list[str] | None = None,
) -> list[tuple[float, float, float]]:
    """Jaya Algorithm: move toward best, away from worst. Zero hyperparameters."""
    pop_size = 20
    dim = n_words * 3

    def sol_to_vec(sol: list[tuple[float, float, float]]) -> list[float]:
        v: list[float] = []
        for x, y, r in sol:
            v.extend([x, y, r])
        return v

    def vec_to_sol(v: list[float]) -> list[tuple[float, float, float]]:
        s: list[tuple[float, float, float]] = []
        for i in range(0, len(v), 3):
            s.append((v[i], v[i + 1], v[i + 2]))
        return _clamp_solution(s, canvas_w, canvas_h)

    pop = [sol_to_vec(_random_solution(n_words, canvas_w, canvas_h, rng)) for _ in range(pop_size)]
    fits = [_eval_fitness(vec_to_sol(p), sizes, canvas_w, canvas_h, texts) for p in pop]

    for _ in range(max_iter):
        best_idx = max(range(pop_size), key=lambda k: fits[k])
        worst_idx = min(range(pop_size), key=lambda k: fits[k])
        best_p = pop[best_idx]
        worst_p = pop[worst_idx]

        for i in range(pop_size):
            r1, r2 = rng.random(), rng.random()
            new_pos = [
                pop[i][d]
                + r1 * (best_p[d] - abs(pop[i][d]))
                - r2 * (worst_p[d] - abs(pop[i][d]))
                for d in range(dim)
            ]
            new_sol = vec_to_sol(new_pos)
            new_fit = _eval_fitness(new_sol, sizes, canvas_w, canvas_h, texts)
            if new_fit > fits[i]:
                pop[i] = sol_to_vec(new_sol)
                fits[i] = new_fit

    best_idx = max(range(pop_size), key=lambda k: fits[k])
    return vec_to_sol(pop[best_idx])


def _solve_water_cycle(
    n_words: int, sizes: list[float], canvas_w: float, canvas_h: float,
    max_iter: int, rng: random.Random, texts: list[str] | None = None,
) -> list[tuple[float, float, float]]:
    """Water Cycle Algorithm: N_sr=4 (rivers+sea), evap_rate=0.01."""
    pop_size = 20
    n_sr = 4
    evap_rate = 0.01
    dim = n_words * 3

    def sol_to_vec(sol: list[tuple[float, float, float]]) -> list[float]:
        v: list[float] = []
        for x, y, r in sol:
            v.extend([x, y, r])
        return v

    def vec_to_sol(v: list[float]) -> list[tuple[float, float, float]]:
        s: list[tuple[float, float, float]] = []
        for i in range(0, len(v), 3):
            s.append((v[i], v[i + 1], v[i + 2]))
        return _clamp_solution(s, canvas_w, canvas_h)

    streams = [sol_to_vec(_random_solution(n_words, canvas_w, canvas_h, rng)) for _ in range(pop_size)]
    fits = [_eval_fitness(vec_to_sol(s), sizes, canvas_w, canvas_h, texts) for s in streams]

    sorted_idx = sorted(range(pop_size), key=lambda k: fits[k], reverse=True)
    # sea = index 0, rivers = indices 1..n_sr-1, streams = rest
    sea_idx = sorted_idx[0]

    for _ in range(max_iter):
        for i in range(pop_size):
            if i == sea_idx:
                continue
            # Flow toward sea or a river
            target = sea_idx if i >= n_sr else sea_idx
            if i < n_sr and i != sea_idx:
                target = sea_idx
            new_pos = [streams[i][d] + rng.random() * 2 * (streams[target][d] - streams[i][d]) for d in range(dim)]
            new_sol = vec_to_sol(new_pos)
            new_fit = _eval_fitness(new_sol, sizes, canvas_w, canvas_h, texts)
            if new_fit > fits[i]:
                streams[i] = sol_to_vec(new_sol)
                fits[i] = new_fit

        # Evaporation + rain
        for i in range(n_sr, pop_size):
            dist = math.sqrt(sum((streams[i][d] - streams[sea_idx][d]) ** 2 for d in range(dim)))
            if dist < evap_rate * canvas_w:
                streams[i] = sol_to_vec(_random_solution(n_words, canvas_w, canvas_h, rng))
                fits[i] = _eval_fitness(vec_to_sol(streams[i]), sizes, canvas_w, canvas_h, texts)

        # Update sea
        sea_idx = max(range(pop_size), key=lambda k: fits[k])

    return vec_to_sol(streams[sea_idx])


def _solve_biogeography(
    n_words: int, sizes: list[float], canvas_w: float, canvas_h: float,
    max_iter: int, rng: random.Random, texts: list[str] | None = None,
) -> list[tuple[float, float, float]]:
    """Biogeography-Based Optimization: immigration/emigration curves + mutation."""
    pop_size = 20
    dim = n_words * 3
    mutation_rate = 0.05

    def sol_to_vec(sol: list[tuple[float, float, float]]) -> list[float]:
        v: list[float] = []
        for x, y, r in sol:
            v.extend([x, y, r])
        return v

    def vec_to_sol(v: list[float]) -> list[tuple[float, float, float]]:
        s: list[tuple[float, float, float]] = []
        for i in range(0, len(v), 3):
            s.append((v[i], v[i + 1], v[i + 2]))
        return _clamp_solution(s, canvas_w, canvas_h)

    habitats = [sol_to_vec(_random_solution(n_words, canvas_w, canvas_h, rng)) for _ in range(pop_size)]
    fits = [_eval_fitness(vec_to_sol(h), sizes, canvas_w, canvas_h, texts) for h in habitats]

    for _ in range(max_iter):
        sorted_idx = sorted(range(pop_size), key=lambda k: fits[k], reverse=True)
        # Immigration/emigration rates linear
        lambdas = [1.0 - rank / pop_size for rank in range(pop_size)]  # immigration
        mus = [rank / pop_size for rank in range(pop_size)]  # emigration

        new_habitats = [list(h) for h in habitats]
        for idx_rank, i in enumerate(sorted_idx):
            for d in range(dim):
                if rng.random() < lambdas[idx_rank]:
                    # Immigration: pick emigrating habitat
                    # Roulette on emigration rates
                    total_mu = sum(mus)
                    r = rng.random() * total_mu
                    cum = 0.0
                    donor = sorted_idx[0]
                    for r_idx, j in enumerate(sorted_idx):
                        cum += mus[r_idx]
                        if cum >= r:
                            donor = j
                            break
                    new_habitats[i][d] = habitats[donor][d]

                # Mutation
                if rng.random() < mutation_rate:
                    if d % 3 == 0:
                        new_habitats[i][d] = rng.uniform(canvas_w * 0.05, canvas_w * 0.95)
                    elif d % 3 == 1:
                        new_habitats[i][d] = rng.uniform(canvas_h * 0.05, canvas_h * 0.95)
                    else:
                        new_habitats[i][d] = float(rng.choice(_META_ROTATIONS))

        for i in range(pop_size):
            sol = vec_to_sol(new_habitats[i])
            new_fit = _eval_fitness(sol, sizes, canvas_w, canvas_h, texts)
            if new_fit > fits[i]:
                habitats[i] = sol_to_vec(sol)
                fits[i] = new_fit

    best_idx = max(range(pop_size), key=lambda k: fits[k])
    return vec_to_sol(habitats[best_idx])


def _solve_artificial_bee_colony(
    n_words: int, sizes: list[float], canvas_w: float, canvas_h: float,
    max_iter: int, rng: random.Random, texts: list[str] | None = None,
) -> list[tuple[float, float, float]]:
    """Artificial Bee Colony: employed->onlooker->scout, limit=n_words*5."""
    pop_size = 20
    limit = n_words * 5
    dim = n_words * 3

    def sol_to_vec(sol: list[tuple[float, float, float]]) -> list[float]:
        v: list[float] = []
        for x, y, r in sol:
            v.extend([x, y, r])
        return v

    def vec_to_sol(v: list[float]) -> list[tuple[float, float, float]]:
        s: list[tuple[float, float, float]] = []
        for i in range(0, len(v), 3):
            s.append((v[i], v[i + 1], v[i + 2]))
        return _clamp_solution(s, canvas_w, canvas_h)

    food_sources = [sol_to_vec(_random_solution(n_words, canvas_w, canvas_h, rng)) for _ in range(pop_size)]
    fits = [_eval_fitness(vec_to_sol(f), sizes, canvas_w, canvas_h, texts) for f in food_sources]
    trials = [0] * pop_size

    for _ in range(max_iter):
        # Employed bee phase
        for i in range(pop_size):
            k = rng.randint(0, pop_size - 1)
            while k == i:
                k = rng.randint(0, pop_size - 1)
            d_idx = rng.randint(0, dim - 1)
            new_pos = list(food_sources[i])
            phi = rng.uniform(-1, 1)
            new_pos[d_idx] = food_sources[i][d_idx] + phi * (food_sources[i][d_idx] - food_sources[k][d_idx])
            new_sol = vec_to_sol(new_pos)
            new_fit = _eval_fitness(new_sol, sizes, canvas_w, canvas_h, texts)
            if new_fit > fits[i]:
                food_sources[i] = sol_to_vec(new_sol)
                fits[i] = new_fit
                trials[i] = 0
            else:
                trials[i] += 1

        # Onlooker bee phase (roulette wheel)
        min_fit = min(fits)
        adjusted = [f - min_fit + 1e-10 for f in fits]
        total_fit = sum(adjusted)
        for _ in range(pop_size):
            # Select food source
            r = rng.random() * total_fit
            cum = 0.0
            selected = 0
            for j in range(pop_size):
                cum += adjusted[j]
                if cum >= r:
                    selected = j
                    break

            k = rng.randint(0, pop_size - 1)
            while k == selected:
                k = rng.randint(0, pop_size - 1)
            d_idx = rng.randint(0, dim - 1)
            new_pos = list(food_sources[selected])
            phi = rng.uniform(-1, 1)
            new_pos[d_idx] = food_sources[selected][d_idx] + phi * (food_sources[selected][d_idx] - food_sources[k][d_idx])
            new_sol = vec_to_sol(new_pos)
            new_fit = _eval_fitness(new_sol, sizes, canvas_w, canvas_h, texts)
            if new_fit > fits[selected]:
                food_sources[selected] = sol_to_vec(new_sol)
                fits[selected] = new_fit
                trials[selected] = 0
            else:
                trials[selected] += 1

        # Scout bee phase
        for i in range(pop_size):
            if trials[i] > limit:
                food_sources[i] = sol_to_vec(_random_solution(n_words, canvas_w, canvas_h, rng))
                fits[i] = _eval_fitness(vec_to_sol(food_sources[i]), sizes, canvas_w, canvas_h, texts)
                trials[i] = 0

    best_idx = max(range(pop_size), key=lambda k: fits[k])
    return vec_to_sol(food_sources[best_idx])


def _solve_tabu_search(
    n_words: int, sizes: list[float], canvas_w: float, canvas_h: float,
    max_iter: int, rng: random.Random, texts: list[str] | None = None,
) -> list[tuple[float, float, float]]:
    """Tabu Search: neighborhood perturbation, tabu list size=20, aspiration."""
    tabu_size = 20
    dim = n_words * 3

    def sol_to_vec(sol: list[tuple[float, float, float]]) -> list[float]:
        v: list[float] = []
        for x, y, r in sol:
            v.extend([x, y, r])
        return v

    def vec_to_sol(v: list[float]) -> list[tuple[float, float, float]]:
        s: list[tuple[float, float, float]] = []
        for i in range(0, len(v), 3):
            s.append((v[i], v[i + 1], v[i + 2]))
        return _clamp_solution(s, canvas_w, canvas_h)

    def sol_hash(sol: list[tuple[float, float, float]]) -> int:
        return hash(tuple(round(v, 1) for pos in sol for v in pos))

    current = _random_solution(n_words, canvas_w, canvas_h, rng)
    current_fit = _eval_fitness(current, sizes, canvas_w, canvas_h, texts)
    best = list(current)
    best_fit = current_fit
    tabu_list: list[int] = []

    for _ in range(max_iter):
        # Generate neighborhood
        neighbors: list[list[tuple[float, float, float]]] = []
        n_neighbors = 10
        for _ in range(n_neighbors):
            neighbor = list(current)
            n_perturb = rng.randint(1, min(3, n_words))
            for _ in range(n_perturb):
                idx = rng.randint(0, n_words - 1)
                x, y, rot = neighbor[idx]
                x += rng.gauss(0, canvas_w * 0.08)
                y += rng.gauss(0, canvas_h * 0.08)
                rot = rng.choice(_META_ROTATIONS)
                neighbor[idx] = (x, y, float(rot))
            neighbors.append(_clamp_solution(neighbor, canvas_w, canvas_h))

        # Pick best non-tabu neighbor (or aspiration)
        best_neighbor = None
        best_neighbor_fit = float("-inf")
        for nb in neighbors:
            nb_fit = _eval_fitness(nb, sizes, canvas_w, canvas_h, texts)
            h = sol_hash(nb)
            if h not in tabu_list or nb_fit > best_fit:  # aspiration
                if nb_fit > best_neighbor_fit:
                    best_neighbor = nb
                    best_neighbor_fit = nb_fit

        if best_neighbor is not None:
            current = best_neighbor
            current_fit = best_neighbor_fit
            tabu_list.append(sol_hash(current))
            if len(tabu_list) > tabu_size:
                tabu_list.pop(0)
            if current_fit > best_fit:
                best = list(current)
                best_fit = current_fit

    return best


def _solve_cultural(
    n_words: int, sizes: list[float], canvas_w: float, canvas_h: float,
    max_iter: int, rng: random.Random, texts: list[str] | None = None,
) -> list[tuple[float, float, float]]:
    """Cultural Algorithm: belief space with normative knowledge, acceptance=0.2."""
    pop_size = 20
    acceptance_rate = 0.2
    dim = n_words * 3

    def sol_to_vec(sol: list[tuple[float, float, float]]) -> list[float]:
        v: list[float] = []
        for x, y, r in sol:
            v.extend([x, y, r])
        return v

    def vec_to_sol(v: list[float]) -> list[tuple[float, float, float]]:
        s: list[tuple[float, float, float]] = []
        for i in range(0, len(v), 3):
            s.append((v[i], v[i + 1], v[i + 2]))
        return _clamp_solution(s, canvas_w, canvas_h)

    pop = [sol_to_vec(_random_solution(n_words, canvas_w, canvas_h, rng)) for _ in range(pop_size)]
    fits = [_eval_fitness(vec_to_sol(p), sizes, canvas_w, canvas_h, texts) for p in pop]

    # Belief space: min/max bounds per dimension from best individuals
    belief_min = [min(pop[i][d] for i in range(pop_size)) for d in range(dim)]
    belief_max = [max(pop[i][d] for i in range(pop_size)) for d in range(dim)]

    for _ in range(max_iter):
        # Accept top fraction into belief space
        sorted_idx = sorted(range(pop_size), key=lambda k: fits[k], reverse=True)
        n_accept = max(1, int(acceptance_rate * pop_size))
        accepted = sorted_idx[:n_accept]

        # Update belief space
        for d in range(dim):
            vals = [pop[i][d] for i in accepted]
            belief_min[d] = min(vals)
            belief_max[d] = max(vals)

        # Influence: generate new population using belief space
        for i in range(pop_size):
            new_pos: list[float] = []
            for d in range(dim):
                span = belief_max[d] - belief_min[d]
                if span < 1e-6:
                    span = canvas_w * 0.1 if d % 3 == 0 else canvas_h * 0.1 if d % 3 == 1 else 20.0
                new_val = pop[i][d] + rng.uniform(-1, 1) * span * 0.3
                new_pos.append(new_val)
            new_sol = vec_to_sol(new_pos)
            new_fit = _eval_fitness(new_sol, sizes, canvas_w, canvas_h, texts)
            if new_fit > fits[i]:
                pop[i] = sol_to_vec(new_sol)
                fits[i] = new_fit

    best_idx = max(range(pop_size), key=lambda k: fits[k])
    return vec_to_sol(pop[best_idx])


def _solve_invasive_weed(
    n_words: int, sizes: list[float], canvas_w: float, canvas_h: float,
    max_iter: int, rng: random.Random, texts: list[str] | None = None,
) -> list[tuple[float, float, float]]:
    """Invasive Weed Optimization: seeds=5 initial, max_seeds=5, sigma decay."""
    initial_pop = 5
    max_pop = 20
    max_seeds = 5
    sigma_init = min(canvas_w, canvas_h) / 4
    sigma_final = min(canvas_w, canvas_h) / 40
    dim = n_words * 3

    def sol_to_vec(sol: list[tuple[float, float, float]]) -> list[float]:
        v: list[float] = []
        for x, y, r in sol:
            v.extend([x, y, r])
        return v

    def vec_to_sol(v: list[float]) -> list[tuple[float, float, float]]:
        s: list[tuple[float, float, float]] = []
        for i in range(0, len(v), 3):
            s.append((v[i], v[i + 1], v[i + 2]))
        return _clamp_solution(s, canvas_w, canvas_h)

    weeds = [sol_to_vec(_random_solution(n_words, canvas_w, canvas_h, rng)) for _ in range(initial_pop)]
    fits = [_eval_fitness(vec_to_sol(w), sizes, canvas_w, canvas_h, texts) for w in weeds]

    for it in range(max_iter):
        sigma = sigma_init - (sigma_init - sigma_final) * ((it / max(max_iter - 1, 1)) ** 2)

        # Seed production
        if len(fits) > 0:
            min_fit = min(fits)
            max_fit = max(fits)
            span = max_fit - min_fit if max_fit != min_fit else 1.0

        new_weeds: list[list[float]] = []
        new_fits: list[float] = []
        for i in range(len(weeds)):
            n_seeds = max(1, int(1 + (fits[i] - min_fit) / span * (max_seeds - 1)))
            for _ in range(n_seeds):
                child = [weeds[i][d] + rng.gauss(0, sigma) for d in range(dim)]
                child_sol = vec_to_sol(child)
                child_fit = _eval_fitness(child_sol, sizes, canvas_w, canvas_h, texts)
                new_weeds.append(sol_to_vec(child_sol))
                new_fits.append(child_fit)

        weeds.extend(new_weeds)
        fits.extend(new_fits)

        # Competitive exclusion: keep top max_pop
        if len(weeds) > max_pop:
            sorted_idx = sorted(range(len(weeds)), key=lambda k: fits[k], reverse=True)
            weeds = [weeds[sorted_idx[i]] for i in range(max_pop)]
            fits = [fits[sorted_idx[i]] for i in range(max_pop)]

    best_idx = max(range(len(weeds)), key=lambda k: fits[k])
    return vec_to_sol(weeds[best_idx])


def _solve_charged_system_search(
    n_words: int, sizes: list[float], canvas_w: float, canvas_h: float,
    max_iter: int, rng: random.Random, texts: list[str] | None = None,
) -> list[tuple[float, float, float]]:
    """Charged System Search: ka=0.1, charged memory ratio=0.1."""
    pop_size = 20
    ka = 0.1
    dim = n_words * 3

    def sol_to_vec(sol: list[tuple[float, float, float]]) -> list[float]:
        v: list[float] = []
        for x, y, r in sol:
            v.extend([x, y, r])
        return v

    def vec_to_sol(v: list[float]) -> list[tuple[float, float, float]]:
        s: list[tuple[float, float, float]] = []
        for i in range(0, len(v), 3):
            s.append((v[i], v[i + 1], v[i + 2]))
        return _clamp_solution(s, canvas_w, canvas_h)

    particles = [sol_to_vec(_random_solution(n_words, canvas_w, canvas_h, rng)) for _ in range(pop_size)]
    velocities = [[0.0] * dim for _ in range(pop_size)]
    fits = [_eval_fitness(vec_to_sol(p), sizes, canvas_w, canvas_h, texts) for p in particles]

    for it in range(max_iter):
        worst = min(fits)
        best = max(fits)
        span = best - worst if best != worst else 1.0

        # Charge magnitude proportional to fitness
        charges = [(fits[i] - worst) / span for i in range(pop_size)]

        # Separation distance for charged memory
        all_dists: list[float] = []
        for i in range(pop_size):
            for j in range(i + 1, pop_size):
                d_ij = math.sqrt(sum((particles[i][d] - particles[j][d]) ** 2 for d in range(dim))) + 1e-10
                all_dists.append(d_ij)
        r_a = max(all_dists) * 0.1 if all_dists else canvas_w * 0.1

        for i in range(pop_size):
            force = [0.0] * dim
            for j in range(pop_size):
                if i == j:
                    continue
                r_ij = math.sqrt(sum((particles[i][d] - particles[j][d]) ** 2 for d in range(dim))) + 1e-10
                if r_ij < r_a:
                    for d_idx in range(dim):
                        force[d_idx] += charges[j] * (particles[j][d_idx] - particles[i][d_idx]) / (r_ij ** 3) * (r_ij)
                else:
                    for d_idx in range(dim):
                        force[d_idx] += charges[j] * (particles[j][d_idx] - particles[i][d_idx]) / (r_ij ** 2)

            for d_idx in range(dim):
                velocities[i][d_idx] = rng.random() * velocities[i][d_idx] + ka * force[d_idx]
                particles[i][d_idx] += velocities[i][d_idx]

            sol = vec_to_sol(particles[i])
            particles[i] = sol_to_vec(sol)
            fits[i] = _eval_fitness(sol, sizes, canvas_w, canvas_h, texts)

    best_idx = max(range(pop_size), key=lambda k: fits[k])
    return vec_to_sol(particles[best_idx])


def _solve_stochastic_fractal_search(
    n_words: int, sizes: list[float], canvas_w: float, canvas_h: float,
    max_iter: int, rng: random.Random, texts: list[str] | None = None,
) -> list[tuple[float, float, float]]:
    """Stochastic Fractal Search: gaussian walks at 2 scales."""
    pop_size = 20
    dim = n_words * 3

    def sol_to_vec(sol: list[tuple[float, float, float]]) -> list[float]:
        v: list[float] = []
        for x, y, r in sol:
            v.extend([x, y, r])
        return v

    def vec_to_sol(v: list[float]) -> list[tuple[float, float, float]]:
        s: list[tuple[float, float, float]] = []
        for i in range(0, len(v), 3):
            s.append((v[i], v[i + 1], v[i + 2]))
        return _clamp_solution(s, canvas_w, canvas_h)

    points = [sol_to_vec(_random_solution(n_words, canvas_w, canvas_h, rng)) for _ in range(pop_size)]
    fits = [_eval_fitness(vec_to_sol(p), sizes, canvas_w, canvas_h, texts) for p in points]
    best_idx = max(range(pop_size), key=lambda k: fits[k])
    g_best = list(points[best_idx])
    g_best_fit = fits[best_idx]

    for it in range(max_iter):
        # Diffusion process: two gaussian walks
        sigma_global = canvas_w * 0.1 * (1 - it / max(max_iter, 1))
        sigma_local = canvas_w * 0.02 * (1 - it / max(max_iter, 1))

        for i in range(pop_size):
            # Global diffusion
            new_global = [points[i][d] + rng.gauss(0, sigma_global) for d in range(dim)]
            sol_g = vec_to_sol(new_global)
            fit_g = _eval_fitness(sol_g, sizes, canvas_w, canvas_h, texts)

            # Local exploitation
            new_local = [points[i][d] + rng.gauss(0, sigma_local) * (g_best[d] - points[i][d]) for d in range(dim)]
            sol_l = vec_to_sol(new_local)
            fit_l = _eval_fitness(sol_l, sizes, canvas_w, canvas_h, texts)

            # Keep the best of the three
            candidates = [(points[i], fits[i]), (sol_to_vec(sol_g), fit_g), (sol_to_vec(sol_l), fit_l)]
            best_c = max(candidates, key=lambda c: c[1])
            points[i] = list(best_c[0])
            fits[i] = best_c[1]

            if fits[i] > g_best_fit:
                g_best = list(points[i])
                g_best_fit = fits[i]

        # Update: random replacement of worst with mutated best
        worst_idx = min(range(pop_size), key=lambda k: fits[k])
        if rng.random() < 0.1:
            new_pt = [g_best[d] + rng.gauss(0, sigma_local * 2) for d in range(dim)]
            sol_new = vec_to_sol(new_pt)
            fit_new = _eval_fitness(sol_new, sizes, canvas_w, canvas_h, texts)
            if fit_new > fits[worst_idx]:
                points[worst_idx] = sol_to_vec(sol_new)
                fits[worst_idx] = fit_new

    return vec_to_sol(g_best)


# ---------------------------------------------------------------------------
# Solver registry
# ---------------------------------------------------------------------------

_META_SOLVERS: dict[str, callable] = {
    "Harmony Search": _solve_harmony_search,
    "Simulated Annealing": _solve_simulated_annealing,
    "Particle Swarm": _solve_particle_swarm,
    "Differential Evolution": _solve_differential_evolution,
    "Ant Colony": _solve_ant_colony,
    "Firefly": _solve_firefly,
    "Cuckoo Search": _solve_cuckoo_search,
    "Bat Algorithm": _solve_bat,
    "Grey Wolf": _solve_grey_wolf,
    "Whale Optimization": _solve_whale,
    "Gravitational Search": _solve_gravitational_search,
    "Flower Pollination": _solve_flower_pollination,
    "Moth-Flame": _solve_moth_flame,
    "Salp Swarm": _solve_salp_swarm,
    "Sine Cosine": _solve_sine_cosine,
    "Teaching-Learning": _solve_teaching_learning,
    "Jaya": _solve_jaya,
    "Water Cycle": _solve_water_cycle,
    "Biogeography-Based": _solve_biogeography,
    "Artificial Bee Colony": _solve_artificial_bee_colony,
    "Tabu Search": _solve_tabu_search,
    "Cultural Algorithm": _solve_cultural,
    "Invasive Weed": _solve_invasive_weed,
    "Charged System Search": _solve_charged_system_search,
    "Stochastic Fractal Search": _solve_stochastic_fractal_search,
}


# ---------------------------------------------------------------------------
# Metaheuristic animation renderer
# ---------------------------------------------------------------------------

class MetaheuristicAnimRenderer(SvgWordCloudEngine):
    """Animated word cloud showing 25 metaheuristic optimization algorithms.

    Each algorithm solves the same word placement problem, producing a frame.
    All 25 frames are stacked in a single SVG with CSS opacity animation
    that cycles through them infinitely.
    """

    def __init__(
        self,
        *,
        hold_duration: float = 2.0,
        fade_duration: float = 0.6,
        pop_size: int = 20,
        max_iter: int = 300,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.hold_duration = hold_duration
        self.fade_duration = fade_duration
        self.pop_size = pop_size
        self.max_iter = max_iter

    def _prepare_words(
        self, frequencies: dict[str, float],
    ) -> tuple[list[str], list[float], list[float], list[str], list[int], list[float]]:
        """Prepare word data from frequencies.

        Returns (texts, sizes, freq_values, colors, weights, opacities).
        """
        sorted_words = sorted(frequencies.items(), key=lambda kv: kv[1], reverse=True)
        min_freq = min(frequencies.values())
        max_freq = max(frequencies.values())
        total = len(sorted_words)

        _GOLDEN_ANGLE_FRAC = (math.sqrt(5) - 1) / 2

        texts: list[str] = []
        sizes_list: list[float] = []
        colors: list[str] = []
        weights: list[int] = []
        opacities: list[float] = []

        for idx, (word, freq) in enumerate(sorted_words):
            texts.append(word)
            sizes_list.append(self._frequency_to_size(freq, min_freq, max_freq))
            weights.append(self._frequency_to_weight(freq, min_freq, max_freq))
            opacities.append(self._frequency_to_opacity(freq, min_freq, max_freq))
            color_idx = int(((idx * _GOLDEN_ANGLE_FRAC) % 1.0) * total)
            colors.append(self.color_func(color_idx, total))

        return texts, sizes_list, [f for _, f in sorted_words], colors, weights, opacities

    def _solve_all(
        self,
        texts: list[str],
        sizes: list[float],
    ) -> list[tuple[str, list[tuple[float, float, float]]]]:
        """Run all 25 metaheuristic solvers and return (name, placements) pairs."""
        n_words = len(texts)
        results: list[tuple[str, list[tuple[float, float, float]]]] = []

        for name, solver_fn in _META_SOLVERS.items():
            rng = random.Random(self.seed)
            placements = solver_fn(
                n_words, sizes, float(self.width), float(self.height),
                self.max_iter, rng, texts,
            )
            results.append((name, placements))
            logger.debug("MetaheuristicAnimRenderer: {name} completed", name=name)

        return results

    def _render_frame(
        self,
        algo_name: str,
        positions: list[tuple[float, float, float]],
        texts: list[str],
        sizes: list[float],
        colors: list[str],
        weights: list[int],
        opacities: list[float],
    ) -> list[PlacedWord]:
        """Convert solver output to PlacedWord list for one frame."""
        placed: list[PlacedWord] = []
        for i in range(len(texts)):
            x, y, rot = positions[i]
            placed.append(
                PlacedWord(
                    text=texts[i],
                    x=x,
                    y=y,
                    font_size=sizes[i],
                    rotation=rot,
                    color=colors[i],
                    font_weight=weights[i],
                    font_family=self.font_family,
                    opacity=opacities[i],
                )
            )
        return placed

    def _render_frame_svg_body(
        self,
        placed_words: list[PlacedWord],
        algo_name: str,
        frame_idx: int,
    ) -> str:
        """Render the SVG elements for a single frame (words + algorithm label)."""
        lines: list[str] = []

        glow_threshold = self._glow_size_threshold(placed_words)
        tier1_threshold = float("inf")
        tier2_threshold = float("inf")
        if placed_words:
            pw_sizes = sorted((pw.font_size for pw in placed_words), reverse=True)
            t1_idx = max(1, int(len(pw_sizes) * 0.10))
            tier1_threshold = pw_sizes[min(t1_idx, len(pw_sizes) - 1)]
            t2_idx = max(1, int(len(pw_sizes) * 0.30))
            tier2_threshold = pw_sizes[min(t2_idx, len(pw_sizes) - 1)]

        for pw in placed_words:
            attrs_parts = [
                f'x="{pw.x:.1f}"',
                f'y="{pw.y:.1f}"',
                f'font-size="{pw.font_size:.1f}"',
                f'fill="{pw.color}"',
                f'font-family="{pw.font_family or self.font_family}"',
                f'font-weight="{pw.font_weight}"',
                'text-anchor="middle"',
                'dominant-baseline="central"',
            ]
            if pw.opacity < 1.0:
                attrs_parts.append(f'opacity="{pw.opacity:.2f}"')
            if pw.rotation != 0:
                attrs_parts.append(
                    f'transform="rotate({pw.rotation:.1f},{pw.x:.1f},{pw.y:.1f})"'
                )
            if pw.font_size >= glow_threshold:
                attrs_parts.append(f'filter="url(#wc-glow-f{frame_idx})"')
            elif pw.font_size >= tier2_threshold:
                attrs_parts.append(f'filter="url(#wc-shadow-f{frame_idx})"')
            if pw.font_size >= tier1_threshold:
                spacing = max(0.5, pw.font_size * 0.02)
                attrs_parts.append(f'letter-spacing="{spacing:.1f}"')

            lines.append(f'  <text {" ".join(attrs_parts)}>{pw.text}</text>')

        # Algorithm name label at bottom
        lines.append(
            f'  <text class="algo-label" x="50%" y="95%" text-anchor="middle"'
            f' fill="#555555" opacity="0.6"'
            f' style="font: 500 14px {self.font_family};">'
            f'{algo_name}</text>'
        )
        return "\n".join(lines)

    def _stack_frames(
        self,
        frame_bodies: list[str],
        algo_names: list[str],
    ) -> str:
        """Stack all frames into a single SVG with CSS opacity animation.

        Each frame gets 2s hold + 0.6s fade, cycling infinitely.
        """
        n = len(frame_bodies)
        frame_time = self.hold_duration + self.fade_duration
        total_duration = frame_time * n

        # Build CSS keyframes for cycling animation
        css_lines = [
            "/* Metaheuristic word cloud animation: 25 algorithms cycling */",
            ".mf { opacity: 0; position: absolute; }",
        ]

        # Each frame visible for (hold + fade) / total of the cycle
        visible_pct = (self.hold_duration / total_duration) * 100
        fade_in_pct = (self.fade_duration / total_duration) * 100
        fade_out_pct = fade_in_pct

        for i in range(n):
            start_pct = (i * frame_time / total_duration) * 100
            visible_start = start_pct + fade_in_pct
            visible_end = visible_start + visible_pct
            end_pct = visible_end + fade_out_pct
            # Wrap-around safety
            kf_name = f"mf{i}"
            css_lines.append(f"@keyframes {kf_name} {{")
            if i == 0:
                css_lines.append(f"  0% {{ opacity: 1; }}")
                css_lines.append(f"  {visible_pct:.2f}% {{ opacity: 1; }}")
                css_lines.append(f"  {visible_pct + fade_out_pct:.2f}% {{ opacity: 0; }}")
                css_lines.append(f"  {100 - fade_in_pct:.2f}% {{ opacity: 0; }}")
                css_lines.append(f"  100% {{ opacity: 1; }}")
            else:
                if start_pct > 0:
                    css_lines.append(f"  0% {{ opacity: 0; }}")
                    css_lines.append(f"  {start_pct:.2f}% {{ opacity: 0; }}")
                css_lines.append(f"  {min(visible_start, 99.99):.2f}% {{ opacity: 1; }}")
                css_lines.append(f"  {min(visible_end, 99.99):.2f}% {{ opacity: 1; }}")
                if end_pct < 100:
                    css_lines.append(f"  {min(end_pct, 99.99):.2f}% {{ opacity: 0; }}")
                    css_lines.append(f"  100% {{ opacity: 0; }}")
                else:
                    css_lines.append(f"  100% {{ opacity: 0; }}")
            css_lines.append("}")
            css_lines.append(
                f".mf.mf{i} {{ animation: {kf_name} {total_duration:.1f}s infinite; }}"
            )

        css = "\n".join(css_lines)

        # Build SVG
        svg_parts: list[str] = [
            f'<svg xmlns="http://www.w3.org/2000/svg"'
            f' width="{self.width}" height="{self.height}"'
            f' viewBox="0 0 {self.width} {self.height}">',
            "<defs>",
        ]

        # Add glow/shadow filters for each frame (namespaced)
        for fi in range(n):
            svg_parts.append(
                f'  <filter id="wc-glow-f{fi}" x="-30%" y="-30%" width="160%" height="160%">'
            )
            svg_parts.append(
                f'    <feGaussianBlur in="SourceGraphic" stdDeviation="2.5" result="glow1"/>'
            )
            svg_parts.append(
                f'    <feGaussianBlur in="SourceGraphic" stdDeviation="0.8" result="glow2"/>'
            )
            svg_parts.append("    <feMerge>")
            svg_parts.append('      <feMergeNode in="glow1"/>')
            svg_parts.append('      <feMergeNode in="glow2"/>')
            svg_parts.append('      <feMergeNode in="SourceGraphic"/>')
            svg_parts.append("    </feMerge>")
            svg_parts.append("  </filter>")
            svg_parts.append(
                f'  <filter id="wc-shadow-f{fi}" x="-10%" y="-10%" width="120%" height="120%">'
            )
            svg_parts.append(
                f'    <feDropShadow dx="0" dy="1" stdDeviation="0.5" flood-color="#00000020"/>'
            )
            svg_parts.append("  </filter>")

        # Background gradient
        svg_parts.append('  <radialGradient id="wc-bg-grad" cx="50%" cy="50%" r="75%">')
        svg_parts.append('    <stop offset="0%" stop-color="#fafbfc" stop-opacity="1"/>')
        svg_parts.append('    <stop offset="100%" stop-color="#f0f1f3" stop-opacity="1"/>')
        svg_parts.append("  </radialGradient>")
        svg_parts.append("</defs>")
        svg_parts.append(f'<style>\n{css}\n</style>')

        # Background rect
        svg_parts.append(
            f'<rect width="{self.width}" height="{self.height}" fill="url(#wc-bg-grad)"/>'
        )

        # Frame groups
        for i, body in enumerate(frame_bodies):
            svg_parts.append(f'<g class="mf mf{i}">')
            svg_parts.append(body)
            svg_parts.append("</g>")

        svg_parts.append("</svg>")
        return "\n".join(svg_parts)

    def place_words(
        self,
        frequencies: dict[str, float],
    ) -> list[PlacedWord]:
        """Place words using the first metaheuristic solver (Harmony Search).

        For the animated version, use generate() directly.
        """
        if not frequencies:
            return []
        texts, sizes, _, colors, weights, opacities = self._prepare_words(frequencies)
        rng = random.Random(self.seed)
        positions = _solve_harmony_search(
            len(texts), sizes, float(self.width), float(self.height),
            self.max_iter, rng, texts,
        )
        return self._render_frame("Harmony Search", positions, texts, sizes, colors, weights, opacities)

    def generate(self, frequencies: dict[str, float], palette: str | None = None, source: str | None = None) -> str:
        """Generate animated SVG with all 25 metaheuristic algorithm frames.

        Parameters
        ----------
        frequencies : dict mapping word text to frequency count.
        palette : optional color palette name (uses constructor default if None).
        source : optional source label (unused, for API compatibility).
        """
        if palette is not None:
            self.color_func = COLOR_FUNCS.get(palette, self.color_func)

        if not frequencies:
            return '<svg xmlns="http://www.w3.org/2000/svg"></svg>'

        texts, sizes, _, colors, weights, opacities = self._prepare_words(frequencies)
        logger.info(
            "MetaheuristicAnimRenderer: solving {n} words with 25 algorithms",
            n=len(texts),
        )

        all_results = self._solve_all(texts, sizes)

        frame_bodies: list[str] = []
        algo_names: list[str] = []
        for name, positions in all_results:
            placed = self._render_frame(name, positions, texts, sizes, colors, weights, opacities)
            body = self._render_frame_svg_body(placed, name, len(frame_bodies))
            frame_bodies.append(body)
            algo_names.append(name)

        return self._stack_frames(frame_bodies, algo_names)


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

RENDERERS: dict[str, type[SvgWordCloudEngine]] = {
    "wordle": WordleRenderer,
    "clustered": ClusteredRenderer,
    "typographic": TypographicRenderer,
    "shaped": ShapedRenderer,
    "metaheuristic-anim": MetaheuristicAnimRenderer,
}


def get_renderer(name: str, **kwargs) -> SvgWordCloudEngine:
    """Factory: create a renderer by name."""
    cls = RENDERERS.get(name)
    if cls is None:
        raise ValueError(
            f"Unknown renderer {name!r}. Choose from: {', '.join(RENDERERS)}"
        )
    return cls(**kwargs)
