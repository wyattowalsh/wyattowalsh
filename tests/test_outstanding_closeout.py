"""Contracts for the outstanding-work closeout facts."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]


def test_lowlighter_svgs_are_absent_and_docs_do_not_keep_them() -> None:
    for name in ("metrics.svg", "metrics.additional.svg", "metrics.extra.svg"):
        assert not (REPO / ".github/assets/img" / name).is_file()
    workflows = (REPO / "docs/content/docs/workflows/index.mdx").read_text()
    assert "may remain" not in workflows
    assert "not generated, uploaded, embedded, or kept" in workflows


def test_generative_svgs_are_present() -> None:
    img = REPO / ".github/assets/img"
    for name in (
        "generative-activity.svg",
        "generative-activity-dark.svg",
        "generative-community.svg",
        "generative-community-dark.svg",
    ):
        assert (img / name).is_file(), name
    showcase = REPO / "docs/public/showcase"
    assert (showcase / "generative-activity.svg").is_file()
    assert (showcase / "generative-community.svg").is_file()


def test_banner_defaults_match_pinned_svg() -> None:
    from scripts.banner import BannerConfig

    config = BannerConfig()
    assert config.width == 1600
    assert config.height == 480
    text = (REPO / ".github/assets/img/banner.svg").read_text(encoding="utf-8")[:400]
    assert 'width="1600"' in text
    assert 'height="480"' in text


def test_schedule_docs_name_the_default_branch() -> None:
    text = (REPO / "docs/content/docs/workflows/index.mdx").read_text()
    assert "default branch, which is `main`" in text
    workflow = (REPO / ".github/workflows/profile-updater.yml").read_text()
    triggers = workflow.split("jobs:", maxsplit=1)[0]
    assert "refs/heads/dev" in workflow
    assert "\n      - main\n" not in triggers


def test_false_doc_commands_are_gone() -> None:
    index = (REPO / "docs/content/docs/index.mdx").read_text()
    assert "scripts/word_clouds.py" not in index
    assert "scripts/animated_art.py" not in index
    agents = (REPO / "tests/AGENTS.md").read_text()
    assert "TestQRCodeGenerator::test_init_success" not in agents
    testing = (REPO / "docs/content/docs/development/testing.mdx").read_text()
    assert "from scripts.art.ink_garden import generate, seed_hash" not in testing
    generate = (REPO / "docs/content/docs/cli/generate.mdx").read_text()
    assert "case-insensitive" not in generate
    history = (REPO / "docs/content/docs/data/fetch-history.mdx").read_text()
    assert "stars_last_30d" not in history
    assert "starred_at" not in history
    rule = (
        REPO / ".cursor/rules/05-python-versioning-and-dependencies.mdc"
    ).read_text()
    assert "3.10" not in rule
    assert "requirements.txt" not in rule
    assert "DEFAULT_MASK_PATH" not in (REPO / "scripts/AGENTS.md").read_text()


def test_probe_does_not_upload_or_forward_metrics_token() -> None:
    workflow = (REPO / ".github/workflows/profile-updater.yml").read_text()
    probe = workflow.split("probe-full-metrics:", maxsplit=1)[1].split(
        "\n  update-starred-lists:",
        maxsplit=1,
    )[0]
    assert "metrics-probe-" not in probe
    lowlighter = probe.split("uses: lowlighter/metrics@", maxsplit=1)[1]
    assert "secrets.METRICS_TOKEN" not in lowlighter
    assert "token: ${{ github.token }}" in probe


def test_wakatime_other_owner_short_name_is_not_public() -> None:
    from scripts.wakatime_readme import is_publishable_project

    allowed = ("docs", "wyattowalsh/docs", "wyattowalsh/wyattowalsh")
    assert (
        is_publishable_project("other-owner/docs", public_repo_names=allowed)
        is False
    )
    assert (
        is_publishable_project(
            "wyattowalsh/wyattowalsh",
            public_repo_names=allowed,
        )
        is True
    )


def test_spotify_callback_host_is_loopback_only() -> None:
    from scripts.spotify_auth import mint_spotify_refresh_token

    with pytest.raises(ValueError, match="callback host"):
        mint_spotify_refresh_token(
            client_id="id",
            client_secret="secret",
            callback_host="0.0.0.0",
        )


def test_console_log_level_follows_env(monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts.utils import console_log_level

    monkeypatch.delenv("LOG_LEVEL", raising=False)
    monkeypatch.delenv("DEBUG_MODE", raising=False)
    assert console_log_level() == "INFO"
    monkeypatch.setenv("LOG_LEVEL", "warning")
    assert console_log_level() == "WARNING"
    monkeypatch.setenv("DEBUG_MODE", "true")
    assert console_log_level() == "DEBUG"


def test_gitignore_covers_spotify_refresh_token() -> None:
    assert "spotify_refresh_token.txt" in (REPO / ".gitignore").read_text()


def test_six_styles_and_no_accepted_key() -> None:
    from scripts.art.roster import CANDIDATE_STYLE_KEYS, SHIPPED_STYLE_KEYS

    assert SHIPPED_STYLE_KEYS is CANDIDATE_STYLE_KEYS
    assert len(SHIPPED_STYLE_KEYS) == 6
    bakeoff = json.loads(
        (REPO / "goals/living-art-overhaul/bakeoff.json").read_text()
    )
    assert "accepted" not in bakeoff


def test_blog_fetch_failure_keeps_the_existing_block(tmp_path: Path) -> None:
    from scripts.config import ReadmeSectionsSettings
    from scripts.readme_sections import ReadmeSectionGenerator

    class FailedFeed:
        def fetch_latest_posts(self, feed_url: str, limit: int) -> None:
            return None

    class EmptyFeed:
        def fetch_latest_posts(self, feed_url: str, limit: int) -> list[object]:
            return []

    readme = tmp_path / "README.md"
    block = (
        "<!-- README:BLOG_POSTS:START -->\nkeep me\n"
        "<!-- README:BLOG_POSTS:END -->"
    )
    readme.write_text(block, encoding="utf-8")
    failed = ReadmeSectionGenerator(
        settings=ReadmeSectionsSettings(readme_path=str(readme)),
        blog_client=FailedFeed(),
    )
    assert failed._render_blog_posts() is None
    assert "keep me" in failed._inject_block(
        block,
        failed.BLOG_START,
        failed.BLOG_END,
        None,
    )
    empty = ReadmeSectionGenerator(
        settings=ReadmeSectionsSettings(readme_path=str(readme)),
        blog_client=EmptyFeed(),
    )
    rendered = empty._render_blog_posts()
    assert rendered is not None
    assert "No recent posts available." in rendered


def test_animated_unknown_profile_exits_nonzero(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import sys

    from scripts.art import animate

    monkeypatch.setattr(sys, "argv", ["animate", "--profile", "wyattowalsh"])
    with pytest.raises(SystemExit) as exc:
        animate.main()
    assert exc.value.code == 1
