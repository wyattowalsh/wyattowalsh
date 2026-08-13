"""Contract tests for independent Python and docs CI assurance."""

import json
import re
from pathlib import Path
from typing import cast

import yaml

CI_WORKFLOW_PATH = Path(".github/workflows/ci.yml")
DOCS_PACKAGE_PATH = Path("docs/package.json")
DOCS_WORKSPACE_PATH = Path("docs/pnpm-workspace.yaml")

EXPECTED_ACTION_PINS = {
    "actions/checkout": (
        "3d3c42e5aac5ba805825da76410c181273ba90b1",
        "v7.0.1",
    ),
    "actions/setup-node": (
        "820762786026740c76f36085b0efc47a31fe5020",
        "v7.0.0",
    ),
    "actions/setup-python": (
        "5fda3b95a4ea91299a34e894583c3862153e4b97",
        "v7.0.0",
    ),
    "astral-sh/setup-uv": (
        "ae62891fec2bb8e7d6c99fc78c9fec3a63790f8d",
        "v10.0.0",
    ),
    "pnpm/action-setup": (
        "0977fd99725f1db4007ccb2928dbb4e90d06cc86",
        "v6.0.10",
    ),
}

USES_LINE_RE = re.compile(
    r"^\s*uses:\s+(?P<action>[^@\s]+)@(?P<sha>[0-9a-f]{40})"
    r"\s+#\s+(?P<version>v\d+(?:\.\d+){0,2})\s*$"
)


def _load_ci_workflow() -> dict[str, object]:
    return _as_dict(yaml.safe_load(CI_WORKFLOW_PATH.read_text(encoding="utf-8")))


def _as_dict(value: object) -> dict[str, object]:
    assert isinstance(value, dict)
    return cast("dict[str, object]", value)


def _as_list(value: object) -> list[object]:
    assert isinstance(value, list)
    return cast("list[object]", value)


def _as_str(value: object) -> str:
    assert isinstance(value, str)
    return value


def test_ci_actions_use_exact_immutable_node24_release_pins() -> None:
    workflow = CI_WORKFLOW_PATH.read_text(encoding="utf-8")
    uses_lines = [
        line for line in workflow.splitlines() if line.lstrip().startswith("uses:")
    ]
    observed_actions: set[str] = set()

    for line in uses_lines:
        match = USES_LINE_RE.fullmatch(line)
        assert match is not None, (
            f"action must use a full SHA and version comment: {line}"
        )
        action = match.group("action")
        assert action in EXPECTED_ACTION_PINS, f"unexpected CI action: {action}"
        assert (match.group("sha"), match.group("version")) == EXPECTED_ACTION_PINS[
            action
        ]
        observed_actions.add(action)

    assert observed_actions == set(EXPECTED_ACTION_PINS)


def test_ci_has_independent_python_and_docs_jobs() -> None:
    workflow = _load_ci_workflow()
    jobs = _as_dict(workflow["jobs"])
    assert set(jobs) == {"lint-and-test", "docs"}
    assert "needs" not in _as_dict(jobs["docs"])


def test_docs_ci_uses_pinned_runtime_frozen_install_and_full_assurance() -> None:
    workflow = _load_ci_workflow()
    jobs = _as_dict(workflow["jobs"])
    docs_job = _as_dict(jobs["docs"])
    assert docs_job["timeout-minutes"] == 20
    defaults = _as_dict(docs_job["defaults"])
    run_defaults = _as_dict(defaults["run"])
    assert run_defaults["working-directory"] == "docs"

    steps = [_as_dict(step) for step in _as_list(docs_job["steps"])]
    named_steps = {
        _as_str(step["name"]): step
        for step in steps
        if isinstance(step.get("name"), str)
    }
    expected_order = [
        "Install docs dependencies",
        "Test docs server contracts",
        "Assert docs type generation starts clean",
        "Generate and typecheck docs",
        "Verify generated docs type surfaces",
        "Build docs",
    ]
    indices = [steps.index(named_steps[name]) for name in expected_order]
    assert indices == sorted(indices)
    assert named_steps["Install docs dependencies"]["run"] == (
        "pnpm install --frozen-lockfile"
    )
    assert named_steps["Test docs server contracts"]["run"] == "pnpm test"
    assert named_steps["Generate and typecheck docs"]["run"] == "pnpm typecheck"
    assert named_steps["Build docs"]["run"] == "pnpm build"
    clean_state_command = _as_str(
        named_steps["Assert docs type generation starts clean"]["run"]
    )
    assert clean_state_command.splitlines() == [
        "test ! -e .next",
        "test ! -e .source",
    ]
    generated_surface_command = _as_str(
        named_steps["Verify generated docs type surfaces"]["run"]
    )
    assert generated_surface_command.splitlines() == [
        "test -s .next/types/routes.d.ts",
        "test -s .next/types/root-params.d.ts",
        "test -s .next/types/validator.ts",
        "test -s .source/server.ts",
    ]

    setup_pnpm_index, setup_pnpm = next(
        (index, step)
        for index, step in enumerate(steps)
        if _as_str(step.get("uses", "")).startswith("pnpm/action-setup@")
    )
    setup_node = next(
        step
        for step in steps
        if _as_str(step.get("uses", "")).startswith("actions/setup-node@")
    )
    setup_node_index = steps.index(setup_node)
    assert setup_pnpm_index < setup_node_index
    setup_pnpm_with = _as_dict(setup_pnpm["with"])
    setup_node_with = _as_dict(setup_node["with"])
    assert setup_pnpm_with["package_json_file"] == "docs/package.json"
    assert setup_node_with["node-version"] == "24"
    assert setup_node_with["cache"] == "pnpm"
    assert setup_node_with["cache-dependency-path"] == "docs/pnpm-lock.yaml"


def test_docs_typecheck_generates_owned_types_and_allows_only_esbuild() -> None:
    package = _as_dict(json.loads(DOCS_PACKAGE_PATH.read_text(encoding="utf-8")))
    scripts = _as_dict(package["scripts"])
    assert scripts["typegen"] == "fumadocs-mdx && next typegen"
    assert scripts["typecheck"] == ("pnpm typegen && tsc --noEmit --incremental false")

    workspace = yaml.safe_load(DOCS_WORKSPACE_PATH.read_text(encoding="utf-8"))
    assert workspace == {"packages": ["."], "allowBuilds": {"esbuild": True}}
