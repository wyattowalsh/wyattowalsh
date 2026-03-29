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
from dataclasses import dataclass

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
    ART_PALETTE_ANCHORS,
    DerivedMetrics,
    ElementBudget,
    Noise2D,
    WorldState,
    _build_world_palette_extended,
    blend_mode_filter,
    compute_derived_metrics,
    compute_maturity,
    compute_world_state,
    hex_frac,
    map_date_to_loop_delay,
    normalize_timeline_window,
    oklch,
    oklch_lerp,
    repo_to_canvas_position,
    seed_hash,
    select_primary_repos,
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


# ---------------------------------------------------------------------------
# Kernel & growth function
# ---------------------------------------------------------------------------


def _build_kernel(radius: int, r_peak: float, width: float) -> np.ndarray:
    """Annular Gaussian ring kernel, normalized to sum to 1."""
    size = 2 * radius + 1
    y, x = np.ogrid[-radius : radius + 1, -radius : radius + 1]
    r = np.sqrt(x * x + y * y).astype(np.float64) / radius
    K = np.exp(-((r - r_peak) ** 2) / (2.0 * width * width))
    K[r > 1.0] = 0.0
    total = K.sum()
    if total > 0:
        K /= total
    return K


def _growth(u: np.ndarray, mu: float, sigma: float) -> np.ndarray:
    """Gaussian bump growth function: G(u) = 2 * exp(-(u-mu)^2/(2*sigma^2)) - 1."""
    return 2.0 * np.exp(-((u - mu) ** 2) / (2.0 * sigma * sigma)) - 1.0


# ---------------------------------------------------------------------------
# Kernel parameterization from language mix
# ---------------------------------------------------------------------------


def _kernel_params_from_mix(
    language_mix: dict[str, float],
    h: str,
) -> tuple[float, float]:
    """Derive kernel ring peak and width from language distribution + seed hash."""
    n_langs = max(1, len(language_mix))
    hash_frac = hex_frac(h, 24, 28)
    # More languages → wider ring; hash adds per-profile variation
    r_peak = 0.3 + 0.3 * math.tanh(n_langs / 5.0) + 0.05 * hash_frac
    width = 0.08 + 0.07 * math.tanh(n_langs / 8.0) + 0.03 * hash_frac
    return r_peak, width


# ---------------------------------------------------------------------------
# Field initialization
# ---------------------------------------------------------------------------


def _seed_organisms(
    field: np.ndarray,
    positions: list[tuple[int, int]],
    rng: np.random.Generator,
    radius: int = CFG.seed_radius,
) -> None:
    """Plant seed organisms at grid positions (in-place)."""
    N = field.shape[0]
    for gx, gy in positions:
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                dist = math.sqrt(dx * dx + dy * dy)
                if dist <= radius:
                    ny, nx = (gy + dy) % N, (gx + dx) % N
                    val = 0.5 + 0.5 * rng.random() * (1.0 - dist / radius)
                    field[ny, nx] = max(field[ny, nx], val)


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


def _field_to_color(value: float) -> tuple[str, float]:
    """Map a field value to (hex color, opacity) via bioluminescent ramp."""
    if value < _BIO_RAMP[1][0]:
        return "#000000", 0.0
    # Find ramp segment
    for i in range(1, len(_BIO_RAMP)):
        lo, hi, L, C, H = _BIO_RAMP[i]
        if value <= hi:
            t = (value - lo) / max(0.001, hi - lo)
            # Interpolate lightness for glow effect
            L_out = L * (0.7 + 0.3 * t)
            C_out = C * (0.8 + 0.2 * t)
            opacity = 0.4 + 0.6 * t
            return oklch(L_out, C_out, H), opacity
    # Above max — full brightness
    return oklch(0.85, 0.12, 140), 1.0


# ---------------------------------------------------------------------------
# SVG rendering
# ---------------------------------------------------------------------------


def _render_svg(
    field: np.ndarray,
    *,
    config: LeniaConfig,
    timeline: bool,
    loop_duration: float,
    reveal_fraction: float,
    growth_mat: float,
    world: WorldState,
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
    P.append(f'<rect width="{WIDTH}" height="{HEIGHT}" fill="{_BG_COLOR}"/>')

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

        color, opacity = _field_to_color(v)
        if opacity < 0.01:
            continue

        cx = (gx + 0.5) * cell_size
        cy = (gy + 0.5) * cell_size
        r = cell_size * 0.5 * (0.3 + 0.7 * v)

        # Maturity fade: early maturity dims the field
        mat_opacity = opacity * _fade_ramp(growth_mat, v)

        style_parts: list[str] = []
        if timeline:
            # Stagger reveal by grid position
            frac = (gx + gy * N) / max(1, N * N)
            delay = frac * reveal_fraction * loop_duration
            style_parts.append(
                f'class="tl-reveal" style="--delay:{delay:.2f}s;--to:{mat_opacity:.2f}"'
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
        core_color = oklch(0.90, 0.06, 160)
        core_opacity = 0.3 * (v - 0.65) / 0.35 * _fade_ramp(growth_mat, v)
        if core_opacity < 0.01:
            continue
        if timeline:
            frac = (gx + gy * N) / max(1, N * N)
            delay = frac * reveal_fraction * loop_duration
            P.append(
                f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" '
                f'fill="{core_color}" class="tl-reveal" '
                f'style="--delay:{delay:.2f}s;--to:{core_opacity:.2f}"/>'
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
# Language mix extraction
# ---------------------------------------------------------------------------


def _extract_language_mix(repos: list[dict]) -> dict[str, float]:
    """Build a normalized language → fraction mapping from repo list."""
    counts: dict[str, int] = {}
    for r in repos:
        lang = r.get("language")
        if lang:
            counts[lang] = counts.get(lang, 0) + 1
    total = max(1, sum(counts.values()))
    return {k: v / total for k, v in counts.items()}


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
    _build_world_palette_extended(
        world.time_of_day,
        world.weather,
        world.season,
        world.energy,
    )  # populates world.palette as side-effect

    # ── Deterministic RNG ─────────────────────────────────────────
    h = seed_hash({"seed": seed}) if seed is not None else seed_hash(metrics)
    rng = np.random.default_rng(int(h[:8], 16))

    # ── Extract data ──────────────────────────────────────────────
    repos = metrics.get("top_repos") or metrics.get("repos") or []
    stars = int(metrics.get("stars", 0) or 0)
    contributions = int(metrics.get("contributions_last_year", 200) or 200)
    primary_repos, _ = select_primary_repos(repos, limit=config.max_repos)
    language_mix = _extract_language_mix(repos)

    # ── Simulation parameters ─────────────────────────────────────
    mu = config.mu_base + config.mu_scale * math.tanh(stars / config.mu_norm)
    sigma = config.sigma_base + config.sigma_scale * math.tanh(
        contributions / config.sigma_norm
    )

    # Kernel shape from language mix
    r_peak, k_width = _kernel_params_from_mix(language_mix, h)
    kernel = _build_kernel(config.kernel_radius, r_peak, k_width)

    # ── Seed organism positions ───────────────────────────────────
    N = config.grid_resolution
    grid_positions: list[tuple[int, int]] = []
    for repo in primary_repos:
        cx, cy = repo_to_canvas_position(repo, h, WIDTH, HEIGHT, strategy="hash")
        gx = int(cx / WIDTH * N) % N
        gy = int(cy / HEIGHT * N) % N
        grid_positions.append((gx, gy))

    # Ensure at least one seed even with no repos
    if not grid_positions:
        gx0 = int(hex_frac(h, 0, 4) * N) % N
        gy0 = int(hex_frac(h, 4, 8) * N) % N
        grid_positions.append((gx0, gy0))

    # ── Initialize field ──────────────────────────────────────────
    field = np.zeros((N, N), dtype=np.float64)
    _seed_organisms(field, grid_positions, rng, radius=config.seed_radius)

    # ── Simulate ──────────────────────────────────────────────────
    sim_steps = int(config.sim_steps_base + config.sim_steps_scale * mat)
    field = _simulate(field, kernel, mu, sigma, sim_steps, config.dt, world.energy)

    # ── Render ────────────────────────────────────────────────────
    return _render_svg(
        field,
        config=config,
        timeline=timeline_enabled,
        loop_duration=loop_duration,
        reveal_fraction=reveal_fraction,
        growth_mat=growth_mat,
        world=world,
    )
