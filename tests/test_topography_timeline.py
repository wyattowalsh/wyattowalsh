from __future__ import annotations

import re

from scripts.art.topography import _choose_label_anchor, generate


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
    matches = re.findall(
        r'data-delay="([0-9]+(?:\.[0-9]+)?)"\s+data-when="(\d{4}-\d{2}-\d{2})"',
        svg,
    )
    for delay, when in matches:
        rows.append((when, float(delay)))
    return rows


def _data_attr(svg: str, name: str) -> str:
    match = re.search(rf'{name}="([^"]+)"', svg)
    assert match is not None
    return match.group(1)


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


def test_topography_maps_commit_hours_and_star_velocity_into_svg_metadata() -> None:
    midday_metrics = _sample_metrics()
    midday_metrics["commit_hour_distribution"] = {12: 14, 13: 8, 14: 3}
    midday_metrics["star_velocity"] = {"recent_rate": 0.5, "peak_rate": 1.0}

    night_metrics = _sample_metrics()
    night_metrics["commit_hour_distribution"] = {23: 18, 0: 10, 1: 6}
    night_metrics["star_velocity"] = {
        "recent_rate": 6.0,
        "peak_rate": 10.0,
        "trend": "rising",
    }

    midday_svg = generate(midday_metrics, seed="topo-signals")
    night_svg = generate(night_metrics, seed="topo-signals")

    midday_altitude = float(_data_attr(midday_svg, "data-sun-altitude"))
    night_altitude = float(_data_attr(night_svg, "data-sun-altitude"))
    midday_azimuth = float(_data_attr(midday_svg, "data-sun-azimuth"))
    night_azimuth = float(_data_attr(night_svg, "data-sun-azimuth"))

    assert midday_altitude > night_altitude
    assert midday_azimuth != night_azimuth
    assert 'data-flow-tier="still"' in midday_svg
    assert 'id="river-system"' in night_svg
    assert 'data-flow-tier="swift"' in night_svg


def test_topography_adds_portfolio_footprint_summary_and_settlement_tier() -> None:
    metrics = _sample_metrics()
    metrics["followers"] = 260

    svg = generate(metrics, seed="topo-footprint")

    assert 'id="portfolio-footprint"' in svg
    assert 'data-settlement-tier="town"' in svg
    assert "2 repos" in svg
    assert "Town reach" in svg


def test_topography_label_avoidance_prefers_clear_candidates() -> None:
    label_x, label_y, clearance = _choose_label_anchor(
        150,
        100,
        [(12, 0), (0, -20), (-20, -20), (18, 14)],
        [[(100, 100), (200, 100)], [(150, 80), (150, 160)]],
    )

    assert (label_x, label_y) == (130, 80)
    assert clearance >= 20
