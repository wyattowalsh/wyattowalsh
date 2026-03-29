"""
Ferrofluid Magnetism Sculpture — living art module.

Dark metallic liquid forms spike sculptures in response to magnetic fields
created by repos.  Each repo places a magnetic dipole; where the field
exceeds a critical threshold the ferrofluid rises into iridescent tapered
spikes with mirrored reflections below a pool surface line.
"""

# ruff: noqa: E501

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass

import numpy as np

from .shared import (
    HEIGHT,
    LANG_HUES,
    MAX_REPOS,
    WIDTH,
    DerivedMetrics,
    ElementBudget,
    Noise2D,
    WorldState,
    _build_world_palette_extended,
    compute_derived_metrics,
    compute_maturity,
    compute_world_state,
    hex_frac,
    map_date_to_loop_delay,
    normalize_timeline_window,
    oklch,
    oklch_lerp,
    organic_texture_filter,
    repo_to_canvas_position,
    seed_hash,
    select_primary_repos,
    visual_complexity,
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
) -> str:
    """SVG linearGradient dark-base -> bright-highlight -> dark-tip."""
    return (
        f'<linearGradient id="{grad_id}" x1="0" y1="1" x2="0" y2="0">'
        f'<stop offset="0%" stop-color="{base_color}"/>'
        f'<stop offset="45%" stop-color="{highlight_color}"/>'
        f'<stop offset="100%" stop-color="{tip_color}"/>'
        f'</linearGradient>'
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
    growth_mat = 1.0 if timeline_enabled else mat

    # ── WorldState ────────────────────────────────────────────────
    world: WorldState = compute_world_state(metrics)
    pal = _build_world_palette_extended(
        world.time_of_day, world.weather, world.season, world.energy,
    )
    complexity = visual_complexity(metrics)
    derived: DerivedMetrics = compute_derived_metrics(metrics)

    def _fade(start: float, full: float) -> float:
        """Smooth 0-1 ramp between start and full maturity."""
        return max(0.0, min(1.0, (growth_mat - start) / max(0.001, full - start)))

    h = seed_hash({"seed": seed}) if seed is not None else seed_hash(metrics)
    rng = np.random.default_rng(int(h[:8], 16))
    noise = Noise2D(seed=int(h[8:16], 16))

    # ── Extract metrics ───────────────────────────────────────────
    repos = list(metrics.get("repos", []))
    monthly = metrics.get("contributions_monthly", {})
    contributions = metrics.get("contributions_last_year", 200)
    stars = metrics.get("stars", 0)

    top_repos, _overflow = select_primary_repos(repos, limit=CFG.max_repos)

    # ── Timeline window ───────────────────────────────────────────
    def _repo_date(repo: dict) -> str | None:
        for key in ("date", "created_at", "created", "pushed_at", "updated_at"):
            val = repo.get(key)
            if isinstance(val, str) and val.strip():
                return val[:10] if len(val) >= 10 else val
        return None

    timeline_window = normalize_timeline_window(
        [{"date": _repo_date(r)} for r in repos if isinstance(r, dict) and _repo_date(r)],
        {"account_created": metrics.get("account_created"), "repos": repos, "contributions_monthly": monthly},
        fallback_days=365,
    )

    def _timeline_style(when: str, opacity: float, cls: str = "tl-reveal") -> str:
        if not timeline_enabled:
            return f'opacity="{opacity:.2f}"'
        delay = map_date_to_loop_delay(when, timeline_window, duration=loop_duration, reveal_fraction=reveal_fraction)
        return (
            f'class="{cls}" '
            f'style="--delay:{delay:.3f}s;--to:{max(0.0, min(1.0, opacity)):.3f};'
            f'--dur:{loop_duration:.2f}s" data-delay="{delay:.3f}" data-when="{when}"'
        )

    # ── Dipole placement ──────────────────────────────────────────
    pool_y = HEIGHT * CFG.pool_y_fraction
    fluid_response = math.tanh(contributions / CFG.viscosity_norm)
    surface_tension = max(0.2, 1.0 - world.energy * 0.6)

    dipoles: list[tuple[float, float, float]] = []
    spike_meta: list[dict] = []  # per-repo metadata for timeline
    for repo in top_repos:
        rx, ry = repo_to_canvas_position(repo, h, WIDTH, pool_y * 0.9, strategy="language_cluster")
        repo_stars = repo.get("stars", 0)
        moment = CFG.moment_base * (1.0 + math.log1p(repo_stars))
        dipoles.append((rx, ry, moment))
        spike_meta.append({
            "repo": repo,
            "x": rx, "y": ry,
            "moment": moment,
            "date": _repo_date(repo) or timeline_window[0].isoformat(),
            "lang": repo.get("language"),
        })

    # ── Compute magnetic field ────────────────────────────────────
    maturity_ramp = _fade(0.0, 0.8)
    field, gx, gy = _compute_field(
        dipoles, CFG.grid_resolution, WIDTH, HEIGHT, pool_y,
        maturity_ramp=maturity_ramp,
    )

    # ── Find spikes ───────────────────────────────────────────────
    b_crit = CFG.b_critical / max(0.3, surface_tension)
    spike_mask = field > b_crit
    spike_heights = CFG.spike_scale * np.sqrt(np.maximum(0.0, field - b_crit))
    spike_heights *= (0.6 + 0.4 * fluid_response)
    spike_heights *= _fade(0.15, 0.7)

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
        f'width="{WIDTH}" height="{HEIGHT}">'
    )

    if timeline_enabled:
        P.append(
            "<style>"
            "@keyframes ferroReveal{0%{opacity:0}100%{opacity:var(--to,1)}}"
            ".tl-reveal{opacity:0;animation:ferroReveal .8s ease-out var(--delay,0s) both}"
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
        '</filter>'
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
        '</linearGradient>'
    )

    # Per-spike gradients (iridescent metallic)
    spike_indices = np.argwhere(spike_mask)
    # Subsample to keep element count sane
    max_spikes = min(400, budget.remaining // 6)
    if len(spike_indices) > max_spikes:
        chosen = rng.choice(len(spike_indices), max_spikes, replace=False)
        spike_indices = spike_indices[chosen]
    # Sort by field strength (tallest last = painter's algorithm)
    spike_indices = sorted(spike_indices, key=lambda idx: spike_heights[idx[0], idx[1]])

    grad_defs: list[str] = []
    for si, (yi, xi) in enumerate(spike_indices):
        sx = float(gx[yi, xi])
        angle_norm = (sx / WIDTH + float(gy[yi, xi]) / pool_y) * 0.5
        hue_shift = angle_norm * CFG.iridescence_strength * 2 - CFG.iridescence_strength
        base_hue = 250.0 + hue_shift + light_angle * 0.1
        dark = oklch(0.10, 0.04, base_hue)
        bright = oklch(0.55, 0.12, base_hue + 15)
        tip = oklch(0.15, 0.06, base_hue - 10)
        grad_defs.append(_make_spike_gradient(f"sg{si}", dark, bright, tip))

    for gd in grad_defs:
        P.append(gd)
        budget.add(1)

    P.append("</defs>")

    # ── Background ────────────────────────────────────────────────
    P.append(f'<rect width="{WIDTH}" height="{HEIGHT}" fill="url(#bgGrad)"/>')
    budget.add(1)

    # ── Subtle liquid surface ripples ─────────────────────────────
    ripple_opacity = 0.06 + 0.04 * _fade(0.0, 0.3)
    P.append(
        f'<rect x="0" y="{pool_y - 15:.0f}" width="{WIDTH}" height="30" '
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

    # ── Assign each spike to the nearest dipole for timeline dating ──
    dipole_xy = np.array([(d[0], d[1]) for d in dipoles]) if dipoles else np.empty((0, 2))

    def _nearest_dipole_date(sx: float, sy: float) -> str:
        if len(dipole_xy) == 0:
            return timeline_window[0].isoformat()
        dists = (dipole_xy[:, 0] - sx) ** 2 + (dipole_xy[:, 1] - sy) ** 2
        idx = int(np.argmin(dists))
        return spike_meta[idx]["date"]

    # ── Render reflections first (behind spikes) ──────────────────
    refl_group: list[str] = []
    for si, (yi, xi) in enumerate(spike_indices):
        if not budget.ok():
            break
        sx = float(gx[yi, xi])
        sh = float(spike_heights[yi, xi])
        if sh < 1.5:
            continue
        field_val = float(field[yi, xi])
        bw = CFG.spike_base_width * math.sqrt(max(0.3, field_val / max(b_crit * 3, 1)))
        refl_h = sh * 0.7
        refl_pts = _reflected_polygon(sx, pool_y, bw, refl_h)
        refl_op = CFG.reflection_opacity * min(1.0, sh / 40.0)
        when = _nearest_dipole_date(sx, float(gy[yi, xi]))
        refl_group.append(
            f'<polygon points="{refl_pts}" fill="url(#sg{si})" '
            f'opacity="{refl_op:.2f}" filter="url(#reflBlur)" '
            f'{_timeline_style(when, refl_op, "tl-reveal tl-soft")}/>'
        )
        budget.add(1)

    if refl_group:
        P.append(f'<g opacity="{CFG.reflection_opacity:.2f}">')
        P.extend(refl_group)
        P.append('</g>')

    # ── Render spikes ─────────────────────────────────────────────
    for si, (yi, xi) in enumerate(spike_indices):
        if not budget.ok():
            break
        sx = float(gx[yi, xi])
        sy = float(gy[yi, xi])
        sh = float(spike_heights[yi, xi])
        if sh < 1.0:
            continue
        field_val = float(field[yi, xi])
        bw = CFG.spike_base_width * math.sqrt(max(0.3, field_val / max(b_crit * 3, 1)))
        pts = _spike_polygon(sx, pool_y, bw, sh)
        when = _nearest_dipole_date(sx, sy)
        P.append(
            f'<polygon points="{pts}" fill="url(#sg{si})" '
            f'{_timeline_style(when, 0.95, "tl-reveal")}/>'
        )
        budget.add(1)

    # ── Specular highlight on tallest spikes ──────────────────────
    highlight_thresh = np.percentile(spike_heights[spike_mask], 75) if spike_mask.any() else 999
    for si, (yi, xi) in enumerate(spike_indices):
        if not budget.ok():
            break
        sh = float(spike_heights[yi, xi])
        if sh < highlight_thresh:
            continue
        sx = float(gx[yi, xi])
        tip_y = pool_y - sh
        hl_color = oklch(0.75, 0.06, 200 + rng.uniform(-15, 15))
        when = _nearest_dipole_date(sx, float(gy[yi, xi]))
        P.append(
            f'<ellipse cx="{sx:.1f}" cy="{tip_y + sh * 0.35:.1f}" '
            f'rx="{max(0.8, sh * 0.04):.1f}" ry="{max(1.5, sh * 0.12):.1f}" '
            f'fill="{hl_color}" opacity="0.35" '
            f'{_timeline_style(when, 0.35, "tl-reveal tl-soft")}/>'
        )
        budget.add(1)

    # ── Low-maturity: ambient ripples when field is too weak ──────
    if growth_mat < 0.35:
        ripple_count = int(8 + rng.integers(0, 6))
        for ri in range(ripple_count):
            if not budget.ok():
                break
            rx = rng.uniform(50, WIDTH - 50)
            ry = pool_y + rng.uniform(-8, 8)
            rr = rng.uniform(15, 45)
            rop = 0.04 + 0.03 * growth_mat
            P.append(
                f'<ellipse cx="{rx:.1f}" cy="{ry:.1f}" rx="{rr:.1f}" ry="{rr * 0.3:.1f}" '
                f'fill="none" stroke="{oklch(0.20, 0.03, 260)}" stroke-width="0.5" '
                f'opacity="{rop:.2f}"/>'
            )
            budget.add(1)

    # ── Dipole markers (subtle glow at each repo position) ────────
    for dm in spike_meta:
        if not budget.ok():
            break
        lang_hue = LANG_HUES.get(dm["lang"], 155)
        glow_color = oklch(0.30, 0.10, lang_hue)
        glow_op = 0.15 + 0.15 * _fade(0.2, 0.6)
        P.append(
            f'<circle cx="{dm["x"]:.1f}" cy="{pool_y:.1f}" r="6" '
            f'fill="{glow_color}" opacity="{glow_op:.2f}" '
            f'{_timeline_style(dm["date"], glow_op, "tl-reveal tl-soft")}/>'
        )
        budget.add(1)

    P.append("</svg>")
    return "\n".join(P)
