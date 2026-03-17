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
import ssl
import urllib.request
from pathlib import Path
from typing import Any

from ._github_http import _graphql, _headers
from .utils import get_logger

logger = get_logger(module=__name__)

_BASE = "https://api.github.com"


def _get(url: str, token: str | None, *, accept: str | None = None) -> Any:
    """Perform an authenticated GET and return parsed JSON."""
    req = urllib.request.Request(url, headers=_headers(token, accept=accept))
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, context=ctx) as resp:
        return json.loads(resp.read().decode())


def collect(owner: str, repo: str, token: str | None = None) -> dict[str, Any]:
    """Collect GitHub metrics for *owner*/*repo* and return a flat dict."""
    metrics: dict[str, Any] = {}

    # -- REST: repo stats ------------------------------------------------
    logger.info("Fetching repo stats for {}/{}", owner, repo)
    try:
        repo_data = _get(f"{_BASE}/repos/{owner}/{repo}", token)
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
        user_data = _get(f"{_BASE}/users/{owner}", token)
        metrics["followers"] = user_data.get("followers", 0)
        metrics["following"] = user_data.get("following", 0)
        metrics["public_repos"] = user_data.get("public_repos", 0)
        metrics["public_gists"] = user_data.get("public_gists", 0)
    except Exception as exc:
        logger.warning("Failed to fetch user stats: {}", exc)

    # -- REST: orgs count ------------------------------------------------
    try:
        orgs = _get(f"{_BASE}/users/{owner}/orgs", token)
        metrics["orgs_count"] = len(orgs) if isinstance(orgs, list) else 0
    except Exception as exc:
        logger.warning("Failed to fetch orgs: {}", exc)
        metrics["orgs_count"] = 0

    # -- REST: latest stargazer ------------------------------------------
    try:
        star_count = metrics.get("stars", 0)
        if star_count > 0:
            stars = _get(
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
        forks = _get(
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
    if token:
        logger.info("Fetching contribution stats via GraphQL")
        query = """
        {
          viewer {
            contributionsCollection {
              contributionCalendar {
                totalContributions
              }
              totalCommitContributions
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
            contrib = (
                raw.get("viewer", {})
                .get("contributionsCollection", {})
            )
            metrics["contributions_last_year"] = (
                contrib.get("contributionCalendar", {}).get("totalContributions", 0)
            )
            metrics["total_commits"] = contrib.get("totalCommitContributions", 0)
        except Exception as exc:
            logger.warning("GraphQL query failed: {}", exc)
            metrics["contributions_last_year"] = None
            metrics["total_commits"] = None
    else:
        logger.info("No GITHUB_TOKEN — skipping GraphQL contribution stats")
        metrics["contributions_last_year"] = None
        metrics["total_commits"] = None

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
