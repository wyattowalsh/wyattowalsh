"""
utils.py
~~~~~~~~~~
General utility functions, including Colourised console logs (Rich)
+ rotating text & JSON log files (Loguru).
Provides helper `get_logger(**extra)` and `create_progress()` utilities.
"""

from __future__ import annotations

import sys  # noqa: F401 -- ensures `sys` is available for `logger.add(..., format=...)`
from pathlib import Path
from typing import Any

# Prefer optional imports for loguru/rich so tests can run in minimal env
try:
    from loguru import logger as loguru_logger
    from loguru._logger import Logger as LoguruLoggerType
except Exception:  # pragma: no cover - fallback for test environments
    class _FallbackLogger:
        def bind(self, **extra):
            return self

        def info(self, *a, **k):
            print("INFO:", *a)

        def warning(self, *a, **k):
            print("WARN:", *a)

        def debug(self, *a, **k):
            print("DEBUG:", *a)

        def add(self, *a, **k):
            return None

        def remove(self, *a, **k):
            return None

        def __getattr__(self, name):
            # return a no-op callable for any logging method used
            def _noop(*a, **k):
                return None

            return _noop

    loguru_logger = _FallbackLogger()
    LoguruLoggerType = _FallbackLogger  # type: ignore

try:
    from rich.console import Console
    from rich.logging import RichHandler
    from rich.progress import BarColumn, Progress, TextColumn, TimeRemainingColumn
except Exception:  # pragma: no cover - fallback minimal console/progress
    class Console:  # very small fallback
        def __init__(self, *a, **k):
            pass

    class RichHandler:
        def __init__(self, *a, **k):
            pass

    class BarColumn:
        pass

    class Progress:
        def __init__(self, *a, **k):
            pass

    class TextColumn:
        def __init__(self, *a, **k):
            pass

    class TimeRemainingColumn:
        pass

def _load_app_settings() -> Any | None:
    """Load logging settings without importing scripts.config during bootstrap.

    This avoids the circular import where scripts.config imports get_logger from
    this module while this module tries to import Settings from scripts.config.
    Tests may still inject a top-level `config` module with a `settings` object,
    so that compatibility path is preserved.
    """

    config_module = sys.modules.get("config")
    if config_module is not None:
        return getattr(config_module, "settings", None)

    return None


app_settings = _load_app_settings()

# 1. Prepare console + remove default Loguru sink
console = Console()
loguru_logger.remove()  # drop Loguru's default stderr sink, use imported logger

# 2. Console sink with Rich prettiness
LOG_LEVEL_STR = "INFO"  # Changed variable name to avoid conflict
if app_settings and hasattr(app_settings, "log_level"):
    # Ensure log_level attribute is correctly accessed and is a string
    level_from_settings = getattr(app_settings, "log_level", "INFO")
    if isinstance(level_from_settings, str):
        LOG_LEVEL_STR = level_from_settings
    else:
        loguru_logger.warning(
            f"Invalid log_level type in settings: {type(level_from_settings)}. "
            "Defaulting to INFO."
        )
        LOG_LEVEL_STR = "INFO"


loguru_logger.add(  # Use the imported loguru_logger
    RichHandler(
        console=console,
        markup=True,
        rich_tracebacks=True,
        show_path=False,  # Default: False, set True to show module path
    ),
    level=LOG_LEVEL_STR,
    format=(
        "[{time:YYYY-MM-DD HH:mm:ss.SSS}] | "
        "{level.icon} {level:<8} | {message}"
    ),
    enqueue=True,  # For thread-safe logging
)

# 3. Rotating text & JSON sinks
if app_settings and hasattr(app_settings, "log_level"):
    # Use getattr for safer access to potentially missing attributes
    log_text_dir = getattr(app_settings, "log_text_dir", Path("logs/text"))
    log_json_dir = getattr(app_settings, "log_json_dir", Path("logs/json"))
    log_rotation = getattr(app_settings, "log_rotation", "10 MB")
    log_retention = getattr(app_settings, "log_retention", "10 days")
    log_compression = getattr(app_settings, "log_compression", "zip")

    # Ensure directories exist
    if isinstance(log_text_dir, Path):
        log_text_dir.mkdir(parents=True, exist_ok=True)
    if isinstance(log_json_dir, Path):
        log_json_dir.mkdir(parents=True, exist_ok=True)

    text_log_format = (
        "{time:YYYY-MM-DD HH:mm:ss.SSS}|{level}|{name}:{function}:{line}|"
        "{extra}|{message}"
    )

    loguru_logger.add(  # Use the imported loguru_logger
        sink=log_text_dir / "{time:YYYY-MM-DD}.log",
        rotation=log_rotation,
        retention=log_retention,
        compression=log_compression,
        level=LOG_LEVEL_STR,
        format=text_log_format,
        enqueue=True,
    )

    loguru_logger.add(  # Use the imported loguru_logger
        sink=log_json_dir / "{time:YYYY-MM-DD}.json",
        rotation=log_rotation,
        retention=log_retention,
        compression=log_compression,
        serialize=True,  # Enable JSON structuring
        level=LOG_LEVEL_STR,
        enqueue=True,
    )
else:
    loguru_logger.info(  # Use the imported loguru_logger
        "File logging (text/JSON) is disabled because "
        "settings are unavailable or lack `log_level`."
    )


logger = loguru_logger


# 4. Helpers
def get_logger(**extra: Any) -> LoguruLoggerType:  # Use the correct type
    """
    Return a contextualised logger:
        `log = get_logger(service='worker', request_id=uuid4())`
    Extra fields are visible in *all* sinks via `{extra}`.
    """
    return loguru_logger.bind(**extra)  # Use the imported loguru_logger


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
        transient=True,  # Progress bar disappears after completion
    )


# 5. Example usage when executed directly
if __name__ == "__main__":  # pragma: no cover
    # Get a logger instance specifically for this example context
    log = get_logger(module="__main__")  # This now uses the corrected get_logger
    log.info(
        "Console logging ready. File logging status determined by "
        "AppSettings availability."
    )
    if app_settings:
        with create_progress("Demo") as progress:
            task_id = progress.add_task("demo-task", total=5)
            for _i in range(5):  # Use _i to denote unused loop variable
                progress.advance(task_id)
                log.debug("Tick…")  # Example debug message
    else:
        log.warning(
            "Skipping progress bar demo as AppSettings are not available."
        )
