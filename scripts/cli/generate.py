"""Generate subcommands — each asset type gets its own Typer command."""

from __future__ import annotations

import json
import os
import re
import sys
from collections.abc import Mapping
from enum import StrEnum
from pathlib import Path
from types import SimpleNamespace
from typing import Annotated, Any

import typer

from ..art.artifacts import (
    DEFAULT_PUBLIC_SURFACE_DIR,
    LIVING_ART_STYLE_KEYS,
    sync_living_art_artifacts,
)
from ..art.timelapse import DEFAULT_PUBLISHED_MAX_FRAMES
from ..config import (
    DEFAULT_CONFIG_PATH,
    DEFAULT_SKILLS_PATH,
    ProjectConfig,
    load_config,
    load_skills,
)
from ..utils import console, get_logger

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
    effective_path = config_path or DEFAULT_CONFIG_PATH
    try:
        return load_config(effective_path)
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


_LIVING_ART_STYLE_HELP = _format_style_help(LIVING_ART_STYLE_KEYS)


def _selected_living_art_styles(only: str | None) -> tuple[str, ...]:
    """Return the active living-art styles for this command invocation."""
    if only:
        if only not in LIVING_ART_STYLE_KEYS:
            console.print(
                f"[bold red]Error:[/bold red] Unknown style [bold]{only}[/bold]. "
                f"Choose from: {_LIVING_ART_STYLE_HELP}"
            )
            raise typer.Exit(code=1)
        return (only,)
    return tuple(LIVING_ART_STYLE_KEYS)


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
) -> list[Path]:
    """Render canonical living-art timelapse GIF outputs."""
    metrics = _load_required_json("--metrics-path", metrics_path)
    history = _load_required_json("--history-path", history_path)
    active_styles = _selected_living_art_styles(only)

    from ..art.timelapse import render_timelapse

    outputs = render_timelapse(
        history,
        metrics,
        styles=list(active_styles),
        max_frames=max_frames,
        size=size,
        owner=profile,
        workers=workers,
    )

    for path in outputs:
        size_mb = path.stat().st_size / (1024 * 1024)
        console.print(f"[bold green]Generated:[/] {path} ({size_mb:.1f} MB)")

    if not outputs:
        console.print("[yellow]No timelapse GIFs generated.[/yellow]")
    else:
        _refresh_living_art_artifacts(outputs[0].parent)

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


@generate_app.command(help="Generate SVG profile banner (light + dark variants).")
def banner(
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
            help="Output path for generated file.",
            rich_help_panel="Configuration",
        ),
    ] = None,
    title: Annotated[
        str | None,
        typer.Option(
            "--title",
            help="Banner title.",
            rich_help_panel="Banner Options",
        ),
    ] = None,
    subtitle: Annotated[
        str | None,
        typer.Option(
            "--subtitle",
            help="Banner subtitle.",
            rich_help_panel="Banner Options",
        ),
    ] = None,
    width: Annotated[
        int | None,
        typer.Option(
            "--width",
            help="Banner width (px).",
            rich_help_panel="Banner Options",
        ),
    ] = None,
    height: Annotated[
        int | None,
        typer.Option(
            "--height",
            help="Banner height (px).",
            rich_help_panel="Banner Options",
        ),
    ] = None,
    optimize_banner: Annotated[
        bool | None,
        typer.Option(
            "--optimize-banner/--no-optimize-banner",
            help="Optimize banner with SVGO.",
            rich_help_panel="Banner Options",
        ),
    ] = None,
) -> None:
    """Generate SVG profile banner with light and dark variants."""
    from ..config import BannerSettings as ConfigBannerSettings  # lazy import

    proj_config = _load_project_config(config_path)

    try:
        from ..banner import BannerConfig, generate_banner
    except ImportError:
        logger.error(
            "Banner dependencies/script components are missing. "
            "Ensure banner.py is correct and dependencies installed: "
            "uv pip install wyattowalsh[banner]"
        )
        console.print("[bold red]Error:[/bold red] Banner components missing.")
        raise typer.Exit(code=1)

    cfg_banner_settings_defaults = ConfigBannerSettings()
    banner_data = cfg_banner_settings_defaults.model_dump()

    if proj_config.banner_settings:
        banner_data.update(proj_config.banner_settings.model_dump(exclude_unset=True))

    if output_path:
        banner_data["output_path"] = str(output_path)
    if title is not None:
        banner_data["title"] = title
    if subtitle is not None:
        banner_data["subtitle"] = subtitle
    if width is not None:
        banner_data["width"] = width
    if height is not None:
        banner_data["height"] = height
    if optimize_banner is not None:
        banner_data["optimize_with_svgo"] = optimize_banner

    try:
        final_banner_config = BannerConfig(**banner_data)
        logger.info(
            "Generating banner with config: "
            f"{final_banner_config.model_dump_json(indent=2)}"
        )
        generate_banner(cfg=final_banner_config)
        console.print(
            f"[bold green]SVG banner generated: {final_banner_config.output_path}[/]"
        )
        # Generate dark variant — failure does not affect the primary banner
        try:
            dark_banner_data = banner_data.copy()
            dark_banner_data["dark_mode"] = True
            dark_output = Path(final_banner_config.output_path)
            dark_banner_data["output_path"] = str(
                dark_output.parent / f"{dark_output.stem}-dark{dark_output.suffix}"
            )
            dark_banner_config = BannerConfig(**dark_banner_data)
            generate_banner(cfg=dark_banner_config)
            console.print(
                "[bold green]Dark SVG banner generated: "
                f"{dark_banner_config.output_path}[/]"
            )
        except Exception as dark_err:
            logger.warning(
                f"Dark banner generation failed (light banner succeeded): {dark_err}",
                exc_info=True,
            )
            console.print(
                "[yellow]Dark banner generation failed — light banner was saved.[/]"
            )
    except Exception as e:
        logger.error("Banner generation failed: {e}", e=e, exc_info=True)
        console.print(f"[bold red]Error:[/bold red] Banner generation failed: {e}")
        raise typer.Exit(code=1)


# ---------------------------------------------------------------------------
# qr
# ---------------------------------------------------------------------------


@generate_app.command(help="Generate artistic vCard QR code.")
def qr(
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
            help="Output path for generated file.",
            rich_help_panel="Configuration",
        ),
    ] = None,
    qr_error_correction: Annotated[
        str | None,
        typer.Option(
            "--qr-error-correction",
            help="QR error correction (L,M,Q,H).",
            case_sensitive=False,
            rich_help_panel="QR Options",
        ),
    ] = None,
    qr_scale: Annotated[
        int | None,
        typer.Option(
            "--qr-scale",
            help="QR code scale factor.",
            rich_help_panel="QR Options",
        ),
    ] = None,
    qr_background_path: Annotated[
        Path | None,
        typer.Option(
            "--qr-background-path",
            help="QR background SVG path.",
            rich_help_panel="QR Options",
        ),
    ] = None,
) -> None:
    """Generate an artistic vCard QR code."""
    from ..config import QRCodeSettings as ConfigQRCodeSettings  # lazy import

    proj_config = _load_project_config(config_path)

    try:
        from ..qr import QRCodeGenerator
    except ImportError:
        logger.error(
            "QR code dependencies/script components are missing. "
            "Ensure qr.py is correct and dependencies installed: "
            "uv pip install wyattowalsh[qr]"
        )
        console.print("[bold red]Error:[/bold red] QR code components missing.")
        raise typer.Exit(code=1)

    cfg_qr_settings_defaults = ConfigQRCodeSettings()
    qr_settings_data = cfg_qr_settings_defaults.model_dump()

    if proj_config.qr_code_settings and isinstance(
        proj_config.qr_code_settings, ConfigQRCodeSettings
    ):
        qr_settings_data.update(
            proj_config.qr_code_settings.model_dump(exclude_unset=True)
        )
    elif proj_config.qr_code_settings:
        logger.warning(
            f"proj_config.qr_code_settings is of unexpected type: "
            f"{type(proj_config.qr_code_settings)}. Expected ConfigQRCodeSettings. "
            "Using defaults."
        )

    cfg_vcard_data = proj_config.v_card_data

    if cfg_vcard_data is None:  # Should not happen with default_factory
        logger.error("Critical: VCardData is None despite default_factory.")
        raise typer.Exit(code=1)

    default_bg_path_str = qr_background_path or qr_settings_data.get(
        "default_background_path"
    )
    default_output_dir_str = (
        output_path.parent
        if output_path
        else qr_settings_data.get("output_dir") or ".github/assets/img"
    )

    final_output_filename = (
        output_path.name
        if output_path
        else qr_settings_data.get("output_filename") or "qr.png"
    )

    try:
        qr_gen = QRCodeGenerator(
            default_background_path=(
                Path(default_bg_path_str) if default_bg_path_str else None
            ),
            default_output_dir=Path(default_output_dir_str),
            default_scale=(
                qr_scale
                if qr_scale is not None
                else int(qr_settings_data.get("default_scale", 25))
            ),
        )

        error_correction = (
            qr_error_correction
            if qr_error_correction is not None
            else qr_settings_data.get("error_correction", "H")
        )
        vcard_display_name = (
            getattr(cfg_vcard_data, "displayname", "DefaultVCard")
            if cfg_vcard_data
            else "DefaultVCard"
        )

        logger.info(
            f"Generating QR for: {vcard_display_name}, "
            f"Output: "
            f"{{Path(default_output_dir_str) / final_output_filename}}, "
            f"Background: {default_bg_path_str}"
        )
        logger.debug(
            f"  QR Settings: scale="
            f"{qr_scale or qr_settings_data.get('default_scale', 25)}, "
            f"error_correction={error_correction}"
        )
        logger.debug("VCard Details: {cfg_vcard_data}", cfg_vcard_data=cfg_vcard_data)

        generated_qr_path = qr_gen.generate_artistic_vcard_qr(
            vcard_details=cfg_vcard_data,
            output_filename=final_output_filename,
            error_correction=error_correction,
        )
        console.print(f"[bold green]QR code generated: {generated_qr_path}[/]")
    except FileNotFoundError as fnf_error:
        logger.error(
            f"QR generation error (file not found): {fnf_error}",
            exc_info=True,
        )
        console.print(f"[bold red]File Not Found Error:[/bold red] {fnf_error}")
        raise typer.Exit(code=1)
    except ValueError as val_error:
        logger.error(
            f"QR generation error (value error): {val_error}",
            exc_info=True,
        )
        console.print(f"[bold red]Value Error:[/bold red] {val_error}")
        raise typer.Exit(code=1)
    except Exception as e:
        logger.error("QR generation failed: {e}", e=e, exc_info=True)
        console.print(f"[bold red]Error:[/bold red] QR generation failed: {e}")
        raise typer.Exit(code=1)


# ---------------------------------------------------------------------------
# word-cloud helpers
# ---------------------------------------------------------------------------


def _wc_import():
    """Lazy-import word cloud and techs modules, raising typer.Exit on failure."""
    try:
        from ..techs import Technology, load_technologies
        from ..word_clouds import (
            DEFAULT_FONT_PATH,
            DEFAULT_MAX_WORDS,
            LANGUAGES_MD_PATH,
            PROFILE_IMG_OUTPUT_DIR,
            TOPICS_MD_PATH,
            WordCloudGenerator,
            WordCloudSettings,
            parse_markdown_for_word_cloud_frequencies,
        )

        return SimpleNamespace(
            Technology=Technology,
            load_technologies=load_technologies,
            DEFAULT_FONT_PATH=DEFAULT_FONT_PATH,
            DEFAULT_MAX_WORDS=DEFAULT_MAX_WORDS,
            LANGUAGES_MD_PATH=LANGUAGES_MD_PATH,
            PROFILE_IMG_OUTPUT_DIR=PROFILE_IMG_OUTPUT_DIR,
            TOPICS_MD_PATH=TOPICS_MD_PATH,
            WordCloudGenerator=WordCloudGenerator,
            WordCloudSettings=WordCloudSettings,
            parse_markdown_for_word_cloud_frequencies=parse_markdown_for_word_cloud_frequencies,
        )
    except ImportError as e_import:
        logger.error("Detailed import error: {e}", e=e_import, exc_info=True)
        logger.error(
            "Word cloud/techs components missing. Install dependencies: "
            "uv pip install readme[word-clouds]"
        )
        console.print("[bold red]Error:[/bold red] Word cloud components missing.")
        raise typer.Exit(code=1)


def _wc_from_markdown(
    wc,
    md_path: Path,
    source: str,
    color_func_name: str,
    output_path: Path | None,
    stopwords_list: list[str],
    max_words: int,
    layout_readability=None,
) -> Path | None:
    """Generate word cloud from a markdown file with source-specific overrides."""
    logger.info("Generating word cloud from {}: {}", source, md_path)
    if not md_path.exists():
        logger.error(
            f"Markdown file not found: {md_path}. "
            f"Cannot generate {source} word cloud via CLI."
        )
        return None

    frequencies = _apply_stopword_filter(
        wc.parse_markdown_for_word_cloud_frequencies(md_path),
        stopwords_list,
    )
    if not frequencies:
        logger.warning(
            f"No frequencies parsed from {md_path.name}, "
            f"skipping {source} word cloud generation via CLI."
        )
        return None

    num_terms = len(frequencies)
    effective_max_words = min(max_words, num_terms)
    logger.info(
        f"Using max_words={effective_max_words} for "
        f"{md_path.name} ({num_terms} filtered terms)."
    )

    out_dir = Path(output_path.parent) if output_path else wc.PROFILE_IMG_OUTPUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    out_filename = (
        output_path.name
        if output_path
        else f"wordcloud_metaheuristic-anim_by_{source}.svg"
    )

    settings = wc.WordCloudSettings(
        renderer="metaheuristic-anim",
        width=1200,
        height=800,
        max_words=effective_max_words,
        output_dir=str(out_dir),
        layout_readability=layout_readability,
    )
    generator = wc.WordCloudGenerator(base_settings=settings)
    return generator.generate(
        frequencies=frequencies,
        output_path=out_dir / out_filename,
        source=source,
        color_func_name=color_func_name,
    )


def _wc_from_topics(
    wc,
    output_path: Path | None,
    stopwords_list: list[str],
    max_words: int,
    layout_readability=None,
) -> Path | None:
    """Generate word cloud from topics.md with topic-specific overrides."""
    return _wc_from_markdown(
        wc,
        wc.TOPICS_MD_PATH,
        "topics",
        "ocean",
        output_path,
        stopwords_list,
        max_words,
        layout_readability,
    )


def _wc_from_languages(
    wc,
    output_path: Path | None,
    stopwords_list: list[str],
    max_words: int,
    layout_readability=None,
) -> Path | None:
    """Generate word cloud from languages.md with language-specific overrides."""
    return _wc_from_markdown(
        wc,
        wc.LANGUAGES_MD_PATH,
        "languages",
        "aurora",
        output_path,
        stopwords_list,
        max_words,
        layout_readability,
    )


def _wc_from_techs(
    wc,
    techs_path: Path,
    output_path: Path | None,
    stopwords_list: list[str],
    max_words: int,
    layout_readability=None,
) -> Path | None:
    """Generate word cloud from a technologies markdown file."""
    logger.info(f"Loading technologies from specified path: {techs_path}")
    loaded_techs_list: list = wc.load_technologies(techs_path)
    if not loaded_techs_list:
        logger.warning(f"load_technologies returned no data from {techs_path}.")
        return None

    frequencies = _apply_stopword_filter(
        {tech.name: float(tech.level) for tech in loaded_techs_list},
        stopwords_list,
    )
    if not frequencies:
        logger.warning(f"No frequencies derived from {techs_path}.")
        return None

    logger.info(f"Derived {len(frequencies)} terms with frequencies from {techs_path}.")

    out_dir = (
        Path(output_path.parent)
        if output_path
        else Path(wc.WordCloudSettings().output_dir)
    )
    out_dir.mkdir(parents=True, exist_ok=True)

    settings = wc.WordCloudSettings(
        output_dir=str(out_dir),
        max_words=max_words,
        layout_readability=layout_readability,
    )
    generator = wc.WordCloudGenerator(base_settings=settings)

    logger.info("Generating word cloud from calculated frequencies.")
    return generator.generate(
        frequencies=frequencies,
        output_path=output_path,
        source="techs",
    )


def _wc_from_prompt(
    wc,
    text: str,
    output_path: Path | None,
    stopwords_list: list[str],
    max_words: int,
    layout_readability=None,
) -> Path | None:
    """Generate word cloud from a text prompt."""
    logger.info("Generating word cloud from text (prompt).")

    frequencies = _prompt_to_frequencies(text, stopwords_list)
    if not frequencies:
        logger.error("Prompt produced no usable terms after stopword filtering.")
        return None

    out_dir = (
        Path(output_path.parent)
        if output_path
        else Path(wc.WordCloudSettings().output_dir)
    )
    out_dir.mkdir(parents=True, exist_ok=True)

    settings = wc.WordCloudSettings(
        output_dir=str(out_dir),
        max_words=max_words,
        layout_readability=layout_readability,
    )
    generator = wc.WordCloudGenerator(base_settings=settings)
    return generator.generate(
        frequencies=frequencies,
        output_path=output_path,
        source="prompt",
    )


# ---------------------------------------------------------------------------
# word-cloud
# ---------------------------------------------------------------------------


@generate_app.command(
    name="word-cloud",
    help="Generate word cloud from topics, languages, or custom text.",
)
def word_cloud(
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
            help="Output path for generated file.",
            rich_help_panel="Configuration",
        ),
    ] = None,
    techs_path: Annotated[
        Path | None,
        typer.Option(
            "--techs-path",
            help="Technologies.md path (for word clouds).",
            rich_help_panel="Word Cloud Options",
        ),
    ] = None,
    prompt: Annotated[
        str | None,
        typer.Option(
            "--prompt",
            help="Prompt for word cloud.",
            rich_help_panel="Word Cloud Options",
        ),
    ] = None,
    from_topics_md: Annotated[
        bool,
        typer.Option(
            "--from-topics-md",
            help="Generate word cloud from .github/assets/topics.md.",
            rich_help_panel="Word Cloud Options",
        ),
    ] = False,
    from_languages_md: Annotated[
        bool,
        typer.Option(
            "--from-languages-md",
            help="Generate word cloud from .github/assets/languages.md.",
            rich_help_panel="Word Cloud Options",
        ),
    ] = False,
) -> None:
    """Generate a word cloud from topics, languages, or custom text.

    Source priority (first match wins):
      1. --from-topics-md    hardcoded topics.md path + topic overrides
      2. --from-languages-md hardcoded languages.md path + language overrides
      3. --techs-path        custom markdown file
      4. --prompt            literal text string
      5. config prompt       from word_cloud_settings.prompt
    """
    from ..config import WordCloudSettingsModel as ConfigWordCloudSettingsModel  # lazy

    proj_config = _load_project_config(config_path)
    wc = _wc_import()

    config_wc_model = proj_config.word_cloud_settings or ConfigWordCloudSettingsModel()

    stopwords_list: list[str] = []
    if config_wc_model and config_wc_model.stopwords:
        stopwords_list.extend(config_wc_model.stopwords)
    max_words = max(
        1,
        int(getattr(config_wc_model, "max_words", wc.DEFAULT_MAX_WORDS)),
    )

    generated_path: Path | None = None
    layout_readability = getattr(config_wc_model, "layout_readability", None)

    if from_topics_md:
        generated_path = _wc_from_topics(
            wc,
            output_path,
            stopwords_list,
            max_words,
            layout_readability=layout_readability,
        )

    elif from_languages_md:
        generated_path = _wc_from_languages(
            wc,
            output_path,
            stopwords_list,
            max_words,
            layout_readability=layout_readability,
        )

    elif techs_path and techs_path.exists():
        generated_path = _wc_from_techs(
            wc,
            techs_path,
            output_path,
            stopwords_list,
            max_words,
            layout_readability=layout_readability,
        )

    else:
        # Resolve prompt text from CLI arg or config
        effective_prompt = prompt
        if effective_prompt is None:
            cfg_data = config_wc_model.model_dump(exclude_unset=True)
            if cfg_data.get("prompt") is not None:
                effective_prompt = cfg_data["prompt"]
                logger.info(f'Using config prompt for word cloud: "{effective_prompt}"')

        if effective_prompt is not None:
            logger.info(f'Using prompt for word cloud: "{effective_prompt}"')
            generated_path = _wc_from_prompt(
                wc,
                effective_prompt,
                output_path,
                stopwords_list,
                max_words,
                layout_readability=layout_readability,
            )
        else:
            logger.error(
                "Word cloud generation skipped: No valid input "
                "(techs_path with data, or text/prompt) was prepared."
            )

    if generated_path and Path(generated_path).exists():
        console.print(f"[bold green]Word cloud generated: {generated_path}[/]")
    else:
        logger.error("Word cloud generation failed or produced no output file.")
        console.print("[bold red]Error:[/bold red] Word cloud generation failed.")


# ---------------------------------------------------------------------------
# generative
# ---------------------------------------------------------------------------


@generate_app.command(
    name="generative",
    help="Generate event-driven generative artwork from metrics.",
)
def generative_art(
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
            help="Output directory for generated files.",
            rich_help_panel="Configuration",
        ),
    ] = None,
    metrics_path: Annotated[
        Path | None,
        typer.Option(
            "--metrics-path",
            help="Path to metrics JSON for generative art.",
            rich_help_panel="Generative Options",
        ),
    ] = None,
) -> None:
    """Generate event-driven generative artwork from metrics JSON."""
    _load_project_config(config_path)  # validate config exists

    try:
        from ..generative import generate_activity_art, generate_community_art
    except ImportError:
        logger.error(
            "Generative art dependencies/script components are missing. "
            "Ensure generative.py is correct."
        )
        console.print("[bold red]Error:[/bold red] Generative art components missing.")
        raise typer.Exit(code=1)

    if not metrics_path or not metrics_path.exists():
        logger.error("Metrics JSON required. Use --metrics-path to specify.")
        raise typer.Exit(code=1)

    metrics = json.loads(metrics_path.read_text())

    output_dir = Path(output_path) if output_path else Path(".github/assets/img")
    output_dir.mkdir(parents=True, exist_ok=True)

    for art_type in ["community", "activity"]:
        for dark in [False, True]:
            suffix = "-dark" if dark else ""
            out = output_dir / f"generative-{art_type}{suffix}.svg"
            if art_type == "community":
                generate_community_art(metrics, dark_mode=dark, output_path=out)
            else:
                generate_activity_art(metrics, dark_mode=dark, output_path=out)
            console.print(f"[bold green]Generated: {out}[/]")


# ---------------------------------------------------------------------------
# living-art
# ---------------------------------------------------------------------------


@generate_app.command(
    name="animated",
    help="Generate CSS-animated SVG living art seeded from commit history.",
)
def animated(
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
            help="GitHub username (used for labeling).",
            rich_help_panel="Animated Art Options",
        ),
    ] = "wyattowalsh",
    output_path: Annotated[
        Path | None,
        typer.Option(
            "--output-path",
            help="Legacy animated exports always write into .github/assets/img.",
            rich_help_panel="Configuration",
        ),
    ] = None,
    metrics_path: Annotated[
        Path | None,
        typer.Option(
            "--metrics-path",
            help="Path to metrics JSON from fetch_metrics.",
            rich_help_panel="Animated Art Options",
        ),
    ] = None,
    history_path: Annotated[
        Path | None,
        typer.Option(
            "--history-path",
            help="Path to history JSON from fetch_history.",
            rich_help_panel="Animated Art Options",
        ),
    ] = None,
    frames: Annotated[
        int,
        typer.Option(
            "--frames",
            min=2,
            help="Frame count for the growth animation.",
            rich_help_panel="Animated Art Options",
        ),
    ] = 7,
    size: Annotated[
        int,
        typer.Option(
            "--size",
            min=64,
            help="Frame size in pixels (square).",
            rich_help_panel="Animated Art Options",
        ),
    ] = 400,
    only: Annotated[
        str | None,
        typer.Option(
            "--only",
            help=f"Restrict to one style: {_LIVING_ART_STYLE_HELP}.",
            rich_help_panel="Animated Art Options",
        ),
    ] = None,
    svg: Annotated[
        bool,
        typer.Option(
            "--svg/--gif",
            help="Emit animated SVG stacks (default) or legacy GIF growth loops.",
            rich_help_panel="Animated Art Options",
        ),
    ] = True,
) -> None:
    """Generate legacy animated living-art outputs via the compatibility module."""
    _load_project_config(config_path)

    from ..art import animate as animate_module

    if output_path is not None:
        logger.info(
            "Animated art ignores --output-path and writes to .github/assets/img: {}",
            output_path,
        )

    argv = [
        "animate",
        "--profile",
        profile,
        "--frames",
        str(frames),
        "--size",
        str(size),
    ]
    if only is not None:
        argv.extend(["--only", only])
    if svg:
        argv.append("--svg")
    if metrics_path is not None:
        argv.extend(["--metrics-path", str(metrics_path)])
    if history_path is not None:
        argv.extend(["--history-path", str(history_path)])

    repo_root = Path(__file__).resolve().parents[2]
    previous_cwd = Path.cwd()
    previous_argv = sys.argv[:]
    try:
        os.chdir(repo_root)
        sys.argv = argv
        animate_module.main()
    finally:
        sys.argv = previous_argv
        os.chdir(previous_cwd)


@generate_app.command(
    name="living-art",
    help="Generate living-art timelapse GIFs.",
)
def living_art(
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
            help="GitHub username (used for labeling).",
            rich_help_panel="Living Art Options",
        ),
    ] = "wyattowalsh",
    max_frames: Annotated[
        int,
        typer.Option(
            "--max-frames",
            "--frames",
            min=5,
            help="Maximum frames per GIF (default 120 targets ~30s playback).",
            rich_help_panel="Living Art Options",
        ),
    ] = _LIVING_ART_DEFAULT_MAX_FRAMES,
    size: Annotated[
        int,
        typer.Option(
            "--size",
            min=64,
            help="Frame size in pixels (square).",
            rich_help_panel="Living Art Options",
        ),
    ] = 400,
    only: Annotated[
        str | None,
        typer.Option(
            "--only",
            help=f"Restrict to one style: {_LIVING_ART_STYLE_HELP}.",
            rich_help_panel="Living Art Options",
        ),
    ] = None,
    metrics_path: Annotated[
        Path | None,
        typer.Option(
            "--metrics-path",
            help="Path to metrics JSON from fetch_metrics.",
            rich_help_panel="Living Art Options",
        ),
    ] = None,
    history_path: Annotated[
        Path | None,
        typer.Option(
            "--history-path",
            help="Path to history JSON from fetch_history.",
            rich_help_panel="Living Art Options",
        ),
    ] = None,
    workers: Annotated[
        int,
        typer.Option(
            "--workers",
            min=1,
            help="Parallel rendering workers.",
            rich_help_panel="Living Art Options",
        ),
    ] = 4,
) -> None:
    """Generate canonical living-art timelapse GIFs."""
    _load_project_config(config_path)  # validate config exists
    _generate_living_art_timelapse(
        profile=profile,
        metrics_path=metrics_path,
        history_path=history_path,
        only=only,
        max_frames=max_frames,
        size=size,
        workers=workers,
    )


# ---------------------------------------------------------------------------
# timelapse
# ---------------------------------------------------------------------------


@generate_app.command(
    name="timelapse",
    help=(
        "Generate living-art timelapse GIFs where each frame = one day of "
        "profile history."
    ),
)
def timelapse(
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
            help="GitHub username (used for labeling).",
            rich_help_panel="Timelapse Options",
        ),
    ] = "wyattowalsh",
    metrics_path: Annotated[
        Path | None,
        typer.Option(
            "--metrics-path",
            help="Path to metrics JSON from fetch_metrics.",
            rich_help_panel="Timelapse Options",
        ),
    ] = None,
    history_path: Annotated[
        Path | None,
        typer.Option(
            "--history-path",
            help="Path to history JSON from fetch_history.",
            rich_help_panel="Timelapse Options",
        ),
    ] = None,
    max_frames: Annotated[
        int,
        typer.Option(
            "--max-frames",
            "--frames",
            min=5,
            help="Maximum frames per GIF (default 120 targets ~30s playback).",
            rich_help_panel="Timelapse Options",
        ),
    ] = _LIVING_ART_DEFAULT_MAX_FRAMES,
    size: Annotated[
        int,
        typer.Option(
            "--size",
            min=64,
            help="Frame size in pixels (square).",
            rich_help_panel="Timelapse Options",
        ),
    ] = 400,
    only: Annotated[
        str | None,
        typer.Option(
            "--only",
            help=f"Restrict to one style: {_LIVING_ART_STYLE_HELP}.",
            rich_help_panel="Timelapse Options",
        ),
    ] = None,
    workers: Annotated[
        int,
        typer.Option(
            "--workers",
            min=1,
            help="Parallel rendering workers.",
            rich_help_panel="Timelapse Options",
        ),
    ] = 4,
) -> None:
    """Generate timelapse GIFs showing day-by-day profile evolution."""
    _load_project_config(config_path)  # validate config exists
    _generate_living_art_timelapse(
        profile=profile,
        metrics_path=metrics_path,
        history_path=history_path,
        only=only,
        max_frames=max_frames,
        size=size,
        workers=workers,
    )


# ---------------------------------------------------------------------------
# skills
# ---------------------------------------------------------------------------


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

    from ..skills import SkillsBadgeGenerator

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
    from ..config import ReadmeSectionsSettings
    from ..readme_sections import ReadmeSectionGenerator

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
# all  — run every generator in sequence
# ---------------------------------------------------------------------------


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

    results: list[tuple[str, str]] = []  # (name, status)

    # -- banner --
    try:
        banner(config_path=config_path, output_path=output_path)
        results.append(("Banner", "[green]OK[/green]"))
    except (typer.Exit, SystemExit):
        results.append(("Banner", "[red]FAILED[/red]"))

    # -- qr --
    try:
        qr(config_path=config_path, output_path=output_path)
        results.append(("QR Code", "[green]OK[/green]"))
    except (typer.Exit, SystemExit):
        results.append(("QR Code", "[red]FAILED[/red]"))

    # -- word cloud (topics) --
    try:
        word_cloud(
            config_path=config_path,
            output_path=output_path,
            from_topics_md=True,
        )
        results.append(("Word Cloud (topics)", "[green]OK[/green]"))
    except (typer.Exit, SystemExit):
        results.append(("Word Cloud (topics)", "[red]FAILED[/red]"))

    # -- word cloud (languages) --
    try:
        word_cloud(
            config_path=config_path,
            output_path=output_path,
            from_languages_md=True,
        )
        results.append(("Word Cloud (languages)", "[green]OK[/green]"))
    except (typer.Exit, SystemExit):
        results.append(("Word Cloud (languages)", "[red]FAILED[/red]"))

    # -- skills --
    try:
        skills(config_path=config_path, skills_path=skills_path)
        results.append(("Skills Badges", "[green]OK[/green]"))
    except (typer.Exit, SystemExit):
        results.append(("Skills Badges", "[red]FAILED[/red]"))

    # -- readme sections --
    try:
        readme_sections(config_path=config_path, output_path=output_path)
        results.append(("README Sections", "[green]OK[/green]"))
    except (typer.Exit, SystemExit):
        results.append(("README Sections", "[red]FAILED[/red]"))

    # -- generative (optional) --
    if metrics_path and metrics_path.exists():
        try:
            generative_art(
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
            animated(
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
            living_art(
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
