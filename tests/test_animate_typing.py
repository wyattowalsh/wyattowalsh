"""Focused target-resolution contracts for the animation CLI."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from PIL import Image

from scripts.art import animate


def test_resolve_target_uses_named_profile_without_live_metrics(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    profile: dict[str, Any] = {"label": "local", "repos": []}
    monkeypatch.setattr(animate, "PROFILES", {"local": profile})

    target = animate._resolve_target(  # noqa: SLF001
        profile="local",
        metrics_file=None,
        history_file=None,
    )

    assert target is profile


def test_resolve_target_falls_back_after_invalid_metrics(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    profile: dict[str, Any] = {"label": "fallback", "repos": []}
    monkeypatch.setattr(animate, "PROFILES", {"fallback": profile})
    metrics_path = tmp_path / "metrics.json"
    metrics_path.write_text("{invalid", encoding="utf-8")

    target = animate._resolve_target(  # noqa: SLF001
        profile="fallback",
        metrics_file=str(metrics_path),
        history_file=None,
    )

    assert target is profile


def test_resolve_target_normalizes_live_metrics_and_history(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    metrics_path = tmp_path / "metrics.json"
    history_path = tmp_path / "history.json"
    metrics_path.write_text(json.dumps({"stars": 7}), encoding="utf-8")
    history_path.write_text(json.dumps({"repos": []}), encoding="utf-8")
    captured: dict[str, Any] = {}

    def normalize(
        raw: dict[str, Any],
        *,
        owner: str,
        history: dict[str, Any],
    ) -> dict[str, Any]:
        captured.update(raw=raw, owner=owner, history=history)
        return {"label": owner, "stars": raw["stars"]}

    monkeypatch.setattr(animate, "normalize_live_metrics", normalize)

    target = animate._resolve_target(  # noqa: SLF001
        profile="live-owner",
        metrics_file=str(metrics_path),
        history_file=str(history_path),
    )

    assert target == {"label": "live-owner", "stars": 7}
    assert captured == {
        "raw": {"stars": 7},
        "owner": "live-owner",
        "history": {"repos": []},
    }


def test_publish_growth_gif_atomically_replaces_the_public_output(
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "inkgarden-growth.gif"
    Image.new("RGB", (8, 8), (1, 2, 3)).save(output_path, format="GIF")
    old_bytes = output_path.read_bytes()
    frames = [
        Image.new("RGB", (8, 8), (10, 20, 30)),
        Image.new("RGB", (8, 8), (30, 20, 10)),
    ]

    size_kb = animate._publish_growth_gif(  # noqa: SLF001
        frames,
        [120, 240],
        output_path,
    )

    assert size_kb == output_path.stat().st_size // 1024
    assert output_path.read_bytes() != old_bytes
    with Image.open(output_path) as published:
        assert published.format == "GIF"
        assert published.size == (8, 8)
        assert getattr(published, "n_frames", 1) == 2
        assert published.info["loop"] == 0
    assert list(tmp_path.glob(".inkgarden-growth.gif.*.publish.tmp")) == []


def test_publish_growth_gif_failure_preserves_the_public_output(
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "topo-growth.gif"
    Image.new("RGB", (8, 8), (1, 2, 3)).save(output_path, format="GIF")
    old_bytes = output_path.read_bytes()

    class FailingFrame:
        def save(self, stage_path: Path, **_kwargs: object) -> None:
            stage_path.write_bytes(b"partial GIF candidate")
            raise RuntimeError("render interrupted")

    with pytest.raises(RuntimeError, match="render interrupted"):
        animate._publish_growth_gif(  # noqa: SLF001
            [FailingFrame()],
            [120],
            output_path,
        )

    assert output_path.read_bytes() == old_bytes
    assert list(tmp_path.glob(".topo-growth.gif.*.publish.tmp")) == []
