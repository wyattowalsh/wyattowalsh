"""Type and behavior contracts for the lightweight SVG builder."""

from __future__ import annotations

from scripts.svg_drawing import Drawing, FeGaussianBlur, Filter


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
