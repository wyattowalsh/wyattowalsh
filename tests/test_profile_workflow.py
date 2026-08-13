"""Workflow contract tests for the profile updater."""

import re
import shlex
import subprocess
from pathlib import Path

WORKFLOW_PATH = Path(".github/workflows/profile-updater.yml")
README_PATH = Path("README.md")
BANNER_LIGHT = Path(".github/assets/img/banner.svg")
BANNER_DARK = Path(".github/assets/img/banner-dark.svg")

LOWLIGHTER_METRICS_PIN = "lowlighter/metrics@65836723097537a54cd8eb90f61839426b4266b6"

EXPECTED_ACTION_PINS = {
    "actions/checkout": (
        "3d3c42e5aac5ba805825da76410c181273ba90b1",
        "v7.0.1",
    ),
    "actions/download-artifact": (
        "3e5f45b2cfb9172054b4087a40e8e0b5a5461e7c",
        "v8.0.1",
    ),
    "actions/setup-python": (
        "5fda3b95a4ea91299a34e894583c3862153e4b97",
        "v7.0.0",
    ),
    "actions/upload-artifact": (
        "043fb46d1a93c77aae656e7c1c64a875d1fc6a0a",
        "v7.0.1",
    ),
    "astral-sh/setup-uv": (
        "ae62891fec2bb8e7d6c99fc78c9fec3a63790f8d",
        "v10.0.0",
    ),
    "lowlighter/metrics": (
        "65836723097537a54cd8eb90f61839426b4266b6",
        "v3.34",
    ),
}

USES_LINE_RE = re.compile(
    r"^\s*uses:\s+(?P<action>[^@\s]+)@(?P<sha>[0-9a-f]{40})"
    r"\s+#\s+(?P<version>v\d+(?:\.\d+){0,2})\s*$"
)

GENERATOR_JOBS = (
    "update-starred-lists",
    "generate-assets",
    "generate-event-art",
    "generate-profile-metrics",
)

FINALIZE_NEEDS = (
    "update-starred-lists",
    "generate-assets",
    "generate-event-art",
    "generate-profile-metrics",
    "update-readme-wakatime",
)


def _workflow_text() -> str:
    return WORKFLOW_PATH.read_text(encoding="utf-8")


def _job_block(workflow: str, job_id: str) -> str:
    match = re.search(
        rf"(?ms)^  {re.escape(job_id)}:\n.*?(?=^  [a-z][a-z0-9-]*:\n|\Z)",
        workflow,
    )
    assert match is not None, f"{job_id} job not found"
    return match.group(0)


def _lowlighter_with_blocks(job_text: str) -> list[str]:
    """Return each lowlighter/metrics step's `with:` mapping body."""
    step_chunks = re.split(
        r"(?m)^(?=      - name:)",
        job_text,
    )
    blocks: list[str] = []
    for chunk in step_chunks:
        if "uses: lowlighter/metrics@" not in chunk:
            continue
        with_match = re.search(
            r"(?ms)^        with:\n((?:          .*\n)*)",
            chunk,
        )
        assert with_match is not None, "lowlighter step missing with: block"
        blocks.append(with_match.group(1))
    assert blocks, "expected at least one lowlighter/metrics with: block"
    return blocks


def _shell_array(job_text: str, name: str) -> tuple[str, ...]:
    match = re.search(
        rf"(?ms)^          {re.escape(name)}=\(\n"
        rf"(?P<body>.*?)^          \)$",
        job_text,
    )
    assert match is not None, f"{name} shell array not found"
    values: list[str] = []
    for line in match.group("body").splitlines():
        parts = shlex.split(line.strip())
        assert len(parts) == 1, f"unexpected {name} entry: {line}"
        values.append(parts[0])
    return tuple(values)


def _run_git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def test_profile_actions_use_exact_immutable_release_pins() -> None:
    workflow = _workflow_text()
    uses_lines = [
        line for line in workflow.splitlines() if line.lstrip().startswith("uses:")
    ]
    observed_actions: set[str] = set()

    for line in uses_lines:
        match = USES_LINE_RE.fullmatch(line)
        assert match is not None, (
            f"action must use a full SHA and version comment: {line}"
        )
        action = match.group("action")
        assert action in EXPECTED_ACTION_PINS, f"unexpected profile action: {action}"
        assert (match.group("sha"), match.group("version")) == EXPECTED_ACTION_PINS[
            action
        ]
        observed_actions.add(action)

    assert observed_actions == set(EXPECTED_ACTION_PINS)


def test_generated_commit_pushes_skip_generator_jobs() -> None:
    workflow = _workflow_text()

    assert "github.event.head_commit.message != 'Updated with Dev Metrics'" in workflow
    assert (
        "github.event.head_commit.message != 'chore(metrics): update generated "
        "metrics assets'"
    ) in workflow
    assert (
        "github.event.head_commit.message != 'chore(readme): update dynamic "
        "sections and skills badges'"
    ) in workflow
    assert workflow.count("github.event.head_commit.message !=") >= 6 * 6


def test_wakatime_job_is_first_party_artifact_only() -> None:
    """F9: first-party Waka generates an artifact; no anmol098 Action."""
    workflow = _workflow_text()
    waka = _job_block(workflow, "update-readme-wakatime")

    assert "anmol098/waka-readme-stats" not in workflow
    assert "anmol098" not in workflow
    assert "generate wakatime" in waka
    assert "waka-readme-${{ github.run_id }}" in waka
    assert "upload-artifact@" in waka
    assert "contents: read" in waka
    assert "git commit" not in waka
    assert "git push" not in waka
    assert "GH_TOKEN" not in waka
    assert "SHOW_LOC_CHART" not in workflow
    assert "PULL_BRANCH_NAME" not in workflow
    assert "PUSH_BRANCH_NAME" not in workflow


def test_generate_assets_runs_banner_step() -> None:
    workflow = _workflow_text()

    assert "generate banner --config-path config.yaml" in workflow
    assert "Generate light and dark banners" in workflow
    assert "banner*.svg" in workflow


def test_banner_and_banner_dark_required_by_ci_contracts() -> None:
    """Both light and dark banners must exist and be non-empty for CI."""
    assert BANNER_LIGHT.is_file(), f"missing required asset: {BANNER_LIGHT}"
    assert BANNER_DARK.is_file(), f"missing required asset: {BANNER_DARK}"
    assert BANNER_LIGHT.stat().st_size > 0, f"empty asset: {BANNER_LIGHT}"
    assert BANNER_DARK.stat().st_size > 0, f"empty asset: {BANNER_DARK}"


def test_uv_sync_requires_locked_and_forbids_all_groups() -> None:
    workflow = _workflow_text()

    assert "--all-groups" not in workflow
    sync_lines = [line.strip() for line in workflow.splitlines() if "uv sync" in line]
    assert sync_lines, "expected at least one uv sync invocation"
    for line in sync_lines:
        assert "--locked" in line, f"missing --locked: {line}"


def test_generate_assets_installs_cairo_apt_deps() -> None:
    workflow = _workflow_text()
    cairo_apt = (
        "sudo apt-get update && sudo apt-get install -y "
        "libcairo2 libcairo2-dev pkg-config libffi-dev"
    )
    assert cairo_apt in workflow


def test_generate_event_art_installs_lossless_gif_optimizer() -> None:
    art = _job_block(_workflow_text(), "generate-event-art")

    assert "apt-get install -y librsvg2-bin gifsicle" in art


def test_living_art_workflow_uses_exact_six_primary_only_handoff() -> None:
    workflow = _workflow_text()
    producer = _job_block(workflow, "generate-event-art")
    finalize = _job_block(workflow, "finalize")

    assert "stage_living_art_fleet(" in producer
    assert "publish_living_art_fleet(" in finalize
    assert "living-art-stage/outputs" not in workflow
    assert "outputs/docs-showcase" not in workflow
    assert "outputs/index" not in workflow
    assert "if-no-files-found: error" in producer
    assert '.glob("living-*.gif")' in workflow  # inventory only; equality-checked
    assert "for file in .github/assets/img/living-*.gif" not in workflow
    assert 'for file in "$stage"/outputs/timelapse/living-*.gif' not in workflow
    assert "':(glob).github/assets/img/living-*.gif'" in finalize
    assert "':(glob)docs/public/showcase/living-*.gif'" in finalize
    assert 'git add -A -- "${owned_files[@]}"' in finalize


def test_generate_assets_uses_locked_qr_and_wordcloud_extras() -> None:
    workflow = _workflow_text()
    assert "uv sync --locked --extra qr --extra word-clouds" in workflow
    assert "uv sync --locked --extra script-tools" in workflow


def test_finalize_needs_generators_and_waka_fail_closed() -> None:
    workflow = _workflow_text()
    finalize = _job_block(workflow, "finalize")

    for dep in FINALIZE_NEEDS:
        assert f"- {dep}" in finalize
        assert f"needs.{dep}.result == 'success'" in finalize

    assert "needs.update-starred-lists.result == 'success'" in finalize
    assert "generate readme-sections --config-path config.yaml" in finalize
    assert "generate skills --skills-path skills.yaml" in finalize


def test_finalize_is_sole_first_party_git_commit_and_push() -> None:
    """Only the finalize job performs first-party git commit/push."""
    workflow = _workflow_text()
    real_jobs = (
        "probe-full-metrics",
        *GENERATOR_JOBS,
        "update-readme-wakatime",
        "finalize",
    )
    for job_id in real_jobs:
        block = _job_block(workflow, job_id)
        if job_id == "finalize":
            assert "git commit" in block
            assert "git push" in block
            assert "contents: write" in block
        else:
            assert "git commit" not in block, f"{job_id} must not git commit"
            assert "git push" not in block, f"{job_id} must not git push"
            assert "contents: write" not in block, f"{job_id} must not request write"

    waka = _job_block(workflow, "update-readme-wakatime")
    assert "anmol098/waka-readme-stats" not in waka
    assert "generate wakatime" in waka

    finalize = _job_block(workflow, "finalize")
    assert "waka-readme-${{ github.run_id }}" in finalize
    assert "scripts.wakatime_readme apply" in finalize

    assert workflow.count("git push") == 1
    assert "update-skills:" not in workflow


def test_generator_jobs_upload_artifacts_without_git_writers() -> None:
    workflow = _workflow_text()

    starred = _job_block(workflow, "update-starred-lists")
    assert "starred-lists-${{ github.run_id }}" in starred
    assert "upload-artifact@" in starred
    assert "contents: read" in starred

    assets = _job_block(workflow, "generate-assets")
    assert "profile-assets-${{ github.run_id }}" in assets
    assert "download-artifact@" in assets
    assert "upload-artifact@" in assets
    assert "contents: read" in assets

    art = _job_block(workflow, "generate-event-art")
    assert "living-art-stage-${{ github.run_id }}" in art
    assert "upload-artifact@" in art
    assert "contents: read" in art

    metrics = _job_block(workflow, "generate-profile-metrics")
    assert "profile-metrics-${{ github.run_id }}" in metrics
    assert "upload-artifact@" in metrics
    assert "contents: read" in metrics

    waka = _job_block(workflow, "update-readme-wakatime")
    assert "waka-readme-${{ github.run_id }}" in waka
    assert "upload-artifact@" in waka
    assert "contents: read" in waka

    finalize = _job_block(workflow, "finalize")
    for artifact in (
        "starred-lists-${{ github.run_id }}",
        "profile-assets-${{ github.run_id }}",
        "living-art-stage-${{ github.run_id }}",
        "profile-metrics-${{ github.run_id }}",
        "waka-readme-${{ github.run_id }}",
    ):
        assert artifact in finalize
    assert finalize.count("download-artifact@") >= 5


def test_finalize_publishes_and_validates_living_art_before_git_staging() -> None:
    """Untrusted living art must fail before the sole writer runs git add."""
    finalize = _job_block(_workflow_text(), "finalize")
    publication = "publish_living_art_fleet("

    assert publication in finalize
    assert "validate_living_art_byte_budgets(primary_manifest)" in finalize
    assert "validate_living_art_byte_budgets(public_manifest)" in finalize
    assert "stable_payload(primary_manifest)" in finalize
    assert "Persisted living-art GIF hashes differ" in finalize
    assert finalize.index(publication) < finalize.index("git add -A --")


def test_finalize_uses_explicit_generated_asset_pathspecs() -> None:
    finalize = _job_block(_workflow_text(), "finalize")

    assert "shopt -s nullglob" not in finalize
    assert _shell_array(finalize, "asset_files") == (
        ":(glob).github/assets/img/qr*.png",
        ":(glob).github/assets/img/wordcloud_*.svg",
        ":(glob).github/assets/img/banner*.svg",
    )
    assert _shell_array(finalize, "readme_files") == (
        "README.md",
        ":(glob).github/assets/img/readme/*.svg",
    )
    assert 'git add -A -- "${owned_files[@]}"' in finalize


def test_finalize_pathspecs_stage_only_owned_tracked_deletions(
    tmp_path: Path,
) -> None:
    finalize = _job_block(_workflow_text(), "finalize")
    cases = {
        "asset_files": (
            ".github/assets/img/qr-obsolete.png",
            ".github/assets/img/wordcloud_obsolete.svg",
            ".github/assets/img/banner-obsolete.svg",
        ),
        "readme_files": (".github/assets/img/readme/obsolete.svg",),
    }

    for array_name, deleted_paths in cases.items():
        repo = tmp_path / array_name
        repo.mkdir()
        _run_git(repo, "init", "--quiet")
        outside_path = ".github/assets/img/outside-owned-namespaces.svg"
        for relative_path in (*deleted_paths, outside_path, "README.md"):
            path = repo / relative_path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f"fixture for {relative_path}\n", encoding="utf-8")
        _run_git(repo, "add", "--", ".")
        _run_git(
            repo,
            "-c",
            "user.name=Workflow Contract Test",
            "-c",
            "user.email=workflow-contract@example.invalid",
            "commit",
            "--quiet",
            "-m",
            "baseline",
        )

        for relative_path in (*deleted_paths, outside_path):
            (repo / relative_path).unlink()

        _run_git(repo, "add", "-A", "--", *_shell_array(finalize, array_name))
        staged = set(_run_git(repo, "diff", "--cached", "--name-status").splitlines())
        assert staged == {f"D\t{path}" for path in deleted_paths}


def test_metrics_probe_and_prod_share_lowlighter_pin_without_felipecrs() -> None:
    workflow = _workflow_text()
    probe = _job_block(workflow, "probe-full-metrics")
    prod = _job_block(workflow, "generate-profile-metrics")

    assert "felipecrs" not in workflow
    assert LOWLIGHTER_METRICS_PIN in probe
    assert LOWLIGHTER_METRICS_PIN in prod
    assert probe.count(LOWLIGHTER_METRICS_PIN) >= 3
    assert prod.count(LOWLIGHTER_METRICS_PIN) >= 3


def test_metrics_third_party_actions_forbid_spotify_secrets_in_with() -> None:
    workflow = _workflow_text()
    for job_id in ("probe-full-metrics", "generate-profile-metrics"):
        for with_block in _lowlighter_with_blocks(_job_block(workflow, job_id)):
            assert "SPOTIFY_" not in with_block
            assert "plugin_music_token" not in with_block
            assert "plugin_music_provider" not in with_block
            assert re.search(r"(?m)^\s*plugin_music:\s*no\s*$", with_block), (
                f"{job_id} lowlighter step missing plugin_music: no"
            )


def test_lowlighter_runner_only_steps_omit_committer_token() -> None:
    workflow = _workflow_text()
    for job_id in ("probe-full-metrics", "generate-profile-metrics"):
        for with_block in _lowlighter_with_blocks(_job_block(workflow, job_id)):
            assert re.search(r"(?m)^\s*output_action:\s*none\s*$", with_block)
            assert "committer_token" not in with_block


def test_metrics_auth_selects_valid_secret_without_error_annotations() -> None:
    workflow = _workflow_text()
    selected_token = (
        "${{ steps.metrics_auth.outputs.has_valid_metrics_token == 'true' && "
        "secrets.METRICS_TOKEN || github.token }}"
    )

    for job_id in ("probe-full-metrics", "generate-profile-metrics"):
        job = _job_block(workflow, job_id)
        assert "id: metrics_auth" in job
        assert "has_valid_metrics_token=false" in job
        assert "https://api.github.com/user" in job
        assert "--silent --output /dev/null --write-out '%{http_code}'" in job
        assert '[ "${metrics_status}" = "200" ]' in job
        assert (
            'echo "has_valid_metrics_token=${has_valid_metrics_token}" '
            '>> "$GITHUB_OUTPUT"'
        ) in job
        assert job.count(f"token: {selected_token}") == 3
        assert "token: ${{ secrets.METRICS_TOKEN || github.token }}" not in job
        assert "::warning::" not in job
        assert "::error::" not in job.split("      - name: Back up", maxsplit=1)[0]

    prod = _job_block(workflow, "generate-profile-metrics")
    assert f"GITHUB_TOKEN: {selected_token}" in prod
    assert (
        "METRICS_TOKEN:"
        not in prod.split(
            "      - name: Generate supplemental metrics cards", maxsplit=1
        )[1].split("      - name:", maxsplit=1)[0]
    )


def test_invalid_metrics_token_disables_elevated_scope_plugins() -> None:
    valid_gate = "steps.metrics_auth.outputs.has_valid_metrics_token == 'true'"

    for job_id in ("probe-full-metrics", "generate-profile-metrics"):
        job = _job_block(_workflow_text(), job_id)
        for plugin in (
            "plugin_traffic",
            "plugin_notable_repositories",
            "plugin_stargazers",
            "plugin_stars",
            "plugin_stars_limit",
        ):
            line = next(
                line for line in job.splitlines() if line.strip().startswith(plugin)
            )
            assert valid_gate in line, f"{plugin} is not guarded in {job_id}"


def test_metrics_production_plugins_match_relevance_matrix() -> None:
    workflow = _workflow_text()
    prod = _job_block(workflow, "generate-profile-metrics")
    blocks = _lowlighter_with_blocks(prod)
    assert len(blocks) >= 3

    primary, additional, extra = blocks[0], blocks[1], blocks[2]

    assert "plugin_isocalendar: yes" in primary
    assert "plugin_languages: yes" in primary
    assert "plugin_notable: yes" in primary
    assert "plugin_topics: yes" in primary
    assert "plugin_achievements: yes" in primary
    assert "plugin_achievements_display: compact" in primary
    assert "plugin_calendar: yes" in primary
    assert "plugin_calendar_limit: 1" in primary
    assert "plugin_habits: no" in primary
    assert "plugin_gists: no" in primary

    assert "plugin_repositories: yes" in additional
    assert "plugin_people: yes" in additional
    assert "plugin_activity: no" in additional
    assert "plugin_habits: no" in additional
    assert "plugin_music: no" in additional
    assert "plugin_tweets: no" in additional
    assert "iina-plugin-bookmarks" in additional

    assert "metrics.extra.svg" in prod
    assert "plugin_reactions: yes" in extra
    assert "plugin_followup: yes" in extra
    assert "plugin_music: no" in extra
    assert "plugin_activity: no" in extra
    assert "plugin_habits: no" in extra


def test_metrics_extra_svg_has_validate_recover_and_finalize_paths() -> None:
    workflow = _workflow_text()
    prod = _job_block(workflow, "generate-profile-metrics")
    finalize = _job_block(workflow, "finalize")

    assert "metrics-backups/metrics.extra.svg" in prod
    assert (
        "uv run python -m scripts.metrics_svg validate "
        "./.github/assets/img/metrics.extra.svg"
    ) in prod
    assert (
        "uv run python -m scripts.metrics_svg recover \\\n"
        "            ./.github/assets/img/metrics.extra.svg \\"
    ) in prod
    assert ".github/assets/img/metrics.extra.svg" in prod
    assert "./.github/assets/img/metrics.extra.svg" in finalize
    assert "chore(metrics): update generated metrics assets" in finalize
    assert Path(".github/assets/img/metrics.extra.svg").is_file()


def test_finalize_applies_waka_before_readme_sections() -> None:
    """Finalize must apply the Waka artifact before readme-sections/skills."""
    finalize = _job_block(_workflow_text(), "finalize")
    apply_idx = finalize.index("scripts.wakatime_readme apply")
    sections_idx = finalize.index("generate readme-sections --config-path config.yaml")
    skills_idx = finalize.index("generate skills --skills-path skills.yaml")
    assert apply_idx < sections_idx < skills_idx

    """Wave R wrap-flow README invariants remain intact under finalize serialization."""
    finalize = _job_block(_workflow_text(), "finalize")
    assert "generate readme-sections --config-path config.yaml" in finalize
    assert "generate skills --skills-path skills.yaml" in finalize
    assert "chore(readme): update dynamic sections and skills badges" in finalize

    readme = README_PATH.read_text(encoding="utf-8")
    from scripts.config import load_config
    from scripts.readme_sections import (
        compile_section_body_re,
        section_order_from_settings,
    )

    order = section_order_from_settings(load_config().readme_sections_settings)
    living_match = compile_section_body_re("Living Art", order).search(readme)
    assert living_match is not None, "Living Art section missing"
    living = living_match.group(0)

    assert living.count('<p align="center">') == 1
    assert living.count('width="360"') == 6
    assert living.count('loading="lazy"') == 6
    assert "<table" not in living.lower()
    assert "<details" not in living.lower()
    assert "display: grid" not in living.lower()

    tech_match = compile_section_body_re("Tech Stack", order).search(readme)
    assert tech_match is not None
    tech = tech_match.group(0)
    assert "<!-- SKILLS:START -->" in tech
    for teaser in ("AI/ML", "Full-Stack", "Data Engineering", "Open Source"):
        assert f'alt="{teaser}"' not in tech

    headings = tuple(f"## {title}" for title in order)
    positions = [readme.index(heading) for heading in headings]
    assert positions == sorted(positions)

    banner_idx = readme.index('alt="Banner"')
    badges_start = readme.index("<!-- README:TOP_BADGES:START -->")
    featured_start = readme.index("<!-- README:FEATURED_PROJECTS:START -->")
    living_start = readme.index("## Living Art")
    assert banner_idx < badges_start < featured_start < living_start
