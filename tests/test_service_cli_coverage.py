"""High-yield deterministic coverage for service and CLI orchestration paths."""

from __future__ import annotations

import importlib
import json
import socket
import subprocess
import xml.etree.ElementTree as xml_etree
from datetime import UTC, date, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest
import typer
from PIL import Image

import scripts.cli.generate as generate_package
import scripts.cli.generate._common as common_cmd
import scripts.cli.generate.all_cmd as all_cmd
import scripts.cli.generate.readme_cmd as readme_cmd
import scripts.cli.preview as preview_cmd
import scripts.config as config_module
import scripts.fetch_metrics as fetch_metrics
import scripts.metrics_svg as metrics_svg
import scripts.readme_sections as readme_sections
import scripts.spotify_auth as spotify_auth
import scripts.supplemental_metrics as supplemental
import scripts.wakatime_readme as wakatime
from scripts.cli._app import _version_callback
from scripts.cli._display import OutputFormat
from scripts.cli.config_cmd import generate_default, save, view
from scripts.cli.preview import PreviewTarget
from scripts.cli.settings_cmd import show_settings
from scripts.config import ProjectConfig, ReadmeSectionsSettings
from scripts.metrics_svg import SvgValidationStatus
from scripts.readme_sections import (
    BlogFeedClient,
    BlogMetadataClient,
    GitHubRepoClient,
    ReadmeSectionGenerator,
    RepoMetadata,
    StarHistoryClient,
)
from scripts.techs import Technology, display_technologies, load_technologies

qr_cmd = importlib.import_module("scripts.cli.generate.qr")


def test_star_history_headers_tolerate_missing_cli_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Keep the local ``gh`` fallback deterministic in full-suite coverage."""

    monkeypatch.delenv("GH_TOKEN", raising=False)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)

    def fail_cli_token(*_args: object, **_kwargs: object) -> bytes:
        raise OSError("gh token unavailable")

    monkeypatch.setattr(subprocess, "check_output", fail_cli_token)

    assert StarHistoryClient()._headers() == {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "readme-section-generator",
    }


class _Response:
    def __init__(
        self,
        body: bytes,
        *,
        headers: dict[str, str] | None = None,
        status: int = 200,
    ) -> None:
        self._body = body
        self.headers = headers or {}
        self.status = status

    def __enter__(self) -> _Response:
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def read(self) -> bytes:
        return self._body


def test_config_services_cover_invalid_and_bootstrap_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    missing = tmp_path / "missing.yaml"
    with pytest.raises(FileNotFoundError, match="Config file not found"):
        config_module.load_config(missing)

    empty = tmp_path / "empty.yaml"
    empty.write_text("# comment only\n", encoding="utf-8")
    with pytest.raises(OSError, match="YAML file is empty"):
        config_module.load_config(empty)

    sequence = tmp_path / "sequence.yaml"
    sequence.write_text("- not\n- a mapping\n", encoding="utf-8")
    with pytest.raises(OSError, match="expected a mapping"):
        config_module.load_config(sequence)

    invalid = tmp_path / "invalid.yaml"
    invalid.write_text("banner_settings: [\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Invalid YAML"):
        config_module.load_config(invalid)

    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    default = config_module.load_config()
    assert isinstance(default, ProjectConfig)
    assert (tmp_path / "config.yaml").is_file()

    (tmp_path / "config.yaml").write_text("", encoding="utf-8")
    monkeypatch.setenv("CI", "true")
    with pytest.raises(FileNotFoundError, match="empty"):
        config_module.load_config()

    monkeypatch.setattr(config_module, "DEFAULT_CONFIG_PATH", tmp_path / "absent.yaml")
    with pytest.raises(FileNotFoundError, match="Refusing"):
        config_module.load_config(tmp_path / "absent.yaml")


def test_skills_and_save_config_errors(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    with pytest.raises(FileNotFoundError):
        config_module.load_skills(tmp_path / "missing.yaml")

    empty = tmp_path / "empty-skills.yaml"
    empty.write_text("", encoding="utf-8")
    with pytest.raises(ValueError, match="empty"):
        config_module.load_skills(empty)

    invalid = tmp_path / "invalid-skills.yaml"
    invalid.write_text("categories: nope\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Invalid skills data"):
        config_module.load_skills(invalid)

    monkeypatch.setattr(
        Path, "mkdir", lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("disk"))
    )
    with pytest.raises(OSError, match="Failed to save config"):
        config_module.save_config(ProjectConfig(), tmp_path / "x" / "config.yaml")


def test_config_and_settings_command_guards(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    printed: list[object] = []
    monkeypatch.setattr(
        "scripts.cli.config_cmd.console.print", lambda value: printed.append(value)
    )
    monkeypatch.setattr("scripts.cli.config_cmd.display_config", lambda *_args: None)
    monkeypatch.setattr(
        "scripts.cli.config_cmd.load_config",
        lambda _path: (_ for _ in ()).throw(FileNotFoundError()),
    )
    with pytest.raises(typer.Exit):
        view(tmp_path / "gone.yaml", OutputFormat.JSON)

    monkeypatch.setattr(
        "scripts.cli.config_cmd.load_config",
        lambda _path: (_ for _ in ()).throw(ValueError("bad")),
    )
    with pytest.raises(typer.Exit):
        view(tmp_path / "bad.yaml", OutputFormat.JSON)

    saved: list[ProjectConfig] = []
    monkeypatch.setattr(
        "scripts.cli.config_cmd.load_config",
        lambda _path: (_ for _ in ()).throw(FileNotFoundError()),
    )
    monkeypatch.setattr(
        "scripts.cli.config_cmd.save_config", lambda cfg, _path: saved.append(cfg)
    )
    save(tmp_path / "new.yaml")
    assert len(saved) == 1

    monkeypatch.setattr(
        "scripts.cli.config_cmd.save_config",
        lambda *_args: (_ for _ in ()).throw(OSError("readonly")),
    )
    with pytest.raises(typer.Exit):
        save(tmp_path / "bad-save.yaml")

    existing = tmp_path / "existing.yaml"
    existing.write_text("x", encoding="utf-8")
    monkeypatch.setattr(
        "scripts.cli.config_cmd.typer.confirm",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(typer.Abort()),
    )
    generate_default(existing, OutputFormat.JSON)

    monkeypatch.setattr(
        "scripts.cli.config_cmd.typer.confirm", lambda *_args, **_kwargs: True
    )
    with pytest.raises(typer.Exit):
        generate_default(existing, OutputFormat.JSON)

    monkeypatch.setattr(
        "scripts.cli.settings_cmd.Settings",
        lambda: (_ for _ in ()).throw(ValueError("bad env")),
    )
    with pytest.raises(typer.Exit):
        show_settings(OutputFormat.JSON)
    assert printed


def test_version_callback_installed_and_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    echoed: list[str] = []
    monkeypatch.setattr("scripts.cli._app.typer.echo", echoed.append)
    monkeypatch.setattr(
        "scripts.cli._app.importlib.metadata.version", lambda _name: "9.8.7"
    )
    with pytest.raises(typer.Exit):
        _version_callback(True)
    assert echoed[-1] == "readme 9.8.7"

    import importlib.metadata

    monkeypatch.setattr(
        "scripts.cli._app.importlib.metadata.version",
        lambda _name: (_ for _ in ()).throw(importlib.metadata.PackageNotFoundError()),
    )
    with pytest.raises(typer.Exit):
        _version_callback(True)
    assert echoed[-1] == "readme 0.0.0-dev"
    _version_callback(False)


def test_technology_loading_and_display(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tech_file = tmp_path / "techs.md"
    tech_file.write_text(
        "loose text\n- Rust (Level: 5) - systems\n## Custom Tools\n"
        "- Zed (Level: 4)\n- Broken (Level: 9)\n"
        "## Programming Languages\n- Python (Level: 5) - daily\n",
        encoding="utf-8",
    )
    technologies = load_technologies(tech_file)
    assert [item.name for item in technologies] == ["Rust", "Zed", "Python"]
    assert technologies[0].category == "Uncategorized"

    printed: list[object] = []
    monkeypatch.setattr(
        "scripts.techs.console.print", lambda value: printed.append(value)
    )
    display_technologies([])
    display_technologies(
        [
            Technology(name="Zed", level=3, category="Custom", notes=None),
            Technology(
                name="Python", level=5, category="Programming Languages", notes="daily"
            ),
            Technology(name="Alpha", level=2, category="Custom", notes="note"),
        ]
    )
    assert len(printed) == 2

    monkeypatch.setattr(
        "builtins.open",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(PermissionError("blocked")),
    )
    assert load_technologies(tech_file) == []
    assert load_technologies(tmp_path / "missing.md") == []


def test_spotify_helpers_and_mint_flow(monkeypatch: pytest.MonkeyPatch) -> None:
    url = spotify_auth.build_spotify_authorize_url(
        client_id="client",
        redirect_uri="http://127.0.0.1:9000/callback",
        state="state",
        scope="scope one",
        show_dialog=False,
    )
    assert "show_dialog=false" in url and "scope=scope+one" in url

    captured: dict[str, object] = {}
    monkeypatch.setattr(
        spotify_auth,
        "_request_json",
        lambda url, **kwargs: captured.update(url=url, **kwargs) or ["bad"],
    )
    with pytest.raises(RuntimeError, match="non-object"):
        spotify_auth.exchange_spotify_authorization_code(
            client_id="id", client_secret="secret", code="code", redirect_uri="uri"
        )

    monkeypatch.setattr(
        spotify_auth,
        "_request_json",
        lambda *_args, **_kwargs: {"refresh_token": " token "},
    )
    payload = spotify_auth.exchange_spotify_authorization_code(
        client_id="id", client_secret="secret", code="code", redirect_uri="uri"
    )
    assert spotify_auth.extract_spotify_refresh_token(payload) == "token"
    with pytest.raises(RuntimeError, match="no refresh_token"):
        spotify_auth.extract_spotify_refresh_token({})

    monkeypatch.setattr(spotify_auth.secrets, "token_urlsafe", lambda _n: "fixed-state")
    monkeypatch.setattr(
        spotify_auth,
        "_wait_for_spotify_authorization_code",
        lambda **_kwargs: "auth-code",
    )
    monkeypatch.setattr(
        spotify_auth,
        "exchange_spotify_authorization_code",
        lambda **_kwargs: {"refresh_token": "new-token"},
    )
    token, auth_url = spotify_auth.mint_spotify_refresh_token(
        client_id="id", client_secret="secret", callback_port=9999, open_browser=False
    )
    assert token == "new-token" and "fixed-state" in auth_url


@pytest.mark.parametrize(
    ("target", "filename"),
    [
        (PreviewTarget.BANNER, "banner.svg"),
        (PreviewTarget.QR, "qr.png"),
        (PreviewTarget.WORD_CLOUD, "wordcloud.svg"),
        (PreviewTarget.README_SECTIONS, "README.md"),
        (PreviewTarget.GENERATIVE, "generative.svg"),
    ],
)
def test_preview_dispatches_isolated_generators(
    target: PreviewTarget,
    filename: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = tmp_path / target.value

    def write_output(*_args: object, **kwargs: object) -> None:
        path = kwargs.get("output_path")
        assert isinstance(path, Path)
        if path.suffix:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("generated", encoding="utf-8")
        else:
            path.mkdir(parents=True, exist_ok=True)
            (path / "generative.svg").write_text("generated", encoding="utf-8")

    for name in ("banner", "qr", "word_cloud", "readme_sections", "generative_art"):
        monkeypatch.setattr(generate_package, name, write_output)
    monkeypatch.chdir(tmp_path)
    if target is PreviewTarget.README_SECTIONS:
        (tmp_path / "README.md").write_text("source", encoding="utf-8")
    preview_cmd.preview(target, output_dir=output, keep=True)
    assert (output / filename).is_file()


def test_preview_skills_cleanup_failure_and_many_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    called: list[str] = []
    monkeypatch.setattr(generate_package, "skills", lambda: called.append("skills"))
    preview_cmd.preview(PreviewTarget.SKILLS, output_dir=tmp_path / "skills", keep=True)
    assert called == ["skills"]

    many = tmp_path / "many"
    monkeypatch.setattr(
        generate_package,
        "banner",
        lambda **_kwargs: [
            (many / f"{index}.svg").write_text("x", encoding="utf-8")
            for index in range(42)
        ],
    )
    preview_cmd.preview(PreviewTarget.BANNER, output_dir=many, keep=False)
    assert not many.exists()

    failed = tmp_path / "failed"
    monkeypatch.setattr(
        generate_package,
        "qr",
        lambda **_kwargs: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    with pytest.raises(typer.Exit):
        preview_cmd.preview(PreviewTarget.QR, output_dir=failed, keep=False)
    assert not failed.exists()

    with pytest.raises(typer.Exit):
        preview_cmd.preview(
            cast(PreviewTarget, "unsupported"),
            output_dir=tmp_path / "bad",
            keep=True,
        )


def test_common_helpers_success_and_guards(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(generate_package, "load_config", lambda _path: ProjectConfig())
    assert isinstance(
        common_cmd._load_project_config(tmp_path / "cfg.yaml"), ProjectConfig
    )
    monkeypatch.setattr(
        generate_package,
        "load_config",
        lambda _path: (_ for _ in ()).throw(ValueError("bad")),
    )
    with pytest.raises(typer.Exit):
        common_cmd._load_project_config(tmp_path / "bad.yaml")

    assert common_cmd._format_style_help(("one", "two")) == "one, or two"
    assert common_cmd._selected_living_art_styles(None)
    assert common_cmd._selected_living_art_styles("inkgarden") == ("inkgarden",)
    with pytest.raises(typer.Exit):
        common_cmd._selected_living_art_styles("not-a-style")

    with pytest.raises(typer.Exit):
        common_cmd._load_required_json("metrics", None)
    missing = tmp_path / "missing.json"
    with pytest.raises(typer.Exit):
        common_cmd._load_required_json("metrics", missing)
    invalid = tmp_path / "invalid.json"
    invalid.write_text("[]", encoding="utf-8")
    assert common_cmd._load_required_json("metrics", invalid) == []
    valid = tmp_path / "valid.json"
    valid.write_text('{"ok": true}', encoding="utf-8")
    assert common_cmd._load_required_json("metrics", valid) == {"ok": True}

    assert common_cmd._apply_stopword_filter({"The": 2, "python": 4}, ["the"]) == {
        "python": 4
    }
    assert common_cmd._prompt_to_frequencies("Python python test", ["test"]) == {
        "Python": 1.0,
        "python": 1.0,
    }
    assert common_cmd._prompt_to_frequencies("the and", ["the", "and"]) == {}


def test_qr_command_success_defaults_and_errors(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output = tmp_path / "qr.png"
    project = ProjectConfig()
    monkeypatch.setattr(qr_cmd, "_load_project_config", lambda _path: project)
    calls: dict[str, Any] = {}

    class FakeGenerator:
        def __init__(self, **kwargs: Any) -> None:
            calls["init"] = kwargs

        def generate_artistic_vcard_qr(self, **kwargs: Any) -> Path:
            calls["generate"] = kwargs
            path = Path(calls["init"]["default_output_dir"]) / str(
                kwargs["output_filename"]
            )
            path.parent.mkdir(parents=True, exist_ok=True)
            Image.new("RGB", (2, 2), color="navy").save(path, format="PNG")
            return path

    monkeypatch.setattr("scripts.qr.QRCodeGenerator", FakeGenerator)
    qr_cmd.qr(
        output_path=output,
        qr_error_correction="H",
        qr_scale=7,
        qr_background_path=tmp_path / "bg.svg",
    )
    assert output.is_file()
    assert calls["generate"]["error_correction"] == "H"

    broken = SimpleNamespace(qr_code_settings={"bad": True}, v_card_data=None)
    monkeypatch.setattr(qr_cmd, "_load_project_config", lambda _path: broken)
    with pytest.raises(typer.Exit):
        qr_cmd.qr(output_path=tmp_path / "bad.png")

    monkeypatch.setattr(qr_cmd, "_load_project_config", lambda _path: project)

    class FailingGenerator(FakeGenerator):
        def generate_artistic_vcard_qr(self, **kwargs: Any) -> Path:
            raise ValueError("invalid qr")

    monkeypatch.setattr("scripts.qr.QRCodeGenerator", FailingGenerator)
    with pytest.raises(typer.Exit):
        qr_cmd.qr(output_path=tmp_path / "failure.png")


def test_readme_cli_commands_are_wired(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        readme_cmd, "_load_project_config", lambda _path: ProjectConfig()
    )
    generated: list[Path] = []

    class FakeSkillsGenerator:
        def __init__(self, **_kwargs: object) -> None:
            pass

        def generate(self) -> Path:
            path = tmp_path / "README.md"
            generated.append(path)
            return path

    monkeypatch.setattr("scripts.skills.SkillsBadgeGenerator", FakeSkillsGenerator)
    monkeypatch.setattr(readme_cmd, "load_skills", lambda _path: object())
    readme_cmd.skills(skills_path=tmp_path / "skills.yaml")
    assert generated
    monkeypatch.setattr(
        readme_cmd,
        "load_skills",
        lambda _path: (_ for _ in ()).throw(ValueError("bad")),
    )
    with pytest.raises(typer.Exit):
        readme_cmd.skills(skills_path=tmp_path / "bad.yaml")

    updates: dict[str, dict[str, Any]] = {}
    readme_cmd._collect_card_style_update(
        updates, "connect", common_cmd.ReadmeCardVariant.LEGACY, False, True
    )
    readme_cmd._collect_card_style_update(updates, "blog", None, None, None)
    assert updates["connect"] == {
        "variant": "legacy",
        "transparent_canvas": False,
        "show_title": True,
    }

    statuses = {
        "on": SimpleNamespace(enabled=True, reason=""),
        "off": SimpleNamespace(enabled=False, reason="missing"),
    }
    monkeypatch.setattr(
        supplemental, "generate_supplemental_metrics", lambda **_kwargs: statuses
    )
    readme_cmd.supplemental_metrics(
        output_dir=tmp_path / "img", manifest_path=tmp_path / "manifest.json"
    )

    class FakeSectionGenerator:
        def __init__(self, settings: ReadmeSectionsSettings) -> None:
            self.settings = settings

        def generate(self) -> Path:
            generated.append(Path(self.settings.readme_path))
            return Path(self.settings.readme_path)

    monkeypatch.setattr(readme_sections, "ReadmeSectionGenerator", FakeSectionGenerator)
    output = tmp_path / "custom-readme.md"
    readme_cmd.readme_sections(
        output_path=output,
        readme_default_card_variant=common_cmd.ReadmeCardVariant.LEGACY,
        readme_connect_card_transparent_canvas=True,
        readme_featured_card_show_title=False,
        readme_blog_card_variant=common_cmd.ReadmeCardVariant.GH_CARD,
    )
    assert output in generated


def test_wakatime_cli_command_branches(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("WAKATIME_API_KEY", raising=False)
    readme_cmd.wakatime(output_dir=tmp_path, allow_missing_key=True)
    assert (tmp_path / wakatime.SKIP_MARKER_NAME).is_file()
    with pytest.raises(typer.Exit):
        readme_cmd.wakatime(output_dir=tmp_path, allow_missing_key=False)

    monkeypatch.setenv("WAKATIME_API_KEY", "key")
    monkeypatch.setattr(wakatime, "generate_waka_section", lambda **_kwargs: "body")
    output = tmp_path / "waka.md"
    svg = tmp_path / "wakatime.svg"
    monkeypatch.setattr(
        "scripts.wakatime_svg.generate_wakatime_svg",
        lambda **kwargs: kwargs["output_path"].write_text("<svg/>\n", encoding="utf-8")
        or kwargs["output_path"],
    )
    readme_cmd.wakatime(output=output, no_github=True, svg_output=svg)
    assert output.read_text(encoding="utf-8") == "body\n"
    assert svg.read_text(encoding="utf-8") == "<svg/>\n"
    monkeypatch.setattr(
        wakatime,
        "generate_waka_section",
        lambda **_kwargs: (_ for _ in ()).throw(RuntimeError("api")),
    )
    with pytest.raises(typer.Exit):
        readme_cmd.wakatime(output=output)


def test_supplemental_json_time_and_event_helpers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with pytest.raises(RuntimeError, match="must be a JSON object"):
        supplemental._require_json_object([], context="payload")
    with pytest.raises(RuntimeError, match="must be a JSON array"):
        supplemental._require_json_array({}, context="payload")
    assert supplemental._optional_json_object(None, context="optional") == {}
    with pytest.raises(RuntimeError):
        supplemental._optional_json_object([], context="optional")

    now = datetime(2026, 8, 12, 12, tzinfo=UTC)
    assert supplemental._relative_label(None, now=now) == "unknown time"
    assert supplemental._relative_label("bad", now=now) == "unknown time"
    assert supplemental._relative_label("2026-08-12T11:59:30Z", now=now) == "1m ago"
    assert supplemental._relative_label("2026-08-12T11:30:00Z", now=now) == "30m ago"
    assert supplemental._relative_label("2026-08-12T08:00:00Z", now=now) == "4h ago"
    assert supplemental._relative_label("2026-08-09T12:00:00Z", now=now) == "3d ago"
    assert supplemental._relative_label("2026-07-01T12:00:00Z", now=now) == "Jul 01"
    assert supplemental._truncate("abcdef", 4) == "a..."
    assert supplemental._truncate("abc", 4) == "abc"

    events = [
        {
            "type": "PushEvent",
            "repo": {"name": "a/r"},
            "payload": {"commits": [{}]},
            "created_at": "now",
        },
        {
            "type": "WatchEvent",
            "repo": {"name": "a/r"},
            "payload": {},
            "created_at": "now",
        },
        {
            "type": "PullRequestEvent",
            "repo": {"name": "a/r"},
            "payload": {"pull_request": {"merged_at": "now"}},
            "created_at": "now",
        },
        {
            "type": "PullRequestEvent",
            "repo": {"name": "a/r"},
            "payload": {"action": "reopened"},
            "created_at": "now",
        },
        {
            "type": "IssuesEvent",
            "repo": {"name": "a/r"},
            "payload": {"action": "closed"},
            "created_at": "now",
        },
        {
            "type": "ReleaseEvent",
            "repo": {"name": "a/r"},
            "payload": {},
            "created_at": "now",
        },
        {
            "type": "CreateEvent",
            "repo": {"name": "a/r"},
            "payload": {"ref_type": "branch"},
            "created_at": "now",
        },
        {"type": "Unknown", "repo": {}, "payload": {}, "created_at": "now"},
    ]
    summaries = [supplemental._summarize_github_event(event) for event in events]
    assert summaries[-1] is None
    assert all(item is not None for item in summaries[:-1])

    monkeypatch.setattr(supplemental, "_request_json", lambda *_args, **_kwargs: events)
    recent = supplemental._fetch_recent_activity("owner", None, limit=3)
    assert len(recent) == 3
    monkeypatch.setattr(
        supplemental,
        "_request_json",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(TimeoutError()),
    )
    assert supplemental._fetch_recent_activity("owner", None) == []


def test_supplemental_statistics_cards_and_optional_credentials(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calendar = [
        {"date": "2026-08-08", "count": 2},
        {"date": "2026-08-09", "count": 0},
        {"date": "2026-08-10", "count": 3},
        {"date": "2026-08-11", "count": 4},
    ]
    daily_counts = {
        date(2026, 8, 8): 2,
        date(2026, 8, 9): 0,
        date(2026, 8, 10): 3,
        date(2026, 8, 11): 4,
    }
    assert supplemental._streaks_from_daily_counts(
        daily_counts, now_date=date(2026, 8, 11)
    ) == (2, 2)
    stats = supplemental._contribution_stats({"contributions_calendar": calendar})
    assert stats["total"] == 9 and stats["busiest_day"] == 4
    assert supplemental._top_languages({"languages": {"Python": 9, "Rust": 3}}) == (
        "Python",
        "Rust",
    )
    assert supplemental._focus_repositories(
        {
            "recent_merged_prs": [
                {"repo_name": "one"},
                {"repo_name": "one"},
                {"repo_name": "two"},
            ]
        }
    ) == ("one", "two")
    assert supplemental._peak_commit_hour({}) == "n/a"
    assert (
        supplemental._peak_commit_hour({"commit_hour_distribution": {"9": 1, "14": 4}})
        == "14:00"
    )
    assert supplemental._render_habits_card({"contributions_calendar": calendar}).cards
    assert supplemental._render_activity_card("owner", []).cards
    assert supplemental._render_music_card([]).cards
    assert supplemental._render_posts_card("owner", []).cards

    stale = tmp_path / "metrics-music.svg"
    stale.write_text("old", encoding="utf-8")
    supplemental._remove_asset_if_present(tmp_path, "metrics-music")
    assert not stale.exists()

    for key in (
        "X_API_KEY",
        "X_API_KEY_SECRET",
        "X_ACCESS_TOKEN",
        "X_ACCESS_TOKEN_SECRET",
    ):
        monkeypatch.delenv(key, raising=False)
    assert supplemental._load_x_oauth1_credentials_from_env() is None
    monkeypatch.setenv("X_API_KEY", "key")
    monkeypatch.setenv("X_API_KEY_SECRET", "secret")
    monkeypatch.setenv("X_ACCESS_TOKEN", "token")
    monkeypatch.setenv("X_ACCESS_TOKEN_SECRET", "token-secret")
    assert supplemental._load_x_oauth1_credentials_from_env() is not None


def test_supplemental_full_generation_optional_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    written: list[str] = []

    class FakeBuilder:
        def __init__(self, *_args: object, **_kwargs: object) -> None:
            pass

        def render_and_write(self, name: str, _block: object) -> Path:
            written.append(name)
            return tmp_path / f"{name}.svg"

    monkeypatch.setattr(supplemental, "ReadmeSvgAssetBuilder", FakeBuilder)
    monkeypatch.setattr(supplemental, "_resolve_github_token", lambda: "token")
    monkeypatch.setattr(supplemental, "collect_github_metrics", lambda *_args: {})
    monkeypatch.setattr(supplemental, "_fetch_recent_activity", lambda *_args: [])
    monkeypatch.setattr(supplemental, "_fetch_recent_tracks", lambda *_args: [])
    credentials = supplemental.XOAuth1Credentials(
        "key", "secret", "token", "token-secret"
    )
    monkeypatch.setattr(
        supplemental, "_load_x_oauth1_credentials_from_env", lambda: credentials
    )
    monkeypatch.setattr(
        supplemental, "_fetch_latest_posts", lambda _creds: ({"username": "owner"}, [])
    )
    monkeypatch.setenv("SPOTIFY_CLIENT_ID", "client")
    monkeypatch.setenv("SPOTIFY_CLIENT_SECRET", "secret")
    monkeypatch.setenv("SPOTIFY_REFRESH_TOKEN", "refresh")
    statuses = supplemental.generate_supplemental_metrics(
        owner="owner",
        repo="repo",
        output_dir=tmp_path / "img",
        manifest_path=tmp_path / "manifest.json",
    )
    assert statuses["habits"].enabled is True
    assert statuses["activity"].enabled is False
    assert statuses["music"].enabled is True
    assert statuses["posts"].enabled is True
    assert set(written) == {
        "metrics-habits",
        "metrics-music",
        "metrics-posts",
    }

    monkeypatch.setattr(
        supplemental, "_fetch_latest_posts", lambda _creds: ({"username": "other"}, [])
    )
    with pytest.raises(RuntimeError, match="OAuth user mismatch"):
        supplemental.generate_supplemental_metrics(
            owner="owner",
            repo="repo",
            output_dir=tmp_path / "other",
            manifest_path=tmp_path / "other.json",
        )
    monkeypatch.setattr(supplemental, "_resolve_github_token", lambda: None)
    with pytest.raises(RuntimeError, match="GitHub token"):
        supplemental.generate_supplemental_metrics(
            owner="owner",
            repo="repo",
            output_dir=tmp_path / "none",
            manifest_path=tmp_path / "none.json",
        )


def test_metrics_svg_structural_validation_and_recovery(tmp_path: Path) -> None:
    assert metrics_svg._has_positive_length(None) is False
    assert metrics_svg._has_positive_length("auto") is False
    assert metrics_svg._has_positive_length("12px") is True
    assert metrics_svg._has_positive_length("0") is False

    rendered = {
        "path": '<path d="M0 0h1"/>',
        "polygon": '<polygon points="0,0 1,1"/>',
        "image": '<image href="x.png"/>',
        "rect": '<rect width="2" height="3"/>',
        "circle": '<circle r="1"/>',
        "ellipse": '<ellipse rx="1" ry="2"/>',
        "line": '<line x1="0" x2="1" y1="0" y2="0"/>',
        "g": '<g data-visible="yes"/>',
    }
    for tag, source in rendered.items():
        element = xml_etree.fromstring(source)
        assert metrics_svg._has_rendered_attributes(element, tag)
    assert not metrics_svg._has_rendered_attributes(
        xml_etree.fromstring('<text x="1"/>'), "text"
    )

    samples = {
        SvgValidationStatus.EMPTY: " ",
        SvgValidationStatus.MALFORMED: "<svg>",
        SvgValidationStatus.INVALID_ROOT: "<html><p>x</p></html>",
        SvgValidationStatus.CONTENTLESS: '<svg xmlns="http://www.w3.org/2000/svg"><g/></svg>',
        SvgValidationStatus.ERROR_PAYLOAD: (
            '<svg xmlns="http://www.w3.org/2000/svg"><text>Bad credentials</text></svg>'
        ),
        SvgValidationStatus.VALID: (
            '<svg xmlns="http://www.w3.org/2000/svg"><rect width="1" height="1"/></svg>'
        ),
    }
    for expected, source in samples.items():
        result = metrics_svg.validate_svg_content(source)
        assert result.status is expected
        assert result.to_dict()["status"] == expected.value

    directory = tmp_path / "directory"
    directory.mkdir()
    assert (
        metrics_svg.validate_svg_file(directory).status is SvgValidationStatus.MALFORMED
    )
    binary = tmp_path / "binary.svg"
    binary.write_bytes(b"\xff\xfe")
    assert metrics_svg.validate_svg_file(binary).status is SvgValidationStatus.MALFORMED

    current = tmp_path / "current.svg"
    previous = tmp_path / "previous.svg"
    current.write_text("<svg>", encoding="utf-8")
    previous.write_text(samples[SvgValidationStatus.VALID], encoding="utf-8")
    recovered = metrics_svg.recover_svg_file(current, previous)
    assert recovered.recovered and recovered.final.is_valid
    assert recovered.to_dict()["previous"] is not None
    accepted = metrics_svg.recover_svg_file(current)
    assert accepted.action is metrics_svg.SvgRecoveryAction.ACCEPTED_CURRENT
    rejected = metrics_svg.recover_svg_file(tmp_path / "missing.svg")
    assert rejected.action is metrics_svg.SvgRecoveryAction.REJECTED


def test_metrics_svg_cli_exit_codes(tmp_path: Path) -> None:
    valid = tmp_path / "valid.svg"
    valid.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg"><text>healthy</text></svg>',
        encoding="utf-8",
    )
    invalid = tmp_path / "invalid.svg"
    invalid.write_text("<svg>", encoding="utf-8")
    previous = tmp_path / "previous.svg"
    previous.write_text(valid.read_text(encoding="utf-8"), encoding="utf-8")
    assert metrics_svg.main(["validate", str(valid)]) == 0
    assert metrics_svg.main(["validate", str(invalid)]) == 1
    assert metrics_svg.main(["recover", str(invalid), "--previous", str(previous)]) == 0
    invalid.write_text("<svg>", encoding="utf-8")
    assert (
        metrics_svg.main(
            [
                "recover",
                str(invalid),
                "--previous",
                str(tmp_path / "missing-previous.svg"),
            ]
        )
        == 1
    )


def test_wakatime_parsing_github_and_formatting(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert wakatime._wakatime_auth_header("secret")["Authorization"].startswith(
        "Basic "
    )
    monkeypatch.setattr(wakatime, "_request_json", lambda *_args, **_kwargs: [])
    with pytest.raises(ValueError, match="not a JSON object"):
        wakatime.fetch_wakatime_stats("key", range_name="last 30 days")

    entries = wakatime._parse_entries(
        [None, {}, {"name": "Python", "total_seconds": 3660, "percent": 50}],
        limit=2,
    )
    assert entries[0].text == "1 hrs 1 mins"
    assert wakatime._parse_entries({}) == ()
    with pytest.raises(ValueError, match="missing data"):
        wakatime.parse_wakatime_stats({})

    monkeypatch.setattr(
        "scripts._github_http._graphql",
        lambda *_args, **_kwargs: {
            "data": {
                "user": {
                    "contributionsCollection": {
                        "contributionCalendar": {"totalContributions": "17"}
                    }
                }
            }
        },
    )
    contribution_result = wakatime._fetch_contributions_this_year("token", "owner")
    assert contribution_result is not None
    assert contribution_result[0] == 17
    monkeypatch.setattr("scripts._github_http._graphql", lambda *_args, **_kwargs: {})
    assert wakatime._fetch_contributions_this_year("token", "owner") is None

    monkeypatch.setattr(
        wakatime,
        "_request_json",
        lambda *_args, **_kwargs: {
            "login": "owner",
            "public_repos": 4,
            "owned_private_repos": 2,
            "disk_usage": 2048,
            "hireable": True,
        },
    )
    monkeypatch.setattr(
        wakatime,
        "_fetch_contributions_this_year",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(ValueError("unavailable")),
    )
    info = wakatime.fetch_github_short_info("token", login="owner")
    assert info.public_repos == 4 and info.private_repos == 2
    monkeypatch.setattr(wakatime, "_request_json", lambda *_args, **_kwargs: [])
    with pytest.raises(ValueError, match="not a JSON object"):
        wakatime.fetch_github_short_info("token")

    assert wakatime._format_duration(-1) == "0 mins"
    assert wakatime._format_duration(60) == "1 mins"
    assert wakatime._format_duration(3600) == "1 hrs"
    assert wakatime._format_bytes(10) == "10 B"
    assert wakatime._format_bytes(2048) == "2.0 KB"
    assert wakatime._format_stat_rows(()) == "No Activity Tracked This Week\n"
    assert len(wakatime._progress_bar(150)) == wakatime.BAR_WIDTH


def test_wakatime_apply_noop_errors_and_cli(tmp_path: Path) -> None:
    readme = tmp_path / "README.md"
    readme.write_text("no markers", encoding="utf-8")
    with pytest.raises(ValueError, match="markers not found"):
        wakatime.apply_waka_section(readme, "body")

    readme.write_text(
        f"{wakatime.MARKER_START}\nbody\n{wakatime.MARKER_END}\n",
        encoding="utf-8",
    )
    assert wakatime.apply_waka_section(readme, "body") is False
    empty = tmp_path / "empty.md"
    empty.write_text(" \n", encoding="utf-8")
    assert wakatime.apply_waka_artifact_to_readme(empty, readme) is False
    artifact = tmp_path / "artifact.md"
    artifact.write_text("new body", encoding="utf-8")
    assert (
        wakatime.main(["apply", "--artifact", str(artifact), "--readme", str(readme)])
        == 0
    )
    assert "new body" in readme.read_text(encoding="utf-8")


def test_fetch_metrics_collection_success_and_fallbacks(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    assert fetch_metrics._repo_languages_url(
        {"owner": {"login": "owner"}, "name": "repo"}
    ).endswith("/repos/owner/repo/languages")
    for invalid in ({}, {"full_name": "owner/repo/extra"}):
        with pytest.raises(ValueError):
            fetch_metrics._repo_languages_url(invalid)

    repos = [
        {
            "full_name": "owner/repo",
            "name": "repo",
            "fork": False,
            "stargazers_count": 10,
            "forks_count": 2,
            "language": "Python",
            "description": "desc",
            "topics": ["python"],
            "updated_at": "now",
        }
    ]

    def fake_json(url: str, _token: str | None, **_kwargs: object) -> object:
        if url.endswith("/repos/owner/repo"):
            return {
                "stargazers_count": 3,
                "forks_count": 2,
                "watchers_count": 1,
                "network_count": 4,
                "open_issues_count": 5,
            }
        if url.endswith("/users/owner"):
            return {
                "followers": 6,
                "following": 7,
                "public_repos": 8,
                "public_gists": 9,
            }
        if url.endswith("/orgs"):
            return [{"login": "org"}]
        if "stargazers" in url:
            return [{"user": {"login": "latest"}}]
        if "forks?" in url:
            return [{"owner": {"login": "forker"}}]
        return {}

    monkeypatch.setattr(fetch_metrics, "_json", fake_json)
    monkeypatch.setattr(
        fetch_metrics, "_paginate_rest", lambda *_args, **_kwargs: repos
    )
    monkeypatch.setattr(
        fetch_metrics, "_collect_languages", lambda *_args: {"Python": 10}
    )
    monkeypatch.setattr(
        fetch_metrics, "_collect_traffic", lambda *_args: {"traffic": 1}
    )
    monkeypatch.setattr(
        fetch_metrics,
        "_collect_recent_merged_prs",
        lambda *_args: [{"repo_name": "repo"}],
    )
    monkeypatch.setattr(
        fetch_metrics,
        "_collect_issue_stats",
        lambda *_args: {"open_count": 1, "closed_count": 2},
    )
    monkeypatch.setattr(
        fetch_metrics, "_collect_commit_hour_distribution", lambda *_args: ({12: 3}, 3)
    )
    monkeypatch.setattr(
        fetch_metrics, "_collect_releases", lambda *_args, **_kwargs: ([], "profile", 1)
    )
    monkeypatch.setattr(
        fetch_metrics,
        "_graphql",
        lambda *_args, **_kwargs: {
            "data": {
                "viewer": {
                    "contributionsCollection": {
                        "contributionCalendar": {
                            "totalContributions": 7,
                            "weeks": [
                                {
                                    "contributionDays": [
                                        {
                                            "date": "2026-01-01",
                                            "contributionCount": 1,
                                            "color": "#1",
                                        }
                                    ]
                                }
                            ],
                        },
                        "totalCommitContributions": 3,
                        "totalPullRequestContributions": 2,
                        "totalPullRequestReviewContributions": 1,
                        "totalIssueContributions": 4,
                        "totalRepositoryContributions": 5,
                    }
                }
            }
        },
    )
    result = fetch_metrics.collect("owner", "repo", "token")
    assert result["stars"] == 3 and result["latest_stargazer"] == "latest"
    assert result["contributions_calendar"][0]["count"] == 1

    monkeypatch.setattr(
        fetch_metrics,
        "_json",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("api")),
    )
    monkeypatch.setattr(
        fetch_metrics,
        "_paginate_rest",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("repos")),
    )
    monkeypatch.setattr(
        fetch_metrics,
        "_collect_recent_merged_prs",
        lambda *_args: (_ for _ in ()).throw(RuntimeError()),
    )
    monkeypatch.setattr(
        fetch_metrics,
        "_collect_issue_stats",
        lambda *_args: (_ for _ in ()).throw(RuntimeError()),
    )
    monkeypatch.setattr(
        fetch_metrics,
        "_collect_commit_hour_distribution",
        lambda *_args: (_ for _ in ()).throw(RuntimeError()),
    )
    monkeypatch.setattr(
        fetch_metrics,
        "_collect_releases",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError()),
    )
    fallback = fetch_metrics.collect("owner", "repo", None)
    assert fallback["orgs_count"] == 0 and fallback["recent_merged_prs"] == []

    output = tmp_path / "metrics" / "metrics.json"
    monkeypatch.setattr(
        fetch_metrics, "collect", lambda *_args, **_kwargs: {"ok": True}
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "fetch_metrics",
            "--owner",
            "owner",
            "--repo",
            "repo",
            "--output",
            str(output),
        ],
    )
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    fetch_metrics.main()
    assert json.loads(output.read_text(encoding="utf-8")) == {"ok": True}


def test_readme_remote_safety_and_clients(monkeypatch: pytest.MonkeyPatch) -> None:
    assert not readme_sections._is_safe_remote_url("file:///tmp/x")
    assert not readme_sections._is_safe_remote_url("https://user:pass@example.com/x")
    assert not readme_sections._is_safe_remote_url("http://127.0.0.1/x")
    assert not readme_sections._is_public_remote_host("service.internal")
    assert not readme_sections._is_public_remote_host("singlelabel")
    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda *_args, **_kwargs: [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 0))
        ],
    )
    assert readme_sections._is_safe_remote_url("https://example.com/x")
    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError()),
    )
    assert not readme_sections._is_safe_remote_url("https://example.com/x")

    monkeypatch.setattr(readme_sections, "_is_safe_remote_url", lambda _url: True)
    metadata_payload = {
        "full_name": "owner/repo",
        "name": "repo",
        "html_url": "https://github.com/owner/repo",
        "description": "desc",
        "stargazers_count": 4,
        "homepage": "https://example.com",
        "topics": ["python"],
        "pushed_at": "2026-01-01T00:00:00Z",
        "created_at": "2025-01-01T00:00:00Z",
        "size": 10,
        "forks_count": 2,
        "language": "Python",
        "open_graph_image_url": "https://example.com/image.png",
        "open_issues_count": 1,
        "license": {"spdx_id": "MIT"},
    }
    responses = iter(
        [
            _Response(json.dumps(metadata_payload).encode()),
            _Response(b'{"Python": 10, "Rust": 2}'),
        ]
    )
    monkeypatch.setattr(
        readme_sections, "_safe_urlopen", lambda *_args, **_kwargs: next(responses)
    )
    client = GitHubRepoClient()
    metadata = client.fetch_repo_metadata("owner/repo")
    assert metadata is not None
    assert metadata.stars == 4
    assert client.fetch_repo_languages("owner/repo") == {"Python": 10, "Rust": 2}
    monkeypatch.setattr(
        readme_sections,
        "_safe_urlopen",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("offline")),
    )
    assert client.fetch_repo_metadata("owner/repo") is None
    assert client.fetch_repo_languages("owner/repo") is None


def test_readme_feed_star_history_and_metadata_clients(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(readme_sections, "_is_safe_remote_url", lambda _url: True)
    rss = (
        b"<rss><channel><item><title>Post</title>"
        b"<link>https://example.com/post</link>"
        b'<enclosure url="https://example.com/image.png" type="image/png"/>'
        b"</item><item><title></title></item></channel></rss>"
    )
    atom = (
        b'<feed xmlns="http://www.w3.org/2005/Atom"><entry>'
        b"<title>Atom Post</title>"
        b'<link rel="alternate" href="https://example.com/atom"/>'
        b"</entry></feed>"
    )
    monkeypatch.setattr(
        readme_sections, "_safe_urlopen", lambda *_args, **_kwargs: _Response(rss)
    )
    assert (
        BlogFeedClient().fetch_latest_posts("https://example.com/rss", 2)[0].image_url
    )
    monkeypatch.setattr(
        readme_sections, "_safe_urlopen", lambda *_args, **_kwargs: _Response(atom)
    )
    assert (
        BlogFeedClient().fetch_latest_posts("https://example.com/atom", 2)[0].title
        == "Atom Post"
    )
    monkeypatch.setattr(
        readme_sections,
        "_safe_urlopen",
        lambda *_args, **_kwargs: _Response(b"not xml"),
    )
    assert BlogFeedClient().fetch_latest_posts("https://example.com/bad", 2) == []

    assert StarHistoryClient().fetch_star_history("invalid") is None
    star_payload = {
        "data": {
            "repository": {
                "stargazers": {
                    "edges": [
                        {"starredAt": "2026-01-01T00:00:00Z"},
                        {"starredAt": "bad"},
                    ],
                    "pageInfo": {"hasNextPage": False},
                }
            }
        }
    }
    monkeypatch.setattr(
        readme_sections,
        "_safe_urlopen",
        lambda *_args, **_kwargs: _Response(json.dumps(star_payload).encode()),
    )
    history = StarHistoryClient().fetch_star_history(
        "owner/repo", sample=4, series_start=datetime(2025, 1, 1)
    )
    assert history is not None and len(history) == 4 and history[-1] == 1
    error_payload = {"errors": [{"message": "no"}]}
    monkeypatch.setattr(
        readme_sections,
        "_safe_urlopen",
        lambda *_args, **_kwargs: _Response(json.dumps(error_payload).encode()),
    )
    assert StarHistoryClient().fetch_star_history("owner/repo") is None

    html = (
        b'<html><meta content="hero.png" property="og:image">'
        b'<meta name="description" content="summary">'
        b'<meta property="article:published_time" content="2026-01-01">'
        b"</html>"
    )
    monkeypatch.setattr(
        readme_sections, "_safe_urlopen", lambda *_args, **_kwargs: _Response(html)
    )
    metadata = BlogMetadataClient().fetch_metadata("https://www.example.com/post")
    assert metadata == {
        "hero_image": "hero.png",
        "summary": "summary",
        "published": "2026-01-01",
        "host": "example.com",
    }


def test_readme_generator_low_level_fallbacks(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    settings = ReadmeSectionsSettings(readme_path=str(tmp_path / "missing.md"))
    generator = ReadmeSectionGenerator(settings=settings)
    assert generator.generate() == tmp_path / "missing.md"
    assert generator._svg_asset_src(" odd name! ").endswith("odd-name.svg")
    assert generator._svg_asset_src("!!!").endswith("section.svg")
    assert (
        generator._slugify_asset_segment(
            "Hello World", fallback="fallback", max_length=7
        )
        == "hello-w"
    )
    assert generator._slugify_asset_segment("!!!", fallback="fallback") == "fallback"

    card = readme_sections.SvgCard(
        title="Same title", lines=("line",), url="https://example.com/one"
    )
    used: set[str] = set()
    first = generator._make_blog_asset_name(card=card, index=1, used_assets=used)
    second = generator._make_blog_asset_name(card=card, index=2, used_assets=used)
    assert first != second
    assert "temporarily unavailable" in generator._build_featured_repo_fallback_line(
        "owner/repo", None
    )

    metadata = RepoMetadata(
        full_name="owner/repo",
        name="repo",
        html_url="https://github.com/owner/repo",
        description="description",
        stars=12,
        homepage=None,
        topics=["python", "ai"],
        updated_at=None,
    )
    assert "★ 12" in generator._build_featured_repo_fallback_line(
        "owner/repo", metadata
    )
    assert generator._repo_accent_color(metadata) == "3776AB"
    assert generator._build_star_history_points("owner/repo", None) is None
    assert generator._parse_iso_datetime("bad") is None
    assert generator._parse_iso_datetime("2026-01-01T00:00:00") is not None
    assert generator._format_timestamp(None) is None
    assert generator._format_timestamp("2026-01-01T02:03:04Z") == "2026-01-01"
    assert generator._relative_time(None) is None
    assert generator._relative_time("bad") is None

    monkeypatch.setattr(
        readme_sections, "_build_remote_get_request", lambda **_kwargs: None
    )
    assert generator._scrape_repo_og_image("owner/repo") is None
    assert (
        generator._fetch_remote_image_data_uri("https://example.com/x", "test") is None
    )


def test_generate_all_orchestrates_success_failure_and_skips(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    metrics = tmp_path / "metrics.json"
    history = tmp_path / "history.json"
    metrics.write_text("{}", encoding="utf-8")
    history.write_text("{}", encoding="utf-8")
    calls: list[str] = []

    class Commands:
        def __getattr__(self, name: str):
            def command(**_kwargs: object) -> None:
                calls.append(name)

            return command

    monkeypatch.setattr(all_cmd, "_cmds", lambda: Commands())
    monkeypatch.setenv("GITHUB_TOKEN", "token")
    all_cmd.all_assets(
        output_path=tmp_path,
        metrics_path=metrics,
        history_path=history,
        skills_path=tmp_path / "skills.yaml",
    )
    assert {"banner", "qr", "word_cloud", "supplemental_metrics", "living_art"} <= set(
        calls
    )

    class FailCommands:
        def __getattr__(self, _name: str):
            def command(**_kwargs: object) -> None:
                raise typer.Exit(code=1)

            return command

    monkeypatch.setattr(all_cmd, "_cmds", lambda: FailCommands())
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("GH_TOKEN", raising=False)
    monkeypatch.delenv("METRICS_TOKEN", raising=False)
    all_cmd.all_assets(metrics_path=None, history_path=None)
