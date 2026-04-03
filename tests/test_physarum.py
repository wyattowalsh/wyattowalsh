from __future__ import annotations

import math
import re
from copy import deepcopy

import pytest
from defusedxml import ElementTree

np = pytest.importorskip("numpy", reason="numpy is required by scripts.art.physarum")
pytest.importorskip("scipy", reason="scipy is required by scripts.art.physarum")

physarum = pytest.importorskip("scripts.art.physarum")

generate = physarum.generate


def _sample_metrics() -> dict:
    return {
        "label": "Physarum Test",
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


def _timeline_rows(svg: str) -> list[tuple[str, float]]:
    return [
        (when, float(delay))
        for delay, when in re.findall(
            r'data-delay="([0-9]+(?:\.[0-9]+)?)"\s+data-when="(\d{4}-\d{2}-\d{2})"',
            svg,
        )
    ]


def _circle_radii_by_day(svg: str) -> dict[str, list[float]]:
    radii_by_day: dict[str, list[float]] = {}
    for radius, when in re.findall(
        r'<circle [^>]*r="([0-9]+(?:\.[0-9]+)?)"[^>]*data-when="(\d{4}-\d{2}-\d{2})"',
        svg,
    ):
        radii_by_day.setdefault(when, []).append(float(radius))
    return radii_by_day


def test_physarum_generate_returns_valid_svg() -> None:
    svg = generate(_sample_metrics(), seed="physarum-svg")

    root = ElementTree.fromstring(svg)

    assert root.tag.endswith("svg")
    assert root.attrib["viewBox"] == "0 0 800 800"
    assert svg.rstrip().endswith("</svg>")
    assert "<path" in svg or "<circle" in svg


def test_physarum_output_is_deterministic_for_same_seed() -> None:
    metrics = _sample_metrics()

    svg_1 = generate(metrics, seed="fixed-seed", timeline=True, loop_duration=24.0)
    svg_2 = generate(metrics, seed="fixed-seed", timeline=True, loop_duration=24.0)

    assert svg_1 == svg_2


def test_physarum_snapshot_signals_modulate_simulation_parameters(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    baseline_metrics = _sample_metrics()
    enriched_metrics = deepcopy(baseline_metrics)
    enriched_metrics["recent_merged_prs"] = [
        {
            "repo_name": "alpha",
            "merged_at": "2023-03-08T10:00:00Z",
            "additions": 120,
            "deletions": 30,
        },
        {
            "repo_name": "alpha",
            "merged_at": "2023-03-18T11:30:00Z",
            "additions": 80,
            "deletions": 12,
        },
    ]
    enriched_metrics["issue_stats"] = {"open_count": 2, "closed_count": 28}
    enriched_metrics["commit_hour_distribution"] = {10: 4, 11: 8, 12: 7}
    enriched_metrics["contribution_streaks"] = {
        "current_streak_months": 9,
        "longest_streak_months": 11,
        "streak_active": True,
    }
    enriched_metrics["repo_recency_bands"] = {
        "fresh": 1,
        "recent": 1,
        "established": 0,
        "legacy": 0,
    }

    runs: list[dict[str, float | list[tuple[int, int, float]]]] = []

    def fake_run_simulation(
        grid: int,
        food_sources: list[tuple[int, int, float]],
        *,
        n_agents: int,
        steps: int,
        config: object,
        rng: object,
        evaporation_rate: float,
        speed_mult: float,
        deposit_amount: float,
    ) -> np.ndarray:
        runs.append(
            {
                "n_agents": float(n_agents),
                "steps": float(steps),
                "evaporation_rate": evaporation_rate,
                "speed_mult": speed_mult,
                "deposit_amount": deposit_amount,
                "food_sources": list(food_sources),
            },
        )
        return np.zeros((grid, grid), dtype=np.float64)

    monkeypatch.setattr(physarum, "_run_simulation", fake_run_simulation)

    generate(baseline_metrics, seed="baseline-signals", timeline=False)
    generate(enriched_metrics, seed="baseline-signals", timeline=False)

    baseline_run, enriched_run = runs

    assert enriched_run["n_agents"] > baseline_run["n_agents"]
    assert enriched_run["speed_mult"] > baseline_run["speed_mult"]
    assert enriched_run["evaporation_rate"] < baseline_run["evaporation_rate"]


def test_physarum_recent_activity_boosts_food_sources_and_contour_density(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    baseline_metrics = _sample_metrics()

    active_metrics = _sample_metrics()
    active_metrics["repos"] = [
        {
            "name": "alpha",
            "language": "Python",
            "stars": 5,
            "age_months": 2,
            "date": "2023-01-05T12:00:00Z",
        },
        {
            "name": "beta",
            "language": "Go",
            "stars": 5,
            "age_months": 48,
            "date": "2023-03-12T00:00:00Z",
        },
    ]
    active_metrics["repo_recency_bands"] = {
        "fresh": 1,
        "recent": 0,
        "established": 0,
        "legacy": 1,
    }
    active_metrics["recent_merged_prs"] = [
        {
            "repo_name": "alpha",
            "merged_at": "2023-03-10T12:00:00Z",
            "additions": 150,
            "deletions": 10,
        },
        {
            "repo_name": "alpha",
            "merged_at": "2023-03-18T09:30:00Z",
            "additions": 90,
            "deletions": 20,
        },
    ]
    active_metrics["issue_stats"] = {"open_count": 1, "closed_count": 24}
    active_metrics["commit_hour_distribution"] = {10: 7, 11: 9, 12: 8}
    active_metrics["contribution_streaks"] = {
        "current_streak_months": 8,
        "longest_streak_months": 9,
        "streak_active": True,
    }

    runs: list[dict[str, list[tuple[int, int, float]] | list[float]]] = []
    current_run = -1

    def fake_run_simulation(
        grid: int,
        food_sources: list[tuple[int, int, float]],
        *,
        n_agents: int,
        steps: int,
        config: object,
        rng: object,
        evaporation_rate: float,
        speed_mult: float,
        deposit_amount: float,
    ) -> np.ndarray:
        nonlocal current_run
        current_run += 1
        runs.append({"food_sources": list(food_sources), "levels": []})
        return np.ones((grid, grid), dtype=np.float64)

    def fake_extract_contours(
        field: np.ndarray,
        grid: int,
        level: float,
        cell_w: float,
        cell_h: float,
    ) -> list[list[tuple[float, float]]]:
        runs[current_run]["levels"].append(level)
        return []

    monkeypatch.setattr(physarum, "_run_simulation", fake_run_simulation)
    monkeypatch.setattr(physarum, "_extract_contours", fake_extract_contours)

    generate(baseline_metrics, seed="physarum-baseline", timeline=False)
    generate(active_metrics, seed="physarum-activity", timeline=False)

    baseline_run, active_run = runs

    assert len(active_run["levels"]) > len(baseline_run["levels"])
    assert active_run["food_sources"][0][2] > active_run["food_sources"][1][2]


def test_physarum_timeline_can_be_enabled_and_disabled() -> None:
    loop_duration = 24.0
    reveal_fraction = 0.6
    metrics = _sample_metrics()

    timeline_svg = generate(
        metrics,
        seed="physarum-timeline",
        timeline=True,
        loop_duration=loop_duration,
        reveal_fraction=reveal_fraction,
    )
    legacy_svg = generate(
        metrics,
        seed="physarum-timeline",
        timeline=False,
        maturity=0.35,
    )

    timeline_rows = _timeline_rows(timeline_svg)
    by_date: dict[str, list[float]] = {}
    for when, delay in timeline_rows:
        by_date.setdefault(when, []).append(delay)

    assert "@keyframes physReveal" in timeline_svg
    assert 'class="tl-reveal' in timeline_svg
    assert timeline_rows
    assert "2023-01-05" in by_date
    assert "2023-03-12" in by_date
    assert max(by_date["2023-01-05"]) < min(by_date["2023-03-12"])

    reveal_end = loop_duration * reveal_fraction
    for _, delay in timeline_rows:
        assert 0.0 <= delay <= reveal_end + 1e-9

    assert "@keyframes physReveal" not in legacy_svg
    assert 'class="tl-reveal' not in legacy_svg
    assert "data-delay=" not in legacy_svg
    assert "opacity=" in legacy_svg


def test_physarum_timeline_prefers_contributions_daily_when_available() -> None:
    metrics = {
        **_sample_metrics(),
        "contributions_monthly": {"2023-01": 40},
        "contributions_daily": {
            "2023-01-01": 1,
            "2023-01-20": 39,
        },
        "repos": [
            {
                "name": "alpha",
                "language": "Python",
                "stars": 3,
                "age_months": 1,
                "date": "2023-01-10T00:00:00Z",
            },
        ],
        "stars": 3,
    }

    svg = generate(metrics, seed="physarum-daily", timeline=True, loop_duration=20.0)
    timeline_days = {when for when, _delay in _timeline_rows(svg)}

    assert "2023-01-20" in timeline_days


def test_physarum_older_repos_render_stronger_nodes_than_fresh_repos() -> None:
    metrics = {
        **_sample_metrics(),
        "contributions_monthly": {
            "2023-01": 20,
            "2023-02": 20,
            "2023-03": 20,
        },
        "contributions_last_year": 60,
        "repos": [
            {
                "name": "mature",
                "language": "Python",
                "stars": 5,
                "age_months": 6,
                "date": "2023-01-05T00:00:00Z",
            },
            {
                "name": "fresh",
                "language": "Go",
                "stars": 5,
                "age_months": 0,
                "date": "2023-03-15T00:00:00Z",
            },
        ],
        "stars": 10,
    }

    svg = generate(metrics, seed="physarum-age", timeline=True)
    radii_by_day = _circle_radii_by_day(svg)

    assert max(radii_by_day["2023-01-05"]) > max(radii_by_day["2023-03-15"])


def test_physarum_growth_origin_biases_toward_weighted_food_cluster() -> None:
    sources = [
        (10.0, 14.0, 10.0),
        (14.0, 18.0, 7.0),
        (62.0, 64.0, 1.5),
    ]

    origin = physarum._resolve_growth_origin(
        sources,
        span=80.0,
        fallback=(40.0, 40.0),
    )
    dominant_x = (10.0 * 10.0 + 14.0 * 7.0) / 17.0
    dominant_y = (14.0 * 10.0 + 18.0 * 7.0) / 17.0

    assert math.hypot(origin.x - dominant_x, origin.y - dominant_y) < math.hypot(
        origin.x - 40.0,
        origin.y - 40.0,
    )
    assert origin.spread > 0


def test_physarum_vein_style_prefers_nearest_repo_identity() -> None:
    python_identity = physarum._repo_identity_palette(
        {"language": "Python", "topics": ["viz", "art"]},
    )
    go_identity = physarum._repo_identity_palette(
        {"language": "Go", "topics": ["infra", "devops"]},
    )
    identity_nodes = [
        physarum.PhysarumIdentityNode(
            x=140.0,
            y=140.0,
            conc=12.0,
            identity=python_identity,
        ),
        physarum.PhysarumIdentityNode(
            x=640.0,
            y=640.0,
            conc=12.0,
            identity=go_identity,
        ),
    ]
    base_color = physarum.oklch(0.70, 0.10, 70.0)

    python_color, python_visibility = physarum._resolve_vein_style(
        [(150.0, 148.0), (162.0, 156.0), (172.0, 166.0)],
        base_color,
        identity_nodes,
    )
    go_color, go_visibility = physarum._resolve_vein_style(
        [(628.0, 632.0), (642.0, 646.0), (652.0, 658.0)],
        base_color,
        identity_nodes,
    )

    assert python_color != base_color
    assert go_color != base_color
    assert python_color != go_color
    assert python_visibility > 0
    assert go_visibility > 0


def test_physarum_svg_nodes_use_identity_tinted_core_colors() -> None:
    metrics = _sample_metrics()
    metrics["repos"] = [
        {
            "name": "alpha",
            "language": "Python",
            "topics": ["viz", "art"],
            "stars": 12,
            "age_months": 24,
            "date": "2023-01-05T12:00:00Z",
        },
        {
            "name": "beta",
            "language": "Go",
            "topics": ["infra", "devops"],
            "stars": 3,
            "age_months": 12,
            "date": "2023-03-12T00:00:00Z",
        },
    ]

    svg = generate(
        metrics,
        seed="physarum-identity-colors",
        timeline=False,
        maturity=0.6,
    )
    node_colors = dict(
        re.findall(
            r'data-role="physarum-node-core"[^>]*data-language="([^"]+)"[^>]*fill="(#[0-9a-f]{6})"',
            svg,
        )
    )

    assert node_colors["Python"] != node_colors["Go"]


def test_physarum_richer_cumulative_snapshots_generate_denser_networks() -> None:
    early_metrics = {
        "account_created": "2023-01-01T00:00:00Z",
        "contributions_monthly": {"2023-01": 2},
        "contributions_last_year": 2,
        "total_commits": 2,
        "repos": [
            {
                "name": "alpha",
                "language": "Python",
                "stars": 0,
                "age_months": 0,
                "date": "2023-01-15T00:00:00Z",
            },
        ],
        "stars": 0,
        "total_prs": 0,
        "total_issues": 0,
        "releases": [],
    }
    late_metrics = {
        "account_created": "2023-01-01T00:00:00Z",
        "contributions_monthly": {
            "2023-01": 40,
            "2023-02": 50,
            "2023-03": 60,
        },
        "contributions_last_year": 150,
        "total_commits": 900,
        "repos": [
            {
                "name": "alpha",
                "language": "Python",
                "stars": 12,
                "age_months": 18,
                "date": "2023-01-10T00:00:00Z",
                "topics": ["ai", "viz"],
            },
            {
                "name": "beta",
                "language": "Go",
                "stars": 6,
                "age_months": 12,
                "date": "2023-02-01T00:00:00Z",
                "topics": ["infra", "viz"],
            },
            {
                "name": "gamma",
                "language": "Rust",
                "stars": 4,
                "age_months": 6,
                "date": "2023-03-01T00:00:00Z",
                "topics": ["viz"],
            },
        ],
        "stars": 22,
        "total_prs": 30,
        "total_issues": 18,
        "releases": [
            {
                "tag_name": "v1.0.0",
                "published_at": "2023-02-15T00:00:00Z",
            },
        ],
        "recent_merged_prs": [
            {
                "repo_name": "alpha",
                "merged_at": "2023-03-05T00:00:00Z",
                "additions": 120,
                "deletions": 30,
            },
            {
                "repo_name": "beta",
                "merged_at": "2023-03-08T00:00:00Z",
                "additions": 80,
                "deletions": 10,
            },
        ],
        "contribution_streaks": {"current": 12},
        "languages": {"Python": 0.5, "Go": 0.3, "Rust": 0.2},
        "topic_clusters": {"build": ["infra"], "creative": ["viz"]},
    }

    early_svg = generate(
        early_metrics,
        seed="physarum-cumulative",
        timeline=False,
        maturity=0.35,
    )
    late_svg = generate(
        late_metrics,
        seed="physarum-cumulative",
        timeline=False,
        maturity=0.35,
    )

    assert late_svg.count("<path ") > early_svg.count("<path ")


@pytest.mark.parametrize(
    ("metrics", "seed"),
    [
        ({}, "physarum-empty"),
        ({"repos": [], "contributions_monthly": {}}, "physarum-minimal"),
    ],
)
def test_physarum_handles_empty_and_minimal_metrics_without_crashing(
    metrics: dict,
    seed: str,
) -> None:
    svg = generate(metrics, seed=seed, timeline=False, maturity=0.0)

    root = ElementTree.fromstring(svg)

    assert root.tag.endswith("svg")
    assert svg.rstrip().endswith("</svg>")
