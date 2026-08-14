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
_BOARD_DIR = _REPO_ROOT / ".github" / "assets" / "img" / "readme"
_BOARD_FONT = (
    "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans',"
    " Helvetica, Arial, sans-serif"
)

# Keep generated Shields source URLs comfortably below the request sizes that
# GitHub's image proxy rejects.  This is a public generation contract: callers
# may use it when validating rendered badge URLs before publishing a README.
MAX_SHIELDS_BADGE_URL_LENGTH = 4_000
_WIKIPEDIA_HOST = "wikipedia.org"


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
        self._persist_boards = False

    def generate(self) -> Path:
        """Generate badge HTML and inject into README.

        Returns:
            Path to the README that was modified.
        """
        self._persist_boards = True
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

    def _homepage_href(self, skill: SkillEntry) -> str | None:
        """Return a GitHub-safe https tech homepage, or None when unlinked.

        Wikipedia is not a homepage. ``http://`` is accepted by the config
        model but is never wrapped — catalog badges must use ``https://``.
        """
        homepage = skill.url.strip() if skill.url else ""
        if not homepage:
            return None
        if not homepage.lower().startswith("https://"):
            return None
        host = urlparse(homepage).netloc.lower().removeprefix("www.")
        if host == _WIKIPEDIA_HOST or host.endswith(f".{_WIKIPEDIA_HOST}"):
            raise ValueError(
                f"Homepage for '{skill.name}' must be the tech homepage, "
                f"not Wikipedia: {homepage}"
            )
        return homepage

    def _render_badge(self, skill: SkillEntry) -> str:
        """Render a single badge as an HTML img tag, optionally linked."""
        badge_url = self._build_badge_url(skill)
        img = f'<img alt="{escape(skill.name)}" src="{escape(badge_url)}"/>'
        homepage = self._homepage_href(skill)
        if homepage:
            return f'<a href="{escape(homepage, quote=True)}">{img}</a>'
        return img

    def _iter_category_groups(
        self, cat: SkillCategory
    ) -> list[tuple[str, list[SkillEntry]]]:
        groups: list[tuple[str, list[SkillEntry]]] = []
        if cat.skills:
            groups.append(("", cat.skills))
        for sub in cat.subcategories:
            if sub.skills:
                groups.append((sub.name, sub.skills))
        return groups

    def _chip_width(self, name: str) -> int:
        return max(72, min(220, 22 + int(len(name) * 7.2)))

    def _render_board_svg(
        self,
        title: str,
        groups: list[tuple[str, list[SkillEntry]]],
    ) -> str:
        width = 1200
        x = 16
        y = 18
        row_h = 34
        chips: list[str] = []
        names: list[str] = []
        for group_name, skills in groups:
            if group_name:
                if x > 16:
                    x = 16
                    y += row_h + 8
                chips.append(
                    f'<text class="group" x="16" y="{y + 18}">'
                    f"{escape(group_name)}</text>"
                )
                y += 26
            for skill in skills:
                chip_w = self._chip_width(skill.name)
                if x + chip_w > width - 16:
                    x = 16
                    y += row_h + 8
                fill = f"#{skill.color.lstrip('#')}"
                chips.append(
                    f'<rect x="{x}" y="{y}" width="{chip_w}" height="30" '
                    f'rx="8" fill="{fill}" />'
                )
                chips.append(
                    f'<text class="chip" x="{x + chip_w / 2:.0f}" y="{y + 20}" '
                    f'text-anchor="middle">{escape(skill.name)}</text>'
                )
                names.append(skill.name)
                x += chip_w + 8
            x = 16
            y += row_h + 12
        height = y + 8
        css = (
            ":root { color-scheme: light dark; }\n"
            f".chip {{ fill: #ffffff; font: 700 12px {_BOARD_FONT}; }}\n"
            f".group {{ fill: #656d76; font: 700 11px {_BOARD_FONT}; "
            "letter-spacing: 0.06em; text-transform: uppercase; }\n"
            "@media (prefers-color-scheme: dark) {\n"
            "  .group { fill: #8b949e; }\n"
            "}\n"
        )
        return "\n".join(
            [
                (
                    f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
                    f'height="{height}" viewBox="0 0 {width} {height}" '
                    f'role="img" aria-label="{escape(title, quote=True)}">'
                ),
                f"<title>{escape(title)}</title>",
                f"<desc>{escape(', '.join(names))}</desc>",
                f"<style>{css}</style>",
                f'<rect width="{width}" height="{height}" rx="12" '
                'fill="transparent" />',
                *chips,
                "</svg>",
            ]
        )

    def _write_category_board(self, cat: SkillCategory) -> Path:
        slug = re.sub(r"[^a-z0-9]+", "-", cat.name.lower()).strip("-")
        path = _BOARD_DIR / f"tech-{slug}.svg"
        if self._persist_boards:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                self._render_board_svg(cat.name, self._iter_category_groups(cat)),
                encoding="utf-8",
            )
        return path

    def _render_skills(self, skills: list[SkillEntry]) -> str:
        """Render a list of skills as a <p> block of badges."""
        if not skills:
            return ""
        badges = "\n  ".join(self._render_badge(s) for s in skills)
        return f"<p>\n  {badges}\n</p>"

    def _render_subcategory(self, sub: SkillSubcategory) -> str:
        """Render a subcategory heading used by board fallbacks."""
        lines = [f"#### {sub.name}", ""]
        names = ", ".join(skill.name for skill in sub.skills)
        if names:
            lines.append(names)
        return "\n".join(lines)

    def _render_category(self, cat: SkillCategory) -> str:
        """Render a category heading plus a first-party chip board."""
        groups = self._iter_category_groups(cat)
        names = [skill.name for _, skills in groups for skill in skills]
        board = self._write_category_board(cat)
        rel = board.relative_to(_REPO_ROOT).as_posix()
        alt = f"{cat.name}: {', '.join(names)}" if names else cat.name
        lines = [
            f"### {cat.name}",
            "",
            (
                f'<p align="center"><img alt="{escape(alt)}" '
                f'src="{escape(rel)}" width="100%" loading="lazy"/></p>'
            ),
        ]
        for sub in cat.subcategories:
            if sub.skills:
                lines.extend(["", f"#### {sub.name}"])
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
