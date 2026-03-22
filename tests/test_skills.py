"""Tests for skills badge generation."""

import base64
from pathlib import Path
from urllib.parse import quote

import pytest
from pydantic import ValidationError

from scripts.config import (
    SkillCategory,
    SkillEntry,
    SkillsSettings,
    SkillSubcategory,
    load_skills,
)
from scripts.skills import SkillsBadgeGenerator

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
        gen = SkillsBadgeGenerator(
            settings=SkillsSettings(style="flat-square")
        )
        skill = SkillEntry(name="Test", color="000000")
        url = gen._build_badge_url(skill)
        assert "style=flat-square" in url

    def test_logo_path_base64(self, tmp_path):
        svg_file = tmp_path / "test.svg"
        svg_content = (
            b'<svg xmlns="http://www.w3.org/2000/svg">'
            b'<circle r="5" fill="white"/>'
            b"</svg>"
        )
        svg_file.write_bytes(svg_content)

        skill = SkillEntry(
            name="TestSkill", logo_path=str(svg_file), color="FF0000"
        )
        url = self.gen._build_badge_url(skill)
        expected_b64 = quote(
            base64.b64encode(svg_content).decode(), safe=""
        )
        assert f"logo=data:image/svg%2Bxml;base64,{expected_b64}" in url
        assert "logo=TestSkill" not in url

    def test_logo_path_base64_urlencodes_plus(self, tmp_path):
        """Base64 +/= chars must be percent-encoded for URL safety."""
        svg_file = tmp_path / "test.svg"
        # Content that produces + in base64 (0xfb byte → +)
        svg_content = b'\xfb\xef\xbe'
        svg_file.write_bytes(svg_content)

        skill = SkillEntry(
            name="Test", logo_path=str(svg_file), color="000000"
        )
        url = self.gen._build_badge_url(skill)
        b64_section = url.split("base64,")[1].split("&")[0]
        assert "+" not in b64_section, "raw + in URL would be decoded as space"
        assert "%2B" in b64_section or "%2b" in b64_section

    def test_logo_path_base64_urlencodes_slash_and_equals(self, tmp_path):
        """Base64 / and = chars must be percent-encoded for URL safety."""
        svg_file = tmp_path / "test.svg"
        # b'\xff' produces /w== in base64 (contains both / and =)
        svg_file.write_bytes(b'\xff')
        skill = SkillEntry(
            name="Test", logo_path=str(svg_file), color="000000"
        )
        url = self.gen._build_badge_url(skill)
        b64_section = url.split("base64,")[1].split("&")[0]
        assert "/" not in b64_section, "raw / would break URL path"
        assert "=" not in b64_section, "raw = would break query parsing"
        assert "%2F" in b64_section
        assert "%3D" in b64_section

    def test_logo_path_priority_over_slug(self, tmp_path):
        svg_file = tmp_path / "custom.svg"
        svg_file.write_bytes(b'<svg xmlns="http://www.w3.org/2000/svg"/>')

        skill = SkillEntry(
            name="PowerShell",
            slug="powershell",
            logo_path=str(svg_file),
            color="5391FE",
        )
        url = self.gen._build_badge_url(skill)
        assert "logo=data:image/svg%2Bxml;base64," in url
        assert "logo=powershell" not in url

    def test_logo_path_fallback_to_slug_when_missing(self, captured_warnings):
        skill = SkillEntry(
            name="Missing",
            slug="fallback",
            logo_path="nonexistent/path.svg",
            color="000000",
        )
        url = self.gen._build_badge_url(skill)
        assert "logo=fallback" in url
        assert "base64" not in url
        assert any(
            "nonexistent/path.svg" in w for w in captured_warnings
        ), f"Expected warning about missing logo_path, got: {captured_warnings}"

    def test_logo_path_missing_no_slug(self):
        skill = SkillEntry(
            name="NoLogo",
            logo_path="nonexistent/path.svg",
            color="000000",
        )
        url = self.gen._build_badge_url(skill)
        assert "logo=" not in url


# ---------------------------------------------------------------------------
# HTML rendering
# ---------------------------------------------------------------------------

class TestRendering:
    def test_render_badge_with_url(self):
        gen = SkillsBadgeGenerator(settings=SkillsSettings())
        skill = SkillEntry(
            name="Python", slug="python", color="3776AB",
            url="https://python.org"
        )
        html = gen._render_badge(skill)
        assert '<a href="https://python.org">' in html
        assert 'alt="Python"' in html

    def test_render_badge_without_url(self):
        gen = SkillsBadgeGenerator(settings=SkillsSettings())
        skill = SkillEntry(name="SQL", color="4479A1")
        html = gen._render_badge(skill)
        assert "<a " not in html
        assert "<img " in html

    def test_render_category(self):
        gen = SkillsBadgeGenerator(settings=SkillsSettings())
        cat = SkillCategory(
            name="Languages",
            skills=[SkillEntry(name="Python", color="3776AB")],
        )
        html = gen._render_category(cat)
        assert "### Languages" in html
        assert "Python" in html

    def test_render_subcategory(self):
        gen = SkillsBadgeGenerator(settings=SkillsSettings())
        cat = SkillCategory(
            name="Data",
            subcategories=[
                SkillSubcategory(
                    name="Storage",
                    skills=[SkillEntry(name="PostgreSQL", color="4169E1")],
                )
            ],
        )
        html = gen._render_category(cat)
        assert "### Data" in html
        assert "#### Storage" in html
        assert "PostgreSQL" in html

    def test_collapsible(self):
        settings = SkillsSettings(
            collapsible=True,
            categories=[
                SkillCategory(
                    name="Test",
                    skills=[SkillEntry(name="X", color="000000")],
                )
            ],
        )
        gen = SkillsBadgeGenerator(settings=settings)
        html = gen._render_all()
        assert "<details>" in html
        assert "</details>" in html


# ---------------------------------------------------------------------------
# README injection
# ---------------------------------------------------------------------------

class TestReadmeInjection:
    def test_replaces_between_markers(self, tmp_path):
        readme = tmp_path / "README.md"
        readme.write_text(
            "before\n"
            "<!-- SKILLS:START -->\n"
            "old content\n"
            "<!-- SKILLS:END -->\n"
            "after\n"
        )
        settings = SkillsSettings(
            readme_path=str(readme),
            categories=[
                SkillCategory(
                    name="Test",
                    skills=[SkillEntry(name="Python", color="3776AB")],
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
                    skills=[SkillEntry(name="X", color="000")],
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
        monkeypatch.chdir(Path(__file__).resolve().parent.parent)
        settings = load_skills()
        for cat in settings.categories:
            for skill in cat.skills:
                if skill.logo_path:
                    assert Path(skill.logo_path).exists(), (
                        f"Missing icon for '{skill.name}': {skill.logo_path}"
                    )
            for sub in cat.subcategories:
                for skill in sub.skills:
                    if skill.logo_path:
                        assert Path(skill.logo_path).exists(), (
                            f"Missing icon for '{skill.name}': {skill.logo_path}"
                        )
