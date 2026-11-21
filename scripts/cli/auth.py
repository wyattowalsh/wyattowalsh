"""Auth helpers for one-time third-party setup flows."""

from __future__ import annotations

from pathlib import Path
from tempfile import NamedTemporaryFile
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

DEFAULT_REFRESH_TOKEN_OUTPUT = Path("spotify_refresh_token.txt")


def mask_secret(value: str, *, visible_prefix: int = 4, visible_suffix: int = 4) -> str:
    """Return a masked representation safe for console/log output."""
    secret = value.strip()
    if not secret:
        return "***"
    if len(secret) <= visible_prefix + visible_suffix:
        return "*" * len(secret)
    return f"{secret[:visible_prefix]}…{secret[-visible_suffix:]}"


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
            help="Loopback callback host. Must match a Spotify redirect URI allowlist entry.",  # noqa: E501
        ),
    ] = DEFAULT_CALLBACK_HOST,
    callback_port: Annotated[
        int,
        typer.Option(
            "--callback-port",
            min=1,
            max=65535,
            help="Loopback callback port. Must match a Spotify redirect URI allowlist entry.",  # noqa: E501
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
    output_path: Annotated[
        Path,
        typer.Option(
            "--output",
            "-o",
            help="Write the refresh token to this file (never printed to the console).",
            writable=True,
        ),
    ] = DEFAULT_REFRESH_TOKEN_OUTPUT,
) -> None:
    """Run the Spotify authorization-code flow and write the refresh token to a file."""

    resolved_client_id = (client_id or "").strip()
    resolved_client_secret = (client_secret or "").strip()
    if not resolved_client_id or not resolved_client_secret:
        raise typer.BadParameter(
            "Spotify client credentials are required via --client-id/--client-secret "
            "or SPOTIFY_CLIENT_ID/SPOTIFY_CLIENT_SECRET."
        )

    def show_authorization_url(url: str) -> None:
        typer.echo("Open this URL in your browser to authorize Spotify:")
        typer.echo(url)

    refresh_token, _ = mint_spotify_refresh_token(
        client_id=resolved_client_id,
        client_secret=resolved_client_secret,
        callback_host=callback_host,
        callback_port=callback_port,
        timeout_seconds=timeout_seconds,
        open_browser=open_browser,
        manual_url_handler=show_authorization_url,
    )

    destination = output_path.expanduser()
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=destination.parent, delete=False
    )
    temporary_path = Path(temporary.name)
    try:
        with temporary:
            temporary.write(f"{refresh_token}\n")
        # The temporary starts at 0600 and shares the destination filesystem.
        temporary_path.replace(destination)
    finally:
        temporary_path.unlink(missing_ok=True)

    typer.echo(f"Spotify refresh token written to {destination}")
    typer.echo(f"Masked preview: {mask_secret(refresh_token)}")
    typer.echo(
        "Store the file contents as the SPOTIFY_REFRESH_TOKEN GitHub Actions secret, "
        "then delete the local file."
    )
