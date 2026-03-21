"""
fetch_metrics.py
~~~~~~~~~~~~~~~~
GitHub API metrics collector that outputs a flat JSON dict.

Collects repository and user statistics via the GitHub REST and GraphQL APIs.
Uses ``GITHUB_TOKEN`` env var for authentication (optional; unauthenticated
requests are subject to stricter rate limits).
"""

from __future__ import annotations

import argparse
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from ._github_http import _BASE, _get, _graphql, _paginate_rest
from .utils import get_logger

logger = get_logger(module=__name__)


def _json(url: str, token: str | None, **kw: Any) -> Any:
    """GET and return just the parsed JSON (discard headers)."""
    data, _ = _get(url, token, **kw)
    return data


def _collect_languages(repos: list[dict], token: str | None) -> dict[str, int]:
    """Aggregate language bytes across all non-fork repos (parallel fetches)."""
    non_forks = [r for r in repos if not r.get("fork")]
    if not non_forks:
        return {}
    totals: dict[str, int] = {}

    def _fetch_lang(repo: dict) -> dict[str, int]:
        data, _ = _get(repo["languages_url"], token)
        return data

    with ThreadPoolExecutor(max_workers=min(16, len(non_forks))) as pool:
        futures = {pool.submit(_fetch_lang, r): r for r in non_forks}
        for fut in as_completed(futures):
            try:
                for lang, count in fut.result().items():
                    totals[lang] = totals.get(lang, 0) + count
            except Exception as exc:
                logger.warning("Failed to fetch languages for {}: {}", futures[fut].get("name"), exc)
    return totals


def _collect_traffic(owner: str, repo: str, token: str | None) -> dict[str, Any]:
    """Collect traffic stats for *owner*/*repo*. Returns ``{}`` without a token."""
    if token is None:
        return {}

    result: dict[str, Any] = {}
    try:
        views = _json(f"{_BASE}/repos/{owner}/{repo}/traffic/views", token)
        result["traffic_views_14d"] = views["count"]
        result["traffic_unique_visitors_14d"] = views["uniques"]

        clones = _json(f"{_BASE}/repos/{owner}/{repo}/traffic/clones", token)
        result["traffic_clones_14d"] = clones["count"]
        result["traffic_unique_cloners_14d"] = clones["uniques"]

        referrers = _json(f"{_BASE}/repos/{owner}/{repo}/traffic/popular/referrers", token)
        result["traffic_top_referrers"] = [r["referrer"] for r in referrers]
    except Exception as exc:
        logger.warning("Failed to fetch traffic stats: {}", exc)

    return result


def _collect_top_repos(repos: list[dict], limit: int | None = None) -> list[dict]:
    """Return the top repos sorted by stars descending."""
    non_forks = [r for r in repos if not r.get("fork")]
    non_forks.sort(key=lambda r: r.get("stargazers_count", 0), reverse=True)
    if limit is not None:
        non_forks = non_forks[:limit]
    return [
        {
            "name": r["name"],
            "full_name": r["full_name"],
            "stars": r["stargazers_count"],
            "forks": r["forks_count"],
            "language": r.get("language"),
            "description": r.get("description"),
            "topics": r.get("topics", []),
            "updated_at": r.get("updated_at"),
        }
        for r in non_forks
    ]


def collect(owner: str, repo: str, token: str | None = None) -> dict[str, Any]:
    """Collect GitHub metrics for *owner*/*repo* and return a flat dict."""
    metrics: dict[str, Any] = {}

    # -- REST: repo stats ------------------------------------------------
    logger.info("Fetching repo stats for {}/{}", owner, repo)
    try:
        repo_data = _json(f"{_BASE}/repos/{owner}/{repo}", token)
        metrics["stars"] = repo_data.get("stargazers_count", 0)
        metrics["forks"] = repo_data.get("forks_count", 0)
        metrics["watchers"] = repo_data.get("watchers_count", 0)
        metrics["network_count"] = repo_data.get("network_count", 0)
        metrics["open_issues_count"] = repo_data.get("open_issues_count", 0)
    except Exception as exc:
        logger.warning("Failed to fetch repo stats: {}", exc)

    # -- REST: user stats ------------------------------------------------
    logger.info("Fetching user stats for {}", owner)
    try:
        user_data = _json(f"{_BASE}/users/{owner}", token)
        metrics["followers"] = user_data.get("followers", 0)
        metrics["following"] = user_data.get("following", 0)
        metrics["public_repos"] = user_data.get("public_repos", 0)
        metrics["public_gists"] = user_data.get("public_gists", 0)
    except Exception as exc:
        logger.warning("Failed to fetch user stats: {}", exc)

    # -- REST: orgs count ------------------------------------------------
    try:
        orgs = _json(f"{_BASE}/users/{owner}/orgs", token)
        metrics["orgs_count"] = len(orgs) if isinstance(orgs, list) else 0
    except Exception as exc:
        logger.warning("Failed to fetch orgs: {}", exc)
        metrics["orgs_count"] = 0

    # -- REST: latest stargazer ------------------------------------------
    try:
        star_count = metrics.get("stars", 0)
        if star_count > 0:
            stars = _json(
                f"{_BASE}/repos/{owner}/{repo}/stargazers?per_page=1&page={star_count}",
                token,
                accept="application/vnd.github.v3.star+json",
            )
        else:
            stars = []
        if stars and isinstance(stars, list) and len(stars) > 0:
            metrics["latest_stargazer"] = stars[0].get("user", {}).get("login")
        else:
            metrics["latest_stargazer"] = None
    except Exception as exc:
        logger.warning("Failed to fetch latest stargazer: {}", exc)
        metrics["latest_stargazer"] = None

    # -- REST: latest fork owner -----------------------------------------
    try:
        forks = _json(
            f"{_BASE}/repos/{owner}/{repo}/forks?sort=newest&per_page=1",
            token,
        )
        if forks and isinstance(forks, list) and len(forks) > 0:
            metrics["latest_fork_owner"] = forks[0].get("owner", {}).get("login")
        else:
            metrics["latest_fork_owner"] = None
    except Exception as exc:
        logger.warning("Failed to fetch latest fork: {}", exc)
        metrics["latest_fork_owner"] = None

    # -- GraphQL: contributions ------------------------------------------
    # Set GraphQL field defaults (overwritten on success)
    for _k in ("contributions_last_year", "total_commits", "total_prs",
               "total_issues", "total_repos_contributed"):
        metrics[_k] = None
    metrics["contributions_calendar"] = []

    if token:
        logger.info("Fetching contribution stats via GraphQL")
        query = """
        {
          viewer {
            contributionsCollection {
              contributionCalendar {
                totalContributions
                weeks {
                  contributionDays {
                    date
                    contributionCount
                    color
                  }
                }
              }
              totalCommitContributions
              totalPullRequestContributions
              totalIssueContributions
              totalRepositoryContributions
            }
          }
        }
        """
        try:
            gql_resp = _graphql(query, token)
            errors = gql_resp.get("errors")
            if errors:
                logger.warning("GraphQL returned errors: {e}", e=errors)
            raw = gql_resp.get("data") or {}
            contrib_coll = (
                raw.get("viewer", {})
                .get("contributionsCollection", {})
            )
            cal = contrib_coll.get("contributionCalendar", {})
            metrics["contributions_last_year"] = cal.get("totalContributions", 0)
            metrics["total_commits"] = contrib_coll.get("totalCommitContributions", 0)
            metrics["total_prs"] = contrib_coll.get("totalPullRequestContributions")
            metrics["total_issues"] = contrib_coll.get("totalIssueContributions")
            metrics["total_repos_contributed"] = contrib_coll.get("totalRepositoryContributions")
            metrics["contributions_calendar"] = [
                {
                    "date": d["date"],
                    "count": d["contributionCount"],
                    "color": d["color"],
                }
                for week in cal.get("weeks", [])
                for d in week.get("contributionDays", [])
            ]
        except Exception as exc:
            logger.warning("GraphQL query failed: {}", exc)
    else:
        logger.info("No GITHUB_TOKEN — skipping GraphQL contribution stats")

    # -- REST: languages, top repos, traffic -----------------------------
    try:
        all_repos = _paginate_rest(f"{_BASE}/users/{owner}/repos?per_page=100", token)
        if not isinstance(all_repos, list):
            all_repos = []
    except Exception as exc:
        logger.warning("Failed to fetch repos list: {}", exc)
        all_repos = []
    metrics["languages"] = _collect_languages(all_repos, token)
    metrics["top_repos"] = _collect_top_repos(all_repos)
    metrics.update(_collect_traffic(owner, repo, token))

    return metrics


def main() -> None:
    """CLI entry-point: parse args, collect metrics, write JSON."""
    parser = argparse.ArgumentParser(description="Collect GitHub metrics as JSON")
    parser.add_argument("--owner", required=True, help="GitHub user or org")
    parser.add_argument("--repo", required=True, help="Repository name")
    parser.add_argument(
        "--output",
        required=True,
        help="Path to write the JSON output",
    )
    args = parser.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        logger.warning(
            "GITHUB_TOKEN not set — requests will be unauthenticated "
            "(lower rate limits, no GraphQL)"
        )

    data = collect(args.owner, args.repo, token)

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=2, default=str) + "\n", encoding="utf-8")
    logger.info("Metrics written to {}", out)


if __name__ == "__main__":
    main()
