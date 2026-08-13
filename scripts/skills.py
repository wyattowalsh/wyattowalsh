"""Skills/Technology Badge Generator.

Reads a SkillsSettings configuration and generates shields.io badge HTML,
optionally injecting it into a README between comment markers.
"""

import base64
import re
from html import escape
from pathlib import Path
from urllib.parse import quote

from .config import (
    SkillCategory,
    SkillEntry,
    SkillsSettings,
    SkillSubcategory,
)
from .utils import get_logger

logger = get_logger(module=__name__)

_REPO_ROOT = Path(__file__).resolve().parent.parent

# Keep generated Shields source URLs comfortably below the request sizes that
# GitHub's image proxy rejects.  This is a public generation contract: callers
# may use it when validating rendered badge URLs before publishing a README.
MAX_SHIELDS_BADGE_URL_LENGTH = 4_000


def _resolve_repo_logo_path(logo_path: str) -> Path:
    """Resolve a validated repo-relative logo_path under the repository root.

    Raises:
        ValueError: if the resolved path escapes the repository root.
        OSError: if the path cannot be resolved on disk.
    """
    candidate = (_REPO_ROOT / logo_path).resolve(strict=False)
    try:
        candidate.relative_to(_REPO_ROOT)
    except ValueError as exc:
        raise ValueError(f"logo_path escapes repository root: {logo_path}") from exc
    return candidate


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
        logger.info(
            "Skills badges injected into {readme_path}", readme_path=readme_path
        )
        return readme_path

    def _build_badge_url(self, skill: SkillEntry) -> str:
        """Construct a GitHub-proxy-safe shields.io badge URL for a skill.

        Local SVG logos are preferred while their fully encoded source URL
        fits :data:`MAX_SHIELDS_BADGE_URL_LENGTH`.  An oversized or unreadable
        custom logo falls back to the configured Simple Icons slug, then to a
        no-logo badge when no usable slug can fit.  Base badge URLs that cannot
        satisfy the contract fail instead of being truncated.
        """
        label = quote(skill.name.replace("-", "--"), safe="")
        color = skill.color.lstrip("#")
        logo_color = skill.logo_color or self.settings.logo_color

        base_url = (
            f"https://img.shields.io/badge/{label}-{color}?style={self.settings.style}"
        )
        if len(base_url) > MAX_SHIELDS_BADGE_URL_LENGTH:
            raise ValueError(
                f"Badge URL for '{skill.name}' exceeds "
                f"{MAX_SHIELDS_BADGE_URL_LENGTH} characters without a logo"
            )

        if skill.logo_path:
            try:
                svg_path = _resolve_repo_logo_path(skill.logo_path)
                svg_b64 = base64.b64encode(svg_path.read_bytes()).decode()
                # safe='' ensures +, /, = in base64 are percent-encoded
                custom_logo_url = (
                    f"{base_url}&logo=data:image/svg%2Bxml;base64,"
                    f"{quote(svg_b64, safe='')}"
                )
                if len(custom_logo_url) <= MAX_SHIELDS_BADGE_URL_LENGTH:
                    return custom_logo_url

                logger.info(
                    "Custom badge logo for {skill_name} produces a {url_length}-"
                    "character URL; applying the {limit}-character fallback policy",
                    skill_name=skill.name,
                    url_length=len(custom_logo_url),
                    limit=MAX_SHIELDS_BADGE_URL_LENGTH,
                )
            except (OSError, ValueError) as exc:
                logger.info(
                    "Custom badge logo at {logo_path} could not be read for "
                    "{skill_name}; applying the fallback policy ({error_type})",
                    logo_path=skill.logo_path,
                    skill_name=skill.name,
                    error_type=type(exc).__name__,
                )

        slug = skill.slug.strip() if skill.slug else ""
        if slug:
            slug_url = (
                f"{base_url}&logo={quote(slug, safe='')}"
                f"&logoColor={quote(logo_color, safe='')}"
            )
            if len(slug_url) <= MAX_SHIELDS_BADGE_URL_LENGTH:
                return slug_url
            logger.info(
                "Simple Icons badge URL for {skill_name} exceeds {limit} "
                "characters; using a no-logo badge",
                skill_name=skill.name,
                limit=MAX_SHIELDS_BADGE_URL_LENGTH,
            )

        return base_url

    def _render_badge(self, skill: SkillEntry) -> str:
        """Render a single badge as an HTML img tag, optionally linked."""
        badge_url = self._build_badge_url(skill)
        img = f'<img alt="{escape(skill.name)}" src="{escape(badge_url)}"/>'
        if skill.url:
            return f'<a href="{escape(skill.url)}">{img}</a>'
        return img

    def _render_skills(self, skills: list[SkillEntry]) -> str:
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
            logger.warning(
                "README not found at {readme_path}, skipping injection",
                readme_path=readme_path,
            )
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
