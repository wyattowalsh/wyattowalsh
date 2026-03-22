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
from .art.cosmic_genesis import render_svg as render_animated_community_svg
from .art.unfurling_spiral import generate as generate_animated_activity_art
from .art.unfurling_spiral import render_svg as render_animated_activity_svg
from .utils import get_logger

logger = get_logger(module=__name__)

# Re-export for backward compatibility
__all__ = [
    "generate_animated_community_art",
    "generate_animated_activity_art",
    "generate_compatibility_gifs",
]


def generate_compatibility_gifs(
    history: dict,
    *,
    output_dir: Path | None = None,
    duration: float = 60.0,
    frames: int = 18,
    size: int = 400,
) -> list[Path]:
    """Render GitHub-safe GIF previews for the historical animated art assets."""
    from PIL import Image

    from .art.animate import narrative_timing, svg_to_png

    out_dir = Path(output_dir or ".github/assets/img")
    out_dir.mkdir(parents=True, exist_ok=True)

    outputs: list[Path] = []
    renderers = {
        "community": render_animated_community_svg,
        "activity": render_animated_activity_svg,
    }

    for art_type, render_svg in renderers.items():
        for dark_mode in (False, True):
            suffix = "-dark" if dark_mode else ""
            frame_images: list[Image.Image] = []
            for frame_index in range(frames):
                raw_t = frame_index / max(1, frames - 1)
                progress = narrative_timing(raw_t)
                svg_markup = render_svg(
                    history,
                    dark_mode=dark_mode,
                    duration=duration,
                    snapshot_progress=progress,
                )
                image = svg_to_png(
                    svg_markup,
                    size,
                    frame_id=f"animated-{art_type}{suffix}-f{frame_index:02d}",
                )
                if image is not None:
                    frame_images.append(image)

            if not frame_images:
                logger.warning(
                    "No GIF preview frames rendered for animated-{}{}",
                    art_type,
                    suffix,
                )
                continue

            palettized = [
                image.convert("RGB").quantize(
                    colors=256,
                    method=Image.Quantize.MEDIANCUT,
                    dither=Image.Dither.FLOYDSTEINBERG,
                )
                for image in frame_images
            ]

            durations: list[int] = []
            for frame_index in range(len(palettized)):
                frac = frame_index / max(1, len(palettized) - 1)
                if frac < 0.167:
                    durations.append(480)
                elif frac < 0.667:
                    durations.append(260)
                else:
                    durations.append(360)
            durations[-1] = 1800

            out_path = out_dir / f"animated-{art_type}{suffix}.gif"
            palettized[0].save(
                out_path,
                save_all=True,
                append_images=palettized[1:],
                loop=0,
                duration=durations,
                optimize=False,
                disposal=2,
            )
            outputs.append(out_path)

    return outputs


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
