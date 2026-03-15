"""Dedicated connect-card builder primitives."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

from ..readme_svg import SvgCard, SvgCardFamily

GH_CARD_CONNECT_VARIANT = "gh-card"
CONNECT_SHELL_CLASS = "connect-card-shell"
CONNECT_BRAND_LOCKUP_CLASS = "connect-brand-lockup"
CONNECT_ACCENT_GLOW_VAR = "--connect-accent-glow"


@dataclass(frozen=True)
class ConnectCardBuildInput:
    """Typed connect-card input contract for SVG composition."""

    title: str
    kicker: Optional[str] = None
    lines: Tuple[str, ...] = ()
    meta: Tuple[str, ...] = ()
    url: Optional[str] = None
    background_image: Optional[str] = None
    sparkline: Optional[Tuple[float, ...]] = None
    icon: Optional[str] = None
    icon_data_uri: Optional[str] = None
    badge: Optional[str] = None
    accent: Optional[str] = None
    host: Optional[str] = None
    handle: Optional[str] = None
    contact_type: Optional[str] = None
    brand_host: Optional[str] = None
    brand_icon_name: Optional[str] = None
    connect_variant: Optional[str] = None
    show_title: bool = False
    transparent_canvas: bool = True
    connect_shell_class: str = CONNECT_SHELL_CLASS
    connect_brand_lockup_class: str = CONNECT_BRAND_LOCKUP_CLASS
    connect_accent_glow_var: str = CONNECT_ACCENT_GLOW_VAR


def build_connect_card(card: ConnectCardBuildInput) -> SvgCard:
    """Build an SVG card with connect-family and composition metadata."""

    svg = SvgCard(
        title=card.title,
        kicker=card.kicker,
        lines=tuple(card.lines),
        meta=tuple(card.meta),
        url=card.url,
        background_image=card.background_image,
        sparkline=tuple(card.sparkline) if card.sparkline is not None else None,
        icon=card.icon,
        icon_data_uri=card.icon_data_uri,
        badge=card.badge,
        accent=card.accent,
    )
    object.__setattr__(svg, "family", SvgCardFamily.CONNECT.value)
    object.__setattr__(svg, "host", card.host)
    object.__setattr__(svg, "handle", card.handle)
    object.__setattr__(svg, "contact_type", card.contact_type)
    object.__setattr__(svg, "brand_host", card.brand_host or card.host)
    object.__setattr__(svg, "brand_icon_name", card.brand_icon_name)
    object.__setattr__(
        svg,
        "connect_variant",
        card.connect_variant or GH_CARD_CONNECT_VARIANT,
    )
    object.__setattr__(svg, "show_title", card.show_title)
    object.__setattr__(svg, "transparent_canvas", card.transparent_canvas)
    object.__setattr__(svg, "connect_shell_class", card.connect_shell_class)
    object.__setattr__(
        svg,
        "connect_brand_lockup_class",
        card.connect_brand_lockup_class,
    )
    object.__setattr__(svg, "connect_accent_glow_var", card.connect_accent_glow_var)
    return svg
