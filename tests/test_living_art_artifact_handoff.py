"""Executable rehearsal of the living-art GitHub Actions artifact handoff."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, cast

import pytest
import yaml
from PIL import Image

from scripts.art.artifacts import (
    GALLERY_FILENAME,
    LIVING_ART_BYTE_BUDGETS,
    MANIFEST_FILENAME,
    sync_living_art_artifacts,
)

WORKFLOW_PATH = Path(".github/workflows/profile-updater.yml").resolve()
PROJECT_ROOT = WORKFLOW_PATH.parents[2]
CANONICAL_NAMES = tuple(sorted(LIVING_ART_BYTE_BUDGETS))
STAGE_STEP = "Stage exact-six living-art artifact"
PUBLISH_STEP = "Publish and validate living-art artifact"


def _workflow_jobs() -> dict[str, dict[str, Any]]:
    raw_workflow: Any = yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))
    if not isinstance(raw_workflow, dict):
        raise AssertionError("profile updater workflow must be a mapping")
    raw_jobs = raw_workflow.get("jobs")
    if not isinstance(raw_jobs, dict):
        raise AssertionError("profile updater workflow must define jobs")
    return cast(dict[str, dict[str, Any]], raw_jobs)


def _workflow_step(job_name: str, step_name: str) -> dict[str, Any]:
    raw_steps = _workflow_jobs()[job_name].get("steps")
    if not isinstance(raw_steps, list):
        raise AssertionError(f"{job_name} must define steps")
    for raw_step in raw_steps:
        if isinstance(raw_step, dict) and raw_step.get("name") == step_name:
            return cast(dict[str, Any], raw_step)
    raise AssertionError(f"workflow step not found: {job_name} / {step_name}")


def _step_script(job_name: str, step_name: str) -> str:
    script = _workflow_step(job_name, step_name).get("run")
    if not isinstance(script, str):
        raise AssertionError(
            f"workflow step has no shell body: {job_name} / {step_name}"
        )
    return script


def _inline_python_source(job_name: str, step_name: str) -> str:
    match = re.fullmatch(
        r"uv run python - <<'PY'\n(?P<source>.*)\nPY\n?",
        _step_script(job_name, step_name),
        flags=re.DOTALL,
    )
    assert match is not None, f"{job_name} / {step_name} must be inline Python"
    return match.group("source")


def _run_inline_python(
    job_name: str,
    step_name: str,
    *,
    cwd: Path,
    runner_temp: Path,
) -> subprocess.CompletedProcess[str]:
    cwd.mkdir(parents=True, exist_ok=True)
    runner_temp.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["RUNNER_TEMP"] = str(runner_temp)
    existing_pythonpath = env.get("PYTHONPATH")
    env["PYTHONPATH"] = (
        f"{PROJECT_ROOT}{os.pathsep}{existing_pythonpath}"
        if existing_pythonpath
        else str(PROJECT_ROOT)
    )
    return subprocess.run(
        [sys.executable, "-c", _inline_python_source(job_name, step_name)],
        cwd=cwd,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )


def _write_test_gif(
    path: Path,
    *,
    color_index: int,
    size: tuple[int, int] = (400, 400),
    loop: int = 0,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    first = Image.new(
        "RGB",
        size,
        color=((37 * color_index) % 255, 40, 180),
    )
    second = Image.new(
        "RGB",
        size,
        color=(30, (53 * color_index) % 255, 210),
    )
    first.save(
        path,
        format="GIF",
        save_all=True,
        append_images=[second],
        duration=[12_000, 12_000],
        loop=loop,
    )


def _generate_fleet(repo: Path) -> tuple[Path, Path]:
    output_dir = repo / ".github" / "assets" / "img"
    public_dir = repo / "docs" / "public" / "showcase"
    for index, name in enumerate(CANONICAL_NAMES, start=1):
        _write_test_gif(output_dir / name, color_index=index)
    sync_living_art_artifacts(output_dir, public_surface_dir=public_dir)
    return output_dir, public_dir


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _round_trip_artifact(stage: Path, destination: Path) -> Path:
    """Approximate upload/download with a ZIP that preserves relative paths."""
    archive_base = stage.parent / "living-art-stage-upload"
    archive = Path(shutil.make_archive(str(archive_base), "zip", root_dir=stage))
    downloaded = destination / "living-art-stage"
    downloaded.mkdir(parents=True)
    shutil.unpack_archive(archive, downloaded)
    return downloaded


def _stable_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in manifest.items()
        if key not in {"generated_at", "output_dir"}
    }


def _managed_snapshot(repo: Path) -> dict[str, str]:
    snapshot: dict[str, str] = {}
    for relative_root in (
        Path(".github/assets/img"),
        Path("docs/public/showcase"),
    ):
        root = repo / relative_root
        if not root.exists():
            continue
        for path in sorted(root.rglob("*")):
            relative = path.relative_to(repo).as_posix()
            if path.is_symlink():
                snapshot[relative] = f"symlink:{os.readlink(path)}"
            elif path.is_file():
                snapshot[relative] = _sha256(path)
            else:
                snapshot[relative] = "directory"
    return snapshot


def _seed_stale_destinations(repo: Path) -> None:
    for surface_index, relative_root in enumerate(
        (Path(".github/assets/img"), Path("docs/public/showcase")),
        start=1,
    ):
        root = repo / relative_root
        for asset_index, name in enumerate(CANONICAL_NAMES, start=1):
            _write_test_gif(
                root / name,
                color_index=50 + surface_index * 10 + asset_index,
            )
        _write_test_gif(root / "living-unknown.gif", color_index=90 + surface_index)
        (root / MANIFEST_FILENAME).write_text("stale manifest", encoding="utf-8")
        (root / GALLERY_FILENAME).write_text("stale gallery", encoding="utf-8")
        (root / "preserve.txt").write_text(
            f"unmanaged sentinel {surface_index}", encoding="utf-8"
        )


def _stage_producer_fleet(
    producer_repo: Path,
    producer_runner: Path,
) -> Path:
    result = _run_inline_python(
        "generate-event-art",
        STAGE_STEP,
        cwd=producer_repo,
        runner_temp=producer_runner,
    )
    assert result.returncode == 0, result.stderr
    return producer_runner / "living-art-stage"


def test_exact_six_gif_artifact_round_trip_regenerates_all_derived_surfaces(
    tmp_path: Path,
) -> None:
    producer_repo = tmp_path / "producer-checkout"
    producer_output, _producer_public = _generate_fleet(producer_repo)
    expected_hashes = {
        name: _sha256(producer_output / name) for name in CANONICAL_NAMES
    }

    producer_runner = tmp_path / "producer-runner"
    stage = _stage_producer_fleet(producer_repo, producer_runner)
    assert {path.name for path in stage.iterdir()} == set(CANONICAL_NAMES)
    assert all(path.is_file() and not path.is_symlink() for path in stage.iterdir())
    assert MANIFEST_FILENAME not in {path.name for path in stage.iterdir()}
    assert GALLERY_FILENAME not in {path.name for path in stage.iterdir()}

    finalizer_runner = tmp_path / "finalizer-runner"
    _round_trip_artifact(stage, finalizer_runner)
    finalizer_repo = tmp_path / "finalizer-checkout"
    _seed_stale_destinations(finalizer_repo)
    result = _run_inline_python(
        "finalize",
        PUBLISH_STEP,
        cwd=finalizer_repo,
        runner_temp=finalizer_runner,
    )
    assert result.returncode == 0, result.stderr
    assert "Living-art publication validation passed: 6 assets" in result.stdout

    output_dir = finalizer_repo / ".github" / "assets" / "img"
    public_dir = finalizer_repo / "docs" / "public" / "showcase"
    for surface in (output_dir, public_dir):
        assert {path.name for path in surface.glob("living-*.gif")} == set(
            CANONICAL_NAMES
        )
        assert (surface / "preserve.txt").is_file()
        for name in CANONICAL_NAMES:
            assert _sha256(surface / name) == expected_hashes[name]

    primary_manifest = json.loads(
        (output_dir / MANIFEST_FILENAME).read_text(encoding="utf-8")
    )
    public_manifest = json.loads(
        (public_dir / MANIFEST_FILENAME).read_text(encoding="utf-8")
    )
    assert _stable_manifest(primary_manifest) == _stable_manifest(public_manifest)
    assert primary_manifest["total_assets"] == len(CANONICAL_NAMES)
    assert (output_dir / GALLERY_FILENAME).read_bytes() == (
        public_dir / GALLERY_FILENAME
    ).read_bytes()


def test_producer_rejects_incomplete_fleet_without_materializing_artifact(
    tmp_path: Path,
) -> None:
    producer_repo = tmp_path / "producer-checkout"
    output_dir, _public_dir = _generate_fleet(producer_repo)
    (output_dir / "living-topo.gif").unlink()
    producer_runner = tmp_path / "producer-runner"

    result = _run_inline_python(
        "generate-event-art",
        STAGE_STEP,
        cwd=producer_repo,
        runner_temp=producer_runner,
    )

    assert result.returncode != 0
    assert "living-art producer source inventory mismatch" in result.stderr
    assert "living-topo.gif" in result.stderr
    assert not (producer_runner / "living-art-stage").exists()


@pytest.mark.parametrize(
    "failure",
    ["missing", "unexpected", "corrupt", "oversized", "wrong-size", "wrong-loop"],
)
def test_finalizer_rejects_invalid_stage_before_destination_mutation(
    tmp_path: Path,
    failure: str,
) -> None:
    producer_repo = tmp_path / "producer-checkout"
    _generate_fleet(producer_repo)
    stage = _stage_producer_fleet(producer_repo, tmp_path / "producer-runner")
    finalizer_runner = tmp_path / "finalizer-runner"
    downloaded = _round_trip_artifact(stage, finalizer_runner)
    target = downloaded / "living-lenia.gif"

    if failure == "missing":
        target.unlink()
    elif failure == "unexpected":
        _write_test_gif(downloaded / "living-unknown.gif", color_index=99)
    elif failure == "corrupt":
        target.write_bytes(b"not-a-gif")
    elif failure == "oversized":
        excess = LIVING_ART_BYTE_BUDGETS[target.name] + 1 - target.stat().st_size
        with target.open("ab") as stream:
            stream.write(b"\0" * excess)
    elif failure == "wrong-size":
        _write_test_gif(target, color_index=99, size=(32, 32))
    else:
        _write_test_gif(target, color_index=99, loop=1)

    finalizer_repo = tmp_path / "finalizer-checkout"
    _seed_stale_destinations(finalizer_repo)
    before = _managed_snapshot(finalizer_repo)
    result = _run_inline_python(
        "finalize",
        PUBLISH_STEP,
        cwd=finalizer_repo,
        runner_temp=finalizer_runner,
    )

    assert result.returncode != 0
    assert _managed_snapshot(finalizer_repo) == before


def test_handoff_steps_precede_upload_and_the_sole_git_writer() -> None:
    jobs = _workflow_jobs()
    producer_steps = cast(list[dict[str, Any]], jobs["generate-event-art"]["steps"])
    producer_names = [step.get("name") for step in producer_steps]
    assert producer_names.index(STAGE_STEP) < producer_names.index(
        "Upload living-art staging bundle"
    )

    finalizer_steps = cast(list[dict[str, Any]], jobs["finalize"]["steps"])
    finalizer_names = [step.get("name") for step in finalizer_steps]
    assert finalizer_names.index("Install dependencies") < finalizer_names.index(
        PUBLISH_STEP
    )
    assert finalizer_names.index(PUBLISH_STEP) < finalizer_names.index(
        "Commit and push owned profile artifacts"
    )


def test_finalize_stages_tracked_unexpected_living_gif_deletions(
    tmp_path: Path,
) -> None:
    """The finalizer's owned pathspecs must include cleanup deletions."""
    commit_script = _step_script(
        "finalize",
        "Commit and push owned profile artifacts",
    )
    art_array = re.search(
        r"(?ms)^art_files=\(\n.*?^\)$",
        commit_script,
    )
    assert art_array is not None
    assert 'git add -A -- "${owned_files[@]}"' in commit_script

    repo = tmp_path / "repo"
    primary = repo / ".github" / "assets" / "img" / "living-unknown.gif"
    public = repo / "docs" / "public" / "showcase" / "living-unknown.gif"
    for path in (primary, public):
        _write_test_gif(path, color_index=99)
        path.parent.joinpath(MANIFEST_FILENAME).write_text(
            "fixture manifest",
            encoding="utf-8",
        )
        path.parent.joinpath(GALLERY_FILENAME).write_text(
            "fixture gallery",
            encoding="utf-8",
        )
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@example.invalid",
            "commit",
            "-qm",
            "fixture",
        ],
        cwd=repo,
        check=True,
    )
    primary.unlink()
    public.unlink()

    stage_script = (
        f'set -euo pipefail\n{art_array.group(0)}\ngit add -A -- "${{art_files[@]}}"\n'
    )
    subprocess.run(["bash", "-c", stage_script], cwd=repo, check=True)
    staged = subprocess.run(
        ["git", "diff", "--cached", "--name-status"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()

    assert staged == [
        "D\t.github/assets/img/living-unknown.gif",
        "D\tdocs/public/showcase/living-unknown.gif",
    ]


def test_finalize_remains_the_only_first_party_git_writer() -> None:
    writer_jobs: set[str] = set()
    for job_name, job in _workflow_jobs().items():
        raw_steps = job.get("steps", [])
        steps = cast(list[dict[str, Any]], raw_steps)
        scripts = "\n".join(
            script for step in steps if isinstance((script := step.get("run")), str)
        )
        raw_permissions = job.get("permissions", {})
        permissions = cast(dict[str, Any], raw_permissions)
        if (
            any(
                command in scripts for command in ("git add ", "git commit", "git push")
            )
            or permissions.get("contents") == "write"
        ):
            writer_jobs.add(job_name)

    assert writer_jobs == {"finalize"}
