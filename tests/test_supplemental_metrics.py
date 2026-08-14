"""Tests for repo-owned supplemental metrics generation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import cast

import pytest

from scripts.supplemental_metrics import (
    XOAuth1Credentials,
    _build_x_oauth1_authorization_header,
    _fetch_authenticated_x_user,
    _fetch_image_data_uri,
    _fetch_latest_posts,
    _fetch_recent_tracks,
    _render_habits_svg,
    _render_music_svg,
    generate_supplemental_metrics,
    validate_supplemental_metrics,
)


def _sample_metrics() -> dict[str, object]:
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


def _forbid_activity_writer(*_args: object, **_kwargs: object) -> list[dict[str, str]]:
    raise AssertionError("generate must not fetch or write metrics-activity")


def _well_formed_svg(path: Path) -> str | None:
    if not path.is_file():
        return None
    text = path.read_text(encoding="utf-8")
    if "<<<<<<<" in text or ">>>>>>>" in text or "=======" in text:
        return None
    return text


def _assert_habits_is_designed(svg: str) -> None:
    assert "habits-streaks" in svg
    assert "habits-focus" in svg
    assert "habits-peak" in svg
    assert "habits-cadence" in svg
    assert "Peak hour" in svg
    assert "Focus" in svg
    assert "Coding habits" in svg
    assert "30-day activity" not in svg
    assert "langs:" not in svg
    assert "JetBrains MPS" not in svg
    assert "card-line" not in svg
    assert "uppercase; }}" not in svg


def _assert_music_is_designed(svg: str) -> None:
    assert "music-hero" in svg
    assert "Recently played" in svg
    assert "Spotify" in svg
    assert "card-line" not in svg
    assert "uppercase; }}" not in svg
    assert "Utta Wanka" not in svg


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
        _forbid_activity_writer,
    )
    monkeypatch.setattr(
        "scripts.supplemental_metrics._render_activity_card",
        _forbid_activity_writer,
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "metrics-activity.svg").write_text("stale", encoding="utf-8")

    statuses = generate_supplemental_metrics(
        owner="wyattowalsh",
        repo="wyattowalsh",
        output_dir=output_dir,
        manifest_path=manifest_path,
    )

    assert (output_dir / "metrics-languages.svg").exists()
    assert (output_dir / "metrics-habits.svg").exists()
    languages_svg = (output_dir / "metrics-languages.svg").read_text(encoding="utf-8")
    assert "Most used languages" in languages_svg
    assert "Python" in languages_svg
    assert "bytes" in languages_svg
    assert not (output_dir / "metrics-activity.svg").exists()
    assert not (output_dir / "metrics-music.svg").exists()
    assert not (output_dir / "metrics-posts.svg").exists()
    assert statuses["activity"].enabled is False
    assert statuses["activity"].reason == "removed-duplicate-github-feed"
    assert statuses["music"].enabled is False
    assert statuses["posts"].enabled is False

    habits_svg = (output_dir / "metrics-habits.svg").read_text(encoding="utf-8")
    _assert_habits_is_designed(habits_svg)
    assert "agents" in habits_svg
    assert "14:00" in habits_svg
    assert "prefers-color-scheme: dark" in habits_svg
    # Dark media closes :root + @media with `}}`; class rules must not.
    assert habits_svg.count("}}") == 1

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["habits"]["enabled"] is True
    assert manifest["habits"]["required_markers"] == [
        "Coding habits",
        "Focus",
        "Peak hour",
    ]
    assert manifest["activity"]["enabled"] is False
    assert manifest["activity"]["reason"] == "removed-duplicate-github-feed"
    assert manifest["music"]["enabled"] is False


def test_validate_supplemental_metrics_rejects_missing_required_marker(
    tmp_path: Path,
) -> None:
    output_dir = tmp_path / "img"
    output_dir.mkdir()
    manifest_path = tmp_path / "metrics-supplemental.json"

    (output_dir / "metrics-habits.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg"><text x="1" y="20">Wrong title</text></svg>',  # noqa: E501
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


def test_fetch_recent_tracks_exchanges_refresh_token_and_parses_payload(
    monkeypatch,
) -> None:
    calls: list[str] = []

    def fake_request_json(url: str, **_: object) -> dict[str, object]:
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
                        "album": {
                            "name": "Album A",
                            "images": [
                                {
                                    "url": "https://i.scdn.co/image/large",
                                    "width": 640,
                                },
                                {
                                    "url": "https://i.scdn.co/image/mid",
                                    "width": 300,
                                },
                            ],
                        },
                    },
                }
            ]
        }

    monkeypatch.setattr("scripts.supplemental_metrics._request_json", fake_request_json)

    tracks = _fetch_recent_tracks("client-id", "client-secret", "refresh-token")

    assert len(tracks) == 1
    assert tracks[0]["name"] == "Song A"
    assert tracks[0]["artists"] == "Artist A, Artist B"
    assert tracks[0]["album"] == "Album A"
    assert tracks[0]["image_url"] == "https://i.scdn.co/image/mid"
    assert any("api/token" in url for url in calls)


def test_fetch_recent_tracks_rejects_malformed_artist_payload(monkeypatch) -> None:
    def fake_request_json(url: str, **_: object) -> dict[str, object]:
        if "api/token" in url:
            return {"access_token": "spotify-access"}
        return {
            "items": [
                {
                    "played_at": "2026-04-22T12:00:00Z",
                    "track": {"name": "Song A", "artists": "Artist A"},
                }
            ]
        }

    monkeypatch.setattr("scripts.supplemental_metrics._request_json", fake_request_json)

    with pytest.raises(
        RuntimeError,
        match="Spotify recently played item 0 artists must be a JSON array",
    ):
        _fetch_recent_tracks("client-id", "client-secret", "refresh-token")


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

    def fake_request_json(url: str, **kwargs: object) -> dict[str, object]:
        captured["url"] = url
        headers = kwargs.get("headers")
        assert isinstance(headers, dict)
        typed_headers = cast(dict[str, object], headers)
        captured["authorization"] = str(typed_headers.get("Authorization"))
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
                    "text": "A longish post about metrics recovery and CI validation that should still be trimmed nicely for the card output.",  # noqa: E501
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
        _forbid_activity_writer,
    )
    monkeypatch.setattr(
        "scripts.supplemental_metrics._render_activity_card",
        _forbid_activity_writer,
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
    assert statuses["activity"].enabled is False
    assert not (output_dir / "metrics-activity.svg").exists()


def _sample_tracks() -> list[dict[str, str]]:
    return [
        {
            "name": "Surreality",
            "artists": "Scope DJ",
            "played_at": "2026-04-22T12:00:00Z",
            "album": "Hardstyle Nights",
            "image_url": "https://i.scdn.co/image/hero",
        },
        {
            "name": "Melancholia",
            "artists": "Wasted Penguinz",
            "played_at": "2026-04-22T11:00:00Z",
            "album": "Melancholia",
            "image_url": "",
        },
        {
            "name": "Traveling",
            "artists": "Coone, Scope DJ",
            "played_at": "2026-04-22T10:00:00Z",
            "album": "",
            "image_url": "",
        },
    ]


def test_render_habits_svg_is_designed_dashboard_not_four_line_recap() -> None:
    svg = _render_habits_svg(_sample_metrics())

    _assert_habits_is_designed(svg)
    assert svg.count("<rect") > 20
    assert "current" in svg
    assert "longest" in svg
    assert "agents" in svg
    assert "14:00" in svg
    assert "habits-hero" in svg
    assert "habits-langs" in svg
    assert "Language mix" in svg


def test_render_music_svg_hero_includes_extras_only_when_data_exists(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "scripts.supplemental_metrics._fetch_image_data_uri",
        lambda url, **_: f"data:image/jpeg;base64,abc{url[-4:]}",
    )

    hero_and_extras = _render_music_svg(_sample_tracks())
    _assert_music_is_designed(hero_and_extras)
    assert "Surreality" in hero_and_extras
    assert "Scope DJ" in hero_and_extras
    assert "Hardstyle Nights" in hero_and_extras
    assert "music-extras" in hero_and_extras
    assert "Melancholia" in hero_and_extras
    assert ">SD</text>" in hero_and_extras
    assert "<image " in hero_and_extras
    assert "prefers-color-scheme: dark" in hero_and_extras

    hero_only = _render_music_svg(_sample_tracks()[:1])
    assert "music-hero" in hero_only
    assert "Surreality" in hero_only
    assert "music-extras" not in hero_only
    assert "Melancholia" not in hero_only


def test_render_music_svg_survives_missing_artwork(monkeypatch) -> None:
    monkeypatch.setattr(
        "scripts.supplemental_metrics._fetch_image_data_uri",
        lambda *_args, **_kwargs: None,
    )

    svg = _render_music_svg(_sample_tracks()[:1])
    assert "Surreality" in svg
    assert ">SD</text>" in svg
    assert "<image " not in svg


def test_fetch_image_data_uri_rejects_non_http_and_non_image(monkeypatch) -> None:
    assert _fetch_image_data_uri("file:///tmp/art.jpg") is None

    monkeypatch.setattr(
        "scripts.supplemental_metrics._request_bytes",
        lambda *_args, **_kwargs: (b"not-an-image", "text/plain"),
    )
    assert _fetch_image_data_uri("https://i.scdn.co/image/x") is None

    png = (
        b"\x89PNG\r\n\x1a\n"
        b"\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    monkeypatch.setattr(
        "scripts.supplemental_metrics._request_bytes",
        lambda *_args, **_kwargs: (png, "image/png"),
    )
    uri = _fetch_image_data_uri("https://i.scdn.co/image/x")
    assert uri is not None
    assert uri.startswith("data:image/png;base64,")


def test_generate_supplemental_metrics_writes_spotify_hero_when_secrets_present(
    tmp_path: Path,
    monkeypatch,
) -> None:
    output_dir = tmp_path / "img"
    manifest_path = tmp_path / "metrics-supplemental.json"

    monkeypatch.setenv("GITHUB_TOKEN", "test-token")
    monkeypatch.setenv("SPOTIFY_CLIENT_ID", "client")
    monkeypatch.setenv("SPOTIFY_CLIENT_SECRET", "secret")
    monkeypatch.setenv("SPOTIFY_REFRESH_TOKEN", "refresh")
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
        _forbid_activity_writer,
    )
    monkeypatch.setattr(
        "scripts.supplemental_metrics._render_activity_card",
        _forbid_activity_writer,
    )
    monkeypatch.setattr(
        "scripts.supplemental_metrics._fetch_recent_tracks",
        lambda *_args: _sample_tracks(),
    )
    monkeypatch.setattr(
        "scripts.supplemental_metrics._fetch_image_data_uri",
        lambda *_args, **_kwargs: None,
    )

    statuses = generate_supplemental_metrics(
        owner="wyattowalsh",
        repo="wyattowalsh",
        output_dir=output_dir,
        manifest_path=manifest_path,
    )

    assert statuses["music"].enabled is True
    assert statuses["activity"].enabled is False
    assert statuses["activity"].reason == "removed-duplicate-github-feed"
    assert not (output_dir / "metrics-activity.svg").exists()
    music_svg = (output_dir / "metrics-music.svg").read_text(encoding="utf-8")
    _assert_music_is_designed(music_svg)
    assert "Surreality" in music_svg
    assert "music-extras" in music_svg
    errors = validate_supplemental_metrics(
        output_dir=output_dir,
        manifest_path=manifest_path,
    )
    assert errors == []


def test_committed_habits_and_music_svgs_use_designed_layouts(
    monkeypatch,
) -> None:
    """fact-habits-split / fact-spotify: cards are designed, not recaps."""
    monkeypatch.setattr(
        "scripts.supplemental_metrics._fetch_image_data_uri",
        lambda url, **_: f"data:image/jpeg;base64,abc{url[-4:]}",
    )
    _assert_habits_is_designed(_render_habits_svg(_sample_metrics()))
    rendered_music = _render_music_svg(_sample_tracks())
    _assert_music_is_designed(rendered_music)
    assert "music-extras" in rendered_music
    assert "Surreality" in rendered_music
    assert "Scope DJ" in rendered_music

    assets = Path(__file__).resolve().parents[1] / ".github" / "assets" / "img"
    committed_habits = _well_formed_svg(assets / "metrics-habits.svg")
    committed_music = _well_formed_svg(assets / "metrics-music.svg")
    if committed_habits is not None:
        _assert_habits_is_designed(committed_habits)
    if committed_music is not None:
        _assert_music_is_designed(committed_music)
