"""Shared soft-fail SVG optimization via the SVGO CLI."""

from __future__ import annotations

import subprocess
from pathlib import Path

from .utils import get_logger

logger = get_logger(module=__name__)


def optimize_with_svgo(svg_path: str | Path) -> None:
    """Optimize an SVG file with the ``svgo`` CLI when available.

    Missing binary or non-zero exit never raises: generation must continue.
    """
    path = str(svg_path)
    try:
        subprocess.run(["svgo", path], check=True, capture_output=True, text=True)
        logger.info("SVG optimized with SVGO: {svg_path}", svg_path=path)
    except subprocess.CalledProcessError as e:
        logger.warning(
            "SVGO optimization failed with error: {stderr}",
            stderr=e.stderr,
        )
    except FileNotFoundError:
        logger.warning("SVGO command not found. Skipping SVG optimization.")
