"""Generate word_cloud commands."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Any

import typer

from ._common import (
    Annotated,
    Any,
    Mapping,
    Path,
    SimpleNamespace,
    _apply_stopword_filter,
    _load_project_config,
    _prompt_to_frequencies,
    console,
    generate_app,
    json,
    logger,
    os,
    re,
    typer,
)

def _wc_import():
    """Lazy-import word cloud and techs modules, raising typer.Exit on failure."""
    try:
        from ...techs import Technology, load_technologies
        from ...word_clouds import (
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
            "uv sync --locked --extra word-clouds"
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
    yaml_settings=None,
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
    # Always pack the full filtered vocabulary (every topic / every language).
    effective_max_words = num_terms
    logger.info(
        f"Using max_words={effective_max_words} for "
        f"{md_path.name} ({num_terms} filtered terms — full vocabulary)."
    )

    out_dir = Path(output_path.parent) if output_path else wc.PROFILE_IMG_OUTPUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    out_filename = (
        output_path.name
        if output_path
        else f"wordcloud_typographic_by_{source}.svg"
    )

    # Larger canvas + slightly smaller max font so dense vocabularies (300+ topics)
    # remain fully legible under the fit-all typographic packer.
    canvas_w, canvas_h = (1680, 1050) if num_terms > 100 else (1400, 900)
    settings = wc.WordCloudSettings.from_yaml_model(
        yaml_settings,
        renderer="typographic",
        width=canvas_w,
        height=canvas_h,
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
        min_font_size=5.0 if num_terms > 100 else 7.0,
        max_font_size=42.0 if num_terms > 100 else 64.0,
    )


def _wc_from_topics(
    wc,
    output_path: Path | None,
    stopwords_list: list[str],
    max_words: int,
    layout_readability=None,
    yaml_settings=None,
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
        yaml_settings=yaml_settings,
    )


def _wc_from_languages(
    wc,
    output_path: Path | None,
    stopwords_list: list[str],
    max_words: int,
    layout_readability=None,
    yaml_settings=None,
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
        yaml_settings=yaml_settings,
    )


def _wc_from_techs(
    wc,
    techs_path: Path,
    output_path: Path | None,
    stopwords_list: list[str],
    max_words: int,
    layout_readability=None,
    yaml_settings=None,
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
        else Path(
            yaml_settings.output_dir
            if yaml_settings is not None
            else wc.WordCloudSettings().output_dir
        )
    )
    out_dir.mkdir(parents=True, exist_ok=True)

    settings = wc.WordCloudSettings.from_yaml_model(
        yaml_settings,
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
    yaml_settings=None,
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
        else Path(
            yaml_settings.output_dir
            if yaml_settings is not None
            else wc.WordCloudSettings().output_dir
        )
    )
    out_dir.mkdir(parents=True, exist_ok=True)

    settings = wc.WordCloudSettings.from_yaml_model(
        yaml_settings,
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
    from ...config import WordCloudSettingsModel as ConfigWordCloudSettingsModel  # lazy

    proj_config = _load_project_config(config_path)
    wc = _wc_import()

    config_wc_model = proj_config.word_cloud_settings or ConfigWordCloudSettingsModel()

    stopwords_list: list[str] = []
    if config_wc_model and config_wc_model.stopwords:
        stopwords_list.extend(config_wc_model.stopwords)
    # Prefer adapter-derived max_words so YAML↔runtime stay aligned (HR-05).
    runtime_defaults = config_wc_model.to_word_cloud_settings()
    max_words = max(1, int(runtime_defaults.max_words))

    generated_path: Path | None = None
    layout_readability = runtime_defaults.layout_readability
    ran_source = False

    if from_topics_md:
        generated_path = _wc_from_topics(
            wc,
            output_path if not from_languages_md else None,
            stopwords_list,
            max_words,
            layout_readability=layout_readability,
            yaml_settings=config_wc_model,
        )
        ran_source = True

    if from_languages_md:
        generated_path = _wc_from_languages(
            wc,
            output_path if not from_topics_md else None,
            stopwords_list,
            max_words,
            layout_readability=layout_readability,
            yaml_settings=config_wc_model,
        )
        ran_source = True

    if not ran_source and techs_path and techs_path.exists():
        generated_path = _wc_from_techs(
            wc,
            techs_path,
            output_path,
            stopwords_list,
            max_words,
            layout_readability=layout_readability,
            yaml_settings=config_wc_model,
        )
        ran_source = True

    if not ran_source:
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
                yaml_settings=config_wc_model,
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



