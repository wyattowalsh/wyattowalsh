"""First-party WakaTime README section collector and generator.

Fetches WakaTime (and optionally GitHub) stats, renders markdown for the
``<!--START_SECTION:waka-->`` … ``<!--END_SECTION:waka-->`` zone, and can
write an artifact for finalize to apply — no third-party Actions required.

Public-safe collection never requests heartbeats, durations, or file
entities. Project names are published only when they match a public repo
or an explicit allowlist. Leisure / unprofessional app rows are dropped.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import ssl
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable, Iterable
from dataclasses import dataclass, replace
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any, Final

from .utils import get_logger

logger = get_logger(module=__name__)

WAKATIME_API_BASE: Final[str] = "https://wakatime.com/api/v1"
WAKATIME_STATS_RANGE: Final[str] = "last_7_days"
WAKA_STATS_RANGES: Final[tuple[str, ...]] = (
    "last_7_days",
    "last_year",
    "all_time",
)
GITHUB_API_BASE: Final[str] = "https://api.github.com"
MARKER_START: Final[str] = "<!--START_SECTION:waka-->"
MARKER_END: Final[str] = "<!--END_SECTION:waka-->"
SECTION_RE: Final[re.Pattern[str]] = re.compile(
    rf"(?ms)({re.escape(MARKER_START)})(.*?)({re.escape(MARKER_END)})",
)
TIMESTAMP_FORMAT: Final[str] = "%d/%m/%Y %H:%M:%S UTC"
BAR_WIDTH: Final[int] = 25
DEFAULT_TOP_N: Final[int] = 5
SVG_TOP_N: Final[int] = 8
DEFAULT_ARTIFACT_NAME: Final[str] = "waka-section.md"
SKIP_MARKER_NAME: Final[str] = "waka-section.skipped"
DEFAULT_WAKATIME_SVG_PATH: Final[Path] = Path(".github/assets/img/wakatime.svg")

_OPTIONAL_FETCH_ERRORS: Final[tuple[type[BaseException], ...]] = (
    urllib.error.HTTPError,
    urllib.error.URLError,
    TimeoutError,
    OSError,
    ValueError,
    TypeError,
    json.JSONDecodeError,
)

_FILE_PATH_RE: Final[re.Pattern[str]] = re.compile(
    r"^(?:~(?=$|[/\\])|[/\\]|[A-Za-z]:[\\/])"
    r"|(?:^|[/\\])(?:Users|home|var|tmp|private|opt)[/\\]"
    r"|[/\\][^/\\]+\.[A-Za-z0-9]{1,8}$"
)
_REPO_SLUG_RE: Final[re.Pattern[str]] = re.compile(
    r"^[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?$"
)
_OWNER_REPO_RE: Final[re.Pattern[str]] = re.compile(
    r"^[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?/"
    r"[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?$"
)
_TOKEN_RE: Final[re.Pattern[str]] = re.compile(r"[a-z0-9+]+")

LEISURE_CATEGORY_DENYLIST: Final[frozenset[str]] = frozenset(
    {
        "dating",
        "entertainment",
        "fitness",
        "game",
        "games",
        "gaming",
        "health",
        "imessage",
        "messages",
        "messaging",
        "music",
        "photo",
        "photos",
        "shop",
        "shopping",
        "sms",
        "social",
        "social media",
        "social networking",
        "wellness",
    }
)
LEISURE_NAME_TOKENS: Final[frozenset[str]] = frozenset(
    {
        "dating",
        "entertainment",
        "fitness",
        "game",
        "games",
        "gaming",
        "health",
        "imessage",
        "messages",
        "messaging",
        "music",
        "photo",
        "photos",
        "shopping",
        "sms",
        "social",
        "tinder",
        "wellness",
    }
)
LEISURE_APP_DENYLIST: Final[frozenset[str]] = frozenset(
    {
        "amazon",
        "amazon music",
        "apple music",
        "books",
        "bumble",
        "disney+",
        "facebook",
        "facetime",
        "fitness",
        "health",
        "hinge",
        "hulu",
        "imessage",
        "instagram",
        "messages",
        "music",
        "netflix",
        "news",
        "photos",
        "podcasts",
        "signal",
        "sms",
        "spotify",
        "telegram",
        "tiktok",
        "tinder",
        "twitch",
        "twitter",
        "whatsapp",
        "youtube",
        "youtube music",
    }
)
PROFESSIONAL_EDITORS: Final[frozenset[str]] = frozenset(
    {
        "alacritty",
        "android studio",
        "antigravity",
        "appcode",
        "atom",
        "bbedit",
        "brackets",
        "claude code",
        "clion",
        "code",
        "code oss",
        "codex",
        "copilot",
        "cursor",
        "datagrip",
        "eclipse",
        "emacs",
        "fleet",
        "gedit",
        "ghostty",
        "goland",
        "helix",
        "hyper",
        "idle",
        "intellij",
        "intellij idea",
        "iterm",
        "iterm2",
        "jupyter",
        "jupyterlab",
        "kakoune",
        "kate",
        "kitty",
        "lapce",
        "lite xl",
        "matlab",
        "micro",
        "neovim",
        "netbeans",
        "nova",
        "notepad++",
        "nvim",
        "oni",
        "opencode",
        "phpstorm",
        "playgrounds",
        "pycharm",
        "rider",
        "rstudio",
        "rubymine",
        "spyder",
        "sublime",
        "sublime text",
        "terminal",
        "textmate",
        "thonny",
        "tmux",
        "trae",
        "vim",
        "visual studio",
        "visual studio code",
        "void",
        "vs code",
        "vscode",
        "vscodium",
        "warp",
        "webstorm",
        "wezterm",
        "windsurf",
        "xcode",
        "xcode playgrounds",
        "zed",
    }
)
UNKNOWN_PROJECT_NAMES: Final[frozenset[str]] = frozenset(
    {
        "",
        "<<unnamed>>",
        "no project",
        "none",
        "unknown",
        "unknown project",
    }
)


@dataclass(frozen=True)
class WakaStatEntry:
    """A single named WakaTime aggregate (language, editor, …)."""

    name: str
    total_seconds: float
    percent: float
    text: str


@dataclass(frozen=True)
class WakaWeekStats:
    """Parsed WakaTime stats used for README / SVG rendering."""

    timezone: str
    languages: tuple[WakaStatEntry, ...]
    editors: tuple[WakaStatEntry, ...]
    projects: tuple[WakaStatEntry, ...]
    operating_systems: tuple[WakaStatEntry, ...]
    categories: tuple[WakaStatEntry, ...] = ()
    total_seconds: float = 0.0
    human_readable_total: str = ""
    human_readable_daily_average: str = ""
    range_name: str = WAKATIME_STATS_RANGE
    is_up_to_date: bool = True


@dataclass(frozen=True)
class WakaDayTotal:
    """One day's coding total for the public heatmap (no entities)."""

    day: date
    total_seconds: float
    text: str = ""


@dataclass(frozen=True)
class WakaAllTimeTotal:
    """Account-lifetime total from ``all_time_since_today``."""

    total_seconds: float
    text: str
    start_date: str | None = None
    is_up_to_date: bool = True


@dataclass(frozen=True)
class WakaCollection:
    """Multi-range public-safe WakaTime snapshot."""

    week: WakaWeekStats
    year: WakaWeekStats | None = None
    all_time: WakaWeekStats | None = None
    all_time_since_today: WakaAllTimeTotal | None = None
    daily: tuple[WakaDayTotal, ...] = ()
    fetched_ranges: tuple[str, ...] = ()
    public_repo_names: tuple[str, ...] = ()


@dataclass(frozen=True)
class GitHubShortInfo:
    """Optional short GitHub profile facts for the Waka section."""

    public_repos: int
    private_repos: int
    disk_usage_bytes: int | None
    hireable: bool | None
    contributions_this_year: int | None
    year: int | None


def _wakatime_auth_header(api_key: str) -> dict[str, str]:
    """Build Basic-auth header for a WakaTime API key."""
    token = base64.b64encode(f"{api_key}:".encode()).decode()
    return {
        "Authorization": f"Basic {token}",
        "Accept": "application/json",
        "User-Agent": "wyattowalsh-profile-wakatime",
    }


def _request_json(
    url: str,
    *,
    headers: dict[str, str] | None = None,
    method: str = "GET",
) -> Any:
    """GET JSON from an HTTPS endpoint with a hard timeout."""
    request = urllib.request.Request(
        url,
        headers=headers or {},
        method=method,
    )
    context = ssl.create_default_context()
    with urllib.request.urlopen(request, context=context, timeout=30) as response:
        return json.loads(response.read().decode())


def _normalize_label(name: str) -> str:
    return name.strip().casefold()


def _folded_words(name: str) -> str:
    return re.sub(r"[^a-z0-9+]+", " ", _normalize_label(name)).strip()


def _name_tokens(name: str) -> frozenset[str]:
    return frozenset(_TOKEN_RE.findall(_normalize_label(name)))


def looks_like_file_path(name: str) -> bool:
    """Return True when *name* looks like a filesystem path or file entity."""
    stripped = name.strip()
    if not stripped:
        return False
    if _FILE_PATH_RE.search(stripped):
        return True
    if "\\" in stripped:
        return True
    if "/" in stripped and re.search(r"\.[A-Za-z0-9]{1,8}$", stripped):
        return True
    return False


def looks_like_heartbeat_entity(name: str) -> bool:
    """Return True for heartbeat / duration entity labels."""
    folded = _normalize_label(name)
    return "heartbeat" in folded or folded in {"duration", "durations", "entity"}


def looks_like_repo_name(name: str) -> bool:
    """Return True when *name* has GitHub owner/repo or slug shape."""
    stripped = name.strip()
    if not stripped or looks_like_file_path(stripped):
        return False
    if _OWNER_REPO_RE.fullmatch(stripped):
        return True
    return bool(
        _REPO_SLUG_RE.fullmatch(stripped) and any(char.isalpha() for char in stripped)
    )


def is_leisure_or_unprofessional(name: str) -> bool:
    """Return True for leisure / social / health / shopping / entertainment rows."""
    folded = _folded_words(name)
    if not folded:
        return False
    if folded in LEISURE_CATEGORY_DENYLIST or folded in LEISURE_APP_DENYLIST:
        return True
    tokens = _name_tokens(name)
    if tokens & LEISURE_NAME_TOKENS:
        return True
    return any(
        folded == app or folded.startswith(f"{app} ") or folded.endswith(f" {app}")
        for app in LEISURE_APP_DENYLIST
    )


def is_professional_editor(name: str) -> bool:
    """Return True when *name* is a known professional editor or terminal."""
    folded = _folded_words(name)
    if not folded or is_leisure_or_unprofessional(name):
        return False
    if folded in PROFESSIONAL_EDITORS:
        return True
    return any(
        folded == editor or folded.startswith(f"{editor} ")
        for editor in PROFESSIONAL_EDITORS
    )


def is_publishable_project(
    name: str,
    *,
    public_repo_names: Iterable[str] = (),
    project_allowlist: Iterable[str] = (),
) -> bool:
    """Keep a project name only when it is a known public repo or allowlisted."""
    stripped = name.strip()
    if not stripped:
        return False
    if looks_like_file_path(stripped) or looks_like_heartbeat_entity(stripped):
        return False
    if _normalize_label(stripped) in UNKNOWN_PROJECT_NAMES:
        return False
    if is_leisure_or_unprofessional(stripped):
        return False
    if not looks_like_repo_name(stripped):
        return False
    allowed = {
        _normalize_label(item)
        for item in (*public_repo_names, *project_allowlist)
        if str(item).strip()
    }
    if not allowed:
        return False
    candidate = _normalize_label(stripped)
    slug = candidate.rsplit("/", 1)[-1]
    if candidate in allowed or slug in allowed:
        return True
    return any(
        item == candidate
        or item.endswith(f"/{candidate}")
        or item.endswith(f"/{slug}")
        or candidate.endswith(f"/{item}")
        for item in allowed
    )


def _filter_named_entries(
    entries: tuple[WakaStatEntry, ...],
    *,
    keep: Callable[[str], bool],
) -> tuple[WakaStatEntry, ...]:
    return tuple(entry for entry in entries if keep(entry.name))


def filter_waka_stats(
    stats: WakaWeekStats,
    *,
    public_repo_names: Iterable[str] = (),
    project_allowlist: Iterable[str] = (),
    top_n: int | None = None,
) -> WakaWeekStats:
    """Drop private, path-like, heartbeat, and leisure rows from *stats*."""

    def keep_language(name: str) -> bool:
        return not looks_like_file_path(name) and not looks_like_heartbeat_entity(name)

    def keep_category(name: str) -> bool:
        return keep_language(name) and not is_leisure_or_unprofessional(name)

    def keep_project(name: str) -> bool:
        return is_publishable_project(
            name,
            public_repo_names=public_repo_names,
            project_allowlist=project_allowlist,
        )

    filtered = replace(
        stats,
        languages=_filter_named_entries(stats.languages, keep=keep_language),
        editors=_filter_named_entries(stats.editors, keep=is_professional_editor),
        projects=_filter_named_entries(stats.projects, keep=keep_project),
        categories=_filter_named_entries(stats.categories, keep=keep_category),
        operating_systems=_filter_named_entries(
            stats.operating_systems,
            keep=keep_language,
        ),
    )
    if top_n is None:
        return filtered
    return replace(
        filtered,
        languages=filtered.languages[:top_n],
        editors=filtered.editors[:top_n],
        projects=filtered.projects[:top_n],
        categories=filtered.categories[:top_n],
        operating_systems=filtered.operating_systems[:top_n],
    )


def filter_waka_collection(
    collection: WakaCollection,
    *,
    public_repo_names: Iterable[str] = (),
    project_allowlist: Iterable[str] = (),
    top_n: int | None = SVG_TOP_N,
) -> WakaCollection:
    """Apply the public-safe filter to every range in *collection*."""
    names = tuple(
        {
            *collection.public_repo_names,
            *(item.strip() for item in public_repo_names if str(item).strip()),
        }
    )
    return replace(
        collection,
        week=filter_waka_stats(
            collection.week,
            public_repo_names=names,
            project_allowlist=project_allowlist,
            top_n=top_n,
        ),
        year=(
            None
            if collection.year is None
            else filter_waka_stats(
                collection.year,
                public_repo_names=names,
                project_allowlist=project_allowlist,
                top_n=top_n,
            )
        ),
        all_time=(
            None
            if collection.all_time is None
            else filter_waka_stats(
                collection.all_time,
                public_repo_names=names,
                project_allowlist=project_allowlist,
                top_n=top_n,
            )
        ),
        public_repo_names=names,
    )


def fetch_wakatime_stats(
    api_key: str,
    *,
    range_name: str = WAKATIME_STATS_RANGE,
) -> dict[str, Any]:
    """Fetch raw WakaTime stats JSON for ``range_name``."""
    path = f"/users/current/stats/{urllib.parse.quote(range_name, safe='')}"
    url = f"{WAKATIME_API_BASE}{path}"
    logger.info("Fetching WakaTime stats range={range}", range=range_name)
    payload = _request_json(url, headers=_wakatime_auth_header(api_key))
    if not isinstance(payload, dict):
        raise ValueError("WakaTime stats response was not a JSON object")
    return payload


def fetch_all_time_since_today(api_key: str) -> dict[str, Any]:
    """Fetch ``/users/current/all_time_since_today`` (lifetime total)."""
    url = f"{WAKATIME_API_BASE}/users/current/all_time_since_today"
    logger.info("Fetching WakaTime all_time_since_today")
    payload = _request_json(url, headers=_wakatime_auth_header(api_key))
    if not isinstance(payload, dict):
        raise ValueError("WakaTime all_time_since_today was not a JSON object")
    return payload


def fetch_wakatime_insights(
    api_key: str,
    *,
    insight_type: str = "days",
    range_name: str = "last_year",
) -> dict[str, Any]:
    """Fetch a WakaTime insights payload (daily heatmap source)."""
    path = (
        f"/users/current/insights/"
        f"{urllib.parse.quote(insight_type, safe='')}/"
        f"{urllib.parse.quote(range_name, safe='')}"
    )
    url = f"{WAKATIME_API_BASE}{path}"
    logger.info(
        "Fetching WakaTime insights type={insight} range={range}",
        insight=insight_type,
        range=range_name,
    )
    payload = _request_json(url, headers=_wakatime_auth_header(api_key))
    if not isinstance(payload, dict):
        raise ValueError("WakaTime insights response was not a JSON object")
    return payload


def fetch_wakatime_summaries(
    api_key: str,
    *,
    start: str | None = None,
    end: str | None = None,
    range_label: str | None = None,
) -> dict[str, Any]:
    """Fetch daily summaries. Only grand totals are consumed (no entities)."""
    params: dict[str, str] = {}
    if range_label:
        params["range"] = range_label
    else:
        if not start or not end:
            raise ValueError("summaries require range_label or start and end")
        params["start"] = start
        params["end"] = end
    query = urllib.parse.urlencode(params)
    url = f"{WAKATIME_API_BASE}/users/current/summaries?{query}"
    logger.info("Fetching WakaTime summaries query={query}", query=query)
    payload = _request_json(url, headers=_wakatime_auth_header(api_key))
    if not isinstance(payload, dict):
        raise ValueError("WakaTime summaries response was not a JSON object")
    return payload


def _parse_iso_date(value: Any) -> date | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return date.fromisoformat(text[:10])
    except ValueError:
        return None


def _parse_daily_item(item: Any) -> WakaDayTotal | None:
    if not isinstance(item, dict):
        return None
    day = _parse_iso_date(item.get("date")) or _parse_iso_date(item.get("day"))
    range_info = item.get("range")
    if day is None and isinstance(range_info, dict):
        day = _parse_iso_date(range_info.get("date"))
    seconds_raw = item.get("total_seconds")
    if seconds_raw is None:
        seconds_raw = item.get("total")
    if seconds_raw is None:
        seconds_raw = item.get("seconds")
    text = str(item.get("text") or "").strip()
    grand = item.get("grand_total")
    if seconds_raw is None and isinstance(grand, dict):
        seconds_raw = grand.get("total_seconds")
        text = str(grand.get("text") or text).strip()
    if day is None:
        return None
    try:
        seconds = float(seconds_raw or 0.0)
    except (TypeError, ValueError):
        seconds = 0.0
    return WakaDayTotal(day=day, total_seconds=max(0.0, seconds), text=text)


def parse_daily_totals_from_insights(
    payload: dict[str, Any],
) -> tuple[WakaDayTotal, ...]:
    """Parse ``insights/days`` into day totals. Ignores entity payloads."""
    data = payload.get("data")
    raw: Any = None
    if isinstance(data, dict):
        raw = data.get("days")
    elif isinstance(data, list):
        raw = data
    days: list[WakaDayTotal] = []
    if isinstance(raw, list):
        for item in raw:
            parsed = _parse_daily_item(item)
            if parsed is not None:
                days.append(parsed)
    elif isinstance(raw, dict):
        for key, value in raw.items():
            if isinstance(value, dict):
                parsed = _parse_daily_item({"date": key, **value})
            else:
                parsed = _parse_daily_item({"date": key, "total_seconds": value})
            if parsed is not None:
                days.append(parsed)
    days.sort(key=lambda item: item.day)
    return tuple(days)


def parse_daily_totals_from_summaries(
    payload: dict[str, Any],
) -> tuple[WakaDayTotal, ...]:
    """Parse summaries into day totals. Never reads ``entities`` / files."""
    data = payload.get("data")
    if not isinstance(data, list):
        return ()
    days: list[WakaDayTotal] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        # Explicitly ignore file/heartbeat-bearing keys.
        grand = item.get("grand_total")
        range_info = item.get("range")
        day = None
        if isinstance(range_info, dict):
            day = _parse_iso_date(range_info.get("date"))
        seconds = 0.0
        text = ""
        if isinstance(grand, dict):
            try:
                seconds = float(grand.get("total_seconds") or 0.0)
            except (TypeError, ValueError):
                seconds = 0.0
            text = str(grand.get("text") or "").strip()
        if day is None:
            continue
        days.append(WakaDayTotal(day=day, total_seconds=max(0.0, seconds), text=text))
    days.sort(key=lambda item: item.day)
    return tuple(days)


def parse_all_time_since_today(payload: dict[str, Any]) -> WakaAllTimeTotal:
    """Normalize ``all_time_since_today`` into a lifetime total."""
    data = payload.get("data")
    if not isinstance(data, dict):
        raise ValueError("WakaTime all_time_since_today missing data object")
    try:
        seconds = float(data.get("total_seconds") or 0.0)
    except (TypeError, ValueError):
        seconds = 0.0
    text = str(data.get("text") or "").strip() or _format_duration(seconds)
    range_info = data.get("range") if isinstance(data.get("range"), dict) else {}
    start_date = None
    if isinstance(range_info, dict):
        start_date = str(range_info.get("start_date") or "").strip() or None
    return WakaAllTimeTotal(
        total_seconds=max(0.0, seconds),
        text=text,
        start_date=start_date,
        is_up_to_date=bool(data.get("is_up_to_date", True)),
    )


def fetch_wakatime_daily_totals(
    api_key: str,
    *,
    range_name: str = "last_year",
) -> tuple[WakaDayTotal, ...]:
    """Load daily totals for a heatmap, preferring insights then summaries."""
    try:
        payload = fetch_wakatime_insights(
            api_key,
            insight_type="days",
            range_name=range_name,
        )
        days = parse_daily_totals_from_insights(payload)
        if days:
            return days
    except _OPTIONAL_FETCH_ERRORS as exc:
        logger.warning("WakaTime insights days skipped: {exc}", exc=exc)

    for label in ("Last 30 Days", "Last 7 Days"):
        try:
            payload = fetch_wakatime_summaries(api_key, range_label=label)
            days = parse_daily_totals_from_summaries(payload)
            if days:
                return days
        except _OPTIONAL_FETCH_ERRORS as exc:
            logger.warning(
                "WakaTime summaries {label} skipped: {exc}",
                label=label,
                exc=exc,
            )
    return ()


def _parse_entries(
    raw: Any, *, limit: int = DEFAULT_TOP_N
) -> tuple[WakaStatEntry, ...]:
    if not isinstance(raw, list):
        return ()
    entries: list[WakaStatEntry] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "").strip()
        if not name:
            continue
        total_seconds = float(item.get("total_seconds") or 0.0)
        percent = float(item.get("percent") or 0.0)
        text = str(item.get("text") or "").strip()
        if not text:
            text = _format_duration(total_seconds)
        entries.append(
            WakaStatEntry(
                name=name,
                total_seconds=total_seconds,
                percent=percent,
                text=text,
            )
        )
    entries.sort(key=lambda entry: entry.total_seconds, reverse=True)
    if limit > 0:
        return tuple(entries[:limit])
    return tuple(entries)


def parse_wakatime_stats(
    payload: dict[str, Any],
    *,
    range_name: str = WAKATIME_STATS_RANGE,
    limit: int = DEFAULT_TOP_N,
) -> WakaWeekStats:
    """Normalize a WakaTime stats API payload into typed stats."""
    data = payload.get("data")
    if not isinstance(data, dict):
        raise ValueError("WakaTime stats payload missing data object")
    timezone = str(data.get("timezone") or "UTC").strip() or "UTC"
    try:
        total_seconds = float(
            data.get("total_seconds_including_other_language")
            or data.get("total_seconds")
            or 0.0
        )
    except (TypeError, ValueError):
        total_seconds = 0.0
    human_total = str(
        data.get("human_readable_total_including_other_language")
        or data.get("human_readable_total")
        or ""
    ).strip()
    if not human_total and total_seconds:
        human_total = _format_duration(total_seconds)
    daily_average = str(
        data.get("human_readable_daily_average_including_other_language")
        or data.get("human_readable_daily_average")
        or ""
    ).strip()
    return WakaWeekStats(
        timezone=timezone,
        languages=_parse_entries(data.get("languages"), limit=limit),
        editors=_parse_entries(data.get("editors"), limit=limit),
        projects=_parse_entries(data.get("projects"), limit=limit),
        operating_systems=_parse_entries(data.get("operating_systems"), limit=limit),
        categories=_parse_entries(data.get("categories"), limit=limit),
        total_seconds=max(0.0, total_seconds),
        human_readable_total=human_total,
        human_readable_daily_average=daily_average,
        range_name=str(data.get("range") or range_name),
        is_up_to_date=bool(data.get("is_up_to_date", True)),
    )


def collect_wakatime_stats(
    api_key: str,
    *,
    ranges: tuple[str, ...] = WAKA_STATS_RANGES,
    include_daily: bool = True,
    include_all_time_since_today: bool = True,
    entry_limit: int = SVG_TOP_N,
) -> WakaCollection:
    """Fetch last_7_days plus yearly / all-time ranges the API documents."""
    parsed: dict[str, WakaWeekStats] = {}
    fetched: list[str] = []
    required = ranges[0] if ranges else WAKATIME_STATS_RANGE
    for range_name in ranges:
        try:
            payload = fetch_wakatime_stats(api_key, range_name=range_name)
            parsed[range_name] = parse_wakatime_stats(
                payload,
                range_name=range_name,
                limit=entry_limit,
            )
            fetched.append(range_name)
        except _OPTIONAL_FETCH_ERRORS as exc:
            if range_name == required:
                raise
            logger.warning(
                "WakaTime range {range} skipped: {exc}",
                range=range_name,
                exc=exc,
            )

    week = parsed.get(WAKATIME_STATS_RANGE) or parsed.get(required)
    if week is None:
        raise ValueError("WakaTime last_7_days stats are required")

    all_time_total: WakaAllTimeTotal | None = None
    if include_all_time_since_today:
        try:
            all_time_total = parse_all_time_since_today(
                fetch_all_time_since_today(api_key)
            )
        except _OPTIONAL_FETCH_ERRORS as exc:
            logger.warning("WakaTime all_time_since_today skipped: {exc}", exc=exc)

    daily: tuple[WakaDayTotal, ...] = ()
    if include_daily:
        daily = fetch_wakatime_daily_totals(api_key, range_name="last_year")

    return WakaCollection(
        week=week,
        year=parsed.get("last_year"),
        all_time=parsed.get("all_time"),
        all_time_since_today=all_time_total,
        daily=daily,
        fetched_ranges=tuple(fetched),
    )


def fetch_public_repo_names(
    token: str,
    *,
    login: str | None = None,
) -> frozenset[str]:
    """Return public GitHub repository names and ``owner/repo`` slugs."""
    from ._github_http import _paginate_rest

    if login:
        quoted = urllib.parse.quote(login)
        url = f"{GITHUB_API_BASE}/users/{quoted}/repos?type=public&per_page=100"
    else:
        url = (
            f"{GITHUB_API_BASE}/user/repos?visibility=public"
            "&per_page=100&affiliation=owner"
        )
    pages = _paginate_rest(url, token, max_pages=10)
    names: set[str] = set()
    for repo in pages:
        if not isinstance(repo, dict) or repo.get("private"):
            continue
        name = str(repo.get("name") or "").strip()
        full_name = str(repo.get("full_name") or "").strip()
        if name:
            names.add(name)
        if full_name:
            names.add(full_name)
    return frozenset(names)


def _fetch_contributions_this_year(token: str, login: str) -> tuple[int, int] | None:
    """Return (total, year) via GitHub GraphQL contribution calendar."""
    from ._github_http import _graphql

    year = datetime.now(UTC).year
    query = """
    query($login: String!, $from: DateTime!, $to: DateTime!) {
      user(login: $login) {
        contributionsCollection(from: $from, to: $to) {
          contributionCalendar { totalContributions }
        }
      }
    }
    """
    payload = _graphql(
        query,
        token,
        variables={
            "login": login,
            "from": f"{year}-01-01T00:00:00Z",
            "to": f"{year}-12-31T23:59:59Z",
        },
    )
    user = (payload.get("data") or {}).get("user") or {}
    calendar = (user.get("contributionsCollection") or {}).get(
        "contributionCalendar"
    ) or {}
    total = calendar.get("totalContributions")
    if total is None:
        return None
    return int(total), year


def fetch_github_short_info(
    token: str,
    *,
    login: str | None = None,
) -> GitHubShortInfo:
    """Fetch optional GitHub short-info fields for the Waka section."""
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "wyattowalsh-profile-wakatime",
    }
    user_url = (
        f"{GITHUB_API_BASE}/users/{urllib.parse.quote(login)}"
        if login
        else f"{GITHUB_API_BASE}/user"
    )
    user = _request_json(user_url, headers=headers)
    if not isinstance(user, dict):
        raise ValueError("GitHub user response was not a JSON object")

    username = str(user.get("login") or login or "").strip()
    contributions: int | None = None
    year: int | None = None
    if username:
        try:
            result = _fetch_contributions_this_year(token, username)
            if result is not None:
                contributions, year = result
        except (
            urllib.error.URLError,
            TimeoutError,
            ValueError,
            TypeError,
            KeyError,
        ) as exc:
            logger.warning("GitHub contributions lookup skipped: {exc}", exc=exc)

    private_repos = user.get("total_private_repos")
    if private_repos is None:
        private_repos = user.get("owned_private_repos")
    return GitHubShortInfo(
        public_repos=int(user.get("public_repos") or 0),
        private_repos=int(private_repos or 0),
        disk_usage_bytes=(
            int(user["disk_usage"]) if user.get("disk_usage") is not None else None
        ),
        hireable=user.get("hireable") if "hireable" in user else None,
        contributions_this_year=contributions,
        year=year,
    )


def _format_duration(total_seconds: float) -> str:
    total = max(0, int(total_seconds))
    hours, rem = divmod(total, 3600)
    minutes = rem // 60
    if hours and minutes:
        return f"{hours} hrs {minutes} mins"
    if hours:
        return f"{hours} hrs"
    if minutes:
        return f"{minutes} mins"
    return "0 mins"


def _format_bytes(num_bytes: int) -> str:
    value = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if value < 1024.0 or unit == "TB":
            if unit == "B":
                return f"{int(value)} {unit}"
            return f"{value:.1f} {unit}"
        value /= 1024.0
    return f"{num_bytes} B"


def _progress_bar(percent: float, *, width: int = BAR_WIDTH) -> str:
    filled = max(0, min(width, round((percent / 100.0) * width)))
    return f"{'█' * filled}{'░' * (width - filled)}"


def _format_stat_rows(entries: tuple[WakaStatEntry, ...]) -> str:
    if not entries:
        return "No Activity Tracked This Week\n"
    name_width = max(len(entry.name) for entry in entries)
    text_width = max(len(entry.text) for entry in entries)
    lines: list[str] = []
    for entry in entries:
        bar = _progress_bar(entry.percent)
        lines.append(
            f"{entry.name:<{name_width}}  "
            f"{entry.text:<{text_width}}  "
            f"{bar}   {entry.percent:g}% "
        )
    return "\n".join(lines) + "\n"


def render_waka_section(
    week: WakaWeekStats,
    *,
    github: GitHubShortInfo | None = None,
    updated_at: datetime | None = None,
    year: WakaWeekStats | None = None,
    all_time: WakaWeekStats | None = None,
    all_time_since_today: WakaAllTimeTotal | None = None,
) -> str:
    """Render the inner markdown for the Waka README markers (no markers)."""
    stamp = (updated_at or datetime.now(UTC)).astimezone(UTC)
    parts: list[str] = []

    if github is not None:
        parts.append("**🐱 My Github Data** \n")
        if github.contributions_this_year is not None and github.year is not None:
            contrib = f"{github.contributions_this_year:,}"
            parts.append(f"> 🏆 {contrib} Contributions in the Year {github.year}")
            parts.append(" > ")
        if github.disk_usage_bytes is not None:
            parts.append(
                f"> 📦 {_format_bytes(github.disk_usage_bytes)} Used in Github's Storage "  # noqa: E501
            )
            parts.append(" > ")
        if github.hireable is True:
            parts.append("> 💼 Opted to Hire")
            parts.append(" > ")
        elif github.hireable is False:
            parts.append("> 🚫 Not Opted to Hire")
            parts.append(" > ")
        public_label = (
            "Public Repository" if github.public_repos == 1 else "Public Repositories"
        )
        private_label = (
            "Private Repository"
            if github.private_repos == 1
            else "Private Repositories"
        )
        parts.append(f"> 📜 {github.public_repos} {public_label} ")
        parts.append(" > ")
        parts.append(f"> 🔑 {github.private_repos} {private_label}  ")
        parts.append(" > ")
        parts.append("")

    parts.append("📊 **This Week I Spent My Time On** \n")
    parts.append("")
    parts.append("```text")
    parts.append(f"⌚︎ Time Zone: {week.timezone}")
    if week.human_readable_total:
        parts.append(f"⏳ This Week: {week.human_readable_total}")
    if year is not None and year.human_readable_total:
        parts.append(f"📅 Last Year: {year.human_readable_total}")
    lifetime = ""
    if all_time is not None and all_time.human_readable_total:
        lifetime = all_time.human_readable_total
    elif all_time_since_today is not None:
        lifetime = all_time_since_today.text
    if lifetime:
        parts.append(f"∞ All Time: {lifetime}")
    parts.append("")
    parts.append("💬 Programming Languages: ")
    parts.append(_format_stat_rows(week.languages).rstrip("\n"))
    parts.append("")
    parts.append("🔥 Editors: ")
    parts.append(_format_stat_rows(week.editors).rstrip("\n"))
    if week.categories:
        parts.append("")
        parts.append("🧠 Categories: ")
        parts.append(_format_stat_rows(week.categories).rstrip("\n"))
    parts.append("")
    parts.append("🐱‍💻 Projects: ")
    parts.append(_format_stat_rows(week.projects).rstrip("\n"))
    parts.append("")
    parts.append("💻 Operating System: ")
    parts.append(_format_stat_rows(week.operating_systems).rstrip("\n"))
    parts.append("")
    parts.append("```")
    parts.append("")
    parts.append("")
    parts.append(f" Last Updated on {stamp.strftime(TIMESTAMP_FORMAT)}")
    return "\n".join(parts) + "\n"


def apply_waka_section(readme_path: Path, section_body: str) -> bool:
    """Replace the Waka marker zone in ``readme_path``. Returns True if changed."""
    content = readme_path.read_text(encoding="utf-8")
    match = SECTION_RE.search(content)
    if match is None:
        raise ValueError(
            f"Waka markers not found in {readme_path}: {MARKER_START} … {MARKER_END}"
        )
    body = section_body.strip("\n")
    replacement = f"{match.group(1)}\n{body}\n{match.group(3)}"
    updated = content[: match.start()] + replacement + content[match.end() :]
    if updated == content:
        logger.info("Waka section already up to date in {path}", path=readme_path)
        return False
    readme_path.write_text(updated, encoding="utf-8")
    logger.info("Applied Waka section to {path}", path=readme_path)
    return True


def write_waka_artifact(section_body: str, output_path: Path) -> Path:
    """Write the generated section body to an artifact path."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        section_body if section_body.endswith("\n") else f"{section_body}\n",
        encoding="utf-8",
    )
    logger.info("Wrote Waka artifact to {path}", path=output_path)
    return output_path


def write_skip_artifact(output_dir: Path, reason: str) -> Path:
    """Write a skip marker when generation is intentionally skipped."""
    output_dir.mkdir(parents=True, exist_ok=True)
    skip_path = output_dir / SKIP_MARKER_NAME
    skip_path.write_text(f"{reason.strip()}\n", encoding="utf-8")
    logger.info("Wrote Waka skip marker to {path}", path=skip_path)
    return skip_path


def _resolve_public_repo_names(
    *,
    token: str,
    github_login: str | None,
    public_repo_names: Iterable[str],
    include_github: bool,
) -> tuple[str, ...]:
    names = {item.strip() for item in public_repo_names if str(item).strip()}
    if include_github and token:
        try:
            names.update(fetch_public_repo_names(token, login=github_login))
        except _OPTIONAL_FETCH_ERRORS as exc:
            logger.warning("Public repo name lookup skipped: {exc}", exc=exc)
    return tuple(sorted(names))


def generate_waka_section(
    *,
    api_key: str | None = None,
    github_token: str | None = None,
    github_login: str | None = None,
    include_github: bool = True,
    public_repo_names: Iterable[str] = (),
    project_allowlist: Iterable[str] = (),
) -> str:
    """Collect stats and return rendered Waka README section body."""
    key = (api_key or os.environ.get("WAKATIME_API_KEY") or "").strip()
    if not key:
        raise ValueError("WAKATIME_API_KEY is required to generate the Waka section")

    collection = collect_wakatime_stats(
        key,
        include_daily=False,
        include_all_time_since_today=False,
        entry_limit=DEFAULT_TOP_N,
    )
    token = (github_token or os.environ.get("GITHUB_TOKEN") or "").strip()
    names = _resolve_public_repo_names(
        token=token,
        github_login=github_login,
        public_repo_names=public_repo_names,
        include_github=include_github,
    )
    filtered = filter_waka_collection(
        replace(collection, public_repo_names=names),
        public_repo_names=names,
        project_allowlist=project_allowlist,
        top_n=DEFAULT_TOP_N,
    )

    github_info: GitHubShortInfo | None = None
    if include_github and token:
        try:
            github_info = fetch_github_short_info(token, login=github_login)
        except (urllib.error.URLError, TimeoutError, ValueError) as exc:
            logger.warning("Skipping GitHub short info: {exc}", exc=exc)

    return render_waka_section(
        filtered.week,
        github=github_info,
        year=filtered.year,
        all_time=filtered.all_time,
        all_time_since_today=filtered.all_time_since_today,
    )


def apply_waka_artifact_to_readme(
    artifact_path: Path,
    readme_path: Path,
) -> bool:
    """Apply a generated artifact file to README markers if present/non-empty."""
    if not artifact_path.is_file():
        logger.info(
            "No Waka artifact at {path}; leaving README markers unchanged",
            path=artifact_path,
        )
        return False
    body = artifact_path.read_text(encoding="utf-8").strip()
    if not body:
        logger.info("Waka artifact empty; leaving README markers unchanged")
        return False
    return apply_waka_section(readme_path, body)


def _parse_allowlist_arg(raw: str | None) -> tuple[str, ...]:
    if not raw:
        return ()
    return tuple(part.strip() for part in raw.split(",") if part.strip())


def main(argv: list[str] | None = None) -> int:
    """CLI entry for generate / apply flows used by CI."""
    parser = argparse.ArgumentParser(
        description="First-party WakaTime README section generator",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    generate = sub.add_parser(
        "generate", help="Fetch WakaTime stats and write artifact"
    )
    generate.add_argument(
        "--output-dir",
        type=Path,
        default=Path("."),
        help="Directory for waka-section.md artifact",
    )
    generate.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Explicit artifact path (defaults to OUTPUT_DIR/waka-section.md)",
    )
    generate.add_argument(
        "--svg-output",
        type=Path,
        default=None,
        help="Optional path for the first-party wakatime.svg card",
    )
    generate.add_argument(
        "--github-login",
        default=None,
        help="Optional GitHub login for short-info enrichment",
    )
    generate.add_argument(
        "--no-github",
        action="store_true",
        help="Skip optional GitHub short-info enrichment",
    )
    generate.add_argument(
        "--project-allowlist",
        default="",
        help="Comma-separated public project names that may appear",
    )
    generate.add_argument(
        "--allow-missing-key",
        action="store_true",
        help="Exit 0 and write skip marker when WAKATIME_API_KEY is absent",
    )

    apply = sub.add_parser("apply", help="Apply artifact into README waka markers")
    apply.add_argument(
        "--artifact",
        type=Path,
        required=True,
        help="Path to waka-section.md artifact",
    )
    apply.add_argument(
        "--readme",
        type=Path,
        default=Path("README.md"),
        help="README path containing waka markers",
    )

    args = parser.parse_args(argv)

    if args.command == "generate":
        api_key = (os.environ.get("WAKATIME_API_KEY") or "").strip()
        output_dir: Path = args.output_dir
        output_path: Path = args.output or (output_dir / DEFAULT_ARTIFACT_NAME)
        if not api_key:
            if args.allow_missing_key:
                write_skip_artifact(
                    output_dir if args.output is None else output_path.parent,
                    "WAKATIME_API_KEY missing; skipped first-party Waka generation",
                )
                return 0
            raise SystemExit(
                "WAKATIME_API_KEY is required (or pass --allow-missing-key)"
            )
        allowlist = _parse_allowlist_arg(args.project_allowlist)
        body = generate_waka_section(
            api_key=api_key,
            github_login=args.github_login,
            include_github=not args.no_github,
            project_allowlist=allowlist,
        )
        write_waka_artifact(body, output_path)
        if args.svg_output is not None:
            from .wakatime_svg import generate_wakatime_svg

            generate_wakatime_svg(
                api_key=api_key,
                output_path=args.svg_output,
                github_login=args.github_login,
                include_github=not args.no_github,
                project_allowlist=allowlist,
            )
        return 0

    if args.command == "apply":
        changed = apply_waka_artifact_to_readme(args.artifact, args.readme)
        logger.info("Waka apply changed={changed}", changed=changed)
        return 0

    raise SystemExit(f"Unknown command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
