"""Typographic baseline-grid word cloud renderer."""

from __future__ import annotations

from .colors import TYPOGRAPHIC_PALETTE
from .core import PlacedWord
from .engine import SvgWordCloudEngine


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
