"""
utils.py
~~~~~~~~~~
General utility functions, including Colourised console logs (Rich)
+ rotating text & JSON log files (Loguru).
Provides helper `get_logger(**extra)` and `create_progress()` utilities.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from loguru import logger
from rich.console import Console
from rich.logging import RichHandler
from rich.progress import BarColumn, Progress, TextColumn, TimeRemainingColumn

# Attempt to import settings, gracefully handle if not found
try:
    from .config import Settings as AppSettings

    # Explicitly provide default values during instantiation if linter requires
    # or ensure defaults in Settings model are sufficient for pydantic-settings
    app_settings: Optional[AppSettings] = AppSettings(
        log_level="INFO",  # Default from Settings model
        debug_mode=False,  # Default from Settings model
    )
except ImportError:
    app_settings = None
    logger.warning(
        "`scripts.config.Settings` not found or failed to import. "
        "Logging to files might be disabled or use defaults."
    )

# 1. Prepare console + remove default Loguru sink
console = Console()
logger.remove()  # drop Loguru's default stderr sink

# 2. Console sink with Rich prettiness
LOG_LEVEL = "INFO"
if app_settings and hasattr(app_settings, "log_level"):
    LOG_LEVEL = app_settings.log_level

logger.add(
    RichHandler(
        console=console,
        markup=True,
        rich_tracebacks=True,
        show_path=False,
    ),
    level=LOG_LEVEL,
    format=(
        "[{time:YYYY-MM-DD HH:mm:ss.SSS}] | " "{level.icon} {level:<8} | {message}"
    ),
    enqueue=True,
)

# 3. Rotating text & JSON sinks
if app_settings and hasattr(app_settings, "log_level"):
    log_text_dir = getattr(app_settings, "log_text_dir", Path("logs/text"))
    log_json_dir = getattr(app_settings, "log_json_dir", Path("logs/json"))
    log_rotation = getattr(app_settings, "log_rotation", "10 MB")
    log_retention = getattr(app_settings, "log_retention", "10 days")
    log_compression = getattr(app_settings, "log_compression", "zip")

    log_text_dir.mkdir(parents=True, exist_ok=True)
    log_json_dir.mkdir(parents=True, exist_ok=True)

    text_log_format = (
        "{time:YYYY-MM-DD HH:mm:ss.SSS}|{level}|{name}:{function}:{line}|"
        "{extra}|{message}"
    )

    logger.add(
        sink=log_text_dir / "{time:YYYY-MM-DD}.log",
        rotation=log_rotation,
        retention=log_retention,
        compression=log_compression,
        level=LOG_LEVEL,
        format=text_log_format,
        enqueue=True,
    )

    logger.add(
        sink=log_json_dir / "{time:YYYY-MM-DD}.json",
        rotation=log_rotation,
        retention=log_retention,
        compression=log_compression,
        serialize=True,
        level=LOG_LEVEL,
        enqueue=True,
    )
else:
    logger.info(
        "File logging (text/JSON) is disabled because "
        "`scripts.config.Settings` was not found, failed to import, "
        "or lacks `log_level`."
    )


# 4. Helpers
def get_logger(**extra: Any):
    """
    Return a contextualised logger:
        `log = get_logger(service='worker', request_id=uuid4())`
    Extra fields are visible in *all* sinks via `{extra}`.
    """
    return logger.bind(**extra)


def create_progress(description: str = "Working…") -> Progress:
    """
    Rich Progress factory with sensible columns. Usage:

    ```python
    with create_progress("Your task") as progress:
        task_id = progress.add_task("step-1", total=100)
        # ...
    ```
    """
    return Progress(
        TextColumn("[bold blue]{task.description}"),
        BarColumn(bar_width=None),
        "[progress.percentage]{task.percentage:>3.0f}%",
        TimeRemainingColumn(),
        console=console,
        transient=True,
    )


# 5. Example usage when executed directly
if __name__ == "__main__":  # pragma: no cover
    log = get_logger(module="__main__")
    log.info(
        "Console logging ready. File logging status determined by "
        "AppSettings availability."
    )
    if app_settings:
        with create_progress("Demo") as progress:
            task = progress.add_task("demo-task", total=5)
            for _ in range(5):
                progress.advance(task)
                log.debug("Tick…")
    else:
        log.warning("Skipping progress bar demo as AppSettings are not available.")

def get_project_root() -> Path:
    """Returns the project root directory."""
    # Assuming utils.py is in a 'scripts' subdirectory of the project root
    return Path(__file__).resolve().parent.parent
