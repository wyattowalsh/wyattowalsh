"""Enforce the checked-in ``ty`` diagnostic non-regression baseline."""

from __future__ import annotations

import json
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BASELINE_PATH = Path(__file__).with_name("ty_warning_baseline.json")
CHECK_PATHS = ("scripts", "tests")


def _diagnostic_key(diagnostic: dict[str, Any]) -> tuple[str, str]:
    location = diagnostic.get("location")
    path = location.get("path") if isinstance(location, dict) else None
    rule = diagnostic.get("check_name")
    if not isinstance(path, str) or not isinstance(rule, str):
        raise ValueError("ty emitted a diagnostic without a path/rule key")
    return path, rule


def _warning_counts(diagnostics: list[dict[str, Any]]) -> Counter[tuple[str, str]]:
    return Counter(
        _diagnostic_key(diagnostic)
        for diagnostic in diagnostics
        if diagnostic.get("severity") == "minor"
    )


def _load_baseline() -> Counter[tuple[str, str]]:
    raw = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    entries = raw.get("warning_counts")
    if raw.get("schema_version") != 1 or not isinstance(entries, list):
        raise ValueError("ty warning baseline has an unsupported schema")
    baseline: Counter[tuple[str, str]] = Counter()
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError("ty warning baseline contains a non-object entry")
        path = entry.get("path")
        rule = entry.get("rule")
        count = entry.get("count")
        if (
            not isinstance(path, str)
            or not isinstance(rule, str)
            or not isinstance(count, int)
            or count < 1
        ):
            raise ValueError("ty warning baseline contains an invalid entry")
        baseline[path, rule] = count
    return baseline


def evaluate_warning_ratchet(
    diagnostics: list[dict[str, Any]],
    baseline: Counter[tuple[str, str]],
) -> list[str]:
    """Return deterministic failures for errors or warning-count regressions."""
    errors = [
        _diagnostic_key(diagnostic)
        for diagnostic in diagnostics
        if diagnostic.get("severity") != "minor"
    ]
    failures = [f"configured error: {path} [{rule}]" for path, rule in errors]
    current = _warning_counts(diagnostics)
    for (path, rule), count in sorted(current.items()):
        allowed = baseline.get((path, rule), 0)
        if count > allowed:
            failures.append(
                f"warning regression: {path} [{rule}] "
                f"observed={count} allowed={allowed}"
            )
    return failures


def main() -> int:
    result = subprocess.run(
        [
            "uv",
            "run",
            "--",
            "ty",
            "check",
            *CHECK_PATHS,
            "--output-format",
            "gitlab",
            "--color",
            "never",
        ],
        cwd=PROJECT_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    try:
        diagnostics = json.loads(result.stdout)
        if not isinstance(diagnostics, list):
            raise ValueError("ty JSON output is not a list")
        baseline = _load_baseline()
        failures = evaluate_warning_ratchet(diagnostics, baseline)
    except (json.JSONDecodeError, OSError, ValueError) as error:
        print(f"ty ratchet could not evaluate diagnostics: {error}", file=sys.stderr)
        if result.stderr:
            print(result.stderr.rstrip(), file=sys.stderr)
        return 2

    if result.returncode != 0 and not failures:
        print(
            f"ty exited {result.returncode} without a structured diagnostic failure",
            file=sys.stderr,
        )
        if result.stderr:
            print(result.stderr.rstrip(), file=sys.stderr)
        return 2

    if failures:
        print("ty diagnostic ratchet failed:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    warnings = sum(_warning_counts(diagnostics).values())
    baseline_warnings = sum(baseline.values())
    print(
        f"ty diagnostic ratchet passed: 0 errors, {warnings}/{baseline_warnings} "
        "allowed warnings"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
