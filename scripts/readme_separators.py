"""Unique horizontal SVG separators for README section breaks.

Each separator is a distinct visual dialect so adjacent sections do not
rhyme. Files land under ``.github/assets/img/readme/sep-*.svg``.
"""

from __future__ import annotations

from pathlib import Path

from .utils import get_logger

logger = get_logger(module=__name__)

_REPO_ROOT = Path(__file__).resolve().parent.parent
_OUT_DIR = _REPO_ROOT / ".github" / "assets" / "img" / "readme"

SEPARATOR_SPECS: tuple[tuple[str, str], ...] = (
    ("sep-featured.svg", "featured"),
    ("sep-metrics.svg", "metrics"),
    ("sep-living.svg", "living"),
    ("sep-tech.svg", "tech"),
    ("sep-clouds.svg", "clouds"),
    ("sep-blog.svg", "blog"),
)


def _svg(body: str, *, aria: str) -> str:
    return "\n".join(
        (
            '<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="36" '
            'viewBox="0 0 1200 36" role="img" '
            f'aria-label="{aria}">',
            body,
            "</svg>",
            "",
        )
    )


def _featured() -> str:
    ticks = []
    for i in range(17):
        x = 40 + i * 70
        h = 6 + (i * 5) % 14
        ticks.append(
            f'<rect x="{x}" y="{18 - h / 2:.1f}" width="2.2" height="{h:.1f}" '
            'rx="1" fill="#6366f1"/>'
        )
    return _svg(
        "\n".join(
            (
                '<style>:root { color-scheme: light dark; } '
                "@media (prefers-color-scheme: dark) { "
                ".rail { stroke: #30363d; } }</style>",
                '<line class="rail" x1="24" y1="18" x2="1176" y2="18" '
                'stroke="#d0d7de" stroke-width="1"/>',
                '<circle cx="600" cy="18" r="5" fill="none" stroke="#6366f1" '
                'stroke-width="1.6"/>',
                *ticks,
            )
        ),
        aria="Featured projects",
    )


def _metrics() -> str:
    pts = (
        "24,28 80,10 140,22 210,8 280,20 360,6 440,18 520,9 "
        "600,16 680,7 760,19 840,8 920,21 1000,11 1080,24 1176,14"
    )
    return _svg(
        "\n".join(
            (
                '<style>:root { color-scheme: light dark; } '
                ".spark { fill: none; stroke: #1a7f37; stroke-width: 1.8; "
                "stroke-linejoin: round; } "
                "@media (prefers-color-scheme: dark) { "
                ".spark { stroke: #3fb950; } .base { stroke: #30363d; } }</style>",
                '<line class="base" x1="24" y1="30" x2="1176" y2="30" '
                'stroke="#d0d7de" stroke-width="1"/>',
                f'<polyline class="spark" points="{pts}"/>',
            )
        ),
        aria="Metrics",
    )


def _living() -> str:
    rings = []
    for i, r in enumerate((4, 8, 13, 16)):
        rings.append(
            f'<circle cx="600" cy="18" r="{r}" fill="none" '
            f'stroke="#bf4b8a" stroke-opacity="{0.85 - i * 0.18:.2f}" '
            'stroke-width="1.1"/>'
        )
    vines = []
    for x in (80, 200, 320, 880, 1000, 1120):
        vines.append(
            f'<path d="M{x} 30 C{x + 10} 18, {x - 8} 12, {x + 4} 6" '
            'fill="none" stroke="#1a7f37" stroke-width="1.3"/>'
        )
    return _svg(
        "\n".join(
            (
                '<style>:root { color-scheme: light dark; } '
                "@media (prefers-color-scheme: dark) { "
                ".soil { stroke: #30363d; } }</style>",
                '<line class="soil" x1="24" y1="30" x2="1176" y2="30" '
                'stroke="#d0d7de" stroke-width="1"/>',
                *rings,
                *vines,
            )
        ),
        aria="Living art",
    )


def _tech() -> str:
    chips = []
    xs = (60, 180, 320, 470, 620, 760, 900, 1040)
    colors = (
        "#3776ab",
        "#f7df1e",
        "#3178c6",
        "#e34f26",
        "#2496ed",
        "#000000",
        "#ff6c37",
        "#0969da",
    )
    for x, color in zip(xs, colors, strict=True):
        chips.append(
            f'<rect x="{x}" y="10" width="54" height="16" rx="8" fill="{color}"/>'
        )
    return _svg(
        "\n".join(
            (
                '<style>:root { color-scheme: light dark; } '
                "@media (prefers-color-scheme: dark) { "
                ".rail { stroke: #30363d; } }</style>",
                '<line class="rail" x1="24" y1="18" x2="1176" y2="18" '
                'stroke="#d0d7de" stroke-width="1"/>',
                *chips,
            )
        ),
        aria="Tech stack",
    )


def _clouds() -> str:
    flakes = []
    for i in range(11):
        x = 80 + i * 100
        s = 5 + (i % 3) * 3
        flakes.append(
            f'<path transform="translate({x} 18) scale({s / 10:.2f})" '
            'd="M0-8 L2-2 L8-2 L3 1 L5 7 L0 3 L-5 7 L-3 1 L-8-2 L-2-2 Z" '
            'fill="#8250df"/>'
        )
    return _svg(
        "\n".join(
            (
                '<style>:root { color-scheme: light dark; } '
                "@media (prefers-color-scheme: dark) { "
                ".haze { stroke: #30363d; } }</style>",
                '<line class="haze" x1="24" y1="18" x2="1176" y2="18" '
                'stroke="#d0d7de" stroke-width="1" stroke-dasharray="2 8"/>',
                *flakes,
            )
        ),
        aria="Word clouds",
    )


def _blog() -> str:
    return _svg(
        "\n".join(
            (
                '<style>:root { color-scheme: light dark; } '
                ".rule { stroke: #8250df; } "
                "@media (prefers-color-scheme: dark) { "
                ".rule { stroke: #a371f7; } .page { fill: #0d1117; "
                "stroke: #30363d; } }</style>",
                '<line class="rule" x1="24" y1="18" x2="520" y2="18" '
                'stroke-width="1.4"/>',
                '<rect class="page" x="568" y="6" width="64" height="24" '
                'rx="3" fill="#ffffff" stroke="#d0d7de"/>',
                '<line x1="578" y1="13" x2="622" y2="13" stroke="#656d76" '
                'stroke-width="1"/>',
                '<line x1="578" y1="18" x2="614" y2="18" stroke="#656d76" '
                'stroke-width="1"/>',
                '<line x1="578" y1="23" x2="618" y2="23" stroke="#656d76" '
                'stroke-width="1"/>',
                '<line class="rule" x1="680" y1="18" x2="1176" y2="18" '
                'stroke-width="1.4"/>',
            )
        ),
        aria="Latest blog posts",
    )


_BUILDERS = {
    "featured": _featured,
    "metrics": _metrics,
    "living": _living,
    "tech": _tech,
    "clouds": _clouds,
    "blog": _blog,
}


def generate_separators(*, output_dir: Path | None = None) -> list[Path]:
    """Write the unique separator fleet and return written paths."""
    dest = output_dir or _OUT_DIR
    dest.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for filename, key in SEPARATOR_SPECS:
        path = dest / filename
        path.write_text(_BUILDERS[key](), encoding="utf-8")
        written.append(path)
        logger.info("Wrote README separator {}", path)
    return written
