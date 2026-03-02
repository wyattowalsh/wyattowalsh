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
            meta = [link.url]
            svg_cards.append(
                SvgCard(
                    title=link.label,
                    lines=(link.url,),
                    meta=tuple(meta),
                    url=link.url,
                )
            )
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
        gif_html = (
            '<p align="center">'
            '<img src=".github/assets/img/gh.gif" '
            'alt="Animated GitHub contributions garden" '
            'width="260" loading="lazy"/>'
            "</p>"
        )
        social_links = " · ".join(
            f"[{escape(link.label)}]({escape(link.url)})"
            for link in self.settings.social_links
        )
        lines = [gif_html]
        if svg_embed:
            lines.append(f'<p align="center">{svg_embed}</p>')
        if social_links:
            lines.append(social_links)
        return "\n".join(lines)

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
            '<p align="center"><sub>GitHub metadata + star history, '
            "updated on every README refresh.</sub></p>"
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
            return SvgCard(
                title=repo_name,
                lines=("Unable to fetch repository metadata.",),
                meta=("GitHub",),
                url=repo_url,
            )

        description = metadata.description or "No description provided."
        lines: list[str] = [description]
        if metadata.topics:
            topics = ", ".join(metadata.topics[:3])
            lines.append(f"Topics: {topics}")
        if metadata.homepage:
            lines.append(metadata.homepage)
        info_bits = [f"★ {metadata.stars:,}"]
        updated = self._format_timestamp(metadata.updated_at)
        if updated:
            info_bits.append(f"Updated {updated}")
        sparkline = self._build_star_history_points(repo_full_name, metadata)
        return SvgCard(
            title=metadata.name,
            lines=tuple(lines),
            meta=tuple(info_bits),
            url=metadata.html_url,
            background_image=self._repo_background_image(repo_full_name),
            sparkline=sparkline,
        )

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
                *fallback_lines,
                f'<p align="center"><sub>📡 Source: <a href="{feed_url}">RSS feed</a></sub></p>',
            ]
            if svg_embed:
                lines.insert(0, f'<p align="center">{svg_embed}</p>')
            return self._wrap_blog_post_list_markers(lines)

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
            svg_cards.append(
                SvgCard(
                    title=post.title,
                    lines=(host or "blog", summary),
                    meta=tuple(card_meta),
                    url=post.url,
                    background_image=metadata.get("hero_image"),
                )
            )
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
            *fallback_lines,
            (
                f'<p align="center"><sub>📡 Auto-updated from '
                f'<a href="{feed_url}">RSS feed</a></sub></p>'
            ),
        ]
        if svg_embed:
            lines.insert(0, f'<p align="center">{svg_embed}</p>')
        return self._wrap_blog_post_list_markers(lines)

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
                "— Unable to fetch repository metadata."
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

    def _repo_background_image(self, repo_full_name: str) -> str:
        return f"https://opengraph.githubassets.com/1/{repo_full_name}"

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
        return (
            "<!-- BLOG-POST-LIST:START -->\n"
            + "\n".join(lines)
            + "\n<!-- BLOG-POST-LIST:END -->"
        )
