"""Card data contracts and adapters for README SVG generators.

This lightweight module defines family-specific input dataclasses (ConnectCard,
FeaturedCard, BlogCard) and a common CardData base. It provides adapter helpers
that produce presentation SvgCard instances consumed by the existing
SvgBlockRenderer. This file is intentionally implementation-ready and does
not change existing behaviour until generators switch to these types.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple, List

from .readme_svg import SvgCard


@dataclass(frozen=True)
class CardData:
    """Common, renderer-agnostic card data contract."""

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


@dataclass(frozen=True)
class ConnectCard(CardData):
    """Contact/connect family card contract."""

    # e.g. social provider host (github.com), handle, contact_type (email, social)
    host: Optional[str] = None
    handle: Optional[str] = None
    contact_type: Optional[str] = None


@dataclass(frozen=True)
class FeaturedCard(CardData):
    """Featured project card contract with repo metadata."""

    repo_full_name: Optional[str] = None
    stars: Optional[int] = None
    topics: Tuple[str, ...] = ()
    homepage: Optional[str] = None
    updated_at: Optional[str] = None
    open_graph_image_url: Optional[str] = None


@dataclass(frozen=True)
class BlogCard(CardData):
    """Blog post card contract."""

    published: Optional[str] = None
    host: Optional[str] = None
    summary: Optional[str] = None
    hero_image: Optional[str] = None


# Adapters: convert CardData (or family specific) into presentation SvgCard

def carddata_to_svgcard(card: CardData) -> SvgCard:
    """Map CardData -> SvgCard for rendering.

    This is intentionally conservative: it preserves existing field names and
    delegates trimming / truncation to the renderer.
    """
    return SvgCard(
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


def connect_to_svg(connect: ConnectCard) -> SvgCard:
    return carddata_to_svgcard(connect)


def featured_to_svg(featured: FeaturedCard) -> SvgCard:
    return carddata_to_svgcard(featured)


def blog_to_svg(blog: BlogCard) -> SvgCard:
    return carddata_to_svgcard(blog)
