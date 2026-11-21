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
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any
from urllib.error import HTTPError

from ._github_http import (
    _BASE,
    _are_expected_optional_graphql_errors,
    _get,
    _graphql,
    _paginate_rest,
)
from .utils import get_logger

logger = get_logger(module=__name__)


def _json(url: str, token: str | None, **kw: Any) -> Any:
    """GET and return just the parsed JSON (discard headers)."""
    data, _ = _get(url, token, **kw)
    return data


def _json_object(value: object) -> dict[str, Any] | None:
    """Copy a JSON object, or return ``None`` when the value is not one."""
    if not isinstance(value, dict):
        return None
    parsed: dict[str, Any] = {}
    for key, item in value.items():
        if not isinstance(key, str):
            return None
        parsed[key] = item
    return parsed


def _repo_languages_url(repo: dict[str, Any]) -> str:
    """Build languages URL on api.github.com (never trust API-provided hosts)."""
    full_name = str(repo.get("full_name") or "").strip()
    if "/" not in full_name:
        owner = str((repo.get("owner") or {}).get("login") or "").strip()
        name = str(repo.get("name") or "").strip()
        if not owner or not name:
            raise ValueError(f"Cannot build languages URL for repo: {repo!r}")
        full_name = f"{owner}/{name}"
    owner, _, name = full_name.partition("/")
    if not owner or not name or "/" in name:
        raise ValueError(f"Invalid repo full_name for languages URL: {full_name!r}")
    return f"{_BASE}/repos/{owner}/{name}/languages"


def _language_byte_totals(payload: object) -> dict[str, int]:
    """Parse a GitHub languages object into byte totals."""
    parsed = _json_object(payload)
    if parsed is None:
        raise TypeError("Language payload was not a JSON object")
    totals: dict[str, int] = {}
    for lang, count in parsed.items():
        if isinstance(count, bool) or not isinstance(count, int):
            raise TypeError("Language payload contained a non-integer count")
        if count < 0:
            raise ValueError("Language byte count must be nonnegative")
        totals[lang] = count
    return totals


def _collect_languages(
    repos: list[Any],
    token: str | None,
    failures: list[str] | None = None,
) -> dict[str, int]:
    """Aggregate language bytes across all non-fork repos (parallel fetches)."""
    non_fork_urls: list[str] = []
    seen_ids: set[int] = set()
    seen_urls: set[str] = set()
    for repo in repos:
        row = _json_object(repo)
        if row is None or not isinstance(row.get("fork"), bool):
            if failures is not None and "languages" not in failures:
                failures.append("languages")
            continue
        try:
            url = _repo_languages_url(row)
        except (ValueError, AttributeError):
            logger.warning("Invalid repository identity in language inventory")
            if failures is not None and "languages" not in failures:
                failures.append("languages")
            continue
        repo_id = row.get("id")
        folded_url = url.casefold()
        if folded_url in seen_urls or (type(repo_id) is int and repo_id in seen_ids):
            logger.warning("Discarding language totals for overlapping repo pages")
            if failures is not None and "languages" not in failures:
                failures.append("languages")
            return {}
        seen_urls.add(folded_url)
        if type(repo_id) is int:
            seen_ids.add(repo_id)
        if row["fork"] is False:
            non_fork_urls.append(url)
    if not non_fork_urls:
        return {}
    totals: dict[str, int] = {}
    failed_repos = 0

    def _fetch_lang(url: str) -> dict[str, int]:
        data, _ = _get(url, token)
        return _language_byte_totals(data)

    with ThreadPoolExecutor(max_workers=min(16, len(non_fork_urls))) as pool:
        futures = {pool.submit(_fetch_lang, url): url for url in non_fork_urls}
        for fut in as_completed(futures):
            try:
                for lang, count in fut.result().items():
                    totals[lang] = totals.get(lang, 0) + count
            except Exception as exc:
                logger.warning(
                    "Failed to fetch languages for {}: {}",
                    futures[fut],
                    exc,
                )
                failed_repos += 1
    if failed_repos:
        if failures is not None and "languages" not in failures:
            failures.append("languages")
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
        if isinstance(exc, HTTPError) and exc.code == 403:
            logger.info(
                "Optional traffic metrics unavailable for {}/{}: HTTP 403",
                owner,
                repo,
            )
        else:
            logger.warning("Failed to fetch traffic stats: {}", exc)

    return result


def _collect_latest_stargazer(
    owner: str,
    repo: str,
    star_count: int,
    token: str | None,
) -> str | None:
    """Return the latest visible stargazer, or ``None`` when unavailable."""
    if star_count <= 0:
        return None

    try:
        # GitHub allows up to 100 stargazers per page. Request the bounded
        # final page instead of using one result per page, which makes a
        # popular repository ask for an inaccessible page in the thousands.
        per_page = 100
        last_page = ((star_count - 1) // per_page) + 1
        stars = _json(
            f"{_BASE}/repos/{owner}/{repo}/stargazers"
            f"?per_page={per_page}&page={last_page}",
            token,
            accept="application/vnd.github.v3.star+json",
        )
        if isinstance(stars, list) and stars:
            last = _json_object(stars[-1])
            user = _json_object(last.get("user")) if last is not None else None
            if user is None:
                return None
            login = user.get("login")
            return login if isinstance(login, str) else None
    except Exception as exc:
        if isinstance(exc, HTTPError) and exc.code == 403:
            logger.info("Optional latest stargazer unavailable: HTTP 403")
        else:
            logger.warning("Failed to fetch latest stargazer: {}", exc)
    return None


def _collect_contribution_stats(owner: str, token: str | None) -> dict[str, Any]:
    """Collect public contribution fields for *owner*, not the token viewer.

    Habits hero chips (30d commits, active days, streak, reviews) read this
    calendar. Querying ``viewer`` hydrates the Actions app / PAT identity and
    ships zeros while REST ``/users/{owner}`` still shows public_repos.
    """
    result: dict[str, Any] = {
        "contributions_last_year": None,
        "total_commits": None,
        "total_prs": None,
        "total_issues": None,
        "total_repos_contributed": None,
        "pr_review_count": None,
        "contributions_calendar": [],
    }
    login = owner.strip()
    if token is None or token == "":
        logger.info("No GITHUB_TOKEN — skipping GraphQL contribution stats")
        return result
    if not login:
        logger.info("No owner login — skipping GraphQL contribution stats")
        return result

    logger.info("Fetching contribution stats via GraphQL for {}", login)
    query = """
    query($login: String!) {
      user(login: $login) {
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
        gql_resp = _graphql(query, token, variables={"login": login})
        errors = gql_resp.get("errors")
        if errors:
            if _are_expected_optional_graphql_errors(errors):
                logger.info("Optional GraphQL contribution fields unavailable")
            else:
                logger.warning("GraphQL contribution errors: {e}", e=errors)
            result["collection_failed"] = True
        raw = gql_resp.get("data") or {}
        user = raw.get("user") or {}
        contrib_coll = user.get("contributionsCollection") or {}
        if not contrib_coll:
            result["collection_failed"] = True
            return result
        cal = contrib_coll["contributionCalendar"]
        weeks = cal["weeks"]
        if not isinstance(weeks, list):
            raise TypeError("Contribution calendar weeks must be a list")
        total = cal["totalContributions"]
        if type(total) is not int or total < 0:
            raise ValueError("Invalid contribution calendar total")
        days: list[dict[str, Any]] = []
        seen_dates: set[date] = set()
        daily_total = 0
        for week in weeks:
            week_days = week["contributionDays"]
            if not isinstance(week_days, list):
                raise TypeError("Contribution days must be a list")
            for day in week_days:
                count = day["contributionCount"]
                if type(count) is not int or count < 0:
                    raise ValueError("Invalid contribution count")
                calendar_date = date.fromisoformat(day["date"])
                if calendar_date in seen_dates:
                    raise ValueError("Contribution calendar contains a duplicate day")
                seen_dates.add(calendar_date)
                daily_total += count
                days.append(
                    {"date": day["date"], "count": count, "color": day["color"]}
                )
        if daily_total != total:
            result["collection_failed"] = True
        result.update(
            {
                "contributions_last_year": total,
                "total_commits": contrib_coll.get("totalCommitContributions", 0),
                "total_prs": contrib_coll.get("totalPullRequestContributions"),
                "total_issues": contrib_coll.get("totalIssueContributions"),
                "total_repos_contributed": contrib_coll.get(
                    "totalRepositoryContributions"
                ),
                "pr_review_count": contrib_coll.get(
                    "totalPullRequestReviewContributions", 0
                ),
                "contributions_calendar": days,
            }
        )
    except Exception as exc:
        logger.warning("GraphQL contribution query failed: {}", exc)
        result["collection_failed"] = True
    return result


def _collect_recent_merged_prs(
    owner: str, token: str | None, *, public_profile: bool = False
) -> list[dict[str, Any]]:
    """Fetch the account's merged PR history via paginated GraphQL."""
    if token is None or token == "":
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
              visibility
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
        seen_cursors: set[str] = set()
        while True:
            resp = _graphql(
                query,
                token,
                variables={"login": owner, "cursor": cursor},
            )
            errors = resp.get("errors")
            if errors:
                if public_profile:
                    raise ValueError("GitHub merged PR query returned errors")
                logger.warning("GraphQL errors fetching merged PRs: {}", errors)
                return []
            pull_requests = ((resp.get("data") or {}).get("user") or {}).get(
                "pullRequests", {}
            )
            if public_profile and not isinstance(pull_requests.get("nodes"), list):
                raise ValueError("GitHub merged PR collection is missing nodes")
            nodes = pull_requests.get("nodes", [])
            for node in nodes:
                repo = node.get("repository") or {}
                if public_profile:
                    visibility = repo.get("visibility")
                    if visibility not in {"PRIVATE", "INTERNAL", "PUBLIC"}:
                        raise ValueError("Missing merged PR repository visibility")
                    if visibility != "PUBLIC":
                        continue
                    if not repo.get("name") or not repo.get("nameWithOwner"):
                        raise ValueError("Missing public merged PR repository identity")
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
            if public_profile:
                if not isinstance(page_info.get("hasNextPage"), bool):
                    raise ValueError("Invalid merged PR pagination state")
                if page_info["hasNextPage"]:
                    if (
                        not isinstance(end_cursor, str)
                        or not end_cursor
                        or end_cursor in seen_cursors
                    ):
                        raise ValueError("Invalid merged PR pagination cursor")
                    seen_cursors.add(end_cursor)
            if not page_info.get("hasNextPage") or not end_cursor:
                break
            cursor = str(end_cursor)
        merged_prs.sort(key=lambda entry: entry.get("merged_at") or "")
        return merged_prs
    except Exception as exc:
        if public_profile:
            raise
        logger.warning("Failed to fetch recent merged PRs: {}", exc)
        return []


def _collect_issue_stats(owner: str, token: str | None) -> dict[str, int]:
    """Fetch user's open/closed issue counts via GraphQL."""
    if token is None or token == "":
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
    owner: str, token: str | None, *, public_profile: bool = False
) -> tuple[dict[int, int], int]:
    """Bucket commit activity by hour from GitHub's visible push-event window.

    GitHub does not expose an all-time, account-wide commit timestamp history.
    This intentionally models a recent activity window using push-event
    timestamps weighted by each event's commit count rather than claiming to be
    a lifetime histogram.
    """
    try:
        if public_profile:
            data = _paginate_rest(
                f"{_BASE}/users/{owner}/events/public?per_page=100",
                token,
                require_complete=True,
            )
        else:
            data = _paginate_rest(f"{_BASE}/users/{owner}/events?per_page=100", token)
        hours: dict[int, int] = {}
        sampled_commits = 0
        for event in data:
            if event.get("type") != "PushEvent":
                continue
            created = event.get("created_at", "")
            if not created and not public_profile:
                continue
            try:
                dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
                if public_profile:
                    if dt.tzinfo is None:
                        raise ValueError("Missing UTC offset")
                    dt = dt.astimezone(UTC)
            except (ValueError, AttributeError):
                if public_profile:
                    raise ValueError("Invalid public push timestamp") from None
                continue
            payload = event.get("payload")
            payload_dict = payload if isinstance(payload, dict) else {}
            event_size = payload_dict.get("size")
            if public_profile and (
                not isinstance(payload, dict)
                or (
                    event_size is not None
                    and (type(event_size) is not int or event_size < 0)
                )
                or not isinstance(payload_dict.get("commits", []), list)
            ):
                raise ValueError("Invalid public push payload")
            if isinstance(event_size, int) and event_size >= 0:
                commit_count = event_size
            elif "commits" in payload_dict:
                commit_count = len(payload_dict["commits"] or [])
            else:
                # A push without either count contributes one unit to the
                # historical event-weighted estimate. Explicit zeros do not.
                commit_count = 1
            if commit_count == 0:
                continue
            sampled_commits += commit_count
            hour = dt.hour
            hours[hour] = hours.get(hour, 0) + commit_count
        return dict(sorted(hours.items())), sampled_commits
    except Exception as exc:
        if public_profile:
            raise
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
        if owner_login is not None and owner_login != owner_casefold:
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
        repo_data: dict[str, Any],
    ) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        repo_name = str(repo_data.get("name") or repo)
        full_name = str(repo_data.get("full_name") or f"{owner}/{repo_name}")
        data = _paginate_rest(
            f"{_BASE}/repos/{full_name}/releases?per_page=100",
            token,
        )
        release_rows = [row for item in data if (row := _json_object(item)) is not None]
        return repo_data, release_rows

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


def _collect_top_repos(
    repos: list[Any],
    limit: int | None = None,
) -> list[dict[str, Any]]:
    """Return the top repos sorted by stars descending."""
    non_forks: list[dict[str, Any]] = []
    for repo in repos:
        row = _json_object(repo)
        if row is not None and not row.get("fork"):
            non_forks.append(row)
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


def collect(
    owner: str, repo: str, token: str | None = None, *, public_profile: bool = False
) -> dict[str, Any]:
    """Collect GitHub metrics for *owner*/*repo* and return a flat dict."""
    failures: list[str] = []
    metrics: dict[str, Any] = {"collection_failures": failures}

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
    metrics["latest_stargazer"] = _collect_latest_stargazer(
        owner,
        repo,
        int(metrics.get("stars", 0) or 0),
        token,
    )

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

    # -- GraphQL: contributions for the profile owner, not the token viewer
    contribution_stats = _collect_contribution_stats(owner, token)
    calendar_failed = bool(contribution_stats.pop("collection_failed", False))
    if calendar_failed:
        failures.append("contributions_calendar")
    metrics.update(contribution_stats)

    # -- REST: languages, top repos, traffic -----------------------------
    try:
        all_repos = _paginate_rest(
            f"{_BASE}/users/{owner}/repos?per_page=100", token, require_complete=True
        )
        if any(not isinstance(row, dict) for row in all_repos):
            raise TypeError("Required GitHub inventory contains a malformed repository")
        if public_profile:
            if any(not isinstance(row.get("private"), bool) for row in all_repos):
                raise ValueError("Missing public repository visibility")
            all_repos = [
                row
                for row in all_repos
                if row["private"] is False
                and row.get("visibility", "public") == "public"
            ]
            for row in all_repos:
                if row.get("fork") is False and row.get("language") is not None:
                    if (
                        not isinstance(row["language"], str)
                        or not row["language"].strip()
                    ):
                        raise ValueError("Malformed primary repository language")
                    datetime.fromisoformat(row["created_at"])
    except Exception as exc:
        logger.warning("Failed to fetch repos list: {}", exc)
        all_repos = []
        failures.append("languages")
    metrics["languages"] = _collect_languages(all_repos, token, failures)
    metrics["repos"] = all_repos
    metrics["top_repos"] = _collect_top_repos(all_repos)
    metrics.update(_collect_traffic(owner, repo, token))

    # -- New collectors: PRs, issues, commit hours, releases ----------------
    try:
        metrics["recent_merged_prs"] = (
            _collect_recent_merged_prs(owner, token, public_profile=True)
            if public_profile
            else _collect_recent_merged_prs(owner, token)
        )
    except Exception as exc:
        logger.warning("Failed to collect recent merged PRs: {}", exc)
        failures.append("recent_merged_prs")
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
        ) = (
            _collect_commit_hour_distribution(owner, token, public_profile=True)
            if public_profile
            else _collect_commit_hour_distribution(owner, token)
        )
    except Exception as exc:
        logger.warning("Failed to collect commit hour distribution: {}", exc)
        failures.append("commit_hour_distribution")
        metrics["commit_hour_distribution"] = {}
        metrics["commit_hour_distribution_sample_size"] = 0

    if not metrics.get("contributions_calendar") and (
        metrics.get("recent_merged_prs") or metrics.get("commit_hour_distribution")
    ):
        logger.warning(
            "Contribution calendar empty for {} while owner-scoped activity exists",
            owner,
        )

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
    if token is None or token == "":
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
