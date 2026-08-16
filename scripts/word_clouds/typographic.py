"""Typographic word-cloud renderer: phyllotaxis core + packed remainder.

Fits **every** input term using multi-pass adaptive scaling. The
highest-frequency words form an elliptical sunflower (golden-angle
phyllotaxis) constellation; everything else packs into the leftover
banner space. Horizontal only. Never drops terms when ``require_all``
is True (default). Last-resort grid exists only for tiny canvases.
"""

from __future__ import annotations

import math
from collections.abc import Iterator
from typing import override

from ..utils import get_logger
from .colors import (
    CLUSTER_PALETTES,
    TYPOGRAPHIC_PALETTE,
    _classify_word,
    github_readable_fills,
    is_github_dual_surface_readable,
)
from .core import BBox, PlacedWord
from .engine import SvgWordCloudEngine

logger = get_logger(module=__name__)

# Golden angle 2π/φ² — sunflower phyllotaxis.
_GOLDEN_ANGLE = math.pi * (3.0 - math.sqrt(5.0))
_PUBLIC_WIDTH = 1600
_PUBLIC_HEIGHT = 520
_PUBLIC_MIN_FONT = 8.0
_PUBLIC_MAX_FONT = 56.0


class TypographicRenderer(SvgWordCloudEngine):
    """Phyllotaxis constellation plus a packed remainder on a wide canvas.

    Top-frequency terms sit on a golden-angle spiral (stretched to the
    banner aspect). The rest fill leftover intervals. Horizontal only.
    Never drops terms when ``require_all`` is True (default).
    """

    def __init__(
        self,
        *,
        palette: list[str] | None = None,
        line_spacing: float = 1.18,
        margin: float = 16.0,
        word_gap_ratio: float = 0.34,
        weight_range: tuple[int, int] = (300, 800),
        require_all: bool = True,
        scale_passes: int = 14,
        **kwargs,
    ) -> None:
        kwargs.setdefault("width", _PUBLIC_WIDTH)
        kwargs.setdefault("height", _PUBLIC_HEIGHT)
        kwargs.setdefault("min_font_size", _PUBLIC_MIN_FONT)
        kwargs.setdefault("max_font_size", _PUBLIC_MAX_FONT)
        super().__init__(**kwargs)
        if palette is not None:
            self.palette = list(palette)
        elif self.color_palette_override:
            self.palette = list(self.color_palette_override)
        else:
            self.palette = list(TYPOGRAPHIC_PALETTE)
        self.line_spacing = line_spacing
        self.margin = margin
        self.word_gap_ratio = word_gap_ratio
        self.weight_range = weight_range
        self.require_all = require_all
        self.scale_passes = scale_passes

    @override
    def _frequency_to_opacity(
        self,
        freq: float,
        min_freq: float,
        max_freq: float,
    ) -> float:
        """Keep fills fully opaque so volume stays in size/weight, not washout."""
        del freq, min_freq, max_freq
        return 1.0

    def _freq_to_weight(self, freq: float, min_freq: float, max_freq: float) -> int:
        """Map frequency to font-weight (100-900 in steps of 100)."""
        if max_freq == min_freq:
            return 500
        t = (freq - min_freq) / (max_freq - min_freq)
        # Log-ish boost so mid-tier terms stay substantial on large vocabularies.
        t = math.sqrt(max(0.0, min(1.0, t)))
        raw = self.weight_range[0] + t * (self.weight_range[1] - self.weight_range[0])
        return int(round(raw / 100)) * 100

    @override
    def _frequency_to_size(
        self,
        freq: float,
        min_freq: float,
        max_freq: float,
    ) -> float:
        """Map starred-repo count to font size (monotonic in *freq*)."""
        if max_freq == min_freq:
            return (self.min_font_size + self.max_font_size) / 2
        t = (freq - min_freq) / (max_freq - min_freq)
        # Exponent 0.42 compresses the top end so many mid words keep presence.
        t_scaled = t**0.42
        return self.min_font_size + t_scaled * (self.max_font_size - self.min_font_size)

    def _word_color(self, word: str, idx: int) -> str:
        if self.color_palette_override:
            candidate = self.palette[
                int((idx * 0.6180339887 * len(self.palette)) % len(self.palette))
            ]
        else:
            cluster = _classify_word(word)
            cluster_palette = CLUSTER_PALETTES.get(cluster)
            if cluster_palette:
                candidate = cluster_palette[idx % len(cluster_palette)]
            else:
                candidate = self.palette[
                    int((idx * 0.6180339887 * len(self.palette)) % len(self.palette))
                ]
        if self.color_palette_override:
            return candidate
        if is_github_dual_surface_readable(candidate):
            return candidate
        for fill in github_readable_fills():
            if is_github_dual_surface_readable(fill):
                return fill
        return "#2563EB"

    def _make_word(
        self,
        word: str,
        freq: float,
        idx: int,
        x: float,
        y: float,
        font_size: float,
        min_freq: float,
        max_freq: float,
        *,
        rotation: float = 0.0,
    ) -> PlacedWord:
        return PlacedWord(
            text=word,
            x=x,
            y=y,
            font_size=font_size,
            rotation=rotation,
            color=self._word_color(word, idx),
            font_weight=self._freq_to_weight(freq, min_freq, max_freq),
            font_family=self.font_family,
            opacity=self._frequency_to_opacity(freq, min_freq, max_freq),
        )

    def _constellation_count(self, n: int) -> int:
        """How many top-frequency terms sit on the sunflower spiral."""
        if n <= 1:
            return n
        return max(1, min(n, min(20, max(6, round(n * 0.18)))))

    def _phyllotaxis_positions(
        self,
        count: int,
        cx: float,
        cy: float,
        scale: float,
        *,
        aspect: float = 1.0,
    ) -> list[tuple[float, float]]:
        """Yield *count* golden-angle sunflower slots, optionally stretched."""
        points: list[tuple[float, float]] = []
        for index in range(max(0, count)):
            radius = scale * math.sqrt(index + 0.35)
            theta = index * _GOLDEN_ANGLE
            points.append(
                (cx + radius * math.cos(theta) * aspect, cy + radius * math.sin(theta))
            )
        return points

    def _archimedean_positions(
        self,
        cx: float,
        cy: float,
        step: float,
        max_steps: int = 2400,
        *,
        aspect: float = 1.0,
    ) -> Iterator[tuple[float, float]]:
        """Yield positions along an elliptical Archimedean spiral."""
        angular_step = 0.18
        for index in range(max_steps):
            theta = index * angular_step
            radius = step * theta
            yield cx + radius * math.cos(theta) * aspect, cy + radius * math.sin(theta)

    def _word_font_size(
        self,
        freq: float,
        min_freq: float,
        max_freq: float,
        scale: float,
    ) -> float:
        return max(
            self.min_font_size,
            self._frequency_to_size(freq, min_freq, max_freq) * scale,
        )

    def _free_x_intervals(
        self,
        y: float,
        height: float,
        boxes: list[BBox],
    ) -> list[tuple[float, float]]:
        """Open horizontal spans at *y* that do not hit *boxes*."""
        top = y - height / 2
        bottom = y + height / 2
        blockers: list[tuple[float, float]] = []
        for box in boxes:
            if box.y2 <= top or box.y >= bottom:
                continue
            blockers.append((box.x, box.x2))
        blockers.sort()
        merged: list[tuple[float, float]] = []
        for start, end in blockers:
            if merged and start <= merged[-1][1] + 1.0:
                merged[-1] = (merged[-1][0], max(merged[-1][1], end))
            else:
                merged.append((start, end))
        left = self.margin
        right = self.width - self.margin
        free: list[tuple[float, float]] = []
        cursor = left
        for start, end in merged:
            if start > cursor:
                free.append((cursor, min(start, right)))
            cursor = max(cursor, end)
        if cursor < right:
            free.append((cursor, right))
        return [(start, end) for start, end in free if end - start > 4.0]

    def _word_rotation(self, idx: int, font_size: float) -> float:
        """Tilt mid/small words; keep headline terms flat for reading."""
        if font_size >= self.max_font_size * 0.55:
            return 0.0
        angles = (-16.0, 12.0, -9.0, 15.0, 8.0, -13.0)
        return angles[idx % len(angles)]

    def _try_anchor(
        self,
        word: str,
        font_size: float,
        x: float,
        y: float,
        boxes: list[BBox],
        *,
        rotation: float = 0.0,
    ) -> BBox | None:
        bbox = self._estimate_bbox(word, font_size, x, y, rotation)
        if self._in_bounds(bbox) and not self._check_collision(bbox, boxes):
            return bbox
        return None

    def _place_constellation(
        self,
        constellation: list[tuple[str, float]],
        min_freq: float,
        max_freq: float,
        scale: float,
    ) -> tuple[list[PlacedWord], list[BBox]] | None:
        """Park the top-frequency terms on an elliptical sunflower spiral."""
        count = len(constellation)
        if count == 0:
            return [], []
        aspect = self.width / max(float(self.height), 1.0)
        usable_y = self.height / 2.0 - self.margin
        usable_x = self.width / 2.0 - self.margin
        outer = math.sqrt(count + 0.35)
        slot_scale = min(usable_x / (outer * aspect), usable_y / outer) * 0.86
        cx, cy = self.width / 2.0, self.height / 2.0
        slots = self._phyllotaxis_positions(
            count * 5 + 24,
            cx,
            cy,
            slot_scale,
            aspect=aspect,
        )
        placed: list[PlacedWord] = []
        boxes: list[BBox] = []
        used_slots: set[int] = set()
        for idx, (word, freq) in enumerate(constellation):
            font_size = self._word_font_size(freq, min_freq, max_freq, scale)
            rotation = self._word_rotation(idx, font_size)
            settled: tuple[float, float, BBox] | None = None
            preferred = list(range(idx, len(slots))) + list(range(idx))
            for slot_i in preferred:
                if slot_i in used_slots:
                    continue
                x, y = slots[slot_i]
                bbox = self._try_anchor(
                    word, font_size, x, y, boxes, rotation=rotation
                )
                if bbox is not None:
                    settled = (x, y, bbox)
                    used_slots.add(slot_i)
                    break
            if settled is None:
                walk_step = max(3.0, font_size * 0.22)
                for x, y in self._archimedean_positions(
                    cx, cy, walk_step, max_steps=900, aspect=aspect
                ):
                    bbox = self._try_anchor(
                        word, font_size, x, y, boxes, rotation=rotation
                    )
                    if bbox is not None:
                        settled = (x, y, bbox)
                        break
            if settled is None:
                return None
            x, y, bbox = settled
            boxes.append(bbox)
            placed.append(
                self._make_word(
                    word, freq, idx, x, y, font_size, min_freq, max_freq,
                    rotation=rotation,
                )
            )
        return placed, boxes

    def _place_remainder(
        self,
        remainder: list[tuple[str, float]],
        start_idx: int,
        min_freq: float,
        max_freq: float,
        scale: float,
        occupied: list[BBox],
        *,
        line_spacing: float,
        gap_ratio: float,
    ) -> list[PlacedWord] | None:
        """Dense first-fit packer that flows around the constellation."""
        if not remainder:
            return []
        items: list[tuple[int, str, float, float, float, float]] = []
        for offset, (word, freq) in enumerate(remainder):
            idx = start_idx + offset
            font_size = self._word_font_size(freq, min_freq, max_freq, scale)
            width = self._estimate_text_width(word, font_size)
            height = self._estimate_text_height(font_size) * line_spacing
            items.append((idx, word, freq, font_size, width, height))
        # Largest first: leftover holes take the small labels.
        items.sort(key=lambda item: item[3], reverse=True)

        placed: list[PlacedWord] = []
        boxes = list(occupied)
        aspect = self.width / max(float(self.height), 1.0)
        cx, cy = self.width / 2.0, self.height / 2.0
        max_y = self.height - self.margin

        for idx, word, freq, font_size, word_w, word_h in items:
            rotation = self._word_rotation(idx, font_size)
            gap = font_size * gap_ratio
            need = word_w + gap + self.padding
            settled: tuple[float, float, BBox] | None = None
            y = self.margin + word_h * 0.5
            y_step = max(2.0, word_h * 0.28)
            while y + word_h * 0.5 <= max_y + 1e-6:
                for left, right in self._free_x_intervals(y, word_h, boxes):
                    if right - left < need:
                        continue
                    x = left + word_w / 2.0 + 1.0
                    bbox = self._try_anchor(
                        word, font_size, x, y, boxes, rotation=rotation
                    )
                    if bbox is not None:
                        settled = (x, y, bbox)
                        break
                if settled is not None:
                    break
                y += y_step
            if settled is None:
                walk_step = max(2.5, font_size * 0.16)
                for x, y in self._archimedean_positions(
                    cx, cy, walk_step, max_steps=1600, aspect=aspect
                ):
                    bbox = self._try_anchor(
                        word, font_size, x, y, boxes, rotation=rotation
                    )
                    if bbox is not None:
                        settled = (x, y, bbox)
                        break
            if settled is None:
                return None
            x, y, bbox = settled
            boxes.append(bbox)
            placed.append(
                self._make_word(
                    word, freq, idx, x, y, font_size, min_freq, max_freq,
                    rotation=rotation,
                )
            )
        return placed

    def _place_at_scale(
        self,
        sorted_words: list[tuple[str, float]],
        min_freq: float,
        max_freq: float,
        scale: float,
        *,
        line_spacing: float | None = None,
        gap_ratio: float | None = None,
    ) -> list[PlacedWord] | None:
        """Phyllotaxis constellation for the head, packed remainder for the tail."""
        if not sorted_words:
            return []
        line_sp = self.line_spacing if line_spacing is None else line_spacing
        gap_r = self.word_gap_ratio if gap_ratio is None else gap_ratio
        split = self._constellation_count(len(sorted_words))
        head = sorted_words[:split]
        tail = sorted_words[split:]
        core = self._place_constellation(head, min_freq, max_freq, scale)
        if core is None:
            return None
        placed, boxes = core
        remainder = self._place_remainder(
            tail,
            split,
            min_freq,
            max_freq,
            scale,
            boxes,
            line_spacing=line_sp,
            gap_ratio=gap_r,
        )
        if remainder is None:
            return None
        packed = placed + remainder
        if len(packed) != len(sorted_words):
            return None
        return packed

    def _grid_force_all(
        self,
        sorted_words: list[tuple[str, float]],
        min_freq: float,
        max_freq: float,
    ) -> list[PlacedWord]:
        """Last-resort dense grid so every term is present (may shrink heavily)."""
        n = len(sorted_words)
        if n == 0:
            return []
        # Estimate columns from average short label width.
        font = max(4.0, min(self.min_font_size, 7.0))
        avg_chars = sum(len(w) for w, _ in sorted_words) / n
        cell_w = max(font * avg_chars * 0.52 + 4.0, 28.0)
        cell_h = font * 1.35
        cols = max(1, int((self.width - 2 * self.margin) // cell_w))
        rows_needed = math.ceil(n / cols)
        # Shrink until rows fit
        usable_h = self.height - 2 * self.margin
        if rows_needed * cell_h > usable_h:
            shrink = usable_h / (rows_needed * cell_h)
            font = max(3.5, font * shrink)
            cell_w = max(font * avg_chars * 0.52 + 3.0, 20.0)
            cell_h = font * 1.3
            cols = max(1, int((self.width - 2 * self.margin) // cell_w))

        placed: list[PlacedWord] = []
        for idx, (word, freq) in enumerate(sorted_words):
            col = idx % cols
            row = idx // cols
            fs = max(
                3.5,
                self._frequency_to_size(freq, min_freq, max_freq)
                * (font / self.max_font_size),
            )
            fs = min(fs, font * 1.6)
            x = self.margin + col * cell_w + cell_w / 2
            y = self.margin + row * cell_h + cell_h * 0.65
            # Keep inside canvas
            x = min(max(x, self.margin), self.width - self.margin)
            y = min(max(y, self.margin), self.height - self.margin)
            placed.append(
                PlacedWord(
                    text=word,
                    x=x,
                    y=y,
                    font_size=fs,
                    rotation=0,
                    color=self.palette[idx % len(self.palette)],
                    font_weight=self._freq_to_weight(freq, min_freq, max_freq),
                    font_family=self.font_family,
                    opacity=self._frequency_to_opacity(freq, min_freq, max_freq),
                )
            )
        return placed

    @override
    def place_words(
        self,
        frequencies: dict[str, float],
    ) -> list[PlacedWord]:
        if not frequencies:
            return []

        sorted_words = sorted(frequencies.items(), key=lambda kv: kv[1], reverse=True)
        min_freq = min(frequencies.values())
        max_freq = max(frequencies.values())
        n = len(sorted_words)

        # Soften only the *max* so a public min of 8 stays readable.
        original_max = self.max_font_size
        original_min = self.min_font_size
        if n > 80:
            self.max_font_size = min(original_max, max(28.0, 72.0 - n * 0.08))
        if n > 200:
            self.max_font_size = min(self.max_font_size, 34.0)

        try:
            # Binary search largest scale that still packs every word.
            lo, hi = 0.08, 1.15
            best: list[PlacedWord] | None = None
            for _ in range(self.scale_passes):
                mid = (lo + hi) / 2
                attempt = self._place_at_scale(sorted_words, min_freq, max_freq, mid)
                if attempt is not None:
                    best = attempt
                    lo = mid
                else:
                    hi = mid

            # Secondary densify: tighter gaps / line spacing at best scale.
            if best is not None:
                denser = self._place_at_scale(
                    sorted_words,
                    min_freq,
                    max_freq,
                    lo,
                    line_spacing=max(1.05, self.line_spacing * 0.92),
                    gap_ratio=max(0.20, self.word_gap_ratio * 0.85),
                )
                if denser is not None:
                    best = denser
                logger.info(
                    "TypographicRenderer: packed {}/{} words at scale={:.3f} "
                    "(phyllotaxis constellation + packed remainder)",
                    len(best),
                    n,
                    lo,
                )
                return best

            if not self.require_all:
                # Partial pack at small scale for legacy behavior.
                partial = self._place_at_scale(sorted_words, min_freq, max_freq, 0.25)
                return partial or []

            logger.warning(
                "TypographicRenderer: scale search incomplete for {} terms; "
                "using dense grid fallback.",
                n,
            )
            return self._grid_force_all(sorted_words, min_freq, max_freq)
        finally:
            self.max_font_size = original_max
            self.min_font_size = original_min
