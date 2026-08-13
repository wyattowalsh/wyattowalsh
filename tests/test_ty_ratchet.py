"""Contracts for the structured ``ty`` diagnostic ratchet."""

from __future__ import annotations

from collections import Counter
from subprocess import CompletedProcess
from unittest.mock import patch

from scripts.quality import ty_ratchet
from scripts.quality.ty_ratchet import evaluate_warning_ratchet


def _diagnostic(path: str, rule: str, severity: str = "minor") -> dict:
    return {
        "check_name": rule,
        "severity": severity,
        "location": {"path": path},
    }


def test_ty_ratchet_allows_warning_debt_to_decrease() -> None:
    baseline = Counter({("scripts/example.py", "example-rule"): 2})

    assert (
        evaluate_warning_ratchet(
            [_diagnostic("scripts/example.py", "example-rule")], baseline
        )
        == []
    )


def test_ty_ratchet_rejects_new_or_increased_warnings() -> None:
    baseline = Counter({("scripts/example.py", "example-rule"): 1})

    failures = evaluate_warning_ratchet(
        [
            _diagnostic("scripts/example.py", "example-rule"),
            _diagnostic("scripts/example.py", "example-rule"),
            _diagnostic("scripts/new.py", "new-rule"),
        ],
        baseline,
    )

    assert failures == [
        "warning regression: scripts/example.py [example-rule] observed=2 allowed=1",
        "warning regression: scripts/new.py [new-rule] observed=1 allowed=0",
    ]


def test_ty_ratchet_rejects_every_configured_error() -> None:
    failures = evaluate_warning_ratchet(
        [_diagnostic("scripts/example.py", "example-rule", severity="major")],
        Counter(),
    )

    assert failures == ["configured error: scripts/example.py [example-rule]"]


def test_ty_ratchet_fails_closed_when_the_tool_crashes(capsys) -> None:
    with (
        patch.object(
            ty_ratchet.subprocess,
            "run",
            return_value=CompletedProcess(
                args=["ty"], returncode=2, stdout="[]", stderr="ty crashed"
            ),
        ),
        patch.object(ty_ratchet, "_load_baseline", return_value=Counter()),
    ):
        assert ty_ratchet.main() == 2

    captured = capsys.readouterr()
    assert "exited 2" in captured.err
    assert "ty crashed" in captured.err
