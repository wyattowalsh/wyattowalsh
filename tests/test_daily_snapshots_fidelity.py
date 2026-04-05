"""Focused fidelity tests for daily snapshot reconstruction."""

from __future__ import annotations

from datetime import date, timedelta

import pytest

pytest.importorskip("numpy", reason="scripts.art.shared requires numpy")

from scripts.art.daily_snapshots import build_daily_snapshots  # noqa: E402


def _history_for_days(days: int = 14) -> dict:
    start = date.today() - timedelta(days=days)
    return {
        "account_created": f"{start.isoformat()}T00:00:00Z",
        "repos": [
            {"date": start.isoformat(), "name": "py-0"},
            {"date": (start + timedelta(days=5)).isoformat(), "name": "py-1"},
            {"date": (start + timedelta(days=10)).isoformat(), "name": "py-2"},
        ],
        "stars": [
            {
                "date": f"{(start + timedelta(days=2)).isoformat()}T21:00:00Z",
                "user": "a",
            },
            {
                "date": f"{(start + timedelta(days=9)).isoformat()}T10:00:00Z",
                "user": "b",
            },
        ],
        "forks": [
            {
                "date": f"{(start + timedelta(days=3)).isoformat()}T19:00:00Z",
                "user": "c",
            },
        ],
        "contributions_daily": {
            (start + timedelta(days=i)).isoformat(): (6 if i % 6 in (0, 1) else 2)
            for i in range(days + 1)
        },
        "contributions_monthly": {f"{start.year:04d}-{start.month:02d}": 40},
    }


def _metrics_for_history() -> dict:
    release_day = date.today() - timedelta(days=7)
    merged_pr_day = date.today() - timedelta(days=4)
    return {
        "followers": 20,
        "following": 10,
        "watchers": 8,
        "total_commits": 500,
        "total_prs": 120,
        "total_issues": 180,
        "open_issues_count": 24,
        "orgs_count": 2,
        "network_count": 40,
        "public_gists": 3,
        "pr_review_count": 12,
        "total_repos_contributed": 30,
        "issue_stats": {"open_count": 24, "closed_count": 156},
        "commit_hour_distribution": {9: 4, 14: 8, 21: 5},
        "languages": {"Python": 900},
        "top_repos": [
            {
                "name": "py-0",
                "language": "Python",
                "stars": 10,
                "forks": 1,
                "topics": ["ai"],
            },
            {
                "name": "py-1",
                "language": "Python",
                "stars": 8,
                "forks": 1,
                "topics": ["viz"],
            },
            {
                "name": "py-2",
                "language": "Python",
                "stars": 7,
                "forks": 1,
                "topics": ["tools"],
            },
        ],
        "releases": [
            {"published_at": f"{release_day.isoformat()}T20:00:00Z", "name": "v1"}
        ],
        "recent_merged_prs": [
            {"merged_at": f"{merged_pr_day.isoformat()}T09:00:00Z", "title": "PR"}
        ],
    }


def test_build_daily_snapshots_terminal_day_contract() -> None:
    history = _history_for_days(3)
    metrics = _metrics_for_history()

    snaps_default = build_daily_snapshots(history, metrics)
    snaps_with_today = build_daily_snapshots(history, metrics, include_today=True)

    assert snaps_default[-1].day == date.today() - timedelta(days=1)
    assert snaps_with_today[-1].day == date.today()
    assert len(snaps_with_today) == len(snaps_default) + 1


def test_language_allocation_grows_gradually() -> None:
    history = _history_for_days(14)
    metrics = _metrics_for_history()
    snaps = build_daily_snapshots(history, metrics)

    first_val = snaps[0].metrics_dict["languages"].get("Python", 0)
    mid_val = snaps[6].metrics_dict["languages"].get("Python", 0)
    final_val = snaps[-1].metrics_dict["languages"].get("Python", 0)

    assert 0 < first_val < mid_val <= final_val
    assert final_val <= metrics["languages"]["Python"]


def test_atmospheric_inputs_are_not_frozen_across_timeline() -> None:
    history = _history_for_days(18)
    metrics = _metrics_for_history()
    snaps = build_daily_snapshots(history, metrics)

    issue_series = [s.metrics_dict["issue_stats"]["open_count"] for s in snaps]
    hour_peaks = [
        max(
            s.metrics_dict["commit_hour_distribution"],
            key=s.metrics_dict["commit_hour_distribution"].get,
        )
        for s in snaps
    ]

    assert len(set(issue_series)) > 1
    assert len(set(hour_peaks)) > 1
