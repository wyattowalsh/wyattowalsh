from __future__ import annotations

import re

import pytest

pytest.importorskip("numpy", reason="living-art generators require numpy")

from scripts.art.ink_garden import generate as generate_ink_garden  # noqa: E402
from scripts.art.shared import (  # noqa: E402
    compute_world_state,
    ensure_contrast,
    normalize_live_metrics,
    seed_hash,
    wcag_contrast_ratio,
)
from scripts.art.topography import generate as generate_topography  # noqa: E402


def _raw_metrics() -> dict:
    return {
        "label": "Contrast Check",
        "stars": 64,
        "forks": 14,
        "followers": 31,
        "following": 9,
        "watchers": 18,
        "open_issues_count": 9,
        "total_commits": 1200,
        "contributions_last_year": 340,
        "languages": {"Rust": 4400, "Go": 2800, "Python": 1200},
        "top_repos": [
            {
                "name": "aurora-core",
                "language": "Rust",
                "stars": 40,
                "forks": 9,
                "topics": ["systems", "visualization"],
                "description": "Night-heavy renderer",
                "updated_at": "2025-03-12T12:00:00Z",
            },
            {
                "name": "ridge-lab",
                "language": "Go",
                "stars": 16,
                "forks": 3,
                "topics": ["mapping", "automation"],
                "description": "Terrain experiments",
                "updated_at": "2025-03-18T12:00:00Z",
            },
        ],
        "contributions_calendar": [
            {"date": "2025-01-08", "count": 5},
            {"date": "2025-02-14", "count": 7},
            {"date": "2025-03-21", "count": 9},
        ],
        "commit_hour_distribution": {"23": 18, "0": 12, "1": 8},
        "recent_merged_prs": [
            {"date": f"2025-03-{day:02d}T12:00:00Z"}
            for day in range(1, 8)
        ],
        "issue_stats": {"closed_count": 1},
        "star_velocity": {"recent_rate": 9.5, "peak_rate": 14.0, "trend": "rising"},
        "contribution_streaks": {
            "current_streak_months": 8,
            "longest_streak_months": 13,
            "streak_active": True,
        },
    }


def _history() -> dict:
    return {
        "account_created": "2020-01-01T00:00:00Z",
        "repos": [
            {"name": "aurora-core", "date": "2023-07-10T00:00:00Z"},
            {"name": "ridge-lab", "date": "2024-02-18T00:00:00Z"},
        ],
        "stars": [
            {"date": "2024-02-01T00:00:00Z"},
            {"date": "2025-03-10T00:00:00Z"},
        ],
        "forks": [{"date": "2024-06-01T00:00:00Z"}],
        "contributions_monthly": {"2025-01": 22, "2025-02": 31, "2025-03": 37},
        "recent_merged_prs": [
            {"date": f"2025-03-{day:02d}T12:00:00Z"}
            for day in range(1, 8)
        ],
        "issue_stats": {"closed_count": 1},
        "commit_hour_distribution": {"23": 18, "0": 12, "1": 8},
        "star_velocity": {"recent_rate": 9.5, "peak_rate": 14.0, "trend": "rising"},
        "contribution_streaks": {
            "current_streak_months": 8,
            "longest_streak_months": 13,
            "streak_active": True,
        },
    }


def _normalized_metrics() -> dict:
    return normalize_live_metrics(
        _raw_metrics(),
        owner="contrast-check",
        history=_history(),
    )


def _high_contrast_color_count(
    svg: str,
    background: str,
    min_ratio: float = 4.5,
) -> int:
    colors = set(re.findall(r"#[0-9A-Fa-f]{6}", svg))
    return sum(
        1 for color in colors if wcag_contrast_ratio(color, background) >= min_ratio
    )


def test_night_world_state_palette_can_be_pushed_to_wcag_contrast() -> None:
    metrics = _normalized_metrics()
    world = compute_world_state(metrics)

    assert world.time_of_day == "night"
    assert world.weather == "stormy"

    for foreground in (world.palette["accent"], world.palette["glow"]):
        adjusted = ensure_contrast(foreground, world.palette["sky_top"])
        assert wcag_contrast_ratio(adjusted, world.palette["sky_top"]) >= 4.5


def test_dark_scene_generators_emit_multiple_high_contrast_colors() -> None:
    metrics = _normalized_metrics()
    world = compute_world_state(metrics)
    background = world.palette["sky_top"]

    svg_outputs = [
        generate_ink_garden(
            metrics,
            seed=seed_hash(metrics),
            maturity=0.95,
            timeline=False,
        ),
        generate_topography(metrics, seed="contrast-topo", timeline=False),
    ]

    for svg in svg_outputs:
        assert _high_contrast_color_count(svg, background) >= 3
