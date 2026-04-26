"""Workflow contract tests for the profile updater."""

from pathlib import Path

WORKFLOW_PATH = Path(".github/workflows/profile-updater.yml")


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
