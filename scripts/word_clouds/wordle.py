"""Wordle spiral-placement word cloud renderer."""

from __future__ import annotations

import math
import random

from ..utils import get_logger
from .colors import COLOR_FUNCS
from .core import BBox, PlacedWord
from .engine import SvgWordCloudEngine

logger = get_logger(module=__name__)


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
                if self._in_bounds(bbox) and not self._check_collision(
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
                # Try with progressively reduced font size as fallback
                for scale in (0.7, 0.5, 0.35, 0.25, 0.15):
                    reduced = font_size * scale
                    if reduced < _ABSOLUTE_MIN_FONT:
                        break
                    for x, y in self._spiral_positions(
                        cx, cy, max(0.8, reduced * 0.08)
                    ):
                        bbox = self._estimate_bbox(word, reduced, x, y, 0)
                        if self._in_bounds(bbox) and not self._check_collision(
                            bbox, placed_bboxes
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

            # Grid-scan final fallback -- guarantees placement
            if not found:
                grid_size = _ABSOLUTE_MIN_FONT
                for gy in range(0, int(self.height), int(grid_size * 2)):
                    if found:
                        break
                    for gx in range(0, int(self.width), int(grid_size * 2)):
                        bbox = self._estimate_bbox(word, grid_size, gx, gy, 0)
                        if self._in_bounds(bbox) and not self._check_collision(
                            bbox, placed_bboxes
                        ):
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
                    len(placed),
                    total,
                    fill_ratio * 100,
                )

        return placed
