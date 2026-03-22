"""Shape-constrained word cloud renderer."""

from __future__ import annotations

import math
import xml.etree.ElementTree as ET

from ..utils import get_logger
from .core import BBox, PlacedWord
from .engine import SvgWordCloudEngine

logger = get_logger(module=__name__)

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
        (
            0.5 + 0.5 * math.cos(2 * math.pi * i / 36),
            0.5 + 0.5 * math.sin(2 * math.pi * i / 36),
        )
        for i in range(36)
    ],
    "rounded-rect": [
        *[
            (
                0.15 - 0.15 * math.cos(math.pi / 2 * i / 4),
                0.15 - 0.15 * math.sin(math.pi / 2 * i / 4),
            )
            for i in range(5)
        ],
        *[
            (
                0.85 + 0.15 * math.sin(math.pi / 2 * i / 4),
                0.15 - 0.15 * math.cos(math.pi / 2 * i / 4),
            )
            for i in range(5)
        ],
        *[
            (
                0.85 + 0.15 * math.cos(math.pi / 2 * i / 4),
                0.85 + 0.15 * math.sin(math.pi / 2 * i / 4),
            )
            for i in range(5)
        ],
        *[
            (
                0.15 - 0.15 * math.sin(math.pi / 2 * i / 4),
                0.85 + 0.15 * math.cos(math.pi / 2 * i / 4),
            )
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


def _point_in_polygon(px: float, py: float, polygon: list[tuple[float, float]]) -> bool:
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
                if self._all_corners_in_shape(bbox) and not self._check_collision(
                    bbox, placed_bboxes
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
                        if self._all_corners_in_shape(
                            bbox
                        ) and not self._check_collision(bbox, placed_bboxes):
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

        root = ET.Element(
            "svg",
            xmlns="http://www.w3.org/2000/svg",
            width=str(self.width),
            height=str(self.height),
            viewBox=f"0 0 {self.width} {self.height}",
        )

        defs = self._add_glow_filter(root)
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
        ET.SubElement(
            root,
            "rect",
            width=str(self.width),
            height=str(self.height),
            fill="url(#wc-bg-grad)",
        )

        glow_threshold = self._glow_size_threshold(placed_words)

        tier1_threshold = float("inf")
        tier2_threshold = float("inf")
        if placed_words:
            sizes = sorted((pw.font_size for pw in placed_words), reverse=True)
            t1_idx = max(1, int(len(sizes) * 0.10))
            tier1_threshold = sizes[min(t1_idx, len(sizes) - 1)]
            t2_idx = max(1, int(len(sizes) * 0.30))
            tier2_threshold = sizes[min(t2_idx, len(sizes) - 1)]

        points_str = " ".join(f"{x:.1f},{y:.1f}" for x, y in self._polygon)
        ET.SubElement(
            root,
            "polygon",
            points=points_str,
            fill="none",
            stroke=self.outline_color,
        ).set("stroke-width", str(self.outline_width))

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
                attrs["transform"] = f"rotate({pw.rotation:.1f},{pw.x:.1f},{pw.y:.1f})"
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
        self,
        cx: float,
        cy: float,
        step: float,
        max_steps: int = 2000,
    ):
        b = step
        for i in range(max_steps):
            theta = i * 0.1
            r = b * theta
            yield cx + r * math.cos(theta), cy + r * math.sin(theta)
