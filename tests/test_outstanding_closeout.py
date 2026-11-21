"""Contracts for the outstanding-work closeout facts."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]


def test_lowlighter_svgs_are_absent_and_docs_do_not_keep_them() -> None:
    for name in ("metrics.svg", "metrics.additional.svg", "metrics.extra.svg"):
        assert not (REPO / ".github/assets/img" / name).is_file()
    workflows = (REPO / "docs/content/docs/workflows/index.mdx").read_text()
    assert "may remain" not in workflows
    assert "not generated, uploaded, embedded, or kept" in workflows


def test_generative_svgs_are_present() -> None:
    img = REPO / ".github/assets/img"
    for name in (
        "generative-activity.svg",
        "generative-activity-dark.svg",
        "generative-community.svg",
        "generative-community-dark.svg",
    ):
        assert (img / name).is_file(), name
    showcase = REPO / "docs/public/showcase"
    assert (showcase / "generative-activity.svg").is_file()
    assert (showcase / "generative-community.svg").is_file()


def test_banner_defaults_match_pinned_svg() -> None:
    from scripts.banner import BannerConfig

    config = BannerConfig()
    assert config.width == 1600
    assert config.height == 480
    text = (REPO / ".github/assets/img/banner.svg").read_text(encoding="utf-8")[:400]
    assert 'width="1600"' in text
    assert 'height="480"' in text


def test_schedule_docs_name_the_default_branch() -> None:
    text = (REPO / "docs/content/docs/workflows/index.mdx").read_text()
    assert (
        "A GitHub `schedule` event loads the workflow file on the default "
        "branch, which is `main`, until an explicit cutover."
    ) in text
    assert "default branch, which is `main`" in text
    workflow = (REPO / ".github/workflows/profile-updater.yml").read_text()
    triggers = workflow.split("jobs:", maxsplit=1)[0]
    assert "refs/heads/dev" in workflow
    assert "\n      - main\n" not in triggers


def test_false_doc_commands_are_gone() -> None:
    index = (REPO / "docs/content/docs/index.mdx").read_text()
    assert "scripts/word_clouds.py" not in index
    assert "scripts/animated_art.py" not in index
    agents = (REPO / "tests/AGENTS.md").read_text()
    assert "TestQRCodeGenerator::test_init_success" not in agents
    testing = (REPO / "docs/content/docs/development/testing.mdx").read_text()
    assert "from scripts.art.ink_garden import generate, seed_hash" not in testing
    generate = (REPO / "docs/content/docs/cli/generate.mdx").read_text()
    assert "case-insensitive" not in generate
    history = (REPO / "docs/content/docs/data/fetch-history.mdx").read_text()
    assert "stars_last_30d" not in history
    assert "starred_at" not in history
    rule = (
        REPO / ".cursor/rules/05-python-versioning-and-dependencies.mdc"
    ).read_text()
    assert "3.10" not in rule
    assert "requirements.txt" not in rule
    assert "DEFAULT_MASK_PATH" not in (REPO / "scripts/AGENTS.md").read_text()


def test_probe_does_not_upload_or_forward_metrics_token() -> None:
    workflow = (REPO / ".github/workflows/profile-updater.yml").read_text()
    probe = workflow.split("probe-full-metrics:", maxsplit=1)[1].split(
        "\n  update-starred-lists:",
        maxsplit=1,
    )[0]
    assert "metrics-probe-" not in probe
    lowlighter = probe.split("uses: lowlighter/metrics@", maxsplit=1)[1]
    assert "secrets.METRICS_TOKEN" not in lowlighter
    assert "token: ${{ github.token }}" in probe


def test_wakatime_other_owner_short_name_is_not_public() -> None:
    from scripts.wakatime_readme import is_publishable_project

    allowed = ("docs", "wyattowalsh/docs", "wyattowalsh/wyattowalsh")
    assert (
        is_publishable_project("other-owner/docs", public_repo_names=allowed) is False
    )
    assert (
        is_publishable_project(
            "wyattowalsh/wyattowalsh",
            public_repo_names=allowed,
        )
        is True
    )
    assert (
        is_publishable_project(
            "wyattowalsh/docs",
            public_repo_names=allowed,
        )
        is True
    )
    public = ("wyattowalsh/docs",)
    assert is_publishable_project("docs", public_repo_names=public) is True
    assert is_publishable_project("wyattowalsh/docs", public_repo_names=public) is True
    assert is_publishable_project("other-owner/docs", public_repo_names=public) is False
    assert (
        is_publishable_project("other-owner/docs", public_repo_names=("docs",))
        is False
    )
    assert (
        is_publishable_project("other-owner/docs", project_allowlist=("docs",))
        is False
    )
    assert is_publishable_project("docs", project_allowlist=("docs",)) is True


def test_spotify_callback_host_is_loopback_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from scripts.spotify_auth import mint_spotify_refresh_token

    with pytest.raises(ValueError, match="callback host"):
        mint_spotify_refresh_token(
            client_id="id",
            client_secret="secret",
            callback_host="0.0.0.0",
        )

    redirects: list[str] = []

    def _wait(**kwargs: object) -> str:
        redirects.append(str(kwargs["redirect_uri"]))
        return "code"

    def _exchange(**_kwargs: object) -> dict[str, str]:
        return {"refresh_token": "loopback-ok"}

    monkeypatch.setattr(
        "scripts.spotify_auth._wait_for_spotify_authorization_code",
        _wait,
    )
    monkeypatch.setattr(
        "scripts.spotify_auth.exchange_spotify_authorization_code",
        _exchange,
    )
    expected_redirects = {
        "127.0.0.1": "http://127.0.0.1:8888/callback",
        "localhost": "http://127.0.0.1:8888/callback",
        "::1": "http://[::1]:8888/callback",
    }
    for host, redirect_uri in expected_redirects.items():
        token, _url = mint_spotify_refresh_token(
            client_id="id",
            client_secret="secret",
            callback_host=host,
            open_browser=False,
        )
        assert token == "loopback-ok"
        assert redirects[-1] == redirect_uri


def test_console_log_level_follows_env(monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts.utils import console_log_level

    monkeypatch.delenv("LOG_LEVEL", raising=False)
    monkeypatch.delenv("DEBUG_MODE", raising=False)
    assert console_log_level() == "INFO"
    monkeypatch.setenv("LOG_LEVEL", "warning")
    assert console_log_level() == "WARNING"
    for flag in ("1", "true", "yes", "on"):
        monkeypatch.setenv("DEBUG_MODE", flag)
        assert console_log_level() == "DEBUG"


def test_gitignore_covers_spotify_refresh_token() -> None:
    assert "spotify_refresh_token.txt" in (REPO / ".gitignore").read_text()


def test_six_styles_and_no_accepted_key() -> None:
    from scripts.art.roster import CANDIDATE_STYLE_KEYS, SHIPPED_STYLE_KEYS

    assert SHIPPED_STYLE_KEYS is CANDIDATE_STYLE_KEYS
    assert len(SHIPPED_STYLE_KEYS) == 6
    bakeoff = json.loads((REPO / "goals/living-art-overhaul/bakeoff.json").read_text())
    assert "accepted" not in bakeoff


def test_blog_fetch_failure_keeps_the_existing_block(tmp_path: Path) -> None:
    from typing import Any, cast

    from scripts.config import ReadmeSectionsSettings
    from scripts.readme_sections import BlogPost, BlogPostSource, ReadmeSectionGenerator

    class FailedFeed:
        def fetch_latest_posts(
            self,
            feed_url: str,
            limit: int,
        ) -> list[BlogPost] | None:
            return None

    class EmptyFeed:
        def fetch_latest_posts(self, feed_url: str, limit: int) -> list[BlogPost]:
            return []

    readme = tmp_path / "README.md"
    block = "<!-- README:BLOG_POSTS:START -->\nkeep me\n<!-- README:BLOG_POSTS:END -->"
    readme.write_text(block, encoding="utf-8")
    failed = ReadmeSectionGenerator(
        settings=ReadmeSectionsSettings(readme_path=str(readme)),
        blog_client=cast(BlogPostSource, FailedFeed()),
    )
    assert failed._render_blog_posts() is None
    missing_render: Any = None
    assert "keep me" in failed._inject_block(
        block,
        failed.BLOG_START,
        failed.BLOG_END,
        missing_render,
    )
    empty = ReadmeSectionGenerator(
        settings=ReadmeSectionsSettings(readme_path=str(readme)),
        blog_client=EmptyFeed(),
    )
    rendered = empty._render_blog_posts()
    assert rendered is not None
    assert "No recent posts available." in rendered


def test_animated_unknown_profile_exits_nonzero(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import sys

    from scripts.art import animate

    monkeypatch.setattr(sys, "argv", ["animate", "--profile", "wyattowalsh"])
    with pytest.raises(SystemExit) as exc:
        animate.main()
    assert exc.value.code == 1


def test_supplemental_metrics_fail_when_collection_fails(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    import scripts.supplemental_metrics as supplemental

    monkeypatch.setenv("GITHUB_TOKEN", "token")
    monkeypatch.setattr(
        supplemental,
        "collect_github_metrics",
        lambda *_args, **_kwargs: {
            "collection_failures": ["languages"],
            "languages": {},
        },
    )
    with pytest.raises(RuntimeError, match="Language totals"):
        supplemental.generate_supplemental_metrics(
            owner="owner",
            repo="repo",
            output_dir=tmp_path,
            manifest_path=tmp_path / "manifest.json",
        )

    monkeypatch.setattr(
        supplemental,
        "collect_github_metrics",
        lambda *_args, **_kwargs: {
            "collection_failures": ["contributions_calendar"],
            "languages": {"Python": 1},
            "contributions_calendar": [],
        },
    )
    with pytest.raises(RuntimeError, match="Contribution calendar"):
        supplemental.generate_supplemental_metrics(
            owner="owner",
            repo="repo",
            output_dir=tmp_path,
            manifest_path=tmp_path / "manifest.json",
        )


def test_utils_imports_os_before_sys() -> None:
    lines = (REPO / "scripts/utils.py").read_text(encoding="utf-8").splitlines()
    os_line = next(index for index, line in enumerate(lines) if line == "import os")
    sys_line = next(
        index for index, line in enumerate(lines) if line.startswith("import sys")
    )
    assert os_line < sys_line


def test_mock_profiles_include_wyatt_and_prolific() -> None:
    from scripts.art._dev_profiles import PROFILES

    assert {"wyatt", "prolific"} <= set(PROFILES)


def test_animated_metrics_keep_unknown_profile_and_disable_timeline(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    import sys

    from scripts.art import animate
    from scripts.art.roster import CANDIDATE_STYLE_KEYS

    monkeypatch.chdir(tmp_path)
    assert Path.cwd() == tmp_path.resolve()
    calls: dict[str, list[dict[str, object]]] = {}

    def _bind(style: str):
        def _generate(_target: object, **kwargs: object) -> str:
            calls.setdefault(style, []).append(dict(kwargs))
            return (
                '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
                "<defs></defs><g/></svg>"
            )

        return _generate

    monkeypatch.setattr(
        animate,
        "_GROWTH_GENERATORS",
        {style: _bind(style) for style in CANDIDATE_STYLE_KEYS},
    )
    monkeypatch.setattr(animate, "compute_maturity", lambda _metrics: 0.42)
    metrics = tmp_path / "metrics.json"
    metrics.write_text('{"stars": 3}\n', encoding="utf-8")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "animate",
            "--svg",
            "--frames",
            "2",
            "--profile",
            "not-a-profile",
            "--metrics-path",
            str(metrics),
        ],
    )

    animate.main()

    assert set(calls) == set(CANDIDATE_STYLE_KEYS)
    for style, frames in calls.items():
        assert len(frames) == 2
        assert all(frame["timeline"] is False for frame in frames)
        if style == "topo":
            assert all(frame["chrome_maturity"] == 0.42 for frame in frames)
        else:
            assert all("chrome_maturity" not in frame for frame in frames)
    assert (tmp_path / ".github/assets/img/topo-growth-animated.svg").is_file()


def test_word_cloud_filenames_renderer_and_output_path(tmp_path: Path) -> None:
    from types import SimpleNamespace

    from scripts.cli.generate.word_cloud import (
        _default_word_cloud_output,
        _wc_from_languages,
        _wc_from_prompt,
        _wc_from_techs,
        _wc_from_topics,
    )

    fresh = '<svg xmlns="http://www.w3.org/2000/svg" id="fresh"/>'
    old = '<svg xmlns="http://www.w3.org/2000/svg" id="old"/>'

    class _Settings:
        renderer: str

        def __init__(self, **kwargs: object) -> None:
            for key, value in kwargs.items():
                setattr(self, key, value)
            renderer = kwargs.get("renderer", "")
            self.renderer = renderer if isinstance(renderer, str) else str(renderer)

        @classmethod
        def from_yaml_model(
            cls,
            _model: object = None,
            **kwargs: object,
        ) -> _Settings:
            return cls(
                **{key: value for key, value in kwargs.items() if value is not None}
            )

    class _Generator:
        last: _Settings | None = None

        def __init__(self, base_settings: _Settings) -> None:
            type(self).last = base_settings

        def generate(self, **kwargs: object) -> Path:
            output = Path(str(kwargs["output_path"]))
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(fresh, encoding="utf-8")
            return output

    topics = tmp_path / "topics.md"
    languages = tmp_path / "languages.md"
    topics.write_text("- python\n", encoding="utf-8")
    languages.write_text("- python\n", encoding="utf-8")
    wc = SimpleNamespace(
        TOPICS_MD_PATH=topics,
        LANGUAGES_MD_PATH=languages,
        PROFILE_IMG_OUTPUT_DIR=tmp_path,
        parse_markdown_for_word_cloud_frequencies=lambda _path: {"python": 4},
        load_technologies=lambda _path: [SimpleNamespace(name="Python", level=4)],
        WordCloudSettings=_Settings,
        WordCloudGenerator=_Generator,
    )
    typographic_topics = tmp_path / "wordcloud_typographic_by_topics.svg"
    typographic_languages = tmp_path / "wordcloud_typographic_by_languages.svg"
    typographic_topics.write_text(old, encoding="utf-8")
    typographic_languages.write_text(old, encoding="utf-8")

    assert _wc_from_topics(wc, None, [], 10) == typographic_topics
    assert _wc_from_languages(wc, None, [], 10) == typographic_languages
    assert typographic_topics.read_text(encoding="utf-8") == fresh
    assert typographic_languages.read_text(encoding="utf-8") == fresh

    typographic_topics.write_text(old, encoding="utf-8")
    typographic_languages.write_text(old, encoding="utf-8")
    shaped_topics = tmp_path / "wordcloud_shaped_by_topics.svg"
    shaped_languages = tmp_path / "wordcloud_shaped_by_languages.svg"
    assert _wc_from_topics(wc, None, [], 10, renderer="shaped") == shaped_topics
    assert _wc_from_languages(wc, None, [], 10, renderer="shaped") == shaped_languages
    assert typographic_topics.read_text(encoding="utf-8") == old
    assert typographic_languages.read_text(encoding="utf-8") == old
    assert shaped_topics.read_text(encoding="utf-8") == fresh
    assert shaped_languages.read_text(encoding="utf-8") == fresh

    chosen = tmp_path / "chosen.svg"
    shaped_before = shaped_topics.read_text(encoding="utf-8")
    assert _wc_from_topics(wc, chosen, [], 10, renderer="shaped") == chosen
    assert chosen.read_text(encoding="utf-8") == fresh
    assert shaped_topics.read_text(encoding="utf-8") == shaped_before

    yaml_settings = SimpleNamespace(output_dir=str(tmp_path))
    techs = tmp_path / "techs.md"
    techs.write_text("python\n", encoding="utf-8")
    fractal = tmp_path / "wordcloud_fractal_by_techs.svg"
    assert (
        _wc_from_techs(
            wc,
            techs,
            None,
            [],
            10,
            yaml_settings=yaml_settings,
            renderer="fractal",
        )
        == fractal
    )
    assert _Generator.last is not None
    assert _Generator.last.renderer == "fractal"
    prompt = tmp_path / "wordcloud_wordle_by_prompt.svg"
    assert (
        _wc_from_prompt(
            wc,
            "python, rust",
            None,
            [],
            10,
            yaml_settings=yaml_settings,
            renderer="wordle",
        )
        == prompt
    )
    assert _Generator.last.renderer == "wordle"
    assert (
        _default_word_cloud_output(
            SimpleNamespace(renderer="shaped", output_dir=tmp_path),
            "topics",
        )
        == tmp_path / "wordcloud_shaped_by_topics.svg"
    )
    assert (
        _default_word_cloud_output(
            SimpleNamespace(renderer="typographic", output_dir=tmp_path),
            "languages",
        )
        == tmp_path / "wordcloud_typographic_by_languages.svg"
    )


def test_word_cloud_command_forwards_renderer(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import importlib
    from types import SimpleNamespace

    cli_word_cloud = importlib.import_module("scripts.cli.generate.word_cloud")

    class _ConfigModel:
        stopwords: list[str] = []
        prompt: str | None = None

        def to_word_cloud_settings(self) -> object:
            return SimpleNamespace(max_words=10, layout_readability=None)

        def model_dump(self, **_kwargs: object) -> dict[str, object]:
            return {}

    monkeypatch.setattr(
        cli_word_cloud,
        "_load_project_config",
        lambda _path: SimpleNamespace(word_cloud_settings=_ConfigModel()),
    )
    monkeypatch.setattr(cli_word_cloud, "_wc_import", lambda: SimpleNamespace())
    seen: list[tuple[str, object, object]] = []

    def _publish(path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            '<svg xmlns="http://www.w3.org/2000/svg"/>',
            encoding="utf-8",
        )
        return path

    def _topics(*args: object, **kwargs: object) -> Path:
        seen.append(("topics", args[1], kwargs.get("renderer")))
        return _publish(tmp_path / "topics.svg")

    def _languages(*args: object, **kwargs: object) -> Path:
        seen.append(("languages", args[1], kwargs.get("renderer")))
        return _publish(tmp_path / "languages.svg")

    def _techs(*args: object, **kwargs: object) -> Path:
        seen.append(("techs", args[2], kwargs.get("renderer")))
        return _publish(Path(str(args[2])))

    def _prompt(*args: object, **kwargs: object) -> Path:
        seen.append(("prompt", args[2], kwargs.get("renderer")))
        return _publish(tmp_path / "prompt.svg")

    monkeypatch.setattr(cli_word_cloud, "_wc_from_topics", _topics)
    monkeypatch.setattr(cli_word_cloud, "_wc_from_languages", _languages)
    monkeypatch.setattr(cli_word_cloud, "_wc_from_techs", _techs)
    monkeypatch.setattr(cli_word_cloud, "_wc_from_prompt", _prompt)

    cli_word_cloud.word_cloud(from_topics_md=True, renderer="shaped")
    cli_word_cloud.word_cloud(from_languages_md=True, renderer="fractal")
    techs = tmp_path / "techs.md"
    techs.write_text("python\n", encoding="utf-8")
    chosen = tmp_path / "chosen.svg"
    cli_word_cloud.word_cloud(
        techs_path=techs,
        output_path=chosen,
        renderer="wordle",
    )
    cli_word_cloud.word_cloud(prompt="python, rust", renderer="clustered")

    assert seen == [
        ("topics", None, "shaped"),
        ("languages", None, "fractal"),
        ("techs", chosen, "wordle"),
        ("prompt", None, "clustered"),
    ]


def test_preview_generative_passes_fixture_metrics(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from scripts.cli.preview import PreviewTarget, preview

    captured: dict[str, object] = {}

    def _generative(**kwargs: object) -> None:
        captured.update(kwargs)

    monkeypatch.setattr("scripts.cli.generate.generative_art", _generative)
    output = tmp_path / "preview"
    preview(PreviewTarget.GENERATIVE, output_dir=output, keep=True)

    metrics = output / "preview-metrics.json"
    assert metrics.read_text(encoding="utf-8") == (
        '{"repos": [], "stars": 1, "languages": {"Python": 10}}\n'
    )
    assert Path(str(captured["output_path"])).resolve() == output.resolve()
    assert Path(str(captured["metrics_path"])).resolve() == metrics.resolve()


def test_generate_all_wakatime_follows_api_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import scripts.cli.generate.all_cmd as all_cmd

    calls: list[str] = []
    printed: list[object] = []

    class _Commands:
        def __getattr__(self, name: str):
            def _command(**_kwargs: object) -> None:
                calls.append(name)

            return _command

    def _texts() -> list[str]:
        rendered: list[str] = []
        for item in printed:
            renderable = getattr(item, "renderable", None)
            rendered.append(item if isinstance(item, str) else str(renderable))
        return rendered

    def _wakatime_summary(texts: list[str]) -> str:
        for text in texts:
            for line in text.splitlines():
                if line.strip().startswith("WakaTime"):
                    return line
        return ""

    monkeypatch.setattr(all_cmd, "_cmds", lambda: _Commands())
    monkeypatch.setattr(
        all_cmd.console,
        "print",
        lambda *args, **_kwargs: printed.append(args[0] if args else ""),
    )
    for name in ("GITHUB_TOKEN", "GH_TOKEN", "METRICS_TOKEN", "WAKATIME_API_KEY"):
        monkeypatch.delenv(name, raising=False)

    all_cmd.all_assets()
    absent = _texts()
    assert "wakatime" not in calls
    assert any("WAKATIME_API_KEY is not set" in text for text in absent)
    assert "SKIPPED" in _wakatime_summary(absent)

    printed.clear()
    calls.clear()
    monkeypatch.setenv("WAKATIME_API_KEY", "   ")
    all_cmd.all_assets()
    blank = _texts()
    assert "wakatime" not in calls
    assert any("WAKATIME_API_KEY is not set" in text for text in blank)
    assert "SKIPPED" in _wakatime_summary(blank)

    printed.clear()
    calls.clear()
    monkeypatch.setenv("WAKATIME_API_KEY", "present")
    all_cmd.all_assets()
    present = _texts()
    assert calls.count("wakatime") == 1
    assert all("WAKATIME_API_KEY is not set" not in text for text in present)
    assert "OK" in _wakatime_summary(present)
    assert "SKIPPED" not in _wakatime_summary(present)


def test_cli_readme_and_skills_use_strict_markers(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from types import SimpleNamespace

    from scripts.cli.generate import readme_cmd
    from scripts.config import ReadmeSectionsSettings, SkillsSettings

    seen: dict[str, object] = {}

    class _Skills:
        def __init__(self, settings: object) -> None:
            self.settings = settings

        def generate(self, *, strict: bool = False) -> Path:
            seen["skills_strict"] = strict
            return tmp_path / "README.md"

    class _Sections:
        def __init__(self, settings: ReadmeSectionsSettings) -> None:
            self.settings = settings

        def generate(self, *, require_markers: bool = False) -> Path:
            seen["require_markers"] = require_markers
            seen["readme_path"] = Path(self.settings.readme_path)
            return Path(self.settings.readme_path)

    monkeypatch.setattr(readme_cmd, "_load_project_config", lambda _path: object())
    monkeypatch.setattr(readme_cmd, "load_skills", lambda _path: SkillsSettings())
    monkeypatch.setattr("scripts.skills.SkillsBadgeGenerator", _Skills)
    readme_cmd.skills(skills_path=tmp_path / "skills.yaml")
    assert seen["skills_strict"] is True

    monkeypatch.setattr(
        readme_cmd,
        "_load_project_config",
        lambda _path: SimpleNamespace(
            readme_sections_settings=ReadmeSectionsSettings()
        ),
    )
    monkeypatch.setattr(
        "scripts.readme_sections.ReadmeSectionGenerator",
        _Sections,
    )
    output = tmp_path / "README.md"
    readme_cmd.readme_sections(output_path=output)
    assert seen["require_markers"] is True
    assert seen["readme_path"] == output


def test_library_defaults_warn_and_return(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import inspect

    from scripts.config import ReadmeSectionsSettings, SkillsSettings
    from scripts.readme_sections import ReadmeSectionGenerator
    from scripts.skills import SkillsBadgeGenerator

    require_markers = inspect.signature(ReadmeSectionGenerator.generate).parameters[
        "require_markers"
    ]
    strict = inspect.signature(SkillsBadgeGenerator.generate).parameters["strict"]
    assert require_markers.default is False
    assert strict.default is False

    missing = tmp_path / "missing.md"
    warnings: list[str] = []

    def _warning(*args: object, **_kwargs: object) -> None:
        if args:
            warnings.append(str(args[0]))

    monkeypatch.setattr("scripts.readme_sections.logger.warning", _warning)
    generator = ReadmeSectionGenerator(
        settings=ReadmeSectionsSettings(readme_path=str(missing))
    )
    assert generator.generate() == missing
    assert not missing.exists()
    assert any("skipping injection" in message for message in warnings)

    original = "no markers\n"
    kept = generator._inject_block(
        original,
        generator.TOP_BADGES_START,
        generator.TOP_BADGES_END,
        "fresh badges",
    )
    assert kept == original
    assert any("Markers not found" in message for message in warnings)
    with pytest.raises(FileNotFoundError, match="README not found"):
        generator.generate(require_markers=True)

    readme = tmp_path / "skills.md"
    readme.write_text(original, encoding="utf-8")
    skills = SkillsBadgeGenerator(
        settings=SkillsSettings(readme_path=str(readme), categories=[])
    )
    assert skills.generate() == readme
    assert readme.read_text(encoding="utf-8") == original
    with pytest.raises(FileNotFoundError, match="Skills markers were not replaced"):
        skills.generate(strict=True)
    assert readme.read_text(encoding="utf-8") == original


def test_missing_secrets_omit_spotify_x_and_wakatime_cards(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from datetime import UTC, datetime, timedelta

    from scripts._publish_metrics import MANIFEST_NAME, publish_metrics
    from scripts.cli.generate.readme_cmd import wakatime
    from scripts.profile_metric_family import metric_files
    from scripts.supplemental_metrics import generate_supplemental_metrics
    from scripts.wakatime_readme import (
        DEFAULT_ARTIFACT_NAME,
        MARKER_END,
        MARKER_START,
        SKIP_MARKER_NAME,
        WAKA_SVG_POINTER,
        WakaCollection,
        WakaWeekStats,
        generate_waka_section,
    )
    from scripts.wakatime_svg import generate_wakatime_svg

    today = datetime.now(UTC).date()
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("GITHUB_TOKEN", "token")
    for name in (
        "SPOTIFY_CLIENT_ID",
        "SPOTIFY_CLIENT_SECRET",
        "SPOTIFY_REFRESH_TOKEN",
        "X_API_KEY",
        "X_API_KEY_SECRET",
        "X_ACCESS_TOKEN",
        "X_ACCESS_TOKEN_SECRET",
        "WAKATIME_API_KEY",
    ):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(
        "scripts.supplemental_metrics.collect_github_metrics",
        lambda *_args, **_kwargs: {
            "languages": {"Python": 1000},
            "contributions_calendar": [
                {
                    "date": (today - timedelta(days=index)).isoformat(),
                    "count": 3,
                    "color": "#1f6feb",
                }
                for index in range(3)
            ],
            "recent_merged_prs": [{"repo_name": "agents"}],
            "pr_review_count": 1,
            "public_repos": 2,
            "commit_hour_distribution": {14: 4},
            "collection_failures": [],
        },
    )
    output_dir = tmp_path / "img"
    output_dir.mkdir()
    (output_dir / "metrics-music.svg").write_text("stale", encoding="utf-8")
    (output_dir / "metrics-posts.svg").write_text("stale", encoding="utf-8")
    statuses = generate_supplemental_metrics(
        owner="owner",
        repo="repo",
        output_dir=output_dir,
        manifest_path=output_dir / MANIFEST_NAME,
    )
    assert statuses["music"].enabled is False
    assert statuses["music"].reason == "spotify-secrets-missing"
    assert statuses["posts"].enabled is False
    assert statuses["posts"].reason == "x-oauth1-secrets-missing"
    assert not (output_dir / "metrics-music.svg").exists()
    assert not (output_dir / "metrics-posts.svg").exists()
    assert (output_dir / "metrics-languages.svg").is_file()
    assert (output_dir / "metrics-habits.svg").is_file()

    waka_dir = tmp_path / "waka"
    wakatime(output_dir=waka_dir, allow_missing_key=True)
    assert (waka_dir / SKIP_MARKER_NAME).is_file()
    assert "WAKATIME_API_KEY missing" in (waka_dir / SKIP_MARKER_NAME).read_text(
        encoding="utf-8"
    )
    assert not (waka_dir / DEFAULT_ARTIFACT_NAME).exists()
    assert not (waka_dir / "wakatime.svg").exists()
    with pytest.raises(ValueError, match="WAKATIME_API_KEY"):
        generate_waka_section()
    readme = tmp_path / "README.md"
    readme.write_text(f"{MARKER_START}\nold link\n{MARKER_END}\n", encoding="utf-8")
    published = tmp_path / ".github/assets/img"
    published.mkdir(parents=True)
    optional = (*metric_files("metrics-music"), "metrics-posts.svg")
    for name in ("wakatime.svg", *optional):
        (published / name).write_bytes(b"stale")
    before = {file.name: file.read_bytes() for file in published.iterdir()}
    old_readme = readme.read_bytes()
    with pytest.raises(ValueError, match="Incomplete profile metric family: wakatime"):
        publish_metrics(output_dir, waka_dir, readme)
    assert {file.name: file.read_bytes() for file in published.iterdir()} == before
    assert readme.read_bytes() == old_readme

    generate_wakatime_svg(
        collection=WakaCollection(week=WakaWeekStats("UTC", (), (), (), ())),
        output_path=published / "wakatime.svg",
        include_github=False,
        updated_at=datetime(2026, 8, 27, tzinfo=UTC),
    )
    saved = {name: (published / name).read_bytes() for name in metric_files("wakatime")}
    publish_metrics(output_dir, waka_dir, readme)
    expected = dict(saved)
    for metric in ("metrics-languages", "metrics-habits"):
        for name in metric_files(metric):
            expected[name] = (output_dir / name).read_bytes()
    assert {file.name: file.read_bytes() for file in published.iterdir()} == expected
    assert readme.read_text(encoding="utf-8") == (
        f"{MARKER_START}\n{WAKA_SVG_POINTER}\n{MARKER_END}\n"
    )
    workflow = (REPO / ".github/workflows/profile-updater.yml").read_text()
    assert "--allow-missing-key" in workflow
    assert "python -m scripts._publish_metrics" in workflow


def test_preview_skills_writes_a_copy(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from scripts.cli.preview import PreviewTarget, preview
    from scripts.config import SkillsSettings

    source = tmp_path / "README.md"
    source.write_text("skills source\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    seen: list[Path] = []

    def _generate(self: object) -> Path:
        settings = getattr(self, "settings")
        path = Path(str(settings.readme_path))
        seen.append(path)
        assert path.read_text(encoding="utf-8") == "skills source\n"
        return path

    monkeypatch.setattr("scripts.config.load_skills", lambda: SkillsSettings())
    monkeypatch.setattr("scripts.skills.SkillsBadgeGenerator.generate", _generate)
    output = tmp_path / "preview"
    preview(PreviewTarget.SKILLS, output_dir=output, keep=True)

    copied = output / "README.md"
    assert seen
    assert seen[0].resolve() == copied.resolve()
    assert copied.read_text(encoding="utf-8") == "skills source\n"
    assert source.read_text(encoding="utf-8") == "skills source\n"


def test_action_pins_stay_on_the_accepted_shas() -> None:
    import re

    expected = {
        "astral-sh/setup-uv": (
            "ae62891fec2bb8e7d6c99fc78c9fec3a63790f8d",
            "v10.0.0",
        ),
        "actions/upload-artifact": (
            "cf430e030ddbb5b0abf93d22962f4752f3646cd9",
            "v7.0.2",
        ),
        "actions/download-artifact": (
            "9000827ccba6bdab643e8b6fd33ac0654aef8333",
            "v8.0.2",
        ),
    }
    pattern = re.compile(
        r"uses:\s+(?P<action>[\w./-]+)@(?P<sha>[0-9a-f]{40})"
        r"\s+#\s+(?P<version>v\d+(?:\.\d+){0,2})"
    )
    workflows = sorted((REPO / ".github/workflows").glob("*.yml"))
    assert workflows
    seen = dict.fromkeys(expected, 0)
    for path in workflows:
        for match in pattern.finditer(path.read_text(encoding="utf-8")):
            action = match.group("action")
            if action not in expected:
                continue
            sha, version = expected[action]
            assert match.group("sha") == sha, path.name
            assert match.group("version") == version, path.name
            seen[action] += 1
    assert all(count > 0 for count in seen.values())
