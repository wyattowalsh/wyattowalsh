from __future__ import annotations

import json
from pathlib import Path
from subprocess import CompletedProcess

import pytest
from typer.testing import CliRunner

pytest.importorskip(
    "numpy",
    reason="living-art CLI rehearsal requires numpy-backed imports",
)

import scripts.cli.generate as generate_cmd  # noqa: E402
from scripts.cli import app  # noqa: E402


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def _history_payload() -> dict:
    return {
        "account_created": "2020-01-01T00:00:00Z",
        "repos": [
            {"name": "aurora-core", "date": "2024-01-10T00:00:00Z"},
            {"name": "ridge-lab", "date": "2024-07-05T00:00:00Z"},
        ],
        "stars": [{"date": "2025-01-10T00:00:00Z"}],
        "forks": [{"date": "2025-02-12T00:00:00Z"}],
        "contributions_monthly": {"2025-01": 18, "2025-02": 24},
        "current_metrics": {"label": "rehearsal", "repos": []},
    }


def _metrics_payload() -> dict:
    return {
        "label": "Rehearsal",
        "languages": {"Python": 1200, "Go": 400},
        "top_repos": [
            {
                "name": "aurora-core",
                "language": "Python",
                "stars": 12,
                "forks": 3,
                "topics": ["agents"],
                "description": "Primary repo",
                "updated_at": "2025-03-10T12:00:00Z",
            }
        ],
        "contributions_calendar": [{"date": "2025-01-01", "count": 2}],
    }


def _write_svg(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
            '<rect width="100" height="100" fill="#111827"/></svg>'
        ),
        encoding="utf-8",
    )


def _write_gif(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"GIF89a")


def test_living_art_cli_rehearsal_generates_all_preview_surfaces(
    runner: CliRunner, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        generate_cmd,
        "_load_project_config",
        lambda *_args, **_kwargs: None,
    )

    history_path = tmp_path / "history.json"
    metrics_path = tmp_path / "metrics.json"
    _write_json(history_path, _history_payload())
    _write_json(metrics_path, _metrics_payload())

    def _stub_subprocess_run(
        command: list[str],
        check: bool = True,
    ) -> CompletedProcess[str]:
        del check
        out_dir = tmp_path / ".github" / "assets" / "img"
        if "--svg" in command:
            _write_svg(out_dir / "inkgarden-growth-animated.svg")
            _write_svg(out_dir / "topo-growth-animated.svg")
        else:
            _write_gif(out_dir / "inkgarden-growth.gif")
            _write_gif(out_dir / "topo-growth.gif")
        return CompletedProcess(command, 0)

    def _stub_render_timelapse(
        history: dict,
        metrics: dict,
        *,
        styles: list[str] | None = None,
        max_frames: int = 150,
        size: int = 400,
        owner: str = "wyattowalsh",
        workers: int = 4,
    ) -> list[Path]:
        del history, metrics, styles, max_frames, size, owner, workers
        out_dir = tmp_path / ".github" / "assets" / "img"
        outputs = [
            out_dir / "living-inkgarden.gif",
            out_dir / "living-topo.gif",
        ]
        for path in outputs:
            _write_gif(path)
        return outputs

    monkeypatch.setattr(generate_cmd.subprocess, "run", _stub_subprocess_run)
    monkeypatch.setattr(
        "scripts.art.timelapse.render_timelapse",
        _stub_render_timelapse,
    )

    living_art = runner.invoke(
        app,
        [
            "generate",
            "living-art",
            "--metrics-path",
            str(metrics_path),
            "--history-path",
            str(history_path),
            "--profile",
            "rehearsal",
        ],
    )
    timelapse = runner.invoke(
        app,
        [
            "generate",
            "timelapse",
            "--metrics-path",
            str(metrics_path),
            "--history-path",
            str(history_path),
            "--profile",
            "rehearsal",
            "--max-frames",
            "6",
            "--size",
            "96",
        ],
    )

    assert living_art.exit_code == 0, living_art.stdout
    assert timelapse.exit_code == 0, timelapse.stdout

    output_dir = tmp_path / ".github" / "assets" / "img"
    expected_outputs = [
        output_dir / "inkgarden-growth-animated.svg",
        output_dir / "topo-growth-animated.svg",
        output_dir / "inkgarden-growth.gif",
        output_dir / "topo-growth.gif",
        output_dir / "living-inkgarden.gif",
        output_dir / "living-topo.gif",
        output_dir / "living-art-manifest.json",
        output_dir / "living-art-preview.html",
    ]

    for path in expected_outputs:
        assert path.exists(), (
            f"Expected rehearsal artifact was not generated: {path}"
        )

    manifest = json.loads(
        (output_dir / "living-art-manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["total_assets"] == 6
    assert manifest["counts"]["source_svg"] == 2
    assert manifest["counts"]["compatibility_gif"] == 2
    assert manifest["counts"]["timelapse_gif"] == 2


def test_living_art_svg_only_skips_compatibility_gifs(
    runner: CliRunner, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        generate_cmd,
        "_load_project_config",
        lambda *_args, **_kwargs: None,
    )

    history_path = tmp_path / "history.json"
    metrics_path = tmp_path / "metrics.json"
    _write_json(history_path, _history_payload())
    _write_json(metrics_path, _metrics_payload())

    calls: list[list[str]] = []

    def _stub_subprocess_run(
        command: list[str],
        check: bool = True,
    ) -> CompletedProcess[str]:
        del check
        calls.append(command)
        out_dir = tmp_path / ".github" / "assets" / "img"
        if "--svg" in command:
            _write_svg(out_dir / "inkgarden-growth-animated.svg")
            _write_svg(out_dir / "topo-growth-animated.svg")
        else:
            _write_gif(out_dir / "inkgarden-growth.gif")
            _write_gif(out_dir / "topo-growth.gif")
        return CompletedProcess(command, 0)

    monkeypatch.setattr(generate_cmd.subprocess, "run", _stub_subprocess_run)

    result = runner.invoke(
        app,
        [
            "generate",
            "living-art",
            "--metrics-path",
            str(metrics_path),
            "--history-path",
            str(history_path),
            "--profile",
            "rehearsal",
            "--svg-only",
        ],
    )

    assert result.exit_code == 0, result.stdout
    assert len(calls) == 1
    assert "--svg" in calls[0]

    output_dir = tmp_path / ".github" / "assets" / "img"
    assert (output_dir / "inkgarden-growth-animated.svg").exists()
    assert (output_dir / "topo-growth-animated.svg").exists()
    assert (output_dir / "living-art-manifest.json").exists()
    assert (output_dir / "living-art-preview.html").exists()
    assert not (output_dir / "inkgarden-growth.gif").exists()
    assert not (output_dir / "topo-growth.gif").exists()
