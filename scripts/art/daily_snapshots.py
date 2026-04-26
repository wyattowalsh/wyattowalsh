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
MONOTONIC_CUMULATIVE_KEYS: tuple[str, ...] = (
    "stars",
    "forks",
    "watchers",
    "followers",
    "public_repos",
    "orgs_count",
    "total_commits",
    "total_prs",
    "total_issues",
    "total_repos_contributed",
    "network_count",
    "public_gists",
    "pr_review_count",
    "release_count",
    "merged_pr_count",
    "contributions_to_date",
)
RENDER_STATE_SCALAR_KEYS: tuple[str, ...] = (
    "stars",
    "forks",
    "watchers",
    "followers",
    "public_repos",
    "network_count",
    "total_commits",
    "total_prs",
    "total_issues",
    "total_repos_contributed",
    "public_gists",
    "pr_review_count",
    "release_count",
    "merged_pr_count",
    "contributions_to_date",
    "contributions_last_year",
    "language_count",
    "language_diversity",
    "open_issues_count",
)
RENDER_STATE_MAPPING_KEYS: tuple[str, ...] = (
    "languages",
    "topic_clusters",
    "repo_recency_bands",
    "commit_hour_distribution",
)
EVOLUTION_STATE_SCALAR_KEYS: tuple[str, ...] = (
    "maturity",
    "repo_density",
    "repo_age_maturity",
    "language_diversity_signal",
    "topic_diversity_signal",
    "release_pressure",
    "collaboration_pressure",
    "activity_pressure",
    "issue_pressure",
    "star_pressure",
)
EVOLUTION_STATE_MAPPING_KEYS: tuple[str, ...] = (
    "atmosphere_weights",
    "season_weights",
    "feature_ramps",
)


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


def _monotone_non_decreasing(current: int, previous: int) -> int:
    """Clamp *current* so cumulative public-history channels never regress."""

    return max(previous, current)


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


def _mapping_envelope(
    current: dict[str | int, int | float] | None,
    previous: dict[str | int, int | float] | None,
) -> dict[str | int, int | float]:
    """Clamp mapping values upward key-by-key."""
    current_mapping = current or {}
    previous_mapping = previous or {}
    merged: dict[str | int, int | float] = {}
    for key in set(current_mapping.keys()) | set(previous_mapping.keys()):
        curr = current_mapping.get(key, 0) or 0
        prev = previous_mapping.get(key, 0) or 0
        merged[key] = max(curr, prev)
    return merged


def _allocate_histogram_delta(
    delta: int,
    histogram: dict[int, int],
    distribution: dict[int, int],
) -> dict[int, int]:
    """Allocate an integer delta across histogram buckets using weighted quotas."""
    if delta <= 0:
        return dict(histogram)

    normalized = {
        hour: max(0.0, float(distribution.get(hour, 0) or 0.0)) for hour in range(24)
    }
    total = sum(normalized.values())
    if total <= 0:
        normalized = {hour: 0.0 for hour in range(24)}
        normalized[12] = 1.0
        total = 1.0

    quotas = {hour: (delta * normalized[hour]) / total for hour in range(24)}
    allocations = {hour: int(math.floor(quota)) for hour, quota in quotas.items()}
    assigned = sum(allocations.values())

    while assigned < delta:
        recipient = max(
            range(24),
            key=lambda hour: (quotas[hour] - allocations[hour], -abs(hour - 12), -hour),
        )
        allocations[recipient] += 1
        assigned += 1

    updated = {int(hour): int(histogram.get(hour, 0) or 0) for hour in range(24)}
    for hour, allocation in allocations.items():
        updated[hour] = updated.get(hour, 0) + allocation
    return updated


def _build_render_state(
    metrics_dict: dict[str, Any],
    *,
    previous_render_state: dict[str, Any] | None,
    cumulative_commit_hours: dict[int, int],
) -> dict[str, Any]:
    """Build the monotonic timelapse render contract consumed by generators."""
    previous_render_state = previous_render_state or {}
    previous_star_velocity = previous_render_state.get("star_velocity", {})
    current_star_velocity = metrics_dict.get("star_velocity", {})
    prev_recent_rate = (
        float(previous_star_velocity.get("recent_rate", 0.0) or 0.0)
        if isinstance(previous_star_velocity, dict)
        else 0.0
    )
    prev_peak_rate = (
        float(previous_star_velocity.get("peak_rate", 0.0) or 0.0)
        if isinstance(previous_star_velocity, dict)
        else 0.0
    )
    current_recent_rate = (
        float(current_star_velocity.get("recent_rate", 0.0) or 0.0)
        if isinstance(current_star_velocity, dict)
        else 0.0
    )
    current_peak_rate = (
        float(current_star_velocity.get("peak_rate", 0.0) or 0.0)
        if isinstance(current_star_velocity, dict)
        else 0.0
    )
    render_recent_rate = max(prev_recent_rate, current_recent_rate)
    render_peak_rate = max(prev_peak_rate, current_peak_rate, render_recent_rate)
    render_trend = (
        "rising"
        if render_recent_rate > prev_recent_rate or render_peak_rate > prev_peak_rate
        else str(previous_star_velocity.get("trend", "stable") or "stable")
        if isinstance(previous_star_velocity, dict)
        else "stable"
    )

    current_streaks = metrics_dict.get("contribution_streaks", {})
    previous_streaks = previous_render_state.get("contribution_streaks", {})
    streak_envelope = max(
        int(current_streaks.get("longest_streak_months", 0) or 0)
        if isinstance(current_streaks, dict)
        else 0,
        int(current_streaks.get("current_streak_months", 0) or 0)
        if isinstance(current_streaks, dict)
        else 0,
        int(previous_streaks.get("longest_streak_months", 0) or 0)
        if isinstance(previous_streaks, dict)
        else 0,
        int(previous_streaks.get("current_streak_months", 0) or 0)
        if isinstance(previous_streaks, dict)
        else 0,
    )

    current_issue_stats = (
        metrics_dict.get("issue_stats")
        if isinstance(metrics_dict.get("issue_stats"), dict)
        else {}
    )
    previous_issue_stats = (
        previous_render_state.get("issue_stats")
        if isinstance(previous_render_state.get("issue_stats"), dict)
        else {}
    )
    open_issue_envelope = max(
        int(metrics_dict.get("open_issues_count", 0) or 0),
        int(current_issue_stats.get("open_count", 0) or 0),
        int(previous_render_state.get("open_issues_count", 0) or 0),
        int(previous_issue_stats.get("open_count", 0) or 0),
    )
    closed_issue_envelope = max(
        int(current_issue_stats.get("closed_count", 0) or 0),
        int(previous_issue_stats.get("closed_count", 0) or 0),
        max(0, int(metrics_dict.get("total_issues", 0) or 0) - open_issue_envelope),
    )

    cumulative_state = dict(metrics_dict.get("cumulative_state", {}))
    languages = _mapping_envelope(
        metrics_dict.get("languages"),
        previous_render_state.get("languages"),
    )
    topic_clusters = _mapping_envelope(
        metrics_dict.get("topic_clusters"),
        previous_render_state.get("topic_clusters"),
    )
    repo_recency_bands = _mapping_envelope(
        metrics_dict.get("repo_recency_bands"),
        previous_render_state.get("repo_recency_bands"),
    )
    language_count = max(
        int(metrics_dict.get("language_count", 0) or 0),
        len(languages),
        int(previous_render_state.get("language_count", 0) or 0),
    )
    language_diversity = max(
        float(metrics_dict.get("language_diversity", 0.0) or 0.0),
        float(previous_render_state.get("language_diversity", 0.0) or 0.0),
    )

    return {
        "label": metrics_dict.get("label"),
        "account_created": metrics_dict.get("account_created"),
        "repos": [dict(repo) for repo in metrics_dict.get("repos", [])],
        "repo_visual_order": list(metrics_dict.get("repo_visual_order", []) or []),
        "stars": cumulative_state.get("stars", metrics_dict.get("stars", 0)),
        "forks": cumulative_state.get("forks", metrics_dict.get("forks", 0)),
        "watchers": cumulative_state.get("watchers", metrics_dict.get("watchers", 0)),
        "followers": cumulative_state.get(
            "followers", metrics_dict.get("followers", 0)
        ),
        "public_repos": cumulative_state.get(
            "public_repos", metrics_dict.get("public_repos", 0)
        ),
        "network_count": cumulative_state.get(
            "network_count", metrics_dict.get("network_count", 0)
        ),
        "total_commits": cumulative_state.get(
            "total_commits", metrics_dict.get("total_commits", 0)
        ),
        "total_prs": cumulative_state.get("total_prs", metrics_dict.get("total_prs", 0)),
        "total_issues": cumulative_state.get(
            "total_issues", metrics_dict.get("total_issues", 0)
        ),
        "total_repos_contributed": cumulative_state.get(
            "total_repos_contributed",
            metrics_dict.get("total_repos_contributed", 0),
        ),
        "public_gists": cumulative_state.get(
            "public_gists", metrics_dict.get("public_gists", 0)
        ),
        "pr_review_count": cumulative_state.get(
            "pr_review_count", metrics_dict.get("pr_review_count", 0)
        ),
        "release_count": cumulative_state.get(
            "release_count", metrics_dict.get("release_count", 0)
        ),
        "merged_pr_count": cumulative_state.get(
            "merged_pr_count", metrics_dict.get("merged_pr_count", 0)
        ),
        "contributions_to_date": cumulative_state.get(
            "contributions_to_date", metrics_dict.get("contributions_to_date", 0)
        ),
        # Keep compatibility with existing generators that still read this key.
        "contributions_last_year": cumulative_state.get(
            "contributions_to_date", metrics_dict.get("contributions_to_date", 0)
        ),
        "contributions_monthly": dict(metrics_dict.get("contributions_monthly", {})),
        "contributions_daily": dict(metrics_dict.get("contributions_daily", {})),
        "languages": languages,
        "language_count": language_count,
        "language_diversity": language_diversity,
        "topic_clusters": topic_clusters,
        "repo_recency_bands": repo_recency_bands,
        "releases": list(metrics_dict.get("releases", []) or []),
        "recent_merged_prs": list(metrics_dict.get("recent_merged_prs", []) or []),
        "commit_hour_distribution": dict(cumulative_commit_hours),
        "star_velocity": {
            "recent_rate": round(render_recent_rate, 2),
            "peak_rate": round(render_peak_rate, 2),
            "trend": render_trend,
        },
        "contribution_streaks": {
            "longest_streak_months": streak_envelope,
            "current_streak_months": streak_envelope,
            "streak_active": streak_envelope > 0,
        },
        # Treat issue burden as a monotonic envelope instead of a shrinking current-state estimate.
        "open_issues_count": open_issue_envelope,
        "issue_stats": {
            "open_count": open_issue_envelope,
            "closed_count": closed_issue_envelope,
        },
        "cumulative_state": cumulative_state,
    }


def _clamp01(value: int | float) -> float:
    return max(0.0, min(1.0, float(value or 0.0)))


def _log_signal(value: int | float, *, ceiling: int | float) -> float:
    value_f = max(0.0, float(value or 0.0))
    ceiling_f = max(1.0, float(ceiling or 1.0))
    return _clamp01(math.log1p(value_f) / math.log1p(ceiling_f))


def _repo_identity_map(render_state: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Return stable per-repo identity metadata for timelapse rendering."""
    identities: dict[str, dict[str, Any]] = {}
    visual_order = {
        str(name): index
        for index, name in enumerate(render_state.get("repo_visual_order", []) or [])
        if str(name)
    }
    repos = render_state.get("repos", []) or []
    max_age = max(
        (
            int(repo.get("age_months", 0) or 0)
            for repo in repos
            if isinstance(repo, dict)
        ),
        default=1,
    )
    for fallback_index, repo in enumerate(repos):
        if not isinstance(repo, dict):
            continue
        name = str(repo.get("name") or "")
        if not name:
            continue
        order = visual_order.get(name, fallback_index)
        stars = int(repo.get("stars", 0) or 0)
        age_months = int(repo.get("age_months", 0) or 0)
        topics = repo.get("topics", []) if isinstance(repo.get("topics"), list) else []
        identities[name] = {
            "visual_index": order,
            "language": repo.get("language"),
            "archetype": order % 8,
            "star_rank_signal": _log_signal(stars, ceiling=500),
            "age_signal": _clamp01(age_months / max(1, max_age)),
            "topic_count_signal": _clamp01(len(topics) / 6.0),
        }
    return identities


def _mapping_max(
    current: dict[str, float],
    previous: dict[str, Any] | None,
) -> dict[str, float]:
    previous = previous or {}
    return {
        key: round(max(float(value), float(previous.get(key, 0.0) or 0.0)), 4)
        for key, value in current.items()
    }


def _build_evolution_state(
    render_state: dict[str, Any],
    *,
    maturity: float,
    previous_evolution_state: dict[str, Any] | None,
) -> dict[str, Any]:
    """Build a smoothed monotonic art envelope from the raw render contract."""
    previous_evolution_state = previous_evolution_state or {}
    repo_count = len(render_state.get("repos", []) or [])
    max_age = max(
        (
            int(repo.get("age_months", 0) or 0)
            for repo in render_state.get("repos", []) or []
            if isinstance(repo, dict)
        ),
        default=0,
    )
    topic_clusters = render_state.get("topic_clusters", {})
    topic_count = len(topic_clusters) if isinstance(topic_clusters, dict) else 0
    total_commits = int(render_state.get("total_commits", 0) or 0)
    total_prs = int(render_state.get("total_prs", 0) or 0)
    merged_prs = int(render_state.get("merged_pr_count", 0) or 0)
    review_count = int(render_state.get("pr_review_count", 0) or 0)
    forks = int(render_state.get("forks", 0) or 0)
    stars = int(render_state.get("stars", 0) or 0)
    releases = int(render_state.get("release_count", 0) or 0)
    total_issues = int(render_state.get("total_issues", 0) or 0)
    open_issues = int(render_state.get("open_issues_count", 0) or 0)
    contributions = int(render_state.get("contributions_to_date", 0) or 0)

    scalars = {
        "maturity": _clamp01(maturity),
        "repo_density": _log_signal(repo_count, ceiling=80),
        "repo_age_maturity": _clamp01(max_age / 72.0),
        "language_diversity_signal": max(
            _clamp01(float(render_state.get("language_count", 0) or 0) / 12.0),
            _clamp01(float(render_state.get("language_diversity", 0.0) or 0.0)),
        ),
        "topic_diversity_signal": _clamp01(topic_count / 24.0),
        "release_pressure": _log_signal(releases, ceiling=32),
        "collaboration_pressure": _log_signal(
            total_prs + merged_prs + review_count + forks,
            ceiling=1000,
        ),
        "activity_pressure": _log_signal(total_commits + contributions, ceiling=20000),
        "issue_pressure": _clamp01(open_issues / max(1, total_issues)),
        "star_pressure": _log_signal(stars, ceiling=5000),
    }
    scalars = {
        key: round(max(value, float(previous_evolution_state.get(key, 0.0) or 0.0)), 4)
        for key, value in scalars.items()
    }

    atmosphere_weights = _mapping_max(
        {
            "clear": max(scalars["star_pressure"], scalars["activity_pressure"] * 0.55),
            "cloud": max(scalars["repo_density"], scalars["issue_pressure"] * 0.65),
            "rain": max(
                scalars["collaboration_pressure"] * 0.7,
                scalars["release_pressure"],
            ),
            "storm": max(
                scalars["issue_pressure"],
                scalars["activity_pressure"] * 0.35,
            ),
        },
        previous_evolution_state.get("atmosphere_weights")
        if isinstance(previous_evolution_state.get("atmosphere_weights"), dict)
        else {},
    )
    season_weights = _mapping_max(
        {
            "spring": scalars["repo_density"],
            "summer": max(
                scalars["activity_pressure"],
                scalars["language_diversity_signal"],
            ),
            "autumn": max(scalars["release_pressure"], scalars["repo_age_maturity"]),
            "winter": max(scalars["issue_pressure"], scalars["star_pressure"] * 0.4),
        },
        previous_evolution_state.get("season_weights")
        if isinstance(previous_evolution_state.get("season_weights"), dict)
        else {},
    )
    feature_ramps = _mapping_max(
        {
            "structure": scalars["maturity"],
            "texture": max(scalars["repo_age_maturity"], scalars["activity_pressure"]),
            "network": scalars["collaboration_pressure"],
            "flora": max(scalars["repo_density"], scalars["language_diversity_signal"]),
            "release": scalars["release_pressure"],
            "weather": max(atmosphere_weights.values(), default=0.0),
        },
        previous_evolution_state.get("feature_ramps")
        if isinstance(previous_evolution_state.get("feature_ramps"), dict)
        else {},
    )

    evolution_state = dict(render_state)
    evolution_state.update(scalars)
    evolution_state["evolution_state"] = True
    evolution_state["source_contract"] = "evolution_state"
    evolution_state["atmosphere_weights"] = atmosphere_weights
    evolution_state["season_weights"] = season_weights
    evolution_state["feature_ramps"] = feature_ramps
    evolution_state["repo_identity"] = _repo_identity_map(render_state)
    return evolution_state


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
    previous_cumulative_state: dict[str, int] = {}
    previous_render_state: dict[str, Any] = {}
    previous_evolution_state: dict[str, Any] = {}
    cumulative_commit_hours: dict[int, int] = {}

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
        contributions_to_date = sum(daily_trunc.values())
        cumulative_state = {
            "stars": total_stars,
            "forks": forks_cumulative.get(day, 0),
            "watchers": _monotone_non_decreasing(
                _interpolate_scalar(curr_watchers, progress),
                previous_cumulative_state.get("watchers", 0),
            ),
            "followers": _monotone_non_decreasing(
                _interpolate_scalar(curr_followers, progress),
                previous_cumulative_state.get("followers", 0),
            ),
            "public_repos": len(repos_so_far),
            "orgs_count": _monotone_non_decreasing(
                _interpolate_scalar(curr_orgs, progress),
                previous_cumulative_state.get("orgs_count", 0),
            ),
            "total_commits": _monotone_non_decreasing(
                _interpolate_scalar(curr_total_commits, progress),
                previous_cumulative_state.get("total_commits", 0),
            ),
            "total_prs": _monotone_non_decreasing(
                _interpolate_scalar(curr_total_prs, progress),
                previous_cumulative_state.get("total_prs", 0),
            ),
            "total_issues": _monotone_non_decreasing(
                _interpolate_scalar(curr_total_issues, progress),
                previous_cumulative_state.get("total_issues", 0),
            ),
            "total_repos_contributed": _monotone_non_decreasing(
                _interpolate_scalar(curr_total_repos_contrib, progress),
                previous_cumulative_state.get("total_repos_contributed", 0),
            ),
            "network_count": _monotone_non_decreasing(
                _interpolate_scalar(curr_network, progress),
                previous_cumulative_state.get("network_count", 0),
            ),
            "public_gists": _monotone_non_decreasing(
                _interpolate_scalar(curr_gists, progress),
                previous_cumulative_state.get("public_gists", 0),
            ),
            "pr_review_count": _monotone_non_decreasing(
                _interpolate_scalar(curr_pr_review, progress),
                previous_cumulative_state.get("pr_review_count", 0),
            ),
            "release_count": len(releases_trunc),
            "merged_pr_count": len(recent_merged_prs_trunc),
            "contributions_to_date": _monotone_non_decreasing(
                contributions_to_date,
                previous_cumulative_state.get("contributions_to_date", 0),
            ),
        }
        recent_activity_state = {
            "contributions_last_year": contribs_last_year,
            "open_issues_count": open_issues_estimate,
            "issue_stats": issue_stats,
        }

        # Build metrics_dict (for ink_garden / topography)
        metrics_dict: dict[str, Any] = {
            "repos": repos_so_far,
            "stars": cumulative_state["stars"],
            "forks": cumulative_state["forks"],
            "watchers": cumulative_state["watchers"],
            "followers": cumulative_state["followers"],
            "following": _interpolate_scalar(curr_following, progress),
            "public_repos": cumulative_state["public_repos"],
            "orgs_count": cumulative_state["orgs_count"],
            "contributions_last_year": contribs_last_year,
            "total_commits": cumulative_state["total_commits"],
            "total_prs": cumulative_state["total_prs"],
            "total_issues": cumulative_state["total_issues"],
            "total_repos_contributed": cumulative_state["total_repos_contributed"],
            "open_issues_count": open_issues_estimate,
            "network_count": cumulative_state["network_count"],
            "public_gists": cumulative_state["public_gists"],
            "pr_review_count": cumulative_state["pr_review_count"],
            "languages": langs,
            "contributions_monthly": monthly_trunc,
            "contributions_daily": daily_trunc,
            "contributions_to_date": cumulative_state["contributions_to_date"],
            "label": owner,
            "account_created": ac_str,
            "issue_stats": issue_stats,
            "recent_merged_prs": recent_merged_prs_trunc,
            "merged_pr_count": cumulative_state["merged_pr_count"],
            "releases": releases_trunc,
            "release_count": cumulative_state["release_count"],
            "cumulative_state": cumulative_state,
            "recent_activity_state": recent_activity_state,
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
        cumulative_commit_hours = _allocate_histogram_delta(
            max(0, int(daily_contribs.get(day_iso, 0) or 0)),
            cumulative_commit_hours,
            metrics_dict["commit_hour_distribution"],
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

        render_state = _build_render_state(
            metrics_dict,
            previous_render_state=previous_render_state,
            cumulative_commit_hours=cumulative_commit_hours,
        )
        metrics_dict["render_state"] = render_state

        # Timelapse frames should never regress once cumulative signals have appeared.
        maturity = max(previous_maturity, compute_maturity(render_state))
        evolution_state = _build_evolution_state(
            render_state,
            maturity=maturity,
            previous_evolution_state=previous_evolution_state,
        )
        metrics_dict["evolution_state"] = evolution_state
        world_state = compute_world_state(evolution_state)

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
        previous_cumulative_state = cumulative_state.copy()
        previous_render_state = render_state
        previous_evolution_state = evolution_state

    logger.info(
        "Built {} snapshots; maturity range {:.3f} → {:.3f}",
        len(snapshots),
        snapshots[0].maturity if snapshots else 0,
        snapshots[-1].maturity if snapshots else 0,
    )
    validate_snapshot_monotonic_contract(snapshots)
    return snapshots


def validate_snapshot_monotonic_contract(snapshots: list[DailySnapshot]) -> None:
    """Raise when cumulative profile-history channels regress across snapshots."""

    if len(snapshots) < 2:
        return

    previous = snapshots[0]
    previous_cumulative = cast(
        "dict[str, int]",
        previous.metrics_dict.get("cumulative_state", {}),
    )
    for current in snapshots[1:]:
        current_cumulative = cast(
            "dict[str, int]",
            current.metrics_dict.get("cumulative_state", {}),
        )
        for key in MONOTONIC_CUMULATIVE_KEYS:
            current_value = int(
                current_cumulative.get(key, current.metrics_dict.get(key, 0)) or 0
            )
            previous_value = int(
                previous_cumulative.get(key, previous.metrics_dict.get(key, 0)) or 0
            )
            if current_value < previous_value:
                raise ValueError(
                    f"Cumulative snapshot channel {key!r} regressed on "
                    f"{current.day.isoformat()}: {previous_value} -> {current_value}"
                )
        if current.maturity < previous.maturity:
            raise ValueError(
                f"Snapshot maturity regressed on {current.day.isoformat()}: "
                f"{previous.maturity:.4f} -> {current.maturity:.4f}"
            )

        previous_render_state = cast(
            "dict[str, Any]",
            previous.metrics_dict.get("render_state", {}),
        )
        current_render_state = cast(
            "dict[str, Any]",
            current.metrics_dict.get("render_state", {}),
        )
        if previous_render_state and current_render_state:
            for key in RENDER_STATE_SCALAR_KEYS:
                current_value = float(current_render_state.get(key, 0) or 0)
                previous_value = float(previous_render_state.get(key, 0) or 0)
                if current_value < previous_value:
                    raise ValueError(
                        f"Render-state scalar {key!r} regressed on "
                        f"{current.day.isoformat()}: {previous_value} -> {current_value}"
                    )

            for key in RENDER_STATE_MAPPING_KEYS:
                current_mapping = cast(
                    "dict[str | int, int | float]",
                    current_render_state.get(key, {}),
                )
                previous_mapping = cast(
                    "dict[str | int, int | float]",
                    previous_render_state.get(key, {}),
                )
                for item_key in set(current_mapping.keys()) | set(previous_mapping.keys()):
                    current_value = float(current_mapping.get(item_key, 0) or 0)
                    previous_value = float(previous_mapping.get(item_key, 0) or 0)
                    if current_value < previous_value:
                        raise ValueError(
                            f"Render-state mapping {key!r}[{item_key!r}] regressed on "
                            f"{current.day.isoformat()}: {previous_value} -> {current_value}"
                        )

            for key in ("releases", "recent_merged_prs", "repos"):
                current_len = len(current_render_state.get(key, []) or [])
                previous_len = len(previous_render_state.get(key, []) or [])
                if current_len < previous_len:
                    raise ValueError(
                        f"Render-state sequence {key!r} regressed on "
                        f"{current.day.isoformat()}: {previous_len} -> {current_len}"
                    )

            previous_repos = {
                str(repo.get("name")): repo
                for repo in previous_render_state.get("repos", [])
                if isinstance(repo, dict) and repo.get("name")
            }
            current_repos = {
                str(repo.get("name")): repo
                for repo in current_render_state.get("repos", [])
                if isinstance(repo, dict) and repo.get("name")
            }
            for repo_name in previous_repos.keys() & current_repos.keys():
                for repo_key in ("stars", "forks", "age_months"):
                    current_value = int(current_repos[repo_name].get(repo_key, 0) or 0)
                    previous_value = int(previous_repos[repo_name].get(repo_key, 0) or 0)
                    if current_value < previous_value:
                        raise ValueError(
                            f"Render-state repo {repo_name!r} key {repo_key!r} regressed on "
                            f"{current.day.isoformat()}: {previous_value} -> {current_value}"
                        )

        previous_evolution_state = cast(
            "dict[str, Any]",
            previous.metrics_dict.get("evolution_state", {}),
        )
        current_evolution_state = cast(
            "dict[str, Any]",
            current.metrics_dict.get("evolution_state", {}),
        )
        if previous_evolution_state and current_evolution_state:
            for key in EVOLUTION_STATE_SCALAR_KEYS:
                current_value = float(current_evolution_state.get(key, 0) or 0)
                previous_value = float(previous_evolution_state.get(key, 0) or 0)
                if current_value < previous_value:
                    raise ValueError(
                        f"Evolution-state scalar {key!r} regressed on "
                        f"{current.day.isoformat()}: {previous_value} -> {current_value}"
                    )

            for key in EVOLUTION_STATE_MAPPING_KEYS:
                current_mapping = cast(
                    "dict[str, int | float]",
                    current_evolution_state.get(key, {}),
                )
                previous_mapping = cast(
                    "dict[str, int | float]",
                    previous_evolution_state.get(key, {}),
                )
                for item_key in set(current_mapping.keys()) | set(previous_mapping.keys()):
                    current_value = float(current_mapping.get(item_key, 0) or 0)
                    previous_value = float(previous_mapping.get(item_key, 0) or 0)
                    if current_value < previous_value:
                        raise ValueError(
                            f"Evolution-state mapping {key!r}[{item_key!r}] regressed on "
                            f"{current.day.isoformat()}: {previous_value} -> {current_value}"
                        )

            previous_identity = cast(
                "dict[str, dict[str, Any]]",
                previous_evolution_state.get("repo_identity", {}),
            )
            current_identity = cast(
                "dict[str, dict[str, Any]]",
                current_evolution_state.get("repo_identity", {}),
            )
            for repo_name in previous_identity.keys() & current_identity.keys():
                for identity_key in ("visual_index", "language", "archetype"):
                    if (
                        current_identity[repo_name].get(identity_key)
                        != previous_identity[repo_name].get(identity_key)
                    ):
                        raise ValueError(
                            f"Evolution-state repo identity {repo_name!r} key "
                            f"{identity_key!r} changed on {current.day.isoformat()}"
                        )
        previous = current
        previous_cumulative = current_cumulative


# ---------------------------------------------------------------------------
# Adaptive frame sampling
# ---------------------------------------------------------------------------


def _sampling_metrics(snapshot: DailySnapshot) -> dict[str, Any]:
    evolution_state = snapshot.metrics_dict.get("evolution_state")
    if isinstance(evolution_state, dict):
        return evolution_state
    render_state = snapshot.metrics_dict.get("render_state")
    if isinstance(render_state, dict):
        return render_state
    return snapshot.metrics_dict


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
    previous_metrics = _sampling_metrics(previous)
    current_metrics = _sampling_metrics(current)
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


def _sample_gap_score(
    snapshots: list[DailySnapshot],
    transition_scores: list[float],
    *,
    left: int,
    right: int,
) -> float:
    """Score a sampled gap by visual jump first, elapsed time second."""
    if right <= left + 1:
        return -1.0
    span = right - left
    visual_jump = _transition_score(snapshots[left], snapshots[right])
    interior_peak = max(transition_scores[left + 1 : right], default=0.0)
    temporal_jump = span / max(1, len(snapshots) - 1)
    return max(visual_jump, interior_peak) + temporal_jump * 2.0


def _best_gap_split_index(
    snapshots: list[DailySnapshot],
    transition_scores: list[float],
    *,
    left: int,
    right: int,
) -> int | None:
    """Pick the real day that best halves a sampled visual-state jump."""
    if right <= left + 1:
        return None

    midpoint = (left + right) / 2.0
    candidates = range(left + 1, right)
    return min(
        candidates,
        key=lambda index: (
            max(
                _transition_score(snapshots[left], snapshots[index]),
                _transition_score(snapshots[index], snapshots[right]),
            ),
            abs(
                _transition_score(snapshots[left], snapshots[index])
                - _transition_score(snapshots[index], snapshots[right])
            ),
            -transition_scores[index],
            abs(index - midpoint),
            index,
        ),
    )


def sample_frames(
    snapshots: list[DailySnapshot],
    *,
    max_frames: int = DEFAULT_PUBLISHED_MAX_FRAMES,
) -> list[DailySnapshot]:
    """Select representative snapshots without collapsing the published frame budget.

    Strategy:
    1. Always include the first and last day.
    2. Reserve chronological real-day anchors first so the render cost and
       narrative stay distributed across the whole account history.
    3. Reserve a bounded set of high-transition days so events survive.
    4. Spend remaining slots splitting the largest adjacent visual jump.
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
    selected_indices: set[int] = {0, n - 1}

    if interior_slots <= 3:
        anchor_slots = 0
        transition_slots = min(
            interior_slots,
            max(1, math.ceil(interior_slots * 0.67)),
        )
    else:
        anchor_slots = min(
            interior_slots,
            max(1, round(interior_slots * 0.45)),
        )
        remaining_after_anchors = max(0, interior_slots - anchor_slots)
        transition_slots = min(
            remaining_after_anchors,
            max(1, round(interior_slots * 0.30)) if remaining_after_anchors else 0,
        )

    if anchor_slots > 0:
        total_anchor_count = anchor_slots + 2
        for anchor_step in range(1, total_anchor_count - 1):
            anchor_index = int(
                round(anchor_step * (n - 1) / max(1, total_anchor_count - 1))
            )
            anchor_index = max(1, min(n - 2, anchor_index))
            selected_indices.add(anchor_index)

    if transition_slots > 0:
        for slot_index in range(transition_slots):
            start = 1 + (slot_index * interior_count) // transition_slots
            stop = 1 + ((slot_index + 1) * interior_count) // transition_slots
            if stop <= start:
                stop = min(n - 1, start + 1)
            bucket_span = max(1, stop - start)
            bucket_indices = range(start, stop)
            bucket_reference = snapshots[start - 1]
            bucket_midpoint = start + (bucket_span - 1) / 2.0
            best_index = max(
                bucket_indices,
                key=lambda index: (
                    transition_scores[index]
                    + _transition_score(bucket_reference, snapshots[index])
                    + 0.05 * (1.0 - abs(index - bucket_midpoint) / bucket_span),
                    -abs(index - bucket_midpoint),
                    -index,
                ),
            )
            selected_indices.add(best_index)

    while len(selected_indices) < max_frames:
        ordered = sorted(selected_indices)
        best_gap: tuple[int, int] | None = None
        best_score = -1.0
        for left, right in zip(ordered, ordered[1:]):
            score = _sample_gap_score(
                snapshots,
                transition_scores,
                left=left,
                right=right,
            )
            if score > best_score:
                best_gap = (left, right)
                best_score = score
        if best_gap is None or best_score < 0:
            break

        left, right = best_gap
        split_index = _best_gap_split_index(
            snapshots,
            transition_scores,
            left=left,
            right=right,
        )
        if split_index is None or split_index in selected_indices:
            break
        selected_indices.add(split_index)

    ordered_indices = sorted(selected_indices)
    if len(ordered_indices) > max_frames:
        protected = {0, n - 1}
        interior_selected = [
            index for index in ordered_indices if index not in protected
        ]
        ranked_interior = sorted(
            interior_selected,
            key=lambda index: (transition_scores[index], index),
            reverse=True,
        )
        keep_interior = sorted(ranked_interior[: interior_slots])
        ordered_indices = [0, *keep_interior, n - 1]

    result = [snapshots[index] for index in ordered_indices]

    logger.info(
        "Sampled {} frames from {} days (first: {}, last: {})",
        len(result),
        len(snapshots),
        result[0].day if result else "N/A",
        result[-1].day if result else "N/A",
    )
    return result
