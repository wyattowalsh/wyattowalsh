"""Skills/Technology Badge Generator.

Reads a SkillsSettings configuration and generates shields.io badge HTML,
optionally injecting it into a README between comment markers.
"""

import base64
import re
from html import escape
from pathlib import Path
from typing import List
from urllib.parse import quote

from .config import (
    SkillCategory,
    SkillEntry,
    SkillsSettings,
    SkillSubcategory,
)
from .utils import get_logger

logger = get_logger(module=__name__)


class SkillsBadgeGenerator:
    """Generates shields.io badge HTML from skills configuration."""

    MARKER_START = "<!-- SKILLS:START -->"
    MARKER_END = "<!-- SKILLS:END -->"

    def __init__(self, settings: SkillsSettings) -> None:
        self.settings = settings

    def generate(self) -> Path:
        """Generate badge HTML and inject into README.

        Returns:
            Path to the README that was modified.
        """
        html = self._render_all()
        readme_path = Path(self.settings.readme_path)
        self._inject_readme(html, readme_path)
        logger.info(f"Skills badges injected into {readme_path}")
        return readme_path

    def _build_badge_url(self, skill: SkillEntry) -> str:
        """Construct a shields.io badge URL for a skill."""
        label = quote(
            skill.name.replace("-", "--"), safe=""
        )
        color = skill.color.lstrip("#")
        logo_color = skill.logo_color or self.settings.logo_color

        url = (
            f"https://img.shields.io/badge/{label}-{color}"
            f"?style={self.settings.style}"
        )
        if skill.logo_path:
            svg_path = Path(skill.logo_path)
            try:
                svg_b64 = base64.b64encode(
                    svg_path.read_bytes()
                ).decode()
                # safe='' ensures +, /, = in base64 are percent-encoded
                url += (
                    f"&logo=data:image/svg%2Bxml;base64,"
                    f"{quote(svg_b64, safe='')}"
                )
            except OSError as exc:
                logger.warning(
                    f"logo_path '{skill.logo_path}' could not be read "
                    f"for '{skill.name}': {exc}"
                )
                if skill.slug:
                    url += f"&logo={quote(skill.slug, safe='')}"
                    url += f"&logoColor={logo_color}"
        elif skill.slug:
            url += f"&logo={quote(skill.slug, safe='')}"
            url += f"&logoColor={logo_color}"
        return url

    def _render_badge(self, skill: SkillEntry) -> str:
        """Render a single badge as an HTML img tag, optionally linked."""
        badge_url = self._build_badge_url(skill)
        img = f'<img alt="{escape(skill.name)}" src="{escape(badge_url)}"/>'
        if skill.url:
            return f'<a href="{escape(skill.url)}">{img}</a>'
        return img

    def _render_skills(self, skills: List[SkillEntry]) -> str:
        """Render a list of skills as a <p> block of badges."""
        if not skills:
            return ""
        badges = "\n  ".join(self._render_badge(s) for s in skills)
        return f"<p>\n  {badges}\n</p>"

    def _render_subcategory(self, sub: SkillSubcategory) -> str:
        """Render a subcategory with heading and badges."""
        lines = [f"#### {sub.name}", ""]
        rendered = self._render_skills(sub.skills)
        if rendered:
            lines.append(rendered)
        return "\n".join(lines)

    def _render_category(self, cat: SkillCategory) -> str:
        """Render a category with heading, badges, and subcategories."""
        lines = [f"### {cat.name}", ""]
        if cat.skills:
            lines.append(self._render_skills(cat.skills))
            lines.append("")
        for sub in cat.subcategories:
            lines.append(self._render_subcategory(sub))
            lines.append("")
        return "\n".join(lines).rstrip()

    def _render_all(self) -> str:
        """Render the full skills section HTML."""
        sections = []
        for cat in self.settings.categories:
            sections.append(self._render_category(cat))
        body = "\n\n".join(sections)

        if self.settings.collapsible:
            return (
                f"<details>\n"
                f"<summary><h2>{self.settings.section_title}</h2></summary>\n\n"
                f"{body}\n\n"
                f"</details>"
            )
        return body

    def _inject_readme(self, html: str, readme_path: Path) -> None:
        """Replace content between SKILLS markers in README."""
        if not readme_path.exists():
            logger.warning(f"README not found at {readme_path}, skipping injection")
            return

        content = readme_path.read_text(encoding="utf-8")
        pattern = re.compile(
            rf"{re.escape(self.MARKER_START)}\n.*?{re.escape(self.MARKER_END)}",
            re.DOTALL,
        )
        match = pattern.search(content)
        if not match:
            logger.warning(
                f"Skills markers not found in {readme_path}. "
                "Add <!-- SKILLS:START --> and <!-- SKILLS:END --> markers."
            )
            return

        replacement = f"{self.MARKER_START}\n{html}\n{self.MARKER_END}"
        new_content = content[: match.start()] + replacement + content[match.end() :]
        readme_path.write_text(new_content, encoding="utf-8")
