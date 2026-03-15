"""Typed card contracts and adapters for README SVG generators."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

from .readme_svg import SvgCard, SvgCardFamily


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
class FeaturedMetadataChip:
    """Structured metadata chip for featured project cards."""

    label: str
    value: str


@dataclass(frozen=True)
class BlogWrapHints:
    """Wrapping and readability hints for blog cards."""

    wrap_title_with_tspan: bool = True
    title_wrap_chars: int = 48
    title_max_lines: int = 2
    wrap_lines_with_tspan: bool = True
    line_wrap_chars: int = 72
    max_lines: int = 5


@dataclass(frozen=True)
class ConnectCard(CardData):
    """Contact/connect family card contract."""

    host: Optional[str] = None
    handle: Optional[str] = None
    contact_type: Optional[str] = None
    brand_host: Optional[str] = None
    brand_icon_name: Optional[str] = None
    connect_variant: Optional[str] = None


@dataclass(frozen=True)
class FeaturedCard(CardData):
    """Featured project card contract with repo metadata."""

    repo_full_name: Optional[str] = None
    stars: Optional[int] = None
    topics: Tuple[str, ...] = ()
    homepage: Optional[str] = None
    homepage_url: Optional[str] = None
    updated_at: Optional[str] = None
    created_at: Optional[str] = None
    forks: Optional[int] = None
    language: Optional[str] = None
    size_kb: Optional[int] = None
    open_graph_image_url: Optional[str] = None
    metadata_chips: Tuple[FeaturedMetadataChip, ...] = ()
    metadata_lanes: Tuple[str, ...] = ()
    social_image_hint: Optional[str] = None


@dataclass(frozen=True)
class BlogCard(CardData):
    """Blog post card contract."""

    published: Optional[str] = None
    host: Optional[str] = None
    summary: Optional[str] = None
    hero_image: Optional[str] = None
    wrap_hints: Optional[BlogWrapHints] = None


def carddata_to_svgcard(card: CardData) -> SvgCard:
    """Map common contract fields to renderer-facing SvgCard."""
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
    from .readme_cards.connect import ConnectCardBuildInput, build_connect_card

    return build_connect_card(
        ConnectCardBuildInput(
            title=connect.title,
            kicker=connect.kicker,
            lines=tuple(connect.lines),
            meta=tuple(connect.meta),
            url=connect.url,
            background_image=connect.background_image,
            sparkline=tuple(connect.sparkline)
            if connect.sparkline is not None
            else None,
            icon=connect.icon,
            icon_data_uri=connect.icon_data_uri,
            badge=connect.badge,
            accent=connect.accent,
            host=connect.host,
            handle=connect.handle,
            contact_type=connect.contact_type,
            brand_host=connect.brand_host,
            brand_icon_name=connect.brand_icon_name,
            connect_variant=connect.connect_variant,
        )
    )


def featured_to_svg(featured: FeaturedCard) -> SvgCard:
    svg = carddata_to_svgcard(featured)
    metadata_chips = tuple(
        {"label": chip.label, "value": chip.value} for chip in featured.metadata_chips
    )
    metadata_lanes = tuple(featured.metadata_lanes or featured.meta)

    object.__setattr__(svg, "family", SvgCardFamily.FEATURED.value)
    object.__setattr__(svg, "repo_full_name", featured.repo_full_name)
    object.__setattr__(svg, "stars", featured.stars)
    object.__setattr__(svg, "topics", tuple(featured.topics))
    object.__setattr__(svg, "homepage", featured.homepage)
    object.__setattr__(svg, "homepage_url", featured.homepage_url)
    object.__setattr__(svg, "updated_at", featured.updated_at)
    object.__setattr__(svg, "created_at", featured.created_at)
    object.__setattr__(svg, "forks", featured.forks)
    object.__setattr__(svg, "language", featured.language)
    object.__setattr__(svg, "size_kb", featured.size_kb)
    object.__setattr__(svg, "open_graph_image_url", featured.open_graph_image_url)
    object.__setattr__(svg, "metadata_chips", metadata_chips)
    object.__setattr__(svg, "metadata_lanes", metadata_lanes)
    object.__setattr__(svg, "metadata_rows", metadata_lanes)
    object.__setattr__(svg, "social_image_hint", featured.social_image_hint)
    return svg


def blog_to_svg(blog: BlogCard) -> SvgCard:
    svg = carddata_to_svgcard(blog)
    if blog.hero_image and not svg.background_image:
        object.__setattr__(svg, "background_image", blog.hero_image)
    object.__setattr__(svg, "family", SvgCardFamily.BLOG.value)
    object.__setattr__(svg, "published", blog.published)
    object.__setattr__(svg, "host", blog.host)
    object.__setattr__(svg, "summary", blog.summary)
    object.__setattr__(svg, "hero_image", blog.hero_image or svg.background_image)
    if blog.wrap_hints is not None:
        object.__setattr__(
            svg, "wrap_title_with_tspan", blog.wrap_hints.wrap_title_with_tspan
        )
        object.__setattr__(svg, "title_wrap_chars", blog.wrap_hints.title_wrap_chars)
        object.__setattr__(svg, "title_max_lines", blog.wrap_hints.title_max_lines)
        object.__setattr__(
            svg, "wrap_lines_with_tspan", blog.wrap_hints.wrap_lines_with_tspan
        )
        object.__setattr__(svg, "line_wrap_chars", blog.wrap_hints.line_wrap_chars)
        object.__setattr__(svg, "max_lines", blog.wrap_hints.max_lines)
    return svg
