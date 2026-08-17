"""GFM UX contracts for the live profile README (post-R2 wrap-flow design).

These tests assert the committed README.md composition and the generator
rewrites that keep Living Art / My Tech Stack aligned with that design.
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
from scripts.readme_separators import SEPARATOR_SPECS, generate_separators

REPO_ROOT = Path(__file__).resolve().parents[1]
README_PATH = REPO_ROOT / "README.md"

_FEATURED_RE = re.compile(
    r"(?ms)<!-- README:FEATURED_PROJECTS:START -->\n"
    r".*?"
    r"<!-- README:FEATURED_PROJECTS:END -->"
)

# Category teaser shields that used to sit above the full-stack <details>.
_TEASER_ALTS = ("AI/ML", "Full-Stack", "Data Engineering", "Open Source")

_SECTION_TITLES = (
    "Featured Projects",
    "Metrics",
    "Living Art",
    "My Tech Stack",
    "Word Clouds",
)
SECTION_SEPARATORS = {
    "Featured Projects": "sep-featured.svg",
    "Metrics": "sep-metrics.svg",
    "Living Art": "sep-living.svg",
    "My Tech Stack": "sep-tech.svg",
    "Word Clouds": "sep-clouds.svg",
    "Latest Blog Posts": "sep-blog.svg",
    "Connect": "sep-qr.svg",
}


def test_section_separators_paint_outside_defs() -> None:
    """Separator strokes must render; wrapping them in <defs> hides them."""
    for filename in SECTION_SEPARATORS.values():
        svg = (REPO_ROOT / ".github/assets/img/readme" / filename).read_text(
            encoding="utf-8"
        )
        after_defs = re.sub(r"<defs>.*?</defs>", "", svg, flags=re.S)
        assert re.search(r"<(line|rect|circle|path|polyline)\b", after_defs), filename


def _assert_separator_contract(svg: str, filename: str) -> None:
    assert "@media (prefers-color-scheme: dark)" in svg, filename
    assert "<style" in svg, filename
    assert 'width="1200"' in svg, filename
    height = re.search(r'\bheight="(\d+)"', svg)
    assert height is not None, filename
    assert 48 <= int(height.group(1)) <= 56, filename
    after_defs = re.sub(r"<defs>.*?</defs>", "", svg, flags=re.S)
    assert re.search(r"<(line|rect|circle|path|polyline)\b", after_defs), filename


def test_section_separators_exist_unique_and_themed() -> None:
    """Each sep-*.svg exists, is unique bytes, and ships a style media query."""
    blobs: list[bytes] = []
    names = [name for name, _key in SEPARATOR_SPECS]
    assert names == list(SECTION_SEPARATORS.values())
    for filename in names:
        path = REPO_ROOT / ".github/assets/img/readme" / filename
        assert path.is_file(), filename
        data = path.read_bytes()
        assert data, filename
        blobs.append(data)
        _assert_separator_contract(data.decode("utf-8"), filename)
    assert len(set(blobs)) == len(blobs)
    tech = (REPO_ROOT / ".github/assets/img/readme/sep-tech.svg").read_text(
        encoding="utf-8"
    )
    assert 'aria-label="My Tech Stack"' in tech


def test_generate_separators_writes_unique_themed_fleet(tmp_path: Path) -> None:
    """generate_separators writes the six unique themed dialect files."""
    written = generate_separators(output_dir=tmp_path)
    assert [path.name for path in written] == [name for name, _key in SEPARATOR_SPECS]
    blobs = [path.read_bytes() for path in written]
    assert all(blobs)
    assert len(set(blobs)) == len(blobs)
    for path in written:
        _assert_separator_contract(path.read_text(encoding="utf-8"), path.name)
    tech = next(path for path in written if path.name == "sep-tech.svg")
    assert 'aria-label="My Tech Stack"' in tech.read_text(encoding="utf-8")


_LIVING_WRAP_RE = re.compile(
    r'<p align="center">\s*'
    r'(?:<a href="[^"]+">\s*<img src="\.github/assets/img/living-[^"]+"'
    r"[^>]*>\s*</a>\s*){6}</p>",
    re.S,
)


def heading_line_re(title: str) -> re.Pattern[str]:
    return re.compile(
        rf"(?m)^(?:## {re.escape(title)}\s*|<!-- ## {re.escape(title)} -->)\s*$"
    )


def assert_visible_or_comment_heading(text: str, title: str) -> None:
    """Accept a visible H2 or the SVG separator plus comment stand-in."""
    visible = re.search(rf"(?m)^## {re.escape(title)}\s*$", text)
    comment = re.search(rf"(?m)^<!-- ## {re.escape(title)} -->\s*$", text)
    assert visible or comment, f"missing {title} heading"
    if comment is not None and visible is None:
        sep = SECTION_SEPARATORS[title]
        assert f".github/assets/img/readme/{sep}" in text, (
            f"comment heading {title} requires {sep}"
        )


def heading_index(text: str, title: str) -> int:
    match = heading_line_re(title).search(text)
    assert match is not None, f"missing heading {title}"
    return match.start()


def after_heading(text: str, title: str) -> str:
    match = heading_line_re(title).search(text)
    assert match is not None, f"missing heading {title}"
    return text[match.end() :]


def slice_between_headings(text: str, start: str, end: str) -> str:
    rest = after_heading(text, start)
    end_match = heading_line_re(end).search(rest)
    assert end_match is not None, f"missing heading {end}"
    return rest[: end_match.start()]


def living_art_wrap(text: str) -> str:
    match = _LIVING_WRAP_RE.search(text)
    assert match is not None, "living-art wrap-flow paragraph missing"
    return match.group(0)


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
    match = compile_section_body_re("My Tech Stack", _order()).search(readme)
    assert match is not None, "My Tech Stack section missing"
    return match.group(0)


def test_living_art_wrap_flow_shows_all_six_gifs() -> None:
    """All six living-art GIFs are inline at width 360 inside one centered wrap."""
    readme = _read_readme()
    assert_visible_or_comment_heading(readme, "Living Art")
    wrap = living_art_wrap(readme)

    assert wrap.count('<p align="center">') == 1
    assert wrap.count("</p>") == 1
    assert wrap.count('width="360"') == 6
    assert wrap.count('width="100%"') == 0
    assert wrap.count('loading="lazy"') == 6

    for style in LIVING_ART_STYLE_KEYS:
        poster = f".github/assets/img/living-{style}.gif"
        film = f".github/assets/img/living-{style}.mp4"
        assert wrap.count(f'src="{poster}"') == 1
        assert wrap.count(f'href="{film}"') == 1


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
    """My Tech Stack opens on the full-stack details; category teasers are gone."""
    readme = _read_readme()
    assert_visible_or_comment_heading(readme, "My Tech Stack")
    tech = _tech_stack_section(readme)
    body = after_heading(tech, "My Tech Stack").lstrip()

    assert body.startswith("<details>")
    assert "<summary><strong>My Tech Stack</strong></summary>" in tech
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
    assert featured.count('width="360"') == 8
    assert featured.count("featured-card-") == 8
    assert featured.count('loading="lazy"') == 8
    assert "listentropy" not in featured
    assert "mdxpad" not in featured
    assert 'alt="Featured project card for ' in featured


def test_readme_section_order_and_managed_markers() -> None:
    """Major sections and injection markers stay ordered for GFM composition."""
    readme = _read_readme()

    for title in _SECTION_TITLES:
        assert_visible_or_comment_heading(readme, title)
    positions = [heading_index(readme, title) for title in _SECTION_TITLES]
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
    living_start = heading_index(readme, "Living Art")
    assert banner_idx < badges_start < featured_start < living_start


def test_waka_and_blog_are_visible_not_details() -> None:
    """WakaTime and blog are open-flow surfaces; only My Tech Stack stays collapsed."""
    readme = _read_readme()
    living = _living_art_section(readme)

    assert "<summary><strong>WakaTime Stats</strong></summary>" not in readme
    assert "<summary><strong>Latest Blog Posts</strong></summary>" not in readme
    assert 'src=".github/assets/img/wakatime.svg"' in readme
    assert "<!--START_SECTION:waka-->" in readme
    assert "<!--END_SECTION:waka-->" in readme
    assert_visible_or_comment_heading(readme, "Latest Blog Posts")
    assert "<!-- README:BLOG_POSTS:START -->" in readme
    assert "metrics-activity.svg" not in readme
    assert "200+" not in readme
    assert "hitscounter.dev/api/hit" in readme
    assert "style=for-the-badge" in readme
    assert "style=flat-square" not in readme

    blog = readme[
        readme.index("<!-- README:BLOG_POSTS:START -->") : readme.index(
            "<!-- README:BLOG_POSTS:END -->"
        )
    ]
    assert re.search(r"blog-(?:posts|[a-z0-9-]+)\.svg", blog)
    assert blog.count("w4w.dev/blog") >= 4
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


def test_generator_groups_waka_with_metrics_and_strips_dump() -> None:
    """WakaTime SVG + markers move into Metrics; the markdown dump is dropped."""
    stale = dedent(
        """\
        ## Metrics

        <p align="center">
        <img src=".github/assets/img/metrics.svg" alt="metrics" width="100%"/>
        </p>

        ## Word Clouds

        stale word clouds

        <p align="center">
        <img src=".github/assets/img/wakatime.svg"
             alt="WakaTime coding activity" width="100%" loading="lazy"/>
        </p>

        <details>
        <summary><strong>WakaTime Stats</strong></summary>

        <!--START_SECTION:waka-->
        **This Week I Spent My Time On**
        <!--END_SECTION:waka-->

        </details>
        """
    )
    generator = ReadmeSectionGenerator(
        settings=ReadmeSectionsSettings(
            featured_repos=[],
            social_links=[],
            section_order=[
                "Featured Projects",
                "Metrics",
                "Living Art",
                "My Tech Stack",
                "Word Clouds",
            ],
        ),
    )
    rendered = generator._rewrite_wakatime_section(stale)
    assert_visible_or_comment_heading(rendered, "Metrics")
    metrics = slice_between_headings(rendered, "Metrics", "Word Clouds")
    word_clouds = after_heading(rendered, "Word Clouds")

    assert "This Week I Spent My Time On" not in rendered
    assert "<summary><strong>WakaTime Stats</strong></summary>" not in rendered
    assert "<details" not in rendered
    assert 'src=".github/assets/img/wakatime.svg"' in metrics
    assert "<!--START_SECTION:waka-->" in metrics
    assert "<!--END_SECTION:waka-->" in metrics
    assert rendered.count('src=".github/assets/img/wakatime.svg"') == 1
    assert 'src=".github/assets/img/wakatime.svg"' not in word_clouds
    assert "## Waka" not in rendered


def test_generator_rewrites_living_art_and_drops_teasers() -> None:
    """Generator rewrites emit wrap-flow Living Art and strip tech teasers."""
    stale = dedent(
        """\
        ## Living Art

        <table><tr><td>stale</td></tr></table>
        <details><summary>hidden</summary>old</details>

        ## My Tech Stack

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
    assert_visible_or_comment_heading(rendered, "Living Art")
    assert_visible_or_comment_heading(rendered, "My Tech Stack")
    living = living_art_wrap(rendered)
    tech = after_heading(rendered, "My Tech Stack")

    assert living.count('src=".github/assets/img/living-') == 6
    assert living.count('width="360"') == 6
    assert "<table" not in living.lower()
    assert "<details" not in living.lower()
    assert living.count('<p align="center">') == 1
    assert 'alt="AI/ML"' not in tech
    assert 'alt="Open Source"' not in tech
    assert tech.lstrip().startswith("<details>")
    assert "<summary><strong>My Tech Stack</strong></summary>" in tech
    assert "View full stack" not in tech
    assert "200+" not in tech
    assert "kept" in tech


def test_fact_no_200_copy_summary_has_no_count_or_blurb() -> None:
    """fact-no-200-copy: tech-stack summary is a bare label with no count."""
    readme = _read_readme()
    tech = _tech_stack_section(readme)
    assert "200+" not in readme
    assert "View full stack" not in readme
    assert "<summary><strong>My Tech Stack</strong></summary>" in tech


def test_fact_tech_details_stack_in_details_waka_with_metrics() -> None:
    """fact-tech-details: shield wall stays in details; Waka sits with metric cards."""
    readme = _read_readme()
    assert_visible_or_comment_heading(readme, "Metrics")
    metrics = slice_between_headings(readme, "Metrics", "Living Art")
    tech = _tech_stack_section(readme)
    assert 'src=".github/assets/img/wakatime.svg"' in metrics
    assert "<details>" in tech
    assert "<summary><strong>My Tech Stack</strong></summary>" in tech
    assert "<!-- SKILLS:START -->" in tech
    assert "wakatime.svg" not in tech
    assert "<!--START_SECTION:waka-->" in metrics


def test_fact_views_komarev_for_the_badge() -> None:
    """fact-views: incrementing komarev chip restyled to for-the-badge."""
    readme = _read_readme()
    assert "hitscounter.dev/api/hit" in readme
    assert "icon=stars" in readme
    assert "style=for-the-badge" in readme
    assert "label=Views" in readme
    assert "views-peek.svg" not in readme
    assert "komarev.com/ghpvc" not in readme
    assert "style=flat-square" not in readme


def test_fact_remove_feed_readme_omits_activity_card() -> None:
    """fact-remove-feed: committed README has no first-party activity widget."""
    assert "metrics-activity.svg" not in _read_readme()


def test_custom_widgets_are_full_width() -> None:
    """First-party metrics and word clouds stack at 100% width."""
    readme = _read_readme()
    for src in (
        "metrics-languages.svg",
        "metrics-habits.svg",
        "metrics-music.svg",
        "wordcloud_typographic_by_topics.svg",
        "wordcloud_typographic_by_languages.svg",
        "wakatime.svg",
    ):
        assert re.search(
            rf'<img src="[^"]*{re.escape(src)}"[^>]*width="100%"',
            readme,
        ), src
    clouds = slice_between_headings(readme, "Word Clouds", "Latest Blog Posts")
    assert "<table" not in clouds.lower()
    tech = slice_between_headings(readme, "My Tech Stack", "Word Clouds")
    assert "wordcloud_typographic" not in tech


def test_blog_cards_are_links_without_extra_caption_row() -> None:
    """Blog cards wrap as links; no second paragraph of title URLs."""
    readme = _read_readme()
    blog = after_heading(readme, "Latest Blog Posts")
    assert "sep-blog.svg" in _read_readme()
    assert_visible_or_comment_heading(readme, "Latest Blog Posts")
    assert blog.count("<a href=") >= 5
    assert re.search(r'<a href="[^"]+"[^>]*>\s*<img ', blog)
    # The old caption row joined titles with " · " outside <img> tags.
    caption_row = re.search(
        r"<p align=\"center\"><a href=\"https://www\.w4w\.dev/blog",
        blog,
    )
    assert caption_row is None
