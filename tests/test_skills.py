"""Tests for skills badge generation."""

import base64
import os
import re
import xml.etree.ElementTree as ET
from collections.abc import Iterable
from concurrent.futures import ThreadPoolExecutor, as_completed
from html import escape, unescape
from html.parser import HTMLParser
from http.client import HTTPMessage
from pathlib import Path
from typing import TypeGuard, override
from urllib.error import HTTPError
from urllib.parse import parse_qsl, quote, unquote_to_bytes, urlparse
from urllib.request import Request, urlopen

import pytest
import typer
from pydantic import ValidationError

from scripts.config import (
    SkillCategory,
    SkillEntry,
    SkillsSettings,
    SkillSubcategory,
    load_skills,
)
from scripts.skills import MAX_SHIELDS_BADGE_URL_LENGTH, SkillsBadgeGenerator

REPO_ROOT = Path(__file__).resolve().parent.parent
SIMPLE_ICON_SLUGS_USED = (
    REPO_ROOT / "tests" / "fixtures" / "simple_icons_slugs_used.txt"
)
EXPECTED_LOCAL_LOGO_SLUG_FALLBACKS = {
    "D3.js": "d3",
    "Jest": "jest",
    "Obsidian": "obsidian",
    "Prettier": "prettier",
    "Sass": "sass",
}
EXPECTED_COMPACT_LOCAL_LOGO_EMBEDS = {
    "Amazon AWS": (
        "iconify:tabler",
        "https://icon-sets.iconify.design/tabler/brand-aws/",
        "MIT",
    ),
    "Canva": (
        "iconify:bxl",
        "https://icon-sets.iconify.design/bxl/canva/",
        "MIT",
    ),
    "Playwright": (
        "iconify:devicon-plain",
        "https://icon-sets.iconify.design/devicon-plain/playwright/",
        "MIT",
    ),
    "Tableau": (
        "iconify:logos",
        "https://icon-sets.iconify.design/logos/tableau-icon/",
        "CC0-1.0",
    ),
    "Visual Studio Code": (
        "iconify:devicon-plain",
        "https://icon-sets.iconify.design/devicon-plain/vscode/",
        "MIT",
    ),
}
EXPECTED_MONOCHROME_LOCAL_LOGO_PAINT = {
    "Amazon AWS": 'stroke="white"',
    "Canva": 'fill="white"',
    "Playwright": 'fill="white"',
    "Visual Studio Code": 'fill="white"',
}
RENDER_QA_TIMEOUT_SECONDS = 8.0
live_badge_qa = pytest.mark.skipif(
    os.environ.get("PROFILE_LIVE_BADGE_QA") != "1",
    reason="live readback requires PROFILE_LIVE_BADGE_QA=1",
)
GITHUB_DEV_README_HTML_URL = (
    "https://api.github.com/repos/wyattowalsh/wyattowalsh/readme?ref=dev"
)
_SKILLS_MARKER_START = "<!-- SKILLS:START -->"
_SKILLS_MARKER_END = "<!-- SKILLS:END -->"


def iter_skills(settings: SkillsSettings) -> Iterable[SkillEntry]:
    """Yield every configured skill, including subcategory entries."""
    for cat in settings.categories:
        yield from cat.skills
        for sub in cat.subcategories:
            yield from sub.skills


def load_known_simple_icon_slugs() -> set[str]:
    return {
        line.strip()
        for line in SIMPLE_ICON_SLUGS_USED.read_text(encoding="utf-8").splitlines()
        if line.strip()
    }


def load_known_simple_icon_slug_lines() -> list[str]:
    """Load non-empty fixture lines without discarding order or duplicates."""
    return [
        line.strip()
        for line in SIMPLE_ICON_SLUGS_USED.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _badge_logo_value(src: str) -> str | None:
    """Return the decoded shields ``logo`` query value, if present."""
    for key, value in parse_qsl(urlparse(unescape(src)).query, keep_blank_values=True):
        if key == "logo":
            return value
    return None


def _data_uri_svg_is_well_formed(logo: str) -> bool:
    """Check the embedded image is a parseable SVG document."""
    metadata, separator, payload = logo.partition(",")
    if not metadata.startswith("data:image/svg+xml") or not separator:
        return False
    try:
        data = (
            base64.b64decode(payload, validate=True)
            if ";base64" in metadata
            else unquote_to_bytes(payload)
        )
        return ET.fromstring(data).tag == "{http://www.w3.org/2000/svg}svg"
    except (ValueError, ET.ParseError):
        return False


def _check_rendered_badge(name: str, url: str) -> None:
    """Require a successfully rendered SVG containing its label and embedded logo."""
    request = Request(url, headers={"User-Agent": "wyattowalsh-skills-badge-qa"})
    with urlopen(request, timeout=RENDER_QA_TIMEOUT_SECONDS) as response:
        root = ET.fromstring(response.read())
    svg = "{http://www.w3.org/2000/svg}"
    assert root.tag == f"{svg}svg", name
    assert root.findtext(f"{svg}title") in {name, name.upper()}, (
        f"Unexpected badge title: {name}"
    )
    for icon in root.iter(f"{svg}image"):
        href = icon.get("{http://www.w3.org/1999/xlink}href") or icon.get("href", "")
        if href.startswith("data:image/svg+xml") and _data_uri_svg_is_well_formed(href):
            return
    pytest.fail(f"Rendered badge has no embedded SVG logo: {name}")


def _check_rendered_badges(sources: dict[str, str]) -> None:
    assert sources, "Expected badge sources"
    failures: list[str] = []
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {
            pool.submit(_check_rendered_badge, name, url): name
            for name, url in sources.items()
        }
        for future in as_completed(futures):
            name = futures[future]
            try:
                future.result()
            except HTTPError as exc:
                failures.append(f"{name}: HTTP {exc.code}")
            except OSError as exc:
                failures.append(f"{name}: unreachable ({exc})")
            except (ET.ParseError, AssertionError, pytest.fail.Exception) as exc:
                failures.append(f"{name}: invalid SVG ({exc})")
    assert not failures, (
        f"{len(failures)} of {len(sources)} badges failed:\n"
        + "\n".join(sorted(failures))
    )


def _filled(value: str | None) -> TypeGuard[str]:
    """True when an optional string is present and not empty."""
    return value is not None and value != ""


def _fetch_github_dev_readme_html() -> str:
    """Load the rendered dev README. Errors in an opted-in run must be visible."""
    request = Request(
        GITHUB_DEV_README_HTML_URL,
        headers={
            "Accept": "application/vnd.github.html+json",
            "User-Agent": "wyattowalsh-skills-badge-qa",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    with urlopen(request, timeout=RENDER_QA_TIMEOUT_SECONDS) as response:
        payload = response.read()
        if not isinstance(payload, bytes):
            raise TypeError("GitHub README response must be bytes")
        return payload.decode("utf-8")


class _BadgeImages(HTMLParser):
    """Collect image attributes together with their enclosing link destination."""

    def __init__(self, section_title: str | None = None) -> None:
        super().__init__()
        self.destination = ""
        self.images: list[tuple[str, str, str, str]] = []
        self.section_title = section_title
        self.in_section = section_title is None
        self.heading_parts: list[str] | None = None

    @override
    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key: value or "" for key, value in attrs}
        if tag == "h2" and self.section_title is not None:
            self.in_section = False
            self.heading_parts = []
        elif tag == "a":
            self.destination = values.get("href", "")
        elif tag == "img" and self.in_section:
            self.images.append(
                (
                    values.get("alt", ""),
                    self.destination,
                    values.get("src", ""),
                    values.get("data-canonical-src", ""),
                )
            )

    @override
    def handle_data(self, data: str) -> None:
        if self.heading_parts is not None:
            self.heading_parts.append(data)

    @override
    def handle_endtag(self, tag: str) -> None:
        if tag == "h2" and self.heading_parts is not None:
            self.in_section = "".join(self.heading_parts).strip() == self.section_title
            self.heading_parts = None
        elif tag == "details" and self.section_title is not None:
            self.in_section = False
        elif tag == "a":
            self.destination = ""


def _camo_sources(
    html: str,
    expected: dict[str, tuple[str, str]],
    section_title: str,
) -> dict[str, str]:
    parser = _BadgeImages(section_title)
    parser.feed(html)
    parser.close()
    camo: dict[str, str] = {}
    for name, href, src, canonical in parser.images:
        assert name in expected, f"Unexpected badge in {section_title}: {name}"
        assert name not in camo, f"Duplicate rendered badge: {name}"
        assert (href, canonical) == expected[name], (
            f"Wrong badge link or source: {name}"
        )
        parsed = urlparse(src)
        assert (parsed.scheme, parsed.netloc) == (
            "https",
            "camo.githubusercontent.com",
        ), f"Expected GitHub Camo for {name}"
        camo[name] = src
    assert camo.keys() == expected.keys(), (
        f"Missing badges: {sorted(expected.keys() - camo.keys())}"
    )
    assert len(set(camo.values())) == len(camo), "Duplicate Camo image"
    return camo


# ---------------------------------------------------------------------------
# Model tests
# ---------------------------------------------------------------------------


class TestSkillEntry:
    def test_minimal(self):
        e = SkillEntry(name="Python", slug="python", color="3776AB")
        assert e.name == "Python"
        assert e.color == "3776AB"

    def test_defaults(self):
        e = SkillEntry(name="Test")
        assert e.color == "555555"
        assert e.slug is None
        assert e.logo_path is None
        assert e.url is None

    def test_logo_path_field(self):
        e = SkillEntry(
            name="SQL", logo_path=".github/assets/skill-icons/sql.svg", color="4479A1"
        )
        assert e.logo_path == ".github/assets/skill-icons/sql.svg"

    def test_logo_source_metadata_fields(self):
        e = SkillEntry(
            name="SQL",
            logo_path=".github/assets/skill-icons/sql.svg",
            logo_source="local-original",
            logo_source_url="https://example.com/icons/sql.svg",
            logo_license="MIT",
            logo_style="custom-generic",
            color="4479A1",
        )
        assert e.logo_source == "local-original"
        assert e.logo_source_url == "https://example.com/icons/sql.svg"
        assert e.logo_license == "MIT"
        assert e.logo_style == "custom-generic"


class TestSkillsSettings:
    def test_defaults(self):
        s = SkillsSettings()
        assert s.style == "for-the-badge"
        assert s.logo_color == "white"
        assert s.categories == []


# ---------------------------------------------------------------------------
# Validator tests
# ---------------------------------------------------------------------------


class TestSkillEntryValidators:
    def test_logo_path_rejects_traversal(self):
        with pytest.raises(ValidationError, match="must not contain"):
            SkillEntry(name="X", logo_path="../secret", color="000")

    def test_logo_path_rejects_nested_traversal(self):
        with pytest.raises(ValidationError, match="must not contain"):
            SkillEntry(name="X", logo_path="foo/../../etc/passwd", color="000")

    def test_logo_path_rejects_absolute(self):
        with pytest.raises(ValidationError, match="repo-relative"):
            SkillEntry(name="X", logo_path="/etc/passwd", color="000")

    def test_logo_path_rejects_home_prefix(self):
        with pytest.raises(ValidationError, match="repo-relative"):
            SkillEntry(name="X", logo_path="~/.ssh/id_rsa", color="000")

    def test_logo_path_rejects_url(self):
        with pytest.raises(ValidationError, match="not a URL"):
            SkillEntry(
                name="X",
                logo_path="https://example.com/icon.svg",
                color="000",
            )

    def test_logo_path_rejects_file_url(self):
        with pytest.raises(ValidationError, match="not a URL"):
            SkillEntry(name="X", logo_path="file:///tmp/x.svg", color="000")

    def test_logo_path_accepts_normal(self):
        e = SkillEntry(name="X", logo_path=".github/assets/test.svg", color="000")
        assert e.logo_path == ".github/assets/test.svg"

    def test_logo_path_rejects_empty(self):
        with pytest.raises(ValidationError, match="must not be empty"):
            SkillEntry(name="X", logo_path="", color="000")

    def test_url_rejects_javascript(self):
        with pytest.raises(ValidationError, match="http"):
            SkillEntry(name="X", color="000", url="javascript:alert(1)")

    def test_url_accepts_https(self):
        e = SkillEntry(name="X", color="000", url="https://example.com")
        assert e.url == "https://example.com"

    def test_url_accepts_uppercase_scheme(self):
        e = SkillEntry(name="X", color="000", url="HTTP://example.com")
        assert e.url == "HTTP://example.com"

    def test_url_rejects_no_scheme(self):
        with pytest.raises(ValidationError):
            SkillEntry(name="X", color="000", url="//example.com")

    def test_logo_source_url_rejects_no_scheme(self):
        with pytest.raises(ValidationError, match="logo_source_url"):
            SkillEntry(
                name="X",
                logo_path=".github/assets/test.svg",
                logo_source_url="//example.com/icon.svg",
                color="000",
            )


# ---------------------------------------------------------------------------
# Badge URL construction
# ---------------------------------------------------------------------------


class TestBadgeUrl:
    def setup_method(self):
        self.gen = SkillsBadgeGenerator(settings=SkillsSettings())

    def test_basic_url(self):
        skill = SkillEntry(name="Python", slug="python", color="3776AB")
        url = self.gen._build_badge_url(skill)
        assert "Python" in url
        assert "3776AB" in url
        assert "style=for-the-badge" in url
        assert "logo=python" in url
        assert "logoColor=white" in url

    def test_no_slug(self):
        skill = SkillEntry(name="SQL", color="4479A1")
        url = self.gen._build_badge_url(skill)
        assert "SQL" in url
        assert "logo=" not in url
        assert "4479A1" in url

    def test_spaces_encoded(self):
        skill = SkillEntry(
            name="Visual Studio Code", slug="visualstudiocode", color="007ACC"
        )
        url = self.gen._build_badge_url(skill)
        assert "Visual%20Studio%20Code" in url

    def test_dashes_escaped(self):
        skill = SkillEntry(name="Next.js", slug="nextdotjs", color="000000")
        url = self.gen._build_badge_url(skill)
        assert "Next.js" in url

    def test_custom_logo_color(self):
        skill = SkillEntry(
            name="JS", slug="javascript", color="F7DF1E", logo_color="black"
        )
        url = self.gen._build_badge_url(skill)
        assert "logoColor=black" in url

    def test_style_override(self):
        gen = SkillsBadgeGenerator(settings=SkillsSettings(style="flat-square"))
        skill = SkillEntry(name="Test", color="000000")
        url = gen._build_badge_url(skill)
        assert "style=flat-square" in url

    def test_logo_path_base64(self, tmp_path, monkeypatch):
        monkeypatch.setattr("scripts.skills._REPO_ROOT", tmp_path)
        rel = Path("assets/logo.svg")
        svg_path = tmp_path / rel
        svg_path.parent.mkdir()
        svg_content = (
            b'<svg xmlns="http://www.w3.org/2000/svg">'
            b'<circle r="5" fill="white"/>'
            b"</svg>"
        )
        svg_path.write_bytes(svg_content)

        skill = SkillEntry(
            name="TestSkill",
            logo_path=rel.as_posix(),
            color="FF0000",
        )
        url = self.gen._build_badge_url(skill)
        expected_b64 = quote(base64.b64encode(svg_content).decode(), safe="")
        assert f"logo=data:image/svg%2Bxml;base64,{expected_b64}" in url
        assert "logo=TestSkill" not in url

    def test_logo_path_base64_urlencodes_plus(self, tmp_path, monkeypatch):
        """Base64 +/= chars must be percent-encoded for URL safety."""
        monkeypatch.setattr("scripts.skills._REPO_ROOT", tmp_path)
        rel = Path("assets/plus.svg")
        svg_path = tmp_path / rel
        svg_path.parent.mkdir()
        # Content that produces + in base64 (0xfb byte → +)
        svg_content = b"\xfb\xef\xbe"
        svg_path.write_bytes(svg_content)

        skill = SkillEntry(name="Test", logo_path=rel.as_posix(), color="000000")
        url = self.gen._build_badge_url(skill)
        b64_section = url.split("base64,")[1].split("&")[0]
        assert "+" not in b64_section, "raw + in URL would be decoded as space"
        assert "%2B" in b64_section or "%2b" in b64_section

    def test_logo_path_base64_urlencodes_slash_and_equals(self, tmp_path, monkeypatch):
        """Base64 / and = chars must be percent-encoded for URL safety."""
        monkeypatch.setattr("scripts.skills._REPO_ROOT", tmp_path)
        rel = Path("assets/slash.svg")
        svg_path = tmp_path / rel
        svg_path.parent.mkdir()
        # b'\xff' produces /w== in base64 (contains both / and =)
        svg_path.write_bytes(b"\xff")

        skill = SkillEntry(name="Test", logo_path=rel.as_posix(), color="000000")
        url = self.gen._build_badge_url(skill)
        b64_section = url.split("base64,")[1].split("&")[0]
        assert "/" not in b64_section, "raw / would break URL path"
        assert "=" not in b64_section, "raw = would break query parsing"
        assert "%2F" in b64_section
        assert "%3D" in b64_section

    def test_supported_slug_priority_over_local_logo(self, tmp_path, monkeypatch):
        monkeypatch.setattr("scripts.skills._REPO_ROOT", tmp_path)
        rel = Path("assets/priority.svg")
        svg_path = tmp_path / rel
        svg_path.parent.mkdir()
        svg_path.write_bytes(b'<svg xmlns="http://www.w3.org/2000/svg"/>')

        skill = SkillEntry(
            name="Python",
            slug="python",
            logo_path=rel.as_posix(),
            color="5391FE",
        )
        url = self.gen._build_badge_url(skill)
        assert "logo=python" in url
        assert "logo=data:image" not in url

    def test_oversized_logo_path_falls_back_to_slug(
        self, tmp_path, monkeypatch, mocker
    ):
        monkeypatch.setattr("scripts.skills._REPO_ROOT", tmp_path)
        warning = mocker.patch("scripts.skills.logger.warning")
        rel = Path("assets/oversized.svg")
        svg_path = tmp_path / rel
        svg_path.parent.mkdir()
        svg_path.write_bytes(b"x" * MAX_SHIELDS_BADGE_URL_LENGTH)

        skill = SkillEntry(
            name="Oversized",
            slug="python",
            logo_path=rel.as_posix(),
            color="3776AB",
        )
        url = self.gen._build_badge_url(skill)

        assert "logo=python" in url
        assert "logo=data:image" not in url
        assert len(url) <= MAX_SHIELDS_BADGE_URL_LENGTH
        warning.assert_not_called()

    def test_oversized_logo_path_without_slug_uses_no_logo(self, tmp_path, monkeypatch):
        monkeypatch.setattr("scripts.skills._REPO_ROOT", tmp_path)
        rel = Path("assets/oversized.svg")
        svg_path = tmp_path / rel
        svg_path.parent.mkdir()
        svg_path.write_bytes(b"x" * MAX_SHIELDS_BADGE_URL_LENGTH)

        skill = SkillEntry(
            name="Oversized",
            logo_path=rel.as_posix(),
            color="3776AB",
        )
        url = self.gen._build_badge_url(skill)

        assert url == (
            "https://img.shields.io/badge/Oversized-3776AB?style=for-the-badge"
        )
        assert len(url) <= MAX_SHIELDS_BADGE_URL_LENGTH

    def test_encoded_url_length_controls_custom_logo_fallback(
        self, tmp_path, monkeypatch
    ):
        monkeypatch.setattr("scripts.skills._REPO_ROOT", tmp_path)
        rel = Path("assets/encoded.svg")
        svg_path = tmp_path / rel
        svg_path.parent.mkdir()
        # 0xff encodes as /w==, so URL quoting expands every base64 character.
        svg_path.write_bytes(b"\xff" * 1_000)

        skill = SkillEntry(
            name="Encoded",
            slug="python",
            logo_path=rel.as_posix(),
            color="3776AB",
        )
        encoded = quote(base64.b64encode(svg_path.read_bytes()).decode(), safe="")
        assert len(encoded) > len(svg_path.read_bytes())

        url = self.gen._build_badge_url(skill)
        assert "logo=python" in url
        assert len(url) <= MAX_SHIELDS_BADGE_URL_LENGTH

    def test_logo_path_fallback_to_slug_when_missing(self, mocker):
        warning = mocker.patch("scripts.skills.logger.warning")
        skill = SkillEntry(
            name="Missing",
            slug="fallback",
            logo_path="nonexistent/path.svg",
            color="000000",
        )
        url = self.gen._build_badge_url(skill)
        assert "logo=fallback" in url
        assert "base64" not in url
        warning.assert_not_called()

    def test_logo_path_missing_no_slug(self):
        skill = SkillEntry(
            name="NoLogo",
            logo_path="nonexistent/path.svg",
            color="000000",
        )
        url = self.gen._build_badge_url(skill)
        assert url == "https://img.shields.io/badge/NoLogo-000000?style=for-the-badge"

    def test_whitespace_slug_uses_complete_no_logo_badge(self):
        skill = SkillEntry(name="NoLogo", slug="   ", color="000000")

        url = self.gen._build_badge_url(skill)

        assert url == "https://img.shields.io/badge/NoLogo-000000?style=for-the-badge"

    def test_oversized_slug_uses_complete_no_logo_badge(self, mocker):
        info = mocker.patch("scripts.skills.logger.info")
        prefix = "https://img.shields.io/badge/"
        suffix = "-000000?style=for-the-badge"
        name = "x" * (MAX_SHIELDS_BADGE_URL_LENGTH - len(prefix) - len(suffix))
        skill = SkillEntry(name=name, slug="python", color="000000")

        url = self.gen._build_badge_url(skill)

        assert url == f"{prefix}{name}{suffix}"
        assert len(url) == MAX_SHIELDS_BADGE_URL_LENGTH
        assert "logo=" not in url
        info.assert_called_once()

    def test_base_badge_over_limit_fails_instead_of_truncating(self):
        skill = SkillEntry(
            name="x" * MAX_SHIELDS_BADGE_URL_LENGTH,
            color="000000",
        )

        with pytest.raises(ValueError, match="exceeds 4000 characters"):
            self.gen._build_badge_url(skill)


# ---------------------------------------------------------------------------
# HTML rendering
# ---------------------------------------------------------------------------


class TestRendering:
    def test_render_badge_with_url(self):
        gen = SkillsBadgeGenerator(settings=SkillsSettings())
        skill = SkillEntry(
            name="Python", slug="python", color="3776AB", url="https://python.org"
        )
        html = gen._render_badge(skill)
        assert '<a href="https://python.org">' in html
        assert 'alt="Python"' in html

    def test_render_badge_strips_homepage_whitespace(self):
        gen = SkillsBadgeGenerator(settings=SkillsSettings())
        skill = SkillEntry(
            name="Python",
            slug="python",
            color="3776AB",
            url="https://www.python.org  ",
        )
        html = gen._render_badge(skill)
        assert '<a href="https://www.python.org">' in html
        assert 'href="https://www.python.org  "' not in html

    def test_render_badge_without_url(self):
        gen = SkillsBadgeGenerator(settings=SkillsSettings())
        skill = SkillEntry(name="SQL", color="4479A1")
        with pytest.raises(ValueError, match="required"):
            gen._render_badge(skill)

    def test_render_badge_rejects_wikipedia_homepage(self):
        gen = SkillsBadgeGenerator(settings=SkillsSettings())
        skill = SkillEntry(
            name="SQL",
            color="4479A1",
            url="https://en.wikipedia.org/wiki/SQL",
        )
        with pytest.raises(ValueError, match="not Wikipedia"):
            gen._render_badge(skill)

    def test_render_badge_rejects_http_homepage(self):
        gen = SkillsBadgeGenerator(settings=SkillsSettings())
        skill = SkillEntry(name="X", color="000000", url="http://example.com")
        with pytest.raises(ValueError, match="must be https"):
            gen._render_badge(skill)

    def test_render_category(self):
        gen = SkillsBadgeGenerator(settings=SkillsSettings())
        cat = SkillCategory(
            name="Languages",
            skills=[
                SkillEntry(
                    name="Python",
                    color="3776AB",
                    url="https://www.python.org",
                )
            ],
        )
        html = gen._render_category(cat)
        assert "<summary>Languages</summary>" in html
        assert "Python" in html
        assert '<a href="https://www.python.org">' in html
        assert "https://img.shields.io/badge/" in html

    def test_render_subcategory(self):
        gen = SkillsBadgeGenerator(settings=SkillsSettings())
        cat = SkillCategory(
            name="Data",
            subcategories=[
                SkillSubcategory(
                    name="Storage",
                    skills=[
                        SkillEntry(
                            name="PostgreSQL",
                            color="4169E1",
                            url="https://www.postgresql.org",
                        )
                    ],
                )
            ],
        )
        html = gen._render_category(cat)
        assert "<summary>Data</summary>" in html
        assert "#### Storage" in html
        assert "PostgreSQL" in html
        assert '<a href="https://www.postgresql.org">' in html

    def test_collapsible(self):
        settings = SkillsSettings(
            collapsible=True,
            categories=[
                SkillCategory(
                    name="Test",
                    skills=[
                        SkillEntry(
                            name="X",
                            color="000000",
                            url="https://example.com",
                        )
                    ],
                )
            ],
        )
        gen = SkillsBadgeGenerator(settings=settings)
        html = gen._render_all()
        assert "<details>" in html
        assert "</details>" in html
        assert '<a href="https://example.com">' in html


# ---------------------------------------------------------------------------
# README injection
# ---------------------------------------------------------------------------


class TestReadmeInjection:
    def test_replaces_between_markers(self, tmp_path):
        readme = tmp_path / "README.md"
        readme.write_text(
            "before\n<!-- SKILLS:START -->\nold content\n<!-- SKILLS:END -->\nafter\n"
        )
        settings = SkillsSettings(
            readme_path=str(readme),
            categories=[
                SkillCategory(
                    name="Test",
                    skills=[
                        SkillEntry(
                            name="Python",
                            color="3776AB",
                            url="https://www.python.org",
                        )
                    ],
                )
            ],
        )
        gen = SkillsBadgeGenerator(settings=settings)
        gen.generate()
        content = readme.read_text()
        assert "Python" in content
        assert "old content" not in content
        assert "before" in content
        assert "after" in content

    def test_missing_markers_warns(self, tmp_path, mocker):
        error = mocker.patch("scripts.skills.logger.error")
        warning = mocker.patch("scripts.skills.logger.warning")
        readme = tmp_path / "README.md"
        readme.write_text("# Hello\nNo markers here\n")
        settings = SkillsSettings(
            readme_path=str(readme),
            categories=[
                SkillCategory(
                    name="Test",
                    skills=[
                        SkillEntry(
                            name="X",
                            color="000",
                            url="https://example.com",
                        )
                    ],
                )
            ],
        )
        gen = SkillsBadgeGenerator(settings=settings)
        result = gen.generate()
        assert result == readme
        assert readme.read_text() == "# Hello\nNo markers here\n"
        error.assert_called_once()
        assert "Skills markers not found" in error.call_args.args[0]
        warning.assert_not_called()

    def test_missing_readme_warns(self, tmp_path, mocker):
        error = mocker.patch("scripts.skills.logger.error")
        warning = mocker.patch("scripts.skills.logger.warning")
        settings = SkillsSettings(
            readme_path=str(tmp_path / "nonexistent.md"),
            categories=[],
        )
        gen = SkillsBadgeGenerator(settings=settings)
        result = gen.generate()
        assert result == Path(settings.readme_path)
        assert not Path(settings.readme_path).exists()
        error.assert_called_once()
        assert "README not found" in error.call_args.args[0]
        warning.assert_not_called()

    def test_strict_generate_raises_when_markers_are_not_replaced(self, tmp_path):
        missing = tmp_path / "nonexistent.md"
        missing_gen = SkillsBadgeGenerator(
            settings=SkillsSettings(readme_path=str(missing), categories=[])
        )
        with pytest.raises(
            FileNotFoundError,
            match="Skills markers were not replaced",
        ):
            missing_gen.generate(strict=True)
        assert not missing.exists()

        readme = tmp_path / "README.md"
        original = "# Hello\nNo markers here\n"
        readme.write_text(original)
        unmarked = SkillsBadgeGenerator(
            settings=SkillsSettings(readme_path=str(readme), categories=[])
        )
        with pytest.raises(
            FileNotFoundError,
            match="Skills markers were not replaced",
        ):
            unmarked.generate(strict=True)
        assert readme.read_text() == original


# ---------------------------------------------------------------------------
# Integration tests
# ---------------------------------------------------------------------------


class TestIntegration:
    def test_skills_yaml_logo_paths_all_exist(self, monkeypatch):
        """All logo_path entries in skills.yaml must point to real files."""
        monkeypatch.chdir(REPO_ROOT)
        settings = load_skills()
        for skill in iter_skills(settings):
            logo_path = skill.logo_path
            if _filled(logo_path):
                assert Path(logo_path).exists(), (
                    f"Missing icon for '{skill.name}': {logo_path}"
                )

    def test_skills_yaml_badge_logo_outcomes_are_supported(self, monkeypatch):
        """Slug-backed logos must be known; intentional no-logo badges are exact."""
        monkeypatch.chdir(REPO_ROOT)
        settings = load_skills()
        gen = SkillsBadgeGenerator(settings=settings)
        known_slugs = load_known_simple_icon_slugs()
        no_logo_badges: set[str] = set()

        for skill in iter_skills(settings):
            url = gen._build_badge_url(skill)
            if "logo=data:image/svg%2Bxml;base64," in url:
                continue
            if "&logo=" in url:
                assert skill.slug in known_slugs, (
                    f"Unsupported rendered Simple Icons slug for '{skill.name}': "
                    f"{skill.slug}"
                )
                continue
            no_logo_badges.add(skill.name)

        assert no_logo_badges == set()

    def test_skills_yaml_logo_paths_are_svg_with_provenance(self, monkeypatch):
        """Local SVGs need source metadata so bespoke icons stay auditable."""
        monkeypatch.chdir(REPO_ROOT)
        settings = load_skills()
        gen = SkillsBadgeGenerator(settings=settings)
        for skill in iter_skills(settings):
            logo_path = skill.logo_path
            if not _filled(logo_path):
                continue

            path = Path(logo_path)
            assert path.suffix == ".svg", (
                f"Local logo must be SVG for '{skill.name}': {logo_path}"
            )
            content = path.read_text(encoding="utf-8")
            assert "<svg" in content, f"Local logo is not SVG: {logo_path}"
            logo_source = skill.logo_source
            logo_source_url = skill.logo_source_url
            logo_license = skill.logo_license
            logo_style = skill.logo_style
            assert _filled(logo_source), f"Missing logo_source for '{skill.name}'"
            assert _filled(logo_source_url), (
                f"Missing logo_source_url for '{skill.name}'"
            )
            assert _filled(logo_license), f"Missing logo_license for '{skill.name}'"
            assert _filled(logo_style), f"Missing logo_style for '{skill.name}'"

            url = gen._build_badge_url(skill)
            assert len(url) <= MAX_SHIELDS_BADGE_URL_LENGTH
            if "logo=data:image/svg%2Bxml;base64," not in url:
                slug = skill.slug
                if _filled(slug):
                    assert f"logo={quote(slug, safe='')}" in url
                else:
                    assert "&logo=" not in url

    def test_skills_yaml_local_logo_fallbacks_are_expected(self, monkeypatch):
        """Only the audited overlong local logos may use slug fallbacks."""
        monkeypatch.chdir(REPO_ROOT)
        settings = load_skills()
        gen = SkillsBadgeGenerator(settings=settings)
        known_slugs = load_known_simple_icon_slugs()
        fallbacks: dict[str, str] = {}
        no_logo_fallbacks: set[str] = set()
        compact_embeds: set[str] = set()

        for skill in iter_skills(settings):
            if not _filled(skill.logo_path):
                continue

            url = gen._build_badge_url(skill)
            if "logo=data:image/svg%2Bxml;base64," in url:
                if skill.name in EXPECTED_COMPACT_LOCAL_LOGO_EMBEDS:
                    expected_provenance = EXPECTED_COMPACT_LOCAL_LOGO_EMBEDS[skill.name]
                    assert (
                        skill.logo_source,
                        skill.logo_source_url,
                        skill.logo_license,
                    ) == expected_provenance
                    compact_embeds.add(skill.name)
                continue

            slug = skill.slug
            if _filled(slug):
                assert slug in known_slugs, (
                    f"Unsupported local-logo fallback slug for '{skill.name}': {slug}"
                )
                assert f"logo={quote(slug, safe='')}" in url
                fallbacks[skill.name] = slug
            else:
                assert "&logo=" not in url
                no_logo_fallbacks.add(skill.name)

        expected_slug_first = {
            skill.name: skill.slug
            for skill in iter_skills(settings)
            if _filled(skill.logo_path) and _filled(skill.slug) and skill.slug.strip()
        }
        assert fallbacks == expected_slug_first
        assert no_logo_fallbacks == set()
        assert compact_embeds == set(EXPECTED_COMPACT_LOCAL_LOGO_EMBEDS)
        assert set(EXPECTED_LOCAL_LOGO_SLUG_FALLBACKS).issubset(fallbacks)

    def test_skills_yaml_local_svgs_are_safe_for_badges(self, monkeypatch):
        """Vendored badge SVGs must stay self-contained and inert."""
        monkeypatch.chdir(REPO_ROOT)
        settings = load_skills()
        for skill in iter_skills(settings):
            logo_path = skill.logo_path
            if not _filled(logo_path):
                continue

            path = Path(logo_path)
            content = path.read_text(encoding="utf-8")
            lowered = content.lower()
            assert "<script" not in lowered, (
                f"Local logo must not include scripts: {skill.logo_path}"
            )
            assert "currentcolor" not in lowered, (
                f"Local logo paint must not depend on inherited currentColor: "
                f"{skill.logo_path}"
            )
            assert "javascript:" not in lowered, (
                f"Local logo must not include javascript URLs: {skill.logo_path}"
            )
            assert 'href="http' not in lowered, (
                f"Local logo must be self-contained: {skill.logo_path}"
            )
            assert "href='http" not in lowered, (
                f"Local logo must be self-contained: {skill.logo_path}"
            )
            assert "data:image/png" not in lowered, (
                f"Local logo must not embed raster PNGs: {skill.logo_path}"
            )
            assert "data:image/jpeg" not in lowered, (
                f"Local logo must not embed raster JPEGs: {skill.logo_path}"
            )
            expected_paint = EXPECTED_MONOCHROME_LOCAL_LOGO_PAINT.get(skill.name)
            if _filled(expected_paint):
                assert expected_paint in lowered, (
                    f"Compact monochrome logo needs explicit high-contrast paint: "
                    f"{skill.logo_path}"
                )
            if skill.name == "Tableau":
                assert 'fill="#' in lowered, (
                    "Compact Tableau logo must preserve explicit brand-color fills"
                )

    def test_skills_yaml_simple_icon_slugs_are_known_good(self, monkeypatch):
        """Simple Icons slugs used directly must be audited, current slugs."""
        monkeypatch.chdir(REPO_ROOT)
        settings = load_skills()
        known_slugs = load_known_simple_icon_slugs()
        gen = SkillsBadgeGenerator(settings=settings)
        for skill in iter_skills(settings):
            url = gen._build_badge_url(skill)
            if "&logo=" in url and "logo=data:image/svg%2Bxml;base64," not in url:
                slug = skill.slug
                assert _filled(slug)
                assert slug in known_slugs, (
                    f"Unknown Simple Icons slug for '{skill.name}': {slug}"
                )

    def test_simple_icon_slug_fixture_is_sorted_and_unique(self):
        """Keep the audited slug fixture deterministic and duplicate-free."""
        slug_lines = load_known_simple_icon_slug_lines()

        assert slug_lines == sorted(set(slug_lines))

    def test_skills_yaml_badge_urls_fit_github_image_proxy(self, monkeypatch):
        """Every published source URL must fit the GitHub/Camo-safe budget."""
        monkeypatch.chdir(REPO_ROOT)
        settings = load_skills()
        gen = SkillsBadgeGenerator(settings=settings)

        for skill in iter_skills(settings):
            url = gen._build_badge_url(skill)
            assert len(url) <= MAX_SHIELDS_BADGE_URL_LENGTH, (
                f"Badge URL exceeds {MAX_SHIELDS_BADGE_URL_LENGTH} characters: "
                f"{skill.name} ({len(url)})"
            )

    def test_skills_yaml_badges_have_https_hrefs_and_camo_safe_urls(self, monkeypatch):
        """Every catalog badge must have an https homepage and a Camo-safe src."""
        monkeypatch.chdir(REPO_ROOT)
        settings = load_skills()
        gen = SkillsBadgeGenerator(settings=settings)
        html = gen._render_all()
        catalog = list(iter_skills(settings))
        badges = re.findall(
            r'<a href="([^"]+)"><img alt="([^"]+)" src="([^"]+)"/></a>',
            html,
        )

        assert catalog
        assert len(badges) == len(catalog)
        css3 = next(skill for skill in catalog if skill.name == "CSS3")
        assert css3.logo_style == "custom-retro"
        by_name = {skill.name: skill.url for skill in catalog}
        assert by_name["Shell Script"] != by_name["Bash"]
        assert "gnu.org/software/bash" not in (by_name["Shell Script"] or "")
        assert "gnu.org/software/bash" in (by_name["Bash"] or "")
        for skill, (href, alt, src) in zip(catalog, badges, strict=True):
            assert unescape(alt) == skill.name
            homepage_url = skill.url
            assert _filled(homepage_url), f"Missing homepage url for '{skill.name}'"
            homepage = homepage_url.strip()
            assert homepage.startswith("https://"), (
                f"Homepage for '{skill.name}' must be https: {skill.url}"
            )
            assert unescape(href) == homepage
            host = urlparse(homepage).netloc.lower().removeprefix("www.")
            assert host != "wikipedia.org" and not host.endswith(".wikipedia.org"), (
                f"Homepage for '{skill.name}' must not be Wikipedia: {homepage}"
            )
            decoded = unescape(src)
            assert decoded == gen._build_badge_url(skill)
            assert decoded.startswith("https://img.shields.io/badge/")
            assert len(decoded) <= MAX_SHIELDS_BADGE_URL_LENGTH

    def test_skills_badges_have_well_fitting_icons_and_renderable_sources(
        self, monkeypatch
    ):
        """Every badge has an https homepage, camo-safe src, and a real icon."""
        monkeypatch.chdir(REPO_ROOT)
        settings = load_skills()
        gen = SkillsBadgeGenerator(settings=settings)
        catalog = list(iter_skills(settings))
        html = gen._render_all()
        badges = re.findall(
            r'<a href="([^"]+)"><img alt="([^"]+)" src="([^"]+)"/></a>',
            html,
        )

        assert catalog
        assert len(badges) == len(catalog)
        for skill, (href, alt, src) in zip(catalog, badges, strict=True):
            assert unescape(alt) == skill.name
            assert unescape(href) == (skill.url or "").strip()
            decoded = unescape(src)
            assert decoded.startswith("https://img.shields.io/badge/")
            logo = _badge_logo_value(decoded)
            assert logo is not None and logo.strip(), (
                f"Missing well-fitting icon for '{skill.name}'"
            )

    def test_committed_readme_skill_srcs_fit_github_image_proxy(self):
        """Verify every committed badge against the catalog and its intended logo."""
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        start = readme.index(_SKILLS_MARKER_START) + len(_SKILLS_MARKER_START)
        end = readme.index(_SKILLS_MARKER_END, start)
        parser = _BadgeImages()
        parser.feed(readme[start:end])
        parser.close()
        settings = load_skills(REPO_ROOT / "skills.yaml")
        gen = SkillsBadgeGenerator(settings=settings)
        assert readme[start:end] == f"\n{gen._render_all()}\n"
        catalog = list(iter_skills(settings))
        assert catalog
        for skill, (alt, href, src, _) in zip(catalog, parser.images, strict=True):
            assert (alt, href, src) == (
                skill.name,
                skill.url,
                gen._build_badge_url(skill),
            )
            assert len(src) <= MAX_SHIELDS_BADGE_URL_LENGTH
            if _filled(skill.slug):
                assert _badge_logo_value(src) == skill.slug
            else:
                assert _filled(skill.logo_path)
                encoded = base64.b64encode(
                    (REPO_ROOT / skill.logo_path).read_bytes()
                ).decode()
                assert _badge_logo_value(src) == f"data:image/svg+xml;base64,{encoded}"

    @live_badge_qa
    def test_github_dev_readme_camo_renders_skill_icons(self, monkeypatch):
        """Verify the complete dev catalog through GitHub Camo."""
        monkeypatch.chdir(REPO_ROOT)
        settings = load_skills()
        gen = SkillsBadgeGenerator(settings=settings)
        catalog = list(iter_skills(settings))
        expected = {
            skill.name: (skill.url or "", gen._build_badge_url(skill))
            for skill in catalog
        }
        assert len(expected) == len(catalog)
        sources = _camo_sources(
            _fetch_github_dev_readme_html(), expected, settings.section_title
        )
        _check_rendered_badges(sources)

    def test_fact_badges_stack_every_shield_links_homepage(self, monkeypatch):
        """fact-badges-stack: every rendered shield wraps its https homepage."""
        monkeypatch.chdir(REPO_ROOT)
        settings = load_skills()
        gen = SkillsBadgeGenerator(settings=settings)
        html = gen._render_all()
        catalog = list(iter_skills(settings))
        badges = re.findall(
            r'<a href="([^"]+)"><img alt="([^"]+)" src="([^"]+)"/></a>',
            html,
        )
        assert catalog
        assert len(badges) == len(catalog)
        for skill, (href, alt, src) in zip(catalog, badges, strict=True):
            homepage = (skill.url or "").strip()
            assert homepage.startswith("https://"), skill.name
            assert unescape(alt) == skill.name
            assert unescape(href) == homepage
            decoded = unescape(src)
            assert decoded.startswith("https://img.shields.io/badge/")
            assert len(decoded) <= MAX_SHIELDS_BADGE_URL_LENGTH
            assert _filled(skill.slug) or _filled(skill.logo_path), skill.name

    def test_fact_badges_qa_shipped_shields_have_well_fitting_icons(self, monkeypatch):
        """fact-badges-qa: every rendered shield src has a well-fitting icon."""
        monkeypatch.chdir(REPO_ROOT)
        settings = load_skills()
        gen = SkillsBadgeGenerator(settings=settings)
        html = gen._render_all()
        catalog = list(iter_skills(settings))
        badges = re.findall(
            r'<a href="([^"]+)"><img alt="([^"]+)" src="([^"]+)"/></a>',
            html,
        )
        assert badges
        assert len(badges) == len(catalog)
        for skill, (_href, alt, src) in zip(catalog, badges, strict=True):
            assert unescape(alt) == skill.name
            decoded = unescape(src)
            assert decoded.startswith("https://img.shields.io/badge/")
            logo = _badge_logo_value(decoded)
            assert logo is not None and logo.strip(), skill.name
            assert len(decoded) <= MAX_SHIELDS_BADGE_URL_LENGTH

    @live_badge_qa
    def test_fact_badges_qa_every_shield_source_renders(self, monkeypatch):
        """fact-badges-qa: Verify every Shields badge's label and embedded icon."""
        monkeypatch.chdir(REPO_ROOT)
        settings = load_skills()
        gen = SkillsBadgeGenerator(settings=settings)
        sources = {
            skill.name: gen._build_badge_url(skill) for skill in iter_skills(settings)
        }
        assert len(sources) == len(list(iter_skills(settings)))
        _check_rendered_badges(sources)


@pytest.mark.parametrize(
    "defect", ["none", "partial", "wrong-logo", "duplicate", "wrong-host", "wrong-link"]
)
def test_camo_readback_requires_complete_catalog(defect: str) -> None:
    keys = ("Python", "R")
    expected = {
        k: (f"https://example.com/{k}", f"https://img.shields.io/badge/{k}?logo={k}")
        for k in keys
    }
    pieces = []
    for key in keys:
        href, canonical = expected[key]
        src = f"https://camo.githubusercontent.com/{key}"
        if key == "R":
            if defect == "partial":
                continue
            if defect == "wrong-logo":
                canonical = expected["Python"][1]
            if defect == "duplicate":
                src = "https://camo.githubusercontent.com/Python"
            if defect == "wrong-host":
                src = f"https://img.shields.io/camo.githubusercontent.com/{key}"
            if defect == "wrong-link":
                href = expected["Python"][0]
        pieces.append(
            f'<a href="{href}"><img alt="{key}" '
            f'data-canonical-src="{escape(canonical)}" src="{src}"></a>'
        )
    outside = '<a href="/profile"><img alt="Python" src="/connect-python.svg"></a>'
    html = (
        outside
        + "<details><summary><h2>My Tech Stack</h2></summary>"
        + "".join(pieces)
        + "</details>"
        + outside
        + "<h2>Next</h2>"
    )
    if defect == "none":
        assert _camo_sources(html, expected, "My Tech Stack") == {
            key: f"https://camo.githubusercontent.com/{key}" for key in keys
        }
    else:
        with pytest.raises(AssertionError):
            _camo_sources(html, expected, "My Tech Stack")


def test_badge_readback_exposes_unreachable_sources(monkeypatch):
    def unavailable(request, timeout):
        if request.full_url.endswith("/R"):
            raise HTTPError(request.full_url, 404, "Not found", HTTPMessage(), None)
        raise OSError("fixture unavailable")

    monkeypatch.setattr(__name__ + ".urlopen", unavailable)
    with pytest.raises(AssertionError) as result:
        _check_rendered_badges(
            {
                "Python": "https://img.shields.io/badge/Python",
                "R": "https://img.shields.io/badge/R",
            }
        )
    assert "Python: unreachable (fixture unavailable)" in str(result.value)
    assert "R: HTTP 404" in str(result.value)


def test_cli_skills_passes_strict_and_exits(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import scripts.cli.generate.readme_cmd as readme_cmd

    captured: dict[str, object] = {}

    class Recorder:
        def __init__(self, settings: SkillsSettings) -> None:
            self.settings = settings

        def generate(self, **kwargs: object) -> Path:
            captured.update(kwargs)
            return Path(self.settings.readme_path)

    skills_path = tmp_path / "skills.yaml"
    readme = tmp_path / "README.md"
    readme.write_text("untouched", encoding="utf-8")
    skills_path.write_text(
        f'readme_path: "{readme.as_posix()}"\ncategories: []\n',
        encoding="utf-8",
    )
    monkeypatch.setattr(readme_cmd, "_load_project_config", lambda _path: object())
    monkeypatch.setattr("scripts.skills.SkillsBadgeGenerator", Recorder)

    readme_cmd.skills(skills_path=skills_path)

    assert captured == {"strict": True}
    assert readme.read_text(encoding="utf-8") == "untouched"

    monkeypatch.setattr(
        "scripts.skills.SkillsBadgeGenerator",
        SkillsBadgeGenerator,
    )
    missing = tmp_path / "missing.md"
    skills_path.write_text(
        f'readme_path: "{missing.as_posix()}"\ncategories: []\n',
        encoding="utf-8",
    )
    with pytest.raises(typer.Exit) as missing_readme:
        readme_cmd.skills(skills_path=skills_path)
    assert missing_readme.value.exit_code == 1
    assert not missing.exists()

    unmarked = tmp_path / "unmarked.md"
    original = "# Hello\nNo markers here\n"
    unmarked.write_text(original, encoding="utf-8")
    skills_path.write_text(
        f'readme_path: "{unmarked.as_posix()}"\ncategories: []\n',
        encoding="utf-8",
    )
    with pytest.raises(typer.Exit) as missing_markers:
        readme_cmd.skills(skills_path=skills_path)
    assert missing_markers.value.exit_code == 1
    assert unmarked.read_text(encoding="utf-8") == original
