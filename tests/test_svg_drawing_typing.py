"""Type and behavior contracts for the lightweight SVG builder."""

from __future__ import annotations

from xml.etree import ElementTree

from scripts.svg_drawing import Drawing, FeGaussianBlur, Filter


def test_empty_size_uses_explicit_dimensions() -> None:
    drawing = Drawing(size=(), width=80, height=40)
    root = ElementTree.fromstring(drawing.tostring())
    assert (root.get("width"), root.get("height"), root.get("viewBox")) == (
        "80", "40", "0 0 80 40",
    )


def test_add_preserves_concrete_element_type() -> None:
    drawing = Drawing()

    glow_filter = drawing.defs.add(drawing.filter(id="glow"))
    assert isinstance(glow_filter, Filter)

    blur = glow_filter.feGaussianBlur(
        in_="SourceGraphic",
        stdDeviation="2",
        result="blur",
    )
    assert isinstance(blur, FeGaussianBlur)

    assert glow_filter is drawing.defs.elements[-1]
    assert blur is glow_filter.elements[-1]
