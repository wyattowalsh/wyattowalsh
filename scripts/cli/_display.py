"""Shared display helpers for config and settings output."""

from __future__ import annotations

from enum import Enum

from ..config import ProjectConfig
from ..config import Settings as AppSettings
from ..utils import console, get_logger

logger = get_logger(module=__name__)

try:
    import yaml  # type: ignore
except ImportError:
    yaml = None  # type: ignore


class OutputFormat(str, Enum):
    JSON = "json"
    YAML = "yaml"


def display_config(
    config_data: ProjectConfig | AppSettings,
    output_format: OutputFormat = OutputFormat.JSON,
) -> None:
    """Pretty-print a config/settings object to the console."""
    from rich.syntax import Syntax  # lazy import

    if output_format == OutputFormat.JSON:
        config_str = config_data.model_dump_json(indent=2)
        syntax = Syntax(config_str, "json", theme="monokai", line_numbers=True)
        console.print(syntax)
    elif output_format == OutputFormat.YAML:
        if yaml is None:
            logger.error(
                "PyYAML is not installed. Cannot display config as YAML. "
                "Falling back to JSON. Install with: uv add PyYAML"
            )
            console.print("PyYAML is not installed. Falling back to JSON.")
            display_config(config_data, OutputFormat.JSON)
        else:
            try:
                config_dict = config_data.model_dump(mode="python")
                yaml_str = yaml.dump(config_dict, indent=2, sort_keys=False)
                syntax = Syntax(
                    yaml_str, "yaml", theme="monokai", line_numbers=True
                )
                console.print(syntax)
            except Exception as e:
                logger.error("Error converting config to YAML: {e}", e=e)
                display_config(config_data, OutputFormat.JSON)
