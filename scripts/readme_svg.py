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
    kicker: str | None = None
    lines: tuple[str, ...] = ()
    meta: tuple[str, ...] = ()
    url: str | None = None
    background_image: str | None = None
    sparkline: tuple[float, ...] | None = None
    icon: str | None = None
    icon_data_uri: str | None = None
    badge: str | None = None
    accent: str | None = None


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
            ".card-kicker { fill: #8FA1B8; font: 700 11px ui-sans-serif; letter-spacing: 0.08em; text-transform: uppercase; }",
            ".card-title { fill: #FFFFFF; font: 700 21px ui-sans-serif; }",
            ".card-line { fill: #E3ECF7; font: 500 15px ui-sans-serif; }",
            ".card-meta { fill: #B7C3D4; font: 500 13px ui-sans-serif; }",
            ".card-icon { fill: #F8FAFC; font: 700 13px ui-sans-serif; }",
            ".card-badge { fill: #FFFFFF; font: 700 12px ui-sans-serif; letter-spacing: 0.01em; }",
            ".sparkline { fill: none; stroke: #7DD3FC; stroke-width: 2; opacity: 0.88; }",
            "</style>",
            (
                "<linearGradient id=\"cardGradient\" x1=\"0%\" y1=\"0%\" "
                "x2=\"0%\" y2=\"100%\">"
                "<stop offset=\"0%\" stop-color=\"#0B111A\" stop-opacity=\"0.26\"/>"
                "<stop offset=\"56%\" stop-color=\"#0B111A\" stop-opacity=\"0.72\"/>"
                "<stop offset=\"100%\" stop-color=\"#0B111A\" stop-opacity=\"0.97\"/>"
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
        accent = self._normalize_hex_color(card.accent)
        lines = [f'<g class="card" transform="translate({x},{y})">']
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
                    "\" rx=\"16\" fill=\"#121A25\" stroke=\""
                    f"{accent}"
                    "\" stroke-opacity=\"0.45\" />"
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
                f'clip-path="url(#{clip_id})" opacity="0.16" />'
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
                '<rect x="12" y="12" width="'
                f'{width - 24}'
                '" height="88" rx="12" fill="#0B111A" fill-opacity="0.64" />'
            )

        title_x = 18
        title_y = 44
        monogram = self._truncate((card.icon or "").upper(), 3)
        icon_data_uri = self._sanitize_icon_data_uri(card.icon_data_uri)
        if icon_data_uri or monogram:
            lines.append(
                '<circle cx="36" cy="36" r="18" fill="'
                f"{accent}"
                '" fill-opacity="0.30" stroke="#FFFFFF" stroke-opacity="0.18" '
                'stroke-width="1" />'
            )
            lines.append(
                '<circle cx="36" cy="36" r="13.5" fill="#0B111A" '
                'fill-opacity="0.64" />'
            )
            if icon_data_uri:
                icon_clip_id = f"icon-clip-{card_index}"
                lines.append(
                    "<defs>"
                    f'<clipPath id="{icon_clip_id}">'
                    '<circle cx="36" cy="36" r="13.5" />'
                    "</clipPath>"
                    "</defs>"
                )
                lines.append(
                    '<image class="card-icon-image" href="'
                    f"{self._esc(icon_data_uri)}"
                    '" x="22.5" y="22.5" width="27" height="27" '
                    'preserveAspectRatio="xMidYMid meet" '
                    f'clip-path="url(#{icon_clip_id})" />'
                )
                lines.append(
                    '<circle cx="36" cy="36" r="13.5" fill="none" '
                    'stroke="#FFFFFF" stroke-opacity="0.16" stroke-width="1" />'
                )
            elif monogram:
                lines.append(
                    '<text class="card-icon" x="36" y="41" text-anchor="middle">'
                    f"{self._esc(monogram)}"
                    "</text>"
                )
            title_x = 62

        if card.kicker:
            lines.append(
                (
                    '<text class="card-kicker" x="'
                    f"{title_x}"
                    '" y="22">'
                    f"{self._esc(self._truncate(card.kicker, 56))}"
                    "</text>"
                )
            )
            title_y = 48

        if card.badge:
            badge_text = self._truncate(card.badge, 20)
            badge_width = max(90, min(220, len(badge_text) * 8 + 26))
            badge_x = max(16, width - badge_width - 16)
            badge_on_image = card.background_image is not None
            badge_fill = "#0B111A" if badge_on_image else accent
            badge_fill_opacity = "0.68" if badge_on_image else "0.36"
            badge_stroke = accent if badge_on_image else "#FFFFFF"
            badge_stroke_opacity = "0.86" if badge_on_image else "0.18"
            lines.append(
                (
                    '<rect x="'
                    f"{badge_x}"
                    '" y="16" width="'
                    f"{badge_width}"
                    '" height="24" rx="12" fill="'
                    f"{badge_fill}"
                    f'" fill-opacity="{badge_fill_opacity}" stroke="{badge_stroke}" '
                    f'stroke-opacity="{badge_stroke_opacity}" stroke-width="1" />'
                )
            )
            lines.append(
                (
                    '<text class="card-badge" x="'
                    f"{badge_x + (badge_width / 2):.1f}"
                    '" y="32" text-anchor="middle">'
                    f"{self._esc(badge_text)}"
                    "</text>"
                )
            )

        lines.append(
            (
                '<text class="card-title" x="'
                f"{title_x}"
                '" y="'
                f"{title_y}"
                '">'
                f"{self._esc(self._truncate(card.title, 52))}"
                "</text>"
            )
        )

        text_y = title_y + 26
        for line in card.lines[:3]:
            lines.append(
                (
                    '<text class="card-line" x="'
                    f"{title_x}"
                    '" y="'
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
                    '<text class="card-meta" x="'
                    f"{title_x}"
                    '" y="'
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

    def _normalize_hex_color(self, value: str | None) -> str:
        if not value:
            return "#60A5FA"
        cleaned = value.strip()
        if re.fullmatch(r"#?[0-9A-Fa-f]{6}", cleaned):
            return f"#{cleaned.lstrip('#')}"
        return "#60A5FA"

    def _sanitize_icon_data_uri(self, value: str | None) -> str | None:
        if not value:
            return None
        cleaned = value.strip()
        if len(cleaned) > 32768:
            return None
        if re.fullmatch(
            r"data:image/[A-Za-z0-9.+-]+;base64,[A-Za-z0-9+/=]+",
            cleaned,
        ):
            return cleaned
        return None


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
