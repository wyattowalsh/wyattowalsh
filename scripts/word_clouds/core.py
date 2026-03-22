"""Core data structures, font constants, and font resolution for word clouds."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass


@dataclass(slots=True)
class PlacedWord:
    """A word that has been assigned a position in the SVG canvas."""

    text: str
    x: float
    y: float
    font_size: float
    rotation: float  # degrees
    color: str  # CSS color string
    font_weight: int = 400
    font_family: str = "Inter, 'Segoe UI', system-ui, -apple-system, sans-serif"
    opacity: float = 1.0


@dataclass(slots=True)
class BBox:
    """Axis-aligned bounding box."""

    x: float
    y: float
    w: float
    h: float

    @property
    def x2(self) -> float:
        return self.x + self.w

    @property
    def y2(self) -> float:
        return self.y + self.h

    def intersects(self, other: BBox) -> bool:
        return not (
            self.x2 <= other.x
            or other.x2 <= self.x
            or self.y2 <= other.y
            or other.y2 <= self.y
        )

    def corners(self) -> list[tuple[float, float]]:
        return [
            (self.x, self.y),
            (self.x2, self.y),
            (self.x, self.y2),
            (self.x2, self.y2),
        ]


FONT_STACK = "Inter, 'Segoe UI', system-ui, -apple-system, sans-serif"
FONT_STACK_MONO = "'JetBrains Mono', 'Fira Code', 'SF Mono', 'Cascadia Code', monospace"


def resolve_preferred_wordcloud_font_path() -> str | None:
    """Try to find Monaspace Neon or Montserrat; return path or None."""
    for font_name in ("MonaspaceNeon", "Monaspace Neon", "Montserrat"):
        try:
            result = subprocess.run(
                ["fc-list", f":family={font_name}", "file"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0 and result.stdout.strip():
                path = result.stdout.strip().split(":")[0].strip()
                if path:
                    return path
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue
    return None
