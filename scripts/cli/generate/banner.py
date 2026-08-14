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
        from ...banner import (
            _cleanup_banner_output,
            _remove_banner_output,
            _validate_or_remove_banner_svg,
            generate_banner,
        )
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

    generated_outputs: tuple[Path, ...] = ()
    generation_complete = False
    try:
        final_banner_config = banner_settings.to_banner_config(**cli_overrides)
        logger.info(
            "Generating banner with config: "
            f"{final_banner_config.model_dump_json(indent=2)}"
        )
        light_output = Path(final_banner_config.output_path)
        dark_output = light_output.with_name(
            f"{light_output.stem}-dark{light_output.suffix}"
        )
        dark_overrides = {
            **cli_overrides,
            "dark_mode": True,
            "output_path": str(dark_output),
        }
        dark_banner_config = banner_settings.to_banner_config(**dark_overrides)

        generated_variants = (
            ("SVG banner", final_banner_config, light_output),
            ("Dark SVG banner", dark_banner_config, dark_output),
        )
        generated_outputs = (light_output, dark_output)
        # The command publishes a matched pair. Clear both exact targets before
        # either render so an old peer can never survive a partial attempt.
        for _label, _variant_config, variant_output in generated_variants:
            _remove_banner_output(variant_output)

        for _label, variant_config, variant_output in generated_variants:
            generate_banner(cfg=variant_config)
            _validate_or_remove_banner_svg(variant_output)

        for label, _variant_config, variant_output in generated_variants:
            console.print(f"[bold green]{label} generated: {variant_output}[/]")
        generation_complete = True
    except (ValidationError, OSError, ValueError, TypeError, RuntimeError) as e:
        logger.error("Banner generation failed: {e}", e=e, exc_info=True)
        console.print(f"[bold red]Error:[/bold red] Banner generation failed: {e}")
        raise typer.Exit(code=1)
    finally:
        if not generation_complete:
            for variant_output in generated_outputs:
                _cleanup_banner_output(variant_output)


# ---------------------------------------------------------------------------
# qr
# ---------------------------------------------------------------------------
