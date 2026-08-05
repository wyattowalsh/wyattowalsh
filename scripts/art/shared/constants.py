"""Canvas and living-art shared constants."""

from __future__ import annotations

# Canvas
WIDTH = 800
HEIGHT = 800
CX = WIDTH / 2
CY = HEIGHT / 2

# Language → hue mapping
LANG_HUES = {
    "Python": 215,
    "JavaScript": 48,
    "TypeScript": 220,
    "Java": 8,
    "C++": 285,
    "C": 255,
    "Go": 178,
    "Rust": 22,
    "Ruby": 348,
    "Shell": 118,
    "HTML": 28,
    "CSS": 198,
    "Jupyter Notebook": 168,
    None: 155,
}

MAX_REPOS: int = 10
"""Soft emphasis baseline for dense living-art layouts."""
