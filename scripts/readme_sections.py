"""README dynamic section generator (badges, projects, and blog posts)."""

import base64
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
from .utils import get_logger

logger = get_logger(module=__name__)


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
        request = Request(
            url=f"https://api.github.com/repos/{full_name}",
            headers=self._headers(),
            method="GET",
        )
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
        request = Request(
            url=feed_url,
            headers={"User-Agent": "readme-section-generator"},
            method="GET",
        )
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
            title = (entry.findtext("atom:title", default="", namespaces=ns) or "").strip()
            link_elem = entry.find("atom:link[@rel='alternate']", ns)
            if link_elem is None:
                link_elem = entry.find("atom:link", ns)
            link = (link_elem.get("href") if link_elem is not None else "") or ""
            link = link.strip()
            if title and link:
                posts.append(BlogPost(title=title, url=link))
        return posts


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
    ) -> None:
        self.settings = settings
        self.repo_client = repo_client or GitHubRepoClient()
        self.blog_client = blog_client or BlogFeedClient()

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
        badges: list[str] = []
        separator = '<span aria-hidden="true">&nbsp;✦&nbsp;</span>'
        ornate_separator = (
            '<p align="center"><span aria-hidden="true">❈ ┈┈ ✦ ┈┈ ❈</span></p>'
        )
        for link in self.settings.social_links:
            badge_url = self._build_badge_url(
                link.label, link.color, link.logo, link.logo_color
            )
            badge = (
                f'<a href="{escape(link.url)}">'
                f'<img src="{escape(badge_url)}" alt="{escape(link.label)}"/>'
                "</a>"
            )
            badges.append(badge)
        joined = f"\n  {separator}\n  ".join(badges)
        return (
            f"{ornate_separator}\n"
            f"<p align=\"center\">\n  {joined}\n</p>\n"
            f"{ornate_separator}"
        )

    def _render_featured_projects(self) -> str:
        cards: list[str] = []
        for repo in self.settings.featured_repos:
            metadata = self.repo_client.fetch_repo_metadata(repo.full_name)
            cards.append(self._render_project_card(repo.full_name, metadata))

        if not cards:
            return "<p><em>No featured repositories configured.</em></p>"

        rows: list[str] = []
        for idx in range(0, len(cards), 2):
            left = cards[idx]
            right = cards[idx + 1] if idx + 1 < len(cards) else ""
            rows.append(
                "<tr>"
                f"<td width=\"50%\" valign=\"top\">{left}</td>"
                f"<td width=\"50%\" valign=\"top\">{right}</td>"
                "</tr>"
            )
        rows_html = "\n".join(rows)
        return f"<table role=\"presentation\">\n{rows_html}\n</table>"

    def _render_project_card(
        self,
        repo_full_name: str,
        metadata: Optional[RepoMetadata],
    ) -> str:
        if metadata is None:
            repo_url = f"https://github.com/{repo_full_name}"
            repo_name = repo_full_name.split("/")[-1]
            return (
                f"<h3><a href=\"{escape(repo_url)}\">{escape(repo_name)}</a></h3>"
                "<p><em>Unable to fetch repository metadata.</em></p>"
            )

        repo_url = metadata.html_url
        repo_name = metadata.name
        description = metadata.description or "No description provided."

        links = [
            f'<a href="{escape(repo_url)}">Repository</a>',
            f'<a href="{escape(repo_url)}/stargazers">Stars</a>',
            f'<a href="{escape(repo_url)}/issues">Issues</a>',
        ]
        if metadata.homepage:
            links.append(f'<a href="{escape(metadata.homepage)}">Live</a>')

        info_bits = [f"★ {metadata.stars:,}"]
        updated = self._format_timestamp(metadata.updated_at)
        if updated:
            info_bits.append(f"Updated {updated}")

        topics_html = " ".join(
            f"<code>{escape(topic)}</code>" for topic in metadata.topics[:4]
        )

        return (
            f"<h3><a href=\"{escape(repo_url)}\">{escape(repo_name)}</a></h3>"
            f"<p>{escape(description)}</p>"
            f"<p><sub>{' · '.join(info_bits)}</sub></p>"
            f"<p>{' · '.join(links)}</p>"
            f"<p>{topics_html}</p>"
        )

    def _render_blog_posts(self) -> str:
        posts = self.blog_client.fetch_latest_posts(
            self.settings.blog_feed_url,
            self.settings.blog_post_limit,
        )
        feed_url = escape(self.settings.blog_feed_url)
        if not posts:
            lines = [
                "<p><em>No recent posts available.</em></p>",
                f"<p><sub>📡 Source: <a href=\"{feed_url}\">RSS feed</a></sub></p>",
            ]
            return self._wrap_blog_post_list_markers(lines)

        lines = ["<table role=\"presentation\">"]
        for post in posts:
            host = urlparse(post.url).netloc.replace("www.", "").strip() or "article"
            lines.append(
                "<tr><td>📝</td><td>"
                f"<a href=\"{escape(post.url)}\"><strong>{escape(post.title)}</strong></a>"
                f"<br/><sub>{escape(host)}</sub>"
                "</td></tr>"
            )
        lines.extend(
            [
                "</table>",
                (
                    f"<p><sub>📡 Auto-updated from "
                    f"<a href=\"{feed_url}\">RSS feed</a></sub></p>"
                ),
            ]
        )
        return self._wrap_blog_post_list_markers(lines)

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

        request = Request(
            url=logo,
            headers={"User-Agent": "readme-section-generator"},
            method="GET",
        )
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

    def _wrap_blog_post_list_markers(self, lines: Sequence[str]) -> str:
        return (
            "<!-- BLOG-POST-LIST:START -->\n"
            + "\n".join(lines)
            + "\n<!-- BLOG-POST-LIST:END -->"
        )
