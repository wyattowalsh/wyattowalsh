"""Abstract base engine for SVG word cloud renderers."""

from __future__ import annotations

import math
import random
import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod

from .colors import COLOR_FUNCS, primary_color_func
from .core import BBox, FONT_STACK, PlacedWord
from .readability import coerce_layout_readability_policy
from ..utils import get_logger

logger = get_logger(module=__name__)


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
        layout_readability: object | None = None,
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
        self.layout_readability = coerce_layout_readability_policy(layout_readability)
        self._rng = random.Random(seed)

    def _is_large_word(self, font_size: float) -> bool:
        return self.layout_readability.is_large_word(
            font_size, self.min_font_size, self.max_font_size
        )

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
        t_scaled = t**0.5
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
        raw = 400 + (t**0.6) * 400  # 400 -> 800
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
        return 0.65 + 0.35 * (t**0.4)

    # -- BBox estimation ----------------------------------------------------

    @staticmethod
    def _estimate_text_width(
        text: str, font_size: float, proportional: bool = True
    ) -> float:
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
            defs,
            "filter",
            id="wc-glow",
            x="-30%",
            y="-30%",
            width="160%",
            height="160%",
        )
        # Layer 1: soft outer glow
        ET.SubElement(
            filt,
            "feGaussianBlur",
            attrib={"in": "SourceGraphic", "stdDeviation": "2.5", "result": "glow1"},
        )
        # Layer 2: tighter inner glow for crispness
        ET.SubElement(
            filt,
            "feGaussianBlur",
            attrib={"in": "SourceGraphic", "stdDeviation": "0.8", "result": "glow2"},
        )
        merge = ET.SubElement(filt, "feMerge")
        ET.SubElement(merge, "feMergeNode", attrib={"in": "glow1"})
        ET.SubElement(merge, "feMergeNode", attrib={"in": "glow2"})
        ET.SubElement(merge, "feMergeNode", attrib={"in": "SourceGraphic"})

        # Subtle drop shadow for mid-tier words
        shadow_filt = ET.SubElement(
            defs,
            "filter",
            id="wc-shadow",
            x="-10%",
            y="-10%",
            width="120%",
            height="120%",
        )
        ET.SubElement(
            shadow_filt,
            "feDropShadow",
            attrib={
                "dx": "0",
                "dy": "1",
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
            defs,
            "radialGradient",
            id="wc-bg-grad",
            cx="50%",
            cy="50%",
            r="75%",
        )
        ET.SubElement(
            radial,
            "stop",
            offset="0%",
            attrib={
                "stop-color": "#fafbfc",
                "stop-opacity": "1",
            },
        )
        ET.SubElement(
            radial,
            "stop",
            offset="100%",
            attrib={
                "stop-color": "#f0f1f3",
                "stop-opacity": "1",
            },
        )

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
                attrs["transform"] = f"rotate({pw.rotation:.1f},{pw.x:.1f},{pw.y:.1f})"

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
