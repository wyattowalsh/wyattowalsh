"""Reusable SVG rendering and writing helpers for README dynamic sections."""

from __future__ import annotations

import re
from dataclasses import dataclass
from html import escape
from pathlib import Path

from .utils import get_logger

logger = get_logger(module=__name__)


@dataclass(frozen=True)
class SvgCard:
    """Content for a single card in a generated SVG block."""

    title: str
    lines: tuple[str, ...] = ()
    meta: tuple[str, ...] = ()
    url: str | None = None
    background_image: str | None = None
    sparkline: tuple[float, ...] | None = None


@dataclass(frozen=True)
class SvgBlock:
    """A group of cards rendered as a single SVG section asset."""

    title: str
    cards: tuple[SvgCard, ...]
    columns: int = 1


class SvgBlockRenderer:
    """Render a block of cards into a standalone SVG document."""

    def __init__(
        self,
        width: int = 1200,
        card_height: int = 176,
        padding: int = 24,
    ) -> None:
        self.width = width
        self.card_height = card_height
        self.padding = padding

    def render(self, block: SvgBlock) -> str:
        cards = block.cards or (SvgCard(title="No items available."),)
        columns = max(1, block.columns)
        rows = (len(cards) + columns - 1) // columns
        card_width = int((self.width - (self.padding * (columns + 1))) / columns)
        header_height = 88
        height = (
            header_height
            + self.padding
            + (rows * (self.card_height + self.padding))
        )

        svg_lines = [
            (
                f'<svg xmlns="http://www.w3.org/2000/svg" '
                f'width="{self.width}" height="{height}" '
                f'viewBox="0 0 {self.width} {height}" role="img">'
            ),
            "<defs>",
            "<style>",
            ".title { fill: #F5F5F5; font: 700 32px ui-sans-serif; }",
            ".card-title { fill: #FFFFFF; font: 700 22px ui-sans-serif; }",
            ".card-line { fill: #D8DEE9; font: 400 16px ui-sans-serif; }",
            ".card-meta { fill: #AAB5C4; font: 400 14px ui-sans-serif; }",
            ".sparkline { fill: none; stroke: #7DD3FC; stroke-width: 2; opacity: 0.85; }",
            "</style>",
            (
                "<linearGradient id=\"cardGradient\" x1=\"0%\" y1=\"0%\" "
                "x2=\"0%\" y2=\"100%\">"
                "<stop offset=\"0%\" stop-color=\"#0B111A\" stop-opacity=\"0.05\"/>"
                "<stop offset=\"100%\" stop-color=\"#0B111A\" stop-opacity=\"0.95\"/>"
                "</linearGradient>"
            ),
            "</defs>",
            '<rect width="100%" height="100%" rx="24" fill="#0B111A" />',
            (
                f'<text class="title" x="{self.padding}" y="54">'
                f"{self._esc(block.title)}</text>"
            ),
        ]

        for idx, card in enumerate(cards):
            column = idx % columns
            row = idx // columns
            x = self.padding + (column * (card_width + self.padding))
            y = header_height + (row * (self.card_height + self.padding))
            svg_lines.extend(self._render_card(card, x, y, card_width, idx))

        svg_lines.append("</svg>")
        return "\n".join(svg_lines)

    def _render_card(
        self,
        card: SvgCard,
        x: int,
        y: int,
        width: int,
        card_index: int,
    ) -> list[str]:
        lines = [f'<g transform="translate({x},{y})">']
        if card.url:
            lines.append(
                "<a href=\""
                f"{self._esc(card.url)}"
                "\" target=\"_blank\" rel=\"noopener noreferrer\">"
            )

        lines.extend(
            [
                (
                    "<rect width=\""
                    f"{width}"
                    "\" height=\""
                    f"{self.card_height}"
                    "\" rx=\"16\" fill=\"#121A25\" stroke=\"#1F2C3D\" />"
                )
            ]
        )

        if card.background_image:
            clip_id = f"clip-{card_index}"
            lines.append(
                "<defs>"
                f'<clipPath id="{clip_id}"><rect width="{width}" '
                f'height="{self.card_height}" rx="16" /></clipPath>'
                "</defs>"
            )
            lines.append(
                '<image href="'
                f"{self._esc(card.background_image)}"
                f'" width="{width}" height="{self.card_height}" '
                'preserveAspectRatio="xMidYMid slice" '
                f'clip-path="url(#{clip_id})" opacity="0.5" />'
            )
            lines.append(
                (
                    "<rect width=\""
                    f"{width}"
                    "\" height=\""
                    f"{self.card_height}"
                    "\" rx=\"16\" fill=\"url(#cardGradient)\" />"
                )
            )

        lines.append(
            (
                '<text class="card-title" x="18" y="36">'
                f"{self._esc(self._truncate(card.title, 52))}"
                "</text>"
            )
        )

        text_y = 62
        for line in card.lines[:4]:
            lines.append(
                (
                    '<text class="card-line" x="18" y="'
                    f"{text_y}"
                    '">'
                    f"{self._esc(self._truncate(line, 72))}"
                    "</text>"
                )
            )
            text_y += 22

        if card.sparkline and len(card.sparkline) >= 2:
            sparkline_path = self._sparkline_path(
                card.sparkline,
                width=width - 48,
                height=36,
            )
            lines.append(
                '<path class="sparkline" d="'
                f"{sparkline_path}"
                '" transform="translate(18,'
                f"{self.card_height - 64}"
                ')" />'
            )

        if card.meta:
            meta = " · ".join(self._truncate(item, 28) for item in card.meta[:3])
            lines.append(
                (
                    '<text class="card-meta" x="18" y="'
                    f"{self.card_height - 18}"
                    '">'
                    f"{self._esc(meta)}"
                    "</text>"
                )
            )

        if card.url:
            lines.append("</a>")
        lines.append("</g>")
        return lines

    def _truncate(self, value: str, limit: int) -> str:
        return value if len(value) <= limit else f"{value[: limit - 1]}…"

    def _esc(self, value: str) -> str:
        return escape(value, quote=True)

    def _sparkline_path(
        self,
        points: tuple[float, ...],
        width: int,
        height: int,
    ) -> str:
        total = len(points) - 1
        if total <= 0:
            return ""
        min_val = min(points)
        max_val = max(points)
        span = max(max_val - min_val, 1e-6)
        coords: list[tuple[float, float]] = []
        for idx, value in enumerate(points):
            norm_x = idx / total
            norm_y = (value - min_val) / span
            x_pos = norm_x * width
            y_pos = height - (norm_y * height)
            coords.append((x_pos, y_pos))
        path_segments = [f"M{coords[0][0]:.2f},{coords[0][1]:.2f}"]
        for x_pos, y_pos in coords[1:]:
            path_segments.append(f"L{x_pos:.2f},{y_pos:.2f}")
        return " ".join(path_segments)


class SvgAssetWriter:
    """Write rendered SVG assets to disk with safe filenames."""

    def __init__(self, output_dir: Path | str) -> None:
        self.output_dir = Path(output_dir)

    def write(self, asset_name: str, svg_content: str) -> Path:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        filename = self._sanitize_filename(asset_name)
        output_path = self.output_dir / f"{filename}.svg"
        output_path.write_text(svg_content, encoding="utf-8")
        logger.debug("Wrote README SVG asset to {path}", path=output_path)
        return output_path

    def _sanitize_filename(self, asset_name: str) -> str:
        sanitized = re.sub(r"[^a-zA-Z0-9_-]+", "-", asset_name).strip("-_")
        return sanitized or "section"


class ReadmeSvgAssetBuilder:
    """Facade to render and persist SVG section assets."""

    def __init__(
        self,
        output_dir: Path | str,
        renderer: SvgBlockRenderer | None = None,
    ) -> None:
        self.renderer = renderer or SvgBlockRenderer()
        self.writer = SvgAssetWriter(output_dir=output_dir)

    def render_and_write(self, asset_name: str, block: SvgBlock) -> Path:
        svg_content = self.renderer.render(block)
        return self.writer.write(asset_name=asset_name, svg_content=svg_content)

    def write_raw(self, asset_name: str, svg_content: str) -> Path:
        return self.writer.write(asset_name=asset_name, svg_content=svg_content)
