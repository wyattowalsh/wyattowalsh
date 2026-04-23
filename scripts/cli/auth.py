"""Auth helpers for one-time third-party setup flows."""

from __future__ import annotations

from typing import Annotated

import typer

from ..spotify_auth import (
    DEFAULT_CALLBACK_HOST,
    DEFAULT_CALLBACK_PORT,
    DEFAULT_TIMEOUT_SECONDS,
    mint_spotify_refresh_token,
)

auth_app = typer.Typer(
    name="auth",
    help="One-time auth helpers for external provider credentials.",
    no_args_is_help=True,
    add_completion=False,
)


@auth_app.command(
    name="spotify-refresh-token",
    help="Mint a Spotify refresh token for the supplemental music metrics card.",
)
def spotify_refresh_token(
    client_id: Annotated[
        str | None,
        typer.Option(
            "--client-id",
            envvar="SPOTIFY_CLIENT_ID",
            help="Spotify client ID. Falls back to SPOTIFY_CLIENT_ID.",
        ),
    ] = None,
    client_secret: Annotated[
        str | None,
        typer.Option(
            "--client-secret",
            envvar="SPOTIFY_CLIENT_SECRET",
            help="Spotify client secret. Falls back to SPOTIFY_CLIENT_SECRET.",
        ),
    ] = None,
    callback_host: Annotated[
        str,
        typer.Option(
            "--callback-host",
            help="Loopback callback host. Must match a Spotify redirect URI allowlist entry.",
        ),
    ] = DEFAULT_CALLBACK_HOST,
    callback_port: Annotated[
        int,
        typer.Option(
            "--callback-port",
            min=1,
            max=65535,
            help="Loopback callback port. Must match a Spotify redirect URI allowlist entry.",
        ),
    ] = DEFAULT_CALLBACK_PORT,
    timeout_seconds: Annotated[
        int,
        typer.Option(
            "--timeout-seconds",
            min=30,
            help="How long to wait for the Spotify callback before failing.",
        ),
    ] = DEFAULT_TIMEOUT_SECONDS,
    open_browser: Annotated[
        bool,
        typer.Option(
            "--open-browser/--no-open-browser",
            help="Open the authorize URL in the system browser automatically.",
        ),
    ] = True,
) -> None:
    """Run the Spotify authorization-code flow and print a refresh token."""

    resolved_client_id = (client_id or "").strip()
    resolved_client_secret = (client_secret or "").strip()
    if not resolved_client_id or not resolved_client_secret:
        raise typer.BadParameter(
            "Spotify client credentials are required via --client-id/--client-secret "
            "or SPOTIFY_CLIENT_ID/SPOTIFY_CLIENT_SECRET."
        )

    refresh_token, authorize_url = mint_spotify_refresh_token(
        client_id=resolved_client_id,
        client_secret=resolved_client_secret,
        callback_host=callback_host,
        callback_port=callback_port,
        timeout_seconds=timeout_seconds,
        open_browser=open_browser,
    )

    if not open_browser:
        typer.echo("Open this URL in your browser to authorize Spotify:")
        typer.echo(authorize_url)
    typer.echo("Spotify refresh token:")
    typer.echo(refresh_token)
    typer.echo("Store this value as the SPOTIFY_REFRESH_TOKEN GitHub Actions secret.")
