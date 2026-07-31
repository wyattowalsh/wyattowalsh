"""Live metrics / history contracts and normalization for living-art."""
from __future__ import annotations

import math
from collections import defaultdict
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

_REPO_RECENCY_BANDS = (
    ("fresh", 3),
    ("recent", 12),
    ("established", 36),
    ("legacy", math.inf),
)

# ---------------------------------------------------------------------------
# Live metrics normalization
# ---------------------------------------------------------------------------


class _SignalContractModel(BaseModel):
    model_config = ConfigDict(extra="ignore")


class ContributionCalendarEntry(_SignalContractModel):
    date: str
    count: int = 0


class ContributionDailyEntry(_SignalContractModel):
    date: str
    count: int = 0


class RepoSignalEntry(_SignalContractModel):
    name: str
    language: str | None = None
    stars: int | None = 0
    forks: int | None = 0
    topics: list[str] = Field(default_factory=list)
    description: str | None = ""
    updated_at: str | None = None
    date: str | None = None
    age_months: int | None = None


class TimelineEventEntry(_SignalContractModel):
    name: str | None = None
    date: str | None = None


class StarVelocitySignal(_SignalContractModel):
    recent_rate: float = 0.0
    peak_rate: float = 0.0
    trend: str = "stable"


class ContributionStreakSignal(_SignalContractModel):
    current_streak_months: int = 0
    longest_streak_months: int = 0
    streak_active: bool = False


class MetricsSnapshotContract(_SignalContractModel):
    label: str | None = None
    stars: int | None = 0
    forks: int | None = 0
    watchers: int | None = 0
    followers: int | None = 0
    following: int | None = 0
    public_repos: int | None = 0
    public_gists: int | None = 0
    orgs_count: int | None = 0
    contributions_last_year: int | None = 0
    total_commits: int | None = 0
    total_prs: int | None = 0
    total_issues: int | None = 0
    total_repos_contributed: int | None = 0
    open_issues_count: int | None = 0
    network_count: int | None = 0
    pr_review_count: int | None = 0
    account_created: str | None = None
    languages: dict[str, int] = Field(default_factory=dict)
    top_repos: list[RepoSignalEntry] = Field(default_factory=list)
    repos: list[RepoSignalEntry] = Field(default_factory=list)
    contributions_calendar: list[ContributionCalendarEntry] = Field(
        default_factory=list
    )
    contributions_monthly: dict[str, int] = Field(default_factory=dict)
    contributions_daily: dict[str, int] = Field(default_factory=dict)
    recent_merged_prs: list[dict[str, Any]] = Field(default_factory=list)
    issue_stats: dict[str, Any] = Field(default_factory=dict)
    commit_hour_distribution: dict[str, int] = Field(default_factory=dict)
    commit_hour_distribution_scope: str | None = None
    commit_hour_distribution_sample_size: int = 0
    releases: list[dict[str, Any]] = Field(default_factory=list)
    releases_scope: str | None = None
    releases_repo_count: int = 0
    traffic_views_14d: int | None = 0
    traffic_unique_visitors_14d: int | None = 0
    traffic_clones_14d: int | None = 0
    traffic_unique_cloners_14d: int | None = 0
    traffic_top_referrers: list[str] = Field(default_factory=list)
    star_velocity: StarVelocitySignal | None = None
    contribution_streaks: ContributionStreakSignal | None = None


class HistorySnapshotContract(_SignalContractModel):
    account_created: str | None = None
    repos: list[RepoSignalEntry] = Field(default_factory=list)
    stars: list[TimelineEventEntry] = Field(default_factory=list)
    forks: list[TimelineEventEntry] = Field(default_factory=list)
    contributions_monthly: dict[str, int] = Field(default_factory=dict)
    contributions_daily: dict[str, int] = Field(default_factory=dict)
    current_metrics: dict[str, Any] = Field(default_factory=dict)
    recent_merged_prs: list[dict[str, Any]] = Field(default_factory=list)
    issue_stats: dict[str, Any] = Field(default_factory=dict)
    commit_hour_distribution: dict[str, int] = Field(default_factory=dict)
    commit_hour_distribution_scope: str | None = None
    commit_hour_distribution_sample_size: int = 0
    releases: list[dict[str, Any]] = Field(default_factory=list)
    releases_scope: str | None = None
    releases_repo_count: int = 0
    star_velocity: StarVelocitySignal | None = None
    contribution_streaks: ContributionStreakSignal | None = None


def _age_months_from_date(date_str: str | None, *, now: datetime) -> int | None:
    """Return age in months from an ISO-like timestamp, or ``None`` if invalid."""
    if not date_str:
        return None
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except ValueError:
        return None
    return max(1, (now.year - dt.year) * 12 + (now.month - dt.month))


def _repo_recency_band(age_months: int) -> str:
    """Bucket a repo age in months into a stable recency band."""
    for band, upper_bound in _REPO_RECENCY_BANDS:
        if age_months <= upper_bound:
            return band
    return "legacy"


def _build_repo_recency_bands(
    repos: Sequence[Mapping[str, Any]],
    *,
    now: datetime,
) -> dict[str, int]:
    """Aggregate repos into coarse age bands for downstream visual pacing."""
    bands = {band: 0 for band, _ in _REPO_RECENCY_BANDS}
    for repo in repos:
        age_months = repo.get("age_months")
        if not isinstance(age_months, int) or age_months <= 0:
            derived_age = _age_months_from_date(
                repo.get("date") or repo.get("updated_at"),
                now=now,
            )
            age_months = derived_age if derived_age is not None else 6
        bands[_repo_recency_band(age_months)] += 1
    return bands


def validate_live_metrics_payload(raw: Mapping[str, Any]) -> dict[str, Any]:
    """Validate and normalize the metrics payload used by living-art generators."""
    contract = MetricsSnapshotContract.model_validate(raw)
    return contract.model_dump(
        mode="python", exclude_none=True, exclude_unset=True
    )


def validate_live_history_payload(history: Mapping[str, Any]) -> dict[str, Any]:
    """Validate and normalize the history payload used by living-art generators."""
    contract = HistorySnapshotContract.model_validate(history)
    return contract.model_dump(
        mode="python", exclude_none=True, exclude_unset=True
    )


def resolve_render_metrics(metrics: Mapping[str, Any]) -> dict[str, Any]:
    """Prefer the timelapse render contract when present.

    ``evolution_state`` is the smoothed artistic envelope layered over
    ``render_state`` for canonical timelapse output.  ``render_state`` remains
    the raw monotonic data contract and the fallback for older snapshots.
    Generators retain access to stable metadata from the outer payload.
    """
    evolution_state = metrics.get("evolution_state")
    if isinstance(evolution_state, Mapping):
        resolved = dict(metrics)
        resolved.update(dict(evolution_state))
        return resolved

    render_state = metrics.get("render_state")
    if not isinstance(render_state, Mapping):
        return dict(metrics)

    resolved = dict(metrics)
    resolved.update(dict(render_state))
    return resolved


def is_monotonic_timelapse_metrics(metrics: Mapping[str, Any]) -> bool:
    """Return ``True`` when metrics come from the canonical timelapse contract.

    Timelapse snapshots either carry the outer ``render_state`` wrapper or are
    already resolved down to the monotonic payload. In both cases we expose a
    ``cumulative_state`` envelope that standalone live renders do not have.
    """
    return isinstance(metrics.get("render_state"), Mapping) or isinstance(
        metrics.get("cumulative_state"),
        Mapping,
    )


def normalize_live_metrics(
    raw: Mapping[str, Any],
    *,
    owner: str | None = None,
    history: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Transform ``fetch_metrics.collect()`` output into the shape generators expect.

    The art generators (ink_garden, topography) consume a metrics dict shaped
    like the mock profiles in ``_dev_profiles.py``.  Live API data differs in
    key names and structure.  This function bridges the gap.
    """
    validated_history = (
        validate_live_history_payload(history) if history is not None else None
    )
    metrics: dict[str, Any] = validate_live_metrics_payload(raw)
    now = datetime.now(tz=UTC)

    # 0. Coerce None numeric fields to 0 (GraphQL fields are None without a token)
    _NUMERIC_KEYS = (
        "stars", "forks", "watchers", "followers", "following",
        "public_repos", "orgs_count", "contributions_last_year",
        "total_commits", "total_prs", "total_issues",
        "total_repos_contributed", "open_issues_count", "network_count",
        "pr_review_count",
    )
    for k in _NUMERIC_KEYS:
        if k in metrics and metrics[k] is None:
            metrics[k] = 0

    # 1. top_repos → repos with age_months
    if "top_repos" in metrics and "repos" not in metrics:
        # Build a creation-date lookup from history if available
        creation_dates: dict[str, str] = {}
        if validated_history and validated_history.get("repos"):
            for r in validated_history["repos"]:
                if r.get("name") and r.get("date"):
                    creation_dates[r["name"]] = r["date"]

        repos: list[dict[str, Any]] = []
        for r in metrics.pop("top_repos"):
            repo: dict[str, Any] = {
                "name": r["name"],
                "language": r.get("language"),
                "stars": r.get("stars", 0),
                "forks": r.get("forks", 0),
                "topics": r.get("topics", []),
                "description": r.get("description", ""),
            }
            # Prefer history creation date; fall back to updated_at
            date_str = creation_dates.get(r["name"]) or r.get("updated_at")
            if date_str:
                repo["age_months"] = _age_months_from_date(date_str, now=now) or 6
            else:
                repo["age_months"] = 6
            repos.append(repo)
        metrics["repos"] = repos

    if metrics.get("repos"):
        creation_dates = {}
        if validated_history and validated_history.get("repos"):
            creation_dates = {
                repo["name"]: repo["date"]
                for repo in validated_history["repos"]
                if repo.get("name") and repo.get("date")
            }
        for repo in metrics["repos"]:
            if repo.get("age_months"):
                continue
            repo_date = (
                repo.get("date")
                or creation_dates.get(repo.get("name", ""))
                or repo.get("updated_at")
            )
            repo["age_months"] = _age_months_from_date(repo_date, now=now) or 6

    # 2. contributions_calendar → contributions_monthly / contributions_daily
    if "contributions_daily" not in metrics and "contributions_calendar" in metrics:
        daily: dict[str, int] = {}
        for entry in metrics["contributions_calendar"]:
            date_str = entry.get("date", "")
            if date_str:
                daily[date_str] = int(entry.get("count", 0) or 0)
        metrics["contributions_daily"] = dict(sorted(daily.items()))

    if "contributions_monthly" not in metrics:
        monthly: dict[str, int] = defaultdict(int)
        if metrics.get("contributions_daily"):
            for date_str, count in metrics["contributions_daily"].items():
                if len(date_str) >= 7:
                    monthly[date_str[:7]] += int(count or 0)
        elif "contributions_calendar" in metrics:
            for entry in metrics["contributions_calendar"]:
                date_str = entry.get("date", "")
                if len(date_str) >= 7:
                    monthly[date_str[:7]] += int(entry.get("count", 0) or 0)
        metrics["contributions_monthly"] = dict(sorted(monthly.items()))

    # 3. Merge richer history data when available
    if validated_history:
        if "account_created" not in metrics and "account_created" in validated_history:
            metrics["account_created"] = validated_history["account_created"]
        if validated_history.get("contributions_daily"):
            metrics["contributions_daily"] = validated_history[
                "contributions_daily"
            ]
        # Prefer history's multi-year contributions_monthly over single-year calendar
        if validated_history.get("contributions_monthly"):
            metrics["contributions_monthly"] = validated_history[
                "contributions_monthly"
            ]

    # 4. Label
    if "label" not in metrics and owner:
        metrics["label"] = owner

    # 5. Topic aggregation
    topic_counts: dict[str, int] = defaultdict(int)
    for repo in metrics.get("repos", []):
        for topic in repo.get("topics", []):
            topic_counts[topic] += 1
    metrics["topic_clusters"] = dict(
        sorted(topic_counts.items(), key=lambda kv: kv[1], reverse=True)
    )

    # 6. Language diversity (Shannon entropy in bits)
    lang_bytes = metrics.get("languages", {})
    if lang_bytes:
        total = sum(lang_bytes.values())
        if total > 0:
            entropy = 0.0
            for count in lang_bytes.values():
                if count > 0:
                    p = count / total
                    entropy -= p * math.log2(p)
            metrics["language_diversity"] = round(entropy, 4)
        else:
            metrics["language_diversity"] = 0.0
        metrics["language_count"] = len(lang_bytes)
    else:
        metrics["language_diversity"] = 0.0
        metrics["language_count"] = 0

    metrics["repo_recency_bands"] = _build_repo_recency_bands(
        metrics.get("repos", []),
        now=now,
    )

    # 7. Pass through new fields from fetch_metrics and fetch_history
    _PASSTHROUGH_KEYS = (
        "recent_merged_prs", "issue_stats", "pr_review_count",
        "commit_hour_distribution",
        "commit_hour_distribution_scope",
        "commit_hour_distribution_sample_size",
        "releases",
        "releases_scope",
        "releases_repo_count",
        "star_velocity", "contribution_streaks",
        "public_gists",
        "traffic_views_14d", "traffic_unique_visitors_14d",
        "traffic_clones_14d", "traffic_unique_cloners_14d",
        "traffic_top_referrers",
    )
    if validated_history:
        for key in _PASSTHROUGH_KEYS:
            if key not in metrics and key in validated_history:
                metrics[key] = validated_history[key]

    return metrics
