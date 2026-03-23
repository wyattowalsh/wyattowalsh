"""Reusable SVG rendering and writing helpers for README dynamic sections."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from html import escape
from pathlib import Path

from .utils import get_logger

logger = get_logger(module=__name__)

# ---------------------------------------------------------------------------
# SVG icon paths (GitHub Octicons)
# ---------------------------------------------------------------------------

STAR_ICON_PATH = (
    "M8 .25a.75.75 0 0 1 .673.418l1.882 3.815 4.21.612a.75.75 0 0 1"
    " .416 1.279l-3.046 2.97.719 4.192a.75.75 0 0 1-1.088.791L8"
    " 12.347l-3.766 1.98a.75.75 0 0 1-1.088-.79l.72-4.194L.818"
    " 6.374a.75.75 0 0 1 .416-1.28l4.21-.611L7.327.668A.75.75 0 0 1 8 .25Z"
)

ISSUE_ICON_PATH = (
    "M8 9.5a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3ZM8 0a8 8 0 1 1 0 16"
    "A8 8 0 0 1 8 0ZM1.5 8a6.5 6.5 0 1 0 13 0 6.5 6.5 0 0 0-13 0Z"
)

LAW_ICON_PATH = (
    "M8.75.75V2h.985c.304 0 .603.08.867.231l1.29.736c.038.022.08.033"
    ".124.033h2.234a.75.75 0 0 1 0 1.5h-.427l2.111 4.692a.75.75 0 0 1"
    "-.154.838l-.53-.53.529.531-.001.002-.002.002-.006.006-.006.005-.01"
    ".01-.045.04c-.21.176-.441.327-.686.45C14.556 10.78 13.88 11 13 11"
    "a4.498 4.498 0 0 1-2.023-.454 3.544 3.544 0 0 1-.686-.45l-.045"
    "-.04-.016-.015-.006-.006-.004-.004v-.001a.75.75 0 0 1-.154-.838"
    "L12.178 4.5h-.162c-.305 0-.604-.079-.868-.231l-1.29-.736a.245.245"
    " 0 0 0-.124-.033H8.75V13h2.5a.75.75 0 0 1 0 1.5h-6.5a.75.75 0 0"
    " 1 0-1.5h2.5V3.5h-.984a.245.245 0 0 0-.124.033l-1.289.737c-.265"
    ".15-.564.23-.869.23h-.162l2.112 4.692a.75.75 0 0 1-.154.838l-.53"
    "-.53.529.531-.001.002-.002.002-.006.006-.016.015-.045.04c-.21.176"
    "-.441.327-.686.45C4.556 10.78 3.88 11 3 11a4.498 4.498 0 0 1"
    "-2.023-.454 3.544 3.544 0 0 1-.686-.45l-.045-.04-.016-.015-.006"
    "-.006-.004-.004v-.001a.75.75 0 0 1-.154-.838L2.178 4.5H1.75a.75"
    ".75 0 0 1 0-1.5h2.234a.249.249 0 0 0 .125-.033l1.288-.737c.265"
    "-.15.564-.23.869-.23h.984V.75a.75.75 0 0 1 1.5 0Zm2.945 8.477"
    "c.285.135.718.273 1.305.273s1.02-.138 1.305-.273L13 6.327Zm-10"
    " 0c.285.135.718.273 1.305.273s1.02-.138 1.305-.273L3 6.327Z"
)

FORK_ICON_PATH = (
    "M5 5.372v.878c0 .414.336.75.75.75h4.5a.75.75 0 0 0 .75-.75v-.878"
    "a2.25 2.25 0 1 1 1.5 0v.878a2.25 2.25 0 0 1-2.25 2.25h-1.5v2.128"
    "a2.251 2.251 0 1 1-1.5 0V8.5h-1.5A2.25 2.25 0 0 1 3.5 6.25v-.878"
    "a2.25 2.25 0 1 1 1.5 0ZM5 3.25a.75.75 0 1 0-1.5 0 .75.75 0 0 0"
    " 1.5 0Zm6.75.75a.75.75 0 1 0 0-1.5.75.75 0 0 0 0 1.5Zm-3 8.75"
    "a.75.75 0 1 0-1.5 0 .75.75 0 0 0 1.5 0Z"
)

# ---------------------------------------------------------------------------
# Theme support
# ---------------------------------------------------------------------------

# NOTE: SVG <text> ignores CSS line-height; vertical spacing uses y/dy attributes.
FONT_FAMILY = (
    "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans',"
    " Helvetica, Arial, sans-serif"
)


@dataclass(frozen=True)
class SvgCardTheme:
    """Color theme for SVG cards."""

    bg: str
    border: str
    title_color: str
    text_color: str
    meta_color: str
    accent: str
    link_color: str


LIGHT_THEME = SvgCardTheme(
    bg="transparent",
    border="#d0d7de",
    title_color="#1f2328",
    text_color="#656d76",
    meta_color="#656d76",
    accent="#0969da",
    link_color="#0969da",
)

DARK_THEME = SvgCardTheme(
    bg="transparent",
    border="#30363d",
    title_color="#e6edf3",
    text_color="#8b949e",
    meta_color="#8b949e",
    accent="#58a6ff",
    link_color="#58a6ff",
)

# ---------------------------------------------------------------------------
# Language color map
# ---------------------------------------------------------------------------

LANGUAGE_COLORS: dict[str, str] = {
    "Python": "#3572A5",
    "JavaScript": "#f1e05a",
    "TypeScript": "#3178c6",
    "Rust": "#dea584",
    "Go": "#00ADD8",
    "Java": "#b07219",
    "C": "#555555",
    "C++": "#f34b7d",
    "C#": "#178600",
    "Ruby": "#701516",
    "PHP": "#4F5D95",
    "Swift": "#F05138",
    "Kotlin": "#A97BFF",
    "Scala": "#c22d40",
    "Shell": "#89e051",
    "HTML": "#e34c26",
    "CSS": "#563d7c",
    "Dart": "#00B4AB",
    "Lua": "#000080",
    "R": "#198CE7",
    "Jupyter Notebook": "#DA5B0B",
}


# ---------------------------------------------------------------------------
# Text wrapping utilities
# ---------------------------------------------------------------------------


def _word_wrap(
    text: str,
    width: int,
    max_lines: int | None = 3,
    *,
    ellipsize: bool = True,
) -> list[str]:
    """Break *text* into lines of at most *width* characters on word
    boundaries.  The last visible line is ellipsized if there is
    remaining text."""
    if not text:
        return []
    words = text.split()
    result: list[str] = []
    current = ""
    for word in words:
        trial = f"{current} {word}".strip() if current else word
        if len(trial) <= width:
            current = trial
        else:
            if current:
                result.append(current)
            current = word
            if max_lines is not None and len(result) >= max_lines:
                break
    if current and (max_lines is None or len(result) < max_lines):
        result.append(current)
    # Ellipsize last line if we ran out of room
    full = " ".join(words)
    shown = " ".join(result)
    if result and ellipsize and len(shown) < len(full):
        last = result[-1]
        if len(last) > width - 1:
            last = last[: width - 1]
        result[-1] = f"{last}\u2026"
    return result[:max_lines] if max_lines is not None else result


def _chars_for_width(width_px: int, font_size: int, factor: float) -> int:
    """Approximate character count that fits in *width_px* at *font_size*."""
    return max(8, int(width_px / max(font_size * factor, 1)))


# ---------------------------------------------------------------------------
# Card shell helpers (shared across SvgRepoCard / SvgBlogCard / SvgConnect)
# ---------------------------------------------------------------------------


def _shadow_filter_defs() -> str:
    """Return SVG ``<filter>`` and ``<linearGradient>`` defs for the shared
    drop-shadow + glass-gradient treatment used by all gh-card renderers."""
    return (
        '<filter id="shadow" x="-5%" y="-5%" width="110%" height="110%">'
        '<feDropShadow dx="0" dy="4" stdDeviation="5"'
        ' flood-color="#000000" flood-opacity="0.06"/>'
        '<feDropShadow dx="0" dy="1" stdDeviation="2"'
        ' flood-color="#000000" flood-opacity="0.04"/>'
        '</filter>'
        '<linearGradient id="glass-grad" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0%" stop-color="#ffffff" stop-opacity="0.04" />'
        '<stop offset="100%" stop-color="#ffffff" stop-opacity="0" />'
        '</linearGradient>'
    )


def _card_shell(
    w: int,
    h: int,
    rx: int = 10,
    accent_fill: str = "var(--accent)",
    clip_id: str = "bar-clip",
) -> list[str]:
    """Return the five ``<rect>`` elements forming the standard card shell:
    background with shadow, glass overlay, border, inner rim, accent bar."""
    inner_rx = max(rx - 1, 0)
    return [
        f'<rect class="rc-bg" width="{w}" height="{h}" rx="{rx}"'
        ' fill="transparent" filter="url(#shadow)" />',
        f'<rect width="{w}" height="{h}" rx="{rx}"'
        ' fill="url(#glass-grad)" />',
        f'<rect class="rc-border" x="0.5" y="0.5" width="{w - 1}" height="{h - 1}"'
        f' rx="{rx}" fill="none"'
        ' stroke-width="1" />',
        f'<rect x="1.5" y="1.5" width="{w - 3}" height="{h - 3}"'
        f' rx="{inner_rx}" fill="none"'
        ' stroke="#ffffff" stroke-opacity="0.1" stroke-width="1" />',
        f'<rect x="0" y="0" width="{w}" height="3"'
        f' fill="{accent_fill}"'
        f' clip-path="url(#{clip_id})" />',
    ]


# ---------------------------------------------------------------------------
# Card and block dataclasses (public API — do NOT change fields)
# ---------------------------------------------------------------------------


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
    homepage: str | None = None
    topics: tuple[str, ...] | None = None
    updated_at: str | None = None
    created_at: str | None = None
    forks: int | None = None
    size_kb: int | None = None
    languages: dict[str, int] | None = None
    license_spdx: str | None = None
    open_issues: int | None = None


class SvgCardFamily(str, Enum):
    """Supported card families for legacy block rendering."""

    DEFAULT = "default"
    CONNECT = "connect"
    FEATURED = "featured"
    BLOG = "blog"


@dataclass(frozen=True)
class SvgBlock:
    """A group of cards rendered as a single SVG section asset."""

    title: str
    cards: tuple[SvgCard, ...]
    columns: int = 1
    family: SvgCardFamily | str | None = None
    show_title: bool = False
    transparent_canvas: bool = True


# ---------------------------------------------------------------------------
# Renderer
# ---------------------------------------------------------------------------


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

    # -- public ------------------------------------------------------------

    def render(self, block: SvgBlock) -> str:
        cards = block.cards or (SvgCard(title="No items available."),)
        columns = max(1, block.columns)
        rows = (len(cards) + columns - 1) // columns
        card_width = int(
            (self.width - (self.padding * (columns + 1))) / columns
        )
        title_offset = 28 if block.show_title and block.title else 0
        canvas_padding = 16 if not block.transparent_canvas else 0
        height = (
            self.padding
            + title_offset
            + canvas_padding
            + (rows * (self.card_height + self.padding))
        )

        block_family = block.family or block.title or ""
        family = (
            block_family.value
            if isinstance(block_family, SvgCardFamily)
            else str(block_family)
        ).lower()

        svg_lines = [
            (
                f'<svg xmlns="http://www.w3.org/2000/svg" '
                f'width="{self.width}" height="{height}" '
                f'viewBox="0 0 {self.width} {height}" role="img">'
            ),
            "<defs>",
            "<style>",
            self._build_css(),
            "</style>",
            "</defs>",
        ]

        if not block.transparent_canvas:
            svg_lines.append(
                '<rect width="100%" height="100%" fill="var(--canvas-bg)" />'
            )

        if block.show_title and block.title:
            svg_lines.append(
                f'<text class="section-title" x="{self.padding}" '
                f'y="{self.padding + 16}">{self._esc(block.title)}</text>'
            )

        card_y_offset = title_offset + canvas_padding

        for idx, card in enumerate(cards):
            column = idx % columns
            row = idx // columns
            x = self.padding + (column * (card_width + self.padding))
            y = (
                self.padding
                + card_y_offset
                + (row * (self.card_height + self.padding))
            )
            svg_lines.extend(
                self._render_card(card, x, y, card_width, idx, family)
            )

        svg_lines.append("</svg>")
        return "\n".join(svg_lines)

    # -- CSS ---------------------------------------------------------------

    def _build_css(self) -> str:  # noqa: PLR6301
        lt = LIGHT_THEME
        dk = DARK_THEME
        # Use direct colors — GitHub SVG sanitizer doesn't resolve var().
        return "\n".join(
            [
                f".rc-bg {{ fill: {lt.bg}; }}",
                f".rc-border {{ stroke: {lt.border}; }}",
                f".section-title {{ fill: {lt.title_color};"
                f" font: 700 14px {FONT_FAMILY}; }}",
                f".card-title {{ fill: {lt.title_color};"
                f" font: 700 16px {FONT_FAMILY}; }}",
                f".card-line {{ fill: {lt.text_color};"
                f" font: 400 14px {FONT_FAMILY}; }}",
                f".card-meta {{ fill: {lt.meta_color};"
                f" font: 400 12px {FONT_FAMILY}; }}",
                f".card-kicker {{ fill: {lt.meta_color};"
                f" font: 700 11px {FONT_FAMILY};"
                " letter-spacing: 0.08em; text-transform: uppercase; }",
                f".card-icon {{ fill: {lt.title_color};"
                f" font: 700 12px {FONT_FAMILY}; }}",
                f".card-badge {{ fill: {lt.title_color};"
                f" font: 700 12px {FONT_FAMILY};"
                " letter-spacing: 0.01em; }",
                f".sparkline {{ fill: none; stroke: {lt.accent};"
                " stroke-width: 2; opacity: 0.88; }",
                f".lang-dot {{ stroke: {lt.border}; stroke-width: 1; }}",
                f".lang-label {{ fill: {lt.meta_color};"
                f" font: 400 12px {FONT_FAMILY}; }}",
                "@media (prefers-color-scheme: dark) {",
                f"  .rc-bg {{ fill: {dk.bg}; }}",
                f"  .rc-border {{ stroke: {dk.border}; }}",
                f"  .section-title {{ fill: {dk.title_color}; }}",
                f"  .card-title {{ fill: {dk.title_color}; }}",
                f"  .card-line {{ fill: {dk.text_color}; }}",
                f"  .card-meta {{ fill: {dk.meta_color}; }}",
                f"  .card-kicker {{ fill: {dk.meta_color}; }}",
                f"  .card-icon {{ fill: {dk.title_color}; }}",
                f"  .card-badge {{ fill: {dk.title_color}; }}",
                f"  .sparkline {{ stroke: {dk.accent}; }}",
                f"  .lang-dot {{ stroke: {dk.border}; }}",
                f"  .lang-label {{ fill: {dk.meta_color}; }}",
                "}",
            ]
        )

    # -- card rendering ----------------------------------------------------

    def _render_card(
        self,
        card: SvgCard,
        x: int,
        y: int,
        width: int,
        card_index: int,
        family: str = "",
    ) -> list[str]:
        accent = self._normalize_hex_color(card.accent)
        is_blog_family = "blog" in family
        lines: list[str] = [
            f'<g class="card" transform="translate({x},{y})">'
        ]
        if card.url:
            lines.append(
                f'<a href="{self._esc(card.url)}"'
                ' target="_blank" rel="noopener noreferrer">'
            )

        # Card background rect — gh-card style
        lines.append(
            f'<rect width="{width}" height="{self.card_height}"'
            ' rx="6" fill="transparent"'
            ' stroke="var(--card-border)" stroke-width="1" />'
        )

        # Background image support
        if card.background_image:
            clip_id = f"clip-{card_index}"
            lines.append(
                f'<defs><clipPath id="{clip_id}">'
                f'<rect width="{width}" height="{self.card_height}" rx="6" />'
                f"</clipPath></defs>"
            )
            lines.append(
                f'<image href="{self._esc(card.background_image)}"'
                f' width="{width}" height="{self.card_height}"'
                ' preserveAspectRatio="xMidYMid slice"'
                f' clip-path="url(#{clip_id})" opacity="0.10" />'
            )

        # ---- Top row: icon circle + title --------------------------------
        inner_x = 16
        title_y = 32
        monogram = self._truncate((card.icon or "").upper(), 3)
        icon_data_uri = self._sanitize_icon_data_uri(card.icon_data_uri)
        if not is_blog_family and (icon_data_uri or monogram):
            cx = 34
            cy = 28
            r = 14
            lines.append(
                f'<circle cx="{cx}" cy="{cy}" r="{r}"'
                f' fill="{accent}" fill-opacity="0.15"'
                f' stroke="{accent}" stroke-opacity="0.40"'
                ' stroke-width="1" />'
            )
            if icon_data_uri:
                icon_clip_id = f"icon-clip-{card_index}"
                img_size = r * 2 - 4
                img_offset_x = cx - img_size / 2
                img_offset_y = cy - img_size / 2
                lines.append(
                    f'<defs><clipPath id="{icon_clip_id}">'
                    f'<circle cx="{cx}" cy="{cy}" r="{r - 1}" />'
                    f"</clipPath></defs>"
                )
                lines.append(
                    f'<image class="card-icon-image"'
                    f' href="{self._esc(icon_data_uri)}"'
                    f' x="{img_offset_x}" y="{img_offset_y}"'
                    f' width="{img_size}" height="{img_size}"'
                    ' preserveAspectRatio="xMidYMid meet"'
                    f' clip-path="url(#{icon_clip_id})" />'
                )
            elif monogram:
                lines.append(
                    f'<text class="card-icon" x="{cx}" y="{cy + 4}"'
                    f' text-anchor="middle">{self._esc(monogram)}</text>'
                )
            inner_x = 56

        # Kicker
        if card.kicker and not is_blog_family:
            lines.append(
                f'<text class="card-kicker" x="{inner_x}" y="20">'
                f"{self._esc(self._truncate(card.kicker, 56))}</text>"
            )
            title_y = 40

        # Badge (suppressed for blog family)
        if card.badge and not is_blog_family:
            badge_text = self._truncate(card.badge, 20)
            badge_width = max(60, min(200, len(badge_text) * 7 + 20))
            badge_x = max(16, width - badge_width - 16)
            lines.append(
                f'<rect x="{badge_x}" y="12" width="{badge_width}"'
                ' height="22" rx="11" fill="var(--accent)"'
                ' fill-opacity="0.12" stroke="var(--accent)"'
                ' stroke-opacity="0.30" stroke-width="1" />'
            )
            lines.append(
                f'<text class="card-badge"'
                f' x="{badge_x + badge_width / 2:.1f}" y="27"'
                f' text-anchor="middle">{self._esc(badge_text)}</text>'
            )

        # Title
        if is_blog_family:
            sanitized_title = re.sub(r"\.{2,}|[…]", "", card.title)
            sanitized_title = re.sub(
                r"\bupdate\b", "", sanitized_title, flags=re.IGNORECASE
            ).strip()
            lines.append(
                f'<text class="card-title" x="{inner_x}" y="{title_y}">'
                f'<tspan x="{inner_x}">'
                f"{self._esc(sanitized_title)}</tspan></text>"
            )
        else:
            lines.append(
                f'<text class="card-title" x="{inner_x}" y="{title_y}">'
                f"{self._esc(self._truncate(card.title, 52))}</text>"
            )

        # ---- Middle: description lines -----------------------------------
        text_y = title_y + 22
        visible_lines = list(card.lines or ())
        if "connect" in family:
            visible_lines = [
                ln for ln in visible_lines if not ln.strip().startswith("@")
            ]
        if "featured" in family:
            if card.homepage:
                visible_lines.append(card.homepage)
            if card.topics:
                for t in card.topics:
                    visible_lines.append(str(t))

        for line in visible_lines[:3]:
            display = (
                line
                if is_blog_family
                else self._truncate(line, 72)
            )
            lines.append(
                f'<text class="card-line" x="{inner_x}" y="{text_y}">'
                f"{self._esc(display)}</text>"
            )
            text_y += 20

        # Sparkline
        if card.sparkline and len(card.sparkline) >= 2:
            sparkline_path = self._sparkline_path(
                card.sparkline, width=width - 48, height=28
            )
            lines.append(
                f'<path class="sparkline" d="{sparkline_path}"'
                f' transform="translate(16,{self.card_height - 52})" />'
            )

        # ---- Bottom bar: language dot + stats ----------------------------
        if card.meta:
            bottom_y = self.card_height - 14
            meta_x = inner_x
            meta_x = self._render_bottom_bar(
                lines, card.meta, meta_x, bottom_y
            )

        if card.url:
            lines.append("</a>")
        lines.append("</g>")
        return lines

    def _render_bottom_bar(
        self,
        lines: list[str],
        meta: tuple[str, ...],
        start_x: int,
        y: int,
    ) -> int:
        """Render language dot, star/fork icons, and remaining meta items."""
        x = start_x
        remaining: list[str] = []

        for item in meta[:4]:
            stripped = item.strip()

            # Language item: "lang:Python"
            if stripped.startswith("lang:"):
                lang_name = stripped[5:].strip()
                color = LANGUAGE_COLORS.get(lang_name, "#8b949e")
                lines.append(
                    f'<circle class="lang-dot" cx="{x + 5}" cy="{y - 3}"'
                    f' r="5" fill="{color}" />'
                )
                lines.append(
                    f'<text class="lang-label" x="{x + 14}" y="{y}">'
                    f"{self._esc(lang_name)}</text>"
                )
                x += 14 + len(lang_name) * 7 + 12
                continue

            # Star count
            star_match = re.match(r"[★☆]\s*(.+)", stripped)
            if star_match:
                count_text = star_match.group(1).strip()
                lines.append(
                    f'<svg x="{x}" y="{y - 12}" width="16" height="16"'
                    ' viewBox="0 0 16 16" fill="var(--meta-color)">'
                    f'<path d="{STAR_ICON_PATH}" /></svg>'
                )
                lines.append(
                    f'<text class="card-meta" x="{x + 18}" y="{y}">'
                    f"{self._esc(count_text)}</text>"
                )
                x += 18 + len(count_text) * 7 + 12
                continue

            # Fork count
            fork_match = re.match(r"[⑂]\s*(.+)", stripped)
            if fork_match:
                count_text = fork_match.group(1).strip()
                lines.append(
                    f'<svg x="{x}" y="{y - 12}" width="16" height="16"'
                    ' viewBox="0 0 16 16" fill="var(--meta-color)">'
                    f'<path d="{FORK_ICON_PATH}" /></svg>'
                )
                lines.append(
                    f'<text class="card-meta" x="{x + 18}" y="{y}">'
                    f"{self._esc(count_text)}</text>"
                )
                x += 18 + len(count_text) * 7 + 12
                continue

            remaining.append(stripped)

        if remaining:
            joined = " \u00b7 ".join(
                self._truncate(r, 28) for r in remaining
            )
            lines.append(
                f'<text class="card-meta" x="{x}" y="{y}">'
                f"{self._esc(joined)}</text>"
            )
            x += len(joined) * 7

        return x

    # -- helpers -----------------------------------------------------------

    def _truncate(self, value: str, limit: int) -> str:  # noqa: PLR6301
        return value if len(value) <= limit else f"{value[: limit - 1]}\u2026"

    def _esc(self, value: str) -> str:  # noqa: PLR6301
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

    def _normalize_hex_color(self, value: str | None) -> str:  # noqa: PLR6301
        if not value:
            return "#60A5FA"
        cleaned = value.strip()
        if re.fullmatch(r"#?[0-9A-Fa-f]{6}", cleaned):
            return f"#{cleaned.lstrip('#')}"
        return "#60A5FA"

    def _sanitize_icon_data_uri(self, value: str | None) -> str | None:  # noqa: PLR6301
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


# ---------------------------------------------------------------------------
# Repo card icon path (GitHub Octicons — repo icon, 16×16 viewBox)
# ---------------------------------------------------------------------------

REPO_ICON_PATH = (
    "M2 2.5A2.5 2.5 0 0 1 4.5 0h8.75a.75.75 0 0 1 .75.75v12.5a.75.75"
    " 0 0 1-.75.75h-2.5a.75.75 0 0 1 0-1.5h1.75v-2h-8a1 1 0 0 0-.714"
    " 1.7.75.75 0 1 1-1.072 1.05A2.495 2.495 0 0 1 2 11.5Zm10.5-1h-8a1"
    " 1 0 0 0-1 1v6.708A2.486 2.486 0 0 1 4.5 9h8ZM5 12.25a.25.25 0 0 1"
    " .25-.25h3.5a.25.25 0 0 1 .25.25v3.25a.25.25 0 0 1-.4.2l-1.45-1.087"
    "a.249.249 0 0 0-.3 0L5.4 15.7a.25.25 0 0 1-.4-.2Z"
)

# ---------------------------------------------------------------------------
# Individual repo card renderer (gh-card style, improved)
# ---------------------------------------------------------------------------


class SvgRepoCardRenderer:
    """Render a featured repo card as a standalone SVG.

    Transparent background, smooth sparkline, OG preview thumbnail,
    language indicator, star/fork stats, word-wrapped descriptions.
    """

    # Approximate char width at 13px sans-serif
    _CHAR_W = 6.8
    _TITLE_FONT_SIZES = (17, 16, 15, 14, 13, 12)
    _DESC_FONT_SIZES = (13, 12, 11, 10, 9)

    def __init__(
        self,
        width: int = 500,
        height: int = 185,
    ) -> None:
        self.width = width
        self.height = height

    def render_card(self, card: SvgCard) -> str:
        w = self.width
        h = self.height
        esc = escape
        lang_name, lang_color = self._extract_language(card.meta)
        has_thumb = bool(card.background_image)
        thumb_w, thumb_h = (130, 75) if has_thumb else (0, 0)
        px = 20  # left padding
        sparkline_data = card.sparkline if card.sparkline and len(card.sparkline) >= 2 else None
        text_px_w = (w - thumb_w - 36 - px) if has_thumb else (w - px - 20)
        raw_desc = " ".join(
            ln.strip() for ln in (card.lines or ()) if ln.strip()
        )
        bar_y = h - 30
        show_sparkline = False
        layout: tuple[list[str], list[str], int, int] | None = None
        for try_sparkline in ([True, False] if sparkline_data else [False]):
            text_bottom = (h - 64) if try_sparkline else (bar_y - 12)
            available_height = max(36, text_bottom - 16)
            candidate, fits = self._fit_copy_layout(
                title=card.title,
                description=raw_desc,
                text_px_w=text_px_w,
                available_height=available_height,
            )
            layout = candidate
            if fits or not try_sparkline:
                show_sparkline = try_sparkline and sparkline_data is not None and fits
                break

        if layout is None:
            layout = ([card.title], [], 17, 13)
        title_lines, desc_lines, title_size, desc_size = layout
        title_x = px + 24
        title_y = 16 + title_size
        title_line_height = title_size + 4
        desc_y = title_y + (len(title_lines) * title_line_height) + (10 if desc_lines else 0)
        desc_line_height = desc_size + 3

        lines: list[str] = [
            (
                f'<svg xmlns="http://www.w3.org/2000/svg" '
                f'xmlns:xlink="http://www.w3.org/1999/xlink" '
                f'width="{w}" height="{h}" '
                f'viewBox="0 0 {w} {h}" role="img" '
                f'aria-label="{esc(card.title, quote=True)}">'
            ),
            "<defs>",
            "<style>",
            self._build_css(lang_color),
            "</style>",
            f'<clipPath id="card-clip">'
            f'<rect width="{w}" height="{h}" rx="10" /></clipPath>',
            _shadow_filter_defs(),
        ]
        if has_thumb:
            thumb_x = w - thumb_w - 18
            lines.append(
                f'<clipPath id="thumb-clip">'
                f'<rect x="{thumb_x}" y="18" '
                f'width="{thumb_w}" height="{thumb_h}" rx="8" />'
                f'</clipPath>'
            )
        if show_sparkline:
            lines.append(
                '<linearGradient id="spark-grad" x1="0" y1="0"'
                ' x2="0" y2="1">'
                '<stop offset="0%" stop-color="var(--spark-stroke)"'
                ' stop-opacity="0.18" />'
                '<stop offset="100%" stop-color="var(--spark-stroke)"'
                ' stop-opacity="0" />'
                '</linearGradient>'
            )
        lines.append("</defs>")

        accent_color = lang_color or "var(--spark-stroke)"
        lines.extend(_card_shell(
            w, h, rx=10, accent_fill=accent_color, clip_id="card-clip",
        ))

        if has_thumb:
            thumb_x = w - thumb_w - 18
            lines.append(
                f'<image href="{esc(card.background_image, quote=True)}"'
                f' x="{thumb_x}" y="18"'
                f' width="{thumb_w}" height="{thumb_h}"'
                ' preserveAspectRatio="xMidYMid slice"'
                ' clip-path="url(#thumb-clip)" />'
            )
            lines.append(
                f'<rect x="{thumb_x}" y="18"'
                f' width="{thumb_w}" height="{thumb_h}" rx="8"'
                ' fill="none" stroke="var(--card-border)"'
                ' stroke-opacity="0.5" stroke-width="1" />'
            )

        if show_sparkline and sparkline_data:
            spark_w = w - 40
            spark_h = 28
            spark_y = h - 56
            spark_path = self._smooth_sparkline(
                sparkline_data, width=spark_w, height=spark_h,
            )
            if spark_path:
                area = (
                    f"{spark_path} "
                    f"L{spark_w:.1f},{spark_h:.1f} L0,{spark_h:.1f} Z"
                )
                lines.append(
                    f'<g transform="translate({px},{spark_y})"'
                    ' class="sparkline-group">'
                )
                lines.append(
                    f'<path d="{area}" fill="url(#spark-grad)" />'
                )
                lines.append(
                    f'<path d="{spark_path}"'
                    ' fill="none" stroke="var(--spark-stroke)"'
                    ' stroke-width="1.5" stroke-linecap="round"'
                    ' stroke-linejoin="round" />'
                )
                lines.append("</g>")

        lines.append(
            f'<svg x="{px}" y="18" width="18" height="18"'
            ' viewBox="0 0 16 16" fill="var(--meta-color)">'
            f'<path fill-rule="evenodd" d="{REPO_ICON_PATH}" /></svg>'
        )
        for index, line_text in enumerate(title_lines):
            lines.append(
                f'<text class="rc-title" x="{title_x}" y="{title_y + (index * title_line_height)}"'
                f' style="font: 600 {title_size}px {FONT_FAMILY};">'
                f"{esc(line_text, quote=True)}</text>"
            )

        stat_right = (w - thumb_w - 36) if has_thumb else (w - 20)
        self._render_stats(lines, card.meta, stat_right, title_y)

        for line_text in desc_lines:
            lines.append(
                f'<text class="rc-desc" x="{px}" y="{desc_y}"'
                f' style="font: 400 {desc_size}px {FONT_FAMILY};">'
                f"{esc(line_text, quote=True)}</text>"
            )
            desc_y += desc_line_height

        # Shorten language bar when license label needs space in bottom-right
        has_license = bool(card.license_spdx and card.license_spdx != "NOASSERTION")
        license_reserve = (len(card.license_spdx or "") * 7 + 30) if has_license else 0
        bar_w = min(w - 40 - license_reserve, 340)
        if card.languages and sum(card.languages.values()) > 0:
            self._render_lang_bar(
                lines, card.languages, px, bar_y, bar_w,
            )
        elif lang_name and lang_color:
            lines.append(
                f'<rect x="{px}" y="{bar_y}" width="{bar_w}"'
                f' height="3" rx="1.5" fill="{lang_color}"'
                ' fill-opacity="0.5" />'
            )

        fy = h - 14
        self._render_footer(lines, card, px, fy, lang_name, lang_color)

        lines.append("</svg>")
        return "\n".join(lines)

    def _build_css(self, accent: str | None = None) -> str:
        lt = LIGHT_THEME
        dk = DARK_THEME
        ac = accent or lt.accent
        # Use direct colors instead of CSS custom properties — GitHub's SVG
        # sanitizer does not resolve var() in <img> context.
        return "\n".join(
            [
                f".rc-bg {{ fill: transparent; }}",
                f".rc-border {{ stroke: {lt.border}; }}",
                f".rc-title {{ fill: {lt.link_color};"
                f" font: 600 17px {FONT_FAMILY}; }}",
                f".rc-desc {{ fill: {lt.text_color};"
                f" font: 400 13px {FONT_FAMILY}; }}",
                f".rc-meta {{ fill: #24292e;"
                f" font: 400 12px {FONT_FAMILY}; }}",
                ".rc-lang-dot { stroke: none; }",
                f".rc-lang-label {{ fill: #24292e;"
                f" font: 400 12px {FONT_FAMILY}; }}",
                f".sparkline {{ fill: none; stroke: {ac};"
                " stroke-width: 2; opacity: 0.88; }",
                "@media (prefers-color-scheme: dark) {",
                f"  .rc-bg {{ fill: transparent; }}",
                f"  .rc-border {{ stroke: {dk.border}; }}",
                f"  .rc-title {{ fill: {dk.link_color}; }}",
                f"  .rc-desc {{ fill: {dk.text_color}; }}",
                f"  .rc-meta {{ fill: {dk.text_color}; }}",
                f"  .rc-lang-label {{ fill: {dk.text_color}; }}",
                f"  .sparkline {{ stroke: {dk.accent}; }}",
                "}",
            ]
        )

    def _render_stats(
        self,
        lines: list[str],
        meta: tuple[str, ...],
        right_x: int,
        y: int,
    ) -> None:
        """Render star/fork counts right-aligned at (right_x, y)."""
        esc = escape
        items: list[tuple[str, str]] = []  # (icon_path, count_text)
        for item in (meta or ()):
            stripped = item.strip()
            star_match = re.match(r"[★☆]\s*(.+)", stripped)
            if star_match:
                items.append((STAR_ICON_PATH, star_match.group(1).strip()))
                continue
            fork_match = re.match(r"[⑂]\s*(.+)", stripped)
            if fork_match:
                items.append((FORK_ICON_PATH, fork_match.group(1).strip()))
                continue
            issue_match = re.match(r"[⊙]\s*(.+)", stripped)
            if issue_match:
                items.append((ISSUE_ICON_PATH, issue_match.group(1).strip()))
        if not items:
            return
        # Layout right-to-left from right_x
        x = right_x
        for icon_path, ct in reversed(items):
            text_w = int(len(ct) * 7)
            x -= text_w
            lines.append(
                f'<text class="rc-meta" x="{x}" y="{y}">'
                f"{esc(ct, quote=True)}</text>"
            )
            x -= 18
            vb = "0 0 16 16"
            lines.append(
                f'<svg x="{x}" y="{y - 12}" width="16" height="16"'
                f' viewBox="{vb}" fill="var(--meta-color)">'
                f'<path d="{icon_path}" /></svg>'
            )
            x -= 12

    def _render_footer(
        self,
        lines: list[str],
        card: SvgCard,
        start_x: int,
        y: int,
        lang_name: str | None,
        lang_color: str | None,
    ) -> int:
        """Render footer — languages only (stats shown in title row)."""
        x = start_x
        esc = escape

        if card.languages and sum(card.languages.values()) > 0:
            total = sum(card.languages.values())
            has_license = bool(card.license_spdx and card.license_spdx != "NOASSERTION")
            max_langs = 2 if has_license else 3
            top = sorted(
                card.languages.items(), key=lambda kv: kv[1],
                reverse=True,
            )[:max_langs]
            for lname, lbytes in top:
                lcolor = LANGUAGE_COLORS.get(lname, "#8b949e")
                pct = round(100 * lbytes / total)
                label = f"{lname} {pct}%"
                lines.append(
                    f'<circle class="rc-lang-dot" cx="{x + 4}"'
                    f' cy="{y - 4}" r="4" fill="{lcolor}" />'
                )
                lines.append(
                    f'<text class="rc-meta" x="{x + 12}" y="{y}">'
                    f"{esc(label, quote=True)}</text>"
                )
                x += 12 + int(len(label) * 6.5) + 10
        elif lang_name and lang_color:
            lines.append(
                f'<circle class="rc-lang-dot" cx="{x + 5}" cy="{y - 4}"'
                f' r="5" fill="{lang_color}" />'
            )
            lines.append(
                f'<text class="rc-lang-label" x="{x + 15}" y="{y}">'
                f"{esc(lang_name, quote=True)}</text>"
            )
            x += 15 + len(lang_name) * 7 + 14

        # License label — right-aligned in footer, with overlap guard
        if card.license_spdx and card.license_spdx != "NOASSERTION":
            lt = card.license_spdx
            text_w = int(len(lt) * 7)
            icon_w = 18
            license_total_w = icon_w + text_w
            lx_text = self.width - 20 - text_w
            lx_icon = lx_text - icon_w
            # Only render if there's enough gap from the language dots
            if lx_icon > x + 8:
                lines.append(
                    f'<svg x="{lx_icon}" y="{y - 12}" width="14" height="14"'
                    ' viewBox="0 0 16 16" fill="var(--meta-color)">'
                    f'<path d="{LAW_ICON_PATH}" /></svg>'
                )
                lines.append(
                    f'<text class="rc-meta" x="{lx_text}" y="{y}">'
                    f"{esc(lt, quote=True)}</text>"
                )

        return x

    def _render_lang_bar(
        self,
        lines: list[str],
        languages: dict[str, int],
        x: int,
        y: int,
        width: int,
    ) -> None:
        """Render a GitHub-style multi-color language proportion bar."""
        total = sum(languages.values())
        if total <= 0:
            return
        sorted_langs = sorted(
            languages.items(), key=lambda kv: kv[1], reverse=True,
        )
        # Clip to card shape
        clip_id = "lang-bar-clip"
        lines.append(
            f'<clipPath id="{clip_id}">'
            f'<rect x="{x}" y="{y}" width="{width}"'
            f' height="4" rx="2" /></clipPath>'
        )
        lines.append(f'<g clip-path="url(#{clip_id})">')
        cx = x
        for lang, count in sorted_langs:
            seg_w = max(1, (count / total) * width)
            color = LANGUAGE_COLORS.get(lang, "#8b949e")
            lines.append(
                f'<rect x="{cx:.1f}" y="{y}" width="{seg_w:.1f}"'
                f' height="4" fill="{color}" />'
            )
            cx += seg_w
        lines.append("</g>")

    # -- helpers -----------------------------------------------------------

    def _extract_language(
        self, meta: tuple[str, ...] | None,
    ) -> tuple[str | None, str | None]:
        for item in (meta or ()):
            if item.strip().startswith("lang:"):
                lang = item.strip()[5:].strip()
                color = LANGUAGE_COLORS.get(lang, "#8b949e")
                return lang, color
        return None, None

    def _fit_copy_layout(
        self,
        *,
        title: str,
        description: str,
        text_px_w: int,
        available_height: int,
    ) -> tuple[tuple[list[str], list[str], int, int], bool]:
        best: tuple[list[str], list[str], int, int] | None = None
        best_overflow: int | None = None

        for title_size in self._TITLE_FONT_SIZES:
            title_width = _chars_for_width(text_px_w, title_size, 0.56)
            title_lines = _word_wrap(
                title,
                title_width,
                max_lines=None,
                ellipsize=False,
            )
            title_line_height = title_size + 4
            title_height = len(title_lines) * title_line_height
            for desc_size in self._DESC_FONT_SIZES:
                desc_width = _chars_for_width(text_px_w, desc_size, 0.58)
                desc_lines = _word_wrap(
                    description,
                    desc_width,
                    max_lines=None,
                    ellipsize=False,
                )
                desc_line_height = desc_size + 3
                gap = 10 if desc_lines else 0
                total_height = title_height + gap + (len(desc_lines) * desc_line_height)
                layout = (title_lines, desc_lines, title_size, desc_size)
                if total_height <= available_height:
                    return layout, True
                overflow = total_height - available_height
                if best is None or best_overflow is None or overflow < best_overflow:
                    best = layout
                    best_overflow = overflow

        if best is None:
            return ([title], [], 17, 13), False

        title_lines, desc_lines, title_size, desc_size = best
        title_height = len(title_lines) * (title_size + 4)
        remaining_height = max(0, available_height - title_height - (10 if desc_lines else 0))
        max_desc_lines = remaining_height // (desc_size + 3)
        if max_desc_lines <= 0:
            desc_lines = []
        else:
            desc_lines = desc_lines[:max_desc_lines]
        return (title_lines, desc_lines, title_size, desc_size), False

    @staticmethod
    def _truncate(value: str, limit: int) -> str:
        return value if len(value) <= limit else f"{value[: limit - 1]}\u2026"

    @staticmethod
    def _smooth_sparkline(
        points: tuple[float, ...],
        width: int,
        height: int,
    ) -> str:
        """Generate a smooth cubic-bezier sparkline path (catmull-rom
        converted to SVG cubic beziers)."""
        n = len(points)
        if n < 2:
            return ""
        lo = min(points)
        hi = max(points)
        span = max(hi - lo, 1e-6)
        coords = [
            ((i / (n - 1)) * width, height - ((v - lo) / span) * height)
            for i, v in enumerate(points)
        ]
        # Catmull-Rom → cubic bezier segments
        parts = [f"M{coords[0][0]:.1f},{coords[0][1]:.1f}"]
        for i in range(len(coords) - 1):
            p0 = coords[max(i - 1, 0)]
            p1 = coords[i]
            p2 = coords[min(i + 1, len(coords) - 1)]
            p3 = coords[min(i + 2, len(coords) - 1)]
            # Tension 0.5
            cp1x = p1[0] + (p2[0] - p0[0]) / 6
            cp1y = p1[1] + (p2[1] - p0[1]) / 6
            cp2x = p2[0] - (p3[0] - p1[0]) / 6
            cp2y = p2[1] - (p3[1] - p1[1]) / 6
            parts.append(
                f"C{cp1x:.1f},{cp1y:.1f}"
                f" {cp2x:.1f},{cp2y:.1f}"
                f" {p2[0]:.1f},{p2[1]:.1f}"
            )
        return " ".join(parts)


# ---------------------------------------------------------------------------
# Blog post card renderer
# ---------------------------------------------------------------------------


class SvgBlogCardRenderer:
    """Render a single blog post card as a standalone SVG.

    Clean layout with optional hero thumbnail, word-wrapped summary,
    and date/host footer with a subtle accent line.
    """

    def __init__(self, width: int = 480, height: int = 150) -> None:
        self.width = width
        self.height = height

    def render_card(self, card: SvgCard) -> str:
        w = self.width
        esc = escape
        has_hero = bool(card.background_image)
        hero_w, hero_h = (110, 68) if has_hero else (0, 0)
        px = 20
        text_w = (w - hero_w - 56) if has_hero else (w - 40)
        sanitized_title = re.sub(r"\.{2,}|[…]", "", card.title)
        sanitized_title = re.sub(
            r"\bupdate\b", "", sanitized_title, flags=re.IGNORECASE,
        ).strip()
        raw = " ".join(
            ln.strip() for ln in (card.lines or ()) if ln.strip()
        )
        title_size = 16
        desc_size = 13
        title_line_height = title_size + 4
        desc_line_height = desc_size + 3
        title_char_lim = _chars_for_width(text_w, title_size, 0.58)
        desc_cpl = _chars_for_width(text_w, desc_size, 0.58)
        title_lines = _word_wrap(
            sanitized_title,
            title_char_lim,
            max_lines=None,
            ellipsize=False,
        )
        wrapped = _word_wrap(
            raw,
            desc_cpl,
            max_lines=None,
            ellipsize=False,
        )
        title_top = 18
        title_first_y = title_top + title_size
        summary_y = title_first_y + (len(title_lines) * title_line_height) + (8 if wrapped else 0)
        content_bottom = summary_y + (max(0, len(wrapped) - 1) * desc_line_height)
        hero_bottom = 18 + hero_h if has_hero else 0
        footer_y = max(content_bottom + 28, hero_bottom + 26, self.height - 14)
        h = footer_y + 14

        lines: list[str] = [
            f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'role="img" aria-label="{esc(sanitized_title, quote=True)}">',
            "<defs><style>",
            self._css(),
            "</style>",
        ]
        # Shared defs: clip, shadow, glass + blog-specific footer gradient
        lines.append(
            f'<clipPath id="bar-clip">'
            f'<rect width="{w}" height="{h}" rx="10"/></clipPath>'
            + _shadow_filter_defs()
            + '<linearGradient id="footer-div-grad" x1="0" y1="0" x2="1" y2="0">'
            '<stop offset="0%" stop-color="var(--accent)" stop-opacity="0.5" />'
            '<stop offset="100%" stop-color="var(--accent)" stop-opacity="0" />'
            '</linearGradient>'
        )
        if has_hero:
            hx = w - hero_w - 18
            lines.append(
                f'<clipPath id="hero-clip"><rect x="{hx}" y="18"'
                f' width="{hero_w}" height="{hero_h}" rx="8" />'
                f"</clipPath>"
            )
        lines.append("</defs>")

        # Shell
        lines.extend(_card_shell(w, h, rx=10, accent_fill="var(--accent)"))

        # Hero thumbnail
        if has_hero:
            hx = w - hero_w - 18
            lines.append(
                f'<image href="{esc(card.background_image, quote=True)}"'
                f' x="{hx}" y="18" width="{hero_w}" height="{hero_h}"'
                ' preserveAspectRatio="xMidYMid slice"'
                ' clip-path="url(#hero-clip)" />'
            )
            lines.append(
                f'<rect x="{hx}" y="18" width="{hero_w}"'
                f' height="{hero_h}" rx="8" fill="none"'
                ' stroke="var(--card-border)" stroke-opacity="0.5"'
                ' stroke-width="1" />'
            )

        ty = title_first_y
        for tl in title_lines:
            lines.append(
                f'<text class="blog-title" x="{px}" y="{ty}">'
                f"{esc(tl, quote=True)}</text>"
            )
            ty += title_line_height

        dy = summary_y
        for line_text in wrapped:
            lines.append(
                f'<text class="blog-desc" x="{px}" y="{dy}">'
                f"{esc(line_text, quote=True)}</text>"
            )
            dy += desc_line_height

        # Accent line above footer
        lines.append(
            f'<rect x="{px}" y="{footer_y - 16}" width="80"'
            ' height="1.5" rx="0.5" fill="url(#footer-div-grad)" />'
        )

        # Footer: date · host
        fy = footer_y
        meta_parts = [m for m in (card.meta or ()) if m.strip()]
        if meta_parts:
            joined = " · ".join(meta_parts)
            lines.append(
                f'<text class="blog-meta" x="{px}" y="{fy}">'
                f"{esc(joined, quote=True)}</text>"
            )

        lines.append("</svg>")
        return "\n".join(lines)

    def _css(self) -> str:
        lt, dk = LIGHT_THEME, DARK_THEME
        return "\n".join([
            ":root {",
            "  --card-bg: transparent;",
            f"  --card-border: {lt.border};",
            f"  --title-color: {lt.link_color};",
            f"  --text-color: {lt.text_color};",
            f"  --meta-color: {lt.meta_color};",
            f"  --accent: {lt.accent};",
            "}",
            "@media (prefers-color-scheme: dark) { :root {",
            "  --card-bg: transparent;",
            f"  --card-border: {dk.border};",
            f"  --title-color: {dk.link_color};",
            f"  --text-color: {dk.text_color};",
            f"  --meta-color: {dk.meta_color};",
            f"  --accent: {dk.accent};",
            "}}",
            f".rc-bg {{ fill: transparent; }}",
            f".rc-border {{ stroke: {lt.border}; }}",
            "@media (prefers-color-scheme: dark) {",
            f"  .rc-bg {{ fill: transparent; }}",
            f"  .rc-border {{ stroke: {dk.border}; }}",
            "}",
            f".blog-title {{ fill: var(--title-color);"
            f" font: 600 16px {FONT_FAMILY}; }}",
            f".blog-desc {{ fill: var(--text-color);"
            f" font: 400 13px {FONT_FAMILY}; }}",
            f".blog-meta {{ fill: var(--meta-color);"
            f" font: 400 12px {FONT_FAMILY}; }}",
        ])


# ---------------------------------------------------------------------------
# Connect / social card renderer
# ---------------------------------------------------------------------------


class SvgConnectCardRenderer:
    """Render an icon-forward social/contact card as a standalone SVG.

    Squarish card with large centered brand icon, platform name, and
    subtle category label.
    """

    def __init__(self, width: int = 140, height: int = 130) -> None:
        self.width = width
        self.height = height

    # Brand-color map for accent bar detection by card title.
    _BRAND_COLORS: dict[str, str] = {
        "linkedin": "#0A66C2",
        "github": "#24292e",
        "x": "#000000",
        "x.com": "#000000",
        "kaggle": "#20BEFF",
        "w4w.dev": "#0EA5E9",
        "website": "#0EA5E9",
        "email": "#EA4335",
    }

    def _accent_color(self, card: SvgCard) -> str:
        """Resolve brand accent color.

        Uses `card.accent` if present, falls back to known brand color by title,
        or uses the CSS variable `var(--accent)`.
        """
        if card.accent:
            raw = card.accent.strip()
            if not raw.startswith("#"):
                raw = f"#{raw}"
            return raw
        title_lower = card.title.strip().lower()
        return self._BRAND_COLORS.get(title_lower, "var(--accent)")

    def render_card(self, card: SvgCard) -> str:
        w, h = self.width, self.height
        esc = escape
        icon_uri = card.icon_data_uri
        cx = w // 2  # center x
        accent = self._accent_color(card)

        lines: list[str] = [
            f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'role="img" aria-label="{esc(card.title, quote=True)}">',
            "<defs><style>",
            self._css(),
            "</style>",
        ]
        # Shared defs: clip, shadow, glass + connect-specific gradients
        lines.append(
            f'<clipPath id="bar-clip">'
            f'<rect width="{w}" height="{h}" rx="12"/></clipPath>'
            + _shadow_filter_defs()
            + '<radialGradient id="icon-glow">'
            f'<stop offset="0%" stop-color="{esc(accent, quote=True)}" '
            'stop-opacity="0.18" />'
            f'<stop offset="100%" stop-color="{esc(accent, quote=True)}" '
            'stop-opacity="0" />'
            '</radialGradient>'
        )
        if icon_uri:
            lines.append(
                f'<clipPath id="ico-clip">'
                f'<rect x="{cx - 24}" y="18" width="48" height="48"'
                f' rx="12" /></clipPath>'
            )
        lines.append("</defs>")

        # Shell
        lines.extend(_card_shell(
            w, h, rx=12, accent_fill=esc(accent, quote=True),
        ))

        # Brand icon glow
        lines.append(
            f'<circle cx="{cx}" cy="42" r="34" fill="url(#icon-glow)" />'
        )

        # Brand icon — large, centered, rounded-square clip
        if icon_uri:
            lines.append(
                f'<image href="{esc(icon_uri, quote=True)}"'
                f' x="{cx - 24}" y="18" width="48" height="48"'
                ' preserveAspectRatio="xMidYMid meet"'
                ' clip-path="url(#ico-clip)" />'
            )

        # Platform name — centered below icon
        lines.append(
            f'<text class="con-title" x="{cx}" y="96"'
            f' text-anchor="middle">'
            f"{esc(card.title, quote=True)}</text>"
        )

        lines.append("</svg>")
        return "\n".join(lines)

    def _css(self) -> str:
        lt, dk = LIGHT_THEME, DARK_THEME
        return "\n".join([
            ":root {",
            "  --card-bg: transparent;",
            f"  --card-border: {lt.border};",
            f"  --title-color: {lt.title_color};",
            f"  --text-color: {lt.text_color};",
            f"  --meta-color: {lt.meta_color};",
            f"  --accent: {lt.accent};",
            "}",
            "@media (prefers-color-scheme: dark) { :root {",
            "  --card-bg: transparent;",
            f"  --card-border: {dk.border};",
            f"  --title-color: {dk.title_color};",
            f"  --text-color: {dk.text_color};",
            f"  --meta-color: {dk.meta_color};",
            f"  --accent: {dk.accent};",
            "}}",
            f".rc-bg {{ fill: transparent; }}",
            f".rc-border {{ stroke: {lt.border}; }}",
            "@media (prefers-color-scheme: dark) {",
            f"  .rc-bg {{ fill: transparent; }}",
            f"  .rc-border {{ stroke: {dk.border}; }}",
            "}",
            f".con-title {{ fill: var(--title-color);"
            f" font: 600 14px {FONT_FAMILY}; }}",
        ])


# ---------------------------------------------------------------------------
# Asset writer and builder (public API — unchanged)
# ---------------------------------------------------------------------------


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
