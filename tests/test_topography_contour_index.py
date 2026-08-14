"""Regression tests for byte-stable indexed topography contour stitching."""

from __future__ import annotations

import copy
import math
from collections.abc import Callable

import pytest

from scripts.art import topography

_JOIN_RADIUS = 8.0

_Point = tuple[float, float]
_Segment = tuple[_Point, _Point]
_Distance = Callable[[_Point, _Point], float]


def _distance(first: _Point, second: _Point) -> float:
    return math.sqrt((second[0] - first[0]) ** 2 + (second[1] - first[1]) ** 2)


def _reference_stitch(
    segments: list[_Segment],
    *,
    distance: _Distance = _distance,
) -> list[list[_Point]]:
    """Former all-segments scan, retained here as the parity oracle."""
    used = [False] * len(segments)
    chains: list[list[_Point]] = []
    for start_index in range(len(segments)):
        if used[start_index]:
            continue
        used[start_index] = True
        chain = [segments[start_index][0], segments[start_index][1]]
        changed = True
        while changed:
            changed = False
            last = chain[-1]
            best_distance, best_segment, best_endpoint = _JOIN_RADIUS, -1, 0
            for segment_index in range(len(segments)):
                if used[segment_index]:
                    continue
                for endpoint_index in (0, 1):
                    candidate_distance = distance(
                        last,
                        segments[segment_index][endpoint_index],
                    )
                    if candidate_distance < best_distance:
                        best_distance = candidate_distance
                        best_segment = segment_index
                        best_endpoint = endpoint_index
            if best_segment >= 0:
                used[best_segment] = True
                chain.append(
                    segments[best_segment][1 - best_endpoint]
                    if best_endpoint == 0
                    else segments[best_segment][0]
                )
                changed = True
        if len(chain) >= 3:
            chains.append(chain)
    return chains


@pytest.mark.parametrize(
    "segments",
    [
        pytest.param([], id="empty"),
        pytest.param(
            [
                ((-9.0, 0.0), (-0.1, 0.0)),
                ((7.8, 0.0), (20.0, 0.0)),
            ],
            id="joins-across-negative-bucket-boundary",
        ),
        pytest.param(
            [
                ((-10.0, 0.0), (0.0, 0.0)),
                ((8.0, 0.0), (20.0, 0.0)),
            ],
            id="strict-radius-does-not-join-at-eight",
        ),
        pytest.param(
            [
                ((-10.0, 0.0), (0.0, 0.0)),
                ((3.0, 4.0), (30.0, 30.0)),
                ((0.0, 5.0), (40.0, 40.0)),
            ],
            id="equal-distance-keeps-earlier-segment",
        ),
        pytest.param(
            [
                ((-10.0, 0.0), (0.0, 0.0)),
                ((30.0, 30.0), (4.0, 3.0)),
                ((40.0, 40.0), (0.0, 5.0)),
            ],
            id="equal-distance-keeps-earlier-endpoint-order",
        ),
    ],
)
def test_indexed_stitch_matches_reference_edge_cases(
    segments: list[_Segment],
) -> None:
    assert topography._stitch_contour_segments(segments) == _reference_stitch(segments)


def _snapshot_metrics(repo_count: int) -> dict:
    repos = [
        {
            "name": f"repo-{index}",
            "language": ("Python", "Go", "Rust")[index % 3],
            "stars": 3 + index * 11,
            "age_months": 36 - index * 5,
            "date": f"202{index}-0{index + 1}-01T00:00:00Z",
            "topics": ["art", f"topic-{index}"],
        }
        for index in range(repo_count)
    ]
    render_state = {
        "label": "Contour parity",
        "account_created": "2019-01-01T00:00:00Z",
        "contributions_last_year": 80 + repo_count * 120,
        "contributions_monthly": {
            "2023-01": 10,
            "2023-06": 20 + repo_count * 5,
            "2024-01": 30 + repo_count * 10,
        },
        "contributions_daily": {
            "2023-01-03": 2,
            "2023-06-12": 4 + repo_count,
            "2024-01-20": 8 + repo_count * 2,
        },
        "repos": repos,
        "top_repos": repos,
        "public_repos": repo_count,
        "followers": repo_count * 14,
        "forks": repo_count * 3,
        "stars": sum(repo["stars"] for repo in repos),
        "total_commits": 200 + repo_count * 500,
        "languages": {
            language: repo_count * (index + 1)
            for index, language in enumerate(("Python", "Go", "Rust"))
        },
        "topic_clusters": {"art": repo_count, "mapping": max(1, repo_count - 1)},
        "cumulative_state": {"snapshot_index": repo_count},
    }
    return {"label": "Contour parity wrapper", "render_state": render_state}


@pytest.mark.parametrize(
    ("repo_count", "maturity"),
    [(1, 0.2), (2, 0.6), (3, 1.0)],
    ids=("early", "middle", "late"),
)
def test_indexed_stitch_preserves_representative_snapshot_svg_bytes(
    monkeypatch: pytest.MonkeyPatch,
    repo_count: int,
    maturity: float,
) -> None:
    monkeypatch.setattr(topography, "TOPOGRAPHY_GRID_SIZE", 48)
    metrics = _snapshot_metrics(repo_count)
    seed = f"contour-index-parity-{repo_count}"

    indexed_svg = topography.generate(
        copy.deepcopy(metrics),
        seed=seed,
        maturity=maturity,
        timeline=False,
    )
    monkeypatch.setattr(topography, "_stitch_contour_segments", _reference_stitch)
    reference_svg = topography.generate(
        copy.deepcopy(metrics),
        seed=seed,
        maturity=maturity,
        timeline=False,
    )

    assert indexed_svg.encode("utf-8") == reference_svg.encode("utf-8")


def test_spatial_index_reduces_distance_evaluations_deterministically(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    segments: list[_Segment] = [
        ((index * 7.0, 0.0), (index * 7.0 + 1.0, 0.0)) for index in range(240)
    ]
    reference_evaluations = 0
    indexed_evaluations = 0

    def reference_distance(first: _Point, second: _Point) -> float:
        nonlocal reference_evaluations
        reference_evaluations += 1
        return _distance(first, second)

    def indexed_distance(first: _Point, second: _Point) -> float:
        nonlocal indexed_evaluations
        indexed_evaluations += 1
        return _distance(first, second)

    expected = _reference_stitch(segments, distance=reference_distance)
    monkeypatch.setattr(topography, "_contour_endpoint_distance", indexed_distance)
    observed = topography._stitch_contour_segments(segments)

    assert observed == expected
    assert indexed_evaluations * 10 < reference_evaluations
