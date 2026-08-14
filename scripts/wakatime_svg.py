"""First-party WakaTime SVG card renderer.

Writes ``.github/assets/img/wakatime.svg`` with languages, professional
editors, platforms, coding categories, week/year/all-time totals, and a
daily heatmap when data is available. Dark mode uses
``@media (prefers-color-scheme: dark)``. Does not use anmol098.
"""

from __future__ import annotations

import argparse
import os
import urllib.error
from collections.abc import Iterable
from dataclasses import replace
from datetime import UTC, date, datetime, timedelta
from html import escape
from pathlib import Path
from typing import Final

from .utils import get_logger
from .wakatime_readme import (
    DEFAULT_WAKATIME_SVG_PATH,
    GitHubShortInfo,
    WakaCollection,
    WakaDayTotal,
    WakaStatEntry,
    _parse_allowlist_arg,
    _resolve_public_repo_names,
    collect_wakatime_stats,
    fetch_github_short_info,
    filter_waka_collection,
    write_skip_artifact,
)

logger = get_logger(module=__name__)

WIDTH: Final[int] = 1200
PADDING: Final[int] = 28
INNER_PAD: Final[int] = 24
CARD_RX: Final[int] = 10
FONT_FAMILY: Final[str] = (
    "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans',"
    " Helvetica, Arial, sans-serif"
)
LANGUAGE_COLORS: Final[dict[str, str]] = {
    "Python": "#3572A5",
    "JavaScript": "#f1e05a",
    "TypeScript": "#3178c6",
    "Rust": "#dea584",
    "Go": "#00ADD8",
    "Java": "#b07219",
    "C": "#555555",
    "C++": "#f34b7d",
    "C#": "#178600",
    "Ruby": "#701516",
    "PHP": "#4F5D95",
    "Swift": "#F05138",
    "Kotlin": "#A97BFF",
    "Shell": "#89e051",
    "HTML": "#e34c26",
    "CSS": "#563d7c",
    "Markdown": "#083fa1",
    "JSON": "#292929",
    "YAML": "#cb171e",
}
ACCENT_FALLBACK: Final[tuple[str, ...]] = (
    "#0969da",
    "#1f883d",
    "#8250df",
    "#bf3989",
    "#d1242f",
    "#9a6700",
    "#1b7c83",
    "#cf222e",
)
CELL: Final[int] = 11
CELL_GAP: Final[int] = 3


def _esc(value: str) -> str:
    return escape(value, quote=True)


def _language_color(name: str, index: int) -> str:
    return LANGUAGE_COLORS.get(name, ACCENT_FALLBACK[index % len(ACCENT_FALLBACK)])


def _css() -> str:
    return "\n".join(
        [
            ":root {",
            "  --canvas-bg: #ffffff;",
            "  --card-bg: #ffffff;",
            "  --card-border: #d0d7de;",
            "  --title-color: #1f2328;",
            "  --text-color: #656d76;",
            "  --meta-color: #656d76;",
            "  --accent: #0969da;",
            "  --bar-track: #eaeef2;",
            "  --hm-0: #ebedf0;",
            "  --hm-1: #9be9a8;",
            "  --hm-2: #40c463;",
            "  --hm-3: #30a14e;",
            "  --hm-4: #216e39;",
            "}",
            "@media (prefers-color-scheme: dark) { :root {",
            "  --canvas-bg: #0d1117;",
            "  --card-bg: #0d1117;",
            "  --card-border: #30363d;",
            "  --title-color: #e6edf3;",
            "  --text-color: #8b949e;",
            "  --meta-color: #8b949e;",
            "  --accent: #58a6ff;",
            "  --bar-track: #21262d;",
            "  --hm-0: #161b22;",
            "  --hm-1: #0e4429;",
            "  --hm-2: #006d32;",
            "  --hm-3: #26a641;",
            "  --hm-4: #39d353;",
            "}}",
            ".rc-bg { fill: var(--card-bg); }",
            ".rc-border { stroke: var(--card-border); }",
            f".card-title {{ fill: var(--title-color);"
            f" font: 700 18px {FONT_FAMILY}; }}",
            f".card-kicker {{ fill: var(--meta-color); font: 700 11px {FONT_FAMILY};"
            " letter-spacing: 0.08em; text-transform: uppercase; }",
            f".card-line {{ fill: var(--text-color); font: 400 13px {FONT_FAMILY}; }}",
            f".card-meta {{ fill: var(--meta-color); font: 400 12px {FONT_FAMILY}; }}",
            f".stat-name {{ fill: var(--title-color); font: 600 12px {FONT_FAMILY}; }}",
            f".stat-time {{ fill: var(--meta-color); font: 400 11px {FONT_FAMILY}; }}",
            f".total-label {{ fill: var(--meta-color); font: 600 11px {FONT_FAMILY};"
            " letter-spacing: 0.04em; text-transform: uppercase; }",
            f".total-value {{ fill: var(--title-color);"
            f" font: 700 16px {FONT_FAMILY}; }}",
            f".gh-chip {{ fill: var(--title-color);"
            f" font: 700 13px {FONT_FAMILY}; }}",
            ".bar-track { fill: var(--bar-track); }",
            ".day-bar { fill: var(--accent); }",
            ".hm-0 { fill: var(--hm-0); }",
            ".hm-1 { fill: var(--hm-1); }",
            ".hm-2 { fill: var(--hm-2); }",
            ".hm-3 { fill: var(--hm-3); }",
            ".hm-4 { fill: var(--hm-4); }",
        ]
    )


def _section_heading(label: str, x: float, y: float) -> str:
    return (
        f'<text class="card-kicker" x="{x:.1f}" y="{y:.1f}">'
        f"{_esc(label)}</text>"
    )


def _stat_rows(
    entries: tuple[WakaStatEntry, ...],
    *,
    x: float,
    y: float,
    width: float,
    empty: str,
) -> tuple[list[str], float]:
    lines: list[str] = []
    cursor = y
    if not entries:
        lines.append(
            f'<text class="card-line" x="{x:.1f}" y="{cursor:.1f}">'
            f"{_esc(empty)}</text>"
        )
        return lines, cursor + 22.0
    bar_x = x + 118
    bar_w = max(80.0, width - 200)
    for index, entry in enumerate(entries):
        color = _language_color(entry.name, index)
        pct = max(0.0, min(100.0, entry.percent))
        fill_w = bar_w * (pct / 100.0)
        name = entry.name if len(entry.name) <= 16 else f"{entry.name[:15]}…"
        lines.append(
            f'<text class="stat-name" x="{x:.1f}" y="{cursor:.1f}">'
            f"{_esc(name)}</text>"
        )
        track_y = cursor - 9
        lines.append(
            f'<rect class="bar-track" x="{bar_x:.1f}" y="{track_y:.1f}" '
            f'width="{bar_w:.1f}" height="8" rx="4" />'
        )
        if fill_w > 0:
            lines.append(
                f'<rect x="{bar_x:.1f}" y="{track_y:.1f}" '
                f'width="{fill_w:.1f}" height="8" rx="4" fill="{color}" />'
            )
        lines.append(
            f'<text class="stat-time" x="{bar_x + bar_w + 8:.1f}" '
            f'y="{cursor:.1f}">{_esc(entry.text)}</text>'
        )
        cursor += 22.0
    return lines, cursor


def _heatmap_level(seconds: float, peak: float) -> int:
    if seconds <= 0 or peak <= 0:
        return 0
    ratio = seconds / peak
    if ratio < 0.25:
        return 1
    if ratio < 0.5:
        return 2
    if ratio < 0.75:
        return 3
    return 4


def _sunday_on_or_before(day: date) -> date:
    return day - timedelta(days=(day.weekday() + 1) % 7)


def _render_heatmap(
    daily: tuple[WakaDayTotal, ...],
    *,
    x: float,
    y: float,
    width: float,
) -> tuple[list[str], float]:
    if not daily:
        return [], y
    by_day = {item.day: item for item in daily}
    start = _sunday_on_or_before(min(by_day))
    end = max(by_day)
    peak = max((item.total_seconds for item in daily), default=0.0)
    week_count = max(1, ((end - start).days // 7) + 1)
    step = CELL + CELL_GAP
    max_weeks = max(1, int((width - 28) // step))
    if week_count > max_weeks:
        start = _sunday_on_or_before(end - timedelta(days=7 * max_weeks - 1))
        week_count = max_weeks
    lines = [_section_heading("Coding heatmap", x, y)]
    grid_y = y + 14
    weekday_labels = ("S", "M", "T", "W", "T", "F", "S")
    for row, label in enumerate(weekday_labels):
        if row % 2:
            continue
        lines.append(
            f'<text class="card-meta" x="{x:.1f}" '
            f'y="{grid_y + row * step + 9:.1f}">{label}</text>'
        )
    grid_x = x + 16
    cursor = start
    col = 0
    while cursor <= end and col < week_count:
        row = (cursor.weekday() + 1) % 7
        item = by_day.get(cursor)
        seconds = item.total_seconds if item is not None else 0.0
        level = _heatmap_level(seconds, peak)
        title = cursor.isoformat()
        if item is not None and item.text:
            title = f"{title}: {item.text}"
        elif seconds:
            title = f"{title}: {int(seconds)}s"
        cx = grid_x + col * step
        cy = grid_y + row * step
        lines.append(
            f'<rect class="hm-{level}" x="{cx}" y="{cy}" width="{CELL}" '
            f'height="{CELL}" rx="2"><title>{_esc(title)}</title></rect>'
        )
        cursor += timedelta(days=1)
        if row == 6:
            col += 1
    height = 7 * step
    return lines, grid_y + height + 8


def _duration_label(total_seconds: float) -> str:
    total = max(0, int(total_seconds))
    hours, rem = divmod(total, 3600)
    minutes = rem // 60
    if hours and minutes:
        return f"{hours}h {minutes}m"
    if hours:
        return f"{hours}h"
    if minutes:
        return f"{minutes}m"
    return "0m"


def _totals(collection: WakaCollection) -> tuple[tuple[str, str], ...]:
    week_text = collection.week.human_readable_total or (
        _duration_label(collection.week.total_seconds)
        if collection.week.total_seconds
        else "—"
    )
    year_text = "—"
    if collection.year is not None:
        year_text = collection.year.human_readable_total or _duration_label(
            collection.year.total_seconds
        )
    all_text = "—"
    if collection.all_time is not None and (
        collection.all_time.human_readable_total or collection.all_time.total_seconds
    ):
        all_text = collection.all_time.human_readable_total or _duration_label(
            collection.all_time.total_seconds
        )
    elif collection.all_time_since_today is not None:
        all_text = collection.all_time_since_today.text
    return (
        ("This week", week_text or "—"),
        ("Last year", year_text or "—"),
        ("All time", all_text or "—"),
    )


def _github_chips(github: GitHubShortInfo | None) -> tuple[tuple[str, str], ...]:
    if github is None:
        return ()
    chips: list[tuple[str, str]] = []
    if github.contributions_this_year is not None and github.year is not None:
        chips.append(
            (f"{github.year} contribs", f"{github.contributions_this_year:,}")
        )
    chips.append(("Public repos", str(github.public_repos)))
    chips.append(("Private repos", str(github.private_repos)))
    if github.hireable is True:
        chips.append(("Hiring", "Open"))
    elif github.hireable is False:
        chips.append(("Hiring", "Closed"))
    return tuple(chips)


def _daily_bars(
    daily: tuple[WakaDayTotal, ...],
    *,
    x: float,
    y: float,
    width: float,
) -> tuple[list[str], float]:
    if not daily:
        return [], y
    recent = daily[-14:]
    peak = max((item.total_seconds for item in recent), default=0.0)
    lines = [_section_heading("Last 14 days", x, y)]
    bar_gap = 6.0
    bar_w = max(8.0, (width - bar_gap * (len(recent) - 1)) / len(recent))
    base = y + 86
    for index, item in enumerate(recent):
        bx = x + index * (bar_w + bar_gap)
        ratio = 0.0 if peak <= 0 else item.total_seconds / peak
        bar_h = 6.0 if item.total_seconds <= 0 else max(8.0, 56.0 * ratio)
        lines.append(
            f'<rect class="day-bar" x="{bx:.1f}" y="{base - bar_h:.1f}" '
            f'width="{bar_w:.1f}" height="{bar_h:.1f}" rx="3">'
            f"<title>{_esc(item.day.isoformat())}: {_esc(item.text)}</title>"
            "</rect>"
        )
    avg = sum(item.total_seconds for item in recent) / max(1, len(recent))
    lines.append(
        f'<text class="card-meta" x="{x:.1f}" y="{base + 18:.1f}">'
        f"avg {_esc(_duration_label(avg))}/day</text>"
    )
    return lines, base + 28


def render_wakatime_svg(
    collection: WakaCollection,
    *,
    updated_at: datetime | None = None,
    github: GitHubShortInfo | None = None,
) -> str:
    """Render a public-safe WakaTime card (no anmol098, no file paths)."""
    stamp = (updated_at or datetime.now(UTC)).astimezone(UTC)
    week = collection.week
    inner_w = WIDTH - (PADDING * 2)
    content_w = inner_w - (INNER_PAD * 2)
    col_w = (content_w - 28) / 2
    left_x = float(PADDING + INNER_PAD)
    right_x = left_x + col_w + 28

    totals = list(_totals(collection))
    if week.human_readable_daily_average:
        totals.append(("Daily avg", week.human_readable_daily_average))
    y = float(PADDING + 22)
    parts: list[str] = []
    parts.append(_section_heading("WakaTime", left_x, y))
    y += 22
    parts.append(
        f'<text class="card-title" x="{left_x:.1f}" y="{y:.1f}">'
        "Coding activity</text>"
    )
    y += 16
    parts.append(
        f'<text class="card-meta" x="{left_x:.1f}" y="{y:.1f}">'
        f"{_esc(week.timezone)} · public-safe stats</text>"
    )
    y += 28
    chip_w = content_w / max(1, len(totals))
    for index, (label, value) in enumerate(totals):
        cx = left_x + index * chip_w
        parts.append(
            f'<text class="total-label" x="{cx:.1f}" y="{y:.1f}">'
            f"{_esc(label)}</text>"
        )
        parts.append(
            f'<text class="total-value" x="{cx:.1f}" y="{y + 20:.1f}">'
            f"{_esc(value)}</text>"
        )
    y += 48
    github_chips = _github_chips(github)
    if github_chips:
        parts.append(_section_heading("GitHub", left_x, y))
        y += 18
        gh_w = content_w / len(github_chips)
        for index, (label, value) in enumerate(github_chips):
            cx = left_x + index * gh_w
            parts.append(
                f'<text class="total-label" x="{cx:.1f}" y="{y:.1f}">'
                f"{_esc(label)}</text>"
            )
            parts.append(
                f'<text class="gh-chip" x="{cx:.1f}" y="{y + 18:.1f}">'
                f"{_esc(value)}</text>"
            )
        y += 40

    lang_lines, lang_bottom = _stat_rows(
        week.languages,
        x=left_x,
        y=y + 18,
        width=col_w,
        empty="No languages this week",
    )
    editor_lines, editor_bottom = _stat_rows(
        week.editors,
        x=right_x,
        y=y + 18,
        width=col_w,
        empty="No professional editors this week",
    )
    parts.append(_section_heading("Languages", left_x, y))
    parts.append(_section_heading("Editors", right_x, y))
    parts.extend(lang_lines)
    parts.extend(editor_lines)
    y = max(lang_bottom, editor_bottom) + 16

    os_lines, os_bottom = _stat_rows(
        week.operating_systems,
        x=left_x,
        y=y + 18,
        width=col_w,
        empty="No platforms this week",
    )
    cat_lines, cat_bottom = _stat_rows(
        week.categories,
        x=right_x,
        y=y + 18,
        width=col_w,
        empty="No coding categories this week",
    )
    parts.append(_section_heading("Platforms", left_x, y))
    parts.append(_section_heading("Categories", right_x, y))
    parts.extend(os_lines)
    parts.extend(cat_lines)
    y = max(os_bottom, cat_bottom) + 12

    if week.projects:
        proj_lines, proj_bottom = _stat_rows(
            week.projects,
            x=left_x,
            y=y + 18,
            width=content_w,
            empty="No public projects this week",
        )
        parts.append(_section_heading("Public projects", left_x, y))
        parts.extend(proj_lines)
        y = proj_bottom + 12

    day_lines, day_bottom = _daily_bars(
        collection.daily,
        x=left_x,
        y=y,
        width=content_w,
    )
    if day_lines:
        parts.extend(day_lines)
        y = day_bottom + 10

    heat_lines, heat_bottom = _render_heatmap(
        collection.daily,
        x=left_x,
        y=y,
        width=content_w,
    )
    if heat_lines:
        parts.extend(heat_lines)
        y = heat_bottom

    y += 8
    parts.append(
        f'<text class="card-meta" x="{left_x:.1f}" y="{y:.1f}">'
        f"Updated {stamp.strftime('%Y-%m-%d %H:%M UTC')}"
        "</text>"
    )
    card_h = int(y - PADDING + INNER_PAD + 8)
    height = card_h + (PADDING * 2)

    svg = [
        (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" '
            f'height="{height}" viewBox="0 0 {WIDTH} {height}" role="img" '
            'aria-label="WakaTime coding activity">'
        ),
        "<defs>",
        "<style>",
        _css(),
        "</style>",
        "</defs>",
        f'<g class="card" transform="translate({PADDING},{PADDING})">',
        (
            f'<rect class="rc-bg" width="{inner_w}" height="{card_h}" '
            f'rx="{CARD_RX}" />'
        ),
        (
            f'<rect class="rc-border" x="0.5" y="0.5" width="{inner_w - 1}" '
            f'height="{card_h - 1}" rx="{CARD_RX}" fill="none" '
            'stroke-width="1" />'
        ),
        (
            f'<rect x="0" y="0" width="{inner_w}" height="3" '
            'fill="var(--accent)" '
            'clip-path="inset(0 round 10px 10px 0 0)" />'
        ),
        "</g>",
        *parts,
        "</svg>",
    ]
    return "\n".join(svg) + "\n"


def write_wakatime_svg(
    svg: str,
    output_path: Path | None = None,
) -> Path:
    """Write *svg* to ``.github/assets/img/wakatime.svg`` by default."""
    path = output_path or DEFAULT_WAKATIME_SVG_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    text = svg if svg.endswith("\n") else f"{svg}\n"
    path.write_text(text, encoding="utf-8")
    logger.info("Wrote WakaTime SVG to {path}", path=path)
    return path


def generate_wakatime_svg(
    *,
    api_key: str | None = None,
    output_path: Path | None = None,
    public_repo_names: Iterable[str] = (),
    project_allowlist: Iterable[str] = (),
    github_token: str | None = None,
    github_login: str | None = None,
    include_github: bool = True,
    updated_at: datetime | None = None,
    collection: WakaCollection | None = None,
) -> Path:
    """Collect public-safe WakaTime stats and write the SVG card."""
    key = (api_key or os.environ.get("WAKATIME_API_KEY") or "").strip()
    snapshot = collection
    if snapshot is None:
        if not key:
            raise ValueError(
                "WAKATIME_API_KEY is required to generate the WakaTime SVG"
            )
        snapshot = collect_wakatime_stats(key)
    token = (github_token or os.environ.get("GITHUB_TOKEN") or "").strip()
    names = _resolve_public_repo_names(
        token=token,
        github_login=github_login,
        public_repo_names=public_repo_names,
        include_github=include_github,
    )
    filtered = filter_waka_collection(
        replace(snapshot, public_repo_names=names),
        public_repo_names=names,
        project_allowlist=project_allowlist,
    )
    github_info: GitHubShortInfo | None = None
    if include_github and token:
        try:
            github_info = fetch_github_short_info(token, login=github_login)
        except (
            urllib.error.URLError,
            TimeoutError,
            ValueError,
            TypeError,
            OSError,
        ) as exc:
            logger.warning("Skipping GitHub short info for Waka SVG: {exc}", exc=exc)
    svg = render_wakatime_svg(
        filtered,
        updated_at=updated_at,
        github=github_info,
    )
    return write_wakatime_svg(svg, output_path)


def main(argv: list[str] | None = None) -> int:
    """CLI entry that writes the first-party WakaTime SVG card."""
    parser = argparse.ArgumentParser(
        description="First-party WakaTime SVG generator",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_WAKATIME_SVG_PATH,
        help="SVG output path",
    )
    parser.add_argument(
        "--project-allowlist",
        default="",
        help="Comma-separated public project names that may appear",
    )
    parser.add_argument(
        "--github-login",
        default=None,
        help="Optional GitHub login used to resolve public repo names",
    )
    parser.add_argument(
        "--no-github",
        action="store_true",
        help="Skip GitHub public-repo lookup",
    )
    parser.add_argument(
        "--allow-missing-key",
        action="store_true",
        help="Exit 0 when WAKATIME_API_KEY is absent",
    )
    args = parser.parse_args(argv)
    api_key = (os.environ.get("WAKATIME_API_KEY") or "").strip()
    if not api_key:
        if args.allow_missing_key:
            write_skip_artifact(
                args.output.parent,
                "WAKATIME_API_KEY missing; skipped first-party Waka SVG",
            )
            return 0
        raise SystemExit("WAKATIME_API_KEY is required (or pass --allow-missing-key)")
    generate_wakatime_svg(
        api_key=api_key,
        output_path=args.output,
        project_allowlist=_parse_allowlist_arg(args.project_allowlist),
        github_login=args.github_login,
        include_github=not args.no_github,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
