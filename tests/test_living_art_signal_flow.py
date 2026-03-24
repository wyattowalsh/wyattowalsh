"""Signal-flow guardrails for normalized GitHub metrics reaching living-art output."""

from __future__ import annotations

import pytest

pytest.importorskip("numpy", reason="living-art generators require numpy")

from scripts.art.cosmic_genesis import render_svg as render_cosmic_genesis  # noqa: E402
from scripts.art.ink_garden import generate as generate_ink_garden  # noqa: E402
from scripts.art.shared import normalize_live_metrics, seed_hash  # noqa: E402
from scripts.art.topography import generate as generate_topography  # noqa: E402
from scripts.art.unfurling_spiral import (
    render_svg as render_unfurling_spiral,  # noqa: E402
)


def _raw_metrics() -> dict:
    return {
        "label": "Signal Flow",
        "stars": 52,
        "forks": 11,
        "followers": 48,
        "watchers": 14,
        "open_issues_count": 4,
        "total_commits": 820,
        "contributions_last_year": 260,
        "languages": {"Python": 8000, "Go": 3200},
        "top_repos": [
            {
                "name": "orchid-core",
                "language": "Python",
                "stars": 36,
                "forks": 7,
                "topics": ["ai", "agents"],
                "description": "Signal-rich botanical engine",
                "updated_at": "2025-02-10T12:00:00Z",
            },
            {
                "name": "ridge-cli",
                "language": "Go",
                "stars": 18,
                "forks": 2,
                "topics": ["cli", "automation"],
                "description": "Cartographic automation utilities",
                "updated_at": "2025-03-15T12:00:00Z",
            },
        ],
        "contributions_calendar": [
            {"date": "2025-01-02", "count": 3},
            {"date": "2025-01-15", "count": 5},
            {"date": "2025-02-10", "count": 8},
        ],
    }


def _history() -> dict:
    return {
        "account_created": "2020-01-01T00:00:00Z",
        "repos": [
            {"name": "orchid-core", "date": "2024-01-10T00:00:00Z"},
            {"name": "ridge-cli", "date": "2024-07-05T00:00:00Z"},
        ],
        "contributions_monthly": {"2025-01": 18, "2025-02": 24},
        "star_velocity": {"recent_rate": 4.5, "peak_rate": 7.0, "trend": "rising"},
        "contribution_streaks": {
            "current_streak_months": 6,
            "longest_streak_months": 9,
            "streak_active": True,
        },
    }


def _animated_history(metrics: dict) -> dict:
    return {
        **_history(),
        "stars": [
            {"date": "2024-01-10T00:00:00Z"},
            {"date": "2025-02-14T00:00:00Z"},
        ],
        "forks": [{"date": "2024-03-01T00:00:00Z"}],
        "repos": metrics["repos"],
        "current_metrics": metrics,
    }


def test_normalize_live_metrics_retains_enrichment_fields() -> None:
    metrics = normalize_live_metrics(
        _raw_metrics(), owner="signal-flow", history=_history()
    )

    assert len(metrics["repos"]) == 2
    assert metrics["repos"][0]["age_months"] >= 1
    assert metrics["topic_clusters"] == {
        "ai": 1,
        "agents": 1,
        "cli": 1,
        "automation": 1,
    }
    assert metrics["language_count"] == 2
    assert metrics["language_diversity"] > 0.0
    assert metrics["star_velocity"]["recent_rate"] == 4.5
    assert metrics["contribution_streaks"]["current_streak_months"] == 6


def test_normalized_signals_reach_ink_garden_output() -> None:
    metrics = normalize_live_metrics(
        _raw_metrics(), owner="signal-flow", history=_history()
    )
    svg = generate_ink_garden(metrics, seed=seed_hash(metrics), maturity=0.9)

    assert 'id="fireflies"' in svg
    assert "ai · agents" in svg


def test_normalized_topic_clusters_reach_topography_output() -> None:
    metrics = normalize_live_metrics(
        _raw_metrics(), owner="signal-flow", history=_history()
    )
    svg = generate_topography(metrics, seed="signal-flow")

    assert "Mt. Ai" in svg


def test_topography_topic_cluster_strength_reaches_annotations() -> None:
    metrics = normalize_live_metrics(
        _raw_metrics(), owner="signal-flow", history=_history()
    )
    metrics["topic_clusters"] = {
        "ai": 3,
        "agents": 2,
        "automation": 2,
        "cli": 1,
    }
    metrics["repos"] = [
        {
            "name": "orchid-core",
            "language": "Python",
            "stars": 36,
            "age_months": 15,
            "topics": ["ai", "agents"],
            "date": "2025-02-10T12:00:00Z",
        },
        {
            "name": "ridge-cli",
            "language": "Go",
            "stars": 18,
            "age_months": 11,
            "topics": ["cli", "automation"],
            "date": "2025-03-15T12:00:00Z",
        },
        {
            "name": "garden-lab",
            "language": "Python",
            "stars": 12,
            "age_months": 9,
            "topics": ["ai", "automation"],
            "date": "2025-01-28T12:00:00Z",
        },
        {
            "name": "signal-notes",
            "language": "Python",
            "stars": 8,
            "age_months": 6,
            "topics": ["agents"],
            "date": "2024-12-20T12:00:00Z",
        },
    ]

    svg = generate_topography(metrics, seed="signal-flow-clusters")

    assert "3 linked repos" in svg
    assert "2 linked repos" in svg
    assert svg.count("Mt. Ai") == 2


def test_signal_strength_reaches_cosmic_genesis_output() -> None:
    metrics = normalize_live_metrics(
        _raw_metrics(), owner="signal-flow", history=_history()
    )
    metrics["topic_clusters"] = {"ai": 3, "agents": 2, "automation": 1}

    svg = render_cosmic_genesis(_animated_history(metrics), duration=24.0)

    assert 'id="topic-constellations"' in svg
    assert "Ai Field" in svg
    assert "3 linked repos" in svg


def test_signal_strength_reaches_unfurling_spiral_output() -> None:
    metrics = normalize_live_metrics(
        _raw_metrics(), owner="signal-flow", history=_history()
    )
    metrics["topic_clusters"] = {"ai": 3, "agents": 2, "automation": 1}

    svg = render_unfurling_spiral(_animated_history(metrics), duration=24.0)

    assert 'id="topic-nexuses"' in svg
    assert "Ai Nexus" in svg
    assert "3 linked repos" in svg
