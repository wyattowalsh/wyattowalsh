"""Focused edge-path coverage for the six standalone living-art renderers.

The production renderers intentionally contain many defensive branches because
they consume partially trusted GitHub snapshot data.  These tests exercise those
branches with small deterministic inputs and use the supported grid/budget seams
to avoid turning coverage into a high-resolution rendering benchmark.
"""

from __future__ import annotations

import math
from dataclasses import replace
from datetime import date
from typing import Any, cast
from xml.etree import ElementTree

import pytest

np = pytest.importorskip("numpy", reason="living-art renderers require numpy")
pytest.importorskip("scipy", reason="physarum requires scipy")

from scripts.art import (  # noqa: E402
    ferrofluid,
    genetic_landscape,
    ink_garden,
    lenia,
    physarum,
    topography,
)
from scripts.art.shared import compute_world_state  # noqa: E402


def _repo(
    name: str,
    *,
    language: str = "Python",
    stars: int = 10,
    age_months: int = 12,
    when: str = "2023-01-01T12:00:00Z",
    topics: list[str] | None = None,
    forks: int = 2,
) -> dict[str, Any]:
    return {
        "name": name,
        "language": language,
        "stars": stars,
        "forks": forks,
        "age_months": age_months,
        "date": when,
        "topics": topics or [],
    }


def _rich_metrics() -> dict[str, Any]:
    repos = [
        _repo(
            "data-oak",
            stars=180,
            age_months=50,
            when="2021-01-05T12:00:00Z",
            topics=["data", "analytics", "shared"],
            forks=24,
        ),
        _repo(
            "web-fern",
            language="TypeScript",
            stars=48,
            age_months=30,
            when="2021-08-15T12:00:00Z",
            topics=["web", "frontend", "shared"],
            forks=8,
        ),
        _repo(
            "agent-wisteria",
            stars=70,
            age_months=22,
            when="2022-02-20T12:00:00Z",
            topics=["agents", "ai", "shared"],
            forks=12,
        ),
        _repo(
            "infra-bamboo",
            language="Shell",
            stars=22,
            age_months=18,
            when="2022-07-01T12:00:00Z",
            topics=["devops", "cli", "shared"],
            forks=10,
        ),
        _repo(
            "creative-flower",
            language="JavaScript",
            stars=14,
            age_months=10,
            when="2023-01-08T12:00:00Z",
            topics=["art", "graphics", "shared"],
            forks=3,
        ),
        _repo(
            "rust-conifer",
            language="Rust",
            stars=7,
            age_months=7,
            when="2023-05-12T12:00:00Z",
            topics=["systems", "shared"],
            forks=1,
        ),
        _repo(
            "fork-banyan",
            language="Go",
            stars=2,
            age_months=5,
            when="2023-08-21T12:00:00Z",
            topics=["network", "shared"],
            forks=9,
        ),
        _repo(
            "young-seedling",
            stars=1,
            age_months=1,
            when="2023-11-03T12:00:00Z",
            topics=["new"],
            forks=0,
        ),
    ]
    return {
        "label": "Renderer Coverage",
        "login": "renderer-coverage",
        "account_created": "2020-01-01T00:00:00Z",
        "total_commits": 8000,
        "total_prs": 180,
        "total_issues": 72,
        "open_issues_count": 8,
        "stars": 420,
        "contributions_last_year": 1500,
        "followers": 1200,
        "following": 48,
        "forks": 90,
        "watchers": 35,
        "network_count": 160,
        "orgs_count": 4,
        "public_gists": 32,
        "traffic_views_14d": 2400,
        "pr_review_count": 180,
        "total_repos_contributed": 20,
        "language_count": 8,
        "language_diversity": 0.94,
        "languages": {
            "Python": 900,
            "TypeScript": 500,
            "Rust": 260,
            "Go": 180,
        },
        "topic_clusters": {
            "data": 4,
            "web": 3,
            "agents": 3,
            "devops": 2,
            "art": 2,
        },
        "repo_visual_order": [
            "",
            "data-oak",
            "data-oak",
            "young-seedling",
            "missing",
        ],
        "canonical_primary_repo_names": [
            "web-fern",
            "web-fern",
            "agent-wisteria",
        ],
        "repos": repos,
        "contributions_monthly": {
            "2023-01": 6,
            "2": 42,
            "odd": 2,
            "2023-04": 80,
            "2023-05": 4,
            "2023-06": 95,
        },
        "contributions_daily": {
            "bad-day": 9,
            "2023-01-02": 0,
            "2023-02-10": 12,
            "2023-05-15": 32,
            "2023-11-25": 18,
        },
        "commit_hour_distribution": {"6": 90, "18": 3},
        "star_velocity": {
            "recent_rate": 12,
            "peak_rate": 15,
            "trend": "rising",
        },
        "contribution_streaks": {
            "current_streak_months": 9,
            "longest_streak_months": 12,
            "streak_active": True,
        },
        "recent_merged_prs": [
            "not-a-pr",
            {"merged_at": "bad-date"},
            {
                "merged_at": "2023-02-12T12:00:00Z",
                "repo_name": "data-oak",
                "additions": 240,
                "deletions": 40,
            },
            {
                "mergedAt": "2023-03-01T12:00:00Z",
                "repo_name": "web-fern",
                "additions": 100,
                "deletions": 20,
            },
        ],
        "releases": [
            "not-a-release",
            {"date": "bad-date"},
            {
                "published_at": "2023-06-01T00:00:00Z",
                "repo_name": "data-oak",
                "tag_name": "v1.0",
            },
            {
                "created_at": "2023-09-01T00:00:00Z",
                "repo_name": "web-fern",
                "name": "v2.0",
            },
        ],
        "issue_stats": {"open_count": 0, "closed_count": 24},
        "repo_recency_bands": {
            "fresh": 2,
            "recent": 2,
            "established": 2,
            "legacy": 2,
        },
    }


def _svg_data_roles(svg: str) -> set[str]:
    root = ElementTree.fromstring(svg)
    assert root.tag == "{http://www.w3.org/2000/svg}svg"
    return {
        role
        for element in root.iter()
        if (role := element.attrib.get("data-role")) is not None
    }


def _patch_world(
    monkeypatch: pytest.MonkeyPatch,
    module: Any,
    metrics: dict[str, Any],
    **changes: Any,
) -> None:
    world = replace(compute_world_state(metrics), **changes)
    monkeypatch.setattr(module, "compute_world_state", lambda _metrics: world)


def test_ink_garden_defensive_helpers_cover_invalid_and_semantic_inputs() -> None:
    assert ink_garden._classify_species({"topics": ["data"]}) == "oak"
    assert ink_garden._classify_species({"topics": ["frontend"]}) == "fern"

    selected, _ = ink_garden._select_primary_repos(
        [_repo("alpha"), _repo("beta")],
        limit=1,
        repo_visual_order=["", "alpha", "alpha"],
        canonical_repo_names=["alpha", "beta"],
    )
    assert [repo["name"] for repo in selected][0] == "alpha"

    assert ink_garden._parse_iso_datetime("not-a-date") is None
    assert ink_garden._recent_activity_variance(cast(Any, [])) == 0.0
    assert ink_garden._recent_activity_variance({"1": 0, "2": 0}) == 0.0
    assert ink_garden._extract_dated_entries("bad", "date") == []
    assert ink_garden._extract_dated_entries([None, {"date": "2024-01-01"}], "date")

    cadence = ink_garden._summarize_merged_pr_cadence(
        cast(
            list[dict],
            [None, {"merged_at": "bad"}, {"merged_at": "2024-01-01"}],
        )
    )
    assert cadence["entries"]

    dates = ink_garden._repo_emergence_dates(
        "2023-04-01",
        (date(2023, 1, 1), date(2024, 1, 1)),
        repo_frac=0.4,
        prev_frac=0.2,
        next_frac=0.7,
        age_days=300,
    )
    assert dates["root"] <= dates["detail"]

    annotation = ink_garden._repo_topic_annotation(
        {
            "topics": [
                "",
                "Extremely-Long-Topic-Name-For-Coverage",
                "extremely-long-topic-name-for-coverage",
                "other",
            ]
        }
    )
    assert annotation == "Extremely Long Topic Name For Coverage +1"

    canopy_candidate = _repo("young-canopy", stars=200, age_months=30)
    plans, counts = ink_garden._build_repo_ecology_plan(
        [canopy_candidate],
        base_seed=7,
        repo_recency_days_by_name={"young-canopy": 90},
    )
    assert plans[0]["stratum"] == "understory"
    assert counts["understory"] == 1


@pytest.mark.parametrize("bloom_type", ["raceme", "aerial_root"])
def test_ink_garden_bloom_budget_fallbacks(bloom_type: str) -> None:
    parts: list[str] = []
    ink_garden._draw_bloom(
        parts,
        100,
        100,
        12,
        40,
        8,
        2,
        bloom_type,
        np.random.default_rng(4),
        lambda: False,
        ink_garden.oklch,
    )
    assert isinstance(parts, list)


def test_ink_garden_rich_autumn_dawn_render(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    metrics = _rich_metrics()
    _patch_world(
        monkeypatch,
        ink_garden,
        metrics,
        season="autumn",
        weather="clear",
        time_of_day="dawn",
    )

    svg = ink_garden.generate(metrics, seed="coverage-ink", maturity=0.67)

    assert svg.startswith("<svg")
    assert "BOTANICAL GARDEN" in svg
    assert "repo-tree" in svg
    assert "ferro-ripple" not in svg


def test_ink_garden_storm_timeline_and_budget_limits(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    metrics = _rich_metrics()
    metrics["issue_stats"] = {"open_count": 60, "closed_count": 1}
    metrics["commit_hour_distribution"] = {23: 40}
    metrics["recent_merged_prs"] = "invalid"
    metrics["contributions_daily"] = {}
    _patch_world(
        monkeypatch,
        ink_garden,
        metrics,
        season="winter",
        weather="stormy",
        time_of_day="night",
    )
    monkeypatch.setattr(ink_garden, "MAX_SEGS", 20)
    monkeypatch.setattr(ink_garden, "MAX_ROOTS", 6)
    monkeypatch.setattr(ink_garden, "MAX_BLOOMS", 2)
    monkeypatch.setattr(ink_garden, "MAX_ELEMENTS", 380)

    svg = ink_garden.generate(
        metrics,
        seed="coverage-ink-storm",
        timeline=True,
        loop_duration=12,
    )

    assert "@keyframes" in svg
    assert svg.endswith("</svg>")


def test_topography_defensive_helpers_and_boundaries() -> None:
    assert topography._topo_color(float("inf")) == topography._TOPO_STOPS[-1][1]
    assert topography._normalize_hour_distribution([]) == {}
    assert topography._normalize_hour_distribution({"bad": "bad", 24: 1}) == {}
    assert topography._commit_hour_hillshade_profile({0: 1, 12: 1})["peak_hour"] == 12
    assert topography._settlement_scale_tier(1000) == ("capital", "Capital")
    assert topography._settlement_scale_tier(500) == ("city", "City")

    falling = topography._river_flow_profile(
        {"recent_rate": "bad", "peak_rate": object(), "trend": "falling"}
    )
    assert falling["tier"] == "still"

    window = (date(2020, 1, 1), date(2024, 1, 1))
    empty = topography._repo_recency_landscape_profile([], window)
    assert empty["band"] == "balanced"
    invalid = topography._repo_recency_landscape_profile(
        [None, {"date": "bad", "age_months": "bad"}, {"name": "undated"}],  # type: ignore[list-item]
        window,
    )
    assert invalid["band"] == "balanced"
    assert math.isinf(topography._polyline_distance(0, 0, [(0, 0)]))

    fallback = topography._choose_label_anchor(
        topography.MAP_L,
        topography.MAP_T,
        [(-1000, -1000)],
        [[(0, 0), (1, 1)]],
    )
    assert fallback[0] == topography.MAP_L + 6
    assert fallback[1] == topography.MAP_T + 6


def test_topography_rich_rainy_capital_render(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    metrics = _rich_metrics()
    metrics["total_issues"] = "bad"
    metrics["contributions_daily"]["2023-10-10"] = "bad"
    metrics["commit_hour_distribution"] = {"bad": 100}
    _patch_world(monkeypatch, topography, metrics, weather="rainy")
    monkeypatch.setattr(topography, "TOPOGRAPHY_GRID_SIZE", 40)

    svg = topography.generate(
        metrics,
        seed="coverage-topography",
        maturity=1.0,
        chrome_maturity=1.0,
        timeline=False,
    )

    assert 'data-tier="capital"' in svg
    assert "Visitors: 2400" in svg
    assert "Topographic Survey" in svg


def test_topography_city_timeline_with_invalid_history(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    metrics = _rich_metrics()
    metrics["followers"] = 500
    metrics["repos"] = [
        _repo("age-only", age_months=18, when="bad"),
        {"name": "undated", "age_months": 0, "topics": []},
    ]
    metrics["repo_visual_order"] = [None, "", "age-only"]
    metrics["releases"] = [None, {"date": "bad"}]
    metrics["recent_merged_prs"] = [None, {"merged_at": "bad"}]
    metrics["contributions_monthly"] = {}
    metrics["contributions_daily"] = {"2023-01-01": 0}
    metrics["topic_clusters"] = {"orphan": 2}
    monkeypatch.setattr(topography, "TOPOGRAPHY_GRID_SIZE", 20)

    svg = topography.generate(metrics, seed="coverage-topography-city", timeline=True)

    assert 'data-tier="city"' in svg
    assert "@keyframes topoReveal" in svg


def test_physarum_defensive_helpers() -> None:
    assert physarum._coerce_nonnegative_int(object()) == 0
    assert physarum._repo_topics({"topics": ["a", "b", "c"]}, limit=1) == ["a"]
    assert physarum._circular_hue_mean([]) == 155.0
    assert physarum._circular_hue_mean([(0.0, 1.0), (180.0, 1.0)]) == 0.0
    assert physarum._topic_hue("  ") == 155.0
    assert physarum._identity_influence(1, 1, []) == (None, 0.0)
    assert physarum._resolve_vein_style([], "#fff", []) == ("#fff", 0.0)
    assert physarum._repo_recency_bands("bad") == {
        "fresh": 0,
        "recent": 0,
        "established": 0,
        "legacy": 0,
    }
    bands = physarum._repo_recency_bands([None, {"age_months": 60}])  # type: ignore[list-item]
    assert bands["legacy"] == 1
    assert physarum._commit_hour_focus([]) == (0.0, 12.0)
    assert physarum._commit_hour_focus({"bad": "bad", 0: 1, 12: 1})[1] == 12.0
    density, burst, boosts = physarum._summarize_recent_pr_activity(
        [None, {}, {"merged_at": "bad"}]  # type: ignore[list-item]
    )
    assert (density, burst, boosts) == (0.0, 0.0, {})
    assert physarum._extract_contours(np.zeros((3, 3)), 3, 1, 1, 1) == []
    assert physarum._chaikin_smooth([(0, 0), (1, 1)], iterations=1) == [
        (0, 0),
        (1, 1),
    ]


def test_physarum_budget_and_invalid_timeline_inputs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    metrics = _rich_metrics()
    metrics["repos"].append({"name": "broken-date", "date": "bad"})
    metrics["contributions_daily"] = {"bad": 3, "2023-01-01": object()}
    monkeypatch.setattr(
        physarum,
        "CFG",
        replace(
            physarum.CFG,
            grid_resolution=24,
            contour_levels=2,
            agent_base=20,
            agent_scale=5.0,
            sim_steps_base=5,
            sim_steps_scale=2.0,
            max_elements=0,
        ),
    )
    constrained = physarum.generate(metrics, seed="coverage-physarum", timeline=True)
    repeated = physarum.generate(metrics, seed="coverage-physarum", timeline=True)
    assert constrained == repeated
    roles = _svg_data_roles(constrained)
    assert "physarum-spore" in roles
    assert roles.isdisjoint(
        {
            "physarum-node-halo",
            "physarum-node-shell",
            "physarum-node-core",
            "physarum-node-satellite",
        }
    )

    monkeypatch.setattr(physarum, "CFG", replace(physarum.CFG, max_elements=10_000))
    full = physarum.generate(metrics, seed="coverage-physarum", timeline=True)
    assert "physarum-node-halo" in _svg_data_roles(full)


def test_lenia_defensive_helpers_and_small_render_budget(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert lenia._circular_hue_average(
        [(10, 0), (20, -1), (30, 1)], fallback=100
    ) == pytest.approx(30)
    assert lenia._build_kernel(4, 0.4, 0.1, profile="halo").shape == (9, 9)

    palette = lenia._LeniaPalette(
        background="#000",
        ramp=((0.0, "#000"), (0.5, "#888"), (1.0, "#fff")),
        core="#fff",
    )
    assert lenia._field_to_color(2.0, palette) == ("#fff", 1.0)
    assert lenia._signal_date({}, "date") is None
    mix = lenia._extract_language_mix(
        cast(
            list[dict],
            [None, {"language": ""}, {"language": "Python", "stars": 1}],
        ),
        cast(dict[str, int], {"": 10, "Python": "bad", "Rust": 20}),
    )
    assert mix == {"Rust": 1.0}
    assert lenia._normalize_hour_distribution({"bad": "bad"}) == {}
    assert lenia._commit_hour_profile({0: 1, 12: 1})[0] == pytest.approx(12.0)
    assert lenia._summarize_merged_pr_cadence([None, {}, {"merged_at": "bad"}]) == (  # type: ignore[list-item]
        0.0,
        0.0,
        set(),
    )

    repos = [_repo("one"), _repo("two")]
    augmented = lenia._augment_primary_repos(
        [repos[0]],
        repos,
        merged_repo_names=frozenset({"missing", "two"}),
        limit=2,
    )
    assert [repo["name"] for repo in augmented] == ["two", "one"]
    assert lenia._build_timeline_lookup([], 2, fallback_when="2024-01-01") == [
        ["2024-01-01", "2024-01-01"],
        ["2024-01-01", "2024-01-01"],
    ]

    monkeypatch.setattr(
        lenia,
        "CFG",
        replace(
            lenia.CFG,
            grid_resolution=18,
            kernel_radius=4,
            sim_steps_base=5,
            sim_steps_scale=2.0,
            max_elements=0,
        ),
    )
    metrics = _rich_metrics()
    constrained = lenia.generate(metrics, seed="coverage-lenia", timeline=True)
    repeated = lenia.generate(metrics, seed="coverage-lenia", timeline=True)
    assert constrained == repeated
    assert _svg_data_roles(constrained).isdisjoint(
        {"lenia-seed-halo", "lenia-seed-orbit"}
    )

    monkeypatch.setattr(lenia, "CFG", replace(lenia.CFG, max_elements=10_000))
    full = lenia.generate(metrics, seed="coverage-lenia", timeline=True)
    assert "lenia-seed-halo" in _svg_data_roles(full)


def test_genetic_landscape_helpers_and_budget_paths(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert genetic_landscape._as_non_negative_int(object()) == 0
    assert genetic_landscape._as_non_negative_float(object()) == 0.0
    assert (
        genetic_landscape._repo_establishment_signal({"age_months": 0}, max_repo_age=24)
        == 0.0
    )
    falling = _rich_metrics()
    falling["star_velocity"] = {"recent_rate": 8, "trend": "falling"}
    assert genetic_landscape._derive_landscape_dynamics(
        falling, maturity=0.8, tempo=0.7
    )
    assert genetic_landscape._extract_contours(np.zeros((3, 3)), 3, 1, 1, 1) == []

    terrain = np.zeros((1, 1))
    organisms = genetic_landscape._simulate_population(
        [(100.0, 100.0, 2.0)],
        terrain,
        1,
        1.0,
        1.0,
        np.random.default_rng(2),
        2,
        1,
        0.1,
    )
    assert len(organisms) == 2

    metrics = _rich_metrics()
    metrics["repos"].append({"name": "invalid", "date": "bad", "age_months": 0})
    metrics["contributions_daily"] = {
        "2023-01-01": 1,
        "2023-01-02": 0,
        "2023-01-03": 2,
    }
    monkeypatch.setattr(
        genetic_landscape,
        "CFG",
        replace(
            genetic_landscape.CFG,
            grid_resolution=20,
            contour_levels=3,
            pop_base=5,
            pop_scale=2.0,
            max_elements=0,
        ),
    )
    constrained = genetic_landscape.generate(
        metrics, seed="coverage-genetic", timeline=True, loop_duration=12
    )
    repeated = genetic_landscape.generate(
        metrics, seed="coverage-genetic", timeline=True, loop_duration=12
    )
    assert constrained == repeated
    assert _svg_data_roles(constrained).isdisjoint(
        {"gl-micro-colony", "genetic-peak-glow", "genetic-peak-core"}
    )

    monkeypatch.setattr(
        genetic_landscape,
        "CFG",
        replace(genetic_landscape.CFG, max_elements=10_000),
    )
    full = genetic_landscape.generate(
        metrics, seed="coverage-genetic", timeline=True, loop_duration=12
    )
    assert "genetic-peak-glow" in _svg_data_roles(full)


def test_ferrofluid_helpers_and_high_signal_ripples() -> None:
    assert ferrofluid._event_dates("bad", "date") == []
    assert ferrofluid._event_dates(
        [None, {"date": "bad"}, {"date": "2024-01-01"}],
        "date",  # type: ignore[list-item]
    ) == [date(2024, 1, 1)]
    assert (
        ferrofluid._select_strongest_spikes(
            np.ones((2, 2), dtype=bool),
            np.ones((2, 2)),
            np.ones((2, 2)),
            max_spikes=0,
        )
        == []
    )
    assert ferrofluid._nearest_dipole_index(0, 0, np.empty((0, 2))) == -1

    signals = ferrofluid.FerrofluidSignals(
        field_gain=0.8,
        fluid_response=0.8,
        surface_tension=0.2,
        iridescence=30,
        max_spikes=20,
        social_pull=0.8,
        build_volume=0.8,
        collaboration_heat=0.8,
        diversity=0.8,
        star_velocity_pull=0.8,
        traffic_heat=0.8,
        merge_cadence=0.8,
        release_charge=0.8,
        streak_heat=0.8,
        highlight_density=0.8,
        dipole_lift=0.8,
    )
    ripples = ferrofluid._ambient_ripple_specs(
        [
            {
                "x": 100.0,
                "strength": 1.0,
                "radius": 8.0,
                "lang": "Python",
                "lang_hue": 150.0,
                "when": "2024-01-01",
            }
        ],
        signals,
        pool_y=500,
        visual_seed="coverage",
    )
    assert len(ripples) >= 3


def test_ferrofluid_budget_paths_and_invalid_repo_date(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    metrics = _rich_metrics()
    metrics["repos"].append({"name": "invalid", "date": "bad"})
    monkeypatch.setattr(
        ferrofluid,
        "CFG",
        replace(ferrofluid.CFG, grid_resolution=20, max_elements=0),
    )
    constrained = ferrofluid.generate(
        metrics, seed="coverage-ferrofluid", timeline=True
    )
    repeated = ferrofluid.generate(metrics, seed="coverage-ferrofluid", timeline=True)
    assert constrained == repeated
    assert not any(role.startswith("ferro-") for role in _svg_data_roles(constrained))

    monkeypatch.setattr(
        ferrofluid,
        "CFG",
        replace(ferrofluid.CFG, max_elements=10_000),
    )
    full = ferrofluid.generate(metrics, seed="coverage-ferrofluid", timeline=True)
    assert "ferro-dipole" in _svg_data_roles(full)
