"""Typed blog card builder for README SVG card composition."""

from __future__ import annotations

import ipaddress
import re
from dataclasses import dataclass, field
from typing import Mapping
from urllib.parse import urljoin, urlparse

from ..readme_card_types import BlogCard, BlogWrapHints, blog_to_svg
from ..readme_svg import SvgCard


def _default_wrap_hints() -> BlogWrapHints:
    return BlogWrapHints(
        wrap_title_with_tspan=True,
        title_wrap_chars=48,
        title_max_lines=2,
        wrap_lines_with_tspan=True,
        line_wrap_chars=72,
        max_lines=5,
    )


def _is_public_remote_host(host: str) -> bool:
    normalized_host = host.strip().lower().rstrip(".")
    if not normalized_host:
        return False
    if normalized_host in {"localhost", "localhost.localdomain"}:
        return False
    if normalized_host.endswith(
        (
            ".local",
            ".localdomain",
            ".internal",
            ".intranet",
            ".lan",
            ".home",
            ".corp",
        )
    ):
        return False

    try:
        ip = ipaddress.ip_address(normalized_host)
    except ValueError:
        return "." in normalized_host

    return not (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
    )


def is_safe_remote_url(url: str) -> bool:
    """Return True when URL is a public HTTP(S) URL safe for card media."""
    try:
        parsed = urlparse(url)
    except ValueError:
        return False
    if parsed.scheme.lower() not in {"http", "https"}:
        return False
    if parsed.hostname is None:
        return False
    return _is_public_remote_host(parsed.hostname)


@dataclass(frozen=True)
class BlogCardPost:
    """Typed source post payload for blog card composition."""

    title: str
    url: str


@dataclass(frozen=True)
class BlogCardMetadata:
    """Typed source metadata payload for blog card composition."""

    summary: str | None = None
    published: str | None = None
    host: str | None = None
    hero_image: str | None = None


def metadata_from_mapping(
    payload: Mapping[str, object] | None,
) -> BlogCardMetadata:
    """Adapt mapping payloads into strongly typed blog metadata."""
    if payload is None:
        return BlogCardMetadata()

    def _coerce_optional_text(value: object) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    return BlogCardMetadata(
        summary=_coerce_optional_text(payload.get("summary")),
        published=_coerce_optional_text(payload.get("published")),
        host=_coerce_optional_text(payload.get("host")),
        hero_image=_coerce_optional_text(payload.get("hero_image")),
    )


@dataclass(frozen=True)
class BlogCardBuilder:
    """Composable builder preserving current README blog card assumptions."""

    default_summary: str = "Tap to read the full story."
    untitled_fallback: str = "Untitled post"
    summary_line_width: int = 72
    summary_max_lines: int = 2
    preferred_host: str = "w4w.dev"
    preferred_host_accent: str = "F59E0B"
    default_accent: str = "F97316"
    wrap_hints: BlogWrapHints = field(default_factory=_default_wrap_hints)

    def normalize_primary_copy(self, value: str | None) -> str:
        """Normalize post title/summary copy for readability and consistency."""
        cleaned = re.sub(r"\.{2,}|[…]", "", value or "")
        cleaned = re.sub(r"\bupdate\b", "", cleaned, flags=re.IGNORECASE)
        return re.sub(r"\s+", " ", cleaned).strip()

    def wrap_copy_lines(
        self,
        value: str,
        *,
        line_width: int | None = None,
        max_lines: int | None = None,
    ) -> tuple[str, ...]:
        """Wrap copy into deterministic line chunks without forced ellipsis."""
        width = line_width if line_width is not None else self.summary_line_width
        limit = max_lines if max_lines is not None else self.summary_max_lines
        if not value:
            return ()
        words = value.split()
        if not words:
            return ()
        normalized_words: list[str] = []
        for word in words:
            if len(word) <= width:
                normalized_words.append(word)
                continue
            normalized_words.extend(
                word[index : index + width] for index in range(0, len(word), width)
            )
        lines: list[str] = []
        current = ""
        for word in normalized_words:
            candidate = word if not current else f"{current} {word}"
            if len(candidate) <= width or not current:
                current = candidate
                continue
            lines.append(current)
            if len(lines) >= limit:
                break
            current = word
        if len(lines) < limit and current:
            lines.append(current)
        wrapped = lines[:limit]
        if len(wrapped) > 1 and len(wrapped[-1].split()) == 1:
            previous = wrapped[-2]
            orphan = wrapped[-1]
            if len(previous) + len(orphan) + 1 <= width:
                wrapped[-2] = f"{previous} {orphan}"
                wrapped.pop()
        return tuple(wrapped)

    def resolve_hero_image(self, *, post_url: str, hero_image: str | None) -> str | None:
        """Resolve hero image URLs while enforcing safe remote URL constraints."""
        if not hero_image:
            return None
        candidate = hero_image.strip()
        if not candidate:
            return None
        if candidate.startswith("//"):
            candidate = f"https:{candidate}"
        elif candidate.startswith("/"):
            candidate = urljoin(post_url, candidate)
        elif not urlparse(candidate).scheme:
            candidate = urljoin(post_url, candidate)
        if is_safe_remote_url(candidate):
            return candidate
        return None

    def build_card(self, *, post: BlogCardPost, metadata: BlogCardMetadata) -> BlogCard:
        """Build a clutter-free blog card contract with hero-first media hints."""
        host = metadata.host or urlparse(post.url).netloc.replace("www.", "")
        title = self.normalize_primary_copy(post.title) or self.untitled_fallback
        summary_copy = self.normalize_primary_copy(metadata.summary or self.default_summary)
        body_lines = self.wrap_copy_lines(summary_copy)
        if not body_lines:
            body_lines = (self.default_summary,)
        card_meta: list[str] = []
        if host:
            card_meta.append(host)
        if metadata.published:
            card_meta.append(f"Published {metadata.published[:10]}")
        accent = (
            self.preferred_host_accent
            if self.preferred_host in (host or "")
            else self.default_accent
        )
        resolved_hero_image = self.resolve_hero_image(
            post_url=post.url,
            hero_image=metadata.hero_image,
        )
        return BlogCard(
            title=title,
            kicker=None,
            lines=body_lines,
            meta=tuple(card_meta),
            url=post.url,
            background_image=resolved_hero_image,
            icon=(host or "BL")[:2].upper(),
            badge=None,
            accent=accent,
            published=metadata.published,
            host=host,
            summary=summary_copy,
            hero_image=resolved_hero_image,
            wrap_hints=self.wrap_hints,
        )

    def build_svg_card(self, *, post: BlogCardPost, metadata: BlogCardMetadata) -> SvgCard:
        """Compose blog card payload and adapt to the renderer-facing SvgCard."""
        return blog_to_svg(self.build_card(post=post, metadata=metadata))

