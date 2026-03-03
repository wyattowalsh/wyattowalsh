"""README dynamic section generator (badges, projects, and blog posts)."""

import base64
import ipaddress
import json
import os
import re
from dataclasses import dataclass
from html import escape
from pathlib import Path
from typing import Optional, Sequence
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen
from xml.etree import ElementTree

from .config import ReadmeSectionsSettings
from .readme_svg import (
    ReadmeSvgAssetBuilder,
    SvgBlock,
    SvgBlockRenderer,
    SvgCard,
)
from .utils import get_logger

logger = get_logger(module=__name__)


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


def _is_safe_remote_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
    except ValueError:
        return False
    if parsed.scheme.lower() not in {"http", "https"}:
        return False
    if parsed.hostname is None:
        return False
    return _is_public_remote_host(parsed.hostname)


def _build_remote_get_request(
    *,
    url: str,
    headers: dict[str, str],
    context: str,
) -> Optional[Request]:
    if not _is_safe_remote_url(url):
        logger.warning(f"Blocked unsafe URL for {context}: {url}")
        return None
    return Request(url=url, headers=headers, method="GET")


@dataclass(frozen=True)
class RepoMetadata:
    """Repository metadata fetched from the GitHub API."""

    full_name: str
    name: str
    html_url: str
    description: Optional[str]
    stars: int
    homepage: Optional[str]
    topics: list[str]
    updated_at: Optional[str]
    # additional metadata exposed for featured cards
    created_at: Optional[str] = None
    size_kb: Optional[int] = None
    forks: Optional[int] = None
    open_graph_image_url: Optional[str] = None


@dataclass(frozen=True)
class BlogPost:
    """A single blog post item from RSS/Atom."""

    title: str
    url: str


class GitHubRepoClient:
    """Simple GitHub API client for repository metadata."""

    def __init__(self, timeout: float = 10.0) -> None:
        self.timeout = timeout

    def fetch_repo_metadata(self, full_name: str) -> Optional[RepoMetadata]:
        """Fetch metadata for owner/repo from GitHub REST API."""
        request = _build_remote_get_request(
            url=f"https://api.github.com/repos/{full_name}",
            headers=self._headers(),
            context=f"repo metadata for {full_name}",
        )
        if request is None:
            return None
        try:
            with urlopen(request, timeout=self.timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except Exception as exc:  # pragma: no cover - network path
            logger.warning(
                f"Failed to fetch repo metadata for {full_name}: {exc}"
            )
            return None

        return RepoMetadata(
            full_name=payload.get("full_name", full_name),
            name=payload.get("name", full_name.split("/")[-1]),
            html_url=payload.get("html_url", f"https://github.com/{full_name}"),
            description=payload.get("description"),
            stars=int(payload.get("stargazers_count", 0)),
            homepage=payload.get("homepage") or None,
            topics=list(payload.get("topics", [])),
            updated_at=payload.get("pushed_at") or payload.get("updated_at"),
            created_at=payload.get("created_at") or None,
            size_kb=int(payload.get("size", 0)) if payload.get("size") is not None else None,
            forks=int(payload.get("forks_count", 0)) if payload.get("forks_count") is not None else None,
            open_graph_image_url=payload.get("open_graph_image_url") or None,
        )

    def _headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "readme-section-generator",
        }
        token = os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN")
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers


class BlogFeedClient:
    """Fetches latest blog posts from RSS/Atom feeds."""

    def __init__(self, timeout: float = 10.0) -> None:
        self.timeout = timeout

    def fetch_latest_posts(self, feed_url: str, limit: int) -> list[BlogPost]:
        """Fetch latest posts from feed URL."""
        request = _build_remote_get_request(
            url=feed_url,
            headers={"User-Agent": "readme-section-generator"},
            context="blog feed fetch",
        )
        if request is None:
            return []
        try:
            with urlopen(request, timeout=self.timeout) as response:
                body = response.read()
        except Exception as exc:  # pragma: no cover - network path
            logger.warning(f"Failed to fetch blog feed {feed_url}: {exc}")
            return []

        try:
            root = ElementTree.fromstring(body)
        except ElementTree.ParseError as exc:
            logger.warning(f"Invalid blog feed XML from {feed_url}: {exc}")
            return []

        posts = self._parse_rss_items(root)
        if not posts:
            posts = self._parse_atom_entries(root)
        return posts[:limit]

    def _parse_rss_items(self, root: ElementTree.Element) -> list[BlogPost]:
        posts: list[BlogPost] = []
        for item in root.findall(".//item"):
            title = (item.findtext("title") or "").strip()
            link = (item.findtext("link") or "").strip()
            if title and link:
                posts.append(BlogPost(title=title, url=link))
        return posts

    def _parse_atom_entries(self, root: ElementTree.Element) -> list[BlogPost]:
        posts: list[BlogPost] = []
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        for entry in root.findall(".//atom:entry", ns):
            title = (
                entry.findtext("atom:title", default="", namespaces=ns) or ""
            ).strip()
            link_elem = entry.find("atom:link[@rel='alternate']", ns)
            if link_elem is None:
                link_elem = entry.find("atom:link", ns)
            link = (link_elem.get("href") if link_elem is not None else "") or ""
            link = link.strip()
            if title and link:
                posts.append(BlogPost(title=title, url=link))
        return posts


class StarHistoryClient:
    """Fetch stargazer timestamps for sparkline generation."""

    def __init__(self, timeout: float = 10.0) -> None:
        self.timeout = timeout

    def fetch_star_history(
        self,
        full_name: str,
        sample: int = 24,
    ) -> Optional[list[int]]:
        """Return cumulative star counts sampled to the requested length."""
        request = _build_remote_get_request(
            url=f"https://api.github.com/repos/{full_name}/stargazers?per_page=100",
            headers=self._headers(),
            context=f"star history for {full_name}",
        )
        if request is None:
            return None
        try:
            with urlopen(request, timeout=self.timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except Exception as exc:  # pragma: no cover - network path
            logger.warning(
                "Failed to fetch star history for %s: %s", full_name, exc
            )
            return None

        if not isinstance(payload, list) or not payload:
            return None

        counts = list(range(1, len(payload) + 1))
        if len(counts) <= sample:
            return counts
        step = len(counts) / sample
        sampled: list[int] = []
        for idx in range(sample):
            pos = min(int(round(idx * step)), len(counts) - 1)
            sampled.append(counts[pos])
        return sampled

    def _headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/vnd.github.star+json",
            "User-Agent": "readme-section-generator",
        }
        token = os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN")
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers


class BlogMetadataClient:
    """Resolve hero imagery and descriptions for blog posts."""

    def __init__(self, timeout: float = 10.0) -> None:
        self.timeout = timeout

    def fetch_metadata(self, url: str) -> dict[str, Optional[str]]:
        parsed_host = urlparse(url).netloc.replace("www.", "") or None
        fallback = {
            "hero_image": None,
            "summary": None,
            "published": None,
            "host": parsed_host,
        }
        request = _build_remote_get_request(
            url=url,
            headers={"User-Agent": "readme-section-generator"},
            context="blog metadata fetch",
        )
        if request is None:
            return fallback
        try:
            with urlopen(request, timeout=self.timeout) as response:
                html = response.read().decode("utf-8", errors="ignore")
        except Exception as exc:  # pragma: no cover - network path
            logger.warning("Failed to fetch blog metadata for %s: %s", url, exc)
            return fallback

        hero = self._extract_meta(
            html,
            (
                ("property", "og:image"),
                ("name", "twitter:image"),
            ),
        )
        summary = self._extract_meta(
            html,
            (
                ("property", "og:description"),
                ("name", "description"),
            ),
        )
        published = self._extract_meta(
            html,
            (
                ("property", "article:published_time"),
                ("name", "date"),
            ),
        )
        host = urlparse(url).netloc.replace("www.", "")
        return {
            "hero_image": hero,
            "summary": summary,
            "published": published,
            "host": host or None,
        }

    def _extract_meta(
        self,
        html: str,
        candidates: tuple[tuple[str, str], ...],
    ) -> Optional[str]:
        for attr, value in candidates:
            regex = re.compile(
                rf'<meta[^>]+{attr}\s*=\s*["\']{value}["\'][^>]*content\s*=\s*["\']([^"\']+)["\']',
                flags=re.IGNORECASE,
            )
            match = regex.search(html)
            if match:
                return match.group(1).strip()
        return None

class ReadmeSectionGenerator:
    """Renders and injects dynamic README sections between markers."""

    TOP_BADGES_START = "<!-- README:TOP_BADGES:START -->"
    TOP_BADGES_END = "<!-- README:TOP_BADGES:END -->"
    FEATURED_START = "<!-- README:FEATURED_PROJECTS:START -->"
    FEATURED_END = "<!-- README:FEATURED_PROJECTS:END -->"
    BLOG_START = "<!-- README:BLOG_POSTS:START -->"
    BLOG_END = "<!-- README:BLOG_POSTS:END -->"

    def __init__(
        self,
        settings: ReadmeSectionsSettings,
        repo_client: Optional[GitHubRepoClient] = None,
        blog_client: Optional[BlogFeedClient] = None,
        star_history_client: Optional[StarHistoryClient] = None,
        blog_metadata_client: Optional[BlogMetadataClient] = None,
    ) -> None:
        self.settings = settings
        self.repo_client = repo_client or GitHubRepoClient()
        self.blog_client = blog_client or BlogFeedClient()
        self.star_history_client = star_history_client or StarHistoryClient()
        self.blog_metadata_client = blog_metadata_client or BlogMetadataClient()
        self.svg_builder: Optional[ReadmeSvgAssetBuilder] = None
        if self.settings.svg.enabled:
            self.svg_builder = ReadmeSvgAssetBuilder(
                output_dir=self.settings.svg.output_dir
            )

    def generate(self) -> Path:
        """Render dynamic sections and inject them into README."""
        readme_path = Path(self.settings.readme_path)
        if not readme_path.exists():
            logger.warning(f"README not found at {readme_path}, skipping injection")
            return readme_path

        content = readme_path.read_text(encoding="utf-8")
        content = self._inject_block(
            content,
            self.TOP_BADGES_START,
            self.TOP_BADGES_END,
            self._render_top_badges(),
        )
        content = self._inject_block(
            content,
            self.FEATURED_START,
            self.FEATURED_END,
            self._render_featured_projects(),
        )
        content = self._inject_block(
            content,
            self.BLOG_START,
            self.BLOG_END,
            self._render_blog_posts(),
        )
        readme_path.write_text(content, encoding="utf-8")
        return readme_path

    def _inject_block(
        self,
        content: str,
        marker_start: str,
        marker_end: str,
        rendered: str,
    ) -> str:
        pattern = re.compile(
            rf"{re.escape(marker_start)}\n.*?{re.escape(marker_end)}",
            re.DOTALL,
        )
        match = pattern.search(content)
        if not match:
            logger.warning(
                f"Markers not found for section {marker_start} .. {marker_end}"
            )
            return content
        replacement = f"{marker_start}\n{rendered}\n{marker_end}"
        return content[: match.start()] + replacement + content[match.end() :]

    def _render_top_badges(self) -> str:
        svg_cards: list[SvgCard] = []
        for link in self.settings.social_links:
            parsed = urlparse(link.url)
            host = parsed.netloc.replace("www.", "")
            handle = parsed.path.strip("/").split("/")[-1] if parsed.path else ""
            # For connect cards we avoid exposing raw profile handles/URLs in the visible lines.
            # Keep kicker minimal and expose a small personality meta/badge instead.
            meta_line = self._social_personality_badge(link.url)
            card = SvgCard(
                title=link.label,
                kicker=None,
                lines=(),
                meta=(meta_line,),
                url=link.url,
                icon=self._social_icon(link.label),
                badge=self._social_personality_badge(link.url),
                accent=link.color,
            )
            # populate icon payloads (brand glyph or data-uri)
            self._set_card_icon_data_uri(
                card,
                url=link.url,
                host=host,
                label=link.label,
                accent=link.color,
            )
            svg_cards.append(card)
        columns = min(4, max(1, len(svg_cards))) if svg_cards else 1
        block = SvgBlock(
            title="Connect & Contact",
            cards=tuple(svg_cards) or (SvgCard(title="No social links configured."),),
            columns=columns,
        )
        renderer = SvgBlockRenderer(width=1100, card_height=140, padding=24)
        svg_embed = self._render_svg_embed(
            section_flag="top_contact",
            asset_name="top-contact",
            block=block,
            renderer=renderer,
            alt_text="Connect and contact cards",
        )
        social_links = " · ".join(
            f"[{escape(link.label)}]({escape(link.url)})"
            for link in self.settings.social_links
        )
        lines: list[str] = []
        if svg_embed:
            lines.append(f'<p align="center">{svg_embed}</p>')
        if social_links:
            lines.append(social_links)
        return "\n".join(lines)

    def _social_icon(self, label: str) -> str:
        cleaned = "".join(ch for ch in label.upper() if ch.isalnum())
        if len(cleaned) >= 2:
            return cleaned[:2]
        return (cleaned or "•").ljust(2, "•")

    def _social_personality_badge(self, url: str) -> str:
        parsed = urlparse(url)
        host = parsed.netloc.replace("www.", "").lower()
        if parsed.scheme == "mailto":
            return "Email"
        if "github.com" in host:
            return "Builder"
        if "linkedin.com" in host:
            return "Network"
        if "kaggle.com" in host:
            return "Data"
        if "x.com" in host or "twitter.com" in host:
            return "Broadcast"
        return "Link"

    def _social_kicker(self, url: str) -> str:
        parsed = urlparse(url)
        if parsed.scheme == "mailto":
            return "Direct Contact"
        return parsed.netloc.replace("www.", "") or "Profile"

    def _set_card_icon_data_uri(
        self,
        card: SvgCard,
        *,
        url: Optional[str] = None,
        host: Optional[str] = None,
        label: Optional[str] = None,
        accent: Optional[str] = None,
    ) -> None:
        icon_data_uri = self._brand_icon_data_uri(
            url=url,
            host=host,
            label=label,
            accent=accent,
        )
        if icon_data_uri:
            object.__setattr__(card, "icon_data_uri", icon_data_uri)

    def _brand_icon_data_uri(
        self,
        *,
        url: Optional[str] = None,
        host: Optional[str] = None,
        label: Optional[str] = None,
        accent: Optional[str] = None,
    ) -> Optional[str]:
        normalized_host = (host or "").strip().replace("www.", "").lower()
        if not normalized_host and url:
            normalized_host = (
                urlparse(url).netloc.strip().replace("www.", "").lower()
            )

        accent_hex = (
            accent.lstrip("#")
            if accent and re.fullmatch(r"[0-9a-fA-F]{6}", accent.lstrip("#"))
            else None
        )

        glyph: Optional[str] = None
        background: Optional[str] = None
        foreground: Optional[str] = None
        if normalized_host.endswith("linkedin.com"):
            background, foreground = ("0A66C2", "FFFFFF")
            glyph = (
                f"<circle cx='21.5' cy='19.5' r='4.5' fill='#{foreground}'/>"
                f"<rect x='17' y='27' width='9' height='20' rx='2' fill='#{foreground}'/>"
                f"<path d='M34 27h8v3.2c1.5-2.2 3.9-3.8 7.4-3.8 7.3 0 8.6 4.8 8.6 11.2V47h-9v-6.6c0-3.4-.6-5.8-3.4-5.8-2.9 0-4.1 2.1-4.1 5.8V47h-8.5z' fill='#{foreground}'/>"
            )
        elif normalized_host.endswith("kaggle.com"):
            background, foreground = ("20BEFF", "062F40")
            glyph = (
                f"<path d='M20 15h7v15.4L38.2 15h9.2L34 31.4 47.6 49h-9.3L27 34.2V49h-7z' fill='#{foreground}'/>"
            )
        elif normalized_host.endswith("x.com") or normalized_host.endswith(
            "twitter.com"
        ):
            background, foreground = ("000000", "FFFFFF")
            glyph = (
                f"<path d='M15 15h10.5l8.6 11.7L43.3 15H53L38.9 32.2 53.2 49H42.7l-9.4-12.1L23.6 49H14l14.4-17.6z' fill='#{foreground}'/>"
            )
        elif normalized_host.endswith("github.com"):
            background, foreground = ("181717", "FFFFFF")
            glyph = (
                f"<path d='M22.5 24 18 16m23.5 8L46 16' stroke='#{foreground}' stroke-width='3.8' stroke-linecap='round' fill='none'/>"
                f"<circle cx='32' cy='34' r='13' fill='#{foreground}'/>"
                f"<circle cx='27.2' cy='33' r='1.7' fill='#{background}'/>"
                f"<circle cx='36.8' cy='33' r='1.7' fill='#{background}'/>"
                f"<path d='M27.8 39.3c1.2 1.2 7.2 1.2 8.4 0' stroke='#{background}' stroke-width='2.1' stroke-linecap='round' fill='none'/>"
            )
        elif normalized_host.endswith("w4w.dev"):
            background, foreground = ("0F172A", "22D3EE")
            glyph = (
                f"<path d='M11 44 19 20 27 44 35 20 43 44 51 20' stroke='#{foreground}' stroke-width='4' stroke-linecap='round' stroke-linejoin='round' fill='none'/>"
                f"<circle cx='19' cy='20' r='2.6' fill='#{foreground}'/>"
                f"<circle cx='35' cy='20' r='2.6' fill='#{foreground}'/>"
                f"<circle cx='51' cy='20' r='2.6' fill='#{foreground}'/>"
            )
        elif (url and urlparse(url).scheme == "mailto") or (
            label and "email" in label.lower()
        ):
            background, foreground = (accent_hex or "EA4335", "FFFFFF")
            glyph = (
                f"<rect x='12' y='20' width='40' height='24' rx='4' fill='none' stroke='#{foreground}' stroke-width='3'/>"
                f"<path d='M14 23.5 32 35l18-11.5' fill='none' stroke='#{foreground}' stroke-width='3' stroke-linecap='round' stroke-linejoin='round'/>"
            )
        elif normalized_host or label:
            background, foreground = (accent_hex or "334155", "E2E8F0")
            glyph = (
                f"<circle cx='32' cy='32' r='13' fill='none' stroke='#{foreground}' stroke-width='3'/>"
                f"<path d='M19 32h26M32 19.5c4.2 4.4 4.2 20.6 0 25M32 19.5c-4.2 4.4-4.2 20.6 0 25' stroke='#{foreground}' stroke-width='2.4' stroke-linecap='round' fill='none'/>"
            )
        if not glyph or not background or not foreground:
            # Fallback — try fetching a friendly favicon (w4w.dev) before giving up.
            try_fallback = self._fetch_remote_image_data_uri(
                "https://w4w.dev/favicon.ico",
                context="brand favicon fallback",
            )
            if try_fallback:
                return try_fallback
            return None

        icon_svg = (
            "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'>"
            f"<rect width='64' height='64' rx='14' fill='#{background}'/>"
            f"{glyph}"
            "</svg>"
        )
        return (
            "data:image/svg+xml;base64,"
            + base64.b64encode(icon_svg.encode("utf-8")).decode("ascii")
        )

    def _render_featured_projects(self) -> str:
        svg_cards: list[SvgCard] = []
        fallback_lines: list[str] = []
        for repo in self.settings.featured_repos:
            metadata = self.repo_client.fetch_repo_metadata(repo.full_name)
            svg_cards.append(self._build_project_svg_card(repo.full_name, metadata))
            fallback_lines.append(
                self._build_featured_repo_fallback_line(
                    repo_full_name=repo.full_name,
                    metadata=metadata,
                )
            )

        if not svg_cards:
            block = SvgBlock(
                title="Featured Projects",
                cards=(SvgCard(title="No featured repositories configured."),),
                columns=1,
            )
            renderer = SvgBlockRenderer(width=1100, card_height=200, padding=28)
            svg_embed = self._render_svg_embed(
                section_flag="featured_projects",
                asset_name="featured-projects",
                block=block,
                renderer=renderer,
                alt_text="Featured projects cards",
            )
            lines = ["- No featured repositories configured."]
            if svg_embed:
                lines.insert(0, f'<p align="center">{svg_embed}</p>')
            return "\n".join(lines)

        block = SvgBlock(
            title="Featured Projects",
            cards=tuple(svg_cards),
            columns=2,
        )
        renderer = SvgBlockRenderer(width=1200, card_height=220, padding=28)
        svg_embed = self._render_svg_embed(
            section_flag="featured_projects",
            asset_name="featured-projects",
            block=block,
            renderer=renderer,
            alt_text="Featured projects cards",
        )
        caption = (
            '<p align="center"><sub>Snapshot includes stars, freshness, '
            "topic signals, and trendline momentum.</sub></p>"
        )
        lines = [
            "\n".join(fallback_lines),
            caption,
        ]
        if svg_embed:
            lines.insert(0, f'<p align="center">{svg_embed}</p>')
        return "\n".join(lines)

    def _build_project_svg_card(
        self,
        repo_full_name: str,
        metadata: Optional[RepoMetadata],
    ) -> SvgCard:
        if metadata is None:
            repo_url = f"https://github.com/{repo_full_name}"
            repo_name = repo_full_name.split("/")[-1]
            card = SvgCard(
                title=repo_name,
                kicker=repo_full_name,
                lines=(
                    "Live stats are temporarily unavailable.",
                    "Open the repository for full details.",
                ),
                meta=(),
                url=repo_url,
                badge="Featured",
                icon=repo_name[:2].upper(),
            )
            self._set_card_icon_data_uri(
                card,
                url=repo_url,
                label=repo_name,
            )
            return card

        description = metadata.description or "No description provided."
        lines: list[str] = [description]
        if metadata.topics:
            topics = " · ".join(metadata.topics[:3])
            lines.append(f"Topics {topics}")
        # avoid duplicative host clutter in the visible lines; surface homepage in card attributes instead
        if metadata.homepage:
            homepage_host = urlparse(metadata.homepage).netloc.replace("www.", "")
            if homepage_host:
                # keep homepage as an attribute for the renderer to expose if desired
                pass
        # richer metadata for featured projects
        info_bits: list[str] = []
        info_bits.append(f"★ {metadata.stars:,}")
        if metadata.forks:
            info_bits.append(f"Forks {metadata.forks:,}")
        if metadata.size_kb:
            info_bits.append(f"Size {metadata.size_kb:,} KB")
        updated = self._format_timestamp(metadata.updated_at)
        if updated:
            info_bits.append(f"Updated {updated}")
        created = self._format_timestamp(metadata.created_at)
        if created:
            info_bits.append(f"Created {created}")
        sparkline = self._build_star_history_points(repo_full_name, metadata)
        # distinct colorful treatment for featured projects
        accent = self._repo_accent_color(metadata) or "8B5CF6"
        card = SvgCard(
            title=metadata.name,
            kicker=repo_full_name,
            lines=tuple(lines),
            meta=tuple(info_bits),
            url=metadata.html_url,
            background_image=self._repo_background_image(repo_full_name, metadata),
            sparkline=sparkline,
            icon=metadata.name[:2].upper(),
            badge="Showcase",
            accent=accent,
        )
        # expose rich attributes on the presentation card for downstream assertions
        object.__setattr__(card, "homepage", metadata.homepage)
        object.__setattr__(card, "topics", tuple(metadata.topics))
        object.__setattr__(card, "updated_at", metadata.updated_at)
        object.__setattr__(card, "created_at", metadata.created_at)
        object.__setattr__(card, "forks", metadata.forks)
        object.__setattr__(card, "size_kb", metadata.size_kb)

        self._set_card_icon_data_uri(
            card,
            url=metadata.html_url,
            label=metadata.name,
            accent=accent,
        )
        return card

    def _render_blog_posts(self) -> str:
        posts = self.blog_client.fetch_latest_posts(
            self.settings.blog_feed_url,
            self.settings.blog_post_limit,
        )
        feed_url = escape(self.settings.blog_feed_url)
        feed_url_raw = self.settings.blog_feed_url
        svg_cards: list[SvgCard] = []
        fallback_lines: list[str] = []
        if not posts:
            block = SvgBlock(
                title="Latest Blog Posts",
                cards=(
                    SvgCard(
                        title="No recent posts available.",
                        lines=(self.settings.blog_feed_url,),
                        meta=("RSS feed",),
                        url=self.settings.blog_feed_url,
                    ),
                ),
                columns=1,
            )
            renderer = SvgBlockRenderer(width=1000, card_height=200, padding=28)
            svg_embed = self._render_svg_embed(
                section_flag="blog_posts",
                asset_name="blog-posts",
                block=block,
                renderer=renderer,
                alt_text="Latest blog posts cards",
            )
            fallback_lines.append(
                f"- No recent posts available. [RSS feed]({feed_url_raw})"
            )
            lines = [
                self._wrap_blog_post_list_markers(fallback_lines),
                f'<p align="center"><sub>📡 Source: <a href="{feed_url}">RSS feed</a></sub></p>',
            ]
            if svg_embed:
                lines.insert(0, f'<p align="center">{svg_embed}</p>')
            return "\n".join(lines)

        for post in posts:
            metadata = self.blog_metadata_client.fetch_metadata(post.url)
            host = metadata.get("host") or urlparse(post.url).netloc.replace(
                "www.", ""
            )
            summary = metadata.get("summary") or "Tap to read the full story."
            published = metadata.get("published")
            card_meta: list[str] = []
            if host:
                card_meta.append(host)
            if published:
                card_meta.append(f"Published {published[:10]}")
            # blog cards get a warmer accent and do not render a badge/pill
            accent = "F59E0B" if "w4w.dev" in (host or "") else "F97316"
            card = SvgCard(
                title=post.title,
                kicker=f"{host or 'blog'}",
                lines=(summary,),
                meta=tuple(card_meta),
                url=post.url,
                background_image=metadata.get("hero_image"),
                icon=(host or "BL")[:2].upper(),
                badge=None,
                accent=accent,
            )
            self._set_card_icon_data_uri(
                card,
                url=post.url,
                host=host,
                label=post.title,
                accent=accent,
            )
            svg_cards.append(card)
            meta_bits = [bit for bit in card_meta if bit]
            line = f"- [{escape(post.title)}]({escape(post.url)})"
            if meta_bits:
                line += f" — {escape(' · '.join(meta_bits))}"
            fallback_lines.append(line)
        block = SvgBlock(
            title="Latest Blog Posts",
            cards=tuple(svg_cards),
            columns=1,
        )
        renderer = SvgBlockRenderer(width=1100, card_height=220, padding=28)
        svg_embed = self._render_svg_embed(
            section_flag="blog_posts",
            asset_name="blog-posts",
            block=block,
            renderer=renderer,
            alt_text="Latest blog posts cards",
        )
        lines = [
            self._wrap_blog_post_list_markers(fallback_lines),
            (
                f'<p align="center"><sub>📡 Auto-updated from '
                f'<a href="{feed_url}">RSS feed</a></sub></p>'
            ),
        ]
        if svg_embed:
            lines.insert(0, f'<p align="center">{svg_embed}</p>')
        return "\n".join(lines)

    def _render_svg_embed(
        self,
        section_flag: str,
        asset_name: str,
        block: SvgBlock,
        renderer: SvgBlockRenderer,
        alt_text: str,
    ) -> str:
        if not self._svg_section_enabled(section_flag):
            return ""
        self._render_svg_inline(
            section_flag=section_flag,
            asset_name=asset_name,
            block=block,
            renderer=renderer,
        )
        src = escape(self._svg_asset_src(asset_name))
        alt = escape(alt_text)
        return (
            f'<img src="{src}" alt="{alt}" '
            f'width="{renderer.width}" loading="lazy"/>'
        )

    def _svg_asset_src(self, asset_name: str) -> str:
        filename = re.sub(r"[^a-zA-Z0-9_-]+", "-", asset_name).strip("-_")
        normalized = filename or "section"
        return (
            Path(self.settings.svg.output_dir) / f"{normalized}.svg"
        ).as_posix()

    def _build_featured_repo_fallback_line(
        self,
        repo_full_name: str,
        metadata: Optional[RepoMetadata],
    ) -> str:
        if metadata is None:
            repo_name = repo_full_name.split("/")[-1]
            repo_url = f"https://github.com/{repo_full_name}"
            return (
                f"- [{escape(repo_name)}]({escape(repo_url)}) "
                "— Live stats are temporarily unavailable; open repository for details."
            )
        description = metadata.description or "No description provided."
        return (
            f"- [{escape(metadata.name)}]({escape(metadata.html_url)}) "
            f"— {escape(description)} (★ {metadata.stars:,})"
        )

    def _svg_section_enabled(self, section: str) -> bool:
        if self.svg_builder is None:
            return False
        if section == "top_contact":
            return self.settings.svg.top_contact
        if section == "featured_projects":
            return self.settings.svg.featured_projects
        if section == "blog_posts":
            return self.settings.svg.blog_posts
        return False

    def _render_svg_inline(
        self,
        section_flag: str,
        asset_name: str,
        block: SvgBlock,
        renderer: SvgBlockRenderer,
    ) -> str:
        svg_markup = renderer.render(block)
        if self._svg_section_enabled(section_flag):
            self._write_svg_asset(
                asset_name=asset_name,
                block=block,
                svg_markup=svg_markup,
            )
        return svg_markup

    def _write_svg_asset(
        self,
        asset_name: str,
        block: SvgBlock,
        svg_markup: str | None = None,
        renderer: SvgBlockRenderer | None = None,
    ) -> None:
        if self.svg_builder is None:
            return
        try:
            if svg_markup is not None:
                self.svg_builder.write_raw(
                    asset_name=asset_name,
                    svg_content=svg_markup,
                )
                return
            render_from = renderer or self.svg_builder.renderer
            rendered = render_from.render(block)
            self.svg_builder.write_raw(asset_name=asset_name, svg_content=rendered)
        except OSError as exc:
            logger.warning(f"Failed to write README SVG asset {asset_name}: {exc}")

    def _build_badge_url(
        self,
        label: str,
        color: str,
        logo: Optional[str],
        logo_color: str,
    ) -> str:
        encoded_label = quote(label.replace("-", "--"), safe="")
        badge_url = (
            f"https://img.shields.io/badge/{encoded_label}-{color.lstrip('#')}"
            f"?style={quote(self.settings.badge_style, safe='')}"
        )
        if logo:
            badge_url += f"&logo={quote(self._resolve_logo(logo), safe='')}"
            badge_url += f"&logoColor={quote(logo_color, safe='')}"
        return badge_url

    def _resolve_logo(self, logo: str) -> str:
        if not logo.lower().startswith(("http://", "https://")):
            return logo

        request = _build_remote_get_request(
            url=logo,
            headers={"User-Agent": "readme-section-generator"},
            context="badge logo fetch",
        )
        if request is None:
            return logo
        try:
            with urlopen(request, timeout=10.0) as response:
                logo_bytes = response.read()
                content_type = (
                    response.headers.get("Content-Type", "")
                    .split(";", maxsplit=1)[0]
                    .strip()
                    .lower()
                )
        except Exception as exc:  # pragma: no cover - network path
            logger.warning(f"Failed to fetch badge logo from {logo}: {exc}")
            return logo

        if not logo_bytes:
            return logo

        if not content_type:
            if logo.lower().endswith(".svg"):
                content_type = "image/svg+xml"
            elif logo.lower().endswith(".png"):
                content_type = "image/png"
            elif logo.lower().endswith(".ico"):
                content_type = "image/x-icon"
            elif logo.lower().endswith((".jpg", ".jpeg")):
                content_type = "image/jpeg"
            else:
                content_type = "application/octet-stream"

        if content_type == "image/svg+xml":
            return (
                "data:image/svg+xml;base64,"
                + base64.b64encode(logo_bytes).decode("ascii")
            )

        raw_logo_data_uri = (
            f"data:{content_type};base64,"
            f"{base64.b64encode(logo_bytes).decode('ascii')}"
        )
        wrapped_svg = (
            "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'>"
            f"<image href='{raw_logo_data_uri}' width='64' height='64'/>"
            "</svg>"
        )
        return (
            "data:image/svg+xml;base64,"
            + base64.b64encode(wrapped_svg.encode("utf-8")).decode("ascii")
        )

    def _format_timestamp(self, timestamp: Optional[str]) -> Optional[str]:
        if not timestamp:
            return None
        if "T" not in timestamp:
            return timestamp
        return timestamp.split("T", maxsplit=1)[0]

    def _repo_background_image(
        self,
        repo_full_name: str,
        metadata: Optional[RepoMetadata],
    ) -> Optional[str]:
        candidates: list[str] = []
        if metadata and metadata.open_graph_image_url:
            candidates.append(metadata.open_graph_image_url)
        candidates.append(f"https://opengraph.githubassets.com/1/{repo_full_name}")
        for image_url in candidates:
            data_uri = self._fetch_remote_image_data_uri(
                image_url,
                context=f"repo preview for {repo_full_name}",
            )
            if data_uri:
                return data_uri
        return None

    def _fetch_remote_image_data_uri(
        self,
        url: str,
        context: str,
    ) -> Optional[str]:
        request = _build_remote_get_request(
            url=url,
            headers={"User-Agent": "readme-section-generator"},
            context=context,
        )
        if request is None:
            return None
        try:
            with urlopen(request, timeout=10.0) as response:
                image_bytes = response.read()
                content_type = (
                    response.headers.get("Content-Type", "")
                    .split(";", maxsplit=1)[0]
                    .strip()
                    .lower()
                )
        except Exception as exc:  # pragma: no cover - network path
            logger.warning(f"Failed to fetch image for {context}: {exc}")
            return None

        if not image_bytes:
            return None
        if not content_type.startswith("image/"):
            content_type = "image/png"
        return (
            f"data:{content_type};base64,"
            f"{base64.b64encode(image_bytes).decode('ascii')}"
        )

    def _repo_accent_color(self, metadata: RepoMetadata) -> str:
        joined_topics = " ".join(topic.lower() for topic in metadata.topics)
        if "python" in joined_topics:
            return "3776AB"
        if "typescript" in joined_topics or "javascript" in joined_topics:
            return "3178C6"
        if "ai" in joined_topics or "ml" in joined_topics:
            return "8B5CF6"
        return "60A5FA"

    def _build_star_history_points(
        self,
        repo_full_name: str,
        metadata: Optional[RepoMetadata],
    ) -> tuple[float, ...] | None:
        if metadata is None:
            return None
        history: Optional[list[int]] = None
        if self.star_history_client:
            history = self.star_history_client.fetch_star_history(
                repo_full_name,
                sample=24,
            )
        if history:
            return tuple(float(value) for value in history)
        if metadata.stars > 0:
            return (0.0, float(metadata.stars))
        return None

    def _wrap_blog_post_list_markers(self, lines: Sequence[str]) -> str:
        """Wrap blog post list in manager markers and a GFM <details> disclosure.

        This preserves the HTML comment markers used by the injection engine
        while also providing a GitHub-friendly collapsible UX and a safe
        fallback list for non-HTML consumers.
        """
        inner = "\n".join(lines)
        details = (
            "<details>\n"
            "<summary><strong>Latest posts (auto-updated)</strong></summary>\n\n"
            f"{inner}\n\n"
            "</details>\n"
        )
        return (
            "<!-- BLOG-POST-LIST:START -->\n"
            f"{details}"
            "<!-- BLOG-POST-LIST:END -->"
        )
