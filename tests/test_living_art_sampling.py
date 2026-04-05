"""Focused regression tests for adaptive timelapse frame sampling."""

from __future__ import annotations

from datetime import date, timedelta

import pytest

pytest.importorskip("numpy", reason="scripts.art.shared requires numpy")

from scripts.art.daily_snapshots import DailySnapshot, sample_frames  # noqa: E402
from scripts.art.shared import WorldState  # noqa: E402


def _snapshot(
    *,
    idx: int,
    maturity: float = 0.5,
    stars: int = 10,
    releases: int = 0,
    merged_prs: int = 0,
    weather: str = "clear",
) -> DailySnapshot:
    day = date.today() - timedelta(days=(20 - idx))
    metrics = {
        "repos": [{"name": "repo"}],
        "stars": stars,
        "forks": 1,
        "releases": [{"name": f"r{i}"} for i in range(releases)],
        "recent_merged_prs": [{"title": f"pr{i}"} for i in range(merged_prs)],
        "language_count": 1,
        "contributions_monthly": {"2025-01": 1},
        "topic_clusters": {"art": 1},
    }
    world = WorldState(
        time_of_day="day",
        weather=weather,
        season="summer",
        energy=0.5,
        vitality=0.5,
    )
    return DailySnapshot(
        day=day,
        day_index=idx,
        total_days=20,
        progress=idx / 19,
        maturity=maturity,
        world_state=world,
        metrics_dict=metrics,
        history_dict={},
    )


def test_sample_frames_keeps_release_event_even_when_maturity_is_flat() -> None:
    snaps = [_snapshot(idx=i) for i in range(20)]
    snaps[11] = _snapshot(idx=11, releases=1)

    sampled = sample_frames(snaps, max_frames=6)

    assert any(len(s.metrics_dict.get("releases", [])) == 1 for s in sampled)


def test_sample_frames_keeps_weather_shift_even_with_equal_maturity() -> None:
    snaps = [_snapshot(idx=i, weather="clear") for i in range(20)]
    snaps[10] = _snapshot(idx=10, weather="stormy")
    snaps[11] = _snapshot(idx=11, weather="stormy")

    sampled = sample_frames(snaps, max_frames=8)
    sampled_weathers = [s.world_state.weather for s in sampled]

    assert "stormy" in sampled_weathers
