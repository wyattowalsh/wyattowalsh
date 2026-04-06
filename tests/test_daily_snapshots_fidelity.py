"""Focused fidelity tests for daily snapshot reconstruction."""

from __future__ import annotations

import inspect
from datetime import date, timedelta

import pytest

pytest.importorskip("numpy", reason="scripts.art.shared requires numpy")

from scripts.art import daily_snapshots as daily_snapshots_module  # noqa: E402
from scripts.art.daily_snapshots import (
    build_daily_snapshots,  # noqa: E402
    sample_frames,  # noqa: E402
)
from scripts.art.shared import (  # noqa: E402
    MAX_REPOS,
    select_primary_repos,
    stable_repo_visual_order,
)
from scripts.art.timelapse import DEFAULT_PUBLISHED_MAX_FRAMES  # noqa: E402


def _history_for_days(days: int = 14, *, anchor_day: date) -> dict:
    start = anchor_day - timedelta(days=days)
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


def _metrics_for_history(*, anchor_day: date) -> dict:
    release_day = anchor_day - timedelta(days=7)
    merged_pr_day = anchor_day - timedelta(days=4)
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


def _freeze_timeline_end(
    monkeypatch: pytest.MonkeyPatch,
    *,
    anchor_day: date,
) -> None:
    monkeypatch.setattr(
        daily_snapshots_module,
        "_timeline_end_day",
        lambda *, include_today: (
            anchor_day if include_today else anchor_day - timedelta(days=1)
        ),
    )


def test_build_daily_snapshots_terminal_day_contract(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    anchor_day = date(2025, 1, 15)
    _freeze_timeline_end(monkeypatch, anchor_day=anchor_day)
    history = _history_for_days(3, anchor_day=anchor_day)
    metrics = _metrics_for_history(anchor_day=anchor_day)

    snaps_default = build_daily_snapshots(
        history,
        metrics,
        include_today=False,
    )
    snaps_with_today = build_daily_snapshots(
        history,
        metrics,
        include_today=True,
    )

    assert snaps_default[-1].day == anchor_day - timedelta(days=1)
    assert snaps_with_today[-1].day == anchor_day
    assert len(snaps_with_today) == len(snaps_default) + 1


def test_language_allocation_grows_gradually(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    anchor_day = date(2025, 1, 15)
    _freeze_timeline_end(monkeypatch, anchor_day=anchor_day)
    history = _history_for_days(14, anchor_day=anchor_day)
    metrics = _metrics_for_history(anchor_day=anchor_day)
    snaps = build_daily_snapshots(history, metrics)

    first_val = snaps[0].metrics_dict["languages"].get("Python", 0)
    mid_val = snaps[6].metrics_dict["languages"].get("Python", 0)
    final_val = snaps[-1].metrics_dict["languages"].get("Python", 0)

    assert 0 < first_val < mid_val <= final_val
    assert final_val <= metrics["languages"]["Python"]


def test_atmospheric_inputs_are_not_frozen_across_timeline(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    anchor_day = date(2025, 1, 15)
    _freeze_timeline_end(monkeypatch, anchor_day=anchor_day)
    history = _history_for_days(18, anchor_day=anchor_day)
    metrics = _metrics_for_history(anchor_day=anchor_day)
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


def test_repo_star_allocation_stays_monotonic_when_late_repo_enters(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    anchor_day = date(2025, 1, 15)
    _freeze_timeline_end(monkeypatch, anchor_day=anchor_day)
    start = anchor_day - timedelta(days=12)
    late_repo_day = start + timedelta(days=6)

    history = {
        "account_created": f"{start.isoformat()}T00:00:00Z",
        "repos": [
            {"date": start.isoformat(), "name": "foundation"},
            {"date": late_repo_day.isoformat(), "name": "breakout"},
        ],
        "stars": [
            {
                "date": f"{(start + timedelta(days=1)).isoformat()}T12:00:00Z",
                "user": "a",
            },
            {
                "date": f"{(start + timedelta(days=2)).isoformat()}T12:00:00Z",
                "user": "b",
            },
            {
                "date": f"{(start + timedelta(days=3)).isoformat()}T12:00:00Z",
                "user": "c",
            },
            {
                "date": f"{(start + timedelta(days=8)).isoformat()}T12:00:00Z",
                "user": "d",
            },
        ],
        "forks": [],
        "contributions_daily": {
            (start + timedelta(days=i)).isoformat(): 3 for i in range(13)
        },
        "contributions_monthly": {f"{start.year:04d}-{start.month:02d}": 39},
    }
    metrics = _metrics_for_history(anchor_day=anchor_day)
    metrics["top_repos"] = [
        {
            "name": "foundation",
            "language": "Python",
            "stars": 10,
            "forks": 1,
            "topics": ["core"],
        },
        {
            "name": "breakout",
            "language": "Python",
            "stars": 250,
            "forks": 1,
            "topics": ["viral"],
        },
    ]

    snaps = build_daily_snapshots(history, metrics)
    foundation_by_day = {
        snap.day: next(
            repo["stars"]
            for repo in snap.metrics_dict["repos"]
            if repo["name"] == "foundation"
        )
        for snap in snaps
    }

    foundation_series = [foundation_by_day[snap.day] for snap in snaps]

    assert foundation_series == sorted(foundation_series)
    assert all(
        sum(repo["stars"] for repo in snap.metrics_dict["repos"])
        == snap.metrics_dict["stars"]
        for snap in snaps
    )
    assert foundation_by_day[late_repo_day - timedelta(days=1)] > 0
    assert (
        foundation_by_day[late_repo_day]
        == foundation_by_day[late_repo_day - timedelta(days=1)]
    )


def test_select_primary_repos_preserves_all_repos_under_shared_contract() -> None:
    repos = [
        {"name": "foundation", "stars": 6, "forks": 1, "age_months": 24},
        {"name": "late-surge", "stars": 250, "forks": 18, "age_months": 2},
    ]

    primary, overflow = select_primary_repos(repos, limit=1)

    assert [repo["name"] for repo in primary] == ["foundation", "late-surge"]
    assert overflow == []


def test_build_daily_snapshots_freezes_repo_visual_order(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    anchor_day = date(2025, 1, 15)
    _freeze_timeline_end(monkeypatch, anchor_day=anchor_day)
    history = _history_for_days(20, anchor_day=anchor_day)
    start = date.fromisoformat(history["account_created"][:10])
    repo_names = [f"core-{index}" for index in range(MAX_REPOS)]
    repo_names.extend(["shadow-repo", "late-surge"])
    repo_dates = [start + timedelta(days=index) for index in range(len(repo_names))]
    history["repos"] = [
        {"date": repo_date.isoformat(), "name": repo_name}
        for repo_date, repo_name in zip(repo_dates, repo_names, strict=True)
    ]

    metrics = _metrics_for_history(anchor_day=anchor_day)
    metrics["top_repos"] = [
        {
            "name": repo_name,
            "language": "Python",
            "stars": 24 - index,
            "forks": 2,
            "topics": ["core"],
        }
        for index, repo_name in enumerate(repo_names[:MAX_REPOS])
    ]
    metrics["top_repos"].extend(
        [
            {
                "name": "shadow-repo",
                "language": "Python",
                "stars": 1,
                "forks": 0,
                "topics": [],
            },
            {
                "name": "late-surge",
                "language": "Go",
                "stars": 180,
                "forks": 28,
                "topics": ["automation", "viz"],
                "description": "Late repo with enduring prominence.",
            },
        ]
    )

    terminal_day = anchor_day - timedelta(days=1)
    final_repos = []
    for repo_date, repo in zip(repo_dates, metrics["top_repos"], strict=True):
        final_repo = dict(repo)
        final_repo["age_months"] = max(
            1,
            (terminal_day.year - repo_date.year) * 12
            + (terminal_day.month - repo_date.month),
        )
        final_repos.append(final_repo)
    expected_names = stable_repo_visual_order(final_repos)

    snaps = build_daily_snapshots(history, metrics)

    assert snaps
    assert {
        tuple(snap.metrics_dict["repo_visual_order"]) for snap in snaps
    } == {tuple(expected_names)}
    assert all(
        "canonical_primary_repo_names" not in snap.metrics_dict for snap in snaps
    )
    assert all(
        [repo["name"] for repo in snap.metrics_dict["repos"]]
        == expected_names[: len(snap.metrics_dict["repos"])]
        for snap in snaps
    )


def test_build_daily_snapshots_prefers_full_repo_inventory_over_top_repos(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    anchor_day = date(2025, 1, 15)
    _freeze_timeline_end(monkeypatch, anchor_day=anchor_day)
    start = anchor_day - timedelta(days=6)
    history = {
        "account_created": f"{start.isoformat()}T00:00:00Z",
        "repos": [
            {"date": start.isoformat(), "name": "alpha"},
            {"date": (start + timedelta(days=2)).isoformat(), "name": "beta"},
        ],
        "stars": [],
        "forks": [],
        "contributions_daily": {
            (start + timedelta(days=i)).isoformat(): 2 for i in range(7)
        },
        "contributions_monthly": {f"{start.year:04d}-{start.month:02d}": 14},
    }
    metrics = _metrics_for_history(anchor_day=anchor_day)
    metrics["top_repos"] = [
        {
            "name": "alpha",
            "language": "Python",
            "stars": 10,
            "forks": 1,
            "topics": ["core"],
        }
    ]
    metrics["repos"] = [
        {
            "name": "alpha",
            "language": "Python",
            "stars": 10,
            "forks": 1,
            "topics": ["core"],
        },
        {
            "name": "beta",
            "language": "Go",
            "stars": 3,
            "forks": 1,
            "topics": ["viz"],
            "description": "Secondary repo that should still retain details.",
        },
    ]

    snaps = build_daily_snapshots(history, metrics)
    final_repos = snaps[-1].metrics_dict["repos"]

    assert [repo["name"] for repo in final_repos] == ["alpha", "beta"]
    beta = next(repo for repo in final_repos if repo["name"] == "beta")
    assert beta["language"] == "Go"
    assert beta["topics"] == ["viz"]
    assert snaps[-1].metrics_dict["repo_visual_order"] == ["alpha", "beta"]


def test_build_daily_snapshots_clamps_maturity_when_rolling_signals_fade(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    anchor_day = date(2026, 1, 15)
    _freeze_timeline_end(monkeypatch, anchor_day=anchor_day)
    history = _history_for_days(400, anchor_day=anchor_day)
    start = date.fromisoformat(history["account_created"][:10])
    history["contributions_daily"] = {
        start.isoformat(): 120,
        (start + timedelta(days=1)).isoformat(): 120,
    }
    history["contributions_monthly"] = {f"{start.year:04d}-{start.month:02d}": 240}
    metrics = _metrics_for_history(anchor_day=anchor_day)

    monkeypatch.setattr(
        daily_snapshots_module,
        "compute_maturity",
        lambda metrics: 0.85 if metrics.get("contributions_last_year", 0) > 0 else 0.25,
    )

    snaps = build_daily_snapshots(history, metrics)
    maturities = [snap.maturity for snap in snaps]

    assert any(snap.metrics_dict["contributions_last_year"] == 0 for snap in snaps)
    assert maturities == sorted(maturities)
    assert maturities[-1] == 0.85


def test_sample_frames_default_matches_published_contract() -> None:
    max_frames_default = (
        inspect.signature(sample_frames).parameters["max_frames"].default
    )
    assert max_frames_default == DEFAULT_PUBLISHED_MAX_FRAMES == 120
