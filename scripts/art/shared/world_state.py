"""Ecosystem maturity and shared WorldState atmospherics."""

from __future__ import annotations

import math
from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from .color import oklch

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
    if m.get("source_contract") == "evolution_state" and "maturity" in m:
        try:
            return max(0.0, min(1.0, float(m.get("maturity", 0.0) or 0.0)))
        except (TypeError, ValueError):
            pass

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
    "Python": "summer",
    "Jupyter Notebook": "summer",
    "JavaScript": "autumn",
    "TypeScript": "autumn",
    "HTML": "autumn",
    "CSS": "autumn",
    "Rust": "winter",
    "C": "winter",
    "C++": "winter",
    "Go": "winter",
    "Ruby": "spring",
    "Shell": "spring",
    "Java": "spring",
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

    # ── Weather (from issue stats or timelapse atmosphere envelope) ─
    atmosphere_weights = metrics.get("atmosphere_weights")
    if isinstance(atmosphere_weights, Mapping) and atmosphere_weights:
        cloud = max(0.0, float(atmosphere_weights.get("cloud", 0.0) or 0.0))
        rain = max(0.0, float(atmosphere_weights.get("rain", 0.0) or 0.0))
        storm = max(0.0, float(atmosphere_weights.get("storm", 0.0) or 0.0))
        weather_severity = round(
            min(1.0, cloud * 0.25 + rain * 0.55 + storm * 0.85),
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
    else:
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
    season_envelope = metrics.get("season_weights")
    if isinstance(season_envelope, Mapping) and season_envelope:
        season_transition_weights = _normalize_season_weights(
            {
                str(season): max(0.0, float(weight or 0.0))
                for season, weight in season_envelope.items()
            }
        )
        season = max(season_transition_weights, key=season_transition_weights.get)
    else:
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
        streaks.get("current_streak_months", 0) if isinstance(streaks, dict) else 0
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
