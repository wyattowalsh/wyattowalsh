"""Generate and validate supplemental profile metrics cards."""

from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import json
import os
import secrets
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any, Final, TypeGuard

from .fetch_metrics import collect as collect_github_metrics
from .metrics_svg import validate_svg_file
from .readme_svg import ReadmeSvgAssetBuilder, SvgBlock, SvgBlockRenderer, SvgCard
from .utils import get_logger

logger = get_logger(module=__name__)

GITHUB_API_BASE: Final[str] = "https://api.github.com"
SPOTIFY_TOKEN_URL: Final[str] = "https://accounts.spotify.com/api/token"
SPOTIFY_RECENT_TRACKS_URL: Final[str] = (
    "https://api.spotify.com/v1/me/player/recently-played?limit=3"
)
X_API_BASE: Final[str] = "https://api.x.com/2"


def _is_json_object(value: object) -> TypeGuard[dict[str, Any]]:
    """Return whether *value* is a JSON object with string keys."""

    return isinstance(value, dict) and all(isinstance(key, str) for key in value)


def _require_json_object(value: object, *, context: str) -> dict[str, Any]:
    """Narrow an untrusted decoded value to a JSON object or fail closed."""

    if not _is_json_object(value):
        raise RuntimeError(f"{context} must be a JSON object")
    return value


def _require_json_array(value: object, *, context: str) -> list[Any]:
    """Narrow an untrusted decoded value to a JSON array or fail closed."""

    if not isinstance(value, list):
        raise RuntimeError(f"{context} must be a JSON array")
    return value


def _optional_json_object(value: object, *, context: str) -> dict[str, Any]:
    """Return an absent optional object as empty, rejecting wrong shapes."""

    if value is None:
        return {}
    return _require_json_object(value, context=context)


@dataclass(frozen=True)
class SupplementalAssetSpec:
    """Contract for a generated supplemental metrics asset."""

    asset_name: str
    title: str
    required_markers: tuple[str, ...]
    optional: bool = False


@dataclass(frozen=True)
class SupplementalAssetStatus:
    """Generation/validation state for a single supplemental asset."""

    asset_name: str
    filename: str
    enabled: bool
    optional: bool
    title: str
    required_markers: tuple[str, ...]
    reason: str = ""


@dataclass(frozen=True)
class XOAuth1Credentials:
    """User-context OAuth 1.0a credentials for X API v2 requests."""

    api_key: str
    api_key_secret: str
    access_token: str
    access_token_secret: str


ASSET_SPECS: Final[dict[str, SupplementalAssetSpec]] = {
    "habits": SupplementalAssetSpec(
        asset_name="metrics-habits",
        title="Coding habits",
        required_markers=("Coding habits", "30-day activity"),
    ),
    "activity": SupplementalAssetSpec(
        asset_name="metrics-activity",
        title="Recent activity",
        required_markers=("Recent activity", "GitHub"),
    ),
    "music": SupplementalAssetSpec(
        asset_name="metrics-music",
        title="Recently played",
        required_markers=("Recently played", "Spotify"),
        optional=True,
    ),
    "posts": SupplementalAssetSpec(
        asset_name="metrics-posts",
        title="Latest posts",
        required_markers=("Latest posts", "X"),
        optional=True,
    ),
}


def _github_headers(token: str | None) -> dict[str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


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


def _probe_github_token(token: str) -> bool:
    """Return True when *token* can call the GitHub API (cheap user probe)."""
    try:
        _request_json(
            f"{GITHUB_API_BASE}/user",
            headers=_github_headers(token),
        )
        return True
    except (
        urllib.error.HTTPError,
        urllib.error.URLError,
        TimeoutError,
        OSError,
        json.JSONDecodeError,
    ):
        return False


def _resolve_github_token() -> str | None:
    """Pick a usable GitHub token for supplemental generation.

    Prefer ``METRICS_TOKEN`` when it authenticates, otherwise fall back to the
    Actions ``GITHUB_TOKEN`` / ``GH_TOKEN``. An expired METRICS_TOKEN must not
    block generation when a working default token is available.
    """
    candidates = [
        os.getenv("METRICS_TOKEN", "").strip(),
        os.getenv("GITHUB_TOKEN", "").strip(),
        os.getenv("GH_TOKEN", "").strip(),
    ]
    non_empty = [token for token in candidates if token]
    if not non_empty:
        return None
    for token in non_empty:
        if _probe_github_token(token):
            return token
    # Last resort: return first candidate so callers can still surface 401s.
    return non_empty[0]


def _parse_iso8601(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)
    except ValueError:
        return None


def _relative_label(value: str | None, *, now: datetime | None = None) -> str:
    dt = _parse_iso8601(value)
    if dt is None:
        return "unknown time"
    now_utc = now or datetime.now(UTC)
    delta = now_utc - dt
    total_seconds = max(0, int(delta.total_seconds()))
    if total_seconds < 3600:
        minutes = max(1, total_seconds // 60)
        return f"{minutes}m ago"
    if total_seconds < 86400:
        hours = total_seconds // 3600
        return f"{hours}h ago"
    if total_seconds < 86400 * 14:
        days = total_seconds // 86400
        return f"{days}d ago"
    return dt.strftime("%b %d")


def _truncate(value: str, limit: int) -> str:
    compact = " ".join(value.split())
    if len(compact) <= limit:
        return compact
    return f"{compact[: max(0, limit - 3)].rstrip()}..."


def _normalize_token(value: str | None) -> str:
    if not value:
        return ""
    return urllib.parse.unquote(value.strip())


def _load_x_oauth1_credentials_from_env() -> XOAuth1Credentials | None:
    api_key = _normalize_token(os.getenv("X_API_KEY"))
    api_key_secret = _normalize_token(os.getenv("X_API_KEY_SECRET"))
    access_token = _normalize_token(os.getenv("X_ACCESS_TOKEN"))
    access_token_secret = _normalize_token(os.getenv("X_ACCESS_TOKEN_SECRET"))
    if all((api_key, api_key_secret, access_token, access_token_secret)):
        return XOAuth1Credentials(
            api_key=api_key,
            api_key_secret=api_key_secret,
            access_token=access_token,
            access_token_secret=access_token_secret,
        )
    return None


def _oauth1_percent_encode(value: str) -> str:
    return urllib.parse.quote(value, safe="~-._")


def _build_x_oauth1_authorization_header(
    *,
    method: str,
    url: str,
    credentials: XOAuth1Credentials,
    nonce: str | None = None,
    timestamp: str | None = None,
) -> str:
    """Create an OAuth 1.0a Authorization header for an X API request."""

    parsed = urllib.parse.urlsplit(url)
    base_url = urllib.parse.urlunsplit(
        (parsed.scheme, parsed.netloc, parsed.path, "", "")
    )
    oauth_params = {
        "oauth_consumer_key": credentials.api_key,
        "oauth_nonce": nonce or secrets.token_hex(16),
        "oauth_signature_method": "HMAC-SHA1",
        "oauth_timestamp": timestamp or str(int(time.time())),
        "oauth_token": credentials.access_token,
        "oauth_version": "1.0",
    }
    query_params = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    signature_params = list(query_params) + list(oauth_params.items())
    normalized = "&".join(
        f"{_oauth1_percent_encode(key)}={_oauth1_percent_encode(value)}"
        for key, value in sorted(
            signature_params,
            key=lambda item: (
                _oauth1_percent_encode(item[0]),
                _oauth1_percent_encode(item[1]),
            ),
        )
    )
    signature_base_string = "&".join(
        (
            method.upper(),
            _oauth1_percent_encode(base_url),
            _oauth1_percent_encode(normalized),
        )
    )
    signing_key = (
        f"{_oauth1_percent_encode(credentials.api_key_secret)}&"
        f"{_oauth1_percent_encode(credentials.access_token_secret)}"
    )
    signature = base64.b64encode(
        hmac.new(
            signing_key.encode("utf-8"),
            signature_base_string.encode("utf-8"),
            hashlib.sha1,
        ).digest()
    ).decode("ascii")
    oauth_params["oauth_signature"] = signature
    serialized = ", ".join(
        f'{_oauth1_percent_encode(key)}="{_oauth1_percent_encode(value)}"'
        for key, value in sorted(oauth_params.items())
    )
    return f"OAuth {serialized}"


def _x_request_json(
    url: str,
    credentials: XOAuth1Credentials,
) -> Any:
    headers = {
        "Authorization": _build_x_oauth1_authorization_header(
            method="GET",
            url=url,
            credentials=credentials,
        ),
        "Accept": "application/json",
    }
    return _request_json(url, headers=headers)


def _write_manifest(
    manifest_path: Path,
    statuses: dict[str, SupplementalAssetStatus],
) -> Path:
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        key: {
            **asdict(status),
            "required_markers": list(status.required_markers),
        }
        for key, status in statuses.items()
    }
    manifest_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return manifest_path


def _remove_asset_if_present(output_dir: Path, asset_name: str) -> None:
    path = output_dir / f"{asset_name}.svg"
    if path.exists():
        path.unlink()
        logger.info("Removed stale optional asset {}", path)


def _streaks_from_daily_counts(
    daily_counts: dict[date, int],
    *,
    now_date: date,
) -> tuple[int, int]:
    if not daily_counts:
        return 0, 0

    current = 0
    cursor = now_date
    while daily_counts.get(cursor, 0) > 0:
        current += 1
        cursor -= timedelta(days=1)

    longest = 0
    running = 0
    for day in sorted(daily_counts):
        if daily_counts.get(day, 0) > 0:
            running += 1
            longest = max(longest, running)
        else:
            running = 0
    return current, longest


def _contribution_stats(
    metrics: dict[str, Any],
    *,
    window_days: int = 30,
) -> dict[str, Any]:
    raw_calendar = metrics.get("contributions_calendar") or []
    daily_counts: dict[date, int] = {}
    for entry in raw_calendar:
        parsed_date = _parse_iso8601(entry.get("date"))
        if parsed_date is None:
            try:
                parsed_date = datetime.strptime(
                    entry.get("date", ""), "%Y-%m-%d"
                ).replace(tzinfo=UTC)
            except ValueError:
                continue
        daily_counts[parsed_date.date()] = int(entry.get("count", 0) or 0)

    today = max(daily_counts.keys(), default=datetime.now(UTC).date())
    cutoff = today - timedelta(days=window_days - 1)
    recent_counts = {
        day: count for day, count in daily_counts.items() if cutoff <= day <= today
    }
    total = sum(recent_counts.values())
    active_days = sum(1 for count in recent_counts.values() if count > 0)
    busiest_day = max(recent_counts.values(), default=0)
    current_streak, longest_streak = _streaks_from_daily_counts(
        daily_counts,
        now_date=today,
    )
    return {
        "total": total,
        "active_days": active_days,
        "busiest_day": busiest_day,
        "current_streak": current_streak,
        "longest_streak": longest_streak,
    }


def _top_languages(metrics: dict[str, Any], *, limit: int = 3) -> tuple[str, ...]:
    languages = metrics.get("languages") or {}
    ranked = sorted(
        (
            (name, int(size or 0))
            for name, size in languages.items()
            if int(size or 0) > 0
        ),
        key=lambda item: item[1],
        reverse=True,
    )
    return tuple(name for name, _ in ranked[:limit])


def _focus_repositories(metrics: dict[str, Any], *, limit: int = 2) -> tuple[str, ...]:
    recent_prs = metrics.get("recent_merged_prs") or []
    counts: dict[str, int] = {}
    for pr in recent_prs:
        repo_name = str(pr.get("repo_name") or "").strip()
        if not repo_name:
            continue
        counts[repo_name] = counts.get(repo_name, 0) + 1
    ranked = sorted(counts.items(), key=lambda item: item[1], reverse=True)
    return tuple(name for name, _ in ranked[:limit])


def _peak_commit_hour(metrics: dict[str, Any]) -> str:
    distribution = metrics.get("commit_hour_distribution") or {}
    if not distribution:
        return "n/a"
    hour = max(distribution.items(), key=lambda item: int(item[1] or 0))[0]
    return f"{int(hour):02d}:00"


def _render_habits_card(metrics: dict[str, Any]) -> SvgBlock:
    stats = _contribution_stats(metrics)
    top_languages = ", ".join(_top_languages(metrics)) or "none yet"
    focus_repos = ", ".join(_focus_repositories(metrics)) or "profile-wide work"
    peak_hour = _peak_commit_hour(metrics)

    card = SvgCard(
        title=ASSET_SPECS["habits"].title,
        kicker="GitHub last 30 days",
        lines=(
            f"30-day activity: {stats['total']} contributions across {stats['active_days']} active days",  # noqa: E501
            f"Current streak: {stats['current_streak']}d | longest streak: {stats['longest_streak']}d",  # noqa: E501
            f"Peak hour: {peak_hour} UTC | focus: {focus_repos} | langs: {top_languages}",  # noqa: E501
        ),
        meta=(
            f"Reviews {int(metrics.get('pr_review_count') or 0)}",
            f"Repos {int(metrics.get('public_repos') or 0)}",
            f"Busiest day {stats['busiest_day']}",
        ),
        icon="GH",
        badge="Custom",
        accent="#0969da",
    )
    return SvgBlock(title=card.title, cards=(card,))


def _summarize_github_event(event: dict[str, Any]) -> tuple[str, str] | None:
    event_type = str(event.get("type") or "")
    repo_payload = _optional_json_object(
        event.get("repo"),
        context="GitHub event repo",
    )
    repo = str(repo_payload.get("name") or "").strip()
    created_at = str(event.get("created_at") or "")
    payload = _optional_json_object(
        event.get("payload"),
        context=f"GitHub {event_type or 'unknown'} payload",
    )

    if event_type == "PushEvent":
        commits = payload.get("commits")
        commit_count = (
            len(
                _require_json_array(
                    commits,
                    context="GitHub PushEvent commits",
                )
            )
            if commits is not None
            else 0
        )
        size = int(payload.get("size") or commit_count or 1)
        noun = "commit" if size == 1 else "commits"
        return f"Pushed {size} {noun} to {repo}", created_at
    if event_type == "WatchEvent":
        return f"Starred {repo}", created_at
    if event_type == "PullRequestEvent":
        pr = _optional_json_object(
            payload.get("pull_request"),
            context="GitHub PullRequestEvent pull_request",
        )
        if pr.get("merged_at"):
            return f"Merged PR in {repo}", created_at
        action = str(payload.get("action") or "updated").replace("_", " ")
        return f"{action.title()} PR in {repo}", created_at
    if event_type == "IssuesEvent":
        action = str(payload.get("action") or "updated").replace("_", " ")
        return f"{action.title()} issue in {repo}", created_at
    if event_type == "ReleaseEvent":
        return f"Published release in {repo}", created_at
    if event_type == "CreateEvent":
        ref_type = str(payload.get("ref_type") or "resource")
        return f"Created {ref_type} in {repo}", created_at
    return None


def _fetch_recent_activity(
    owner: str,
    token: str | None,
    *,
    limit: int = 3,
) -> list[dict[str, str]]:
    url = f"{GITHUB_API_BASE}/users/{owner}/events/public?per_page=30"
    try:
        data = _request_json(url, headers=_github_headers(token))
    except (
        urllib.error.HTTPError,
        urllib.error.URLError,
        TimeoutError,
        OSError,
        json.JSONDecodeError,
    ) as exc:
        logger.warning(
            "Failed to fetch recent activity for {}: {}",
            owner,
            exc,
        )
        return []
    decoded_events = _require_json_array(data, context="GitHub events response")
    events: list[dict[str, str]] = []
    for index, raw_item in enumerate(decoded_events):
        item = _require_json_object(
            raw_item,
            context=f"GitHub event {index}",
        )
        summarized = _summarize_github_event(item)
        if summarized is None:
            continue
        summary, created_at = summarized
        events.append(
            {
                "summary": summary,
                "created_at": created_at,
                "age": _relative_label(created_at),
            }
        )
        if len(events) >= limit:
            break
    return events


def _render_activity_card(owner: str, events: list[dict[str, str]]) -> SvgBlock:
    lines = tuple(
        _truncate(f"{event['age']} | {event['summary']}", 84) for event in events[:3]
    )
    if not lines:
        lines = ("No recent public GitHub events were available.",)
    card = SvgCard(
        title=ASSET_SPECS["activity"].title,
        kicker=f"GitHub feed for {owner}",
        lines=lines,
        meta=("GitHub", f"Items {len(events)}"),
        icon="GH",
        badge="Custom",
        accent="#1f883d",
    )
    return SvgBlock(title=card.title, cards=(card,))


def _spotify_access_token(
    client_id: str,
    client_secret: str,
    refresh_token: str,
) -> str:
    auth = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode("ascii")
    body = urllib.parse.urlencode(
        {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        }
    ).encode("utf-8")
    payload = _require_json_object(
        _request_json(
            SPOTIFY_TOKEN_URL,
            headers={
                "Authorization": f"Basic {auth}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            method="POST",
            data=body,
        ),
        context="Spotify token response",
    )
    token = str(payload.get("access_token") or "").strip()
    if not token:
        raise RuntimeError("Spotify token exchange returned no access_token")
    return token


def _fetch_recent_tracks(
    client_id: str,
    client_secret: str,
    refresh_token: str,
) -> list[dict[str, str]]:
    access_token = _spotify_access_token(client_id, client_secret, refresh_token)
    payload = _require_json_object(
        _request_json(
            SPOTIFY_RECENT_TRACKS_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        ),
        context="Spotify recently played response",
    )
    items = _require_json_array(
        payload.get("items"),
        context="Spotify recently played items",
    )
    tracks: list[dict[str, str]] = []
    for item_index, raw_item in enumerate(items):
        item = _require_json_object(
            raw_item,
            context=f"Spotify recently played item {item_index}",
        )
        track = _require_json_object(
            item.get("track"),
            context=f"Spotify recently played item {item_index} track",
        )
        artists = _require_json_array(
            track.get("artists"),
            context=f"Spotify recently played item {item_index} artists",
        )
        artist_names_list: list[str] = []
        for artist_index, raw_artist in enumerate(artists):
            artist = _require_json_object(
                raw_artist,
                context=(
                    f"Spotify recently played item {item_index} artist {artist_index}"
                ),
            )
            artist_name = str(artist.get("name") or "").strip()
            if artist_name:
                artist_names_list.append(artist_name)
        artist_names = ", ".join(artist_names_list)
        tracks.append(
            {
                "name": str(track.get("name") or "").strip(),
                "artists": artist_names or "Unknown artist",
                "played_at": str(item.get("played_at") or "").strip(),
            }
        )
    return tracks


def _render_music_card(tracks: list[dict[str, str]]) -> SvgBlock:
    lines = tuple(
        _truncate(f"{track['name']} - {track['artists']}", 84) for track in tracks[:3]
    )
    if not lines:
        lines = ("No recent Spotify tracks were available.",)
    latest_played = tracks[0]["played_at"] if tracks else None
    card = SvgCard(
        title=ASSET_SPECS["music"].title,
        kicker="Spotify recent listens",
        lines=lines,
        meta=("Spotify", _relative_label(latest_played)),
        icon="SP",
        badge="Custom",
        accent="#1db954",
    )
    return SvgBlock(title=card.title, cards=(card,))


def _fetch_authenticated_x_user(
    credentials: XOAuth1Credentials,
) -> dict[str, str]:
    payload = _require_json_object(
        _x_request_json(
            f"{X_API_BASE}/users/me?user.fields=username,name",
            credentials,
        ),
        context="X authenticated user response",
    )
    user = _require_json_object(
        payload.get("data"),
        context="X authenticated user data",
    )
    user_id = str(user.get("id") or "").strip()
    username = str(user.get("username") or "").strip()
    if not user_id or not username:
        raise RuntimeError("X authenticated user lookup returned no id or username")
    return {
        "id": user_id,
        "username": username,
        "name": str(user.get("name") or "").strip(),
    }


def _fetch_latest_posts(
    credentials: XOAuth1Credentials,
    *,
    limit: int = 3,
) -> tuple[dict[str, str], list[dict[str, str]]]:
    user = _fetch_authenticated_x_user(credentials)
    params = urllib.parse.urlencode(
        {
            "max_results": str(limit),
            "exclude": "replies,retweets",
            "tweet.fields": "created_at,public_metrics,text",
        }
    )
    payload = _require_json_object(
        _x_request_json(
            f"{X_API_BASE}/users/{user['id']}/tweets?{params}",
            credentials,
        ),
        context="X posts response",
    )
    posts: list[dict[str, str]] = []
    raw_posts = payload.get("data")
    decoded_posts = (
        _require_json_array(raw_posts, context="X posts data")
        if raw_posts is not None
        else []
    )
    for item_index, raw_item in enumerate(decoded_posts):
        item = _require_json_object(
            raw_item,
            context=f"X post {item_index}",
        )
        metrics = _optional_json_object(
            item.get("public_metrics"),
            context=f"X post {item_index} public_metrics",
        )
        posts.append(
            {
                "text": _truncate(str(item.get("text") or "").replace("\n", " "), 84),
                "created_at": str(item.get("created_at") or "").strip(),
                "likes": str(int(metrics.get("like_count") or 0)),
            }
        )
    return user, posts


def _render_posts_card(handle: str, posts: list[dict[str, str]]) -> SvgBlock:
    lines = tuple(_truncate(post["text"], 84) for post in posts[:3])
    if not lines:
        lines = ("No recent X posts were available.",)
    latest_posted = posts[0]["created_at"] if posts else None
    card = SvgCard(
        title=ASSET_SPECS["posts"].title,
        kicker=f"X by @{handle}",
        lines=lines,
        meta=("X", _relative_label(latest_posted)),
        icon="X",
        badge="Custom",
        accent="#000000",
    )
    return SvgBlock(title=card.title, cards=(card,))


def generate_supplemental_metrics(
    *,
    owner: str,
    repo: str,
    output_dir: Path,
    manifest_path: Path,
    x_handle: str | None = None,
) -> dict[str, SupplementalAssetStatus]:
    """Generate the supplemental metrics cards and return their manifest."""

    output_dir.mkdir(parents=True, exist_ok=True)
    builder = ReadmeSvgAssetBuilder(
        output_dir,
        renderer=SvgBlockRenderer(width=1200, card_height=208, padding=28),
    )

    github_token = _resolve_github_token()
    if not github_token:
        raise RuntimeError(
            "A GitHub token is required to generate supplemental metrics"
        )

    x_credentials = _load_x_oauth1_credentials_from_env()
    spotify_client_id = os.getenv("SPOTIFY_CLIENT_ID", "").strip()
    spotify_client_secret = os.getenv("SPOTIFY_CLIENT_SECRET", "").strip()
    spotify_refresh_token = os.getenv("SPOTIFY_REFRESH_TOKEN", "").strip()
    expected_x_handle = (x_handle or owner).strip().lstrip("@")

    metrics = collect_github_metrics(owner, repo, github_token)
    events = _fetch_recent_activity(owner, github_token)

    builder.render_and_write(
        ASSET_SPECS["habits"].asset_name,
        _render_habits_card(metrics),
    )
    builder.render_and_write(
        ASSET_SPECS["activity"].asset_name,
        _render_activity_card(owner, events),
    )

    statuses: dict[str, SupplementalAssetStatus] = {
        "habits": SupplementalAssetStatus(
            asset_name=ASSET_SPECS["habits"].asset_name,
            filename=f"{ASSET_SPECS['habits'].asset_name}.svg",
            enabled=True,
            optional=False,
            title=ASSET_SPECS["habits"].title,
            required_markers=ASSET_SPECS["habits"].required_markers,
        ),
        "activity": SupplementalAssetStatus(
            asset_name=ASSET_SPECS["activity"].asset_name,
            filename=f"{ASSET_SPECS['activity'].asset_name}.svg",
            enabled=True,
            optional=False,
            title=ASSET_SPECS["activity"].title,
            required_markers=ASSET_SPECS["activity"].required_markers,
        ),
    }

    if spotify_client_id and spotify_client_secret and spotify_refresh_token:
        tracks = _fetch_recent_tracks(
            spotify_client_id,
            spotify_client_secret,
            spotify_refresh_token,
        )
        builder.render_and_write(
            ASSET_SPECS["music"].asset_name,
            _render_music_card(tracks),
        )
        statuses["music"] = SupplementalAssetStatus(
            asset_name=ASSET_SPECS["music"].asset_name,
            filename=f"{ASSET_SPECS['music'].asset_name}.svg",
            enabled=True,
            optional=True,
            title=ASSET_SPECS["music"].title,
            required_markers=ASSET_SPECS["music"].required_markers,
        )
    else:
        _remove_asset_if_present(output_dir, ASSET_SPECS["music"].asset_name)
        statuses["music"] = SupplementalAssetStatus(
            asset_name=ASSET_SPECS["music"].asset_name,
            filename=f"{ASSET_SPECS['music'].asset_name}.svg",
            enabled=False,
            optional=True,
            title=ASSET_SPECS["music"].title,
            required_markers=ASSET_SPECS["music"].required_markers,
            reason="spotify-secrets-missing",
        )

    if x_credentials:
        x_user, posts = _fetch_latest_posts(x_credentials)
        actual_handle = x_user["username"]
        if expected_x_handle and actual_handle.lower() != expected_x_handle.lower():
            raise RuntimeError(
                f"X OAuth user mismatch: expected @{expected_x_handle}, got @{actual_handle}"  # noqa: E501
            )
        builder.render_and_write(
            ASSET_SPECS["posts"].asset_name,
            _render_posts_card(actual_handle, posts),
        )
        statuses["posts"] = SupplementalAssetStatus(
            asset_name=ASSET_SPECS["posts"].asset_name,
            filename=f"{ASSET_SPECS['posts'].asset_name}.svg",
            enabled=True,
            optional=True,
            title=ASSET_SPECS["posts"].title,
            required_markers=ASSET_SPECS["posts"].required_markers,
        )
    else:
        _remove_asset_if_present(output_dir, ASSET_SPECS["posts"].asset_name)
        statuses["posts"] = SupplementalAssetStatus(
            asset_name=ASSET_SPECS["posts"].asset_name,
            filename=f"{ASSET_SPECS['posts'].asset_name}.svg",
            enabled=False,
            optional=True,
            title=ASSET_SPECS["posts"].title,
            required_markers=ASSET_SPECS["posts"].required_markers,
            reason="x-oauth1-secrets-missing",
        )

    _write_manifest(manifest_path, statuses)
    return statuses


def validate_supplemental_metrics(
    *,
    output_dir: Path,
    manifest_path: Path,
) -> list[str]:
    """Validate enabled supplemental metric assets against the manifest."""

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    errors: list[str] = []
    for item in manifest.values():
        filename = str(item["filename"])
        enabled = bool(item["enabled"])
        asset_path = output_dir / filename
        if not enabled:
            if asset_path.exists():
                errors.append(f"{filename}: disabled asset is still present")
            continue

        result = validate_svg_file(asset_path)
        if not result.is_valid:
            errors.append(f"{filename}: {result.status.value} - {result.detail}")
            continue

        svg_text = asset_path.read_text(encoding="utf-8")
        for marker in item.get("required_markers", []):
            if marker not in svg_text:
                errors.append(f"{filename}: missing required marker '{marker}'")
    return errors


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate_parser = subparsers.add_parser("generate")
    generate_parser.add_argument("--owner", required=True)
    generate_parser.add_argument("--repo", required=True)
    generate_parser.add_argument("--output-dir", type=Path, required=True)
    generate_parser.add_argument("--manifest-path", type=Path, required=True)
    generate_parser.add_argument("--x-handle", default=None)

    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("--output-dir", type=Path, required=True)
    validate_parser.add_argument("--manifest-path", type=Path, required=True)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "generate":
            statuses = generate_supplemental_metrics(
                owner=args.owner,
                repo=args.repo,
                output_dir=args.output_dir,
                manifest_path=args.manifest_path,
                x_handle=args.x_handle,
            )
            for key, status in statuses.items():
                state = "enabled" if status.enabled else f"disabled ({status.reason})"
                print(f"{key}: {state}")
            return 0

        if args.command == "validate":
            errors = validate_supplemental_metrics(
                output_dir=args.output_dir,
                manifest_path=args.manifest_path,
            )
            if errors:
                for error in errors:
                    print(error)
                return 1
            print("supplemental-metrics: valid")
            return 0
    except urllib.error.HTTPError as exc:
        logger.error("Supplemental metrics API request failed: {}", exc)
        print(f"supplemental-metrics: http-error {exc.code}")
        return 1
    except Exception as exc:  # pragma: no cover - CLI guard
        logger.error("Supplemental metrics command failed: {}", exc)
        print(f"supplemental-metrics: error {exc}")
        return 1

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
