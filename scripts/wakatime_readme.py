"""First-party WakaTime README section collector and generator.

Fetches WakaTime (and optionally GitHub) stats, renders markdown for the
``<!--START_SECTION:waka-->`` … ``<!--END_SECTION:waka-->`` zone, and can
write an artifact for finalize to apply — no third-party Actions required.
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
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Final

from .utils import get_logger

logger = get_logger(module=__name__)

WAKATIME_API_BASE: Final[str] = "https://wakatime.com/api/v1"
WAKATIME_STATS_RANGE: Final[str] = "last_7_days"
GITHUB_API_BASE: Final[str] = "https://api.github.com"
MARKER_START: Final[str] = "<!--START_SECTION:waka-->"
MARKER_END: Final[str] = "<!--END_SECTION:waka-->"
SECTION_RE: Final[re.Pattern[str]] = re.compile(
    rf"(?ms)({re.escape(MARKER_START)})(.*?)({re.escape(MARKER_END)})",
)
TIMESTAMP_FORMAT: Final[str] = "%d/%m/%Y %H:%M:%S UTC"
BAR_WIDTH: Final[int] = 25
DEFAULT_TOP_N: Final[int] = 5
DEFAULT_ARTIFACT_NAME: Final[str] = "waka-section.md"
SKIP_MARKER_NAME: Final[str] = "waka-section.skipped"


@dataclass(frozen=True)
class WakaStatEntry:
    """A single named WakaTime aggregate (language, editor, …)."""

    name: str
    total_seconds: float
    percent: float
    text: str


@dataclass(frozen=True)
class WakaWeekStats:
    """Parsed last-7-days WakaTime stats used for README rendering."""

    timezone: str
    languages: tuple[WakaStatEntry, ...]
    editors: tuple[WakaStatEntry, ...]
    projects: tuple[WakaStatEntry, ...]
    operating_systems: tuple[WakaStatEntry, ...]


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
        if len(entries) >= limit:
            break
    return tuple(entries)


def parse_wakatime_stats(payload: dict[str, Any]) -> WakaWeekStats:
    """Normalize a WakaTime stats API payload into typed week stats."""
    data = payload.get("data")
    if not isinstance(data, dict):
        raise ValueError("WakaTime stats payload missing data object")
    timezone = str(data.get("timezone") or "UTC").strip() or "UTC"
    return WakaWeekStats(
        timezone=timezone,
        languages=_parse_entries(data.get("languages")),
        editors=_parse_entries(data.get("editors")),
        projects=_parse_entries(data.get("projects")),
        operating_systems=_parse_entries(data.get("operating_systems")),
    )


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
    parts.append("")
    parts.append("💬 Programming Languages: ")
    parts.append(_format_stat_rows(week.languages).rstrip("\n"))
    parts.append("")
    parts.append("🔥 Editors: ")
    parts.append(_format_stat_rows(week.editors).rstrip("\n"))
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


def generate_waka_section(
    *,
    api_key: str | None = None,
    github_token: str | None = None,
    github_login: str | None = None,
    include_github: bool = True,
) -> str:
    """Collect stats and return rendered Waka README section body."""
    key = (api_key or os.environ.get("WAKATIME_API_KEY") or "").strip()
    if not key:
        raise ValueError("WAKATIME_API_KEY is required to generate the Waka section")

    payload = fetch_wakatime_stats(key)
    week = parse_wakatime_stats(payload)

    github_info: GitHubShortInfo | None = None
    token = (github_token or os.environ.get("GITHUB_TOKEN") or "").strip()
    if include_github and token:
        try:
            github_info = fetch_github_short_info(token, login=github_login)
        except (urllib.error.URLError, TimeoutError, ValueError) as exc:
            logger.warning("Skipping GitHub short info: {exc}", exc=exc)

    return render_waka_section(week, github=github_info)


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
        body = generate_waka_section(
            api_key=api_key,
            github_login=args.github_login,
            include_github=not args.no_github,
        )
        write_waka_artifact(body, output_path)
        return 0

    if args.command == "apply":
        changed = apply_waka_artifact_to_readme(args.artifact, args.readme)
        logger.info("Waka apply changed={changed}", changed=changed)
        return 0

    raise SystemExit(f"Unknown command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
