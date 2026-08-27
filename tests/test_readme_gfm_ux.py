"""GFM UX contracts for the live profile README (full-width Living Art stack).

These tests assert README composition and generator rewrites that keep
Living Art / My Tech Stack aligned with that design. Living Art is a
full-width stack with per-piece <details>; My Tech Stack stays collapsed.
Featured projects remain a wrap-flow of 360 cards.
"""

from __future__ import annotations

import re
from pathlib import Path
from textwrap import dedent

import pytest

from scripts.art.roster import SHIPPED_STYLE_KEYS, shipped_legends
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


# Inverse of the retired six-thumb wrap (one centered <p> of living-* posters).
_FORBIDDEN_LIVING_WRAP_RE = re.compile(
    r'<p align="center">\s*'
    r'(?:<a href="[^"]+">\s*<img src="\.github/assets/img/living-[^"]+"'
    r"[^>]*>\s*</a>\s*){6}</p>",
    re.S,
)
_SPINE_IN_INTRO_RE = re.compile(
    r"\b(repos?|stars?|commits?|followers?|four-signal spine)\b",
    re.I,
)
_FORBIDDEN_HOST_RE = re.compile(
    r"youtube\.com|youtu\.be|cloudinary|vimeo|"
    r"user-images\.githubusercontent\.com|"
    r"github\.com/\S+/assets/|"
    r"github\.com/user-attachments/|"
    r"<iframe\b",
    re.I,
)
_ALLOWED_LIVING_MEDIA_RE = re.compile(
    r"^\.github/assets/img/living-[a-z0-9-]+\.(gif|mp4)$"
)
_SEPARATOR_SRC_RE = re.compile(r"^\.github/assets/img/readme/sep-[a-z]+\.svg$")
_MEDIA_URL_ATTR_RE = re.compile(
    r"""\b(?:src|href|poster)=["']([^"']+)["']""",
    re.I,
)
_DETAILS_RE = re.compile(r"(?is)<details\b.*?</details>")
_TRAILING_SEP_RE = re.compile(
    r'(?:\s*<p align="center">\s*<img src="\.github/assets/img/readme/'
    r'sep-[a-z]+\.svg"[^>]*>\s*</p>\s*)+$',
    re.I,
)


def heading_line_re(title: str) -> re.Pattern[str]:
    return re.compile(
        rf"(?m)^(?:## {re.escape(title)}\s*|<!-- ## {re.escape(title)} -->)\s*$"
    )


def assert_visible_or_comment_heading(text: str, title: str) -> None:
    """Require a visible H2. Comment-only stand-ins are no longer accepted."""
    visible = re.search(rf"(?m)^## {re.escape(title)}\s*$", text)
    comment = re.search(rf"(?m)^<!-- ## {re.escape(title)} -->\s*$", text)
    assert visible is not None, f"missing visible ## {title}"
    assert comment is None, f"comment stand-in remains for {title}"


def heading_index(text: str, title: str) -> int:
    match = heading_line_re(title).search(text)
    assert match is not None, f"missing heading {title}"
    return match.start()


def after_heading(text: str, title: str) -> str:
    match = heading_line_re(title).search(text)
    assert match is not None, f"missing heading {title}"
    return text[match.end() :]


def after_heading_body(text: str, title: str) -> str:
    """Section body after the visible H2 (strips a leftover post-heading sep)."""
    rest = after_heading(text, title).lstrip()
    return re.sub(
        r'^<p align="center"><img src="\.github/assets/img/readme/'
        r'sep-[a-z]+\.svg"[^>]*></p>\s*',
        "",
        rest,
        count=1,
    )


def slice_between_headings(text: str, start: str, end: str) -> str:
    rest = after_heading(text, start)
    end_match = heading_line_re(end).search(rest)
    assert end_match is not None, f"missing heading {end}"
    return rest[: end_match.start()]


def _order() -> tuple[str, ...]:
    try:
        settings = load_config().readme_sections_settings
    except Exception:  # noqa: BLE001 — fall back for isolated unit runs
        settings = ReadmeSectionsSettings()
    return section_order_from_settings(settings)


def _read_readme() -> str:
    return README_PATH.read_text(encoding="utf-8")


def shipped_living_art_count() -> int:
    n = len(SHIPPED_STYLE_KEYS)
    assert 1 <= n <= 6, n
    return n


def living_art_section(text: str) -> str:
    match = compile_section_body_re("Living Art", _order()).search(text)
    assert match is not None, "Living Art section missing"
    return _TRAILING_SEP_RE.sub("", match.group(0)).rstrip() + "\n"


def visible_living_art_and_details(living: str) -> tuple[str, list[str]]:
    blocks = _DETAILS_RE.findall(living)
    visible = _DETAILS_RE.sub("\n", living)
    return visible, blocks


def living_art_intro(living: str) -> str:
    """First unaligned paragraph after the Living Art heading."""
    match = re.search(r"(?s)<p>(.*?)</p>", living)
    assert match is not None, "Living Art intro paragraph missing"
    return match.group(1)


def assert_living_art_not_wrapped(living: str) -> None:
    assert _FORBIDDEN_LIVING_WRAP_RE.search(living) is None
    assert 'width="360"' not in living
    lowered = living.lower()
    assert "<table" not in lowered
    assert "</table>" not in lowered
    assert "display: grid" not in lowered
    assert "grid-template" not in lowered
    assert "<br/>" not in lowered
    assert "<sub>" not in lowered


def assert_art_outside_details(living: str) -> None:
    _visible, blocks = visible_living_art_and_details(living)
    n = shipped_living_art_count()
    assert len(blocks) == n
    assert living.count("<details") == n
    assert living.count("</details>") == n
    assert re.search(r"<details\b[^>]*\bopen\b", living, flags=re.I) is None
    for block in blocks:
        assert "living-" not in block
        assert "<video" not in block.lower()
        assert re.search(r"<img\b", block, flags=re.I) is None


def assert_full_width_media(living: str) -> None:
    """One piece per row with a 70% display gutter (not a 360 wrap)."""
    visible, _blocks = visible_living_art_and_details(living)
    assert visible.count('width="70%"') >= shipped_living_art_count()
    for style in SHIPPED_STYLE_KEYS:
        gif = f".github/assets/img/living-{style}.gif"
        mp4 = f".github/assets/img/living-{style}.mp4"
        video_hit = re.search(
            rf'<video\b[^>]*src="{re.escape(mp4)}"[^>]*>',
            visible,
        )
        img_hit = re.search(
            rf'<img\b[^>]*src="{re.escape(gif)}"[^>]*>',
            visible,
        )
        if video_hit is not None:
            assert 'width="70%"' in video_hit.group(0)
        if img_hit is not None:
            assert 'width="70%"' in img_hit.group(0)
            assert 'loading="lazy"' in img_hit.group(0)
        assert video_hit is not None or img_hit is not None, style


def assert_legal_media_forms(living: str) -> None:
    visible, _blocks = visible_living_art_and_details(living)
    for style in SHIPPED_STYLE_KEYS:
        gif = f".github/assets/img/living-{style}.gif"
        mp4 = f".github/assets/img/living-{style}.mp4"
        has_video = (
            re.search(rf'<video\b[^>]*\bsrc="{re.escape(mp4)}"', visible) is not None
        )
        has_gif = f'src="{gif}"' in visible
        has_href = f'href="{mp4}"' in visible
        assert has_video or (has_gif and has_href), style


def assert_living_art_hosts_allowed(living: str) -> None:
    assert "<iframe" not in living.lower()
    assert _FORBIDDEN_HOST_RE.search(living) is None
    for url in _MEDIA_URL_ATTR_RE.findall(living):
        if _SEPARATOR_SRC_RE.fullmatch(url):
            continue
        assert _ALLOWED_LIVING_MEDIA_RE.fullmatch(url), url


def assert_living_art_intro_has_no_spine(living: str) -> None:
    intro = living_art_intro(living)
    lowered = intro.lower()
    assert "daily timelapses" in lowered
    assert "visual world" in lowered
    assert _SPINE_IN_INTRO_RE.search(intro) is None


def assert_living_art_dropdown_copy(living: str) -> None:
    _visible, blocks = visible_living_art_and_details(living)
    legends = dict(shipped_legends())
    assert len(blocks) == len(SHIPPED_STYLE_KEYS)
    titles: list[str] = []
    for block in blocks:
        summary = re.search(
            r"<summary>\s*<strong>(.*?)</strong>\s*</summary>",
            block,
            flags=re.S,
        )
        assert summary is not None, block[:200]
        titles.append(summary.group(1))
    assert titles == [legends[key].title for key in SHIPPED_STYLE_KEYS]
    assert "how to read" not in living.lower()
    for style, block in zip(SHIPPED_STYLE_KEYS, blocks, strict=True):
        legend = legends[style]
        assert legend.metaphor in block
        assert legend.mapping.repos in block
        assert legend.mapping.stars in block
        assert legend.mapping.commits in block
        assert legend.mapping.followers in block
        assert "**Repos:**" in block
        assert "**Stars:**" in block
        assert "**Commits:**" in block
        assert "**Followers:**" in block


def assert_living_art_stack_layout(living: str) -> None:
    assert_living_art_not_wrapped(living)
    assert_art_outside_details(living)
    assert_full_width_media(living)
    assert_legal_media_forms(living)


def _synthetic_living_art_section(*, form: str) -> str:
    pieces = [
        "<!-- ## Living Art -->",
        (
            "<p>These are daily timelapses of this GitHub account from "
            "creation to now, each a different visual world.</p>"
        ),
    ]
    for style, legend in shipped_legends():
        gif = f".github/assets/img/living-{style}.gif"
        mp4 = f".github/assets/img/living-{style}.mp4"
        if form == "video":
            media = f'<p align="center">\n<video src="{mp4}" width="70%"></video>\n</p>'
        elif form == "gif-href":
            media = (
                f'<p align="center">\n'
                f'<a href="{mp4}">'
                f'<img src="{gif}" alt="{legend.title}" width="70%" '
                f'loading="lazy"/></a>\n'
                "</p>"
            )
        elif form == "both":
            media = (
                f'<p align="center">\n'
                f'<video src="{mp4}" width="70%" poster="{gif}">\n'
                f'<a href="{mp4}">'
                f'<img src="{gif}" alt="{legend.title}" width="70%" '
                f'loading="lazy"/></a>\n'
                "</video>\n"
                "</p>"
            )
        else:
            raise ValueError(f"unknown living-art media form {form!r}")
        details = (
            f"<details>\n<summary><strong>{legend.title}</strong></summary>\n\n"
            f"{legend.metaphor}\n\n"
            f"- **Repos:** {legend.mapping.repos}\n"
            f"- **Stars:** {legend.mapping.stars}\n"
            f"- **Commits:** {legend.mapping.commits}\n"
            f"- **Followers:** {legend.mapping.followers}\n\n"
            "</details>"
        )
        pieces.extend(["", media, details])
    return "\n".join(pieces)


def _featured_block(readme: str) -> str:
    match = _FEATURED_RE.search(readme)
    assert match is not None, "Featured Projects managed markers missing"
    return match.group(0)


def _tech_stack_section(readme: str) -> str:
    match = compile_section_body_re("My Tech Stack", _order()).search(readme)
    assert match is not None, "My Tech Stack section missing"
    return match.group(0)


def test_living_art_closes_with_separator_before_tech_stack() -> None:
    """Last timelapse (ferrofluid) is followed by a living-art rule, then H2."""
    readme = _read_readme()
    match = compile_section_body_re("Living Art", _order()).search(readme)
    assert match is not None
    living = match.group(0)
    assert living.count("sep-living.svg") == 1
    ferro = living.rfind("living-ferrofluid.gif")
    closer = living.rfind("sep-living.svg")
    assert ferro != -1
    assert closer > ferro
    tech_heading = heading_index(readme, "My Tech Stack")
    living_end = match.end()
    assert living_end <= tech_heading
    closer_abs = match.start() + closer
    assert closer_abs < tech_heading
    opening = re.search(
        r'(?m)^<p align="center"><img src="\.github/assets/img/readme/'
        r'sep-living\.svg" alt="" width="100%" loading="lazy"/></p>\n+'
        r"## Living Art\s*$",
        readme,
    )
    assert opening is not None
    assert opening.start() < match.start()
    assert not re.search(r"(?m)^---$", living[ferro:closer])


def test_living_art_thematic_breaks_between_pieces() -> None:
    """Standalone --- rules sit between shipped pieces, not after ferrofluid."""
    readme = _read_readme()
    match = compile_section_body_re("Living Art", _order()).search(readme)
    assert match is not None
    living = match.group(0)
    rules = re.findall(r"(?m)^---$", living)
    assert len(rules) == len(SHIPPED_STYLE_KEYS) - 1
    ferro = living.rfind("living-ferrofluid.gif")
    closer = living.rfind("sep-living.svg")
    assert ferro != -1
    assert closer > ferro
    assert not re.search(r"(?m)^---$", living[ferro:closer])


def test_living_art_full_width_stack_shows_shipped_media() -> None:
    """Shipped living-art media is an inset 70% stack, one piece per row."""
    readme = _read_readme()
    assert_visible_or_comment_heading(readme, "Living Art")
    living = living_art_section(readme)
    n = shipped_living_art_count()
    visible, _blocks = visible_living_art_and_details(living)
    lazy = len(
        re.findall(
            r'<img src="\.github/assets/img/living-[^"]+"[^>]*loading="lazy"',
            visible,
        )
    )

    assert_living_art_stack_layout(living)
    assert living.count('width="70%"') >= n
    assert living.count('width="360"') == 0
    assert visible.count('<p align="center">') >= n
    assert lazy == n

    for style in SHIPPED_STYLE_KEYS:
        gif = f".github/assets/img/living-{style}.gif"
        mp4 = f".github/assets/img/living-{style}.mp4"
        assert gif in visible or f'src="{mp4}"' in visible
        assert f'src="{mp4}"' in visible or f'href="{mp4}"' in visible


def test_living_art_has_no_table_or_css_grid_and_one_details_per_piece() -> None:
    """Full-width Living Art has no table/grid and one details per shipped key."""
    living = living_art_section(_read_readme())
    assert_living_art_not_wrapped(living)
    assert_art_outside_details(living)


def test_tech_stack_has_no_teaser_shields() -> None:
    """My Tech Stack opens on the full-stack details; category teasers are gone."""
    readme = _read_readme()
    assert_visible_or_comment_heading(readme, "My Tech Stack")
    tech = _tech_stack_section(readme)
    body = after_heading_body(tech, "My Tech Stack").lstrip()

    assert body.startswith("<details>")
    assert "<summary>Technologies</summary>" in tech
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
    assert featured.count('width="360"') == 18
    assert featured.count('width="280"') == 0
    assert featured.count("featured-card-") == 18
    assert featured.count('loading="lazy"') == 18
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


def test_section_headings_are_visible_h2_with_empty_alt_rules() -> None:
    """Each managed section uses a visible H2; the SVG rule sits immediately above."""
    readme = _read_readme()
    for title, filename in SECTION_SEPARATORS.items():
        assert_visible_or_comment_heading(readme, title)
        match = re.search(
            rf'(?m)^<p align="center"><img src="\.github/assets/img/readme/'
            rf'{re.escape(filename)}" alt="" width="100%" loading="lazy"/></p>'
            rf"\n+## {re.escape(title)}\s*$",
            readme,
        )
        assert match is not None, title
        assert f"<!-- ## {title} -->" not in readme


def test_readme_omits_lowlighter_metrics_cards() -> None:
    """Production README ships first-party metrics only — no lowlighter pair."""
    readme = _read_readme()
    assert ".github/assets/img/metrics.svg" not in readme
    assert ".github/assets/img/metrics.additional.svg" not in readme
    assert ".github/assets/img/metrics.extra.svg" not in readme
    metrics = slice_between_headings(readme, "Metrics", "Living Art")
    assert "<table" not in metrics.lower()
    assert 'width="50%"' not in metrics
    assert ".github/assets/img/metrics-languages.svg" in metrics
    assert ".github/assets/img/metrics-habits.svg" in metrics
    assert 'src=".github/assets/img/wakatime.svg"' in metrics


def test_waka_and_blog_are_visible_not_details() -> None:
    """WakaTime and blog stay open-flow; Living Art details do not wrap the media."""
    readme = _read_readme()
    living = living_art_section(readme)

    assert "<summary><strong>WakaTime Stats</strong></summary>" not in readme
    assert "<summary><strong>Latest Blog Posts</strong></summary>" not in readme
    assert 'src=".github/assets/img/wakatime.svg"' in readme
    assert "<!--START_SECTION:waka-->" in readme
    assert "<!--END_SECTION:waka-->" in readme
    assert_visible_or_comment_heading(readme, "Latest Blog Posts")
    assert "<!-- README:BLOG_POSTS:START -->" in readme
    assert "metrics-activity.svg" not in readme
    assert "200+" not in readme
    assert "hitscounter.dev" in readme
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

    # GIF/video must not be nested inside any details block (tech or living).
    for match in _DETAILS_RE.finditer(readme):
        block = match.group(0)
        assert "living-" not in block
        assert "## Living Art" not in block
        assert "wakatime.svg" not in block
        assert "README:BLOG_POSTS" not in block

    assert living.count("<details") == shipped_living_art_count()


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
    """Generator rewrites emit the full-width Living Art stack and strip teasers."""
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
    raw_living = compile_section_body_re("Living Art", _order()).search(rendered)
    assert raw_living is not None
    assert raw_living.group(0).count("sep-living.svg") == 1
    assert raw_living.group(0).rfind("living-ferrofluid.gif") < raw_living.group(
        0
    ).rfind("sep-living.svg")
    assert re.search(
        r'(?m)^<p align="center"><img src="\.github/assets/img/readme/'
        r'sep-living\.svg" alt="" width="100%" loading="lazy"/></p>\n+'
        r"## Living Art\s*$",
        rendered,
    )
    living_body = raw_living.group(0)
    assert len(re.findall(r"(?m)^---$", living_body)) == len(SHIPPED_STYLE_KEYS) - 1
    ferro = living_body.rfind("living-ferrofluid.gif")
    closer = living_body.rfind("sep-living.svg")
    assert not re.search(r"(?m)^---$", living_body[ferro:closer])
    living = living_art_section(rendered)
    tech = after_heading(rendered, "My Tech Stack")

    assert "stale" not in living
    assert "hidden" not in living
    assert_living_art_stack_layout(living)
    assert_living_art_intro_has_no_spine(living)
    assert_living_art_dropdown_copy(living)
    assert_living_art_hosts_allowed(living)
    assert 'alt="AI/ML"' not in tech
    assert 'alt="Open Source"' not in tech
    assert (
        after_heading_body(rendered, "My Tech Stack").lstrip().startswith("<details>")
    )
    assert "<summary>Technologies</summary>" in tech
    assert "View full stack" not in tech
    assert "200+" not in tech
    assert "kept" in tech


def test_fact_no_200_copy_summary_has_no_count_or_blurb() -> None:
    """fact-no-200-copy: tech-stack summary is a bare label with no count."""
    readme = _read_readme()
    tech = _tech_stack_section(readme)
    assert "200+" not in readme
    assert "View full stack" not in readme
    assert "<summary>Technologies</summary>" in tech


def test_fact_tech_details_stack_in_details_waka_with_metrics() -> None:
    """fact-tech-details: shield wall stays in details; Waka sits with metric cards."""
    readme = _read_readme()
    assert_visible_or_comment_heading(readme, "Metrics")
    metrics = slice_between_headings(readme, "Metrics", "Living Art")
    tech = _tech_stack_section(readme)
    assert 'src=".github/assets/img/wakatime.svg"' in metrics
    assert "<details>" in tech
    assert "<summary>Technologies</summary>" in tech
    assert "<!-- SKILLS:START -->" in tech
    assert "wakatime.svg" not in tech
    assert "<!--START_SECTION:waka-->" in metrics


def test_fact_views_komarev_for_the_badge() -> None:
    """fact-views: incrementing komarev chip restyled to for-the-badge."""
    readme = _read_readme()
    assert "custom-icon-badges.demolab.com/badge/dynamic/json" in readme
    assert "logo=telescope" in readme
    assert "hitscounter.dev" in readme
    assert "style=for-the-badge" in readme
    assert "label=views" in readme
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


def test_living_art_intro_does_not_list_the_four_signal_spine() -> None:
    """Intro is the clock sentence; repos/stars/commits/followers stay in dropdowns."""
    living = living_art_section(_read_readme())
    assert_living_art_intro_has_no_spine(living)


def test_living_art_dropdowns_match_shipped_legends() -> None:
    """One collapsed details per shipped piece, with title, metaphor, and mapping."""
    living = living_art_section(_read_readme())
    assert_living_art_dropdown_copy(living)
    assert "faq" not in living.lower()


def test_living_art_media_hosts_are_in_repo_only() -> None:
    """Living Art src/href/poster stay on relative in-repo gif/mp4 stems."""
    living = living_art_section(_read_readme())
    assert_living_art_hosts_allowed(living)


def test_living_art_accepts_native_video_or_gif_href_mp4() -> None:
    """Native <video src=mp4> and visible GIF+href MP4 are both legal forms."""
    for form in ("video", "gif-href", "both"):
        living = _synthetic_living_art_section(form=form)
        assert_legal_media_forms(living)
        assert_full_width_media(living)
        assert_art_outside_details(living)
        assert_living_art_hosts_allowed(living)
        assert_living_art_not_wrapped(living)


@pytest.mark.parametrize(
    ("needle", "poison"),
    [
        (
            ".github/assets/img/living-inkgarden.mp4",
            "https://www.youtube.com/embed/x",
        ),
        (
            ".github/assets/img/living-inkgarden.mp4",
            "https://youtu.be/x",
        ),
        (
            ".github/assets/img/living-topo.mp4",
            "https://res.cloudinary.com/demo/video/upload/dog.mp4",
        ),
        (
            ".github/assets/img/living-genetic.mp4",
            "https://vimeo.com/123",
        ),
        (
            ".github/assets/img/living-physarum.gif",
            "https://user-images.githubusercontent.com/1/x.gif",
        ),
        (
            ".github/assets/img/living-lenia.gif",
            "https://github.com/wyattowalsh/assets/123",
        ),
        (
            ".github/assets/img/living-ferrofluid.gif",
            "https://github.com/user-attachments/assets/abc",
        ),
    ],
)
def test_living_art_external_hosts_fail(needle: str, poison: str) -> None:
    """YouTube, Cloudinary, and other external hosts fail the living-art allowlist."""
    legal = _synthetic_living_art_section(form="both")
    assert_living_art_hosts_allowed(legal)
    poisoned = legal.replace(needle, poison, 1)
    with pytest.raises(AssertionError):
        assert_living_art_hosts_allowed(poisoned)


def test_living_art_iframe_fails_host_allowlist() -> None:
    """Iframes are not a legal living-art media host."""
    legal = _synthetic_living_art_section(form="gif-href")
    poisoned = legal + '\n<iframe src="https://youtube.com/embed/x"></iframe>\n'
    with pytest.raises(AssertionError):
        assert_living_art_hosts_allowed(poisoned)


def test_living_art_rejects_media_hidden_in_details() -> None:
    """GIF/video nested in details fails visible-art even with in-repo paths."""
    pieces = [
        "<!-- ## Living Art -->",
        (
            "<p>These are daily timelapses of this GitHub account from "
            "creation to now, each a different visual world.</p>"
        ),
    ]
    for style, legend in shipped_legends():
        gif = f".github/assets/img/living-{style}.gif"
        pieces.append(
            f"<details>\n<summary><strong>{legend.title}</strong></summary>\n"
            f'<img src="{gif}" alt="{legend.title}" width="70%" '
            f'loading="lazy"/>\n'
            f"{legend.metaphor}\n"
            "</details>"
        )
    hidden = "\n".join(pieces)
    with pytest.raises(AssertionError):
        assert_art_outside_details(hidden)
