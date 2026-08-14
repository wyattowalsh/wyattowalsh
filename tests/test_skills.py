"""Tests for skills badge generation."""

import base64
import re
from collections.abc import Iterable
from concurrent.futures import ThreadPoolExecutor, as_completed
from html import unescape
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qsl, quote, unquote, urlparse
from urllib.request import Request, urlopen

import pytest
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
RENDER_QA_HEAD_TIMEOUT_SECONDS = 8.0
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
    """Return True when a data-URI logo starts as SVG or decodes to ``<svg``."""
    if not logo.startswith("data:"):
        return logo.lstrip().lower().startswith(("svg", "<svg"))
    metadata, separator, payload = logo.partition(",")
    if not separator:
        stripped = logo.lstrip()
        return stripped.lower().startswith(("svg", "<svg"))
    if "base64" in metadata.lower():
        try:
            text = base64.b64decode(payload).decode("utf-8")
        except (ValueError, UnicodeDecodeError):
            return False
    else:
        text = unquote(payload)
    stripped = text.lstrip("\ufeff \t\r\n")
    return stripped.startswith("<svg") or stripped.lower().startswith("svg")


def _request_badge_source_status(src: str) -> int:
    """HEAD a shields.io or Camo URL, falling back to GET when HEAD is rejected."""
    headers = {"User-Agent": "wyattowalsh-skills-badge-qa"}
    request = Request(src, method="HEAD", headers=headers)
    try:
        with urlopen(request, timeout=RENDER_QA_HEAD_TIMEOUT_SECONDS) as response:
            return int(getattr(response, "status", None) or response.getcode())
    except HTTPError as exc:
        if exc.code != 405:
            raise
        get_request = Request(src, method="GET", headers=headers)
        with urlopen(get_request, timeout=RENDER_QA_HEAD_TIMEOUT_SECONDS) as response:
            return int(getattr(response, "status", None) or response.getcode())


def _head_all_or_skip(srcs: list[str], *, label: str) -> None:
    """HEAD every source URL; skip only when the host is unreachable."""
    decoded = [unescape(src) for src in srcs]
    if not decoded:
        pytest.skip(f"no {label} sources available to HEAD")
    errors: list[str] = []
    try:
        with ThreadPoolExecutor(max_workers=8) as pool:
            futures = {
                pool.submit(_request_badge_source_status, src): src for src in decoded
            }
            for future in as_completed(futures):
                src = futures[future]
                try:
                    status = future.result()
                except HTTPError as exc:
                    errors.append(f"HTTP {exc.code}: {src[:96]}")
                    continue
                if not (200 <= status < 400):
                    errors.append(f"HTTP {status}: {src[:96]}")
    except (URLError, TimeoutError, OSError) as exc:
        pytest.skip(f"{label} unreachable for render QA: {exc}")
    assert not errors, f"{label} sources failed render QA:\n" + "\n".join(errors)


def _fetch_github_dev_readme_html_or_skip() -> str:
    """Load GitHub-rendered origin/dev README HTML (Camo img srcs)."""
    request = Request(
        GITHUB_DEV_README_HTML_URL,
        headers={
            "Accept": "application/vnd.github.html+json",
            "User-Agent": "wyattowalsh-skills-badge-qa",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with urlopen(request, timeout=RENDER_QA_HEAD_TIMEOUT_SECONDS) as response:
            return response.read().decode("utf-8", errors="replace")
    except HTTPError as exc:
        if exc.code in {401, 403, 404, 429}:
            pytest.skip(f"GitHub README HTML unavailable: HTTP {exc.code}")
        raise
    except (URLError, TimeoutError, OSError) as exc:
        pytest.skip(f"GitHub README HTML unreachable: {exc}")


def _alt_covers_catalog(alt: str, catalog_names: set[str]) -> bool:
    """True when *alt* is a skill name or a category board listing catalog names."""
    if alt in catalog_names:
        return True
    if ": " not in alt:
        return False
    listed = {part.strip() for part in alt.split(":", 1)[1].split(",")}
    return bool(listed & catalog_names)


def _camo_images_from_html(html: str) -> list[tuple[str, str]]:
    """Return ``(alt, camo_src)`` pairs from GitHub-rendered README HTML."""
    found: list[tuple[str, str]] = []
    for tag in re.findall(r"<img\b[^>]*>", html, flags=re.IGNORECASE):
        src_match = re.search(r'\bsrc="([^"]+)"', tag, flags=re.IGNORECASE)
        alt_match = re.search(r'\balt="([^"]*)"', tag, flags=re.IGNORECASE)
        if src_match is None:
            continue
        src = unescape(src_match.group(1))
        if "camo.githubusercontent.com" not in src:
            continue
        alt = unescape(alt_match.group(1)) if alt_match is not None else ""
        found.append((alt, src))
    return found


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

    def test_logo_path_priority_over_slug(self, tmp_path, monkeypatch):
        monkeypatch.setattr("scripts.skills._REPO_ROOT", tmp_path)
        rel = Path("assets/priority.svg")
        svg_path = tmp_path / rel
        svg_path.parent.mkdir()
        svg_path.write_bytes(b'<svg xmlns="http://www.w3.org/2000/svg"/>')

        skill = SkillEntry(
            name="PowerShell",
            slug="powershell",
            logo_path=rel.as_posix(),
            color="5391FE",
        )
        url = self.gen._build_badge_url(skill)
        assert "logo=powershell" in url
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
        assert "### Languages" in html
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
        assert "### Data" in html
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

    def test_missing_markers_warns(self, tmp_path):
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
        gen.generate()
        # Content should be unchanged
        assert readme.read_text() == "# Hello\nNo markers here\n"

    def test_missing_readme_warns(self, tmp_path):
        settings = SkillsSettings(
            readme_path=str(tmp_path / "nonexistent.md"),
            categories=[],
        )
        gen = SkillsBadgeGenerator(settings=settings)
        # Should not raise
        result = gen.generate()
        assert result == Path(settings.readme_path)


# ---------------------------------------------------------------------------
# Integration tests
# ---------------------------------------------------------------------------


class TestIntegration:
    def test_skills_yaml_logo_paths_all_exist(self, monkeypatch):
        """All logo_path entries in skills.yaml must point to real files."""
        monkeypatch.chdir(REPO_ROOT)
        settings = load_skills()
        for skill in iter_skills(settings):
            if skill.logo_path:
                assert Path(skill.logo_path).exists(), (
                    f"Missing icon for '{skill.name}': {skill.logo_path}"
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
            if not skill.logo_path:
                continue

            path = Path(skill.logo_path)
            assert path.suffix == ".svg", (
                f"Local logo must be SVG for '{skill.name}': {skill.logo_path}"
            )
            content = path.read_text(encoding="utf-8")
            assert "<svg" in content, f"Local logo is not SVG: {skill.logo_path}"
            assert skill.logo_source, f"Missing logo_source for '{skill.name}'"
            assert skill.logo_source_url, f"Missing logo_source_url for '{skill.name}'"
            assert skill.logo_license, f"Missing logo_license for '{skill.name}'"
            assert skill.logo_style, f"Missing logo_style for '{skill.name}'"

            url = gen._build_badge_url(skill)
            assert len(url) <= MAX_SHIELDS_BADGE_URL_LENGTH
            if "logo=data:image/svg%2Bxml;base64," not in url:
                if skill.slug:
                    assert f"logo={quote(skill.slug, safe='')}" in url
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
            if not skill.logo_path:
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

            if skill.slug:
                assert skill.slug in known_slugs, (
                    f"Unsupported local-logo fallback slug for '{skill.name}': "
                    f"{skill.slug}"
                )
                assert f"logo={quote(skill.slug, safe='')}" in url
                fallbacks[skill.name] = skill.slug
            else:
                assert "&logo=" not in url
                no_logo_fallbacks.add(skill.name)

        expected_slug_first = {
            skill.name: skill.slug
            for skill in iter_skills(settings)
            if skill.logo_path and (skill.slug or "").strip()
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
            if not skill.logo_path:
                continue

            path = Path(skill.logo_path)
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
            if expected_paint:
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
                assert skill.slug
                assert skill.slug in known_slugs, (
                    f"Unknown Simple Icons slug for '{skill.name}': {skill.slug}"
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
            assert skill.url, f"Missing homepage url for '{skill.name}'"
            homepage = skill.url.strip()
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
        """Every committed README skill src stays under the Camo URL budget."""
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        start = readme.find(_SKILLS_MARKER_START)
        end = readme.find(_SKILLS_MARKER_END)
        assert start != -1 and end != -1 and start < end
        block = readme[start:end]
        srcs = re.findall(r'<img alt="[^"]+" src="([^"]+)"', block)
        assert srcs
        for src in srcs:
            decoded = unescape(src)
            assert decoded.startswith("https://img.shields.io/badge/"), decoded[:96]
            assert len(decoded) <= MAX_SHIELDS_BADGE_URL_LENGTH

    def test_github_dev_readme_camo_renders_skill_icons(self, monkeypatch):
        """Every skill icon on blob/dev README must render through GitHub Camo."""
        monkeypatch.chdir(REPO_ROOT)
        settings = load_skills()
        catalog = list(iter_skills(settings))
        catalog_names = {skill.name for skill in catalog}
        html = _fetch_github_dev_readme_html_or_skip()
        camo = [
            (alt, src)
            for alt, src in _camo_images_from_html(html)
            if _alt_covers_catalog(alt, catalog_names)
        ]
        if camo:
            _head_all_or_skip([src for _alt, src in camo], label="github.com/camo")
            return
        gen = SkillsBadgeGenerator(settings=settings)
        _head_all_or_skip(
            [gen._build_badge_url(skill) for skill in catalog],
            label="img.shields.io",
        )

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
            assert skill.slug or skill.logo_path, skill.name

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

    def test_fact_badges_qa_every_shield_source_renders(self, monkeypatch):
        """fact-badges-qa: HEAD every generated shields.io source URL."""
        monkeypatch.chdir(REPO_ROOT)
        settings = load_skills()
        gen = SkillsBadgeGenerator(settings=settings)
        srcs = [gen._build_badge_url(skill) for skill in iter_skills(settings)]
        assert len(srcs) == 151
        _head_all_or_skip(srcs, label="img.shields.io")
