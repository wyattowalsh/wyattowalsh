"""Tests for first-party WakaTime README section generation."""

from __future__ import annotations

from datetime import UTC, date, datetime
from pathlib import Path
from textwrap import dedent
from typing import Any

import pytest

from scripts.wakatime_readme import (
    DEFAULT_WAKATIME_SVG_PATH,
    MARKER_END,
    MARKER_START,
    WAKA_STATS_RANGES,
    WAKA_SVG_POINTER,
    GitHubShortInfo,
    WakaDayTotal,
    WakaStatEntry,
    WakaWeekStats,
    apply_waka_artifact_to_readme,
    apply_waka_section,
    apply_wakatime_svg,
    collect_wakatime_stats,
    fetch_public_repo_names,
    fetch_wakatime_daily_totals,
    filter_waka_stats,
    generate_waka_section,
    is_leisure_or_unprofessional,
    is_professional_editor,
    is_publishable_project,
    looks_like_file_path,
    looks_like_heartbeat_entity,
    main,
    parse_all_time_since_today,
    parse_daily_totals_from_insights,
    parse_daily_totals_from_summaries,
    parse_wakatime_stats,
    render_waka_section,
    write_skip_artifact,
    write_waka_artifact,
)


def _sample_waka_payload() -> dict[str, Any]:
    return {
        "data": {
            "timezone": "America/New_York",
            "languages": [
                {
                    "name": "Python",
                    "total_seconds": 49600,
                    "percent": 55.5,
                    "text": "13 hrs 46 mins",
                },
                {
                    "name": "TypeScript",
                    "total_seconds": 19200,
                    "percent": 21.5,
                    "text": "5 hrs 20 mins",
                },
            ],
            "editors": [
                {
                    "name": "VS Code",
                    "total_seconds": 33840,
                    "percent": 60.0,
                    "text": "9 hrs 24 mins",
                }
            ],
            "projects": [
                {
                    "name": "wyattowalsh",
                    "total_seconds": 37080,
                    "percent": 40.0,
                    "text": "10 hrs 18 mins",
                }
            ],
            "operating_systems": [
                {
                    "name": "Mac",
                    "total_seconds": 205140,
                    "percent": 100.0,
                    "text": "56 hrs 59 mins",
                }
            ],
            "categories": [
                {
                    "name": "Coding",
                    "total_seconds": 40000,
                    "percent": 80.0,
                    "text": "11 hrs 6 mins",
                }
            ],
        }
    }


def test_parse_wakatime_stats_extracts_top_entries() -> None:
    week = parse_wakatime_stats(_sample_waka_payload())
    assert week.timezone == "America/New_York"
    assert week.languages[0].name == "Python"
    assert week.editors[0].name == "VS Code"
    assert week.projects[0].name == "wyattowalsh"
    assert week.operating_systems[0].percent == 100.0
    assert week.categories[0].name == "Coding"


def test_render_waka_section_is_svg_pointer_not_text_dump() -> None:
    week = parse_wakatime_stats(_sample_waka_payload())
    github = GitHubShortInfo(
        public_repos=170,
        private_repos=92,
        disk_usage_bytes=10_384_384,
        hireable=True,
        contributions_this_year=1800,
        year=2026,
    )
    rendered = render_waka_section(
        week,
        github=github,
        updated_at=datetime(2026, 7, 31, 12, 0, 0, tzinfo=UTC),
    )

    assert WAKA_SVG_POINTER in rendered
    assert DEFAULT_WAKATIME_SVG_PATH.as_posix() in rendered
    assert "This Week I Spent My Time On" not in rendered
    assert "My Github Data" not in rendered
    assert "Programming Languages" not in rendered
    assert MARKER_START not in rendered
    assert MARKER_END not in rendered
    assert "anmol098" not in rendered


def test_generate_waka_section_uses_mocked_waka_api(monkeypatch) -> None:
    monkeypatch.setenv("WAKATIME_API_KEY", "test-waka-key")
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)

    calls: list[str] = []

    def fake_fetch(api_key: str, *, range_name: str = "last_7_days") -> dict[str, Any]:
        calls.append(f"{api_key}:{range_name}")
        return _sample_waka_payload()

    monkeypatch.setattr(
        "scripts.wakatime_readme.fetch_wakatime_stats",
        fake_fetch,
    )

    body = generate_waka_section(include_github=False)
    assert calls == [
        "test-waka-key:last_7_days",
        "test-waka-key:last_year",
        "test-waka-key:all_time",
    ]
    assert WAKA_SVG_POINTER in body
    assert DEFAULT_WAKATIME_SVG_PATH.as_posix() in body
    assert "This Week I Spent My Time On" not in body
    assert "anmol098" not in body


def test_generate_waka_section_uses_public_repos_without_dump(monkeypatch) -> None:
    monkeypatch.setenv("WAKATIME_API_KEY", "waka")
    monkeypatch.setenv("GITHUB_TOKEN", "gh")
    looked_up: list[str | None] = []

    def fake_public_repos(token: str, *, login: str | None = None) -> frozenset[str]:
        del token
        looked_up.append(login)
        return frozenset({"wyattowalsh"})

    monkeypatch.setattr(
        "scripts.wakatime_readme.fetch_wakatime_stats",
        lambda api_key, *, range_name="last_7_days": _sample_waka_payload(),
    )
    monkeypatch.setattr(
        "scripts.wakatime_readme.fetch_public_repo_names",
        fake_public_repos,
    )

    body = generate_waka_section(github_login="wyattowalsh")
    assert looked_up == ["wyattowalsh"]
    assert WAKA_SVG_POINTER in body
    assert "This Week I Spent My Time On" not in body
    assert "My Github Data" not in body
    assert "secret-client" not in body


def test_apply_waka_section_rewrites_only_marker_zone(tmp_path: Path) -> None:
    readme = tmp_path / "README.md"
    readme.write_text(
        dedent(
            f"""\
            before
            {MARKER_START}
            stale
            {MARKER_END}
            after
            """
        ),
        encoding="utf-8",
    )
    body = render_waka_section(
        WakaWeekStats(
            timezone="UTC",
            languages=(WakaStatEntry("Python", 3600, 100.0, "1 hrs"),),
            editors=(),
            projects=(),
            operating_systems=(),
        ),
        updated_at=datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC),
    )
    assert apply_waka_section(readme, body) is True
    text = readme.read_text(encoding="utf-8")
    assert text.startswith("before\n")
    assert text.endswith("after\n")
    assert MARKER_START in text
    assert MARKER_END in text
    assert "stale" not in text
    assert WAKA_SVG_POINTER in text
    assert "This Week I Spent My Time On" not in text
    assert text.index(MARKER_START) < text.index(WAKA_SVG_POINTER) < text.index(
        MARKER_END
    )


def test_apply_waka_artifact_to_readme_noop_when_missing(tmp_path: Path) -> None:
    readme = tmp_path / "README.md"
    readme.write_text(
        f"{MARKER_START}\nold\n{MARKER_END}\n",
        encoding="utf-8",
    )
    assert apply_waka_artifact_to_readme(tmp_path / "missing.md", readme) is False
    assert "old" in readme.read_text(encoding="utf-8")


def test_write_and_apply_artifact_roundtrip(tmp_path: Path) -> None:
    artifact = write_waka_artifact(
        f"{WAKA_SVG_POINTER}\n", tmp_path / "waka-section.md"
    )
    readme = tmp_path / "README.md"
    readme.write_text(f"{MARKER_START}\n\n{MARKER_END}\n", encoding="utf-8")
    assert apply_waka_artifact_to_readme(artifact, readme) is True
    applied = readme.read_text(encoding="utf-8")
    assert WAKA_SVG_POINTER in applied
    assert "This Week I Spent My Time On" not in applied


def test_main_generate_allow_missing_key_writes_skip(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.delenv("WAKATIME_API_KEY", raising=False)
    out = tmp_path / "out"
    assert main(["generate", "--output-dir", str(out), "--allow-missing-key"]) == 0
    skip = out / "waka-section.skipped"
    assert skip.is_file()
    assert "WAKATIME_API_KEY missing" in skip.read_text(encoding="utf-8")


def test_main_generate_requires_key_without_allow(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.delenv("WAKATIME_API_KEY", raising=False)
    with pytest.raises(SystemExit):
        main(["generate", "--output-dir", str(tmp_path)])


def test_main_generate_writes_artifact_with_mocked_api(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("WAKATIME_API_KEY", "key")
    monkeypatch.setattr(
        "scripts.wakatime_readme.fetch_wakatime_stats",
        lambda api_key, *, range_name="last_7_days": _sample_waka_payload(),
    )
    out = tmp_path / "waka-section.md"
    assert (
        main(
            [
                "generate",
                "--output",
                str(out),
                "--no-github",
            ]
        )
        == 0
    )
    artifact = out.read_text(encoding="utf-8")
    assert WAKA_SVG_POINTER in artifact
    assert "This Week I Spent My Time On" not in artifact
    assert "Programming Languages" not in artifact


def test_write_skip_artifact(tmp_path: Path) -> None:
    path = write_skip_artifact(tmp_path, "skipped for test")
    assert path.name == "waka-section.skipped"
    assert "skipped for test" in path.read_text(encoding="utf-8")


def test_privacy_helpers_reject_paths_heartbeats_and_leisure() -> None:
    assert looks_like_file_path("/Users/ww/dev/secret.py")
    assert looks_like_file_path("~/Documents/notes.md")
    assert looks_like_file_path(r"C:\Users\ww\app.py")
    assert looks_like_heartbeat_entity("heartbeat")
    assert not looks_like_file_path("wyattowalsh")
    assert is_leisure_or_unprofessional("Games")
    assert is_leisure_or_unprofessional("Social Media")
    assert is_leisure_or_unprofessional("Shopping")
    assert is_leisure_or_unprofessional("Health")
    assert is_leisure_or_unprofessional("Entertainment")
    assert is_leisure_or_unprofessional("Dating")
    assert is_leisure_or_unprofessional("Messages")
    assert is_leisure_or_unprofessional("Photos")
    assert is_leisure_or_unprofessional("Spotify")
    assert is_leisure_or_unprofessional("Apple Music")
    assert is_leisure_or_unprofessional("Safari")
    assert is_leisure_or_unprofessional("Mail")
    assert is_leisure_or_unprofessional("Workout")
    assert is_leisure_or_unprofessional("Mindfulness")
    assert is_leisure_or_unprofessional("Heart Rate")
    assert is_professional_editor("Cursor")
    assert is_professional_editor("VS Code")
    assert is_professional_editor("Xcode")
    assert not is_professional_editor("Spotify")
    assert not is_professional_editor("Messages")
    assert not is_publishable_project("secret-client")
    assert not is_publishable_project("/Users/ww/dev/secret.py")
    assert is_publishable_project(
        "wyattowalsh",
        public_repo_names=("wyattowalsh/wyattowalsh",),
    )
    assert is_publishable_project(
        "wyattowalsh/agents",
        project_allowlist=("agents",),
    )


def test_filter_waka_stats_drops_private_and_leisure_rows() -> None:
    week = WakaWeekStats(
        timezone="UTC",
        languages=(
            WakaStatEntry("Python", 3600, 90.0, "1 hrs"),
            WakaStatEntry("/Users/ww/secret.py", 100, 10.0, "1 mins"),
        ),
        editors=(
            WakaStatEntry("Cursor", 3000, 80.0, "50 mins"),
            WakaStatEntry("Spotify", 400, 10.0, "6 mins"),
            WakaStatEntry("Messages", 200, 5.0, "3 mins"),
            WakaStatEntry("Safari", 180, 4.0, "3 mins"),
            WakaStatEntry("Mail", 90, 2.0, "1 mins"),
        ),
        projects=(
            WakaStatEntry("wyattowalsh", 2000, 50.0, "33 mins"),
            WakaStatEntry("secret-client", 1500, 40.0, "25 mins"),
            WakaStatEntry("/home/ww/heartbeat.py", 100, 5.0, "1 mins"),
        ),
        operating_systems=(
            WakaStatEntry("Mac", 2000, 50.0, "33 mins"),
            WakaStatEntry("iOS", 1200, 30.0, "20 mins"),
            WakaStatEntry("watchOS", 800, 20.0, "13 mins"),
            WakaStatEntry("Instagram", 40, 1.0, "1 mins"),
        ),
        categories=(
            WakaStatEntry("Coding", 3000, 70.0, "50 mins"),
            WakaStatEntry("Debugging", 800, 20.0, "13 mins"),
            WakaStatEntry("Entertainment", 200, 5.0, "3 mins"),
            WakaStatEntry("Games", 100, 2.0, "1 mins"),
            WakaStatEntry("Workout", 80, 2.0, "1 mins"),
            WakaStatEntry("Mindfulness", 40, 1.0, "1 mins"),
        ),
    )
    filtered = filter_waka_stats(
        week,
        public_repo_names=("wyattowalsh",),
    )
    assert [entry.name for entry in filtered.languages] == ["Python"]
    assert [entry.name for entry in filtered.editors] == ["Cursor"]
    assert [entry.name for entry in filtered.projects] == ["wyattowalsh"]
    assert [entry.name for entry in filtered.operating_systems] == [
        "Mac",
        "iOS",
        "watchOS",
    ]
    assert [entry.name for entry in filtered.categories] == ["Coding", "Debugging"]
    assert "Safari" not in {entry.name for entry in filtered.editors}
    assert "Mail" not in {entry.name for entry in filtered.editors}
    assert "Instagram" not in {entry.name for entry in filtered.operating_systems}
    assert "Workout" not in {entry.name for entry in filtered.categories}
    assert "Mindfulness" not in {entry.name for entry in filtered.categories}


def test_collect_wakatime_stats_fetches_documented_ranges(monkeypatch) -> None:
    calls: list[str] = []

    def fake_fetch(api_key: str, *, range_name: str = "last_7_days") -> dict[str, Any]:
        calls.append(range_name)
        payload = _sample_waka_payload()
        payload["data"] = {
            **payload["data"],
            "range": range_name,
            "human_readable_total": f"{range_name} total",
            "total_seconds": 1000.0,
        }
        return payload

    monkeypatch.setattr(
        "scripts.wakatime_readme.fetch_wakatime_stats",
        fake_fetch,
    )
    monkeypatch.setattr(
        "scripts.wakatime_readme.fetch_all_time_since_today",
        lambda api_key: {
            "data": {
                "text": "4,500 hrs 12 mins",
                "total_seconds": 16_200_720,
                "is_up_to_date": True,
                "range": {"start_date": "2018-01-01"},
            }
        },
    )
    monkeypatch.setattr(
        "scripts.wakatime_readme.fetch_wakatime_daily_totals",
        lambda api_key, *, range_name="last_year": (
            WakaDayTotal(day=date(2026, 8, 1), total_seconds=1200),
        ),
    )

    collection = collect_wakatime_stats("key")
    assert calls == list(WAKA_STATS_RANGES)
    assert collection.week.range_name == "last_7_days"
    assert collection.year is not None
    assert collection.all_time is not None
    assert collection.all_time_since_today is not None
    assert collection.all_time_since_today.text == "4,500 hrs 12 mins"
    assert collection.daily[0].total_seconds == 1200
    assert collection.fetched_ranges == WAKA_STATS_RANGES


def test_collect_wakatime_stats_skips_optional_ranges(monkeypatch) -> None:
    def fake_fetch(api_key: str, *, range_name: str = "last_7_days") -> dict[str, Any]:
        if range_name != "last_7_days":
            raise ValueError(f"{range_name} unavailable")
        return _sample_waka_payload()

    monkeypatch.setattr(
        "scripts.wakatime_readme.fetch_wakatime_stats",
        fake_fetch,
    )
    collection = collect_wakatime_stats(
        "key",
        include_daily=False,
        include_all_time_since_today=False,
    )
    assert collection.year is None
    assert collection.all_time is None
    assert collection.fetched_ranges == ("last_7_days",)


def test_parse_daily_totals_ignore_entities() -> None:
    insights = parse_daily_totals_from_insights(
        {
            "data": {
                "days": [
                    {"date": "2026-08-01", "total_seconds": 100, "text": "1 min"},
                    {
                        "date": "2026-08-02",
                        "total": 200,
                        "entities": [{"name": "/Users/ww/secret.py"}],
                    },
                ]
            }
        }
    )
    assert [item.day.isoformat() for item in insights] == [
        "2026-08-01",
        "2026-08-02",
    ]
    summaries = parse_daily_totals_from_summaries(
        {
            "data": [
                {
                    "grand_total": {"total_seconds": 300, "text": "5 mins"},
                    "range": {"date": "2026-08-03"},
                    "entities": [{"name": "/private/var/heartbeat.py"}],
                }
            ]
        }
    )
    assert summaries[0].total_seconds == 300
    assert summaries[0].text == "5 mins"
    lifetime = parse_all_time_since_today(
        {"data": {"total_seconds": 3600, "text": "1 hr", "is_up_to_date": True}}
    )
    assert lifetime.total_seconds == 3600
    assert lifetime.text == "1 hr"
    mapped = parse_daily_totals_from_insights(
        {"data": {"days": {"2026-08-04": 90, "2026-08-05": {"total_seconds": 45}}}}
    )
    assert [item.day.isoformat() for item in mapped] == ["2026-08-04", "2026-08-05"]


def test_fetch_wakatime_daily_totals_falls_back_to_summaries(monkeypatch) -> None:
    monkeypatch.setattr(
        "scripts.wakatime_readme.fetch_wakatime_insights",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(ValueError("stale")),
    )

    def fake_summaries(api_key: str, *, range_label: str | None = None, **_kwargs):
        if range_label != "Last 7 Days":
            raise ValueError(range_label)
        return {
            "data": [
                {
                    "grand_total": {"total_seconds": 42, "text": "42 secs"},
                    "range": {"date": "2026-08-10"},
                    "entities": [{"name": "/tmp/secret.py"}],
                }
            ]
        }

    monkeypatch.setattr(
        "scripts.wakatime_readme.fetch_wakatime_summaries",
        fake_summaries,
    )
    days = fetch_wakatime_daily_totals("key")
    assert len(days) == 1
    assert days[0].total_seconds == 42
    assert days[0].text == "42 secs"


def test_fetch_public_repo_names_skips_private(monkeypatch) -> None:
    monkeypatch.setattr(
        "scripts._github_http._paginate_rest",
        lambda *_args, **_kwargs: [
            {"name": "agents", "full_name": "wyattowalsh/agents", "private": False},
            {"name": "secret", "full_name": "wyattowalsh/secret", "private": True},
            "not-a-repo",
        ],
    )
    names = fetch_public_repo_names("token", login="wyattowalsh")
    assert "agents" in names
    assert "wyattowalsh/agents" in names
    assert "secret" not in names


def test_generate_waka_section_hides_private_projects(monkeypatch) -> None:
    monkeypatch.setenv("WAKATIME_API_KEY", "key")
    payload = _sample_waka_payload()
    payload["data"]["projects"] = [
        {
            "name": "secret-client",
            "total_seconds": 9000,
            "percent": 80.0,
            "text": "2 hrs 30 mins",
        },
        {
            "name": "wyattowalsh",
            "total_seconds": 1000,
            "percent": 20.0,
            "text": "16 mins",
        },
    ]
    payload["data"]["editors"].append(
        {
            "name": "Spotify",
            "total_seconds": 400,
            "percent": 5.0,
            "text": "6 mins",
        }
    )
    monkeypatch.setattr(
        "scripts.wakatime_readme.fetch_wakatime_stats",
        lambda api_key, *, range_name="last_7_days": payload,
    )
    body = generate_waka_section(
        include_github=False,
        project_allowlist=("wyattowalsh",),
    )
    assert WAKA_SVG_POINTER in body
    assert "secret-client" not in body
    assert "Spotify" not in body
    assert "This Week I Spent My Time On" not in body


def test_main_generate_writes_svg_when_requested(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("WAKATIME_API_KEY", "key")
    monkeypatch.setattr(
        "scripts.wakatime_readme.fetch_wakatime_stats",
        lambda api_key, *, range_name="last_7_days": _sample_waka_payload(),
    )
    written: list[Path] = []

    def fake_svg(**kwargs):
        path = kwargs["output_path"]
        path.write_text("<svg>waka</svg>\n", encoding="utf-8")
        written.append(path)
        return path

    monkeypatch.setattr("scripts.wakatime_svg.generate_wakatime_svg", fake_svg)
    markdown = tmp_path / "waka-section.md"
    svg = tmp_path / "wakatime.svg"
    assert (
        main(
            [
                "generate",
                "--output",
                str(markdown),
                "--svg-output",
                str(svg),
                "--no-github",
                "--project-allowlist",
                "wyattowalsh",
            ]
        )
        == 0
    )
    markdown_text = markdown.read_text(encoding="utf-8")
    assert WAKA_SVG_POINTER in markdown_text
    assert "This Week I Spent My Time On" not in markdown_text
    assert "Programming Languages" not in markdown_text
    assert written == [svg]
    assert svg.read_text(encoding="utf-8").startswith("<svg>")
    assert "anmol098" not in markdown_text


def test_apply_wakatime_svg_copies_committed_card(tmp_path: Path) -> None:
    """SVG apply copies wakatime.svg; markdown dump is not the sole ship artifact."""
    source = tmp_path / "artifact" / "wakatime.svg"
    dest = tmp_path / "img" / "wakatime.svg"
    source.parent.mkdir()
    source.write_text(
        "<svg xmlns='http://www.w3.org/2000/svg'>Languages Editors</svg>",
        encoding="utf-8",
    )
    assert apply_wakatime_svg(source, dest) is True
    assert dest.read_text(encoding="utf-8").startswith("<svg")
    assert apply_wakatime_svg(source, dest) is False
    assert apply_wakatime_svg(tmp_path / "missing.svg", dest) is False
    junk = tmp_path / "not-an.svg"
    junk.write_text("not svg", encoding="utf-8")
    assert apply_wakatime_svg(junk, dest) is False
    assert dest.read_text(encoding="utf-8").startswith("<svg")


def test_main_apply_copies_svg_artifact(tmp_path: Path) -> None:
    readme = tmp_path / "README.md"
    readme.write_text(f"{MARKER_START}\nold\n{MARKER_END}\n", encoding="utf-8")
    markdown = tmp_path / "waka-section.md"
    markdown.write_text(f"{WAKA_SVG_POINTER}\n", encoding="utf-8")
    svg_src = tmp_path / "wakatime.svg"
    svg_src.write_text("<svg>Languages</svg>\n", encoding="utf-8")
    dest = tmp_path / "committed.svg"
    assert (
        main(
            [
                "apply",
                "--artifact",
                str(markdown),
                "--readme",
                str(readme),
                "--svg-artifact",
                str(svg_src),
                "--svg-dest",
                str(dest),
            ]
        )
        == 0
    )
    applied = readme.read_text(encoding="utf-8")
    assert WAKA_SVG_POINTER in applied
    assert "This Week I Spent My Time On" not in applied
    assert dest.read_text(encoding="utf-8") == "<svg>Languages</svg>\n"
    assert dest != DEFAULT_WAKATIME_SVG_PATH
