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
from typing import Any

from ..utils import get_logger
from .shared import (
    WorldState,
    compute_maturity,
    compute_world_state,
    contributions_monthly_to_daily_series,
)

logger = get_logger(module=__name__)


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
    current_repos = current_metrics.get("top_repos", []) or current_metrics.get(
        "repos", []
    )
    dated_repos = _repos_by_creation_date(
        history.get("repos", []),
        current_repos,
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

    snapshots: list[DailySnapshot] = []

    for day_idx in range(total_days):
        day = account_created + timedelta(days=day_idx)
        progress = day_idx / max(1, total_days - 1)
        day_iso = day.isoformat()

        # Repos existing on this day
        repos_so_far: list[dict[str, Any]] = []
        for created, repo_info in dated_repos:
            if created <= day:
                age_months = max(
                    1, (day.year - created.year) * 12 + (day.month - created.month)
                )
                r = dict(repo_info)
                r["age_months"] = age_months
                # Distribute stars proportionally
                total_stars = stars_cumulative.get(day, 0)
                if repos_so_far or total_stars == 0:
                    # Proportional distribution based on current stars
                    pass
                repos_so_far.append(r)
            else:
                break

        # Distribute cumulative stars across repos proportionally
        total_stars = stars_cumulative.get(day, 0)
        if repos_so_far and total_stars > 0:
            total_current_stars = sum(r.get("stars", 0) for r in repos_so_far)
            if total_current_stars > 0:
                for r in repos_so_far:
                    r["stars"] = round(
                        total_stars * (r.get("stars", 0) / total_current_stars)
                    )
            else:
                # Equal distribution
                per_repo = total_stars // len(repos_so_far)
                for r in repos_so_far:
                    r["stars"] = per_repo

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

        # Maturity and world state
        maturity = compute_maturity(metrics_dict)
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


def sample_frames(
    snapshots: list[DailySnapshot],
    *,
    max_frames: int = 150,
) -> list[DailySnapshot]:
    """Adaptively sample snapshots to produce a manageable frame count.

    Strategy:
    1. Always include first and last day.
    2. Score eventful transitions
       (repos, stars, releases, PRs, language/topic/world shifts).
    3. Fill remaining budget with uniform temporal sampling.
    4. Deduplicate only near-identical adjacent frames across multiple signals.
    """
    if not snapshots:
        return []
    if len(snapshots) <= max_frames:
        return list(snapshots)

    n = len(snapshots)
    selected_indices: set[int] = {0, n - 1}

    # Identify event days
    event_budget = int(max_frames * 0.4)
    event_scores: list[tuple[float, int]] = []

    for i in range(1, n):
        score = 0.0
        curr = snapshots[i].metrics_dict
        prev = snapshots[i - 1].metrics_dict
        curr_world = snapshots[i].world_state
        prev_world = snapshots[i - 1].world_state

        # New repo created
        repo_diff = len(curr.get("repos", [])) - len(prev.get("repos", []))
        if repo_diff > 0:
            score += 2.5 + min(2.0, repo_diff * 0.8)

        # Star burst (>= 3 new stars in a day)
        star_diff = curr.get("stars", 0) - prev.get("stars", 0)
        if star_diff > 0:
            score += min(4.0, star_diff * 0.5)

        # Maturity jump
        mat_diff = abs(snapshots[i].maturity - snapshots[i - 1].maturity)
        if mat_diff > 0.01:
            score += mat_diff * 50

        # Contribution/month boundary changes
        monthly_curr = curr.get("contributions_monthly", {})
        monthly_prev = prev.get("contributions_monthly", {})
        if len(monthly_curr) > len(monthly_prev):
            score += 1.2

        # Releases / merged PRs
        release_diff = len(curr.get("releases", [])) - len(prev.get("releases", []))
        if release_diff > 0:
            score += 2.0 + min(3.0, release_diff * 1.2)
        merged_pr_diff = len(curr.get("recent_merged_prs", [])) - len(
            prev.get("recent_merged_prs", [])
        )
        if merged_pr_diff > 0:
            score += 1.5 + min(3.0, merged_pr_diff * 0.9)

        # Language/topic shifts
        lang_div_diff = abs(
            float(curr.get("language_diversity", 0.0) or 0.0)
            - float(prev.get("language_diversity", 0.0) or 0.0)
        )
        score += min(2.5, lang_div_diff * 4.0)
        if curr.get("language_count", 0) != prev.get("language_count", 0):
            score += 1.0
        if curr.get("topic_clusters", {}) != prev.get("topic_clusters", {}):
            score += 0.8

        # Atmosphere/world shifts
        if curr_world.time_of_day != prev_world.time_of_day:
            score += 1.2
        if curr_world.weather != prev_world.weather:
            score += 1.6
        if curr_world.season != prev_world.season:
            score += 1.2
        score += min(
            1.8,
            abs(curr_world.weather_severity - prev_world.weather_severity) * 4.0,
        )
        score += min(
            1.4, abs(curr_world.activity_pressure - prev_world.activity_pressure) * 2.5
        )

        if score > 0:
            event_scores.append((score, i))

    # Select top event days
    event_scores.sort(reverse=True)
    for _, idx in event_scores[:event_budget]:
        selected_indices.add(idx)

    # Fill remaining budget with uniform sampling
    remaining = max_frames - len(selected_indices)
    if remaining > 0:
        step = max(1, n // remaining)
        for i in range(0, n, step):
            selected_indices.add(i)
            if len(selected_indices) >= max_frames:
                break

    # Sort and deduplicate by multi-signal similarity
    sorted_indices = sorted(selected_indices)
    result: list[DailySnapshot] = [snapshots[sorted_indices[0]]]
    for idx in sorted_indices[1:]:
        candidate = snapshots[idx]
        previous = result[-1]
        is_distinct = any(
            (
                abs(candidate.maturity - previous.maturity) >= 0.001,
                candidate.world_state.time_of_day != previous.world_state.time_of_day,
                candidate.world_state.weather != previous.world_state.weather,
                candidate.world_state.season != previous.world_state.season,
                candidate.metrics_dict.get("stars", 0)
                != previous.metrics_dict.get("stars", 0),
                candidate.metrics_dict.get("forks", 0)
                != previous.metrics_dict.get("forks", 0),
                candidate.metrics_dict.get("language_count", 0)
                != previous.metrics_dict.get("language_count", 0),
                len(candidate.metrics_dict.get("releases", []))
                != len(previous.metrics_dict.get("releases", [])),
                len(candidate.metrics_dict.get("recent_merged_prs", []))
                != len(previous.metrics_dict.get("recent_merged_prs", [])),
            )
        )
        if is_distinct or idx == n - 1:
            result.append(candidate)

    # Final trim if over budget
    if len(result) > max_frames:
        step = len(result) / max_frames
        sampled: list[DailySnapshot] = []
        for i in range(max_frames):
            sampled.append(result[int(i * step)])
        # Ensure last frame
        if sampled[-1] is not result[-1]:
            sampled[-1] = result[-1]
        result = sampled

    logger.info(
        "Sampled {} frames from {} days (first: {}, last: {})",
        len(result),
        len(snapshots),
        result[0].day if result else "N/A",
        result[-1].day if result else "N/A",
    )
    return result
