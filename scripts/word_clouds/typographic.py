"""Typographic baseline-grid word cloud renderer.

Fits **every** input term using multi-pass adaptive scaling:
binary-search a global size scale until the full vocabulary packs onto the
canvas, with a densified grid fallback as last resort.
"""

from __future__ import annotations

import math

from ..utils import get_logger
from .colors import TYPOGRAPHIC_PALETTE
from .core import PlacedWord
from .engine import SvgWordCloudEngine

logger = get_logger(module=__name__)


class TypographicRenderer(SvgWordCloudEngine):
    """Editorial baseline-grid typography with complete vocabulary packing.

    Words flow left-to-right on a baseline grid with variable font weights.
    Horizontal only (no rotation) for maximum readability. Never drops terms
    when ``require_all`` is True (default).
    """

    def __init__(
        self,
        *,
        palette: list[str] | None = None,
        line_spacing: float = 1.22,
        margin: float = 20.0,
        word_gap_ratio: float = 0.42,
        weight_range: tuple[int, int] = (300, 800),
        require_all: bool = True,
        scale_passes: int = 14,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.palette = palette or list(TYPOGRAPHIC_PALETTE)
        self.line_spacing = line_spacing
        self.margin = margin
        self.word_gap_ratio = word_gap_ratio
        self.weight_range = weight_range
        self.require_all = require_all
        self.scale_passes = scale_passes

    def _freq_to_weight(self, freq: float, min_freq: float, max_freq: float) -> int:
        """Map frequency to font-weight (100-900 in steps of 100)."""
        if max_freq == min_freq:
            return 500
        t = (freq - min_freq) / (max_freq - min_freq)
        # Log-ish boost so mid-tier terms stay substantial on large vocabularies.
        t = math.sqrt(max(0.0, min(1.0, t)))
        raw = self.weight_range[0] + t * (self.weight_range[1] - self.weight_range[0])
        return int(round(raw / 100)) * 100

    def _frequency_to_size(
        self,
        freq: float,
        min_freq: float,
        max_freq: float,
    ) -> float:
        """Power-law size with softer floor so long tails stay legible."""
        if max_freq == min_freq:
            return (self.min_font_size + self.max_font_size) / 2
        t = (freq - min_freq) / (max_freq - min_freq)
        # Exponent 0.42 compresses the top end so many mid words keep presence.
        t_scaled = t**0.42
        return self.min_font_size + t_scaled * (self.max_font_size - self.min_font_size)

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
        """Single-pass pack at *scale*. Return list if all fit, else None."""
        line_sp = self.line_spacing if line_spacing is None else line_spacing
        gap_r = self.word_gap_ratio if gap_ratio is None else gap_ratio
        placed: list[PlacedWord] = []
        cursor_x = self.margin
        cursor_y = self.margin + self.max_font_size * scale * 0.55
        line_max_h = 0.0
        total = len(sorted_words)

        for idx, (word, freq) in enumerate(sorted_words):
            font_size = self._frequency_to_size(freq, min_freq, max_freq) * scale
            font_size = max(self.min_font_size * 0.85, font_size)
            weight = self._freq_to_weight(freq, min_freq, max_freq)
            opacity = self._frequency_to_opacity(freq, min_freq, max_freq)
            # Golden-angle palette walk for vivid but non-clashing progression.
            color = self.palette[
                int((idx * 0.6180339887 * len(self.palette)) % len(self.palette))
            ]
            word_w = self._estimate_text_width(word, font_size)
            word_h = self._estimate_text_height(font_size) * line_sp
            gap = font_size * gap_r

            if cursor_x + word_w + self.margin > self.width:
                cursor_x = self.margin
                cursor_y += line_max_h
                line_max_h = 0.0

            if cursor_y + word_h / 2 > self.height - self.margin:
                return None

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
            cursor_x += word_w + gap

        if len(placed) != total:
            return None
        return placed

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

        # Auto-soften max font when vocabulary is large so more terms share space.
        original_max = self.max_font_size
        original_min = self.min_font_size
        if n > 80:
            self.max_font_size = min(original_max, max(28.0, 96.0 - n * 0.08))
            self.min_font_size = min(original_min, max(5.0, 9.0 - n * 0.005))
        if n > 200:
            self.max_font_size = min(self.max_font_size, 36.0)
            self.min_font_size = min(self.min_font_size, 5.5)

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
                    gap_ratio=max(0.22, self.word_gap_ratio * 0.85),
                )
                if denser is not None:
                    best = denser
                logger.info(
                    "TypographicRenderer: packed {}/{} words at scale={:.3f}",
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
