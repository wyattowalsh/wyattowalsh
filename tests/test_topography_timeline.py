from __future__ import annotations

import re

from scripts.art.topography import generate


def _sample_metrics() -> dict:
    return {
        "label": "Topo Test",
        "account_created": "2022-01-01T00:00:00Z",
        "contributions_last_year": 420,
        "contributions_monthly": {
            "2023-01": 10,
            "2023-02": 14,
            "2023-03": 22,
        },
        "repos": [
            {
                "name": "alpha",
                "language": "Python",
                "stars": 12,
                "age_months": 24,
                "date": "2023-01-05T12:00:00Z",
            },
            {
                "name": "beta",
                "language": "Go",
                "stars": 3,
                "age_months": 12,
                "date": "2023-03-12T00:00:00Z",
            },
        ],
        "followers": 30,
        "forks": 8,
        "stars": 44,
        "total_commits": 800,
    }


def _timeline_delay_rows(svg: str) -> list[tuple[str, float]]:
    rows: list[tuple[str, float]] = []
    for delay, when in re.findall(r'data-delay="([0-9]+(?:\.[0-9]+)?)"\s+data-when="(\d{4}-\d{2}-\d{2})"', svg):
        rows.append((when, float(delay)))
    return rows


def test_topography_timeline_enabled_by_default() -> None:
    svg = generate(_sample_metrics(), seed="abc123")
    assert "@keyframes topoReveal" in svg
    assert 'class="tl-reveal"' in svg
    assert 'data-when="2023-01-05"' in svg
    assert "data-delay=" in svg


def test_topography_timeline_respects_repo_chronology_and_reveal_window() -> None:
    loop_duration = 24.0
    reveal_fraction = 0.6
    svg = generate(
        _sample_metrics(),
        seed="abc123",
        timeline=True,
        loop_duration=loop_duration,
        reveal_fraction=reveal_fraction,
    )

    rows = _timeline_delay_rows(svg)
    assert rows

    by_date: dict[str, list[float]] = {}
    for when, delay in rows:
        by_date.setdefault(when, []).append(delay)

    early_repo_date = "2023-01-05"
    later_repo_date = "2023-03-12"
    assert early_repo_date in by_date
    assert later_repo_date in by_date
    assert max(by_date[early_repo_date]) < min(by_date[later_repo_date])

    reveal_end = loop_duration * reveal_fraction
    for _, delay in rows:
        assert 0.0 <= delay <= reveal_end + 1e-9


def test_topography_timeline_can_be_disabled_for_legacy_opacity_mode() -> None:
    svg = generate(_sample_metrics(), seed="abc123", timeline=False, maturity=0.35)
    assert "@keyframes topoReveal" not in svg
    assert 'class="tl-reveal"' not in svg
    assert "data-delay=" not in svg
    assert "opacity=" in svg


def test_topography_timeline_output_is_deterministic_for_same_input() -> None:
    metrics = _sample_metrics()
    svg_1 = generate(metrics, seed="fixed-seed", timeline=True, loop_duration=24.0)
    svg_2 = generate(metrics, seed="fixed-seed", timeline=True, loop_duration=24.0)
    assert svg_1 == svg_2
