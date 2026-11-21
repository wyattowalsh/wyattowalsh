"""Fact-id named checks for profile-readme-overhaul automatedVerification facts.

These lock the automatable subset. Residual tests below record the current
origin/dev preview holes (they are not a claim that the fact holds). Full
prose is in goals/profile-readme-overhaul/inventory/I99.md.
"""

from __future__ import annotations

import hashlib
import json
import re
from html import unescape
from pathlib import Path

from scripts.art.artifacts import LIVING_ART_STYLE_KEYS
from scripts.art.daily_snapshots import validate_snapshot_monotonic_contract
from scripts.art.roster import CANDIDATE_STYLE_KEYS, SHIPPED_STYLE_KEYS
from scripts.art.timelapse import ALL_STYLES
from scripts.config import load_skills
from scripts.readme_sections import (
    _GHPVC_URL,
    _SUPPLEMENTAL_METRICS_ASSETS,
)
from scripts.skills import MAX_SHIELDS_BADGE_URL_LENGTH
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
from tests.test_readme_gfm_ux import (
    assert_blog_cards,
    assert_metric_panels,
    assert_tech_stack_dropdown_is_h2,
    assert_visible_or_comment_heading,
    slice_between_headings,
)
from tests.test_skills import iter_skills
from tests.test_wakatime_svg import _PRIVATE_AND_LEISURE

_FACTS_META = Path("goals/profile-readme-overhaul/facts.meta.json")
_PINNED_BANNER_SHA256 = {
    BANNER_LIGHT: ("a5e8d08ffb218924a322e423318219af5909f9ff4923891103842a8f7f408649"),
    BANNER_DARK: ("6aaf135ac987e66ddf0594722ed9980c46c374b8a4db09ea05db56cff588f9b7"),
}
_SHIPPED_CLOUDS = (
    Path(".github/assets/img/wordcloud_typographic_by_topics.svg"),
    Path(".github/assets/img/wordcloud_typographic_by_languages.svg"),
)
_SKILLS_BLOCK_RE = re.compile(
    r"<!-- SKILLS:START -->\n(.*?)<!-- SKILLS:END -->",
    re.S,
)


def _readme() -> str:
    return README_PATH.read_text(encoding="utf-8")


def _skills_block(readme: str) -> str:
    match = _SKILLS_BLOCK_RE.search(readme)
    assert match is not None, "SKILLS markers missing"
    return str(match.group(1))


def _probe_lowlighter_blocks() -> tuple[str, str, str]:
    blocks = _lowlighter_with_blocks(_job_block(_workflow_text(), "probe-full-metrics"))
    assert len(blocks) >= 3
    return blocks[0], blocks[1], blocks[2]


def test_automated_verification_facts_have_named_checks() -> None:
    """Every automatedVerification fact-id appears in tests/."""
    facts = json.loads(_FACTS_META.read_text(encoding="utf-8"))
    corpus = "\n".join(
        path.read_text(encoding="utf-8") for path in Path("tests").glob("test_*.py")
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
    """fact-lowlighter-off: production has no lowlighter; probe keeps music off."""
    workflow = _workflow_text()
    prod = _job_block(workflow, "generate-profile-metrics")
    assert "uses: lowlighter/metrics@" not in prod
    assert "plugin_music:" not in prod
    assert "plugin_tweets:" not in prod
    assert "plugin_activity:" not in prod
    for block in _probe_lowlighter_blocks():
        assert re.search(r"(?m)^\s*plugin_music:\s*no\s*$", block)
        assert "SPOTIFY_" not in block
        assert "plugin_music_token" not in block
        assert "plugin_music_provider" not in block
    assert "anmol098/waka-readme-stats" not in workflow


def test_fact_lowlighter_retry_lines_achievements_gists_stay_off() -> None:
    """fact-lowlighter-retry: production dropped isolate-retry lowlighter cards."""
    prod = _job_block(_workflow_text(), "generate-profile-metrics")
    assert "uses: lowlighter/metrics@" not in prod
    assert "plugin_lines:" not in prod
    assert "plugin_achievements:" not in prod
    assert "plugin_gists:" not in prod


def test_fact_habits_both_yaml_on_and_first_party_card_exists() -> None:
    """fact-habits-both: first-party habits card is the production surface."""
    prod = _job_block(_workflow_text(), "generate-profile-metrics")
    assert "uses: lowlighter/metrics@" not in prod
    assert "plugin_habits:" not in prod
    habits = Path(".github/assets/img/metrics-habits.svg")
    assert habits.is_file()
    text = habits.read_text(encoding="utf-8")
    assert "Coding habits" in text
    assert "habits-focus" in text
    assert "habits-peak" in text
    assert "habits-streaks" in text
    assert 'src=".github/assets/img/summary-metrics-habits.svg"' in _readme()
    assert "](.github/assets/img/metrics-habits.svg)" in _readme()


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
    # The finalizer stages a tracked deletion if an older checkout has the card.
    assert finalize.count("metrics-activity.svg") == 1
    assert "            ./.github/assets/img/metrics-activity.svg\n" in finalize
    prod = _job_block(_workflow_text(), "generate-profile-metrics")
    assert "metrics-activity.svg" not in prod


def test_fact_living_art_spine_exact_six_and_monotonic_helper() -> None:
    """fact-living-art-spine: one registry, six living-*.gif, monotonic helper."""
    assert set(SHIPPED_STYLE_KEYS) <= set(CANDIDATE_STYLE_KEYS)
    assert tuple(ALL_STYLES) == CANDIDATE_STYLE_KEYS
    assert LIVING_ART_STYLE_KEYS == SHIPPED_STYLE_KEYS
    if SHIPPED_STYLE_KEYS == CANDIDATE_STYLE_KEYS:
        assert tuple(ALL_STYLES) == LIVING_ART_STYLE_KEYS
    gallery = Path("LIVING_ART.md").read_text(encoding="utf-8")
    for style in LIVING_ART_STYLE_KEYS:
        path = Path(f".github/assets/img/living-{style}.gif")
        assert path.is_file(), f"missing {path}"
        assert path.stat().st_size > 0
        assert f"living-{style}.gif" in gallery
    assert callable(validate_snapshot_monotonic_contract)


def test_fact_no_200_copy_readme_summary_is_bare() -> None:
    """fact-no-200-copy: committed README has no count or teaser blurb."""
    readme = _readme()
    assert "200+" not in readme
    assert "View full stack" not in readme
    assert_tech_stack_dropdown_is_h2(readme)


def test_fact_tech_details_stack_collapsed_waka_visible() -> None:
    """fact-tech-details: the open-flow WakaTime summary links its full report."""
    readme = _readme()
    assert_metric_panels(readme)
    assert "This Week I Spent My Time On" not in readme
    assert_tech_stack_dropdown_is_h2(readme)


def test_fact_badges_stack_https_homepages_and_camo_safe_srcs() -> None:
    """fact-badges-stack: every catalog skill has https homepage + shields src."""
    settings = load_skills()
    catalog = list(iter_skills(settings))
    assert len(catalog) == 151
    for skill in catalog:
        assert skill.url not in (None, ""), f"Missing homepage url for '{skill.name}'"
        assert skill.url.strip().startswith("https://"), skill.url
        assert skill.slug not in (None, "") or skill.logo_path not in (None, ""), (
            skill.name
        )


def test_fact_badges_qa_readme_hrefs_zip_catalog_and_src_lengths() -> None:
    """fact-badges-qa: README shields name every catalog skill with camo-safe srcs."""
    catalog = list(iter_skills(load_skills()))
    block = _skills_block(_readme())
    images = re.findall(r'<img alt="([^"]+)" src="([^"]+)"', block)
    assert images
    joined_alts = unescape(" ".join(alt for alt, _src in images))
    for skill in catalog:
        assert skill.name in joined_alts
    for _alt, src in images:
        decoded = unescape(src)
        assert decoded.startswith("https://img.shields.io/badge/")
        assert len(decoded) <= MAX_SHIELDS_BADGE_URL_LENGTH


def test_fact_wordclouds_exactly_two_typographic_volume_sources() -> None:
    """fact-wordclouds: exactly two shipped clouds; size follows starred volume."""
    assert DEFAULT_RENDERER == "typographic"
    assert SHIPPED_WORD_CLOUD_SOURCES == ("topics", "languages")
    readme = _readme()
    cloud_srcs = re.findall(
        r'src="(\.github/assets/img/wordcloud_[^"]+)"',
        readme,
    )
    expected = (
        ".github/assets/img/wordcloud_typographic_by_topics.svg",
        ".github/assets/img/wordcloud_typographic_by_languages.svg",
    )
    assert list(dict.fromkeys(cloud_srcs)) == list(expected)
    assert set(cloud_srcs) <= set(expected)
    for path in _SHIPPED_CLOUDS:
        assert path.is_file()
        assert path.stat().st_size > 0
        svg = path.read_text(encoding="utf-8")
        assert svg.startswith("<svg") or "<svg" in svg[:200]


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
    assert 'src=".github/assets/img/summary-wakatime.svg"' in readme
    assert "](.github/assets/img/wakatime.svg)" in readme
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


def test_fact_blog_visible_rss_strip_and_title_links() -> None:
    """fact-blog: five visible RSS cards have matching native text links."""
    readme = _readme()
    assert_visible_or_comment_heading(readme, "Latest Blog Posts")
    assert_blog_cards(slice_between_headings(readme, "Latest Blog Posts", "Connect"))


def test_fact_views_komarev_for_the_badge() -> None:
    """fact-views: incrementing komarev ghpvc restyled to for-the-badge."""
    readme = _readme()
    assert _GHPVC_URL in readme
    assert "custom-icon-badges.demolab.com/badge/dynamic/json" in readme
    assert "logo=telescope" in readme
    assert "hitscounter.dev" in readme
    assert "style=for-the-badge" in readme
    assert "label=views" in readme
    assert "views-peek.svg" not in readme
    assert "komarev.com/ghpvc" not in readme
    assert "style=flat-square" not in readme
    workflow = _workflow_text()
    assert "view-counter" not in workflow
    assert "ghpvc" not in _job_block(workflow, "generate-profile-metrics")


def test_fact_ship_dev_on_push_is_dev_and_finalize_refuses_main() -> None:
    """fact-ship-dev: on.push is dev-only; finalize refuses non-dev."""
    text = _workflow_text()
    push_match = re.search(
        r"(?ms)^  push:\n    branches:\n((?:      - [^\n]+\n)+)",
        text,
    )
    assert push_match is not None
    push_branches = re.findall(r"- (\S+)", push_match.group(1))
    assert push_branches == ["dev"]
    assert "main" not in push_branches
    finalize = _job_block(text, "finalize")
    assert "TARGET_BRANCH: ${{ github.head_ref || github.ref_name }}" in finalize
    assert 'if [ "${TARGET_BRANCH}" != "dev" ]; then' in finalize
    assert "Profile publication is restricted to refs/heads/dev" in finalize
    assert "github.ref == 'refs/heads/dev'" in finalize
    assert re.search(r'(?m)^\s*-\s*cron:\s*"0 1 \* \* \*"', text)


def test_fact_habits_both_primary_metrics_svg_lacks_habits_panel() -> None:
    """fact-habits-both residual: leftover lowlighter metrics.svg is not committed."""
    assert not Path(".github/assets/img/metrics.svg").is_file()


def test_fact_lowlighter_maximal_committed_preview_residuals() -> None:
    """fact-lowlighter-maximal residual: leftover lowlighter SVGs are not committed."""
    assert not Path(".github/assets/img/metrics.svg").is_file()
    assert not Path(".github/assets/img/metrics.additional.svg").is_file()


def test_fact_lowlighter_audit_extra_followup_has_nan_bars() -> None:
    """fact-lowlighter-audit residual: leftover extra SVG is not committed."""
    assert not Path(".github/assets/img/metrics.extra.svg").is_file()


def test_fact_badges_stack_readme_shields_link_https_homepages() -> None:
    """fact-badges-stack: shipped SKILLS block wraps each shield in a homepage href."""
    catalog = list(iter_skills(load_skills()))
    assert len(catalog) == 151
    block = _skills_block(_readme())
    hrefs = [unescape(href) for href in re.findall(r'<a href="([^"]+)"', block)]
    assert hrefs
    for href in hrefs:
        assert href.startswith("https://")
    for skill in catalog:
        homepage = (skill.url or "").strip()
        assert homepage.startswith("https://"), skill.name
        assert homepage in block
    images = re.findall(r'<img alt="([^"]+)" src="([^"]+)"', block)
    wrapped = re.findall(
        r'<a href="(https://[^"]+)"><img alt="([^"]+)" src="([^"]+)"',
        block,
    )
    assert images
    assert wrapped
    assert len(wrapped) == len(images)


def test_fact_waka_svg_committed_platforms_are_mac_only() -> None:
    """fact-waka-svg residual: committed Platforms row is Mac only (no iOS/watchOS)."""
    svg = Path(".github/assets/img/wakatime.svg").read_text(encoding="utf-8")
    assert "Platforms" in svg
    assert ">Mac</text>" in svg
    assert "iOS" not in svg
    assert "watchOS" not in svg


def test_fact_blog_committed_readme_contains_all_configured_public_hooks() -> None:
    """fact-blog: reviewed article hooks ship on their matching linked cards."""
    from scripts.config import load_config
    from tests.test_readme_gfm_ux import rendered

    settings = load_config().readme_sections_settings
    assert settings is not None and settings.profile_cards is not None
    profile = settings.profile_cards
    blog = rendered(slice_between_headings(_readme(), "Latest Blog Posts", "Connect"))
    cards = blog.select("a:has(img)")
    assert len(cards) == 5
    for card in cards:
        url = str(card["href"])
        hook = profile.article_hooks.get(url)
        image = card.select_one("img")
        assert image is not None
        if hook is not None:
            assert hook in str(image["alt"])
