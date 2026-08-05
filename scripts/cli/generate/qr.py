"""Generate qr commands."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from ._common import _load_project_config, console, generate_app, logger


@generate_app.command(help="Generate artistic vCard QR code.")
def qr(
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
    qr_error_correction: Annotated[
        str | None,
        typer.Option(
            "--qr-error-correction",
            help="QR error correction (L,M,Q,H).",
            case_sensitive=False,
            rich_help_panel="QR Options",
        ),
    ] = None,
    qr_scale: Annotated[
        int | None,
        typer.Option(
            "--qr-scale",
            help="QR code scale factor.",
            rich_help_panel="QR Options",
        ),
    ] = None,
    qr_background_path: Annotated[
        Path | None,
        typer.Option(
            "--qr-background-path",
            help="QR background SVG path.",
            rich_help_panel="QR Options",
        ),
    ] = None,
) -> None:
    """Generate an artistic vCard QR code."""
    from ...config import QRCodeSettings as ConfigQRCodeSettings  # lazy import

    proj_config = _load_project_config(config_path)

    try:
        from ...qr import QRCodeGenerator
    except ImportError:
        logger.error(
            "QR code dependencies/script components are missing. "
            "Ensure qr.py is correct and dependencies installed: "
            "uv sync --locked --extra qr"
        )
        console.print("[bold red]Error:[/bold red] QR code components missing.")
        raise typer.Exit(code=1)

    cfg_qr_settings_defaults = ConfigQRCodeSettings()
    qr_settings_data = cfg_qr_settings_defaults.model_dump()

    if proj_config.qr_code_settings and isinstance(
        proj_config.qr_code_settings, ConfigQRCodeSettings
    ):
        qr_settings_data.update(
            proj_config.qr_code_settings.model_dump(exclude_unset=True)
        )
    elif proj_config.qr_code_settings:
        logger.warning(
            f"proj_config.qr_code_settings is of unexpected type: "
            f"{type(proj_config.qr_code_settings)}. Expected ConfigQRCodeSettings. "
            "Using defaults."
        )

    cfg_vcard_data = proj_config.v_card_data

    if cfg_vcard_data is None:  # Should not happen with default_factory
        logger.error("Critical: VCardData is None despite default_factory.")
        raise typer.Exit(code=1)

    default_bg_path_str = qr_background_path or qr_settings_data.get(
        "default_background_path"
    )
    default_output_dir_str = (
        output_path.parent
        if output_path
        else qr_settings_data.get("output_dir") or ".github/assets/img"
    )

    final_output_filename = (
        output_path.name
        if output_path
        else qr_settings_data.get("output_filename") or "qr.png"
    )

    try:
        qr_gen = QRCodeGenerator(
            default_background_path=(
                Path(default_bg_path_str) if default_bg_path_str else None
            ),
            default_output_dir=Path(default_output_dir_str),
            default_scale=(
                qr_scale
                if qr_scale is not None
                else int(qr_settings_data.get("default_scale", 25))
            ),
        )

        error_correction = (
            qr_error_correction
            if qr_error_correction is not None
            else qr_settings_data.get("error_correction", "H")
        )
        vcard_display_name = (
            getattr(cfg_vcard_data, "displayname", "DefaultVCard")
            if cfg_vcard_data
            else "DefaultVCard"
        )

        logger.info(
            f"Generating QR for: {vcard_display_name}, "
            f"Output: "
            f"{{Path(default_output_dir_str) / final_output_filename}}, "
            f"Background: {default_bg_path_str}"
        )
        logger.debug(
            f"  QR Settings: scale="
            f"{qr_scale or qr_settings_data.get('default_scale', 25)}, "
            f"error_correction={error_correction}"
        )
        logger.debug("VCard Details: {cfg_vcard_data}", cfg_vcard_data=cfg_vcard_data)

        generated_qr_path = qr_gen.generate_artistic_vcard_qr(
            vcard_details=cfg_vcard_data,
            output_filename=final_output_filename,
            error_correction=error_correction,
        )
        console.print(f"[bold green]QR code generated: {generated_qr_path}[/]")
    except FileNotFoundError as fnf_error:
        logger.error(
            f"QR generation error (file not found): {fnf_error}",
            exc_info=True,
        )
        console.print(f"[bold red]File Not Found Error:[/bold red] {fnf_error}")
        raise typer.Exit(code=1)
    except ValueError as val_error:
        logger.error(
            f"QR generation error (value error): {val_error}",
            exc_info=True,
        )
        console.print(f"[bold red]Value Error:[/bold red] {val_error}")
        raise typer.Exit(code=1)
    except (OSError, AttributeError, TypeError, RuntimeError) as e:
        logger.error("QR generation failed: {e}", e=e, exc_info=True)
        console.print(f"[bold red]Error:[/bold red] QR generation failed: {e}")
        raise typer.Exit(code=1)


# ---------------------------------------------------------------------------
# word-cloud helpers
# ---------------------------------------------------------------------------
