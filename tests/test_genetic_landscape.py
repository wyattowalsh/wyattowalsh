from __future__ import annotations

# ruff: noqa: I001

from copy import deepcopy
import math
import re
from xml.etree.ElementTree import Element

import pytest
from defusedxml import ElementTree

np = pytest.importorskip(
    "numpy", reason="numpy is required by scripts.art.genetic_landscape"
)

from scripts.art import genetic_landscape  # noqa: E402
from scripts.art.genetic_landscape import _derive_landscape_dynamics, generate  # noqa: E402


def _sample_metrics() -> dict:
    return {
        "label": "Genetic Test",
        "account_created": "2022-01-01T00:00:00Z",
        "total_commits": 1200,
        "stars": 40,
        "contributions_last_year": 320,
        "followers": 25,
        "forks": 7,
        "network_count": 12,
        "repos": [
            {
                "name": "alpha",
                "language": "Python",
                "stars": 8,
                "age_months": 24,
                "date": "2023-01-05T12:00:00Z",
            },
            {
                "name": "beta",
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


def _svg_root(svg: str) -> Element:
    return ElementTree.fromstring(svg)


def _timeline_rows(svg: str) -> list[tuple[str, float]]:
    return [
        (when, float(delay))
        for delay, when in re.findall(
            r'data-delay="([0-9]+(?:\.[0-9]+)?)"\s+data-when="(\d{4}-\d{2}-\d{2})"',
            svg,
        )
    ]


def _delays_for_when(svg: str, when: str) -> list[float]:
    pattern = rf'data-delay="([0-9.]+)" data-when="{re.escape(when)}"'
    return [float(delay) for delay in re.findall(pattern, svg)]


def test_genetic_landscape_generate_returns_valid_svg() -> None:
    svg = generate(_sample_metrics(), seed="fixed-seed", timeline=True)

    root = _svg_root(svg)

    assert root.tag == "{http://www.w3.org/2000/svg}svg"
    assert root.attrib["viewBox"] == "0 0 800 800"
    assert root.attrib["data-maturity"]
    assert "@keyframes glReveal" in svg


def test_genetic_landscape_generate_is_deterministic_for_same_seed() -> None:
    metrics = _sample_metrics()

    svg_1 = generate(metrics, seed="fixed-seed", timeline=True, loop_duration=24.0)
    svg_2 = generate(metrics, seed="fixed-seed", timeline=True, loop_duration=24.0)

    assert svg_1 == svg_2


def test_genetic_landscape_generate_is_deterministic_for_minimal_static_metrics() -> (
    None
):
    metrics = {"repos": [], "contributions_monthly": {}}

    svg_1 = generate(metrics, seed="fixed-seed", timeline=False)
    svg_2 = generate(metrics, seed="fixed-seed", timeline=False)

    assert svg_1 == svg_2


def test_genetic_landscape_timeline_can_be_disabled() -> None:
    svg = generate(_sample_metrics(), seed="fixed-seed", timeline=False, maturity=0.35)

    assert "@keyframes glReveal" not in svg
    assert 'class="tl-reveal"' not in svg
    assert "data-delay=" not in svg
    assert "opacity=" in svg


@pytest.mark.parametrize(
    "metrics",
    [
        {},
        {"repos": [], "contributions_monthly": {}},
    ],
)
def test_genetic_landscape_handles_empty_and_minimal_metrics(metrics: dict) -> None:
    svg = generate(metrics, seed="fixed-seed", timeline=True)

    root = _svg_root(svg)

    assert root.tag == "{http://www.w3.org/2000/svg}svg"
    assert svg.endswith("</svg>")


def test_genetic_landscape_dynamics_grow_with_additional_snapshot_signals() -> None:
    baseline_metrics = _sample_metrics()
    baseline_metrics.update(
        {
            "repo_recency_bands": {
                "fresh": 0,
                "recent": 0,
                "established": 2,
                "legacy": 0,
            },
            "star_velocity": {
                "recent_rate": 1.0,
                "peak_rate": 4.0,
                "trend": "stable",
            },
            "contribution_streaks": {
                "current_streak_months": 1,
                "longest_streak_months": 4,
                "streak_active": False,
            },
            "recent_merged_prs": [],
            "releases": [],
            "issue_stats": {"open_count": 6, "closed_count": 2},
        }
    )
    growth_metrics = deepcopy(baseline_metrics)
    growth_metrics.update(
        {
            "repo_recency_bands": {
                "fresh": 1,
                "recent": 1,
                "established": 0,
                "legacy": 0,
            },
            "star_velocity": {
                "recent_rate": 4.0,
                "peak_rate": 4.0,
                "trend": "rising",
            },
            "contribution_streaks": {
                "current_streak_months": 4,
                "longest_streak_months": 5,
                "streak_active": True,
            },
            "recent_merged_prs": [
                {"merged_at": "2023-01-20T12:00:00Z", "repo_name": "alpha"},
                {"merged_at": "2023-02-18T09:00:00Z", "repo_name": "beta"},
            ],
            "releases": [
                {"published_at": "2023-02-25T12:00:00Z", "name": "v0.2.0"},
            ],
            "issue_stats": {"open_count": 2, "closed_count": 8},
        }
    )

    baseline = _derive_landscape_dynamics(
        baseline_metrics,
        maturity=0.4,
        tempo=0.5,
    )
    growth = _derive_landscape_dynamics(
        growth_metrics,
        maturity=0.4,
        tempo=0.5,
    )

    assert growth.generations > baseline.generations
    assert growth.pop_count > baseline.pop_count
    assert growth.ridge_intensity > baseline.ridge_intensity


def test_genetic_landscape_growth_profile_fallback_treats_young_repo_as_growth() -> (
    None
):
    growth_share, legacy_share = genetic_landscape._repo_growth_profile(
        {"repos": [{"name": "fresh", "stars": 2, "age_months": 6}]}
    )

    assert growth_share > legacy_share
    assert growth_share > 0.5


def test_genetic_landscape_peak_profile_broadens_older_repos() -> None:
    older = {"name": "legacy", "stars": 5, "age_months": 60}
    newer = {"name": "flash", "stars": 18, "age_months": 6}

    older_peak_h, older_sigma, older_terrace_h, older_terrace_sigma = (
        genetic_landscape._repo_peak_profile(older, max_repo_age=60)
    )
    newer_peak_h, newer_sigma, newer_terrace_h, newer_terrace_sigma = (
        genetic_landscape._repo_peak_profile(newer, max_repo_age=60)
    )

    older_center = older_peak_h + older_terrace_h
    newer_center = newer_peak_h + newer_terrace_h
    older_shoulder = older_peak_h * genetic_landscape._gaussian(
        8.0, 0.0, 0.0, 0.0, older_sigma
    ) + older_terrace_h * genetic_landscape._gaussian(
        8.0, 0.0, 0.0, 0.0, older_terrace_sigma
    )
    newer_shoulder = newer_peak_h * genetic_landscape._gaussian(
        8.0, 0.0, 0.0, 0.0, newer_sigma
    ) + newer_terrace_h * genetic_landscape._gaussian(
        8.0, 0.0, 0.0, 0.0, newer_terrace_sigma
    )

    assert newer_center > older_center
    assert older_sigma > newer_sigma
    assert older_terrace_sigma > newer_terrace_sigma
    assert older_shoulder > newer_shoulder


def test_genetic_landscape_generate_passes_stabilized_mutation_to_simulation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: list[dict[str, float]] = []

    def _capture_simulation(
        peaks: list[tuple[float, float, float]],
        elevation: object,
        grid: int,
        cell_w: float,
        cell_h: float,
        rng: object,
        pop_count: int,
        generations: int,
        mutation_rate: float,
    ) -> list[tuple[float, float, list[tuple[float, float]]]]:
        captured.append(
            {
                "pop_count": float(pop_count),
                "generations": float(generations),
                "mutation_rate": mutation_rate,
            }
        )
        return []

    monkeypatch.setattr(genetic_landscape, "_simulate_population", _capture_simulation)

    volatile_metrics = _sample_metrics()
    volatile_metrics.update(
        {
            "repo_recency_bands": {
                "fresh": 1,
                "recent": 1,
                "established": 0,
                "legacy": 0,
            },
            "star_velocity": {
                "recent_rate": 4.0,
                "peak_rate": 4.0,
                "trend": "rising",
            },
            "contribution_streaks": {
                "current_streak_months": 0,
                "longest_streak_months": 1,
                "streak_active": False,
            },
            "recent_merged_prs": [
                {"merged_at": "2023-01-20T12:00:00Z", "repo_name": "alpha"},
                {"merged_at": "2023-02-18T09:00:00Z", "repo_name": "beta"},
            ],
            "releases": [],
            "issue_stats": {"open_count": 8, "closed_count": 1},
        }
    )
    stable_metrics = deepcopy(volatile_metrics)
    stable_metrics.update(
        {
            "contribution_streaks": {
                "current_streak_months": 4,
                "longest_streak_months": 4,
                "streak_active": True,
            },
            "releases": [
                {"published_at": "2023-02-25T12:00:00Z", "name": "v0.2.0"},
                {"published_at": "2023-03-01T12:00:00Z", "name": "v0.3.0"},
            ],
            "issue_stats": {"open_count": 2, "closed_count": 8},
        }
    )

    generate(volatile_metrics, seed="fixed-seed", timeline=False, maturity=0.4)
    generate(stable_metrics, seed="fixed-seed", timeline=False, maturity=0.4)

    assert len(captured) == 2
    assert captured[1]["mutation_rate"] < captured[0]["mutation_rate"]


def test_genetic_landscape_population_seeding_prefers_peak_structures() -> None:
    grid = 18
    cell_w = genetic_landscape._MAP_W / grid
    cell_h = genetic_landscape._MAP_H / grid
    peaks = [
        (
            genetic_landscape._MAP_L + genetic_landscape._MAP_W * 0.28,
            genetic_landscape._MAP_T + genetic_landscape._MAP_H * 0.36,
            18.0,
        ),
        (
            genetic_landscape._MAP_L + genetic_landscape._MAP_W * 0.72,
            genetic_landscape._MAP_T + genetic_landscape._MAP_H * 0.64,
            10.0,
        ),
    ]
    elevation = np.zeros((grid, grid), dtype=np.float64)

    for px, py, peak_h in peaks:
        gpx = (px - genetic_landscape._MAP_L) / cell_w
        gpy = (py - genetic_landscape._MAP_T) / cell_h
        for gy in range(grid):
            for gx in range(grid):
                elevation[gy, gx] += peak_h * genetic_landscape._gaussian(
                    gx,
                    gy,
                    gpx,
                    gpy,
                    4.5,
                )

    organisms = genetic_landscape._simulate_population(
        peaks,
        elevation,
        grid,
        cell_w,
        cell_h,
        np.random.default_rng(1234),
        pop_count=48,
        generations=0,
        mutation_rate=0.2,
    )
    distances = [
        min(math.hypot(ox - px, oy - py) for px, py, _ in peaks)
        for ox, oy, _trail in organisms
    ]

    assert sum(distance < 120.0 for distance in distances) >= 30
    assert sum(distance < 80.0 for distance in distances) >= 14


def test_genetic_landscape_static_frames_keep_all_snapshot_repo_peaks() -> None:
    metrics = _sample_metrics()
    metrics["repos"] = [
        *metrics["repos"],
        {
            "name": "gamma",
            "language": "Rust",
            "stars": 4,
            "age_months": 6,
            "date": "2023-04-20T00:00:00Z",
        },
    ]

    svg = generate(metrics, seed="fixed-seed", timeline=False, maturity=0.12)
    root = _svg_root(svg)

    assert root.attrib["data-peak-count"] == "3"


def test_genetic_landscape_dense_repo_snapshots_add_micro_colonies_without_omission(
) -> None:
    metrics = _sample_metrics()
    metrics["repos"] = [
        {
            "name": f"repo-{index}",
            "language": ("Python", "Go", "Rust", "TypeScript")[index % 4],
            "stars": max(1, 18 - index),
            "age_months": 4 + index,
            "date": f"2023-{(index % 9) + 1:02d}-{(index % 25) + 1:02d}T00:00:00Z",
            "topics": ["automation", f"cluster-{index % 3}"],
        }
        for index in range(12)
    ]

    svg = generate(metrics, seed="genetic-dense-repos", timeline=False, maturity=0.22)
    root = _svg_root(svg)

    assert root.attrib["data-peak-count"] == str(len(metrics["repos"]))
    assert svg.count('data-role="gl-micro-colony"') >= len(metrics["repos"])


def test_genetic_landscape_static_render_uses_snapshot_signals_at_same_maturity() -> (
    None
):
    early = _sample_metrics()
    early.update(
        {
            "stars": 2,
            "followers": 3,
            "network_count": 1,
            "repos": [deepcopy(_sample_metrics()["repos"][0])],
            "contributions_last_year": 8,
            "contributions_monthly": {"2023-01": 8},
            "contributions_daily": {
                "2023-01-05": 2,
                "2023-01-06": 2,
                "2023-01-07": 2,
                "2023-01-08": 2,
            },
            "recent_merged_prs": [],
            "releases": [],
            "traffic_views_14d": 0,
            "traffic_unique_visitors_14d": 0,
            "traffic_clones_14d": 0,
            "traffic_unique_cloners_14d": 0,
        }
    )

    late = _sample_metrics()
    late.update(
        {
            "stars": 64,
            "followers": 36,
            "network_count": 18,
            "repos": [
                *late["repos"],
                {
                    "name": "gamma",
                    "language": "Rust",
                    "stars": 14,
                    "age_months": 8,
                    "date": "2023-04-20T00:00:00Z",
                },
            ],
            "contributions_last_year": 420,
            "contributions_monthly": {
                "2023-01": 40,
                "2023-02": 70,
                "2023-03": 110,
                "2023-04": 200,
            },
            "contributions_daily": {
                "2023-01-05": 5,
                "2023-01-10": 9,
                "2023-02-12": 18,
                "2023-02-18": 26,
                "2023-03-05": 32,
                "2023-03-21": 40,
                "2023-04-10": 52,
                "2023-04-19": 60,
            },
            "recent_merged_prs": [
                {"merged_at": "2023-02-18T09:00:00Z", "repo_name": "beta"},
                {"merged_at": "2023-03-04T11:30:00Z", "repo_name": "alpha"},
                {"merged_at": "2023-04-16T12:15:00Z", "repo_name": "gamma"},
            ],
            "releases": [
                {"published_at": "2023-02-25T12:00:00Z", "name": "v0.2.0"},
                {"published_at": "2023-04-18T12:00:00Z", "name": "v0.3.0"},
            ],
            "traffic_views_14d": 1800,
            "traffic_unique_visitors_14d": 420,
            "traffic_clones_14d": 260,
            "traffic_unique_cloners_14d": 110,
        }
    )

    early_root = _svg_root(
        generate(early, seed="fixed-seed", timeline=False, maturity=0.2)
    )
    late_root = _svg_root(
        generate(late, seed="fixed-seed", timeline=False, maturity=0.2)
    )

    assert int(late_root.attrib["data-generations"]) > int(
        early_root.attrib["data-generations"]
    )
    assert int(late_root.attrib["data-population"]) > int(
        early_root.attrib["data-population"]
    )
    assert float(late_root.attrib["data-activity-signal"]) > float(
        early_root.attrib["data-activity-signal"]
    )


def test_genetic_landscape_activity_midpoint_tracks_contribution_distribution() -> None:
    front_loaded = _sample_metrics()
    front_loaded["contributions_daily"] = {
        f"2023-01-{day:02d}": (10 if day <= 5 else 0) for day in range(1, 31)
    }
    front_loaded["contributions_monthly"] = {"2023-01": 50}

    back_loaded = _sample_metrics()
    back_loaded["contributions_daily"] = {
        f"2023-01-{day:02d}": (10 if day >= 26 else 0) for day in range(1, 31)
    }
    back_loaded["contributions_monthly"] = {"2023-01": 50}

    front_root = _svg_root(
        generate(front_loaded, seed="fixed-seed", timeline=True, loop_duration=24.0)
    )
    back_root = _svg_root(
        generate(back_loaded, seed="fixed-seed", timeline=True, loop_duration=24.0)
    )

    assert (
        front_root.attrib["data-activity-midpoint"]
        < back_root.attrib["data-activity-midpoint"]
    )


def test_genetic_landscape_daily_only_activity_sets_timeline_delays() -> None:
    loop_duration = 24.0
    reveal_fraction = 0.6
    front_loaded = _sample_metrics()
    front_loaded["contributions_monthly"] = {}
    front_loaded["contributions_daily"] = {
        "2024-05-01": 6,
        "2024-05-03": 2,
        "2024-05-05": 1,
    }

    back_loaded = _sample_metrics()
    back_loaded["contributions_monthly"] = {}
    back_loaded["contributions_daily"] = {
        "2024-05-18": 1,
        "2024-05-20": 2,
        "2024-05-24": 6,
    }

    front_svg = generate(
        front_loaded,
        seed="fixed-seed",
        timeline=True,
        loop_duration=loop_duration,
        reveal_fraction=reveal_fraction,
    )
    back_svg = generate(
        back_loaded,
        seed="fixed-seed",
        timeline=True,
        loop_duration=loop_duration,
        reveal_fraction=reveal_fraction,
    )
    front_midpoint = _svg_root(front_svg).attrib["data-activity-midpoint"]
    back_midpoint = _svg_root(back_svg).attrib["data-activity-midpoint"]
    front_rows = _timeline_rows(front_svg)
    back_rows = _timeline_rows(back_svg)
    front_by_date: dict[str, list[float]] = {}
    back_by_date: dict[str, list[float]] = {}
    for when, delay in front_rows:
        front_by_date.setdefault(when, []).append(delay)
    for when, delay in back_rows:
        back_by_date.setdefault(when, []).append(delay)

    assert front_midpoint < back_midpoint
    assert (
        max(front_by_date["2024-05-01"])
        < min(front_by_date["2024-05-03"])
        < min(front_by_date["2024-05-05"])
    )
    assert (
        max(back_by_date["2024-05-18"])
        < min(back_by_date["2024-05-20"])
        < min(back_by_date["2024-05-24"])
    )

    reveal_end = loop_duration * reveal_fraction
    for _, delay in front_rows + back_rows:
        assert 0.0 <= delay <= reveal_end + 1e-9

    assert _delays_for_when(front_svg, front_midpoint)
    assert _delays_for_when(back_svg, back_midpoint)
    assert min(_delays_for_when(front_svg, front_midpoint)) < min(
        _delays_for_when(back_svg, back_midpoint)
    )
