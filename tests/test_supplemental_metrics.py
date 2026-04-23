"""Tests for repo-owned supplemental metrics generation."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.supplemental_metrics import (
    XOAuth1Credentials,
    _build_x_oauth1_authorization_header,
    _fetch_authenticated_x_user,
    _fetch_latest_posts,
    _fetch_recent_tracks,
    generate_supplemental_metrics,
    validate_supplemental_metrics,
)


def _sample_metrics() -> dict:
    return {
        "contributions_calendar": [
            {"date": "2026-04-20", "count": 5, "color": "#1f6feb"},
            {"date": "2026-04-21", "count": 3, "color": "#1f6feb"},
            {"date": "2026-04-22", "count": 7, "color": "#1f6feb"},
        ],
        "languages": {"Python": 1000, "TypeScript": 500, "HTML": 200},
        "recent_merged_prs": [
            {"repo_name": "agents"},
            {"repo_name": "agents"},
            {"repo_name": "nbadb"},
        ],
        "pr_review_count": 11,
        "public_repos": 42,
        "commit_hour_distribution": {13: 4, 14: 9, 15: 2},
    }


def test_generate_supplemental_metrics_writes_required_cards_and_disables_optional(
    tmp_path: Path,
    monkeypatch,
) -> None:
    output_dir = tmp_path / "img"
    manifest_path = tmp_path / "metrics-supplemental.json"

    monkeypatch.setenv("GITHUB_TOKEN", "test-token")
    monkeypatch.delenv("SPOTIFY_CLIENT_ID", raising=False)
    monkeypatch.delenv("SPOTIFY_CLIENT_SECRET", raising=False)
    monkeypatch.delenv("SPOTIFY_REFRESH_TOKEN", raising=False)
    monkeypatch.delenv("X_API_KEY", raising=False)
    monkeypatch.delenv("X_API_KEY_SECRET", raising=False)
    monkeypatch.delenv("X_ACCESS_TOKEN", raising=False)
    monkeypatch.delenv("X_ACCESS_TOKEN_SECRET", raising=False)
    monkeypatch.setattr(
        "scripts.supplemental_metrics.collect_github_metrics",
        lambda owner, repo, token: _sample_metrics(),
    )
    monkeypatch.setattr(
        "scripts.supplemental_metrics._fetch_recent_activity",
        lambda owner, token, limit=3: [
            {"summary": "Pushed 2 commits to wyattowalsh/agents", "age": "2h ago", "created_at": "2026-04-22T12:00:00Z"},
            {"summary": "Starred wyattowalsh/nbadb", "age": "1d ago", "created_at": "2026-04-21T12:00:00Z"},
        ],
    )

    statuses = generate_supplemental_metrics(
        owner="wyattowalsh",
        repo="wyattowalsh",
        output_dir=output_dir,
        manifest_path=manifest_path,
    )

    assert (output_dir / "metrics-habits.svg").exists()
    assert (output_dir / "metrics-activity.svg").exists()
    assert not (output_dir / "metrics-music.svg").exists()
    assert not (output_dir / "metrics-posts.svg").exists()
    assert statuses["music"].enabled is False
    assert statuses["posts"].enabled is False

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["habits"]["enabled"] is True
    assert manifest["music"]["enabled"] is False


def test_validate_supplemental_metrics_rejects_missing_required_marker(
    tmp_path: Path,
) -> None:
    output_dir = tmp_path / "img"
    output_dir.mkdir()
    manifest_path = tmp_path / "metrics-supplemental.json"

    (output_dir / "metrics-habits.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg"><text x="1" y="20">Wrong title</text></svg>',
        encoding="utf-8",
    )
    manifest_path.write_text(
        json.dumps(
            {
                "habits": {
                    "asset_name": "metrics-habits",
                    "filename": "metrics-habits.svg",
                    "enabled": True,
                    "optional": False,
                    "title": "Coding habits",
                    "required_markers": ["Coding habits"],
                    "reason": "",
                }
            }
        ),
        encoding="utf-8",
    )

    errors = validate_supplemental_metrics(
        output_dir=output_dir,
        manifest_path=manifest_path,
    )

    assert errors == ["metrics-habits.svg: missing required marker 'Coding habits'"]


def test_fetch_recent_tracks_exchanges_refresh_token_and_parses_payload(monkeypatch) -> None:
    calls: list[str] = []

    def fake_request_json(url: str, **_: object) -> dict:
        calls.append(url)
        if "api/token" in url:
            return {"access_token": "spotify-access"}
        return {
            "items": [
                {
                    "played_at": "2026-04-22T12:00:00Z",
                    "track": {
                        "name": "Song A",
                        "artists": [{"name": "Artist A"}, {"name": "Artist B"}],
                    },
                }
            ]
        }

    monkeypatch.setattr("scripts.supplemental_metrics._request_json", fake_request_json)

    tracks = _fetch_recent_tracks("client-id", "client-secret", "refresh-token")

    assert len(tracks) == 1
    assert tracks[0]["name"] == "Song A"
    assert tracks[0]["artists"] == "Artist A, Artist B"
    assert any("api/token" in url for url in calls)


def test_build_x_oauth1_authorization_header_contains_signature() -> None:
    credentials = XOAuth1Credentials(
        api_key="api-key",
        api_key_secret="api-secret",
        access_token="access-token",
        access_token_secret="access-secret",
    )

    header = _build_x_oauth1_authorization_header(
        method="GET",
        url="https://api.x.com/2/users/me?user.fields=username,name",
        credentials=credentials,
        nonce="fixednonce",
        timestamp="1710000000",
    )

    assert header.startswith("OAuth ")
    assert 'oauth_consumer_key="api-key"' in header
    assert 'oauth_token="access-token"' in header
    assert 'oauth_signature_method="HMAC-SHA1"' in header
    assert 'oauth_nonce="fixednonce"' in header
    assert 'oauth_timestamp="1710000000"' in header
    assert 'oauth_signature="' in header


def test_fetch_authenticated_x_user_uses_oauth1_headers(monkeypatch) -> None:
    captured: dict[str, str] = {}

    def fake_request_json(url: str, **kwargs: object) -> dict:
        captured["url"] = url
        captured["authorization"] = str((kwargs.get("headers") or {}).get("Authorization"))
        return {"data": {"id": "12345", "username": "wyattowalsh", "name": "Wyatt"}}

    monkeypatch.setattr(
        "scripts.supplemental_metrics._request_json",
        fake_request_json,
    )

    user = _fetch_authenticated_x_user(
        XOAuth1Credentials(
            api_key="api-key",
            api_key_secret="api-secret",
            access_token="access-token",
            access_token_secret="access-secret",
        )
    )

    assert user["id"] == "12345"
    assert user["username"] == "wyattowalsh"
    assert captured["url"].endswith("/users/me?user.fields=username,name")
    assert captured["authorization"].startswith("OAuth ")


def test_fetch_latest_posts_uses_authenticated_user_and_trims_text(monkeypatch) -> None:
    monkeypatch.setattr(
        "scripts.supplemental_metrics._fetch_authenticated_x_user",
        lambda credentials: {"id": "12345", "username": "wyattowalsh", "name": "Wyatt"},
    )
    monkeypatch.setattr(
        "scripts.supplemental_metrics._x_request_json",
        lambda url, credentials: {
            "data": [
                {
                    "text": "A longish post about metrics recovery and CI validation that should still be trimmed nicely for the card output.",
                    "created_at": "2026-04-22T12:00:00Z",
                    "public_metrics": {"like_count": 3},
                }
            ]
        },
    )

    user, posts = _fetch_latest_posts(
        XOAuth1Credentials(
            api_key="api-key",
            api_key_secret="api-secret",
            access_token="access-token",
            access_token_secret="access-secret",
        )
    )

    assert user["username"] == "wyattowalsh"
    assert len(posts) == 1
    assert posts[0]["created_at"] == "2026-04-22T12:00:00Z"
    assert len(posts[0]["text"]) <= 84


def test_generate_supplemental_metrics_enables_x_posts_from_oauth1_secret_quartet(
    tmp_path: Path,
    monkeypatch,
) -> None:
    output_dir = tmp_path / "img"
    manifest_path = tmp_path / "metrics-supplemental.json"
    captured: dict[str, str] = {}

    monkeypatch.setenv("GITHUB_TOKEN", "test-token")
    monkeypatch.setenv("X_API_KEY", "api-key")
    monkeypatch.setenv("X_API_KEY_SECRET", "api-secret")
    monkeypatch.setenv("X_ACCESS_TOKEN", "access-token")
    monkeypatch.setenv("X_ACCESS_TOKEN_SECRET", "access-secret")
    monkeypatch.delenv("SPOTIFY_CLIENT_ID", raising=False)
    monkeypatch.delenv("SPOTIFY_CLIENT_SECRET", raising=False)
    monkeypatch.delenv("SPOTIFY_REFRESH_TOKEN", raising=False)
    monkeypatch.setattr(
        "scripts.supplemental_metrics.collect_github_metrics",
        lambda owner, repo, token: _sample_metrics(),
    )
    monkeypatch.setattr(
        "scripts.supplemental_metrics._fetch_recent_activity",
        lambda owner, token, limit=3: [],
    )

    def fake_fetch_latest_posts(
        credentials: XOAuth1Credentials,
        limit: int = 3,
    ) -> tuple[dict[str, str], list[dict[str, str]]]:
        captured["api_key"] = credentials.api_key
        return (
            {"id": "12345", "username": "wyattowalsh", "name": "Wyatt"},
            [{"text": "Post", "created_at": "2026-04-22T12:00:00Z", "likes": "1"}],
        )

    monkeypatch.setattr(
        "scripts.supplemental_metrics._fetch_latest_posts",
        fake_fetch_latest_posts,
    )

    statuses = generate_supplemental_metrics(
        owner="wyattowalsh",
        repo="wyattowalsh",
        output_dir=output_dir,
        manifest_path=manifest_path,
    )

    assert captured["api_key"] == "api-key"
    assert statuses["posts"].enabled is True
