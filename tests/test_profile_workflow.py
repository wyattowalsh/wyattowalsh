"""Workflow contract tests for the profile updater."""

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
