"""Focused contracts for lossless living-art GIF post-processing."""

from __future__ import annotations

import io
import os
import shutil
import stat
import subprocess
import sys
import time
from pathlib import Path

import pytest
from PIL import Image, ImageDraw

from scripts.art import timelapse
from scripts.art._gif_optimize import (
    _ConcurrentGifOutputError,
    _gif_fingerprint,
    _gif_output_transaction,
    _GifOutputLockTimeout,
    _open_gif_output_lock,
    _optimize_gif_with_gifsicle,
    _preserves_playback_contract,
    _resolve_logical_output,
    _UnsafeGifOutputError,
)


def _write_animation(file_path: Path, *, color_offset: int = 0) -> None:
    frames: list[Image.Image] = []
    for frame_index in range(12):
        image = Image.new("RGB", (96, 96), (245, 245, 245))
        draw = ImageDraw.Draw(image)
        draw.rectangle(
            (frame_index * 4, 20, frame_index * 4 + 30, 50),
            fill=(30 + color_offset, 80 + frame_index * 8, 180),
        )
        frames.append(image)
    frames[0].save(
        file_path,
        format="GIF",
        save_all=True,
        append_images=frames[1:],
        duration=[80 + frame_index * 10 for frame_index in range(12)],
        loop=0,
        optimize=False,
    )


def _png_frame(color: tuple[int, int, int]) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (32, 32), color).save(buffer, format="PNG")
    return buffer.getvalue()


@pytest.mark.skipif(shutil.which("gifsicle") is None, reason="gifsicle unavailable")
def test_gifsicle_optimization_is_deterministic_smaller_and_pixel_exact(
    tmp_path: Path,
) -> None:
    first_path = tmp_path / "first.gif"
    second_path = tmp_path / "second.gif"
    _write_animation(first_path)
    _write_animation(second_path)
    source_mode = first_path.stat().st_mode
    source = _gif_fingerprint(first_path)

    first_result = _optimize_gif_with_gifsicle(first_path)
    second_result = _optimize_gif_with_gifsicle(second_path)
    first_output = _gif_fingerprint(first_path)
    second_output = _gif_fingerprint(second_path)

    assert first_result.replaced is True
    assert first_result.reason == "optimized"
    assert first_result.output_size < first_result.source_size
    assert second_result.replaced is True
    assert first_output.file_sha256 == second_output.file_sha256
    assert _preserves_playback_contract(source, first_output)
    assert first_path.stat().st_mode == source_mode


def test_optimizer_rejects_a_visually_changed_candidate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_path = tmp_path / "source.gif"
    changed_path = tmp_path / "changed.gif"
    _write_animation(source_path)
    _write_animation(changed_path, color_offset=20)
    source_bytes = source_path.read_bytes()

    monkeypatch.setattr(
        "scripts.art._gif_optimize.shutil.which",
        lambda _executable: "/usr/bin/gifsicle",
    )

    def _fake_run(command: list[str], **_kwargs: object) -> subprocess.CompletedProcess:
        candidate_path = Path(command[command.index("--output") + 1])
        candidate_path.write_bytes(changed_path.read_bytes())
        return subprocess.CompletedProcess(command, returncode=0)

    monkeypatch.setattr("scripts.art._gif_optimize.subprocess.run", _fake_run)

    result = _optimize_gif_with_gifsicle(source_path)

    assert result.replaced is False
    assert result.reason == "playback-contract-changed"
    assert source_path.read_bytes() == source_bytes


def test_optimizer_retains_source_when_tool_is_unavailable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_path = tmp_path / "source.gif"
    _write_animation(source_path)
    source_bytes = source_path.read_bytes()
    monkeypatch.setattr(
        "scripts.art._gif_optimize.shutil.which",
        lambda _executable: None,
    )

    result = _optimize_gif_with_gifsicle(source_path)

    assert result.replaced is False
    assert result.reason == "optimizer-unavailable"
    assert source_path.read_bytes() == source_bytes


def test_optimizer_retains_source_without_a_size_improvement(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_path = tmp_path / "source.gif"
    _write_animation(source_path)
    source_bytes = source_path.read_bytes()
    monkeypatch.setattr(
        "scripts.art._gif_optimize.shutil.which",
        lambda _executable: "/usr/bin/gifsicle",
    )

    def _fake_run(command: list[str], **_kwargs: object) -> subprocess.CompletedProcess:
        candidate_path = Path(command[command.index("--output") + 1])
        candidate_path.write_bytes(source_bytes)
        return subprocess.CompletedProcess(command, returncode=0)

    monkeypatch.setattr("scripts.art._gif_optimize.subprocess.run", _fake_run)

    result = _optimize_gif_with_gifsicle(source_path)

    assert result.replaced is False
    assert result.reason == "no-size-improvement"
    assert source_path.read_bytes() == source_bytes


def test_optimizer_failure_retains_source_and_cleans_candidate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_path = tmp_path / "source.gif"
    _write_animation(source_path)
    source_bytes = source_path.read_bytes()
    monkeypatch.setattr(
        "scripts.art._gif_optimize.shutil.which",
        lambda _executable: "/usr/bin/gifsicle",
    )

    def _fake_run(command: list[str], **_kwargs: object) -> subprocess.CompletedProcess:
        return subprocess.CompletedProcess(command, returncode=2)

    monkeypatch.setattr("scripts.art._gif_optimize.subprocess.run", _fake_run)

    result = _optimize_gif_with_gifsicle(source_path)

    assert result.replaced is False
    assert result.reason == "optimizer-failed"
    assert source_path.read_bytes() == source_bytes
    assert list(tmp_path.glob("*.gifsicle.tmp")) == []


@pytest.mark.parametrize("failure", ["timeout", "invalid-candidate"])
def test_optimizer_process_failures_retain_the_owned_stage(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failure: str,
) -> None:
    stage_path = tmp_path / ".living-test.gif.unit.publish.tmp"
    _write_animation(stage_path)
    source_bytes = stage_path.read_bytes()
    monkeypatch.setattr(
        "scripts.art._gif_optimize.shutil.which",
        lambda _executable: "/usr/bin/gifsicle",
    )

    def _fake_run(command: list[str], **_kwargs: object) -> subprocess.CompletedProcess:
        if failure == "timeout":
            raise subprocess.TimeoutExpired(command, timeout=1)
        candidate_path = Path(command[command.index("--output") + 1])
        candidate_path.write_bytes(b"not a gif")
        return subprocess.CompletedProcess(command, returncode=0)

    monkeypatch.setattr("scripts.art._gif_optimize.subprocess.run", _fake_run)

    result = _optimize_gif_with_gifsicle(stage_path)

    assert result.replaced is False
    assert result.reason == (
        "optimizer-failed" if failure == "timeout" else "invalid-candidate"
    )
    assert stage_path.read_bytes() == source_bytes
    assert list(tmp_path.glob("*.gifsicle.tmp")) == []


def test_output_transaction_preserves_old_file_on_body_failure(
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "living-test.gif"
    _write_animation(output_path)
    old_bytes = output_path.read_bytes()

    with pytest.raises(RuntimeError, match="injected assembly failure"):
        with _gif_output_transaction(output_path) as stage_path:
            _write_animation(stage_path, color_offset=10)
            raise RuntimeError("injected assembly failure")

    assert output_path.read_bytes() == old_bytes
    assert list(tmp_path.glob("*.publish.tmp")) == []


def test_output_transaction_leaves_new_target_absent_for_an_invalid_stage(
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "living-invalid.gif"

    with pytest.raises(ValueError, match="Unable to decode GIF"):
        with _gif_output_transaction(output_path) as stage_path:
            stage_path.write_bytes(b"not a gif")

    assert not output_path.exists()
    assert list(tmp_path.glob("*.publish.tmp")) == []


def test_output_transaction_rejects_a_replaced_stage_symlink(
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "living-test.gif"
    external_path = tmp_path / "external.gif"
    _write_animation(external_path)

    with pytest.raises(_UnsafeGifOutputError, match="regular file"):
        with _gif_output_transaction(output_path) as stage_path:
            stage_path.unlink()
            stage_path.symlink_to(external_path)

    assert not output_path.exists()
    assert external_path.is_file()


def test_output_transaction_preserves_mode_and_uses_one_public_replace(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output_path = tmp_path / "living-test.gif"
    _write_animation(output_path)
    os.chmod(output_path, 0o640)
    old_bytes = output_path.read_bytes()
    replace_calls: list[tuple[Path, Path]] = []
    real_replace = os.replace

    def _record_replace(source: str | Path, destination: str | Path) -> None:
        replace_calls.append((Path(source), Path(destination)))
        real_replace(source, destination)

    monkeypatch.setattr("scripts.art._gif_optimize.os.replace", _record_replace)

    with _gif_output_transaction(output_path) as stage_path:
        assert stage_path.parent == output_path.parent.resolve()
        assert stage_path != output_path
        assert output_path.read_bytes() == old_bytes
        _write_animation(stage_path, color_offset=10)

    assert len(replace_calls) == 1
    assert replace_calls[0][0] != output_path
    assert replace_calls[0][1] == output_path.resolve()
    assert stat.S_IMODE(output_path.stat().st_mode) == 0o640
    assert output_path.read_bytes() != old_bytes


def test_output_transaction_uses_documented_mode_for_a_new_file(
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "living-new.gif"

    with _gif_output_transaction(output_path) as stage_path:
        _write_animation(stage_path)

    assert stat.S_IMODE(output_path.stat().st_mode) == 0o644
    assert _gif_fingerprint(output_path).frame_count == 12


def test_output_transaction_rejects_noncooperating_change_before_publish(
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "living-test.gif"
    external_path = tmp_path / "external.gif"
    _write_animation(output_path)
    _write_animation(external_path, color_offset=20)
    external_bytes = external_path.read_bytes()

    with pytest.raises(_ConcurrentGifOutputError, match="changed before publication"):
        with _gif_output_transaction(output_path) as stage_path:
            _write_animation(stage_path, color_offset=10)
            output_path.write_bytes(external_bytes)

    assert output_path.read_bytes() == external_bytes
    assert list(tmp_path.glob("*.publish.tmp")) == []


@pytest.mark.parametrize("target_kind", ["symlink", "directory"])
def test_output_transaction_rejects_non_regular_public_targets(
    tmp_path: Path,
    target_kind: str,
) -> None:
    output_path = tmp_path / "living-test.gif"
    if target_kind == "symlink":
        real_path = tmp_path / "real.gif"
        _write_animation(real_path)
        output_path.symlink_to(real_path)
    else:
        output_path.mkdir()

    with pytest.raises(_UnsafeGifOutputError, match="regular file"):
        with _gif_output_transaction(output_path):
            pytest.fail("an unsafe public target must fail before yielding")


def test_output_transaction_cleans_only_owned_abandoned_stages(
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "living-test.gif"
    stale_stage = tmp_path / ".living-test.gif.dead.publish.tmp"
    stale_candidate = (
        tmp_path / ".living-test.gif.dead.publish.tmp.candidate.gifsicle.tmp"
    )
    unrelated = tmp_path / ".living-test.gif.keep.tmp"
    stale_stage.write_bytes(b"stale")
    stale_candidate.write_bytes(b"stale")
    unrelated.write_bytes(b"keep")

    with _gif_output_transaction(output_path) as stage_path:
        assert not stale_stage.exists()
        assert not stale_candidate.exists()
        assert unrelated.read_bytes() == b"keep"
        _write_animation(stage_path)

    assert unrelated.read_bytes() == b"keep"
    assert list(tmp_path.glob("*.publish.tmp")) == []
    assert list(tmp_path.glob("*.gifsicle.tmp")) == []


def test_output_lock_node_is_stable_and_never_unlinked_by_transactions(
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "living-test.gif"
    logical_output = _resolve_logical_output(output_path)
    first_descriptor, first_lock_path = _open_gif_output_lock(logical_output)
    first_inode = os.fstat(first_descriptor).st_ino
    os.close(first_descriptor)

    with _gif_output_transaction(output_path) as stage_path:
        _write_animation(stage_path)

    assert first_lock_path.is_file()
    second_descriptor, second_lock_path = _open_gif_output_lock(logical_output)
    try:
        assert second_lock_path == first_lock_path
        assert os.fstat(second_descriptor).st_ino == first_inode
    finally:
        os.close(second_descriptor)


def test_output_lock_serializes_processes_and_recovers_after_crash(
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "living-test.gif"
    ready_path = tmp_path / "child-ready"
    project_root = Path(__file__).resolve().parents[1]
    child_code = """
import sys
import time
from pathlib import Path

from PIL import Image

from scripts.art._gif_optimize import _gif_output_transaction

output_path = Path(sys.argv[1])
ready_path = Path(sys.argv[2])
with _gif_output_transaction(output_path, lock_timeout_seconds=5.0) as stage_path:
    Image.new("RGB", (8, 8), (10, 20, 30)).save(stage_path, format="GIF")
    ready_path.write_text(str(stage_path), encoding="utf-8")
    time.sleep(60)
"""
    process = subprocess.Popen(
        [sys.executable, "-c", child_code, str(output_path), str(ready_path)],
        cwd=project_root,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )
    deadline = time.monotonic() + 10
    while not ready_path.exists() and process.poll() is None:
        if time.monotonic() >= deadline:
            break
        time.sleep(0.02)

    try:
        if not ready_path.exists():
            if process.poll() is None:
                process.kill()
            _, stderr = process.communicate(timeout=5)
            pytest.fail(f"lock-holder subprocess did not become ready: {stderr}")
        abandoned_stage = Path(ready_path.read_text(encoding="utf-8"))
        with pytest.raises(_GifOutputLockTimeout, match="Timed out"):
            with _gif_output_transaction(output_path, lock_timeout_seconds=0.1):
                pytest.fail("a contender must not enter while the child holds the lock")
    finally:
        if process.poll() is None:
            process.kill()
        process.wait(timeout=5)

    with _gif_output_transaction(output_path, lock_timeout_seconds=1.0) as stage_path:
        _write_animation(stage_path)

    assert output_path.is_file()
    assert not abandoned_stage.exists()
    assert _gif_fingerprint(output_path).frame_count == 12


def test_timelapse_assembly_optimizes_only_a_private_stage(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output_path = tmp_path / "living-test.gif"
    _write_animation(output_path)
    old_bytes = output_path.read_bytes()
    calls: list[Path] = []

    def _record_optimizer(file_path: Path) -> None:
        assert file_path.is_file()
        assert file_path != output_path
        assert file_path.name.startswith(f".{output_path.name}.")
        assert file_path.name.endswith(".publish.tmp")
        assert output_path.read_bytes() == old_bytes
        calls.append(file_path)

    monkeypatch.setattr(timelapse, "_optimize_gif_with_gifsicle", _record_optimizer)

    result = timelapse._assemble_gif(
        [_png_frame((220, 20, 40)), _png_frame((30, 80, 200))],
        [100, 300],
        output_path,
        max_size_mb=-1,
    )

    assert result == output_path
    assert len(calls) == 1
    assert calls[0] != output_path
    assert not calls[0].exists()
    assert output_path.read_bytes() != old_bytes
    assert _gif_fingerprint(output_path).dimensions == (16, 16)
