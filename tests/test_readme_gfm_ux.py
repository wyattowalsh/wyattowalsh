"""GitHub profile README, generated sections, and linked living art gallery."""

from __future__ import annotations

import re
from pathlib import Path
from textwrap import dedent

import pytest
from bs4 import BeautifulSoup, Tag
from markdown_it import MarkdownIt

from scripts.art.roster import shipped_legends
from scripts.config import ReadmeSectionsSettings, load_config
from scripts.readme_sections import (
    TECH_STACK_H2_SUMMARY,
    TECH_STACK_START,
    ReadmeSectionGenerator,
    compile_section_body_re,
    section_order_from_settings,
)
from scripts.readme_separators import SEPARATOR_SPECS, generate_separators

REPO_ROOT = Path(__file__).resolve().parents[1]
README_PATH = REPO_ROOT / "README.md"
GALLERY_PATH = REPO_ROOT / "LIVING_ART.md"
GALLERY_LINK = "[living art gallery](LIVING_ART.md)"

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


def rendered(markup: str) -> BeautifulSoup:
    html = MarkdownIt("commonmark", {"html": True}).enable("table").render(markup)
    return BeautifulSoup(html, "html.parser")


def required_tag(parent: Tag, selector: str) -> Tag:
    tag = parent.select_one(selector)
    assert tag is not None, f"Missing element matching {selector}"
    return tag


def heading_line_re(title: str) -> re.Pattern[str]:
    return re.compile(
        rf"(?m)^(?:## {re.escape(title)}\s*|<!-- ## {re.escape(title)} -->)\s*$"
    )


def assert_tech_stack_dropdown_is_h2(text: str) -> None:
    """My Tech Stack H2 lives in the details summary, not above the dropdown."""
    assert TECH_STACK_START in text
    assert TECH_STACK_H2_SUMMARY in text
    assert text.count("## My Tech Stack") == 1
    assert "<summary>Technologies</summary>" not in text
    heading = heading_index(text, "My Tech Stack")
    details = text.rfind("<details>", 0, heading)
    assert details != -1
    assert text.rfind("</details>", details, heading) == -1
    assert text.index(TECH_STACK_START) < heading


def assert_word_clouds_have_h3s_and_frequency_tables(clouds: str) -> None:
    """Topics/Languages H3s plus one markdown frequency-table details."""
    assert "### Topics" in clouds
    assert "### Languages" in clouds
    assert "<summary>Frequency tables</summary>" in clouds
    assert "| Topic |" in clouds
    assert "| Language |" in clouds
    assert "<table" not in clouds.lower()
    assert "</table>" not in clouds.lower()


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


def assert_profile_gallery_link(readme: str) -> None:
    intro = readme.split("## Featured Projects", 1)[0]
    links = rendered(intro).select('a[href="LIVING_ART.md"]')
    assert (
        len(links) == 1
        and links[0].get_text(strip=True).lower() == "living art gallery"
    )
    assert links[0].find_parent("details") is None
    assert len(rendered(readme).select('a[href="LIVING_ART.md"]')) == 1
    assert re.search(r"(?m)^I\b", intro)
    assert heading_line_re("Living Art").search(readme) is None
    assert not re.search(
        r"living-(?:stills/)?[^\s\"]+\.(gif|mp4|jpg)|sep-living\.svg", readme
    )


def assert_gallery_contents(gallery: str) -> None:
    intro, *pieces = re.split(r"(?m)^## (.+)$", gallery)
    legends = shipped_legends()
    assert pieces[::2] == [legend.title for _, legend in legends]
    doc = rendered(gallery)
    assert doc.select("video, iframe, object, embed, [poster]") == []
    assert len(doc.select("source")) == len(legends)
    assert len(doc.select("img")) == len(legends)
    assert len(doc.select('a[href="README.md#wyatt-walsh"]')) == 2
    assert [a["href"] for a in rendered(intro).select('a[href^="#"]')] == [
        "#" + legend.title.lower().replace(" ", "-") for _, legend in legends
    ]
    for body, (style, legend) in zip(pieces[1::2], legends, strict=True):
        section = rendered(body)
        previews = section.select("details")
        assert len(previews) == 2
        preview, reading = previews
        assert preview.has_attr("open") and not reading.has_attr("open")
        assert required_tag(preview, "summary").get_text(strip=True) == (
            f"Show or hide the {legend.title} preview"
        )
        assert reading.select("img, video, a, source") == []
        assert legend.metaphor in section.get_text()
        assert [
            li.get_text(strip=True, separator=" ") for li in reading.select("li")
        ] == [f"{k.title()}: {v}" for k, v in legend.mapping.model_dump().items()]
        prefix = ".github/assets/img/"
        gif = f"{prefix}living-{style}.gif"
        film = f"{prefix}living-{style}.mp4"
        still = f"{prefix}living-stills/living-{style}.jpg"
        picture = preview.select_one(f'a[href="{film}"] > picture')
        assert picture is not None
        source = picture.select_one("source")
        assert source is not None and source.get("srcset") == gif
        assert source.get("media") == "(prefers-reduced-motion: no-preference)"
        image = picture.select_one("img")
        assert image is not None and image.get("src") == still
        assert (
            str(image.get("alt", ""))
            .strip()
            .endswith(f"Open {legend.title} as an MP4.")
        )
        assert image.get("width") == image.get("height") == "400"
        assert [
            a["href"] for a in section.select("a") if a.find_parent("details") is None
        ][:2] == [film, gif]
        for path in (gif, film, still):
            assert (GALLERY_PATH.parent / path).stat().st_size > 0


def assert_project_finder(markup: str, repos: list[str]) -> None:
    doc = rendered(markup)
    finders = doc.select("details")
    assert len(finders) == 1
    finder = finders[0]
    assert not finder.has_attr("open")
    assert (
        required_tag(finder, "summary").get_text(strip=True)
        == "Find a project by topic"
    )
    assert len(finder.select("li")) == 5
    assert finder.select("img") == []
    expected = [f"https://github.com/{repo}" for repo in repos]
    assert sorted(a["href"] for a in finder.select("a")) == sorted(expected)
    assert [a["href"] for a in doc.select("a:has(img)")] == expected


def _featured_block(readme: str) -> str:
    match = _FEATURED_RE.search(readme)
    assert match is not None, "Featured Projects managed markers missing"
    return match.group(0)


def _tech_stack_section(readme: str) -> str:
    """Span from TECH_STACK_START (or the H2) through the next neighbor H2.

    ``compile_section_body_re("My Tech Stack")`` stops at the in-summary H2
    because the neighbor catch-all is ``^##(?!#)``. Skip that heading.
    """
    start_idx = readme.find(TECH_STACK_START)
    if start_idx == -1:
        start_idx = heading_index(readme, "My Tech Stack")
    rest = readme[start_idx:]
    neighbor = re.search(r"(?m)^## (?!My Tech Stack).+$", rest)
    assert neighbor is not None, "My Tech Stack neighbor missing"
    return rest[: neighbor.start()]


def test_profile_gallery_link_and_gallery_contents() -> None:
    assert_profile_gallery_link(_read_readme())
    assert_gallery_contents(GALLERY_PATH.read_text(encoding="utf-8"))


def test_tech_stack_has_no_teaser_shields() -> None:
    """My Tech Stack opens on the full-stack details; category teasers are gone."""
    readme = _read_readme()
    assert_visible_or_comment_heading(readme, "My Tech Stack")
    tech = _tech_stack_section(readme)
    assert_tech_stack_dropdown_is_h2(readme)
    body = after_heading_body(readme, "My Tech Stack").lstrip()

    assert body.startswith("</summary>")
    assert "View full stack" not in tech
    assert "200+" not in tech
    assert "<!-- SKILLS:START -->" in tech
    assert "<!-- SKILLS:END -->" in tech

    for alt in _TEASER_ALTS:
        assert f'alt="{alt}"' not in tech


def test_featured_projects_use_visible_profile_cards_and_a_topic_finder() -> None:
    settings = load_config().readme_sections_settings
    assert settings is not None and settings.profile_cards is not None
    repos = [p.full_name for p in settings.profile_cards.projects]
    assert len(repos) == len(set(repos)) == 24
    assert set(repos) == {r.full_name for r in settings.featured_repos} | {
        "wyattowalsh/" + name
        for name in (
            "hue-board",
            "awesome-iina",
            "agentic-cad",
            "NYC-recs",
            "iina-plugin-starter",
            "soundlab",
        )
    }
    featured = _featured_block(_read_readme())
    assert_project_finder(featured, repos)
    doc = rendered(featured)
    assert doc.select("table") == []
    for image, repo in zip(doc.select("a > img"), repos, strict=True):
        name = repo.split("/")[1]
        src = f".github/assets/img/readme-profile/project-{name}.svg"
        assert image.get("src") == src and (REPO_ROOT / src).is_file()
        assert image.get("width") == "274" and image.get("height") == "112"
        assert image.find_parent("details") is None
        assert name in str(image.get("alt", ""))


def test_readme_section_order_and_managed_markers() -> None:
    readme = _read_readme()
    titles = (*_SECTION_TITLES, "Latest Blog Posts", "Connect")
    for title in titles:
        assert_visible_or_comment_heading(readme, title)
    positions = [heading_index(readme, title) for title in titles]
    assert positions == sorted(positions)
    for block in (
        "FEATURED_PROJECTS",
        "METRICS",
        "TECH_STACK",
        "FREQUENCIES",
        "BLOG_POSTS",
        "TOP_BADGES",
    ):
        start, end = (f"<!-- README:{block}:{side} -->" for side in ("START", "END"))
        assert readme.count(start) == readme.count(end) == 1
        assert readme.index(start) < readme.index(end)
    intro = rendered(readme.split("## Featured Projects", 1)[0])
    assert required_tag(intro, "h1").get_text(strip=True) == "Wyatt Walsh"
    assert [
        (a.get_text(strip=True), a["href"]) for a in intro.select('a[href^="#"]')
    ] == [
        ("Projects", "#featured-projects"),
        ("Metrics", "#metrics"),
        ("Writing", "#latest-blog-posts"),
        ("Connect", "#connect"),
    ]
    assert readme.index("## Connect") < readme.index("<!-- README:TOP_BADGES:START -->")


def test_section_headings_are_visible_and_identifiable_without_images() -> None:
    readme = _read_readme()
    doc = rendered(readme)
    headings = [h.get_text(strip=True) for h in doc.select("h2")]
    assert headings == [*_SECTION_TITLES, "Latest Blog Posts", "Connect"]
    assert_tech_stack_dropdown_is_h2(readme)
    assert not doc.select('img[src*="/sep-"]')


def assert_metric_panels(readme: str) -> None:
    metrics = rendered(
        readme.split("<!-- README:METRICS:START -->", 1)[1].split(
            "<!-- README:METRICS:END -->", 1
        )[0]
    )
    names = ["metrics-languages", "metrics-habits", "wakatime"]
    if (REPO_ROOT / ".github/assets/img/metrics-music.svg").is_file():
        names.append("metrics-music")
    images = metrics.select("img")
    details = metrics.select("details")
    assert len(images) == len(details) == len(names)
    for name, image, detail in zip(names, images, details, strict=True):
        src = f".github/assets/img/summary-{name}.svg"
        assert image.get("src") == src and (REPO_ROOT / src).is_file()
        assert image.find_parent("details") is None and image.get("width") == "360"
        assert len(str(image.get("alt", "")).strip()) > 20
        assert not detail.has_attr("open") and detail.select("table")
        full = detail.select_one(f'a[href=".github/assets/img/{name}.svg"]')
        assert full is not None and full.get_text(strip=True)


def test_readme_uses_first_party_metric_summaries_and_full_chart_links() -> None:
    readme = _read_readme()
    assert_metric_panels(readme)
    assert "metrics.additional.svg" not in readme and "metrics.extra.svg" not in readme
    assert 'src=".github/assets/img/metrics.svg"' not in readme


def assert_blog_cards(blog: str) -> None:
    doc = rendered(blog)
    cards = doc.select("a:has(img)")
    assert len(cards) == 5
    disclosures = doc.select("details")
    assert len(disclosures) == 1 and not disclosures[0].has_attr("open")
    assert (
        required_tag(disclosures[0], "summary").get_text(strip=True)
        == "Read the post titles as text"
    )
    text_links = disclosures[0].select("a")
    assert len(text_links) == len(cards)
    for card, link in zip(cards, text_links, strict=True):
        assert card.find_parent("details") is None
        assert card["href"] == link["href"]
        assert str(card["href"]).startswith("https://www.w4w.dev/blog/posts/")
        image = required_tag(card, "img")
        src = str(image["src"])
        assert src.startswith(".github/assets/img/readme-profile/blog-")
        assert (REPO_ROOT / src).is_file()
        assert image.get("width") == "360" and image.get("height") == "152"
        title, date, hook = str(image["alt"]).split(" · ", 2)
        assert title == link.get_text(strip=True)
        assert link.parent is not None and date in link.parent.get_text()
        assert hook.strip()
    assert doc.select_one('a[href="https://w4w.dev/feed.xml"]') is not None


def test_profile_shows_articles_and_exposes_full_titles_as_text() -> None:
    assert_blog_cards(
        slice_between_headings(_read_readme(), "Latest Blog Posts", "Connect")
    )


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
    # Rewrite-only: WakaTime <details> are stripped and Word Clouds are not
    # regenerated, so this fixture still has no <details> at all.
    assert "<details" not in rendered
    assert 'src=".github/assets/img/wakatime.svg"' in metrics
    assert "<!--START_SECTION:waka-->" in metrics
    assert "<!--END_SECTION:waka-->" in metrics
    assert rendered.count('src=".github/assets/img/wakatime.svg"') == 1
    assert 'src=".github/assets/img/wakatime.svg"' not in word_clouds
    assert "## Waka" not in rendered


def test_fact_no_200_copy_summary_has_no_count_or_blurb() -> None:
    """fact-no-200-copy: tech-stack summary is a bare label with no count."""
    readme = _read_readme()
    tech = _tech_stack_section(readme)
    assert "200+" not in readme
    assert "View full stack" not in readme
    assert "200+" not in tech
    assert "View full stack" not in tech
    assert_tech_stack_dropdown_is_h2(readme)


def test_fact_tech_details_stack_in_details_waka_with_metrics() -> None:
    """fact-tech-details: 151 shields are accessible through category disclosures."""
    readme = _read_readme()
    assert_tech_stack_dropdown_is_h2(readme)
    tech = rendered(_tech_stack_section(readme))
    groups = tech.select("details details")
    assert groups and all(not group.has_attr("open") for group in groups)
    shields = tech.select('img[src^="https://img.shields.io/badge/"]')
    assert len(shields) == 151
    for img in shields:
        assert len(img.find_parents("details")) == 2
        assert img.find_parent("a") is not None
    metrics = slice_between_headings(readme, "Metrics", "My Tech Stack")
    assert (
        "<!--START_SECTION:waka-->" in metrics and "<!--END_SECTION:waka-->" in metrics
    )
    assert 'src=".github/assets/img/summary-wakatime.svg"' in metrics


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


def test_profile_links_full_word_clouds_and_two_frequency_tables() -> None:
    doc = rendered(
        slice_between_headings(_read_readme(), "Word Clouds", "Latest Blog Posts")
    )
    for kind, img in zip(("topics", "languages"), doc.select("img"), strict=True):
        src = f".github/assets/img/wordcloud_typographic_by_{kind}.svg"
        anchor = img.find_parent("a")
        assert img["src"] == src and anchor is not None and anchor["href"] == src
        assert kind in str(img["alt"]).lower() and img.get("width") == "400"
        assert img.find_parent("details") is None and (REPO_ROOT / src).is_file()
    tables = doc.select("details table")
    assert len(tables) == 2
    for table, key in zip(tables, ("Topic", "Language"), strict=True):
        assert required_tag(table, "th").get_text(strip=True) == key
        assert 1 <= len(table.select("tbody tr")) <= 12


def test_contact_actions_precede_the_expandable_full_size_qr() -> None:
    doc = rendered(after_heading(_read_readme(), "Connect"))
    actions = [
        "https://w4w.dev",
        "https://linkedin.com/in/wyattowalsh",
        "https://www.kaggle.com/wyattowalsh",
        "https://x.com/wyattowalsh",
    ]
    assert [a["href"] for a in doc.select("a")][:4] == actions
    assert all(a.find_parent("details") is None for a in doc.select("a")[:4])
    disclosure = doc.select_one("details")
    assert disclosure is not None and not disclosure.has_attr("open")
    qr = disclosure.select_one('a[href=".github/assets/img/qr.png"] > img')
    assert qr is not None and qr.get("src") == ".github/assets/img/qr.png"
    assert qr.get("width") == "240" and str(qr.get("alt", "")).strip()
    assert doc.select_one('a[href="#wyatt-walsh"]') is not None
    assert (
        doc.select_one('a[href$="actions/workflows/profile-updater.yml"] > img')
        is not None
    )


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
    gallery = GALLERY_PATH.read_text(encoding="utf-8")
    assert needle in gallery
    with pytest.raises(AssertionError):
        assert_gallery_contents(gallery.replace(needle, poison, 1))


@pytest.mark.parametrize(
    ("original", "replacement"),
    [
        ("living-inkgarden.mp4", "living-topo.mp4"),
        ("## Ink Garden", "## Lenia"),
        ("<details>", "<details open>"),
        ("Open Ink Garden as an MP4.", "Unlabelled preview."),
        ("README.md", "index.html"),
        ("(prefers-reduced-motion: no-preference)", "(prefers-reduced-motion: reduce)"),
        ("living-stills/living-inkgarden.jpg", "living-inkgarden.gif"),
        ("- **Stars:** bloom", "- **Stars:** glints"),
        (
            "Six timelapses trace",
            '<iframe src="https://example.org/video"></iframe>\n\nSix timelapses trace',
        ),
    ],
)
def test_gallery_rejects_broken_presentation(original: str, replacement: str) -> None:
    gallery = GALLERY_PATH.read_text(encoding="utf-8")
    assert original in gallery
    with pytest.raises(AssertionError):
        assert_gallery_contents(gallery.replace(original, replacement, 1))


def test_gallery_rejects_media_hidden_in_legend() -> None:
    gallery = GALLERY_PATH.read_text(encoding="utf-8")
    media = re.search(r"<p><a .*?</picture></a></p>", gallery, re.S)
    assert media is not None
    hidden = gallery.replace(media.group(), "", 1).replace(
        "<summary>Read the garden</summary>",
        f"<summary>Read the garden</summary>\n{media.group()}",
        1,
    )
    with pytest.raises(AssertionError):
        assert_gallery_contents(hidden)


def test_generator_connect_qr_uses_width_400() -> None:
    """Connect vCard QR is width 400, not the old 200 thumbnail."""
    stale = dedent(
        """\
        ## Connect

        <p align="center">
          <img src=".github/assets/img/qr.png" alt="vCard QR Code"
               width="200" loading="lazy"/>
        </p>
        """
    )
    generator = ReadmeSectionGenerator(
        settings=ReadmeSectionsSettings(featured_repos=[], social_links=[]),
    )
    rendered = generator._rewrite_qr_block(stale)
    tag = re.search(
        r'<img src="\.github/assets/img/qr\.png"[^>]*>',
        rendered,
    )
    assert tag is not None
    assert 'width="400"' in tag.group(0)
    assert 'width="200"' not in tag.group(0)
    assert 'width="200"' not in rendered


def test_compile_section_body_re_keeps_word_cloud_h3s() -> None:
    """Neighbor catch-all is ^##(?!#) so ### Topics does not truncate Word Clouds."""
    order = _order()
    stub = "## Word Clouds\n\n### Topics\nbody\n\n## Latest Blog Posts\n"
    match = compile_section_body_re("Word Clouds", order).search(stub)
    assert match is not None
    body = match.group(0)
    assert "### Topics" in body
    assert "body" in body
    assert "Latest Blog Posts" not in body


def test_generator_word_clouds_use_h3s_and_markdown_frequency_tables(
    tmp_path: Path,
) -> None:
    """Word Clouds rewrite emits Topics/Languages H3s and pipe-table frequencies."""
    assets = tmp_path / ".github" / "assets"
    assets.mkdir(parents=True)
    (assets / "topics.md").write_text(
        "## Contents\n- [python](#python)\n\n## python\n"
        "- [org/repo](https://example.com/repo)\n",
        encoding="utf-8",
    )
    (assets / "languages.md").write_text(
        "## Contents\n- [Python](#python)\n\n## Python\n"
        "- [org/repo](https://example.com/repo)\n",
        encoding="utf-8",
    )
    stale = "## Word Clouds\n\nstale clouds\n\n## Latest Blog Posts\n"
    generator = ReadmeSectionGenerator(
        settings=ReadmeSectionsSettings(featured_repos=[], social_links=[]),
    )
    rendered = generator._rewrite_word_clouds_section(
        stale, readme_path=tmp_path / "README.md"
    )
    match = compile_section_body_re("Word Clouds", _order()).search(rendered)
    assert match is not None
    clouds = match.group(0)
    assert re.search(
        r'<img src="[^"]*wordcloud_typographic_by_topics\.svg"[^>]*width="100%"',
        clouds,
    )
    assert re.search(
        r'<img src="[^"]*wordcloud_typographic_by_languages\.svg"[^>]*width="100%"',
        clouds,
    )
    assert_word_clouds_have_h3s_and_frequency_tables(clouds)
    assert "<summary><strong>WakaTime Stats</strong></summary>" not in rendered
