from enum import Enum
from pathlib import Path
from typing import Annotated, Dict, List, Optional, Union

import typer
from rich.console import Console
from rich.syntax import Syntax

# Core config imports
from .config import DEFAULT_CONFIG_PATH
from .config import BannerSettings as ConfigBannerSettings
from .config import ProjectConfig
from .config import QRCodeSettings as ConfigQRCodeSettings
from .config import Settings as AppSettings
from .config import VCardDataModel
from .config import WordCloudSettingsModel as ConfigWordCloudSettingsModel
from .config import load_config, save_config
from .utils import console as util_console
from .utils import get_logger

logger = get_logger(module=__name__)

app = typer.Typer(
    name="w4w-dev-cli",
    help="CLI for w4w.dev project utilities, generation, and management.",
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


class OutputFormat(str, Enum):
    JSON = "json"
    YAML = "yaml"


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
                f"[bold red]Error:[/bold red] Failed to load configuration: {e}"
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
                f"[bold red]Error:[/bold red] Failed to save configuration: {e}"
            )

    elif action == "generate-default":
        try:
            if effective_path.exists():
                overwrite = typer.confirm(
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
                f"[bold red]Error:[/bold red] Could not gen/save default config: {e}"
            )
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
            f"[bold red]Error:[/bold red] Failed to load configuration: {e}"
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
            banner_data.update(proj_config.banner_settings.model_dump(exclude_unset=True))

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

        if proj_config.qr_code_settings:
            qr_settings_data.update(proj_config.qr_code_settings.model_dump(exclude_unset=True))
        
        cfg_vcard_data = proj_config.v_card_data

        if not cfg_vcard_data:
            logger.error(
                "VCardData (v_card_data) not defined in project config."
            )
            util_console.print(
                "[bold red]Error:[/bold red] VCard details (v_card_data) "
                "missing in project config."
            )
            raise typer.Exit(code=1)

        default_bg_path_str = qr_background_path_cli or qr_settings_data.get("default_background_path") or ".github/assets/img/icon.svg"
        default_output_dir_str = (output_path_cli.parent if output_path_cli 
                                   else qr_settings_data.get("output_dir") or ".github/assets/img")
        
        final_output_filename = (output_path_cli.name if output_path_cli
                                else qr_settings_data.get("output_filename") or "qr_code_vcard.png")

        try:
            qr_gen = QRCodeGenerator(
                default_background_path=Path(default_bg_path_str),
                default_output_dir=Path(default_output_dir_str),
                default_scale=(qr_scale_cli if qr_scale_cli is not None
                               else int(qr_settings_data.get("default_scale", 25))),
            )

            error_correction = (qr_error_correction_cli
                                if qr_error_correction_cli is not None
                                else qr_settings_data.get("error_correction", "H"))
            
            logger.info(
                 f"Generating QR for: {cfg_vcard_data.displayname}, "
                 f"Output: {Path(default_output_dir_str) / final_output_filename}, "
                 f"Background: {default_bg_path_str}"
            )

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
            util_console.print(f"[bold red]Value Error:[/bold red] {val_error}")
            raise typer.Exit(code=1)
        except Exception as e:
            logger.error(f"QR generation failed: {e}", exc_info=True)
            util_console.print(
                f"[bold red]Error:[/bold red] QR generation failed: {e}"
            )
            raise typer.Exit(code=1)

    elif entity_type == EntityType.WORD_CLOUD:
        try:
            from .techs import Technology, load_technologies
            from .word_clouds import WordCloudGenerator, WordCloudSettings
        except ImportError:
            logger.error(
                "Word cloud/techs components missing. Install dependencies: "
                "uv pip install wyattowalsh[word-clouds]"
            )
            util_console.print(
                "[bold red]Error:[/bold red] Word cloud components missing."
            )
            raise typer.Exit(code=1)

        effective_wc_settings_data: Dict[str, Any] = {}
        config_wc_model = proj_config.word_cloud_settings or ConfigWordCloudSettingsModel()
        effective_wc_settings_data.update(config_wc_model.model_dump(exclude_unset=True))

        if output_path_cli:
            effective_wc_settings_data["output_dir"] = str(output_path_cli.parent)
            effective_wc_settings_data["output_filename"] = output_path_cli.name
        if prompt_cli is not None:
            effective_wc_settings_data["text"] = prompt_cli
            logger.info(f"Using CLI prompt for word cloud: \"{prompt_cli}\"")
            techs_path_cli = None
        elif "prompt" in effective_wc_settings_data and effective_wc_settings_data["prompt"] is not None:
            effective_wc_settings_data["text"] = effective_wc_settings_data["prompt"]
            logger.info(f"Using config prompt for word cloud: \"{effective_wc_settings_data['text']}\"")
            techs_path_cli = None
        
        stopwords_list: List[str] = []
        if config_wc_model and config_wc_model.stopwords:
            stopwords_list.extend(config_wc_model.stopwords)

        effective_wc_settings_data["stopwords"] = stopwords_list
        
        output_dir_path = Path(effective_wc_settings_data.get("output_dir", WordCloudSettings().output_dir))
        try:
            output_dir_path.mkdir(parents=True, exist_ok=True)
            effective_wc_settings_data["output_dir"] = output_dir_path
        except Exception as e_mkdir:
            logger.error(f"Could not create output directory {output_dir_path}: {e_mkdir}")
            util_console.print(f"[bold red]Error:[/bold red] Failed to create output directory.")
            raise typer.Exit(1)

        if "font_path" in effective_wc_settings_data and isinstance(effective_wc_settings_data["font_path"], str):
            fp = Path(effective_wc_settings_data["font_path"])
            effective_wc_settings_data["font_path"] = fp if fp.exists() else None
        if "mask_path" in effective_wc_settings_data and isinstance(effective_wc_settings_data["mask_path"], str):
            mp = Path(effective_wc_settings_data["mask_path"])
            effective_wc_settings_data["mask_path"] = mp if mp.exists() else None

        try:
            final_wc_script_settings = WordCloudSettings(**effective_wc_settings_data)
        except Exception as e_val:
            logger.error(
                "Failed to create WordCloudSettings for generator: "
                f"{e_val}",
                exc_info=True,
            )
            util_console.print(
                f"[bold red]Error:[/bold red] Invalid word cloud settings for generator: {e_val}"
            )
            raise typer.Exit(code=1)

        generator = WordCloudGenerator(base_settings=final_wc_script_settings)
        generated_path: Optional[Path] = None
        frequencies_for_cloud: Optional[Dict[str, float]] = None

        if techs_path_cli and techs_path_cli.exists():
            logger.info(
                f"Loading technologies from specified path: {techs_path_cli}"
            )
            loaded_techs_list: List[Technology] = load_technologies(techs_path_cli)
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
                    f"load_technologies returned no data from {techs_path_cli}."
                )
            
            if frequencies_for_cloud:
                logger.info("Generating word cloud from calculated frequencies.")
                generated_path = generator.generate(frequencies=frequencies_for_cloud)
            else:
                logger.warning(f"No frequencies from {techs_path_cli}, word cloud from this source might be empty.")

        elif final_wc_script_settings.text:
            logger.info("Generating word cloud from text (prompt).")
            generated_path = generator.generate(text_input=final_wc_script_settings.text)
        else:
            logger.error(
                "Word cloud generation skipped: No valid input "
                "(techs_path with data, or text/prompt) was prepared."
            )

        if generated_path and generated_path.exists():
            util_console.print(f"[bold green]Word cloud generated: {generated_path}[/]")
        else:
            logger.error(
                "Word cloud generation failed or produced no output file."
            )
            util_console.print(
                "[bold red]Error:[/bold red] Word cloud generation failed."
            )

    elif entity_type == EntityType.README:
        logger.info("README generation requested (Not implemented yet).")
        util_console.print(
            "[yellow]README generation is not yet implemented in this CLI.[/yellow]"
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
    try:
        app_settings_instance = AppSettings()
        util_console.print(
            "[bold blue]Current Application Settings "
            "(from env/.env or defaults):[/bold blue]"
        )
        _display_config(app_settings_instance, output_format)
    except Exception as e:
        logger.error(
            f"Failed to load or display application settings: {e}",
            exc_info=True
        )
        util_console.print(
            "[bold red]Error:[/bold red] Could not load or display "
            f"application settings: {e}"
        )


if __name__ == "__main__":
    logger.info("CLI application initiated directly by script execution.")
    app()
