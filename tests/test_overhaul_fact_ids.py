"""Fact-id named checks for profile-readme-overhaul automatedVerification facts.

These lock the automatable subset. Residuals (github.com/camo, live Waka API,
habits panel missing from metrics.svg, G-DEV) are recorded in
goals/profile-readme-overhaul/inventory/I99.md — they are not claimed here.
"""

from __future__ import annotations

import hashlib
import json
import re
from html import unescape
from pathlib import Path

from scripts.art.artifacts import LIVING_ART_STYLE_KEYS
from scripts.art.daily_snapshots import validate_snapshot_monotonic_contract
from scripts.art.timelapse import ALL_STYLES
from scripts.config import load_skills
from scripts.readme_sections import (
    _GHPVC_URL,
    _SUPPLEMENTAL_METRICS_ASSETS,
    _WAKATIME_ASSET_SRC,
)
from scripts.wakatime_readme import (
    DEFAULT_WAKATIME_SVG_PATH,
    is_leisure_or_unprofessional,
    looks_like_file_path,
    looks_like_heartbeat_entity,
)
from scripts.word_clouds import DEFAULT_RENDERER
from scripts.word_clouds.generate import SHIPPED_WORD_CLOUD_SOURCES
from tests.test_profile_workflow import (
    BANNER_DARK,
    BANNER_LIGHT,
    README_PATH,
    _git_show_bytes,
    _job_block,
    _lowlighter_with_blocks,
    _workflow_text,
)
from tests.test_skills import iter_skills
from tests.test_wakatime_svg import _PRIVATE_AND_LEISURE

_FACTS_META = Path("goals/profile-readme-overhaul/facts.meta.json")
_PINNED_BANNER_SHA256 = {
    BANNER_LIGHT: (
        "a5e8d08ffb218924a322e423318219af5909f9ff4923891103842a8f7f408649"
    ),
    BANNER_DARK: (
        "6aaf135ac987e66ddf0594722ed9980c46c374b8a4db09ea05db56cff588f9b7"
    ),
}
_SHIPPED_CLOUDS = (
    Path(".github/assets/img/wordcloud_typographic_by_topics.svg"),
    Path(".github/assets/img/wordcloud_typographic_by_languages.svg"),
)
_SKILLS_BLOCK_RE = re.compile(
    r"<!-- SKILLS:START -->\n(.*?)<!-- SKILLS:END -->",
    re.S,
)
_DETAILS_RE = re.compile(r"(?is)<details\b.*?</details>")


def _readme() -> str:
    return README_PATH.read_text(encoding="utf-8")


def _skills_block(readme: str) -> str:
    match = _SKILLS_BLOCK_RE.search(readme)
    assert match is not None, "SKILLS markers missing"
    return match.group(1)


def _prod_lowlighter_blocks() -> tuple[str, str, str]:
    blocks = _lowlighter_with_blocks(
        _job_block(_workflow_text(), "generate-profile-metrics")
    )
    assert len(blocks) >= 3
    return blocks[0], blocks[1], blocks[2]


def test_automated_verification_facts_have_named_checks() -> None:
    """Every automatedVerification fact-id appears in tests/."""
    facts = json.loads(_FACTS_META.read_text(encoding="utf-8"))
    corpus = "\n".join(
        path.read_text(encoding="utf-8")
        for path in Path("tests").glob("test_*.py")
    )
    missing = [
        fact["id"]
        for fact in facts
        if fact["automatedVerification"] and fact["id"] not in corpus
    ]
    assert missing == []


def test_fact_banner_pin_worktree_matches_pinned_origin_main_hashes() -> None:
    """fact-banner-pin: header pair matches pinned origin/main SHA-256."""
    for path, digest in _PINNED_BANNER_SHA256.items():
        assert path.is_file(), f"missing {path}"
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        assert actual == digest, f"{path} hash {actual} != pinned {digest}"
        origin = _git_show_bytes(f"origin/main:{path.as_posix()}")
        if origin is None:
            continue
        assert hashlib.sha256(origin).hexdigest() == digest
        assert path.read_bytes() == origin
    assert "generate banner" not in _workflow_text()


def test_fact_lowlighter_off_production_music_tweets_activity_stay_no() -> None:
    """fact-lowlighter-off: music/tweets/activity stay off; no Spotify in with:."""
    workflow = _workflow_text()
    prod = _job_block(workflow, "generate-profile-metrics")
    for block in _lowlighter_with_blocks(prod):
        assert re.search(r"(?m)^\s*plugin_music:\s*no\s*$", block)
        assert re.search(r"(?m)^\s*plugin_tweets:\s*no\s*$", block)
        assert re.search(r"(?m)^\s*plugin_activity:\s*no\s*$", block)
        assert "SPOTIFY_" not in block
        assert "plugin_music_token" not in block
        assert "plugin_music_provider" not in block
    assert "anmol098/waka-readme-stats" not in workflow


def test_fact_lowlighter_retry_lines_achievements_gists_stay_off() -> None:
    """fact-lowlighter-retry: no isolate-retry; unclean plugins stay off."""
    primary, _additional, extra = _prod_lowlighter_blocks()
    prod = _job_block(_workflow_text(), "generate-profile-metrics")
    assert "plugin_lines: no" in primary
    assert "plugin_achievements: no" in primary
    assert "plugin_gists: no" in primary
    assert "plugin_gists: no" in extra
    assert "plugin_lines:" not in extra
    assert "plugin_achievements:" not in extra
    assert "plugin_lines: yes" not in prod
    assert "plugin_achievements: yes" not in prod
    assert "plugin_gists: yes" not in prod


def test_fact_habits_both_yaml_on_and_first_party_card_exists() -> None:
    """fact-habits-both: YAML plugin_habits yes + first-party metrics-habits.svg.

    Does not claim the committed primary metrics.svg renders a habits plugin panel.
    """
    primary, additional, extra = _prod_lowlighter_blocks()
    assert "plugin_habits: yes" in primary
    assert "plugin_habits: no" in additional
    assert "plugin_habits: no" in extra
    habits = Path(".github/assets/img/metrics-habits.svg")
    assert habits.is_file()
    text = habits.read_text(encoding="utf-8")
    assert "Coding habits" in text
    assert "habits-focus" in text
    assert "habits-peak" in text
    assert "habits-streaks" in text
    assert 'src=".github/assets/img/metrics-habits.svg"' in _readme()


def test_fact_remove_feed_metrics_activity_absent() -> None:
    """fact-remove-feed: first-party activity card is not emitted or embedded."""
    readme = _readme()
    assert "metrics-activity.svg" not in readme
    names = {name for name, _alt in _SUPPLEMENTAL_METRICS_ASSETS}
    assert "metrics-activity.svg" not in names
    assert names == {
        "metrics-languages.svg",
        "metrics-habits.svg",
        "metrics-music.svg",
        "metrics-posts.svg",
    }
    finalize = _job_block(_workflow_text(), "finalize")
    assert "metrics-activity.svg" not in finalize
    prod = _job_block(_workflow_text(), "generate-profile-metrics")
    assert "metrics-activity.svg" not in prod


def test_fact_living_art_spine_exact_six_and_monotonic_helper() -> None:
    """fact-living-art-spine: one registry, six living-*.gif, monotonic helper."""
    assert tuple(ALL_STYLES) == LIVING_ART_STYLE_KEYS
    assert ALL_STYLES == [
        "inkgarden",
        "topo",
        "genetic",
        "physarum",
        "lenia",
        "ferrofluid",
    ]
    readme = _readme()
    for style in ALL_STYLES:
        path = Path(f".github/assets/img/living-{style}.gif")
        assert path.is_file(), f"missing {path}"
        assert path.stat().st_size > 0
        assert f"living-{style}.gif" in readme
    assert callable(validate_snapshot_monotonic_contract)


def test_fact_no_200_copy_readme_summary_is_bare() -> None:
    """fact-no-200-copy: committed README has no count or teaser blurb."""
    readme = _readme()
    assert "200+" not in readme
    assert "View full stack" not in readme
    assert "<summary><strong>Tech Stack</strong></summary>" in readme


def test_fact_tech_details_stack_collapsed_waka_visible() -> None:
    """fact-tech-details: stack in <details>; Waka <img> is open-flow.

    Does not require the SVG to sit inside ## Metrics (current README places
    it after ## Word Clouds).
    """
    readme = _readme()
    assert f'src="{_WAKATIME_ASSET_SRC}"' in readme
    details_blocks = _DETAILS_RE.findall(readme)
    assert details_blocks
    assert any("<!-- SKILLS:START -->" in block for block in details_blocks)
    for block in details_blocks:
        assert _WAKATIME_ASSET_SRC not in block
        assert "README:BLOG_POSTS" not in block


def test_fact_badges_stack_https_homepages_and_camo_safe_srcs() -> None:
    """fact-badges-stack: every catalog skill has https homepage + shields src."""
    settings = load_skills()
    catalog = list(iter_skills(settings))
    assert len(catalog) == 151
    for skill in catalog:
        assert skill.url, f"Missing homepage url for '{skill.name}'"
        assert skill.url.strip().startswith("https://"), skill.url
        assert skill.slug or skill.logo_path, skill.name


def test_fact_badges_qa_readme_hrefs_zip_catalog_and_src_lengths() -> None:
    """fact-badges-qa: first-party boards name every catalog skill."""
    catalog = list(iter_skills(load_skills()))
    block = _skills_block(_readme())
    images = re.findall(r'<img alt="([^"]+)" src="([^"]+)"', block)
    assert images
    joined_alts = unescape(" ".join(alt for alt, _src in images))
    for skill in catalog:
        assert skill.name in joined_alts
    for _alt, src in images:
        decoded = unescape(src)
        assert decoded.startswith(".github/assets/img/readme/tech-")
        assert decoded.endswith(".svg")
        assert Path(decoded).is_file()


def test_fact_wordclouds_exactly_two_typographic_volume_sources() -> None:
    """fact-wordclouds: exactly two shipped clouds; size follows starred volume."""
    assert DEFAULT_RENDERER == "typographic"
    assert SHIPPED_WORD_CLOUD_SOURCES == ("topics", "languages")
    readme = _readme()
    cloud_srcs = re.findall(
        r'src="(\.github/assets/img/wordcloud_[^"]+)"',
        readme,
    )
    assert cloud_srcs == [
        ".github/assets/img/wordcloud_typographic_by_topics.svg",
        ".github/assets/img/wordcloud_typographic_by_languages.svg",
    ]
    for path in _SHIPPED_CLOUDS:
        assert path.is_file()
        assert path.stat().st_size > 0
        svg = path.read_text(encoding="utf-8")
        assert svg.startswith("<svg") or "<svg" in svg[:200]
        assert "rotate(" not in svg


def test_fact_waka_svg_committed_card_has_public_safe_sections() -> None:
    """fact-waka-svg: first-party SVG (not anmol098) with public-safe sections.

    Does not claim the committed card is live Waka API output.
    """
    assert DEFAULT_WAKATIME_SVG_PATH == Path(".github/assets/img/wakatime.svg")
    path = DEFAULT_WAKATIME_SVG_PATH
    assert path.is_file()
    svg = path.read_text(encoding="utf-8")
    assert svg.startswith("<svg")
    assert "anmol098" not in svg
    assert "Languages" in svg
    assert "Editors" in svg
    assert "Platforms" in svg
    assert "Categories" in svg
    assert "This week" in svg
    assert "Last year" in svg
    assert "All time" in svg
    assert "Coding heatmap" in svg
    assert "Mac" in svg
    readme = _readme()
    assert f'src="{_WAKATIME_ASSET_SRC}"' in readme
    assert "anmol098/waka-readme-stats" not in _workflow_text()


def test_fact_waka_privacy_committed_svg_omits_banned_rows() -> None:
    """fact-waka-privacy: committed SVG has no paths/heartbeats/leisure rows."""
    svg = Path(".github/assets/img/wakatime.svg").read_text(encoding="utf-8")
    for banned in _PRIVATE_AND_LEISURE:
        assert banned not in svg
    assert "/Users/" not in svg
    assert "~/" not in svg
    assert "C:\\" not in svg
    assert looks_like_file_path("/Users/ww/private.py")
    assert looks_like_heartbeat_entity("heartbeat")
    assert is_leisure_or_unprofessional("Entertainment")
    assert is_leisure_or_unprofessional("Games")
    assert is_leisure_or_unprofessional("Spotify")


def test_fact_blog_visible_rss_strip_not_details() -> None:
    """fact-blog: 4–5 visible w4w.dev RSS cards with title, date, hook, link."""
    readme = _readme()
    start = readme.index("<!-- README:BLOG_POSTS:START -->")
    end = readme.index("<!-- README:BLOG_POSTS:END -->")
    blog = readme[start:end]
    assert "<details" not in blog.lower()
    assert "<summary><strong>Latest Blog Posts</strong></summary>" not in readme
    assert "## Latest Blog Posts" in readme
    assert "blog-posts.svg" in blog
    hrefs = re.findall(r'<a href="([^"]+)"', blog)
    assert len(hrefs) >= 4
    for href in hrefs:
        assert "w4w.dev" in unescape(href)
    assert len(re.findall(r"20\d{2}-\d{2}-\d{2}", blog)) >= 4


def test_fact_views_komarev_for_the_badge() -> None:
    """fact-views: incrementing komarev ghpvc restyled to for-the-badge."""
    readme = _readme()
    assert _GHPVC_URL in readme
    assert "komarev.com/ghpvc/?username=wyattowalsh" in readme
    assert "style=for-the-badge" in readme
    assert "label=Views" in readme
    assert "style=flat-square" not in readme
    workflow = _workflow_text()
    assert "view-counter" not in workflow
    assert "ghpvc" not in _job_block(workflow, "generate-profile-metrics")
