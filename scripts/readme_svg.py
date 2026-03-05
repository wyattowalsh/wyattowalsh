"""Reusable SVG rendering and writing helpers for README dynamic sections."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
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
    family: SvgCardFamily | str | None = None


class SvgCardFamily(str, Enum):
    """Supported card families with dedicated render policies."""

    DEFAULT = "default"
    CONNECT = "connect"
    FEATURED = "featured"
    BLOG = "blog"


@dataclass(frozen=True)
class SvgTextPolicy:
    """Text rendering policy knobs for card families."""

    title_limit: int | None
    line_limit: int | None
    max_lines: int = 3
    wrap_title_with_tspan: bool = False
    title_wrap_chars: int = 52
    title_max_lines: int = 1
    wrap_lines_with_tspan: bool = False
    line_wrap_chars: int = 72
    strip_update_suffix: bool = False


@dataclass(frozen=True)
class SvgFamilyRenderPolicy:
    """Family-specific rendering policy for cards."""

    text: SvgTextPolicy
    show_badge: bool = True
    hide_handle_lines: bool = False
    include_featured_details: bool = False
    meta_item_limit: int = 28


_FAMILY_RENDER_POLICIES: dict[SvgCardFamily, SvgFamilyRenderPolicy] = {
    SvgCardFamily.DEFAULT: SvgFamilyRenderPolicy(
        text=SvgTextPolicy(title_limit=52, line_limit=72),
    ),
    SvgCardFamily.CONNECT: SvgFamilyRenderPolicy(
        text=SvgTextPolicy(title_limit=52, line_limit=72),
        show_badge=False,
        hide_handle_lines=True,
    ),
    SvgCardFamily.FEATURED: SvgFamilyRenderPolicy(
        text=SvgTextPolicy(title_limit=52, line_limit=72),
        include_featured_details=True,
        meta_item_limit=38,
    ),
    SvgCardFamily.BLOG: SvgFamilyRenderPolicy(
        text=SvgTextPolicy(
            title_limit=None,
            line_limit=None,
            wrap_title_with_tspan=True,
            title_wrap_chars=48,
            title_max_lines=2,
            wrap_lines_with_tspan=True,
            line_wrap_chars=72,
            max_lines=5,
            strip_update_suffix=True,
        ),
        show_badge=False,
    ),
}

_FAMILY_ALIASES: dict[str, SvgCardFamily] = {
    "default": SvgCardFamily.DEFAULT,
    "general": SvgCardFamily.DEFAULT,
    "connect": SvgCardFamily.CONNECT,
    "contact": SvgCardFamily.CONNECT,
    "featured": SvgCardFamily.FEATURED,
    "project": SvgCardFamily.FEATURED,
    "projects": SvgCardFamily.FEATURED,
    "blog": SvgCardFamily.BLOG,
    "posts": SvgCardFamily.BLOG,
}

_FAMILY_TITLE_HINTS: tuple[tuple[SvgCardFamily, tuple[str, ...]], ...] = (
    (SvgCardFamily.CONNECT, ("connect", "contact", "social")),
    (SvgCardFamily.FEATURED, ("featured", "project", "showcase")),
    (SvgCardFamily.BLOG, ("blog", "post", "dispatch")),
)


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
            header_height + self.padding + (rows * (self.card_height + self.padding))
        )

        family = self._resolve_family(block, cards)
        family_policy = _FAMILY_RENDER_POLICIES[family]

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
            (
                ".card-badge { fill: #FFFFFF; font: 700 12px ui-sans-serif; letter-spacing: 0.01em; }"
                if any(c.badge for c in cards) and family_policy.show_badge
                else ""
            ),
            ".sparkline { fill: none; stroke: #7DD3FC; stroke-width: 2; opacity: 0.88; }",
            "</style>",
            (
                '<linearGradient id="cardGradient" x1="0%" y1="0%" '
                'x2="0%" y2="100%">'
                '<stop offset="0%" stop-color="#0B111A" stop-opacity="0.26"/>'
                '<stop offset="56%" stop-color="#0B111A" stop-opacity="0.72"/>'
                '<stop offset="100%" stop-color="#0B111A" stop-opacity="0.97"/>'
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
            svg_lines.extend(
                self._render_card(
                    card=card,
                    x=x,
                    y=y,
                    width=card_width,
                    card_index=idx,
                    family_policy=family_policy,
                )
            )

        svg_lines.append("</svg>")
        return "\n".join(svg_lines)

    def _render_card(
        self,
        card: SvgCard,
        x: int,
        y: int,
        width: int,
        card_index: int,
        family_policy: SvgFamilyRenderPolicy,
    ) -> list[str]:
        accent = self._normalize_hex_color(card.accent)
        lines = [f'<g class="card" transform="translate({x},{y})">']
        if card.url:
            lines.append(
                '<a href="'
                f"{self._esc(card.url)}"
                '" target="_blank" rel="noopener noreferrer">'
            )

        lines.extend(
            [
                (
                    '<rect width="'
                    f"{width}"
                    '" height="'
                    f"{self.card_height}"
                    '" rx="16" fill="#121A25" stroke="'
                    f"{accent}"
                    '" stroke-opacity="0.45" />'
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
                    '<rect width="'
                    f"{width}"
                    '" height="'
                    f"{self.card_height}"
                    '" rx="16" fill="url(#cardGradient)" />'
                )
            )
            lines.append(
                '<rect x="12" y="12" width="'
                f"{width - 24}"
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

        if card.badge and family_policy.show_badge:
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

        title = self._format_title(card.title, family_policy.text)
        if family_policy.text.wrap_title_with_tspan:
            wrapped_title = self._wrap_text(
                title,
                max_chars=family_policy.text.title_wrap_chars,
                max_lines=family_policy.text.title_max_lines,
            )
            title_tspans = "".join(
                (
                    f'<tspan x="{title_x}">{self._esc(segment)}</tspan>'
                    if idx == 0
                    else f'<tspan x="{title_x}" dy="20">{self._esc(segment)}</tspan>'
                )
                for idx, segment in enumerate(wrapped_title)
            )
            lines.append(
                (
                    '<text class="card-title" x="'
                    f"{title_x}"
                    '" y="'
                    f"{title_y}"
                    '">'
                    f"{title_tspans}"
                    "</text>"
                )
            )
            title_visual_lines = max(1, len(wrapped_title))
        else:
            lines.append(
                (
                    '<text class="card-title" x="'
                    f"{title_x}"
                    '" y="'
                    f"{title_y}"
                    '">'
                    f"{self._esc(title)}"
                    "</text>"
                )
            )
            title_visual_lines = 1

        text_y = title_y + 26 + max(0, title_visual_lines - 1) * 20
        visible_lines = self._visible_lines(card, family_policy)
        remaining_line_slots = max(0, family_policy.text.max_lines)
        for line in visible_lines:
            if remaining_line_slots <= 0:
                break
            line_copy = self._apply_limit(line, family_policy.text.line_limit)
            if family_policy.text.wrap_lines_with_tspan:
                wrapped_lines = self._wrap_text(
                    line_copy,
                    max_chars=family_policy.text.line_wrap_chars,
                    max_lines=remaining_line_slots,
                )
                tspans = "".join(
                    (
                        f'<tspan x="{title_x}">{self._esc(segment)}</tspan>'
                        if idx == 0
                        else f'<tspan x="{title_x}" dy="18">{self._esc(segment)}</tspan>'
                    )
                    for idx, segment in enumerate(wrapped_lines)
                )
                lines.append(
                    (
                        '<text class="card-line" x="'
                        f"{title_x}"
                        '" y="'
                        f"{text_y}"
                        '">'
                        f"{tspans}"
                        "</text>"
                    )
                )
                text_y += 22 + max(0, len(wrapped_lines) - 1) * 18
                remaining_line_slots -= len(wrapped_lines)
            else:
                lines.append(
                    (
                        '<text class="card-line" x="'
                        f"{title_x}"
                        '" y="'
                        f"{text_y}"
                        '">'
                        f"{self._esc(line_copy)}"
                        "</text>"
                    )
                )
                text_y += 22
                remaining_line_slots -= 1

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
            meta = " · ".join(
                self._truncate(item, family_policy.meta_item_limit) for item in card.meta[:3]
            )
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

    def _resolve_family(
        self,
        block: SvgBlock,
        cards: tuple[SvgCard, ...],
    ) -> SvgCardFamily:
        explicit = self._parse_family(block.family)
        if explicit is not None:
            return explicit
        inferred = self._infer_family_from_cards(cards)
        if inferred is not None:
            return inferred
        return self._infer_family_from_title(block.title)

    def _parse_family(self, family: SvgCardFamily | str | None) -> SvgCardFamily | None:
        if family is None:
            return None
        if isinstance(family, SvgCardFamily):
            return family
        normalized = family.strip().lower().replace("_", "-")
        return _FAMILY_ALIASES.get(normalized)

    def _infer_family_from_cards(
        self,
        cards: tuple[SvgCard, ...],
    ) -> SvgCardFamily | None:
        if any("/blog/" in (card.url or "").lower() for card in cards):
            return SvgCardFamily.BLOG
        if any(
            bool(getattr(card, "homepage", None)) or bool(getattr(card, "topics", ()))
            for card in cards
        ):
            return SvgCardFamily.FEATURED
        if any(
            any(line.strip().startswith("@") for line in (card.lines or ()))
            for card in cards
        ):
            return SvgCardFamily.CONNECT
        return None

    def _infer_family_from_title(self, title: str) -> SvgCardFamily:
        title_copy = (title or "").lower()
        for family, hints in _FAMILY_TITLE_HINTS:
            if any(hint in title_copy for hint in hints):
                return family
        return SvgCardFamily.DEFAULT

    def _visible_lines(
        self,
        card: SvgCard,
        family_policy: SvgFamilyRenderPolicy,
    ) -> list[str]:
        visible_lines = list(card.lines or ())
        if family_policy.hide_handle_lines:
            visible_lines = [
                line
                for line in visible_lines
                if not line.strip().startswith("@")
                and "://" not in line
                and "open-profile" not in line.lower()
            ]
        if family_policy.include_featured_details:
            homepage = getattr(card, "homepage", None)
            if homepage:
                visible_lines.append(str(homepage))
            topics = getattr(card, "topics", ())
            for topic in topics:
                visible_lines.append(str(topic))
        return visible_lines

    def _format_title(self, title: str, text_policy: SvgTextPolicy) -> str:
        title_copy = title
        if text_policy.strip_update_suffix:
            title_copy = re.sub(r"\.{2,}|[…]", "", title_copy)
            title_copy = re.sub(
                r"\bupdate\b",
                "",
                title_copy,
                flags=re.IGNORECASE,
            ).strip()
        return self._apply_limit(title_copy, text_policy.title_limit)

    def _apply_limit(self, value: str, limit: int | None) -> str:
        if limit is None:
            return value
        return self._truncate(value, limit)

    def _wrap_text(
        self,
        value: str,
        max_chars: int,
        max_lines: int | None = None,
    ) -> tuple[str, ...]:
        words = value.split()
        if not words:
            return ("",)
        normalized_words: list[str] = []
        for word in words:
            if len(word) <= max_chars:
                normalized_words.append(word)
                continue
            normalized_words.extend(
                word[idx : idx + max_chars] for idx in range(0, len(word), max_chars)
            )
        wrapped: list[str] = []
        current = normalized_words[0]
        for word in normalized_words[1:]:
            candidate = f"{current} {word}"
            if len(candidate) <= max_chars:
                current = candidate
            else:
                wrapped.append(current)
                if max_lines is not None and len(wrapped) >= max_lines:
                    return tuple(wrapped[:max_lines])
                current = word
        wrapped.append(current)
        if len(wrapped) > 1 and len(wrapped[-1]) <= 3:
            prev = wrapped[-2]
            if len(prev) + len(wrapped[-1]) + 1 <= max_chars:
                wrapped[-2] = f"{prev} {wrapped[-1]}"
                wrapped.pop()
        if max_lines is None:
            return tuple(wrapped)
        return tuple(wrapped[:max_lines])

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
