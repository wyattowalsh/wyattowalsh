"""
Ferrofluid Magnetism Sculpture — living art module.

Dark metallic liquid forms spike sculptures in response to magnetic fields
created by repos.  Each repo places a magnetic dipole; where the field
exceeds a critical threshold the ferrofluid rises into iridescent tapered
spikes with mirrored reflections below a pool surface line.
"""

# ruff: noqa: E501

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date

import numpy as np

from .shared import (
    HEIGHT,
    LANG_HUES,
    WIDTH,
    ElementBudget,
    WorldState,
    compute_maturity,
    compute_world_state,
    contributions_monthly_to_daily_series,
    map_date_to_loop_delay,
    normalize_timeline_window,
    oklch,
    organic_texture_filter,
    repo_to_canvas_position,
    seed_hash,
    select_primary_repos,
)

# ── Configuration ────────────────────────────────────────────────────────


@dataclass(frozen=True)
class FerrofluidConfig:
    """Tunable constants for the ferrofluid simulation."""

    max_repos: int = 10
    max_elements: int = 25000
    grid_resolution: int = 60
    moment_base: float = 500.0
    b_critical: float = 0.3
    spike_scale: float = 80.0
    spike_base_width: float = 8.0
    viscosity_norm: float = 3000.0
    pool_y_fraction: float = 0.55
    reflection_opacity: float = 0.25
    iridescence_strength: float = 30.0


CFG = FerrofluidConfig()


@dataclass(frozen=True)
class FerrofluidSignals:
    """Derived snapshot signals that shape ferrofluid composition."""

    field_gain: float
    fluid_response: float
    surface_tension: float
    iridescence: float
    max_spikes: int
    social_pull: float
    build_volume: float
    collaboration_heat: float
    diversity: float
    star_velocity_pull: float
    traffic_heat: float
    merge_cadence: float
    release_charge: float
    streak_heat: float
    highlight_density: float
    dipole_lift: float


# ── Helpers ──────────────────────────────────────────────────────────────


def _spike_polygon(
    cx: float,
    cy: float,
    base_w: float,
    height: float,
    *,
    taper: float = 0.15,
) -> str:
    """Return SVG polygon points for a tapered spike (diamond/cone)."""
    half_b = base_w / 2
    half_tip = half_b * taper
    return (
        f"{cx - half_b:.1f},{cy:.1f} "
        f"{cx - half_tip:.1f},{cy - height:.1f} "
        f"{cx + half_tip:.1f},{cy - height:.1f} "
        f"{cx + half_b:.1f},{cy:.1f}"
    )


def _reflected_polygon(
    cx: float,
    pool_y: float,
    base_w: float,
    height: float,
    *,
    taper: float = 0.15,
) -> str:
    """Mirror spike below the pool surface (inverted, pointing down)."""
    half_b = base_w / 2
    half_tip = half_b * taper
    return (
        f"{cx - half_b:.1f},{pool_y:.1f} "
        f"{cx - half_tip:.1f},{pool_y + height:.1f} "
        f"{cx + half_tip:.1f},{pool_y + height:.1f} "
        f"{cx + half_b:.1f},{pool_y:.1f}"
    )


def _make_spike_gradient(
    grad_id: str,
    base_color: str,
    highlight_color: str,
    tip_color: str,
    *,
    extra_attrs: str = "",
) -> str:
    """SVG linearGradient dark-base -> bright-highlight -> dark-tip."""
    attrs = f" {extra_attrs.strip()}" if extra_attrs.strip() else ""
    return (
        f'<linearGradient id="{grad_id}"{attrs} x1="0" y1="1" x2="0" y2="0">'
        f'<stop offset="0%" stop-color="{base_color}"/>'
        f'<stop offset="45%" stop-color="{highlight_color}"/>'
        f'<stop offset="100%" stop-color="{tip_color}"/>'
        f"</linearGradient>"
    )


def _norm_log(value: float, scale: float) -> float:
    """Clamp a positive metric into a stable 0-1 log-normalized band."""
    safe_value = max(0.0, float(value))
    safe_scale = max(float(scale), 1.0)
    return min(1.0, math.log1p(safe_value) / math.log1p(safe_scale))


def _daily_contribution_series(metrics: dict) -> dict[str, int]:
    """Return deterministic per-day contribution counts when available."""
    daily = metrics.get("contributions_daily")
    if isinstance(daily, dict) and daily:
        return {str(key): max(0, int(value or 0)) for key, value in daily.items()}

    monthly = metrics.get("contributions_monthly")
    if isinstance(monthly, dict) and monthly:
        return contributions_monthly_to_daily_series(monthly)

    return {}


def _recent_contribution_volume(metrics: dict, *, days: int = 45) -> int:
    """Rolling contribution sum used to express recent magnetic agitation."""
    daily = _daily_contribution_series(metrics)
    if not daily:
        return 0
    recent = sorted(daily.items())[-max(days, 1) :]
    return sum(count for _date, count in recent)


def _event_dates(events: object, *keys: str) -> list[date]:
    """Extract valid event dates from a list of timestamp-bearing dictionaries."""
    if not isinstance(events, list):
        return []

    extracted: list[date] = []
    for event in events:
        if not isinstance(event, dict):
            continue
        for key in keys:
            raw = event.get(key)
            if not isinstance(raw, str) or not raw.strip():
                continue
            try:
                extracted.append(date.fromisoformat(raw[:10]))
            except ValueError:
                pass
            break

    return sorted(extracted)


def _compute_ferrofluid_signals(
    metrics: dict,
    world: WorldState,
    *,
    repo_count: int,
    maturity_hint: float,
) -> FerrofluidSignals:
    """Translate cumulative GitHub metrics into ferrofluid composition signals."""
    stars = int(metrics.get("stars", 0) or 0)
    forks = int(metrics.get("forks", 0) or 0)
    followers = int(metrics.get("followers", 0) or 0)
    watchers = int(metrics.get("watchers", 0) or 0)
    network = int(metrics.get("network_count", 0) or 0)

    total_commits = int(metrics.get("total_commits", 0) or 0)
    total_prs = int(metrics.get("total_prs", 0) or 0)
    total_issues = int(metrics.get("total_issues", 0) or 0)
    total_repos_contributed = int(metrics.get("total_repos_contributed", 0) or 0)
    public_gists = int(metrics.get("public_gists", 0) or 0)
    pr_review_count = int(metrics.get("pr_review_count", 0) or 0)

    releases = metrics.get("releases") or []
    recent_merged_prs = metrics.get("recent_merged_prs") or []
    release_dates = _event_dates(releases, "date", "published_at", "created_at")
    merged_pr_dates = _event_dates(recent_merged_prs, "merged_at", "date", "created_at")

    star_velocity = metrics.get("star_velocity") or {}
    recent_star_rate = (
        float(star_velocity.get("recent_rate", 0.0) or 0.0)
        if isinstance(star_velocity, dict)
        else 0.0
    )
    peak_star_rate = (
        float(star_velocity.get("peak_rate", recent_star_rate) or recent_star_rate)
        if isinstance(star_velocity, dict)
        else recent_star_rate
    )
    star_trend = (
        str(star_velocity.get("trend", "steady") or "steady").lower()
        if isinstance(star_velocity, dict)
        else "steady"
    )

    traffic_views = int(metrics.get("traffic_views_14d", 0) or 0)
    traffic_unique_visitors = int(
        metrics.get("traffic_unique_visitors_14d", 0) or 0,
    )
    traffic_clones = int(metrics.get("traffic_clones_14d", 0) or 0)

    issue_stats = metrics.get("issue_stats") or {}
    open_issues = int(metrics.get("open_issues_count", 0) or 0)
    closed_issues = (
        int(issue_stats.get("closed_count", 0) or 0)
        if isinstance(issue_stats, dict)
        else 0
    )
    total_issue_volume = open_issues + closed_issues
    issue_drag = open_issues / total_issue_volume if total_issue_volume > 0 else 0.0

    topic_clusters = metrics.get("topic_clusters") or {}
    language_diversity = float(metrics.get("language_diversity", 0.0) or 0.0)
    language_count = int(metrics.get("language_count", 0) or 0)
    topic_count = len(topic_clusters) if isinstance(topic_clusters, dict) else 0

    recent_contribs = _recent_contribution_volume(metrics, days=45)
    yearly_contribs = int(metrics.get("contributions_last_year", 0) or 0)

    streaks = metrics.get("contribution_streaks") or {}
    current_streak = (
        int(streaks.get("current_streak_months", 0) or 0)
        if isinstance(streaks, dict)
        else 0
    )
    longest_streak = (
        int(streaks.get("longest_streak_months", 0) or 0)
        if isinstance(streaks, dict)
        else 0
    )
    streak_active = (
        bool(streaks.get("streak_active", False))
        if isinstance(streaks, dict)
        else False
    )

    social_pull = _norm_log(
        stars + 1.4 * forks + 0.8 * followers + 0.6 * watchers + 0.5 * network,
        2200.0,
    )
    build_volume = _norm_log(
        total_commits
        + 2.0 * total_prs
        + 1.4 * total_issues
        + 1.5 * total_repos_contributed
        + 1.5 * public_gists,
        14000.0,
    )
    base_collaboration = _norm_log(
        len(releases) * 3 + len(recent_merged_prs) + pr_review_count * 0.5,
        80.0,
    )
    contribution_heat = max(
        _norm_log(recent_contribs, 240.0),
        _norm_log(yearly_contribs, 4000.0) * 0.65,
    )
    streak_heat = min(
        1.0,
        max(current_streak / 12.0, longest_streak / 18.0)
        + (0.08 if streak_active and current_streak > 0 else 0.0),
    )
    diversity = max(
        min(1.0, language_diversity / 2.6),
        min(1.0, language_count / 6.0),
        min(1.0, topic_count / 6.0),
    )
    repo_presence = min(1.0, repo_count / max(1.0, CFG.max_repos * 0.6))

    star_velocity_pull = min(
        1.0,
        max(
            0.0,
            0.56 * _norm_log(recent_star_rate, 18.0)
            + 0.34 * min(1.0, recent_star_rate / max(peak_star_rate, 1.0))
            + {
                "rising": 0.10,
                "surging": 0.14,
                "steady": 0.04,
                "falling": -0.05,
            }.get(star_trend, 0.0),
        ),
    )
    traffic_heat = _norm_log(
        traffic_views + 1.8 * traffic_unique_visitors + 2.5 * traffic_clones,
        9000.0,
    )
    if merged_pr_dates:
        pr_span_days = max(1, (merged_pr_dates[-1] - merged_pr_dates[0]).days + 1)
        merge_cadence = min(
            1.0,
            0.52 * _norm_log(len(merged_pr_dates) * 10, 120.0)
            + 0.48 * min(1.0, len(merged_pr_dates) / max(1.0, pr_span_days / 14.0)),
        )
    else:
        merge_cadence = 0.0
    release_charge = _norm_log(len(release_dates) * 6, 48.0) if release_dates else 0.0
    collaboration_heat = min(
        1.0,
        max(
            base_collaboration,
            base_collaboration * 0.68 + merge_cadence * 0.22 + release_charge * 0.18,
        ),
    )

    field_gain = min(
        1.35,
        max(
            0.18,
            0.22
            + 0.24 * repo_presence
            + 0.20 * social_pull
            + 0.16 * build_volume
            + 0.12 * collaboration_heat
            + 0.08 * contribution_heat
            + 0.06 * streak_heat
            + 0.05 * diversity
            + 0.08 * star_velocity_pull
            + 0.06 * merge_cadence
            + 0.05 * release_charge
            + 0.05 * traffic_heat
            + 0.04 * world.energy
            + 0.03 * max(0.0, min(1.0, maturity_hint)),
        ),
    )
    fluid_response = min(
        1.1,
        max(
            0.24,
            0.28
            + 0.30 * contribution_heat
            + 0.18 * streak_heat
            + 0.15 * build_volume
            + 0.12 * collaboration_heat
            + 0.12 * traffic_heat
            + 0.10 * star_velocity_pull
            + 0.08 * merge_cadence
            + 0.07 * world.vitality,
        ),
    )
    surface_tension = min(
        1.2,
        max(
            0.24,
            1.08
            - 0.33 * social_pull
            - 0.20 * build_volume
            - 0.18 * collaboration_heat
            - 0.14 * streak_heat
            - 0.10 * diversity
            - 0.10 * merge_cadence
            - 0.08 * traffic_heat
            - 0.08 * star_velocity_pull
            - 0.05 * release_charge
            + 0.18 * issue_drag
            + 0.06 * (1.0 - world.energy),
        ),
    )
    iridescence = CFG.iridescence_strength * (
        0.75
        + 0.55 * diversity
        + 0.35 * collaboration_heat
        + 0.22 * star_velocity_pull
        + 0.12 * release_charge
        + 0.18 * world.aurora_intensity
    )
    max_spikes = max(
        70,
        min(
            420,
            int(
                80
                + 55 * repo_presence
                + 120 * social_pull
                + 90 * build_volume
                + 70 * collaboration_heat
                + 35 * diversity
                + 35 * star_velocity_pull
                + 26 * traffic_heat
                + 22 * merge_cadence
            ),
        ),
    )
    highlight_density = min(
        1.0,
        max(
            0.0,
            0.20
            + 0.34 * streak_heat
            + 0.18 * traffic_heat
            + 0.14 * merge_cadence
            + 0.10 * release_charge,
        ),
    )
    dipole_lift = min(
        1.0,
        max(
            0.0,
            0.12
            + 0.26 * star_velocity_pull
            + 0.18 * merge_cadence
            + 0.12 * release_charge
            + 0.10 * streak_heat,
        ),
    )

    return FerrofluidSignals(
        field_gain=field_gain,
        fluid_response=fluid_response,
        surface_tension=surface_tension,
        iridescence=iridescence,
        max_spikes=max_spikes,
        social_pull=social_pull,
        build_volume=build_volume,
        collaboration_heat=collaboration_heat,
        diversity=diversity,
        star_velocity_pull=star_velocity_pull,
        traffic_heat=traffic_heat,
        merge_cadence=merge_cadence,
        release_charge=release_charge,
        streak_heat=streak_heat,
        highlight_density=highlight_density,
        dipole_lift=dipole_lift,
    )


# ── Magnetic field simulation ────────────────────────────────────────────


def _compute_field(
    dipoles: list[tuple[float, float, float]],
    grid_res: int,
    canvas_w: float,
    canvas_h: float,
    pool_y: float,
    *,
    maturity_ramp: float = 1.0,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Vectorised 2D magnetic field magnitude on a grid.

    Returns (field_magnitude, grid_xs, grid_ys) where coordinates are
    canvas-space and only the upper half (above pool_y) is computed.
    """
    xs = np.linspace(0, canvas_w, grid_res)
    ys = np.linspace(0, pool_y, grid_res)
    gx, gy = np.meshgrid(xs, ys)

    field = np.zeros_like(gx)
    eps = 1e-3
    for dx, dy, moment in dipoles:
        dist_sq = (gx - dx) ** 2 + (gy - dy) ** 2 + eps
        field += moment / dist_sq

    field *= maturity_ramp
    return field, gx, gy


def _stable_fraction(seed_key: str, *parts: object) -> float:
    """Deterministic 0-1 helper anchored to stable visual identity."""
    digest = seed_hash({"seed": "|".join([seed_key, *(str(part) for part in parts)])})
    return int(digest[:8], 16) / 0xFFFFFFFF


def _wrap_hue(hue: float) -> float:
    """Wrap hue degrees into the canonical 0-360 range."""
    return hue % 360.0


def _select_strongest_spikes(
    spike_mask: np.ndarray,
    field: np.ndarray,
    spike_heights: np.ndarray,
    max_spikes: int,
) -> list[tuple[int, int]]:
    """Select the strongest field cells deterministically, then painter-sort."""
    if max_spikes <= 0:
        return []

    candidates = [tuple(map(int, idx)) for idx in np.argwhere(spike_mask)]
    ranked = sorted(
        candidates,
        key=lambda idx: (
            -float(field[idx[0], idx[1]]),
            -float(spike_heights[idx[0], idx[1]]),
            idx[0],
            idx[1],
        ),
    )
    selected = ranked[:max_spikes]
    return sorted(
        selected,
        key=lambda idx: (
            float(spike_heights[idx[0], idx[1]]),
            float(field[idx[0], idx[1]]),
            idx[0],
            idx[1],
        ),
    )


def _nearest_dipole_index(
    sx: float,
    sy: float,
    dipole_xy: np.ndarray,
) -> int:
    """Return the nearest dipole index for a spike location."""
    if len(dipole_xy) == 0:
        return -1
    dists = (dipole_xy[:, 0] - sx) ** 2 + (dipole_xy[:, 1] - sy) ** 2
    return int(np.argmin(dists))


def _spike_gradient_palette(
    *,
    lang_hue: float,
    field_norm: float,
    owner_distance: float,
    height_ratio: float,
    light_angle: float,
    iridescence: float,
) -> tuple[str, str, str]:
    """Build a language-anchored metallic palette for a selected spike."""
    base_hue = _wrap_hue(
        lang_hue * 0.68
        + (248.0 + (light_angle - 90.0) * 0.12) * 0.32
        + (field_norm - 0.5) * iridescence * 0.82
        + (0.5 - owner_distance) * iridescence * 0.46
        + (height_ratio - 0.5) * 18.0
    )
    dark = oklch(
        0.09 + 0.04 * field_norm,
        0.03 + 0.02 * (1.0 - owner_distance),
        _wrap_hue(base_hue - 8.0),
    )
    bright = oklch(
        0.47 + 0.16 * field_norm,
        0.10 + 0.05 * (1.0 - owner_distance),
        _wrap_hue(base_hue + 12.0),
    )
    tip = oklch(
        0.15 + 0.04 * height_ratio,
        0.05 + 0.02 * field_norm,
        _wrap_hue(base_hue - 18.0),
    )
    return dark, bright, tip


def _highlight_fill(
    *,
    lang_hue: float,
    field_norm: float,
    highlight_density: float,
    height_ratio: float,
) -> str:
    """Specular highlight tint anchored to language identity and spike energy."""
    hue = _wrap_hue(
        lang_hue * 0.78
        + 195.0 * 0.22
        + 14.0 * field_norm
        + 10.0 * height_ratio
    )
    return oklch(
        0.70 + 0.10 * height_ratio,
        0.05 + 0.04 * highlight_density,
        hue,
    )


def _ambient_ripple_specs(
    dipole_meta: list[dict[str, object]],
    signals: FerrofluidSignals,
    *,
    pool_y: float,
    visual_seed: str,
    fallback_when: str = "",
) -> list[dict[str, float | int | str]]:
    """Return deterministic surface ripple specs anchored to dipoles."""
    anchors = dipole_meta
    if not anchors:
        anchors = [
            {
                "x": WIDTH * frac,
                "lang": None,
                "lang_hue": float(LANG_HUES.get(None, 155)),
                "strength": 0.18 + 0.05 * idx,
                "owner_index": idx,
                "identity": f"ambient-{idx}",
                "date": fallback_when,
            }
            for idx, frac in enumerate((0.28, 0.50, 0.72))
        ]

    specs: list[dict[str, float | int | str]] = []
    for owner_index, anchor in enumerate(anchors):
        anchor_x = float(anchor.get("x", WIDTH * 0.5) or WIDTH * 0.5)
        lang = str(anchor.get("lang") or "unknown")
        lang_hue = float(anchor.get("lang_hue", LANG_HUES.get(lang, 155)) or 155.0)
        strength = float(anchor.get("strength", 0.22) or 0.22)
        identity = str(
            anchor.get("identity")
            or anchor.get("name")
            or f"ambient-{owner_index}"
        )
        when = str(anchor.get("date") or fallback_when)
        anchor_index = int(anchor.get("owner_index", owner_index) or owner_index)
        ring_count = 1 + int(strength > 0.42)
        if signals.traffic_heat + signals.release_charge > 0.72:
            ring_count += 1
        if not dipole_meta:
            ring_count = min(ring_count, 2)

        for ring_idx in range(ring_count):
            lateral = (_stable_fraction(visual_seed, identity, "ripple-x", ring_idx) - 0.5) * (
                20.0 + 16.0 * ring_idx
            )
            vertical = (_stable_fraction(visual_seed, identity, "ripple-y", ring_idx) - 0.5) * 8.0
            cx = max(50.0, min(WIDTH - 50.0, anchor_x + lateral))
            cy = pool_y + vertical
            rx = 16.0 + 10.0 * ring_idx + 12.0 * strength + 12.0 * signals.release_charge
            opacity = min(
                0.16,
                0.03
                + 0.04 * signals.field_gain
                + 0.03 * signals.traffic_heat
                + 0.02 * signals.release_charge
                + 0.03 * strength,
            )
            stroke = oklch(
                0.20 + 0.04 * strength,
                0.03 + 0.02 * signals.traffic_heat,
                _wrap_hue(lang_hue * 0.70 + 250.0 * 0.30 + ring_idx * 8.0),
            )
            specs.append(
                {
                    "owner_index": anchor_index,
                    "lang": lang,
                    "cx": cx,
                    "cy": cy,
                    "rx": rx,
                    "ry": rx * 0.3,
                    "opacity": opacity,
                    "stroke": stroke,
                    "when": when,
                }
            )

    return sorted(
        specs,
        key=lambda spec: (
            int(spec["owner_index"]),
            float(spec["rx"]),
            float(spec["cx"]),
        ),
    )


# ── Main generate ────────────────────────────────────────────────────────


def generate(
    metrics: dict,
    *,
    seed: str | None = None,
    maturity: float | None = None,
    timeline: bool = True,
    loop_duration: float = 60.0,
    reveal_fraction: float = 0.93,
) -> str:
    """Render a ferrofluid magnetism sculpture as an SVG string."""
    mat = maturity if maturity is not None else compute_maturity(metrics)
    timeline_enabled = bool(timeline and loop_duration > 0)
    maturity_hint = 1.0 if timeline_enabled else mat

    # ── WorldState ────────────────────────────────────────────────
    world: WorldState = compute_world_state(metrics)

    snapshot_seed = seed_hash({"seed": seed}) if seed is not None else seed_hash(metrics)
    visual_seed = str(
        seed
        if seed is not None
        else (
            metrics.get("label")
            or metrics.get("login")
            or metrics.get("account_created")
            or snapshot_seed
        )
    )

    # ── Extract metrics ───────────────────────────────────────────
    repos = list(metrics.get("repos", []))
    monthly = metrics.get("contributions_monthly", {})

    top_repos, _overflow = select_primary_repos(repos, limit=CFG.max_repos)
    signals = _compute_ferrofluid_signals(
        metrics,
        world,
        repo_count=len(top_repos),
        maturity_hint=maturity_hint,
    )

    # ── Timeline window ───────────────────────────────────────────
    def _repo_date(repo: dict) -> str | None:
        for key in ("date", "created_at", "created", "pushed_at", "updated_at"):
            val = repo.get(key)
            if isinstance(val, str) and val.strip():
                return val[:10] if len(val) >= 10 else val
        return None

    timeline_window = normalize_timeline_window(
        [
            {"date": _repo_date(r)}
            for r in repos
            if isinstance(r, dict) and _repo_date(r)
        ],
        {
            "account_created": metrics.get("account_created"),
            "repos": repos,
            "contributions_monthly": monthly,
        },
        fallback_days=365,
    )

    def _timeline_style(
        when: str,
        opacity: float,
        cls: str = "tl-reveal",
        *,
        fallback_opacity: bool = True,
    ) -> str:
        final_opacity = max(0.0, min(1.0, opacity))
        opacity_attr = (
            f'opacity="{final_opacity:.2f}"' if fallback_opacity else ""
        )
        if not timeline_enabled:
            return opacity_attr
        delay = map_date_to_loop_delay(
            when,
            timeline_window,
            duration=loop_duration,
            reveal_fraction=reveal_fraction,
        )
        attrs = [
            attr
            for attr in (
                opacity_attr,
                f'class="{cls}"',
                f'style="--delay:{delay:.3f}s;--to:{final_opacity:.3f};'
                f'--dur:{loop_duration:.2f}s"',
                f'data-delay="{delay:.3f}"',
                f'data-when="{when}"',
            )
            if attr
        ]
        return " ".join(attrs)

    # ── Dipole placement ──────────────────────────────────────────
    pool_y = HEIGHT * CFG.pool_y_fraction
    fluid_response = signals.fluid_response
    surface_tension = signals.surface_tension

    dipoles: list[tuple[float, float, float]] = []
    spike_meta: list[dict] = []  # per-repo metadata for timeline
    for repo in top_repos:
        rx, ry = repo_to_canvas_position(
            repo, visual_seed, WIDTH, pool_y * 0.9, strategy="language_cluster"
        )
        repo_name = str(repo.get("name", "") or "")
        repo_lang = repo.get("language")
        repo_lang_hue = float(LANG_HUES.get(repo_lang, 155))
        repo_stars = int(repo.get("stars", 0) or 0)
        repo_forks = int(repo.get("forks", 0) or 0)
        repo_topics = repo.get("topics") or []
        repo_age = min(1.0, max(float(repo.get("age_months", 1) or 1), 1.0) / 48.0)
        repo_visibility = _norm_log(
            repo_stars + 1.6 * repo_forks + len(repo_topics) * 2,
            180.0,
        )
        repo_identity = f"{repo_name}:{repo_lang or 'unknown'}"
        repo_bias = _stable_fraction(visual_seed, repo_identity, "dipole-bias") - 0.5
        rx = max(
            WIDTH * 0.08,
            min(
                WIDTH * 0.92,
                rx + repo_bias * WIDTH * 0.035 * (0.4 + signals.traffic_heat),
            ),
        )
        ry = max(
            pool_y * 0.08,
            min(
                pool_y * 0.95,
                ry
                + (pool_y - ry)
                * (
                    0.06
                    + 0.16 * signals.dipole_lift
                    + 0.08 * repo_visibility
                    + 0.05 * repo_forks / max(1.0, repo_forks + 4.0)
                ),
            ),
        )
        moment = (
            CFG.moment_base
            * (
                0.55
                + 0.40 * signals.social_pull
                + 0.20 * signals.build_volume
                + 0.15 * signals.collaboration_heat
            )
            * (
                0.70
                + 0.85 * repo_visibility
                + 0.20 * repo_age
                + 0.08 * signals.diversity
                + 0.10 * signals.star_velocity_pull
                + 0.08 * signals.merge_cadence
                + 0.06 * signals.release_charge
            )
        )
        dipoles.append((rx, ry, moment))
        spike_meta.append(
            {
                "repo": repo,
                "name": repo_name,
                "identity": repo_identity,
                "x": rx,
                "y": ry,
                "moment": moment,
                "date": _repo_date(repo) or timeline_window[0].isoformat(),
                "lang": repo_lang,
                "lang_hue": repo_lang_hue,
                "strength": repo_visibility,
            }
        )

    # ── Compute magnetic field ────────────────────────────────────
    field, gx, gy = _compute_field(
        dipoles,
        CFG.grid_resolution,
        WIDTH,
        HEIGHT,
        pool_y,
        maturity_ramp=signals.field_gain,
    )

    # ── Find spikes ───────────────────────────────────────────────
    b_crit = CFG.b_critical / max(0.24, surface_tension)
    b_crit *= 1.0 - 0.12 * signals.diversity
    b_crit = max(0.08, b_crit)
    spike_mask = field > b_crit
    spike_heights = CFG.spike_scale * np.sqrt(np.maximum(0.0, field - b_crit))
    spike_heights *= (
        0.42
        + 0.32 * fluid_response
        + 0.16 * signals.social_pull
        + 0.10 * signals.collaboration_heat
        + 0.10 * signals.star_velocity_pull
        + 0.08 * signals.merge_cadence
        + 0.06 * signals.release_charge
    )

    # ── Lighting angle from time of day ───────────────────────────
    tod_angles = {"dawn": 20.0, "day": 70.0, "golden": 150.0, "night": 250.0}
    light_angle = tod_angles.get(world.time_of_day, 70.0)

    # ══════════════════════════════════════════════════════════════
    # BUILD SVG
    # ══════════════════════════════════════════════════════════════
    P: list[str] = []
    budget = ElementBudget(CFG.max_elements)

    P.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" '
        f'width="{WIDTH}" height="{HEIGHT}" '
        f'data-surface-tension="{surface_tension:.3f}" '
        f'data-highlight-density="{signals.highlight_density:.3f}" '
        f'data-dipole-lift="{signals.dipole_lift:.3f}">'
    )

    if timeline_enabled:
        P.append(
            "<style>"
            "@keyframes ferroReveal{0%{opacity:0}100%{opacity:var(--to,1)}}"
            ".tl-reveal{animation:ferroReveal .8s ease-out var(--delay,0s) both}"
            ".tl-soft{animation-duration:1.15s}"
            "</style>"
        )

    # ── Defs ──────────────────────────────────────────────────────
    P.append("<defs>")

    # Liquid surface texture
    P.append(organic_texture_filter("ferroTexture", "water", intensity=0.35))

    # Reflection blur
    P.append(
        '<filter id="reflBlur" x="-10%" y="-10%" width="120%" height="120%">'
        '<feGaussianBlur stdDeviation="3.5"/>'
        "</filter>"
    )

    # Background gradient (near-black with slight blue)
    bg_top = oklch(0.08, 0.02, 270)
    bg_mid = oklch(0.06, 0.015, 260)
    bg_bot = oklch(0.04, 0.01, 250)
    P.append(
        '<linearGradient id="bgGrad" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0%" stop-color="{bg_top}"/>'
        f'<stop offset="55%" stop-color="{bg_mid}"/>'
        f'<stop offset="100%" stop-color="{bg_bot}"/>'
        "</linearGradient>"
    )

    # Per-spike gradients (iridescent metallic)
    max_spikes = min(signals.max_spikes, budget.remaining // 6)
    spike_indices = _select_strongest_spikes(
        spike_mask,
        field,
        spike_heights,
        max_spikes,
    )
    dipole_xy = (
        np.array([(d[0], d[1]) for d in dipoles]) if dipoles else np.empty((0, 2))
    )
    selected_field_max = max(
        (float(field[yi, xi]) for yi, xi in spike_indices),
        default=max(b_crit, 1.0),
    )
    selected_height_max = max(
        (float(spike_heights[yi, xi]) for yi, xi in spike_indices),
        default=1.0,
    )

    spike_records: list[dict[str, float | int | str]] = []
    grad_defs: list[str] = []
    fallback_when = timeline_window[0].isoformat()
    for si, (yi, xi) in enumerate(spike_indices):
        sx = float(gx[yi, xi])
        sy = float(gy[yi, xi])
        sh = float(spike_heights[yi, xi])
        field_val = float(field[yi, xi])
        owner_index = _nearest_dipole_index(sx, sy, dipole_xy)
        owner = (
            spike_meta[owner_index]
            if 0 <= owner_index < len(spike_meta)
            else {
                "x": sx,
                "y": sy,
                "date": fallback_when,
                "lang": None,
                "lang_hue": float(LANG_HUES.get(None, 155)),
                "strength": 0.0,
            }
        )
        owner_distance = min(
            1.0,
            math.hypot(
                sx - float(owner["x"]),
                sy - float(owner["y"]),
            )
            / max(WIDTH * 0.22, 1.0),
        )
        field_norm = min(1.0, field_val / max(selected_field_max, 1e-6))
        height_ratio = min(1.0, sh / max(selected_height_max, 1e-6))
        lang_hue = float(owner["lang_hue"])
        dark, bright, tip = _spike_gradient_palette(
            lang_hue=lang_hue,
            field_norm=field_norm,
            owner_distance=owner_distance,
            height_ratio=height_ratio,
            light_angle=light_angle,
            iridescence=signals.iridescence,
        )
        lang_label = str(owner.get("lang") or "unknown")
        grad_id = f"sg{si}"
        grad_defs.append(
            _make_spike_gradient(
                grad_id,
                dark,
                bright,
                tip,
                extra_attrs=(
                    f'data-owner-index="{owner_index}" '
                    f'data-lang="{lang_label}"'
                ),
            )
        )
        spike_records.append(
            {
                "grad_id": grad_id,
                "yi": yi,
                "xi": xi,
                "sx": sx,
                "sy": sy,
                "height": sh,
                "field": field_val,
                "when": str(owner["date"]),
                "owner_index": owner_index,
                "lang": lang_label,
                "lang_hue": lang_hue,
                "field_norm": field_norm,
                "height_ratio": height_ratio,
            }
        )

    for gd in grad_defs:
        P.append(gd)
        budget.add(1)

    P.append("</defs>")

    # ── Background ────────────────────────────────────────────────
    P.append(f'<rect width="{WIDTH}" height="{HEIGHT}" fill="url(#bgGrad)"/>')
    budget.add(1)

    # ── Subtle liquid surface ripples ─────────────────────────────
    ripple_opacity = min(
        0.18,
        0.05
        + 0.04 * min(1.0, fluid_response)
        + 0.03 * signals.traffic_heat
        + 0.02 * signals.release_charge,
    )
    P.append(
        f'<rect class="ferro-surface-ripple" x="0" y="{pool_y - 15:.0f}" width="{WIDTH}" height="30" '
        f'fill="{oklch(0.20, 0.03, 260)}" opacity="{ripple_opacity:.2f}" '
        f'filter="url(#ferroTexture)"/>'
    )
    budget.add(1)

    # ── Pool surface line ─────────────────────────────────────────
    surface_color = oklch(0.25, 0.05, 240)
    P.append(
        f'<line x1="0" y1="{pool_y:.1f}" x2="{WIDTH}" y2="{pool_y:.1f}" '
        f'stroke="{surface_color}" stroke-width="0.8" opacity="0.5"/>'
    )
    budget.add(1)

    # ── Render reflections first (behind spikes) ──────────────────
    refl_group: list[str] = []
    for record in spike_records:
        if not budget.ok():
            break
        sx = float(record["sx"])
        sh = float(record["height"])
        if sh < 1.5:
            continue
        field_val = float(record["field"])
        bw = CFG.spike_base_width * math.sqrt(max(0.3, field_val / max(b_crit * 3, 1)))
        refl_h = sh * 0.7
        refl_pts = _reflected_polygon(sx, pool_y, bw, refl_h)
        refl_op = CFG.reflection_opacity * min(1.0, sh / 40.0)
        refl_group.append(
            f'<polygon points="{refl_pts}" fill="url(#{record["grad_id"]})" '
            f'opacity="{refl_op:.2f}" filter="url(#reflBlur)" '
            f"{_timeline_style(str(record['when']), refl_op, 'tl-reveal tl-soft', fallback_opacity=False)}/>"
        )
        budget.add(1)

    if refl_group:
        P.append(f'<g opacity="{CFG.reflection_opacity:.2f}">')
        P.extend(refl_group)
        P.append("</g>")

    # ── Render spikes ─────────────────────────────────────────────
    for record in spike_records:
        if not budget.ok():
            break
        sx = float(record["sx"])
        sy = float(record["sy"])
        sh = float(record["height"])
        if sh < 1.0:
            continue
        field_val = float(record["field"])
        bw = CFG.spike_base_width * math.sqrt(max(0.3, field_val / max(b_crit * 3, 1)))
        pts = _spike_polygon(sx, pool_y, bw, sh)
        P.append(
            f'<polygon points="{pts}" fill="url(#{record["grad_id"]})" '
            f"{_timeline_style(str(record['when']), 0.95, 'tl-reveal')}/>"
        )
        budget.add(1)

    # ── Specular highlight on tallest spikes ──────────────────────
    highlight_percentile = max(42.0, 82.0 - signals.highlight_density * 36.0)
    highlight_thresh = (
        np.percentile(spike_heights[spike_mask], highlight_percentile)
        if spike_mask.any()
        else 999
    )
    for record in spike_records:
        if not budget.ok():
            break
        sh = float(record["height"])
        if sh < highlight_thresh:
            continue
        sx = float(record["sx"])
        tip_y = pool_y - sh
        hl_color = _highlight_fill(
            lang_hue=float(record["lang_hue"]),
            field_norm=float(record["field_norm"]),
            highlight_density=signals.highlight_density,
            height_ratio=float(record["height_ratio"]),
        )
        P.append(
            f'<ellipse data-role="ferro-highlight" data-owner-index="{int(record["owner_index"])}" '
            f'data-lang="{record["lang"]}" cx="{sx:.1f}" cy="{tip_y + sh * 0.35:.1f}" '
            f'rx="{max(0.8, sh * 0.04):.1f}" ry="{max(1.5, sh * 0.12):.1f}" '
            f'fill="{hl_color}" opacity="{0.28 + 0.16 * signals.highlight_density:.2f}" '
            f"{_timeline_style(str(record['when']), 0.35, 'tl-reveal tl-soft', fallback_opacity=False)}/>"
        )
        budget.add(1)

    # ── Sparse-history: ambient ripples when the field is still nascent ──────
    if signals.field_gain < 0.5:
        for ripple in _ambient_ripple_specs(
            spike_meta,
            signals,
            pool_y=pool_y,
            visual_seed=visual_seed,
            fallback_when=fallback_when,
        ):
            if not budget.ok():
                break
            P.append(
                f'<ellipse data-role="ferro-ripple" '
                f'data-owner-index="{int(ripple["owner_index"])}" data-lang="{ripple["lang"]}" '
                f'cx="{float(ripple["cx"]):.1f}" cy="{float(ripple["cy"]):.1f}" '
                f'rx="{float(ripple["rx"]):.1f}" ry="{float(ripple["ry"]):.1f}" '
                f'fill="none" stroke="{ripple["stroke"]}" stroke-width="0.5" '
                f"{_timeline_style(str(ripple['when']), float(ripple['opacity']), 'ferro-ripple tl-reveal tl-soft')}/>"
            )
            budget.add(1)

    # ── Dipole markers (subtle glow at each repo position) ────────
    for dm in spike_meta:
        if not budget.ok():
            break
        lang_hue = float(dm["lang_hue"])
        glow_color = oklch(0.30, 0.10, lang_hue)
        marker_radius = 4.0 + 4.5 * dm["strength"] + 2.0 * signals.collaboration_heat
        halo_rx = 12.0 + 14.0 * dm["strength"] + 8.0 * signals.diversity
        halo_ry = 3.0 + 4.5 * min(1.0, fluid_response)
        halo_op = 0.04 + 0.06 * (
            0.5 * dm["strength"] + 0.5 * signals.collaboration_heat
        )
        glow_op = 0.10 + 0.12 * dm["strength"] + 0.08 * signals.build_volume
        P.append(
            f'<ellipse cx="{dm["x"]:.1f}" cy="{pool_y:.1f}" '
            f'rx="{halo_rx:.1f}" ry="{halo_ry:.1f}" fill="{glow_color}" '
            f'opacity="{halo_op:.2f}" '
            f"{_timeline_style(dm['date'], halo_op, 'tl-reveal tl-soft', fallback_opacity=False)}/>"
        )
        budget.add(1)
        if not budget.ok():
            break
        P.append(
            f'<circle data-role="ferro-dipole" data-lang="{dm["lang"] or "unknown"}" '
            f'cx="{dm["x"]:.1f}" cy="{pool_y:.1f}" r="{marker_radius:.1f}" '
            f'fill="{glow_color}" opacity="{glow_op:.2f}" '
            f'data-moment="{dm["moment"]:.1f}" data-depth="{dm["y"]:.1f}" '
            f"{_timeline_style(dm['date'], glow_op, 'tl-reveal tl-soft', fallback_opacity=False)}/>"
        )
        budget.add(1)

    P.append("</svg>")
    return "\n".join(P)
