import importlib
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock, call

import loguru
import pytest
from loguru._logger import Logger as LoguruLoggerType
from pytest_mock import MockerFixture
from rich.console import Console
from rich.logging import RichHandler
from rich.progress import BarColumn, Progress, TextColumn, TimeRemainingColumn

# Module to be tested
# We will reload it in specific tests to apply mocks at import time
utils_module: ModuleType | None
try:
    import scripts.utils as utils_module_imported

    utils_module = utils_module_imported
except ImportError as e:
    # This can happen if tests are not run from the project root
    # or if PYTHONPATH is not set up correctly.
    # For now, we'll let it slide and expect test functions to handle
    # module loading.
    utils_module = None
    print(
        f"Initial import of scripts.utils failed: {e}. "
        "Will attempt re-import in tests."
    )


@pytest.fixture(autouse=True)
def reset_loguru_handlers():
    """Ensure a clean state for Loguru handlers before each test."""
    if utils_module:
        utils_module.logger.remove()
    yield
    if utils_module:
        utils_module.logger.remove()


@pytest.fixture
def mock_settings(mocker: MockerFixture):
    """Fixture to mock the settings object."""
    return SimpleNamespace(
        log_level="DEBUG",
        log_text_dir=Path("logs/test_text_logs"),
        log_json_dir=Path("logs/test_json_logs"),
        log_rotation="1 day",
        log_retention="7 days",
        log_compression="zip",
    )


@pytest.fixture
def mock_rich_console_instance(mocker: MockerFixture):
    """Fixture to mock the Rich Console *instance* used by utils."""
    mock_console = mocker.MagicMock(spec=Console)
    mock_console.get_time = mocker.MagicMock(return_value=0.0)
    mock_console.is_jupyter = False
    mock_console.is_interactive = True  # For Progress bar exit
    mocker.patch("rich.console.Console", return_value=mock_console)
    return mock_console


@pytest.fixture
def mock_logger_add(mocker: MockerFixture):
    """Fixture to mock logger.add."""
    if utils_module:
        return mocker.spy(utils_module.logger, "add")
    return None


@pytest.fixture
def mock_logger_remove(mocker: MockerFixture):
    """Fixture to mock logger.remove."""
    if utils_module:
        return mocker.spy(utils_module.logger, "remove")
    return None


@pytest.fixture
def mock_path_mkdir(mocker: MockerFixture):
    """Fixture to mock Path.mkdir."""
    return mocker.patch("pathlib.Path.mkdir", autospec=True)


def reload_utils_module(
    mocker: MockerFixture, mock_settings_val=None, fail_config_import=False
):
    """
    Helper function to reload the utils module.
    This is crucial for testing import-time logic.
    The mock_rich_console_instance fixture should be active if console mocking
    is needed during utils module's import/reload, as it patches
    rich.console.Console globally.
    """
    global utils_module

    # Ensure Loguru's logger is reset for each reload to test initial setup
    # This needs to happen *before* the import/reload of utils_module
    if "loguru" in sys.modules:
        # We need to get a fresh logger instance or mock its methods
        # if we want to track calls across reloads properly.
        # For simplicity, if we spy on LoguruLoggerType.remove, it should
        # catch the call within utils.py
        pass

    if fail_config_import:
        mocker.patch.dict(sys.modules, {"config": None})
    elif (
        "config" in sys.modules
        and sys.modules["config"] is None
        and not fail_config_import
    ):
        if "config" in sys.modules:
            del sys.modules["config"]

    if mock_settings_val is not None:
        mock_config_module = MagicMock()
        mock_config_module.settings = mock_settings_val
        mocker.patch.dict(sys.modules, {"config": mock_config_module})

    if "scripts.utils" in sys.modules:
        importlib.reload(sys.modules["scripts.utils"])
        utils_module = sys.modules["scripts.utils"]
    else:
        utils_module = importlib.import_module("scripts.utils")

    return utils_module


def _get_sink_from_add_call(call_obj):
    for arg in call_obj.args:
        if not isinstance(arg, LoguruLoggerType):
            return arg
    return call_obj.kwargs.get("sink")


# --- Test Functions ---


def test_get_logger_returns_logger_instance(mocker: MockerFixture):
    """Test that get_logger returns a Loguru Logger instance."""
    current_utils = reload_utils_module(mocker)
    logger_instance = current_utils.get_logger()
    assert isinstance(
        logger_instance, LoguruLoggerType
    ), "get_logger should return a Logger instance"


def test_get_logger_binds_extra_kwargs(mocker: MockerFixture):
    """Test that get_logger binds extra keyword arguments."""
    current_utils = reload_utils_module(mocker)
    captured_records = []

    def capturing_sink(message):
        captured_records.append(message.record)

    # current_utils.logger points to loguru.logger after reload
    # So we clear handlers from the global loguru.logger
    loguru.logger.remove()
    handler_id = loguru.logger.add(capturing_sink, format="{extra}")
    bound_logger = current_utils.get_logger(service="test_service", request_id="12345")
    bound_logger.info("Test message with bound args")
    loguru.logger.remove(handler_id)

    assert len(captured_records) == 1, "A single message should have been logged"
    record = captured_records[0]
    assert "extra" in record, "Record should have an 'extra' field"
    assert record["extra"].get("service") == "test_service", "Service should be bound"
    assert record["extra"].get("request_id") == "12345", "Request ID should be bound"


def test_initial_logger_remove_call(mocker: MockerFixture):
    """Test that logger.remove() is called when utils is imported."""
    # Spy on the remove method of the actual loguru.logger instance
    mock_loguru_remove = mocker.spy(loguru.logger, "remove")
    reload_utils_module(mocker)
    # The first call to remove() in utils.py is `logger.remove()`
    # to drop Loguru's default stderr sink.
    mock_loguru_remove.assert_any_call()
    # Ensure it's called at least once for the initial setup.
    # Depending on subsequent setups in tests, it might be called more.
    assert mock_loguru_remove.call_count >= 1


def test_utils_console_instance(mocker: MockerFixture, mock_rich_console_instance):
    """Test that utils.py's global `console` is the mocked one."""
    current_utils = reload_utils_module(mocker)
    assert (
        current_utils.console is mock_rich_console_instance
    ), "The global `console` in utils.py was not the mocked instance."


def test_create_progress_returns_progress_instance(
    mocker: MockerFixture, mock_rich_console_instance
):
    """Test create_progress returns Progress instance using mocked console."""
    current_utils = reload_utils_module(mocker)
    progress_instance = current_utils.create_progress()
    assert isinstance(
        progress_instance, Progress
    ), "create_progress should return a Progress instance"
    assert (
        progress_instance.console is mock_rich_console_instance
    ), "Progress instance not created with the mocked console instance."


def test_create_progress_task_description_handling(
    mocker: MockerFixture, mock_rich_console_instance
):
    """Test how task descriptions are handled with create_progress."""
    current_utils = reload_utils_module(mocker)
    progress_instance = current_utils.create_progress(
        description="ThisDescriptionIsForTextColumnFormat"
    )

    with progress_instance:
        task_desc_1 = "My Specific Task 1"
        task_id_1 = progress_instance.add_task(task_desc_1, total=1)
        assert progress_instance.tasks[task_id_1].description == task_desc_1

        task_desc_2 = "Another Task Here"
        task_id_2 = progress_instance.add_task(task_desc_2, total=1)
        assert progress_instance.tasks[task_id_2].description == task_desc_2

    first_text_column = None
    for col in progress_instance.columns:
        if isinstance(col, TextColumn) and "{task.description}" in col.text_format:
            first_text_column = col
            break
    assert first_text_column is not None, "TextColumn for task.description not found"
    assert first_text_column.text_format == "[bold blue]{task.description}"


def test_create_progress_column_types(
    mocker: MockerFixture, mock_rich_console_instance
):
    """Test create_progress sets up correct column types and formats."""
    current_utils = reload_utils_module(mocker)
    progress_instance = current_utils.create_progress()

    actual_columns = progress_instance.columns
    assert (
        len(actual_columns) == 4
    ), f"Expected 4 progress columns, got {len(actual_columns)}"

    assert isinstance(
        actual_columns[0], TextColumn
    ), "First column should be TextColumn"
    assert (
        actual_columns[0].text_format == "[bold blue]{task.description}"
    ), "Incorrect format for task description column"

    assert isinstance(actual_columns[1], BarColumn), "Second column should be BarColumn"

    assert isinstance(
        actual_columns[2], str
    ), "Third column (percentage) should be a string format"
    expected_perc_fmt = "[progress.percentage]{task.percentage:>3.0f}%"
    assert (
        actual_columns[2] == expected_perc_fmt
    ), "Incorrect format for percentage column"

    assert isinstance(
        actual_columns[3], TimeRemainingColumn
    ), "Fourth column should be TimeRemainingColumn"


def test_rich_handler_instantiation_parameters(
    mocker: MockerFixture, mock_settings, mock_rich_console_instance
):
    """Test that RichHandler is instantiated with correct parameters."""
    # We need to mock RichHandler *before* utils.py is imported the first time
    # or reloaded, so we can inspect how it's called.
    mock_rich_handler_constructor = mocker.patch(
        "rich.logging.RichHandler", return_value=mocker.MagicMock(spec=RichHandler)
    )

    reload_utils_module(mocker, mock_settings_val=mock_settings)

    # Check that RichHandler was called with the expected arguments
    # from scripts/utils.py lines 30-35
    mock_rich_handler_constructor.assert_called_once_with(
        console=mock_rich_console_instance,
        markup=True,
        rich_tracebacks=True,
        show_path=False,
    )


def test_logging_setup_with_settings(
    mocker: MockerFixture, mock_settings, mock_path_mkdir, mock_rich_console_instance
):
    """Test logging setup when config.settings is available."""
    mocker.patch("loguru.logger.remove")
    mock_add_global = mocker.spy(loguru.logger, "add")
    mock_warning_global = mocker.spy(loguru.logger, "warning")
    mock_info_global = mocker.spy(loguru.logger, "info")

    reload_utils_module(mocker, mock_settings_val=mock_settings)

    expected_mkdir_calls = [
        call(mock_settings.log_text_dir, parents=True, exist_ok=True),
        call(mock_settings.log_json_dir, parents=True, exist_ok=True),
    ]
    mock_path_mkdir.assert_has_calls(expected_mkdir_calls, any_order=True)
    assert mock_path_mkdir.call_count == 2

    assert (
        mock_add_global.call_count == 3
    ), f"Expected 3 calls to logger.add, got {mock_add_global.call_count}"

    rich_handler_call = None
    text_log_call_found = None
    json_log_call_found = None

    for call_obj in mock_add_global.mock_calls:
        # The sink may be passed positionally or via kwargs depending on how
        # logger.add is spied on, so normalize it before assertions.
        sink = _get_sink_from_add_call(call_obj)
        if sink is None:
            continue  # Should not happen with standard Loguru usage

        if isinstance(sink, RichHandler):
            rich_handler_call = call_obj
        elif isinstance(sink, Path) and sink.name.endswith(".log"):
            text_log_call_found = call_obj
        elif isinstance(sink, Path) and sink.name.endswith(".json"):
            json_log_call_found = call_obj

    assert rich_handler_call is not None, "RichHandler not added to logger"
    assert text_log_call_found is not None, "Text log sink not found"
    assert json_log_call_found is not None, "JSON log sink not found"

    actual_rich_handler_instance = _get_sink_from_add_call(rich_handler_call)
    assert (
        actual_rich_handler_instance.console is mock_rich_console_instance
    ), "RichHandler console mismatch"
    assert rich_handler_call.kwargs["level"] == mock_settings.log_level
    expected_rich_format = (
        "[{time:YYYY-MM-DD HH:mm:ss.SSS}] | " "{level.icon} {level:<8} | {message}"
    )
    assert rich_handler_call.kwargs["format"] == expected_rich_format
    assert rich_handler_call.kwargs["enqueue"] is True

    expected_text_log_path = (
        mock_settings.log_text_dir / "{time:YYYY-MM-DD}.log"
    )
    assert _get_sink_from_add_call(text_log_call_found) == expected_text_log_path
    assert text_log_call_found.kwargs["rotation"] == mock_settings.log_rotation
    assert text_log_call_found.kwargs["retention"] == mock_settings.log_retention
    assert text_log_call_found.kwargs["compression"] == mock_settings.log_compression
    assert text_log_call_found.kwargs["level"] == mock_settings.log_level
    expected_text_format = (
        "{time:YYYY-MM-DD HH:mm:ss.SSS}|{level}|"
        "{name}:{function}:{line}|{extra}|{message}"
    )
    assert expected_text_format in text_log_call_found.kwargs["format"]
    assert text_log_call_found.kwargs["enqueue"] is True

    expected_json_log_path = (
        mock_settings.log_json_dir / "{time:YYYY-MM-DD}.json"
    )
    assert _get_sink_from_add_call(json_log_call_found) == expected_json_log_path
    assert json_log_call_found.kwargs["rotation"] == mock_settings.log_rotation
    assert json_log_call_found.kwargs["retention"] == mock_settings.log_retention
    assert json_log_call_found.kwargs["compression"] == mock_settings.log_compression
    assert json_log_call_found.kwargs["serialize"] is True
    assert json_log_call_found.kwargs["level"] == mock_settings.log_level
    assert json_log_call_found.kwargs["enqueue"] is True

    mock_warning_global.assert_not_called()
    for call_obj in mock_info_global.mock_calls:
        assert "File logging is disabled" not in call_obj.args[0]


def test_logging_setup_no_settings_or_import_error(
    mocker: MockerFixture, mock_path_mkdir, mock_rich_console_instance
):
    """
    Test logging when config import fails or settings is None.
    Covers `except ImportError` and `settings = None` paths in utils.py.
    """
    mocker.patch("loguru.logger.remove")
    captured_messages = []
    capture_sink_id = loguru.logger.add(
        lambda message: captured_messages.append(message.record["message"]),
        format="{message}",
    )
    mock_add_global = mocker.spy(loguru.logger, "add")

    # Scenario 1: ImportError when importing config
    mock_add_global.reset_mock()
    captured_messages.clear()

    reload_utils_module(mocker, fail_config_import=True)

    mock_path_mkdir.assert_not_called()
    assert (
        mock_add_global.call_count == 1
    ), "Expected 1 logger.add call for RichHandler (ImportError)"

    rich_handler_call_ie = mock_add_global.mock_calls[0]
    actual_rich_handler_instance_ie = _get_sink_from_add_call(rich_handler_call_ie)
    assert isinstance(actual_rich_handler_instance_ie, RichHandler)
    assert actual_rich_handler_instance_ie.console is (
        mock_rich_console_instance
    ), "RichHandler (ImportError) not using mocked console"
    assert (
        rich_handler_call_ie.kwargs["level"] == "INFO"
    ), "Default log level (ImportError) incorrect"

    assert any(
        "`config` module not found" in message for message in captured_messages
    ), "Warning for 'config module not found' not logged (ImportError)"

    # Scenario 2: config imports, but settings is None
    mock_add_global.reset_mock()
    mock_path_mkdir.reset_mock()
    captured_messages.clear()

    mock_config_module_with_none_settings = MagicMock()
    mock_config_module_with_none_settings.settings = None

    # Patch sys.modules directly before reloading utils
    mocker.patch.dict(sys.modules, {"config": mock_config_module_with_none_settings})
    if "scripts.utils" in sys.modules:
        del sys.modules["scripts.utils"]  # Ensure it re-imports
    # Reload utils module; it will pick up the mocked config with settings=None
    reload_utils_module(mocker)

    mock_path_mkdir.assert_not_called()
    assert (
        mock_add_global.call_count == 1
    ), "Expected 1 logger.add call for RichHandler (settings None)"
    rich_handler_call_sn = mock_add_global.mock_calls[0]
    actual_rich_handler_instance_sn = _get_sink_from_add_call(rich_handler_call_sn)
    assert isinstance(actual_rich_handler_instance_sn, RichHandler)
    assert actual_rich_handler_instance_sn.console is (
        mock_rich_console_instance
    ), "RichHandler (settings None) not using mocked console"
    assert (
        rich_handler_call_sn.kwargs["level"] == "INFO"
    ), "Default log level (settings None) incorrect"

    assert not any(
        "`config` module not found" in message for message in captured_messages
    ), "Warning 'config module not found' logged unexpectedly (settings None)"

    LoguruLoggerType.remove(loguru.logger, capture_sink_id)
