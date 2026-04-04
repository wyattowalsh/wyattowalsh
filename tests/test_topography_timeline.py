from __future__ import annotations

import re
from datetime import date, timedelta

import pytest
from defusedxml import ElementTree

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


def _group_data_attr(svg: str, group_id: str, name: str) -> str:
    match = re.search(rf'<g[^>]*id="{group_id}"[^>]*{name}="([^"]+)"', svg)
    assert match is not None
    return match.group(1)


def _group_markup(svg: str, group_id: str) -> str:
    match = re.search(rf'(<g[^>]*id="{group_id}"[^>]*>.*?</g>)', svg, re.DOTALL)
    assert match is not None
    return match.group(1)


def _topic_feature_markup(svg: str, topic: str) -> str:
    match = re.search(
        rf'(<g[^>]*class="[^"]*topic-feature[^"]*"[^>]*data-topic="{re.escape(topic)}"[^>]*>.*?</g>)',
        svg,
        re.DOTALL,
    )
    assert match is not None
    return match.group(1)


def _topic_feature_metrics() -> dict:
    return {
        "label": "Topo Topics",
        "account_created": "2022-01-01T00:00:00Z",
        "contributions_last_year": 580,
        "contributions_monthly": {
            "2023-01": 14,
            "2023-02": 21,
            "2023-03": 18,
            "2023-04": 24,
        },
        "repos": [
            {
                "name": "unrelated-peak",
                "language": "Rust",
                "stars": 80,
                "age_months": 36,
                "topics": ["systems"],
                "date": "2023-01-03T12:00:00Z",
            },
            {
                "name": "semantic-core",
                "language": "Python",
                "stars": 24,
                "age_months": 18,
                "topics": ["ai"],
                "date": "2023-01-18T12:00:00Z",
            },
            {
                "name": "floor-data",
                "language": "Go",
                "stars": 1,
                "age_months": 11,
                "topics": ["storage"],
                "date": "2023-01-25T12:00:00Z",
            },
            {
                "name": "agent-harbor",
                "language": "Python",
                "stars": 9,
                "age_months": 14,
                "topics": ["agents"],
                "date": "2023-02-12T12:00:00Z",
            },
            {
                "name": "pipeline-valley",
                "language": "Go",
                "stars": 7,
                "age_months": 9,
                "topics": ["automation"],
                "date": "2023-03-05T12:00:00Z",
            },
            {
                "name": "cli-pass",
                "language": "Rust",
                "stars": 17,
                "age_months": 6,
                "topics": ["cli"],
                "date": "2023-03-22T12:00:00Z",
            },
        ],
        "topic_clusters": {
            "ai": 1,
            "agents": 1,
            "automation": 1,
            "cli": 1,
        },
        "followers": 14,
        "forks": 5,
        "stars": 138,
        "total_commits": 1100,
    }


@pytest.fixture
def topic_feature_svg() -> str:
    return generate(
        _topic_feature_metrics(),
        seed="topo-topic-features",
        timeline=True,
        loop_duration=24.0,
    )


def test_topography_timeline_enabled_by_default() -> None:
    svg = generate(_sample_metrics(), seed="abc123")
    assert "@keyframes topoReveal" in svg
    assert 'class="tl-reveal"' in svg
    assert 'data-when="2023-01-05"' in svg
    assert "data-delay=" in svg


def test_topography_timeline_respects_repo_chronology_and_reveal_window() -> None:
    loop_duration = 24.0
    reveal_fraction = 0.6
    metrics = _sample_metrics()
    metrics["repos"][0]["age_months"] = 1
    metrics["repos"][1]["age_months"] = 48
    svg = generate(
        metrics,
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


def test_topography_timeline_falls_back_to_repo_ages_when_dates_are_missing() -> None:
    metrics = _sample_metrics()
    metrics["repos"][0].pop("date", None)
    metrics["repos"][1].pop("date", None)
    metrics["repos"][0]["age_months"] = 12
    metrics["repos"][1]["age_months"] = 2
    metrics["releases"] = [{"published_at": "2024-05-01T00:00:00Z"}]
    metrics["recent_merged_prs"] = [{"merged_at": "2024-04-15T00:00:00Z"}]

    svg = generate(metrics, seed="topo-age-fallback", timeline=True, loop_duration=24.0)
    rows = _timeline_delay_rows(svg)
    by_date: dict[str, list[float]] = {}
    for when, delay in rows:
        by_date.setdefault(when, []).append(delay)

    anchor = date(2024, 5, 1)
    older_repo_date = (anchor - timedelta(days=int(12 * 30.4))).isoformat()
    newer_repo_date = (anchor - timedelta(days=int(2 * 30.4))).isoformat()
    assert older_repo_date in by_date
    assert newer_repo_date in by_date
    assert max(by_date[older_repo_date]) < min(by_date[newer_repo_date])


def test_topography_age_only_inputs_remain_deterministic_without_other_dates() -> None:
    metrics = {
        "label": "Topo Age Only",
        "repos": [
            {"name": "alpha", "language": "Python", "stars": 5, "age_months": 12},
            {"name": "beta", "language": "Go", "stars": 2, "age_months": 2},
        ],
        "stars": 7,
        "followers": 4,
        "forks": 1,
    }

    svg_1 = generate(metrics, seed="age-only", timeline=True, loop_duration=24.0)
    svg_2 = generate(metrics, seed="age-only", timeline=True, loop_duration=24.0)

    assert svg_1 == svg_2


def test_topography_age_only_repo_delays_remain_ordered_for_older_histories() -> None:
    metrics = {
        "label": "Topo Age Spread",
        "repos": [
            {"name": "alpha", "language": "Python", "stars": 9, "age_months": 48},
            {"name": "beta", "language": "Go", "stars": 6, "age_months": 24},
            {"name": "gamma", "language": "Rust", "stars": 3, "age_months": 2},
        ],
        "stars": 18,
        "followers": 3,
        "forks": 1,
        "total_commits": 120,
    }

    svg = generate(metrics, seed="age-spread", timeline=True, loop_duration=24.0)
    rows = _timeline_delay_rows(svg)
    by_date: dict[str, list[float]] = {}
    for when, delay in rows:
        by_date.setdefault(when, []).append(delay)

    anchor = date(2024, 1, 1)
    oldest = (anchor - timedelta(days=int(48 * 30.4))).isoformat()
    middle = (anchor - timedelta(days=int(24 * 30.4))).isoformat()
    newest = (anchor - timedelta(days=int(2 * 30.4))).isoformat()

    assert oldest in by_date
    assert middle in by_date
    assert newest in by_date
    assert max(by_date[oldest]) < min(by_date[middle]) < min(by_date[newest])


def test_topography_timeline_can_be_disabled_for_legacy_opacity_mode() -> None:
    svg = generate(_sample_metrics(), seed="abc123", timeline=False, maturity=0.35)
    assert "@keyframes topoReveal" not in svg
    assert 'class="tl-reveal"' not in svg
    assert "data-delay=" not in svg
    assert "opacity=" in svg


def test_topography_topic_feature_leaders_do_not_duplicate_opacity_when_static(
) -> None:
    svg = generate(
        _topic_feature_metrics(),
        seed="topo-topic-features-static",
        timeline=False,
        maturity=0.35,
    )

    ElementTree.fromstring(svg)
    ai_markup = _topic_feature_markup(svg, "ai")
    leader = re.search(r'<path class="topic-feature-leader"[^>]+>', ai_markup)

    assert leader is not None
    assert leader.group(0).count('opacity="') == 1


def test_topography_timeline_output_is_deterministic_for_same_input() -> None:
    metrics = _sample_metrics()
    svg_1 = generate(metrics, seed="fixed-seed", timeline=True, loop_duration=24.0)
    svg_2 = generate(metrics, seed="fixed-seed", timeline=True, loop_duration=24.0)
    assert svg_1 == svg_2


def test_topography_timeline_keeps_all_repo_landmarks_with_low_maturity() -> None:
    svg = generate(
        _sample_metrics(),
        seed="abc123",
        timeline=True,
        maturity=0.02,
        loop_duration=24.0,
    )

    assert ">alpha</text>" in svg
    assert ">beta</text>" in svg
    assert 'data-when="2023-03-12"' in svg


def test_topography_prefers_daily_activity_series_when_available() -> None:
    metrics = _sample_metrics()
    metrics["contributions_daily"] = {"2023-02-20": 25}
    metrics["contributions_monthly"] = {"2023-01": 1, "2023-02": 1, "2023-03": 30}

    svg = generate(metrics, seed="topo-daily", timeline=True, loop_duration=24.0)

    assert 'data-activity-series="hybrid"' in svg
    assert 'data-when="2023-02-20"' in svg
    assert _data_attr(svg, "data-central-rise-date").startswith("2023-03-")


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


def test_topography_river_reveals_do_not_precede_river_carve_date() -> None:
    metrics = _sample_metrics()
    metrics["star_velocity"] = {
        "recent_rate": 6.0,
        "peak_rate": 10.0,
        "trend": "rising",
    }

    svg = generate(metrics, seed="topo-river-carve", timeline=True, loop_duration=24.0)

    river_markup = _group_markup(svg, "river-system")
    river_dates = {when for when, _delay in _timeline_delay_rows(river_markup)}
    river_carve_date = _data_attr(svg, "data-river-carve-date")

    assert river_dates
    assert min(river_dates) >= river_carve_date


def test_topography_chronology_trail_waits_for_oldest_repo_date() -> None:
    svg = generate(
        _sample_metrics(), seed="topo-trail", timeline=True, loop_duration=24.0
    )

    trail_dates = {
        when
        for when, _delay in _timeline_delay_rows(_group_markup(svg, "chronology-trail"))
    }

    assert trail_dates
    assert min(trail_dates) >= "2023-01-05"
    assert "2023-03-12" in trail_dates
    assert max(trail_dates) >= _data_attr(svg, "data-central-rise-date")


def test_topography_adds_portfolio_footprint_summary_and_settlement_tier() -> None:
    metrics = _sample_metrics()
    metrics["followers"] = 260

    svg = generate(metrics, seed="topo-footprint")

    assert 'id="portfolio-footprint"' in svg
    assert 'data-settlement-tier="town"' in svg
    assert "2 repos" in svg
    assert "Town reach" in svg


def test_topography_release_flags_follow_release_dates() -> None:
    metrics = _sample_metrics()
    metrics["releases"] = [
        {"name": "v0.1.0", "published_at": "2023-01-25T12:00:00Z"},
        {"name": "v0.2.0", "published_at": "2023-03-25T12:00:00Z"},
    ]

    svg = generate(
        metrics, seed="topo-release-flags", timeline=True, loop_duration=24.0
    )

    assert 'data-release-date="2023-01-25"' in svg
    assert 'data-release-date="2023-03-25"' in svg


def test_topography_release_flags_wait_for_host_terrain() -> None:
    metrics = {
        "label": "Topo Release Terrain",
        "account_created": "2022-01-01T00:00:00Z",
        "contributions_monthly": {"2023-03": 30},
        "repos": [
            {
                "name": "late-peak",
                "language": "Python",
                "stars": 40,
                "age_months": 1,
                "date": "2023-03-20T00:00:00Z",
            }
        ],
        "stars": 40,
        "followers": 0,
        "forks": 0,
        "total_commits": 200,
        "releases": [{"name": "v0.1.0", "published_at": "2023-01-25T00:00:00Z"}],
    }

    svg = generate(
        metrics, seed="topo-release-terrain", timeline=True, loop_duration=24.0
    )

    assert 'data-release-date="2023-01-25"' in svg
    assert _data_attr(svg, "data-release-reveal-date") >= "2023-03-20"


def test_topography_maps_repo_recency_and_issue_pressure_into_contour_density() -> None:
    legacy_metrics = _sample_metrics()
    legacy_metrics["repos"] = [
        {
            "name": "alpha",
            "language": "Python",
            "stars": 12,
            "age_months": 24,
            "date": "2022-01-05T12:00:00Z",
        },
        {
            "name": "beta",
            "language": "Go",
            "stars": 3,
            "age_months": 22,
            "date": "2022-03-12T00:00:00Z",
        },
    ]
    legacy_metrics["total_issues"] = 0

    recent_metrics = _sample_metrics()
    recent_metrics["total_issues"] = 32

    legacy_svg = generate(legacy_metrics, seed="topo-recency")
    recent_svg = generate(recent_metrics, seed="topo-recency")

    assert (
        _group_data_attr(legacy_svg, "topography-contours", "data-recency-band")
        == "legacy"
    )
    assert (
        _group_data_attr(recent_svg, "topography-contours", "data-recency-band")
        == "recent"
    )

    legacy_roughness = float(
        _group_data_attr(legacy_svg, "topography-contours", "data-contour-roughness")
    )
    recent_roughness = float(
        _group_data_attr(recent_svg, "topography-contours", "data-contour-roughness")
    )
    legacy_foothills = int(
        _group_data_attr(legacy_svg, "topography-contours", "data-foothill-count")
    )
    recent_foothills = int(
        _group_data_attr(recent_svg, "topography-contours", "data-foothill-count")
    )

    assert legacy_roughness < recent_roughness
    assert legacy_foothills < recent_foothills
    assert "foothill-contour" not in legacy_svg
    assert re.search(r'class="[^"]*foothill-contour', recent_svg)


@pytest.mark.parametrize(
    ("topic", "expected_repo"),
    [
        ("ai", "semantic-core"),
        ("agents", "agent-harbor"),
        ("automation", "pipeline-valley"),
        ("cli", "cli-pass"),
    ],
)
def test_topography_topic_features_bind_to_matching_topic_repos(
    topic_feature_svg: str, topic: str, expected_repo: str
) -> None:
    markup = _topic_feature_markup(topic_feature_svg, topic)

    assert _data_attr(markup, "data-repo") == expected_repo
    assert _data_attr(markup, "data-topic-match") == "direct"


def test_topography_topic_features_add_legible_promoted_labels(
    topic_feature_svg: str,
) -> None:
    ai_markup = _topic_feature_markup(topic_feature_svg, "ai")
    agents_markup = _topic_feature_markup(topic_feature_svg, "agents")
    automation_markup = _topic_feature_markup(topic_feature_svg, "automation")

    assert "Mt. Ai" in ai_markup
    assert "Agents Lake" in agents_markup
    assert "Automation Valley" in automation_markup
    assert 'class="topic-feature-leader"' in ai_markup
    assert float(_data_attr(automation_markup, "data-anchor-clearance")) >= 0.0


def test_topography_label_avoidance_prefers_clear_candidates() -> None:
    label_x, label_y, clearance = _choose_label_anchor(
        150,
        100,
        [(12, 0), (0, -20), (-20, -20), (18, 14)],
        [[(100, 100), (200, 100)], [(150, 80), (150, 160)]],
    )

    assert (label_x, label_y) == (130, 80)
    assert clearance >= 20
