"""Shared utilities for generative / living-art.

Public import path remains ``scripts.art.shared`` (and ``from .shared import …``).
Implementation lives in focused sibling modules:

- ``constants`` — canvas size, language hues, repo soft-limit
- ``timeline`` — date windows and contribution series
- ``world_state`` — maturity + ``WorldState`` atmospherics
- ``metrics`` — live metrics/history contracts and normalization
- ``seeds`` — deterministic hashing + CLI arg helpers
- ``color`` — OKLCH / HSL / WCAG contrast
- ``noise`` — ``Noise2D`` + presets
- ``math_helpers`` — phyllotaxis / flow-field geometry
- ``svg`` — SVG markup, filters, weather overlays, SMIL
- ``palette`` — named art palettes + extended world palettes
- ``visual`` — repo layout, derived metrics, element budgets
"""
from __future__ import annotations

from .color import (
    ensure_contrast,
    hex_to_oklch,
    hsl_to_hex,
    lerp_color,
    oklch,
    oklch_gamut_map,
    oklch_gradient,
    oklch_lerp,
    wcag_contrast_ratio,
)
from .constants import CX, CY, HEIGHT, LANG_HUES, MAX_REPOS, WIDTH
from .math_helpers import flow_field_lines, phyllotaxis_points
from .metrics import (
    ContributionCalendarEntry,
    ContributionDailyEntry,
    ContributionStreakSignal,
    HistorySnapshotContract,
    MetricsSnapshotContract,
    RepoSignalEntry,
    StarVelocitySignal,
    TimelineEventEntry,
    is_monotonic_timelapse_metrics,
    normalize_live_metrics,
    resolve_render_metrics,
    validate_live_history_payload,
    validate_live_metrics_payload,
)
from .noise import NOISE_PRESETS, Noise2D, resolve_noise_preset
from .palette import (
    ART_PALETTE_ANCHORS,
    CLUSTER_PALETTES,
    _build_world_palette_extended,
    select_palette_for_world,
)
from .seeds import _hex_slice, _seed_hash, hex_frac, parse_cli_args, seed_hash
from .svg import (
    annotation_tooltip_metadata,
    atmospheric_haze_filter,
    aurora_band_elements,
    aurora_filter,
    blend_mode_filter,
    firefly_elements,
    lightning_path,
    make_linear_gradient,
    make_radial_gradient,
    organic_texture_filter,
    rain_pattern,
    smil_animate,
    smil_animate_transform,
    snow_pattern,
    sparkline_svg,
    svg_footer,
    svg_header,
    volumetric_glow_filter,
    weather_overlay_elements,
    xml_escape,
)
from .timeline import (
    contributions_monthly_to_daily_series,
    map_date_to_loop_delay,
    normalize_timeline_window,
)
from .visual import (
    DerivedMetrics,
    ElementBudget,
    activity_tempo,
    compute_derived_metrics,
    order_repos_for_visual_plan,
    repo_to_canvas_position,
    repo_visibility_score,
    select_primary_repos,
    stable_repo_visual_order,
    topic_affinity_matrix,
    visual_complexity,
)
from .world_state import (
    WorldState,
    _build_world_palette,
    compute_maturity,
    compute_world_state,
)

__all__ = [
    "ART_PALETTE_ANCHORS",
    "CLUSTER_PALETTES",
    "CX",
    "CY",
    "ContributionCalendarEntry",
    "ContributionDailyEntry",
    "ContributionStreakSignal",
    "DerivedMetrics",
    "ElementBudget",
    "HEIGHT",
    "HistorySnapshotContract",
    "LANG_HUES",
    "MAX_REPOS",
    "MetricsSnapshotContract",
    "NOISE_PRESETS",
    "Noise2D",
    "RepoSignalEntry",
    "StarVelocitySignal",
    "TimelineEventEntry",
    "WIDTH",
    "WorldState",
    "_build_world_palette",
    "_build_world_palette_extended",
    "_hex_slice",
    "_seed_hash",
    "activity_tempo",
    "annotation_tooltip_metadata",
    "atmospheric_haze_filter",
    "aurora_band_elements",
    "aurora_filter",
    "blend_mode_filter",
    "compute_derived_metrics",
    "compute_maturity",
    "compute_world_state",
    "contributions_monthly_to_daily_series",
    "ensure_contrast",
    "firefly_elements",
    "flow_field_lines",
    "hex_frac",
    "hex_to_oklch",
    "hsl_to_hex",
    "is_monotonic_timelapse_metrics",
    "lerp_color",
    "lightning_path",
    "make_linear_gradient",
    "make_radial_gradient",
    "map_date_to_loop_delay",
    "normalize_live_metrics",
    "normalize_timeline_window",
    "oklch",
    "oklch_gamut_map",
    "oklch_gradient",
    "oklch_lerp",
    "order_repos_for_visual_plan",
    "organic_texture_filter",
    "parse_cli_args",
    "phyllotaxis_points",
    "rain_pattern",
    "repo_to_canvas_position",
    "repo_visibility_score",
    "resolve_noise_preset",
    "resolve_render_metrics",
    "seed_hash",
    "select_palette_for_world",
    "select_primary_repos",
    "smil_animate",
    "smil_animate_transform",
    "snow_pattern",
    "sparkline_svg",
    "stable_repo_visual_order",
    "svg_footer",
    "svg_header",
    "topic_affinity_matrix",
    "validate_live_history_payload",
    "validate_live_metrics_payload",
    "visual_complexity",
    "volumetric_glow_filter",
    "wcag_contrast_ratio",
    "weather_overlay_elements",
    "xml_escape",
]
