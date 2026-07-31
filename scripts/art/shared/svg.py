"""SVG markup helpers, filters, weather overlays, and SMIL utilities."""
from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from typing import Any

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
