from __future__ import annotations

import re
from dataclasses import replace

import pytest
from defusedxml import ElementTree as ET

np = pytest.importorskip("numpy", reason="numpy is required by scripts.art.ferrofluid")

from scripts.art.ferrofluid import (  # noqa: E402
    FerrofluidSignals,
    _ambient_ripple_specs,
    _compute_ferrofluid_signals,
    _highlight_fill,
    _select_strongest_spikes,
    _spike_gradient_palette,
    generate,
)
from scripts.art.shared import LANG_HUES, compute_world_state  # noqa: E402


def _sample_metrics(
    *,
    repo_stars: tuple[int, int] = (12, 4),
    extra: dict | None = None,
) -> dict:
    metrics = {
        "label": "Ferro Test",
        "account_created": "2022-01-01T00:00:00Z",
        "total_commits": 800,
        "total_prs": 24,
        "total_issues": 16,
        "stars": 44,
        "contributions_last_year": 420,
        "followers": 30,
        "forks": 8,
        "watchers": 6,
        "network_count": 12,
        "languages": {"Python": 700, "Go": 280},
        "language_count": 2,
        "language_diversity": 0.94,
        "topic_clusters": {"automation": 1, "art": 1},
        "contribution_streaks": {
            "current_streak_months": 2,
            "longest_streak_months": 5,
            "streak_active": True,
        },
        "recent_merged_prs": [{"merged_at": "2023-03-12T00:00:00Z"}],
        "releases": [{"date": "2023-03-15T00:00:00Z"}],
        "issue_stats": {"closed_count": 12},
        "open_issues_count": 4,
        "pr_review_count": 5,
        "repos": [
            {
                "name": "alpha",
                "language": "Python",
                "stars": repo_stars[0],
                "forks": 5,
                "topics": ["automation", "art"],
                "age_months": 24,
                "date": "2023-01-05T12:00:00Z",
            },
            {
                "name": "beta",
                "language": "Go",
                "stars": repo_stars[1],
                "forks": 3,
                "topics": ["automation"],
                "age_months": 12,
                "date": "2023-03-12T00:00:00Z",
            },
        ],
        "contributions_daily": {
            "2023-02-24": 4,
            "2023-02-25": 5,
            "2023-02-26": 4,
            "2023-02-27": 6,
            "2023-02-28": 5,
            "2023-03-01": 4,
            "2023-03-02": 7,
            "2023-03-03": 5,
            "2023-03-04": 6,
            "2023-03-05": 7,
            "2023-03-06": 6,
            "2023-03-07": 5,
            "2023-03-08": 8,
            "2023-03-09": 6,
            "2023-03-10": 7,
            "2023-03-11": 5,
            "2023-03-12": 9,
        },
        "contributions_monthly": {
            "2023-01": 10,
            "2023-02": 14,
            "2023-03": 22,
        },
    }
    if extra:
        metrics.update(extra)
    return metrics


def _assert_valid_svg(svg: str) -> None:
    root = ET.fromstring(svg)
    assert root.tag.endswith("svg")
    assert root.attrib["viewBox"] == "0 0 800 800"


def _count_spike_gradients(svg: str) -> int:
    return len(re.findall(r'<linearGradient id="sg\d+"', svg))


def _count_dipole_markers(svg: str) -> int:
    return len(re.findall(r"<circle ", svg))


def _spike_polygons(svg: str) -> list[ET.Element]:
    root = ET.fromstring(svg)
    return [
        elem
        for elem in root.iter()
        if elem.tag.endswith("polygon")
        and elem.attrib.get("fill", "").startswith("url(#sg")
        and "filter" not in elem.attrib
    ]


def _root_attr(svg: str, name: str) -> float:
    root = ET.fromstring(svg)
    return float(root.attrib[name])


def _elements_with_attr(svg: str, attr: str, value: str) -> list[ET.Element]:
    root = ET.fromstring(svg)
    return [elem for elem in root.iter() if elem.attrib.get(attr) == value]


def _dipole_attr_values(svg: str, name: str) -> list[float]:
    return [
        float(elem.attrib[name])
        for elem in _elements_with_attr(svg, "data-role", "ferro-dipole")
    ]


def _dipole_x_positions(svg: str) -> list[float]:
    return [
        float(elem.attrib["cx"])
        for elem in _elements_with_attr(svg, "data-role", "ferro-dipole")
    ]


def _timeline_rows(svg: str) -> list[tuple[str, float]]:
    return [
        (when, float(delay))
        for delay, when in re.findall(
            r'data-delay="([0-9]+(?:\.[0-9]+)?)"\s+data-when="(\d{4}-\d{2}-\d{2})"',
            svg,
        )
    ]


def _sample_signals(**overrides: float | int) -> FerrofluidSignals:
    values = {
        "field_gain": 0.42,
        "fluid_response": 0.36,
        "surface_tension": 0.88,
        "iridescence": 18.0,
        "max_spikes": 120,
        "social_pull": 0.28,
        "build_volume": 0.24,
        "collaboration_heat": 0.18,
        "diversity": 0.22,
        "star_velocity_pull": 0.12,
        "traffic_heat": 0.14,
        "merge_cadence": 0.0,
        "release_charge": 0.0,
        "streak_heat": 0.20,
        "highlight_density": 0.26,
        "dipole_lift": 0.18,
    }
    values.update(overrides)
    return FerrofluidSignals(**values)


def test_ferrofluid_generate_returns_valid_svg() -> None:
    svg = generate(_sample_metrics(), seed="fixed-seed")

    _assert_valid_svg(svg)
    assert svg.lstrip().startswith("<svg")
    assert svg.rstrip().endswith("</svg>")


def test_ferrofluid_generate_is_deterministic_for_same_seed() -> None:
    metrics = _sample_metrics()

    svg_1 = generate(metrics, seed="fixed-seed", timeline=True, loop_duration=24.0)
    svg_2 = generate(metrics, seed="fixed-seed", timeline=True, loop_duration=24.0)

    assert svg_1 == svg_2


def test_ferrofluid_timeline_can_be_enabled_and_disabled() -> None:
    loop_duration = 24.0
    reveal_fraction = 0.6
    metrics = _sample_metrics()

    timeline_svg = generate(
        metrics,
        seed="fixed-seed",
        timeline=True,
        loop_duration=loop_duration,
        reveal_fraction=reveal_fraction,
    )
    legacy_svg = generate(metrics, seed="fixed-seed", timeline=False, maturity=0.5)
    timeline_rows = _timeline_rows(timeline_svg)
    by_date: dict[str, list[float]] = {}
    for when, delay in timeline_rows:
        by_date.setdefault(when, []).append(delay)

    assert "@keyframes ferroReveal" in timeline_svg
    assert 'class="tl-reveal"' in timeline_svg
    assert timeline_rows
    assert "2023-01-05" in by_date
    assert "2023-03-12" in by_date
    assert "data-delay=" in timeline_svg
    assert max(by_date["2023-01-05"]) < min(by_date["2023-03-12"])

    reveal_end = loop_duration * reveal_fraction
    for _, delay in timeline_rows:
        assert 0.0 <= delay <= reveal_end + 1e-9

    assert "@keyframes ferroReveal" not in legacy_svg
    assert 'class="tl-reveal"' not in legacy_svg
    assert "data-delay=" not in legacy_svg
    assert "opacity=" in legacy_svg


def test_ferrofluid_timeline_svg_keeps_static_spike_opacity_for_export() -> None:
    timeline_svg = generate(
        _sample_metrics(),
        seed="fixed-seed",
        timeline=True,
        loop_duration=24.0,
    )

    spike_polygons = _spike_polygons(timeline_svg)

    assert spike_polygons
    assert ".tl-reveal{opacity:0;" not in timeline_svg
    assert all(polygon.attrib.get("class") == "tl-reveal" for polygon in spike_polygons)
    assert all(
        polygon.attrib.get("opacity") == "0.95" for polygon in spike_polygons
    )


def test_ferrofluid_legacy_maturity_still_changes_shape() -> None:
    metrics = _sample_metrics()

    early_svg = generate(metrics, seed="fixed-seed", timeline=False, maturity=0.20)
    late_svg = generate(metrics, seed="fixed-seed", timeline=False, maturity=0.90)

    assert early_svg != late_svg


@pytest.mark.parametrize("metrics", [{}, _sample_metrics(repo_stars=(1, 0))])
def test_ferrofluid_handles_empty_and_minimal_metrics(metrics: dict) -> None:
    svg = generate(metrics, seed="fixed-seed", timeline=False)

    _assert_valid_svg(svg)


def test_ferrofluid_higher_repo_star_energy_yields_richer_spike_field() -> None:
    low_energy_svg = generate(
        _sample_metrics(repo_stars=(1, 1)),
        seed="fixed-seed",
        timeline=False,
        maturity=1.0,
    )
    high_energy_svg = generate(
        _sample_metrics(repo_stars=(100, 80)),
        seed="fixed-seed",
        timeline=False,
        maturity=1.0,
    )

    assert _count_spike_gradients(high_energy_svg) > _count_spike_gradients(
        low_energy_svg
    )


def test_ferrofluid_signals_scale_with_cumulative_snapshot_metrics() -> None:
    early_metrics = _sample_metrics(
        repo_stars=(1, 0),
        extra={
            "stars": 2,
            "forks": 0,
            "followers": 1,
            "watchers": 0,
            "network_count": 0,
            "total_commits": 28,
            "total_prs": 1,
            "total_issues": 0,
            "contributions_last_year": 24,
            "language_count": 1,
            "language_diversity": 0.0,
            "topic_clusters": {"automation": 1},
            "contribution_streaks": {
                "current_streak_months": 0,
                "longest_streak_months": 1,
                "streak_active": False,
            },
            "star_velocity": {
                "recent_rate": 0.2,
                "peak_rate": 1.0,
                "trend": "steady",
            },
            "traffic_views_14d": 0,
            "traffic_unique_visitors_14d": 0,
            "traffic_clones_14d": 0,
            "recent_merged_prs": [],
            "releases": [],
            "pr_review_count": 0,
            "open_issues_count": 0,
            "issue_stats": {"closed_count": 0},
            "languages": {"Python": 120},
            "repos": [
                {
                    "name": "alpha",
                    "language": "Python",
                    "stars": 1,
                    "forks": 0,
                    "topics": ["automation"],
                    "age_months": 1,
                    "date": "2023-01-05T12:00:00Z",
                }
            ],
            "contributions_daily": {
                "2023-01-05": 1,
                "2023-01-06": 1,
                "2023-01-07": 2,
            },
            "contributions_monthly": {"2023-01": 4},
        },
    )
    late_metrics = _sample_metrics(
        repo_stars=(48, 24),
        extra={
            "stars": 128,
            "forks": 20,
            "followers": 84,
            "watchers": 18,
            "network_count": 32,
            "total_commits": 2100,
            "total_prs": 92,
            "total_issues": 48,
            "total_repos_contributed": 11,
            "public_gists": 4,
            "contributions_last_year": 980,
            "language_count": 3,
            "language_diversity": 1.42,
            "topic_clusters": {"automation": 3, "art": 2, "cli": 1},
            "contribution_streaks": {
                "current_streak_months": 5,
                "longest_streak_months": 9,
                "streak_active": True,
            },
            "star_velocity": {
                "recent_rate": 7.5,
                "peak_rate": 9.0,
                "trend": "rising",
            },
            "traffic_views_14d": 2800,
            "traffic_unique_visitors_14d": 160,
            "traffic_clones_14d": 90,
            "recent_merged_prs": [
                {"merged_at": "2023-03-10T00:00:00Z"},
                {"merged_at": "2023-03-12T00:00:00Z"},
                {"merged_at": "2023-03-16T00:00:00Z"},
            ],
            "releases": [
                {"date": "2023-03-13T00:00:00Z"},
                {"date": "2023-03-18T00:00:00Z"},
            ],
            "pr_review_count": 14,
            "open_issues_count": 6,
            "issue_stats": {"closed_count": 30},
            "languages": {"Python": 900, "Go": 400, "Rust": 220},
            "repos": [
                {
                    "name": "alpha",
                    "language": "Python",
                    "stars": 48,
                    "forks": 9,
                    "topics": ["automation", "art"],
                    "age_months": 24,
                    "date": "2023-01-05T12:00:00Z",
                },
                {
                    "name": "beta",
                    "language": "Go",
                    "stars": 24,
                    "forks": 6,
                    "topics": ["automation", "cli"],
                    "age_months": 12,
                    "date": "2023-03-12T00:00:00Z",
                },
                {
                    "name": "gamma",
                    "language": "Rust",
                    "stars": 14,
                    "forks": 4,
                    "topics": ["art"],
                    "age_months": 4,
                    "date": "2023-03-20T00:00:00Z",
                },
            ],
            "contributions_daily": {
                "2023-02-20": 6,
                "2023-02-21": 7,
                "2023-02-22": 5,
                "2023-02-23": 8,
                "2023-02-24": 6,
                "2023-02-25": 7,
                "2023-02-26": 9,
                "2023-02-27": 8,
                "2023-02-28": 7,
                "2023-03-01": 10,
                "2023-03-02": 8,
                "2023-03-03": 9,
                "2023-03-04": 7,
                "2023-03-05": 8,
                "2023-03-06": 10,
                "2023-03-07": 9,
                "2023-03-08": 11,
                "2023-03-09": 10,
                "2023-03-10": 12,
                "2023-03-11": 9,
                "2023-03-12": 14,
                "2023-03-13": 10,
                "2023-03-14": 11,
                "2023-03-15": 12,
                "2023-03-16": 13,
                "2023-03-17": 11,
                "2023-03-18": 10,
                "2023-03-19": 12,
                "2023-03-20": 14,
            },
            "contributions_monthly": {"2023-02": 63, "2023-03": 170},
        },
    )

    early_signals = _compute_ferrofluid_signals(
        early_metrics,
        compute_world_state(early_metrics),
        repo_count=len(early_metrics["repos"]),
        maturity_hint=0.45,
    )
    late_signals = _compute_ferrofluid_signals(
        late_metrics,
        compute_world_state(late_metrics),
        repo_count=len(late_metrics["repos"]),
        maturity_hint=0.45,
    )

    assert late_signals.field_gain > early_signals.field_gain
    assert late_signals.max_spikes > early_signals.max_spikes
    assert late_signals.collaboration_heat > early_signals.collaboration_heat
    assert late_signals.iridescence > early_signals.iridescence
    assert late_signals.star_velocity_pull > early_signals.star_velocity_pull
    assert late_signals.traffic_heat > early_signals.traffic_heat
    assert late_signals.merge_cadence > early_signals.merge_cadence
    assert late_signals.highlight_density > early_signals.highlight_density
    assert late_signals.dipole_lift > early_signals.dipole_lift


def test_ferrofluid_cumulative_history_changes_shape_without_maturity_boost() -> None:
    early_metrics = _sample_metrics(
        repo_stars=(1, 0),
        extra={
            "stars": 2,
            "forks": 0,
            "followers": 1,
            "watchers": 0,
            "network_count": 0,
            "total_commits": 28,
            "total_prs": 1,
            "total_issues": 0,
            "contributions_last_year": 24,
            "language_count": 1,
            "language_diversity": 0.0,
            "topic_clusters": {"automation": 1},
            "contribution_streaks": {
                "current_streak_months": 0,
                "longest_streak_months": 1,
                "streak_active": False,
            },
            "recent_merged_prs": [],
            "releases": [],
            "pr_review_count": 0,
            "open_issues_count": 0,
            "issue_stats": {"closed_count": 0},
            "languages": {"Python": 120},
            "repos": [
                {
                    "name": "alpha",
                    "language": "Python",
                    "stars": 1,
                    "forks": 0,
                    "topics": ["automation"],
                    "age_months": 1,
                    "date": "2023-01-05T12:00:00Z",
                }
            ],
            "contributions_daily": {
                "2023-01-05": 1,
                "2023-01-06": 1,
                "2023-01-07": 2,
            },
            "contributions_monthly": {"2023-01": 4},
        },
    )
    late_metrics = _sample_metrics(
        repo_stars=(48, 24),
        extra={
            "stars": 128,
            "forks": 20,
            "followers": 84,
            "watchers": 18,
            "network_count": 32,
            "total_commits": 2100,
            "total_prs": 92,
            "total_issues": 48,
            "total_repos_contributed": 11,
            "public_gists": 4,
            "contributions_last_year": 980,
            "language_count": 3,
            "language_diversity": 1.42,
            "topic_clusters": {"automation": 3, "art": 2, "cli": 1},
            "contribution_streaks": {
                "current_streak_months": 5,
                "longest_streak_months": 9,
                "streak_active": True,
            },
            "recent_merged_prs": [
                {"merged_at": "2023-03-10T00:00:00Z"},
                {"merged_at": "2023-03-12T00:00:00Z"},
                {"merged_at": "2023-03-16T00:00:00Z"},
            ],
            "releases": [
                {"date": "2023-03-13T00:00:00Z"},
                {"date": "2023-03-18T00:00:00Z"},
            ],
            "pr_review_count": 14,
            "open_issues_count": 6,
            "issue_stats": {"closed_count": 30},
            "languages": {"Python": 900, "Go": 400, "Rust": 220},
            "repos": [
                {
                    "name": "alpha",
                    "language": "Python",
                    "stars": 48,
                    "forks": 9,
                    "topics": ["automation", "art"],
                    "age_months": 24,
                    "date": "2023-01-05T12:00:00Z",
                },
                {
                    "name": "beta",
                    "language": "Go",
                    "stars": 24,
                    "forks": 6,
                    "topics": ["automation", "cli"],
                    "age_months": 12,
                    "date": "2023-03-12T00:00:00Z",
                },
                {
                    "name": "gamma",
                    "language": "Rust",
                    "stars": 14,
                    "forks": 4,
                    "topics": ["art"],
                    "age_months": 4,
                    "date": "2023-03-20T00:00:00Z",
                },
            ],
            "contributions_daily": {
                "2023-02-20": 6,
                "2023-02-21": 7,
                "2023-02-22": 5,
                "2023-02-23": 8,
                "2023-02-24": 6,
                "2023-02-25": 7,
                "2023-02-26": 9,
                "2023-02-27": 8,
                "2023-02-28": 7,
                "2023-03-01": 10,
                "2023-03-02": 8,
                "2023-03-03": 9,
                "2023-03-04": 7,
                "2023-03-05": 8,
                "2023-03-06": 10,
                "2023-03-07": 9,
                "2023-03-08": 11,
                "2023-03-09": 10,
                "2023-03-10": 12,
                "2023-03-11": 9,
                "2023-03-12": 14,
                "2023-03-13": 10,
                "2023-03-14": 11,
                "2023-03-15": 12,
                "2023-03-16": 13,
                "2023-03-17": 11,
                "2023-03-18": 10,
                "2023-03-19": 12,
                "2023-03-20": 14,
            },
            "contributions_monthly": {"2023-02": 63, "2023-03": 170},
        },
    )

    early_svg = generate(
        early_metrics,
        seed="fixed-seed",
        timeline=False,
        maturity=0.45,
    )
    late_svg = generate(
        late_metrics,
        seed="fixed-seed",
        timeline=False,
        maturity=0.45,
    )

    assert _count_spike_gradients(late_svg) > _count_spike_gradients(early_svg)
    assert _count_dipole_markers(late_svg) > _count_dipole_markers(early_svg)


def test_ferrofluid_signal_rich_snapshots_raise_dipole_moments_and_depth() -> None:
    calm_svg = generate(
        _sample_metrics(
            extra={
                "star_velocity": {
                    "recent_rate": 0.2,
                    "peak_rate": 1.0,
                    "trend": "steady",
                },
                "traffic_views_14d": 0,
                "traffic_unique_visitors_14d": 0,
                "traffic_clones_14d": 0,
                "recent_merged_prs": [],
                "releases": [],
                "contribution_streaks": {
                    "current_streak_months": 0,
                    "longest_streak_months": 1,
                    "streak_active": False,
                },
            },
        ),
        seed="fixed-seed",
        timeline=False,
        maturity=1.0,
    )
    signal_rich_svg = generate(
        _sample_metrics(
            extra={
                "stars": 180,
                "forks": 42,
                "watchers": 28,
                "network_count": 60,
                "star_velocity": {
                    "recent_rate": 8.5,
                    "peak_rate": 10.0,
                    "trend": "rising",
                },
                "traffic_views_14d": 3200,
                "traffic_unique_visitors_14d": 180,
                "traffic_clones_14d": 120,
                "recent_merged_prs": [
                    {"merged_at": "2023-03-01T12:00:00Z"},
                    {"merged_at": "2023-03-05T08:30:00Z"},
                    {"merged_at": "2023-03-09T16:45:00Z"},
                    {"merged_at": "2023-03-12T09:15:00Z"},
                ],
                "releases": [
                    {"date": "2023-02-18"},
                    {"date": "2023-03-10"},
                ],
                "contribution_streaks": {
                    "current_streak_months": 9,
                    "longest_streak_months": 14,
                    "streak_active": True,
                },
            },
        ),
        seed="fixed-seed",
        timeline=False,
        maturity=1.0,
    )

    assert sum(_dipole_attr_values(signal_rich_svg, "data-moment")) > sum(
        _dipole_attr_values(calm_svg, "data-moment"),
    )
    assert sum(_dipole_attr_values(signal_rich_svg, "data-depth")) > sum(
        _dipole_attr_values(calm_svg, "data-depth"),
    )


def test_ferrofluid_signal_rich_snapshots_reduce_surface_tension() -> None:
    calm_svg = generate(
        _sample_metrics(
            extra={
                "star_velocity": {
                    "recent_rate": 0.2,
                    "peak_rate": 1.0,
                    "trend": "steady",
                },
                "traffic_views_14d": 0,
                "traffic_unique_visitors_14d": 0,
                "traffic_clones_14d": 0,
                "recent_merged_prs": [],
                "releases": [],
                "contribution_streaks": {
                    "current_streak_months": 0,
                    "longest_streak_months": 1,
                    "streak_active": False,
                },
            },
        ),
        seed="fixed-seed",
        timeline=False,
        maturity=1.0,
    )
    signal_rich_svg = generate(
        _sample_metrics(
            extra={
                "stars": 180,
                "forks": 42,
                "watchers": 28,
                "network_count": 60,
                "star_velocity": {
                    "recent_rate": 8.5,
                    "peak_rate": 10.0,
                    "trend": "rising",
                },
                "traffic_views_14d": 3200,
                "traffic_unique_visitors_14d": 180,
                "traffic_clones_14d": 120,
                "recent_merged_prs": [
                    {"merged_at": "2023-03-01T12:00:00Z"},
                    {"merged_at": "2023-03-05T08:30:00Z"},
                    {"merged_at": "2023-03-09T16:45:00Z"},
                    {"merged_at": "2023-03-12T09:15:00Z"},
                ],
                "releases": [
                    {"date": "2023-02-18"},
                    {"date": "2023-03-10"},
                ],
                "contribution_streaks": {
                    "current_streak_months": 9,
                    "longest_streak_months": 14,
                    "streak_active": True,
                },
            },
        ),
        seed="fixed-seed",
        timeline=False,
        maturity=1.0,
    )

    assert _root_attr(signal_rich_svg, "data-surface-tension") < _root_attr(
        calm_svg,
        "data-surface-tension",
    )
    assert _root_attr(signal_rich_svg, "data-highlight-density") > _root_attr(
        calm_svg,
        "data-highlight-density",
    )
    assert len(
        _elements_with_attr(signal_rich_svg, "data-role", "ferro-highlight"),
    ) > len(
        _elements_with_attr(calm_svg, "data-role", "ferro-highlight"),
    )


def test_select_strongest_spikes_prefers_highest_field_cells() -> None:
    field = np.array(
        [
            [0.10, 0.90, 0.70],
            [0.60, 0.20, 0.80],
        ],
    )
    heights = np.array(
        [
            [1.0, 9.0, 7.0],
            [6.0, 2.0, 8.0],
        ],
    )
    mask = field >= 0.20

    selected = _select_strongest_spikes(mask, field, heights, max_spikes=3)

    assert selected == [(0, 2), (1, 2), (0, 1)]

    tied_field = np.array(
        [
            [0.90, 0.80],
            [0.80, 0.40],
        ],
    )
    tied_heights = np.array(
        [
            [9.0, 7.0],
            [7.0, 4.0],
        ],
    )
    tied_mask = tied_field >= 0.40

    tied_selected = _select_strongest_spikes(
        tied_mask,
        tied_field,
        tied_heights,
        max_spikes=2,
    )

    assert tied_selected == [(0, 1), (0, 0)]


def test_spike_palette_and_highlight_tints_track_language_identity() -> None:
    python_palette = _spike_gradient_palette(
        lang_hue=float(LANG_HUES["Python"]),
        field_norm=0.82,
        owner_distance=0.24,
        height_ratio=0.90,
        light_angle=70.0,
        iridescence=24.0,
    )
    go_palette = _spike_gradient_palette(
        lang_hue=float(LANG_HUES["Go"]),
        field_norm=0.82,
        owner_distance=0.24,
        height_ratio=0.90,
        light_angle=70.0,
        iridescence=24.0,
    )

    assert python_palette == _spike_gradient_palette(
        lang_hue=float(LANG_HUES["Python"]),
        field_norm=0.82,
        owner_distance=0.24,
        height_ratio=0.90,
        light_angle=70.0,
        iridescence=24.0,
    )
    assert python_palette != go_palette
    assert _highlight_fill(
        lang_hue=float(LANG_HUES["Python"]),
        field_norm=0.82,
        highlight_density=0.46,
        height_ratio=0.90,
    ) != _highlight_fill(
        lang_hue=float(LANG_HUES["Go"]),
        field_norm=0.82,
        highlight_density=0.46,
        height_ratio=0.90,
    )


def test_ambient_ripple_specs_keep_owner_centers_stable() -> None:
    dipoles = [
        {
            "x": 180.0,
            "lang": "Python",
            "lang_hue": float(LANG_HUES["Python"]),
            "strength": 0.55,
            "owner_index": 0,
            "identity": "alpha:Python",
        },
        {
            "x": 420.0,
            "lang": "Go",
            "lang_hue": float(LANG_HUES["Go"]),
            "strength": 0.38,
            "owner_index": 1,
            "identity": "beta:Go",
        },
    ]
    base_specs = _ambient_ripple_specs(
        dipoles,
        _sample_signals(),
        pool_y=440.0,
        visual_seed="profile-seed",
    )
    nearby_specs = _ambient_ripple_specs(
        dipoles,
        replace(_sample_signals(), field_gain=0.47, build_volume=0.29),
        pool_y=440.0,
        visual_seed="profile-seed",
    )

    def first_centers(
        specs: list[dict[str, float | int | str]],
    ) -> dict[int, tuple[float, float]]:
        centers: dict[int, tuple[float, float]] = {}
        for spec in specs:
            owner_index = int(spec["owner_index"])
            centers.setdefault(
                owner_index,
                (round(float(spec["cx"]), 1), round(float(spec["cy"]), 1)),
            )
        return centers

    assert first_centers(base_specs) == first_centers(nearby_specs)


def test_ferrofluid_nearby_snapshots_keep_dipole_x_positions_without_seed() -> None:
    base_svg = generate(_sample_metrics(), timeline=False, maturity=0.45)
    nearby_svg = generate(
        _sample_metrics(
            extra={
                "stars": 47,
                "followers": 33,
                "total_commits": 824,
                "contributions_last_year": 438,
            },
        ),
        timeline=False,
        maturity=0.45,
    )

    assert _dipole_x_positions(base_svg) == _dipole_x_positions(nearby_svg)


def test_ferrofluid_timeline_styles_low_field_ripples() -> None:
    svg = generate(
        _sample_metrics(
            repo_stars=(1, 0),
            extra={
                "stars": 2,
                "forks": 0,
                "followers": 1,
                "watchers": 0,
                "network_count": 0,
                "total_commits": 28,
                "total_prs": 1,
                "total_issues": 0,
                "contributions_last_year": 24,
                "language_count": 1,
                "language_diversity": 0.0,
                "topic_clusters": {"automation": 1},
                "contribution_streaks": {
                    "current_streak_months": 0,
                    "longest_streak_months": 1,
                    "streak_active": False,
                },
                "recent_merged_prs": [],
                "releases": [],
                "pr_review_count": 0,
                "open_issues_count": 0,
                "issue_stats": {"closed_count": 0},
                "languages": {"Python": 120},
                "repos": [
                    {
                        "name": "alpha",
                        "language": "Python",
                        "stars": 1,
                        "forks": 0,
                        "topics": ["automation"],
                        "age_months": 1,
                        "date": "2023-01-05T12:00:00Z",
                    }
                ],
                "contributions_daily": {
                    "2023-01-05": 1,
                    "2023-01-06": 1,
                    "2023-01-07": 2,
                },
                "contributions_monthly": {"2023-01": 4},
            },
        ),
        seed="fixed-seed",
        timeline=True,
        loop_duration=18.0,
    )

    ripples = _elements_with_attr(svg, "data-role", "ferro-ripple")

    assert ripples
    assert all(
        {"ferro-ripple", "tl-reveal", "tl-soft"}.issubset(
            set((elem.attrib.get("class") or "").split()),
        )
        for elem in ripples
    )
    assert all("data-when" in elem.attrib for elem in ripples)
