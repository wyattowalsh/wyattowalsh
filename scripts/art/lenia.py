"""
Lenia — Continuous cellular automata living art.

Digital organisms (soft, bioluminescent blobs) emerge from seed points,
pulsate, and interact in a continuous field. Each repo seeds one organism.
Kernel physics are parameterized by the language mix, creating a unique
species of digital life for each profile.
"""

# ruff: noqa: E501, F401

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass
from datetime import date as dt_date

import numpy as np

try:
    from scipy.signal import fftconvolve  # type: ignore[import-untyped]
except ImportError:  # pragma: no cover — scipy optional
    from numpy import convolve as _np_convolve  # type: ignore[attr-defined]

    def fftconvolve(a: np.ndarray, b: np.ndarray, mode: str = "same") -> np.ndarray:  # type: ignore[misc]
        """Fallback 2D convolution via numpy when scipy is unavailable."""
        from numpy.fft import fft2, ifft2  # noqa: PLC0415

        pad_h = a.shape[0] + b.shape[0] - 1
        pad_w = a.shape[1] + b.shape[1] - 1
        fa = fft2(a, s=(pad_h, pad_w))
        fb = fft2(b, s=(pad_h, pad_w))
        out = np.real(ifft2(fa * fb))
        if mode == "same":
            top = (b.shape[0] - 1) // 2
            left = (b.shape[1] - 1) // 2
            return out[top : top + a.shape[0], left : left + a.shape[1]]
        return out


from .shared import (
    ART_PALETTE_ANCHORS,
    HEIGHT,
    LANG_HUES,
    MAX_REPOS,
    WIDTH,
    DerivedMetrics,
    ElementBudget,
    Noise2D,
    WorldState,
    _build_world_palette_extended,
    blend_mode_filter,
    compute_derived_metrics,
    compute_maturity,
    compute_world_state,
    contributions_monthly_to_daily_series,
    hex_frac,
    map_date_to_loop_delay,
    normalize_timeline_window,
    oklch,
    oklch_lerp,
    repo_to_canvas_position,
    seed_hash,
    select_palette_for_world,
    select_primary_repos,
    topic_affinity_matrix,
    visual_complexity,
    volumetric_glow_filter,
)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class LeniaConfig:
    """Tunable parameters for the Lenia simulation and rendering."""

    max_repos: int = 10
    max_elements: int = 25_000
    grid_resolution: int = 50
    dt: float = 0.1
    mu_base: float = 0.05
    mu_scale: float = 0.08
    mu_norm: float = 100.0
    sigma_base: float = 0.02
    sigma_scale: float = 0.02
    sigma_norm: float = 5000.0
    kernel_radius: int = 13
    sim_steps_base: int = 60
    sim_steps_scale: float = 30.0
    field_threshold: float = 0.15
    seed_radius: int = 4


CFG = LeniaConfig()


@dataclass(frozen=True)
class _SeedSpec:
    """Deterministic nutrient or organism seed."""

    gx: int
    gy: int
    radius: int
    amplitude: float
    softness: float
    when: str


@dataclass(frozen=True)
class LeniaDynamics:
    """Resolved simulation knobs from cumulative GitHub activity signals."""

    mu: float
    sigma: float
    sim_steps: int
    kernel_profile: str
    r_peak: float
    k_width: float
    pr_burst: float
    pr_density: float
    commit_phase: float
    commit_focus: float
    day_bias: float
    recency_mix: float
    streak_strength: float
    repo_density: float
    recent_flux: float
    release_energy: float
    traffic_heat: float
    activity_drive: float
    seed_drift: tuple[int, int]
    satellite_count: int
    merged_repo_names: frozenset[str]


@dataclass(frozen=True)
class _LeniaPalette:
    """Snapshot-specific render palette for the Lenia field."""

    background: str
    ramp: tuple[tuple[float, str], ...]
    core: str


# Bioluminescent color ramp (OKLCH anchors)
_BIO_RAMP: list[tuple[float, float, float, float, float]] = [
    # (field_lo, field_hi, L, C, H)
    (0.0, 0.2, 0.0, 0.0, 0.0),  # transparent
    (0.2, 0.4, 0.25, 0.12, 260.0),  # deep blue
    (0.4, 0.6, 0.50, 0.18, 200.0),  # cyan
    (0.6, 0.8, 0.65, 0.20, 150.0),  # green
    (0.8, 1.0, 0.85, 0.12, 140.0),  # bright white-green
]

_BG_COLOR = oklch(0.08, 0.04, 280)


def _circular_hue_average(
    entries: list[tuple[float, float]],
    *,
    fallback: float,
) -> float:
    """Return a weighted circular hue mean in degrees."""
    x = 0.0
    y = 0.0
    total = 0.0
    for hue, weight in entries:
        if weight <= 0:
            continue
        angle = math.radians(hue % 360.0)
        x += math.cos(angle) * weight
        y += math.sin(angle) * weight
        total += weight
    if total <= 0 or (abs(x) < 1e-9 and abs(y) < 1e-9):
        return fallback % 360.0
    return math.degrees(math.atan2(y, x)) % 360.0


def _clamp_canvas_position(x: float, y: float) -> tuple[float, float]:
    """Keep semantic layout positions safely inside the canvas frame."""
    return (
        max(WIDTH * 0.08, min(WIDTH * 0.92, x)),
        max(HEIGHT * 0.08, min(HEIGHT * 0.92, y)),
    )


# ---------------------------------------------------------------------------
# Kernel & growth function
# ---------------------------------------------------------------------------


def _build_ring_kernel(radius: int, r_peak: float, width: float) -> np.ndarray:
    """Build an unnormalized annular Gaussian ring kernel."""
    y, x = np.ogrid[-radius : radius + 1, -radius : radius + 1]
    r = np.sqrt(x * x + y * y).astype(np.float64) / radius
    kernel = np.exp(-((r - r_peak) ** 2) / (2.0 * width * width))
    kernel[r > 1.0] = 0.0
    return kernel


def _build_kernel(
    radius: int,
    r_peak: float,
    width: float,
    *,
    profile: str = "ring",
) -> np.ndarray:
    """Build a normalized Lenia kernel with a stable profile family."""
    base = _build_ring_kernel(radius, r_peak, width)
    y, x = np.ogrid[-radius : radius + 1, -radius : radius + 1]
    r = np.sqrt(x * x + y * y).astype(np.float64) / radius

    if profile == "dual":
        inner = _build_ring_kernel(
            radius,
            max(0.14, min(0.55, r_peak * 0.58)),
            max(0.04, min(0.18, width * 0.82)),
        )
        kernel = 0.72 * base + 0.28 * inner
    elif profile == "core":
        core_width = max(0.04, min(0.16, width * 0.78))
        core = np.exp(-(r**2) / (2.0 * core_width * core_width))
        core[r > 1.0] = 0.0
        kernel = 0.58 * base + 0.42 * core
    elif profile == "halo":
        halo = _build_ring_kernel(
            radius,
            max(0.28, min(0.92, r_peak + 0.14)),
            max(0.06, min(0.24, width * 1.35)),
        )
        kernel = 0.62 * base + 0.38 * halo
    else:
        kernel = base

    total = kernel.sum()
    if total > 0:
        kernel /= total
    return kernel


def _growth(u: np.ndarray, mu: float, sigma: float) -> np.ndarray:
    """Gaussian bump growth function: G(u) = 2 * exp(-(u-mu)^2/(2*sigma^2)) - 1."""
    return 2.0 * np.exp(-((u - mu) ** 2) / (2.0 * sigma * sigma)) - 1.0


# ---------------------------------------------------------------------------
# Kernel parameterization from language mix
# ---------------------------------------------------------------------------


def _kernel_params_from_mix(
    language_mix: dict[str, float],
    h: str,
    *,
    diversity: float = 0.0,
    activity: float = 0.0,
    recency: float = 0.0,
    velocity: float = 0.0,
    pr_burst: float = 0.0,
    commit_focus: float = 0.0,
    day_bias: float = 1.0,
) -> tuple[str, float, float]:
    """Derive kernel profile, ring peak, and width from cumulative snapshot signals."""
    n_langs = max(1, len(language_mix))
    hash_frac = hex_frac(h, 24, 28)
    diversity = max(0.0, min(1.0, diversity))
    activity = max(0.0, min(1.0, activity))
    recency = max(0.0, min(1.0, recency))
    velocity = max(0.0, min(1.0, velocity))
    pr_burst = max(0.0, min(1.0, pr_burst))
    commit_focus = max(0.0, min(1.0, commit_focus))
    # More languages → wider ring; active streaks and fresh repos add instability.
    r_peak = (
        0.28
        + 0.24 * math.tanh(n_langs / 4.0)
        + 0.09 * diversity
        + 0.05 * recency
        + 0.03 * pr_burst
        + 0.04 * hash_frac
    )
    width = (
        0.07
        + 0.05 * math.tanh(n_langs / 6.0)
        + 0.04 * diversity
        + 0.02 * activity
        + 0.02 * (1.0 - commit_focus)
        + 0.02 * hash_frac
    )

    profile_scores = {
        "ring": 0.34 + 0.16 * activity + 0.12 * commit_focus,
        "dual": 0.18 + 0.42 * recency + 0.24 * pr_burst + 0.14 * velocity,
        "core": 0.20 + 0.24 * activity + 0.18 * commit_focus + 0.12 * diversity,
        "halo": 0.14
        + 0.38 * max(0.0, -day_bias)
        + 0.18 * pr_burst
        + 0.12 * (1.0 - commit_focus),
    }
    profile = max(profile_scores.items(), key=lambda item: (item[1], item[0]))[0]
    return profile, min(0.82, r_peak), min(0.28, width)


# ---------------------------------------------------------------------------
# Field initialization
# ---------------------------------------------------------------------------


def _seed_organisms(
    field: np.ndarray,
    seeds: list[_SeedSpec],
    rng: np.random.Generator,
) -> None:
    """Plant seed organisms at grid positions (in-place)."""
    N = field.shape[0]
    for spec in seeds:
        radius = max(1, spec.radius)
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                dist = math.sqrt(dx * dx + dy * dy)
                if dist <= radius:
                    ny, nx = (spec.gy + dy) % N, (spec.gx + dx) % N
                    norm = dist / radius
                    falloff = math.exp(-(1.8 + 1.6 * spec.softness) * norm * norm)
                    val = spec.amplitude * falloff * (0.92 + 0.16 * rng.random())
                    field[ny, nx] = max(field[ny, nx], min(1.0, val))


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------


def _simulate(
    field: np.ndarray,
    kernel: np.ndarray,
    mu: float,
    sigma: float,
    steps: int,
    dt: float,
    energy: float,
) -> np.ndarray:
    """Run Lenia simulation for *steps* timesteps, return final field."""
    energy_mod = 0.8 + 0.4 * energy  # 0.8-1.2 speed modifier
    for _ in range(steps):
        potential = fftconvolve(field, kernel, mode="same")
        G = _growth(potential, mu, sigma)
        field = np.clip(field + dt * energy_mod * G, 0.0, 1.0)
    return field


# ---------------------------------------------------------------------------
# Color mapping
# ---------------------------------------------------------------------------


def _build_lenia_palette(
    world: WorldState,
    *,
    language_mix: dict[str, float],
    repos: list[dict],
    dynamics: LeniaDynamics,
    h: str,
) -> _LeniaPalette:
    """Resolve a snapshot-specific palette from world, language, and repo signals."""
    palette = world.palette
    if "bg_secondary" not in palette or "highlight" not in palette:
        palette = _build_world_palette_extended(
            world.time_of_day,
            world.weather,
            world.season,
            world.energy,
            daylight_hue_drift=world.daylight_hue_drift,
            weather_severity=world.weather_severity,
            season_transition_weights=world.season_transition_weights,
            activity_pressure=world.activity_pressure,
        )

    palette_name = select_palette_for_world(world)
    anchor_defs = ART_PALETTE_ANCHORS.get(palette_name, ART_PALETTE_ANCHORS["aurora"])
    anchor_colors = [oklch(L, C, H) for L, C, H in anchor_defs]
    fallback_hue = anchor_defs[min(2, len(anchor_defs) - 1)][2]

    language_entries = sorted(
        ((lang, float(weight)) for lang, weight in language_mix.items() if weight > 0),
        key=lambda item: (item[1], item[0]),
        reverse=True,
    )[:4]
    hue_entries = [
        (
            float(LANG_HUES.get(lang, anchor_defs[index % len(anchor_defs)][2])),
            weight,
        )
        for index, (lang, weight) in enumerate(language_entries)
    ]
    dominant_hue = _circular_hue_average(hue_entries, fallback=fallback_hue)
    secondary_hue = _circular_hue_average(
        hue_entries[1:] or hue_entries,
        fallback=anchor_defs[-1][2],
    )
    dominant_share = language_entries[0][1] if language_entries else 1.0
    language_diversity = min(1.0, len(language_entries) / 4.0)

    repo_count = max(1, len(repos))
    recent_repo_share = (
        sum(1 for repo in repos if int(repo.get("age_months", 0) or 0) <= 12)
        / repo_count
    )
    topic_signal = min(
        1.0,
        sum(len(repo.get("topics") or []) for repo in repos)
        / max(1.0, repo_count * 4.0),
    )
    repo_visibility = min(
        1.0,
        sum(math.log1p(max(0, int(repo.get("stars", 0) or 0)) + 1) for repo in repos)
        / max(1.0, repo_count * 2.4),
    )
    glow_mix = min(
        1.0,
        0.32 * world.energy
        + 0.18 * world.aurora_intensity
        + 0.14 * dynamics.pr_burst
        + 0.14 * dynamics.recency_mix
        + 0.12 * repo_visibility
        + 0.10 * topic_signal,
    )

    dominant_lang_color = oklch(
        0.50 + 0.12 * world.energy + 0.05 * recent_repo_share,
        0.12 + 0.05 * dominant_share + 0.03 * topic_signal,
        dominant_hue,
    )
    secondary_lang_color = oklch(
        0.62 + 0.08 * dynamics.recency_mix + 0.06 * world.activity_pressure,
        0.10 + 0.04 * language_diversity + 0.03 * dynamics.pr_burst,
        secondary_hue,
    )

    background = oklch_lerp(
        palette["bg_secondary"],
        oklch(
            0.12 + 0.06 * world.energy + 0.03 * recent_repo_share,
            0.03 + 0.02 * world.activity_pressure,
            dominant_hue,
        ),
        min(
            0.62,
            0.22
            + 0.16 * recent_repo_share
            + 0.10 * dynamics.traffic_heat
            + 0.08 * dominant_share,
        ),
    )
    low_color = oklch_lerp(
        oklch_lerp(
            anchor_colors[0], palette["accent"], 0.30 + 0.16 * world.activity_pressure
        ),
        dominant_lang_color,
        0.24 + 0.22 * dominant_share,
    )
    mid_color = oklch_lerp(
        oklch_lerp(
            anchor_colors[min(2, len(anchor_colors) - 1)],
            dominant_lang_color,
            0.40 + 0.18 * language_diversity,
        ),
        palette["highlight"],
        0.16 + 0.14 * dynamics.commit_focus,
    )
    high_color = oklch_lerp(
        oklch_lerp(anchor_colors[-2], secondary_lang_color, 0.34 + 0.16 * topic_signal),
        palette["glow"],
        0.22 + 0.18 * dynamics.recency_mix + 0.08 * world.aurora_intensity,
    )
    peak_color = oklch_lerp(
        oklch_lerp(anchor_colors[-1], palette["highlight"], 0.24 + 0.22 * glow_mix),
        dominant_lang_color,
        0.10 + 0.10 * dynamics.pr_density,
    )
    core = oklch_lerp(
        peak_color,
        palette["highlight"],
        0.52 + 0.18 * glow_mix + 0.10 * repo_visibility,
    )

    ramp = (
        (0.20, low_color),
        (
            min(
                0.50,
                0.38 + 0.04 * world.activity_pressure + 0.03 * dynamics.commit_focus,
            ),
            mid_color,
        ),
        (
            min(0.74, 0.58 + 0.05 * dynamics.recency_mix + 0.03 * topic_signal),
            high_color,
        ),
        (
            min(0.90, 0.80 + 0.04 * dominant_share + 0.02 * world.energy),
            peak_color,
        ),
        (1.0, core),
    )
    return _LeniaPalette(background=background, ramp=ramp, core=core)


def _field_to_color(value: float, palette: _LeniaPalette) -> tuple[str, float]:
    """Map a field value to (hex color, opacity) via the resolved snapshot ramp."""
    if not palette.ramp or value < palette.ramp[0][0]:
        return "#000000", 0.0
    prev_cutoff, prev_color = palette.ramp[0]
    for cutoff, color in palette.ramp[1:]:
        if value <= cutoff:
            t = (value - prev_cutoff) / max(0.001, cutoff - prev_cutoff)
            opacity = max(0.0, min(1.0, 0.28 + 0.72 * (0.45 * t + 0.55 * value)))
            return oklch_lerp(prev_color, color, t), opacity
        prev_cutoff, prev_color = cutoff, color
    return palette.ramp[-1][1], 1.0


# ---------------------------------------------------------------------------
# SVG rendering
# ---------------------------------------------------------------------------


def _render_svg(
    field: np.ndarray,
    *,
    config: LeniaConfig,
    palette: _LeniaPalette,
    timeline: bool,
    timeline_lookup: list[list[str]],
    timeline_window: tuple[dt_date, dt_date],
    loop_duration: float,
    reveal_fraction: float,
    growth_mat: float,
) -> str:
    """Render the Lenia field as an SVG of glowing circles."""
    N = config.grid_resolution
    cell_size = WIDTH / N  # 800/50 = 16
    budget = ElementBudget(config.max_elements)

    P: list[str] = []

    # ── SVG header ────────────────────────────────────────────────
    P.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" '
        f'width="{WIDTH}" height="{HEIGHT}">'
    )

    # ── Defs: glow filter ─────────────────────────────────────────
    P.append("<defs>")
    P.append(volumetric_glow_filter("lenia-glow", radius=6.0))
    P.append(
        '<filter id="lenia-halo" x="-40%" y="-40%" width="180%" height="180%">'
        '<feGaussianBlur in="SourceGraphic" stdDeviation="10" result="blur"/>'
        '<feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>'
        "</filter>"
    )
    P.append("</defs>")

    # ── CSS animation (timeline reveal) ───────────────────────────
    if timeline:
        P.append(
            "<style>"
            "@keyframes leniaReveal{0%{opacity:0}100%{opacity:var(--to,1)}}"
            ".tl-reveal{opacity:0;animation:leniaReveal .8s ease-out var(--delay,0s) both}"
            "</style>"
        )

    # ── Background ────────────────────────────────────────────────
    P.append(f'<rect width="{WIDTH}" height="{HEIGHT}" fill="{palette.background}"/>')

    # ── Organism circles ──────────────────────────────────────────
    P.append('<g filter="url(#lenia-glow)">')

    # Collect cells above threshold, sort by value for layering
    cells: list[tuple[float, int, int]] = []
    for gy in range(N):
        for gx in range(N):
            v = float(field[gy, gx])
            if v > config.field_threshold:
                cells.append((v, gx, gy))
    cells.sort(key=lambda c: c[0])

    for v, gx, gy in cells:
        if not budget.ok():
            break

        color, opacity = _field_to_color(v, palette)
        if opacity < 0.01:
            continue

        cx = (gx + 0.5) * cell_size
        cy = (gy + 0.5) * cell_size
        r = cell_size * 0.5 * (0.3 + 0.7 * v)

        # Maturity fade: early maturity dims the field
        mat_opacity = opacity * _fade_ramp(growth_mat, v)

        style_parts: list[str] = []
        if timeline:
            when = timeline_lookup[gy][gx]
            delay = map_date_to_loop_delay(
                when,
                timeline_window,
                duration=loop_duration,
                reveal_fraction=reveal_fraction,
            )
            style_parts.append(
                f'class="tl-reveal" '
                f'style="--delay:{delay:.3f}s;--to:{mat_opacity:.2f};--dur:{loop_duration:.2f}s" '
                f'data-delay="{delay:.3f}" data-when="{when}"'
            )
        else:
            style_parts.append(f'opacity="{mat_opacity:.2f}"')

        P.append(
            f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" '
            f'fill="{color}" {" ".join(style_parts)}/>'
        )
        budget.add(1)

    P.append("</g>")

    # ── Bright core highlights for high-value cells ───────────────
    P.append('<g filter="url(#lenia-halo)">')
    for v, gx, gy in cells:
        if v < 0.65 or not budget.ok():
            continue
        cx = (gx + 0.5) * cell_size
        cy = (gy + 0.5) * cell_size
        r = cell_size * 0.25 * v
        core_color = palette.core
        core_opacity = 0.3 * (v - 0.65) / 0.35 * _fade_ramp(growth_mat, v)
        if core_opacity < 0.01:
            continue
        if timeline:
            when = timeline_lookup[gy][gx]
            delay = map_date_to_loop_delay(
                when,
                timeline_window,
                duration=loop_duration,
                reveal_fraction=reveal_fraction,
            )
            P.append(
                f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" '
                f'fill="{core_color}" class="tl-reveal" '
                f'style="--delay:{delay:.3f}s;--to:{core_opacity:.2f};--dur:{loop_duration:.2f}s" '
                f'data-delay="{delay:.3f}" data-when="{when}"/>'
            )
        else:
            P.append(
                f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" '
                f'fill="{core_color}" opacity="{core_opacity:.2f}"/>'
            )
        budget.add(1)
    P.append("</g>")

    P.append("</svg>")
    return "\n".join(P)


def _fade_ramp(growth_mat: float, field_value: float) -> float:
    """Progressive reveal: higher field values require more maturity to appear."""
    # Low values appear early, high values need maturity >= 0.5
    threshold = 0.1 + 0.4 * field_value
    return max(0.0, min(1.0, (growth_mat - threshold) / max(0.001, 1.0 - threshold)))


# ---------------------------------------------------------------------------
# Metric signal extraction
# ---------------------------------------------------------------------------


def _signal_date(entry: dict, *keys: str) -> str | None:
    """Return the first usable ISO date string from *entry*."""
    for key in keys:
        value = entry.get(key)
        if isinstance(value, str) and value.strip():
            return value[:10] if len(value) >= 10 else value
    return None


def _extract_language_mix(
    repos: list[dict],
    language_bytes: dict[str, int] | None = None,
) -> dict[str, float]:
    """Build a normalized language → fraction mapping from bytes or repos."""
    weights: dict[str, float] = {}

    if language_bytes and isinstance(language_bytes, dict):
        for lang, raw in language_bytes.items():
            if not isinstance(lang, str) or not lang:
                continue
            try:
                amount = float(raw or 0)
            except (TypeError, ValueError):
                continue
            if amount > 0:
                weights[lang] = amount
        total = sum(weights.values())
        if total > 0:
            return {k: v / total for k, v in weights.items()}

    for repo in repos:
        lang = repo.get("language")
        if not lang:
            continue
        star_weight = 1.0 + 0.35 * math.log1p(int(repo.get("stars", 0) or 0))
        weights[lang] = weights.get(lang, 0.0) + star_weight

    total = max(1.0, sum(weights.values()))
    return {k: v / total for k, v in weights.items()}


def _normalized_language_diversity(
    metrics: dict,
    language_mix: dict[str, float],
) -> float:
    """Normalize language diversity into a stable 0-1 band."""
    explicit = metrics.get("language_diversity")
    if isinstance(explicit, (int, float)):
        denom = max(1.0, math.log2(max(2, len(language_mix))))
        return max(0.0, min(1.0, float(explicit) / denom))

    if len(language_mix) <= 1:
        return 0.0

    entropy = 0.0
    for portion in language_mix.values():
        if portion > 0:
            entropy -= portion * math.log2(portion)
    return max(0.0, min(1.0, entropy / math.log2(len(language_mix))))


def _daily_contribution_series(
    metrics: dict,
    *,
    reference_year: int,
) -> dict[str, int]:
    """Return per-day contribution counts, preferring explicit daily history."""
    raw_daily = metrics.get("contributions_daily") or {}
    daily: dict[str, int] = {}
    if isinstance(raw_daily, dict):
        for key, value in raw_daily.items():
            when = str(key).strip()
            if len(when) >= 10 and when[4] == "-" and when[7] == "-":
                daily[when[:10]] = max(0, int(value or 0))
    if daily:
        return dict(sorted(daily.items()))
    return contributions_monthly_to_daily_series(
        metrics.get("contributions_monthly"),
        reference_year=reference_year,
    )


def _recent_contribution_load(daily_series: dict[str, int], *, days: int = 45) -> int:
    """Recent activity window used to keep early snapshots quieter."""
    if not daily_series:
        return 0
    recent_days = list(sorted(daily_series.items()))[-max(1, days) :]
    return sum(max(0, int(value or 0)) for _day, value in recent_days)


def _recency_signal(metrics: dict, repos: list[dict]) -> float:
    """Return how much the current repo set skews toward fresh work."""
    raw_bands = metrics.get("repo_recency_bands") or {}
    if isinstance(raw_bands, dict) and raw_bands:
        total = sum(max(0, int(value or 0)) for value in raw_bands.values())
        if total > 0:
            fresh = max(0, int(raw_bands.get("fresh", 0) or 0))
            recent = max(0, int(raw_bands.get("recent", 0) or 0))
            established = max(0, int(raw_bands.get("established", 0) or 0))
            return min(1.0, (fresh + 0.6 * recent + 0.2 * established) / total)

    if not repos:
        return 0.0

    score = 0.0
    for repo in repos:
        age = int(repo.get("age_months", 0) or 0)
        if age <= 3:
            score += 1.0
        elif age <= 12:
            score += 0.6
        elif age <= 36:
            score += 0.25
    return min(1.0, score / len(repos))


def _normalize_hour_distribution(commit_hours: object) -> dict[int, float]:
    """Normalize commit-hour payloads into a stable ``hour -> weight`` mapping."""
    hours: dict[int, float] = {}
    if not isinstance(commit_hours, dict):
        return hours
    for raw_hour, raw_count in commit_hours.items():
        try:
            hour = int(raw_hour)
            count = float(raw_count)
        except (TypeError, ValueError):
            continue
        if 0 <= hour <= 23 and count > 0:
            hours[hour] = hours.get(hour, 0.0) + count
    return hours


def _commit_hour_profile(commit_hours: object) -> tuple[float, float, float]:
    """Return peak hour, focus, and day/night bias from commit-hour data."""
    hours = _normalize_hour_distribution(commit_hours)
    if not hours:
        return 12.0, 0.0, 1.0

    total = sum(hours.values())
    vec_x = sum(
        math.cos(2.0 * math.pi * hour / 24.0) * weight for hour, weight in hours.items()
    )
    vec_y = sum(
        math.sin(2.0 * math.pi * hour / 24.0) * weight for hour, weight in hours.items()
    )
    focus = min(1.0, max(0.0, math.hypot(vec_x, vec_y) / max(total, 1e-6)))
    if abs(vec_x) < 1e-9 and abs(vec_y) < 1e-9:
        peak_hour = 12.0
    else:
        mean_angle = math.atan2(vec_y, vec_x)
        if mean_angle < 0:
            mean_angle += 2.0 * math.pi
        peak_hour = mean_angle * 24.0 / (2.0 * math.pi)

    day_bias = math.cos((peak_hour - 12.0) * math.pi / 12.0)
    return peak_hour, focus, day_bias


def _summarize_merged_pr_cadence(
    recent_merged_prs: object,
) -> tuple[float, float, frozenset[str]]:
    """Compress merged-PR history into density, burstiness, and touched repos."""
    if not isinstance(recent_merged_prs, list):
        return 0.0, 0.0, frozenset()

    parsed: list[tuple[dt_date, float]] = []
    repo_names: set[str] = set()
    for pr in recent_merged_prs:
        if not isinstance(pr, dict):
            continue

        merged_when = _signal_date(pr, "merged_at", "mergedAt", "date")
        if not merged_when:
            continue
        try:
            merged_day = dt_date.fromisoformat(merged_when[:10])
        except ValueError:
            continue

        additions = max(0, int(pr.get("additions", 0) or 0))
        deletions = max(0, int(pr.get("deletions", 0) or 0))
        change_scale = min(1.0, math.log1p(additions + deletions) / math.log1p(600.0))
        parsed.append((merged_day, change_scale))

        repo_name = str(pr.get("repo_name") or "").strip()
        if repo_name:
            repo_names.add(repo_name)

    if not parsed:
        return 0.0, 0.0, frozenset()

    parsed.sort(key=lambda item: item[0])
    density = min(1.0, len(parsed) / 8.0)
    if len(parsed) == 1:
        return (
            density,
            min(1.0, density * 0.45 + parsed[0][1] * 0.20),
            frozenset(repo_names),
        )

    gaps = [max(1, (curr[0] - prev[0]).days) for prev, curr in zip(parsed, parsed[1:])]
    mean_gap = sum(gaps) / len(gaps)
    gap_variance = sum((gap - mean_gap) ** 2 for gap in gaps) / len(gaps)
    gap_cv = math.sqrt(gap_variance) / mean_gap if mean_gap > 0 else 0.0
    tempo = min(1.0, 16.0 / max(mean_gap, 1.0))
    change_pressure = sum(scale for _day, scale in parsed) / max(1, len(parsed))
    burst = min(
        1.0,
        0.38 * density
        + 0.38 * tempo
        + min(0.12, gap_cv * 0.12)
        + 0.12 * change_pressure,
    )
    return density, burst, frozenset(repo_names)


def _augment_primary_repos(
    primary_repos: list[dict],
    all_repos: list[dict],
    *,
    merged_repo_names: frozenset[str],
    limit: int,
) -> list[dict]:
    """Promote merged or fresh repos into the limited seed pool."""
    if not all_repos:
        return primary_repos

    def _priority(repo: dict) -> tuple[int, int, float, int, str]:
        name = str(repo.get("name") or "").strip()
        age_months = int(repo.get("age_months", 0) or 0)
        is_recent = age_months > 0 and age_months <= 12
        return (
            1 if name in merged_repo_names else 0,
            1 if is_recent else 0,
            float(repo.get("stars", 0) or 0.0),
            -age_months if age_months > 0 else 0,
            name,
        )

    boosted = sorted(all_repos, key=_priority, reverse=True)
    active_candidates = [
        repo for repo in boosted if _priority(repo)[0] > 0 or _priority(repo)[1] > 0
    ]
    seen: set[str] = set()
    selected: list[dict] = []
    for repo in active_candidates + primary_repos:
        name = str(repo.get("name") or "").strip()
        key = name or f"repo-{len(selected)}"
        if key in seen:
            continue
        selected.append(repo)
        seen.add(key)
        if len(selected) >= limit:
            break
    return selected or primary_repos


def _semantic_repo_positions(
    repos: list[dict],
    *,
    h: str,
    dynamics: LeniaDynamics,
) -> list[tuple[float, float]]:
    """Lay out repos with language clustering plus topic-aware local structure."""
    if not repos:
        return []

    positions: list[list[float]] = []
    language_groups: dict[str, list[int]] = defaultdict(list)
    for index, repo in enumerate(repos):
        cluster_x, cluster_y = repo_to_canvas_position(
            repo,
            h,
            WIDTH,
            HEIGHT,
            strategy="language_cluster",
            jitter=0.10 + 0.05 * dynamics.repo_density,
        )
        hash_x, hash_y = repo_to_canvas_position(
            repo,
            h,
            WIDTH,
            HEIGHT,
            strategy="hash",
        )
        repo_name = str(repo.get("name") or "").strip()
        repo_hash = seed_hash(
            {
                "seed": h,
                "repo": repo_name,
                "language": repo.get("language"),
            }
        )
        stars = max(0, int(repo.get("stars", 0) or 0))
        age_months = max(1, int(repo.get("age_months", 1) or 1))
        topic_count = len(repo.get("topics") or [])
        star_norm = math.tanh(stars / 24.0)
        recency = 1.0 - min(1.0, age_months / 36.0)
        cluster_weight = max(
            0.54,
            min(
                0.84,
                0.58
                + 0.16 * recency
                + 0.08 * min(1.0, topic_count / 4.0)
                + 0.06 * dynamics.recency_mix,
            ),
        )
        x = hash_x + (cluster_x - hash_x) * cluster_weight
        y = hash_y + (cluster_y - hash_y) * cluster_weight

        orbit_angle = (
            2.0 * math.pi * (hex_frac(repo_hash, 0, 4) + 0.25 * dynamics.commit_phase)
        )
        orbit_radius = WIDTH * (
            0.018
            + 0.010 * (1.0 - star_norm)
            + 0.010 * min(1.0, topic_count / 4.0)
            + 0.008 * recency
            + 0.006 * hex_frac(repo_hash, 4, 8)
        )
        x += math.cos(orbit_angle) * orbit_radius
        y += math.sin(orbit_angle) * orbit_radius
        clamped_x, clamped_y = _clamp_canvas_position(x, y)
        positions.append([clamped_x, clamped_y])
        language_groups[str(repo.get("language") or "Other")].append(index)

    cohesion = 0.16 + 0.08 * dynamics.repo_density + 0.04 * dynamics.commit_focus
    for indices in language_groups.values():
        if len(indices) < 2:
            continue
        center_x = sum(positions[i][0] for i in indices) / len(indices)
        center_y = sum(positions[i][1] for i in indices) / len(indices)
        ordered = sorted(
            indices,
            key=lambda item: (
                -max(0, int(repos[item].get("stars", 0) or 0)),
                str(repos[item].get("name") or ""),
            ),
        )
        for rank, index in enumerate(ordered):
            repo_hash = seed_hash(
                {
                    "seed": h,
                    "repo": repos[index].get("name", ""),
                    "rank": rank,
                }
            )
            angle = (
                2.0
                * math.pi
                * (rank / len(indices) + hex_frac(repo_hash, 8, 12) * 0.12)
            )
            angle += math.pi * dynamics.day_bias * 0.15
            radius = WIDTH * (
                0.020 + 0.010 * rank + 0.006 * hex_frac(repo_hash, 12, 16)
            )
            target_x = center_x + math.cos(angle) * radius
            target_y = center_y + math.sin(angle) * radius
            positions[index][0] += (target_x - positions[index][0]) * min(
                0.42, cohesion
            )
            positions[index][1] += (target_y - positions[index][1]) * min(
                0.42, cohesion
            )

    affinities = topic_affinity_matrix(repos)
    if affinities:
        adjusted = [pos[:] for pos in positions]
        attraction = 0.12 + 0.08 * dynamics.pr_burst + 0.06 * dynamics.commit_focus
        for (left, right), affinity in affinities.items():
            if affinity <= 0:
                continue
            dx = positions[right][0] - positions[left][0]
            dy = positions[right][1] - positions[left][1]
            move = min(0.22, attraction * affinity) * 0.5
            adjusted[left][0] += dx * move
            adjusted[left][1] += dy * move
            adjusted[right][0] -= dx * move
            adjusted[right][1] -= dy * move
        positions = adjusted

    return [_clamp_canvas_position(x, y) for x, y in positions]


def _derive_dynamics(
    metrics: dict,
    *,
    config: LeniaConfig,
    maturity: float,
    language_mix: dict[str, float],
    repos: list[dict],
    h: str,
) -> LeniaDynamics:
    """Resolve simulation knobs from current and recent GitHub signals."""
    dated_events = [
        {
            "date": _signal_date(
                repo,
                "date",
                "created_at",
                "created",
                "pushed_at",
                "updated_at",
            )
        }
        for repo in repos
        if isinstance(repo, dict)
        and _signal_date(
            repo, "date", "created_at", "created", "pushed_at", "updated_at"
        )
    ]
    dated_events.extend(
        {"date": _signal_date(release, "date", "published_at", "created_at")}
        for release in metrics.get("releases", []) or []
        if isinstance(release, dict)
        and _signal_date(release, "date", "published_at", "created_at")
    )
    dated_events.extend(
        {"date": _signal_date(pr, "merged_at", "date")}
        for pr in metrics.get("recent_merged_prs", []) or []
        if isinstance(pr, dict) and _signal_date(pr, "merged_at", "date")
    )
    timeline_window = normalize_timeline_window(
        dated_events,
        {
            "account_created": metrics.get("account_created"),
            "repos": repos,
            "contributions_monthly": metrics.get("contributions_monthly", {}) or {},
            "contributions_daily": metrics.get("contributions_daily", {}) or {},
        },
        fallback_days=365,
    )
    daily_series = _daily_contribution_series(
        metrics,
        reference_year=timeline_window[1].year,
    )
    recent_activity = _recent_contribution_load(daily_series)
    contribution_energy = math.tanh(
        int(metrics.get("contributions_last_year", 200) or 200) / 420.0
    )
    recent_flux = math.tanh(recent_activity / 90.0)
    language_diversity = _normalized_language_diversity(metrics, language_mix)
    derived = compute_derived_metrics(metrics)
    topic_clusters = metrics.get("topic_clusters", {}) or {}
    topic_diversity = min(1.0, max(len(topic_clusters), derived.topic_diversity) / 6.0)
    raw_streaks = metrics.get("contribution_streaks") or {}
    if isinstance(raw_streaks, dict):
        current_streak = int(raw_streaks.get("current_streak_months", 0) or 0)
        longest_streak = int(raw_streaks.get("longest_streak_months", 0) or 0)
        streak_active = bool(raw_streaks.get("streak_active", False))
    else:
        current_streak = 0
        longest_streak = 0
        streak_active = False
    streak_strength = min(1.0, current_streak / max(1, longest_streak, 6))
    if not streak_active:
        streak_strength *= 0.65

    raw_star_velocity = metrics.get("star_velocity") or {}
    recent_rate = (
        float(raw_star_velocity.get("recent_rate", 0.0) or 0.0)
        if isinstance(raw_star_velocity, dict)
        else 0.0
    )
    velocity = math.tanh(recent_rate / 4.0)
    release_energy = math.tanh(len(metrics.get("releases", []) or []) / 3.0)
    traffic_heat = math.tanh(
        (
            int(metrics.get("traffic_views_14d", 0) or 0)
            + int(metrics.get("traffic_clones_14d", 0) or 0)
        )
        / 360.0
    )
    repo_density = min(1.0, len(repos) / max(1, config.max_repos))
    activity_drive = max(
        0.0,
        min(
            1.0,
            0.28 * repo_density
            + 0.22 * contribution_energy
            + 0.18 * recent_flux
            + 0.12 * streak_strength
            + 0.08 * release_energy
            + 0.07 * velocity
            + 0.05 * topic_diversity,
        ),
    )

    peak_hour, commit_focus, day_bias = _commit_hour_profile(
        metrics.get("commit_hour_distribution")
    )
    pr_density, pr_burst, merged_repo_names = _summarize_merged_pr_cadence(
        metrics.get("recent_merged_prs")
    )
    recency_mix = _recency_signal(metrics, repos)

    mu_drive = min(
        1.0,
        0.34 * math.tanh(int(metrics.get("stars", 0) or 0) / 60.0)
        + 0.16 * velocity
        + 0.12 * traffic_heat
        + 0.10 * language_diversity
        + 0.08 * repo_density
        + 0.10 * pr_burst
        + 0.06 * recency_mix
        + 0.04 * commit_focus,
    )
    sigma_drive = min(
        1.0,
        0.36 * contribution_energy
        + 0.18 * recent_flux
        + 0.14 * streak_strength
        + 0.10 * release_energy
        + 0.08 * language_diversity
        + 0.08 * pr_density
        + 0.06 * (1.0 - commit_focus)
        + 0.05 * recency_mix,
    )
    mu = config.mu_base + config.mu_scale * mu_drive
    sigma = config.sigma_base + config.sigma_scale * sigma_drive

    kernel_profile, r_peak, k_width = _kernel_params_from_mix(
        language_mix,
        h,
        diversity=language_diversity,
        activity=min(1.0, recent_flux + 0.45 * streak_strength + 0.25 * pr_burst),
        recency=recency_mix,
        velocity=velocity,
        pr_burst=pr_burst,
        commit_focus=commit_focus,
        day_bias=day_bias,
    )

    sim_progress = max(
        0.0,
        min(
            1.0,
            0.44 * maturity
            + 0.34 * activity_drive
            + 0.10 * pr_burst
            + 0.07 * commit_focus
            + 0.05 * recency_mix,
        ),
    )
    sim_steps = int(
        config.sim_steps_base
        + config.sim_steps_scale * sim_progress
        + 8 * release_energy
        + 6 * recency_mix
        + 8 * pr_density
        + 4 * velocity
        + 4 * commit_focus
    )
    sim_steps = max(config.sim_steps_base // 2, min(140, sim_steps))

    drift_strength = max(
        1.0,
        (0.55 + 0.45 * max(commit_focus, 0.25))
        * (1.0 + 2.2 * pr_burst + 1.6 * recency_mix),
    )
    commit_angle = 2.0 * math.pi * (peak_hour / 24.0)
    seed_drift = (
        int(round(math.cos(commit_angle) * drift_strength)),
        int(round(math.sin(commit_angle) * drift_strength)),
    )
    satellite_count = int(round(max(pr_burst, recency_mix) * 2.0 + pr_density))

    return LeniaDynamics(
        mu=mu,
        sigma=sigma,
        sim_steps=sim_steps,
        kernel_profile=kernel_profile,
        r_peak=r_peak,
        k_width=k_width,
        pr_burst=pr_burst,
        pr_density=pr_density,
        commit_phase=peak_hour / 24.0,
        commit_focus=commit_focus,
        day_bias=day_bias,
        recency_mix=recency_mix,
        streak_strength=streak_strength,
        repo_density=repo_density,
        recent_flux=recent_flux,
        release_energy=release_energy,
        traffic_heat=traffic_heat,
        activity_drive=activity_drive,
        seed_drift=seed_drift,
        satellite_count=satellite_count,
        merged_repo_names=merged_repo_names,
    )


def _build_seed_specs(
    repos: list[dict],
    daily_series: dict[str, int],
    *,
    config: LeniaConfig,
    h: str,
    timeline_window: tuple[dt_date, dt_date],
    dynamics: LeniaDynamics,
) -> list[_SeedSpec]:
    """Build deterministic organism and nutrient seeds from cumulative signals."""
    N = config.grid_resolution
    timeline_start = timeline_window[0].isoformat()
    span_days = max((timeline_window[1] - timeline_window[0]).days, 1)
    specs: list[_SeedSpec] = []
    commit_angle = 2.0 * math.pi * dynamics.commit_phase
    drift_x, drift_y = dynamics.seed_drift
    satellite_budget = dynamics.satellite_count
    semantic_positions = _semantic_repo_positions(repos, h=h, dynamics=dynamics)

    for repo, (cx, cy) in zip(repos, semantic_positions, strict=False):
        gx = int(cx / WIDTH * N) % N
        gy = int(cy / HEIGHT * N) % N
        repo_name = str(repo.get("name") or "").strip()
        repo_stars = int(repo.get("stars", 0) or 0)
        age_months = int(repo.get("age_months", 1) or 1)
        topic_count = len(repo.get("topics") or [])
        age_norm = math.tanh(age_months / 18.0)
        star_norm = math.tanh(repo_stars / 18.0)
        is_recent = age_months <= 12
        is_fresh = age_months <= 3
        is_merged = repo_name in dynamics.merged_repo_names
        shift_scale = 0.35 + 0.30 * dynamics.recency_mix + 0.20 * dynamics.commit_focus
        if is_recent:
            shift_scale += 0.18
        if is_merged:
            shift_scale += 0.22
        gx = (gx + int(round(drift_x * shift_scale))) % N
        gy = (gy + int(round(drift_y * shift_scale))) % N
        amplitude = 0.24 + 0.26 * star_norm + 0.16 * age_norm
        amplitude += 0.05 * min(1.0, topic_count / 4.0)
        amplitude += 0.06 * dynamics.pr_burst + 0.04 * dynamics.recency_mix
        if is_recent:
            amplitude += 0.04
        if is_merged:
            amplitude += 0.06
        radius = max(
            2,
            int(
                round(
                    config.seed_radius
                    * (
                        0.55
                        + 0.50 * age_norm
                        + 0.25 * star_norm
                        + 0.12 * dynamics.streak_strength
                        - 0.06 * float(is_fresh)
                    )
                )
            ),
        )
        softness = min(
            1.0,
            0.60
            + 0.20 * age_norm
            + 0.10 * star_norm
            + 0.08 * dynamics.commit_focus
            + 0.05 * dynamics.pr_burst,
        )
        specs.append(
            _SeedSpec(
                gx=gx,
                gy=gy,
                radius=radius,
                amplitude=min(0.95, amplitude),
                softness=softness,
                when=_signal_date(
                    repo,
                    "date",
                    "created_at",
                    "created",
                    "pushed_at",
                    "updated_at",
                )
                or timeline_start,
            )
        )

        if satellite_budget > 0 and (is_recent or is_merged):
            satellite_budget -= 1
            sat_angle = commit_angle + (
                math.pi / 3.0 if satellite_budget % 2 == 0 else -math.pi / 3.0
            )
            sat_distance = max(
                1,
                int(round(1.0 + 2.0 * dynamics.pr_burst + 1.5 * dynamics.recency_mix)),
            )
            sat_gx = (gx + int(round(math.cos(sat_angle) * sat_distance))) % N
            sat_gy = (gy + int(round(math.sin(sat_angle) * sat_distance))) % N
            specs.append(
                _SeedSpec(
                    gx=sat_gx,
                    gy=sat_gy,
                    radius=max(1, radius - 1),
                    amplitude=min(0.90, amplitude * (0.72 + 0.10 * dynamics.pr_burst)),
                    softness=min(1.0, softness + 0.08),
                    when=_signal_date(
                        repo,
                        "date",
                        "created_at",
                        "created",
                        "pushed_at",
                        "updated_at",
                    )
                    or timeline_start,
                )
            )

    total_contrib = sum(max(0, int(value or 0)) for value in daily_series.values())
    if daily_series and total_contrib > 0:
        ranked_days = sorted(
            daily_series.items(),
            key=lambda item: (item[1], item[0]),
            reverse=True,
        )
        max_nodes = min(8, 2 + int(math.log1p(total_contrib)))
        for day, count in sorted(ranked_days[:max_nodes], key=lambda item: item[0]):
            amount = max(0, int(count or 0))
            if amount <= 0:
                continue
            try:
                parsed_day = dt_date.fromisoformat(day)
            except ValueError:
                continue
            frac = max(
                0.0,
                min(1.0, (parsed_day - timeline_window[0]).days / span_days),
            )
            day_hash = seed_hash({"seed": h, "day": day})
            angle = (
                2.0
                * math.pi
                * (
                    0.20
                    + 1.25 * frac
                    + 0.18 * dynamics.commit_phase
                    + 0.12 * dynamics.pr_burst
                    + hex_frac(day_hash, 0, 4)
                )
            )
            orbit = (
                0.08
                + 0.30 * math.sqrt(frac)
                + 0.07 * dynamics.recency_mix
                + 0.05 * dynamics.commit_focus
                + 0.08 * hex_frac(day_hash, 4, 8)
            )
            cx = WIDTH * 0.5 + math.cos(angle) * WIDTH * orbit
            cy = HEIGHT * 0.5 + math.sin(angle) * HEIGHT * orbit
            gx = int(cx / WIDTH * N) % N
            gy = int(cy / HEIGHT * N) % N
            intensity = math.tanh(amount / 6.0) * (0.88 + 0.12 * dynamics.pr_density)
            specs.append(
                _SeedSpec(
                    gx=gx,
                    gy=gy,
                    radius=max(1, 1 + int(round(2 * intensity))),
                    amplitude=0.08 + 0.12 * intensity + 0.02 * dynamics.pr_burst,
                    softness=0.42 + 0.25 * intensity + 0.08 * dynamics.commit_focus,
                    when=day,
                )
            )

    if specs:
        return specs

    gx0 = int(hex_frac(h, 0, 4) * N) % N
    gy0 = int(hex_frac(h, 4, 8) * N) % N
    return [
        _SeedSpec(
            gx=gx0,
            gy=gy0,
            radius=config.seed_radius,
            amplitude=0.28,
            softness=0.70,
            when=timeline_start,
        )
    ]


def _build_timeline_lookup(
    seeds: list[_SeedSpec],
    grid_resolution: int,
    *,
    fallback_when: str,
) -> list[list[str]]:
    """Assign each grid cell a reveal date based on its nearest seed influence."""
    if not seeds:
        return [[fallback_when] * grid_resolution for _ in range(grid_resolution)]

    lookup: list[list[str]] = []
    for gy in range(grid_resolution):
        row: list[str] = []
        for gx in range(grid_resolution):
            best_when = fallback_when
            best_score = float("inf")
            for spec in seeds:
                dx = gx - spec.gx
                dy = gy - spec.gy
                radius = max(1.0, float(spec.radius))
                score = (dx * dx + dy * dy) / (radius * radius * (0.6 + spec.amplitude))
                if score < best_score:
                    best_score = score
                    best_when = spec.when
            row.append(best_when)
        lookup.append(row)
    return lookup


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def generate(
    metrics: dict,
    *,
    seed: str | None = None,
    maturity: float | None = None,
    timeline: bool = True,
    loop_duration: float = 60.0,
    reveal_fraction: float = 0.93,
) -> str:
    """Generate a Lenia continuous cellular automata SVG.

    Parameters
    ----------
    metrics:
        GitHub profile metrics dict (repos, stars, contributions, etc.).
    seed:
        Optional deterministic seed override.
    maturity:
        0.0-1.0 growth stage. ``None`` auto-computes from metrics.
    timeline:
        Enable CSS reveal animation synced to contribution timeline.
    loop_duration:
        Total animation loop duration in seconds.
    reveal_fraction:
        Fraction of loop_duration used for progressive reveal.

    Returns
    -------
    str
        Complete SVG document as a string.
    """
    config = CFG
    mat = maturity if maturity is not None else compute_maturity(metrics)
    timeline_enabled = bool(timeline and loop_duration > 0)
    growth_mat = 1.0 if timeline_enabled else mat

    # ── WorldState ────────────────────────────────────────────────
    world: WorldState = compute_world_state(metrics)
    world.palette = _build_world_palette_extended(
        world.time_of_day,
        world.weather,
        world.season,
        world.energy,
        daylight_hue_drift=world.daylight_hue_drift,
        weather_severity=world.weather_severity,
        season_transition_weights=world.season_transition_weights,
        activity_pressure=world.activity_pressure,
    )

    # ── Deterministic RNG ─────────────────────────────────────────
    h = seed_hash({"seed": seed}) if seed is not None else seed_hash(metrics)
    rng = np.random.default_rng(int(h[:8], 16))

    # ── Extract data ──────────────────────────────────────────────
    repos = metrics.get("top_repos") or metrics.get("repos") or []
    all_repos = metrics.get("repos") or repos
    monthly = metrics.get("contributions_monthly", {}) or {}
    releases = metrics.get("releases", []) or []
    recent_merged_prs = metrics.get("recent_merged_prs", []) or []
    primary_repos, _ = select_primary_repos(repos, limit=config.max_repos)
    language_mix = _extract_language_mix(all_repos, metrics.get("languages"))

    dated_events = [
        {
            "date": _signal_date(
                repo, "date", "created_at", "created", "pushed_at", "updated_at"
            )
        }
        for repo in repos
        if isinstance(repo, dict)
        and _signal_date(
            repo, "date", "created_at", "created", "pushed_at", "updated_at"
        )
    ]
    dated_events.extend(
        {"date": _signal_date(release, "date", "published_at", "created_at")}
        for release in releases
        if isinstance(release, dict)
        and _signal_date(release, "date", "published_at", "created_at")
    )
    dated_events.extend(
        {"date": _signal_date(pr, "merged_at", "date")}
        for pr in recent_merged_prs
        if isinstance(pr, dict) and _signal_date(pr, "merged_at", "date")
    )
    timeline_window = normalize_timeline_window(
        dated_events,
        {
            "account_created": metrics.get("account_created"),
            "repos": repos,
            "contributions_monthly": monthly,
            "contributions_daily": metrics.get("contributions_daily", {}),
        },
        fallback_days=365,
    )
    daily_series = _daily_contribution_series(
        metrics,
        reference_year=timeline_window[1].year,
    )

    dynamics = _derive_dynamics(
        metrics,
        config=config,
        maturity=mat,
        language_mix=language_mix,
        repos=all_repos,
        h=h,
    )
    primary_repos = _augment_primary_repos(
        primary_repos,
        all_repos,
        merged_repo_names=dynamics.merged_repo_names,
        limit=config.max_repos,
    )
    palette = _build_lenia_palette(
        world,
        language_mix=language_mix,
        repos=primary_repos,
        dynamics=dynamics,
        h=h,
    )
    kernel = _build_kernel(
        config.kernel_radius,
        dynamics.r_peak,
        dynamics.k_width,
        profile=dynamics.kernel_profile,
    )

    # ── Seed organism positions ───────────────────────────────────
    N = config.grid_resolution
    seed_specs = _build_seed_specs(
        primary_repos,
        daily_series,
        config=config,
        h=h,
        timeline_window=timeline_window,
        dynamics=dynamics,
    )
    timeline_lookup = _build_timeline_lookup(
        seed_specs,
        N,
        fallback_when=timeline_window[0].isoformat(),
    )

    # ── Initialize field ──────────────────────────────────────────
    field = np.zeros((N, N), dtype=np.float64)
    _seed_organisms(field, seed_specs, rng)
    seed_field = field.copy()

    # ── Simulate ──────────────────────────────────────────────────
    sim_energy = min(
        1.35,
        0.45
        + 0.35 * world.energy
        + 0.18 * world.vitality
        + 0.12 * world.aurora_intensity
        + 0.14 * dynamics.recent_flux
        + 0.08 * dynamics.traffic_heat,
    )
    field = _simulate(
        field,
        kernel,
        dynamics.mu,
        dynamics.sigma,
        dynamics.sim_steps,
        config.dt,
        sim_energy,
    )
    residue_gain = min(
        1.0,
        0.55
        + 0.35 * dynamics.activity_drive
        + 0.15 * dynamics.repo_density
        + 0.10 * dynamics.release_energy,
    )
    field = np.maximum(field, np.clip(seed_field * residue_gain, 0.0, 1.0))

    # ── Render ────────────────────────────────────────────────────
    return _render_svg(
        field,
        config=config,
        palette=palette,
        timeline=timeline_enabled,
        timeline_lookup=timeline_lookup,
        timeline_window=timeline_window,
        loop_duration=loop_duration,
        reveal_fraction=reveal_fraction,
        growth_mat=growth_mat,
    )
