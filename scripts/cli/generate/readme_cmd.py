"""Generate readme domain commands."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Annotated, Any

import typer

from ._common import (
    DEFAULT_SKILLS_PATH,
    ReadmeCardVariant,
    _load_project_config,
    console,
    generate_app,
    load_skills,
    logger,
)


@generate_app.command(
    help="Generate shields.io technology badges and inject into README."
)
def skills(
    config_path: Annotated[
        Path | None,
        typer.Option(
            "--config-path",
            help="Project configuration file path.",
            rich_help_panel="Configuration",
        ),
    ] = None,
    skills_path: Annotated[
        Path | None,
        typer.Option(
            "--skills-path",
            help="Path to skills.yaml for badge generation.",
            rich_help_panel="Configuration",
        ),
    ] = None,
) -> None:
    """Generate shields.io technology badges and inject into README."""
    _load_project_config(config_path)  # validate config exists

    from ...skills import SkillsBadgeGenerator

    effective_skills_path = skills_path or DEFAULT_SKILLS_PATH
    try:
        skills_settings = load_skills(effective_skills_path)
    except (FileNotFoundError, ValueError) as e:
        logger.error("Failed to load skills config: {e}", e=e)
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(code=1)

    generator = SkillsBadgeGenerator(settings=skills_settings)
    result_path = generator.generate()
    console.print(f"[bold green]Skills badges injected into {result_path}[/]")


# ---------------------------------------------------------------------------
# readme-sections
# ---------------------------------------------------------------------------


def _collect_card_style_update(
    card_style_updates: dict[str, dict[str, Any]],
    family: str,
    variant: ReadmeCardVariant | None,
    transparent_canvas: bool | None,
    show_title: bool | None,
) -> None:
    """Collect non-None card style overrides into *card_style_updates*."""
    update: dict[str, Any] = {}
    if variant is not None:
        update["variant"] = variant.value
    if transparent_canvas is not None:
        update["transparent_canvas"] = transparent_canvas
    if show_title is not None:
        update["show_title"] = show_title
    if update:
        card_style_updates[family] = update


@generate_app.command(
    name="supplemental-metrics",
    help="Generate repo-owned supplemental metrics cards.",
)
def supplemental_metrics(
    config_path: Annotated[
        Path | None,
        typer.Option(
            "--config-path",
            help="Project configuration file path.",
            rich_help_panel="Configuration",
        ),
    ] = None,
    owner: Annotated[
        str,
        typer.Option(
            "--owner",
            help="GitHub owner/login to render metrics for.",
            rich_help_panel="Supplemental Metrics Options",
        ),
    ] = "wyattowalsh",
    repo: Annotated[
        str,
        typer.Option(
            "--repo",
            help="Repository name used for GitHub-side metrics hydration.",
            rich_help_panel="Supplemental Metrics Options",
        ),
    ] = "wyattowalsh",
    output_dir: Annotated[
        Path,
        typer.Option(
            "--output-dir",
            help="Directory to write supplemental SVG assets into.",
            rich_help_panel="Configuration",
        ),
    ] = Path(".github/assets/img"),
    manifest_path: Annotated[
        Path,
        typer.Option(
            "--manifest-path",
            help="Path for the supplemental metrics manifest JSON.",
            rich_help_panel="Configuration",
        ),
    ] = Path(".github/assets/img/metrics-supplemental.manifest.json"),
    x_handle: Annotated[
        str | None,
        typer.Option(
            "--x-handle",
            help="X handle to query; defaults to --owner.",
            rich_help_panel="Supplemental Metrics Options",
        ),
    ] = None,
) -> None:
    """Generate repo-owned supplemental metrics SVG assets."""
    _load_project_config(config_path)
    from ...supplemental_metrics import generate_supplemental_metrics

    statuses = generate_supplemental_metrics(
        owner=owner,
        repo=repo,
        output_dir=output_dir,
        manifest_path=manifest_path,
        x_handle=x_handle,
    )
    for key, status in statuses.items():
        state = "enabled" if status.enabled else f"disabled ({status.reason})"
        console.print(f"[bold green]{key}[/]: {state}")


@generate_app.command(
    name="readme-sections",
    help="Generate dynamic README sections (badges, projects, blog posts).",
)
def readme_sections(
    config_path: Annotated[
        Path | None,
        typer.Option(
            "--config-path",
            help="Project configuration file path.",
            rich_help_panel="Configuration",
        ),
    ] = None,
    output_path: Annotated[
        Path | None,
        typer.Option(
            "--output-path",
            help="Output path for README file.",
            rich_help_panel="Configuration",
        ),
    ] = None,
    # -- default card --
    readme_default_card_variant: Annotated[
        ReadmeCardVariant | None,
        typer.Option(
            "--readme-default-card-variant",
            help="Default README per-card SVG variant.",
            case_sensitive=False,
            rich_help_panel="Card Styles",
        ),
    ] = None,
    readme_default_card_transparent_canvas: Annotated[
        bool | None,
        typer.Option(
            "--readme-default-card-transparent-canvas/--no-readme-default-card-transparent-canvas",
            help="Default README legacy per-card SVG canvas transparency.",
            rich_help_panel="Card Styles",
        ),
    ] = None,
    readme_default_card_show_title: Annotated[
        bool | None,
        typer.Option(
            "--readme-default-card-show-title/--no-readme-default-card-show-title",
            help="Default README legacy per-card SVG title visibility.",
            rich_help_panel="Card Styles",
        ),
    ] = None,
    # -- connect card --
    readme_connect_card_variant: Annotated[
        ReadmeCardVariant | None,
        typer.Option(
            "--readme-connect-card-variant",
            help="Connect README per-card SVG variant.",
            case_sensitive=False,
            rich_help_panel="Card Styles",
        ),
    ] = None,
    readme_connect_card_transparent_canvas: Annotated[
        bool | None,
        typer.Option(
            "--readme-connect-card-transparent-canvas/--no-readme-connect-card-transparent-canvas",
            help="Connect README legacy per-card SVG canvas transparency.",
            rich_help_panel="Card Styles",
        ),
    ] = None,
    readme_connect_card_show_title: Annotated[
        bool | None,
        typer.Option(
            "--readme-connect-card-show-title/--no-readme-connect-card-show-title",
            help="Connect README legacy per-card SVG title visibility.",
            rich_help_panel="Card Styles",
        ),
    ] = None,
    # -- featured card --
    readme_featured_card_variant: Annotated[
        ReadmeCardVariant | None,
        typer.Option(
            "--readme-featured-card-variant",
            help="Featured README per-card SVG variant.",
            case_sensitive=False,
            rich_help_panel="Card Styles",
        ),
    ] = None,
    readme_featured_card_transparent_canvas: Annotated[
        bool | None,
        typer.Option(
            "--readme-featured-card-transparent-canvas/--no-readme-featured-card-transparent-canvas",
            help="Featured README legacy per-card SVG canvas transparency.",
            rich_help_panel="Card Styles",
        ),
    ] = None,
    readme_featured_card_show_title: Annotated[
        bool | None,
        typer.Option(
            "--readme-featured-card-show-title/--no-readme-featured-card-show-title",
            help="Featured README legacy per-card SVG title visibility.",
            rich_help_panel="Card Styles",
        ),
    ] = None,
    # -- blog card --
    readme_blog_card_variant: Annotated[
        ReadmeCardVariant | None,
        typer.Option(
            "--readme-blog-card-variant",
            help="Blog README per-card SVG variant.",
            case_sensitive=False,
            rich_help_panel="Card Styles",
        ),
    ] = None,
    readme_blog_card_transparent_canvas: Annotated[
        bool | None,
        typer.Option(
            "--readme-blog-card-transparent-canvas/--no-readme-blog-card-transparent-canvas",
            help="Blog README legacy per-card SVG canvas transparency.",
            rich_help_panel="Card Styles",
        ),
    ] = None,
    readme_blog_card_show_title: Annotated[
        bool | None,
        typer.Option(
            "--readme-blog-card-show-title/--no-readme-blog-card-show-title",
            help="Blog README legacy per-card SVG title visibility.",
            rich_help_panel="Card Styles",
        ),
    ] = None,
) -> None:
    """Generate dynamic README sections (badges, projects, blog posts)."""
    from ...config import ReadmeSectionsSettings
    from ...readme_sections import ReadmeSectionGenerator

    proj_config = _load_project_config(config_path)

    readme_settings_raw = proj_config.readme_sections_settings
    readme_settings = (
        readme_settings_raw
        if isinstance(readme_settings_raw, ReadmeSectionsSettings)
        else ReadmeSectionsSettings.model_validate(readme_settings_raw or {})
    )
    if output_path:
        readme_settings = readme_settings.model_copy(
            update={"readme_path": str(output_path)}
        )

    card_style_updates: dict[str, dict[str, Any]] = {}

    _collect_card_style_update(
        card_style_updates,
        "default",
        readme_default_card_variant,
        readme_default_card_transparent_canvas,
        readme_default_card_show_title,
    )
    _collect_card_style_update(
        card_style_updates,
        "connect",
        readme_connect_card_variant,
        readme_connect_card_transparent_canvas,
        readme_connect_card_show_title,
    )
    _collect_card_style_update(
        card_style_updates,
        "featured",
        readme_featured_card_variant,
        readme_featured_card_transparent_canvas,
        readme_featured_card_show_title,
    )
    _collect_card_style_update(
        card_style_updates,
        "blog",
        readme_blog_card_variant,
        readme_blog_card_transparent_canvas,
        readme_blog_card_show_title,
    )

    if card_style_updates:
        current_styles = readme_settings.svg.card_styles
        style_update_payload: dict[str, Any] = {}
        for family, update in card_style_updates.items():
            current_style = getattr(current_styles, family)
            style_update_payload[family] = current_style.model_copy(update=update)
        readme_settings = readme_settings.model_copy(
            update={
                "svg": readme_settings.svg.model_copy(
                    update={
                        "card_styles": current_styles.model_copy(
                            update=style_update_payload
                        )
                    }
                )
            }
        )

    generator = ReadmeSectionGenerator(settings=readme_settings)
    result_path = generator.generate()
    console.print(f"[bold green]README sections updated in {result_path}[/]")


# ---------------------------------------------------------------------------
# wakatime — first-party WakaTime README section artifact
# ---------------------------------------------------------------------------


@generate_app.command(
    name="wakatime",
    help=(
        "Generate first-party WakaTime README section artifact "
        "(waka-section.md). Finalize applies markers."
    ),
)
def wakatime(
    output_dir: Annotated[
        Path,
        typer.Option(
            "--output-dir",
            help="Directory for waka-section.md artifact.",
            rich_help_panel="Configuration",
        ),
    ] = Path("."),
    output: Annotated[
        Path | None,
        typer.Option(
            "--output",
            help="Explicit artifact path (defaults to OUTPUT_DIR/waka-section.md).",
            rich_help_panel="Configuration",
        ),
    ] = None,
    github_login: Annotated[
        str | None,
        typer.Option(
            "--github-login",
            help="Optional GitHub login for short-info enrichment.",
            rich_help_panel="Data",
        ),
    ] = None,
    no_github: Annotated[
        bool,
        typer.Option(
            "--no-github",
            help="Skip optional GitHub short-info enrichment.",
            rich_help_panel="Data",
        ),
    ] = False,
    allow_missing_key: Annotated[
        bool,
        typer.Option(
            "--allow-missing-key",
            help="Exit 0 and write skip marker when WAKATIME_API_KEY is absent.",
            rich_help_panel="Configuration",
        ),
    ] = False,
) -> None:
    """Fetch WakaTime stats and write the README section artifact for CI."""
    from ...wakatime_readme import (
        DEFAULT_ARTIFACT_NAME,
        generate_waka_section,
        write_skip_artifact,
        write_waka_artifact,
    )

    api_key = (os.environ.get("WAKATIME_API_KEY") or "").strip()
    output_path = output or (output_dir / DEFAULT_ARTIFACT_NAME)

    if not api_key:
        if allow_missing_key:
            skip_dir = output_dir if output is None else output_path.parent
            write_skip_artifact(
                skip_dir,
                "WAKATIME_API_KEY missing; skipped first-party Waka generation",
            )
            console.print("[yellow]WAKATIME_API_KEY missing; wrote skip marker.[/]")
            return
        console.print(
            "[bold red]Error:[/bold red] WAKATIME_API_KEY is required "
            "(or pass --allow-missing-key)."
        )
        raise typer.Exit(code=1)

    try:
        body = generate_waka_section(
            api_key=api_key,
            github_login=github_login,
            include_github=not no_github,
        )
        write_waka_artifact(body, output_path)
    except (OSError, ValueError, RuntimeError) as exc:
        console.print(f"[bold red]Error:[/bold red] WakaTime generation failed: {exc}")
        raise typer.Exit(code=1) from exc

    console.print(f"[bold green]WakaTime section artifact:[/] {output_path}")


# ---------------------------------------------------------------------------
# all  — run every generator in sequence
# ---------------------------------------------------------------------------
