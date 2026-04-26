"""Workflow contract tests for the profile updater."""

from pathlib import Path

WORKFLOW_PATH = Path(".github/workflows/profile-updater.yml")


def test_wakatime_job_skips_wakatime_generated_commits() -> None:
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "github.event.head_commit.message != 'Updated with Dev Metrics'" in workflow


def test_wakatime_action_avoids_known_bad_inputs_and_loc_chart() -> None:
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "PULL_BRANCH_NAME" not in workflow
    assert "PUSH_BRANCH_NAME" not in workflow
    assert 'SHOW_LOC_CHART: "False"' in workflow
