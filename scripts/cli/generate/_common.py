"""Shared helpers and generate Typer app shell."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from enum import StrEnum
from pathlib import Path
from typing import Any

import typer

from ...art.artifacts import (
    DEFAULT_PUBLIC_SURFACE_DIR,
    sync_living_art_artifacts,
)
from ...art.roster import CANDIDATE_STYLE_KEYS, SHIPPED_STYLE_KEYS
from ...art.timelapse import DEFAULT_PUBLISHED_MAX_FRAMES
from ...config import (
    DEFAULT_CONFIG_PATH,
    DEFAULT_SKILLS_PATH,  # noqa: F401 - re-export for domain modules
    ProjectConfig,
    load_config,
    load_skills,  # noqa: F401 - re-export for domain modules
)
from ...utils import console, get_logger

logger = get_logger(module=__name__)
_LIVING_ART_DEFAULT_MAX_FRAMES = DEFAULT_PUBLISHED_MAX_FRAMES

generate_app = typer.Typer(
    name="generate",
    help=(
        "[bold]Generate profile assets[/bold] — banners, QR codes, "
        "word clouds, and more."
    ),
    no_args_is_help=True,
    rich_markup_mode="rich",
)


class ReadmeCardVariant(StrEnum):
    GH_CARD = "gh-card"
    LEGACY = "legacy"


def _load_project_config(config_path: Path | None) -> ProjectConfig:
    """Load project config with consistent error handling."""
    # Prefer package-level load_config so tests can patch scripts.cli.generate.load_config  # noqa: E501
    try:
        from scripts.cli import generate as generate_pkg

        _load = getattr(generate_pkg, "load_config", load_config)
    except Exception:  # noqa: BLE001 — fall back to direct import
        _load = load_config
    effective_path = config_path or DEFAULT_CONFIG_PATH
    try:
        return _load(effective_path)
    except FileNotFoundError:
        console.print(
            f"[bold red]Error:[/bold red] Config not found: "
            "[yellow]"
            f"{effective_path}"
            "[/yellow]. Run "
            "[cyan]readme config generate-default[/cyan]."
        )
        raise typer.Exit(code=1)
    except (OSError, ValueError) as e:
        console.print(f"[bold red]Error:[/bold red] Failed to load config: {e}")
        raise typer.Exit(code=1)


def _refresh_living_art_artifacts(output_dir: Path) -> None:
    """Regenerate the manifest and HTML gallery for current living-art outputs."""
    public_surface_dir = (
        DEFAULT_PUBLIC_SURFACE_DIR
        if DEFAULT_PUBLIC_SURFACE_DIR.parent.exists()
        else None
    )
    manifest_path, gallery_path, manifest = sync_living_art_artifacts(
        output_dir,
        public_surface_dir=public_surface_dir,
    )
    console.print(
        "[dim]Updated living-art index:[/] "
        f"{manifest['total_assets']} assets, "
        f"manifest={manifest_path}, gallery={gallery_path}"
        + (
            f", public_surface={public_surface_dir}"
            if public_surface_dir is not None
            else ""
        )
    )


def _format_style_help(styles: tuple[str, ...]) -> str:
    """Render a human-readable style list for CLI help text."""
    if not styles:
        return ""
    if len(styles) == 1:
        return styles[0]
    return f"{', '.join(styles[:-1])}, or {styles[-1]}"


_LIVING_ART_STYLE_HELP = _format_style_help(CANDIDATE_STYLE_KEYS)


def _selected_living_art_styles(only: str | None) -> tuple[str, ...]:
    """Return styles for this invocation: ``--only`` ∈ candidates, else shipped."""
    if only:
        if only not in CANDIDATE_STYLE_KEYS:
            console.print(
                f"[bold red]Error:[/bold red] Unknown style [bold]{only}[/bold]. "
                f"Choose from: {_LIVING_ART_STYLE_HELP}"
            )
            raise typer.Exit(code=1)
        return (only,)
    return tuple(SHIPPED_STYLE_KEYS)


def _load_required_json(option_name: str, path: Path | None) -> dict[str, Any]:
    """Read a required JSON payload from disk with consistent CLI errors."""
    if not path or not path.exists():
        console.print(
            f"[bold red]Error:[/bold red] {option_name} is required and must exist."
        )
        raise typer.Exit(code=1)
    return json.loads(path.read_text(encoding="utf-8"))


def _generate_living_art_timelapse(
    *,
    profile: str,
    metrics_path: Path | None,
    history_path: Path | None,
    only: str | None,
    max_frames: int,
    size: int,
    workers: int,
    output_dir: Path,
) -> list[Path]:
    """Render canonical living-art timelapse GIF outputs."""
    metrics = _load_required_json("--metrics-path", metrics_path)
    history = _load_required_json("--history-path", history_path)
    active_styles = _selected_living_art_styles(only)

    from ...art.timelapse import render_timelapse

    outputs = render_timelapse(
        history,
        metrics,
        styles=list(active_styles),
        max_frames=max_frames,
        size=size,
        output_dir=output_dir,
        owner=profile,
        workers=workers,
    )

    expected_output_names = {f"living-{style}.gif" for style in active_styles}
    observed_output_names = [path.name for path in outputs]
    observed_output_name_set = set(observed_output_names)
    missing_output_names = sorted(expected_output_names - observed_output_name_set)
    unexpected_output_names = sorted(observed_output_name_set - expected_output_names)
    duplicate_output_names = sorted(
        name
        for name in observed_output_name_set
        if observed_output_names.count(name) > 1
    )
    missing_output_files = sorted(str(path) for path in outputs if not path.is_file())
    expected_output_parent = output_dir.resolve()
    unexpected_output_locations = sorted(
        str(path) for path in outputs if path.resolve().parent != expected_output_parent
    )

    generation_issues: list[str] = []
    if missing_output_names:
        generation_issues.append(
            f"missing requested outputs: {', '.join(missing_output_names)}"
        )
    if unexpected_output_names:
        generation_issues.append(
            f"unexpected outputs: {', '.join(unexpected_output_names)}"
        )
    if duplicate_output_names:
        generation_issues.append(
            f"duplicate outputs: {', '.join(duplicate_output_names)}"
        )
    if missing_output_files:
        generation_issues.append(
            f"returned paths do not exist: {', '.join(missing_output_files)}"
        )
    if unexpected_output_locations:
        generation_issues.append(
            "outputs escaped the requested directory: "
            + ", ".join(unexpected_output_locations)
        )
    if generation_issues:
        console.print(
            "[bold red]Error:[/bold red] Living-art generation was incomplete; "
            + "; ".join(generation_issues)
        )
        raise typer.Exit(code=1)

    for path in outputs:
        size_mb = path.stat().st_size / (1024 * 1024)
        console.print(f"[bold green]Generated:[/] {path} ({size_mb:.1f} MB)")

    if active_styles == tuple(SHIPPED_STYLE_KEYS):
        _refresh_living_art_artifacts(output_dir)
    else:
        console.print(
            "[yellow]Skipped living-art index refresh for a partial style "
            "invocation.[/yellow]"
        )

    return outputs


def _apply_stopword_filter(
    frequencies: Mapping[str, int | float],
    stopwords_list: list[str],
) -> dict[str, int | float]:
    """Drop case-insensitive stopwords from explicit frequency maps."""
    blocked = {word.strip().casefold() for word in stopwords_list if word.strip()}
    if not blocked:
        return dict(frequencies)
    return {
        term: weight
        for term, weight in frequencies.items()
        if term.casefold() not in blocked
    }


def _prompt_to_frequencies(text: str, stopwords_list: list[str]) -> dict[str, float]:
    """Derive prompt frequencies from tags or free text."""
    blocked = {word.strip().casefold() for word in stopwords_list if word.strip()}

    chunked = [chunk.strip() for chunk in re.split(r"[\n,;|]+", text) if chunk.strip()]
    if len(chunked) > 1:
        frequencies: dict[str, float] = {}
        for chunk in chunked:
            phrase = chunk.split(":", 1)[-1].strip()
            if not phrase or phrase.casefold() in blocked:
                continue
            frequencies[phrase] = frequencies.get(phrase, 0.0) + 1.0
        if frequencies:
            return frequencies

    frequencies: dict[str, float] = {}
    for token in re.findall(r"[A-Za-z0-9][A-Za-z0-9+#.\-]*", text):
        if token.casefold() in blocked:
            continue
        frequencies[token] = frequencies.get(token, 0.0) + 1.0
    return frequencies


# ---------------------------------------------------------------------------
# banner
# ---------------------------------------------------------------------------
