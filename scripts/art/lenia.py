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
from typing import Any

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
    HEIGHT,
    LANG_HUES,
    MAX_REPOS,
    WIDTH,
    DerivedMetrics,
    ElementBudget,
    Noise2D,
    StyleDialect,
    WorldState,
    _build_world_palette_extended,
    blend_mode_filter,
    build_style_dialect,
    compute_derived_metrics,
    compute_maturity,
    compute_world_state,
    contributions_monthly_to_daily_series,
    dialect_group_markup,
    hex_frac,
    map_date_to_loop_delay,
    normalize_timeline_window,
    oklch,
    oklch_lerp,
    order_repos_for_visual_plan,
    repo_to_canvas_position,
    repo_visibility_score,
    resolve_render_metrics,
    seed_hash,
    select_primary_repos,
    topic_affinity_matrix,
    volumetric_glow_filter,
)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class LeniaConfig:
    """Tunable parameters for the Lenia simulation and rendering."""

    max_repos: int = MAX_REPOS
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
    kind: str = "repo"
    visibility: float = 1.0


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


def _signed_hue_delta(source: float, target: float) -> float:
    """Return the signed shortest hue delta from *target* toward *source*."""
    return ((source - target + 540.0) % 360.0) - 180.0


def _place_satellite_cell(
    gx: int,
    gy: int,
    *,
    angle: float,
    distance: float,
    grid: int,
) -> tuple[int, int]:
    """Offset a satellite without toroidal wrap so SVG extent stays readable."""
    dx = int(round(math.cos(angle) * distance))
    dy = int(round(math.sin(angle) * distance))
    sat_gx = gx + dx
    sat_gy = gy + dy
    if not (0 <= sat_gx < grid and 0 <= sat_gy < grid):
        sat_gx = gx - dx
        sat_gy = gy - dy
    last = max(0, grid - 1)
    return (min(last, max(0, sat_gx)), min(last, max(0, sat_gy)))


def _extent_distance_cells(
    extent_gain: float,
    *,
    extra_idx: int = 0,
    burst: float = 0.0,
    recency: float = 0.0,
    visibility: float = 1.0,
) -> int:
    """Satellite offset in grid cells (8 px on the 400 GIF)."""
    if extent_gain <= 0:
        return max(2, int(round(1.6 + extra_idx + 1.4 * burst + 0.8 * recency)))
    span = (
        5.2
        + 11.0 * extent_gain
        + extra_idx * (1.8 + 2.6 * extent_gain)
        + 1.4 * burst
        + 1.0 * recency
        + 0.8 * (1.0 - visibility)
    )
    return max(5, int(round(span)))


def _select_organism_cells(
    cells: list[tuple[float, int, int]],
    *,
    cap: int,
) -> list[tuple[float, int, int]]:
    """Keep the brightest field cells with spatial coverage under a draw cap."""
    if cap <= 0:
        return []
    if len(cells) <= cap:
        return cells
    ranked = sorted(cells, key=lambda item: item[0], reverse=True)
    stride = max(1, int(math.ceil(math.sqrt(len(cells) / cap))))
    kept: list[tuple[float, int, int]] = []
    occupied: set[tuple[int, int]] = set()
    for value, gx, gy in ranked:
        bucket = (gx // stride, gy // stride)
        if bucket in occupied and value < 0.52:
            continue
        occupied.add(bucket)
        kept.append((value, gx, gy))
        if len(kept) >= cap:
            break
    kept.sort(key=lambda item: item[0])
    return kept


def _clamp_canvas_position(x: float, y: float) -> tuple[float, float]:
    """Keep semantic layout positions safely inside the canvas frame."""
    return (
        max(WIDTH * 0.08, min(WIDTH * 0.92, x)),
        max(HEIGHT * 0.08, min(HEIGHT * 0.92, y)),
    )


def _dense_repo_signal(repo_count: int, *, baseline: int) -> float:
    """Return a soft density signal that keeps rising past the baseline."""
    if repo_count <= 0:
        return 0.0
    return min(1.0, math.log1p(repo_count) / math.log1p(max(2, baseline * 4)))


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
    repos: list[dict[str, Any]],
    dynamics: LeniaDynamics,
    h: str,
) -> _LeniaPalette:
    """Resolve one dark morphogenetic look from language and activity signals."""
    language_entries = sorted(
        ((lang, float(weight)) for lang, weight in language_mix.items() if weight > 0),
        key=lambda item: (item[1], item[0]),
        reverse=True,
    )[:4]
    hue_entries = [
        (float(LANG_HUES.get(lang, 260.0)), weight) for lang, weight in language_entries
    ]
    dominant_hue = _circular_hue_average(hue_entries, fallback=260.0)
    dominant_share = language_entries[0][1] if language_entries else 1.0
    language_diversity = min(1.0, len(language_entries) / 4.0)
    hue_nudge = _signed_hue_delta(dominant_hue, 280.0)
    seed_jitter = hex_frac(h, 16, 20)

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
    glow_mix = min(
        1.0,
        0.34 * world.energy
        + 0.16 * world.aurora_intensity
        + 0.16 * dynamics.pr_burst
        + 0.16 * dynamics.recency_mix
        + 0.10 * dynamics.activity_drive
        + 0.08 * topic_signal,
    )

    bg_hue = (
        280.0 + 0.14 * hue_nudge + 10.0 * dynamics.recency_mix + 6.0 * seed_jitter
    ) % 360.0
    bg_light = (
        0.072
        + 0.018 * world.energy
        + 0.012 * dynamics.activity_drive
        + 0.008 * recent_repo_share
    )
    bg_chroma = 0.036 + 0.014 * dominant_share + 0.008 * world.activity_pressure
    background = oklch_lerp(
        _BG_COLOR,
        oklch(bg_light, bg_chroma, bg_hue),
        min(
            0.32,
            0.10
            + 0.12 * dominant_share
            + 0.08 * dynamics.activity_drive
            + 0.06 * glow_mix,
        ),
    )

    lang_lean = 0.16 + 0.12 * dominant_share
    energy_lift = 0.06 * world.energy + 0.05 * dynamics.recency_mix + 0.04 * glow_mix
    stops: list[tuple[float, str]] = []
    for _band_lo, field_hi, light, chroma, hue in _BIO_RAMP:
        if light <= 0.0 and chroma <= 0.0:
            continue
        mixed_hue = (hue + lang_lean * hue_nudge) % 360.0
        mixed_light = min(0.94, light + energy_lift)
        mixed_chroma = max(0.05, chroma * (0.90 + 0.12 * language_diversity))
        color = oklch(mixed_light, mixed_chroma, mixed_hue)
        if not stops:
            stops.append((0.05, color))
        stops.append((field_hi, color))

    peak = stops[-1][1] if stops else oklch(0.85, 0.12, 140.0)
    core = oklch_lerp(
        peak,
        oklch(
            min(0.92, 0.82 + 0.08 * glow_mix + 0.04 * recent_repo_share),
            0.10 + 0.04 * language_diversity,
            (140.0 + 0.20 * hue_nudge) % 360.0,
        ),
        0.28 + 0.22 * glow_mix,
    )
    if stops:
        last_cutoff, _ = stops[-1]
        stops[-1] = (last_cutoff, core)
    ramp = tuple(stops) if stops else ((1.0, core),)
    return _LeniaPalette(background=background, ramp=ramp, core=core)


def _field_to_color(value: float, palette: _LeniaPalette) -> tuple[str, float]:
    """Map a field value to a discrete ramp stop; keep a smooth opacity ramp."""
    if not palette.ramp or value < palette.ramp[0][0]:
        return _BG_COLOR, 0.0
    prev_cutoff, prev_color = palette.ramp[0]
    for cutoff, color in palette.ramp[1:]:
        if value <= cutoff:
            t = (value - prev_cutoff) / max(0.001, cutoff - prev_cutoff)
            opacity = max(0.0, min(1.0, 0.50 + 0.50 * (0.35 * t + 0.65 * value)))
            snapped = prev_color if t < 0.5 else color
            return snapped, opacity
        prev_cutoff, prev_color = cutoff, color
    return palette.ramp[-1][1], 1.0


# ---------------------------------------------------------------------------
# SVG rendering
# ---------------------------------------------------------------------------


def _render_svg(
    field: np.ndarray,
    *,
    config: LeniaConfig,
    field_threshold: float,
    palette: _LeniaPalette,
    seed_specs: list[_SeedSpec],
    timeline: bool,
    timeline_lookup: list[list[str]],
    timeline_window: tuple[dt_date, dt_date],
    loop_duration: float,
    reveal_fraction: float,
    growth_mat: float,
    dialect: StyleDialect | None = None,
    field_gain: float = 0.0,
    extent_gain: float = 0.0,
    simulation_mix: float = 0.0,
    sim_steps: int = 0,
) -> str:
    """Render the Lenia field as an SVG of glowing circles."""
    N = config.grid_resolution
    cell_size = WIDTH / N  # 800/50 = 16
    budget = ElementBudget(config.max_elements)

    P: list[str] = []

    # ── SVG header ────────────────────────────────────────────────
    dialect_attrs = dialect.svg_attrs() if dialect is not None else ""
    P.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" '
        f'width="{WIDTH}" height="{HEIGHT}" {dialect_attrs} '
        f'data-field-gain="{field_gain:.3f}" data-extent-gain="{extent_gain:.3f}" '
        f'data-simulation-mix="{simulation_mix:.3f}" data-sim-steps="{sim_steps}" '
        f'data-halo-scale="{(dialect.knobs["halo_scale"] if dialect is not None else 1.0):.3f}" '
        f'data-satellite-count="{sum(1 for spec in seed_specs if spec.kind == "satellite")}">'
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

    # ── Seed halos, secondary populations, and nutrient dust ─────
    if seed_specs:
        repo_seed_color = palette.core
        satellite_seed_color = (
            palette.ramp[min(2, len(palette.ramp) - 1)][1]
            if palette.ramp
            else palette.core
        )
        nutrient_seed_color = (
            palette.ramp[min(1, len(palette.ramp) - 1)][1]
            if palette.ramp
            else palette.core
        )
        P.append("<g>")
        for spec in seed_specs:
            if not budget.ok():
                break
            cx = (spec.gx + 0.5) * cell_size
            cy = (spec.gy + 0.5) * cell_size
            if spec.kind == "repo":
                seed_color = repo_seed_color
                halo_boost = dialect.knobs["halo_scale"] if dialect is not None else 1.0
                halo_radius = (
                    cell_size
                    * (0.34 + 0.28 * spec.radius + 0.16 * spec.visibility)
                    * halo_boost
                )
                star_ink = 0.70 + 0.30 * max(0.0, min(1.0, (halo_boost - 0.75) / 0.70))
                halo_opacity = min(
                    0.90,
                    (0.36 + 0.16 * spec.visibility + 0.10 * spec.amplitude)
                    * star_ink
                    * _visible_mark_fade(
                        growth_mat,
                        0.55 + 0.25 * spec.visibility,
                        floor=0.60,
                    ),
                )
            elif spec.kind == "satellite":
                seed_color = satellite_seed_color
                halo_radius = (
                    cell_size
                    * (0.42 + 0.20 * spec.radius + 0.12 * spec.visibility)
                    * (1.05 + 0.90 * extent_gain)
                )
                halo_opacity = min(
                    0.78,
                    (0.30 + 0.14 * spec.visibility + 0.10 * spec.amplitude)
                    * _visible_mark_fade(
                        growth_mat,
                        0.45 + 0.20 * spec.visibility,
                        floor=0.58,
                    ),
                )
            else:
                seed_color = nutrient_seed_color
                halo_radius = cell_size * (0.16 + 0.14 * spec.radius)
                halo_opacity = min(
                    0.42,
                    (0.14 + 0.08 * spec.visibility + 0.06 * spec.amplitude)
                    * _visible_mark_fade(
                        growth_mat,
                        0.30 + 0.18 * spec.visibility,
                        floor=0.50,
                    ),
                )
            if halo_opacity < 0.01:
                continue
            if timeline:
                delay = map_date_to_loop_delay(
                    spec.when,
                    timeline_window,
                    duration=loop_duration,
                    reveal_fraction=reveal_fraction,
                )
                halo_attrs = (
                    f'class="tl-reveal" '
                    f'style="opacity:{halo_opacity:.3f};--delay:{delay:.3f}s;'
                    f'--to:{halo_opacity:.3f};--dur:{loop_duration:.2f}s" '
                    f'data-delay="{delay:.3f}" data-when="{spec.when}"'
                )
            else:
                halo_attrs = f'opacity="{halo_opacity:.3f}"'
            halo_scale_attr = (
                f' data-halo-scale="{dialect.knobs["halo_scale"]:.3f}"'
                if spec.kind == "repo" and dialect is not None
                else ""
            )
            halo_role = (
                "lenia-seed-halo" if spec.kind != "nutrient" else "lenia-nutrient-halo"
            )
            P.append(
                f'<circle data-role="{halo_role}" data-kind="{spec.kind}"'
                f"{halo_scale_attr} "
                f'cx="{cx:.1f}" cy="{cy:.1f}" r="{halo_radius:.1f}" '
                f'fill="{seed_color}" {halo_attrs}/>'
            )
            budget.add(1)
            if spec.kind != "nutrient" and budget.ok() and timeline:
                orbit_opacity = halo_opacity * (0.44 if spec.kind == "repo" else 0.36)
                orbit_rx = halo_radius * (1.8 + 0.2 * (1.0 - spec.visibility))
                orbit_ry = orbit_rx * (0.62 if spec.kind == "repo" else 0.48)
                if timeline:
                    delay = map_date_to_loop_delay(
                        spec.when,
                        timeline_window,
                        duration=loop_duration,
                        reveal_fraction=reveal_fraction,
                    )
                    orbit_attrs = (
                        f'class="tl-reveal" '
                        f'style="opacity:{orbit_opacity:.3f};--delay:{delay:.3f}s;'
                        f'--to:{orbit_opacity:.3f};--dur:{loop_duration:.2f}s" '
                        f'data-delay="{delay:.3f}" data-when="{spec.when}"'
                    )
                else:
                    orbit_attrs = f'opacity="{orbit_opacity:.3f}"'
                P.append(
                    f'<ellipse data-role="lenia-seed-orbit" data-kind="{spec.kind}" '
                    f'cx="{cx:.1f}" cy="{cy:.1f}" rx="{orbit_rx:.1f}" ry="{orbit_ry:.1f}" '
                    f'fill="none" stroke="{seed_color}" stroke-width="0.7" {orbit_attrs}/>'
                )
                budget.add(1)
        P.append("</g>")

    # ── Organism circles ──────────────────────────────────────────
    P.append('<g data-role="lenia-field">')

    # Collect cells above threshold, sort by value for layering
    cells: list[tuple[float, int, int]] = []
    for gy in range(N):
        for gx in range(N):
            v = float(field[gy, gx])
            if v > field_threshold:
                cells.append((v, gx, gy))
    cells.sort(key=lambda c: c[0])
    organism_cap = 16 + int(round(28.0 * max(0.0, min(1.5, field_gain))))
    drawn_cells = _select_organism_cells(
        cells, cap=min(organism_cap, max(0, budget.remaining))
    )

    for v, gx, gy in drawn_cells:
        if not budget.ok():
            break

        color, opacity = _field_to_color(v, palette)
        if opacity < 0.01:
            continue

        cx = (gx + 0.5) * cell_size
        cy = (gy + 0.5) * cell_size
        r = cell_size * 0.70 * (0.68 + 0.62 * v) * (0.94 + 0.26 * field_gain)

        mat_opacity = min(
            0.96,
            opacity
            * _visible_mark_fade(growth_mat, v, floor=0.52)
            * (0.88 + 0.28 * field_gain),
        )

        style_parts: list[str] = []
        if timeline:
            when = timeline_lookup[gy][gx]
            delay = map_date_to_loop_delay(
                when,
                timeline_window,
                duration=loop_duration,
                reveal_fraction=reveal_fraction,
            )
            # Keep a visible inline opacity fallback for static SVG rasterizers.
            style_parts.append(
                f'class="tl-reveal" '
                f'style="opacity:{mat_opacity:.3f};--delay:{delay:.3f}s;'
                f'--to:{mat_opacity:.3f};--dur:{loop_duration:.2f}s" '
                f'data-delay="{delay:.3f}" data-when="{when}"'
            )
        else:
            style_parts.append(f'opacity="{mat_opacity:.3f}"')

        P.append(
            f'<circle data-role="lenia-organism" cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" '
            f'fill="{color}" {" ".join(style_parts)}/>'
        )
        budget.add(1)

    P.append("</g>")

    # ── Bright core highlights for high-value cells ───────────────
    core_lo = max(0.40, 0.58 - 0.18 * field_gain)
    core_candidates = [cell for cell in drawn_cells if cell[0] >= core_lo]
    core_candidates.sort(key=lambda item: item[0], reverse=True)
    core_cells = core_candidates[:16] if timeline else []
    P.append('<g data-role="lenia-field-core">')
    for v, gx, gy in core_cells:
        if v < core_lo or not budget.ok():
            continue
        cx = (gx + 0.5) * cell_size
        cy = (gy + 0.5) * cell_size
        r = cell_size * 0.28 * v * (0.90 + 0.20 * field_gain)
        core_color = palette.core
        core_opacity = (
            0.38
            * (v - core_lo)
            / max(0.08, 1.0 - core_lo)
            * _visible_mark_fade(growth_mat, v, floor=0.48)
        )
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
                f'<circle data-role="lenia-organism-core" cx="{cx:.1f}" cy="{cy:.1f}" '
                f'r="{r:.1f}" fill="{core_color}" class="tl-reveal" '
                f'style="opacity:{core_opacity:.3f};--delay:{delay:.3f}s;'
                f'--to:{core_opacity:.3f};--dur:{loop_duration:.2f}s" '
                f'data-delay="{delay:.3f}" data-when="{when}"/>'
            )
        else:
            P.append(
                f'<circle data-role="lenia-organism-core" cx="{cx:.1f}" cy="{cy:.1f}" '
                f'r="{r:.1f}" fill="{core_color}" opacity="{core_opacity:.3f}"/>'
            )
        budget.add(1)
    P.append("</g>")

    if dialect is not None:
        P.append(dialect_group_markup(dialect))
    P.append("</svg>")
    return "\n".join(P)


def _fade_ramp(growth_mat: float, field_value: float) -> float:
    """Keep low-maturity static exports legible while preserving a maturity ramp."""
    # Timelapse snapshots for sparse histories can stay near zero maturity for a
    # long time. Preserve a dim organism residue so static rasterization does not
    # collapse to a monochrome background, then ramp toward full intensity.
    threshold = 0.04 + 0.22 * field_value
    reveal = max(
        0.0,
        min(1.0, (growth_mat - threshold) / max(0.001, 1.0 - threshold)),
    )
    low_maturity_gain = min(1.0, growth_mat * 28.0)
    residue_floor = (0.20 + 0.18 * low_maturity_gain + 0.14 * growth_mat) * (
        1.0 - 0.35 * field_value
    )
    return max(reveal, min(0.50, max(0.12, residue_floor)))


def _visible_mark_fade(growth_mat: float, field_value: float, *, floor: float) -> float:
    """Lift GIF-scale marks above the residue floor without flattening maturity."""
    return min(1.0, floor + (1.0 - floor) * _fade_ramp(growth_mat, field_value))


# ---------------------------------------------------------------------------
# Metric signal extraction
# ---------------------------------------------------------------------------


def _signal_date(entry: object, *keys: str) -> str | None:
    """Return the first usable ISO date string from *entry*."""
    if not isinstance(entry, dict):
        return None
    for key in keys:
        value = entry.get(key)
        if isinstance(value, str) and value.strip():
            return value[:10] if len(value) >= 10 else value
    return None


def _extract_language_mix(
    repos: list[dict[str, Any]],
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
        lang_raw = repo.get("language")
        if not lang_raw:
            continue
        lang = str(lang_raw)
        star_weight = 1.0 + 0.35 * math.log1p(int(repo.get("stars", 0) or 0))
        weights[lang] = weights.get(lang, 0.0) + star_weight

    total = max(1.0, sum(weights.values()))
    return {k: v / total for k, v in weights.items()}


def _normalized_language_diversity(
    metrics: dict[str, Any],
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
    metrics: dict[str, Any],
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


def _recency_signal(metrics: dict[str, Any], repos: list[dict[str, Any]]) -> float:
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
        if isinstance(raw_hour, bool) or not isinstance(raw_hour, (int, float, str)):
            continue
        if isinstance(raw_count, bool) or not isinstance(raw_count, (int, float, str)):
            continue
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

        raw_additions = pr.get("additions", 0)
        raw_deletions = pr.get("deletions", 0)
        additions = max(0, int(str(raw_additions or 0)))
        deletions = max(0, int(str(raw_deletions or 0)))
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
    primary_repos: list[dict[str, Any]],
    all_repos: list[dict[str, Any]],
    *,
    merged_repo_names: frozenset[str],
    limit: int,
) -> list[dict[str, Any]]:
    """Promote merged or fresh repos without truncating the full seed pool."""
    if not all_repos:
        return primary_repos
    _ = limit

    def _priority(repo: dict[str, Any]) -> tuple[int, int, float, float, int, str]:
        name = str(repo.get("name") or "").strip()
        age_months = int(repo.get("age_months", 0) or 0)
        is_recent = age_months > 0 and age_months <= 12
        return (
            1 if name in merged_repo_names else 0,
            1 if is_recent else 0,
            repo_visibility_score(repo),
            float(repo.get("stars", 0) or 0.0),
            -age_months if age_months > 0 else 0,
            name,
        )

    boosted = sorted(all_repos, key=_priority, reverse=True)
    active_candidates = [
        repo for repo in boosted if _priority(repo)[0] > 0 or _priority(repo)[1] > 0
    ]
    seen: set[str] = set()
    selected: list[dict[str, Any]] = []
    for repo in active_candidates + primary_repos:
        name = str(repo.get("name") or "").strip()
        key = name or f"repo-{len(selected)}"
        if key in seen:
            continue
        selected.append(repo)
        seen.add(key)
    for repo in all_repos:
        name = str(repo.get("name") or "").strip()
        key = name or f"repo-{len(selected)}"
        if key in seen:
            continue
        selected.append(repo)
        seen.add(key)
    return selected or primary_repos or all_repos


def _semantic_repo_positions(
    repos: list[dict[str, Any]],
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
    metrics: dict[str, Any],
    *,
    config: LeniaConfig,
    maturity: float,
    language_mix: dict[str, float],
    repos: list[dict[str, Any]],
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
    repo_density = _dense_repo_signal(len(repos), baseline=config.max_repos)
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
    dialect = build_style_dialect("lenia", metrics)

    mu_drive = min(
        1.0,
        0.26 * dialect.channels.star_scale
        + 0.14 * math.tanh(int(metrics.get("stars", 0) or 0) / 60.0)
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
        + 10 * dialect.knobs["field_gain"]
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
    satellite_count = int(
        round(
            max(pr_burst, recency_mix) * 2.0
            + pr_density
            + 3.0 * dialect.knobs["extent_gain"]
        )
    )

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
    repos: list[dict[str, Any]],
    daily_series: dict[str, int],
    *,
    config: LeniaConfig,
    h: str,
    timeline_window: tuple[dt_date, dt_date],
    dynamics: LeniaDynamics,
    extent_gain: float = 0.0,
) -> list[_SeedSpec]:
    """Build deterministic organism and nutrient seeds from cumulative signals."""
    N = config.grid_resolution
    timeline_start = timeline_window[0].isoformat()
    span_days = max((timeline_window[1] - timeline_window[0]).days, 1)
    specs: list[_SeedSpec] = []
    commit_angle = 2.0 * math.pi * dynamics.commit_phase
    drift_x, drift_y = dynamics.seed_drift
    visibility_scores = [repo_visibility_score(repo) for repo in repos]
    visibility_max = max(visibility_scores, default=1.0)
    visibility_min = min(visibility_scores, default=0.0)
    visibility_span = max(0.001, visibility_max - visibility_min)
    visibility_norms = [
        (
            0.18 + 0.82 * ((score - visibility_min) / visibility_span)
            if len(visibility_scores) > 1
            else 1.0
        )
        for score in visibility_scores
    ]
    crowding_scale = max(
        0.46,
        1.0 / math.sqrt(max(1.0, len(repos) / max(1, config.max_repos))),
    )
    satellite_budget = dynamics.satellite_count + int(
        round(math.sqrt(max(0.0, float(len(repos) - config.max_repos))))
    )
    semantic_positions = _semantic_repo_positions(repos, h=h, dynamics=dynamics)

    for index, (repo, (cx, cy)) in enumerate(
        zip(repos, semantic_positions, strict=False)
    ):
        gx = int(cx / WIDTH * N) % N
        gy = int(cy / HEIGHT * N) % N
        repo_name = str(repo.get("name") or "").strip()
        repo_stars = int(repo.get("stars", 0) or 0)
        age_months = int(repo.get("age_months", 1) or 1)
        topic_count = len(repo.get("topics") or [])
        visibility = visibility_norms[index] if index < len(visibility_norms) else 1.0
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
        amplitude += 0.08 * dynamics.activity_drive + 0.04 * dynamics.pr_density
        if is_recent:
            amplitude += 0.06
        if is_merged:
            amplitude += 0.10
        amplitude *= (0.56 + 0.60 * visibility) * (0.84 + 0.16 * crowding_scale)
        radius = max(
            1,
            int(
                round(
                    config.seed_radius
                    * (
                        0.55
                        + 0.50 * age_norm
                        + 0.25 * star_norm
                        + 0.12 * dynamics.streak_strength
                        + 0.14 * dynamics.recency_mix
                        + 0.10 * dynamics.pr_burst
                        + 0.08 * float(is_recent)
                        - 0.02 * float(is_fresh)
                    )
                    * (0.52 + 0.48 * visibility)
                    * crowding_scale
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
                kind="repo",
                visibility=visibility,
            )
        )

        if satellite_budget > 0 and (is_recent or is_merged or visibility < 0.45):
            satellite_budget -= 1
            sat_angle = commit_angle + (
                math.pi / 3.0 if satellite_budget % 2 == 0 else -math.pi / 3.0
            )
            sat_distance = _extent_distance_cells(
                extent_gain,
                burst=dynamics.pr_burst,
                recency=dynamics.recency_mix,
                visibility=visibility,
            )
            sat_gx, sat_gy = _place_satellite_cell(
                gx,
                gy,
                angle=sat_angle,
                distance=float(sat_distance),
                grid=N,
            )
            specs.append(
                _SeedSpec(
                    gx=sat_gx,
                    gy=sat_gy,
                    radius=max(1, radius),
                    amplitude=min(
                        0.90,
                        amplitude
                        * (0.46 + 0.20 * (1.0 - visibility) + 0.12 * dynamics.pr_burst),
                    ),
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
                    kind="satellite",
                    visibility=max(0.22, visibility * 0.88),
                )
            )

    repo_hosts = [spec for spec in specs if spec.kind == "repo"]
    if extent_gain > 0 and repo_hosts:
        forced_count = 1 + int(round(3.0 * extent_gain))
        for extra_idx in range(forced_count):
            host_spec = repo_hosts[extra_idx % len(repo_hosts)]
            host = repos[extra_idx % len(repos)]
            sat_angle = commit_angle + extra_idx * (math.tau / max(3, forced_count))
            sat_distance = _extent_distance_cells(
                extent_gain,
                extra_idx=extra_idx,
                burst=dynamics.pr_burst,
                recency=dynamics.recency_mix,
            )
            sat_gx, sat_gy = _place_satellite_cell(
                host_spec.gx,
                host_spec.gy,
                angle=sat_angle,
                distance=float(sat_distance),
                grid=N,
            )
            specs.append(
                _SeedSpec(
                    gx=sat_gx,
                    gy=sat_gy,
                    radius=max(1, 1 + extra_idx % 2),
                    amplitude=min(0.82, 0.28 + 0.18 * extent_gain),
                    softness=0.72,
                    when=_signal_date(
                        host,
                        "date",
                        "created_at",
                        "created",
                        "pushed_at",
                        "updated_at",
                    )
                    or timeline_start,
                    kind="satellite",
                    visibility=max(0.22, 0.34 + 0.40 * extent_gain),
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
            orbit_scale = 1.0 if extent_gain <= 0 else 0.90 + 0.70 * extent_gain
            orbit = (
                0.08
                + 0.30 * math.sqrt(frac)
                + 0.07 * dynamics.recency_mix
                + 0.05 * dynamics.commit_focus
                + 0.08 * hex_frac(day_hash, 4, 8)
            ) * orbit_scale
            cx = WIDTH * 0.5 + math.cos(angle) * WIDTH * orbit
            cy = HEIGHT * 0.5 + math.sin(angle) * HEIGHT * orbit
            gx = int(cx / WIDTH * N) % N
            gy = int(cy / HEIGHT * N) % N
            intensity = math.tanh(amount / 6.0) * (0.88 + 0.12 * dynamics.pr_density)
            specs.append(
                _SeedSpec(
                    gx=gx,
                    gy=gy,
                    radius=max(1, 1 + int(round(2.5 * intensity + dynamics.pr_burst))),
                    amplitude=0.08 + 0.12 * intensity + 0.02 * dynamics.pr_burst,
                    softness=0.42 + 0.25 * intensity + 0.08 * dynamics.commit_focus,
                    when=day,
                    kind="nutrient",
                    visibility=min(1.0, 0.24 + 0.52 * intensity),
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
            kind="repo",
            visibility=0.4,
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
    metrics: dict[str, Any],
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
    metrics = resolve_render_metrics(metrics)
    dialect = build_style_dialect("lenia", metrics)
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
    raw_repos = metrics.get("repos") or metrics.get("top_repos") or []
    preferred_repo_names = metrics.get("repo_visual_order")
    repos = order_repos_for_visual_plan(
        list(raw_repos) if isinstance(raw_repos, list) else [],
        preferred_names=(
            preferred_repo_names
            if isinstance(preferred_repo_names, (list, tuple))
            else None
        ),
    )
    all_repos = repos
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

    field_gain = float(dialect.knobs["field_gain"])
    extent_gain = float(dialect.knobs["extent_gain"])
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
        extent_gain=extent_gain,
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
    sim_steps = max(
        config.sim_steps_base // 2,
        min(140, dynamics.sim_steps + int(round(16 * field_gain))),
    )
    field = _simulate(
        field,
        kernel,
        dynamics.mu,
        dynamics.sigma,
        sim_steps,
        config.dt,
        sim_energy,
    )
    residue_gain = min(
        1.0,
        0.58
        + 0.28 * dynamics.activity_drive
        + 0.10 * dynamics.repo_density
        + 0.08 * dynamics.release_energy,
    )
    seed_residue = np.clip(seed_field * residue_gain, 0.0, 1.0)
    simulation_mix = min(
        1.0,
        0.16
        + 0.74 * field_gain
        + 0.06 * dynamics.activity_drive
        + 0.04 * dynamics.recent_flux,
    )
    field_ca = np.clip(field, 0.0, 1.0)
    residue_weight = max(1.0 - simulation_mix, 0.45)
    field = np.clip(
        field_ca * simulation_mix + seed_residue * residue_weight,
        0.0,
        1.0,
    )

    # ── Render ────────────────────────────────────────────────────
    field_render_threshold = max(
        0.035,
        config.field_threshold
        - 0.08 * field_gain
        - 0.08 * dynamics.activity_drive
        - 0.04 * max(dynamics.pr_burst, dynamics.recent_flux)
        - 0.02 * dynamics.streak_strength,
    )
    return _render_svg(
        field,
        config=config,
        field_threshold=field_render_threshold,
        palette=palette,
        seed_specs=seed_specs,
        timeline=timeline_enabled,
        timeline_lookup=timeline_lookup,
        timeline_window=timeline_window,
        loop_duration=loop_duration,
        reveal_fraction=reveal_fraction,
        growth_mat=growth_mat,
        dialect=dialect,
        field_gain=field_gain,
        extent_gain=extent_gain,
        simulation_mix=simulation_mix,
        sim_steps=sim_steps,
    )
