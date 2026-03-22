from __future__ import annotations

import re

import pytest

pytest.importorskip("numpy", reason="numpy is required by scripts.art.ink_garden")

from scripts.art.ink_garden import (
    generate,  # noqa: E402
    seed_hash,  # noqa: E402
)


def _extract_timeline_points(svg: str) -> list[tuple[str, float]]:
    return [
        (when, float(delay))
        for delay, when in re.findall(
            r'data-delay="([0-9.]+)" data-when="([0-9-]+)"', svg
        )
    ]


def _sample_metrics() -> dict:
    return {
        "label": "Ink Timeline Test",
        "account_created": "2022-01-01T00:00:00Z",
        "total_commits": 1200,
        "stars": 40,
        "contributions_last_year": 320,
        "followers": 25,
        "forks": 7,
        "network_count": 12,
        "repos": [
            {
                "name": "seed-repo",
                "language": "Python",
                "stars": 8,
                "age_months": 24,
                "date": "2023-01-05T12:00:00Z",
            },
            {
                "name": "growth-repo",
                "language": "Go",
                "stars": 18,
                "age_months": 16,
                "date": "2023-03-12T00:00:00Z",
            },
        ],
        "contributions_monthly": {
            "2023-01": 10,
            "2023-02": 14,
            "2023-03": 22,
        },
    }


def test_ink_garden_timeline_can_be_enabled() -> None:
    metrics = _sample_metrics()
    svg = generate(metrics, seed=seed_hash(metrics), timeline=True, loop_duration=24.0)
    assert "@keyframes inkGardenReveal" in svg
    assert 'class="tl-reveal"' in svg
    assert 'data-when="2023-01-05"' in svg
    assert "data-delay=" in svg


def test_ink_garden_timeline_repo_dates_follow_chronology_in_delays() -> None:
    metrics = _sample_metrics()
    svg = generate(metrics, seed=seed_hash(metrics), timeline=True, loop_duration=24.0)
    timeline_points = _extract_timeline_points(svg)
    assert timeline_points

    delays_by_date: dict[str, list[float]] = {}
    for when, delay in timeline_points:
        delays_by_date.setdefault(when, []).append(delay)

    earlier_repo_date = "2023-01-05"
    later_repo_date = "2023-03-12"
    assert earlier_repo_date in delays_by_date
    assert later_repo_date in delays_by_date

    assert min(delays_by_date[earlier_repo_date]) < min(delays_by_date[later_repo_date])
    assert max(delays_by_date[earlier_repo_date]) < max(delays_by_date[later_repo_date])


def test_ink_garden_timeline_delays_stay_within_configured_bounds() -> None:
    metrics = _sample_metrics()
    loop_duration = 24.0
    reveal_fraction = 0.93
    svg = generate(
        metrics,
        seed=seed_hash(metrics),
        timeline=True,
        loop_duration=loop_duration,
        reveal_fraction=reveal_fraction,
    )
    timeline_points = _extract_timeline_points(svg)
    assert timeline_points

    delays = [delay for _, delay in timeline_points]
    reveal_window = loop_duration * reveal_fraction
    jitter_window = 0.12 * loop_duration
    expected_upper_bound = min(loop_duration, reveal_window + jitter_window)

    assert min(delays) >= 0.0
    assert max(delays) <= loop_duration
    assert max(delays) <= expected_upper_bound


def test_ink_garden_timeline_disabled_uses_legacy_opacity_mode() -> None:
    metrics = _sample_metrics()
    svg = generate(metrics, seed=seed_hash(metrics), timeline=False, maturity=0.35)
    assert "@keyframes inkGardenReveal" not in svg
    assert 'class="tl-reveal"' not in svg
    assert "data-delay=" not in svg
    assert "opacity=" in svg


def test_ink_garden_timeline_is_deterministic_for_same_input() -> None:
    metrics = _sample_metrics()
    fixed_seed = seed_hash(metrics)
    svg_1 = generate(metrics, seed=fixed_seed, timeline=True, loop_duration=30.0)
    svg_2 = generate(metrics, seed=fixed_seed, timeline=True, loop_duration=30.0)
    assert svg_1 == svg_2
