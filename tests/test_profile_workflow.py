"""Workflow contract tests for the profile updater."""

import re
from pathlib import Path

WORKFLOW_PATH = Path(".github/workflows/profile-updater.yml")
BANNER_LIGHT = Path(".github/assets/img/banner.svg")
BANNER_DARK = Path(".github/assets/img/banner-dark.svg")

LOWLIGHTER_METRICS_PIN = (
    "lowlighter/metrics@65836723097537a54cd8eb90f61839426b4266b6"
)


def _workflow_text() -> str:
    return WORKFLOW_PATH.read_text(encoding="utf-8")


def _job_block(workflow: str, job_id: str) -> str:
    match = re.search(
        rf"(?ms)^  {re.escape(job_id)}:\n.*?(?=^  [a-z][a-z0-9-]*:\n|\Z)",
        workflow,
    )
    assert match is not None, f"{job_id} job not found"
    return match.group(0)


def _lowlighter_with_blocks(job_text: str) -> list[str]:
    """Return each lowlighter/metrics step's `with:` mapping body."""
    step_chunks = re.split(
        r"(?m)^(?=      - name:)",
        job_text,
    )
    blocks: list[str] = []
    for chunk in step_chunks:
        if "uses: lowlighter/metrics@" not in chunk:
            continue
        with_match = re.search(
            r"(?ms)^        with:\n((?:          .*\n)*)",
            chunk,
        )
        assert with_match is not None, "lowlighter step missing with: block"
        blocks.append(with_match.group(1))
    assert blocks, "expected at least one lowlighter/metrics with: block"
    return blocks


def test_generated_commit_pushes_skip_generator_jobs() -> None:
    workflow = _workflow_text()

    assert "github.event.head_commit.message != 'Updated with Dev Metrics'" in workflow
    assert (
        "github.event.head_commit.message != 'chore(metrics): update generated "
        "metrics assets'"
    ) in workflow
    assert (
        "github.event.head_commit.message != 'chore(readme): update dynamic "
        "sections and skills badges'"
    ) in workflow
    assert workflow.count("github.event.head_commit.message !=") >= 6 * 6


def test_wakatime_action_avoids_known_bad_inputs_and_loc_chart() -> None:
    workflow = _workflow_text()

    assert "PULL_BRANCH_NAME" not in workflow
    assert "PUSH_BRANCH_NAME" not in workflow
    assert 'SHOW_LOC_CHART: "False"' in workflow


def test_generate_assets_runs_banner_step() -> None:
    workflow = _workflow_text()

    assert "generate banner --config-path config.yaml" in workflow
    assert "Generate light and dark banners" in workflow
    assert "banner*.svg" in workflow


def test_banner_and_banner_dark_required_by_ci_contracts() -> None:
    """Both light and dark banners must exist and be non-empty for CI."""
    assert BANNER_LIGHT.is_file(), f"missing required asset: {BANNER_LIGHT}"
    assert BANNER_DARK.is_file(), f"missing required asset: {BANNER_DARK}"
    assert BANNER_LIGHT.stat().st_size > 0, f"empty asset: {BANNER_LIGHT}"
    assert BANNER_DARK.stat().st_size > 0, f"empty asset: {BANNER_DARK}"


def test_uv_sync_requires_locked_and_forbids_all_groups() -> None:
    workflow = _workflow_text()

    assert "--all-groups" not in workflow
    sync_lines = [
        line.strip()
        for line in workflow.splitlines()
        if "uv sync" in line
    ]
    assert sync_lines, "expected at least one uv sync invocation"
    for line in sync_lines:
        assert "--locked" in line, f"missing --locked: {line}"


def test_generate_assets_installs_cairo_apt_deps() -> None:
    workflow = _workflow_text()
    cairo_apt = (
        "sudo apt-get update && sudo apt-get install -y "
        "libcairo2 libcairo2-dev pkg-config libffi-dev"
    )
    assert cairo_apt in workflow


def test_generate_assets_uses_locked_qr_and_wordcloud_extras() -> None:
    workflow = _workflow_text()
    assert "uv sync --locked --extra qr --extra word-clouds" in workflow
    assert "uv sync --locked --extra script-tools" in workflow


def test_update_skills_needs_generate_assets_fail_closed() -> None:
    workflow = _workflow_text()
    skills_block = _job_block(workflow, "update-skills")

    assert "- generate-assets" in skills_block
    assert "needs.generate-assets.result == 'success'" in skills_block
    assert "needs.update-starred-lists.result == 'success'" in workflow


def test_metrics_probe_and_prod_share_lowlighter_pin_without_felipecrs() -> None:
    workflow = _workflow_text()
    probe = _job_block(workflow, "probe-full-metrics")
    prod = _job_block(workflow, "generate-profile-metrics")

    assert "felipecrs" not in workflow
    assert LOWLIGHTER_METRICS_PIN in probe
    assert LOWLIGHTER_METRICS_PIN in prod
    assert probe.count(LOWLIGHTER_METRICS_PIN) >= 3
    assert prod.count(LOWLIGHTER_METRICS_PIN) >= 3


def test_metrics_third_party_actions_forbid_spotify_secrets_in_with() -> None:
    workflow = _workflow_text()
    for job_id in ("probe-full-metrics", "generate-profile-metrics"):
        for with_block in _lowlighter_with_blocks(_job_block(workflow, job_id)):
            assert "SPOTIFY_" not in with_block
            assert "plugin_music_token" not in with_block
            assert "plugin_music_provider" not in with_block
            assert re.search(r"(?m)^\s*plugin_music:\s*no\s*$", with_block), (
                f"{job_id} lowlighter step missing plugin_music: no"
            )


def test_metrics_production_plugins_match_relevance_matrix() -> None:
    workflow = _workflow_text()
    prod = _job_block(workflow, "generate-profile-metrics")
    blocks = _lowlighter_with_blocks(prod)
    assert len(blocks) >= 3

    primary, additional, extra = blocks[0], blocks[1], blocks[2]

    assert "plugin_isocalendar: yes" in primary
    assert "plugin_languages: yes" in primary
    assert "plugin_notable: yes" in primary
    assert "plugin_topics: yes" in primary
    assert "plugin_achievements: yes" in primary
    assert "plugin_achievements_display: compact" in primary
    assert "plugin_calendar: yes" in primary
    assert "plugin_calendar_limit: 1" in primary
    assert "plugin_habits: no" in primary
    assert "plugin_gists: no" in primary

    assert "plugin_repositories: yes" in additional
    assert "plugin_people: yes" in additional
    assert "plugin_activity: no" in additional
    assert "plugin_habits: no" in additional
    assert "plugin_music: no" in additional
    assert "plugin_tweets: no" in additional
    assert "iina-plugin-bookmarks" in additional

    assert "metrics.extra.svg" in prod
    assert "plugin_reactions: yes" in extra
    assert "plugin_followup: yes" in extra
    assert "plugin_music: no" in extra
    assert "plugin_activity: no" in extra
    assert "plugin_habits: no" in extra


def test_metrics_extra_svg_has_validate_recover_and_commit_paths() -> None:
    workflow = _workflow_text()
    prod = _job_block(workflow, "generate-profile-metrics")

    assert "metrics-backups/metrics.extra.svg" in prod
    assert (
        "uv run python -m scripts.metrics_svg validate "
        "./.github/assets/img/metrics.extra.svg"
    ) in prod
    assert (
        "uv run python -m scripts.metrics_svg recover \\\n"
        "            ./.github/assets/img/metrics.extra.svg \\"
    ) in prod
    assert "./.github/assets/img/metrics.extra.svg" in prod
    assert Path(".github/assets/img/metrics.extra.svg").is_file()
