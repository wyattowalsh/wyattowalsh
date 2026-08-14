"""Generate art commands."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Annotated

import typer

from ._common import (
    _LIVING_ART_DEFAULT_MAX_FRAMES,
    _LIVING_ART_STYLE_HELP,
    _generate_living_art_timelapse,
    _load_project_config,
    console,
    generate_app,
    logger,
)


@generate_app.command(
    name="generative",
    help="Generate event-driven generative artwork from metrics.",
)
def generative_art(
    config_path: Annotated[
        Path | None,
        typer.Option(
            "--config-path",
            help="Project configuration file path.",
            rich_help_panel="Configuration",
        ),
    ] = None,
    output_path: Annotated[
        Path | None,
        typer.Option(
            "--output-path",
            help="Output directory for generated files.",
            rich_help_panel="Configuration",
        ),
    ] = None,
    metrics_path: Annotated[
        Path | None,
        typer.Option(
            "--metrics-path",
            help="Path to metrics JSON for generative art.",
            rich_help_panel="Generative Options",
        ),
    ] = None,
) -> None:
    """Generate event-driven generative artwork from metrics JSON."""
    _load_project_config(config_path)  # validate config exists

    try:
        from ...generative import generate_activity_art, generate_community_art
    except ImportError:
        logger.error(
            "Generative art dependencies/script components are missing. "
            "Ensure generative.py is correct and dependencies installed: "
            "uv sync --locked"
        )
        console.print("[bold red]Error:[/bold red] Generative art components missing.")
        raise typer.Exit(code=1)

    if not metrics_path or not metrics_path.exists():
        logger.error("Metrics JSON required. Use --metrics-path to specify.")
        raise typer.Exit(code=1)

    metrics = json.loads(metrics_path.read_text())

    output_dir = Path(output_path) if output_path else Path(".github/assets/img")
    output_dir.mkdir(parents=True, exist_ok=True)

    for art_type in ["community", "activity"]:
        for dark in [False, True]:
            suffix = "-dark" if dark else ""
            out = output_dir / f"generative-{art_type}{suffix}.svg"
            if art_type == "community":
                generate_community_art(metrics, dark_mode=dark, output_path=out)
            else:
                generate_activity_art(metrics, dark_mode=dark, output_path=out)
            console.print(f"[bold green]Generated: {out}[/]")


# ---------------------------------------------------------------------------
# living-art
# ---------------------------------------------------------------------------


@generate_app.command(
    name="animated",
    help="Generate CSS-animated SVG living art seeded from commit history.",
)
def animated(
    config_path: Annotated[
        Path | None,
        typer.Option(
            "--config-path",
            help="Project configuration file path.",
            rich_help_panel="Configuration",
        ),
    ] = None,
    profile: Annotated[
        str,
        typer.Option(
            "--profile",
            help="GitHub username (used for labeling).",
            rich_help_panel="Animated Art Options",
        ),
    ] = "wyattowalsh",
    output_path: Annotated[
        Path | None,
        typer.Option(
            "--output-path",
            help="Legacy animated exports always write into .github/assets/img.",
            rich_help_panel="Configuration",
        ),
    ] = None,
    metrics_path: Annotated[
        Path | None,
        typer.Option(
            "--metrics-path",
            help="Path to metrics JSON from fetch_metrics.",
            rich_help_panel="Animated Art Options",
        ),
    ] = None,
    history_path: Annotated[
        Path | None,
        typer.Option(
            "--history-path",
            help="Path to history JSON from fetch_history.",
            rich_help_panel="Animated Art Options",
        ),
    ] = None,
    frames: Annotated[
        int,
        typer.Option(
            "--frames",
            min=2,
            help="Frame count for the growth animation.",
            rich_help_panel="Animated Art Options",
        ),
    ] = 7,
    size: Annotated[
        int,
        typer.Option(
            "--size",
            min=64,
            help="Frame size in pixels (square).",
            rich_help_panel="Animated Art Options",
        ),
    ] = 400,
    only: Annotated[
        str | None,
        typer.Option(
            "--only",
            help=f"Restrict to one style: {_LIVING_ART_STYLE_HELP}.",
            rich_help_panel="Animated Art Options",
        ),
    ] = None,
    svg: Annotated[
        bool,
        typer.Option(
            "--svg/--gif",
            help="Emit animated SVG stacks (default) or legacy GIF growth loops.",
            rich_help_panel="Animated Art Options",
        ),
    ] = True,
) -> None:
    """Generate legacy animated living-art outputs via the compatibility module."""
    _load_project_config(config_path)

    from ...art import animate as animate_module

    if output_path is not None:
        logger.info(
            "Animated art ignores --output-path and writes to .github/assets/img: {}",
            output_path,
        )

    argv = [
        "animate",
        "--profile",
        profile,
        "--frames",
        str(frames),
        "--size",
        str(size),
    ]
    if only is not None:
        argv.extend(["--only", only])
    if svg:
        argv.append("--svg")
    if metrics_path is not None:
        argv.extend(["--metrics-path", str(metrics_path)])
    if history_path is not None:
        argv.extend(["--history-path", str(history_path)])

    repo_root = Path(__file__).resolve().parents[3]
    previous_cwd = Path.cwd()
    previous_argv = sys.argv[:]
    try:
        os.chdir(repo_root)
        sys.argv = argv
        animate_module.main()
    finally:
        sys.argv = previous_argv
        os.chdir(previous_cwd)


@generate_app.command(
    name="living-art",
    help="Generate living-art timelapse GIFs.",
)
def living_art(
    config_path: Annotated[
        Path | None,
        typer.Option(
            "--config-path",
            help="Project configuration file path.",
            rich_help_panel="Configuration",
        ),
    ] = None,
    profile: Annotated[
        str,
        typer.Option(
            "--profile",
            help="GitHub username (used for labeling).",
            rich_help_panel="Living Art Options",
        ),
    ] = "wyattowalsh",
    max_frames: Annotated[
        int,
        typer.Option(
            "--max-frames",
            "--frames",
            min=5,
            help="Maximum frames per GIF (default 120 targets ~30s playback).",
            rich_help_panel="Living Art Options",
        ),
    ] = _LIVING_ART_DEFAULT_MAX_FRAMES,
    size: Annotated[
        int,
        typer.Option(
            "--size",
            min=64,
            help="Frame size in pixels (square).",
            rich_help_panel="Living Art Options",
        ),
    ] = 400,
    only: Annotated[
        str | None,
        typer.Option(
            "--only",
            help=f"Restrict to one style: {_LIVING_ART_STYLE_HELP}.",
            rich_help_panel="Living Art Options",
        ),
    ] = None,
    metrics_path: Annotated[
        Path | None,
        typer.Option(
            "--metrics-path",
            help="Path to metrics JSON from fetch_metrics.",
            rich_help_panel="Living Art Options",
        ),
    ] = None,
    history_path: Annotated[
        Path | None,
        typer.Option(
            "--history-path",
            help="Path to history JSON from fetch_history.",
            rich_help_panel="Living Art Options",
        ),
    ] = None,
    workers: Annotated[
        int,
        typer.Option(
            "--workers",
            min=1,
            help="Parallel rendering workers.",
            rich_help_panel="Living Art Options",
        ),
    ] = 4,
    output_dir: Annotated[
        Path,
        typer.Option(
            "--output-dir",
            help="Directory for generated living-art GIFs.",
            rich_help_panel="Living Art Options",
        ),
    ] = Path(".github/assets/img"),
) -> None:
    """Generate canonical living-art timelapse GIFs."""
    _load_project_config(config_path)  # validate config exists
    _generate_living_art_timelapse(
        profile=profile,
        metrics_path=metrics_path,
        history_path=history_path,
        only=only,
        max_frames=max_frames,
        size=size,
        workers=workers,
        output_dir=output_dir,
    )


# ---------------------------------------------------------------------------
# timelapse
# ---------------------------------------------------------------------------


@generate_app.command(
    name="timelapse",
    help=(
        "Generate living-art timelapse GIFs where each frame = one day of "
        "profile history."
    ),
)
def timelapse(
    config_path: Annotated[
        Path | None,
        typer.Option(
            "--config-path",
            help="Project configuration file path.",
            rich_help_panel="Configuration",
        ),
    ] = None,
    profile: Annotated[
        str,
        typer.Option(
            "--profile",
            help="GitHub username (used for labeling).",
            rich_help_panel="Timelapse Options",
        ),
    ] = "wyattowalsh",
    metrics_path: Annotated[
        Path | None,
        typer.Option(
            "--metrics-path",
            help="Path to metrics JSON from fetch_metrics.",
            rich_help_panel="Timelapse Options",
        ),
    ] = None,
    history_path: Annotated[
        Path | None,
        typer.Option(
            "--history-path",
            help="Path to history JSON from fetch_history.",
            rich_help_panel="Timelapse Options",
        ),
    ] = None,
    max_frames: Annotated[
        int,
        typer.Option(
            "--max-frames",
            "--frames",
            min=5,
            help="Maximum frames per GIF (default 120 targets ~30s playback).",
            rich_help_panel="Timelapse Options",
        ),
    ] = _LIVING_ART_DEFAULT_MAX_FRAMES,
    size: Annotated[
        int,
        typer.Option(
            "--size",
            min=64,
            help="Frame size in pixels (square).",
            rich_help_panel="Timelapse Options",
        ),
    ] = 400,
    only: Annotated[
        str | None,
        typer.Option(
            "--only",
            help=f"Restrict to one style: {_LIVING_ART_STYLE_HELP}.",
            rich_help_panel="Timelapse Options",
        ),
    ] = None,
    workers: Annotated[
        int,
        typer.Option(
            "--workers",
            min=1,
            help="Parallel rendering workers.",
            rich_help_panel="Timelapse Options",
        ),
    ] = 4,
    output_dir: Annotated[
        Path,
        typer.Option(
            "--output-dir",
            help="Directory for generated living-art GIFs.",
            rich_help_panel="Timelapse Options",
        ),
    ] = Path(".github/assets/img"),
) -> None:
    """Generate timelapse GIFs showing day-by-day profile evolution."""
    _load_project_config(config_path)  # validate config exists
    _generate_living_art_timelapse(
        profile=profile,
        metrics_path=metrics_path,
        history_path=history_path,
        only=only,
        max_frames=max_frames,
        size=size,
        workers=workers,
        output_dir=output_dir,
    )


# ---------------------------------------------------------------------------
# skills
# ---------------------------------------------------------------------------
