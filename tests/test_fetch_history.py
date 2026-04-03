from __future__ import annotations

from scripts import fetch_history


def test_fetch_contributions_returns_daily_and_monthly(monkeypatch) -> None:
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


def test_collect_history_includes_contributions_daily(monkeypatch) -> None:
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
