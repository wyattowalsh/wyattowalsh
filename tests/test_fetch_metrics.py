"""Tests for scripts.fetch_metrics — expanded metrics collection."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_repo(
    name: str,
    *,
    fork: bool = False,
    stars: int = 0,
    forks: int = 0,
    language: str | None = None,
    languages_url: str = "",
    owner_login: str = "owner",
) -> dict[str, Any]:
    """Build a minimal repo dict matching GitHub REST shape."""
    return {
        "name": name,
        "full_name": f"owner/{name}",
        "owner": {"login": owner_login},
        "fork": fork,
        "stargazers_count": stars,
        "forks_count": forks,
        "language": language,
        "languages_url": (
            languages_url
            or f"https://api.github.com/repos/owner/{name}/languages"
        ),
        "description": f"Description of {name}",
        "topics": ["topic-a"],
        "updated_at": "2025-01-01T00:00:00Z",
    }


@pytest.fixture
def mock_get():
    """Patch _get in scripts.fetch_metrics (returns (data, headers) tuples)."""
    with patch("scripts.fetch_metrics._get") as m:
        yield m


@pytest.fixture
def mock_paginate_rest():
    """Patch _paginate_rest in scripts.fetch_metrics."""
    with patch("scripts.fetch_metrics._paginate_rest") as m:
        yield m


@pytest.fixture
def mock_graphql():
    """Patch _graphql in scripts.fetch_metrics."""
    with patch("scripts.fetch_metrics._graphql") as m:
        yield m


# ---------------------------------------------------------------------------
# _collect_languages
# ---------------------------------------------------------------------------

class TestCollectLanguages:
    def test_aggregates_bytes_across_repos(self, mock_get: MagicMock) -> None:
        from scripts.fetch_metrics import _collect_languages

        repos = [
            _make_repo("a", languages_url="http://lang/a"),
            _make_repo("b", languages_url="http://lang/b"),
        ]
        mock_get.side_effect = [
            ({"Python": 100, "Go": 50}, {}),  # languages for repo a
            ({"Python": 200, "Rust": 30}, {}),  # languages for repo b
        ]
        result = _collect_languages(repos, "tok")
        assert result == {"Python": 300, "Go": 50, "Rust": 30}

    def test_skips_forks(self, mock_get: MagicMock) -> None:
        from scripts.fetch_metrics import _collect_languages

        repos = [
            _make_repo("mine", languages_url="http://lang/mine"),
            _make_repo("forked", fork=True, languages_url="http://lang/forked"),
        ]
        mock_get.side_effect = [
            ({"Python": 100}, {}),
        ]
        result = _collect_languages(repos, "tok")
        assert result == {"Python": 100}
        # Should not have fetched languages for the fork
        # (only 1 call — no repos list fetch).
        assert mock_get.call_count == 1

    def test_handles_language_fetch_error(self, mock_get: MagicMock) -> None:
        from scripts.fetch_metrics import _collect_languages

        repos = [_make_repo("a", languages_url="http://lang/a")]
        mock_get.side_effect = [
            Exception("network error"),
        ]
        result = _collect_languages(repos, "tok")
        assert result == {}


# ---------------------------------------------------------------------------
# _collect_traffic
# ---------------------------------------------------------------------------

class TestCollectTraffic:
    def test_returns_empty_without_token(self) -> None:
        from scripts.fetch_metrics import _collect_traffic

        result = _collect_traffic("owner", "repo", None)
        assert result == {}

    def test_collects_views_and_clones(self, mock_get: MagicMock) -> None:
        from scripts.fetch_metrics import _collect_traffic

        mock_get.side_effect = [
            ({"count": 100, "uniques": 42}, {}),  # views
            ({"count": 20, "uniques": 5}, {}),  # clones
            (
                [{"referrer": "google"}, {"referrer": "github"}],
                {},
            ),  # referrers
        ]
        result = _collect_traffic("owner", "repo", "tok")
        assert result["traffic_views_14d"] == 100
        assert result["traffic_unique_visitors_14d"] == 42
        assert result["traffic_clones_14d"] == 20
        assert result["traffic_unique_cloners_14d"] == 5
        assert result["traffic_top_referrers"] == ["google", "github"]

    def test_handles_traffic_errors_gracefully(self, mock_get: MagicMock) -> None:
        from scripts.fetch_metrics import _collect_traffic

        mock_get.side_effect = Exception("forbidden")
        result = _collect_traffic("owner", "repo", "tok")
        # Should not raise; returns partial or empty
        assert isinstance(result, dict)


# ---------------------------------------------------------------------------
# _collect_recent_merged_prs
# ---------------------------------------------------------------------------

class TestCollectRecentMergedPrs:
    def test_paginates_and_preserves_repo_identity(
        self, mock_graphql: MagicMock
    ) -> None:
        from scripts.fetch_metrics import _collect_recent_merged_prs

        mock_graphql.side_effect = [
            {
                "data": {
                    "user": {
                        "pullRequests": {
                            "nodes": [
                                {
                                    "mergedAt": "2024-03-01T00:00:00Z",
                                    "additions": 4,
                                    "deletions": 1,
                                    "repository": {
                                        "name": "beta",
                                        "nameWithOwner": "owner/beta",
                                    },
                                },
                                {
                                    "mergedAt": "2024-02-01T00:00:00Z",
                                    "additions": 10,
                                    "deletions": 3,
                                    "repository": {
                                        "name": "alpha",
                                        "nameWithOwner": "owner/alpha",
                                    },
                                },
                            ],
                            "pageInfo": {
                                "hasNextPage": True,
                                "endCursor": "cursor-1",
                            },
                        }
                    }
                }
            },
            {
                "data": {
                    "user": {
                        "pullRequests": {
                            "nodes": [
                                {
                                    "mergedAt": "2024-04-01T00:00:00Z",
                                    "additions": 7,
                                    "deletions": 2,
                                    "repository": {
                                        "name": "gamma",
                                        "nameWithOwner": "owner/gamma",
                                    },
                                },
                            ],
                            "pageInfo": {"hasNextPage": False, "endCursor": None},
                        }
                    }
                }
            },
        ]

        result = _collect_recent_merged_prs("owner", "tok")

        assert [pr["repo_full_name"] for pr in result] == [
            "owner/alpha",
            "owner/beta",
            "owner/gamma",
        ]
        assert result[0]["repo_name"] == "alpha"
        assert mock_graphql.call_count == 2
        assert (
            mock_graphql.call_args_list[1].kwargs["variables"]["cursor"]
            == "cursor-1"
        )

    def test_returns_empty_without_token(self) -> None:
        from scripts.fetch_metrics import _collect_recent_merged_prs

        assert _collect_recent_merged_prs("owner", None) == []


# ---------------------------------------------------------------------------
# _collect_commit_hour_distribution
# ---------------------------------------------------------------------------

class TestCollectCommitHourDistribution:
    def test_uses_all_visible_event_pages_and_weights_commit_counts(
        self, mock_paginate_rest: MagicMock
    ) -> None:
        from scripts.fetch_metrics import _BASE, _collect_commit_hour_distribution

        mock_paginate_rest.return_value = [
            {
                "type": "PushEvent",
                "created_at": "2025-03-01T01:15:00Z",
                "payload": {"size": 2},
            },
            {
                "type": "PushEvent",
                "created_at": "2025-03-02T01:45:00Z",
                "payload": {"commits": [{"sha": "1"}]},
            },
            {
                "type": "PushEvent",
                "created_at": "2025-03-03T23:00:00Z",
                "payload": {},
            },
            {"type": "IssuesEvent", "created_at": "2025-03-03T11:00:00Z"},
            {
                "type": "PushEvent",
                "created_at": "bad",
                "payload": {"size": 4},
            },
        ]

        distribution, sample_size = _collect_commit_hour_distribution("owner", "tok")

        assert distribution == {1: 3, 23: 1}
        assert sample_size == 4
        mock_paginate_rest.assert_called_once_with(
            f"{_BASE}/users/owner/events?per_page=100",
            "tok",
        )


# ---------------------------------------------------------------------------
# _collect_releases
# ---------------------------------------------------------------------------

class TestCollectReleases:
    def test_aggregates_owned_repo_releases_and_skips_unpublished(
        self, mock_paginate_rest: MagicMock
    ) -> None:
        from scripts.fetch_metrics import _BASE, _collect_releases

        repos = [
            _make_repo("alpha"),
            _make_repo("beta"),
            _make_repo("shared", owner_login="upstream"),
        ]

        def fake_paginate(
            url: str,
            token: str | None,
            *,
            accept: str | None = None,
            max_pages: int = 100,
        ) -> list[dict[str, Any]]:
            assert token == "tok"
            assert accept is None
            assert max_pages == 100
            if url == f"{_BASE}/repos/owner/alpha/releases?per_page=100":
                return [
                    {
                        "tag_name": "v1.0.0",
                        "published_at": "2024-01-01T00:00:00Z",
                        "name": "Alpha 1",
                    },
                    {
                        "tag_name": "draft",
                        "published_at": None,
                        "name": "Draft only",
                    },
                ]
            if url == f"{_BASE}/repos/owner/beta/releases?per_page=100":
                return [
                    {
                        "tag_name": "v2.0.0",
                        "published_at": "2024-02-01T00:00:00Z",
                        "name": "Beta 2",
                    },
                ]
            pytest.fail(f"Unexpected releases URL: {url}")

        mock_paginate_rest.side_effect = fake_paginate

        releases, scope, repo_count = _collect_releases(
            "owner", "profile", "tok", repos=repos
        )

        assert scope == "account_owned_repos"
        assert repo_count == 2
        assert releases == [
            {
                "tag_name": "v2.0.0",
                "published_at": "2024-02-01T00:00:00Z",
                "date": "2024-02-01T00:00:00Z",
                "name": "Beta 2",
                "repo_name": "beta",
                "repo_full_name": "owner/beta",
            },
            {
                "tag_name": "v1.0.0",
                "published_at": "2024-01-01T00:00:00Z",
                "date": "2024-01-01T00:00:00Z",
                "name": "Alpha 1",
                "repo_name": "alpha",
                "repo_full_name": "owner/alpha",
            },
        ]

    def test_falls_back_to_profile_repo_when_repo_inventory_is_missing(
        self, mock_paginate_rest: MagicMock
    ) -> None:
        from scripts.fetch_metrics import _BASE, _collect_releases

        mock_paginate_rest.return_value = [
            {
                "tag_name": "v1.0.0",
                "published_at": "2024-03-01T00:00:00Z",
                "name": "Profile 1",
            },
        ]

        releases, scope, repo_count = _collect_releases("owner", "profile", "tok")

        assert scope == "profile_repo_fallback"
        assert repo_count == 1
        assert releases == [
            {
                "tag_name": "v1.0.0",
                "published_at": "2024-03-01T00:00:00Z",
                "date": "2024-03-01T00:00:00Z",
                "name": "Profile 1",
                "repo_name": "profile",
                "repo_full_name": "owner/profile",
            },
        ]
        mock_paginate_rest.assert_called_once_with(
            f"{_BASE}/repos/owner/profile/releases?per_page=100",
            "tok",
        )

    def test_matches_owned_repos_case_insensitively(
        self, mock_paginate_rest: MagicMock
    ) -> None:
        from scripts.fetch_metrics import _BASE, _collect_releases

        repos = [_make_repo("alpha", owner_login="WyAttOwAlsh")]
        repos[0]["full_name"] = "WyAttOwAlsh/alpha"
        mock_paginate_rest.return_value = [
            {
                "tag_name": "v1.0.0",
                "published_at": "2024-04-01T00:00:00Z",
                "name": "Alpha 1",
            },
        ]

        releases, scope, repo_count = _collect_releases(
            "wyattowalsh", "profile", "tok", repos=repos
        )

        assert scope == "account_owned_repos"
        assert repo_count == 1
        assert releases[0]["repo_full_name"] == "WyAttOwAlsh/alpha"
        mock_paginate_rest.assert_called_once_with(
            f"{_BASE}/repos/WyAttOwAlsh/alpha/releases?per_page=100",
            "tok",
        )


# ---------------------------------------------------------------------------
# _collect_top_repos
# ---------------------------------------------------------------------------

class TestCollectTopRepos:
    def test_filters_forks_and_respects_limit(self) -> None:
        from scripts.fetch_metrics import _collect_top_repos

        repos = [
            _make_repo("star1", stars=100),
            _make_repo("forked", fork=True, stars=500),
            _make_repo("star2", stars=50),
            _make_repo("star3", stars=30),
        ]
        result = _collect_top_repos(repos, limit=2)
        assert len(result) == 2
        assert result[0]["name"] == "star1"
        assert result[1]["name"] == "star2"
        # Forked repo should not appear
        assert all(r["name"] != "forked" for r in result)

    def test_returns_expected_fields(self) -> None:
        from scripts.fetch_metrics import _collect_top_repos

        repos = [_make_repo("myrepo", stars=10, language="Python")]
        result = _collect_top_repos(repos)
        repo = result[0]
        for key in (
            "name",
            "full_name",
            "stars",
            "forks",
            "language",
            "description",
            "topics",
            "updated_at",
        ):
            assert key in repo


# ---------------------------------------------------------------------------
# GraphQL expanded fields
# ---------------------------------------------------------------------------

class TestGraphQLExpanded:
    def test_parses_all_new_fields(
        self,
        mock_get: MagicMock,
        mock_graphql: MagicMock,
        mock_paginate_rest: MagicMock,
    ) -> None:
        from scripts.fetch_metrics import collect

        # Stub REST calls to return minimal data (tuples for _get)
        mock_get.return_value = ([], {})
        mock_paginate_rest.return_value = []

        mock_graphql.return_value = {
            "data": {
                "viewer": {
                    "contributionsCollection": {
                        "contributionCalendar": {
                            "totalContributions": 1234,
                            "weeks": [
                                {
                                    "contributionDays": [
                                        {
                                            "date": "2025-03-01",
                                            "contributionCount": 5,
                                            "color": "#216e39",
                                        },
                                        {
                                            "date": "2025-03-02",
                                            "contributionCount": 3,
                                            "color": "#30a14e",
                                        },
                                    ]
                                },
                            ],
                        },
                        "totalCommitContributions": 800,
                        "totalPullRequestContributions": 150,
                        "totalIssueContributions": 50,
                        "totalRepositoryContributions": 20,
                    }
                }
            }
        }

        result = collect("owner", "repo", "tok")
        assert result["contributions_last_year"] == 1234
        assert result["total_commits"] == 800
        assert result["total_prs"] == 150
        assert result["total_issues"] == 50
        assert result["total_repos_contributed"] == 20
        assert isinstance(result["contributions_calendar"], list)
        assert len(result["contributions_calendar"]) == 2
        assert result["contributions_calendar"][0] == {
            "date": "2025-03-01",
            "count": 5,
            "color": "#216e39",
        }

    def test_no_token_sets_none_values(
        self, mock_get: MagicMock, mock_paginate_rest: MagicMock
    ) -> None:
        from scripts.fetch_metrics import collect

        mock_get.return_value = ([], {})
        mock_paginate_rest.return_value = []
        result = collect("owner", "repo", None)
        assert result["contributions_last_year"] is None
        assert result["total_commits"] is None
        assert result["total_prs"] is None
        assert result["total_issues"] is None
        assert result["total_repos_contributed"] is None
        assert result["contributions_calendar"] == []


# ---------------------------------------------------------------------------
# collect() integration — all keys present
# ---------------------------------------------------------------------------

class TestCollectIntegration:
    def test_collect_returns_all_expected_keys(
        self,
        mock_get: MagicMock,
        mock_paginate_rest: MagicMock,
        mock_graphql: MagicMock,
    ) -> None:
        from scripts.fetch_metrics import collect

        # Stub REST calls
        repo_data = {
            "stargazers_count": 10,
            "forks_count": 2,
            "watchers_count": 10,
            "network_count": 2,
            "open_issues_count": 1,
        }
        user_data = {
            "followers": 100,
            "following": 50,
            "public_repos": 30,
            "public_gists": 5,
        }
        orgs = [{"login": "org1"}]
        stars = [{"user": {"login": "alice"}}]
        forks_data = [{"owner": {"login": "bob"}}]

        mock_get.side_effect = [
            (repo_data, {}),   # 1. repo stats
            (user_data, {}),   # 2. user stats
            (orgs, {}),        # 3. orgs
            (stars, {}),       # 4. latest stargazer
            (forks_data, {}),  # 5. latest fork
            ({"count": 10, "uniques": 5}, {}),  # 6. traffic views
            ({"count": 3, "uniques": 2}, {}),  # 7. traffic clones
            ([], {}),  # 8. traffic referrers
        ]
        # Repos list now uses _paginate_rest
        mock_paginate_rest.return_value = []

        def graphql_side_effect(
            query: str, token: str, *, variables: dict[str, Any] | None = None
        ) -> dict[str, Any]:
            assert token == "tok"
            del variables
            if "viewer" in query and "contributionsCollection" in query:
                return {
                    "data": {
                        "viewer": {
                            "contributionsCollection": {
                                "contributionCalendar": {
                                    "totalContributions": 100,
                                    "weeks": [],
                                },
                                "totalCommitContributions": 80,
                                "totalPullRequestContributions": 10,
                                "totalIssueContributions": 5,
                                "totalRepositoryContributions": 3,
                                "totalPullRequestReviewContributions": 4,
                            }
                        }
                    }
                }
            if "pullRequests" in query:
                return {
                    "data": {
                        "user": {
                            "pullRequests": {
                                "nodes": [],
                                "pageInfo": {
                                    "hasNextPage": False,
                                    "endCursor": None,
                                },
                            }
                        }
                    }
                }
            if "issues(states: OPEN)" in query:
                return {
                    "data": {
                        "user": {
                            "open": {"totalCount": 2},
                            "closed": {"totalCount": 7},
                        }
                    }
                }
            raise AssertionError(f"Unexpected GraphQL query: {query}")

        mock_graphql.side_effect = graphql_side_effect

        result = collect("owner", "repo", "tok")

        expected_keys = {
            "stars",
            "forks",
            "watchers",
            "network_count",
            "open_issues_count",
            "followers",
            "following",
            "public_repos",
            "public_gists",
            "orgs_count",
            "latest_stargazer",
            "latest_fork_owner",
            "contributions_last_year",
            "total_commits",
            "total_prs",
            "total_issues",
            "total_repos_contributed",
            "pr_review_count",
            "contributions_calendar",
            "languages",
            "repos",
            "top_repos",
            "traffic_views_14d",
            "traffic_unique_visitors_14d",
            "traffic_clones_14d",
            "traffic_unique_cloners_14d",
            "traffic_top_referrers",
            "recent_merged_prs",
            "issue_stats",
            "commit_hour_distribution",
            "commit_hour_distribution_scope",
            "commit_hour_distribution_sample_size",
            "releases",
            "releases_scope",
            "releases_repo_count",
        }
        assert expected_keys.issubset(set(result.keys())), (
            f"Missing keys: {expected_keys - set(result.keys())}"
        )
        assert result["repos"] == []
        assert result["issue_stats"] == {"open_count": 2, "closed_count": 7}
        assert result["commit_hour_distribution"] == {}
        assert result["commit_hour_distribution_scope"] == "recent_push_events_window"
        assert result["commit_hour_distribution_sample_size"] == 0
        assert result["releases"] == []
        assert result["releases_scope"] == "profile_repo_fallback"
        assert result["releases_repo_count"] == 1

    def test_collect_exposes_full_repo_inventory(
        self,
        mock_get: MagicMock,
        mock_paginate_rest: MagicMock,
    ) -> None:
        from scripts.fetch_metrics import _BASE, collect

        repo_data = {
            "stargazers_count": 0,
            "forks_count": 0,
            "watchers_count": 0,
            "network_count": 0,
            "open_issues_count": 0,
        }
        user_data = {
            "followers": 1,
            "following": 2,
            "public_repos": 2,
            "public_gists": 0,
        }
        repo_inventory = [
            _make_repo(
                "alpha",
                stars=5,
                language="Python",
                languages_url="http://lang/alpha",
            ),
            _make_repo(
                "beta",
                stars=2,
                language="Go",
                languages_url="http://lang/beta",
            ),
        ]

        mock_get.side_effect = [
            (repo_data, {}),
            (user_data, {}),
            ([], {}),
            ([], {}),
            ({"Python": 100}, {}),
            ({"Go": 50}, {}),
        ]

        def paginate_side_effect(
            url: str,
            token: str | None,
            *,
            accept: str | None = None,
            max_pages: int = 100,
        ) -> list[dict[str, Any]]:
            del token
            assert accept is None
            assert max_pages == 100
            if url == f"{_BASE}/users/owner/repos?per_page=100":
                return repo_inventory
            if url == f"{_BASE}/users/owner/events?per_page=100":
                return []
            if url == f"{_BASE}/repos/owner/alpha/releases?per_page=100":
                return []
            if url == f"{_BASE}/repos/owner/beta/releases?per_page=100":
                return []
            pytest.fail(f"Unexpected paginated URL: {url}")

        mock_paginate_rest.side_effect = paginate_side_effect

        result = collect("owner", "repo", None)

        assert result["repos"] == repo_inventory
        assert [repo["name"] for repo in result["top_repos"]] == ["alpha", "beta"]
        assert result["releases_scope"] == "account_owned_repos"
        assert result["releases_repo_count"] == 2
