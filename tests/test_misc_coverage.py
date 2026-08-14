"""Focused branch coverage for compact quality, HTTP, CLI, and art helpers."""

from __future__ import annotations

import builtins
import importlib
import json
import random
import runpy
from collections import Counter
from pathlib import Path
from subprocess import CompletedProcess
from types import SimpleNamespace
from typing import Any

import pytest

from scripts import _github_http, banner_patterns
from scripts import skills as skills_module
from scripts.art import optimize
from scripts.cli import _display, dev
from scripts.config import ProjectConfig, SkillsSettings
from scripts.quality import ty_ratchet
from scripts.skills import SkillsBadgeGenerator


def _diagnostic(path: str, rule: str, severity: str = "minor") -> dict[str, Any]:
    return {
        "check_name": rule,
        "severity": severity,
        "location": {"path": path},
    }


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        ({"schema_version": 2, "warning_counts": []}, "unsupported schema"),
        ({"schema_version": 1, "warning_counts": ["bad"]}, "non-object"),
        (
            {
                "schema_version": 1,
                "warning_counts": [{"path": "x.py", "rule": "r", "count": 0}],
            },
            "invalid entry",
        ),
    ],
)
def test_ty_ratchet_rejects_malformed_baselines(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    payload: dict[str, Any],
    message: str,
) -> None:
    baseline = tmp_path / "baseline.json"
    baseline.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setattr(ty_ratchet, "BASELINE_PATH", baseline)

    with pytest.raises(ValueError, match=message):
        ty_ratchet._load_baseline()


def test_ty_ratchet_loads_valid_baseline(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    baseline = tmp_path / "baseline.json"
    baseline.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "warning_counts": [
                    {"path": "scripts/a.py", "rule": "sample", "count": 2}
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(ty_ratchet, "BASELINE_PATH", baseline)

    assert ty_ratchet._load_baseline() == Counter({("scripts/a.py", "sample"): 2})


def test_ty_ratchet_rejects_diagnostic_without_path_or_rule() -> None:
    with pytest.raises(ValueError, match="without a path/rule"):
        ty_ratchet.evaluate_warning_ratchet([{"severity": "minor"}], Counter())


@pytest.mark.parametrize(
    ("stdout", "returncode", "expected", "stderr"),
    [
        ("{}", 0, 2, "not a list"),
        ("not-json", 0, 2, "could not evaluate"),
        (
            json.dumps([_diagnostic("scripts/new.py", "new-rule")]),
            1,
            1,
            "warning regression",
        ),
    ],
)
def test_ty_ratchet_main_failure_modes(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    stdout: str,
    returncode: int,
    expected: int,
    stderr: str,
) -> None:
    result = CompletedProcess(["ty"], returncode, stdout=stdout, stderr="tool detail")
    monkeypatch.setattr(ty_ratchet.subprocess, "run", lambda *_a, **_k: result)
    monkeypatch.setattr(ty_ratchet, "_load_baseline", lambda: Counter())

    assert ty_ratchet.main() == expected
    assert stderr in capsys.readouterr().err


def test_ty_ratchet_main_reports_success(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    diagnostics = [_diagnostic("scripts/a.py", "sample")]
    result = CompletedProcess(["ty"], 0, stdout=json.dumps(diagnostics), stderr="")
    monkeypatch.setattr(ty_ratchet.subprocess, "run", lambda *_a, **_k: result)
    monkeypatch.setattr(
        ty_ratchet,
        "_load_baseline",
        lambda: Counter({("scripts/a.py", "sample"): 1}),
    )

    assert ty_ratchet.main() == 0
    assert "1/1 allowed warnings" in capsys.readouterr().out


def test_github_url_parser_wraps_invalid_ipv6() -> None:
    with pytest.raises(ValueError, match="Invalid URL"):
        _github_http._assert_allowed_url("https://[invalid")


def test_graphql_includes_variables(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}

    class Response:
        headers: dict[str, str] = {}

        def __enter__(self) -> Response:
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        def read(self) -> bytes:
            return b'{"data": {"ok": true}}'

    def fake_open(request: Any) -> Response:
        captured["body"] = json.loads(request.data)
        return Response()

    monkeypatch.setattr(_github_http, "_urlopen", fake_open)

    assert _github_http._graphql("query", "token", variables={"name": "repo"}) == {
        "data": {"ok": True}
    }
    assert captured["body"]["variables"] == {"name": "repo"}


def test_paginate_stops_at_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        _github_http,
        "_get",
        lambda *_a, **_k: ([1], {"Link": '<https://api.github.com/next>; rel="next"'}),
    )

    assert _github_http._paginate_rest(
        "https://api.github.com/first", None, max_pages=1
    ) == [1]


def test_paginate_rejects_non_list_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(_github_http, "_get", lambda *_a, **_k: ({"id": 1}, {}))

    assert _github_http._paginate_rest("https://api.github.com/first", None) == []


def test_new_report_dir_is_unique_and_created(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(dev.uuid, "uuid4", lambda: SimpleNamespace(hex="fixed"))

    report_dir = dev._new_test_report_dir()

    assert report_dir == Path("logs/runs/fixed")
    assert (tmp_path / report_dir).is_dir()


def test_clean_removes_optional_venv_and_generated_assets(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".venv").mkdir()
    asset_dir = tmp_path / ".github/assets/img"
    asset_dir.mkdir(parents=True)
    generated = asset_dir / "banner-test.svg"
    generated.write_text("generated", encoding="utf-8")
    retained = asset_dir / "other.svg"
    retained.write_text("retained", encoding="utf-8")

    dev.clean(venv=True, generated=True)

    assert not (tmp_path / ".venv").exists()
    assert not generated.exists()
    assert retained.exists()


def test_docs_command_fails_without_docs_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)

    with pytest.raises(Exception) as error:
        dev.docs()

    assert getattr(error.value, "exit_code", None) == 1


def test_docs_command_runs_from_docs_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "docs").mkdir()
    calls: list[tuple[list[str], str | None]] = []
    monkeypatch.setattr(
        dev,
        "_run",
        lambda command, *, cwd=None, **_kwargs: calls.append((command, cwd)),
    )

    dev.docs()

    assert calls == [(["pnpm", "dev"], "docs")]


def test_display_import_fallback_and_yaml_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    real_import = builtins.__import__

    def reject_yaml(name: str, *args: Any, **kwargs: Any) -> Any:
        if name == "yaml":
            raise ImportError("no yaml")
        return real_import(name, *args, **kwargs)

    with monkeypatch.context() as scoped:
        scoped.setattr(builtins, "__import__", reject_yaml)
        assert importlib.reload(_display).yaml is None
    importlib.reload(_display)

    class BrokenYaml:
        YAMLError = RuntimeError

        @staticmethod
        def dump(*_args: Any, **_kwargs: Any) -> str:
            raise RuntimeError("broken")

    printed: list[object] = []
    monkeypatch.setattr(_display, "yaml", BrokenYaml)
    monkeypatch.setattr(_display, "_print", printed.append)
    _display.display_config(ProjectConfig(), _display.OutputFormat.YAML)
    assert len(printed) == 1


def test_banner_pattern_enum_contract() -> None:
    assert {pattern.value for pattern in banner_patterns.PatternType} == {
        "lorenz",
        "neural",
        "flow",
        "micro",
        "aizawa",
        "clifford",
    }


def test_skills_helpers_cover_empty_and_resolved_escape(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "root"
    outside = tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    (root / "link").symlink_to(outside, target_is_directory=True)
    monkeypatch.setattr(skills_module, "_REPO_ROOT", root)

    with pytest.raises(ValueError, match="escapes repository root"):
        skills_module._resolve_repo_logo_path("link/icon.svg")
    assert SkillsBadgeGenerator(SkillsSettings())._render_skills([]) == ""


def test_art_optimizer_helpers_and_singleton_solver_shortcuts() -> None:
    rng = random.Random(7)
    points = optimize._random_art_positions(3, 100.0, 80.0, rng)
    assert len(points) == 3
    assert all(8.0 <= x <= 92.0 and 6.4 <= y <= 73.6 for x, y in points)

    singleton = [(5.0, 6.0)]
    for solver in (
        optimize._art_solve_grey_wolf,
        optimize._art_solve_whale,
        optimize._art_solve_firefly,
        optimize._art_solve_flower_pollination,
        optimize._art_solve_differential_evolution,
    ):
        assert solver(singleton, [1.0], 100.0, 100.0) == singleton

    assert (
        optimize.constellation_layout_cost(
            [(10.0, 10.0), (12.0, 12.0)],
            [0, 1],
            100.0,
            100.0,
            inter_spacing=20.0,
        )
        > 0
    )
    assert optimize._margin_score([(100.0, 0.0)], 100.0, 100.0) > 0


def test_art_optimizer_auto_selects_large_pso(monkeypatch: pytest.MonkeyPatch) -> None:
    positions = [(float(index), float(index)) for index in range(50)]
    seen: dict[str, Any] = {}

    def fake_pso(*args: Any, **kwargs: Any) -> list[tuple[float, float]]:
        seen["args"] = args
        seen["kwargs"] = kwargs
        return positions

    monkeypatch.setattr(optimize, "optimize_layout_pso", fake_pso)
    monkeypatch.setitem(optimize._SOLVER_MAP, "pso", fake_pso)

    assert (
        optimize.optimize_placement(
            positions, [1.0] * len(positions), 100.0, 100.0, max_iter=1
        )
        == positions
    )
    assert seen["kwargs"]["iterations"] == 1


def test_art_optimizer_rejects_unknown_solver() -> None:
    with pytest.raises(ValueError, match="Unknown solver"):
        optimize.optimize_placement(
            [(0.0, 0.0), (1.0, 1.0)],
            [1.0, 1.0],
            10.0,
            10.0,
            solver="missing",
        )


def test_ty_ratchet_module_entrypoint(monkeypatch: pytest.MonkeyPatch) -> None:
    result = CompletedProcess(["ty"], 0, stdout="[]", stderr="")
    monkeypatch.setattr(ty_ratchet.subprocess, "run", lambda *_a, **_k: result)

    with pytest.raises(SystemExit, match="0"):
        runpy.run_path(str(ty_ratchet.__file__), run_name="__main__")
