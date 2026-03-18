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
) -> dict[str, Any]:
    """Build a minimal repo dict matching GitHub REST shape."""
    return {
        "name": name,
        "full_name": f"owner/{name}",
        "fork": fork,
        "stargazers_count": stars,
        "forks_count": forks,
        "language": language,
        "languages_url": languages_url or f"https://api.github.com/repos/owner/{name}/languages",
        "description": f"Description of {name}",
        "topics": ["topic-a"],
        "updated_at": "2025-01-01T00:00:00Z",
    }


@pytest.fixture
def mock_get():
    """Patch _get in scripts.fetch_metrics."""
    with patch("scripts.fetch_metrics._get") as m:
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
            repos,                          # repos list
            {"Python": 100, "Go": 50},      # languages for repo a
            {"Python": 200, "Rust": 30},    # languages for repo b
        ]
        result = _collect_languages("owner", "tok")
        assert result == {"Python": 300, "Go": 50, "Rust": 30}

    def test_skips_forks(self, mock_get: MagicMock) -> None:
        from scripts.fetch_metrics import _collect_languages

        repos = [
            _make_repo("mine", languages_url="http://lang/mine"),
            _make_repo("forked", fork=True, languages_url="http://lang/forked"),
        ]
        mock_get.side_effect = [
            repos,
            {"Python": 100},
        ]
        result = _collect_languages("owner", "tok")
        assert result == {"Python": 100}
        # Should not have fetched languages for the fork (only 2 calls total)
        assert mock_get.call_count == 2

    def test_handles_language_fetch_error(self, mock_get: MagicMock) -> None:
        from scripts.fetch_metrics import _collect_languages

        repos = [_make_repo("a", languages_url="http://lang/a")]
        mock_get.side_effect = [
            repos,
            Exception("network error"),
        ]
        result = _collect_languages("owner", "tok")
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
            {"count": 100, "uniques": 42},          # views
            {"count": 20, "uniques": 5},             # clones
            [{"referrer": "google"}, {"referrer": "github"}],  # referrers
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
# _collect_top_repos
# ---------------------------------------------------------------------------

class TestCollectTopRepos:
    def test_filters_forks_and_respects_limit(self, mock_get: MagicMock) -> None:
        from scripts.fetch_metrics import _collect_top_repos

        repos = [
            _make_repo("star1", stars=100),
            _make_repo("forked", fork=True, stars=500),
            _make_repo("star2", stars=50),
            _make_repo("star3", stars=30),
        ]
        mock_get.return_value = repos
        result = _collect_top_repos("owner", "tok", limit=2)
        assert len(result) == 2
        assert result[0]["name"] == "star1"
        assert result[1]["name"] == "star2"
        # Forked repo should not appear
        assert all(r["name"] != "forked" for r in result)

    def test_returns_expected_fields(self, mock_get: MagicMock) -> None:
        from scripts.fetch_metrics import _collect_top_repos

        mock_get.return_value = [_make_repo("myrepo", stars=10, language="Python")]
        result = _collect_top_repos("owner", "tok")
        repo = result[0]
        for key in ("name", "full_name", "stars", "forks", "language", "description", "topics", "updated_at"):
            assert key in repo


# ---------------------------------------------------------------------------
# GraphQL expanded fields
# ---------------------------------------------------------------------------

class TestGraphQLExpanded:
    def test_parses_all_new_fields(self, mock_get: MagicMock, mock_graphql: MagicMock) -> None:
        from scripts.fetch_metrics import collect

        # Stub REST calls to return minimal data
        mock_get.return_value = []

        mock_graphql.return_value = {
            "data": {
                "viewer": {
                    "contributionsCollection": {
                        "contributionCalendar": {
                            "totalContributions": 1234,
                            "weeks": [
                                {
                                    "contributionDays": [
                                        {"date": "2025-03-01", "contributionCount": 5, "color": "#216e39"},
                                        {"date": "2025-03-02", "contributionCount": 3, "color": "#30a14e"},
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

    def test_no_token_sets_none_values(self, mock_get: MagicMock) -> None:
        from scripts.fetch_metrics import collect

        mock_get.return_value = []
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
    def test_collect_returns_all_expected_keys(self, mock_get: MagicMock, mock_graphql: MagicMock) -> None:
        from scripts.fetch_metrics import collect

        # Stub REST calls
        repo_data = {
            "stargazers_count": 10, "forks_count": 2, "watchers_count": 10,
            "network_count": 2, "open_issues_count": 1,
        }
        user_data = {
            "followers": 100, "following": 50, "public_repos": 30, "public_gists": 5,
        }
        orgs = [{"login": "org1"}]
        stars = [{"user": {"login": "alice"}}]
        forks_data = [{"owner": {"login": "bob"}}]

        mock_get.side_effect = [
            repo_data,   # repo stats
            user_data,   # user stats
            orgs,        # orgs
            stars,       # latest stargazer
            forks_data,  # latest fork
            [],          # languages repos
            [],          # top repos
            {"count": 10, "uniques": 5},   # traffic views
            {"count": 3, "uniques": 2},    # traffic clones
            [],          # referrers
        ]
        mock_graphql.return_value = {
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
                    }
                }
            }
        }

        result = collect("owner", "repo", "tok")

        expected_keys = {
            "stars", "forks", "watchers", "network_count", "open_issues_count",
            "followers", "following", "public_repos", "public_gists",
            "orgs_count", "latest_stargazer", "latest_fork_owner",
            "contributions_last_year", "total_commits", "total_prs",
            "total_issues", "total_repos_contributed", "contributions_calendar",
            "languages", "top_repos",
            "traffic_views_14d", "traffic_unique_visitors_14d",
            "traffic_clones_14d", "traffic_unique_cloners_14d",
        }
        assert expected_keys.issubset(set(result.keys())), (
            f"Missing keys: {expected_keys - set(result.keys())}"
        )
