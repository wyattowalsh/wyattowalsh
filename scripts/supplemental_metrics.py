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
from html import escape
from pathlib import Path
from typing import Any, Final, TypeGuard

from .fetch_metrics import collect as collect_github_metrics
from .metrics_svg import validate_svg_file
from .readme_svg import (
    FONT_FAMILY,
    ReadmeSvgAssetBuilder,
    SvgBlock,
    SvgBlockRenderer,
    SvgCard,
)
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
        required_markers=("Coding habits", "Focus", "Peak hour"),
    ),
    # Unused for README emit. Kept so coverage and CLI tests can still
    # exercise the GitHub-event helpers; generate never writes this file.
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


def _request_bytes(
    url: str,
    *,
    headers: dict[str, str] | None = None,
    timeout: int = 15,
    max_bytes: int = 120_000,
) -> tuple[bytes, str]:
    """Fetch a bounded binary payload and its Content-Type."""

    request = urllib.request.Request(url, headers=headers or {}, method="GET")
    context = ssl.create_default_context()
    with urllib.request.urlopen(request, context=context, timeout=timeout) as response:
        payload = response.read(max_bytes + 1)
        content_type = str(response.headers.get("Content-Type") or "")
    if len(payload) > max_bytes:
        raise RuntimeError(f"Remote payload exceeded {max_bytes} bytes")
    return payload, content_type.split(";", 1)[0].strip().lower()


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


def _calendar_daily_counts(metrics: dict[str, Any]) -> dict[date, int]:
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
    return daily_counts


def _contribution_stats(
    metrics: dict[str, Any],
    *,
    window_days: int = 30,
) -> dict[str, Any]:
    daily_counts = _calendar_daily_counts(metrics)
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


def _cadence_series(metrics: dict[str, Any], *, days: int = 30) -> list[int]:
    daily_counts = _calendar_daily_counts(metrics)
    today = max(daily_counts.keys(), default=datetime.now(UTC).date())
    return [
        daily_counts.get(today - timedelta(days=offset), 0)
        for offset in range(days - 1, -1, -1)
    ]


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


def _focus_repository_counts(
    metrics: dict[str, Any],
    *,
    limit: int = 3,
) -> tuple[tuple[str, int], ...]:
    recent_prs = metrics.get("recent_merged_prs") or []
    counts: dict[str, int] = {}
    for pr in recent_prs:
        repo_name = str(pr.get("repo_name") or "").strip()
        if not repo_name:
            continue
        counts[repo_name] = counts.get(repo_name, 0) + 1
    ranked = sorted(counts.items(), key=lambda item: item[1], reverse=True)
    return tuple((name, count) for name, count in ranked[:limit])


def _focus_repositories(metrics: dict[str, Any], *, limit: int = 2) -> tuple[str, ...]:
    return tuple(name for name, _ in _focus_repository_counts(metrics, limit=limit))


def _hour_buckets(metrics: dict[str, Any]) -> list[int]:
    distribution = metrics.get("commit_hour_distribution") or {}
    buckets = [0] * 24
    if not isinstance(distribution, dict):
        return buckets
    for raw_hour, raw_count in distribution.items():
        try:
            hour = int(raw_hour)
            count = int(raw_count or 0)
        except (TypeError, ValueError):
            continue
        if 0 <= hour <= 23 and count > 0:
            buckets[hour] += count
    return buckets


def _peak_commit_hour(metrics: dict[str, Any]) -> str:
    buckets = _hour_buckets(metrics)
    if not any(buckets):
        return "n/a"
    hour = max(range(24), key=lambda item: (buckets[item], -item))
    return f"{hour:02d}:00"


def _svg_text(value: str) -> str:
    return escape(value, quote=True)


def _svg_num(value: float) -> str:
    return f"{value:.1f}".rstrip("0").rstrip(".")


def _label_swatch(label: str) -> str:
    digest = hashlib.sha256(label.encode("utf-8")).digest()
    palette = (
        "#1db954",
        "#0969da",
        "#8250df",
        "#bf4b8a",
        "#d4a72c",
        "#1a7f37",
        "#cf222e",
        "#218bff",
    )
    return palette[digest[0] % len(palette)]


def _supplemental_svg_css(*, accent: str, accent_dark: str) -> str:
    return "\n".join(
        (
            ":root {",
            "  --canvas-bg: #ffffff;",
            "  --card-bg: #ffffff;",
            "  --panel-bg: #f6f8fa;",
            "  --card-border: #d0d7de;",
            "  --title-color: #1f2328;",
            "  --text-color: #656d76;",
            "  --meta-color: #656d76;",
            f"  --accent: {accent};",
            "  --focus: #8250df;",
            "  --peak: #1a7f37;",
            "  --streak: #bf4b8a;",
            "}",
            "@media (prefers-color-scheme: dark) { :root {",
            "  --canvas-bg: #0d1117;",
            "  --card-bg: #0d1117;",
            "  --panel-bg: #161b22;",
            "  --card-border: #30363d;",
            "  --title-color: #e6edf3;",
            "  --text-color: #8b949e;",
            "  --meta-color: #8b949e;",
            f"  --accent: {accent_dark};",
            "  --focus: #a371f7;",
            "  --peak: #3fb950;",
            "  --streak: #db61a2;",
            "}}",
            f".title {{ fill: var(--title-color); font: 700 22px {FONT_FAMILY}; }}",
            f".kicker {{ fill: var(--meta-color); font: 700 11px {FONT_FAMILY};",
            " letter-spacing: 0.08em; text-transform: uppercase; }",
            f".label {{ fill: var(--meta-color); font: 700 11px {FONT_FAMILY};",
            " letter-spacing: 0.08em; text-transform: uppercase; }",
            f".value {{ fill: var(--title-color); font: 700 28px {FONT_FAMILY}; }}",
            f".body {{ fill: var(--title-color); font: 600 14px {FONT_FAMILY}; }}",
            f".muted {{ fill: var(--text-color); font: 400 12px {FONT_FAMILY}; }}",
            f".meta {{ fill: var(--meta-color); font: 400 12px {FONT_FAMILY}; }}",
            (
                ".hero-title { fill: var(--title-color); "
                f"font: 700 28px {FONT_FAMILY}; "
                "}"
            ),
            (
                ".hero-artist { fill: var(--title-color); "
                f"font: 600 16px {FONT_FAMILY}; "
                "}"
            ),
            (
                ".extra-title { fill: var(--title-color); "
                f"font: 600 13px {FONT_FAMILY}; "
                "}"
            ),
            ".panel { fill: var(--panel-bg); }",
            ".panel-stroke { fill: none; stroke: var(--card-border); }",
            ".card-bg { fill: var(--card-bg); }",
            ".card-stroke { fill: none; stroke: var(--card-border); }",
            ".focus-bar { fill: var(--focus); }",
            ".peak-tick { fill: var(--card-border); }",
            ".peak-tick-on { fill: var(--peak); fill-opacity: 0.55; }",
            ".peak-tick-max { fill: var(--peak); }",
            ".streak-fill { fill: var(--streak); }",
            ".streak-empty { fill: var(--card-border); }",
            ".cadence { fill: var(--streak); }",
        )
    )


def _wrap_supplemental_svg(
    *,
    width: int,
    height: int,
    aria_label: str,
    accent: str,
    accent_dark: str,
    body: list[str],
    extra_defs: list[str] | None = None,
) -> str:
    lines = [
        (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
            f'height="{height}" viewBox="0 0 {width} {height}" role="img" '
            f'aria-label="{_svg_text(aria_label)}">'
        ),
        "<defs>",
        "<style>",
        _supplemental_svg_css(accent=accent, accent_dark=accent_dark),
        "</style>",
    ]
    if extra_defs:
        lines.extend(extra_defs)
    lines.extend(
        (
            "</defs>",
            f'<rect class="card-bg" width="{width}" height="{height}" rx="12" />',
            (
                f'<rect class="card-stroke" x="0.5" y="0.5" width="{width - 1}" '
                f'height="{height - 1}" rx="12" stroke-width="1" />'
            ),
            f'<rect width="{width}" height="3" fill="var(--accent)" />',
            *body,
            "</svg>",
        )
    )
    return "\n".join(lines)


def _render_habits_focus_panel(
    repos: tuple[tuple[str, int], ...],
    *,
    x: int,
    y: int,
    width: int,
    height: int,
) -> list[str]:
    lines = [
        f'<g class="habits-focus" transform="translate({x},{y})">',
        f'<rect class="panel" width="{width}" height="{height}" rx="10" />',
        f'<rect class="panel-stroke" width="{width}" height="{height}" rx="10" />',
        '<text class="label" x="16" y="24">Focus</text>',
        '<text class="meta" x="16" y="42">Merged PRs by repo</text>',
    ]
    if not repos:
        lines.extend(
            (
                '<text class="body" x="16" y="88">profile-wide work</text>',
                (
                    '<text class="muted" x="16" y="110">'
                    "No recent merged-PR focus yet</text>"
                ),
                "</g>",
            )
        )
        return lines

    max_count = max(count for _, count in repos)
    row_top = 58
    row_height = 34
    bar_width = width - 32
    for index, (name, count) in enumerate(repos[:3]):
        row_y = row_top + index * row_height
        filled = 8 if max_count <= 0 else max(8, int(bar_width * (count / max_count)))
        lines.extend(
            (
                (
                    f'<text class="body" x="16" y="{row_y}">'
                    f"{_svg_text(_truncate(name, 22))}</text>"
                ),
                (
                    f'<text class="meta" x="{width - 16}" y="{row_y}" '
                    f'text-anchor="end">×{count}</text>'
                ),
                (
                    f'<rect x="16" y="{row_y + 6}" width="{bar_width}" height="6" '
                    'rx="3" fill="var(--card-border)" fill-opacity="0.45" />'
                ),
                (
                    f'<rect class="focus-bar" x="16" y="{row_y + 6}" '
                    f'width="{filled}" height="6" rx="3" />'
                ),
            )
        )
    lines.append("</g>")
    return lines


def _render_habits_peak_panel(
    buckets: list[int],
    peak_hour: str,
    *,
    x: int,
    y: int,
    width: int,
    height: int,
) -> list[str]:
    max_count = max(buckets) if buckets else 0
    peak_index = next(
        (index for index, count in enumerate(buckets) if count == max_count and count),
        None,
    )
    lines = [
        f'<g class="habits-peak" transform="translate({x},{y})">',
        f'<rect class="panel" width="{width}" height="{height}" rx="10" />',
        f'<rect class="panel-stroke" width="{width}" height="{height}" rx="10" />',
        '<text class="label" x="16" y="24">Peak hour</text>',
        '<text class="meta" x="16" y="42">Recent pushes · UTC</text>',
        f'<text class="value" x="16" y="86">{_svg_text(peak_hour)}</text>',
    ]
    chart_x = 16
    chart_width = width - 32
    gap = 3
    bar_width = max(4, int((chart_width - gap * 23) / 24))
    baseline = 150
    for hour, count in enumerate(buckets):
        bar_x = chart_x + hour * (bar_width + gap)
        bar_h = 6 if count <= 0 else max(8, int(44 * (count / max_count)))
        css = "peak-tick"
        if count > 0:
            css = "peak-tick-on"
        if peak_index is not None and hour == peak_index:
            css = "peak-tick-max"
        lines.append(
            f'<rect class="{css}" x="{bar_x}" y="{baseline - bar_h}" '
            f'width="{bar_width}" height="{bar_h}" rx="2" />'
        )
    lines.extend(
        (
            '<text class="meta" x="16" y="166">00</text>',
            (
                f'<text class="meta" x="{width // 2}" y="166" '
                'text-anchor="middle">12</text>'
            ),
            f'<text class="meta" x="{width - 16}" y="166" text-anchor="end">23</text>',
            "</g>",
        )
    )
    return lines


def _render_habits_streaks_panel(
    current: int,
    longest: int,
    *,
    x: int,
    y: int,
    width: int,
    height: int,
) -> list[str]:
    bead_count = 12
    filled = 0 if current <= 0 else min(current, bead_count)
    bead_r = 5
    usable = width - 32
    step = usable / max(bead_count - 1, 1)
    track_width = usable
    current_fill = (
        0
        if current <= 0
        else max(10, int(track_width * (current / max(longest, current, 1))))
    )
    lines = [
        f'<g class="habits-streaks" transform="translate({x},{y})">',
        f'<rect class="panel" width="{width}" height="{height}" rx="10" />',
        f'<rect class="panel-stroke" width="{width}" height="{height}" rx="10" />',
        '<text class="label" x="16" y="24">Streaks</text>',
        f'<text class="value" x="16" y="70">{current}d</text>',
        '<text class="meta" x="16" y="90">current</text>',
    ]
    for index in range(bead_count):
        bead_x = 16 + index * step
        css = "streak-fill" if index < filled else "streak-empty"
        lines.append(
            f'<circle class="{css}" cx="{_svg_num(bead_x)}" cy="112" r="{bead_r}" />'
        )
    if current > bead_count:
        lines.append(
            f'<text class="meta" x="{width - 16}" y="116" text-anchor="end">'
            f"+{current - bead_count}</text>"
        )
    lines.extend(
        (
            f'<rect x="16" y="136" width="{track_width}" height="8" rx="4" '
            'class="streak-empty" fill-opacity="0.55" />',
            f'<rect class="streak-fill" x="16" y="136" width="{current_fill}" '
            'height="8" rx="4" />',
            f'<text class="meta" x="16" y="162">{longest}d longest</text>',
            "</g>",
        )
    )
    return lines


def _render_habits_cadence(
    series: list[int],
    *,
    x: int,
    y: int,
    width: int,
) -> list[str]:
    lines = [
        f'<g class="habits-cadence" transform="translate({x},{y})">',
        '<text class="label" x="0" y="12">Cadence</text>',
    ]
    if not series:
        lines.extend(
            (
                '<text class="muted" x="72" y="12">no recent days</text>',
                "</g>",
            )
        )
        return lines
    max_count = max(series) or 1
    bar_gap = 4
    bar_width = max(4, int((width - (len(series) - 1) * bar_gap) / len(series)))
    for index, count in enumerate(series):
        bar_x = index * (bar_width + bar_gap)
        bar_h = 4 if count <= 0 else max(6, int(18 * (count / max_count)))
        opacity = 0.22 if count <= 0 else 0.35 + 0.65 * (count / max_count)
        lines.append(
            f'<rect class="cadence" x="{bar_x}" y="{38 - bar_h}" width="{bar_width}" '
            f'height="{bar_h}" rx="2" fill-opacity="{opacity:.2f}" />'
        )
    lines.append("</g>")
    return lines


def _render_habits_svg(metrics: dict[str, Any]) -> str:
    stats = _contribution_stats(metrics)
    repos = _focus_repository_counts(metrics, limit=3)
    buckets = _hour_buckets(metrics)
    peak_hour = _peak_commit_hour(metrics)
    cadence = _cadence_series(metrics, days=30)
    width, height = 1200, 312
    panel_y, panel_h, panel_w = 58, 176, 376
    body = [
        (
            f'<text class="title" x="28" y="40">'
            f"{_svg_text(ASSET_SPECS['habits'].title)}</text>"
        ),
        '<text class="kicker" x="1172" y="38" text-anchor="end">'
        "Focus · Peak hour · Streaks</text>",
        *_render_habits_focus_panel(
            repos,
            x=20,
            y=panel_y,
            width=panel_w,
            height=panel_h,
        ),
        *_render_habits_peak_panel(
            buckets,
            peak_hour,
            x=412,
            y=panel_y,
            width=panel_w,
            height=panel_h,
        ),
        *_render_habits_streaks_panel(
            int(stats["current_streak"]),
            int(stats["longest_streak"]),
            x=804,
            y=panel_y,
            width=panel_w,
            height=panel_h,
        ),
        *_render_habits_cadence(cadence, x=28, y=246, width=1144),
    ]
    return _wrap_supplemental_svg(
        width=width,
        height=height,
        aria_label=ASSET_SPECS["habits"].title,
        accent="#8250df",
        accent_dark="#a371f7",
        body=body,
    )


def _render_habits_card(metrics: dict[str, Any]) -> SvgBlock:
    stats = _contribution_stats(metrics)
    focus_repos = (
        ", ".join(_focus_repositories(metrics, limit=3)) or "profile-wide work"
    )
    peak_hour = _peak_commit_hour(metrics)
    card = SvgCard(
        title=ASSET_SPECS["habits"].title,
        kicker="Focus · Peak hour · Streaks",
        lines=(
            f"Focus: {focus_repos}",
            f"Peak hour: {peak_hour} UTC",
            (
                f"Current streak {stats['current_streak']}d · "
                f"longest {stats['longest_streak']}d"
            ),
        ),
        meta=(
            f"Current {stats['current_streak']}d",
            f"Longest {stats['longest_streak']}d",
            f"Peak {peak_hour}",
        ),
        icon="GH",
        badge="Focus",
        accent="#8250df",
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
    # Unused for README emit. GitHub already shows a native activity feed;
    # this helper remains for tests and local inspection only.
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
    # Unused for README emit. Retained because coverage tests still call it.
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
        album = _optional_json_object(
            track.get("album"),
            context=f"Spotify recently played item {item_index} album",
        )
        image_url = ""
        raw_images = album.get("images")
        if raw_images is not None:
            image_url = _best_spotify_image_url(
                _require_json_array(
                    raw_images,
                    context=f"Spotify recently played item {item_index} album images",
                ),
                context=f"Spotify recently played item {item_index} album image",
            )
        tracks.append(
            {
                "name": str(track.get("name") or "").strip() or "Untitled track",
                "artists": artist_names or "Unknown artist",
                "played_at": str(item.get("played_at") or "").strip(),
                "album": str(album.get("name") or "").strip(),
                "image_url": image_url,
            }
        )
    return tracks


def _best_spotify_image_url(images: list[Any], *, context: str) -> str:
    ranked: list[tuple[int, str]] = []
    for image_index, raw_image in enumerate(images):
        image = _require_json_object(
            raw_image,
            context=f"{context} {image_index}",
        )
        url = str(image.get("url") or "").strip()
        if not url:
            continue
        try:
            width = int(image.get("width") or 0)
        except (TypeError, ValueError):
            width = 0
        ranked.append((width, url))
    if not ranked:
        return ""
    ranked.sort(key=lambda item: abs(item[0] - 300) if item[0] else 10_000)
    return ranked[0][1]


def _sniff_image_media_type(payload: bytes, content_type: str) -> str | None:
    if payload.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if payload.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if payload.startswith(b"RIFF") and payload[8:12] == b"WEBP":
        return "image/webp"
    if content_type in {"image/png", "image/jpeg", "image/webp", "image/jpg"}:
        return "image/jpeg" if content_type == "image/jpg" else content_type
    return None


def _fetch_image_data_uri(url: str, *, max_bytes: int = 80_000) -> str | None:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return None
    try:
        payload, content_type = _request_bytes(url, max_bytes=max_bytes)
    except (
        urllib.error.HTTPError,
        urllib.error.URLError,
        TimeoutError,
        OSError,
        RuntimeError,
    ) as exc:
        logger.info("Skipping album artwork from {}: {}", url, exc)
        return None
    media_type = _sniff_image_media_type(payload, content_type)
    if media_type is None or not payload:
        return None
    encoded = base64.b64encode(payload).decode("ascii")
    return f"data:{media_type};base64,{encoded}"


def _with_track_artwork(tracks: list[dict[str, str]]) -> list[dict[str, str]]:
    enriched: list[dict[str, str]] = []
    for track in tracks:
        item = dict(track)
        image_url = item.get("image_url") or ""
        if image_url and not item.get("image_data_uri"):
            data_uri = _fetch_image_data_uri(image_url)
            if data_uri:
                item["image_data_uri"] = data_uri
        enriched.append(item)
    return enriched


def _music_sleeve(
    track: dict[str, str],
    *,
    x: int,
    y: int,
    size: int,
    clip_id: str,
) -> tuple[list[str], list[str]]:
    fill = _label_swatch(track.get("album") or track.get("name") or "track")
    monogram = _truncate(
        "".join(part[0] for part in (track.get("artists") or "S").split()[:2]).upper()
        or "SP",
        2,
    )
    defs = [
        f'<clipPath id="{clip_id}">'
        f'<rect x="{x}" y="{y}" width="{size}" height="{size}" rx="10" />'
        "</clipPath>"
    ]
    body = [
        f'<rect x="{x}" y="{y}" width="{size}" height="{size}" rx="10" fill="{fill}" />'
    ]
    data_uri = track.get("image_data_uri") or ""
    if data_uri:
        body.append(
            f'<image href="{_svg_text(data_uri)}" x="{x}" y="{y}" width="{size}" '
            f'height="{size}" preserveAspectRatio="xMidYMid slice" '
            f'clip-path="url(#{clip_id})" />'
        )
    else:
        mid_x = x + size / 2
        mid_y = y + size / 2 + 6
        body.append(
            f'<text class="hero-artist" x="{mid_x:.0f}" y="{mid_y:.0f}" '
            f'text-anchor="middle" fill="#ffffff">{_svg_text(monogram)}</text>'
        )
    body.append(
        f'<rect x="{x}" y="{y}" width="{size}" height="{size}" rx="10" fill="none" '
        'stroke="var(--accent)" stroke-opacity="0.45" stroke-width="1.5" />'
    )
    return defs, body


def _render_music_extras(
    tracks: list[dict[str, str]],
    *,
    y: int,
) -> tuple[list[str], list[str]]:
    extras = tracks[1:3]
    if not extras:
        return [], []
    defs: list[str] = []
    body: list[str] = [f'<g class="music-extras" transform="translate(28,{y})">']
    tile_w = 564
    for index, track in enumerate(extras):
        tile_x = index * (tile_w + 16)
        clip_id = f"music-extra-{index}"
        sleeve_defs, sleeve_body = _music_sleeve(
            track,
            x=tile_x + 12,
            y=10,
            size=44,
            clip_id=clip_id,
        )
        defs.extend(sleeve_defs)
        album = track.get("album") or ""
        meta = _relative_label(track.get("played_at"))
        if album:
            meta = f"{_truncate(album, 28)} · {meta}"
        extra_artists = _truncate(
            track.get("artists") or "Unknown artist",
            36,
        )
        body.extend(
            (
                (
                    f'<rect class="panel" x="{tile_x}" y="0" '
                    f'width="{tile_w}" height="64" rx="10" />'
                ),
                (
                    f'<rect class="panel-stroke" x="{tile_x}" y="0" width="{tile_w}" '
                    'height="64" rx="10" />'
                ),
                *sleeve_body,
                (
                    f'<text class="extra-title" x="{tile_x + 68}" y="28">'
                    f"{_svg_text(_truncate(track.get('name') or 'Untitled track', 42))}"
                    "</text>"
                ),
                (
                    f'<text class="muted" x="{tile_x + 68}" y="46">'
                    f"{_svg_text(extra_artists)} · {_svg_text(meta)}</text>"
                ),
            )
        )
    body.append("</g>")
    return defs, body


def _render_music_svg(tracks: list[dict[str, str]]) -> str:
    hydrated = _with_track_artwork(tracks[:3])
    extras = hydrated[1:3]
    height = 328 if extras else 236
    defs: list[str] = []
    body = [
        (
            f'<text class="kicker" x="28" y="36">'
            f"{_svg_text(ASSET_SPECS['music'].title)}</text>"
        ),
        '<text class="kicker" x="1172" y="36" text-anchor="end">Spotify</text>',
        '<g class="music-hero">',
    ]
    if not hydrated:
        body.extend(
            (
                '<text class="hero-title" x="28" y="120">'
                "No recent Spotify tracks were available.</text>",
                "</g>",
            )
        )
    else:
        hero = hydrated[0]
        sleeve_defs, sleeve_body = _music_sleeve(
            hero,
            x=28,
            y=56,
            size=132,
            clip_id="music-hero-art",
        )
        defs.extend(sleeve_defs)
        album = hero.get("album") or ""
        played = _relative_label(hero.get("played_at"))
        hero_meta = played if not album else f"{_truncate(album, 48)} · {played}"
        hero_artists = _truncate(hero.get("artists") or "Unknown artist", 44)
        body.extend(
            (
                *sleeve_body,
                (
                    f'<text class="hero-title" x="180" y="104">'
                    f"{_svg_text(_truncate(hero.get('name') or 'Untitled track', 40))}"
                    "</text>"
                ),
                (
                    f'<text class="hero-artist" x="180" y="136">'
                    f"{_svg_text(hero_artists)}</text>"
                ),
                f'<text class="muted" x="180" y="164">{_svg_text(hero_meta)}</text>',
                "</g>",
            )
        )
        extra_defs, extra_body = _render_music_extras(hydrated, y=208)
        defs.extend(extra_defs)
        body.extend(extra_body)
    return _wrap_supplemental_svg(
        width=1200,
        height=height,
        aria_label=ASSET_SPECS["music"].title,
        accent="#1db954",
        accent_dark="#1ed760",
        body=body,
        extra_defs=defs,
    )


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
        badge="Spotify",
        accent="#1db954",
        background_image=(tracks[0].get("image_data_uri") if tracks else None),
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


def _write_supplemental_asset(
    builder: ReadmeSvgAssetBuilder,
    asset_name: str,
    block: SvgBlock,
    svg: str,
) -> None:
    builder.render_and_write(asset_name, block)
    write_raw = getattr(builder, "write_raw", None)
    if callable(write_raw):
        write_raw(asset_name, svg)


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

    _write_supplemental_asset(
        builder,
        ASSET_SPECS["habits"].asset_name,
        _render_habits_card(metrics),
        _render_habits_svg(metrics),
    )
    # GitHub already renders a native activity feed below the profile README.
    _remove_asset_if_present(output_dir, ASSET_SPECS["activity"].asset_name)

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
            enabled=False,
            optional=True,
            title=ASSET_SPECS["activity"].title,
            required_markers=ASSET_SPECS["activity"].required_markers,
            reason="removed-duplicate-github-feed",
        ),
    }

    if spotify_client_id and spotify_client_secret and spotify_refresh_token:
        tracks = _fetch_recent_tracks(
            spotify_client_id,
            spotify_client_secret,
            spotify_refresh_token,
        )
        _write_supplemental_asset(
            builder,
            ASSET_SPECS["music"].asset_name,
            _render_music_card(tracks),
            _render_music_svg(tracks),
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
