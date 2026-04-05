"""Regression tests for timelapse runtime and frame-duration contracts."""

from __future__ import annotations

from pathlib import Path

from scripts.art.timelapse import (
    DEFAULT_PUBLISHED_MAX_FRAMES,
    DEFAULT_PUBLISHED_RUNTIME_MS,
    MIN_PUBLISHED_RUNTIME_MS,
    _compute_frame_durations,
    _select_valid_frames_with_durations,
)


def test_default_runtime_contract_is_legible() -> None:
    """Canonical defaults should produce a materially legible runtime."""
    durations = _compute_frame_durations(DEFAULT_PUBLISHED_MAX_FRAMES)
    total_runtime_ms = sum(durations)

    assert len(durations) == DEFAULT_PUBLISHED_MAX_FRAMES
    assert durations[-1] == 3000
    assert total_runtime_ms >= MIN_PUBLISHED_RUNTIME_MS
    assert total_runtime_ms <= DEFAULT_PUBLISHED_RUNTIME_MS + 2000


def test_small_frame_durations_keep_final_hold() -> None:
    """Edge cases should still end with the contracted hold duration."""
    assert _compute_frame_durations(1) == [3000]
    assert _compute_frame_durations(2) == [1200, 3000]


def test_high_frame_count_runtime_plan_stays_within_budget() -> None:
    """Floor protection should not allow runtime plans to exceed total_ms."""
    frame_count = 150
    durations = _compute_frame_durations(frame_count)

    assert len(durations) == frame_count
    assert durations[-1] == 3000
    assert sum(durations) <= DEFAULT_PUBLISHED_RUNTIME_MS


def test_dropped_frame_duration_alignment_uses_original_indices() -> None:
    """Duration mapping must follow original frame indices after failures."""
    all_durations = [101, 202, 303, 404]
    rendered = [
        (2, b"frame-2"),
        (0, b"frame-0"),
        (3, None),
        (1, None),
    ]

    valid_frames, valid_durations = _select_valid_frames_with_durations(
        rendered,
        all_durations,
    )

    assert valid_frames == [b"frame-0", b"frame-2"]
    assert valid_durations == [101, 303]


def test_render_timelapse_requests_today_terminal_snapshot(
    monkeypatch,
    tmp_path: Path,
) -> None:
    """Canonical timelapse rendering should include today in the terminal snapshot."""
    captured: dict[str, bool] = {}

    monkeypatch.setattr(
        "scripts.art.timelapse.validate_live_history_payload",
        lambda h: h,
    )
    monkeypatch.setattr(
        "scripts.art.timelapse.validate_live_metrics_payload",
        lambda m: m,
    )

    def _fake_build_daily_snapshots(
        history: dict,
        metrics: dict,
        *,
        owner: str = "",
        include_today: bool = False,
    ) -> list[object]:
        _ = history, metrics, owner
        captured["include_today"] = include_today
        return []

    monkeypatch.setattr(
        "scripts.art.timelapse.build_daily_snapshots",
        _fake_build_daily_snapshots,
    )

    from scripts.art.timelapse import render_timelapse

    assert render_timelapse({}, {}, output_dir=tmp_path) == []
    assert captured["include_today"] is True
