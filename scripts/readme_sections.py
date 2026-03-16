"""README dynamic section generator (badges, projects, and blog posts)."""

import base64
import ipaddress
import json
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from typing import Optional, Sequence
from urllib.error import HTTPError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen
import defusedxml.ElementTree as DefusedET
from xml.etree.ElementTree import Element

from .config import ReadmeSectionsSettings
from .readme_svg import (
    ReadmeSvgAssetBuilder,
    SvgAssetWriter,
    SvgBlock,
    SvgBlockRenderer,
    SvgBlogCardRenderer,
    SvgCard,
    SvgConnectCardRenderer,
    SvgRepoCardRenderer,
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
    language: Optional[str] = None
    open_graph_image_url: Optional[str] = None
    languages: Optional[dict[str, int]] = None


@dataclass(frozen=True)
class BlogPost:
    """A single blog post item from RSS/Atom."""

    title: str
    url: str
    image_url: Optional[str] = None


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
            language=payload.get("language") or None,
            open_graph_image_url=payload.get("open_graph_image_url") or None,
        )

    def fetch_repo_languages(
        self, full_name: str,
    ) -> Optional[dict[str, int]]:
        """Fetch language byte-count breakdown for owner/repo."""
        request = _build_remote_get_request(
            url=f"https://api.github.com/repos/{full_name}/languages",
            headers=self._headers(),
            context=f"repo languages for {full_name}",
        )
        if request is None:
            return None
        try:
            with urlopen(request, timeout=self.timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except Exception as exc:  # pragma: no cover - network path
            logger.warning(
                "Failed to fetch languages for %s: %s", full_name, exc,
            )
            return None
        if isinstance(payload, dict) and payload:
            return {k: int(v) for k, v in payload.items()}
        return None

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
            root = DefusedET.fromstring(body)
        except DefusedET.ParseError as exc:
            logger.warning(f"Invalid blog feed XML from {feed_url}: {exc}")
            return []

        posts = self._parse_rss_items(root)
        if not posts:
            posts = self._parse_atom_entries(root)
        return posts[:limit]

    def _parse_rss_items(self, root: Element) -> list[BlogPost]:
        posts: list[BlogPost] = []
        for item in root.findall(".//item"):
            title = (item.findtext("title") or "").strip()
            link = (item.findtext("link") or "").strip()
            if not (title and link):
                continue
            image_url: Optional[str] = None
            enc = item.find("enclosure")
            if enc is not None:
                enc_url = (enc.get("url") or "").strip()
                enc_type = (enc.get("type") or "").strip().lower()
                if enc_url and enc_type.startswith("image/"):
                    image_url = enc_url
            posts.append(BlogPost(
                title=title, url=link, image_url=image_url,
            ))
        return posts

    def _parse_atom_entries(self, root: Element) -> list[BlogPost]:
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
    """Fetch stargazer timestamps via GitHub GraphQL API for sparkline generation."""

    _GRAPHQL_URL = "https://api.github.com/graphql"
    _QUERY = (
        "query($owner:String!, $name:String!, $after:String) {"
        "  repository(owner:$owner, name:$name) {"
        "    stargazers(first:100, after:$after, orderBy:{field:STARRED_AT, direction:ASC}) {"
        "      totalCount"
        "      edges { starredAt cursor }"
        "      pageInfo { hasNextPage endCursor }"
        "    }"
        "  }"
        "}"
    )

    def __init__(self, timeout: float = 10.0) -> None:
        self.timeout = timeout

    def fetch_star_history(
        self,
        full_name: str,
        sample: int = 24,
    ) -> Optional[list[int]]:
        """Return cumulative star counts sampled to *sample* time bins."""
        parts = full_name.split("/", 1)
        if len(parts) != 2:
            logger.warning("Invalid repo full_name: %s", full_name)
            return None

        owner, name = parts
        timestamps: list[datetime] = []
        cursor: Optional[str] = None

        while True:
            variables: dict[str, object] = {"owner": owner, "name": name}
            if cursor is not None:
                variables["after"] = cursor

            body = json.dumps({"query": self._QUERY, "variables": variables}).encode("utf-8")
            request = Request(
                url=self._GRAPHQL_URL,
                data=body,
                headers=self._headers(),
                method="POST",
            )

            try:
                with urlopen(request, timeout=self.timeout) as response:
                    payload = json.loads(response.read().decode("utf-8"))
            except Exception as exc:  # pragma: no cover - network path
                logger.warning(
                    "Failed to fetch star history for %s: %s", full_name, exc
                )
                return None

            errors = payload.get("errors")
            if errors:
                logger.warning(
                    "GraphQL errors fetching star history for %s: %s",
                    full_name,
                    errors,
                )
                return None

            repo_data = (payload.get("data") or {}).get("repository")
            if repo_data is None:
                logger.warning(
                    "Repository not found in GraphQL response for %s", full_name
                )
                return None

            stargazers = repo_data["stargazers"]
            for edge in stargazers.get("edges", []):
                starred_at = edge.get("starredAt", "")
                try:
                    ts = datetime.fromisoformat(starred_at.replace("Z", "+00:00"))
                    timestamps.append(ts)
                except (ValueError, AttributeError):
                    continue

            page_info = stargazers.get("pageInfo", {})
            if page_info.get("hasNextPage"):
                cursor = page_info.get("endCursor")
            else:
                break

        if not timestamps:
            return None

        # Bucket into *sample* evenly-spaced time bins from first star to now
        timestamps.sort()
        t_start = timestamps[0]
        t_end = datetime.now(timezone.utc)
        if t_end <= t_start:
            t_end = timestamps[-1]

        total_seconds = (t_end - t_start).total_seconds() or 1.0
        bin_width = total_seconds / sample

        # Build cumulative counts at each bin boundary
        sampled: list[int] = []
        ts_idx = 0
        for b in range(sample):
            bin_end = t_start.timestamp() + (b + 1) * bin_width
            while ts_idx < len(timestamps) and timestamps[ts_idx].timestamp() <= bin_end:
                ts_idx += 1
            sampled.append(ts_idx)

        return sampled

    def _headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "readme-section-generator",
        }
        token = os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN")
        if not token:
            try:
                import subprocess
                token = subprocess.check_output(
                    ["gh", "auth", "token"],
                    stderr=subprocess.DEVNULL,
                    timeout=5,
                ).decode().strip() or None
            except Exception:
                pass
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
            # Try property/name before content
            pattern_prop_first = re.compile(
                rf'<meta[^>]+{attr}\s*=\s*["\']{value}["\'][^>]*content\s*=\s*["\']([^"\']+)["\']',
                flags=re.IGNORECASE,
            )
            match = pattern_prop_first.search(html)
            if not match:
                # Try content before property/name
                pattern_content_first = re.compile(
                    rf'<meta[^>]+content\s*=\s*["\']([^"\']+)["\'][^>]*{attr}\s*=\s*["\']{value}["\']',
                    flags=re.IGNORECASE,
                )
                match = pattern_content_first.search(html)
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
            # Clean layout: kicker = category, title = platform name
            kicker = self._social_category(link.url)
            badge_label = self._social_personality_badge(link.url)
            card = SvgCard(
                title=link.label,
                kicker=kicker,
                lines=(),
                meta=(badge_label,),
                url=link.url,
                icon=self._social_icon(link.label),
                badge=badge_label,
                accent=None,
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
        # Render per-card SVGs
        card_renderer = SvgConnectCardRenderer(width=140, height=130)
        card_embeds: list[tuple[str, str]] = []

        if self._svg_section_enabled("top_contact"):
            writer = SvgAssetWriter(
                output_dir=self.settings.svg.output_dir,
            )
            for card in svg_cards:
                name = re.sub(
                    r"[^a-zA-Z0-9_-]+", "-", card.title,
                ).strip("-_").lower() or "link"
                asset = f"connect-{name}"
                writer.write(
                    asset_name=asset,
                    svg_content=card_renderer.render_card(card),
                )
                src = (
                    Path(self.settings.svg.output_dir)
                    / f"{asset}.svg"
                ).as_posix()
                card_embeds.append((card.url or "#", src))

        result: list[str] = []
        if card_embeds:
            imgs = []
            for url, src in card_embeds:
                imgs.append(
                    f'<a href="{escape(url)}" target="_blank">'
                    f'<img src="{escape(src)}" width="140"'
                    f' loading="lazy"/></a>'
                )
            result.append(
                '<p align="center">' + "\n".join(imgs) + "</p>"
            )
        return "\n".join(result)

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

    def _social_category(self, url: str) -> str:
        """Return a short uppercase category for a social/contact URL."""
        parsed = urlparse(url)
        if parsed.scheme == "mailto":
            return "CONTACT"
        host = parsed.netloc.replace("www.", "").lower()
        if any(kw in host for kw in ("github.com", "gitlab.com", "bitbucket.org")):
            return "CODE"
        if any(kw in host for kw in ("linkedin.com", "kaggle.com", "x.com", "twitter.com")):
            return "SOCIAL"
        return "WEBSITE"

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

    # -- Simple Icons CDN integration ------------------------------------

    # Map normalized host suffixes to (slug, bg_color) for Simple Icons.
    _SIMPLE_ICON_MAP: dict[str, tuple[str, str]] = {
        "linkedin.com": ("linkedin", "0A66C2"),
        "github.com": ("github", "181717"),
        "kaggle.com": ("kaggle", "20BEFF"),
        "x.com": ("x", "000000"),
        "twitter.com": ("x", "000000"),
    }

    def _fetch_simple_icon_data_uri(
        self,
        slug: str,
        bg_color: str,
        fg_color: str = "white",
    ) -> Optional[str]:
        """Fetch an icon from the Simple Icons CDN and wrap it in a 64x64 SVG.

        Returns a ``data:image/svg+xml;base64,...`` URI on success, or *None*
        if the network request fails so the caller can fall back to a
        hardcoded glyph.
        """
        cdn_url = (
            f"https://cdn.jsdelivr.net/npm/simple-icons@v11"
            f"/icons/{slug}.svg"
        )
        request = _build_remote_get_request(
            url=cdn_url,
            headers={"User-Agent": "readme-section-generator"},
            context=f"simple-icon/{slug}",
        )
        if request is None:
            return None
        try:
            with urlopen(request, timeout=10.0) as response:
                svg_bytes = response.read()
        except Exception as exc:  # pragma: no cover - network path
            logger.warning("Failed to fetch Simple Icon %s: %s", slug, exc)
            return None

        if not svg_bytes:
            return None

        # Extract inner SVG content (paths/shapes) from the returned SVG.
        svg_text = svg_bytes.decode("utf-8", errors="replace")
        try:
            root = DefusedET.fromstring(svg_text)
        except Exception:  # pragma: no cover - malformed SVG
            logger.warning("Failed to parse Simple Icon SVG for %s", slug)
            return None

        # Serialize child elements (the icon paths) as raw XML.
        inner_parts: list[str] = []
        for child in root:
            from xml.etree.ElementTree import tostring as _et_tostring

            child_str = _et_tostring(child, encoding="unicode")
            # Strip any namespace prefixes injected by ElementTree.
            child_str = re.sub(
                r'\s*xmlns(?::[a-z]+)?="[^"]*"', "", child_str,
            )
            inner_parts.append(child_str)
        icon_paths = "".join(inner_parts)

        bg_hex = bg_color.lstrip("#")
        fg_hex = fg_color.lstrip("#") if fg_color != "white" else "FFFFFF"
        wrapper_svg = (
            "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'>"
            f"<rect width='64' height='64' rx='14' fill='#{bg_hex}'/>"
            f"<svg x='12' y='12' width='40' height='40'"
            f" viewBox='0 0 24 24' fill='#{fg_hex}'>"
            f"{icon_paths}"
            f"</svg>"
            "</svg>"
        )
        return (
            "data:image/svg+xml;base64,"
            + base64.b64encode(wrapper_svg.encode("utf-8")).decode("ascii")
        )

    # -- w4w.dev favicon fetcher -----------------------------------------

    def _fetch_w4w_favicon_data_uri(self) -> Optional[str]:
        """Fetch w4w.dev logo, convert to PNG, return as data URI."""
        # Try local optimized ICO first (checked into repo assets)
        local_ico = Path(".github/assets/img/favicon.ico")
        if local_ico.exists():
            ico_bytes = local_ico.read_bytes()
            try:
                from PIL import Image as _Img
                from io import BytesIO as _BIO
                with _Img.open(_BIO(ico_bytes)) as img:
                    img = img.resize((64, 64), _Img.Resampling.LANCZOS)
                    buf = _BIO()
                    img.save(buf, format="PNG")
                    png_b64 = base64.b64encode(
                        buf.getvalue()
                    ).decode("ascii")
                    return f"data:image/png;base64,{png_b64}"
            except Exception:
                pass
        # Fall back to remote fetch
        for candidate in (
            "https://w4w.dev/logo.webp",
            "https://w4w.dev/favicon.ico",
        ):
            result = self._fetch_remote_image_data_uri(
                candidate, context="w4w.dev favicon",
            )
            if result:
                return result
        return None

    # -- Brand icon resolution -------------------------------------------

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

        # --- X/Twitter: use Unicode 𝕏 glyph instead of CDN fetch ---------
        if normalized_host.endswith("x.com") or normalized_host.endswith(
            "twitter.com"
        ):
            x_svg = (
                "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'>"
                "<rect width='64' height='64' rx='14' fill='#000'/>"
                "<text x='32' y='46' text-anchor='middle' fill='#fff' "
                "font-family='serif' font-size='40' font-weight='700'>"
                "\U0001d54f</text>"
                "</svg>"
            )
            return (
                "data:image/svg+xml;base64,"
                + base64.b64encode(x_svg.encode("utf-8")).decode("ascii")
            )

        # --- Try Simple Icons CDN first for known platforms ---------------
        for suffix, (slug, bg_color) in self._SIMPLE_ICON_MAP.items():
            if normalized_host.endswith(suffix):
                si_uri = self._fetch_simple_icon_data_uri(
                    slug=slug, bg_color=bg_color, fg_color="white",
                )
                if si_uri:
                    return si_uri
                break  # fall through to hardcoded glyph

        # --- Try w4w.dev favicon before the hardcoded zigzag glyph --------
        if normalized_host.endswith("w4w.dev"):
            favicon_uri = self._fetch_w4w_favicon_data_uri()
            if favicon_uri:
                return favicon_uri

        # --- Hardcoded glyph fallbacks ------------------------------------
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
        repos = self.settings.featured_repos
        # Fetch all repo metadata + languages in parallel
        metadata_by_name: dict[str, Optional[RepoMetadata]] = {}
        languages_by_name: dict[str, Optional[dict[str, int]]] = {}
        if repos:
            max_workers = min(16, len(repos) * 2)
            with ThreadPoolExecutor(max_workers=max_workers) as pool:
                meta_futures = {
                    pool.submit(
                        self.repo_client.fetch_repo_metadata, repo.full_name
                    ): ("meta", repo.full_name)
                    for repo in repos
                }
                lang_futures = {
                    pool.submit(
                        self.repo_client.fetch_repo_languages,
                        repo.full_name,
                    ): ("lang", repo.full_name)
                    for repo in repos
                }
                for future in as_completed(
                    {**meta_futures, **lang_futures}
                ):
                    tag = (
                        meta_futures.get(future)
                        or lang_futures.get(future)
                    )
                    if tag is None:
                        continue  # pragma: no cover
                    kind, name = tag
                    try:
                        if kind == "meta":
                            metadata_by_name[name] = future.result()
                        else:
                            languages_by_name[name] = future.result()
                    except Exception as exc:  # pragma: no cover
                        logger.warning(
                            "Failed to fetch %s for %s: %s",
                            kind, name, exc,
                        )
                        if kind == "meta":
                            metadata_by_name[name] = None
                        else:
                            languages_by_name[name] = None
        # Build cards preserving original order
        for repo in repos:
            metadata = metadata_by_name.get(repo.full_name)
            langs = languages_by_name.get(repo.full_name)
            svg_cards.append(
                self._build_project_svg_card(
                    repo.full_name, metadata, languages=langs,
                )
            )
            fallback_lines.append(
                self._build_featured_repo_fallback_line(
                    repo_full_name=repo.full_name,
                    metadata=metadata,
                )
            )

        if not svg_cards:
            lines = ["- No featured repositories configured."]
            return "\n".join(lines)

        # Render individual per-card SVGs
        card_renderer = SvgRepoCardRenderer(width=500, height=185)
        card_embeds: list[tuple[str, str]] = []  # (html_url, img_src)

        if self._svg_section_enabled("featured_projects"):
            writer = SvgAssetWriter(
                output_dir=self.settings.svg.output_dir,
            )
            for card in svg_cards:
                repo_name = re.sub(
                    r"[^a-zA-Z0-9_-]+", "-", card.title
                ).strip("-_").lower() or "repo"
                asset_name = f"featured-card-{repo_name}"
                svg_markup = card_renderer.render_card(card)
                writer.write(asset_name=asset_name, svg_content=svg_markup)
                src = (
                    Path(self.settings.svg.output_dir) / f"{asset_name}.svg"
                ).as_posix()
                card_embeds.append((card.url or "#", src))

        # Build HTML table grid (2 columns)
        table_lines: list[str] = []
        if card_embeds:
            table_lines.append('<table><tbody>')
            for i in range(0, len(card_embeds), 2):
                table_lines.append("<tr>")
                for j in range(2):
                    idx = i + j
                    if idx < len(card_embeds):
                        url, src = card_embeds[idx]
                        table_lines.append(
                            f'<td><a href="{escape(url)}"'
                            f' target="_blank">'
                            f'<img src="{escape(src)}" width="500"'
                            f' alt="{escape(svg_cards[idx].title)}"'
                            f' loading="lazy"/></a></td>'
                        )
                    else:
                        table_lines.append("<td></td>")
                table_lines.append("</tr>")
            table_lines.append("</tbody></table>")

        result_lines: list[str] = []
        if table_lines:
            result_lines.append("\n".join(table_lines))
        return "\n".join(result_lines)

    def _build_project_svg_card(
        self,
        repo_full_name: str,
        metadata: Optional[RepoMetadata],
        languages: Optional[dict[str, int]] = None,
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
        # richer metadata for featured projects — use prefixed tokens so the
        # new gh-card-style SVG renderer can parse language dots and stat icons.
        info_bits: list[str] = []
        if metadata.language:
            info_bits.append(f"lang:{metadata.language}")
        info_bits.append(f"★ {metadata.stars:,}")
        if metadata.forks:
            info_bits.append(f"⑂ {metadata.forks:,}")
        updated = self._format_timestamp(metadata.updated_at)
        if updated:
            info_bits.append(f"Updated {updated}")
        sparkline = self._build_star_history_points(repo_full_name, metadata)
        bg_image = self._repo_background_image(repo_full_name, metadata)
        accent = self._repo_accent_color(metadata) or "8B5CF6"
        card = SvgCard(
            title=metadata.name,
            kicker=repo_full_name,
            lines=tuple(lines),
            meta=tuple(info_bits),
            url=metadata.html_url,
            background_image=bg_image,
            sparkline=sparkline,
            icon=metadata.name[:2].upper(),
            badge="Showcase",
            accent=accent,
            homepage=metadata.homepage,
            topics=tuple(metadata.topics),
            updated_at=metadata.updated_at,
            created_at=metadata.created_at,
            forks=metadata.forks,
            size_kb=metadata.size_kb,
            languages=languages,
        )

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

        # Fetch blog post metadata in parallel
        metadata_by_url: dict[str, dict[str, Optional[str]]] = {}
        max_workers = min(8, len(posts))
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            future_to_url = {
                pool.submit(
                    self.blog_metadata_client.fetch_metadata, post.url
                ): post.url
                for post in posts
            }
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    metadata_by_url[url] = future.result()
                except Exception as exc:  # pragma: no cover
                    logger.warning("Failed to fetch blog metadata for %s: %s", url, exc)
                    metadata_by_url[url] = {
                        "hero_image": None,
                        "summary": None,
                        "published": None,
                        "host": urlparse(url).netloc.replace("www.", "") or None,
                    }
        # Build cards preserving original post order
        for post in posts:
            metadata = metadata_by_url.get(post.url, {})
            host = metadata.get("host") or urlparse(post.url).netloc.replace(
                "www.", ""
            )
            summary = metadata.get("summary") or "Tap to read the full story."
            published = metadata.get("published")
            # Sanitize title — strip trailing "update" noise (anchored)
            clean_title = re.sub(
                r"\s*\bupdate\s*$", "", post.title, flags=re.IGNORECASE
            ).strip()
            card_meta: list[str] = []
            if published:
                card_meta.append(f"Published {published[:10]}")
            if host:
                card_meta.append(host)
            # Simplified accent — single muted tone for all blog cards
            accent = "94A3B8"
            # Resolve hero image: convert relative URLs to absolute, then
            # fetch as a base64 data URI so GitHub's SVG sanitizer can render
            # the embedded image.
            hero_data_uri: Optional[str] = None
            # Try RSS enclosure first, then og:image from HTML
            hero_url = post.image_url or metadata.get("hero_image")
            if hero_url:
                absolute_hero = urljoin(post.url, hero_url)
                hero_data_uri = self._fetch_remote_image_data_uri(
                    absolute_hero, context="blog hero",
                )
            card = SvgCard(
                title=clean_title,
                kicker=f"{host or 'blog'}",
                lines=(summary,),
                meta=tuple(card_meta),
                url=post.url,
                background_image=hero_data_uri,
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
            line = f"- [{escape(clean_title)}]({escape(post.url)})"
            if meta_bits:
                line += f" — {escape(' · '.join(meta_bits))}"
            fallback_lines.append(line)
        # Render per-card blog SVGs
        blog_renderer = SvgBlogCardRenderer(width=480, height=150)
        card_embeds: list[tuple[str, str]] = []

        if self._svg_section_enabled("blog_posts"):
            writer = SvgAssetWriter(
                output_dir=self.settings.svg.output_dir,
            )
            for idx, card in enumerate(svg_cards):
                name = re.sub(
                    r"[^a-zA-Z0-9_-]+", "-", card.title,
                ).strip("-_").lower()[:40] or f"post-{idx}"
                asset = f"blog-{name}"
                writer.write(
                    asset_name=asset,
                    svg_content=blog_renderer.render_card(card),
                )
                src = (
                    Path(self.settings.svg.output_dir)
                    / f"{asset}.svg"
                ).as_posix()
                card_embeds.append((card.url or "#", src))

        result: list[str] = []
        if card_embeds:
            imgs = []
            for url, src in card_embeds:
                imgs.append(
                    f'<a href="{escape(url)}" target="_blank">'
                    f'<img src="{escape(src)}" width="500"'
                    f' loading="lazy"/></a>'
                )
            result.append(
                '<p align="center">' + "\n".join(imgs) + "</p>"
            )
        result.append(
            f'<p align="center"><sub>📡 Auto-updated from '
            f'<a href="{feed_url}">RSS feed</a></sub></p>'
        )
        return "\n".join(result)

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
        # Try to get the custom social preview from the repo HTML page
        og_url = self._scrape_repo_og_image(repo_full_name)
        if og_url:
            data_uri = self._fetch_remote_image_data_uri(
                og_url,
                context=f"repo social preview for {repo_full_name}",
            )
            if data_uri:
                return data_uri
        # Fall back to the auto-generated GitHub OG image
        fallback = f"https://opengraph.githubassets.com/1/{repo_full_name}"
        return self._fetch_remote_image_data_uri(
            fallback,
            context=f"repo preview for {repo_full_name}",
        )

    def _scrape_repo_og_image(
        self, repo_full_name: str,
    ) -> Optional[str]:
        """Scrape og:image / twitter:image from a GitHub repo page."""
        page_url = f"https://github.com/{repo_full_name}"
        request = _build_remote_get_request(
            url=page_url,
            headers={"User-Agent": "readme-section-generator"},
            context=f"repo page for {repo_full_name}",
        )
        if request is None:
            return None
        try:
            with urlopen(request, timeout=10.0) as response:
                html = response.read().decode("utf-8", errors="ignore")
        except Exception as exc:
            logger.warning(
                "Failed to fetch repo page for %s: %s",
                repo_full_name, exc,
            )
            return None
        # Parse og:image or twitter:image meta tags
        for attr, value in (
            ("property", "og:image"),
            ("name", "twitter:image"),
            ("name", "twitter:image:src"),
        ):
            for pattern in (
                re.compile(
                    rf'<meta[^>]+{attr}\s*=\s*["\']'
                    rf'{value}["\'][^>]*content\s*=\s*["\']'
                    rf'([^"\']+)["\']',
                    flags=re.IGNORECASE,
                ),
                re.compile(
                    rf'<meta[^>]+content\s*=\s*["\']([^"\']+)["\']'
                    rf'[^>]*{attr}\s*=\s*["\']'
                    rf'{value}["\']',
                    flags=re.IGNORECASE,
                ),
            ):
                match = pattern.search(html)
                if match:
                    url = match.group(1).strip()
                    # Skip the generic opengraph.githubassets.com URL
                    if "opengraph.githubassets.com" in url:
                        continue
                    if url.startswith("http"):
                        return url
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
        max_retries = 3
        backoff_delays = (1, 2, 4)
        for attempt in range(max_retries + 1):
            try:
                with urlopen(request, timeout=10.0) as response:
                    image_bytes = response.read()
                    content_type = (
                        response.headers.get("Content-Type", "")
                        .split(";", maxsplit=1)[0]
                        .strip()
                        .lower()
                    )
                break
            except HTTPError as exc:
                if exc.code == 429 and attempt < max_retries:
                    delay = backoff_delays[attempt]
                    logger.info(
                        "Rate-limited (429) fetching image for %s, "
                        "retrying in %ds (attempt %d/%d)",
                        context, delay, attempt + 1, max_retries,
                    )
                    time.sleep(delay)
                    continue
                logger.warning(f"Failed to fetch image for {context}: {exc}")
                return None
            except Exception as exc:  # pragma: no cover - network path
                logger.warning(f"Failed to fetch image for {context}: {exc}")
                return None

        if not image_bytes:
            return None
        if not content_type.startswith("image/"):
            content_type = "image/png"
        # Optimize large images: resize to thumbnail + compress as WEBP
        if len(image_bytes) > 50_000:
            try:
                from PIL import Image as _Img
                from io import BytesIO as _BIO
                with _Img.open(_BIO(image_bytes)) as img:
                    img = img.convert("RGB")
                    img.thumbnail((480, 270), _Img.Resampling.LANCZOS)
                    buf = _BIO()
                    img.save(buf, format="WEBP", quality=72, method=4)
                    image_bytes = buf.getvalue()
                    content_type = "image/webp"
            except Exception:
                pass  # fall through with original bytes
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
        return (
            "<details>\n"
            "<summary><strong>Latest posts (auto-updated)</strong></summary>\n\n"
            "<!-- BLOG-POST-LIST:START -->\n"
            f"{inner}\n"
            "<!-- BLOG-POST-LIST:END -->\n\n"
            "</details>"
        )
