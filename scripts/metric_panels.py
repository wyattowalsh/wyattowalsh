"""Shared SVG and GFM primitives for compact profile metrics."""

from __future__ import annotations

from collections.abc import Iterable
from html import escape
from unicodedata import east_asian_width


def fit_label(value: str, width: float, size: int) -> str:
    """Bound a proportional label, allowing more space for wide glyphs."""
    used = 0.0
    for index, char in enumerate(value):
        if char.isascii() and char in "ilI.,:'| !()":
            advance = 0.36
        elif char.isascii() and char in "MWmw@%":
            advance = 1.0
        elif char.isascii():
            advance = 0.78
        else:
            advance = 1.1 if east_asian_width(char) in {"F", "W"} else 1.0
        used += advance * size
        if used > width - (size if index < len(value) - 1 else 0):
            return value[:index].rstrip() + "…"
    return value


def text(
    x: float, y: float, value: str, cls: str = "label", *, end: bool = False
) -> str:
    anchor = "end" if end else "start"
    return (
        f'<text x="{x:g}" y="{y:g}" class="{cls}" text-anchor="{anchor}">'
        f"{escape(value)}</text>"
    )


def rect(x: float, y: float, w: float, h: float, cls: str, radius: int = 2) -> str:
    return (
        f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" '
        f'rx="{radius}" class="{cls}"/>'
    )


def rule(x1: float, y: float, x2: float, cls: str = "rule") -> str:
    return f'<path d="M{x1:g} {y:g}H{x2:g}" class="{cls}" fill="none"/>'


def panel(title: str, alt: str, light: str, dark: str, content: Iterable[str]) -> str:
    css = f"""
text{{font-family:-apple-system,BlinkMacSystemFont,Arial,Helvetica,sans-serif;
fill:#1d2936;font-variant-numeric:tabular-nums}}
.paper{{fill:#faf8f3;stroke:#c9cec9}}.rule{{stroke:#c9cec9}}.track{{fill:#e2e3de}}
.label,.number,.minor,.accentLabel{{font-size:18px}}.label,.number{{font-weight:600}}
.minor{{fill:#50606d}}.title{{font-size:23px;font-weight:700;letter-spacing:-.55px}}
.hero{{font-size:33px;font-weight:700;letter-spacing:-1px}}.accentLabel{{font-weight:700}}
.accent,.hero,.accentLabel{{fill:{light}}}.soft{{fill:#778594}}
.zero{{stroke:{light};stroke-width:2}}
@media(prefers-color-scheme:dark){{
text{{fill:#eef3f7}}.paper{{fill:#161b22;stroke:#444f5a}}
.rule{{stroke:#444f5a}}.track{{fill:#37424c}}.minor{{fill:#b6c2cc}}
.accent,.hero,.accentLabel{{fill:{dark}}}.soft{{fill:#96a4b1}}.zero{{stroke:{dark}}}
}}
"""
    return "\n".join(
        (
            '<svg xmlns="http://www.w3.org/2000/svg" width="300" height="246" '
            'viewBox="0 0 300 246" role="img" aria-labelledby="title description">',
            f'<title id="title">{escape(title)}</title>',
            f'<desc id="description">{escape(alt)}</desc>',
            f"<style>{css}</style>",
            '<rect x=".5" y=".5" width="299" height="245" rx="9" class="paper"/>',
            *content,
            "</svg>",
            "",
        )
    )


def literal(value: str) -> str:
    """Render collected labels as literal single-line Markdown table/prose text."""
    return escape(" ".join(value.split()), quote=False).translate(
        {ord(char): f"&#{ord(char)};" for char in r"\|`*_[]~!#@"}
    )


def table(left: str, right: str, rows: Iterable[tuple[str, str]]) -> str:
    return "\n".join(
        (
            f"| {left} | {right} |",
            "| --- | --- |",
            *(f"| {literal(name)} | {literal(value)} |" for name, value in rows),
        )
    )


def disclosure(title: str, parts: Iterable[str], link: str, name: str) -> str:
    return (
        "\n\n".join(
            (
                f"<details>\n<summary>{title}</summary>",
                *(part for part in parts if part),
                f"[{link}](.github/assets/img/{name}.svg)",
                "</details>",
            )
        )
        + "\n"
    )
