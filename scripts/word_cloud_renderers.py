"""SVG-native word cloud renderers.

Four canonical SOTA approaches for generating word clouds as pure SVG:
  - WordleRenderer: classic Wordle spiral placement (Viegas & Wattenberg 2008)
  - ClusteredRenderer: semantic clustering + per-cluster Wordle placement
  - TypographicRenderer: editorial baseline-grid typography
  - ShapedRenderer: words packed inside a shape boundary
"""

from __future__ import annotations

import colorsys
import math
import random
import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
from dataclasses import dataclass

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
    font_family: str = "sans-serif"


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

def _hsl_to_css(h: float, s: float, lightness: float) -> str:
    """Convert HSL (0-360, 0-1, 0-1) to hex CSS color."""
    r, g, b = colorsys.hls_to_rgb(h / 360.0, lightness, s)
    return f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}"


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


COLOR_FUNCS = {
    "primary": primary_color_func,
    "analogous": analogous_color_func,
    "complementary": complementary_color_func,
    "triadic": triadic_color_func,
}

# Curated palette for the typographic renderer
TYPOGRAPHIC_PALETTE = ["#60A5FA", "#34D399", "#F59E0B", "#EF4444", "#A78BFA"]

# Cluster-specific palettes (hue families)
CLUSTER_PALETTES: dict[str, list[str]] = {
    "AI/ML": ["#7C3AED", "#8B5CF6", "#A78BFA", "#C4B5FD", "#6D28D9"],
    "Web": ["#2563EB", "#3B82F6", "#60A5FA", "#93C5FD", "#1D4ED8"],
    "Data": ["#059669", "#10B981", "#34D399", "#6EE7B7", "#047857"],
    "DevOps": ["#D97706", "#F59E0B", "#FBBF24", "#FCD34D", "#B45309"],
    "Languages": ["#DC2626", "#EF4444", "#F87171", "#FCA5A5", "#B91C1C"],
    "Tools": ["#0891B2", "#06B6D4", "#22D3EE", "#67E8F9", "#0E7490"],
    "Security": ["#BE185D", "#EC4899", "#F472B6", "#F9A8D4", "#9D174D"],
    "Other": ["#4B5563", "#6B7280", "#9CA3AF", "#D1D5DB", "#374151"],
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
        font_family: str = "sans-serif",
        color_func_name: str = "primary",
        seed: int | None = 42,
        padding: float = 4.0,
        min_font_size: float = 10.0,
        max_font_size: float = 80.0,
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
        """Map a frequency value to a font size."""
        if max_freq == min_freq:
            return (self.min_font_size + self.max_font_size) / 2
        t = (freq - min_freq) / (max_freq - min_freq)
        return self.min_font_size + t * (self.max_font_size - self.min_font_size)

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
        """Compute the AABB for placed text, accounting for rotation."""
        w = self._estimate_text_width(text, font_size)
        h = self._estimate_text_height(font_size)
        if abs(rotation) in (90, 270):
            w, h = h, w
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

    def render_svg(self, placed_words: list[PlacedWord]) -> str:
        """Render placed words into an SVG string."""
        root = ET.Element(
            "svg",
            xmlns="http://www.w3.org/2000/svg",
            width=str(self.width),
            height=str(self.height),
            viewBox=f"0 0 {self.width} {self.height}",
        )
        # transparent background
        ET.SubElement(
            root,
            "rect",
            width=str(self.width),
            height=str(self.height),
            fill="none",
        )

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
            if pw.rotation != 0:
                attrs["transform"] = (
                    f"rotate({pw.rotation:.1f},{pw.x:.1f},{pw.y:.1f})"
                )
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
    """

    def __init__(
        self,
        *,
        rotation_choices: list[float] | None = None,
        spiral_tightness: float = 1.0,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.rotation_choices = rotation_choices if rotation_choices is not None else [0, 90]
        self.spiral_tightness = spiral_tightness

    def _spiral_positions(
        self,
        cx: float,
        cy: float,
        step_size: float,
        max_steps: int = 2000,
    ):
        """Yield (x, y) along an Archimedean spiral."""
        a = 0.0
        b = step_size * self.spiral_tightness
        for i in range(max_steps):
            theta = i * 0.1
            r = a + b * theta
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

        placed: list[PlacedWord] = []
        placed_bboxes: list[BBox] = []

        for idx, (word, freq) in enumerate(sorted_words):
            font_size = self._frequency_to_size(freq, min_freq, max_freq)
            rotation = self._rng.choice(self.rotation_choices)
            color = self.color_func(idx, total)

            step = max(1.0, font_size * 0.15)
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
                            font_family=self.font_family,
                        )
                    )
                    placed_bboxes.append(bbox)
                    found = True
                    break

            if not found:
                # Try with reduced font size as fallback
                for scale in (0.7, 0.5, 0.35):
                    reduced = font_size * scale
                    if reduced < self.min_font_size:
                        break
                    for x, y in self._spiral_positions(cx, cy, max(1.0, reduced * 0.15)):
                        bbox = self._estimate_bbox(word, reduced, x, y, rotation)
                        if self._in_bounds(bbox) and not self._check_collision(bbox, placed_bboxes):
                            placed.append(
                                PlacedWord(
                                    text=word,
                                    x=x,
                                    y=y,
                                    font_size=reduced,
                                    rotation=rotation,
                                    color=color,
                                    font_family=self.font_family,
                                )
                            )
                            placed_bboxes.append(bbox)
                            found = True
                            break
                    if found:
                        break

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

            # Optional faint cluster label
            if self.show_cluster_labels:
                label_size = min(sw, sh) * 0.18
                placed.append(
                    PlacedWord(
                        text=cluster_name,
                        x=cx,
                        y=cy,
                        font_size=label_size,
                        rotation=0,
                        color="#e5e7eb",  # very faint gray
                        font_weight=300,
                        font_family=self.font_family,
                    )
                )

            sorted_words = sorted(
                clusters[cluster_name].items(), key=lambda kv: kv[1], reverse=True
            )

            for local_idx, (word, freq) in enumerate(sorted_words):
                font_size = self._frequency_to_size(freq, min_freq, max_freq)
                # Scale font down slightly so words fit in their sector
                font_size = min(font_size, sh * 0.4, sw * 0.3)
                if font_size < self.min_font_size:
                    font_size = self.min_font_size

                color = palette[local_idx % len(palette)]
                rotation = self._rng.choice([0, 0, 0, 90])  # bias toward horizontal

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
                                font_family=self.font_family,
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
                                        font_family=self.font_family,
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
        line_spacing: float = 1.5,
        margin: float = 20.0,
        weight_range: tuple[int, int] = (200, 900),
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
                )
            )

            cursor_x += word_w + font_size * 0.4  # gap between words

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
            rotation = self._rng.choice([0, 0, 90])  # bias horizontal
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
                            font_family=self.font_family,
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
                                    font_family=self.font_family,
                                )
                            )
                            placed_bboxes.append(bbox)
                            found = True
                            break
                    if found:
                        break

        return placed

    def render_svg(self, placed_words: list[PlacedWord]) -> str:
        """Override to optionally include the shape outline."""
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
        ET.SubElement(
            root, "rect",
            width=str(self.width), height=str(self.height), fill="none",
        )

        # Shape outline polygon
        points_str = " ".join(f"{x:.1f},{y:.1f}" for x, y in self._polygon)
        ET.SubElement(
            root, "polygon",
            points=points_str,
            fill="none",
            stroke=self.outline_color,
        ).set("stroke-width", str(self.outline_width))

        # Text elements
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
            if pw.rotation != 0:
                attrs["transform"] = (
                    f"rotate({pw.rotation:.1f},{pw.x:.1f},{pw.y:.1f})"
                )
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
