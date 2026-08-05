"""Generate all_cmd commands."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Annotated

import typer

from ._common import console, generate_app


def _cmds():
    """Resolve sibling commands via the package (test-patch friendly)."""
    from scripts.cli import generate as generate_pkg

    return generate_pkg


@generate_app.command(
    name="all",
    help="Run all generators (skips those missing required data paths).",
)
def all_assets(
    config_path: Annotated[
        Path | None,
        typer.Option(
            "--config-path",
            help="Project configuration file path.",
            rich_help_panel="Configuration",
        ),
    ] = None,
    profile: Annotated[
        str,
        typer.Option(
            "--profile",
            help="GitHub username used for living-art labeling.",
            rich_help_panel="Configuration",
        ),
    ] = "wyattowalsh",
    output_path: Annotated[
        Path | None,
        typer.Option(
            "--output-path",
            help="Base output directory for generated files.",
            rich_help_panel="Configuration",
        ),
    ] = None,
    metrics_path: Annotated[
        Path | None,
        typer.Option(
            "--metrics-path",
            help="Path to metrics JSON for generative art (optional).",
            rich_help_panel="Data Paths",
        ),
    ] = None,
    history_path: Annotated[
        Path | None,
        typer.Option(
            "--history-path",
            help="Path to history JSON for animated art (optional).",
            rich_help_panel="Data Paths",
        ),
    ] = None,
    skills_path: Annotated[
        Path | None,
        typer.Option(
            "--skills-path",
            help="Path to skills.yaml for badge generation (optional).",
            rich_help_panel="Data Paths",
        ),
    ] = None,
) -> None:
    """Run all generators, skipping those that lack required data paths."""
    from rich.panel import Panel  # lazy import

    g = _cmds()
    results: list[tuple[str, str]] = []  # (name, status)
    repo_name = Path.cwd().name
    supplemental_output_dir = (
        output_path
        if output_path and output_path.is_dir()
        else Path(".github/assets/img")
    )
    supplemental_manifest_path = (
        supplemental_output_dir / "metrics-supplemental.manifest.json"
    )

    # -- banner --
    try:
        g.banner(config_path=config_path, output_path=output_path)
        results.append(("Banner", "[green]OK[/green]"))
    except (typer.Exit, SystemExit):
        results.append(("Banner", "[red]FAILED[/red]"))

    # -- qr --
    try:
        g.qr(config_path=config_path, output_path=output_path)
        results.append(("QR Code", "[green]OK[/green]"))
    except (typer.Exit, SystemExit):
        results.append(("QR Code", "[red]FAILED[/red]"))

    # -- word cloud (topics) --
    try:
        g.word_cloud(
            config_path=config_path,
            output_path=output_path,
            from_topics_md=True,
        )
        results.append(("Word Cloud (topics)", "[green]OK[/green]"))
    except (typer.Exit, SystemExit):
        results.append(("Word Cloud (topics)", "[red]FAILED[/red]"))

    # -- word cloud (languages) --
    try:
        g.word_cloud(
            config_path=config_path,
            output_path=output_path,
            from_languages_md=True,
        )
        results.append(("Word Cloud (languages)", "[green]OK[/green]"))
    except (typer.Exit, SystemExit):
        results.append(("Word Cloud (languages)", "[red]FAILED[/red]"))

    # -- skills --
    try:
        g.skills(config_path=config_path, skills_path=skills_path)
        results.append(("Skills Badges", "[green]OK[/green]"))
    except (typer.Exit, SystemExit):
        results.append(("Skills Badges", "[red]FAILED[/red]"))

    # -- supplemental metrics (optional; requires GitHub token) --
    if any(os.getenv(name) for name in ("METRICS_TOKEN", "GITHUB_TOKEN", "GH_TOKEN")):
        try:
            g.supplemental_metrics(
                config_path=config_path,
                owner=profile,
                repo=repo_name,
                output_dir=supplemental_output_dir,
                manifest_path=supplemental_manifest_path,
                x_handle=profile,
            )
            results.append(("Supplemental Metrics", "[green]OK[/green]"))
        except (typer.Exit, SystemExit):
            results.append(("Supplemental Metrics", "[red]FAILED[/red]"))
    else:
        console.print(
            "[yellow]Skipping supplemental metrics — no GitHub token found in "
            "METRICS_TOKEN, GITHUB_TOKEN, or GH_TOKEN.[/yellow]"
        )
        results.append(("Supplemental Metrics", "[yellow]SKIPPED[/yellow]"))

    # -- readme sections --
    try:
        g.readme_sections(config_path=config_path, output_path=output_path)
        results.append(("README Sections", "[green]OK[/green]"))
    except (typer.Exit, SystemExit):
        results.append(("README Sections", "[red]FAILED[/red]"))

    # -- generative (optional) --
    if metrics_path and metrics_path.exists():
        try:
            g.generative_art(
                config_path=config_path,
                output_path=output_path,
                metrics_path=metrics_path,
            )
            results.append(("Generative Art", "[green]OK[/green]"))
        except (typer.Exit, SystemExit):
            results.append(("Generative Art", "[red]FAILED[/red]"))
    else:
        console.print(
            "[yellow]Skipping generative art — --metrics-path not provided "
            "or file missing.[/yellow]"
        )
        results.append(("Generative Art", "[yellow]SKIPPED[/yellow]"))

    # -- animated (optional) --
    if history_path and history_path.exists():
        try:
            g.animated(
                config_path=config_path,
                profile=profile,
                output_path=output_path,
                metrics_path=metrics_path,
                history_path=history_path,
            )
            results.append(("Animated Art", "[green]OK[/green]"))
        except (typer.Exit, SystemExit):
            results.append(("Animated Art", "[red]FAILED[/red]"))
    else:
        console.print(
            "[yellow]Skipping animated art — --history-path not provided "
            "or file missing.[/yellow]"
        )
        results.append(("Animated Art", "[yellow]SKIPPED[/yellow]"))

    # -- living art / timelapse (optional; requires both metrics + history) --
    missing_living_art_inputs: list[str] = []
    if not metrics_path or not metrics_path.exists():
        missing_living_art_inputs.append("--metrics-path")
    if not history_path or not history_path.exists():
        missing_living_art_inputs.append("--history-path")

    if missing_living_art_inputs:
        missing_display = ", ".join(missing_living_art_inputs)
        console.print(
            "[yellow]Skipping living art — missing required "
            f"{missing_display}.[/yellow]"
        )
        results.append(("Living Art", "[yellow]SKIPPED[/yellow]"))
    else:
        try:
            g.living_art(
                config_path=config_path,
                profile=profile,
                metrics_path=metrics_path,
                history_path=history_path,
            )
            results.append(("Living Art", "[green]OK[/green]"))
        except (typer.Exit, SystemExit):
            results.append(("Living Art", "[red]FAILED[/red]"))

    # -- summary panel --
    lines = [f"  {name:<25} {status}" for name, status in results]
    summary = "\n".join(lines)
    console.print(
        Panel(
            summary,
            title="[bold]Generate All — Summary[/bold]",
            border_style="cyan",
        )
    )
