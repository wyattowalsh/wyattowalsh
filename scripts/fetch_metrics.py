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
from datetime import datetime
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
                logger.warning(
                    "Failed to fetch languages for {}: {}",
                    futures[fut].get("name"),
                    exc,
                )
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

        referrers = _json(
            f"{_BASE}/repos/{owner}/{repo}/traffic/popular/referrers",
            token,
        )
        result["traffic_top_referrers"] = [r["referrer"] for r in referrers]
    except Exception as exc:
        logger.warning("Failed to fetch traffic stats: {}", exc)

    return result


def _collect_recent_merged_prs(owner: str, token: str | None) -> list[dict[str, Any]]:
    """Fetch the account's merged PR history via paginated GraphQL."""
    if not token:
        return []
    query = """
    query($login: String!, $cursor: String) {
      user(login: $login) {
        pullRequests(
          first: 100
          after: $cursor
          states: MERGED
          orderBy: {field: UPDATED_AT, direction: DESC}
        ) {
          nodes {
            mergedAt
            additions
            deletions
            repository {
              name
              nameWithOwner
            }
          }
          pageInfo {
            hasNextPage
            endCursor
          }
        }
      }
    }
    """
    try:
        merged_prs: list[dict[str, Any]] = []
        cursor: str | None = None
        while True:
            resp = _graphql(
                query,
                token,
                variables={"login": owner, "cursor": cursor},
            )
            errors = resp.get("errors")
            if errors:
                logger.warning("GraphQL errors fetching merged PRs: {}", errors)
                return []
            pull_requests = (
                ((resp.get("data") or {}).get("user") or {})
                .get("pullRequests", {})
            )
            nodes = pull_requests.get("nodes", [])
            for node in nodes:
                repo = node.get("repository") or {}
                repo_name = repo.get("name", "")
                merged_prs.append(
                    {
                        "merged_at": node.get("mergedAt"),
                        "additions": int(node.get("additions", 0) or 0),
                        "deletions": int(node.get("deletions", 0) or 0),
                        "repo_name": repo_name,
                        "repo_full_name": (
                            repo.get("nameWithOwner")
                            or (f"{owner}/{repo_name}" if repo_name else "")
                        ),
                    }
                )
            page_info = pull_requests.get("pageInfo", {})
            end_cursor = page_info.get("endCursor")
            if not page_info.get("hasNextPage") or not end_cursor:
                break
            cursor = str(end_cursor)
        merged_prs.sort(key=lambda entry: entry.get("merged_at") or "")
        return merged_prs
    except Exception as exc:
        logger.warning("Failed to fetch recent merged PRs: {}", exc)
        return []


def _collect_issue_stats(owner: str, token: str | None) -> dict[str, int]:
    """Fetch user's open/closed issue counts via GraphQL."""
    if not token:
        return {"open_count": 0, "closed_count": 0}
    query = """
    query($login: String!) {
      user(login: $login) {
        open: issues(states: OPEN) { totalCount }
        closed: issues(states: CLOSED) { totalCount }
      }
    }
    """
    try:
        resp = _graphql(query, token, variables={"login": owner})
        errors = resp.get("errors")
        if errors:
            logger.warning("GraphQL errors fetching issue stats: {}", errors)
            return {"open_count": 0, "closed_count": 0}
        user = (resp.get("data") or {}).get("user", {})
        return {
            "open_count": (user.get("open") or {}).get("totalCount", 0),
            "closed_count": (user.get("closed") or {}).get("totalCount", 0),
        }
    except Exception as exc:
        logger.warning("Failed to fetch issue stats: {}", exc)
        return {"open_count": 0, "closed_count": 0}


def _collect_commit_hour_distribution(
    owner: str, token: str | None
) -> tuple[dict[int, int], int]:
    """Bucket commit activity by hour from GitHub's visible push-event window.

    GitHub does not expose an all-time, account-wide commit timestamp history.
    This intentionally models a recent activity window using push-event
    timestamps weighted by each event's commit count rather than claiming to be
    a lifetime histogram.
    """
    try:
        data = _paginate_rest(f"{_BASE}/users/{owner}/events?per_page=100", token)
        if not isinstance(data, list):
            return {}, 0
        hours: dict[int, int] = {}
        sampled_commits = 0
        for event in data:
            if event.get("type") != "PushEvent":
                continue
            created = event.get("created_at", "")
            if not created:
                continue
            try:
                dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                continue
            payload = event.get("payload")
            payload_dict = payload if isinstance(payload, dict) else {}
            event_size = payload_dict.get("size")
            if isinstance(event_size, int) and event_size > 0:
                commit_count = event_size
            else:
                commit_count = len(payload_dict.get("commits") or []) or 1
            sampled_commits += commit_count
            hour = dt.hour
            hours[hour] = hours.get(hour, 0) + commit_count
        return dict(sorted(hours.items())), sampled_commits
    except Exception as exc:
        logger.warning("Failed to fetch commit hour distribution: {}", exc)
        return {}, 0


def _collect_releases(
    owner: str,
    repo: str,
    token: str | None,
    repos: list[dict[str, Any]] | None = None,
) -> tuple[list[dict[str, Any]], str, int]:
    """Fetch published releases across account-owned repos when available.

    Collaborator/member repos are excluded because their release history belongs
    to another account. If the owned-repo inventory is unavailable, fall back to
    the profile repo and surface that narrower scope in metadata.
    """
    owner_casefold = owner.casefold()
    repo_sources_by_full_name: dict[str, dict[str, Any]] = {}
    for repo_data in repos or []:
        repo_name = repo_data.get("name")
        if not repo_name:
            continue
        repo_owner = repo_data.get("owner")
        owner_login = (
            str(repo_owner.get("login")).casefold()
            if isinstance(repo_owner, dict) and repo_owner.get("login")
            else None
        )
        full_name = str(repo_data.get("full_name") or f"{owner}/{repo_name}")
        full_name_casefold = full_name.casefold()
        if owner_login and owner_login != owner_casefold:
            continue
        if (
            owner_login is None
            and "/" in full_name_casefold
            and not full_name_casefold.startswith(f"{owner_casefold}/")
        ):
            continue
        repo_sources_by_full_name[full_name] = repo_data

    repo_sources = list(repo_sources_by_full_name.values())
    scope = "account_owned_repos" if repo_sources else "profile_repo_fallback"
    if not repo_sources:
        repo_sources = [{"name": repo, "full_name": f"{owner}/{repo}"}]

    def _fetch_repo_releases(
        repo_data: dict[str, Any]
    ) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        repo_name = str(repo_data.get("name") or repo)
        full_name = str(repo_data.get("full_name") or f"{owner}/{repo_name}")
        data = _paginate_rest(
            f"{_BASE}/repos/{full_name}/releases?per_page=100",
            token,
        )
        return repo_data, data if isinstance(data, list) else []

    releases: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=min(8, len(repo_sources))) as pool:
        futures = {
            pool.submit(_fetch_repo_releases, entry): entry for entry in repo_sources
        }
        for fut in as_completed(futures):
            repo_data = futures[fut]
            repo_name = str(repo_data.get("name") or repo)
            full_name = str(repo_data.get("full_name") or f"{owner}/{repo_name}")
            try:
                _, raw_releases = fut.result()
            except Exception as exc:
                logger.warning("Failed to fetch releases for {}: {}", full_name, exc)
                continue
            for release in raw_releases:
                published_at = release.get("published_at")
                if not published_at:
                    continue
                releases.append(
                    {
                        "tag_name": release.get("tag_name", ""),
                        "published_at": published_at,
                        "date": published_at,
                        "name": release.get("name", ""),
                        "repo_name": repo_name,
                        "repo_full_name": full_name,
                    }
                )
    # Preserve the legacy "most recent releases first" ordering even though the
    # release pool now spans the account's owned repositories.
    releases.sort(
        key=lambda entry: (
            entry.get("published_at") or "",
            entry.get("repo_full_name") or "",
            entry.get("tag_name") or "",
            entry.get("name") or "",
        ),
        reverse=True,
    )
    return releases, scope, len(repo_sources)


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
               "total_issues", "total_repos_contributed", "pr_review_count"):
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
              totalPullRequestReviewContributions
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
            metrics["total_repos_contributed"] = contrib_coll.get(
                "totalRepositoryContributions"
            )
            metrics["pr_review_count"] = contrib_coll.get(
                "totalPullRequestReviewContributions",
                0,
            )
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
    metrics["repos"] = all_repos
    metrics["top_repos"] = _collect_top_repos(all_repos)
    metrics.update(_collect_traffic(owner, repo, token))

    # -- New collectors: PRs, issues, commit hours, releases ----------------
    try:
        metrics["recent_merged_prs"] = _collect_recent_merged_prs(owner, token)
    except Exception as exc:
        logger.warning("Failed to collect recent merged PRs: {}", exc)
        metrics["recent_merged_prs"] = []

    try:
        metrics["issue_stats"] = _collect_issue_stats(owner, token)
    except Exception as exc:
        logger.warning("Failed to collect issue stats: {}", exc)
        metrics["issue_stats"] = {"open_count": 0, "closed_count": 0}

    metrics["commit_hour_distribution_scope"] = "recent_push_events_window"
    try:
        (
            metrics["commit_hour_distribution"],
            metrics["commit_hour_distribution_sample_size"],
        ) = _collect_commit_hour_distribution(owner, token)
    except Exception as exc:
        logger.warning("Failed to collect commit hour distribution: {}", exc)
        metrics["commit_hour_distribution"] = {}
        metrics["commit_hour_distribution_sample_size"] = 0

    try:
        (
            metrics["releases"],
            metrics["releases_scope"],
            metrics["releases_repo_count"],
        ) = _collect_releases(owner, repo, token, repos=all_repos or None)
    except Exception as exc:
        logger.warning("Failed to collect releases: {}", exc)
        metrics["releases"] = []
        metrics["releases_scope"] = "unavailable"
        metrics["releases_repo_count"] = 0

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
