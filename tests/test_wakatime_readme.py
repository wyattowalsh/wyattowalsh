"""Tests for first-party WakaTime README section generation."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from textwrap import dedent

import pytest

from scripts.wakatime_readme import (
    MARKER_END,
    MARKER_START,
    GitHubShortInfo,
    WakaStatEntry,
    WakaWeekStats,
    apply_waka_artifact_to_readme,
    apply_waka_section,
    generate_waka_section,
    main,
    parse_wakatime_stats,
    render_waka_section,
    write_skip_artifact,
    write_waka_artifact,
)


def _sample_waka_payload() -> dict:
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
        }
    }


def test_parse_wakatime_stats_extracts_top_entries() -> None:
    week = parse_wakatime_stats(_sample_waka_payload())
    assert week.timezone == "America/New_York"
    assert week.languages[0].name == "Python"
    assert week.editors[0].name == "VS Code"
    assert week.projects[0].name == "wyattowalsh"
    assert week.operating_systems[0].percent == 100.0


def test_render_waka_section_includes_healthy_markers() -> None:
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

    assert "My Github Data" in rendered
    assert "This Week I Spent My Time On" in rendered
    assert "Programming Languages" in rendered
    assert "Editors:" in rendered
    assert "Projects:" in rendered
    assert "Operating System:" in rendered
    assert "Python" in rendered
    assert "Last Updated on 31/07/2026 12:00:00 UTC" in rendered
    assert MARKER_START not in rendered
    assert MARKER_END not in rendered


def test_generate_waka_section_uses_mocked_waka_api(monkeypatch) -> None:
    monkeypatch.setenv("WAKATIME_API_KEY", "test-waka-key")
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)

    calls: list[str] = []

    def fake_fetch(api_key: str, *, range_name: str = "last_7_days") -> dict:
        calls.append(f"{api_key}:{range_name}")
        return _sample_waka_payload()

    monkeypatch.setattr(
        "scripts.wakatime_readme.fetch_wakatime_stats",
        fake_fetch,
    )

    body = generate_waka_section(include_github=False)
    assert calls == ["test-waka-key:last_7_days"]
    assert "This Week I Spent My Time On" in body
    assert "America/New_York" in body


def test_generate_waka_section_enriches_github_when_token_present(monkeypatch) -> None:
    monkeypatch.setenv("WAKATIME_API_KEY", "waka")
    monkeypatch.setenv("GITHUB_TOKEN", "gh")

    monkeypatch.setattr(
        "scripts.wakatime_readme.fetch_wakatime_stats",
        lambda api_key, *, range_name="last_7_days": _sample_waka_payload(),
    )
    monkeypatch.setattr(
        "scripts.wakatime_readme.fetch_github_short_info",
        lambda token, *, login=None: GitHubShortInfo(
            public_repos=10,
            private_repos=2,
            disk_usage_bytes=2048,
            hireable=False,
            contributions_this_year=42,
            year=2026,
        ),
    )

    body = generate_waka_section(github_login="wyattowalsh")
    assert "My Github Data" in body
    assert "42 Contributions in the Year 2026" in body
    assert "Not Opted to Hire" in body


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
    assert "This Week I Spent My Time On" in text
    assert text.index(MARKER_START) < text.index("Python") < text.index(MARKER_END)


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
        "📊 **This Week I Spent My Time On**\n", tmp_path / "waka-section.md"
    )
    readme = tmp_path / "README.md"
    readme.write_text(f"{MARKER_START}\n\n{MARKER_END}\n", encoding="utf-8")
    assert apply_waka_artifact_to_readme(artifact, readme) is True
    assert "This Week I Spent My Time On" in readme.read_text(encoding="utf-8")


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
    assert "Programming Languages" in out.read_text(encoding="utf-8")


def test_write_skip_artifact(tmp_path: Path) -> None:
    path = write_skip_artifact(tmp_path, "skipped for test")
    assert path.name == "waka-section.skipped"
    assert "skipped for test" in path.read_text(encoding="utf-8")
