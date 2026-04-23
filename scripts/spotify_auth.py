"""Spotify authorization-code flow helpers for supplemental metrics."""

from __future__ import annotations

import base64
import json
import secrets
import ssl
import time
import urllib.parse
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Protocol

SPOTIFY_AUTHORIZE_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_RECENTLY_PLAYED_SCOPE = "user-read-recently-played"
SPOTIFY_CALLBACK_PATH = "/callback"
DEFAULT_CALLBACK_HOST = "127.0.0.1"
DEFAULT_CALLBACK_PORT = 8888
DEFAULT_TIMEOUT_SECONDS = 180


class BrowserOpener(Protocol):
    """Callable protocol for opening the system browser."""

    def __call__(self, url: str, *, new: int = 0, autoraise: bool = True) -> bool: ...


def _request_json(
    url: str,
    *,
    headers: dict[str, str] | None = None,
    method: str = "GET",
    data: bytes | None = None,
) -> Any:
    request = urllib.request.Request(
        url,
        headers=headers or {},
        method=method,
        data=data,
    )
    context = ssl.create_default_context()
    with urllib.request.urlopen(request, context=context, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def build_spotify_authorize_url(
    *,
    client_id: str,
    redirect_uri: str,
    state: str,
    scope: str = SPOTIFY_RECENTLY_PLAYED_SCOPE,
    show_dialog: bool = True,
) -> str:
    """Build the Spotify authorization URL for a loopback callback flow."""

    query = urllib.parse.urlencode(
        {
            "client_id": client_id,
            "response_type": "code",
            "redirect_uri": redirect_uri,
            "scope": scope,
            "state": state,
            "show_dialog": "true" if show_dialog else "false",
        }
    )
    return f"{SPOTIFY_AUTHORIZE_URL}?{query}"


def exchange_spotify_authorization_code(
    *,
    client_id: str,
    client_secret: str,
    code: str,
    redirect_uri: str,
) -> dict[str, Any]:
    """Exchange an authorization code for Spotify tokens."""

    auth = base64.b64encode(f"{client_id}:{client_secret}".encode("utf-8")).decode(
        "ascii"
    )
    body = urllib.parse.urlencode(
        {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
        }
    ).encode("utf-8")
    payload = _request_json(
        SPOTIFY_TOKEN_URL,
        headers={
            "Authorization": f"Basic {auth}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        method="POST",
        data=body,
    )
    if not isinstance(payload, dict):
        raise RuntimeError("Spotify authorization exchange returned a non-object payload")
    return payload


def extract_spotify_refresh_token(payload: dict[str, Any]) -> str:
    """Extract a refresh token from the Spotify token payload."""

    refresh_token = str(payload.get("refresh_token") or "").strip()
    if not refresh_token:
        raise RuntimeError(
            "Spotify authorization exchange returned no refresh_token. "
            "Re-authorize after confirming the redirect URI and consent screen."
        )
    return refresh_token


class _SpotifyCallbackServer(HTTPServer):
    allow_reuse_address = True


def _wait_for_spotify_authorization_code(
    *,
    redirect_uri: str,
    state: str,
    timeout_seconds: int,
    authorize_url: str,
    open_browser: bool,
    browser_opener: BrowserOpener,
) -> str:
    """Wait for the authorization callback on a loopback HTTP server."""

    parsed_redirect = urllib.parse.urlsplit(redirect_uri)
    callback_result: dict[str, str] = {}

    class CallbackHandler(BaseHTTPRequestHandler):
        def _finish(self, status_code: int, message: str) -> None:
            body = (
                "<!doctype html><html><head><meta charset='utf-8'><title>"
                "Spotify metrics auth</title></head><body><pre>"
                f"{message}"
                "</pre></body></html>"
            ).encode("utf-8")
            self.send_response(status_code)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:  # noqa: N802
            parsed_request = urllib.parse.urlsplit(self.path)
            if parsed_request.path != parsed_redirect.path:
                callback_result["error"] = "unexpected_callback_path"
                self._finish(404, "Unexpected callback path.")
                return

            query = urllib.parse.parse_qs(parsed_request.query)
            returned_state = (query.get("state") or [""])[0]
            if returned_state != state:
                callback_result["error"] = "state_mismatch"
                self._finish(400, "State mismatch. You can close this window.")
                return

            if "error" in query:
                callback_result["error"] = (query.get("error") or ["unknown_error"])[0]
                self._finish(
                    400,
                    "Spotify authorization returned an error. You can close this window.",
                )
                return

            code = (query.get("code") or [""])[0]
            if not code:
                callback_result["error"] = "missing_code"
                self._finish(400, "Spotify authorization returned no code.")
                return

            callback_result["code"] = code
            self._finish(200, "Spotify authorization complete. You can close this window.")

        def log_message(self, _format: str, *_args: object) -> None:
            return

    with _SpotifyCallbackServer(
        (
            parsed_redirect.hostname or DEFAULT_CALLBACK_HOST,
            parsed_redirect.port or DEFAULT_CALLBACK_PORT,
        ),
        CallbackHandler,
    ) as server:
        server.timeout = 1
        if open_browser:
            browser_opener(authorize_url, new=1, autoraise=True)
        deadline = time.monotonic() + timeout_seconds
        while "code" not in callback_result and "error" not in callback_result:
            if time.monotonic() >= deadline:
                break
            server.handle_request()

    if "error" in callback_result:
        raise RuntimeError(f"Spotify authorization failed: {callback_result['error']}")
    if "code" not in callback_result:
        raise TimeoutError(
            f"Timed out waiting for Spotify authorization callback after {timeout_seconds}s"
        )
    return callback_result["code"]


def mint_spotify_refresh_token(
    *,
    client_id: str,
    client_secret: str,
    callback_host: str = DEFAULT_CALLBACK_HOST,
    callback_port: int = DEFAULT_CALLBACK_PORT,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    open_browser: bool = True,
    browser_opener: BrowserOpener = webbrowser.open,
) -> tuple[str, str]:
    """Run the Spotify auth-code flow and return ``(refresh_token, authorize_url)``."""

    redirect_uri = f"http://{callback_host}:{callback_port}{SPOTIFY_CALLBACK_PATH}"
    state = secrets.token_urlsafe(24)
    authorize_url = build_spotify_authorize_url(
        client_id=client_id,
        redirect_uri=redirect_uri,
        state=state,
    )
    code = _wait_for_spotify_authorization_code(
        redirect_uri=redirect_uri,
        state=state,
        timeout_seconds=timeout_seconds,
        authorize_url=authorize_url,
        open_browser=open_browser,
        browser_opener=browser_opener,
    )
    payload = exchange_spotify_authorization_code(
        client_id=client_id,
        client_secret=client_secret,
        code=code,
        redirect_uri=redirect_uri,
    )
    return extract_spotify_refresh_token(payload), authorize_url
