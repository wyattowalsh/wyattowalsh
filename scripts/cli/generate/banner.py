"""Generate banner commands."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from ._common import _load_project_config, console, generate_app, logger


@generate_app.command(help="Generate SVG profile banner (light + dark variants).")
def banner(
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
            help="Output path for generated file.",
            rich_help_panel="Configuration",
        ),
    ] = None,
    title: Annotated[
        str | None,
        typer.Option(
            "--title",
            help="Banner title.",
            rich_help_panel="Banner Options",
        ),
    ] = None,
    subtitle: Annotated[
        str | None,
        typer.Option(
            "--subtitle",
            help="Banner subtitle.",
            rich_help_panel="Banner Options",
        ),
    ] = None,
    width: Annotated[
        int | None,
        typer.Option(
            "--width",
            help="Banner width (px).",
            rich_help_panel="Banner Options",
        ),
    ] = None,
    height: Annotated[
        int | None,
        typer.Option(
            "--height",
            help="Banner height (px).",
            rich_help_panel="Banner Options",
        ),
    ] = None,
    optimize_banner: Annotated[
        bool | None,
        typer.Option(
            "--optimize-banner/--no-optimize-banner",
            help="Optimize banner with SVGO.",
            rich_help_panel="Banner Options",
        ),
    ] = None,
    seed: Annotated[
        int | None,
        typer.Option(
            "--seed",
            help="Random seed for deterministic banner output.",
            rich_help_panel="Banner Options",
        ),
    ] = None,
) -> None:
    """Generate SVG profile banner with light and dark variants."""
    from ...config import BannerSettings as ConfigBannerSettings  # lazy import

    proj_config = _load_project_config(config_path)

    try:
        from ...banner import generate_banner
    except ImportError:
        logger.error(
            "Banner dependencies/script components are missing. "
            "Ensure banner.py is correct and dependencies installed: "
            "uv sync --locked"
        )
        console.print("[bold red]Error:[/bold red] Banner components missing.")
        raise typer.Exit(code=1)

    banner_settings = proj_config.banner_settings or ConfigBannerSettings()
    cli_overrides = {
        "output_path": str(output_path) if output_path else None,
        "title": title,
        "subtitle": subtitle,
        "width": width,
        "height": height,
        "optimize_with_svgo": optimize_banner,
        "seed": seed,
    }

    from pydantic import ValidationError  # lazy import

    try:
        final_banner_config = banner_settings.to_banner_config(**cli_overrides)
        logger.info(
            "Generating banner with config: "
            f"{final_banner_config.model_dump_json(indent=2)}"
        )
        generate_banner(cfg=final_banner_config)
        console.print(
            f"[bold green]SVG banner generated: {final_banner_config.output_path}[/]"
        )
        # Generate dark variant — failure does not affect the primary banner.
        # Merge overrides into one dict so output_path is not passed twice
        # (cli_overrides already may include output_path).
        try:
            dark_output = Path(final_banner_config.output_path)
            dark_path = str(
                dark_output.parent / f"{dark_output.stem}-dark{dark_output.suffix}"
            )
            dark_overrides = {
                **cli_overrides,
                "dark_mode": True,
                "output_path": dark_path,
            }
            dark_banner_config = banner_settings.to_banner_config(**dark_overrides)
            generate_banner(cfg=dark_banner_config)
            console.print(
                "[bold green]Dark SVG banner generated: "
                f"{dark_banner_config.output_path}[/]"
            )
        except (
            ValidationError,
            OSError,
            ValueError,
            TypeError,
            RuntimeError,
        ) as dark_err:
            logger.warning(
                f"Dark banner generation failed (light banner succeeded): {dark_err}",
                exc_info=True,
            )
            console.print(
                "[yellow]Dark banner generation failed — light banner was saved.[/]"
            )
    except (ValidationError, OSError, ValueError, TypeError, RuntimeError) as e:
        logger.error("Banner generation failed: {e}", e=e, exc_info=True)
        console.print(f"[bold red]Error:[/bold red] Banner generation failed: {e}")
        raise typer.Exit(code=1)


# ---------------------------------------------------------------------------
# qr
# ---------------------------------------------------------------------------
