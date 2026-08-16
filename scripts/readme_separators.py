"""Unique horizontal SVG separators for README section breaks.

Each separator is a distinct visual dialect so adjacent sections do not
rhyme. Files land under ``.github/assets/img/readme/sep-*.svg``.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Sequence
from pathlib import Path

from .utils import get_logger

logger = get_logger(module=__name__)

_REPO_ROOT = Path(__file__).resolve().parent.parent
_OUT_DIR = _REPO_ROOT / ".github" / "assets" / "img" / "readme"

SEP_WIDTH = 1200
SEP_HEIGHT = 52
_MID = SEP_HEIGHT / 2

SEPARATOR_SPECS: tuple[tuple[str, str], ...] = (
    ("sep-featured.svg", "featured"),
    ("sep-metrics.svg", "metrics"),
    ("sep-living.svg", "living"),
    ("sep-tech.svg", "tech"),
    ("sep-clouds.svg", "clouds"),
    ("sep-blog.svg", "blog"),
    ("sep-qr.svg", "qr"),
)

# Assembler titles the section "My Tech Stack".
_TECH_ARIA = "My Tech Stack"


def _n(value: float) -> str:
    rounded = round(float(value), 2)
    if abs(rounded) < 0.005:
        rounded = 0.0
    text = f"{rounded:.2f}"
    return text.rstrip("0").rstrip(".") if "." in text else text


def _el(tag: str, **attrs: object) -> str:
    bits = [f"<{tag}"]
    for key, raw in attrs.items():
        if raw is None:
            continue
        name = "class" if key == "class_" else key.replace("_", "-")
        bits.append(f' {name}="{raw}"')
    bits.append("/>")
    return "".join(bits)


def _style(rules: str, dark: str) -> str:
    return (
        "<style>:root { color-scheme: light dark; } "
        f"{rules} "
        f"@media (prefers-color-scheme: dark) {{ {dark} }}</style>"
    )


def _svg(body: Iterable[str], *, aria: str) -> str:
    return "\n".join(
        (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{SEP_WIDTH}" '
            f'height="{SEP_HEIGHT}" viewBox="0 0 {SEP_WIDTH} {SEP_HEIGHT}" '
            f'role="img" aria-label="{aria}">',
            *body,
            "</svg>",
            "",
        )
    )


def _line(
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    *,
    class_: str,
    sw: float = 1,
    extra: str | None = None,
) -> str:
    attrs = (
        f'<line class="{class_}" x1="{_n(x1)}" y1="{_n(y1)}" '
        f'x2="{_n(x2)}" y2="{_n(y2)}" stroke-width="{_n(sw)}"'
    )
    if extra:
        return f"{attrs} {extra}/>"
    return f"{attrs}/>"


def _circle(
    cx: float,
    cy: float,
    r: float,
    *,
    class_: str,
    sw: float | None = None,
    fill: str = "none",
) -> str:
    bits = (
        f'<circle class="{class_}" cx="{_n(cx)}" cy="{_n(cy)}" r="{_n(r)}" '
        f'fill="{fill}"'
    )
    if sw is not None:
        bits += f' stroke-width="{_n(sw)}"'
    return bits + "/>"


def _path(d: str, *, class_: str, sw: float = 1, fill: str = "none") -> str:
    return (
        f'<path class="{class_}" d="{d}" fill="{fill}" '
        f'stroke-width="{_n(sw)}" stroke-linecap="round" '
        'stroke-linejoin="round"/>'
    )


def _diamond(cx: float, cy: float, rx: float, ry: float) -> str:
    return (
        f"M{_n(cx)} {_n(cy - ry)} L{_n(cx + rx)} {_n(cy)} "
        f"L{_n(cx)} {_n(cy + ry)} L{_n(cx - rx)} {_n(cy)} Z"
    )


def _poly_pts(points: Sequence[tuple[float, float]]) -> str:
    return " ".join(f"{_n(x)},{_n(y)}" for x, y in points)


def _star_pts(
    cx: float,
    cy: float,
    r_out: float,
    r_in: float,
    n: int,
    *,
    rot: float = -math.pi / 2,
) -> str:
    pts: list[tuple[float, float]] = []
    for i in range(n * 2):
        ang = rot + i * math.pi / n
        r = r_out if i % 2 == 0 else r_in
        pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
    return _poly_pts(pts)


def _hex_d(cx: float, cy: float, r: float) -> str:
    pts = [
        (cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a)))
        for a in range(0, 360, 60)
    ]
    return "M" + " L".join(f"{_n(x)} {_n(y)}" for x, y in pts) + " Z"


def _catmull_rom(points: Sequence[tuple[float, float]]) -> str:
    if len(points) < 2:
        return ""
    padded = [points[0], *points, points[-1]]
    parts = [f"M{_n(points[0][0])} {_n(points[0][1])}"]
    for i in range(1, len(padded) - 2):
        p0, p1, p2, p3 = padded[i - 1], padded[i], padded[i + 1], padded[i + 2]
        c1x = p1[0] + (p2[0] - p0[0]) / 6
        c1y = p1[1] + (p2[1] - p0[1]) / 6
        c2x = p2[0] - (p3[0] - p1[0]) / 6
        c2y = p2[1] - (p3[1] - p1[1]) / 6
        parts.append(
            f"C{_n(c1x)} {_n(c1y)} {_n(c2x)} {_n(c2y)} {_n(p2[0])} {_n(p2[1])}"
        )
    return " ".join(parts)


def _corner_bracket(x: float, y: float, dx: float, dy: float, arm: float) -> str:
    return f"M{_n(x + dx * arm)} {_n(y)} L{_n(x)} {_n(y)} L{_n(x)} {_n(y + dy * arm)}"


def _featured() -> str:
    """Art-deco / gothic filigree — pointed bays, layered rails, rose window."""
    parts: list[str] = [
        _style(
            ".rail { stroke: #d0d7de; fill: none; } "
            ".under { stroke: #6366f1; fill: none; opacity: 0.22; } "
            ".filigree { stroke: #6366f1; fill: none; } "
            ".jewel { stroke: #4f46e5; fill: #6366f1; } "
            ".rose { stroke: #4f46e5; fill: none; } "
            ".rose-fill { fill: #6366f1; stroke: none; }",
            ".rail { stroke: #30363d; } "
            ".under { stroke: #818cf8; } "
            ".filigree { stroke: #818cf8; } "
            ".jewel { stroke: #a5b4fc; fill: #818cf8; } "
            ".rose { stroke: #a5b4fc; } "
            ".rose-fill { fill: #818cf8; }",
        )
    ]
    for y, sw in ((10, 0.6), (26, 1.05), (42, 0.6)):
        parts.append(_line(18, y, 1182, y, class_="rail", sw=sw))

    cx_rose = 600.0
    keepout = 78.0
    for x in range(36, 1165, 18):
        if abs(x - cx_rose) < keepout:
            continue
        parts.append(_line(x, 10, x, 42, class_="filigree", sw=0.45))
        if (x - 36) % 36 == 0:
            parts.append(
                _path(_diamond(x, 26, 3.2, 4.6), class_="jewel", sw=0.7, fill="#6366f1")
            )
        else:
            parts.append(_circle(x, 26, 1.15, class_="jewel", fill="#6366f1"))

    for x in range(54, 1147, 36):
        if abs(x - cx_rose) < keepout:
            continue
        outer = (
            f"M{_n(x - 16)} 26 L{_n(x - 8)} 14 Q{_n(x)} 6 {_n(x + 8)} 14 "
            f"L{_n(x + 16)} 26"
        )
        inner = (
            f"M{_n(x - 10)} 26 L{_n(x - 5)} 17 Q{_n(x)} 11 {_n(x + 5)} 17 "
            f"L{_n(x + 10)} 26"
        )
        parts.append(_path(outer, class_="under", sw=2.6))
        parts.append(_path(outer, class_="filigree", sw=1.05))
        parts.append(_path(inner, class_="filigree", sw=0.7))
        parts.append(
            _path(
                _diamond(x, 18, 2.1, 3.2),
                class_="jewel",
                sw=0.6,
                fill="#6366f1",
            )
        )

    for x, dx in ((22, 1), (1178, -1)):
        for inset, sw in ((0, 1.3), (5, 0.7)):
            parts.append(
                _path(
                    _corner_bracket(x + dx * inset, 8 + inset, dx, 1, 16 - inset),
                    class_="filigree",
                    sw=sw,
                )
            )
            parts.append(
                _path(
                    _corner_bracket(x + dx * inset, 44 - inset, dx, -1, 16 - inset),
                    class_="filigree",
                    sw=sw,
                )
            )

    for r, sw in ((21, 1.5), (15.5, 0.9), (9.5, 1.1), (5.2, 0.8)):
        parts.append(_circle(cx_rose, 26, r, class_="rose", sw=sw))
    for i in range(12):
        ang = math.radians(i * 30 - 90)
        x2 = cx_rose + 20.5 * math.cos(ang)
        y2 = 26 + 20.5 * math.sin(ang)
        parts.append(_line(cx_rose, 26, x2, y2, class_="filigree", sw=0.55))
        tip = (
            f"M{_n(cx_rose + 9 * math.cos(ang - 0.18))} "
            f"{_n(26 + 9 * math.sin(ang - 0.18))} "
            f"L{_n(cx_rose + 21 * math.cos(ang))} {_n(26 + 21 * math.sin(ang))} "
            f"L{_n(cx_rose + 9 * math.cos(ang + 0.18))} "
            f"{_n(26 + 9 * math.sin(ang + 0.18))}"
        )
        parts.append(_path(tip, class_="filigree", sw=0.7))
    parts.append(
        f'<polygon class="jewel" points="{_star_pts(cx_rose, 26, 8.2, 3.4, 8)}" '
        'stroke-width="0.7"/>'
    )
    parts.append(_circle(cx_rose, 26, 2.1, class_="rose-fill", fill="#6366f1"))
    for i in range(8):
        ang = math.radians(i * 45 + 22.5)
        parts.append(
            _circle(
                cx_rose + 12.2 * math.cos(ang),
                26 + 12.2 * math.sin(ang),
                1.05,
                class_="rose-fill",
                fill="#6366f1",
            )
        )
    return _svg(parts, aria="Featured projects")


def _metrics() -> str:
    """Instrument cluster — dual harmonic sparks, graduated ticks, reticle."""
    parts: list[str] = [
        _style(
            ".base { stroke: #d0d7de; fill: none; } "
            ".tick { stroke: #8b949e; fill: none; } "
            ".grid { fill: #d0d7de; stroke: none; } "
            ".spark { fill: none; stroke: #1a7f37; } "
            ".spark-b { fill: none; stroke: #1a7f37; opacity: 0.45; } "
            ".bead { fill: #1a7f37; stroke: none; } "
            ".reticle { stroke: #1a7f37; fill: none; }",
            ".base { stroke: #30363d; } "
            ".tick { stroke: #6e7681; } "
            ".grid { fill: #30363d; } "
            ".spark { stroke: #3fb950; } "
            ".spark-b { stroke: #3fb950; } "
            ".bead { fill: #3fb950; } "
            ".reticle { stroke: #3fb950; }",
        )
    ]
    for x in range(24, 1177, 20):
        for y in (12, 22, 32):
            if abs(x - 600) < 34:
                continue
            parts.append(_circle(x, y, 0.55, class_="grid", fill="#d0d7de"))

    parts.append(_line(20, 44, 1180, 44, class_="base", sw=1.1))
    parts.append(_line(20, 8, 20, 44, class_="base", sw=1.0))
    parts.append(_line(1180, 8, 1180, 44, class_="base", sw=1.0))
    for x in range(20, 1181, 8):
        major = (x - 20) % 40 == 0
        h = 8 if major else 3.4
        parts.append(_line(x, 44, x, 44 - h, class_="tick", sw=1.05 if major else 0.6))
        if major and abs(x - 600) > 40:
            parts.append(_line(x, 8, x, 11.5, class_="tick", sw=0.7))

    def _wave(amp: float, phase: float, k2: float) -> list[tuple[float, float]]:
        pts: list[tuple[float, float]] = []
        for x in range(24, 1177, 4):
            t = (x - 24) / 1152 * math.pi * 5
            y = 24 - amp * math.sin(t + phase) - amp * 0.28 * math.sin(2 * t + k2)
            pts.append((x, y))
        return pts

    primary = _wave(11.5, 0.15, 0.8)
    harmonic = _wave(6.4, 1.35, 2.1)
    parts.append(
        f'<polyline class="spark" points="{_poly_pts(primary)}" '
        'stroke-width="2.05" stroke-linejoin="round" stroke-linecap="round"/>'
    )
    parts.append(
        f'<polyline class="spark-b" points="{_poly_pts(harmonic)}" '
        'stroke-width="1.15" stroke-linejoin="round" stroke-dasharray="3 4"/>'
    )
    for i, (x, y) in enumerate(primary):
        if i % 24 != 0:
            continue
        parts.append(_circle(x, y, 1.7, class_="bead", fill="#1a7f37"))

    rcx, rcy = 600.0, 24.0
    parts.append(_circle(rcx, rcy, 16.5, class_="reticle", sw=1.2))
    parts.append(_circle(rcx, rcy, 10.0, class_="reticle", sw=0.7))
    parts.append(_line(rcx - 19, rcy, rcx - 11, rcy, class_="reticle", sw=0.75))
    parts.append(_line(rcx + 11, rcy, rcx + 19, rcy, class_="reticle", sw=0.75))
    parts.append(_line(rcx, rcy - 19, rcx, rcy - 11, class_="reticle", sw=0.75))
    parts.append(_line(rcx, rcy + 11, rcx, rcy + 19, class_="reticle", sw=0.75))
    for i in range(8):
        ang = math.radians(i * 45)
        parts.append(
            _line(
                rcx + 13.4 * math.cos(ang),
                rcy + 13.4 * math.sin(ang),
                rcx + 16.2 * math.cos(ang),
                rcy + 16.2 * math.sin(ang),
                class_="reticle",
                sw=0.8,
            )
        )
    return _svg(parts, aria="Metrics")


def _leaf_d(length: float) -> str:
    return (
        f"M0 0 C{_n(length * 0.28)} {_n(-length * 0.46)} "
        f"{_n(length * 0.68)} {_n(-length * 0.38)} {_n(length)} 0 "
        f"C{_n(length * 0.68)} {_n(length * 0.34)} "
        f"{_n(length * 0.28)} {_n(length * 0.24)} 0 0 Z"
    )


def _living() -> str:
    """Botanical vine — undulating spine, leaves, tendrils, layered bloom."""
    parts: list[str] = [
        _style(
            ".soil { stroke: #d0d7de; fill: none; } "
            ".seed { fill: #9a6700; stroke: none; } "
            ".vine { stroke: #1a7f37; fill: none; } "
            ".tendril { stroke: #2da44e; fill: none; } "
            ".leaf { fill: #1a7f37; stroke: #116329; } "
            ".bloom { stroke: #bf4b8a; fill: none; } "
            ".petal { fill: #bf4b8a; stroke: #9b3b70; } "
            ".pistil { fill: #bf3989; stroke: none; }",
            ".soil { stroke: #30363d; } "
            ".seed { fill: #d4a72c; } "
            ".vine { stroke: #3fb950; } "
            ".tendril { stroke: #56d364; } "
            ".leaf { fill: #3fb950; stroke: #56d364; } "
            ".bloom { stroke: #f778ba; } "
            ".petal { fill: #f778ba; stroke: #ff9bce; } "
            ".pistil { fill: #ff9bce; }",
        )
    ]
    parts.append(_line(16, 46, 1184, 46, class_="soil", sw=1.05))
    for x in range(28, 1173, 14):
        jitter = 1.4 if (x // 14) % 2 == 0 else -1.0
        parts.append(
            _circle(x, 46 + jitter * 0.15, 1.05, class_="seed", fill="#9a6700")
        )
        parts.append(_line(x, 46, x, 43.2, class_="soil", sw=0.5))

    spine: list[tuple[float, float]] = []
    for x in range(16, 1185, 16):
        y = 30 + 9.5 * math.sin((x - 16) / 70) + 3.2 * math.sin((x - 16) / 27)
        spine.append((x, y))
    vine = _catmull_rom(spine)
    parts.append(_path(vine, class_="vine", sw=2.8))
    parts.append(_path(vine, class_="tendril", sw=1.15))

    companion: list[tuple[float, float]] = []
    for x in range(40, 1161, 20):
        y = 34 + 6.5 * math.sin((x - 40) / 55 + 1.2)
        companion.append((x, y))
    parts.append(_path(_catmull_rom(companion), class_="tendril", sw=0.85))

    for i, (x, y) in enumerate(spine[2:-2]):
        if i % 3 != 0 or abs(x - 600) < 48:
            continue
        nxt = spine[i + 3]
        ang = math.degrees(math.atan2(nxt[1] - y, nxt[0] - x))
        side = -1 if i % 6 == 0 else 1
        length = 13 if i % 2 == 0 else 10.5
        rot = ang + side * 58
        parts.append(
            f'<path class="leaf" transform="translate({_n(x)} {_n(y)}) '
            f'rotate({_n(rot)})" d="{_leaf_d(length)}" stroke-width="0.6"/>'
        )
        vein = f"M0 0 L{_n(length * 0.78)} 0"
        parts.append(
            f'<path class="tendril" transform="translate({_n(x)} {_n(y)}) '
            f'rotate({_n(rot)})" d="{vein}" fill="none" stroke-width="0.55"/>'
        )

    for x, y, sweep in (
        (92, 18, 1),
        (248, 36, -1),
        (404, 16, 1),
        (796, 36, -1),
        (952, 16, 1),
        (1108, 36, -1),
    ):
        curl = (
            f"M{_n(x)} {_n(y)} "
            f"C{_n(x + 8)} {_n(y - 10 * sweep)} {_n(x + 18)} {_n(y + 1 * sweep)} "
            f"{_n(x + 12)} {_n(y + 8 * sweep)} "
            f"C{_n(x + 8)} {_n(y + 12 * sweep)} {_n(x + 4)} {_n(y + 5 * sweep)} "
            f"{_n(x + 8)} {_n(y + 2 * sweep)}"
        )
        parts.append(_path(curl, class_="tendril", sw=0.95))

    bx, by = 600.0, 24.0
    parts.append(_circle(bx, by, 18.5, class_="bloom", sw=0.8))
    for i in range(8):
        ang = i * 45
        parts.append(
            f'<path class="petal" transform="translate({_n(bx)} {_n(by)}) '
            f'rotate({_n(ang)}) translate(6.2 0)" d="{_leaf_d(10.5)}" '
            'stroke-width="0.55"/>'
        )
    parts.append(_circle(bx, by, 3.2, class_="pistil", fill="#bf3989"))
    for i in range(5):
        ang = math.radians(i * 72 - 90)
        parts.append(
            _circle(
                bx + 1.6 * math.cos(ang),
                by + 1.6 * math.sin(ang),
                0.65,
                class_="pistil",
                fill="#bf3989",
            )
        )
    return _svg(parts, aria="Living art")


def _tech() -> str:
    """Printed circuit — orthogonal buses, language-colored hex pads, DIP chip."""
    colors = (
        "#3776ab",
        "#f7df1e",
        "#3178c6",
        "#e34f26",
        "#2496ed",
        "#24292f",
        "#ff6c37",
        "#0969da",
    )
    xs = (70, 190, 310, 430, 770, 890, 1010, 1130)
    parts: list[str] = [
        _style(
            ".trace { stroke: #8b949e; fill: none; } "
            ".trace-hi { stroke: #0969da; fill: none; } "
            ".via { stroke: #656d76; fill: #ffffff; } "
            ".chip { fill: #1f2328; stroke: #656d76; } "
            ".pin { stroke: #8b949e; fill: #d0d7de; } "
            ".silk { stroke: #8b949e; fill: none; } "
            ".pad { stroke: #1f2328; }",
            ".trace { stroke: #6e7681; } "
            ".trace-hi { stroke: #58a6ff; } "
            ".via { stroke: #8b949e; fill: #0d1117; } "
            ".chip { fill: #21262d; stroke: #8b949e; } "
            ".pin { stroke: #8b949e; fill: #30363d; } "
            ".silk { stroke: #8b949e; } "
            ".pad { stroke: #c9d1d9; }",
        )
    ]
    for y in (16, 36):
        parts.append(_line(20, y, 1180, y, class_="trace", sw=1.35))
        parts.append(_line(20, y + 3.2, 1180, y + 3.2, class_="trace", sw=0.6))
    parts.append(_line(20, 16, 20, 39.2, class_="trace", sw=1.1))
    parts.append(_line(1180, 16, 1180, 39.2, class_="trace", sw=1.1))

    for i, (x, color) in enumerate(zip(xs, colors, strict=True)):
        bus_y = 16 if i % 2 == 0 else 36
        parts.append(_line(x, bus_y, x, 26, class_="trace-hi", sw=1.2))
        parts.append(
            _line(x, 26, x + (10 if i < 4 else -10), 26, class_="trace-hi", sw=1.2)
        )
        parts.append(_circle(x, bus_y, 2.4, class_="via", sw=0.8, fill="#ffffff"))
        parts.append(
            f'<path class="pad" d="{_hex_d(x, 26, 11)}" fill="{color}" '
            'stroke-width="1.05"/>'
        )
        parts.append(_circle(x, 26, 3.1, class_="via", sw=0.7, fill="#ffffff"))
        if i % 2 == 0:
            zig = (
                f"M{_n(x + 16)} 16 L{_n(x + 20)} 12 L{_n(x + 24)} 16 "
                f"L{_n(x + 28)} 12 L{_n(x + 32)} 16"
            )
            parts.append(_path(zig, class_="silk", sw=0.85))

    for x in range(40, 1161, 40):
        if any(abs(x - px) < 28 for px in xs) or abs(x - 600) < 70:
            continue
        parts.append(_circle(x, 16, 1.5, class_="via", sw=0.6, fill="#ffffff"))
        parts.append(_circle(x, 36, 1.5, class_="via", sw=0.6, fill="#ffffff"))

    chip_x, chip_y, cw, ch = 600.0, 26.0, 78.0, 28.0
    parts.append(
        f'<rect class="chip" x="{_n(chip_x - cw / 2)}" y="{_n(chip_y - ch / 2)}" '
        f'width="{_n(cw)}" height="{_n(ch)}" rx="3" stroke-width="1.15"/>'
    )
    parts.append(
        _path(
            f"M{_n(chip_x - cw / 2)} {_n(chip_y - 5)} "
            f"A5 5 0 0 1 {_n(chip_x - cw / 2)} {_n(chip_y + 5)}",
            class_="silk",
            sw=1.1,
        )
    )
    parts.append(_circle(chip_x - 30, chip_y - 7, 1.6, class_="silk", sw=0.7))
    for i in range(7):
        px = chip_x - 30 + i * 10
        parts.append(
            f'<rect class="pin" x="{_n(px - 1.4)}" y="{_n(chip_y - ch / 2 - 6)}" '
            'width="2.8" height="6" rx="0.6" stroke-width="0.6"/>'
        )
        parts.append(
            f'<rect class="pin" x="{_n(px - 1.4)}" y="{_n(chip_y + ch / 2)}" '
            'width="2.8" height="6" rx="0.6" stroke-width="0.6"/>'
        )
        parts.append(_line(px, chip_y - ch / 2 - 6, px, 16, class_="trace-hi", sw=0.85))
        parts.append(_line(px, chip_y + ch / 2 + 6, px, 36, class_="trace-hi", sw=0.85))
    for dx in (-16, 0, 16):
        parts.append(
            _line(
                chip_x + dx - 8,
                chip_y,
                chip_x + dx + 8,
                chip_y,
                class_="silk",
                sw=0.6,
            )
        )
    return _svg(parts, aria=_TECH_ARIA)


def _cloud_puff(cx: float, cy: float, s: float) -> str:
    return (
        f"M{_n(cx - 22 * s)} {_n(cy + 4 * s)} "
        f"C{_n(cx - 24 * s)} {_n(cy - 8 * s)} {_n(cx - 10 * s)} {_n(cy - 12 * s)} "
        f"{_n(cx - 4 * s)} {_n(cy - 6 * s)} "
        f"C{_n(cx - 2 * s)} {_n(cy - 16 * s)} {_n(cx + 14 * s)} {_n(cy - 16 * s)} "
        f"{_n(cx + 14 * s)} {_n(cy - 5 * s)} "
        f"C{_n(cx + 26 * s)} {_n(cy - 8 * s)} {_n(cx + 28 * s)} {_n(cy + 6 * s)} "
        f"{_n(cx + 16 * s)} {_n(cy + 7 * s)} "
        f"C{_n(cx + 10 * s)} {_n(cy + 12 * s)} {_n(cx - 12 * s)} {_n(cy + 12 * s)} "
        f"{_n(cx - 22 * s)} {_n(cy + 4 * s)} Z"
    )


def _crescent(cx: float, cy: float, r: float, flip: float) -> str:
    sweep = 1 if flip > 0 else 0
    back = 0 if flip > 0 else 1
    return (
        f"M{_n(cx)} {_n(cy - r)} "
        f"A{_n(r)} {_n(r)} 0 1 {sweep} {_n(cx)} {_n(cy + r)} "
        f"A{_n(r * 0.72)} {_n(r * 0.72)} 0 1 {back} {_n(cx)} {_n(cy - r)} Z"
    )


def _spiral(cx: float, cy: float, turns: float = 3.4) -> str:
    pts: list[str] = []
    steps = 92
    for i in range(steps):
        theta = i / steps * turns * 2 * math.pi
        r = 1.1 + 0.55 * theta
        x = cx + r * math.cos(theta)
        y = cy + r * math.sin(theta)
        cmd = "M" if i == 0 else "L"
        pts.append(f"{cmd}{_n(x)} {_n(y)}")
    return " ".join(pts)


def _clouds() -> str:
    """Celestial haze — scalloped puffs, mixed stars, crescents, spiral galaxy."""
    parts: list[str] = [
        _style(
            ".haze { stroke: #d0d7de; fill: none; } "
            ".puff { fill: #ddc7ff; stroke: #8250df; } "
            ".star { fill: #8250df; stroke: #6e40c9; } "
            ".moon { fill: none; stroke: #8250df; } "
            ".spiral { fill: none; stroke: #8250df; } "
            ".comet { fill: none; stroke: #8250df; }",
            ".haze { stroke: #30363d; } "
            ".puff { fill: #2d1b4e; stroke: #a371f7; } "
            ".star { fill: #a371f7; stroke: #d2a8ff; } "
            ".moon { stroke: #a371f7; } "
            ".spiral { stroke: #a371f7; } "
            ".comet { stroke: #d2a8ff; }",
        )
    ]
    haze_pts: list[str] = []
    for x in range(20, 1181, 10):
        y = 26 + 3.2 * math.sin(x / 28) + 1.4 * math.sin(x / 11)
        haze_pts.append(f"{_n(x)},{_n(y)}")
    parts.append(
        f'<polyline class="haze" points="{" ".join(haze_pts)}" '
        'stroke-width="0.9" stroke-dasharray="1.4 5"/>'
    )
    for x in range(28, 1173, 9):
        if abs(x - 600) < 42:
            continue
        y = 18 + (x * 7) % 17
        parts.append(_circle(x, y, 0.55, class_="star", fill="#8250df"))

    for cx, s in (
        (80, 0.95),
        (180, 0.7),
        (300, 1.05),
        (420, 0.78),
        (780, 0.82),
        (900, 1.08),
        (1020, 0.72),
        (1130, 0.92),
    ):
        d = _cloud_puff(cx, 28, s)
        parts.append(_path(d, class_="puff", sw=1.7, fill="#ddc7ff"))
        parts.append(_path(d, class_="puff", sw=0.75, fill="none"))

    star_field = (
        (48, 14, 5, 6.2, 2.4),
        (128, 40, 4, 4.4, 1.7),
        (236, 12, 6, 5.4, 2.2),
        (352, 42, 5, 4.8, 1.9),
        (468, 13, 4, 3.8, 1.5),
        (732, 12, 5, 5.0, 2.0),
        (848, 42, 6, 4.6, 1.8),
        (964, 13, 4, 4.0, 1.6),
        (1084, 40, 5, 5.6, 2.2),
        (1164, 16, 4, 3.6, 1.4),
    )
    for cx, cy, n, r_out, r_in in star_field:
        parts.append(
            f'<polygon class="star" points="{_star_pts(cx, cy, r_out, r_in, n)}" '
            'stroke-width="0.55"/>'
        )

    for cx, flip in ((46, 1.0), (1154, -1.0)):
        parts.append(
            _path(_crescent(cx, 30, 8.6, flip), class_="moon", sw=1.05, fill="none")
        )

    parts.append(_path(_spiral(600, 26), class_="spiral", sw=1.35))
    parts.append(_circle(600, 26, 2.4, class_="star", fill="#8250df"))
    parts.append(_circle(600, 26, 18, class_="spiral", sw=0.6))
    parts.append(_circle(600, 26, 12, class_="spiral", sw=0.45))
    parts.append(
        _path(
            "M670 14 C700 10, 730 16, 754 11",
            class_="comet",
            sw=1.05,
        )
    )
    parts.append(
        f'<polygon class="star" points="{_star_pts(758, 10.5, 3.6, 1.5, 5)}" '
        'stroke-width="0.45"/>'
    )
    return _svg(parts, aria="Word clouds")


def _fleuron(cx: float, cy: float, s: float = 1.0) -> str:
    return (
        f"M{_n(cx)} {_n(cy)} "
        f"C{_n(cx + 5 * s)} {_n(cy - 11 * s)} {_n(cx + 13 * s)} {_n(cy - 7 * s)} "
        f"{_n(cx + 9 * s)} {_n(cy)} "
        f"C{_n(cx + 13 * s)} {_n(cy + 7 * s)} {_n(cx + 5 * s)} {_n(cy + 11 * s)} "
        f"{_n(cx)} {_n(cy)} "
        f"C{_n(cx - 5 * s)} {_n(cy - 11 * s)} {_n(cx - 13 * s)} {_n(cy - 7 * s)} "
        f"{_n(cx - 9 * s)} {_n(cy)} "
        f"C{_n(cx - 13 * s)} {_n(cy + 7 * s)} {_n(cx - 5 * s)} {_n(cy + 11 * s)} "
        f"{_n(cx)} {_n(cy)} Z"
    )


def _blog() -> str:
    """Manuscript rules — double typographic lines, fleurons, open folio, quill."""
    parts: list[str] = [
        _style(
            ".rule { stroke: #8250df; fill: none; } "
            ".rule-thin { stroke: #8250df; fill: none; opacity: 0.55; } "
            ".fleuron { fill: #8250df; stroke: #6e40c9; } "
            ".page { fill: #ffffff; stroke: #d0d7de; } "
            ".ink { stroke: #656d76; fill: none; } "
            ".ribbon { fill: #bf4b8a; stroke: none; } "
            ".quill { stroke: #8250df; fill: #ddc7ff; }",
            ".rule { stroke: #a371f7; } "
            ".rule-thin { stroke: #a371f7; } "
            ".fleuron { fill: #a371f7; stroke: #d2a8ff; } "
            ".page { fill: #0d1117; stroke: #30363d; } "
            ".ink { stroke: #8b949e; } "
            ".ribbon { fill: #f778ba; } "
            ".quill { stroke: #a371f7; fill: #2d1b4e; }",
        )
    ]
    left, right, gap_l, gap_r = 20.0, 1180.0, 528.0, 672.0
    for y, sw, cls in ((22, 2.15, "rule"), (26, 0.7, "rule-thin"), (30, 2.15, "rule")):
        parts.append(_line(left, y, gap_l, y, class_=cls, sw=sw))
        parts.append(_line(gap_r, y, right, y, class_=cls, sw=sw))
    parts.append(_line(left, 18, left, 34, class_="rule", sw=1.2))
    parts.append(_line(right, 18, right, 34, class_="rule", sw=1.2))

    for x in range(48, 501, 68):
        parts.append(
            _path(_fleuron(x, 26, 0.92), class_="fleuron", sw=0.65, fill="#8250df")
        )
        parts.append(
            _path(_diamond(x, 26, 2.0, 2.8), class_="fleuron", sw=0.5, fill="#8250df")
        )
    for x in range(708, 1161, 68):
        parts.append(
            _path(_fleuron(x, 26, 0.92), class_="fleuron", sw=0.65, fill="#8250df")
        )
        parts.append(
            _path(_diamond(x, 26, 2.0, 2.8), class_="fleuron", sw=0.5, fill="#8250df")
        )
    for x in (24, 516, 684, 1176):
        parts.append(
            _path(_diamond(x, 26, 3.4, 5.2), class_="fleuron", sw=0.7, fill="#8250df")
        )

    bx, by = 600.0, 26.0
    parts.append(
        f'<rect class="page" x="{_n(bx - 46)}" y="{_n(by - 18)}" width="44" '
        'height="36" rx="2.5" stroke-width="1.15"/>'
    )
    parts.append(
        f'<rect class="page" x="{_n(bx + 2)}" y="{_n(by - 18)}" width="44" '
        'height="36" rx="2.5" stroke-width="1.15"/>'
    )
    parts.append(_line(bx, by - 18, bx, by + 18, class_="ink", sw=1.25))
    for side in (-1, 1):
        px = bx + side * 8
        for i in range(5):
            y = by - 11 + i * 5.2
            x2 = px + side * 28
            parts.append(_line(px, y, x2, y, class_="ink", sw=0.7))
    parts.append(
        f'<path class="ribbon" d="M{_n(bx + 10)} {_n(by + 18)} '
        f"L{_n(bx + 16)} {_n(by + 18)} L{_n(bx + 16)} {_n(by + 24)} "
        f'L{_n(bx + 13)} {_n(by + 21.5)} L{_n(bx + 10)} {_n(by + 24)} Z"/>'
    )
    parts.append(
        _path(
            f"M{_n(bx - 10)} {_n(by - 18)} Q{_n(bx)} {_n(by - 22)} "
            f"{_n(bx + 10)} {_n(by - 18)}",
            class_="rule",
            sw=1.0,
        )
    )

    qx, qy = 458.0, 40.0
    parts.append(
        _path(
            f"M{_n(qx)} {_n(qy)} L{_n(qx + 34)} {_n(qy - 26)}",
            class_="quill",
            sw=1.2,
        )
    )
    for i in range(4):
        t = 0.28 + i * 0.16
        sx = qx + 34 * t
        sy = qy - 26 * t
        parts.append(_line(sx, sy, sx - 7, sy - 6, class_="quill", sw=0.7))
    parts.append(
        _path(
            f"M{_n(qx)} {_n(qy)} L{_n(qx - 4)} {_n(qy + 5)} "
            f"L{_n(qx + 3)} {_n(qy + 1)} Z",
            class_="quill",
            sw=0.6,
            fill="#ddc7ff",
        )
    )
    return _svg(parts, aria="Latest blog posts")


def _qr() -> str:
    """Finder-square rail — a contact-card motif, not a badge row."""
    parts: list[str] = [
        _style(
            ".rail { stroke: #0969da; fill: none; } "
            ".mod { fill: #0969da; } "
            ".finder { fill: none; stroke: #0969da; }",
            ".rail { stroke: #58a6ff; } "
            ".mod { fill: #58a6ff; } "
            ".finder { stroke: #58a6ff; }",
        ),
        _line(
            20, 26, 520, 26, class_="rail", sw=1.15, extra='stroke-dasharray="3 7"'
        ),
        _line(
            680, 26, 1180, 26, class_="rail", sw=1.15, extra='stroke-dasharray="3 7"'
        ),
    ]
    cx, cy, s = 600.0, 26.0, 18.0
    parts.append(
        _path(
            f"M{_n(cx - s)} {_n(cy - s)} H{_n(cx + s)} V{_n(cy + s)} "
            f"H{_n(cx - s)} Z",
            class_="finder",
            sw=1.6,
        )
    )
    parts.append(
        _path(
            f"M{_n(cx - s + 5)} {_n(cy - s + 5)} H{_n(cx + s - 5)} "
            f"V{_n(cy + s - 5)} H{_n(cx - s + 5)} Z",
            class_="finder",
            sw=1.1,
        )
    )
    parts.append(
        _el("rect", class_="mod", x=_n(cx - 4), y=_n(cy - 4), width="8", height="8")
    )
    modules = ((-28, -8), (-22, 6), (22, -10), (28, 4), (-8, 16), (10, -16))
    for i, (dx, dy) in enumerate(modules):
        size = 3.2 if i % 2 == 0 else 2.2
        parts.append(
            _el(
                "rect",
                class_="mod",
                x=_n(cx + dx),
                y=_n(cy + dy),
                width=_n(size),
                height=_n(size),
            )
        )
    return _svg(parts, aria="Connect")


_BUILDERS = {
    "featured": _featured,
    "metrics": _metrics,
    "living": _living,
    "tech": _tech,
    "clouds": _clouds,
    "blog": _blog,
    "qr": _qr,
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
