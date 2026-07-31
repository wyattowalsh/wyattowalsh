"""Tests for scripts.fetch_history — historical GitHub data collection."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from scripts import fetch_history


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _freeze_now(monkeypatch: pytest.MonkeyPatch, year: int = 2025) -> None:
    """Pin datetime.now so year-loop collectors stay deterministic."""

    class _FrozenDateTime(datetime):
        @classmethod
        def now(cls, tz: Any = None) -> datetime:
            return datetime(year, 6, 15, 12, 0, 0, tzinfo=tz or UTC)

    monkeypatch.setattr(fetch_history, "datetime", _FrozenDateTime)


# ---------------------------------------------------------------------------
# compute_star_velocity
# ---------------------------------------------------------------------------


class TestComputeStarVelocity:
    def test_empty_timeline(self) -> None:
        assert fetch_history.compute_star_velocity([]) == {
            "recent_rate": 0.0,
            "peak_rate": 0.0,
            "trend": "stable",
        }

    def test_entries_without_valid_dates(self) -> None:
        assert fetch_history.compute_star_velocity([{"date": ""}, {"user": "x"}]) == {
            "recent_rate": 0.0,
            "peak_rate": 0.0,
            "trend": "stable",
        }

    def test_rising_trend(self) -> None:
        stars = [
            {"date": "2024-01-01T00:00:00Z"},
            {"date": "2024-02-01T00:00:00Z"},
            {"date": "2024-03-01T00:00:00Z"},
            {"date": "2024-04-01T00:00:00Z"},
            {"date": "2024-04-15T00:00:00Z"},
            {"date": "2024-05-01T00:00:00Z"},
            {"date": "2024-05-15T00:00:00Z"},
            {"date": "2024-06-01T00:00:00Z"},
            {"date": "2024-06-10T00:00:00Z"},
            {"date": "2024-06-20T00:00:00Z"},
        ]
        result = fetch_history.compute_star_velocity(stars)
        assert result["peak_rate"] >= 1
        assert result["recent_rate"] > 0
        assert result["trend"] == "rising"

    def test_falling_trend(self) -> None:
        stars = (
            [{"date": f"2024-01-{d:02d}T00:00:00Z"} for d in range(1, 4)]
            + [{"date": f"2024-02-{d:02d}T00:00:00Z"} for d in range(1, 4)]
            + [{"date": f"2024-03-{d:02d}T00:00:00Z"} for d in range(1, 4)]
            + [{"date": "2024-04-01T00:00:00Z"}]
            + [{"date": "2024-05-01T00:00:00Z"}]
            + [{"date": "2024-06-01T00:00:00Z"}]
        )
        result = fetch_history.compute_star_velocity(stars)
        assert result["trend"] == "falling"

    def test_stable_when_fewer_than_six_months(self) -> None:
        stars = [
            {"date": "2024-01-01T00:00:00Z"},
            {"date": "2024-02-01T00:00:00Z"},
            {"date": "2024-03-01T00:00:00Z"},
        ]
        result = fetch_history.compute_star_velocity(stars)
        assert result["trend"] == "stable"
        assert result["peak_rate"] == 1
        assert result["recent_rate"] == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# compute_contribution_streaks
# ---------------------------------------------------------------------------


class TestComputeContributionStreaks:
    def test_empty(self) -> None:
        assert fetch_history.compute_contribution_streaks({}) == {
            "longest_streak_months": 0,
            "current_streak_months": 0,
            "streak_active": False,
        }

    def test_active_streak(self) -> None:
        monthly = {"2024-01": 5, "2024-02": 3, "2024-03": 0, "2024-04": 2, "2024-05": 4}
        result = fetch_history.compute_contribution_streaks(monthly)
        assert result["longest_streak_months"] == 2
        assert result["current_streak_months"] == 2
        assert result["streak_active"] is True

    def test_inactive_streak(self) -> None:
        monthly = {"2024-01": 5, "2024-02": 3, "2024-03": 0}
        result = fetch_history.compute_contribution_streaks(monthly)
        assert result["longest_streak_months"] == 2
        assert result["current_streak_months"] == 0
        assert result["streak_active"] is False


# ---------------------------------------------------------------------------
# GraphQL / REST collectors (mocked network)
# ---------------------------------------------------------------------------


class TestFetchAccountCreated:
    def test_returns_created_at(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            fetch_history,
            "_graphql",
            lambda *_a, **_k: {"data": {"user": {"createdAt": "2020-05-01T00:00:00Z"}}},
        )
        assert fetch_history._fetch_account_created("owner", "tok") == "2020-05-01T00:00:00Z"

    def test_returns_none_on_errors(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            fetch_history,
            "_graphql",
            lambda *_a, **_k: {"errors": [{"message": "boom"}]},
        )
        assert fetch_history._fetch_account_created("owner", "tok") is None

    def test_returns_none_on_exception(self, monkeypatch: pytest.MonkeyPatch) -> None:
        def boom(*_a: object, **_k: object) -> dict:
            raise RuntimeError("network down")

        monkeypatch.setattr(fetch_history, "_graphql", boom)
        assert fetch_history._fetch_account_created("owner", "tok") is None


class TestFetchStarTimeline:
    def test_parses_and_sorts(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            fetch_history,
            "_paginate_rest",
            lambda *_a, **_k: [
                {"starred_at": "2024-02-01T00:00:00Z", "user": {"login": "b"}},
                {"starred_at": "2024-01-01T00:00:00Z", "user": {"login": "a"}},
                {"user": {"login": "no-date"}},
            ],
        )
        stars = fetch_history._fetch_star_timeline("o", "r", "tok")
        assert stars == [
            {"date": "2024-01-01T00:00:00Z", "user": "a"},
            {"date": "2024-02-01T00:00:00Z", "user": "b"},
        ]

    def test_returns_empty_on_failure(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            fetch_history,
            "_paginate_rest",
            lambda *_a, **_k: (_ for _ in ()).throw(RuntimeError("fail")),
        )
        assert fetch_history._fetch_star_timeline("o", "r", None) == []


class TestFetchForkTimeline:
    def test_parses_and_sorts(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            fetch_history,
            "_paginate_rest",
            lambda *_a, **_k: [
                {"created_at": "2024-03-01T00:00:00Z", "owner": {"login": "c"}},
                {"created_at": "2024-01-01T00:00:00Z", "owner": {"login": "a"}},
                {"owner": {"login": "no-date"}},
            ],
        )
        forks = fetch_history._fetch_fork_timeline("o", "r", "tok")
        assert forks == [
            {"date": "2024-01-01T00:00:00Z", "user": "a"},
            {"date": "2024-03-01T00:00:00Z", "user": "c"},
        ]

    def test_returns_empty_on_failure(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            fetch_history,
            "_paginate_rest",
            lambda *_a, **_k: (_ for _ in ()).throw(OSError("fail")),
        )
        assert fetch_history._fetch_fork_timeline("o", "r", None) == []


class TestFetchRepoTimeline:
    def test_parses_and_sorts(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            fetch_history,
            "_paginate_rest",
            lambda *_a, **_k: [
                {"created_at": "2024-06-01T00:00:00Z", "name": "later"},
                {"created_at": "2023-01-01T00:00:00Z", "name": "earlier"},
                {"name": "no-date"},
            ],
        )
        repos = fetch_history._fetch_repo_timeline("owner", "tok")
        assert repos == [
            {"date": "2023-01-01T00:00:00Z", "name": "earlier"},
            {"date": "2024-06-01T00:00:00Z", "name": "later"},
        ]

    def test_returns_empty_on_failure(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            fetch_history,
            "_paginate_rest",
            lambda *_a, **_k: (_ for _ in ()).throw(TimeoutError("fail")),
        )
        assert fetch_history._fetch_repo_timeline("owner", None) == []


class TestFetchContributions:
    def test_returns_daily_and_monthly(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _freeze_now(monkeypatch, year=2025)
        responses = [
            {
                "data": {
                    "user": {
                        "contributionsCollection": {
                            "contributionCalendar": {
                                "weeks": [
                                    {
                                        "contributionDays": [
                                            {"date": "2024-01-01", "contributionCount": 2},
                                            {"date": "2024-01-02", "contributionCount": 0},
                                            {"date": "2024-02-01", "contributionCount": 3},
                                        ]
                                    }
                                ]
                            }
                        }
                    }
                }
            },
            {
                "data": {
                    "user": {
                        "contributionsCollection": {
                            "contributionCalendar": {
                                "weeks": [
                                    {
                                        "contributionDays": [
                                            {"date": "2025-01-10", "contributionCount": 4},
                                        ]
                                    }
                                ]
                            }
                        }
                    }
                }
            },
        ]

        def fake_graphql(query: str, token: str, variables: dict) -> dict:
            return responses.pop(0)

        monkeypatch.setattr(fetch_history, "_graphql", fake_graphql)

        daily, monthly = fetch_history._fetch_contributions(
            owner="wyattowalsh",
            token="tok",
            account_created="2024-01-01T00:00:00Z",
        )

        assert daily == {
            "2024-01-01": 2,
            "2024-01-02": 0,
            "2024-02-01": 3,
            "2025-01-10": 4,
        }
        assert monthly == {
            "2024-01": 2,
            "2024-02": 3,
            "2025-01": 4,
        }

    def test_invalid_account_created_falls_back_to_current_year(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _freeze_now(monkeypatch, year=2025)
        calls: list[dict] = []

        def fake_graphql(query: str, token: str, variables: dict) -> dict:
            calls.append(variables)
            return {"data": {"user": {"contributionsCollection": {"contributionCalendar": {"weeks": []}}}}}

        monkeypatch.setattr(fetch_history, "_graphql", fake_graphql)
        daily, monthly = fetch_history._fetch_contributions("o", "tok", "not-a-year")
        assert daily == {}
        assert monthly == {}
        assert len(calls) == 1
        assert calls[0]["from"].startswith("2025-")

    def test_skips_year_on_graphql_errors(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _freeze_now(monkeypatch, year=2024)
        monkeypatch.setattr(
            fetch_history,
            "_graphql",
            lambda *_a, **_k: {"errors": [{"message": "rate limited"}]},
        )
        daily, monthly = fetch_history._fetch_contributions(
            "o", "tok", "2024-01-01T00:00:00Z"
        )
        assert daily == {}
        assert monthly == {}

    def test_skips_year_on_exception(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _freeze_now(monkeypatch, year=2024)

        def boom(*_a: object, **_k: object) -> dict:
            raise ConnectionError("down")

        monkeypatch.setattr(fetch_history, "_graphql", boom)
        daily, monthly = fetch_history._fetch_contributions(
            "o", "tok", "2024-01-01T00:00:00Z"
        )
        assert daily == {}
        assert monthly == {}


class TestFetchCurrentMetrics:
    def test_delegates_to_collect(self) -> None:
        fake = MagicMock(return_value={"stars": 10})
        with patch("scripts.fetch_metrics.collect", fake):
            result = fetch_history._fetch_current_metrics("o", "r", "tok")
        assert result == {"stars": 10}
        fake.assert_called_once_with("o", "r", "tok")

    def test_returns_empty_on_failure(self) -> None:
        with patch(
            "scripts.fetch_metrics.collect",
            side_effect=RuntimeError("boom"),
        ):
            assert fetch_history._fetch_current_metrics("o", "r", "tok") == {}


# ---------------------------------------------------------------------------
# collect_history orchestrator
# ---------------------------------------------------------------------------


class TestCollectHistory:
    def test_includes_contributions_daily(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            fetch_history,
            "_fetch_account_created",
            lambda owner, token: "2024-01-01T00:00:00Z",
        )
        monkeypatch.setattr(
            fetch_history,
            "_fetch_star_timeline",
            lambda owner, repo, token: [{"date": "2024-01-01T00:00:00Z", "user": "a"}],
        )
        monkeypatch.setattr(fetch_history, "_fetch_fork_timeline", lambda owner, repo, token: [])
        monkeypatch.setattr(
            fetch_history,
            "_fetch_repo_timeline",
            lambda owner, token: [{"date": "2024-01-01T00:00:00Z", "name": "repo"}],
        )
        monkeypatch.setattr(
            fetch_history,
            "_fetch_contributions",
            lambda owner, token, account_created: (
                {"2024-01-01": 2, "2024-01-02": 0},
                {"2024-01": 2},
            ),
        )
        monkeypatch.setattr(fetch_history, "_fetch_current_metrics", lambda owner, repo, token: {})

        result = fetch_history.collect_history("wyattowalsh", "wyattowalsh", token="tok")

        assert result["contributions_daily"] == {"2024-01-01": 2, "2024-01-02": 0}
        assert result["contributions_monthly"] == {"2024-01": 2}
        assert result["account_created"] == "2024-01-01T00:00:00Z"
        assert "star_velocity" in result
        assert "contribution_streaks" in result

    def test_skips_graphql_without_token(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            fetch_history,
            "_fetch_star_timeline",
            lambda owner, repo, token: [],
        )
        monkeypatch.setattr(fetch_history, "_fetch_fork_timeline", lambda owner, repo, token: [])
        monkeypatch.setattr(fetch_history, "_fetch_repo_timeline", lambda owner, token: [])
        monkeypatch.setattr(
            fetch_history,
            "_fetch_current_metrics",
            lambda owner, repo, token: {"stars": 1},
        )

        def should_not_call(*_a: object, **_k: object) -> None:
            raise AssertionError("GraphQL collectors must not run without token")

        monkeypatch.setattr(fetch_history, "_fetch_account_created", should_not_call)
        monkeypatch.setattr(fetch_history, "_fetch_contributions", should_not_call)

        result = fetch_history.collect_history("owner", "repo", token=None)
        assert result["account_created"] is None
        assert result["contributions_daily"] == {}
        assert result["contributions_monthly"] == {}
        assert result["current_metrics"] == {"stars": 1}


# ---------------------------------------------------------------------------
# CLI main (mocked FS + network)
# ---------------------------------------------------------------------------


class TestMain:
    def test_writes_json(self, tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
        out = tmp_path / "nested" / "history.json"
        payload = {
            "account_created": None,
            "stars": [],
            "forks": [],
            "repos": [],
            "contributions_daily": {},
            "contributions_monthly": {},
            "current_metrics": {},
            "star_velocity": {"recent_rate": 0.0, "peak_rate": 0.0, "trend": "stable"},
            "contribution_streaks": {
                "longest_streak_months": 0,
                "current_streak_months": 0,
                "streak_active": False,
            },
        }
        monkeypatch.setattr(
            fetch_history,
            "collect_history",
            lambda owner, repo, token: payload,
        )
        monkeypatch.setenv("GITHUB_TOKEN", "tok")
        monkeypatch.setattr(
            "sys.argv",
            ["fetch_history", "--owner", "o", "--repo", "r", "--output", str(out)],
        )

        fetch_history.main()

        assert out.exists()
        written = json.loads(out.read_text(encoding="utf-8"))
        assert written["stars"] == []
        assert written["star_velocity"]["trend"] == "stable"

    def test_warns_without_token(self, tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
        out = tmp_path / "history.json"
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        monkeypatch.setattr(
            fetch_history,
            "collect_history",
            lambda owner, repo, token: {
                "account_created": None,
                "stars": [],
                "forks": [],
                "repos": [],
                "contributions_daily": {},
                "contributions_monthly": {},
                "current_metrics": {},
                "star_velocity": {"recent_rate": 0.0, "peak_rate": 0.0, "trend": "stable"},
                "contribution_streaks": {
                    "longest_streak_months": 0,
                    "current_streak_months": 0,
                    "streak_active": False,
                },
            },
        )
        monkeypatch.setattr(
            "sys.argv",
            ["fetch_history", "--owner", "o", "--repo", "r", "--output", str(out)],
        )
        fetch_history.main()
        assert out.exists()
