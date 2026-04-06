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
    repo_count: int = 1,
    repo_names: tuple[str, ...] | None = None,
    languages: dict[str, int] | None = None,
    topic_clusters: dict[str, int] | None = None,
    repo_recency_bands: dict[str, int] | None = None,
    repo_visual_order: list[str] | None = None,
) -> DailySnapshot:
    day = date.today() - timedelta(days=(20 - idx))
    repo_entries = (
        [{"name": repo_name} for repo_name in repo_names]
        if repo_names is not None
        else [{"name": f"repo-{i}"} for i in range(repo_count)]
    )
    language_entries = languages or {"Python": 100}
    topic_entries = topic_clusters or {"art": 1}
    metrics = {
        "repos": repo_entries,
        "stars": stars,
        "forks": 1,
        "releases": [{"name": f"r{i}"} for i in range(releases)],
        "recent_merged_prs": [{"title": f"pr{i}"} for i in range(merged_prs)],
        "languages": language_entries,
        "language_count": len(language_entries),
        "language_diversity": max(0.0, (len(language_entries) - 1) * 0.5),
        "contributions_monthly": {"2025-01": 1},
        "contributions_daily": {day.isoformat(): 1},
        "topic_clusters": topic_entries,
        "repo_recency_bands": repo_recency_bands or {"fresh": len(repo_entries)},
        "repo_visual_order": repo_visual_order
        or [repo["name"] for repo in repo_entries],
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


def test_sample_frames_keeps_repo_growth_event_even_when_other_signals_match() -> None:
    snaps = [_snapshot(idx=i, repo_count=1) for i in range(20)]
    snaps[11] = _snapshot(idx=11, repo_count=2)

    sampled = sample_frames(snaps, max_frames=6)

    assert any(len(s.metrics_dict.get("repos", [])) == 2 for s in sampled)


def test_sample_frames_keeps_late_repo_arrival_with_tight_budget() -> None:
    snaps = [_snapshot(idx=i, repo_names=("foundation",)) for i in range(40)]
    snaps[8] = _snapshot(idx=8, repo_names=("foundation",), releases=3)
    snaps[19] = _snapshot(idx=19, repo_names=("foundation",), merged_prs=4)
    snaps[34] = _snapshot(idx=34, repo_names=("foundation", "late-arrival"))

    sampled = sample_frames(snaps, max_frames=5)

    assert any(
        [repo["name"] for repo in snap.metrics_dict.get("repos", [])]
        == ["foundation", "late-arrival"]
        for snap in sampled
    )


def test_sample_frames_keeps_ecology_shift_with_tight_budget() -> None:
    snaps = [
        _snapshot(
            idx=i,
            repo_names=("foundation",),
            languages={"Python": 100},
            topic_clusters={"art": 1},
            repo_recency_bands={"legacy": 1},
        )
        for i in range(40)
    ]
    snaps[8] = _snapshot(
        idx=8,
        repo_names=("foundation",),
        languages={"Python": 100},
        topic_clusters={"art": 1},
        repo_recency_bands={"legacy": 1},
        releases=3,
    )
    snaps[19] = _snapshot(
        idx=19,
        repo_names=("foundation",),
        languages={"Python": 100},
        topic_clusters={"art": 1},
        repo_recency_bands={"legacy": 1},
        merged_prs=4,
    )
    snaps[32] = _snapshot(
        idx=32,
        repo_names=("foundation",),
        languages={"Python": 70, "Go": 30},
        topic_clusters={"art": 1, "viz": 2},
        repo_recency_bands={"legacy": 1, "fresh": 1},
    )

    sampled = sample_frames(snaps, max_frames=5)

    assert any(
        snap.metrics_dict.get("topic_clusters") == {"art": 1, "viz": 2}
        for snap in sampled
    )
    assert any(snap.metrics_dict.get("language_count") == 2 for snap in sampled)


def test_sample_frames_keeps_repo_visual_order_shift_without_count_change() -> None:
    base_order = ("alpha", "beta", "gamma")
    shifted_order = ("alpha", "late-surge", "beta")
    snaps = [_snapshot(idx=i, repo_names=base_order) for i in range(40)]
    snaps[8] = _snapshot(idx=8, repo_names=base_order, releases=3)
    snaps[19] = _snapshot(idx=19, repo_names=base_order, merged_prs=4)
    snaps[32] = _snapshot(
        idx=32,
        repo_names=shifted_order,
        repo_visual_order=["alpha", "late-surge", "beta", "gamma"],
    )

    sampled = sample_frames(snaps, max_frames=5)

    assert any(
        [repo["name"] for repo in snap.metrics_dict.get("repos", [])]
        == ["alpha", "late-surge", "beta"]
        for snap in sampled
    )
