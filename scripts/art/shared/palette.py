"""Named art palettes and extended world-state palette builders."""

from __future__ import annotations

from collections.abc import Mapping

from .color import oklch
from .world_state import WorldState, _build_world_palette, _seasonal_hues

# ---------------------------------------------------------------------------
# Art palette registry (Phase 2)
# ---------------------------------------------------------------------------


ART_PALETTE_ANCHORS: dict[str, list[tuple[float, float, float]]] = {
    "sunset": [
        (0.48, 0.22, 310),
        (0.58, 0.26, 340),
        (0.65, 0.24, 15),
        (0.72, 0.22, 40),
        (0.78, 0.20, 65),
    ],
    "aurora": [
        (0.55, 0.22, 290),
        (0.65, 0.20, 200),
        (0.60, 0.22, 150),
        (0.62, 0.20, 340),
        (0.68, 0.16, 280),
    ],
    "ocean": [
        (0.38, 0.18, 255),
        (0.48, 0.22, 240),
        (0.56, 0.20, 220),
        (0.62, 0.18, 195),
        (0.68, 0.16, 170),
    ],
    "flora": [
        (0.52, 0.14, 155),
        (0.56, 0.20, 145),
        (0.62, 0.22, 120),
        (0.50, 0.16, 105),
        (0.48, 0.16, 180),
    ],
    "ember": [
        (0.48, 0.24, 15),
        (0.56, 0.22, 30),
        (0.62, 0.20, 45),
        (0.52, 0.18, 25),
        (0.44, 0.22, 5),
    ],
    "neon": [
        (0.72, 0.28, 250),
        (0.70, 0.30, 330),
        (0.78, 0.28, 155),
        (0.80, 0.26, 80),
    ],
    "cosmic": [
        (0.15, 0.08, 280),
        (0.25, 0.14, 260),
        (0.35, 0.18, 240),
        (0.30, 0.12, 300),
        (0.20, 0.10, 320),
    ],
    "spiral": [
        (0.55, 0.12, 260),
        (0.60, 0.14, 220),
        (0.65, 0.16, 180),
        (0.58, 0.10, 300),
        (0.52, 0.14, 340),
    ],
    "turing": [
        (0.18, 0.06, 270),
        (0.35, 0.16, 200),
        (0.50, 0.22, 160),
        (0.65, 0.18, 130),
        (0.80, 0.10, 80),
    ],
    "physarum": [
        (0.12, 0.04, 250),
        (0.30, 0.14, 170),
        (0.55, 0.22, 90),
        (0.70, 0.20, 55),
        (0.85, 0.12, 40),
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
    season_map = {
        "spring": "flora",
        "summer": "ember",
        "autumn": "sunset",
        "winter": "ocean",
    }
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
