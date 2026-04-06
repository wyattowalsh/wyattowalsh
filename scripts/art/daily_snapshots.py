"""
daily_snapshots.py — Historical daily state reconstruction
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Reconstructs what a GitHub profile looked like on each calendar day
from account creation through a configurable terminal day,
producing DailySnapshot objects
that all 4 art generators can consume for timelapse GIF rendering.

Public API::

    build_daily_snapshots(history, current_metrics, *, owner) -> list[DailySnapshot]
    sample_frames(snapshots, *, max_frames) -> list[DailySnapshot]
"""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass
from datetime import date as dt_date
from datetime import datetime, timedelta
from typing import Any, cast

from ..utils import get_logger
from .shared import (
    WorldState,
    compute_maturity,
    compute_world_state,
    contributions_monthly_to_daily_series,
    order_repos_for_visual_plan,
    stable_repo_visual_order,
)

logger = get_logger(module=__name__)
DEFAULT_PUBLISHED_MAX_FRAMES = 120


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class DailySnapshot:
    """Everything all 4 generators need for one calendar day."""

    day: dt_date
    day_index: int
    total_days: int
    progress: float
    maturity: float
    world_state: WorldState
    metrics_dict: dict[str, Any]
    history_dict: dict[str, Any]


# ---------------------------------------------------------------------------
# Pre-indexing helpers
# ---------------------------------------------------------------------------


def _parse_date(value: str | None) -> dt_date | None:
    if not value or not isinstance(value, str):
        return None
    s = value.strip()
    try:
        if "T" in s:
            return datetime.fromisoformat(s.replace("Z", "+00:00")).date()
        if len(s) >= 10:
            return dt_date.fromisoformat(s[:10])
    except ValueError:
        pass
    return None


def _cumulative_counts_by_date(
    events: list[dict[str, Any]],
    start: dt_date,
    end: dt_date,
) -> dict[dt_date, int]:
    """Build a cumulative event count for each day in [start, end]."""
    daily: dict[dt_date, int] = defaultdict(int)
    for ev in events:
        d = _parse_date(ev.get("date"))
        if d is not None:
            daily[d] += 1

    cumulative: dict[dt_date, int] = {}
    running = 0
    current = start
    while current <= end:
        running += daily.get(current, 0)
        cumulative[current] = running
        current += timedelta(days=1)
    return cumulative


def _repos_by_creation_date(
    history_repos: list[dict[str, Any]],
    current_repos: list[dict[str, Any]],
) -> list[tuple[dt_date, dict[str, Any]]]:
    """Merge history repo dates with current repo details, sorted by creation date."""
    # Build detail lookup from current metrics
    detail_by_name: dict[str, dict[str, Any]] = {}
    for r in current_repos:
        name = r.get("name", "")
        if name:
            detail_by_name[name] = r

    result: list[tuple[dt_date, dict[str, Any]]] = []
    for hr in history_repos:
        d = _parse_date(hr.get("date"))
        name = hr.get("name", "")
        if d is None:
            continue
        details = detail_by_name.get(name, {})
        repo = {
            "name": name,
            "language": details.get("language"),
            "stars": details.get("stars", 0),
            "forks": details.get("forks", 0),
            "topics": details.get("topics", []),
            "description": details.get("description", ""),
            "created": d,
        }
        result.append((d, repo))

    result.sort(key=lambda x: x[0])
    return result


def _stable_repo_visual_order(
    dated_repos: list[tuple[dt_date, dict[str, Any]]],
    *,
    terminal_day: dt_date,
    preferred_names: list[str] | None = None,
) -> list[str]:
    """Freeze the stable all-repo visual order for cumulative timelapse frames."""
    if not dated_repos:
        return []

    final_repos: list[dict[str, Any]] = []
    for created, repo_info in dated_repos:
        if created > terminal_day:
            continue
        repo = dict(repo_info)
        repo["age_months"] = max(
            1,
            (terminal_day.year - created.year) * 12
            + (terminal_day.month - created.month),
        )
        final_repos.append(repo)

    final_repo_names = {
        str(repo.get("name"))
        for repo in final_repos
        if isinstance(repo.get("name"), str) and repo.get("name")
    }
    filtered_preferred_names = [
        name for name in (preferred_names or []) if name in final_repo_names
    ]
    return stable_repo_visual_order(
        final_repos,
        preferred_names=filtered_preferred_names,
    )


def _allocate_star_delta(
    delta: int,
    repo_weights: dict[str, int | float],
    repo_balances: dict[str, float],
) -> dict[str, int]:
    """Allocate only newly accrued stars without clawing back prior repo totals."""
    if delta <= 0 or not repo_weights:
        return {}

    normalized_weights = {
        name: max(0.0, float(weight or 0.0)) for name, weight in repo_weights.items()
    }
    total_weight = sum(normalized_weights.values())
    if total_weight <= 0:
        equal_weight = 1.0 / len(normalized_weights)
        normalized_weights = {name: equal_weight for name in normalized_weights}
    else:
        normalized_weights = {
            name: weight / total_weight for name, weight in normalized_weights.items()
        }

    quotas = {
        name: repo_balances.get(name, 0.0) + (delta * share)
        for name, share in normalized_weights.items()
    }
    allocations = {
        name: max(0, int(math.floor(quota))) for name, quota in quotas.items()
    }
    assigned = sum(allocations.values())

    while assigned > delta:
        removable = min(
            (name for name, allocation in allocations.items() if allocation > 0),
            key=lambda name: (
                quotas[name] - allocations[name],
                normalized_weights[name],
                name,
            ),
        )
        allocations[removable] -= 1
        assigned -= 1

    while assigned < delta:
        recipient = max(
            quotas,
            key=lambda name: (
                quotas[name] - allocations[name],
                normalized_weights[name],
                name,
            ),
        )
        allocations[recipient] += 1
        assigned += 1

    for name, quota in quotas.items():
        repo_balances[name] = quota - allocations[name]

    return allocations


def _interpolate_scalar(current_value: int | float, progress: float) -> int:
    """Linearly interpolate a scalar from 0 to current_value based on progress."""
    return max(0, round(current_value * progress))


def _language_distribution_at_day(
    repos_so_far: list[dict[str, Any]],
    current_languages: dict[str, int],
    final_repo_counts_by_lang: dict[str, int],
) -> dict[str, int]:
    """Approximate language byte distribution for repos existing on a given day.

    Partitions current byte totals by language adoption progress over time.
    Each existing repo contributes gradually during its first 6 months.
    """
    if not current_languages:
        return {}

    active_weight_by_lang: dict[str, float] = defaultdict(float)
    for r in repos_so_far:
        lang = r.get("language")
        if lang:
            age_months = max(1, int(r.get("age_months", 1) or 1))
            active_weight_by_lang[lang] += min(1.0, age_months / 6.0)

    result: dict[str, int] = {}
    for lang, byte_count in current_languages.items():
        denom = max(1, final_repo_counts_by_lang.get(lang, 0))
        activation = min(1.0, active_weight_by_lang.get(lang, 0.0) / float(denom))
        if activation > 0:
            result[lang] = max(1, round(max(0, int(byte_count or 0)) * activation))

    return result


def _truncate_monthly(
    contributions_monthly: dict[str, int],
    up_to: dt_date,
) -> dict[str, int]:
    """Return only months <= up_to date."""
    cutoff = f"{up_to.year:04d}-{up_to.month:02d}"
    return {k: v for k, v in contributions_monthly.items() if k <= cutoff}


def _trailing_year_contributions(
    daily_series: dict[str, int],
    on_date: dt_date,
) -> int:
    """Sum contributions in the 365 days ending on on_date."""
    total = 0
    for i in range(365):
        d = (on_date - timedelta(days=i)).isoformat()
        total += daily_series.get(d, 0)
    return total


def _truncate_daily(
    contributions_daily: dict[str, int],
    up_to: dt_date,
) -> dict[str, int]:
    """Return only daily contribution points <= up_to date."""
    truncated: dict[str, int] = {}
    for key, value in contributions_daily.items():
        parsed = _parse_date(key)
        if parsed is not None and parsed <= up_to:
            truncated[key] = value
    return truncated


def _with_canonical_date(
    item: dict[str, Any],
    *,
    fallback_keys: tuple[str, ...],
) -> dict[str, Any]:
    """Fill a canonical ``date`` field from fallback keys when needed."""
    if item.get("date"):
        return item

    normalized = dict(item)
    for key in fallback_keys:
        value = normalized.get(key)
        if isinstance(value, str) and value:
            normalized["date"] = value
            break
    return normalized


def _advance_dated_cursor(
    items: list[dict[str, Any]],
    cursor: int,
    day_iso: str,
    *,
    date_key: str = "date",
) -> int:
    """Advance a sorted event cursor through all entries on or before ``day_iso``."""
    while (
        cursor < len(items) and (items[cursor].get(date_key, "") or "")[:10] <= day_iso
    ):
        cursor += 1
    return cursor


def _timeline_end_day(*, include_today: bool) -> dt_date:
    """Resolve terminal snapshot day.

    Excluding today by default avoids partial-day artifacts that can cause
    unstable timelapse output when metrics are fetched at different times.
    """
    return dt_date.today() if include_today else dt_date.today() - timedelta(days=1)


def _rolling_activity_ratio(daily_contribs: dict[str, int], day: dt_date) -> float:
    """Compute bounded recent activity ratio from real contribution history."""
    recent_total = 0
    long_total = 0
    for i in range(365):
        d = (day - timedelta(days=i)).isoformat()
        value = max(0, int(daily_contribs.get(d, 0) or 0))
        long_total += value
        if i < 60:
            recent_total += value
    if long_total <= 0:
        return 0.0
    return max(0.0, min(1.0, recent_total / float(long_total)))


def _estimate_issue_stats_at_day(
    *,
    day: dt_date,
    progress: float,
    daily_contribs: dict[str, int],
    open_issues_current: int,
    issue_stats_current: dict[str, Any],
    releases_count: int,
    merged_prs_count: int,
) -> tuple[dict[str, int], int]:
    """Estimate historical issue-open/close pressure when no daily issue log exists."""
    current_open = max(0, int(open_issues_current or 0))
    current_closed = max(0, int(issue_stats_current.get("closed_count", 0) or 0))
    total_current = current_open + current_closed
    if total_current <= 0:
        return {"open_count": 0, "closed_count": 0}, 0

    activity_ratio = _rolling_activity_ratio(daily_contribs, day)
    issue_volume = max(
        0.0,
        min(
            1.0,
            (progress * 0.75) + (activity_ratio * 0.25),
        ),
    )
    estimated_total = max(1, round(total_current * issue_volume))

    release_pressure = min(1.0, (releases_count + merged_prs_count) / 16.0)
    current_open_ratio = current_open / float(total_current)
    open_ratio = (
        current_open_ratio + (0.20 * (1.0 - progress)) - (0.12 * release_pressure)
    )
    open_ratio = max(0.05, min(0.90, open_ratio))

    estimated_open = min(estimated_total, max(0, round(estimated_total * open_ratio)))
    estimated_closed = max(0, estimated_total - estimated_open)
    return {
        "open_count": estimated_open,
        "closed_count": estimated_closed,
    }, estimated_open


def _hour_from_event(event: dict[str, Any], keys: tuple[str, ...]) -> int | None:
    for key in keys:
        value = event.get(key)
        if not isinstance(value, str) or not value:
            continue
        try:
            if "T" in value:
                return datetime.fromisoformat(value.replace("Z", "+00:00")).hour
        except ValueError:
            continue
    return None


def _estimate_commit_hours_at_day(
    *,
    day: dt_date,
    daily_contribs: dict[str, int],
    base_distribution: dict[str, int] | dict[int, int],
    stars: list[dict[str, Any]],
    forks: list[dict[str, Any]],
    releases: list[dict[str, Any]],
    merged_prs: list[dict[str, Any]],
) -> dict[int, int]:
    """Estimate hourly activity distribution from available history and priors."""
    event_hours: dict[int, int] = defaultdict(int)

    for ev in stars:
        hour = _hour_from_event(ev, ("date",))
        if hour is not None:
            event_hours[hour] += 1
    for ev in forks:
        hour = _hour_from_event(ev, ("date",))
        if hour is not None:
            event_hours[hour] += 1
    for ev in releases:
        hour = _hour_from_event(ev, ("published_at", "date"))
        if hour is not None:
            event_hours[hour] += 2
    for ev in merged_prs:
        hour = _hour_from_event(ev, ("merged_at", "date"))
        if hour is not None:
            event_hours[hour] += 2

    normalized_base: dict[int, int] = {}
    for key, value in (base_distribution or {}).items():
        try:
            hour = int(key)
            if 0 <= hour <= 23:
                normalized_base[hour] = max(0, int(value or 0))
        except (TypeError, ValueError):
            continue

    recent_points: list[tuple[dt_date, int]] = []
    for i in range(90):
        d = day - timedelta(days=i)
        v = max(0, int(daily_contribs.get(d.isoformat(), 0) or 0))
        if v > 0:
            recent_points.append((d, v))
    weekend_weight = sum(v for d, v in recent_points if d.weekday() >= 5) / max(
        1, sum(v for _, v in recent_points)
    )
    synthetic_peak = int(round(14 + 8 * weekend_weight))
    synthetic_peak = max(8, min(22, synthetic_peak))
    synthetic: dict[int, int] = {}
    for hour in range(24):
        dist = abs(hour - synthetic_peak)
        synthetic[hour] = max(0, 10 - dist * 2)

    if not normalized_base:
        return synthetic

    total_event_points = sum(event_hours.values())
    event_weight = min(0.70, total_event_points / 30.0)
    trend_weight = 0.20 if total_event_points > 0 else 0.35
    base_weight = max(0.10, 1.0 - event_weight - trend_weight)

    result: dict[int, int] = {}
    for hour in range(24):
        combined = (
            normalized_base.get(hour, 0) * base_weight
            + synthetic.get(hour, 0) * trend_weight
            + event_hours.get(hour, 0) * event_weight * 8
        )
        result[hour] = max(0, int(round(combined)))
    return result


def _repo_recency_bands(
    repos: list[dict[str, Any]],
) -> dict[str, int]:
    """Bucket repos by coarse recency bands."""
    bands = {"fresh": 0, "recent": 0, "established": 0, "legacy": 0}
    for repo in repos:
        age = int(repo.get("age_months", 0) or 0)
        if age <= 3:
            bands["fresh"] += 1
        elif age <= 12:
            bands["recent"] += 1
        elif age <= 36:
            bands["established"] += 1
        else:
            bands["legacy"] += 1
    return bands


# ---------------------------------------------------------------------------
# Core builder
# ---------------------------------------------------------------------------


def build_daily_snapshots(
    history: dict[str, Any],
    current_metrics: dict[str, Any],
    *,
    owner: str = "",
    include_today: bool = False,
) -> list[DailySnapshot]:
    """Build one DailySnapshot per day from account creation to terminal day.

    Parameters
    ----------
    history : dict
        Output of ``fetch_history.collect_history()``.
    current_metrics : dict
        Output of ``fetch_metrics.collect()`` (or normalized metrics).
    owner : str
        GitHub username for labeling.
    include_today : bool
        If True, include today's partial day as the terminal snapshot.
        Defaults to False for deterministic daily comparisons.

    Returns
    -------
    list[DailySnapshot]
        One per calendar day, chronologically ordered.
    """
    # Determine timeline boundaries
    account_created = _parse_date(history.get("account_created"))
    if account_created is None:
        account_created = dt_date.today() - timedelta(days=365)
        logger.warning("No account_created in history; defaulting to 1 year ago")

    timeline_end = _timeline_end_day(include_today=include_today)
    if account_created > timeline_end:
        account_created = timeline_end

    total_days = (timeline_end - account_created).days + 1
    if total_days <= 0:
        return []

    logger.info(
        "Building {} daily snapshots from {} to {}",
        total_days,
        account_created,
        timeline_end,
    )
    from ..fetch_history import (
        compute_contribution_streaks,
        compute_star_velocity,
    )

    # Pre-index timeline events
    stars_cumulative = _cumulative_counts_by_date(
        history.get("stars", []),
        account_created,
        timeline_end,
    )
    forks_cumulative = _cumulative_counts_by_date(
        history.get("forks", []),
        account_created,
        timeline_end,
    )

    # Repo details (merged history dates + current details)
    current_repos = current_metrics.get("repos", []) or current_metrics.get(
        "top_repos", []
    )
    dated_repos = _repos_by_creation_date(
        history.get("repos", []),
        current_repos,
    )
    preferred_repo_names_source = current_metrics.get("repo_visual_order")
    preferred_repo_names = (
        [
            str(name)
            for name in preferred_repo_names_source
            if isinstance(name, str) and name
        ]
        if isinstance(preferred_repo_names_source, list)
        else []
    )
    repo_visual_order = _stable_repo_visual_order(
        dated_repos,
        terminal_day=timeline_end,
        preferred_names=preferred_repo_names,
    )

    # Contributions: prefer daily if available; fallback to monthly expansion.
    hist_monthly = history.get("contributions_monthly", {}) or {}
    raw_daily = history.get("contributions_daily", {}) or {}
    hist_daily: dict[str, int] = {}
    if isinstance(raw_daily, dict):
        for key, value in raw_daily.items():
            d = _parse_date(str(key))
            if d is not None:
                hist_daily[d.isoformat()] = max(0, int(value or 0))
    daily_contribs = (
        hist_daily
        if hist_daily
        else contributions_monthly_to_daily_series(hist_monthly)
    )

    # Current scalar values for interpolation
    curr = current_metrics
    curr_followers = curr.get("followers", 0) or 0
    curr_following = curr.get("following", 0) or 0
    curr_watchers = curr.get("watchers", 0) or 0
    curr_total_commits = curr.get("total_commits", 0) or 0
    curr_total_prs = curr.get("total_prs", 0) or 0
    curr_total_issues = curr.get("total_issues", 0) or 0
    curr_orgs = curr.get("orgs_count", 0) or 0
    curr_network = curr.get("network_count", 0) or 0
    curr_open_issues = curr.get("open_issues_count", 0) or 0
    curr_gists = curr.get("public_gists", 0) or 0
    curr_pr_review = curr.get("pr_review_count", 0) or 0
    curr_total_repos_contrib = curr.get("total_repos_contributed", 0) or 0
    curr_languages = curr.get("languages", {}) or {}
    current_issue_stats = (
        curr.get("issue_stats", {}) or history.get("issue_stats", {}) or {}
    )
    base_commit_hour_distribution = (
        curr.get("commit_hour_distribution", {})
        or history.get("commit_hour_distribution", {})
        or {}
    )
    all_releases = sorted(
        [
            _with_canonical_date(release, fallback_keys=("published_at",))
            for release in (
                history.get("releases", []) or curr.get("releases", []) or []
            )
        ],
        key=lambda e: e.get("date", ""),
    )
    all_recent_merged_prs = sorted(
        history.get("recent_merged_prs", []) or curr.get("recent_merged_prs", []) or [],
        key=lambda e: e.get("merged_at", ""),
    )

    # Account created string for history_dict
    ac_str = history.get("account_created", account_created.isoformat())

    # Star/fork event lists for history_dict truncation
    all_stars = sorted(history.get("stars", []), key=lambda e: e.get("date", ""))
    all_forks = sorted(history.get("forks", []), key=lambda e: e.get("date", ""))
    all_hist_repos = sorted(history.get("repos", []), key=lambda e: e.get("date", ""))
    sorted_daily_items = sorted(daily_contribs.items())
    final_repo_counts_by_lang: dict[str, int] = defaultdict(int)
    for _, repo in dated_repos:
        lang = repo.get("language")
        if lang:
            final_repo_counts_by_lang[str(lang)] += 1
    daily_cursor = 0
    stars_cursor = 0
    forks_cursor = 0
    repos_cursor = 0
    releases_cursor = 0
    merged_prs_cursor = 0
    repo_star_allocations: dict[str, int] = defaultdict(int)
    repo_star_balances: dict[str, float] = defaultdict(float)
    pending_star_delta = 0
    previous_total_stars = 0
    previous_maturity = 0.0

    snapshots: list[DailySnapshot] = []

    for day_idx in range(total_days):
        day = account_created + timedelta(days=day_idx)
        progress = day_idx / max(1, total_days - 1)
        day_iso = day.isoformat()
        total_stars = stars_cumulative.get(day, 0)
        pending_star_delta += max(0, total_stars - previous_total_stars)

        # Repos existing on this day
        active_repos: list[tuple[dt_date, dict[str, Any]]] = []
        for created, repo_info in dated_repos:
            if created <= day:
                active_repos.append((created, repo_info))
            else:
                break

        if active_repos and pending_star_delta > 0:
            repo_weights = {
                str(repo_info.get("name")): repo_info.get("stars", 0)
                for _, repo_info in active_repos
                if repo_info.get("name")
            }
            if repo_weights:
                allocations = _allocate_star_delta(
                    pending_star_delta,
                    repo_weights,
                    repo_star_balances,
                )
                for repo_name, repo_delta in allocations.items():
                    repo_star_allocations[repo_name] += repo_delta
                pending_star_delta -= sum(allocations.values())

        repos_so_far: list[dict[str, Any]] = []
        for created, repo_info in active_repos:
            age_months = max(
                1, (day.year - created.year) * 12 + (day.month - created.month)
            )
            r = dict(repo_info)
            r["age_months"] = age_months
            r["stars"] = repo_star_allocations.get(str(r.get("name")), 0)
            repos_so_far.append(r)
        repos_so_far = order_repos_for_visual_plan(
            repos_so_far,
            preferred_names=repo_visual_order,
        )

        # Trailing year contributions
        contribs_last_year = _trailing_year_contributions(daily_contribs, day)

        # Language distribution
        langs = _language_distribution_at_day(
            repos_so_far,
            curr_languages,
            final_repo_counts_by_lang,
        )

        # Monthly/daily contributions truncated
        monthly_trunc = _truncate_monthly(hist_monthly, day)
        while (
            daily_cursor < len(sorted_daily_items)
            and sorted_daily_items[daily_cursor][0] <= day_iso
        ):
            daily_cursor += 1
        daily_trunc = dict(sorted_daily_items[:daily_cursor])
        releases_cursor = _advance_dated_cursor(
            all_releases,
            releases_cursor,
            day_iso,
        )
        releases_trunc = all_releases[:releases_cursor]
        merged_prs_cursor = _advance_dated_cursor(
            all_recent_merged_prs,
            merged_prs_cursor,
            day_iso,
            date_key="merged_at",
        )
        recent_merged_prs_trunc = all_recent_merged_prs[:merged_prs_cursor]
        forks_cursor_for_day = _advance_dated_cursor(all_forks, forks_cursor, day_iso)
        forks_trunc = all_forks[:forks_cursor_for_day]
        issue_stats, open_issues_estimate = _estimate_issue_stats_at_day(
            day=day,
            progress=progress,
            daily_contribs=daily_contribs,
            open_issues_current=curr_open_issues,
            issue_stats_current=current_issue_stats,
            releases_count=len(releases_trunc),
            merged_prs_count=len(recent_merged_prs_trunc),
        )

        # Build metrics_dict (for ink_garden / topography)
        metrics_dict: dict[str, Any] = {
            "repos": repos_so_far,
            "stars": total_stars,
            "forks": forks_cumulative.get(day, 0),
            "watchers": _interpolate_scalar(curr_watchers, progress),
            "followers": _interpolate_scalar(curr_followers, progress),
            "following": _interpolate_scalar(curr_following, progress),
            "public_repos": len(repos_so_far),
            "orgs_count": _interpolate_scalar(curr_orgs, progress),
            "contributions_last_year": contribs_last_year,
            "total_commits": _interpolate_scalar(curr_total_commits, progress),
            "total_prs": _interpolate_scalar(curr_total_prs, progress),
            "total_issues": _interpolate_scalar(curr_total_issues, progress),
            "total_repos_contributed": _interpolate_scalar(
                curr_total_repos_contrib, progress
            ),
            "open_issues_count": open_issues_estimate,
            "network_count": _interpolate_scalar(curr_network, progress),
            "public_gists": _interpolate_scalar(curr_gists, progress),
            "pr_review_count": _interpolate_scalar(curr_pr_review, progress),
            "languages": langs,
            "contributions_monthly": monthly_trunc,
            "contributions_daily": daily_trunc,
            "label": owner,
            "account_created": ac_str,
            "issue_stats": issue_stats,
            "recent_merged_prs": recent_merged_prs_trunc,
            "releases": releases_trunc,
        }

        # Recompute derived signals every day.
        stars_cursor = _advance_dated_cursor(all_stars, stars_cursor, day_iso)
        stars_trunc = all_stars[:stars_cursor]
        metrics_dict["star_velocity"] = compute_star_velocity(stars_trunc)
        metrics_dict["contribution_streaks"] = compute_contribution_streaks(
            monthly_trunc
        )
        metrics_dict["commit_hour_distribution"] = _estimate_commit_hours_at_day(
            day=day,
            daily_contribs=daily_contribs,
            base_distribution=base_commit_hour_distribution,
            stars=stars_trunc,
            forks=forks_trunc,
            releases=releases_trunc,
            merged_prs=recent_merged_prs_trunc,
        )

        # Topic clusters
        topic_counts: dict[str, int] = defaultdict(int)
        for r in repos_so_far:
            for t in r.get("topics", []):
                topic_counts[t] += 1
        metrics_dict["topic_clusters"] = dict(
            sorted(topic_counts.items(), key=lambda kv: kv[1], reverse=True)
        )
        metrics_dict["repo_recency_bands"] = _repo_recency_bands(repos_so_far)
        metrics_dict["repo_visual_order"] = repo_visual_order

        # Language diversity
        if langs:
            total_bytes = sum(langs.values())
            if total_bytes > 0:
                entropy = 0.0
                for count in langs.values():
                    if count > 0:
                        p = count / total_bytes
                        entropy -= p * math.log2(p)
                metrics_dict["language_diversity"] = round(entropy, 4)
            else:
                metrics_dict["language_diversity"] = 0.0
            metrics_dict["language_count"] = len(langs)
        else:
            metrics_dict["language_diversity"] = 0.0
            metrics_dict["language_count"] = 0

        # Build history_dict for historical/timelapse consumers.
        forks_cursor = forks_cursor_for_day
        repos_cursor = _advance_dated_cursor(all_hist_repos, repos_cursor, day_iso)
        repos_trunc = all_hist_repos[:repos_cursor]

        history_dict: dict[str, Any] = {
            "account_created": ac_str,
            "stars": stars_trunc,
            "forks": forks_trunc,
            "repos": repos_trunc,
            "contributions_monthly": monthly_trunc,
            "contributions_daily": daily_trunc,
            "current_metrics": metrics_dict,
            "star_velocity": metrics_dict.get("star_velocity", {}),
            "contribution_streaks": metrics_dict.get("contribution_streaks", {}),
            "releases": releases_trunc,
            "recent_merged_prs": recent_merged_prs_trunc,
            "issue_stats": issue_stats,
            "commit_hour_distribution": metrics_dict["commit_hour_distribution"],
        }

        # Timelapse frames should never regress once cumulative signals have appeared.
        maturity = max(previous_maturity, compute_maturity(metrics_dict))
        world_state = compute_world_state(metrics_dict)

        snapshots.append(
            DailySnapshot(
                day=day,
                day_index=day_idx,
                total_days=total_days,
                progress=progress,
                maturity=maturity,
                world_state=world_state,
                metrics_dict=metrics_dict,
                history_dict=history_dict,
            )
        )
        previous_total_stars = max(previous_total_stars, total_stars)
        previous_maturity = maturity

    logger.info(
        "Built {} snapshots; maturity range {:.3f} → {:.3f}",
        len(snapshots),
        snapshots[0].maturity if snapshots else 0,
        snapshots[-1].maturity if snapshots else 0,
    )
    return snapshots


# ---------------------------------------------------------------------------
# Adaptive frame sampling
# ---------------------------------------------------------------------------


def _repo_signature(metrics: dict[str, Any]) -> tuple[str, ...]:
    return tuple(
        str(repo.get("name") or "")
        for repo in metrics.get("repos", [])
        if isinstance(repo, dict) and repo.get("name")
    )


def _counter_delta(current: object, previous: object) -> float:
    current_mapping = (
        cast("dict[str, Any]", current) if isinstance(current, dict) else {}
    )
    previous_mapping = (
        cast("dict[str, Any]", previous) if isinstance(previous, dict) else {}
    )
    keys = set(current_mapping.keys()) | set(previous_mapping.keys())
    return sum(
        abs(
            float(current_mapping.get(key, 0) or 0)
            - float(previous_mapping.get(key, 0) or 0)
        )
        for key in keys
    )


def _sequence_displacement(
    current_sequence: tuple[str, ...],
    previous_sequence: tuple[str, ...],
) -> int:
    current_positions = {name: index for index, name in enumerate(current_sequence)}
    previous_positions = {name: index for index, name in enumerate(previous_sequence)}
    shared_names = current_positions.keys() & previous_positions.keys()
    return sum(
        abs(current_positions[name] - previous_positions[name]) for name in shared_names
    )


def _transition_score(previous: DailySnapshot, current: DailySnapshot) -> float:
    previous_metrics = previous.metrics_dict
    current_metrics = current.metrics_dict
    previous_world = previous.world_state
    current_world = current.world_state
    previous_repo_signature = _repo_signature(previous_metrics)
    current_repo_signature = _repo_signature(current_metrics)

    score = 0.0

    repo_diff = len(current_repo_signature) - len(previous_repo_signature)
    if repo_diff > 0:
        score += 2.8 + min(4.2, repo_diff * (1.0 + current.progress * 2.0))

    repo_displacement = _sequence_displacement(
        current_repo_signature,
        previous_repo_signature,
    )
    if repo_displacement > 0:
        score += min(3.2, repo_displacement * 1.1)

    star_diff = max(
        0,
        int(current_metrics.get("stars", 0) or 0)
        - int(previous_metrics.get("stars", 0) or 0),
    )
    if star_diff > 0:
        score += min(4.0, star_diff * 0.35)

    fork_diff = max(
        0,
        int(current_metrics.get("forks", 0) or 0)
        - int(previous_metrics.get("forks", 0) or 0),
    )
    if fork_diff > 0:
        score += min(2.5, fork_diff * 0.45)

    maturity_diff = abs(current.maturity - previous.maturity)
    if maturity_diff > 0.001:
        score += min(3.2, maturity_diff * 35.0)

    contributions_day_diff = max(
        0,
        len(current_metrics.get("contributions_daily", {}))
        - len(previous_metrics.get("contributions_daily", {})),
    )
    if contributions_day_diff > 0:
        score += min(1.5, contributions_day_diff * 0.15)

    if len(current_metrics.get("contributions_monthly", {})) > len(
        previous_metrics.get("contributions_monthly", {})
    ):
        score += 0.9

    release_diff = len(current_metrics.get("releases", [])) - len(
        previous_metrics.get("releases", [])
    )
    if release_diff > 0:
        score += 2.0 + min(3.0, release_diff * 1.2)

    merged_pr_diff = len(current_metrics.get("recent_merged_prs", [])) - len(
        previous_metrics.get("recent_merged_prs", [])
    )
    if merged_pr_diff > 0:
        score += 1.5 + min(3.0, merged_pr_diff * 0.9)

    language_mix_shift = _counter_delta(
        current_metrics.get("languages"),
        previous_metrics.get("languages"),
    )
    if language_mix_shift > 0:
        score += min(2.8, math.log1p(language_mix_shift))

    language_diversity_diff = abs(
        float(current_metrics.get("language_diversity", 0.0) or 0.0)
        - float(previous_metrics.get("language_diversity", 0.0) or 0.0)
    )
    if language_diversity_diff > 0:
        score += min(2.0, language_diversity_diff * 4.0)

    if current_metrics.get("language_count", 0) != previous_metrics.get(
        "language_count",
        0,
    ):
        score += 1.0

    topic_shift = _counter_delta(
        current_metrics.get("topic_clusters"),
        previous_metrics.get("topic_clusters"),
    )
    if topic_shift > 0:
        score += min(2.6, topic_shift * 0.6)

    recency_shift = _counter_delta(
        current_metrics.get("repo_recency_bands"),
        previous_metrics.get("repo_recency_bands"),
    )
    if recency_shift > 0:
        score += min(2.3, recency_shift * 0.75)

    if current_world.time_of_day != previous_world.time_of_day:
        score += 1.2
    if current_world.weather != previous_world.weather:
        score += 1.6
    if current_world.season != previous_world.season:
        score += 1.2

    score += min(
        1.8,
        abs(current_world.weather_severity - previous_world.weather_severity) * 4.0,
    )
    score += min(
        1.4,
        abs(current_world.activity_pressure - previous_world.activity_pressure) * 2.5,
    )
    return score


def sample_frames(
    snapshots: list[DailySnapshot],
    *,
    max_frames: int = DEFAULT_PUBLISHED_MAX_FRAMES,
) -> list[DailySnapshot]:
    """Select representative snapshots without collapsing the published frame budget.

    Strategy:
    1. Always include the first and last day.
    2. Partition the interior timeline into budget-sized temporal buckets.
    3. Within each bucket, prefer the day with the largest cumulative,
       structural, or ecological transition.
    4. Break ties toward later days so quiet cumulative growth still reads
       forward instead of flattening into early-bucket states.
    """
    if not snapshots or max_frames <= 0:
        return []
    if max_frames == 1:
        return [snapshots[-1]]
    if len(snapshots) <= max_frames:
        return list(snapshots)
    if max_frames == 2:
        return [snapshots[0], snapshots[-1]]

    n = len(snapshots)
    transition_scores = [0.0] * n
    for index in range(1, n):
        transition_scores[index] = _transition_score(
            snapshots[index - 1],
            snapshots[index],
        )

    interior_slots = max_frames - 2
    interior_count = n - 2
    selected_indices = [0]
    for slot_index in range(interior_slots):
        start = 1 + (slot_index * interior_count) // interior_slots
        stop = 1 + ((slot_index + 1) * interior_count) // interior_slots
        bucket_span = max(1, stop - start)
        bucket_indices = range(start, stop)
        bucket_reference = snapshots[start - 1]
        best_index = max(
            bucket_indices,
            key=lambda index: (
                transition_scores[index]
                + _transition_score(bucket_reference, snapshots[index])
                + 0.15 * ((index - start + 1) / bucket_span),
                index,
            ),
        )
        selected_indices.append(best_index)
    selected_indices.append(n - 1)
    result = [snapshots[index] for index in selected_indices]

    logger.info(
        "Sampled {} frames from {} days (first: {}, last: {})",
        len(result),
        len(snapshots),
        result[0].day if result else "N/A",
        result[-1].day if result else "N/A",
    )
    return result
