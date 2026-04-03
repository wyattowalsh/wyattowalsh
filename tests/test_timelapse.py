"""Tests for the timelapse daily-snapshot and GIF rendering pipeline."""

from __future__ import annotations

import io
import types
from datetime import date, timedelta

import pytest

pytest.importorskip("numpy", reason="scripts.art.shared requires numpy")

from scripts.art.daily_snapshots import (  # noqa: E402, I001
    DailySnapshot,
    build_daily_snapshots,
    sample_frames,
)
from scripts.art.shared import (  # noqa: E402, I001
    WorldState,
    compute_world_state,
)
from scripts.art.timelapse import (  # noqa: E402, I001
    _compute_frame_durations,
    _render_single_frame,
)


# ---------------------------------------------------------------------------
# WorldState tests
# ---------------------------------------------------------------------------


def test_compute_world_state_defaults():
    """Empty metrics should produce calm defaults."""
    ws = compute_world_state({})
    assert ws.time_of_day == "day"
    assert ws.weather == "clear"
    assert ws.season == "summer"
    assert 0.0 <= ws.energy <= 1.0
    assert 0.0 <= ws.vitality <= 1.0
    assert ws.aurora_intensity == 0.0
    assert isinstance(ws.daylight_hue_drift, float)
    assert ws.weather_severity == 0.0
    assert ws.season_transition_weights["summer"] == pytest.approx(1.0)
    assert 0.0 <= ws.activity_pressure <= 1.0


def test_compute_world_state_night():
    """Peak commit hour at 23 → night."""
    ws = compute_world_state({"commit_hour_distribution": {23: 50, 12: 5}})
    assert ws.time_of_day == "night"


def test_compute_world_state_stormy():
    """High open issues → stormy weather."""
    ws = compute_world_state(
        {
            "open_issues_count": 80,
            "issue_stats": {"open_count": 80, "closed_count": 20},
        }
    )
    assert ws.weather == "stormy"


def test_compute_world_state_clear():
    """Low open issues → clear weather."""
    ws = compute_world_state(
        {
            "open_issues_count": 2,
            "issue_stats": {"open_count": 2, "closed_count": 100},
        }
    )
    assert ws.weather == "clear"


def test_compute_world_state_season_python():
    """Python-dominant → summer."""
    ws = compute_world_state({"languages": {"Python": 90000, "Shell": 1000}})
    assert ws.season == "summer"


def test_compute_world_state_season_rust():
    """Rust-dominant → winter."""
    ws = compute_world_state({"languages": {"Rust": 90000, "Python": 1000}})
    assert ws.season == "winter"


def test_compute_world_state_energy_from_stars():
    """High star velocity → high energy."""
    ws = compute_world_state({"star_velocity": {"recent_rate": 15.0}})
    assert ws.energy > 0.5


def test_compute_world_state_hue_drift_weights_and_pressure() -> None:
    """Continuous world-state fields should respond to mixed inputs."""
    dawn = compute_world_state({"commit_hour_distribution": {7: 12, 12: 1}})
    night = compute_world_state({"commit_hour_distribution": {23: 12, 12: 1}})
    mixed = compute_world_state(
        {
            "languages": {"Python": 6000, "Ruby": 2500, "Rust": 1500},
            "contributions_monthly": {
                "2025-01": 12,
                "2025-02": 34,
                "2025-03": 48,
            },
            "star_velocity": {"recent_rate": 8.0},
            "contribution_streaks": {
                "current_streak_months": 9,
                "streak_active": True,
            },
        }
    )

    assert dawn.daylight_hue_drift > 0.0
    assert night.daylight_hue_drift < 0.0
    assert sum(mixed.season_transition_weights.values()) == pytest.approx(1.0)
    assert (
        mixed.season_transition_weights["summer"]
        > mixed.season_transition_weights["spring"]
    )
    assert mixed.activity_pressure > 0.3


def test_compute_world_state_weather_severity_tracks_open_ratio() -> None:
    """Weather severity should scale with open issue pressure."""
    clear = compute_world_state(
        {
            "open_issues_count": 2,
            "issue_stats": {"open_count": 2, "closed_count": 100},
        }
    )
    stormy = compute_world_state(
        {
            "open_issues_count": 80,
            "issue_stats": {"open_count": 80, "closed_count": 20},
        }
    )

    assert clear.weather_severity < stormy.weather_severity
    assert stormy.weather_severity > 0.5


def test_compute_world_state_palette_keys():
    """Palette should contain expected keys."""
    ws = compute_world_state({})
    assert "sky_top" in ws.palette
    assert "sky_bottom" in ws.palette
    assert "ground" in ws.palette
    assert "accent" in ws.palette
    assert "glow" in ws.palette


# ---------------------------------------------------------------------------
# DailySnapshot builder tests
# ---------------------------------------------------------------------------


def _mock_history(days: int = 30) -> dict:
    """Build a minimal history dict spanning N days."""
    start = date.today() - timedelta(days=days)
    return {
        "account_created": start.isoformat() + "T00:00:00Z",
        "stars": [
            {"date": (start + timedelta(days=i * 5)).isoformat(), "user": f"user{i}"}
            for i in range(days // 5)
        ],
        "forks": [
            {"date": (start + timedelta(days=i * 10)).isoformat(), "user": f"forker{i}"}
            for i in range(days // 10)
        ],
        "repos": [
            {"date": (start + timedelta(days=i * 7)).isoformat(), "name": f"repo-{i}"}
            for i in range(days // 7)
        ],
        "contributions_monthly": {
            f"{start.year:04d}-{start.month:02d}": 42,
        },
    }


def _mock_metrics() -> dict:
    release_day = date.today() - timedelta(days=4)
    merged_pr_day = date.today() - timedelta(days=3)
    return {
        "stars": 10,
        "forks": 3,
        "watchers": 5,
        "followers": 20,
        "following": 10,
        "public_repos": 4,
        "orgs_count": 1,
        "contributions_last_year": 200,
        "total_commits": 500,
        "total_prs": 10,
        "total_issues": 5,
        "open_issues_count": 2,
        "network_count": 15,
        "public_gists": 3,
        "pr_review_count": 8,
        "total_repos_contributed": 7,
        "issue_stats": {"open_count": 2, "closed_count": 10},
        "commit_hour_distribution": {9: 3, 21: 4},
        "releases": [
            {
                "published_at": f"{release_day.isoformat()}T12:00:00Z",
                "name": "v1.0.0",
            }
        ],
        "recent_merged_prs": [
            {
                "merged_at": f"{merged_pr_day.isoformat()}T12:00:00Z",
                "title": "PR",
            }
        ],
        "languages": {"Python": 50000, "JavaScript": 20000},
        "top_repos": [
            {
                "name": "repo-0",
                "language": "Python",
                "stars": 5,
                "forks": 1,
                "topics": ["ml"],
            },
            {
                "name": "repo-1",
                "language": "JavaScript",
                "stars": 3,
                "forks": 2,
                "topics": ["web"],
            },
        ],
    }


def test_build_daily_snapshots_basic():
    """Snapshot count matches day range."""
    history = _mock_history(days=30)
    metrics = _mock_metrics()
    snaps = build_daily_snapshots(history, metrics, owner="testuser")
    assert len(snaps) == 30
    assert all(isinstance(s, DailySnapshot) for s in snaps)


def test_build_daily_snapshots_monotonic_stars():
    """Cumulative stars should be non-decreasing."""
    history = _mock_history(days=60)
    metrics = _mock_metrics()
    snaps = build_daily_snapshots(history, metrics, owner="testuser")
    stars = [s.metrics_dict.get("stars", 0) for s in snaps]
    for i in range(1, len(stars)):
        assert stars[i] >= stars[i - 1], (
            f"Stars decreased at index {i}: {stars[i - 1]} → {stars[i]}"
        )


def test_build_daily_snapshots_progress():
    """Progress should go from 0 to 1."""
    history = _mock_history(days=30)
    metrics = _mock_metrics()
    snaps = build_daily_snapshots(history, metrics, owner="testuser")
    assert snaps[0].progress == 0.0
    assert snaps[-1].progress == pytest.approx(1.0)


def test_build_daily_snapshots_has_world_state():
    """Each snapshot should have a WorldState."""
    history = _mock_history(days=10)
    metrics = _mock_metrics()
    snaps = build_daily_snapshots(history, metrics, owner="testuser")
    for s in snaps:
        assert isinstance(s.world_state, WorldState)


def test_build_daily_snapshots_metrics_dict_keys():
    """metrics_dict should have the keys generators need."""
    history = _mock_history(days=10)
    metrics = _mock_metrics()
    snaps = build_daily_snapshots(history, metrics, owner="testuser")
    required = {
        "repos",
        "stars",
        "forks",
        "followers",
        "contributions_monthly",
        "contributions_daily",
        "languages",
        "issue_stats",
        "commit_hour_distribution",
        "repo_recency_bands",
        "total_repos_contributed",
    }
    for s in snaps:
        assert required.issubset(s.metrics_dict.keys()), (
            f"Missing keys: {required - s.metrics_dict.keys()}"
        )


def test_build_daily_snapshots_history_dict_keys():
    """history_dict should have the keys cosmic/spiral generators need."""
    history = _mock_history(days=10)
    metrics = _mock_metrics()
    snaps = build_daily_snapshots(history, metrics, owner="testuser")
    required = {
        "account_created",
        "stars",
        "forks",
        "repos",
        "contributions_monthly",
        "contributions_daily",
        "current_metrics",
        "issue_stats",
        "commit_hour_distribution",
    }
    for s in snaps:
        assert required.issubset(s.history_dict.keys()), (
            f"Missing keys: {required - s.history_dict.keys()}"
        )


def test_build_daily_snapshots_prefers_contributions_daily() -> None:
    """When daily contributions are present, snapshots should use them."""
    history = _mock_history(days=7)
    start = date.fromisoformat(history["account_created"][:10])
    history["contributions_daily"] = {
        (start + timedelta(days=i)).isoformat(): i + 1 for i in range(7)
    }
    history["contributions_monthly"] = {f"{start.year:04d}-{start.month:02d}": 999}
    metrics = _mock_metrics()
    snaps = build_daily_snapshots(history, metrics, owner="testuser")
    assert (
        snaps[-1].metrics_dict["contributions_daily"]
        == history["contributions_daily"]
    )


def test_build_daily_snapshots_monthly_fallback_still_works() -> None:
    """Monthly-only payloads should still produce daily contributions for rendering."""
    history = _mock_history(days=7)
    history.pop("contributions_daily", None)
    metrics = _mock_metrics()
    snaps = build_daily_snapshots(history, metrics, owner="testuser")
    assert "contributions_daily" in snaps[-1].metrics_dict
    assert "contributions_daily" in snaps[-1].history_dict
    assert isinstance(snaps[-1].metrics_dict["contributions_daily"], dict)


def test_build_daily_snapshots_release_and_pr_events_follow_chronology() -> None:
    """Release and merged-PR events should appear on their actual in-range days."""
    history = _mock_history(days=10)
    start = date.fromisoformat(history["account_created"][:10])
    release_day = start + timedelta(days=2)
    merged_pr_day = start + timedelta(days=4)
    metrics = _mock_metrics()
    metrics["releases"] = [
        {
            "published_at": f"{release_day.isoformat()}T12:00:00Z",
            "name": "v1.0.0",
        }
    ]
    metrics["recent_merged_prs"] = [
        {
            "merged_at": f"{merged_pr_day.isoformat()}T12:00:00Z",
            "title": "PR",
        }
    ]

    snaps = build_daily_snapshots(history, metrics, owner="testuser")
    snap_by_day = {snap.day: snap for snap in snaps}

    assert snap_by_day[release_day - timedelta(days=1)].metrics_dict["releases"] == []
    assert (
        snap_by_day[release_day].metrics_dict["releases"][0]["published_at"].startswith(
            release_day.isoformat()
        )
    )
    assert (
        snap_by_day[release_day].history_dict["releases"][0]["published_at"].startswith(
            release_day.isoformat()
        )
    )

    assert (
        snap_by_day[merged_pr_day - timedelta(days=1)].metrics_dict["recent_merged_prs"]
        == []
    )
    assert snap_by_day[merged_pr_day].metrics_dict["recent_merged_prs"][0][
        "merged_at"
    ].startswith(merged_pr_day.isoformat())
    assert snap_by_day[merged_pr_day].history_dict["recent_merged_prs"][0][
        "merged_at"
    ].startswith(merged_pr_day.isoformat())


def test_build_daily_snapshots_recomputes_derived_signals_per_day(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Derived signals should be recomputed for each day."""
    history = _mock_history(days=5)
    metrics = _mock_metrics()

    star_calls: list[int] = []
    streak_calls: list[int] = []

    def _fake_star_velocity(stars_up_to: list[dict]) -> dict[str, float]:
        star_calls.append(len(stars_up_to))
        return {"recent_rate": float(len(stars_up_to))}

    def _fake_streaks(monthly: dict[str, int]) -> dict[str, int | bool]:
        streak_calls.append(len(monthly))
        return {
            "current_streak_months": len(streak_calls),
            "longest_streak_months": len(streak_calls),
            "streak_active": True,
        }

    monkeypatch.setattr(
        "scripts.fetch_history.compute_star_velocity",
        _fake_star_velocity,
    )
    monkeypatch.setattr(
        "scripts.fetch_history.compute_contribution_streaks",
        _fake_streaks,
    )

    snaps = build_daily_snapshots(history, metrics, owner="testuser")
    assert len(star_calls) == len(snaps)
    assert len(streak_calls) == len(snaps)
    assert (
        snaps[-1].metrics_dict["contribution_streaks"]["current_streak_months"]
        == len(snaps)
    )


def test_render_single_frame_topo_does_not_leak_chrome_maturity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Topography timelapse frames should not force final chrome maturity."""
    captured: dict[str, object] = {}

    def _fake_generate(data: dict, **kwargs: object) -> str:
        captured["kwargs"] = kwargs
        return "<svg/>"

    class _FakeImage:
        def save(self, buffer: io.BytesIO, format: str = "PNG") -> None:  # noqa: A002
            _ = format
            buffer.write(b"png")

    monkeypatch.setattr(
        "scripts.art.animate.svg_to_png",
        lambda _svg, _size, frame_id: _FakeImage(),
    )
    monkeypatch.setattr(
        "importlib.import_module",
        lambda _path: types.SimpleNamespace(generate=_fake_generate),
    )

    result = _render_single_frame(
        {
            "metrics_dict": {},
            "maturity": 0.4,
            "day_index": 1,
        },
        "topo",
        "abc123",
        128,
    )

    assert result == b"png"
    assert "chrome_maturity" not in captured.get("kwargs", {})


# ---------------------------------------------------------------------------
# Frame sampling tests
# ---------------------------------------------------------------------------


def test_sample_frames_respects_max():
    """Output never exceeds max_frames."""
    history = _mock_history(days=200)
    metrics = _mock_metrics()
    snaps = build_daily_snapshots(history, metrics)
    sampled = sample_frames(snaps, max_frames=30)
    assert len(sampled) <= 30


def test_sample_frames_includes_first_and_last():
    """First and last days are always in the sample."""
    history = _mock_history(days=100)
    metrics = _mock_metrics()
    snaps = build_daily_snapshots(history, metrics)
    sampled = sample_frames(snaps, max_frames=10)
    assert sampled[0].day == snaps[0].day
    assert sampled[-1].day == snaps[-1].day


def test_sample_frames_passthrough_small():
    """If snapshots <= max_frames, return all."""
    history = _mock_history(days=10)
    metrics = _mock_metrics()
    snaps = build_daily_snapshots(history, metrics)
    sampled = sample_frames(snaps, max_frames=100)
    assert len(sampled) == len(snaps)


# ---------------------------------------------------------------------------
# Frame duration tests
# ---------------------------------------------------------------------------


def test_compute_frame_durations_length():
    """Duration list matches frame count."""
    assert len(_compute_frame_durations(10)) == 10
    assert len(_compute_frame_durations(50)) == 50
    assert len(_compute_frame_durations(1)) == 1


def test_compute_frame_durations_last_hold():
    """Final frame should be 2000ms hold."""
    durations = _compute_frame_durations(20)
    assert durations[-1] == 2000


def test_compute_frame_durations_all_positive():
    """All durations must be positive."""
    for n in (5, 10, 50, 150):
        durations = _compute_frame_durations(n)
        assert all(d > 0 for d in durations), f"Non-positive duration in {durations}"
