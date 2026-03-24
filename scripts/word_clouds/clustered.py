"""Clustered word cloud renderer with semantic domain grouping."""

from __future__ import annotations

import math

from ..utils import get_logger
from .colors import CLUSTER_PALETTES, _classify_word
from .core import BBox, PlacedWord
from .engine import SvgWordCloudEngine

logger = get_logger(module=__name__)


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
        self,
        cluster_names: list[str],
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
                rotation = self.layout_readability.choose_rotation(
                    self._rng,
                    is_large_word=self._is_large_word(font_size),
                )

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
        self,
        cx: float,
        cy: float,
        step: float,
        max_steps: int = 1500,
    ):
        """Yield positions along an Archimedean spiral."""
        b = step
        for i in range(max_steps):
            theta = i * 0.1
            r = b * theta
            yield cx + r * math.cos(theta), cy + r * math.sin(theta)
