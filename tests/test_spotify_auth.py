"""Tests for the Spotify refresh-token bootstrap helpers."""

from __future__ import annotations

import socket
import urllib.parse
from concurrent.futures import Future, ThreadPoolExecutor
from http.client import HTTPConnection
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from typing import cast

import pytest
from typer.testing import CliRunner

from scripts.cli import app
from scripts.cli.auth import mask_secret
from scripts.spotify_auth import (
    build_spotify_authorize_url,
    exchange_spotify_authorization_code,
    extract_spotify_refresh_token,
    mint_spotify_refresh_token,
)


@pytest.mark.parametrize(
    ("host", "response", "expected_status"),
    [
        ("127.0.0.1", "code=test-code", 200),
        ("::1", "code=test-code", 200),
        ("localhost", "error=access_denied", 400),
        ("127.0.0.1", "code=test-code&wrong_state=1", 400),
    ],
)
def test_manual_flow_uses_bound_loopback_listener(
    monkeypatch: pytest.MonkeyPatch, host: str, response: str, expected_status: int
) -> None:
    literal = "127.0.0.1" if host == "localhost" else host
    family = socket.AF_INET6 if literal == "::1" else socket.AF_INET
    with socket.socket(family, socket.SOCK_STREAM) as probe:
        probe.bind((literal, 0))
        port = probe.getsockname()[1]

    exchange_calls: list[str] = []
    read_timeouts: list[float | None] = []
    setup = BaseHTTPRequestHandler.setup

    def record_timeout(handler: BaseHTTPRequestHandler) -> None:
        setup(handler)
        read_timeouts.append(handler.connection.gettimeout())

    monkeypatch.setattr(BaseHTTPRequestHandler, "setup", record_timeout)

    def exchange(*, code: str, **_kwargs: str) -> dict[str, str]:
        exchange_calls.append(code)
        return {"refresh_token": "synthetic"}

    monkeypatch.setattr(
        "scripts.spotify_auth.exchange_spotify_authorization_code", exchange
    )
    requests: list[Future[int]] = []
    with ThreadPoolExecutor(max_workers=1) as pool:

        def deliver(url: str) -> None:
            query = urllib.parse.parse_qs(urllib.parse.urlsplit(url).query)
            redirect = urllib.parse.urlsplit(query["redirect_uri"][0])
            assert redirect.hostname == literal
            assert redirect.port == port
            state = "incorrect" if "wrong_state" in response else query["state"][0]
            # Connect now: the URL may be displayed only after the socket is bound.
            client = HTTPConnection(literal, port, timeout=5)
            client.connect()

            def callback() -> int:
                try:
                    client.request("GET", f"{redirect.path}?state={state}&{response}")
                    return client.getresponse().status
                finally:
                    client.close()

            requests.append(pool.submit(callback))

        def authorize() -> str:
            token, _ = mint_spotify_refresh_token(
                client_id="id",
                client_secret="synthetic",
                callback_host=host,
                callback_port=port,
                open_browser=False,
                manual_url_handler=deliver,
                timeout_seconds=5,
            )
            return token

        if expected_status == 200:
            assert authorize() == "synthetic"
            assert exchange_calls == ["test-code"]
        else:
            with pytest.raises(RuntimeError, match="state_mismatch|access_denied"):
                authorize()
            assert exchange_calls == []
        assert [request.result(timeout=5) for request in requests] == [expected_status]
        assert len(read_timeouts) == 1
        timeout = read_timeouts[0]
        assert timeout is not None and 0 < timeout <= 1


def test_manual_callback_times_out_and_closes_socket() -> None:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    with pytest.raises(TimeoutError, match="Timed out"):
        mint_spotify_refresh_token(
            client_id="id",
            client_secret="synthetic",
            callback_port=port,
            open_browser=False,
            timeout_seconds=0,
        )
    with socket.socket() as after:
        after.bind(("127.0.0.1", port))


def test_failed_private_token_replace_preserves_previous_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "token"
    target.write_text("old synthetic value")
    monkeypatch.setattr(
        "scripts.cli.auth.mint_spotify_refresh_token",
        lambda **_kwargs: ("new synthetic value", "unused"),
    )

    def reject_replace(source: Path, destination: Path) -> Path:
        assert destination == target
        assert source.stat().st_mode & 0o777 == 0o600
        raise OSError("simulated output failure")

    monkeypatch.setattr(Path, "replace", reject_replace)
    result = CliRunner().invoke(
        app,
        [
            "auth",
            "spotify-refresh-token",
            "--client-id",
            "id",
            "--client-secret",
            "synthetic",
            "--no-open-browser",
            "--output",
            str(target),
        ],
    )
    assert isinstance(result.exception, OSError)
    assert list(tmp_path.iterdir()) == [target]
    assert target.read_text() == "old synthetic value"


def test_build_spotify_authorize_url_includes_scope_and_show_dialog() -> None:
    url = build_spotify_authorize_url(
        client_id="client-id",
        redirect_uri="http://127.0.0.1:8888/callback",
        state="state123",
    )

    parsed = urllib.parse.urlsplit(url)
    query = urllib.parse.parse_qs(parsed.query)

    assert parsed.netloc == "accounts.spotify.com"
    assert query["client_id"] == ["client-id"]
    assert query["response_type"] == ["code"]
    assert query["scope"] == ["user-read-recently-played user-top-read"]
    assert query["show_dialog"] == ["true"]


def test_exchange_spotify_authorization_code_posts_expected_form(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_request_json(url: str, **kwargs: object) -> dict[str, str]:
        captured["url"] = url
        captured["headers"] = kwargs["headers"]
        captured["method"] = kwargs["method"]
        captured["data"] = kwargs["data"]
        return {"access_token": "access", "refresh_token": "refresh"}

    monkeypatch.setattr("scripts.spotify_auth._request_json", fake_request_json)

    payload = exchange_spotify_authorization_code(
        client_id="client-id",
        client_secret="client-secret",
        code="code-123",
        redirect_uri="http://127.0.0.1:8888/callback",
    )

    assert payload["refresh_token"] == "refresh"
    assert captured["url"] == "https://accounts.spotify.com/api/token"
    assert captured["method"] == "POST"
    raw_headers = captured["headers"]
    assert isinstance(raw_headers, dict)
    headers = cast(dict[str, str], raw_headers)
    assert str(headers.get("Authorization")).startswith("Basic ")
    data = captured["data"]
    assert isinstance(data, bytes)
    form = urllib.parse.parse_qs(data.decode("utf-8"))
    assert form["grant_type"] == ["authorization_code"]
    assert form["code"] == ["code-123"]


def test_extract_spotify_refresh_token_raises_when_missing() -> None:
    with pytest.raises(RuntimeError, match="no refresh_token"):
        extract_spotify_refresh_token({"access_token": "access"})


def test_mint_spotify_refresh_token_raises_cleanly_on_callback_failure(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "scripts.spotify_auth._wait_for_spotify_authorization_code",
        lambda **kwargs: (_ for _ in ()).throw(
            RuntimeError("Spotify authorization failed: access_denied")
        ),
    )

    with pytest.raises(RuntimeError, match="access_denied"):
        mint_spotify_refresh_token(
            client_id="client-id",
            client_secret="client-secret",
            open_browser=False,
        )


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("", "***"),
        ("short", "*****"),
        ("refresh-token-12345", "refr…2345"),
    ],
)
def test_mask_secret_never_returns_full_long_token(value: str, expected: str) -> None:
    assert mask_secret(value) == expected
    if len(value.strip()) > 8:
        assert value not in mask_secret(value)
