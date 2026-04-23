"""Tests for the Spotify refresh-token bootstrap helpers."""

from __future__ import annotations

import urllib.parse

import pytest

from scripts.spotify_auth import (
    build_spotify_authorize_url,
    exchange_spotify_authorization_code,
    extract_spotify_refresh_token,
    mint_spotify_refresh_token,
)


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
    assert query["scope"] == ["user-read-recently-played"]
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
    assert str((captured["headers"] or {}).get("Authorization")).startswith("Basic ")
    form = urllib.parse.parse_qs((captured["data"] or b"").decode("utf-8"))
    assert form["grant_type"] == ["authorization_code"]
    assert form["code"] == ["code-123"]


def test_extract_spotify_refresh_token_raises_when_missing() -> None:
    with pytest.raises(RuntimeError, match="no refresh_token"):
        extract_spotify_refresh_token({"access_token": "access"})


def test_mint_spotify_refresh_token_raises_cleanly_on_callback_failure(monkeypatch) -> None:
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
