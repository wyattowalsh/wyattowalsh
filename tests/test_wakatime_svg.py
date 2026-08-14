"""Tests for the first-party WakaTime SVG card."""

from __future__ import annotations

from datetime import UTC, date, datetime
from pathlib import Path

import pytest

from scripts.wakatime_readme import (
    DEFAULT_WAKATIME_SVG_PATH,
    GitHubShortInfo,
    WakaAllTimeTotal,
    WakaCollection,
    WakaDayTotal,
    WakaStatEntry,
    WakaWeekStats,
    filter_waka_collection,
)
from scripts.wakatime_svg import (
    generate_wakatime_svg,
    main,
    render_wakatime_svg,
    write_wakatime_svg,
)

COMMITTED_WAKATIME_SVG = Path(".github/assets/img/wakatime.svg")
_PRIVATE_AND_LEISURE = (
    "/Users/ww/private.py",
    "secret-client",
    "Spotify",
    "Messages",
    "Games",
    "Entertainment",
    "heartbeat",
    "anmol098",
)


def _entry(name: str, seconds: float, percent: float, text: str) -> WakaStatEntry:
    return WakaStatEntry(name, seconds, percent, text)


def _week() -> WakaWeekStats:
    return WakaWeekStats(
        timezone="America/New_York",
        languages=(
            _entry("Python", 49600, 55.5, "13 hrs 46 mins"),
            _entry("TypeScript", 19200, 21.5, "5 hrs 20 mins"),
            _entry("/Users/ww/private.py", 100, 0.1, "1 mins"),
        ),
        editors=(
            _entry("Cursor", 33840, 60.0, "9 hrs 24 mins"),
            _entry("VS Code", 10000, 20.0, "2 hrs 46 mins"),
            _entry("Spotify", 400, 1.0, "6 mins"),
            _entry("Messages", 200, 0.5, "3 mins"),
        ),
        projects=(
            _entry("wyattowalsh", 37080, 40.0, "10 hrs 18 mins"),
            _entry("secret-client", 8000, 10.0, "2 hrs 13 mins"),
        ),
        operating_systems=(
            _entry("Mac", 150000, 70.0, "41 hrs 40 mins"),
            _entry("iOS", 40000, 20.0, "11 hrs 6 mins"),
            _entry("watchOS", 15140, 10.0, "4 hrs 12 mins"),
        ),
        categories=(
            _entry("Coding", 40000, 70.0, "11 hrs 6 mins"),
            _entry("Debugging", 8000, 15.0, "2 hrs 13 mins"),
            _entry("Games", 400, 1.0, "6 mins"),
            _entry("Entertainment", 200, 0.5, "3 mins"),
        ),
        total_seconds=89400,
        human_readable_total="24 hrs 50 mins",
        human_readable_daily_average="3 hrs 32 mins",
        range_name="last_7_days",
    )


def public_safe_waka_collection() -> WakaCollection:
    """Public-safe fixture used to bake the committed README card."""
    week = WakaWeekStats(
        timezone="America/New_York",
        languages=(
            _entry("Python", 49600, 55.5, "13 hrs 46 mins"),
            _entry("TypeScript", 19200, 21.5, "5 hrs 20 mins"),
            _entry("Rust", 8000, 9.0, "2 hrs 13 mins"),
        ),
        editors=(
            _entry("Cursor", 33840, 60.0, "9 hrs 24 mins"),
            _entry("VS Code", 10000, 20.0, "2 hrs 46 mins"),
            _entry("Xcode", 5000, 10.0, "1 hr 23 mins"),
        ),
        projects=(_entry("wyattowalsh", 37080, 100.0, "10 hrs 18 mins"),),
        operating_systems=(
            _entry("Mac", 150000, 70.0, "41 hrs 40 mins"),
            _entry("iOS", 40000, 20.0, "11 hrs 6 mins"),
            _entry("watchOS", 15140, 10.0, "4 hrs 12 mins"),
        ),
        categories=(
            _entry("Coding", 40000, 70.0, "11 hrs 6 mins"),
            _entry("Debugging", 8000, 15.0, "2 hrs 13 mins"),
        ),
        total_seconds=89400,
        human_readable_total="24 hrs 50 mins",
        human_readable_daily_average="3 hrs 32 mins",
        range_name="last_7_days",
    )
    return WakaCollection(
        week=week,
        year=WakaWeekStats(
            timezone="America/New_York",
            languages=week.languages,
            editors=week.editors,
            projects=week.projects,
            operating_systems=week.operating_systems,
            categories=week.categories,
            total_seconds=3_600_000,
            human_readable_total="1,000 hrs",
            range_name="last_year",
        ),
        all_time=WakaWeekStats(
            timezone="America/New_York",
            languages=(),
            editors=(),
            projects=(),
            operating_systems=(),
            total_seconds=16_200_000,
            human_readable_total="4,500 hrs",
            range_name="all_time",
        ),
        all_time_since_today=WakaAllTimeTotal(
            total_seconds=16_200_000,
            text="4,500 hrs 0 mins",
        ),
        daily=(
            WakaDayTotal(day=date(2026, 8, 8), total_seconds=1800, text="30 mins"),
            WakaDayTotal(day=date(2026, 8, 9), total_seconds=3600, text="1 hr"),
            WakaDayTotal(day=date(2026, 8, 10), total_seconds=7200, text="2 hrs"),
            WakaDayTotal(day=date(2026, 8, 11), total_seconds=900, text="15 mins"),
            WakaDayTotal(
                day=date(2026, 8, 12),
                total_seconds=5400,
                text="1 hr 30 mins",
            ),
            WakaDayTotal(day=date(2026, 8, 13), total_seconds=2400, text="40 mins"),
            WakaDayTotal(
                day=date(2026, 8, 14),
                total_seconds=4800,
                text="1 hr 20 mins",
            ),
        ),
        fetched_ranges=("last_7_days", "last_year", "all_time"),
        public_repo_names=("wyattowalsh",),
    )


def _collection() -> WakaCollection:
    return WakaCollection(
        week=_week(),
        year=WakaWeekStats(
            timezone="America/New_York",
            languages=_week().languages,
            editors=_week().editors,
            projects=_week().projects,
            operating_systems=_week().operating_systems,
            categories=_week().categories,
            total_seconds=3_600_000,
            human_readable_total="1,000 hrs",
            range_name="last_year",
        ),
        all_time=WakaWeekStats(
            timezone="America/New_York",
            languages=(),
            editors=(),
            projects=(),
            operating_systems=(),
            total_seconds=16_200_000,
            human_readable_total="4,500 hrs",
            range_name="all_time",
        ),
        all_time_since_today=WakaAllTimeTotal(
            total_seconds=16_200_000,
            text="4,500 hrs 0 mins",
        ),
        daily=(
            WakaDayTotal(day=date(2026, 8, 1), total_seconds=1200, text="20 mins"),
            WakaDayTotal(day=date(2026, 8, 2), total_seconds=3600, text="1 hr"),
            WakaDayTotal(day=date(2026, 8, 3), total_seconds=0, text="0 mins"),
        ),
        fetched_ranges=("last_7_days", "last_year", "all_time"),
        public_repo_names=("wyattowalsh",),
    )


def test_render_wakatime_svg_includes_public_safe_sections() -> None:
    filtered = filter_waka_collection(
        _collection(),
        public_repo_names=("wyattowalsh",),
        project_allowlist=("wyattowalsh",),
    )
    svg = render_wakatime_svg(
        filtered,
        updated_at=datetime(2026, 8, 14, 12, 0, tzinfo=UTC),
    )

    assert svg.startswith("<svg")
    assert 'role="img"' in svg
    assert "@media (prefers-color-scheme: dark)" in svg
    assert "Coding activity" in svg
    assert "Languages" in svg
    assert "Editors" in svg
    assert "Platforms" in svg
    assert "Categories" in svg
    assert "Python" in svg
    assert "TypeScript" in svg
    assert "Cursor" in svg
    assert "VS Code" in svg
    assert "Mac" in svg
    assert "iOS" in svg
    assert "watchOS" in svg
    assert "Coding" in svg
    assert "Debugging" in svg
    assert "This week" in svg
    assert "Last year" in svg
    assert "All time" in svg
    assert "24 hrs 50 mins" in svg
    assert "1,000 hrs" in svg
    assert "4,500 hrs" in svg
    assert "Coding heatmap" in svg
    assert "Last 14 days" in svg
    assert 'class="hm-0"' in svg or 'class="hm-1"' in svg or 'class="hm-4"' in svg
    assert "2026-08-01" in svg
    assert "wyattowalsh" in svg
    assert "anmol098" not in svg
    assert "secret-client" not in svg
    assert "Spotify" not in svg
    assert "Messages" not in svg
    assert "Games" not in svg
    assert "Entertainment" not in svg
    assert "/Users/ww/private.py" not in svg
    assert "heartbeat" not in svg.lower()
    for banned in _PRIVATE_AND_LEISURE:
        assert banned not in svg


def test_committed_wakatime_svg_exists_and_is_public_safe() -> None:
    """README embeds this path; the committed card must stay public-safe."""
    assert COMMITTED_WAKATIME_SVG == DEFAULT_WAKATIME_SVG_PATH
    assert COMMITTED_WAKATIME_SVG.is_file()
    svg = COMMITTED_WAKATIME_SVG.read_text(encoding="utf-8")
    assert svg.startswith("<svg")
    assert "@media (prefers-color-scheme: dark)" in svg
    assert "Languages" in svg
    assert "Editors" in svg
    assert "Platforms" in svg
    assert "Categories" in svg
    assert "Python" in svg
    assert "Cursor" in svg
    assert "Mac" in svg
    assert "GitHub" in svg
    assert "Coding" in svg
    assert "wyattowalsh" in svg
    assert "This week" in svg
    assert "Last year" in svg
    assert "All time" in svg
    assert "Coding heatmap" in svg
    for banned in _PRIVATE_AND_LEISURE:
        assert banned not in svg
    assert "/Users/" not in svg
    assert "~/" not in svg
    assert "C:\\" not in svg


def test_render_wakatime_svg_omits_heatmap_without_daily_data() -> None:
    collection = WakaCollection(week=_week(), daily=())
    svg = render_wakatime_svg(filter_waka_collection(collection))
    assert "Coding heatmap" not in svg
    assert "Languages" in svg


def test_render_wakatime_svg_includes_github_chips() -> None:
    svg = render_wakatime_svg(
        filter_waka_collection(_collection()),
        github=GitHubShortInfo(
            public_repos=190,
            private_repos=0,
            disk_usage_bytes=None,
            hireable=True,
            contributions_this_year=3703,
            year=2026,
        ),
    )
    assert "GitHub" in svg
    assert "3,703" in svg
    assert "190" in svg
    assert "Open" in svg


def test_write_wakatime_svg_creates_asset(tmp_path: Path) -> None:
    path = tmp_path / "img" / "wakatime.svg"
    written = write_wakatime_svg("<svg>ok</svg>", path)
    assert written == path
    assert path.read_text(encoding="utf-8") == "<svg>ok</svg>\n"


def test_generate_wakatime_svg_uses_collection_without_api(tmp_path: Path) -> None:
    output = tmp_path / "wakatime.svg"
    path = generate_wakatime_svg(
        collection=_collection(),
        output_path=output,
        project_allowlist=("wyattowalsh",),
        include_github=False,
        updated_at=datetime(2026, 8, 14, 15, 0, tzinfo=UTC),
    )
    text = path.read_text(encoding="utf-8")
    assert path == output
    assert "Python" in text
    assert "secret-client" not in text
    assert "prefers-color-scheme: dark" in text


def test_generate_wakatime_svg_collects_when_needed(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("WAKATIME_API_KEY", "key")
    monkeypatch.setattr(
        "scripts.wakatime_svg.collect_wakatime_stats",
        lambda api_key: _collection(),
    )
    output = tmp_path / "wakatime.svg"
    generate_wakatime_svg(
        output_path=output,
        include_github=False,
        project_allowlist=("wyattowalsh",),
    )
    assert "Cursor" in output.read_text(encoding="utf-8")


def test_generate_wakatime_svg_requires_key_without_collection() -> None:
    with pytest.raises(ValueError, match="WAKATIME_API_KEY"):
        generate_wakatime_svg(include_github=False)


def test_main_requires_key_without_allow(monkeypatch) -> None:
    monkeypatch.delenv("WAKATIME_API_KEY", raising=False)
    with pytest.raises(SystemExit):
        main(["--output", "wakatime.svg"])


def test_main_allow_missing_key(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("WAKATIME_API_KEY", raising=False)
    output = tmp_path / "wakatime.svg"
    assert main(["--output", str(output), "--allow-missing-key"]) == 0
    skip = tmp_path / "waka-section.skipped"
    assert skip.is_file()
    assert "WAKATIME_API_KEY missing" in skip.read_text(encoding="utf-8")


def test_main_writes_svg(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("WAKATIME_API_KEY", "key")
    output = tmp_path / "wakatime.svg"
    monkeypatch.setattr(
        "scripts.wakatime_svg.collect_wakatime_stats",
        lambda api_key: _collection(),
    )
    assert (
        main(
            [
                "--output",
                str(output),
                "--no-github",
                "--project-allowlist",
                "wyattowalsh",
            ]
        )
        == 0
    )
    assert "Coding activity" in output.read_text(encoding="utf-8")
