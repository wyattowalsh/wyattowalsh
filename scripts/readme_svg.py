"""Reusable SVG rendering and writing helpers for README dynamic sections."""

from __future__ import annotations

import re
from dataclasses import dataclass, field, replace
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
    show_title: bool = True
    transparent_canvas: bool = False
    variant: str | None = None


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
    max_lines: int | None = 3
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
    show_kicker: bool = True
    show_icon: bool = True
    show_icon_on_background: bool = True
    hide_handle_lines: bool = False
    include_featured_details: bool = False
    render_featured_chip_row: bool = False
    render_featured_meta_rows: bool = False
    featured_meta_row_limit: int = 2
    show_meta_footer: bool = True
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
        show_badge=False,
        include_featured_details=True,
        render_featured_chip_row=True,
        render_featured_meta_rows=True,
        show_meta_footer=False,
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
            max_lines=None,
            strip_update_suffix=True,
        ),
        show_badge=False,
        show_kicker=False,
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


@dataclass(frozen=True)
class SvgThemePalette:
    """Color tokens used across README SVG card families."""

    canvas_fill: str = "#0B111A"
    gradient_fill: str = "#0B111A"
    card_fill: str = "#0F172A"
    overlay_fill: str = "#0B111A"
    title_text: str = "#F5F5F5"
    kicker_text: str = "#8FA1B8"
    card_title_text: str = "#FFFFFF"
    card_line_text: str = "#E3ECF7"
    card_meta_text: str = "#B7C3D4"
    card_icon_text: str = "#F8FAFC"
    card_badge_text: str = "#FFFFFF"
    card_chip_text: str = "#DBEAFE"
    sparkline_stroke: str = "#7DD3FC"
    icon_inner_fill: str = "#0B111A"
    icon_ring_stroke: str = "#FFFFFF"
    badge_default_stroke: str = "#FFFFFF"
    chip_fill: str = "#0B1220"
    chip_stroke: str = "#60A5FA"


@dataclass(frozen=True)
class SvgThemeSpacing:
    """Layout spacing tokens for README SVG cards."""

    overlay_inset: int = 12
    overlay_height: int = 88
    title_x: int = 18
    title_y: int = 44
    title_with_icon_x: int = 62
    kicker_y: int = 22
    text_start_gap: int = 26
    text_line_gap: int = 22
    wrapped_line_gap: int = 18
    badge_inset: int = 16
    badge_height: int = 24
    badge_min_width: int = 90
    badge_max_width: int = 220
    badge_char_width: int = 8
    badge_horizontal_padding: int = 26
    chip_bottom_inset: int = 68
    chip_gap: int = 8
    chip_height: int = 22
    chip_padding: int = 20
    chip_char_width: int = 7
    meta_row_start_inset: int = 34
    meta_row_gap: int = 15


@dataclass(frozen=True)
class SvgThemeRadii:
    """Corner radius tokens for README SVG card primitives."""

    canvas: int = 24
    card: int = 16
    overlay: int = 12
    badge: int = 12
    icon_outer: float = 18.0
    icon_inner: float = 13.5


@dataclass(frozen=True)
class SvgThemeTypography:
    """Typography tokens for README SVG card text classes."""

    section_title_font: str = "700 32px ui-sans-serif"
    kicker_font: str = "700 11px ui-sans-serif"
    card_title_font: str = "700 21px ui-sans-serif"
    card_line_font: str = "500 15px ui-sans-serif"
    card_meta_font: str = "500 13px ui-sans-serif"
    card_icon_font: str = "700 13px ui-sans-serif"
    card_badge_font: str = "700 12px ui-sans-serif"
    card_chip_font: str = "700 11px ui-sans-serif"


@dataclass(frozen=True)
class SvgThemeEffects:
    """Visual effects tokens for README SVG cards."""

    canvas_fill_opacity: str = "0.38"
    card_fill_opacity: str = "0.78"
    card_stroke_opacity: str = "0.58"
    gradient_top_opacity: str = "0.26"
    gradient_mid_opacity: str = "0.72"
    gradient_bottom_opacity: str = "0.97"
    image_opacity: str = "0.20"
    overlay_fill_opacity: str = "0.54"
    icon_outer_fill_opacity: str = "0.30"
    icon_outer_stroke_opacity: str = "0.18"
    icon_inner_fill_opacity: str = "0.64"
    icon_ring_stroke_opacity: str = "0.16"
    sparkline_stroke_width: int = 2
    sparkline_opacity: str = "0.88"
    badge_fill_opacity_on_image: str = "0.68"
    badge_fill_opacity_default: str = "0.36"
    badge_stroke_opacity_on_image: str = "0.86"
    badge_stroke_opacity_default: str = "0.18"
    chip_fill_opacity: str = "0.30"
    chip_stroke_opacity: str = "0.46"
    connect_accent_glow: str = "rgba(125, 211, 252, 0.26)"


@dataclass(frozen=True)
class SvgFamilyThemeTokens:
    """Token bundle grouped by styling primitive categories."""

    palette: SvgThemePalette = field(default_factory=SvgThemePalette)
    spacing: SvgThemeSpacing = field(default_factory=SvgThemeSpacing)
    radii: SvgThemeRadii = field(default_factory=SvgThemeRadii)
    typography: SvgThemeTypography = field(default_factory=SvgThemeTypography)
    effects: SvgThemeEffects = field(default_factory=SvgThemeEffects)


_BASE_FAMILY_THEME = SvgFamilyThemeTokens()
_FAMILY_THEME_TOKENS: dict[SvgCardFamily, SvgFamilyThemeTokens] = {
    SvgCardFamily.DEFAULT: _BASE_FAMILY_THEME,
    SvgCardFamily.CONNECT: replace(
        _BASE_FAMILY_THEME,
        effects=replace(
            _BASE_FAMILY_THEME.effects,
            connect_accent_glow="rgba(125, 211, 252, 0.30)",
        ),
    ),
    SvgCardFamily.FEATURED: replace(
        _BASE_FAMILY_THEME,
        effects=replace(
            _BASE_FAMILY_THEME.effects,
            card_fill_opacity="0.33",
            card_stroke_opacity="0.46",
            image_opacity="0.40",
            overlay_fill_opacity="0.44",
            chip_fill_opacity="0.42",
            chip_stroke_opacity="0.62",
        ),
    ),
    SvgCardFamily.BLOG: replace(
        _BASE_FAMILY_THEME,
        effects=replace(
            _BASE_FAMILY_THEME.effects,
            card_fill_opacity="0.22",
            card_stroke_opacity="0.40",
        ),
    ),
}


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
        show_title = bool(block.show_title and block.title.strip())
        header_height = 88 if show_title else 0
        top_offset = header_height + self.padding
        height = top_offset + (rows * (self.card_height + self.padding))

        family = self._resolve_family(block, cards)
        family_policy = _FAMILY_RENDER_POLICIES[family]
        theme = _FAMILY_THEME_TOKENS[family]

        svg_lines = [
            (
                f'<svg xmlns="http://www.w3.org/2000/svg" '
                f'width="{self.width}" height="{height}" '
                f'viewBox="0 0 {self.width} {height}" role="img">'
            ),
            "<defs>",
            "<style>",
            (
                ".title { fill: "
                f"{theme.palette.title_text}; font: {theme.typography.section_title_font}; }}"
            ),
            (
                ".card-kicker { fill: "
                f"{theme.palette.kicker_text}; font: {theme.typography.kicker_font}; "
                "letter-spacing: 0.08em; text-transform: uppercase; }"
            ),
            (
                ".card-title { fill: "
                f"{theme.palette.card_title_text}; font: {theme.typography.card_title_font}; }}"
            ),
            (
                ".card-line { fill: "
                f"{theme.palette.card_line_text}; font: {theme.typography.card_line_font}; }}"
            ),
            (
                ".card-meta { fill: "
                f"{theme.palette.card_meta_text}; font: {theme.typography.card_meta_font}; }}"
            ),
            (
                ".card-icon { fill: "
                f"{theme.palette.card_icon_text}; font: {theme.typography.card_icon_font}; }}"
            ),
            (
                ".card-badge { fill: "
                f"{theme.palette.card_badge_text}; font: {theme.typography.card_badge_font}; "
                "letter-spacing: 0.01em; }"
                if any(c.badge for c in cards) and family_policy.show_badge
                else ""
            ),
            (
                ".card-chip { fill: "
                f"{theme.palette.chip_fill}; fill-opacity: {theme.effects.chip_fill_opacity}; "
                f"stroke: {theme.palette.chip_stroke}; "
                f"stroke-opacity: {theme.effects.chip_stroke_opacity}; }}"
            ),
            (
                ".card-chip-text { fill: "
                f"{theme.palette.card_chip_text}; font: {theme.typography.card_chip_font}; }}"
            ),
            (
                ".card-meta-row { fill: "
                f"{theme.palette.card_meta_text}; font: {theme.typography.card_meta_font}; }}"
            ),
            (
                ".sparkline { fill: none; stroke: "
                f"{theme.palette.sparkline_stroke}; "
                f"stroke-width: {theme.effects.sparkline_stroke_width}; "
                f"opacity: {theme.effects.sparkline_opacity}; }}"
            ),
            (
                '.card[data-card-family="connect"][data-connect-variant="gh-card"] '
                "{ --connect-accent-glow: "
                f"{theme.effects.connect_accent_glow}; }}"
            ),
            (
                ".connect-card-shell { filter: drop-shadow(0 0 8px "
                "var(--connect-accent-glow)); }"
            ),
            ".connect-brand-lockup { isolation: isolate; }",
            "</style>",
            (
                '<linearGradient id="cardGradient" x1="0%" y1="0%" '
                'x2="0%" y2="100%">'
                f'<stop offset="0%" stop-color="{theme.palette.gradient_fill}" '
                f'stop-opacity="{theme.effects.gradient_top_opacity}"/>'
                f'<stop offset="56%" stop-color="{theme.palette.gradient_fill}" '
                f'stop-opacity="{theme.effects.gradient_mid_opacity}"/>'
                f'<stop offset="100%" stop-color="{theme.palette.gradient_fill}" '
                f'stop-opacity="{theme.effects.gradient_bottom_opacity}"/>'
                "</linearGradient>"
            ),
            "</defs>",
        ]
        if not block.transparent_canvas:
            svg_lines.append(
                (
                    '<rect width="100%" height="100%" rx="'
                    f"{theme.radii.canvas}"
                    '" fill="'
                    f"{theme.palette.canvas_fill}"
                    '" fill-opacity="'
                    f"{theme.effects.canvas_fill_opacity}"
                    '" />'
                )
            )
        if show_title:
            svg_lines.append(
                f'<text class="title" x="{self.padding}" y="54">{self._esc(block.title)}</text>'
            )

        for idx, card in enumerate(cards):
            column = idx % columns
            row = idx // columns
            x = self.padding + (column * (card_width + self.padding))
            y = top_offset + (row * (self.card_height + self.padding))
            svg_lines.extend(
                self._render_card(
                    card=card,
                    x=x,
                    y=y,
                    width=card_width,
                    card_index=idx,
                    family=family,
                    family_policy=family_policy,
                    theme=theme,
                    card_variant=block.variant,
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
        family: SvgCardFamily,
        family_policy: SvgFamilyRenderPolicy,
        theme: SvgFamilyThemeTokens,
        card_variant: str | None = None,
    ) -> list[str]:
        accent = self._normalize_hex_color(card.accent)
        variant_attr = ""
        if card_variant:
            variant_attr = f' data-card-variant="{self._esc(card_variant)}"'
        connect_variant_attr = ""
        if family is SvgCardFamily.CONNECT and card_variant:
            connect_variant_attr = (
                f' data-connect-variant="{self._esc(card_variant)}"'
            )
        lines = [
            (
                '<g class="card" data-card-family="'
                f"{family.value}"
                f'"{variant_attr}{connect_variant_attr} transform="translate({x},{y})">'
            )
        ]
        if card.url:
            lines.append(
                '<a href="'
                f"{self._esc(card.url)}"
                '" target="_blank" rel="noopener noreferrer">'
            )

        shell_classes = "card-shell"
        if family is SvgCardFamily.CONNECT:
            shell_classes = "connect-card-shell"
        shell_class_attr = (
            f' class="{shell_classes}"' if family is SvgCardFamily.CONNECT else ""
        )
        lines.extend(
            [
                (
                    "<rect"
                    f"{shell_class_attr}"
                    ' width="'
                    f"{width}"
                    '" height="'
                    f"{self.card_height}"
                    '" rx="'
                    f"{theme.radii.card}"
                    '" fill="'
                    f"{theme.palette.card_fill}"
                    '" fill-opacity="'
                    f"{theme.effects.card_fill_opacity}"
                    '" stroke="'
                    f"{accent}"
                    '" stroke-opacity="'
                    f"{theme.effects.card_stroke_opacity}"
                    '" />'
                )
            ]
        )

        if card.background_image:
            clip_id = f"clip-{card_index}"
            lines.append(
                "<defs>"
                f'<clipPath id="{clip_id}"><rect width="{width}" '
                f'height="{self.card_height}" rx="{theme.radii.card}" /></clipPath>'
                "</defs>"
            )
            lines.append(
                '<image class="card-hero-image" href="'
                f"{self._esc(card.background_image)}"
                f'" width="{width}" height="{self.card_height}" '
                'preserveAspectRatio="xMidYMid slice" '
                f'clip-path="url(#{clip_id})" opacity="{theme.effects.image_opacity}" />'
            )
            lines.append(
                (
                    '<rect width="'
                    f"{width}"
                    '" height="'
                    f"{self.card_height}"
                    '" rx="'
                    f"{theme.radii.card}"
                    '" fill="url(#cardGradient)" />'
                )
            )
            lines.append(
                '<rect x="'
                f"{theme.spacing.overlay_inset}"
                '" y="'
                f"{theme.spacing.overlay_inset}"
                '" width="'
                f"{width - (theme.spacing.overlay_inset * 2)}"
                '" height="'
                f"{theme.spacing.overlay_height}"
                '" rx="'
                f"{theme.radii.overlay}"
                '" fill="'
                f"{theme.palette.overlay_fill}"
                '" fill-opacity="'
                f"{theme.effects.overlay_fill_opacity}"
                '" />'
            )

        title_x = theme.spacing.title_x
        title_y = theme.spacing.title_y
        monogram = self._truncate((card.icon or "").upper(), 3)
        icon_data_uri = self._sanitize_icon_data_uri(card.icon_data_uri)
        blog_hero_suppresses_icon = (
            family is SvgCardFamily.BLOG
            and card.background_image is not None
            and getattr(card, "hero_image", None) is None
        )
        show_icon_lockup = family_policy.show_icon and (
            family_policy.show_icon_on_background or card.background_image is None
        )
        show_icon_lockup = show_icon_lockup and not blog_hero_suppresses_icon
        if show_icon_lockup and (icon_data_uri or monogram):
            lockup_class = (
                "connect-brand-lockup"
                if family is SvgCardFamily.CONNECT
                else "card-brand-lockup"
            )
            lines.append(f'<g class="{lockup_class}">')
            lines.append(
                '<circle cx="36" cy="36" r="'
                f"{theme.radii.icon_outer}"
                '" fill="'
                f"{accent}"
                '" fill-opacity="'
                f"{theme.effects.icon_outer_fill_opacity}"
                '" stroke="'
                f"{theme.palette.icon_ring_stroke}"
                '" stroke-opacity="'
                f"{theme.effects.icon_outer_stroke_opacity}"
                '" '
                'stroke-width="1" />'
            )
            lines.append(
                '<circle cx="36" cy="36" r="'
                f"{theme.radii.icon_inner}"
                '" fill="'
                f"{theme.palette.icon_inner_fill}"
                '" fill-opacity="'
                f"{theme.effects.icon_inner_fill_opacity}"
                '" />'
            )
            if icon_data_uri:
                icon_clip_id = f"icon-clip-{card_index}"
                icon_size = theme.radii.icon_inner * 2
                icon_pos = 36 - theme.radii.icon_inner
                lines.append(
                    "<defs>"
                    f'<clipPath id="{icon_clip_id}">'
                    '<circle cx="36" cy="36" r="'
                    f"{theme.radii.icon_inner}"
                    '" />'
                    "</clipPath>"
                    "</defs>"
                )
                lines.append(
                    '<image class="card-icon-image" href="'
                    f"{self._esc(icon_data_uri)}"
                    '" x="'
                    f"{icon_pos:.1f}"
                    '" y="'
                    f"{icon_pos:.1f}"
                    '" width="'
                    f"{icon_size:g}"
                    '" height="'
                    f"{icon_size:g}"
                    '" '
                    'preserveAspectRatio="xMidYMid meet" '
                    f'clip-path="url(#{icon_clip_id})" />'
                )
                lines.append(
                    '<circle cx="36" cy="36" r="'
                    f"{theme.radii.icon_inner}"
                    '" fill="none" '
                    'stroke="'
                    f"{theme.palette.icon_ring_stroke}"
                    '" stroke-opacity="'
                    f"{theme.effects.icon_ring_stroke_opacity}"
                    '" stroke-width="1" />'
                )
            elif monogram:
                lines.append(
                    '<text class="card-icon" x="36" y="41" text-anchor="middle">'
                    f"{self._esc(monogram)}"
                    "</text>"
                )
            lines.append("</g>")
            title_x = theme.spacing.title_with_icon_x

        if card.kicker and family_policy.show_kicker:
            lines.append(
                (
                    '<text class="card-kicker" x="'
                    f"{title_x}"
                    '" y="'
                    f"{theme.spacing.kicker_y}"
                    '">'
                    f"{self._esc(self._truncate(card.kicker, 56))}"
                    "</text>"
                )
            )
            title_y = 48

        if card.badge and family_policy.show_badge:
            badge_text = self._truncate(card.badge, 20)
            badge_width = max(
                theme.spacing.badge_min_width,
                min(
                    theme.spacing.badge_max_width,
                    len(badge_text) * theme.spacing.badge_char_width
                    + theme.spacing.badge_horizontal_padding,
                ),
            )
            badge_x = max(
                theme.spacing.badge_inset,
                width - badge_width - theme.spacing.badge_inset,
            )
            badge_on_image = card.background_image is not None
            badge_fill = theme.palette.overlay_fill if badge_on_image else accent
            badge_fill_opacity = (
                theme.effects.badge_fill_opacity_on_image
                if badge_on_image
                else theme.effects.badge_fill_opacity_default
            )
            badge_stroke = accent if badge_on_image else theme.palette.badge_default_stroke
            badge_stroke_opacity = (
                theme.effects.badge_stroke_opacity_on_image
                if badge_on_image
                else theme.effects.badge_stroke_opacity_default
            )
            lines.append(
                (
                    '<rect x="'
                    f"{badge_x}"
                    '" y="'
                    f"{theme.spacing.badge_inset}"
                    '" width="'
                    f"{badge_width}"
                    '" height="'
                    f"{theme.spacing.badge_height}"
                    '" rx="'
                    f"{theme.radii.badge}"
                    '" fill="'
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

        text_y = title_y + theme.spacing.text_start_gap + max(0, title_visual_lines - 1) * 20
        visible_lines = self._visible_lines(card, family_policy)
        remaining_line_slots = family_policy.text.max_lines
        for line in visible_lines:
            if remaining_line_slots is not None and remaining_line_slots <= 0:
                break
            line_copy = self._apply_limit(
                line,
                family_policy.text.line_limit,
                add_ellipsis=not family_policy.text.wrap_lines_with_tspan,
            )
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
                        else (
                            f'<tspan x="{title_x}" dy="{theme.spacing.wrapped_line_gap}">'
                            f"{self._esc(segment)}</tspan>"
                        )
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
                text_y += theme.spacing.text_line_gap + max(
                    0,
                    len(wrapped_lines) - 1,
                ) * theme.spacing.wrapped_line_gap
                if remaining_line_slots is not None:
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
                text_y += theme.spacing.text_line_gap
                if remaining_line_slots is not None:
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
                '" transform="translate('
                f"{theme.spacing.title_x},"
                f"{self.card_height - 64}"
                ')" />'
            )

        if family_policy.render_featured_chip_row:
            chip_labels = self._featured_chip_labels(card)
            chip_x = title_x
            chip_y = max(
                theme.spacing.kicker_y + 2,
                self.card_height - theme.spacing.chip_bottom_inset,
            )
            for chip_label in chip_labels:
                chip_width = max(
                    64,
                    len(chip_label) * theme.spacing.chip_char_width
                    + theme.spacing.chip_padding,
                )
                if chip_x + chip_width > width - theme.spacing.badge_inset:
                    break
                lines.append(
                    (
                        '<rect class="card-chip" x="'
                        f"{chip_x}"
                        '" y="'
                        f"{chip_y - theme.spacing.chip_height + 1}"
                        '" width="'
                        f"{chip_width}"
                        '" height="'
                        f"{theme.spacing.chip_height}"
                        '" rx="'
                        f"{theme.radii.badge}"
                        '" />'
                    )
                )
                lines.append(
                    (
                        '<text class="card-chip-text" x="'
                        f"{chip_x + (chip_width / 2):.1f}"
                        '" y="'
                        f"{chip_y - 5}"
                        '" text-anchor="middle">'
                        f"{self._esc(chip_label)}"
                        "</text>"
                    )
                )
                chip_x += chip_width + theme.spacing.chip_gap

        if family_policy.render_featured_meta_rows:
            row_y = self.card_height - theme.spacing.meta_row_start_inset
            for row in self._featured_metadata_rows(card, family_policy):
                lines.append(
                    (
                        '<text class="card-meta-row" x="'
                        f"{title_x}"
                        '" y="'
                        f"{row_y}"
                        '">'
                        f"{self._esc(row)}"
                        "</text>"
                    )
                )
                row_y += theme.spacing.meta_row_gap

        elif card.meta and family_policy.show_meta_footer:
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

    def _featured_chip_labels(self, card: SvgCard) -> tuple[str, ...]:
        raw_chips = getattr(card, "metadata_chips", ())
        labels: list[str] = []
        for chip in raw_chips:
            if isinstance(chip, dict):
                chip_label = str(chip.get("label", "")).strip()
                chip_value = str(chip.get("value", "")).strip()
            else:
                chip_label = str(getattr(chip, "label", "")).strip()
                chip_value = str(getattr(chip, "value", "")).strip()
            if not chip_label:
                continue
            display = chip_label if not chip_value else f"{chip_label}: {chip_value}"
            wrapped = self._wrap_text(display, max_chars=28, max_lines=2)
            labels.append(" / ".join(segment for segment in wrapped if segment))
            if len(labels) >= 4:
                break
        return tuple(labels)

    def _featured_metadata_rows(
        self,
        card: SvgCard,
        family_policy: SvgFamilyRenderPolicy,
    ) -> tuple[str, ...]:
        metadata_rows = getattr(card, "metadata_rows", ())
        if not metadata_rows:
            metadata_rows = getattr(card, "metadata_lanes", ())
        if not metadata_rows:
            metadata_rows = card.meta
        rows: list[str] = []
        for row in metadata_rows[: family_policy.featured_meta_row_limit]:
            row_copy = str(row).strip()
            if not row_copy:
                continue
            remaining_rows = family_policy.featured_meta_row_limit - len(rows)
            if remaining_rows <= 0:
                break
            rows.extend(
                self._wrap_text(
                    row_copy,
                    max_chars=family_policy.meta_item_limit * 2,
                    max_lines=remaining_rows,
                )
            )
            if len(rows) >= family_policy.featured_meta_row_limit:
                break
        return tuple(rows)

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
        return self._apply_limit(
            title_copy,
            text_policy.title_limit,
            add_ellipsis=not text_policy.wrap_title_with_tspan,
        )

    def _apply_limit(
        self,
        value: str,
        limit: int | None,
        *,
        add_ellipsis: bool = True,
    ) -> str:
        if limit is None:
            return value
        if add_ellipsis:
            return self._truncate(value, limit)
        return value[:limit]

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
