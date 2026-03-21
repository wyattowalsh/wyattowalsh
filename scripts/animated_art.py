"""
animated_art.py — Backward-compatible shim
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The actual generators live in:
  - ``scripts.art.cosmic_genesis`` (Cosmic Genesis / community art)
  - ``scripts.art.unfurling_spiral`` (Unfurling Spiral / activity art)

This module re-exports them under the old names and provides the CLI
entry point for ``python -m scripts.animated_art``.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .art.cosmic_genesis import generate as generate_animated_community_art
from .art.unfurling_spiral import generate as generate_animated_activity_art
from .utils import get_logger

logger = get_logger(module=__name__)

# Re-export for backward compatibility
__all__ = ["generate_animated_community_art", "generate_animated_activity_art"]


def main() -> None:
    """CLI for standalone animated art generation."""
    parser = argparse.ArgumentParser(description="Generate animated historical artwork")
    parser.add_argument("--history", required=True, help="Path to history JSON")
    parser.add_argument(
        "--type",
        choices=["community", "activity", "all"],
        default="all",
        help="Which artwork to generate",
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=30.0,
        help="Animation duration in seconds",
    )
    parser.add_argument("--dark-mode", action="store_true", help="Dark mode variant")
    parser.add_argument("--output", help="Output SVG path (single type only)")
    args = parser.parse_args()

    history = json.loads(Path(args.history).read_text(encoding="utf-8"))

    if args.type in ("community", "all"):
        for dark in [True, False] if args.type == "all" else [args.dark_mode]:
            out = (
                Path(args.output) if args.output and args.type == "community" else None
            )
            p = generate_animated_community_art(
                history,
                dark_mode=dark,
                output_path=out,
                duration=args.duration,
            )
            logger.info("Wrote {path}", path=p)

    if args.type in ("activity", "all"):
        for dark in [True, False] if args.type == "all" else [args.dark_mode]:
            out = Path(args.output) if args.output and args.type == "activity" else None
            p = generate_animated_activity_art(
                history,
                dark_mode=dark,
                output_path=out,
                duration=args.duration,
            )
            logger.info("Wrote {path}", path=p)


if __name__ == "__main__":
    main()
