"""
Shared utilities for generative art prototypes.
Noise, color science, hash utilities, profiles, constants,
and common math helpers used by generative/animated art.
"""
from __future__ import annotations

import calendar
import hashlib
import math
import re
from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, date as dt_date
from datetime import datetime, timedelta
from typing import Any

import numpy as np
from pydantic import BaseModel, ConfigDict, Field

# Canvas
WIDTH = 800
HEIGHT = 800
CX = WIDTH / 2
CY = HEIGHT / 2

# Language → hue mapping
LANG_HUES = {
    "Python": 215, "JavaScript": 48, "TypeScript": 220, "Java": 8,
    "C++": 285, "C": 255, "Go": 178, "Rust": 22, "Ruby": 348,
    "Shell": 118, "HTML": 28, "CSS": 198, "Jupyter Notebook": 168, None: 155,
}


_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_YYYY_MM_RE = re.compile(r"^\d{4}-\d{2}$")
_MONTH_ONLY_RE = re.compile(r"^\d{1,2}$")
_SEASONS = ("spring", "summer", "autumn", "winter")
_DAYLIGHT_HUE_DRIFT_ANCHORS = (
    (0.0, -18.0),
    (4.0, -14.0),
    (7.0, 20.0),
    (12.0, 2.0),
    (17.0, 14.0),
    (20.0, 18.0),
    (24.0, -18.0),
)
_REPO_RECENCY_BANDS = (
    ("fresh", 3),
    ("recent", 12),
    ("established", 36),
    ("legacy", math.inf),
)


def _as_date(value: Any) -> dt_date | None:
    """Convert common date representations into ``datetime.date``."""
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, dt_date):
        return value
    if not isinstance(value, str):
        return None
    s = value.strip()
    if not s:
        return None
    if _ISO_DATE_RE.match(s):
        try:
            return dt_date.fromisoformat(s)
        except ValueError:
            return None
    if _YYYY_MM_RE.match(s):
        try:
            year, month = map(int, s.split("-"))
            return dt_date(year, month, 1)
        except ValueError:
            return None
    if "T" in s:
        try:
            return datetime.fromisoformat(s.replace("Z", "+00:00")).date()
        except ValueError:
            return None
    return None


def normalize_timeline_window(
    dated_events: Sequence[Any] | None = None,
    history: Mapping[str, Any] | None = None,
    *,
    fallback_days: int = 365,
    now: dt_date | None = None,
) -> tuple[dt_date, dt_date]:
    """Infer a normalized [start, end] window from history and dated events."""
    observed: list[dt_date] = []
    if dated_events:
        for event in dated_events:
            if isinstance(event, Mapping):
                parsed = _as_date(event.get("date"))
            else:
                parsed = _as_date(event)
            if parsed:
                observed.append(parsed)

    if history:
        for key in ("account_created",):
            parsed = _as_date(history.get(key))
            if parsed:
                observed.append(parsed)
        for collection in ("repos", "stars", "forks"):
            for item in history.get(collection, []) or []:
                if isinstance(item, Mapping):
                    parsed = _as_date(item.get("date"))
                    if parsed:
                        observed.append(parsed)
        for month_key in (history.get("contributions_monthly", {}) or {}).keys():
            parsed = _as_date(month_key)
            if parsed:
                observed.append(parsed)
        for day_key in (history.get("contributions_daily", {}) or {}).keys():
            parsed = _as_date(day_key)
            if parsed:
                observed.append(parsed)

    if observed:
        start = min(observed)
        end = max(observed)
        return (start, end if end >= start else start)

    today = now or dt_date.today()
    safe_days = max(int(fallback_days), 1)
    return today - timedelta(days=safe_days), today


def map_date_to_loop_delay(
    when: Any,
    window: tuple[dt_date, dt_date],
    *,
    duration: float,
    reveal_fraction: float = 0.93,
    easing_power: float = 1.0,
) -> float:
    """Map a real date into a loop delay in seconds, clamped to timeline window."""
    start, end = window
    if end < start:
        start, end = end, start
    parsed = _as_date(when)
    if parsed is None:
        parsed = start
    clamped = min(max(parsed, start), end)
    span_days = max((end - start).days, 1)
    frac = (clamped - start).days / span_days
    eased = frac ** max(easing_power, 0.01)
    reveal_end = max(duration, 0.0) * max(min(reveal_fraction, 1.0), 0.0)
    return round(eased * reveal_end, 3)


def _iter_months(start_year: int, start_month: int, end_year: int, end_month: int) -> list[tuple[int, int]]:
    """Yield (year, month) inclusive between start and end."""
    out: list[tuple[int, int]] = []
    year, month = start_year, start_month
    while (year, month) <= (end_year, end_month):
        out.append((year, month))
        month += 1
        if month > 12:
            month = 1
            year += 1
    return out


def _distribute_monthly_count(year: int, month: int, count: int) -> list[int]:
    """Deterministically spread monthly counts across month days."""
    days_in_month = calendar.monthrange(year, month)[1]
    count = max(int(count), 0)
    if count == 0:
        return [0] * days_in_month

    base, remainder = divmod(count, days_in_month)
    daily = [base] * days_in_month
    if remainder == 0:
        return daily

    seed = int(hashlib.sha256(f"{year:04d}-{month:02d}".encode()).hexdigest()[:8], 16)
    start = seed % days_in_month
    step = max(1, days_in_month // remainder)
    used: set[int] = set()
    idx = start
    for _ in range(remainder):
        while idx in used:
            idx = (idx + 1) % days_in_month
        used.add(idx)
        daily[idx] += 1
        idx = (idx + step) % days_in_month
    return daily


def contributions_monthly_to_daily_series(
    contributions_monthly: Mapping[str, int] | None,
    *,
    reference_year: int | None = None,
) -> dict[str, int]:
    """Expand monthly contribution buckets into deterministic per-day series."""
    if not contributions_monthly:
        return {}

    ref_year = reference_year or dt_date.today().year
    month_counts: dict[tuple[int, int], int] = {}
    for key, value in contributions_monthly.items():
        k = str(key).strip()
        if _YYYY_MM_RE.match(k):
            year, month = map(int, k.split("-"))
        elif _MONTH_ONLY_RE.match(k):
            month = int(k)
            year = ref_year
        else:
            continue
        if not (1 <= month <= 12):
            continue
        month_counts[(year, month)] = max(0, int(value or 0))

    if not month_counts:
        return {}

    (start_y, start_m) = min(month_counts.keys())
    (end_y, end_m) = max(month_counts.keys())
    daily: dict[str, int] = {}
    for year, month in _iter_months(start_y, start_m, end_y, end_m):
        distributed = _distribute_monthly_count(year, month, month_counts.get((year, month), 0))
        for day, count in enumerate(distributed, start=1):
            iso = dt_date(year, month, day).isoformat()
            daily[iso] = count
    return daily

# PROFILES moved to _dev_profiles.py


# ---------------------------------------------------------------------------
# Ecosystem maturity score
# ---------------------------------------------------------------------------

def _smoothstep(t: float) -> float:
    """Hermite ease-in-out: slow start, accelerate in middle, slow finish."""
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def _interpolate_hour_signal(
    hour: float,
    anchors: Sequence[tuple[float, float]],
) -> float:
    """Interpolate a smooth hourly signal from ordered control points."""
    wrapped_hour = hour % 24.0
    for (start_hour, start_value), (end_hour, end_value) in zip(
        anchors,
        anchors[1:],
    ):
        if start_hour <= wrapped_hour <= end_hour:
            span = max(end_hour - start_hour, 1.0)
            t = _smoothstep((wrapped_hour - start_hour) / span)
            return start_value + (end_value - start_value) * t
    return anchors[-1][1]


def _compute_daylight_hue_drift(peak_hour: int) -> float:
    """Derive a smooth hue drift so daylight does not jump between bins."""
    return round(_interpolate_hour_signal(peak_hour, _DAYLIGHT_HUE_DRIFT_ANCHORS), 3)


def _normalize_season_weights(
    raw_weights: Mapping[str, float] | None,
    *,
    default: str = "summer",
) -> dict[str, float]:
    """Normalize seasonal weights while keeping a stable four-season contract."""
    weights = {season: 0.0 for season in _SEASONS}
    if raw_weights:
        for season in _SEASONS:
            try:
                weights[season] = max(0.0, float(raw_weights.get(season, 0.0)))
            except (TypeError, ValueError):
                weights[season] = 0.0

    total = sum(weights.values())
    if total <= 0:
        weights[default if default in weights else "summer"] = 1.0
        return weights

    return {season: value / total for season, value in weights.items()}


def _weighted_hue(
    weights: Mapping[str, float],
    hue_map: Mapping[str, float],
    *,
    default: float,
) -> float:
    """Compute a circular weighted mean for hue values."""
    x = 0.0
    y = 0.0
    for season, weight in weights.items():
        if weight <= 0:
            continue
        hue = hue_map.get(season, default)
        x += math.cos(math.radians(hue)) * weight
        y += math.sin(math.radians(hue)) * weight
    if abs(x) < 1e-9 and abs(y) < 1e-9:
        return default
    return math.degrees(math.atan2(y, x)) % 360


def _seasonal_hues(
    season: str,
    season_transition_weights: Mapping[str, float] | None = None,
) -> tuple[float, float]:
    """Return accent and ground hues, blended when seasonal weights exist."""
    season_hues: dict[str, tuple[float, float]] = {
        "spring": (130, 95),
        "summer": (145, 80),
        "autumn": (40, 35),
        "winter": (220, 200),
    }
    default_accent, default_ground = season_hues.get(season, (145, 80))
    if not season_transition_weights:
        return default_accent, default_ground

    accent_map = {name: hues[0] for name, hues in season_hues.items()}
    ground_map = {name: hues[1] for name, hues in season_hues.items()}
    return (
        _weighted_hue(season_transition_weights, accent_map, default=default_accent),
        _weighted_hue(season_transition_weights, ground_map, default=default_ground),
    )


def _compute_activity_pressure(
    metrics: Mapping[str, Any],
    *,
    energy: float,
    vitality: float,
    weather_severity: float,
) -> float:
    """Estimate present-tense activity pressure from recent contribution volume."""
    monthly = metrics.get("contributions_monthly") or {}
    if isinstance(monthly, Mapping) and monthly:
        counts = [
            max(0.0, float(value))
            for _, value in sorted(monthly.items())
            if isinstance(value, int | float)
        ]
        recent_window = counts[-3:] if counts else []
        recent_mean = sum(recent_window) / len(recent_window) if recent_window else 0.0
        baseline = sum(counts) / len(counts) if counts else 0.0
        contribution_pressure = min(1.0, math.log1p(recent_mean) / math.log1p(120))
        surge = max(0.0, recent_mean - baseline) / max(baseline, 1.0)
        surge_pressure = min(1.0, surge / 1.5)
    else:
        monthly_baseline = max(
            0.0,
            float(metrics.get("contributions_last_year", 0) or 0) / 12.0,
        )
        contribution_pressure = min(
            1.0,
            math.log1p(monthly_baseline) / math.log1p(120),
        )
        surge_pressure = 0.0

    return round(
        min(
            1.0,
            0.45 * contribution_pressure
            + 0.25 * max(0.0, min(1.0, energy))
            + 0.15 * max(0.0, min(1.0, vitality))
            + 0.10 * max(0.0, min(1.0, weather_severity))
            + 0.05 * surge_pressure,
        ),
        4,
    )


def compute_maturity(m: dict) -> float:
    """0.0 = brand new account, 1.0 = massively prolific.

    Uses a smoothstep (Hermite ease-in-out) curve so that newcomers see
    visible growth quickly and prolific accounts asymptote gracefully.
    """
    def _log(val: float, lo: float, hi: float) -> float:
        val = max(lo, min(hi, val))
        return math.log(val / lo) / math.log(hi / lo)

    repos = m.get("repos", [])
    max_age = max((r.get("age_months", 0) for r in repos), default=0)
    raw = (
        0.20 * _log(m.get("total_commits", 1), 10, 50000)
        + 0.15 * _log(m.get("stars", 1), 1, 5000)
        + 0.15 * _log(m.get("contributions_last_year", 1), 10, 4000)
        + 0.12 * _log(m.get("followers", 1), 1, 10000)
        + 0.10 * _log(max(1, len(repos)), 1, 15)
        + 0.10 * _log(max(1, max_age), 1, 120)
        + 0.10 * _log(m.get("forks", 1), 1, 1000)
        + 0.08 * _log(m.get("network_count", 1), 1, 3000)
    )
    return _smoothstep(raw)


# ---------------------------------------------------------------------------
# World State — coherent atmospheric/environmental state across all artworks
# ---------------------------------------------------------------------------


@dataclass
class WorldState:
    """Unified environmental state derived from GitHub data.

    All 4 art generators read this to produce coherent atmospherics —
    the same time-of-day lighting, weather, season, and energy level.
    """

    time_of_day: str = "day"
    """'dawn' | 'day' | 'golden' | 'night' — from commit hour distribution."""

    weather: str = "clear"
    """'clear' | 'cloudy' | 'rainy' | 'stormy' — from issue open/close ratio."""

    season: str = "summer"
    """'spring' | 'summer' | 'autumn' | 'winter' — from language distribution."""

    energy: float = 0.5
    """0.0-1.0 — from star velocity (rate of new stars)."""

    vitality: float = 0.5
    """0.0-1.0 — from contribution streak activity."""

    aurora_intensity: float = 0.0
    """0.0-1.0 — from PR merge rate."""

    daylight_hue_drift: float = 0.0
    """Continuous hue offset in degrees layered on top of time-of-day buckets."""

    weather_severity: float = 0.0
    """0.0-1.0 severity backing the coarse weather label."""

    season_transition_weights: dict[str, float] = field(default_factory=dict)
    """Normalized season blend weights used for cross-season palette shifts."""

    activity_pressure: float = 0.5
    """0.0-1.0 recent activity load derived from contributions and momentum."""

    palette: dict[str, str] = field(default_factory=dict)
    """Derived OKLCH palette: sky_top, sky_bottom, ground, accent, glow."""


# Language family groupings for season derivation
_LANG_SEASON: dict[str, str] = {
    "Python": "summer", "Jupyter Notebook": "summer",
    "JavaScript": "autumn", "TypeScript": "autumn", "HTML": "autumn", "CSS": "autumn",
    "Rust": "winter", "C": "winter", "C++": "winter", "Go": "winter",
    "Ruby": "spring", "Shell": "spring", "Java": "spring",
}


def compute_world_state(metrics: dict[str, Any]) -> WorldState:
    """Derive a unified WorldState from a metrics snapshot.

    Designed to degrade gracefully: missing data produces calm defaults
    (clear day in summer at medium energy). Works for any GitHub user.
    """
    # ── Time of day (from commit hour distribution) ──────────────
    commit_hours = metrics.get("commit_hour_distribution") or {}
    if commit_hours and isinstance(commit_hours, dict):
        try:
            peak = max(commit_hours, key=lambda k: commit_hours[k])
            peak_hour = int(peak) if isinstance(peak, str) else peak
        except (ValueError, TypeError):
            peak_hour = 12
    else:
        peak_hour = 12

    daylight_hue_drift = _compute_daylight_hue_drift(peak_hour)

    if 5 <= peak_hour <= 8:
        time_of_day = "dawn"
    elif 17 <= peak_hour <= 20:
        time_of_day = "golden"
    elif peak_hour >= 21 or peak_hour <= 4:
        time_of_day = "night"
    else:
        time_of_day = "day"

    # ── Weather (from issue stats) ───────────────────────────────
    open_issues = metrics.get("open_issues_count", 0) or 0
    issue_stats = metrics.get("issue_stats") or {}
    closed_issues = issue_stats.get("closed_count", 0) or 0
    total_issues = open_issues + closed_issues

    if total_issues == 0:
        weather = "clear"
        weather_severity = 0.0
    else:
        open_ratio = open_issues / total_issues
        issue_volume = min(1.0, total_issues / 40.0)
        weather_severity = round(
            min(1.0, open_ratio * (0.6 + 0.4 * issue_volume)),
            4,
        )
        if weather_severity < 0.15:
            weather = "clear"
        elif weather_severity < 0.35:
            weather = "cloudy"
        elif weather_severity < 0.6:
            weather = "rainy"
        else:
            weather = "stormy"

    # ── Season (from dominant language family) ────────────────────
    lang_bytes = metrics.get("languages") or {}
    if lang_bytes and isinstance(lang_bytes, dict):
        # Weight each language's season by byte count
        season_weight: dict[str, float] = defaultdict(float)
        for lang, byte_count in lang_bytes.items():
            s = _LANG_SEASON.get(lang, "summer")
            try:
                season_weight[s] += max(0.0, float(byte_count))
            except (TypeError, ValueError):
                continue
        season_transition_weights = _normalize_season_weights(season_weight)
        season = max(season_transition_weights, key=season_transition_weights.get)
    else:
        season = "summer"
        season_transition_weights = _normalize_season_weights(None)

    # ── Energy (from star velocity) ──────────────────────────────
    star_vel = metrics.get("star_velocity") or {}
    recent_rate = star_vel.get("recent_rate", 0) if isinstance(star_vel, dict) else 0
    energy = min(1.0, math.log1p(recent_rate) / math.log1p(20))

    # ── Vitality (from contribution streaks) ─────────────────────
    streaks = metrics.get("contribution_streaks") or {}
    streak_months = (
        streaks.get("current_streak_months", 0)
        if isinstance(streaks, dict)
        else 0
    )
    streak_active = (
        streaks.get("streak_active", False) if isinstance(streaks, dict) else False
    )
    vitality = (
        min(1.0, streak_months / 12.0)
        if streak_active
        else max(0.0, streak_months / 24.0)
    )

    # ── Aurora intensity (from PR merge rate) ────────────────────
    recent_prs = metrics.get("recent_merged_prs") or []
    pr_count = len(recent_prs) if isinstance(recent_prs, list) else 0
    aurora_intensity = min(1.0, pr_count / 15.0)

    activity_pressure = _compute_activity_pressure(
        metrics,
        energy=energy,
        vitality=vitality,
        weather_severity=weather_severity,
    )

    # ── Derived palette ──────────────────────────────────────────
    palette = _build_world_palette(
        time_of_day,
        weather,
        season,
        energy,
        daylight_hue_drift=daylight_hue_drift,
        weather_severity=weather_severity,
        season_transition_weights=season_transition_weights,
        activity_pressure=activity_pressure,
    )

    return WorldState(
        time_of_day=time_of_day,
        weather=weather,
        season=season,
        energy=energy,
        vitality=vitality,
        aurora_intensity=aurora_intensity,
        daylight_hue_drift=daylight_hue_drift,
        weather_severity=weather_severity,
        season_transition_weights=season_transition_weights,
        activity_pressure=activity_pressure,
        palette=palette,
    )


def _build_world_palette(
    time_of_day: str,
    weather: str,
    season: str,
    energy: float,
    *,
    daylight_hue_drift: float = 0.0,
    weather_severity: float = 0.0,
    season_transition_weights: Mapping[str, float] | None = None,
    activity_pressure: float = 0.5,
) -> dict[str, str]:
    """Build an OKLCH palette from world-state properties."""
    # Base sky hue by time of day
    sky_params: dict[str, tuple[float, float, float]] = {
        "dawn": (0.82, 0.12, 25),
        "day": (0.88, 0.04, 210),
        "golden": (0.80, 0.10, 55),
        "night": (0.18, 0.05, 250),
    }
    sky_L, sky_C, sky_H = sky_params.get(time_of_day, (0.88, 0.04, 210))
    sky_H = (sky_H + daylight_hue_drift) % 360

    # Weather modifies sky lightness and chroma
    weather_mod: dict[str, tuple[float, float]] = {
        "clear": (0.0, 0.0),
        "cloudy": (-0.08, -0.03),
        "rainy": (-0.15, -0.05),
        "stormy": (-0.25, -0.08),
    }
    dL, dC = weather_mod.get(weather, (0.0, 0.0))
    severity = max(0.0, min(1.0, weather_severity))
    sky_L = max(0.05, min(0.95, sky_L + dL - severity * 0.03))
    sky_C = max(0.0, sky_C + dC - severity * 0.015)

    # Season drives accent and ground hue, with optional transition blending
    accent_H, ground_H = _seasonal_hues(season, season_transition_weights)

    # Energy drives glow brightness
    pressure = max(0.0, min(1.0, activity_pressure))
    glow_L = min(0.92, 0.5 + energy * 0.28 + pressure * 0.07)

    return {
        "sky_top": oklch(sky_L, sky_C, sky_H),
        "sky_bottom": oklch(
            max(0.05, sky_L - 0.15),
            max(0.0, sky_C - 0.02),
            sky_H + 10,
        ),
        "ground": oklch(
            0.45 + energy * 0.08 + pressure * 0.04,
            0.06 + pressure * 0.01,
            ground_H,
        ),
        "accent": oklch(0.65 + pressure * 0.03, 0.14 + pressure * 0.02, accent_H),
        "glow": oklch(glow_L, 0.18 + pressure * 0.01, accent_H - 20),
    }


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
    releases: list[dict[str, Any]] = Field(default_factory=list)
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
    releases: list[dict[str, Any]] = Field(default_factory=list)
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
        "commit_hour_distribution", "releases",
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


# ---------------------------------------------------------------------------
# Hash utilities
# ---------------------------------------------------------------------------

def make_radial_gradient(gid: str, cx: str, cy: str, r: str,
                         stops: list[tuple[str, str, float]]) -> str:
    """Build SVG radialGradient element. stops: [(offset, color, opacity), ...]"""
    s = "".join(f'<stop offset="{o}" stop-color="{c}" stop-opacity="{a:.3f}"/>' for o, c, a in stops)
    return f'<radialGradient id="{gid}" cx="{cx}" cy="{cy}" r="{r}">{s}</radialGradient>'


def make_linear_gradient(gid: str, x1: str, y1: str, x2: str, y2: str,
                         stops: list[tuple[str, str, float]]) -> str:
    """Build SVG linearGradient element. stops: [(offset, color, opacity), ...]"""
    s = "".join(f'<stop offset="{o}" stop-color="{c}" stop-opacity="{a:.3f}"/>' for o, c, a in stops)
    return f'<linearGradient id="{gid}" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}">{s}</linearGradient>'


def parse_cli_args(argv: list[str], extra_keys: dict[str, type] | None = None) -> dict[str, str | int | bool | None]:
    """Parse common CLI args: --profile, --only, plus extras.

    Boolean flags (type=bool) are standalone (no value argument).
    """
    result: dict[str, str | int | bool | None] = {"profile": None, "only": None}
    keys: dict[str, tuple[str, type]] = {"--profile": ("profile", str), "--only": ("only", str)}
    if extra_keys:
        keys.update({f"--{k.replace('_', '-')}": (k, v) for k, v in extra_keys.items()})
    i = 0
    while i < len(argv):
        if argv[i] in keys:
            name, typ = keys[argv[i]]
            if typ is bool:
                result[name] = True
                i += 1
            elif i + 1 < len(argv):
                result[name] = typ(argv[i + 1])
                i += 2
            else:
                import sys
                print(f"Warning: flag {argv[i]} has no value, ignoring", file=sys.stderr)
                i += 1
        else:
            i += 1
    return result


def seed_hash(m: dict) -> str:
    """Deterministic SHA-256 hex digest from metrics dict."""
    s = "-".join(
        str(m.get(k, 0))
        for k in sorted(m.keys())
        if k not in ("label", "repos", "contributions_monthly")
    )
    return hashlib.sha256(s.encode()).hexdigest()


def hex_frac(h: str, a: int, b: int) -> float:
    """Extract a 0-1 float from hex slice h[a:b]."""
    return int(h[a:b], 16) / (16 ** (b - a))


def _seed_hash(seed_str: str) -> str:
    """SHA-256 hex digest of a seed string."""
    return hashlib.sha256(seed_str.encode()).hexdigest()


def _hex_slice(h: str, start: int, end: int) -> float:
    """Extract a normalized float [0, 1) from hex digest slice."""
    return int(h[start:end], 16) / (16 ** (end - start))


# ---------------------------------------------------------------------------
# OKLCH color science (pure Python, no deps)
# ---------------------------------------------------------------------------

def _linear_to_srgb(c: float) -> float:
    return 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055


def oklch(L: float, C: float, H: float) -> str:
    """Convert OKLCH to hex string. L in [0,1], C ~[0,0.4], H in degrees."""
    a = C * math.cos(math.radians(H))
    b = C * math.sin(math.radians(H))
    lc = L + 0.3963377774 * a + 0.2158037573 * b
    mc = L - 0.1055613458 * a - 0.0638541728 * b
    sc = L - 0.0894841775 * a - 1.2914855480 * b
    l_ = lc ** 3
    m_ = mc ** 3
    s_ = sc ** 3
    r = max(0, 4.0767416621 * l_ - 3.3077115913 * m_ + 0.2309699292 * s_)
    g = max(0, -1.2684380046 * l_ + 2.6097574011 * m_ - 0.3413193965 * s_)
    bv = max(0, -0.0041960863 * l_ - 0.7034186147 * m_ + 1.7076147010 * s_)
    r = max(0, min(1, _linear_to_srgb(r)))
    g = max(0, min(1, _linear_to_srgb(g)))
    bv = max(0, min(1, _linear_to_srgb(bv)))
    return f"#{int(r * 255):02x}{int(g * 255):02x}{int(bv * 255):02x}"


# ---------------------------------------------------------------------------
# Gradient noise (Perlin-like)
# ---------------------------------------------------------------------------

class Noise2D:
    """2D gradient noise with fBm support."""

    def __init__(self, seed: int = 0):
        rng = np.random.default_rng(seed)
        self.perm = np.tile(rng.permutation(256).astype(np.int32), 2)
        a = rng.uniform(0, 2 * np.pi, 256)
        self.grads = np.column_stack([np.cos(a), np.sin(a)])

    @staticmethod
    def _fade(t: float) -> float:
        return t * t * t * (t * (t * 6 - 15) + 10)

    def noise(self, x: float, y: float) -> float:
        xi = int(math.floor(x)) & 255
        yi = int(math.floor(y)) & 255
        xf = x - math.floor(x)
        yf = y - math.floor(y)
        u = self._fade(xf)
        v = self._fade(yf)
        aa = self.perm[self.perm[xi] + yi]
        ab = self.perm[self.perm[xi] + yi + 1]
        ba = self.perm[self.perm[xi + 1] + yi]
        bb = self.perm[self.perm[xi + 1] + yi + 1]
        ga = self.grads[aa % 256]
        gb = self.grads[ab % 256]
        gc = self.grads[ba % 256]
        gd = self.grads[bb % 256]
        x1 = (ga[0] * xf + ga[1] * yf) + u * ((gc[0] * (xf - 1) + gc[1] * yf) - (ga[0] * xf + ga[1] * yf))
        x2 = (gb[0] * xf + gb[1] * (yf - 1)) + u * ((gd[0] * (xf - 1) + gd[1] * (yf - 1)) - (gb[0] * xf + gb[1] * (yf - 1)))
        return x1 + v * (x2 - x1)

    def fbm(self, x: float, y: float, octaves: int = 4) -> float:
        val = 0.0
        amp = 1.0
        freq = 1.0
        total = 0.0
        for _ in range(octaves):
            val += amp * self.noise(x * freq, y * freq)
            total += amp
            amp *= 0.5
            freq *= 2
        return val / total


NOISE_PRESETS: dict[str, dict[str, float | int]] = {
    "calm": {"frequency": 0.003, "octaves": 2, "step_size": 2.5, "persistence": 0.55},
    "balanced": {
        "frequency": 0.005,
        "octaves": 4,
        "step_size": 4.0,
        "persistence": 0.5,
    },
    "terrain": {
        "frequency": 0.008,
        "octaves": 5,
        "step_size": 3.5,
        "persistence": 0.58,
    },
    "storm": {"frequency": 0.014, "octaves": 6, "step_size": 5.0, "persistence": 0.68},
}


def resolve_noise_preset(
    name: str | None = None,
    **overrides: float | int | None,
) -> dict[str, float | int]:
    """Resolve a named noise preset with optional numeric overrides."""
    preset_name = name if name in NOISE_PRESETS else "balanced"
    preset = dict(NOISE_PRESETS[preset_name])
    for key, value in overrides.items():
        if value is not None:
            preset[key] = value
    return preset


# ---------------------------------------------------------------------------
# Generative-art math helpers (shared by generative.py + animated_art.py)
# ---------------------------------------------------------------------------

def phyllotaxis_points(
    n: int,
    center_x: float,
    center_y: float,
    scale: float = 12.0,
) -> list[tuple[float, float]]:
    """Compute *n* points on a golden-angle phyllotaxis spiral.

    angle_n = n * 137.508 degrees
    radius_n = sqrt(n) * scale
    """
    golden_angle = 137.508 * (math.pi / 180.0)
    pts: list[tuple[float, float]] = []
    for i in range(1, n + 1):
        r = math.sqrt(i) * scale
        theta = i * golden_angle
        x = center_x + r * math.cos(theta)
        y = center_y + r * math.sin(theta)
        pts.append((x, y))
    return pts


def flow_field_lines(
    width: int,
    height: int,
    num_lines: int,
    steps: int = 30,
    step_size: float = 4.0,
    freq: float = 0.005,
    octaves: int = 3,
    seed: int = 42,
) -> list[list[tuple[float, float]]]:
    """Generate flow-field particle traces using trigonometric noise.

    Uses a trig-based noise approximation so no external noise library
    is required.
    """
    rng = np.random.default_rng(seed)
    lines: list[list[tuple[float, float]]] = []
    for _ in range(num_lines):
        x = float(rng.uniform(0, width))
        y = float(rng.uniform(0, height))
        trail: list[tuple[float, float]] = [(x, y)]
        for _ in range(steps):
            angle = 0.0
            amp = 1.0
            f = freq
            for _o in range(octaves):
                angle += amp * math.sin(x * f) * math.cos(y * f * 0.7)
                amp *= 0.5
                f *= 2.0
            angle *= math.pi * 2
            x += math.cos(angle) * step_size
            y += math.sin(angle) * step_size
            if x < 0 or x > width or y < 0 or y > height:
                break
            trail.append((x, y))
        if len(trail) > 2:
            lines.append(trail)
    return lines


# ---------------------------------------------------------------------------
# SVG helpers (shared by animated art modules)
# ---------------------------------------------------------------------------

def xml_escape(s: str) -> str:
    """Escape XML special characters."""
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def svg_header(width: int, height: int) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}">\n'
    )


def svg_footer() -> str:
    return "</svg>\n"


def annotation_tooltip_metadata(
    label: str,
    *,
    value: str | int | float | None = None,
    detail: str | None = None,
    tags: Sequence[str] | None = None,
    extra: Mapping[str, Any] | None = None,
) -> dict[str, str]:
    """Compose shared tooltip metadata for SVG annotations and overlays."""
    title = str(label).strip() or "annotation"
    tooltip_parts = [title]
    if value not in (None, ""):
        tooltip_parts.append(f"{value}")
    if detail:
        detail_text = str(detail).strip()
        if detail_text:
            tooltip_parts.append(detail_text)
    tag_text = ", ".join(
        str(tag).strip() for tag in (tags or []) if str(tag).strip()
    )
    if tag_text:
        tooltip_parts.append(f"tags: {tag_text}")

    tooltip = " · ".join(tooltip_parts)
    metadata = {
        "aria-label": tooltip,
        "data-title": title,
        "data-tooltip": tooltip,
    }
    if value not in (None, ""):
        metadata["data-value"] = f"{value}"
    if tag_text:
        metadata["data-tags"] = tag_text
    for key, raw_value in (extra or {}).items():
        if raw_value in (None, ""):
            continue
        attr_name = (
            key
            if key.startswith(("data-", "aria-"))
            else f"data-{key.replace('_', '-')}"
        )
        metadata[attr_name] = str(raw_value)
    return metadata


def sparkline_svg(
    values: Sequence[int | float],
    *,
    width: int = 120,
    height: int = 32,
    stroke: str = "currentColor",
    stroke_width: float = 1.5,
    fill: str = "none",
    padding: float = 2.0,
    label: str | None = None,
) -> str:
    """Render a compact sparkline SVG with optional tooltip metadata."""
    numeric_values = [
        float(value) for value in values if isinstance(value, int | float)
    ]
    if not numeric_values:
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
            f'width="{width}" height="{height}"></svg>'
        )

    min_value = min(numeric_values)
    max_value = max(numeric_values)
    inner_width = max(width - padding * 2, 1.0)
    inner_height = max(height - padding * 2, 1.0)
    value_span = max(max_value - min_value, 1e-9)

    points: list[str] = []
    for idx, value in enumerate(numeric_values):
        if len(numeric_values) == 1:
            x = padding + inner_width / 2
        else:
            x = padding + inner_width * (idx / (len(numeric_values) - 1))
        if math.isclose(min_value, max_value):
            y = padding + inner_height / 2
        else:
            y = padding + inner_height * (1.0 - ((value - min_value) / value_span))
        points.append(f"{x:.2f},{y:.2f}")

    metadata = (
        annotation_tooltip_metadata(
            label,
            value=f"{numeric_values[-1]:g}",
            detail=f"range {min_value:g}-{max_value:g}",
        )
        if label
        else {}
    )
    attrs = "".join(
        f' {key}="{xml_escape(value)}"' for key, value in metadata.items()
    )
    title = (
        f"<title>{xml_escape(metadata['data-tooltip'])}</title>"
        if metadata
        else ""
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}"{attrs}>'
        f"{title}"
        f'<polyline fill="{fill}" stroke="{stroke}" stroke-width="{stroke_width}" '
        f'stroke-linecap="round" stroke-linejoin="round" '
        f'points="{" ".join(points)}"/>'
        f"</svg>"
    )


def hsl_to_hex(h: float, s: float, lightness: float) -> str:
    """Convert HSL (all 0..1) to hex colour string."""
    import colorsys
    r, g, b = colorsys.hls_to_rgb(h, lightness, s)
    return f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}"


def lerp_color(hex1: str, hex2: str, t: float) -> str:
    """Linearly interpolate between two hex colours."""
    r1, g1, b1 = int(hex1[1:3], 16), int(hex1[3:5], 16), int(hex1[5:7], 16)
    r2, g2, b2 = int(hex2[1:3], 16), int(hex2[3:5], 16), int(hex2[5:7], 16)
    r = int(r1 + (r2 - r1) * t)
    g = int(g1 + (g2 - g1) * t)
    b = int(b1 + (b2 - b1) * t)
    return f"#{max(0, min(255, r)):02x}{max(0, min(255, g)):02x}{max(0, min(255, b)):02x}"


# ---------------------------------------------------------------------------
# SVG filter & pattern library (shared across all generators)
# ---------------------------------------------------------------------------


def atmospheric_haze_filter(filter_id: str, intensity: float = 0.5) -> str:
    """Gaussian blur + desaturation for atmospheric perspective / depth-of-field.

    *intensity* 0.0-1.0 controls blur radius and desaturation amount.
    Apply to background elements to create depth.
    """
    blur = round(0.3 + intensity * 1.5, 2)
    desat = round(1.0 - intensity * 0.4, 3)  # 1.0 = full color, 0.6 = muted
    return (
        f'<filter id="{filter_id}" x="-5%" y="-5%" width="110%" height="110%">'
        f'<feGaussianBlur in="SourceGraphic" stdDeviation="{blur}" result="blur"/>'
        f'<feColorMatrix in="blur" type="saturate" values="{desat}"/>'
        f'</filter>'
    )


def volumetric_glow_filter(filter_id: str, radius: float = 3.0) -> str:
    """Soft radial glow via blur + luminance composite.

    Use on fireflies, bioluminescent elements, aurora highlights.
    """
    return (
        f'<filter id="{filter_id}" x="-20%" y="-20%" width="140%" height="140%">'
        f'<feGaussianBlur in="SourceGraphic" stdDeviation="{radius:.1f}" result="glow"/>'
        f'<feMerge><feMergeNode in="glow"/><feMergeNode in="SourceGraphic"/></feMerge>'
        f'</filter>'
    )


def aurora_filter(filter_id: str) -> str:
    """Ethereal aurora effect: heavy blur + slight color shift.

    Apply to aurora band paths for soft, luminous appearance.
    """
    return (
        f'<filter id="{filter_id}" x="-10%" y="-30%" width="120%" height="160%">'
        f'<feGaussianBlur in="SourceGraphic" stdDeviation="4 8" result="soft"/>'
        f'<feColorMatrix in="soft" type="saturate" values="1.3" result="vivid"/>'
        f'<feMerge><feMergeNode in="vivid"/><feMergeNode in="SourceGraphic"/></feMerge>'
        f'</filter>'
    )


def rain_pattern(pattern_id: str, intensity: float = 0.5, seed: int = 0) -> str:
    """SVG pattern of angled rain drops.

    *intensity* 0.0-1.0 controls drop count and opacity.
    """
    rng_val = seed * 7919
    opacity = round(0.15 + intensity * 0.3, 3)
    pw, ph = 30, 40
    drops: list[str] = []
    n_drops = max(2, min(8, int(3 + intensity * 5)))
    for i in range(n_drops):
        x = ((rng_val + i * 137) % pw)
        y = ((rng_val + i * 211) % ph)
        length = round(4 + intensity * 6, 1)
        drops.append(
            f'<line x1="{x}" y1="{y}" x2="{x - 1.5}" y2="{y + length}" '
            f'stroke="#8ab4d0" stroke-width="0.4" opacity="{opacity}" stroke-linecap="round"/>'
        )
    return (
        f'<pattern id="{pattern_id}" width="{pw}" height="{ph}" patternUnits="userSpaceOnUse">'
        + "".join(drops)
        + "</pattern>"
    )


def snow_pattern(pattern_id: str, density: float = 0.5, seed: int = 0) -> str:
    """SVG pattern of snowflakes (small circles and star shapes).

    *density* 0.0-1.0 controls flake count.
    """
    rng_val = seed * 6271
    pw, ph = 40, 40
    flakes: list[str] = []
    n_flakes = max(2, min(10, int(3 + density * 7)))
    for i in range(n_flakes):
        x = ((rng_val + i * 173) % pw)
        y = ((rng_val + i * 251) % ph)
        r = round(0.5 + (i % 3) * 0.3, 2)
        opacity = round(0.3 + (i % 4) * 0.1, 2)
        flakes.append(
            f'<circle cx="{x}" cy="{y}" r="{r}" fill="#e8f0ff" opacity="{opacity}"/>'
        )
    return (
        f'<pattern id="{pattern_id}" width="{pw}" height="{ph}" patternUnits="userSpaceOnUse">'
        + "".join(flakes)
        + "</pattern>"
    )


def lightning_path(x: float, y: float, length: float, seed: int = 0) -> str:
    """Generate a jagged lightning bolt SVG path starting at (x, y).

    Returns an SVG ``<path>`` element string with bright white stroke.
    """
    rng_val = seed * 3571
    pts = [(x, y)]
    cx, cy = x, y
    segments = max(3, min(8, int(length / 15)))
    seg_len = length / segments
    for i in range(segments):
        dx = ((rng_val + i * 137) % 20 - 10)
        cy += seg_len
        cx += dx
        pts.append((cx, cy))
        # Branch with 30% probability
        if (rng_val + i) % 3 == 0 and i < segments - 1:
            bx = cx + ((rng_val + i * 97) % 16 - 8)
            by = cy + seg_len * 0.5
            pts.append((bx, by))
            pts.append((cx, cy))  # return to main bolt
    d = "M" + " L".join(f"{px:.1f},{py:.1f}" for px, py in pts)
    return (
        f'<path d="{d}" fill="none" stroke="#f0f0ff" stroke-width="1.2" '
        f'opacity="0.85" stroke-linecap="round" stroke-linejoin="round"/>'
    )


def weather_overlay_elements(
    world: WorldState,
    width: int = 800,
    height: int = 800,
    seed: int = 0,
) -> list[str]:
    """Generate SVG elements for weather effects based on WorldState.

    Returns a list of SVG element strings to insert into the artwork.
    Includes filter defs and visual elements (rain drops, clouds, lightning, snow).
    """
    parts: list[str] = []

    if world.weather == "clear":
        # Sunbeams from upper-left
        beam_opacity = 0.08 + world.energy * 0.06
        if world.time_of_day != "night":
            parts.append(
                f'<ellipse cx="{width * 0.12}" cy="{height * -0.02}" '
                f'rx="{width * 0.9}" ry="{height * 0.45}" '
                f'fill="url(#weatherSunGlow)" opacity="{beam_opacity:.3f}"/>'
            )
        return parts

    if world.weather in ("rainy", "stormy"):
        # Rain overlay
        intensity = 0.5 if world.weather == "rainy" else 0.9
        parts.append(rain_pattern("weatherRain", intensity=intensity, seed=seed))
        rain_opacity = round(0.3 + intensity * 0.3, 3)
        parts.append(
            f'<rect width="{width}" height="{height}" fill="url(#weatherRain)" opacity="{rain_opacity}"/>'
        )

    if world.weather == "stormy":
        # Lightning bolt
        lx = width * (0.3 + (seed % 40) / 100.0)
        parts.append(lightning_path(lx, 0, height * 0.4, seed=seed))

    if world.weather in ("cloudy", "rainy", "stormy"):
        # Cloud wash — darken sky slightly
        cloud_opacity = {"cloudy": 0.08, "rainy": 0.15, "stormy": 0.25}.get(world.weather, 0.1)
        parts.append(
            f'<rect width="{width}" height="{height * 0.45}" '
            f'fill="#7a7a8a" opacity="{cloud_opacity}" rx="40"/>'
        )

    return parts


def aurora_band_elements(
    world: WorldState,
    languages: dict[str, int] | None = None,
    width: int = 800,
    height: int = 800,
    seed: int = 0,
) -> list[str]:
    """Generate aurora borealis band SVG elements.

    Returns empty list if aurora_intensity < 0.2.
    """
    if world.aurora_intensity < 0.2:
        return []

    langs = languages or {}
    sorted_langs = sorted(langs.items(), key=lambda x: x[1], reverse=True)[:6]
    if not sorted_langs:
        sorted_langs = [("Python", 1)]

    parts: list[str] = []
    rng_val = seed * 4219
    n_bands = max(1, min(5, int(world.aurora_intensity * 5)))

    for i in range(n_bands):
        lang = sorted_langs[i % len(sorted_langs)][0]
        hue = LANG_HUES.get(lang, 155)
        color = oklch(0.60 + world.aurora_intensity * 0.15, 0.18, hue)
        y_base = height * (0.02 + i * 0.06)
        cx = width * 0.5 + ((rng_val + i * 137) % 100 - 50)
        band_w = width * (0.4 + world.aurora_intensity * 0.4)
        band_h = height * (0.04 + world.aurora_intensity * 0.03)
        opacity = round(world.aurora_intensity * 0.35 * (1.0 - i * 0.12), 3)
        parts.append(
            f'<ellipse cx="{cx:.0f}" cy="{y_base:.0f}" '
            f'rx="{band_w:.0f}" ry="{band_h:.0f}" '
            f'fill="{color}" opacity="{opacity}" '
            f'filter="url(#auroraGlow)"/>'
        )

    return parts


def firefly_elements(
    star_velocity: dict[str, Any] | None,
    width: int = 800,
    height: int = 800,
    y_min: float = 0.3,
    y_max: float = 0.85,
    seed: int = 0,
) -> list[str]:
    """Generate glowing firefly/bioluminescent particle SVG elements.

    Returns empty list if star velocity is zero or missing.
    """
    vel = star_velocity or {}
    rate = vel.get("recent_rate", 0) if isinstance(vel, dict) else 0
    if rate <= 0:
        return []

    n_flies = max(1, min(15, int(rate * 1.5)))
    rng_val = seed * 8317
    parts: list[str] = []

    for i in range(n_flies):
        x = (rng_val + i * 173) % width
        y = int(height * y_min + ((rng_val + i * 251) % int(height * (y_max - y_min))))
        r = round(0.8 + (i % 3) * 0.4, 2)
        glow_r = round(r * 3, 1)
        opacity = round(0.3 + (i % 5) * 0.1, 2)
        color = oklch(0.78, 0.16, 95 + (i % 4) * 10)  # warm gold-green
        parts.append(
            f'<circle cx="{x}" cy="{y}" r="{glow_r}" fill="{color}" opacity="{opacity * 0.3:.3f}"/>'
        )
        parts.append(
            f'<circle cx="{x}" cy="{y}" r="{r}" fill="{color}" opacity="{opacity}"/>'
        )

    return parts


# ---------------------------------------------------------------------------
# Extended OKLCH color science (Phase 1)
# ---------------------------------------------------------------------------


def _srgb_to_linear(c: float) -> float:
    """sRGB gamma to linear transfer function (inverse of _linear_to_srgb)."""
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hex_to_oklch(hex_str: str) -> tuple[float, float, float]:
    """Convert hex color '#rrggbb' to OKLCH (L, C, H_degrees).

    L in [0,1], C ~[0,0.4], H in [0,360).
    Inverse of ``oklch()``.
    """
    r = int(hex_str[1:3], 16) / 255.0
    g = int(hex_str[3:5], 16) / 255.0
    b = int(hex_str[5:7], 16) / 255.0
    rl = _srgb_to_linear(r)
    gl = _srgb_to_linear(g)
    bl = _srgb_to_linear(b)
    l_ = 0.4122214708 * rl + 0.5363325363 * gl + 0.0514459929 * bl
    m_ = 0.2119034982 * rl + 0.6806995451 * gl + 0.1073969566 * bl
    s_ = 0.0883024619 * rl + 0.2220049256 * gl + 0.6396926125 * bl
    lc = l_ ** (1 / 3) if l_ >= 0 else 0.0
    mc = m_ ** (1 / 3) if m_ >= 0 else 0.0
    sc = s_ ** (1 / 3) if s_ >= 0 else 0.0
    L = 0.2104542553 * lc + 0.7936177850 * mc - 0.0040720468 * sc
    a = 1.9779984951 * lc - 2.4285922050 * mc + 0.4505937099 * sc
    b_val = 0.0259040371 * lc + 0.7827717662 * mc - 0.8086757660 * sc
    C = math.sqrt(a * a + b_val * b_val)
    H = math.degrees(math.atan2(b_val, a)) % 360
    return L, C, H


def oklch_gamut_map(L: float, C: float, H: float) -> tuple[float, float, float]:
    """Reduce chroma until the OKLCH triplet maps to a valid sRGB color.

    Binary-search: halves C until all RGB channels in [0, 1].
    Preserves hue and lightness — only chroma is reduced.
    """
    a = C * math.cos(math.radians(H))
    b = C * math.sin(math.radians(H))

    def _in_gamut(c_val: float) -> bool:
        ca = c_val * math.cos(math.radians(H))
        cb = c_val * math.sin(math.radians(H))
        lc = L + 0.3963377774 * ca + 0.2158037573 * cb
        mc = L - 0.1055613458 * ca - 0.0638541728 * cb
        sc = L - 0.0894841775 * ca - 1.2914855480 * cb
        l3 = lc ** 3
        m3 = mc ** 3
        s3 = sc ** 3
        r = 4.0767416621 * l3 - 3.3077115913 * m3 + 0.2309699292 * s3
        g = -1.2684380046 * l3 + 2.6097574011 * m3 - 0.3413193965 * s3
        bv = -0.0041960863 * l3 - 0.7034186147 * m3 + 1.7076147010 * s3
        eps = -0.001
        return r >= eps and g >= eps and bv >= eps and r <= 1.001 and g <= 1.001 and bv <= 1.001

    if _in_gamut(C):
        return L, C, H

    lo, hi = 0.0, C
    for _ in range(16):
        mid = (lo + hi) / 2
        if _in_gamut(mid):
            lo = mid
        else:
            hi = mid
    return L, lo, H


def oklch_lerp(hex1: str, hex2: str, t: float) -> str:
    """Perceptually uniform interpolation between two hex colors via OKLCH.

    Handles hue wrapping across the 0/360 boundary.
    *t* = 0.0 returns hex1, *t* = 1.0 returns hex2.
    """
    L1, C1, H1 = hex_to_oklch(hex1)
    L2, C2, H2 = hex_to_oklch(hex2)
    L = L1 + (L2 - L1) * t
    C = C1 + (C2 - C1) * t
    # Shortest-arc hue interpolation
    dh = H2 - H1
    if dh > 180:
        dh -= 360
    elif dh < -180:
        dh += 360
    H = (H1 + dh * t) % 360
    return oklch(L, C, H)


def oklch_gradient(anchors: list[tuple[float, float, float]], n: int) -> list[str]:
    """Generate *n* evenly-spaced hex colors along an OKLCH anchor path.

    *anchors*: list of (L, C, H) tuples defining the gradient stops.
    Uses linear interpolation with shortest-arc hue wrapping.
    """
    if n <= 0:
        return []
    if n == 1 or len(anchors) < 2:
        L, C, H = anchors[0] if anchors else (0.5, 0.0, 0)
        return [oklch(L, C, H)]
    colors: list[str] = []
    for i in range(n):
        pos = i / max(n - 1, 1) * (len(anchors) - 1)
        lo = int(pos)
        hi = min(lo + 1, len(anchors) - 1)
        frac = pos - lo
        L = anchors[lo][0] + frac * (anchors[hi][0] - anchors[lo][0])
        C = anchors[lo][1] + frac * (anchors[hi][1] - anchors[lo][1])
        dh = anchors[hi][2] - anchors[lo][2]
        if dh > 180:
            dh -= 360
        elif dh < -180:
            dh += 360
        H = (anchors[lo][2] + frac * dh) % 360
        colors.append(oklch(L, C, H))
    return colors


def wcag_contrast_ratio(hex_fg: str, hex_bg: str) -> float:
    """WCAG 2.1 contrast ratio between two hex colors. Range [1, 21]."""
    def _rel_lum(h: str) -> float:
        r = _srgb_to_linear(int(h[1:3], 16) / 255.0)
        g = _srgb_to_linear(int(h[3:5], 16) / 255.0)
        b = _srgb_to_linear(int(h[5:7], 16) / 255.0)
        return 0.2126 * r + 0.7152 * g + 0.0722 * b
    l1 = _rel_lum(hex_fg)
    l2 = _rel_lum(hex_bg)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def ensure_contrast(hex_fg: str, hex_bg: str, min_ratio: float = 4.5) -> str:
    """Adjust fg lightness in OKLCH to meet min_ratio against bg.

    Tries darkening first, then lightening if needed.
    """
    if wcag_contrast_ratio(hex_fg, hex_bg) >= min_ratio:
        return hex_fg
    L, C, H = hex_to_oklch(hex_fg)
    bg_L, _, _ = hex_to_oklch(hex_bg)
    # Try moving L away from bg_L
    for step in range(20):
        if bg_L > 0.5:
            candidate_L = max(0.0, L - step * 0.04)
        else:
            candidate_L = min(1.0, L + step * 0.04)
        candidate = oklch(candidate_L, C, H)
        if wcag_contrast_ratio(candidate, hex_bg) >= min_ratio:
            return candidate
    return hex_fg


# ---------------------------------------------------------------------------
# Art palette registry (Phase 2)
# ---------------------------------------------------------------------------


ART_PALETTE_ANCHORS: dict[str, list[tuple[float, float, float]]] = {
    "sunset": [
        (0.48, 0.22, 310), (0.58, 0.26, 340), (0.65, 0.24, 15),
        (0.72, 0.22, 40), (0.78, 0.20, 65),
    ],
    "aurora": [
        (0.55, 0.22, 290), (0.65, 0.20, 200), (0.60, 0.22, 150),
        (0.62, 0.20, 340), (0.68, 0.16, 280),
    ],
    "ocean": [
        (0.38, 0.18, 255), (0.48, 0.22, 240), (0.56, 0.20, 220),
        (0.62, 0.18, 195), (0.68, 0.16, 170),
    ],
    "flora": [
        (0.52, 0.14, 155), (0.56, 0.20, 145), (0.62, 0.22, 120),
        (0.50, 0.16, 105), (0.48, 0.16, 180),
    ],
    "ember": [
        (0.48, 0.24, 15), (0.56, 0.22, 30), (0.62, 0.20, 45),
        (0.52, 0.18, 25), (0.44, 0.22, 5),
    ],
    "neon": [
        (0.72, 0.28, 250), (0.70, 0.30, 330), (0.78, 0.28, 155),
        (0.80, 0.26, 80),
    ],
    "cosmic": [
        (0.15, 0.08, 280), (0.25, 0.14, 260), (0.35, 0.18, 240),
        (0.30, 0.12, 300), (0.20, 0.10, 320),
    ],
    "spiral": [
        (0.55, 0.12, 260), (0.60, 0.14, 220), (0.65, 0.16, 180),
        (0.58, 0.10, 300), (0.52, 0.14, 340),
    ],
    "turing": [
        (0.18, 0.06, 270), (0.35, 0.16, 200), (0.50, 0.22, 160),
        (0.65, 0.18, 130), (0.80, 0.10, 80),
    ],
    "physarum": [
        (0.12, 0.04, 250), (0.30, 0.14, 170), (0.55, 0.22, 90),
        (0.70, 0.20, 55), (0.85, 0.12, 40),
    ],
}


CLUSTER_PALETTES: dict[str, list[str]] = {
    "AI/ML": ["#6D28D9", "#7C3AED", "#8B5CF6", "#A78BFA", "#5B21B6"],
    "Web": ["#1D4ED8", "#2563EB", "#3B82F6", "#60A5FA", "#1E40AF"],
    "Data": ["#047857", "#059669", "#10B981", "#34D399", "#065F46"],
    "DevOps": ["#B45309", "#D97706", "#F59E0B", "#FBBF24", "#92400E"],
    "Languages": ["#B91C1C", "#DC2626", "#EF4444", "#F87171", "#991B1B"],
    "Tools": ["#0E7490", "#0891B2", "#06B6D4", "#22D3EE", "#155E75"],
    "Security": ["#9D174D", "#BE185D", "#EC4899", "#F472B6", "#831843"],
    "Other": ["#374151", "#4B5563", "#6B7280", "#9CA3AF", "#1F2937"],
}


def select_palette_for_world(world: WorldState) -> str:
    """Choose the best ART_PALETTE name based on world state."""
    if world.time_of_day == "night":
        return "cosmic"
    if world.time_of_day == "dawn" or world.time_of_day == "golden":
        return "sunset"
    season_map = {"spring": "flora", "summer": "ember", "autumn": "sunset", "winter": "ocean"}
    base = season_map.get(world.season, "aurora")
    if world.energy > 0.7:
        return "neon"
    if world.aurora_intensity > 0.5:
        return "aurora"
    return base


def _build_world_palette_extended(
    time_of_day: str,
    weather: str,
    season: str,
    energy: float,
    *,
    daylight_hue_drift: float = 0.0,
    weather_severity: float = 0.0,
    season_transition_weights: Mapping[str, float] | None = None,
    activity_pressure: float = 0.5,
) -> dict[str, str]:
    """Build an extended 12-key OKLCH palette from world-state properties.

    Superset of the 5-key palette from ``_build_world_palette``.
    """
    base = _build_world_palette(
        time_of_day,
        weather,
        season,
        energy,
        daylight_hue_drift=daylight_hue_drift,
        weather_severity=weather_severity,
        season_transition_weights=season_transition_weights,
        activity_pressure=activity_pressure,
    )

    # Derive additional keys from the 5 base colors
    is_dark = time_of_day == "night"
    if is_dark:
        base["bg_primary"] = oklch(0.12, 0.03, 260)
        base["bg_secondary"] = oklch(0.08, 0.04, 280)
        base["text_primary"] = oklch(0.92, 0.02, 220)
        base["text_secondary"] = oklch(0.72, 0.04, 230)
    else:
        base["bg_primary"] = oklch(0.97, 0.01, 210)
        base["bg_secondary"] = oklch(0.93, 0.02, 220)
        base["text_primary"] = oklch(0.15, 0.02, 250)
        base["text_secondary"] = oklch(0.40, 0.03, 240)

    # Weather modulates highlight
    storm_boost = {"clear": 0.0, "cloudy": -0.02, "rainy": -0.04, "stormy": -0.06}
    severity = max(0.0, min(1.0, weather_severity))
    h_adj = storm_boost.get(weather, 0.0) - severity * 0.01
    accent_H, _ = _seasonal_hues(season, season_transition_weights)

    base["highlight"] = oklch(
        0.75 + energy * 0.1 + activity_pressure * 0.03 - severity * 0.02,
        0.22 + h_adj + activity_pressure * 0.01,
        accent_H - 30,
    )
    base["muted"] = oklch(0.55 + h_adj, 0.06, accent_H + 20)
    base["border"] = oklch(0.60 if is_dark else 0.80, 0.03, accent_H)

    return base


# ---------------------------------------------------------------------------
# GitHub data → visual parameters (Phase 6)
# ---------------------------------------------------------------------------


def visual_complexity(metrics: dict[str, Any]) -> float:
    """0.0-1.0 complexity score from language diversity (Shannon entropy).

    0 languages → 0.0, 1 language → 0.15, max entropy for 10 → 1.0.
    """
    entropy = metrics.get("language_diversity", 0.0)
    return min(1.0, entropy / 3.32)


def topic_affinity_matrix(
    repos: list[dict[str, Any]],
) -> dict[tuple[int, int], float]:
    """Return affinity scores (0-1) between repo pairs based on shared topics.

    High-affinity repos share many topics and should be placed near each other.
    """
    affinities: dict[tuple[int, int], float] = {}
    for i in range(len(repos)):
        topics_i = set(repos[i].get("topics", []))
        if not topics_i:
            continue
        for j in range(i + 1, len(repos)):
            topics_j = set(repos[j].get("topics", []))
            if not topics_j:
                continue
            shared = len(topics_i & topics_j)
            union = len(topics_i | topics_j)
            if shared > 0 and union > 0:
                affinities[(i, j)] = shared / union
    return affinities


def activity_tempo(contributions_monthly: dict[str, int] | None) -> float:
    """0.0-1.0 tempo from contribution pattern.

    Bursty → higher tempo (faster animations), steady → moderate tempo.
    Measured as coefficient of variation of monthly counts.
    """
    if not contributions_monthly:
        return 0.5
    counts = [v for v in contributions_monthly.values() if isinstance(v, int | float)]
    if len(counts) < 2:
        return 0.5
    mean = sum(counts) / len(counts)
    if mean <= 0:
        return 0.0
    variance = sum((c - mean) ** 2 for c in counts) / len(counts)
    cv = math.sqrt(variance) / mean
    return min(1.0, cv / 2.0)


# ---------------------------------------------------------------------------
# Advanced SVG techniques (Phase 5)
# ---------------------------------------------------------------------------


def organic_texture_filter(
    filter_id: str,
    texture_type: str = "cloud",
    intensity: float = 0.5,
    seed: int = 0,
) -> str:
    """SVG filter with feTurbulence + feDisplacementMap for organic textures.

    *texture_type*: 'cloud', 'water', 'marble', 'paper'.
    *intensity*: 0.0-1.0 controls displacement scale.
    Returns a ``<filter>`` element string.
    """
    params: dict[str, tuple[str, str, int, float]] = {
        # (type, baseFrequency, numOctaves, base_scale)
        "cloud": ("fractalNoise", "0.02 0.02", 3, 3.0),
        "water": ("turbulence", "0.03 0.01", 2, 5.0),
        "marble": ("fractalNoise", "0.04 0.04", 5, 2.0),
        "paper": ("fractalNoise", "0.35 0.25", 3, 0.8),
    }
    turb_type, freq, octaves, base_scale = params.get(texture_type, params["cloud"])
    scale = round(base_scale * intensity, 2)
    return (
        f'<filter id="{filter_id}" x="-5%" y="-5%" width="110%" height="110%">'
        f'<feTurbulence type="{turb_type}" baseFrequency="{freq}" '
        f'numOctaves="{octaves}" seed="{seed}" result="tex"/>'
        f'<feDisplacementMap in="SourceGraphic" in2="tex" '
        f'scale="{scale}" xChannelSelector="R" yChannelSelector="G"/>'
        f'</filter>'
    )


def blend_mode_filter(filter_id: str, mode: str = "multiply") -> str:
    """SVG feBlend filter. modes: multiply, screen, overlay, soft-light."""
    return (
        f'<filter id="{filter_id}">'
        f'<feBlend in="SourceGraphic" in2="BackgroundImage" mode="{mode}"/>'
        f'</filter>'
    )


def smil_animate(
    attr: str,
    values: list[str],
    dur: float,
    begin: float = 0.0,
    repeat: str = "indefinite",
    fill: str = "freeze",
) -> str:
    """Generate an SVG ``<animate>`` element string."""
    vals = ";".join(values)
    return (
        f'<animate attributeName="{attr}" values="{vals}" '
        f'dur="{dur}s" begin="{begin}s" repeatCount="{repeat}" fill="{fill}"/>'
    )


def smil_animate_transform(
    transform_type: str,
    values: list[str],
    dur: float,
    begin: float = 0.0,
    repeat: str = "indefinite",
) -> str:
    """Generate an SVG ``<animateTransform>`` element string."""
    vals = ";".join(values)
    return (
        f'<animateTransform attributeName="transform" type="{transform_type}" '
        f'values="{vals}" dur="{dur}s" begin="{begin}s" repeatCount="{repeat}"/>'
    )


# ---------------------------------------------------------------------------
# Shared constants & utilities for living-art modules (Phase 6)
# ---------------------------------------------------------------------------

MAX_REPOS: int = 10
"""Hard cap on repos rendered with full visual treatment in any art module."""


def repo_visibility_score(repo: dict[str, Any]) -> float:
    """Rank repos for full visual treatment when the profile exceeds *MAX_REPOS*.

    Scoring weights: stars (dominant), forks, watchers, topic count,
    age (capped at 6 years), and description presence.
    """
    stars = float(repo.get("stars", 0) or 0)
    forks = float(repo.get("forks", 0) or 0)
    watchers = float(repo.get("watchers", 0) or 0)
    age_months = float(repo.get("age_months", 0) or 0)
    topic_count = len(repo.get("topics") or [])
    has_description = 1.0 if repo.get("description") else 0.0
    return (
        math.log1p(stars) * 4.0
        + math.log1p(forks) * 2.2
        + math.log1p(watchers) * 1.4
        + min(age_months, 72.0) * 0.05
        + topic_count * 0.8
        + has_description * 0.4
    )


def select_primary_repos(
    repos: list[dict[str, Any]], *, limit: int = MAX_REPOS
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Select the most prominent repos while preserving chronological order.

    Returns ``(primary, overflow)`` where *primary* contains at most *limit*
    repos ordered by their original position in *repos*.
    """
    if len(repos) <= limit:
        return repos, []
    ranked = sorted(
        enumerate(repos),
        key=lambda item: (repo_visibility_score(item[1]), -item[0]),
        reverse=True,
    )
    primary_indices = {index for index, _repo in ranked[:limit]}
    primary = [repo for index, repo in enumerate(repos) if index in primary_indices]
    overflow = [repo for _index, repo in ranked[limit:]]
    return primary, overflow


# ── Language-family spatial clustering ────────────────────────────────────

_LANG_FAMILIES: dict[str, str] = {
    "Python": "data",
    "Jupyter Notebook": "data",
    "R": "data",
    "JavaScript": "web",
    "TypeScript": "web",
    "HTML": "web",
    "CSS": "web",
    "Rust": "systems",
    "Go": "systems",
    "C": "systems",
    "C++": "systems",
    "Java": "enterprise",
    "Kotlin": "enterprise",
    "Scala": "enterprise",
    "Ruby": "scripting",
    "Shell": "scripting",
    "Lua": "scripting",
    "PHP": "scripting",
    "Swift": "mobile",
    "Dart": "mobile",
}

_FAMILY_QUADRANT: dict[str, tuple[float, float]] = {
    "data": (0.25, 0.30),
    "web": (0.75, 0.25),
    "systems": (0.25, 0.70),
    "enterprise": (0.75, 0.70),
    "scripting": (0.50, 0.50),
    "mobile": (0.60, 0.45),
}


def repo_to_canvas_position(
    repo: dict[str, Any],
    seed: str,
    canvas_w: float = WIDTH,
    canvas_h: float = HEIGHT,
    *,
    strategy: str = "language_cluster",
    jitter: float = 0.15,
) -> tuple[float, float]:
    """Deterministic 2D position for a repo on the art canvas.

    Strategies
    ----------
    ``"language_cluster"``
        Groups repos by language family into spatial quadrants with
        hash-based jitter within each quadrant.
    ``"hash"``
        Pure deterministic 2D hash of repo name — no clustering.
    """
    name = repo.get("name", "")
    h = hashlib.sha256(f"{seed}-{name}".encode()).hexdigest()

    if strategy == "language_cluster":
        lang = repo.get("language") or ""
        family = _LANG_FAMILIES.get(lang, "scripting")
        cx_frac, cy_frac = _FAMILY_QUADRANT.get(family, (0.5, 0.5))
        jx = (hex_frac(h, 0, 4) - 0.5) * 2 * jitter
        jy = (hex_frac(h, 4, 8) - 0.5) * 2 * jitter
        x = (cx_frac + jx) * canvas_w
        y = (cy_frac + jy) * canvas_h
    else:
        x = hex_frac(h, 0, 8) * canvas_w * 0.8 + canvas_w * 0.1
        y = hex_frac(h, 8, 16) * canvas_h * 0.8 + canvas_h * 0.1

    return (
        max(canvas_w * 0.05, min(canvas_w * 0.95, x)),
        max(canvas_h * 0.05, min(canvas_h * 0.95, y)),
    )


# ── Derived metrics ──────────────────────────────────────────────────────


@dataclass(frozen=True)
class DerivedMetrics:
    """Pre-computed secondary metrics shared across art modules."""

    contribution_intensity: float
    """contributions_last_year / account_age_years (0 if unknown)."""

    star_velocity: float
    """Fraction of total stars gained in the last year (0-1)."""

    topic_diversity: int
    """Count of distinct topics across all repos."""

    language_count: int
    """Count of distinct languages across all repos."""

    total_stars: int
    total_forks: int
    total_contributions: int


def compute_derived_metrics(metrics: dict[str, Any]) -> DerivedMetrics:
    """Compute secondary metrics from the raw metrics payload."""
    repos = metrics.get("top_repos") or metrics.get("repos") or []

    total_stars = int(metrics.get("stars", 0) or 0)
    total_forks = sum(int(r.get("forks", 0) or 0) for r in repos)
    total_contributions = int(metrics.get("contributions_last_year", 0) or 0)
    account_age_years = max(0.1, (metrics.get("account_age_days") or 365) / 365.25)

    contribution_intensity = total_contributions / account_age_years

    # Star velocity: approximate from recent vs total
    recent_stars = int(metrics.get("stars_last_year", 0) or 0)
    star_velocity = min(1.0, recent_stars / max(1, total_stars))

    all_topics: set[str] = set()
    all_languages: set[str] = set()
    for r in repos:
        all_topics.update(r.get("topics") or [])
        lang = r.get("language")
        if lang:
            all_languages.add(lang)

    return DerivedMetrics(
        contribution_intensity=contribution_intensity,
        star_velocity=star_velocity,
        topic_diversity=len(all_topics),
        language_count=len(all_languages),
        total_stars=total_stars,
        total_forks=total_forks,
        total_contributions=total_contributions,
    )


# ── Element budget ────────────────────────────────────────────────────────


class ElementBudget:
    """Track SVG element count against a maximum budget.

    Usage::

        budget = ElementBudget(25000)
        for item in items:
            if not budget.ok():
                break
            P.append(render(item))
            budget.add(1)
    """

    __slots__ = ("_max", "_count")

    def __init__(self, max_elements: int = 25000) -> None:
        self._max = max_elements
        self._count = 0

    def add(self, n: int = 1) -> None:
        self._count += n

    def ok(self) -> bool:
        return self._count < self._max

    @property
    def remaining(self) -> int:
        return max(0, self._max - self._count)

    @property
    def count(self) -> int:
        return self._count
