"""Show-settings command — displays app-level environment settings."""

from __future__ import annotations

from typing import Annotated

import typer

from ..config import Settings as AppSettings
from ..utils import console, get_logger
from ._display import OutputFormat, display_config

logger = get_logger(module=__name__)

# Module-level aliases so tests can patch scripts.cli.settings_cmd.Settings
Settings = AppSettings


def show_settings(
    output_format: Annotated[
        OutputFormat,
        typer.Option(case_sensitive=False, help="Output format (json/yaml)."),
    ] = OutputFormat.JSON,
) -> None:
    """Display current application settings from environment/dotenv."""
    from pydantic import ValidationError  # lazy import

    try:
        current_app_settings = Settings()
        console.print("[bold]Current Application Settings:[/bold]")
        display_config(current_app_settings, output_format)
    except ValidationError as e:
        logger.error("Settings validation error: {e}", e=e)
        raise typer.Exit(code=1)
    except Exception as e:
        logger.error("An unexpected error occurred: {e}", e=e)
        logger.exception("Traceback:")
        raise typer.Exit(code=1)
