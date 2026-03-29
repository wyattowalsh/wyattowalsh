"""
timelapse.py — GIF rendering pipeline for daily-history living art
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Renders timelapse GIFs where each frame = one day of GitHub profile
history, showing the genuine evolution of the artworks over time.

Public API::

    render_timelapse(history, current_metrics, ...) -> list[Path]

Usage::

    python -m scripts.art.timelapse \\
        --metrics-path /tmp/metrics.json \\
        --history-path /tmp/history.json \\
        --owner wyattowalsh --max-frames 100 --size 400
"""

from __future__ import annotations

import os
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from ..utils import get_logger
from .daily_snapshots import build_daily_snapshots, sample_frames
from .shared import (
    seed_hash,
    validate_live_history_payload,
    validate_live_metrics_payload,
)

logger = get_logger(module=__name__)

# ---------------------------------------------------------------------------
# Frame rendering
# ---------------------------------------------------------------------------

# Style name → (module_path, function_name)
_STYLE_REGISTRY: dict[str, tuple[str, str]] = {
    "inkgarden": ("scripts.art.ink_garden", "generate"),
    "topo": ("scripts.art.topography", "generate"),
}

ALL_STYLES = list(_STYLE_REGISTRY.keys())


def _render_single_frame(
    snapshot_data: dict[str, Any],
    style: str,
    seed_hex: str,
    size: int,
    final_maturity: float,
) -> bytes | None:
    """Render one frame as PNG bytes. Runs in a worker process.

    Returns PNG bytes or None on failure.
    """
    from .animate import svg_to_png

    mod_path, func_name = _STYLE_REGISTRY[style]

    # Import the generator
    import importlib

    mod = importlib.import_module(mod_path)
    gen_fn = getattr(mod, func_name)

    data = snapshot_data["metrics_dict"]
    kwargs: dict[str, Any] = {
        "seed": seed_hex,
        "maturity": snapshot_data["maturity"],
        "timeline": False,
    }
    if style == "topo":
        kwargs["chrome_maturity"] = final_maturity
    svg_str = gen_fn(data, **kwargs)

    # SVG → PNG
    img = svg_to_png(svg_str, size, frame_id=f"{style}-d{snapshot_data['day_index']}")
    if img is None:
        return None

    # Convert PIL Image to bytes
    import io

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Frame duration computation
# ---------------------------------------------------------------------------


def _compute_frame_durations(n_frames: int, total_ms: int = 12000) -> list[int]:
    """Narrative-paced frame durations in milliseconds.

    - First 5%: 200ms (slow genesis)
    - Middle 80%: distributed evenly from remaining budget
    - Last 15%: 150ms (dramatic finish)
    - Final frame: 2000ms hold
    """
    if n_frames <= 1:
        return [2000]
    if n_frames == 2:
        return [500, 2000]

    durations: list[int] = []

    first_count = max(1, int(n_frames * 0.05))
    last_count = max(1, int(n_frames * 0.15))
    mid_count = n_frames - first_count - last_count - 1  # -1 for final hold

    first_budget = first_count * 200
    last_budget = last_count * 150
    final_hold = 2000
    mid_budget = max(total_ms - first_budget - last_budget - final_hold, mid_count * 50)
    mid_per = max(50, mid_budget // max(1, mid_count))

    for _ in range(first_count):
        durations.append(200)
    for _ in range(mid_count):
        durations.append(mid_per)
    for _ in range(last_count):
        durations.append(150)
    durations.append(final_hold)

    # Pad or trim to exact n_frames
    while len(durations) < n_frames:
        durations.insert(-1, mid_per)
    durations = durations[:n_frames]

    return durations


# ---------------------------------------------------------------------------
# GIF assembly
# ---------------------------------------------------------------------------


def _assemble_gif(
    png_frames: list[bytes],
    durations: list[int],
    output_path: Path,
    *,
    max_colors: int = 192,
    max_size_mb: float = 12.0,
) -> Path:
    """Assemble PNG frames into an optimized GIF.

    Performs progressive quality degradation if file exceeds max_size_mb.
    """
    import io

    from PIL import Image

    images = [Image.open(io.BytesIO(f)).convert("RGB") for f in png_frames]

    # Quantize
    palettized = [
        img.quantize(
            colors=max_colors,
            method=Image.Quantize.MEDIANCUT,
            dither=Image.Dither.FLOYDSTEINBERG,
        )
        for img in images
    ]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    palettized[0].save(
        str(output_path),
        save_all=True,
        append_images=palettized[1:],
        duration=durations,
        loop=0,
        optimize=True,
    )

    size_mb = output_path.stat().st_size / (1024 * 1024)
    logger.info("{}: {:.1f} MB ({} frames)", output_path.name, size_mb, len(png_frames))

    # Progressive degradation if too large
    if size_mb > max_size_mb and max_colors > 128:
        logger.warning(
            "{} exceeds {}MB, re-quantizing with fewer colors",
            output_path.name,
            max_size_mb,
        )
        palettized = [
            img.quantize(
                colors=128,
                method=Image.Quantize.MEDIANCUT,
                dither=Image.Dither.FLOYDSTEINBERG,
            )
            for img in images
        ]
        palettized[0].save(
            str(output_path),
            save_all=True,
            append_images=palettized[1:],
            duration=durations,
            loop=0,
            optimize=True,
        )
        size_mb = output_path.stat().st_size / (1024 * 1024)
        logger.info("{}: reduced to {:.1f} MB", output_path.name, size_mb)

    if size_mb > max_size_mb:
        logger.warning(
            "{} still exceeds {}MB, halving resolution", output_path.name, max_size_mb
        )
        half_images = [
            img.resize((img.width // 2, img.height // 2), Image.Resampling.LANCZOS)
            for img in images
        ]
        palettized = [
            img.quantize(
                colors=128,
                method=Image.Quantize.MEDIANCUT,
                dither=Image.Dither.FLOYDSTEINBERG,
            )
            for img in half_images
        ]
        palettized[0].save(
            str(output_path),
            save_all=True,
            append_images=palettized[1:],
            duration=durations,
            loop=0,
            optimize=True,
        )

    return output_path


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------


def render_timelapse(
    history: dict[str, Any],
    current_metrics: dict[str, Any],
    *,
    styles: list[str] | None = None,
    max_frames: int = 150,
    size: int = 400,
    output_dir: Path | None = None,
    owner: str = "",
    workers: int | None = None,
    timeout_seconds: int = 1200,
) -> list[Path]:
    """Generate timelapse GIFs for selected art styles.

    Parameters
    ----------
    history : dict
        Output of ``fetch_history.collect_history()``.
    current_metrics : dict
        Output of ``fetch_metrics.collect()``.
    styles : list[str] | None
        Art styles to render. Default: all available living-art styles.
    max_frames : int
        Maximum frames per GIF.
    size : int
        Frame size in pixels (square).
    output_dir : Path | None
        Output directory. Default: ``.github/assets/img``.
    owner : str
        GitHub username.
    workers : int | None
        Parallel workers. Default: min(cpu_count, 8).
    timeout_seconds : int
        Total timeout for all rendering.

    Returns
    -------
    list[Path]
        Paths to generated GIF files.
    """
    history = validate_live_history_payload(history)
    current_metrics = validate_live_metrics_payload(current_metrics)

    start_time = time.monotonic()
    out_dir = Path(output_dir or ".github/assets/img")
    out_dir.mkdir(parents=True, exist_ok=True)

    active_styles = styles or ALL_STYLES
    n_workers = workers or min(os.cpu_count() or 4, 8)

    # Build daily snapshots
    logger.info("Building daily snapshots for timelapse...")
    snapshots = build_daily_snapshots(history, current_metrics, owner=owner)
    if not snapshots:
        logger.warning("No snapshots generated — cannot render timelapse")
        return []

    # Sample frames
    sampled = sample_frames(snapshots, max_frames=max_frames)
    if not sampled:
        logger.warning("No frames after sampling")
        return []

    # Compute deterministic seed from final snapshot
    final_snap = sampled[-1]
    seed_hex = seed_hash(final_snap.metrics_dict)
    final_maturity = final_snap.maturity

    # Serialize snapshots for multiprocessing
    serialized_frames = [
        {
            "metrics_dict": s.metrics_dict,
            "history_dict": s.history_dict,
            "maturity": s.maturity,
            "progress": s.progress,
            "day_index": s.day_index,
        }
        for s in sampled
    ]

    durations = _compute_frame_durations(len(sampled))
    outputs: list[Path] = []

    for style in active_styles:
        if style not in _STYLE_REGISTRY:
            logger.warning("Unknown style '{}', skipping", style)
            continue

        elapsed = time.monotonic() - start_time
        if elapsed > timeout_seconds * 0.9:
            logger.warning(
                "Timeout approaching ({:.0f}s), skipping remaining styles", elapsed
            )
            break

        logger.info(
            "Rendering {} timelapse ({} frames, {}px)...", style, len(sampled), size
        )
        style_start = time.monotonic()

        # Render frames in parallel
        png_frames: list[tuple[int, bytes | None]] = []
        with ProcessPoolExecutor(max_workers=n_workers) as pool:
            futures = {
                pool.submit(
                    _render_single_frame,
                    snap_data,
                    style,
                    seed_hex,
                    size,
                    final_maturity,
                ): i
                for i, snap_data in enumerate(serialized_frames)
            }
            for fut in as_completed(futures):
                idx = futures[fut]
                try:
                    result = fut.result(timeout=60)
                    png_frames.append((idx, result))
                except Exception as exc:
                    logger.warning("Frame {} failed for {}: {}", idx, style, exc)
                    png_frames.append((idx, None))

        # Sort by index and filter failures
        png_frames.sort(key=lambda x: x[0])
        valid_frames = [f for _, f in png_frames if f is not None]
        valid_durations = [
            durations[i] for i, (_, f) in enumerate(png_frames) if f is not None
        ]

        if not valid_frames:
            logger.error("No valid frames rendered for {}", style)
            continue

        # Assemble GIF
        gif_path = out_dir / f"living-{style}.gif"
        _assemble_gif(valid_frames, valid_durations, gif_path)
        outputs.append(gif_path)

        style_elapsed = time.monotonic() - style_start
        logger.info("{} completed in {:.1f}s", style, style_elapsed)

    total_elapsed = time.monotonic() - start_time
    logger.info("Timelapse complete: {} GIFs in {:.1f}s", len(outputs), total_elapsed)
    return outputs


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """CLI entry-point for ``python -m scripts.art.timelapse``."""
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Generate living-art timelapse GIFs")
    parser.add_argument("--metrics-path", required=True, help="Path to metrics JSON")
    parser.add_argument("--history-path", required=True, help="Path to history JSON")
    parser.add_argument("--owner", default="", help="GitHub username")
    parser.add_argument(
        "--max-frames", type=int, default=150, help="Max frames per GIF"
    )
    parser.add_argument("--size", type=int, default=400, help="Frame size in px")
    parser.add_argument(
        "--only",
        default=None,
        help="Restrict to one style: inkgarden or topo",
    )
    parser.add_argument("--workers", type=int, default=None, help="Parallel workers")
    parser.add_argument("--output-dir", default=None, help="Output directory")
    args = parser.parse_args()

    try:
        metrics = json.loads(Path(args.metrics_path).read_text(encoding="utf-8"))
        history = json.loads(Path(args.history_path).read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise SystemExit(f"Failed to load timelapse inputs: {exc}") from exc

    styles = [args.only] if args.only else None
    output_dir = Path(args.output_dir) if args.output_dir else None

    try:
        outputs = render_timelapse(
            history,
            metrics,
            styles=styles,
            max_frames=args.max_frames,
            size=args.size,
            output_dir=output_dir,
            owner=args.owner,
            workers=args.workers,
        )
    except ValidationError as exc:
        raise SystemExit(f"Invalid timelapse payload: {exc}") from exc

    for p in outputs:
        size_mb = p.stat().st_size / (1024 * 1024)
        print(f"Generated: {p} ({size_mb:.1f} MB)")


if __name__ == "__main__":
    main()
