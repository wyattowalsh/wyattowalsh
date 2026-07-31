"""Workflow contract tests for the profile updater."""

import re
from pathlib import Path

WORKFLOW_PATH = Path(".github/workflows/profile-updater.yml")
BANNER_LIGHT = Path(".github/assets/img/banner.svg")
BANNER_DARK = Path(".github/assets/img/banner-dark.svg")


def test_generated_commit_pushes_skip_generator_jobs() -> None:
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

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
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "PULL_BRANCH_NAME" not in workflow
    assert "PUSH_BRANCH_NAME" not in workflow
    assert 'SHOW_LOC_CHART: "False"' in workflow


def test_generate_assets_runs_banner_step() -> None:
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

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
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

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
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
    cairo_apt = (
        "sudo apt-get update && sudo apt-get install -y "
        "libcairo2 libcairo2-dev pkg-config libffi-dev"
    )
    assert cairo_apt in workflow


def test_generate_assets_uses_locked_qr_and_wordcloud_extras() -> None:
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
    assert "uv sync --locked --extra qr --extra word-clouds" in workflow
    assert "uv sync --locked --extra script-tools" in workflow


def test_update_skills_needs_generate_assets_fail_closed() -> None:
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
    match = re.search(
        r"(?ms)^  update-skills:\n.*?(?=^  [a-z][a-z0-9-]*:\n|\Z)",
        workflow,
    )
    assert match is not None, "update-skills job not found"
    skills_block = match.group(0)

    assert "- generate-assets" in skills_block
    assert "needs.generate-assets.result == 'success'" in skills_block
    assert "needs.update-starred-lists.result == 'success'" in workflow
