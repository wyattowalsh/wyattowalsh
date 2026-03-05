import logging
from enum import Enum
from pathlib import Path
from typing import Annotated, Any, Dict, List, Optional, Union

import typer
from pydantic import ValidationError
from rich.syntax import Syntax

# Core config imports
from .config import DEFAULT_CONFIG_PATH

from .config import BannerSettings as ConfigBannerSettings
from .config import ProjectConfig, load_config, save_config
from .config import QRCodeSettings as ConfigQRCodeSettings
from .config import Settings as AppSettings
from .config import WordCloudSettingsModel as ConfigWordCloudSettingsModel
from .utils import console as util_console
from .utils import get_logger

logger = get_logger(module=__name__)

app = typer.Typer(
    name="readme",
    help="CLI for readme project utilities, generation, and management.",
    add_completion=False,
    no_args_is_help=True,
    rich_markup_mode="rich",
)

# Default path for technologies.json, relative to this script's location
# This might be better sourced from ProjectConfig or a global constant
DEFAULT_TECHS_PATH = Path(__file__).parent.parent / "techs.md"


class EntityType(str, Enum):
    BANNER = "banner"
    QR_CODE = "qr_code"
    WORD_CLOUD = "word_cloud"
    CONFIG = "config"
    README = "readme"
    GENERATIVE = "generative"
    ANIMATED = "animated"
    SKILLS = "skills"


class OutputFormat(str, Enum):
    JSON = "json"
    YAML = "yaml"


class ReadmeCardVariant(str, Enum):
    GH_CARD = "gh-card"
    LEGACY = "legacy"


def _display_config(
    config_data: Union[ProjectConfig, AppSettings],
    output_format: OutputFormat = OutputFormat.JSON,
) -> None:
    if output_format == OutputFormat.JSON:
        config_str = config_data.model_dump_json(indent=2)
        syntax = Syntax(config_str, "json", theme="monokai", line_numbers=True)
        util_console.print(syntax)
    elif output_format == OutputFormat.YAML:
        try:
            import yaml  # type: ignore

            config_dict = config_data.model_dump(mode="python")
            yaml_str = yaml.dump(config_dict, indent=2, sort_keys=False)
            syntax = Syntax(
                yaml_str, "yaml", theme="monokai", line_numbers=True
            )
            util_console.print(syntax)
        except ImportError:
            logger.error(
                "PyYAML is not installed. Cannot display config as YAML. "
                "Falling back to JSON. Install with: uv pip install PyYAML"
            )
            _display_config(config_data, OutputFormat.JSON)
        except Exception as e:
            logger.error(f"Error converting config to YAML: {e}")
            _display_config(config_data, OutputFormat.JSON)


@app.command(
    name="config",
    help="Manage project configuration. Use subcommands to view or save.",
)
def config_main(
    ctx: typer.Context,
    action: Annotated[
        str, typer.Argument(help="Action: 'view', 'save', 'generate-default'.")
    ] = "view",
    path: Annotated[
        Optional[Path], typer.Option(help="Path to the configuration file.")
    ] = None,
    output_format: Annotated[
        OutputFormat,
        typer.Option(
            case_sensitive=False, help="Format for 'view' (json/yaml)."
        ),
    ] = OutputFormat.JSON,
) -> None:
    effective_path = path or DEFAULT_CONFIG_PATH
    logger.info(f"Configuration action: {action} for path: {effective_path}")

    if action == "view":
        try:
            config_obj = load_config(effective_path)
            util_console.print(
                f"[bold green]Current project configuration from "
                f"{effective_path}:[/]"
            )
            _display_config(config_obj, output_format)
        except FileNotFoundError:
            logger.error(
                f"Config file not found: {effective_path}. "
                "Use 'generate-default' or 'save' to create it."
            )
            util_console.print(
                f"[bold red]Error:[/bold red] Config file not found: "
                f"[yellow]{effective_path}[/yellow]."
            )
        except (ValueError, IOError) as e:
            logger.error(
                f"Failed to load/display config from {effective_path}: {e}"
            )
            util_console.print(
                f"[bold red]Error:[/bold red] Failed to load configuration: "
                f"{e}"
            )

    elif action == "save":
        try:
            try:
                config_to_save = load_config(effective_path)
                logger.info(
                    f"Loaded existing config from {effective_path} "
                    "to re-save/update."
                )
            except FileNotFoundError:
                logger.info(
                    f"Config file {effective_path} not found. "
                    "Creating new default config to save."
                )
                config_to_save = ProjectConfig()

            save_config(config_to_save, effective_path)
            util_console.print(
                f"[bold green]Configuration successfully saved to "
                f"{effective_path}[/]"
            )
            _display_config(config_to_save, OutputFormat.JSON)
        except (ValueError, IOError) as e:
            logger.error(
                f"Failed to save configuration to {effective_path}: {e}"
            )
            util_console.print(
                f"[bold red]Error:[/bold red] Failed to save configuration: "
                f"{e}"
            )

    elif action == "generate-default":
        try:
            if effective_path.exists():
                typer.confirm(
                    f"Config file {effective_path} already exists. Overwrite?",
                    abort=True,
                )
            default_cfg = ProjectConfig()
            save_config(default_cfg, effective_path)
            util_console.print(
                f"[bold green]Default configuration generated and saved to "
                f"{effective_path}[/]"
            )
            _display_config(default_cfg, output_format)
        except typer.Abort:
            logger.info("Default config generation aborted by user.")
            util_console.print("Aborted. No changes made.")
        except IOError as e:
            logger.error(
                f"Failed to gen/save default config at {effective_path}: {e}"
            )
            util_console.print(
                f"[bold red]Error:[/bold red] Could not gen/save default "
                f"config: {e}"
            )
            raise typer.Exit(code=1)
    else:
        logger.warning(f"Invalid configuration action: {action}")
        util_console.print(
            f"[bold red]Invalid action:[/bold red] '{action}'. "
            "Choose from 'view', 'save', 'generate-default'."
        )


@app.command()
def generate(  # NOSONAR
    entity_type: Annotated[
        EntityType,
        typer.Argument(
            case_sensitive=False, help="Type of entity to generate."
        ),
    ],
    config_path_cli: Annotated[
        Optional[Path],
        typer.Option("--config-path", help="Project configuration file path."),
    ] = None,
    output_path_cli: Annotated[
        Optional[Path],
        typer.Option("--output-path", help="Output path for generated file."),
    ] = None,
    techs_path_cli: Annotated[
        Optional[Path],
        typer.Option(
            "--techs-path", help="Technologies.md path (for word clouds)."
        ),
    ] = None,
    prompt_cli: Annotated[
        Optional[str], typer.Option("--prompt", help="Prompt for word cloud.")
    ] = None,
    title_cli: Annotated[
        Optional[str], typer.Option("--title", help="Banner title.")
    ] = None,
    subtitle_cli: Annotated[
        Optional[str], typer.Option("--subtitle", help="Banner subtitle.")
    ] = None,
    width_cli: Annotated[
        Optional[int], typer.Option("--width", help="Banner width (px).")
    ] = None,
    height_cli: Annotated[
        Optional[int], typer.Option("--height", help="Banner height (px).")
    ] = None,
    optimize_banner_cli: Annotated[
        Optional[bool],
        typer.Option(
            "--optimize-banner/--no-optimize-banner",
            help="Optimize banner with SVGO."
        ),
    ] = None,
    qr_error_correction_cli: Annotated[
        Optional[str],
        typer.Option(
            "--qr-error-correction",
            help="QR error correction (L,M,Q,H).",
            case_sensitive=False,
        ),
    ] = None,
    qr_scale_cli: Annotated[
        Optional[int], typer.Option("--qr-scale", help="QR code scale factor.")
    ] = None,
    qr_background_path_cli: Annotated[
        Optional[Path],
        typer.Option("--qr-background-path", help="QR background SVG path."),
    ] = None,
    readme_default_card_variant_cli: Annotated[
        Optional[ReadmeCardVariant],
        typer.Option(
            "--readme-default-card-variant",
            help="Default README per-card SVG variant.",
            case_sensitive=False,
        ),
    ] = None,
    readme_default_card_transparent_canvas_cli: Annotated[
        Optional[bool],
        typer.Option(
            "--readme-default-card-transparent-canvas/--no-readme-default-card-transparent-canvas",
            help="Default README per-card SVG canvas transparency.",
        ),
    ] = None,
    readme_default_card_show_title_cli: Annotated[
        Optional[bool],
        typer.Option(
            "--readme-default-card-show-title/--no-readme-default-card-show-title",
            help="Default README per-card SVG title visibility.",
        ),
    ] = None,
    readme_connect_card_variant_cli: Annotated[
        Optional[ReadmeCardVariant],
        typer.Option(
            "--readme-connect-card-variant",
            help="Connect README per-card SVG variant.",
            case_sensitive=False,
        ),
    ] = None,
    readme_connect_card_transparent_canvas_cli: Annotated[
        Optional[bool],
        typer.Option(
            "--readme-connect-card-transparent-canvas/--no-readme-connect-card-transparent-canvas",
            help="Connect README per-card SVG canvas transparency.",
        ),
    ] = None,
    readme_connect_card_show_title_cli: Annotated[
        Optional[bool],
        typer.Option(
            "--readme-connect-card-show-title/--no-readme-connect-card-show-title",
            help="Connect README per-card SVG title visibility.",
        ),
    ] = None,
    readme_featured_card_variant_cli: Annotated[
        Optional[ReadmeCardVariant],
        typer.Option(
            "--readme-featured-card-variant",
            help="Featured README per-card SVG variant.",
            case_sensitive=False,
        ),
    ] = None,
    readme_featured_card_transparent_canvas_cli: Annotated[
        Optional[bool],
        typer.Option(
            "--readme-featured-card-transparent-canvas/--no-readme-featured-card-transparent-canvas",
            help="Featured README per-card SVG canvas transparency.",
        ),
    ] = None,
    readme_featured_card_show_title_cli: Annotated[
        Optional[bool],
        typer.Option(
            "--readme-featured-card-show-title/--no-readme-featured-card-show-title",
            help="Featured README per-card SVG title visibility.",
        ),
    ] = None,
    readme_blog_card_variant_cli: Annotated[
        Optional[ReadmeCardVariant],
        typer.Option(
            "--readme-blog-card-variant",
            help="Blog README per-card SVG variant.",
            case_sensitive=False,
        ),
    ] = None,
    readme_blog_card_transparent_canvas_cli: Annotated[
        Optional[bool],
        typer.Option(
            "--readme-blog-card-transparent-canvas/--no-readme-blog-card-transparent-canvas",
            help="Blog README per-card SVG canvas transparency.",
        ),
    ] = None,
    readme_blog_card_show_title_cli: Annotated[
        Optional[bool],
        typer.Option(
            "--readme-blog-card-show-title/--no-readme-blog-card-show-title",
            help="Blog README per-card SVG title visibility.",
        ),
    ] = None,
    # New flags for word cloud generation from specific markdown files
    from_topics_md_cli: Annotated[
        bool,
        typer.Option(
            "--from-topics-md",
            help="Generate word cloud from .github/assets/topics.md.",
        ),
    ] = False,
    from_languages_md_cli: Annotated[
        bool,
        typer.Option(
            "--from-languages-md",
            help="Generate word cloud from .github/assets/languages.md.",
        ),
    ] = False,
    metrics_path_cli: Annotated[
        Optional[Path],
        typer.Option("--metrics-path", help="Path to metrics JSON for generative art."),
    ] = None,
    history_path_cli: Annotated[
        Optional[Path],
        typer.Option("--history-path", help="Path to history JSON for animated art."),
    ] = None,
    skills_path_cli: Annotated[
        Optional[Path],
        typer.Option("--skills-path", help="Path to skills.yaml for badge generation."),
    ] = None,
) -> None:
    effective_config_path = config_path_cli or DEFAULT_CONFIG_PATH
    logger.info(
        f"Attempting to generate {entity_type.value} "
        f"using config {effective_config_path}"
    )

    try:
        proj_config = load_config(effective_config_path)
    except FileNotFoundError:
        logger.error(
            f"Config file not found: {effective_config_path}. "
            "Use `config generate-default`."
        )
        util_console.print(
            f"[bold red]Error:[/bold red] Config file not found: "
            f"[yellow]{effective_config_path}[/yellow]."
        )
        raise typer.Exit(code=1)
    except (ValueError, IOError) as e:
        logger.error(
            f"Failed to load project config from {effective_config_path}: {e}"
        )
        util_console.print(
            f"[bold red]Error:[/bold red] Failed to load configuration: "
            f"{e}"
        )
        raise typer.Exit(code=1)

    if entity_type == EntityType.BANNER:
        try:
            from .banner import BannerConfig, generate_banner
        except ImportError:
            logger.error(
                "Banner dependencies/script components are missing. "
                "Ensure banner.py is correct and dependencies installed: "
                "uv pip install wyattowalsh[banner]"
            )
            util_console.print(
                "[bold red]Error:[/bold red] Banner components missing."
            )
            raise typer.Exit(code=1)

        cfg_banner_settings_defaults = ConfigBannerSettings()
        banner_data = cfg_banner_settings_defaults.model_dump()

        if proj_config.banner_settings:
            banner_data.update(
                proj_config.banner_settings.model_dump(exclude_unset=True)
            )

        if output_path_cli:
            banner_data["output_path"] = str(output_path_cli)
        if title_cli is not None:
            banner_data["title"] = title_cli
        if subtitle_cli is not None:
            banner_data["subtitle"] = subtitle_cli
        if width_cli is not None:
            banner_data["width"] = width_cli
        if height_cli is not None:
            banner_data["height"] = height_cli
        if optimize_banner_cli is not None:
            banner_data["optimize_with_svgo"] = optimize_banner_cli

        try:
            final_banner_config = BannerConfig(**banner_data)
            logger.info(
                "Generating banner with config: "
                f"{final_banner_config.model_dump_json(indent=2)}"
            )
            generate_banner(cfg=final_banner_config)
            util_console.print(
                "[bold green]SVG banner generated: "
                f"{final_banner_config.output_path}[/]"
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
                util_console.print(
                    f"[bold green]Dark SVG banner generated: {dark_banner_config.output_path}[/]"
                )
            except Exception as dark_err:
                logger.warning(
                    f"Dark banner generation failed (light banner succeeded): {dark_err}",
                    exc_info=True,
                )
                util_console.print(
                    "[yellow]Dark banner generation failed — light banner was saved.[/]"
                )
        except Exception as e:
            logger.error(f"Banner generation failed: {e}", exc_info=True)
            util_console.print(
                f"[bold red]Error:[/bold red] Banner generation failed: {e}"
            )
            raise typer.Exit(code=1)

    elif entity_type == EntityType.QR_CODE:
        try:
            from .qr import QRCodeGenerator
        except ImportError:
            logger.error(
                "QR code dependencies/script components are missing. "
                "Ensure qr.py is correct and dependencies installed: "
                "uv pip install wyattowalsh[qr]"
            )
            util_console.print(
                "[bold red]Error:[/bold red] QR code components missing."
            )
            raise typer.Exit(code=1)

        cfg_qr_settings_defaults = ConfigQRCodeSettings()
        qr_settings_data = cfg_qr_settings_defaults.model_dump()

        if (
            proj_config.qr_code_settings 
            and isinstance(proj_config.qr_code_settings, ConfigQRCodeSettings)
        ):
            qr_settings_data.update(
                proj_config.qr_code_settings.model_dump(exclude_unset=True)
            )
        elif proj_config.qr_code_settings:
            # Log a warning if it's not None but also not the expected type
            logger.warning(
                f"proj_config.qr_code_settings is of unexpected type: {type(proj_config.qr_code_settings)}. Expected ConfigQRCodeSettings. Using defaults."
            )
        
        cfg_vcard_data = proj_config.v_card_data

        if cfg_vcard_data is None:  # Should not happen with default_factory
            logger.error(
                "Critical: VCardData is None despite default_factory."
            )
            raise typer.Exit(code=1)

        default_bg_path_str = (
            qr_background_path_cli
            or qr_settings_data.get("default_background_path")
            or ".github/assets/img/icon.svg"
        )
        default_output_dir_str = (
            output_path_cli.parent
            if output_path_cli
            else qr_settings_data.get("output_dir") or ".github/assets/img"
        )
        
        final_output_filename = (
            output_path_cli.name
            if output_path_cli
            else qr_settings_data.get("output_filename")
            or "qr.png"
        )

        try:
            qr_gen = QRCodeGenerator(
                default_background_path=Path(default_bg_path_str),
                default_output_dir=Path(default_output_dir_str),
                default_scale=(
                    qr_scale_cli
                    if qr_scale_cli is not None
                    else int(qr_settings_data.get("default_scale", 25))
                ),
            )

            error_correction = (
                qr_error_correction_cli
                if qr_error_correction_cli is not None
                else qr_settings_data.get("error_correction", "H")
            )
            vcard_display_name = (
                getattr(cfg_vcard_data, 'displayname', "DefaultVCard")
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
                f"{qr_scale_cli or qr_settings_data.get('default_scale', 25)}, "
                f"error_correction={error_correction}"
            )
            logger.debug(f"  VCard Details: {cfg_vcard_data}")

            generated_qr_path = qr_gen.generate_artistic_vcard_qr(
                vcard_details=cfg_vcard_data,
                output_filename=final_output_filename,
                error_correction=error_correction,
            )
            util_console.print(
                f"[bold green]QR code generated: {generated_qr_path}[/]"
            )
        except FileNotFoundError as fnf_error:
            logger.error(
                f"QR generation error (file not found): {fnf_error}",
                exc_info=True
            )
            util_console.print(
                f"[bold red]File Not Found Error:[/bold red] {fnf_error}"
            )
            raise typer.Exit(code=1)
        except ValueError as val_error:
            logger.error(
                f"QR generation error (value error): {val_error}",
                exc_info=True
            )
            util_console.print(
                f"[bold red]Value Error:[/bold red] {val_error}"
            )
            raise typer.Exit(code=1)
        except Exception as e:
            logger.error(f"QR generation failed: {e}", exc_info=True)
            util_console.print(
                f"[bold red]Error:[/bold red] QR generation failed: {e}"
            )
            raise typer.Exit(code=1)

    elif entity_type == EntityType.WORD_CLOUD:
        try:
            logger.debug("Attempting to import .techs...")
            from .techs import Technology, load_technologies
            logger.debug(".techs imported successfully.")

            logger.debug("Attempting to import .word_clouds...")
            from .word_clouds import (
                DEFAULT_FONT_PATH,  # Default font
                LANGUAGES_MD_PATH,  # Default languages.md
                PROFILE_IMG_OUTPUT_DIR,  # Default output
                TOPICS_MD_PATH,  # Default topics.md path
                WordCloudGenerator,
                WordCloudSettings,
                parse_markdown_for_word_cloud_frequencies,
            )
            logger.debug(".word_clouds imported successfully.")

        except ImportError as e_import:  # Catch the specific error
            logger.error(
                f"Detailed import error: {e_import}", exc_info=True
            )
            logger.error(
                "Word cloud/techs components missing. Install dependencies: "
                "uv pip install readme[word-clouds]"
            )
            util_console.print(
                "[bold red]Error:[/bold red] Word cloud components missing."
            )
            raise typer.Exit(code=1)

        effective_wc_settings_data: Dict[str, Any] = {}
        config_wc_model = (
            proj_config.word_cloud_settings or ConfigWordCloudSettingsModel()
        )
        effective_wc_settings_data.update(
            config_wc_model.model_dump(exclude_unset=True)
        )

        if output_path_cli:
            effective_wc_settings_data["output_dir"] = str(
                output_path_cli.parent
            )
            effective_wc_settings_data["output_filename"] = (
                output_path_cli.name
            )
        
        # Check for special flags first before handling prompts
        if not from_topics_md_cli and not from_languages_md_cli:
            if prompt_cli is not None:
                effective_wc_settings_data["text"] = prompt_cli
                logger.info(f'Using CLI prompt for word cloud: "{prompt_cli}"')
                techs_path_cli = None  # Explicitly nullify if prompt is used
            elif (
                "prompt" in effective_wc_settings_data and
                effective_wc_settings_data["prompt"] is not None
            ):
                effective_wc_settings_data["text"] = (
                    effective_wc_settings_data["prompt"]
                )
                logger.info(
                    "Using config prompt for word cloud: "
                    f'"{effective_wc_settings_data["text"]}"'
                )
                techs_path_cli = None  # Explicitly nullify if prompt is used
        
        stopwords_list: List[str] = []
        if config_wc_model and config_wc_model.stopwords:
            stopwords_list.extend(config_wc_model.stopwords)

        effective_wc_settings_data["stopwords"] = stopwords_list
        
        output_dir_path = Path(
            effective_wc_settings_data.get(
                "output_dir", WordCloudSettings().output_dir
            )
        )
        try:
            output_dir_path.mkdir(parents=True, exist_ok=True)
            effective_wc_settings_data["output_dir"] = output_dir_path
        except Exception as e_mkdir:
            logger.error(
                f"Could not create output dir {output_dir_path}: {e_mkdir}"
            )
            util_console.print(
                "[bold red]Error:[/bold red] Failed to create output dir."
            )
            raise typer.Exit(1)

        if (
            "font_path" in effective_wc_settings_data
            and isinstance(effective_wc_settings_data["font_path"], str)
        ):
            fp = Path(effective_wc_settings_data["font_path"])
            effective_wc_settings_data["font_path"] = (
                fp if fp.exists() else None
            )
        if (
            "mask_path" in effective_wc_settings_data
            and isinstance(effective_wc_settings_data["mask_path"], str)
        ):
            mp = Path(effective_wc_settings_data["mask_path"])
            effective_wc_settings_data["mask_path"] = (
                mp if mp.exists() else None
            )

        try:
            final_wc_script_settings = WordCloudSettings(
                **effective_wc_settings_data
            )
        except Exception as e_val:
            logger.error(
                "Failed to create WordCloudSettings for generator: "
                f"{e_val}",
                exc_info=True,
            )
            util_console.print(
                "[bold red]Error:[/bold red] Invalid word cloud settings for "
                f"generator: {e_val}"
            )
            raise typer.Exit(code=1)

        generator = WordCloudGenerator(base_settings=final_wc_script_settings)
        generated_path: Optional[Path] = None
        frequencies_for_cloud: Optional[Dict[str, float]] = None

        # Handle generation from specific markdown files first
        if from_topics_md_cli:
            logger.info(
                f"Generating word cloud from topics.md: {TOPICS_MD_PATH}"
            )
            if TOPICS_MD_PATH.exists():
                frequencies_for_cloud = \
                    parse_markdown_for_word_cloud_frequencies(
                        TOPICS_MD_PATH
                    )
                if frequencies_for_cloud:
                    num_terms = len(frequencies_for_cloud)
                    logger.info(
                        f"Setting max_words to {num_terms} to include all "
                        f"terms from {TOPICS_MD_PATH.name}."
                    )
                    topic_overrides = {
                        "output_dir": PROFILE_IMG_OUTPUT_DIR,
                        "output_filename": "wordcloud_by_topic.svg",
                        "output_format": "svg",
                        "background_color": "rgba(255, 255, 255, 0)",
                        "colormap": "viridis",
                        "custom_color_func_name": "analogous_color_func",
                        "font_path": (
                            str(DEFAULT_FONT_PATH)
                            if DEFAULT_FONT_PATH and DEFAULT_FONT_PATH.exists()
                            else None
                        ),
                        "width": 1200,
                        "height": 800,
                        "max_words": num_terms,
                        "contour_width": 0.5,
                        "contour_color": "#DDDDDD",
                        "stopwords": [
                            "project", "projects", "list", "awesome", "using",
                            "application", "platform", "other", "others",
                        ] + stopwords_list,  # Combine with global
                    }
                    logger.debug(
                        f"Applying overrides for topics.md: {topic_overrides}"
                    )
                    temp_settings_data = effective_wc_settings_data.copy()
                    temp_settings_data.update(topic_overrides)
                    if output_path_cli:  # Keep CLI output path if specified
                        temp_settings_data["output_dir"] = str(
                            output_path_cli.parent
                        )
                        temp_settings_data["output_filename"] = (
                            output_path_cli.name
                        )

                    final_wc_script_settings_topics = WordCloudSettings(
                        **temp_settings_data
                    )
                    generator_topics = WordCloudGenerator(
                        base_settings=final_wc_script_settings_topics
                    )
                    generated_path = generator_topics.generate(
                        frequencies=frequencies_for_cloud
                    )

                else:
                    logger.warning(
                        f"No frequencies parsed from {TOPICS_MD_PATH.name}, "
                        "skipping topics word cloud generation via CLI."
                    )
            else:
                logger.error(
                    f"Topics Markdown file not found: {TOPICS_MD_PATH}. "
                    "Cannot generate topics word cloud via CLI."
                )

        elif from_languages_md_cli:
            logger.info(
                f"Generating word cloud from languages.md: {LANGUAGES_MD_PATH}"
            )
            if LANGUAGES_MD_PATH.exists():
                frequencies_for_cloud = \
                    parse_markdown_for_word_cloud_frequencies(
                        LANGUAGES_MD_PATH
                    )
                if frequencies_for_cloud:
                    num_terms = len(frequencies_for_cloud)
                    logger.info(
                        f"Setting max_words to {num_terms} to include all "
                        f"terms from {LANGUAGES_MD_PATH.name}."
                    )
                    language_overrides = {
                        "output_dir": PROFILE_IMG_OUTPUT_DIR,
                        "output_filename": "wordcloud_by_language.svg",
                        "output_format": "svg",
                        "background_color": "rgba(255, 255, 255, 0)",
                        "custom_color_func_name": "primary_color_func",
                        "color_palette_override": [
                            "#4B8BBE", "#306998", "#FFE873", "#FFD43B",
                            "#646464", "#F1502F", "#00A0B0",
                        ],
                        "font_path": (
                            str(DEFAULT_FONT_PATH)
                            if DEFAULT_FONT_PATH and DEFAULT_FONT_PATH.exists()
                            else None
                        ),
                        "width": 1200,
                        "height": 800,
                        "max_words": num_terms,
                        "contour_width": 0.5,
                        "contour_color": "#AAAAAA",
                        "stopwords": list(set(
                            [
                                "workflow", "workflows", "action", "actions",
                                "github", "github actions", "template",
                                "templates", "automation", "script", "scripts",
                                "tool", "tools", "utility", "utilities",
                                "helper", "helpers", "language", "languages",
                                "code", "script", "file", "files",
                                "other", "others",
                            ] + stopwords_list,  # Combine with global
                        )),
                    }
                    logger.debug(
                        "Applying overrides for languages.md: "
                        f"{language_overrides}"
                    )
                    temp_settings_data = effective_wc_settings_data.copy()
                    temp_settings_data.update(language_overrides)
                    if output_path_cli:  # Keep CLI output path if specified
                        temp_settings_data["output_dir"] = str(
                            output_path_cli.parent
                        )
                        temp_settings_data["output_filename"] = (
                            output_path_cli.name
                        )

                    final_wc_script_settings_langs = WordCloudSettings(
                        **temp_settings_data
                    )
                    generator_langs = WordCloudGenerator(
                        base_settings=final_wc_script_settings_langs
                    )
                    generated_path = generator_langs.generate(
                        frequencies=frequencies_for_cloud
                    )
                else:
                    logger.warning(
                        f"No frequencies parsed from {LANGUAGES_MD_PATH.name}, "
                        "skipping languages word cloud generation via CLI."
                    )
            else:
                logger.error(
                    f"Languages Markdown file not found: {LANGUAGES_MD_PATH}. "
                    "Cannot generate languages word cloud via CLI."
                )

        # Fallback to techs_path or prompt if not from topics/languages MD
        elif techs_path_cli and techs_path_cli.exists():
            logger.info(
                f"Loading technologies from specified path: {techs_path_cli}"
            )
            loaded_techs_list: List[Technology] = load_technologies(
                techs_path_cli
            )
            if loaded_techs_list:
                frequencies_for_cloud = {
                    tech.name: float(tech.level) for tech in loaded_techs_list
                }
                if not frequencies_for_cloud:
                    logger.warning(
                        f"No frequencies derived from {techs_path_cli}."
                    )
                else:
                    logger.info(
                        f"Derived {len(frequencies_for_cloud)} terms with "
                        f"frequencies from {techs_path_cli}."
                    )
            else:
                logger.warning(
                    "load_technologies returned no data from "
                    f"{techs_path_cli}."
                )
            
            if frequencies_for_cloud:
                logger.info(
                    "Generating word cloud from calculated frequencies."
                )
                generated_path = generator.generate(
                    frequencies=frequencies_for_cloud
                )
            else:
                logger.warning(
                    f"No frequencies from {techs_path_cli}, word cloud from "
                    "this source might be empty."
                )

        elif final_wc_script_settings.text:
            logger.info("Generating word cloud from text (prompt).")
            generated_path = generator.generate(
                text_input=final_wc_script_settings.text
            )
        else:
            logger.error(
                "Word cloud generation skipped: No valid input "
                "(techs_path with data, or text/prompt) was prepared."
            )

        if generated_path and generated_path.exists():
            util_console.print(
                f"[bold green]Word cloud generated: {generated_path}[/]"
            )
        else:
            logger.error(
                "Word cloud generation failed or produced no output file."
            )
            util_console.print(
                "[bold red]Error:[/bold red] Word cloud generation failed."
            )

    elif entity_type == EntityType.GENERATIVE:
        try:
            from .generative import generate_community_art, generate_activity_art
        except ImportError:
            logger.error(
                "Generative art dependencies/script components are missing. "
                "Ensure generative.py is correct."
            )
            util_console.print(
                "[bold red]Error:[/bold red] Generative art components missing."
            )
            raise typer.Exit(code=1)

        metrics_path = metrics_path_cli
        if not metrics_path or not metrics_path.exists():
            logger.error("Metrics JSON required. Use --metrics-path to specify.")
            raise typer.Exit(code=1)

        import json
        metrics = json.loads(metrics_path.read_text())

        output_dir = Path(output_path_cli) if output_path_cli else Path(".github/assets/img")
        output_dir.mkdir(parents=True, exist_ok=True)

        for art_type in ["community", "activity"]:
            for dark in [False, True]:
                suffix = "-dark" if dark else ""
                out = output_dir / f"generative-{art_type}{suffix}.svg"
                if art_type == "community":
                    generate_community_art(metrics, dark_mode=dark, output_path=out)
                else:
                    generate_activity_art(metrics, dark_mode=dark, output_path=out)
                util_console.print(f"[bold green]Generated: {out}[/]")

    elif entity_type == EntityType.ANIMATED:
        try:
            from .animated_art import (
                generate_animated_community_art,
                generate_animated_activity_art,
            )
        except ImportError:
            logger.error(
                "Animated art dependencies/script components are missing. "
                "Ensure animated_art.py is correct."
            )
            util_console.print(
                "[bold red]Error:[/bold red] Animated art components missing."
            )
            raise typer.Exit(code=1)

        if not history_path_cli or not history_path_cli.exists():
            logger.error("History JSON required. Use --history-path to specify.")
            util_console.print(
                "[bold red]Error:[/bold red] --history-path is required for animated art."
            )
            raise typer.Exit(code=1)

        import json

        history = json.loads(history_path_cli.read_text())

        output_dir = Path(output_path_cli) if output_path_cli else Path(".github/assets/img")
        output_dir.mkdir(parents=True, exist_ok=True)

        for art_type in ["community", "activity"]:
            for dark in [False, True]:
                suffix = "-dark" if dark else ""
                out = output_dir / f"animated-{art_type}{suffix}.svg"
                if art_type == "community":
                    generate_animated_community_art(
                        history, dark_mode=dark, output_path=out,
                    )
                else:
                    generate_animated_activity_art(
                        history, dark_mode=dark, output_path=out,
                    )
                util_console.print(f"[bold green]Generated: {out}[/]")

    elif entity_type == EntityType.SKILLS:
        from .config import DEFAULT_SKILLS_PATH, load_skills
        from .skills import SkillsBadgeGenerator

        skills_path = skills_path_cli or DEFAULT_SKILLS_PATH
        try:
            skills_settings = load_skills(skills_path)
        except (FileNotFoundError, ValueError) as e:
            logger.error(f"Failed to load skills config: {e}")
            util_console.print(
                f"[bold red]Error:[/bold red] {e}"
            )
            raise typer.Exit(code=1)

        generator = SkillsBadgeGenerator(settings=skills_settings)
        result_path = generator.generate()
        util_console.print(
            f"[bold green]Skills badges injected into {result_path}[/]"
        )

    elif entity_type == EntityType.README:
        from .config import ReadmeSectionsSettings
        from .readme_sections import ReadmeSectionGenerator

        readme_settings_raw = proj_config.readme_sections_settings
        readme_settings = (
            readme_settings_raw
            if isinstance(readme_settings_raw, ReadmeSectionsSettings)
            else ReadmeSectionsSettings.model_validate(readme_settings_raw or {})
        )
        if output_path_cli:
            readme_settings = readme_settings.model_copy(
                update={"readme_path": str(output_path_cli)}
            )

        card_style_updates: dict[str, dict[str, Any]] = {}

        def _collect_card_style_update(
            family: str,
            variant: Optional[ReadmeCardVariant],
            transparent_canvas: Optional[bool],
            show_title: Optional[bool],
        ) -> None:
            update: dict[str, Any] = {}
            if variant is not None:
                update["variant"] = variant.value
            if transparent_canvas is not None:
                update["transparent_canvas"] = transparent_canvas
            if show_title is not None:
                update["show_title"] = show_title
            if update:
                card_style_updates[family] = update

        _collect_card_style_update(
            "default",
            readme_default_card_variant_cli,
            readme_default_card_transparent_canvas_cli,
            readme_default_card_show_title_cli,
        )
        _collect_card_style_update(
            "connect",
            readme_connect_card_variant_cli,
            readme_connect_card_transparent_canvas_cli,
            readme_connect_card_show_title_cli,
        )
        _collect_card_style_update(
            "featured",
            readme_featured_card_variant_cli,
            readme_featured_card_transparent_canvas_cli,
            readme_featured_card_show_title_cli,
        )
        _collect_card_style_update(
            "blog",
            readme_blog_card_variant_cli,
            readme_blog_card_transparent_canvas_cli,
            readme_blog_card_show_title_cli,
        )

        if card_style_updates:
            current_styles = readme_settings.svg.card_styles
            style_update_payload: dict[str, Any] = {}
            for family, update in card_style_updates.items():
                current_style = getattr(current_styles, family)
                style_update_payload[family] = current_style.model_copy(
                    update=update
                )
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
        util_console.print(
            f"[bold green]README sections updated in {result_path}[/]"
        )
    else:
        logger.error(
            f"Generation for entity type '{entity_type}' is not supported."
        )
        util_console.print(
            f"[bold red]Error:[/bold red] Entity type '{entity_type}' "
            "is not supported."
        )
        raise typer.Exit(code=1)


@app.command(
    help="Display current global application settings from environment/dotenv."
)
def show_settings(
    output_format: Annotated[
        OutputFormat,
        typer.Option(
            case_sensitive=False, help="Format for settings (json/yaml)."
        ),
    ] = OutputFormat.JSON,
) -> None:
    """Displays current application settings after loading from all sources."""
    try:
        current_app_settings = AppSettings()
        _display_config(current_app_settings, output_format)
    except ValidationError as e:
        logger.error(f"Settings validation error: {e}")
        # logger.error(e.errors())
        raise typer.Exit(code=1)
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        logger.exception("Traceback:")
        raise typer.Exit(code=1)


def cli_main() -> None:
    """Main entry point for the CLI application."""
    # Configure logging (can be further enhanced, e.g., with RichHandler)
    logging.basicConfig(
        level=logging.INFO, format="%(levelname)s: %(message)s"
    )
    # Example of adding RichHandler if available and desired:
    # try:
    #     from rich.logging import RichHandler
    #     logging.getLogger().handlers = [RichHandler(rich_tracebacks=True)]
    # except ImportError:
    #     pass # Rich is optional

    app()


if __name__ == "__main__":
    cli_main()
