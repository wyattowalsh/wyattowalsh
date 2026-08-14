"""GFM UX contracts for the live profile README (post-R2 wrap-flow design).

These tests assert the committed README.md composition and the generator
rewrites that keep Living Art / Tech Stack aligned with that design.
They intentionally avoid callouts, footnotes, and Living Art <details> —
those are not part of the current GFM UX.
"""

from __future__ import annotations

import re
from pathlib import Path
from textwrap import dedent

from scripts.art.artifacts import LIVING_ART_STYLE_KEYS
from scripts.config import ReadmeSectionsSettings, load_config
from scripts.readme_sections import (
    ReadmeSectionGenerator,
    compile_section_body_re,
    section_order_from_settings,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
README_PATH = REPO_ROOT / "README.md"

_FEATURED_RE = re.compile(
    r"(?ms)<!-- README:FEATURED_PROJECTS:START -->\n"
    r".*?"
    r"<!-- README:FEATURED_PROJECTS:END -->"
)

# Category teaser shields that used to sit above the full-stack <details>.
_TEASER_ALTS = ("AI/ML", "Full-Stack", "Data Engineering", "Open Source")

_SECTION_HEADINGS = (
    "## Featured Projects",
    "## Metrics",
    "## Living Art",
    "## Tech Stack",
    "## Word Clouds",
)


def _order() -> tuple[str, ...]:
    try:
        settings = load_config().readme_sections_settings
    except Exception:  # noqa: BLE001 — fall back for isolated unit runs
        settings = ReadmeSectionsSettings()
    return section_order_from_settings(settings)


def _read_readme() -> str:
    return README_PATH.read_text(encoding="utf-8")


def _living_art_section(readme: str) -> str:
    match = compile_section_body_re("Living Art", _order()).search(readme)
    assert match is not None, "Living Art section missing"
    return match.group(0)


def _featured_block(readme: str) -> str:
    match = _FEATURED_RE.search(readme)
    assert match is not None, "Featured Projects managed markers missing"
    return match.group(0)


def _tech_stack_section(readme: str) -> str:
    match = compile_section_body_re("Tech Stack", _order()).search(readme)
    assert match is not None, "Tech Stack section missing"
    return match.group(0)


def test_living_art_wrap_flow_shows_all_six_gifs() -> None:
    """All six living-art GIFs are inline at width 360 inside one centered wrap."""
    living = _living_art_section(_read_readme())

    assert living.count('<p align="center">') == 1
    assert living.count("</p>") == 1
    assert living.count('width="360"') == 6
    assert living.count('width="100%"') == 0
    assert living.count('loading="lazy"') == 6

    for style in LIVING_ART_STYLE_KEYS:
        src = f".github/assets/img/living-{style}.gif"
        assert living.count(f'src="{src}"') == 1
        assert living.count(f'href="{src}"') == 1


def test_living_art_has_no_table_css_grid_or_details() -> None:
    """Wrap-flow Living Art must not use tables, CSS grid, or disclosures."""
    living = _living_art_section(_read_readme())
    lowered = living.lower()

    assert "<table" not in lowered
    assert "</table>" not in lowered
    assert "<details" not in lowered
    assert "</details>" not in lowered
    assert "display: grid" not in lowered
    assert "grid-template" not in lowered
    assert "<br/>" not in lowered
    assert "<sub>" not in lowered


def test_tech_stack_has_no_teaser_shields() -> None:
    """Tech Stack opens on the full-stack details; category teasers are gone."""
    tech = _tech_stack_section(_read_readme())
    body = tech.split("## Tech Stack", 1)[1].lstrip()

    assert body.startswith("<details>")
    assert "<summary><strong>Tech Stack</strong></summary>" in tech
    assert "View full stack" not in tech
    assert "200+" not in tech
    assert "<!-- SKILLS:START -->" in tech
    assert "<!-- SKILLS:END -->" in tech

    for alt in _TEASER_ALTS:
        assert f'alt="{alt}"' not in tech


def test_featured_projects_use_wrap_flow_cards() -> None:
    """Featured projects are a centered wrap of per-repo SVG cards (no table)."""
    featured = _featured_block(_read_readme())

    assert "<table" not in featured.lower()
    assert "More Featured Projects" not in featured
    assert "<details" not in featured.lower()
    assert featured.count('<p align="center">') == 1
    assert featured.count('width="360"') >= 10
    assert featured.count("featured-card-") >= 10
    assert featured.count('loading="lazy"') >= 10
    assert 'alt="Featured project card for ' in featured


def test_readme_section_order_and_managed_markers() -> None:
    """Major sections and injection markers stay ordered for GFM composition."""
    readme = _read_readme()

    positions = [readme.index(heading) for heading in _SECTION_HEADINGS]
    assert positions == sorted(positions)

    assert "<!-- README:TOP_BADGES:START -->" in readme
    assert "<!-- README:TOP_BADGES:END -->" in readme
    assert readme.index("<!-- README:TOP_BADGES:START -->") < readme.index(
        "<!-- README:TOP_BADGES:END -->"
    )
    assert readme.index("<!-- README:FEATURED_PROJECTS:START -->") < readme.index(
        "<!-- README:FEATURED_PROJECTS:END -->"
    )
    assert readme.index("<!-- README:BLOG_POSTS:START -->") < readme.index(
        "<!-- README:BLOG_POSTS:END -->"
    )

    # First viewport: banner picture → connect badges → featured (no living art yet).
    banner_idx = readme.index('alt="Banner"')
    badges_start = readme.index("<!-- README:TOP_BADGES:START -->")
    featured_start = readme.index("<!-- README:FEATURED_PROJECTS:START -->")
    living_start = readme.index("## Living Art")
    assert banner_idx < badges_start < featured_start < living_start


def test_waka_and_blog_are_visible_not_details() -> None:
    """WakaTime and blog are open-flow surfaces; only Tech Stack stays collapsed."""
    readme = _read_readme()
    living = _living_art_section(readme)

    assert "<summary><strong>WakaTime Stats</strong></summary>" not in readme
    assert "<summary><strong>Latest Blog Posts</strong></summary>" not in readme
    assert 'src=".github/assets/img/wakatime.svg"' in readme
    assert "<!--START_SECTION:waka-->" in readme
    assert "<!--END_SECTION:waka-->" in readme
    assert "## Latest Blog Posts" in readme
    assert "<!-- README:BLOG_POSTS:START -->" in readme
    assert "metrics-activity.svg" not in readme
    assert "200+" not in readme
    assert "komarev.com/ghpvc/" in readme
    assert "style=for-the-badge" in readme
    assert "style=flat-square" not in readme

    blog = readme[
        readme.index("<!-- README:BLOG_POSTS:START -->") : readme.index(
            "<!-- README:BLOG_POSTS:END -->"
        )
    ]
    assert blog.count('alt="Blog post card:') >= 4
    assert re.search(r"20\d{2}-\d{2}-\d{2}", blog)
    assert " · " in blog
    assert "<details" not in blog.lower()

    # Living Art GIFs must not be nested inside any details block.
    for match in re.finditer(
        r"(?is)<details\b.*?</details>",
        readme,
    ):
        block = match.group(0)
        assert "living-" not in block
        assert "## Living Art" not in block
        assert "wakatime.svg" not in block
        assert "README:BLOG_POSTS" not in block

    assert "<details" not in living


def test_generator_rewrites_living_art_and_drops_teasers() -> None:
    """Generator rewrites emit wrap-flow Living Art and strip tech teasers."""
    stale = dedent(
        """\
        ## Living Art

        <table><tr><td>stale</td></tr></table>
        <details><summary>hidden</summary>old</details>

        ## Tech Stack

        <p align="center">
          <img alt="AI/ML" src="https://img.shields.io/badge/AI%2FML-412991?style=for-the-badge"/>
          <img alt="Open Source" src="https://img.shields.io/badge/Open%20Source-181717?style=for-the-badge"/>
        </p>

        <details>
        <summary><strong>View full stack (200+ technologies)</strong></summary>

        <!-- SKILLS:START -->
        kept
        <!-- SKILLS:END -->

        </details>
        """
    )
    generator = ReadmeSectionGenerator(
        settings=ReadmeSectionsSettings(featured_repos=[], social_links=[]),
    )
    rendered = generator._rewrite_living_art_section(stale)
    rendered = generator._rewrite_tech_stack_teaser(rendered)
    living = _living_art_section(rendered)
    tech = rendered.split("## Tech Stack", 1)[1]

    assert living.count('src=".github/assets/img/living-') == 6
    assert living.count('width="360"') == 6
    assert "<table" not in living.lower()
    assert "<details" not in living.lower()
    assert living.count('<p align="center">') == 1
    assert 'alt="AI/ML"' not in tech
    assert 'alt="Open Source"' not in tech
    assert tech.lstrip().startswith("<details>")
    assert "<summary><strong>Tech Stack</strong></summary>" in tech
    assert "View full stack" not in tech
    assert "200+" not in tech
    assert "kept" in tech
