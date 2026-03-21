"""Root Typer application with version callback and sub-app registration."""

from __future__ import annotations

import importlib.metadata
from typing import Annotated

import typer

from .config_cmd import config_app
from .dev import dev_app
from .generate import generate_app
from .settings_cmd import show_settings

app = typer.Typer(
    name="readme",
    help=(
        "[bold]readme[/bold] — CLI for profile asset generation, "
        "project configuration, and development tools."
    ),
    no_args_is_help=True,
    rich_markup_mode="rich",
    add_completion=False,
)


def _version_callback(value: bool) -> None:
    if value:
        try:
            version = importlib.metadata.version("readme")
        except importlib.metadata.PackageNotFoundError:
            version = "0.0.0-dev"
        typer.echo(f"readme {version}")
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        bool | None,
        typer.Option(
            "--version",
            help="Show version and exit.",
            callback=_version_callback,
            is_eager=True,
            expose_value=False,
        ),
    ] = None,
) -> None:
    """CLI for readme project utilities, generation, and management."""


# -- Register sub-apps -------------------------------------------------------
app.add_typer(generate_app)
app.add_typer(config_app)
app.add_typer(dev_app)

# -- Register top-level commands ----------------------------------------------
app.command(
    name="show-settings",
    help="Display current global application settings from environment/dotenv.",
)(show_settings)
