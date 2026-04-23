"""README dynamic section generator (badges, projects, and blog posts)."""

import base64
import dataclasses
import hashlib
import ipaddress
import json
import os
import re
import shutil
import time
from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from html import escape
from pathlib import Path
from typing import cast
from urllib.error import HTTPError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen
from xml.etree.ElementTree import Element

import defusedxml.ElementTree as DefusedET

from .config import ReadmeSectionsSettings, ReadmeSvgCardStyleSettings
from .metrics_svg import validate_svg_file
from .readme_svg import (
    ReadmeSvgAssetBuilder,
    SvgAssetWriter,
    SvgBlock,
    SvgBlockRenderer,
    SvgBlogCardRenderer,
    SvgCard,
    SvgCardFamily,
    SvgConnectCardRenderer,
    SvgRepoCardRenderer,
    sanitize_blog_title,
)
from .utils import get_logger

logger = get_logger(module=__name__)

FEATURED_PROJECTS_MANIFEST_FILENAME = "featured-projects.manifest.json"
FEATURED_PROJECTS_PUBLIC_MANIFEST_PATH = Path(
    "docs/public/showcase/featured-projects.manifest.json"
)
FEATURED_PROJECTS_PUBLIC_DIR = Path("docs/public/showcase/featured-projects")
_URL_RE = re.compile(r"(?:https?://|www\.)\S+", flags=re.IGNORECASE)
_TOPIC_PREFIX_RE = re.compile(r"\btopics?\b\s*[:\-]\s*", flags=re.IGNORECASE)
_PARENS_URL_RE = re.compile(r"\((?:https?://|www\.)[^)]*\)", flags=re.IGNORECASE)
_DUPLICATE_PUNCTUATION_RE = re.compile(r"\s*([,;:/|·])\s*")
_WHITESPACE_RE = re.compile(r"\s+")
_GENERIC_DESCRIPTION_RE = re.compile(
    r"^(?:"
    r"no description provided"
    r"|repository"
    r"|repo"
    r"|source code"
    r"|work in progress"
    r"|wip"
    r"|coming soon"
    r")\.?$",
    flags=re.IGNORECASE,
)
_METRICS_SECTION_RE = re.compile(
    r"(?ms)^## Metrics\n.*?(?=^## Word Clouds\n)",
)
_WAKATIME_SECTION_RE = re.compile(
    r"(?ms)(<!--START_SECTION:waka-->)(.*?)(<!--END_SECTION:waka-->)",
)
_WAKATIME_UPDATED_RE = re.compile(
    r"Last Updated on (\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2} UTC)",
)
_SUPPLEMENTAL_METRICS_ASSETS: tuple[tuple[str, str], ...] = (
    (
        "metrics-habits.svg",
        "Supplemental metrics: coding habits and recent GitHub focus",
    ),
    (
        "metrics-activity.svg",
        "Supplemental metrics: recent GitHub activity feed",
    ),
    (
        "metrics-music.svg",
        "Supplemental metrics: recently played tracks from Spotify",
    ),
    (
        "metrics-posts.svg",
        "Supplemental metrics: latest posts from X",
    ),
)
_WAKATIME_TIMESTAMP_FORMAT = "%d/%m/%Y %H:%M:%S UTC"
_WAKATIME_FRESHNESS_WINDOW = timedelta(days=3)
_ACRONYM_REPLACEMENTS = {
    "ai": "AI",
    "api": "API",
    "cli": "CLI",
    "css": "CSS",
    "db": "DB",
    "devops": "DevOps",
    "github": "GitHub",
    "html": "HTML",
    "ios": "iOS",
    "llm": "LLM",
    "ml": "ML",
    "nba": "NBA",
    "ocr": "OCR",
    "pdf": "PDF",
    "qr": "QR",
    "sdk": "SDK",
    "seo": "SEO",
    "sql": "SQL",
    "svg": "SVG",
    "ui": "UI",
    "ux": "UX",
}


@dataclass(frozen=True)
class FeaturedProjectArtifact:
    """Rendered card asset plus manifest-facing metadata."""

    card: SvgCard
    asset_name: str
    asset_src: str
    public_asset_src: str | None
    alt_text: str
    summary: str
    updated_label: str | None
    top_languages: tuple[str, ...]
    thumbnail_present: bool


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
) -> Request | None:
    if not _is_safe_remote_url(url):
        logger.warning(
            "Blocked unsafe URL for {context}: {url}", context=context, url=url
        )
        return None
    return Request(url=url, headers=headers, method="GET")


@dataclass(frozen=True)
class RepoMetadata:
    """Repository metadata fetched from the GitHub API."""

    full_name: str
    name: str
    html_url: str
    description: str | None
    stars: int
    homepage: str | None
    topics: list[str]
    updated_at: str | None
    # additional metadata exposed for featured cards
    created_at: str | None = None
    size_kb: int | None = None
    forks: int | None = None
    language: str | None = None
    open_graph_image_url: str | None = None
    languages: dict[str, int] | None = None
    open_issues: int | None = None
    license_spdx: str | None = None


@dataclass(frozen=True)
class BlogPost:
    """A single blog post item from RSS/Atom."""

    title: str
    url: str
    image_url: str | None = None


class GitHubRepoClient:
    """Simple GitHub API client for repository metadata."""

    def __init__(self, timeout: float = 10.0) -> None:
        self.timeout = timeout

    def fetch_repo_metadata(self, full_name: str) -> RepoMetadata | None:
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
            logger.warning(f"Failed to fetch repo metadata for {full_name}: {exc}")
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
            size_kb=int(payload.get("size", 0))
            if payload.get("size") is not None
            else None,
            forks=int(payload.get("forks_count", 0))
            if payload.get("forks_count") is not None
            else None,
            language=payload.get("language") or None,
            open_graph_image_url=payload.get("open_graph_image_url") or None,
            open_issues=int(payload.get("open_issues_count", 0))
            if payload.get("open_issues_count") is not None
            else None,
            license_spdx=(payload.get("license") or {}).get("spdx_id") or None,
        )

    def fetch_repo_languages(
        self,
        full_name: str,
    ) -> dict[str, int] | None:
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
                "Failed to fetch languages for %s: %s",
                full_name,
                exc,
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
            logger.warning(
                "Failed to fetch blog feed {feed_url}: {exc}",
                feed_url=feed_url,
                exc=exc,
            )
            return []

        try:
            root = DefusedET.fromstring(body)
        except DefusedET.ParseError as exc:
            logger.warning(
                "Invalid blog feed XML from {feed_url}: {exc}",
                feed_url=feed_url,
                exc=exc,
            )
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
            image_url: str | None = None
            enc = item.find("enclosure")
            if enc is not None:
                enc_url = (enc.get("url") or "").strip()
                enc_type = (enc.get("type") or "").strip().lower()
                if enc_url and enc_type.startswith("image/"):
                    image_url = enc_url
            posts.append(
                BlogPost(
                    title=title,
                    url=link,
                    image_url=image_url,
                )
            )
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
        "    stargazers(first:100, after:$after, "
        "orderBy:{field:STARRED_AT, direction:ASC}) {"
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
        series_start: datetime | None = None,
    ) -> list[int] | None:
        """Return cumulative star counts sampled to *sample* time bins."""
        parts = full_name.split("/", 1)
        if len(parts) != 2:
            logger.warning("Invalid repo full_name: %s", full_name)
            return None

        owner, name = parts
        timestamps: list[datetime] = []
        cursor: str | None = None
        max_pages = 50
        page_count = 0

        while True:
            page_count += 1
            if page_count > max_pages:
                logger.warning(
                    "Star history pagination limit reached (%d pages)",
                    max_pages,
                )
                break

            variables: dict[str, object] = {"owner": owner, "name": name}
            if cursor is not None:
                variables["after"] = cursor

            body = json.dumps({"query": self._QUERY, "variables": variables}).encode(
                "utf-8"
            )
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

        # Bucket into *sample* evenly-spaced time bins from repo creation (when
        # available) or first star to now so low-star repos still show early
        # zero history instead of collapsing to a flat line.
        timestamps.sort()
        t_start = timestamps[0]
        if series_start is not None:
            normalized_start = (
                series_start
                if series_start.tzinfo is not None
                else series_start.replace(tzinfo=UTC)
            )
            if normalized_start < t_start:
                t_start = normalized_start
        t_end = datetime.now(UTC)
        if t_end <= t_start:
            t_end = timestamps[-1]

        total_seconds = (t_end - t_start).total_seconds() or 1.0
        bin_width = total_seconds / sample

        # Build cumulative counts at each bin boundary
        sampled: list[int] = []
        ts_idx = 0
        for b in range(sample):
            bin_end = t_start.timestamp() + (b + 1) * bin_width
            while (
                ts_idx < len(timestamps) and timestamps[ts_idx].timestamp() <= bin_end
            ):
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

                token = (
                    subprocess.check_output(
                        ["gh", "auth", "token"],
                        stderr=subprocess.DEVNULL,
                        timeout=5,
                    )
                    .decode()
                    .strip()
                    or None
                )
            except Exception:
                pass
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers


class BlogMetadataClient:
    """Resolve hero imagery and descriptions for blog posts."""

    def __init__(self, timeout: float = 10.0) -> None:
        self.timeout = timeout

    def fetch_metadata(self, url: str) -> dict[str, str | None]:
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
    ) -> str | None:
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
    _CARD_STYLE_FIELDS = ("variant", "transparent_canvas", "show_title")

    def __init__(
        self,
        settings: ReadmeSectionsSettings,
        repo_client: GitHubRepoClient | None = None,
        blog_client: BlogFeedClient | None = None,
        star_history_client: StarHistoryClient | None = None,
        blog_metadata_client: BlogMetadataClient | None = None,
    ) -> None:
        self.settings = settings
        self.repo_client = repo_client or GitHubRepoClient()
        self.blog_client = blog_client or BlogFeedClient()
        self.star_history_client = star_history_client or StarHistoryClient()
        self.blog_metadata_client = blog_metadata_client or BlogMetadataClient()
        self.svg_builder: ReadmeSvgAssetBuilder | None = None
        if self.settings.svg.enabled:
            self.svg_builder = ReadmeSvgAssetBuilder(
                output_dir=self.settings.svg.output_dir
            )

    def generate(self) -> Path:
        """Render dynamic sections and inject them into README."""
        readme_path = Path(self.settings.readme_path)
        if not readme_path.exists():
            logger.warning(
                "README not found at {readme_path}, skipping injection",
                readme_path=readme_path,
            )
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
        content = self._postprocess_static_sections(content, readme_path=readme_path)
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

    def _postprocess_static_sections(self, content: str, *, readme_path: Path) -> str:
        content = self._rewrite_metrics_section(content, readme_path=readme_path)
        return self._rewrite_wakatime_section(content)

    def _rewrite_metrics_section(self, content: str, *, readme_path: Path) -> str:
        metrics_dir = readme_path.parent / ".github" / "assets" / "img"
        body_lines = [
            "<table><tbody>",
            "<tr>",
            '<td valign="top" width="50%"><img src=".github/assets/img/metrics.svg" alt="GitHub metrics: contributions, languages, topics, and community signals" width="100%" loading="lazy"/></td>',
            '<td valign="top" width="50%"><img src=".github/assets/img/metrics.additional.svg" alt="Additional metrics: featured repositories, recently starred repositories, and stargazers" width="100%" loading="lazy"/></td>',
            "</tr>",
            "</tbody></table>",
        ]

        valid_supplemental_assets = [
            (filename, alt_text)
            for filename, alt_text in _SUPPLEMENTAL_METRICS_ASSETS
            if validate_svg_file(metrics_dir / filename).is_valid
        ]
        if valid_supplemental_assets:
            body_lines.extend(["", "<table><tbody>"])
            for index in range(0, len(valid_supplemental_assets), 2):
                pair = valid_supplemental_assets[index : index + 2]
                body_lines.append("<tr>")
                for filename, alt_text in pair:
                    body_lines.append(
                        '<td valign="top" width="50%"><img '
                        f'src=".github/assets/img/{filename}" '
                        f'alt="{escape(alt_text)}" width="100%" loading="lazy"/></td>'
                    )
                if len(pair) == 1:
                    body_lines.append('<td valign="top" width="50%"></td>')
                body_lines.append("</tr>")
            body_lines.extend(["</tbody></table>"])

        body = "\n".join(body_lines)
        replacement = f"## Metrics\n\n{body}\n\n"
        if not _METRICS_SECTION_RE.search(content):
            logger.warning("Metrics section heading not found in README.")
            return content
        return _METRICS_SECTION_RE.sub(replacement, content, count=1)

    def _rewrite_wakatime_section(self, content: str) -> str:
        match = _WAKATIME_SECTION_RE.search(content)
        if not match:
            return content
        inner = match.group(2)
        updated_match = _WAKATIME_UPDATED_RE.search(inner)
        if updated_match is not None:
            try:
                updated_at = datetime.strptime(
                    updated_match.group(1),
                    _WAKATIME_TIMESTAMP_FORMAT,
                ).replace(tzinfo=UTC)
            except ValueError:
                updated_at = None
            if updated_at is not None:
                if datetime.now(UTC) - updated_at <= _WAKATIME_FRESHNESS_WINDOW:
                    return content
                detail = (
                    f"Latest available update was {updated_match.group(1)}, which is "
                    "outside the freshness window."
                )
            else:
                detail = "The latest WakaTime timestamp could not be parsed."
        else:
            detail = "No fresh WakaTime timestamp was found in the generated section."

        replacement = (
            f"{match.group(1)}\n"
            "> WakaTime stats are temporarily unavailable right now. "
            f"{detail}\n"
            f"{match.group(3)}"
        )
        return content[: match.start()] + replacement + content[match.end() :]

    def _render_top_badges(self) -> str:
        svg_cards: list[SvgCard] = []
        if not self.settings.social_links:
            fallback_card: SvgCard | None = None
            if self.settings.featured_repos:
                owner = (
                    self.settings.featured_repos[0].full_name.split("/", 1)[0].strip()
                )
                if owner:
                    fallback_card = SvgCard(
                        title="GitHub",
                        url=f"https://github.com/{owner}",
                        icon="GH",
                        accent="181717",
                    )
            elif self.settings.blog_feed_url:
                parsed_feed = urlparse(self.settings.blog_feed_url)
                host = parsed_feed.netloc.replace("www.", "")
                if host and parsed_feed.scheme in {"http", "https"}:
                    fallback_card = SvgCard(
                        title=host,
                        url=f"{parsed_feed.scheme}://{host}",
                        accent="334155",
                    )
            if fallback_card is not None:
                parsed = urlparse(fallback_card.url or "")
                host = parsed.netloc.replace("www.", "")
                fallback_card = self._set_card_icon_data_uri(
                    fallback_card,
                    url=fallback_card.url,
                    host=host,
                    label=fallback_card.title,
                    accent=fallback_card.accent,
                )
                svg_cards.append(fallback_card)
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
            card = self._set_card_icon_data_uri(
                card,
                url=link.url,
                host=host,
                label=link.label,
                accent=link.color,
            )
            svg_cards.append(card)
        # Render per-card SVGs
        card_embeds: list[tuple[str, str]] = []

        if self._svg_section_enabled("top_contact"):
            writer = SvgAssetWriter(
                output_dir=self.settings.svg.output_dir,
            )
            for card in svg_cards:
                asset = (
                    "connect-"
                    f"{self._slugify_asset_segment(card.title, fallback='link')}"
                )
                writer.write(
                    asset_name=asset,
                    svg_content=self._render_card_svg_asset(
                        family="connect",
                        card=card,
                        width=140,
                        height=130,
                        section_title="Connect",
                    ),
                )
                src = (Path(self.settings.svg.output_dir) / f"{asset}.svg").as_posix()
                card_embeds.append((card.url or "#", src))

        result: list[str] = []
        if card_embeds:
            imgs = []
            for url, src in card_embeds:
                imgs.append(
                    f'<a href="{escape(url)}" target="_blank"'
                    ' rel="noopener noreferrer">'
                    f'<img src="{escape(src)}" width="140"'
                    f' loading="lazy"/></a>'
                )
            result.append('<p align="center">' + "\n".join(imgs) + "</p>")
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
        if any(
            kw in host for kw in ("linkedin.com", "kaggle.com", "x.com", "twitter.com")
        ):
            return "SOCIAL"
        return "WEBSITE"

    def _set_card_icon_data_uri(
        self,
        card: SvgCard,
        *,
        url: str | None = None,
        host: str | None = None,
        label: str | None = None,
        accent: str | None = None,
    ) -> SvgCard:
        icon_data_uri = self._brand_icon_data_uri(
            url=url,
            host=host,
            label=label,
            accent=accent,
        )
        if icon_data_uri:
            return dataclasses.replace(card, icon_data_uri=icon_data_uri)
        return card

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
    ) -> str | None:
        """Fetch an icon from the Simple Icons CDN and wrap it in a 64x64 SVG.

        Returns a ``data:image/svg+xml;base64,...`` URI on success, or *None*
        if the network request fails so the caller can fall back to a
        hardcoded glyph.
        """
        cdn_url = f"https://cdn.jsdelivr.net/npm/simple-icons@v11/icons/{slug}.svg"
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
                r'\s*xmlns(?::[a-z]+)?="[^"]*"',
                "",
                child_str,
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
        return "data:image/svg+xml;base64," + base64.b64encode(
            wrapper_svg.encode("utf-8")
        ).decode("ascii")

    # -- w4w.dev favicon fetcher -----------------------------------------

    def _fetch_w4w_favicon_data_uri(self) -> str | None:
        """Fetch w4w.dev logo, convert to PNG, return as data URI."""
        # Try local optimized ICO first (checked into repo assets)
        local_ico = Path(".github/assets/img/favicon.ico")
        if local_ico.exists():
            ico_bytes = local_ico.read_bytes()
            try:
                from io import BytesIO as _BIO

                from PIL import Image as _Img

                with _Img.open(_BIO(ico_bytes)) as img:
                    img = img.resize((64, 64), _Img.Resampling.LANCZOS)
                    buf = _BIO()
                    img.save(buf, format="PNG")
                    png_b64 = base64.b64encode(buf.getvalue()).decode("ascii")
                    return f"data:image/png;base64,{png_b64}"
            except Exception:
                pass
        # Fall back to remote fetch
        for candidate in (
            "https://w4w.dev/logo.webp",
            "https://w4w.dev/favicon.ico",
        ):
            result = self._fetch_remote_image_data_uri(
                candidate,
                context="w4w.dev favicon",
            )
            if result:
                return result
        return None

    # -- Brand icon resolution -------------------------------------------

    def _brand_icon_data_uri(
        self,
        *,
        url: str | None = None,
        host: str | None = None,
        label: str | None = None,
        accent: str | None = None,
    ) -> str | None:
        normalized_host = (host or "").strip().replace("www.", "").lower()
        if not normalized_host and url:
            normalized_host = urlparse(url).netloc.strip().replace("www.", "").lower()

        accent_hex = (
            accent.lstrip("#")
            if accent and re.fullmatch(r"[0-9a-fA-F]{6}", accent.lstrip("#"))
            else None
        )

        # --- X/Twitter: use Unicode 𝕏 glyph instead of CDN fetch ---------
        if normalized_host.endswith("x.com") or normalized_host.endswith("twitter.com"):
            x_svg = (
                "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'>"
                "<rect width='64' height='64' rx='14' fill='#000'/>"
                "<text x='32' y='46' text-anchor='middle' fill='#fff' "
                "font-family='serif' font-size='40' font-weight='700'>"
                "\U0001d54f</text>"
                "</svg>"
            )
            return "data:image/svg+xml;base64," + base64.b64encode(
                x_svg.encode("utf-8")
            ).decode("ascii")

        # --- Try Simple Icons CDN first for known platforms ---------------
        for suffix, (slug, bg_color) in self._SIMPLE_ICON_MAP.items():
            if normalized_host.endswith(suffix):
                si_uri = self._fetch_simple_icon_data_uri(
                    slug=slug,
                    bg_color=bg_color,
                    fg_color="white",
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
        glyph: str | None = None
        background: str | None = None
        foreground: str | None = None
        if normalized_host.endswith("linkedin.com"):
            background, foreground = ("0A66C2", "FFFFFF")
            glyph = (
                f"<circle cx='21.5' cy='19.5' r='4.5' fill='#{foreground}'/>"
                f"<rect x='17' y='27' width='9' height='20' "
                f"rx='2' fill='#{foreground}'/>"
                f"<path d='M34 27h8v3.2c1.5-2.2 3.9-3.8 7.4-3.8 "
                "7.3 0 8.6 4.8 8.6 11.2V47h-9v-6.6c0-3.4-.6-5.8-3.4-5.8"
                f"-2.9 0-4.1 2.1-4.1 5.8V47h-8.5z' fill='#{foreground}'/>"
            )
        elif normalized_host.endswith("kaggle.com"):
            background, foreground = ("20BEFF", "062F40")
            glyph = (
                f"<path d='M20 15h7v15.4L38.2 15h9.2L34 31.4 "
                f"47.6 49h-9.3L27 34.2V49h-7z' fill='#{foreground}'/>"
            )
        elif normalized_host.endswith("x.com") or normalized_host.endswith(
            "twitter.com"
        ):
            background, foreground = ("000000", "FFFFFF")
            glyph = (
                f"<path d='M15 15h10.5l8.6 11.7L43.3 15H53L38.9 32.2 "
                f"53.2 49H42.7l-9.4-12.1L23.6 49H14l14.4-17.6z' "
                f"fill='#{foreground}'/>"
            )
        elif normalized_host.endswith("github.com"):
            background, foreground = ("181717", "FFFFFF")
            glyph = (
                f"<path d='M22.5 24 18 16m23.5 8L46 16' "
                f"stroke='#{foreground}' stroke-width='3.8' "
                "stroke-linecap='round' fill='none'/>"
                f"<circle cx='32' cy='34' r='13' fill='#{foreground}'/>"
                f"<circle cx='27.2' cy='33' r='1.7' fill='#{background}'/>"
                f"<circle cx='36.8' cy='33' r='1.7' fill='#{background}'/>"
                f"<path d='M27.8 39.3c1.2 1.2 7.2 1.2 8.4 0' "
                f"stroke='#{background}' stroke-width='2.1' "
                "stroke-linecap='round' fill='none'/>"
            )
        elif normalized_host.endswith("w4w.dev"):
            background, foreground = ("0F172A", "22D3EE")
            glyph = (
                f"<path d='M11 44 19 20 27 44 35 20 43 44 51 20' "
                f"stroke='#{foreground}' stroke-width='4' "
                "stroke-linecap='round' stroke-linejoin='round' fill='none'/>"
                f"<circle cx='19' cy='20' r='2.6' fill='#{foreground}'/>"
                f"<circle cx='35' cy='20' r='2.6' fill='#{foreground}'/>"
                f"<circle cx='51' cy='20' r='2.6' fill='#{foreground}'/>"
            )
        elif (url and urlparse(url).scheme == "mailto") or (
            label and "email" in label.lower()
        ):
            background, foreground = (accent_hex or "EA4335", "FFFFFF")
            glyph = (
                f"<rect x='12' y='20' width='40' height='24' rx='4' "
                f"fill='none' stroke='#{foreground}' stroke-width='3'/>"
                f"<path d='M14 23.5 32 35l18-11.5' fill='none' "
                f"stroke='#{foreground}' stroke-width='3' "
                "stroke-linecap='round' stroke-linejoin='round'/>"
            )
        elif normalized_host or label:
            background, foreground = (accent_hex or "334155", "E2E8F0")
            glyph = (
                f"<circle cx='32' cy='32' r='13' fill='none' "
                f"stroke='#{foreground}' stroke-width='3'/>"
                f"<path d='M19 32h26M32 19.5c4.2 4.4 4.2 20.6 0 25"
                "M32 19.5c-4.2 4.4-4.2 20.6 0 25' "
                f"stroke='#{foreground}' stroke-width='2.4' "
                "stroke-linecap='round' fill='none'/>"
            )
        if not glyph or not background or not foreground:
            return None

        icon_svg = (
            "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'>"
            f"<rect width='64' height='64' rx='14' fill='#{background}'/>"
            f"{glyph}"
            "</svg>"
        )
        return "data:image/svg+xml;base64," + base64.b64encode(
            icon_svg.encode("utf-8")
        ).decode("ascii")

    def _featured_layout_plan(self, repo_count: int) -> dict[str, int]:
        if repo_count <= 1:
            return {
                "columns": 1,
                "width": 1100,
                "height": 236,
            }
        if repo_count <= 4:
            return {
                "columns": 2,
                "width": 540,
                "height": 214,
            }
        return {
            "columns": 3,
            "width": 360,
            "height": 216,
        }

    def _featured_public_surface_dir(self) -> Path | None:
        output_dir = Path(self.settings.svg.output_dir)
        trailing_parts = output_dir.parts[-4:]
        if trailing_parts != (".github", "assets", "img", "readme"):
            return None
        if FEATURED_PROJECTS_PUBLIC_MANIFEST_PATH.parent.exists():
            return FEATURED_PROJECTS_PUBLIC_DIR
        return None

    def _cleanup_featured_assets(
        self,
        *,
        output_dir: Path,
        public_surface_dir: Path | None,
    ) -> None:
        for path in output_dir.glob("featured-card-*.svg"):
            path.unlink(missing_ok=True)
        (output_dir / FEATURED_PROJECTS_MANIFEST_FILENAME).unlink(missing_ok=True)
        if public_surface_dir is None:
            return
        public_surface_dir.mkdir(parents=True, exist_ok=True)
        for path in public_surface_dir.glob("featured-card-*.svg"):
            path.unlink(missing_ok=True)
        FEATURED_PROJECTS_PUBLIC_MANIFEST_PATH.unlink(missing_ok=True)

    def _write_featured_manifest(
        self,
        *,
        output_dir: Path,
        manifest: dict[str, object],
        public_surface_dir: Path | None,
    ) -> Path:
        manifest_path = output_dir / FEATURED_PROJECTS_MANIFEST_FILENAME
        manifest_path.write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        if public_surface_dir is not None:
            FEATURED_PROJECTS_PUBLIC_MANIFEST_PATH.write_text(
                json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
        return manifest_path

    def _humanize_topic(self, topic: str) -> str:
        cleaned = topic.replace("_", " ").replace("-", " ").strip()
        if not cleaned:
            return ""
        words: list[str] = []
        for raw_word in cleaned.split():
            normalized = raw_word.casefold()
            replacement = _ACRONYM_REPLACEMENTS.get(normalized)
            if replacement:
                words.append(replacement)
            elif raw_word.isupper():
                words.append(raw_word)
            else:
                words.append(raw_word.capitalize())
        return " ".join(words)

    def _topic_summary(self, topics: Sequence[str]) -> str | None:
        cleaned_topics: list[str] = []
        for topic in topics:
            humanized = self._humanize_topic(topic)
            if not humanized:
                continue
            if humanized.casefold() in {item.casefold() for item in cleaned_topics}:
                continue
            cleaned_topics.append(humanized)
            if len(cleaned_topics) == 3:
                break
        if not cleaned_topics:
            return None
        if len(cleaned_topics) == 1:
            return f"{cleaned_topics[0]} workflows and tooling."
        if len(cleaned_topics) == 2:
            return f"{cleaned_topics[0]} and {cleaned_topics[1]} workflows."
        return (
            f"{cleaned_topics[0]}, {cleaned_topics[1]}, and "
            f"{cleaned_topics[2]} workflows."
        )

    def _clean_summary_text(
        self,
        text: str,
        *,
        homepage: str | None = None,
    ) -> str:
        summary = _PARENS_URL_RE.sub(" ", text)
        summary = _URL_RE.sub(" ", summary)
        summary = _TOPIC_PREFIX_RE.sub("", summary)
        summary = re.sub(r"\btopics?\b", " ", summary, flags=re.IGNORECASE)
        summary = summary.replace("(", " ").replace(")", " ")
        summary = re.sub(r"\bfrom\s+and\b", "and", summary, flags=re.IGNORECASE)

        if homepage:
            try:
                parsed_homepage = urlparse(homepage)
            except ValueError:
                parsed_homepage = None
            candidates = {homepage}
            if parsed_homepage is not None:
                host = parsed_homepage.netloc.replace("www.", "").strip()
                if host:
                    candidates.add(host)
                if parsed_homepage.path and parsed_homepage.path != "/":
                    candidates.add(parsed_homepage.path.strip("/"))
                    if host:
                        candidates.add(f"{host}/{parsed_homepage.path.strip('/')}")
            for candidate in candidates:
                if candidate:
                    summary = re.sub(
                        re.escape(candidate),
                        " ",
                        summary,
                        flags=re.IGNORECASE,
                    )

        summary = _DUPLICATE_PUNCTUATION_RE.sub(r"\1 ", summary)
        summary = re.sub(r"\s*/\s*", "/", summary)
        summary = re.sub(r",\s*\.", ".", summary)
        summary = re.sub(r"\s+\.", ".", summary)
        summary = re.sub(r"\s+([,.;:!?])", r"\1", summary)
        summary = re.sub(r"([,;:/|·]){2,}", r"\1", summary)
        summary = _WHITESPACE_RE.sub(" ", summary)
        return summary.strip(" -–—,;:/|·.")

    def _shorten_summary(
        self,
        summary: str,
        *,
        compact: bool,
    ) -> str:
        del compact
        return summary.strip()

    def _normalize_project_summary(
        self,
        metadata: RepoMetadata,
        *,
        compact: bool,
    ) -> str:
        summary = self._clean_summary_text(
            metadata.description or "",
            homepage=metadata.homepage,
        )
        if not summary or _GENERIC_DESCRIPTION_RE.fullmatch(summary):
            summary = self._topic_summary(metadata.topics) or ""
        if not summary and metadata.language:
            summary = f"Source code and project assets built with {metadata.language}."
        if not summary:
            summary = "Source code and project assets."
        return self._shorten_summary(summary, compact=compact)

    def _featured_card_alt_text(self, title: str, summary: str) -> str:
        if summary:
            return f"Featured project card for {title}: {summary}"
        return f"Featured project card for {title}"

    def _top_languages(
        self,
        languages: dict[str, int] | None,
    ) -> tuple[str, ...]:
        if not languages:
            return ()
        ranked = sorted(languages.items(), key=lambda item: item[1], reverse=True)
        return tuple(language for language, _ in ranked[:2])

    def _featured_manifest(
        self,
        *,
        artifacts: Sequence[FeaturedProjectArtifact],
        output_dir: Path,
        public_surface_dir: Path | None,
    ) -> dict[str, object]:
        return {
            "generated_at": datetime.now(tz=UTC).isoformat(),
            "output_dir": str(output_dir),
            "public_surface_dir": str(public_surface_dir)
            if public_surface_dir
            else None,
            "priority_contract": "featured_repos order is authoritative",
            "projects": [
                {
                    "full_name": artifact.card.kicker or artifact.card.title,
                    "title": artifact.card.title,
                    "url": artifact.card.url,
                    "summary": artifact.summary,
                    "stars": self._extract_numeric_meta_value(
                        artifact.card.meta, "star"
                    ),
                    "forks": self._extract_numeric_meta_value(
                        artifact.card.meta, "fork"
                    ),
                    "updated_label": artifact.updated_label,
                    "top_languages": list(artifact.top_languages),
                    "license": artifact.card.license_spdx,
                    "thumbnail_present": artifact.thumbnail_present,
                    "svg_asset_path": artifact.public_asset_src or artifact.asset_src,
                    "alt_text": artifact.alt_text,
                }
                for artifact in artifacts
            ],
        }

    def _extract_numeric_meta_value(
        self,
        meta: Sequence[str],
        kind: str,
    ) -> int | None:
        patterns = {
            "star": re.compile(r"[★☆]\s*([\d,]+)"),
            "fork": re.compile(r"[⑂]\s*([\d,]+)"),
        }
        pattern = patterns[kind]
        for item in meta:
            match = pattern.match(item.strip())
            if match:
                return int(match.group(1).replace(",", ""))
        return None

    def _render_featured_table(
        self,
        *,
        artifacts: Sequence[FeaturedProjectArtifact],
        columns: int,
        section_label: str | None = None,
    ) -> str:
        if not artifacts:
            return ""
        column_width = f"{100 / columns:.2f}%"
        lines: list[str] = []
        if section_label:
            lines.append(f'<p align="center"><sub>{escape(section_label)}</sub></p>')
        lines.append("<table><tbody>")
        for row_start in range(0, len(artifacts), columns):
            lines.append("<tr>")
            for offset in range(columns):
                idx = row_start + offset
                if idx >= len(artifacts):
                    lines.append(f'<td width="{column_width}"></td>')
                    continue
                artifact = artifacts[idx]
                lines.append(
                    f'<td valign="top" width="{column_width}">'
                    f'<a href="{escape(artifact.card.url or "#")}"'
                    f' target="_blank" rel="noopener noreferrer">'
                    f'<img src="{escape(artifact.asset_src)}" width="100%"'
                    f' alt="{escape(artifact.alt_text)}"'
                    f' loading="lazy"/></a></td>'
                )
            lines.append("</tr>")
        lines.append("</tbody></table>")
        return "\n".join(lines)

    def _render_featured_projects(self) -> str:
        repos = self.settings.featured_repos
        # Fetch all repo metadata + languages in parallel
        metadata_by_name: dict[str, RepoMetadata | None] = {}
        languages_by_name: dict[str, dict[str, int] | None] = {}
        if repos:
            max_workers = min(16, len(repos) * 2)
            with ThreadPoolExecutor(max_workers=max_workers) as pool:
                meta_futures = {
                    pool.submit(self.repo_client.fetch_repo_metadata, repo.full_name): (
                        "meta",
                        repo.full_name,
                    )
                    for repo in repos
                }
                lang_futures = {
                    pool.submit(
                        self.repo_client.fetch_repo_languages,
                        repo.full_name,
                    ): ("lang", repo.full_name)
                    for repo in repos
                }
                for future in as_completed({**meta_futures, **lang_futures}):
                    tag = meta_futures.get(future) or lang_futures.get(future)
                    if tag is None:
                        continue  # pragma: no cover
                    kind, name = tag
                    try:
                        if kind == "meta":
                            metadata_by_name[name] = cast(
                                RepoMetadata | None, future.result()
                            )
                        else:
                            languages_by_name[name] = cast(
                                dict[str, int] | None, future.result()
                            )
                    except Exception as exc:  # pragma: no cover
                        logger.warning(
                            "Failed to fetch %s for %s: %s",
                            kind,
                            name,
                            exc,
                        )
                        if kind == "meta":
                            metadata_by_name[name] = None
                        else:
                            languages_by_name[name] = None
        if not repos:
            lines = ["- No featured repositories configured."]
            return "\n".join(lines)

        layout = self._featured_layout_plan(len(repos))
        artifacts: list[FeaturedProjectArtifact] = []

        output_dir = Path(self.settings.svg.output_dir)
        public_surface_dir = self._featured_public_surface_dir()
        if self._svg_section_enabled("featured_projects"):
            output_dir.mkdir(parents=True, exist_ok=True)
            self._cleanup_featured_assets(
                output_dir=output_dir,
                public_surface_dir=public_surface_dir,
            )
            writer = SvgAssetWriter(output_dir=self.settings.svg.output_dir)
        else:
            writer = None

        for repo in repos:
            metadata = metadata_by_name.get(repo.full_name)
            languages = languages_by_name.get(repo.full_name)
            card = self._build_project_svg_card(
                repo.full_name,
                metadata,
                languages=languages,
            )
            repo_identity = card.kicker or card.title
            asset_name = (
                f"featured-card-"
                f"{self._slugify_asset_segment(repo_identity, fallback='repo')}"
            )
            canonical_src = (output_dir / f"{asset_name}.svg").as_posix()
            public_src = (
                f"/showcase/featured-projects/{asset_name}.svg"
                if public_surface_dir is not None
                else None
            )
            if writer is not None:
                svg_markup = self._render_card_svg_asset(
                    family="featured",
                    card=card,
                    width=layout["width"],
                    height=layout["height"],
                    section_title="Featured Projects",
                )
                writer.write(asset_name=asset_name, svg_content=svg_markup)
                if public_surface_dir is not None:
                    public_surface_dir.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(
                        output_dir / f"{asset_name}.svg",
                        public_surface_dir / f"{asset_name}.svg",
                    )
            summary = next(iter(card.lines), "")
            artifact = FeaturedProjectArtifact(
                card=card,
                asset_name=asset_name,
                asset_src=canonical_src,
                public_asset_src=public_src,
                alt_text=self._featured_card_alt_text(card.title, summary),
                summary=summary,
                updated_label=(
                    f"Updated {relative}"
                    if (relative := self._relative_time(card.updated_at))
                    else None
                ),
                top_languages=self._top_languages(languages),
                thumbnail_present=bool(card.background_image),
            )
            artifacts.append(artifact)

        if writer is not None and artifacts:
            self._write_featured_manifest(
                output_dir=output_dir,
                manifest=self._featured_manifest(
                    artifacts=artifacts,
                    output_dir=output_dir,
                    public_surface_dir=public_surface_dir,
                ),
                public_surface_dir=public_surface_dir,
            )

        return self._render_featured_table(
            artifacts=artifacts,
            columns=layout["columns"],
        )

    def _build_project_svg_card(
        self,
        repo_full_name: str,
        metadata: RepoMetadata | None,
        languages: dict[str, int] | None = None,
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
            card = self._set_card_icon_data_uri(
                card,
                url=repo_url,
                label=repo_name,
            )
            return card

        summary = self._normalize_project_summary(metadata, compact=False)
        lines = [summary]
        info_bits: list[str] = []
        if metadata.language:
            info_bits.append(f"lang:{metadata.language}")
        info_bits.append(f"★ {metadata.stars:,}")
        if metadata.forks:
            info_bits.append(f"⑂ {metadata.forks:,}")
        relative = self._relative_time(metadata.updated_at)
        if relative:
            info_bits.append(f"Updated {relative}")
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
            license_spdx=metadata.license_spdx,
            open_issues=metadata.open_issues,
        )

        card = self._set_card_icon_data_uri(
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
                (
                    f'<p align="center"><sub>📡 Source: '
                    f'<a href="{feed_url}">RSS feed</a></sub></p>'
                ),
            ]
            if svg_embed:
                lines.insert(0, f'<p align="center">{svg_embed}</p>')
            return "\n".join(lines)

        # Fetch blog post metadata in parallel
        metadata_by_url: dict[str, dict[str, str | None]] = {}
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
            host = metadata.get("host") or urlparse(post.url).netloc.replace("www.", "")
            summary = metadata.get("summary") or "Tap to read the full story."
            published = metadata.get("published")
            # Sanitize title — strip trailing "update" noise (anchored)
            clean_title = sanitize_blog_title(post.title)
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
            hero_data_uri: str | None = None
            # Try RSS enclosure first, then og:image from HTML
            hero_url = post.image_url or metadata.get("hero_image")
            if hero_url:
                absolute_hero = urljoin(post.url, hero_url)
                hero_data_uri = self._fetch_remote_image_data_uri(
                    absolute_hero,
                    context="blog hero",
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
            svg_cards.append(card)
            meta_bits = [bit for bit in card_meta if bit]
            line = f"- [{escape(clean_title)}]({escape(post.url)})"
            if meta_bits:
                line += f" — {escape(' · '.join(meta_bits))}"
            fallback_lines.append(line)
        card_embeds: list[tuple[str, str]] = []

        if self._svg_section_enabled("blog_posts"):
            writer = SvgAssetWriter(
                output_dir=self.settings.svg.output_dir,
            )
            used_assets: set[str] = set()
            for idx, card in enumerate(svg_cards):
                asset = self._make_blog_asset_name(
                    card=card,
                    index=idx,
                    used_assets=used_assets,
                )
                writer.write(
                    asset_name=asset,
                    svg_content=self._render_card_svg_asset(
                        family="blog",
                        card=card,
                        width=480,
                        height=150,
                        section_title="Latest Blog Posts",
                    ),
                )
                src = (Path(self.settings.svg.output_dir) / f"{asset}.svg").as_posix()
                card_embeds.append((card.url or "#", src))

        result: list[str] = []
        if card_embeds:
            imgs = []
            for url, src in card_embeds:
                imgs.append(
                    f'<a href="{escape(url)}" target="_blank" rel="noopener noreferrer">'
                    f'<img src="{escape(src)}" width="500"'
                    f' loading="lazy"/></a>'
                )
            result.append('<p align="center">' + "\n".join(imgs) + "</p>")
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
        return f'<img src="{src}" alt="{alt}" width="{renderer.width}" loading="lazy"/>'

    def _svg_asset_src(self, asset_name: str) -> str:
        filename = re.sub(r"[^a-zA-Z0-9_-]+", "-", asset_name).strip("-_")
        normalized = filename or "section"
        return (Path(self.settings.svg.output_dir) / f"{normalized}.svg").as_posix()

    def _resolved_card_style(self, family: str) -> ReadmeSvgCardStyleSettings:
        default_style = self.settings.svg.card_styles.default
        family_style = getattr(self.settings.svg.card_styles, family)
        family_fields = getattr(family_style, "model_fields_set", set())
        updates = {
            field: getattr(family_style, field)
            for field in self._CARD_STYLE_FIELDS
            if field in family_fields
        }
        return default_style.model_copy(update=updates)

    def _render_card_svg_asset(
        self,
        *,
        family: str,
        card: SvgCard,
        width: int,
        height: int,
        section_title: str,
    ) -> str:
        style = self._resolved_card_style(family)
        if style.variant == "legacy":
            renderer = SvgBlockRenderer(
                width=width,
                card_height=height,
                padding=16,
            )
            block = SvgBlock(
                title=section_title,
                cards=(card,),
                columns=1,
                family=SvgCardFamily(family),
                show_title=style.show_title,
                transparent_canvas=style.transparent_canvas,
            )
            return renderer.render(block)
        if family == "connect":
            return SvgConnectCardRenderer(width=width, height=height).render_card(card)
        if family == "featured":
            return SvgRepoCardRenderer(width=width, height=height).render_card(card)
        if family == "blog":
            return SvgBlogCardRenderer(width=width, height=height).render_card(card)
        raise ValueError(f"Unsupported card family: {family}")

    def _slugify_asset_segment(
        self,
        value: str,
        *,
        fallback: str,
        max_length: int | None = None,
    ) -> str:
        slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", value).strip("-_").lower()
        if max_length is not None:
            slug = slug[:max_length].rstrip("-_")
        return slug or fallback

    def _make_blog_asset_name(
        self,
        *,
        card: SvgCard,
        index: int,
        used_assets: set[str],
    ) -> str:
        base = self._slugify_asset_segment(
            card.title,
            fallback=f"post-{index}",
            max_length=40,
        )
        asset = f"blog-{base}"
        if asset not in used_assets:
            used_assets.add(asset)
            return asset

        unique_source = card.url or f"{card.title}-{index}"
        suffix = hashlib.sha1(unique_source.encode("utf-8")).hexdigest()[:8]
        deduped_base = self._slugify_asset_segment(
            card.title,
            fallback=f"post-{index}",
            max_length=31,
        )
        asset = f"blog-{deduped_base}-{suffix}"
        counter = 2
        while asset in used_assets:
            asset = f"blog-{deduped_base}-{suffix}-{counter}"
            counter += 1
        used_assets.add(asset)
        return asset

    def _build_featured_repo_fallback_line(
        self,
        repo_full_name: str,
        metadata: RepoMetadata | None,
    ) -> str:
        if metadata is None:
            repo_name = repo_full_name.split("/")[-1]
            repo_url = f"https://github.com/{repo_full_name}"
            return (
                f"- [{escape(repo_name)}]({escape(repo_url)}) "
                "— Live stats are temporarily unavailable; open repository for details."
            )
        description = self._normalize_project_summary(metadata, compact=False)
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
            logger.warning(
                "Failed to write README SVG asset {asset_name}: {exc}",
                asset_name=asset_name,
                exc=exc,
            )

    def _format_timestamp(self, timestamp: str | None) -> str | None:
        if not timestamp:
            return None
        if "T" not in timestamp:
            return timestamp
        return timestamp.split("T", maxsplit=1)[0]

    def _relative_time(self, iso_timestamp: str | None) -> str | None:
        """Convert ISO timestamp to relative time like '3d ago', '2mo ago'."""
        if not iso_timestamp:
            return None
        try:
            dt = datetime.fromisoformat(iso_timestamp.replace("Z", "+00:00"))
            delta = datetime.now(UTC) - dt
            seconds = int(delta.total_seconds())
            if seconds < 60:
                return "just now"
            minutes = seconds // 60
            if minutes < 60:
                return f"{minutes}m ago"
            hours = minutes // 60
            if hours < 24:
                return f"{hours}h ago"
            days = hours // 24
            if days < 7:
                return f"{days}d ago"
            weeks = days // 7
            if weeks < 5:
                return f"{weeks}w ago"
            months = days // 30
            if months < 12:
                return f"{months}mo ago"
            years = days // 365
            return f"{years}y ago"
        except (ValueError, TypeError):
            return None

    def _repo_background_image(
        self,
        repo_full_name: str,
        metadata: RepoMetadata | None,
    ) -> str | None:
        # 1. Prefer the API-provided OG image (avoids HTML scrape)
        if metadata and metadata.open_graph_image_url:
            api_og = metadata.open_graph_image_url
            if "opengraph.githubassets.com" not in api_og:
                data_uri = self._fetch_remote_image_data_uri(
                    api_og,
                    context=f"repo API OG image for {repo_full_name}",
                )
                if data_uri:
                    return data_uri
        # 2. Fall back to HTML scrape for custom social preview
        og_url = self._scrape_repo_og_image(repo_full_name)
        if og_url:
            data_uri = self._fetch_remote_image_data_uri(
                og_url,
                context=f"repo social preview for {repo_full_name}",
            )
            if data_uri:
                return data_uri
        # 3. Final fallback: auto-generated GitHub OG image
        fallback = f"https://opengraph.githubassets.com/1/{repo_full_name}"
        return self._fetch_remote_image_data_uri(
            fallback,
            context=f"repo preview for {repo_full_name}",
        )

    def _scrape_repo_og_image(
        self,
        repo_full_name: str,
    ) -> str | None:
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
                repo_full_name,
                exc,
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
    ) -> str | None:
        request = _build_remote_get_request(
            url=url,
            headers={"User-Agent": "readme-section-generator"},
            context=context,
        )
        if request is None:
            return None
        max_retries = 3
        backoff_delays = (1, 2, 4)
        image_bytes = b""
        content_type = "image/png"
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
                        context,
                        delay,
                        attempt + 1,
                        max_retries,
                    )
                    time.sleep(delay)
                    continue
                logger.warning(
                    "Failed to fetch image for {context}: {exc}",
                    context=context,
                    exc=exc,
                )
                return None
            except Exception as exc:  # pragma: no cover - network path
                logger.warning(
                    "Failed to fetch image for {context}: {exc}",
                    context=context,
                    exc=exc,
                )
                return None

        if not image_bytes:
            return None
        if not content_type.startswith("image/"):
            content_type = "image/png"
        # Optimize large images: resize to thumbnail + compress as WEBP
        if len(image_bytes) > 50_000:
            try:
                from io import BytesIO as _BIO

                from PIL import Image as _Img

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
        metadata: RepoMetadata | None,
    ) -> tuple[float, ...] | None:
        if metadata is None:
            return None
        history: list[int] | None = None
        if self.star_history_client:
            series_start = self._parse_iso_datetime(metadata.created_at)
            history = self.star_history_client.fetch_star_history(
                repo_full_name,
                sample=24,
                series_start=series_start,
            )
        if history:
            if metadata.stars > history[-1]:
                history = [*history[:-1], metadata.stars]
            return tuple(float(value) for value in history)
        return None

    def _parse_iso_datetime(self, value: str | None) -> datetime | None:
        if not value:
            return None
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC)

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
