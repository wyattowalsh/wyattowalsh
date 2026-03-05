"""Dedicated featured README card builder helpers."""

from __future__ import annotations

import base64
import re
from dataclasses import dataclass
from datetime import datetime
from html import escape
from typing import Optional, Sequence
from urllib.parse import urlparse

from ..readme_card_types import FeaturedCard, FeaturedMetadataChip


@dataclass(frozen=True)
class FeaturedRepoSnapshot:
    """Typed featured repo metadata used for card composition."""

    full_name: str
    name: str
    html_url: str
    description: Optional[str]
    stars: int
    homepage: Optional[str] = None
    topics: tuple[str, ...] = ()
    updated_at: Optional[str] = None
    created_at: Optional[str] = None
    forks: Optional[int] = None
    language: Optional[str] = None
    size_kb: Optional[int] = None
    open_graph_image_url: Optional[str] = None


@dataclass(frozen=True)
class FeaturedCardHints:
    """Optional deterministic composition hints for featured cards."""

    hero_image: Optional[str] = None
    social_image_hint: Optional[str] = None
    sparkline: Optional[tuple[float, ...]] = None
    icon_data_uri: Optional[str] = None
    accent: Optional[str] = None


@dataclass(frozen=True)
class FeaturedCardBuilder:
    """Builder that creates fully-typed featured cards and metadata lanes."""

    fallback_lines: tuple[str, str] = (
        "Live stats are temporarily unavailable.",
        "Open the repository for full details.",
    )
    default_accent: str = "60A5FA"

    def build(
        self,
        repo_full_name: str,
        metadata: Optional[FeaturedRepoSnapshot],
        hints: Optional[FeaturedCardHints] = None,
    ) -> FeaturedCard:
        """Build a featured card compatible with existing renderer assumptions."""
        resolved_hints = hints or FeaturedCardHints()
        if metadata is None:
            return self._build_fallback_card(repo_full_name, resolved_hints)
        return self._build_metadata_card(metadata, resolved_hints)

    def _build_fallback_card(
        self,
        repo_full_name: str,
        hints: FeaturedCardHints,
    ) -> FeaturedCard:
        repo_name = repo_full_name.split("/")[-1]
        repo_url = f"https://github.com/{repo_full_name}"
        accent = hints.accent or self.default_accent
        fallback_chips = (
            FeaturedMetadataChip(label="Status", value="Fallback"),
            FeaturedMetadataChip(label="Source", value="GitHub"),
        )
        fallback_lanes = (
            "Live stats unavailable · API metadata missing",
            "Open the repository for stars, forks, and activity",
        )
        hero_image = (
            hints.hero_image
            or self.build_featured_background_fallback_data_uri(
                repo_full_name,
                accent,
            )
        )
        return FeaturedCard(
            title=repo_name,
            kicker=repo_full_name,
            lines=self.fallback_lines,
            meta=fallback_lanes,
            url=repo_url,
            background_image=hero_image,
            sparkline=tuple(hints.sparkline) if hints.sparkline is not None else None,
            icon=repo_name[:2].upper(),
            icon_data_uri=hints.icon_data_uri,
            badge="Featured",
            accent=accent,
            repo_full_name=repo_full_name,
            metadata_chips=fallback_chips,
            metadata_lanes=fallback_lanes,
            social_image_hint=hints.social_image_hint or hero_image,
        )

    def _build_metadata_card(
        self,
        metadata: FeaturedRepoSnapshot,
        hints: FeaturedCardHints,
    ) -> FeaturedCard:
        metadata_chips = self.build_featured_metadata_chips(metadata)
        metadata_lanes = self.build_featured_metadata_lanes(metadata_chips)
        accent = hints.accent or self.repo_accent_color(metadata)
        hero_image = hints.hero_image or metadata.open_graph_image_url
        if not hero_image:
            hero_image = self.build_featured_background_fallback_data_uri(
                metadata.full_name,
                accent,
            )
        social_image_hint = (
            hints.social_image_hint or metadata.open_graph_image_url or hero_image
        )
        description = metadata.description or "No description provided."
        return FeaturedCard(
            title=metadata.name,
            kicker=metadata.full_name,
            lines=(description,),
            meta=metadata_lanes,
            url=metadata.html_url,
            background_image=hero_image,
            sparkline=tuple(hints.sparkline) if hints.sparkline is not None else None,
            icon=metadata.name[:2].upper(),
            icon_data_uri=hints.icon_data_uri,
            badge="Showcase",
            accent=accent,
            repo_full_name=metadata.full_name,
            stars=metadata.stars,
            topics=tuple(metadata.topics),
            homepage=self._homepage_display(metadata.homepage),
            homepage_url=metadata.homepage,
            updated_at=metadata.updated_at,
            created_at=metadata.created_at,
            forks=metadata.forks,
            language=metadata.language,
            size_kb=metadata.size_kb,
            open_graph_image_url=metadata.open_graph_image_url,
            metadata_chips=metadata_chips,
            metadata_lanes=metadata_lanes,
            social_image_hint=social_image_hint,
        )

    @staticmethod
    def _homepage_display(homepage: Optional[str]) -> Optional[str]:
        if not homepage:
            return None
        return urlparse(homepage).netloc.replace("www.", "") or homepage

    def build_featured_metadata_chips(
        self,
        metadata: FeaturedRepoSnapshot,
    ) -> tuple[FeaturedMetadataChip, ...]:
        """Build rich, typed chips for featured card metadata."""
        language = metadata.language or (
            metadata.topics[0].title() if metadata.topics else None
        )
        chips: list[FeaturedMetadataChip] = [
            FeaturedMetadataChip(label="Stars", value=f"{metadata.stars:,}")
        ]
        if metadata.forks is not None:
            chips.append(
                FeaturedMetadataChip(
                    label="Forks",
                    value=f"{metadata.forks:,}",
                )
            )
        if language:
            chips.append(FeaturedMetadataChip(label="Language", value=language))
        size_label = self.format_repo_size(metadata.size_kb)
        if size_label:
            chips.append(FeaturedMetadataChip(label="Size", value=size_label))
        lifespan_label = self.format_repo_lifespan(
            metadata.created_at,
            metadata.updated_at,
        )
        if lifespan_label:
            chips.append(FeaturedMetadataChip(label="Lifespan", value=lifespan_label))
        return tuple(chips)

    def build_featured_metadata_lanes(
        self,
        chips: Sequence[FeaturedMetadataChip],
    ) -> tuple[str, ...]:
        """Build concise metadata lanes from structured chips."""
        display_tokens: list[str] = []
        for chip in chips:
            label = chip.label.strip().lower()
            value = chip.value.strip()
            if not value:
                continue
            if label == "stars":
                display_tokens.append(f"★ {value}")
            elif label == "forks":
                display_tokens.append(f"Forks {value}")
            elif label == "language":
                display_tokens.append(value)
            elif label == "size":
                display_tokens.append(value)
            elif label == "lifespan":
                display_tokens.append(f"Life {value}")
            else:
                display_tokens.append(f"{chip.label.strip()} {value}".strip())
        if not display_tokens:
            return ()
        primary = " · ".join(display_tokens[:3])
        secondary = " · ".join(display_tokens[3:6]) if len(display_tokens) > 3 else ""
        return tuple(bit for bit in (primary, secondary) if bit)

    @staticmethod
    def format_repo_size(size_kb: Optional[int]) -> Optional[str]:
        """Format repository size for human-friendly display."""
        if size_kb is None or size_kb <= 0:
            return None
        if size_kb >= 1024 * 1024:
            return f"{size_kb / (1024 * 1024):.1f} GB"
        if size_kb >= 1024:
            return f"{size_kb / 1024:.1f} MB"
        return f"{size_kb:,} KB"

    def format_repo_lifespan(
        self,
        created_at: Optional[str],
        updated_at: Optional[str],
    ) -> Optional[str]:
        """Build a lifespan token for metadata chips and lanes."""
        created_dt = self.parse_timestamp(created_at)
        updated_dt = self.parse_timestamp(updated_at)
        if created_dt is None:
            return None
        if updated_dt is None:
            updated_dt = created_dt
        delta_days = (updated_dt.date() - created_dt.date()).days
        if delta_days < 0:
            return None
        if delta_days == 0:
            return "1d"
        years, remainder = divmod(delta_days, 365)
        months = remainder // 30
        if years and months:
            return f"{years}y {months}m"
        if years:
            return f"{years}y"
        if months:
            return f"{months}m"
        weeks = delta_days // 7
        if weeks:
            return f"{weeks}w"
        return f"{delta_days}d"

    @staticmethod
    def parse_timestamp(timestamp: Optional[str]) -> Optional[datetime]:
        """Parse ISO timestamps with optional trailing Z."""
        if not timestamp:
            return None
        normalized = timestamp.strip()
        if normalized.endswith("Z"):
            normalized = f"{normalized[:-1]}+00:00"
        candidates = [normalized]
        if "T" in normalized:
            candidates.append(normalized.split("T", maxsplit=1)[0])
        for candidate in candidates:
            try:
                return datetime.fromisoformat(candidate)
            except ValueError:
                continue
        return None

    @staticmethod
    def repo_accent_color(metadata: FeaturedRepoSnapshot) -> str:
        """Infer deterministic accent colors from topic keywords."""
        joined_topics = " ".join(topic.lower() for topic in metadata.topics)
        if "python" in joined_topics:
            return "3776AB"
        if "typescript" in joined_topics or "javascript" in joined_topics:
            return "3178C6"
        if "ai" in joined_topics or "ml" in joined_topics:
            return "8B5CF6"
        return "60A5FA"

    @staticmethod
    def build_featured_background_fallback_data_uri(
        repo_full_name: str,
        accent: str,
    ) -> str:
        """Generate a deterministic, transparency-friendly fallback hero image."""
        normalized_accent = (
            accent.lstrip("#")
            if re.fullmatch(r"#?[0-9A-Fa-f]{6}", accent.strip())
            else "60A5FA"
        )
        repo_label = escape(repo_full_name.split("/")[-1][:24], quote=True)
        svg_markup = (
            "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1200 220'>"
            "<defs>"
            "<linearGradient id='bg' x1='0%' y1='0%' x2='100%' y2='100%'>"
            "<stop offset='0%' stop-color='#0B111A'/>"
            f"<stop offset='100%' stop-color='#{normalized_accent}' stop-opacity='0.36'/>"
            "</linearGradient>"
            "<radialGradient id='glow' cx='82%' cy='20%' r='60%'>"
            f"<stop offset='0%' stop-color='#{normalized_accent}' stop-opacity='0.38'/>"
            "<stop offset='100%' stop-color='#0B111A' stop-opacity='0'/>"
            "</radialGradient>"
            "</defs>"
            "<rect width='1200' height='220' fill='url(#bg)'/>"
            "<rect width='1200' height='220' fill='url(#glow)'/>"
            f"<text x='28' y='40' fill='#{normalized_accent}' opacity='0.32' "
            "font-size='20' font-family='ui-sans-serif' font-weight='700'>"
            f"{repo_label}"
            "</text>"
            "</svg>"
        )
        return "data:image/svg+xml;base64," + base64.b64encode(
            svg_markup.encode("utf-8")
        ).decode("ascii")


def build_featured_card(
    repo_full_name: str,
    metadata: Optional[FeaturedRepoSnapshot],
    hints: Optional[FeaturedCardHints] = None,
) -> FeaturedCard:
    """Convenience API for building a featured card with defaults."""
    return FeaturedCardBuilder().build(repo_full_name, metadata, hints)


__all__ = [
    "FeaturedCardBuilder",
    "FeaturedCardHints",
    "FeaturedRepoSnapshot",
    "build_featured_card",
]
