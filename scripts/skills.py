"""Skills/Technology Badge Generator.

Reads a SkillsSettings configuration and generates shields.io badge HTML,
optionally injecting it into a README between comment markers.
"""

import base64
import re
from html import escape
from pathlib import Path
from urllib.parse import quote, urlparse

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
_DEFAULT_BADGE_COLOR = "555555"
_WIKIPEDIA_HOST = "wikipedia.org"

# Offline Simple Icons brand hexes (no '#'). Applied only when a skill still
# uses the default gray badge color. Never fetched at generation time.
_SIMPLE_ICON_BRAND_HEX: dict[str, str] = {
    "amazonaws": "232F3E",
    "apacheairflow": "017CEE",
    "apachekafka": "231F20",
    "apachespark": "E25A1C",
    "cplusplus": "00599C",
    "cypress": "69D3A7",
    "docker": "2496ED",
    "electron": "47848F",
    "eslint": "4B32C3",
    "express": "000000",
    "fastapi": "009688",
    "figma": "F24E1E",
    "flask": "000000",
    "gatsby": "663399",
    "git": "F05032",
    "github": "181717",
    "githubactions": "2088FF",
    "gitlab": "FC6D26",
    "go": "00ADD8",
    "googlecloud": "4285F4",
    "grafana": "F46800",
    "graphql": "E10098",
    "html5": "E34F26",
    "huggingface": "FFD21E",
    "javascript": "F7DF1E",
    "jest": "C21325",
    "jupyter": "F37626",
    "keras": "D00000",
    "kubernetes": "326CE5",
    "langchain": "1C3C3C",
    "linux": "FCC624",
    "markdown": "000000",
    "microsoftazure": "0078D4",
    "mui": "007FFF",
    "mysql": "4479A1",
    "neo4j": "4581C3",
    "nextdotjs": "000000",
    "nodedotjs": "5FA04E",
    "notion": "000000",
    "npm": "CB3837",
    "numpy": "013243",
    "opencv": "5C3EE8",
    "openjdk": "000000",
    "pandas": "150458",
    "postgresql": "4169E1",
    "prometheus": "E6522C",
    "pydantic": "E92063",
    "pytest": "0A9EDC",
    "pytorch": "EE4C2C",
    "python": "3776AB",
    "r": "276DC3",
    "react": "61DAFB",
    "redis": "FF4438",
    "ruby": "CC342D",
    "sass": "CC6699",
    "scikitlearn": "F7931E",
    "sqlite": "003B57",
    "storybook": "FF4785",
    "supabase": "3FCF8E",
    "tailwindcss": "06B6D4",
    "tensorflow": "FF6F00",
    "terraform": "844FBA",
    "typescript": "3178C6",
    "vercel": "000000",
    "vite": "646CFF",
    "yarn": "2C8EBB",
}


def _resolved_badge_color(skill: SkillEntry) -> str:
    """Return the shields hex, using a slug brand color when still default gray."""
    raw = skill.color.strip() if skill.color else ""
    color = raw.lstrip("#")
    if color.casefold() not in {"", _DEFAULT_BADGE_COLOR}:
        return color
    slug = skill.slug.strip().casefold() if skill.slug else ""
    return _SIMPLE_ICON_BRAND_HEX.get(slug, color or _DEFAULT_BADGE_COLOR)


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

        Simple Icons slugs are preferred: they stay well under GitHub Camo's
        URL budget.  A local SVG ``logo_path`` is used only when no usable
        slug exists and the fully encoded data-URI still fits
        :data:`MAX_SHIELDS_BADGE_URL_LENGTH`.  Oversized or unreadable custom
        logos fall back to a no-logo badge.  Base badge URLs that cannot
        satisfy the contract fail instead of being truncated.

        A missing or default gray (``555555``) badge color is replaced with a
        known Simple Icons brand hex when the skill slug is in the offline
        map.  Explicit colors and homepage wrapping are left unchanged.
        """
        label = quote(skill.name.replace("-", "--"), safe="")
        color = _resolved_badge_color(skill)
        logo_color = skill.logo_color or self.settings.logo_color

        base_url = (
            f"https://img.shields.io/badge/{label}-{color}?style={self.settings.style}"
        )
        if len(base_url) > MAX_SHIELDS_BADGE_URL_LENGTH:
            raise ValueError(
                f"Badge URL for '{skill.name}' exceeds "
                f"{MAX_SHIELDS_BADGE_URL_LENGTH} characters without a logo"
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
                "characters; applying the custom-logo / no-logo fallback",
                skill_name=skill.name,
                limit=MAX_SHIELDS_BADGE_URL_LENGTH,
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

        return base_url

    def _homepage_href(self, skill: SkillEntry) -> str:
        """Return the GitHub-safe https tech homepage for a published shield.

        Wikipedia is not a homepage. ``http://`` is accepted by the config
        model but is rejected here — every rendered badge must wrap
        ``https://``.
        """
        homepage = skill.url.strip() if skill.url else ""
        if not homepage:
            raise ValueError(f"Homepage url is required for '{skill.name}'")
        if not homepage.lower().startswith("https://"):
            raise ValueError(
                f"Homepage for '{skill.name}' must be https://: {skill.url}"
            )
        host = urlparse(homepage).netloc.lower().removeprefix("www.")
        if host == _WIKIPEDIA_HOST or host.endswith(f".{_WIKIPEDIA_HOST}"):
            raise ValueError(
                f"Homepage for '{skill.name}' must be the tech homepage, "
                f"not Wikipedia: {homepage}"
            )
        return homepage

    def _render_badge(self, skill: SkillEntry) -> str:
        """Render a single linked shields.io badge."""
        badge_url = self._build_badge_url(skill)
        img = f'<img alt="{escape(skill.name)}" src="{escape(badge_url)}"/>'
        homepage = self._homepage_href(skill)
        return f'<a href="{escape(homepage, quote=True)}">{img}</a>'

    def _render_skills(self, skills: list[SkillEntry]) -> str:
        """Render a list of skills as a <p> block of linked badges."""
        if not skills:
            return ""
        badges = "\n  ".join(self._render_badge(s) for s in skills)
        return f"<p>\n  {badges}\n</p>"

    def _render_subcategory(self, sub: SkillSubcategory) -> str:
        """Render a subcategory heading plus its linked shields.

        Empty skill lists produce no heading.
        """
        rendered = self._render_skills(sub.skills)
        if not rendered:
            return ""
        return f"#### {sub.name}\n\n{rendered}"

    def _render_category(self, cat: SkillCategory) -> str:
        """Render a category heading plus per-skill homepage-linked shields."""
        lines = [f"### {cat.name}", ""]
        if cat.skills:
            lines.append(self._render_skills(cat.skills))
        for sub in cat.subcategories:
            if not sub.skills:
                continue
            if lines[-1] != "":
                lines.append("")
            lines.append(self._render_subcategory(sub))
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
