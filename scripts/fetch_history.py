"""
fetch_history.py
~~~~~~~~~~~~~~~~
Historical GitHub data collector for animated SVG artwork.

Collects timestamped events (stars, forks, repos, contributions) via
the GitHub REST and GraphQL APIs and writes a consolidated JSON file
that the animated art generator consumes to produce 30-second CSS-
animated SVGs.

Usage::

    uv run python -m scripts.fetch_history --owner X --repo Y --output path.json

Requires ``GITHUB_TOKEN`` env var for GraphQL queries and higher rate
limits on REST endpoints.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import ssl
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ._github_http import _graphql, _headers
from .utils import get_logger

logger = get_logger(module=__name__)

_BASE = "https://api.github.com"


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def _get(url: str, token: str | None, *, accept: str | None = None) -> Any:
    """Perform an authenticated GET and return parsed JSON."""
    req = urllib.request.Request(url, headers=_headers(token, accept=accept))
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, context=ctx) as resp:
        return json.loads(resp.read().decode()), resp.headers


# ---------------------------------------------------------------------------
# Pagination
# ---------------------------------------------------------------------------

_LINK_NEXT_RE = re.compile(r'<([^>]+)>;\s*rel="next"')


def _paginate_rest(
    url: str,
    token: str | None,
    *,
    accept: str | None = None,
) -> list[Any]:
    """Follow ``Link: <...>; rel="next"`` headers to collect all pages."""
    results: list[Any] = []
    next_url: str | None = url
    while next_url:
        try:
            data, headers = _get(next_url, token, accept=accept)
        except Exception as exc:
            logger.warning("Pagination request failed ({}): {}", next_url, exc)
            break
        if isinstance(data, list):
            results.extend(data)
        else:
            logger.warning("Expected list from paginated endpoint, got {}", type(data).__name__)
            break
        link_header = headers.get("Link", "")
        match = _LINK_NEXT_RE.search(link_header)
        next_url = match.group(1) if match else None
    return results


# ---------------------------------------------------------------------------
# Data collectors
# ---------------------------------------------------------------------------

def _fetch_account_created(owner: str, token: str) -> str | None:
    """Return ``user.createdAt`` via GraphQL."""
    query = '{ user(login: "%s") { createdAt } }' % owner
    try:
        resp = _graphql(query, token)
        errors = resp.get("errors")
        if errors:
            logger.warning("GraphQL errors fetching account creation: {}", errors)
            return None
        return (resp.get("data") or {}).get("user", {}).get("createdAt")
    except Exception as exc:
        logger.warning("Failed to fetch account creation date: {}", exc)
        return None


def _fetch_star_timeline(
    owner: str,
    repo: str,
    token: str | None,
) -> list[dict[str, str]]:
    """Paginate stargazers with timestamps (REST, star+json accept header)."""
    url = f"{_BASE}/repos/{owner}/{repo}/stargazers?per_page=100"
    logger.info("Fetching star timeline for {}/{}", owner, repo)
    try:
        raw = _paginate_rest(url, token, accept="application/vnd.github.v3.star+json")
    except Exception as exc:
        logger.warning("Star timeline collection failed: {}", exc)
        return []
    stars: list[dict[str, str]] = []
    for entry in raw:
        starred_at = entry.get("starred_at")
        user_login = (entry.get("user") or {}).get("login", "")
        if starred_at:
            stars.append({"date": starred_at, "user": user_login})
    stars.sort(key=lambda s: s["date"])
    return stars


def _fetch_fork_timeline(
    owner: str,
    repo: str,
    token: str | None,
) -> list[dict[str, str]]:
    """Paginate forks sorted by oldest first (REST)."""
    url = f"{_BASE}/repos/{owner}/{repo}/forks?sort=oldest&per_page=100"
    logger.info("Fetching fork timeline for {}/{}", owner, repo)
    try:
        raw = _paginate_rest(url, token)
    except Exception as exc:
        logger.warning("Fork timeline collection failed: {}", exc)
        return []
    forks: list[dict[str, str]] = []
    for entry in raw:
        created_at = entry.get("created_at")
        user_login = (entry.get("owner") or {}).get("login", "")
        if created_at:
            forks.append({"date": created_at, "user": user_login})
    forks.sort(key=lambda f: f["date"])
    return forks


def _fetch_repo_timeline(
    owner: str,
    token: str | None,
) -> list[dict[str, str]]:
    """Paginate user repos sorted by creation date ascending (REST)."""
    url = f"{_BASE}/users/{owner}/repos?type=owner&sort=created&direction=asc&per_page=100"
    logger.info("Fetching repo timeline for {}", owner)
    try:
        raw = _paginate_rest(url, token)
    except Exception as exc:
        logger.warning("Repo timeline collection failed: {}", exc)
        return []
    repos: list[dict[str, str]] = []
    for entry in raw:
        created_at = entry.get("created_at")
        name = entry.get("name", "")
        if created_at:
            repos.append({"date": created_at, "name": name})
    repos.sort(key=lambda r: r["date"])
    return repos


def _fetch_contributions_monthly(
    owner: str,
    token: str,
    account_created: str | None,
) -> dict[str, int]:
    """Aggregate daily contribution counts into monthly totals via GraphQL.

    GitHub enforces 1-year windows on ``contributionsCollection``, so we
    loop year by year from the account creation year to the current year.
    """
    now = datetime.now(tz=timezone.utc)
    current_year = now.year

    if account_created:
        try:
            start_year = int(account_created[:4])
        except (ValueError, IndexError):
            start_year = current_year
    else:
        start_year = current_year

    monthly: dict[str, int] = defaultdict(int)
    for year in range(start_year, current_year + 1):
        from_dt = f"{year}-01-01T00:00:00Z"
        to_dt = f"{year}-12-31T23:59:59Z"
        query = """
        {
          user(login: "%s") {
            contributionsCollection(from: "%s", to: "%s") {
              contributionCalendar {
                weeks {
                  contributionDays {
                    date
                    contributionCount
                  }
                }
              }
            }
          }
        }
        """ % (owner, from_dt, to_dt)
        try:
            resp = _graphql(query, token)
            errors = resp.get("errors")
            if errors:
                logger.warning("GraphQL errors for contributions year {}: {}", year, errors)
                continue
            calendar = (
                (resp.get("data") or {})
                .get("user", {})
                .get("contributionsCollection", {})
                .get("contributionCalendar", {})
            )
            for week in calendar.get("weeks", []):
                for day in week.get("contributionDays", []):
                    date_str = day.get("date", "")
                    count = day.get("contributionCount", 0)
                    if date_str and count:
                        month_key = date_str[:7]  # "YYYY-MM"
                        monthly[month_key] += count
        except Exception as exc:
            logger.warning("Contributions query failed for year {}: {}", year, exc)
            continue

    return dict(sorted(monthly.items()))


def _fetch_current_metrics(
    owner: str,
    repo: str,
    token: str | None,
) -> dict[str, Any]:
    """Delegate to ``scripts.fetch_metrics.collect`` for live metrics."""
    try:
        from .fetch_metrics import collect as collect_current_metrics

        return collect_current_metrics(owner, repo, token)
    except Exception as exc:
        logger.warning("Failed to collect current metrics: {}", exc)
        return {}


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

def collect_history(
    owner: str,
    repo: str,
    token: str | None = None,
) -> dict[str, Any]:
    """Collect all historical data and return the consolidated dict."""
    result: dict[str, Any] = {}

    # 1. Account creation date (GraphQL)
    if token:
        account_created = _fetch_account_created(owner, token)
    else:
        logger.info("No GITHUB_TOKEN -- skipping account creation date (requires GraphQL)")
        account_created = None
    result["account_created"] = account_created

    # 2. Star timeline (REST)
    result["stars"] = _fetch_star_timeline(owner, repo, token)

    # 3. Fork timeline (REST)
    result["forks"] = _fetch_fork_timeline(owner, repo, token)

    # 4. Repo timeline (REST)
    result["repos"] = _fetch_repo_timeline(owner, token)

    # 5. Contribution calendar (GraphQL, year-by-year)
    if token:
        result["contributions_monthly"] = _fetch_contributions_monthly(
            owner, token, account_created,
        )
    else:
        logger.info("No GITHUB_TOKEN -- skipping contribution calendar (requires GraphQL)")
        result["contributions_monthly"] = {}

    # 6. Current metrics snapshot
    result["current_metrics"] = _fetch_current_metrics(owner, repo, token)

    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    """CLI entry-point: parse args, collect history, write JSON."""
    parser = argparse.ArgumentParser(
        description="Collect historical GitHub data for animated art",
    )
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
            "GITHUB_TOKEN not set -- requests will be unauthenticated "
            "(lower rate limits, no GraphQL)"
        )

    data = collect_history(args.owner, args.repo, token)

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=2, default=str) + "\n", encoding="utf-8")
    logger.info("History written to {}", out)


if __name__ == "__main__":
    main()
