"""Generator regression tests for the timelapse render_state contract."""

from __future__ import annotations

import copy
import re
from collections.abc import Callable

import pytest

pytest.importorskip("numpy", reason="living-art generators require numpy")

from scripts.art.ferrofluid import generate as generate_ferrofluid  # noqa: E402
from scripts.art.genetic_landscape import generate as generate_genetic  # noqa: E402
from scripts.art.ink_garden import generate as generate_ink_garden  # noqa: E402
from scripts.art.lenia import generate as generate_lenia  # noqa: E402
from scripts.art.physarum import generate as generate_physarum  # noqa: E402
from scripts.art.topography import generate as generate_topography  # noqa: E402


Generator = Callable[..., str]
Marker = Callable[[str], int]


def _render_state(*, repo_count: int, stars: int) -> dict:
    repos = []
    topic_clusters: dict[str, int] = {}
    languages: dict[str, int] = {}
    for index in range(repo_count):
        name = f"repo-{index}"
        language = "Python" if index % 2 == 0 else "Go"
        topic = "ai" if index % 2 == 0 else "automation"
        repos.append(
            {
                "name": name,
                "language": language,
                "stars": max(1, stars // max(1, repo_count - index)),
                "forks": 1 + index,
                "topics": [topic],
                "description": f"Repo {index}",
                "age_months": 3 + index * 4,
                "date": f"2025-01-{index + 1:02d}T12:00:00Z",
            }
        )
        topic_clusters[topic] = topic_clusters.get(topic, 0) + 1
        languages[language] = languages.get(language, 0) + 1000 * (index + 1)

    return {
        "label": "Render State",
        "account_created": "2024-01-01T00:00:00Z",
        "repos": repos,
        "repo_visual_order": [repo["name"] for repo in repos],
        "stars": stars,
        "forks": repo_count,
        "watchers": repo_count * 2,
        "followers": 12 + repo_count * 5,
        "public_repos": repo_count,
        "network_count": repo_count * 3,
        "total_commits": 120 + repo_count * 60,
        "total_prs": 20 + repo_count * 4,
        "total_issues": 8 + repo_count * 3,
        "total_repos_contributed": 4 + repo_count,
        "public_gists": repo_count,
        "pr_review_count": 3 + repo_count,
        "release_count": repo_count,
        "merged_pr_count": repo_count,
        "contributions_to_date": 80 + repo_count * 40,
        "contributions_last_year": 80 + repo_count * 40,
        "contributions_monthly": {
            "2025-01": 12,
            "2025-02": 16,
            "2025-03": 20 + repo_count,
        },
        "contributions_daily": {
            f"2025-03-{day:02d}": 1 + (day % 3) for day in range(1, 8 + repo_count)
        },
        "languages": languages,
        "language_count": len(languages),
        "language_diversity": 0.8 + repo_count * 0.05,
        "topic_clusters": topic_clusters,
        "repo_recency_bands": {"fresh": 1, "recent": max(0, repo_count - 1)},
        "releases": [
            {
                "published_at": f"2025-03-{index + 1:02d}T12:00:00Z",
                "name": f"v{index + 1}.0.0",
            }
            for index in range(repo_count)
        ],
        "recent_merged_prs": [
            {
                "merged_at": f"2025-03-{index + 1:02d}T13:00:00Z",
                "title": f"PR {index + 1}",
            }
            for index in range(repo_count)
        ],
        "commit_hour_distribution": {9: 2, 12: 4 + repo_count, 18: 3},
        "star_velocity": {
            "recent_rate": 1.0 + repo_count,
            "peak_rate": 1.0 + repo_count,
            "trend": "rising",
        },
        "contribution_streaks": {
            "current_streak_months": 2 + repo_count,
            "longest_streak_months": 2 + repo_count,
            "streak_active": True,
        },
        "issue_stats": {"open_count": 2 + repo_count, "closed_count": 8 + repo_count},
        "open_issues_count": 2 + repo_count,
        "cumulative_state": {
            "stars": stars,
            "forks": repo_count,
            "watchers": repo_count * 2,
            "followers": 12 + repo_count * 5,
            "public_repos": repo_count,
            "network_count": repo_count * 3,
            "total_commits": 120 + repo_count * 60,
            "total_prs": 20 + repo_count * 4,
            "total_issues": 8 + repo_count * 3,
            "total_repos_contributed": 4 + repo_count,
            "public_gists": repo_count,
            "pr_review_count": 3 + repo_count,
            "release_count": repo_count,
            "merged_pr_count": repo_count,
            "contributions_to_date": 80 + repo_count * 40,
        },
    }


def _wrapped_metrics(render_state: dict) -> dict:
    raw = {
        "label": "Shrinking Raw Payload",
        "stars": 1,
        "forks": 0,
        "watchers": 0,
        "followers": 0,
        "public_repos": 0,
        "network_count": 0,
        "total_commits": 1,
        "total_prs": 0,
        "total_issues": 0,
        "total_repos_contributed": 0,
        "public_gists": 0,
        "pr_review_count": 0,
        "contributions_last_year": 1,
        "open_issues_count": 0,
        "repos": [],
        "languages": {},
        "topic_clusters": {},
        "repo_recency_bands": {},
        "contributions_monthly": {},
        "contributions_daily": {},
        "releases": [],
        "recent_merged_prs": [],
        "commit_hour_distribution": {},
        "star_velocity": {"recent_rate": 0.0, "peak_rate": 0.0, "trend": "stable"},
        "contribution_streaks": {
            "current_streak_months": 0,
            "longest_streak_months": 0,
            "streak_active": False,
        },
    }
    raw["render_state"] = copy.deepcopy(render_state)
    return raw


_STYLE_CASES: list[tuple[str, Generator, Marker]] = [
    ("inkgarden", generate_ink_garden, lambda svg: svg.count('class="repo-tree"')),
    ("topo", generate_topography, lambda svg: svg.count('class="repo-peak"')),
    (
        "genetic",
        generate_genetic,
        lambda svg: int(re.search(r'data-peak-count="(\d+)"', svg).group(1)),
    ),
    (
        "physarum",
        generate_physarum,
        lambda svg: svg.count('data-role="physarum-node-core"'),
    ),
    ("lenia", generate_lenia, lambda svg: svg.count('data-role="lenia-seed-halo"')),
    (
        "ferrofluid",
        generate_ferrofluid,
        lambda svg: svg.count('data-role="ferro-dipole"'),
    ),
]


@pytest.mark.parametrize(("style", "generator", "marker"), _STYLE_CASES)
def test_generators_prefer_render_state(
    style: str,
    generator: Generator,
    marker: Marker,
) -> None:
    render_state = _render_state(repo_count=3, stars=30)
    wrapped = _wrapped_metrics(render_state)

    svg_from_wrapper = generator(wrapped, seed=f"{style}-render-state", timeline=False)
    svg_from_render_state = generator(
        copy.deepcopy(render_state),
        seed=f"{style}-render-state",
        timeline=False,
    )

    assert svg_from_wrapper == svg_from_render_state
    assert marker(svg_from_wrapper) > 0


@pytest.mark.parametrize(("style", "generator", "marker"), _STYLE_CASES)
def test_generators_keep_monotonic_complexity_from_render_state(
    style: str,
    generator: Generator,
    marker: Marker,
) -> None:
    early = _render_state(repo_count=1, stars=6)
    mid = _render_state(repo_count=2, stars=16)
    late = _render_state(repo_count=3, stars=30)

    markers = [
        marker(generator(early, seed=f"{style}-mono", timeline=False)),
        marker(generator(mid, seed=f"{style}-mono", timeline=False)),
        marker(generator(late, seed=f"{style}-mono", timeline=False)),
    ]

    assert markers == sorted(markers), f"{style} markers regressed: {markers}"
