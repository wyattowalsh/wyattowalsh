"""Workflow contract tests for the profile updater."""

import hashlib
import os
import re
import shlex
import subprocess
from pathlib import Path
from typing import Any, cast

import yaml

from scripts.config import load_config
from scripts.readme_sections import (
    compile_section_body_re,
    section_order_from_settings,
)
from tests.test_readme_gfm_ux import (
    assert_visible_or_comment_heading,
    heading_index,
    living_art_wrap,
)

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
    "prepare-event-art-inputs",
    "generate-event-art",
    "assemble-event-art",
    "generate-profile-metrics",
)

FINALIZE_NEEDS = (
    "update-starred-lists",
    "generate-assets",
    "assemble-event-art",
    "generate-profile-metrics",
    "update-readme-wakatime",
)


def _workflow_text() -> str:
    return WORKFLOW_PATH.read_text(encoding="utf-8")


def _workflow_jobs() -> dict[str, dict[str, Any]]:
    workflow = yaml.safe_load(_workflow_text())
    assert isinstance(workflow, dict)
    jobs = workflow.get("jobs")
    assert isinstance(jobs, dict)
    return cast(dict[str, dict[str, Any]], jobs)


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


def _git_show_bytes(spec: str) -> bytes | None:
    result = subprocess.run(
        ["git", "show", spec],
        cwd=Path.cwd(),
        capture_output=True,
    )
    if result.returncode != 0:
        return None
    return result.stdout


def _marked_shell_block(workflow: str, start: str, end: str) -> str:
    match = re.search(
        rf"(?ms)^          # BEGIN {re.escape(start)}\n"
        rf"(?P<body>.*?)^          # END {re.escape(end)}$",
        workflow,
    )
    assert match is not None, f"shell block not found: {start}...{end}"
    return "\n".join(
        line.removeprefix("          ") for line in match.group("body").splitlines()
    )


def test_every_inline_python_heredoc_compiles() -> None:
    """Keep embedded workflow validators subject to Python syntax checking."""
    heredoc_pattern = re.compile(r"(?ms)^uv run python - <<'PY'\n(?P<source>.*?)^PY$")
    inline_sources: list[tuple[str, str, str]] = []
    for job_name, job in _workflow_jobs().items():
        for step in cast(list[dict[str, Any]], job.get("steps", [])):
            run = step.get("run")
            if not isinstance(run, str):
                continue
            inline_sources.extend(
                (job_name, str(step.get("name", "unnamed")), match.group("source"))
                for match in heredoc_pattern.finditer(run)
            )

    assert inline_sources, "expected embedded Python workflow validators"
    for job_name, step_name, source in inline_sources:
        compile(source, f"{job_name}/{step_name}", "exec")


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


def test_every_checkout_uses_the_immutable_trigger_sha() -> None:
    jobs = _workflow_jobs()
    checkout_steps: list[tuple[str, dict[str, Any]]] = []
    for job_name, job in jobs.items():
        steps = cast(list[dict[str, Any]], job.get("steps", []))
        checkout_steps.extend(
            (job_name, step)
            for step in steps
            if str(step.get("uses", "")).startswith("actions/checkout@")
        )

    assert len(checkout_steps) == 9
    for job_name, step in checkout_steps:
        assert step.get("with", {}).get("ref") == "${{ github.sha }}", (
            f"{job_name} checkout must remain pinned to the trigger revision"
        )

    for line in _workflow_text().splitlines():
        if line.lstrip().startswith("ref:"):
            assert "github.head_ref" not in line


def test_every_setup_uv_step_disables_cache_for_annotation_clean_parallelism() -> None:
    jobs = _workflow_jobs()
    setup_steps: list[tuple[str, dict[str, Any]]] = []
    for job_name, job in jobs.items():
        steps = cast(list[dict[str, Any]], job.get("steps", []))
        setup_steps.extend(
            (job_name, step)
            for step in steps
            if str(step.get("uses", "")).startswith("astral-sh/setup-uv@")
        )

    assert setup_steps
    for job_name, step in setup_steps:
        assert step.get("with") == {"enable-cache": False}, (
            f"{job_name} setup-uv must disable its shared cache"
        )


def test_download_artifact_dep0005_suppression_is_step_local() -> None:
    jobs = _workflow_jobs()
    download_steps: list[tuple[str, dict[str, Any]]] = []
    for job_name, job in jobs.items():
        steps = cast(list[dict[str, Any]], job.get("steps", []))
        download_steps.extend(
            (job_name, step)
            for step in steps
            if str(step.get("uses", "")).startswith("actions/download-artifact@")
        )

    assert len(download_steps) == 9
    for job_name, step in download_steps:
        assert step.get("env") == {"NODE_OPTIONS": "--disable-warning=DEP0005"}, (
            f"{job_name} must suppress only upstream download-artifact DEP0005"
        )

    workflow = _workflow_text()
    assert workflow.count("NODE_OPTIONS: --disable-warning=DEP0005") == len(
        download_steps
    )
    assert "--no-deprecation" not in workflow
    assert "NODE_NO_WARNINGS" not in workflow
    assert "--disable-warning=DeprecationWarning" not in workflow


def test_every_uploaded_artifact_is_idempotent_for_same_run_reruns() -> None:
    jobs = _workflow_jobs()
    upload_steps: list[tuple[str, dict[str, Any]]] = []
    for job_name, job in jobs.items():
        steps = cast(list[dict[str, Any]], job.get("steps", []))
        upload_steps.extend(
            (job_name, step)
            for step in steps
            if str(step.get("uses", "")).startswith("actions/upload-artifact@")
        )

    assert len(upload_steps) == 9
    for job_name, step in upload_steps:
        assert step.get("with", {}).get("overwrite") is True, (
            f"{job_name} artifact upload must support reruns of the same run_id"
        )


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
    assert "wakatime.svg" in waka
    assert "waka-readme-${{ github.run_id }}" in waka
    assert "upload-artifact@" in waka
    assert "contents: read" in waka
    assert "git commit" not in waka
    assert "git push" not in waka
    assert "GH_TOKEN" not in waka
    assert "SHOW_LOC_CHART" not in workflow
    assert "PULL_BRANCH_NAME" not in workflow
    assert "PUSH_BRANCH_NAME" not in workflow


def test_generate_assets_skips_banner_generation() -> None:
    workflow = _workflow_text()
    assets = _job_block(workflow, "generate-assets")

    assert "generate banner" not in workflow
    assert "Verify pinned light and dark banners" in assets
    assert "banner*.svg" in assets
    assert "origin/main:.github/assets/img/" in assets
    assert "Pinned banner drifted from origin/main" in assets


def test_banner_and_banner_dark_required_by_ci_contracts() -> None:
    """Both light and dark banners must exist and be non-empty for CI."""
    assert BANNER_LIGHT.is_file(), f"missing required asset: {BANNER_LIGHT}"
    assert BANNER_DARK.is_file(), f"missing required asset: {BANNER_DARK}"
    assert BANNER_LIGHT.stat().st_size > 0, f"empty asset: {BANNER_LIGHT}"
    assert BANNER_DARK.stat().st_size > 0, f"empty asset: {BANNER_DARK}"


def test_pinned_banners_match_origin_main_bytes() -> None:
    """Header pair must stay byte-identical to origin/main when files exist."""
    expected = {
        BANNER_LIGHT: (
            "a5e8d08ffb218924a322e423318219af5909f9ff4923891103842a8f7f408649"
        ),
        BANNER_DARK: (
            "6aaf135ac987e66ddf0594722ed9980c46c374b8a4db09ea05db56cff588f9b7"
        ),
    }
    for path, digest in expected.items():
        if not path.is_file():
            continue
        actual_bytes = path.read_bytes()
        actual = hashlib.sha256(actual_bytes).hexdigest()
        assert actual == digest, f"{path} hash {actual} != pinned main {digest}"
        origin = _git_show_bytes(f"origin/main:{path.as_posix()}")
        if origin is None:
            continue
        origin_digest = hashlib.sha256(origin).hexdigest()
        assert origin_digest == digest, (
            f"origin/main:{path.as_posix()} hash "
            f"{origin_digest} != pinned main {digest}"
        )
        assert actual_bytes == origin, f"{path} drifted from origin/main"


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


def test_generate_assets_installs_exact_svgo_release() -> None:
    assets = _job_block(_workflow_text(), "generate-assets")

    assert "npm install --global --no-audit --no-fund svgo@4.0.2" in assets
    assert assets.index("Install SVG optimizer") < assets.index(
        "Verify pinned light and dark banners"
    )


def test_generate_event_art_installs_lossless_gif_optimizer() -> None:
    art = _job_block(_workflow_text(), "generate-event-art")

    assert "apt-get install -y librsvg2-bin gifsicle" in art


def test_living_art_uses_dynamic_six_way_matrix_and_fresh_outputs() -> None:
    jobs = _workflow_jobs()
    prepare = jobs["prepare-event-art-inputs"]
    producer = jobs["generate-event-art"]
    assembler = jobs["assemble-event-art"]

    assert "needs" not in prepare
    assert prepare["timeout-minutes"] == 15
    assert prepare["permissions"] == {"contents": "read"}
    assert prepare["outputs"] == {
        "styles": "${{ steps.contract.outputs.styles }}",
        "max_frames": "${{ steps.contract.outputs.max_frames }}",
    }
    prepare_text = _job_block(_workflow_text(), "prepare-event-art-inputs")
    assert "from scripts.art.artifacts import LIVING_ART_STYLE_KEYS" in prepare_text
    assert "living-art-inputs-${{ github.run_id }}" in prepare_text
    assert "overwrite: true" in prepare_text

    assert producer["needs"] == "prepare-event-art-inputs"
    assert producer["timeout-minutes"] == 45
    assert producer["permissions"] == {"contents": "read"}
    strategy = cast(dict[str, Any], producer["strategy"])
    assert strategy["fail-fast"] is False
    assert strategy["max-parallel"] == 6
    assert strategy["matrix"] == {
        "style": "${{ fromJSON(needs.prepare-event-art-inputs.outputs.styles) }}"
    }
    producer_text = _job_block(_workflow_text(), "generate-event-art")
    assert '--only "$LIVING_ART_STYLE"' in producer_text
    assert '--max-frames "$LIVING_ART_MAX_FRAMES"' in producer_text
    assert "--size 400" in producer_text
    assert "--workers 4" in producer_text
    assert '--output-dir "$LIVING_ART_OUTPUT_DIR"' in producer_text
    assert "living-art-output-${{ matrix.style }}" in producer_text
    assert "living-art-style-${{ github.run_id }}-${{ matrix.style }}" in producer_text
    assert "compression-level: 0" in producer_text
    assert "overwrite: true" in producer_text
    assert "continue-on-error" not in producer_text

    assert assembler["needs"] == "generate-event-art"
    assert assembler["timeout-minutes"] == 15
    assert assembler["permissions"] == {"contents": "read"}
    assembler_text = _job_block(_workflow_text(), "assemble-event-art")
    assert "pattern: living-art-style-${{ github.run_id }}-*" in assembler_text
    assert "merge-multiple: true" in assembler_text
    assert "stage_living_art_fleet(" in assembler_text
    assert "living-art-stage-${{ github.run_id }}" in assembler_text


def test_living_art_workflow_uses_exact_six_primary_only_handoff() -> None:
    workflow = _workflow_text()
    producer = _job_block(workflow, "generate-event-art")
    assembler = _job_block(workflow, "assemble-event-art")
    finalize = _job_block(workflow, "finalize")

    assert "stage_living_art_fleet(" not in producer
    assert "stage_living_art_fleet(" in assembler
    assert "publish_living_art_fleet(" in finalize
    assert "living-art-stage/outputs" not in workflow
    assert "outputs/docs-showcase" not in workflow
    assert "outputs/index" not in workflow
    assert "if-no-files-found: error" in producer
    assert "if-no-files-found: error" in assembler
    assert "validate_living_art_byte_budgets(" in producer
    assert "for file in .github/assets/img/living-*.gif" not in workflow
    assert 'for file in "$stage"/outputs/timelapse/living-*.gif' not in workflow
    assert "':(glob).github/assets/img/living-*.gif'" in finalize
    assert "':(glob).github/assets/img/living-*.mp4'" not in finalize
    assert "mp4s=(.github/assets/img/living-*.mp4)" in finalize
    assert "':(glob)docs/public/showcase/living-*.gif'" in finalize
    assert 'git add -A -- "${owned_files[@]}"' in finalize


def test_generate_assets_word_clouds_use_typographic_renderer() -> None:
    """CI ships the exotic typographic packer under the public filenames."""
    assets = _job_block(_workflow_text(), "generate-assets")
    assert assets.count("--renderer typographic") == 2
    assert "--renderer fractal" not in assets
    assert "--from-topics-md" in assets
    assert "--from-languages-md" in assets
    assert (
        "--output-path .github/assets/img/wordcloud_typographic_by_topics.svg"
        in assets
    )
    assert (
        "--output-path .github/assets/img/wordcloud_typographic_by_languages.svg"
        in assets
    )


def test_generate_assets_uses_locked_qr_and_wordcloud_extras() -> None:
    workflow = _workflow_text()
    jobs = _workflow_jobs()
    assert "uv sync --locked --extra qr --extra word-clouds" in workflow
    starred = _job_block(workflow, "update-starred-lists")
    assert "uv sync --locked" in starred
    assert "scripts.starred_lists" in starred
    assert "uv run starred" not in workflow
    assert "--token" not in starred
    assert "--topic-threshold 500" in starred
    assert "Validate starred-list consumer contract" in starred
    assert 'line.startswith("Error:")' in starred

    for job_name in ("generate-assets", "finalize"):
        steps = cast(list[dict[str, Any]], jobs[job_name]["steps"])
        starred_download = next(
            step
            for step in steps
            if step.get("name") == "Download starred lists artifact"
        )
        assert starred_download["with"]["path"] == ".github/assets"

    finalize_steps = cast(list[dict[str, Any]], jobs["finalize"]["steps"])
    expected_download_paths = {
        "Download profile assets artifact": "${{ runner.temp }}/profile-assets",
        "Download profile metrics artifact": ".github/assets/img",
    }
    for step_name, expected_path in expected_download_paths.items():
        step = next(step for step in finalize_steps if step.get("name") == step_name)
        assert step["with"]["path"] == expected_path


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
    assert ".github/assets/img/wakatime.svg" in finalize
    assert "metrics-activity.svg" not in finalize

    assert workflow.count("git push") == 1
    assert "update-skills:" not in workflow


def test_finalize_push_follows_ref_name_not_hardcoded_main() -> None:
    """fact-ship-dev: finalize publishes to TARGET_BRANCH / github.ref_name."""
    finalize = _job_block(_workflow_text(), "finalize")
    push_script = _marked_shell_block(
        _workflow_text(),
        "trigger-consistent-push",
        "trigger-consistent-push",
    )

    assert "github.ref == 'refs/heads/dev'" in finalize
    assert "TARGET_BRANCH: ${{ github.head_ref || github.ref_name }}" in finalize
    assert 'origin "HEAD:refs/heads/${TARGET_BRANCH}"' in push_script
    lease = '--force-with-lease="refs/heads/${TARGET_BRANCH}:${TRIGGER_SHA}"'
    assert lease in push_script
    assert '[ "${TARGET_BRANCH}" != "dev" ]' in push_script
    assert "HEAD:refs/heads/main" not in push_script
    assert "origin main" not in push_script
    assert re.search(r"git push\s+origin\s+HEAD:main\b", push_script) is None


def test_finalize_never_rebases_generated_outputs_across_trigger_revisions(
    tmp_path: Path,
) -> None:
    script = _marked_shell_block(
        _workflow_text(),
        "trigger-consistent-push",
        "trigger-consistent-push",
    )
    assert "git rebase" not in script
    assert "TRIGGER_SHA" in script
    assert '--force-with-lease="refs/heads/${TARGET_BRANCH}:${TRIGGER_SHA}"' in script
    assert 'git merge-base --is-ancestor "${TRIGGER_SHA}" HEAD' in script

    remote = tmp_path / "remote.git"
    source = tmp_path / "source"
    worker = tmp_path / "worker"
    _run_git(tmp_path, "init", "--bare", "--quiet", str(remote))
    _run_git(tmp_path, "clone", "--quiet", str(remote), str(source))
    _run_git(source, "config", "user.name", "Test")
    _run_git(source, "config", "user.email", "test@example.com")
    (source / "source.txt").write_text("trigger A\n", encoding="utf-8")
    _run_git(source, "add", "source.txt")
    _run_git(source, "commit", "--quiet", "-m", "source A")
    _run_git(source, "branch", "-M", "dev")
    _run_git(source, "push", "--quiet", "-u", "origin", "dev")
    trigger_sha = _run_git(source, "rev-parse", "HEAD").strip()

    _run_git(tmp_path, "clone", "--quiet", "--branch", "dev", str(remote), str(worker))
    _run_git(worker, "config", "user.name", "Test")
    _run_git(worker, "config", "user.email", "test@example.com")
    (worker / "generated.txt").write_text("generated from A\n", encoding="utf-8")
    _run_git(worker, "add", "generated.txt")
    _run_git(worker, "commit", "--quiet", "-m", "generated from A")

    (source / "source.txt").write_text("source B\n", encoding="utf-8")
    _run_git(source, "add", "source.txt")
    _run_git(source, "commit", "--quiet", "-m", "source B")
    _run_git(source, "push", "--quiet", "origin", "dev")
    advanced_sha = _run_git(source, "rev-parse", "HEAD").strip()

    result = subprocess.run(
        ["bash", "-euo", "pipefail", "-c", script],
        cwd=worker,
        env={
            "PATH": os.environ["PATH"],
            "TARGET_BRANCH": "dev",
            "TRIGGER_REF_TYPE": "branch",
            "TRIGGER_SHA": trigger_sha,
        },
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert "advanced beyond this run's trigger revision" in result.stdout
    remote_sha = _run_git(source, "ls-remote", "origin", "refs/heads/dev").split()[0]
    assert remote_sha == advanced_sha
    remote_log = _run_git(source, "log", "--format=%s", "origin/dev")
    assert "generated from A" not in remote_log


def test_finalize_force_refreshes_remote_tracking_ref_before_revision_check(
    tmp_path: Path,
) -> None:
    script = _marked_shell_block(
        _workflow_text(),
        "trigger-consistent-push",
        "trigger-consistent-push",
    )
    assert "+refs/heads/${TARGET_BRANCH}:refs/remotes/origin/${TARGET_BRANCH}" in script
    assert "Failed to refresh" in script

    remote = tmp_path / "remote.git"
    source = tmp_path / "source"
    worker = tmp_path / "worker"
    _run_git(tmp_path, "init", "--bare", "--quiet", str(remote))
    _run_git(tmp_path, "clone", "--quiet", str(remote), str(source))
    _run_git(source, "config", "user.name", "Test")
    _run_git(source, "config", "user.email", "test@example.com")
    (source / "source.txt").write_text("base\n", encoding="utf-8")
    _run_git(source, "add", "source.txt")
    _run_git(source, "commit", "--quiet", "-m", "base")
    _run_git(source, "branch", "-M", "dev")
    _run_git(source, "push", "--quiet", "-u", "origin", "dev")
    base_sha = _run_git(source, "rev-parse", "HEAD").strip()
    (source / "source.txt").write_text("trigger A\n", encoding="utf-8")
    _run_git(source, "commit", "--quiet", "-am", "trigger A")
    _run_git(source, "push", "--quiet", "origin", "dev")
    trigger_sha = _run_git(source, "rev-parse", "HEAD").strip()

    _run_git(tmp_path, "clone", "--quiet", "--branch", "dev", str(remote), str(worker))
    _run_git(worker, "config", "user.name", "Test")
    _run_git(worker, "config", "user.email", "test@example.com")
    (worker / "generated.txt").write_text("generated from A\n", encoding="utf-8")
    _run_git(worker, "add", "generated.txt")
    _run_git(worker, "commit", "--quiet", "-m", "generated from A")

    _run_git(source, "reset", "--hard", base_sha)
    _run_git(source, "push", "--quiet", "--force", "origin", "HEAD:dev")

    result = subprocess.run(
        ["bash", "-euo", "pipefail", "-c", script],
        cwd=worker,
        env={
            "PATH": os.environ["PATH"],
            "TARGET_BRANCH": "dev",
            "TRIGGER_REF_TYPE": "branch",
            "TRIGGER_SHA": trigger_sha,
        },
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert "advanced beyond this run's trigger revision" in result.stdout
    remote_sha = _run_git(source, "ls-remote", "origin", "refs/heads/dev").split()[0]
    assert remote_sha == base_sha


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
    assert "living-art-style-${{ github.run_id }}-${{ matrix.style }}" in art
    assert "upload-artifact@" in art
    assert "contents: read" in art

    art_inputs = _job_block(workflow, "prepare-event-art-inputs")
    assert "living-art-inputs-${{ github.run_id }}" in art_inputs
    assert "upload-artifact@" in art_inputs
    assert "contents: read" in art_inputs

    art_assembler = _job_block(workflow, "assemble-event-art")
    assert "living-art-stage-${{ github.run_id }}" in art_assembler
    assert "download-artifact@" in art_assembler
    assert "upload-artifact@" in art_assembler
    assert "contents: read" in art_assembler

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


def test_profile_asset_artifact_is_structurally_validated_and_exact() -> None:
    """The upload boundary must not inherit stale wildcard matches."""
    assets = _job_block(_workflow_text(), "generate-assets")
    jobs = _workflow_jobs()
    steps = jobs["generate-assets"]["steps"]
    assert isinstance(steps, list)

    validate_step = next(
        step
        for step in steps
        if isinstance(step, dict)
        and step.get("name") == "Validate exact profile asset inventory"
    )
    validation = validate_step.get("run")
    assert isinstance(validation, str)
    for contract in (
        'asset_dir / "banner-dark.svg"',
        'asset_dir / "banner.svg"',
        'asset_dir / "qr.png"',
        'asset_dir / "wordcloud_typographic_by_languages.svg"',
        'asset_dir / "wordcloud_typographic_by_topics.svg"',
        "observed != expected",
        "stat.S_ISREG",
        "ET.parse(path)",
        "image.verify()",
        'image.format != "PNG"',
    ):
        assert contract in validation

    upload_step = next(
        step
        for step in steps
        if isinstance(step, dict)
        and step.get("name") == "Upload profile assets artifact"
    )
    upload_with = upload_step.get("with")
    assert isinstance(upload_with, dict)
    paths = upload_with.get("path")
    assert isinstance(paths, str)
    assert paths.splitlines() == [
        ".github/assets/img/banner-dark.svg",
        ".github/assets/img/banner.svg",
        ".github/assets/img/qr.png",
        ".github/assets/img/wordcloud_typographic_by_languages.svg",
        ".github/assets/img/wordcloud_typographic_by_topics.svg",
    ]
    assert "*." not in paths
    assert assets.index("Validate exact profile asset inventory") < assets.index(
        "Upload profile assets artifact"
    )

    finalize_steps = jobs["finalize"]["steps"]
    assert isinstance(finalize_steps, list)
    publish_step = next(
        step
        for step in finalize_steps
        if isinstance(step, dict)
        and step.get("name") == "Publish and validate exact profile asset inventory"
    )
    publication = publish_step.get("run")
    assert isinstance(publication, str)
    for contract in (
        'stage_dir = Path(os.environ["RUNNER_TEMP"]) / "profile-assets"',
        "validate(stage_dir, exact_directory=True)",
        "path.name not in expected_names",
        "os.replace(temporary_path, output_dir / name)",
        "validate(output_dir, exact_directory=False)",
    ):
        assert contract in publication

    finalize = _job_block(_workflow_text(), "finalize")
    assert finalize.index(
        "Publish and validate exact profile asset inventory"
    ) < finalize.index("git add -A --")


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
    assert 'plugin_languages_threshold: "0%"' in primary
    assert "plugin_notable: yes" in primary
    assert "plugin_topics: yes" in primary
    assert "plugin_topics_limit: 20" in primary
    assert "plugin_achievements: no" in primary
    assert "plugin_achievements_display" not in primary
    assert "plugin_achievements_threshold" not in primary
    assert "plugin_achievements_limit" not in primary
    assert "plugin_calendar: yes" in primary
    assert "plugin_calendar_limit: 0" in primary
    assert "plugin_habits: yes" in primary
    assert "plugin_habits_from: 100" in primary
    assert "plugin_gists: no" in primary
    assert "plugin_lines: no" in primary
    assert "plugin_music: no" in primary
    assert "plugin_activity: no" in primary
    assert "plugin_tweets: no" in primary

    assert "plugin_repositories: no" in additional
    assert "plugin_repositories_featured" not in additional
    assert "plugin_people: no" in additional
    assert "plugin_people_limit" not in additional
    assert (
        "plugin_stars: ${{ steps.metrics_auth.outputs.has_valid_metrics_token "
        "== 'true' && 'yes' || 'no' }}"
    ) in additional
    assert (
        "plugin_stars_limit: ${{ steps.metrics_auth.outputs.has_valid_metrics_token "
        "== 'true' && '16' || '0' }}"
    ) in additional
    assert "plugin_activity: no" in additional
    assert "plugin_habits: no" in additional
    assert "plugin_music: no" in additional
    assert "plugin_tweets: no" in additional

    assert "metrics.extra.svg" in prod
    assert "plugin_reactions: yes" in extra
    assert "plugin_followup: no" in extra
    assert "plugin_music: no" in extra
    assert "plugin_activity: no" in extra
    assert "plugin_habits: no" in extra
    assert "plugin_gists: no" in extra
    assert "plugin_lines:" not in extra
    assert "plugin_achievements:" not in extra


def test_fact_lowlighter_maximal_production_raises_topics_stars_people() -> None:
    """fact-lowlighter-maximal: production (not probe) raises topics/stars/people."""
    prod = _job_block(_workflow_text(), "generate-profile-metrics")
    probe = _job_block(_workflow_text(), "probe-full-metrics")
    primary, additional, _extra = _lowlighter_with_blocks(prod)

    assert "plugin_topics: yes" in primary
    assert "plugin_topics_limit: 20" in primary
    assert 'plugin_languages_threshold: "0%"' in primary
    assert "plugin_calendar_limit: 0" in primary
    assert "plugin_stars:" in additional
    assert "plugin_stars_limit:" in additional
    assert "'16'" in additional
    assert "plugin_people: no" in additional
    assert "plugin_people_limit" not in additional

    assert "plugin_topics_limit: 15" in probe
    assert "plugin_people: no" in probe
    assert "'3'" in probe
    assert "plugin_stars:" in probe
    assert "plugin_people:" in probe


def test_metrics_extra_svg_has_validate_recover_and_finalize_paths() -> None:
    workflow = _workflow_text()
    prod = _job_block(workflow, "generate-profile-metrics")
    finalize = _job_block(workflow, "finalize")

    assert "metrics-backups/metrics.extra.svg" in prod
    assert (
        "uv run python -m scripts.metrics_svg recover \\\n"
        "            ./.github/assets/img/metrics.extra.svg \\"
    ) in prod
    assert ".github/assets/img/metrics.extra.svg" in prod
    assert "./.github/assets/img/metrics.extra.svg" in finalize
    assert "chore(metrics): update generated metrics assets" in finalize
    assert Path(".github/assets/img/metrics.extra.svg").is_file()


def test_metrics_recovery_does_not_create_expected_failure_annotations() -> None:
    prod = _job_block(_workflow_text(), "generate-profile-metrics")

    for label, asset in (
        ("personal", "metrics.svg"),
        ("additional", "metrics.additional.svg"),
        ("extra", "metrics.extra.svg"),
    ):
        assert f"name: Validate and recover {label} metrics output" in prod
        assert (
            "uv run python -m scripts.metrics_svg recover \\\n"
            f"            ./.github/assets/img/{asset} \\"
        ) in prod

    intentionally_failed_validation = (
        "continue-on-error: true\n"
        "        run: uv run python -m scripts.metrics_svg validate"
    )
    assert intentionally_failed_validation not in prod


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
    order = section_order_from_settings(load_config().readme_sections_settings)
    assert compile_section_body_re("Living Art", order).search(readme) is not None
    wrap = living_art_wrap(readme)

    assert wrap.count('<p align="center">') == 1
    assert wrap.count('width="360"') == 6
    assert wrap.count('loading="lazy"') == 6
    assert "<table" not in wrap.lower()
    assert "<details" not in wrap.lower()
    assert "display: grid" not in wrap.lower()

    tech_match = compile_section_body_re("My Tech Stack", order).search(readme)
    assert tech_match is not None
    tech = tech_match.group(0)
    assert "<!-- SKILLS:START -->" in tech
    for teaser in ("AI/ML", "Full-Stack", "Data Engineering", "Open Source"):
        assert f'alt="{teaser}"' not in tech

    for title in order:
        assert_visible_or_comment_heading(readme, title)
    positions = [heading_index(readme, title) for title in order]
    assert positions == sorted(positions)

    banner_idx = readme.index('alt="Banner"')
    badges_start = readme.index("<!-- README:TOP_BADGES:START -->")
    featured_start = readme.index("<!-- README:FEATURED_PROJECTS:START -->")
    living_start = heading_index(readme, "Living Art")
    assert banner_idx < badges_start < featured_start < living_start


def test_finalize_authenticates_readme_star_history_without_argv_token() -> None:
    """README GraphQL enrichment receives only the run-scoped token environment."""
    finalize = _workflow_jobs()["finalize"]
    steps = cast(list[dict[str, Any]], finalize["steps"])
    sections_step = next(
        step for step in steps if step.get("name") == "Generate README Sections"
    )

    assert sections_step.get("env") == {"GITHUB_TOKEN": "${{ github.token }}"}
    run = str(sections_step["run"])
    assert "GITHUB_TOKEN" not in run
    assert "github.token" not in run


def test_fact_ship_dev_main_is_not_a_publication_target() -> None:
    """fact-ship-dev: publication is refs/heads/dev only; main is not a target."""
    text = _workflow_text()
    push_match = re.search(
        r"(?ms)^  push:\n    branches:\n((?:      - [^\n]+\n)+)",
        text,
    )
    assert push_match is not None
    push_branches = re.findall(r"- (\S+)", push_match.group(1))
    assert push_branches == ["dev"]
    assert "main" not in push_branches
    assert "master" not in push_branches

    for job_id in (
        "update-starred-lists",
        "generate-assets",
        "update-readme-wakatime",
        "generate-profile-metrics",
        "prepare-event-art-inputs",
        "finalize",
    ):
        assert "github.ref == 'refs/heads/dev'" in _job_block(text, job_id)

    finalize = _job_block(text, "finalize")
    assert "TARGET_BRANCH: ${{ github.head_ref || github.ref_name }}" in finalize
    push_script = _marked_shell_block(
        text,
        "trigger-consistent-push",
        "trigger-consistent-push",
    )
    assert 'origin "HEAD:refs/heads/${TARGET_BRANCH}"' in push_script
    assert '[ "${TARGET_BRANCH}" != "dev" ]' in push_script
    assert "restricted to refs/heads/dev" in push_script
    assert "HEAD:refs/heads/main" not in push_script
    assert re.search(r"git push\s+origin\s+HEAD:main\b", push_script) is None


def test_fact_banner_pin_ci_byte_compares_origin_main() -> None:
    """fact-banner-pin: CI verify fails closed if origin/main cannot be read."""
    workflow = _workflow_text()
    assets = _job_block(workflow, "generate-assets")
    assert "generate banner" not in workflow
    assert "origin/main:.github/assets/img/" in assets
    assert "Unable to read pinned banner from" in assets
    assert "Pinned banner drifted from origin/main" in assets


def test_finalize_push_refuses_non_dev_target_branch(tmp_path: Path) -> None:
    """fact-ship-dev: the push script refuses TARGET_BRANCH=main."""
    script = _marked_shell_block(
        _workflow_text(),
        "trigger-consistent-push",
        "trigger-consistent-push",
    )
    result = subprocess.run(
        ["bash", "-euo", "pipefail", "-c", script],
        cwd=tmp_path,
        env={
            "PATH": os.environ["PATH"],
            "TARGET_BRANCH": "main",
            "TRIGGER_REF_TYPE": "branch",
            "TRIGGER_SHA": "deadbeef",
        },
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    combined = f"{result.stdout}\n{result.stderr}"
    assert "restricted to refs/heads/dev" in combined
    assert "got main" in combined


def test_fact_lowlighter_off_production_music_tweets_activity_stay_no() -> None:
    """fact-lowlighter-off: music/tweets/activity stay off; no Spotify in with:."""
    workflow = _workflow_text()
    prod = _job_block(workflow, "generate-profile-metrics")
    for block in _lowlighter_with_blocks(prod):
        assert re.search(r"(?m)^\s*plugin_music:\s*no\s*$", block)
        assert re.search(r"(?m)^\s*plugin_tweets:\s*no\s*$", block)
        assert re.search(r"(?m)^\s*plugin_activity:\s*no\s*$", block)
        assert "SPOTIFY_" not in block
        assert "plugin_music_token" not in block
        assert "plugin_music_provider" not in block
    assert "anmol098/waka-readme-stats" not in workflow


def test_fact_lowlighter_retry_lines_achievements_gists_isolated_off() -> None:
    """fact-lowlighter-retry: unclean plugins stay off; no stub isolate-retry card."""
    prod = _job_block(_workflow_text(), "generate-profile-metrics")
    primary, _additional, extra = _lowlighter_with_blocks(prod)
    assert "plugin_lines: no" in primary
    assert "plugin_achievements: no" in primary
    assert "plugin_gists: no" in primary
    assert "plugin_gists: no" in extra
    assert "plugin_lines:" not in extra
    assert "plugin_achievements:" not in extra
    assert "plugin_lines: yes" not in prod
    assert "plugin_achievements: yes" not in prod
    assert "plugin_gists: yes" not in prod
    extra_svg = Path(".github/assets/img/metrics.extra.svg")
    assert extra_svg.is_file()
    extra_text = extra_svg.read_text(encoding="utf-8").lower()
    assert "will be regenerated" not in extra_text
    assert "an error occur" not in extra_text


def test_fact_habits_both_yaml_on_and_first_party_card_exists() -> None:
    """fact-habits-both: plugin_habits on primary and first-party card redesigned."""
    prod = _job_block(_workflow_text(), "generate-profile-metrics")
    primary, additional, extra = _lowlighter_with_blocks(prod)
    assert "plugin_habits: yes" in primary
    assert "plugin_habits_facts: yes" in primary
    assert "plugin_habits_charts: yes" in primary
    assert "plugin_habits: no" in additional
    assert "plugin_habits: no" in extra
    habits = Path(".github/assets/img/metrics-habits.svg")
    assert habits.is_file()
    text = habits.read_text(encoding="utf-8")
    assert "Coding habits" in text
    assert "habits-focus" in text
    assert "habits-peak" in text
    assert "habits-streaks" in text
    assert 'src=".github/assets/img/metrics-habits.svg"' in README_PATH.read_text(
        encoding="utf-8"
    )
