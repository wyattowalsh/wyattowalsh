"""Shared daily-spine accretion channels and per-style visual dialects.

All six living-art styles consume one daily spine. Frame t is the
cumulative end-of-day world through day t. Each style maps the same
four channels (repos, stars, commits, followers) onto a distinct
visual dialect so accretion stays readable without changing the clock.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

ACCRETION_CHANNELS: tuple[str, ...] = ("repos", "stars", "commits", "followers")

# Log ceilings keep early growth visible instead of saturating at tiny totals.
_CHANNEL_CEILINGS: dict[str, float] = {
    "repos": 36.0,
    "stars": 500.0,
    "commits": 8000.0,
    "followers": 400.0,
}

STYLE_DIALECTS: dict[str, str] = {
    "inkgarden": "botanical",
    "topo": "cartographic",
    "genetic": "fitness",
    "physarum": "mycelial",
    "lenia": "morphogenetic",
    "ferrofluid": "magnetic",
}

_FAMILY_INK: dict[str, tuple[str, str]] = {
    "botanical": ("#6a5a4a", "#f5f0e6"),
    "cartographic": ("#4a3a28", "#f3ead8"),
    "fitness": ("#9ec9d8", "#1a1a2e"),
    "mycelial": ("#d4c07a", "#14120c"),
    "morphogenetic": ("#7ee0c0", "#0c1020"),
    "magnetic": ("#8ec8ff", "#0a0c14"),
}

_DEFAULT_ORIGIN: dict[str, tuple[float, float]] = {
    "inkgarden": (40.0, 742.0),
    "topo": (58.0, 708.0),
    "genetic": (44.0, 44.0),
    "physarum": (40.0, 742.0),
    "lenia": (516.0, 36.0),
    "ferrofluid": (516.0, 742.0),
}


def accretion_log_scale(value: float, *, ceiling: float) -> float:
    """Map a non-negative count onto a 0-1 log band with a readable floor."""
    safe_value = max(0.0, float(value))
    safe_ceiling = max(1.0, float(ceiling))
    return min(1.0, math.log1p(safe_value) / math.log1p(safe_ceiling))


def channel_mark_count(value: int, scale: float) -> int:
    """Return a 0-8 tick count that appears from the first unit of growth."""
    if value <= 0:
        return 0
    clamped = max(0.0, min(1.0, float(scale)))
    return 1 + int(round(clamped * 7.0))


def _as_nonneg_int(value: Any) -> int:
    try:
        return max(0, int(value or 0))
    except (TypeError, ValueError):
        return 0


def _repo_count(metrics: Mapping[str, Any]) -> int:
    raw = metrics.get("repos")
    if not isinstance(raw, list) or not raw:
        raw = metrics.get("top_repos")
    if isinstance(raw, list):
        named = [
            repo
            for repo in raw
            if isinstance(repo, dict) and str(repo.get("name") or "").strip()
        ]
        if named:
            return len(named)
        typed = [repo for repo in raw if isinstance(repo, dict)]
        if typed:
            return len(typed)
    return _as_nonneg_int(metrics.get("public_repos"))


@dataclass(frozen=True)
class AccretionChannels:
    """Cumulative spine totals plus log-normalized 0-1 scales."""

    repos: int
    stars: int
    commits: int
    followers: int
    repo_scale: float
    star_scale: float
    commit_scale: float
    follower_scale: float

    def mark_count(self, channel: str) -> int:
        """Tick count for one accretion channel."""
        if channel == "repos":
            return channel_mark_count(self.repos, self.repo_scale)
        if channel == "stars":
            return channel_mark_count(self.stars, self.star_scale)
        if channel == "commits":
            return channel_mark_count(self.commits, self.commit_scale)
        if channel == "followers":
            return channel_mark_count(self.followers, self.follower_scale)
        raise KeyError(channel)


@dataclass(frozen=True)
class StyleDialect:
    """One style's visual mapping of the shared accretion channels."""

    style: str
    family: str
    channels: AccretionChannels
    knobs: dict[str, float]

    def svg_attrs(self) -> str:
        """Machine-readable accretion attributes for the dialect register."""
        ch = self.channels
        return (
            f'data-dialect="{self.family}" '
            f'data-style="{self.style}" '
            f'data-accretion-repos="{ch.repos}" '
            f'data-accretion-stars="{ch.stars}" '
            f'data-accretion-commits="{ch.commits}" '
            f'data-accretion-followers="{ch.followers}" '
            f'data-accretion-repo-scale="{ch.repo_scale:.3f}" '
            f'data-accretion-star-scale="{ch.star_scale:.3f}" '
            f'data-accretion-commit-scale="{ch.commit_scale:.3f}" '
            f'data-accretion-follower-scale="{ch.follower_scale:.3f}"'
        )


def extract_accretion_channels(metrics: Mapping[str, Any]) -> AccretionChannels:
    """Read the four cumulative channels from a snapshot or render state."""
    repos = _repo_count(metrics)
    stars = _as_nonneg_int(metrics.get("stars"))
    commits = _as_nonneg_int(metrics.get("total_commits"))
    followers = _as_nonneg_int(metrics.get("followers"))
    return AccretionChannels(
        repos=repos,
        stars=stars,
        commits=commits,
        followers=followers,
        repo_scale=accretion_log_scale(repos, ceiling=_CHANNEL_CEILINGS["repos"]),
        star_scale=accretion_log_scale(stars, ceiling=_CHANNEL_CEILINGS["stars"]),
        commit_scale=accretion_log_scale(commits, ceiling=_CHANNEL_CEILINGS["commits"]),
        follower_scale=accretion_log_scale(
            followers, ceiling=_CHANNEL_CEILINGS["followers"]
        ),
    )


def _knobs_for(style: str, channels: AccretionChannels) -> dict[str, float]:
    """Return style-specific visual gains driven by the four channels."""
    if style == "inkgarden":
        return {
            "bloom_scale": 0.55 + 1.85 * channels.star_scale,
            "trunk_scale": 0.70 + 1.50 * channels.commit_scale,
            "glint_count": (
                0.0 if channels.followers <= 0 else 1.0 + 7.0 * channels.follower_scale
            ),
        }
    if style == "topo":
        return {
            "prominence_scale": 0.70 + 0.90 * channels.star_scale,
            "contour_gain": 0.35 + 0.65 * channels.commit_scale,
            "settlement_gain": channels.follower_scale,
        }
    if style == "genetic":
        return {
            "peak_scale": 0.72 + 0.70 * channels.star_scale,
            "generation_gain": channels.commit_scale,
            "colony_gain": channels.follower_scale,
        }
    if style == "physarum":
        return {
            "nutrient_scale": 0.70 + 0.80 * channels.star_scale,
            "trail_scale": 0.72 + 0.55 * channels.commit_scale,
            "vein_gain": channels.follower_scale,
        }
    if style == "lenia":
        return {
            "halo_scale": 0.75 + 0.70 * channels.star_scale,
            "field_gain": channels.commit_scale,
            "extent_gain": channels.follower_scale,
        }
    if style == "ferrofluid":
        return {
            "spike_scale": 0.70 + 0.80 * channels.star_scale,
            "ripple_gain": channels.commit_scale,
            "field_gain": 0.82 + 0.30 * channels.follower_scale,
        }
    return {}


def build_style_dialect(style: str, metrics: Mapping[str, Any]) -> StyleDialect:
    """Build the dialect for one registered living-art style."""
    if style not in STYLE_DIALECTS:
        raise KeyError(f"Unknown living-art style {style!r}")
    channels = extract_accretion_channels(metrics)
    return StyleDialect(
        style=style,
        family=STYLE_DIALECTS[style],
        channels=channels,
        knobs=_knobs_for(style, channels),
    )


def _channel_glyph(
    *,
    family: str,
    channel: str,
    count: int,
    cx: float,
    cy: float,
    ink: str,
) -> list[str]:
    """Draw a small style-specific glyph whose ticks grow with *count*."""
    shown = min(max(0, count), 6)
    parts: list[str] = []
    if shown <= 0:
        parts.append(
            f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="1.2" fill="none" '
            f'stroke="{ink}" stroke-width="0.4" opacity="0.28"/>'
        )
        return parts

    if family == "botanical":
        if channel == "repos":
            for index in range(shown):
                x = cx - 6.0 + index * 2.4
                parts.append(
                    f'<path d="M{x:.1f},{cy + 4.2:.1f} L{x:.1f},{cy - 2.6:.1f}" '
                    f'fill="none" stroke="{ink}" stroke-width="0.55"/>'
                )
                parts.append(
                    f'<ellipse cx="{x - 1.5:.1f}" cy="{cy - 1.0:.1f}" '
                    f'rx="1.7" ry="1.0" fill="none" stroke="{ink}" '
                    f'stroke-width="0.4"/>'
                )
        elif channel == "stars":
            for index in range(shown):
                angle = -math.pi / 2 + index * (math.tau / max(5, shown))
                px = cx + 4.2 * math.cos(angle)
                py = cy + 4.2 * math.sin(angle)
                parts.append(
                    f'<path d="M{cx:.1f},{cy:.1f} Q{px:.1f},{py:.1f} '
                    f"{cx + 1.2 * math.cos(angle + 0.6):.1f},"
                    f'{cy + 1.2 * math.sin(angle + 0.6):.1f}" '
                    f'fill="none" stroke="{ink}" stroke-width="0.5"/>'
                )
        elif channel == "commits":
            for index in range(shown):
                radius = 1.3 + index * 0.85
                parts.append(
                    f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{radius:.1f}" '
                    f'fill="none" stroke="{ink}" stroke-width="0.4"/>'
                )
        else:
            for index in range(shown):
                x = cx - 5.5 + index * 2.2
                parts.append(
                    f'<ellipse cx="{x:.1f}" cy="{cy:.1f}" rx="1.5" ry="0.9" '
                    f'fill="{ink}" opacity="0.55"/>'
                )
        return parts

    if family == "cartographic":
        if channel == "repos":
            for index in range(shown):
                x = cx - 6.0 + index * 2.4
                parts.append(
                    f'<path d="M{x:.1f},{cy + 3.4:.1f} L{x + 1.6:.1f},'
                    f'{cy - 3.2:.1f} L{x + 3.2:.1f},{cy + 3.4:.1f}" '
                    f'fill="none" stroke="{ink}" stroke-width="0.5"/>'
                )
        elif channel == "stars":
            for index in range(shown):
                y = cy + 3.6 - index * 1.3
                parts.append(
                    f'<line x1="{cx - 4.2:.1f}" y1="{y:.1f}" '
                    f'x2="{cx + 4.2:.1f}" y2="{y:.1f}" stroke="{ink}" '
                    f'stroke-width="0.45"/>'
                )
        elif channel == "commits":
            for index in range(shown):
                radius = 1.4 + index * 0.8
                parts.append(
                    f'<path d="M{cx - radius:.1f},{cy:.1f} '
                    f'Q{cx:.1f},{cy - radius:.1f} {cx + radius:.1f},{cy:.1f}" '
                    f'fill="none" stroke="{ink}" stroke-width="0.45"/>'
                )
        else:
            for index in range(shown):
                x = cx - 5.5 + index * 2.2
                parts.append(
                    f'<rect x="{x:.1f}" y="{cy - 1.4:.1f}" width="1.8" '
                    f'height="2.8" fill="none" stroke="{ink}" '
                    f'stroke-width="0.45"/>'
                )
        return parts

    if family == "fitness":
        if channel == "repos":
            for index in range(shown):
                x = cx - 6.0 + index * 2.4
                parts.append(
                    f'<path d="M{x:.1f},{cy + 3.6:.1f} '
                    f"Q{x + 1.2:.1f},{cy - 3.8:.1f} {x + 2.4:.1f},"
                    f'{cy + 3.6:.1f}" fill="none" stroke="{ink}" '
                    f'stroke-width="0.5"/>'
                )
        elif channel == "stars":
            height = 2.0 + shown * 1.1
            parts.append(
                f'<path d="M{cx:.1f},{cy + 3.8:.1f} L{cx:.1f},'
                f'{cy + 3.8 - height:.1f}" stroke="{ink}" '
                f'stroke-width="1.1" stroke-linecap="round"/>'
            )
        elif channel == "commits":
            for index in range(shown):
                x = cx - 6.0 + index * 2.2
                bar_h = 1.6 + index * 0.7
                parts.append(
                    f'<rect x="{x:.1f}" y="{cy + 3.2 - bar_h:.1f}" '
                    f'width="1.5" height="{bar_h:.1f}" fill="{ink}" '
                    f'opacity="0.7"/>'
                )
        else:
            for index in range(shown):
                x = cx - 5.5 + index * 2.2
                parts.append(
                    f'<circle cx="{x:.1f}" cy="{cy:.1f}" r="1.15" '
                    f'fill="{ink}" opacity="0.65"/>'
                )
        return parts

    if family == "mycelial":
        if channel == "repos":
            for index in range(shown):
                x = cx - 5.8 + index * 2.3
                parts.append(
                    f'<circle cx="{x:.1f}" cy="{cy:.1f}" r="1.4" fill="none" '
                    f'stroke="{ink}" stroke-width="0.5"/>'
                )
        elif channel == "stars":
            radius = 2.0 + shown * 0.55
            parts.append(
                f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{radius:.1f}" '
                f'fill="none" stroke="{ink}" stroke-width="0.55"/>'
            )
            parts.append(
                f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="1.1" fill="{ink}" '
                f'opacity="0.7"/>'
            )
        elif channel == "commits":
            width = 1.0 + shown * 0.35
            parts.append(
                f'<path d="M{cx - 7:.1f},{cy:.1f} C{cx - 2:.1f},{cy - 4:.1f} '
                f'{cx + 2:.1f},{cy + 4:.1f} {cx + 7:.1f},{cy:.1f}" '
                f'fill="none" stroke="{ink}" stroke-width="{width:.2f}"/>'
            )
        else:
            for index in range(shown):
                angle = index * (math.pi / max(3, shown))
                parts.append(
                    f'<line x1="{cx:.1f}" y1="{cy:.1f}" '
                    f'x2="{cx + 6.2 * math.cos(angle):.1f}" '
                    f'y2="{cy + 4.4 * math.sin(angle) - 1.2:.1f}" '
                    f'stroke="{ink}" stroke-width="0.45"/>'
                )
        return parts

    if family == "morphogenetic":
        if channel == "repos":
            for index in range(shown):
                x = cx - 5.8 + index * 2.3
                parts.append(
                    f'<circle cx="{x:.1f}" cy="{cy:.1f}" r="1.35" '
                    f'fill="{ink}" opacity="0.55"/>'
                )
        elif channel == "stars":
            radius = 2.1 + shown * 0.5
            parts.append(
                f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{radius:.1f}" '
                f'fill="none" stroke="{ink}" stroke-width="0.55"/>'
            )
            parts.append(
                f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{radius * 0.45:.1f}" '
                f'fill="none" stroke="{ink}" stroke-width="0.4"/>'
            )
        elif channel == "commits":
            for index in range(shown):
                y = cy + 3.4 - index * 1.2
                parts.append(
                    f'<circle cx="{cx:.1f}" cy="{y:.1f}" r="1.15" fill="none" '
                    f'stroke="{ink}" stroke-width="0.4"/>'
                )
        else:
            radius = 2.0 + shown * 0.7
            parts.append(
                f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{radius:.1f}" '
                f'fill="none" stroke="{ink}" stroke-width="0.45" '
                f'opacity="0.7"/>'
            )
        return parts

    if channel == "repos":
        for index in range(shown):
            x = cx - 5.8 + index * 2.3
            parts.append(
                f'<circle cx="{x:.1f}" cy="{cy:.1f}" r="1.2" fill="{ink}" '
                f'opacity="0.6"/>'
            )
    elif channel == "stars":
        height = 2.4 + shown * 1.0
        parts.append(
            f'<path d="M{cx - 2.1:.1f},{cy + 3.6:.1f} L{cx:.1f},'
            f'{cy + 3.6 - height:.1f} L{cx + 2.1:.1f},{cy + 3.6:.1f}" '
            f'fill="{ink}" opacity="0.72"/>'
        )
    elif channel == "commits":
        for index in range(shown):
            rx = 2.0 + index * 0.9
            parts.append(
                f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{rx:.1f}" '
                f'ry="{rx * 0.35:.1f}" fill="none" stroke="{ink}" '
                f'stroke-width="0.4"/>'
            )
    else:
        radius = 2.4 + shown * 0.6
        parts.append(
            f'<path d="M{cx - radius:.1f},{cy:.1f} '
            f"A{radius:.1f},{radius * 0.45:.1f} 0 0 1 {cx + radius:.1f},"
            f'{cy:.1f}" fill="none" stroke="{ink}" stroke-width="0.55"/>'
        )
    return parts


def dialect_group_markup(
    dialect: StyleDialect,
    *,
    x: float | None = None,
    y: float | None = None,
    ink: str | None = None,
    paper: str | None = None,
) -> str:
    """Render a compact, style-specific accretion register."""
    origin_x, origin_y = _DEFAULT_ORIGIN.get(dialect.style, (40.0, 742.0))
    left = origin_x if x is None else x
    top = origin_y if y is None else y
    family_ink, family_paper = _FAMILY_INK[dialect.family]
    stroke = ink or family_ink
    fill = paper or family_paper
    width = 248.0
    height = 28.0
    parts = [
        f'<g id="accretion-dialect" {dialect.svg_attrs()} '
        f'data-role="accretion-dialect">',
        f'<rect x="{left:.1f}" y="{top:.1f}" width="{width:.1f}" '
        f'height="{height:.1f}" rx="3.5" fill="{fill}" opacity="0.78" '
        f'stroke="{stroke}" stroke-width="0.45"/>',
        f'<text x="{left + 8:.1f}" y="{top + 9.5:.1f}" '
        f'font-family="Georgia,serif" font-size="5.2" fill="{stroke}" '
        f'opacity="0.7" letter-spacing="0.8">{dialect.family}</text>',
    ]
    slot_w = 58.0
    for index, channel in enumerate(ACCRETION_CHANNELS):
        count = dialect.channels.mark_count(channel)
        raw = {
            "repos": dialect.channels.repos,
            "stars": dialect.channels.stars,
            "commits": dialect.channels.commits,
            "followers": dialect.channels.followers,
        }[channel]
        slot_x = left + 6.0 + index * slot_w
        glyph_x = slot_x + 12.0
        glyph_y = top + 18.5
        parts.append(
            f'<g data-channel="{channel}" data-mark-count="{count}" '
            f'data-channel-value="{raw}">'
        )
        parts.extend(
            _channel_glyph(
                family=dialect.family,
                channel=channel,
                count=count,
                cx=glyph_x,
                cy=glyph_y,
                ink=stroke,
            )
        )
        parts.append(
            f'<text x="{slot_x + 24:.1f}" y="{top + 21.5:.1f}" '
            f'font-family="monospace" font-size="5" fill="{stroke}" '
            f'opacity="0.72">{raw}</text>'
        )
        parts.append("</g>")
    parts.append("</g>")
    return "".join(parts)
