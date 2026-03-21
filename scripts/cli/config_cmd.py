"""Config subcommands — view, save, and generate defaults."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from ..config import DEFAULT_CONFIG_PATH, ProjectConfig, load_config, save_config
from ..utils import console, get_logger
from ._display import OutputFormat, display_config

logger = get_logger(module=__name__)


config_app = typer.Typer(
    name="config",
    help="[bold]Manage project configuration[/bold] — view, save, or generate defaults.",
    no_args_is_help=True,
    rich_markup_mode="rich",
)


@config_app.command(help="Display the current project configuration.")
def view(
    path: Annotated[
        Path | None,
        typer.Option(help="Path to config file.", rich_help_panel="Configuration"),
    ] = None,
    output_format: Annotated[
        OutputFormat,
        typer.Option(
            case_sensitive=False,
            help="Output format.",
            rich_help_panel="Display",
        ),
    ] = OutputFormat.JSON,
) -> None:
    """Load and display the project configuration file."""
    effective_path = path or DEFAULT_CONFIG_PATH
    logger.info(
        "Configuration action: view for path: {effective_path}",
        effective_path=effective_path,
    )
    try:
        config_obj = load_config(effective_path)
        console.print(
            f"[bold green]Current project configuration from "
            f"{effective_path}:[/]"
        )
        display_config(config_obj, output_format)
    except FileNotFoundError:
        logger.error(
            f"Config file not found: {effective_path}. "
            "Use 'generate-default' or 'save' to create it."
        )
        console.print(
            f"[bold red]Error:[/bold red] Config file not found: "
            f"[yellow]{effective_path}[/yellow]."
        )
        raise typer.Exit(code=1)
    except (OSError, ValueError) as e:
        logger.error(
            f"Failed to load/display config from {effective_path}: {e}"
        )
        console.print(
            f"[bold red]Error:[/bold red] Failed to load configuration: "
            f"{e}"
        )
        raise typer.Exit(code=1)


@config_app.command(help="Save the current configuration (creates default if missing).")
def save(
    path: Annotated[
        Path | None,
        typer.Option(help="Path to config file.", rich_help_panel="Configuration"),
    ] = None,
) -> None:
    """Save the current configuration, creating a default if the file is missing."""
    effective_path = path or DEFAULT_CONFIG_PATH
    logger.info(
        "Configuration action: save for path: {effective_path}",
        effective_path=effective_path,
    )
    try:
        try:
            config_to_save = load_config(effective_path)
            logger.info(
                f"Loaded existing config from {effective_path} "
                "to re-save/update."
            )
        except FileNotFoundError:
            logger.info(
                f"Config file {effective_path} not found. "
                "Creating new default config to save."
            )
            config_to_save = ProjectConfig()

        save_config(config_to_save, effective_path)
        console.print(
            f"[bold green]Configuration successfully saved to "
            f"{effective_path}[/]"
        )
        display_config(config_to_save, OutputFormat.JSON)
    except (OSError, ValueError) as e:
        logger.error(
            f"Failed to save configuration to {effective_path}: {e}"
        )
        console.print(
            f"[bold red]Error:[/bold red] Failed to save configuration: "
            f"{e}"
        )
        raise typer.Exit(code=1)


@config_app.command(name="generate-default", help="Generate a default configuration file.")
def generate_default(
    path: Annotated[
        Path | None,
        typer.Option(help="Path to write config.", rich_help_panel="Configuration"),
    ] = None,
    output_format: Annotated[
        OutputFormat,
        typer.Option(
            case_sensitive=False,
            help="Output format.",
            rich_help_panel="Display",
        ),
    ] = OutputFormat.JSON,
) -> None:
    """Generate a default configuration file, optionally overwriting an existing one."""
    effective_path = path or DEFAULT_CONFIG_PATH
    logger.info(
        "Configuration action: generate-default for path: {effective_path}",
        effective_path=effective_path,
    )
    try:
        if effective_path.exists():
            typer.confirm(
                f"Config file {effective_path} already exists. Overwrite?",
                abort=True,
            )
        default_cfg = ProjectConfig()
        save_config(default_cfg, effective_path)
        console.print(
            f"[bold green]Default configuration generated and saved to "
            f"{effective_path}[/]"
        )
        display_config(default_cfg, output_format)
    except typer.Abort:
        logger.info("Default config generation aborted by user.")
        console.print("Aborted. No changes made.")
    except OSError as e:
        logger.error(
            f"Failed to gen/save default config at {effective_path}: {e}"
        )
        console.print(
            f"[bold red]Error:[/bold red] Could not gen/save default "
            f"config: {e}"
        )
        raise typer.Exit(code=1)
