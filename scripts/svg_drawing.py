"""Lightweight svgwrite-compatible SVG builders (string-based).

Replaces the unmaintained ``svgwrite`` dependency for banner / generative art
while preserving the imperative Drawing API surface those modules already use
(``dwg.g``, ``dwg.filter``, ``path.Path``, dict-style attrs, ``Path.push``, etc.).
"""

from __future__ import annotations

import html
from collections.abc import Iterable, Iterator, Sequence
from pathlib import Path as FsPath
from typing import Any


def _xml_escape(value: object) -> str:
    return html.escape(str(value), quote=True)


def _normalize_attr_name(name: str) -> str:
    if name.endswith("_"):
        name = name[:-1]
    return name.replace("__", ":").replace("_", "-")


def _flatten_kwargs(kwargs: dict[str, Any]) -> dict[str, str]:
    attrs: dict[str, str] = {}
    for key, value in kwargs.items():
        if value is None:
            continue
        attrs[_normalize_attr_name(key)] = str(value)
    return attrs


class Element:
    """Minimal SVG element with child list and dict-like attributes."""

    tag: str = "g"

    def __init__(self, **kwargs: Any) -> None:
        self.attribs: dict[str, str] = _flatten_kwargs(kwargs)
        self.elements: list[Element | str] = []
        self.text_content: str | None = None

    def __setitem__(self, key: str, value: Any) -> None:
        self.attribs[_normalize_attr_name(key)] = str(value)

    def __getitem__(self, key: str) -> str:
        return self.attribs[_normalize_attr_name(key)]

    def get(self, key: str, default: str | None = None) -> str | None:
        return self.attribs.get(_normalize_attr_name(key), default)

    def add(self, element: Element | str) -> Element | str:
        self.elements.append(element)
        return element

    def __iter__(self) -> Iterator[Element | str]:
        return iter(self.elements)

    def tostring(self, pretty: bool = False, indent: int = 0) -> str:
        attrs = "".join(
            f' {name}="{_xml_escape(value)}"'
            for name, value in sorted(self.attribs.items())
        )
        pad = ("  " * indent) if pretty else ""
        nl = "\n" if pretty else ""

        children: list[str] = []
        if self.text_content is not None:
            children.append(html.escape(self.text_content))
        for child in self.elements:
            if isinstance(child, Element):
                children.append(child.tostring(pretty=pretty, indent=indent + 1))
            else:
                children.append(str(child))

        if not children:
            return f"{pad}<{self.tag}{attrs} />"

        if pretty:
            inner = nl.join(children)
            return f"{pad}<{self.tag}{attrs}>{nl}{inner}{nl}{pad}</{self.tag}>"
        return f"<{self.tag}{attrs}>{''.join(children)}</{self.tag}>"


class Group(Element):
    tag = "g"


class Defs(Element):
    tag = "defs"


class Rect(Element):
    tag = "rect"

    def __init__(
        self,
        insert: Sequence[float | int | str] | None = None,
        size: Sequence[float | int | str] | None = None,
        **kwargs: Any,
    ) -> None:
        if insert is not None:
            kwargs.setdefault("x", insert[0])
            kwargs.setdefault("y", insert[1])
        if size is not None:
            kwargs.setdefault("width", size[0])
            kwargs.setdefault("height", size[1])
        super().__init__(**kwargs)


class Circle(Element):
    tag = "circle"

    def __init__(
        self,
        center: Sequence[float | int | str] | None = None,
        r: float | int | str | None = None,
        **kwargs: Any,
    ) -> None:
        if center is not None:
            kwargs.setdefault("cx", center[0])
            kwargs.setdefault("cy", center[1])
        if r is not None:
            kwargs.setdefault("r", r)
        super().__init__(**kwargs)


class Line(Element):
    tag = "line"

    def __init__(
        self,
        start: Sequence[float | int | str] | None = None,
        end: Sequence[float | int | str] | None = None,
        **kwargs: Any,
    ) -> None:
        if start is not None:
            kwargs.setdefault("x1", start[0])
            kwargs.setdefault("y1", start[1])
        if end is not None:
            kwargs.setdefault("x2", end[0])
            kwargs.setdefault("y2", end[1])
        super().__init__(**kwargs)


class Path(Element):
    tag = "path"

    def __init__(self, d: str = "", **kwargs: Any) -> None:
        if d:
            kwargs.setdefault("d", d)
        super().__init__(**kwargs)

    def push(self, *commands: str) -> None:
        existing = self.attribs.get("d", "").rstrip()
        addition = " ".join(str(cmd) for cmd in commands)
        self.attribs["d"] = f"{existing} {addition}".strip()


class Text(Element):
    tag = "text"

    def __init__(
        self,
        text: str = "",
        insert: Sequence[float | int | str] | None = None,
        **kwargs: Any,
    ) -> None:
        if insert is not None:
            kwargs.setdefault("x", insert[0])
            kwargs.setdefault("y", insert[1])
        super().__init__(**kwargs)
        self.text_content = text


class Image(Element):
    tag = "image"

    def __init__(
        self,
        href: str | None = None,
        insert: Sequence[float | int | str] | None = None,
        size: Sequence[float | int | str] | None = None,
        **kwargs: Any,
    ) -> None:
        if href is not None:
            kwargs.setdefault("href", href)
            kwargs.setdefault("xlink:href", href)
        if insert is not None:
            kwargs.setdefault("x", insert[0])
            kwargs.setdefault("y", insert[1])
        if size is not None:
            kwargs.setdefault("width", size[0])
            kwargs.setdefault("height", size[1])
        super().__init__(**kwargs)


class Animate(Element):
    tag = "animate"


class ClipPath(Element):
    tag = "clipPath"


class Stop(Element):
    tag = "stop"


class _Gradient(Element):
    def add_stop_color(
        self,
        offset: float | int | str,
        color: str,
        opacity: float | int | str | None = None,
    ) -> Stop:
        if isinstance(offset, (int, float)) and not isinstance(offset, bool):
            if 0.0 <= float(offset) <= 1.0:
                offset_str = f"{float(offset) * 100:g}%"
            else:
                offset_str = str(offset)
        else:
            offset_str = str(offset)
        kwargs: dict[str, Any] = {
            "offset": offset_str,
            "stop_color": color,
        }
        if opacity is not None:
            kwargs["stop_opacity"] = opacity
        stop = Stop(**kwargs)
        self.add(stop)
        return stop


class LinearGradient(_Gradient):
    tag = "linearGradient"


class RadialGradient(_Gradient):
    tag = "radialGradient"


class _FilterPrimitive(Element):
    pass


class FeGaussianBlur(_FilterPrimitive):
    tag = "feGaussianBlur"


class FeColorMatrix(_FilterPrimitive):
    tag = "feColorMatrix"


class FeTurbulence(_FilterPrimitive):
    tag = "feTurbulence"


class FeComposite(_FilterPrimitive):
    tag = "feComposite"


class FeFlood(_FilterPrimitive):
    tag = "feFlood"


class FeOffset(_FilterPrimitive):
    tag = "feOffset"


class FeDisplacementMap(_FilterPrimitive):
    tag = "feDisplacementMap"


class FeMergeNode(_FilterPrimitive):
    tag = "feMergeNode"


class FeMerge(_FilterPrimitive):
    tag = "feMerge"

    def __init__(
        self,
        layernames: Iterable[str] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        if layernames is not None:
            for name in layernames:
                self.add(FeMergeNode(in_=name))


class Filter(Element):
    tag = "filter"

    def feGaussianBlur(self, **kwargs: Any) -> FeGaussianBlur:
        return self.add(FeGaussianBlur(**kwargs))  # type: ignore[return-value]

    def feColorMatrix(self, **kwargs: Any) -> FeColorMatrix:
        return self.add(FeColorMatrix(**kwargs))  # type: ignore[return-value]

    def feTurbulence(self, **kwargs: Any) -> FeTurbulence:
        return self.add(FeTurbulence(**kwargs))  # type: ignore[return-value]

    def feComposite(self, **kwargs: Any) -> FeComposite:
        return self.add(FeComposite(**kwargs))  # type: ignore[return-value]

    def feFlood(self, **kwargs: Any) -> FeFlood:
        return self.add(FeFlood(**kwargs))  # type: ignore[return-value]

    def feOffset(self, **kwargs: Any) -> FeOffset:
        return self.add(FeOffset(**kwargs))  # type: ignore[return-value]

    def feDisplacementMap(self, **kwargs: Any) -> FeDisplacementMap:
        return self.add(FeDisplacementMap(**kwargs))  # type: ignore[return-value]

    def feMerge(
        self,
        layernames: Iterable[str] | None = None,
        **kwargs: Any,
    ) -> FeMerge:
        return self.add(FeMerge(layernames=layernames, **kwargs))  # type: ignore[return-value]


class shapes:  # noqa: N801 — svgwrite-compatible namespace
    Rect = Rect
    Circle = Circle
    Line = Line


class path:  # noqa: N801 — svgwrite-compatible namespace
    Path = Path


class filters:  # noqa: N801 — svgwrite-compatible namespace
    Filter = Filter


class gradients:  # noqa: N801 — svgwrite-compatible namespace
    LinearGradient = LinearGradient
    RadialGradient = RadialGradient


class Drawing(Element):
    """Root SVG document with svgwrite-like factory helpers."""

    tag = "svg"

    def __init__(
        self,
        filename: str | FsPath | None = None,
        size: Sequence[str | float | int] | None = None,
        profile: str = "full",
        **kwargs: Any,
    ) -> None:
        del profile  # retained for call-site compatibility
        self.filename = str(filename) if filename is not None else None
        width = size[0] if size else kwargs.pop("width", None)
        height = size[1] if size else kwargs.pop("height", None)
        attrs: dict[str, Any] = {
            "xmlns": "http://www.w3.org/2000/svg",
            "xmlns:xlink": "http://www.w3.org/1999/xlink",
            **kwargs,
        }
        if width is not None:
            attrs["width"] = width
        if height is not None:
            attrs["height"] = height
        if width is not None and height is not None:
            # viewBox without units for predictable scaling
            w_num = str(width).removesuffix("px")
            h_num = str(height).removesuffix("px")
            attrs.setdefault("viewBox", f"0 0 {w_num} {h_num}")
        super().__init__(**attrs)
        self.defs = Defs()
        self.elements.append(self.defs)

    def g(self, **kwargs: Any) -> Group:
        return Group(**kwargs)

    def rect(self, **kwargs: Any) -> Rect:
        return Rect(**kwargs)

    def circle(self, **kwargs: Any) -> Circle:
        return Circle(**kwargs)

    def line(self, **kwargs: Any) -> Line:
        return Line(**kwargs)

    def path(self, **kwargs: Any) -> Path:
        return Path(**kwargs)

    def text(self, text: str = "", **kwargs: Any) -> Text:
        return Text(text=text, **kwargs)

    def image(self, **kwargs: Any) -> Image:
        return Image(**kwargs)

    def animate(self, **kwargs: Any) -> Animate:
        return Animate(**kwargs)

    def filter(self, **kwargs: Any) -> Filter:
        return Filter(**kwargs)

    def clipPath(self, **kwargs: Any) -> ClipPath:
        return ClipPath(**kwargs)

    def linearGradient(self, **kwargs: Any) -> LinearGradient:
        return LinearGradient(**kwargs)

    def radialGradient(self, **kwargs: Any) -> RadialGradient:
        return RadialGradient(**kwargs)

    def tostring(self, pretty: bool = False, indent: int = 0) -> str:
        body = super().tostring(pretty=pretty, indent=indent)
        return f'<?xml version="1.0" encoding="utf-8"?>\n{body}'

    def save(self, pretty: bool = False, filename: str | FsPath | None = None) -> None:
        target = FsPath(filename or self.filename or "drawing.svg")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(self.tostring(pretty=pretty), encoding="utf-8")
