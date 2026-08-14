"""Shared pytest fixtures."""

import pytest
from loguru import logger
from syrupy.extensions.image import SVGImageSnapshotExtension

_FULL_SUITE_ARGS = {"", "tests", "tests/", ".", "scripts"}


@pytest.hookimpl(trylast=True)
def pytest_configure(config: pytest.Config) -> None:
    """Keep the 95% floor for full-suite runs; skip it on focused file lists.

    Global idle-gate hooks invoke ``pytest path/to/test_*.py`` and inherit
    ``--cov-fail-under=95.0``. A subset cannot cover ``scripts/``. Authoritative
    ``uv run pytest`` / ``readme dev test`` still fail under 95.
    """
    invoked = [str(arg).strip() for arg in (config.args or ())]
    focused = bool(invoked) and not any(
        arg in _FULL_SUITE_ARGS or arg.rstrip("/") == "tests" for arg in invoked
    )
    if not focused:
        return
    # pytest-cov treats 0 as "do not fail"; None is refilled from coveragerc.
    config.option.cov_fail_under = 0
    plugin = config.pluginmanager.get_plugin("_cov")
    if plugin is not None and getattr(plugin, "options", None) is not None:
        plugin.options.cov_fail_under = 0


@pytest.fixture
def captured_warnings():
    """Capture loguru WARNING+ messages during a test."""
    messages = []
    sink_id = logger.add(
        lambda msg: messages.append(msg.record["message"]),
        level="WARNING",
    )
    yield messages
    logger.remove(sink_id)


@pytest.fixture
def snapshot_svg(snapshot):
    """SVG-friendly syrupy assertion (one ``.svg`` file per snapshot)."""
    return snapshot.with_defaults(extension_class=SVGImageSnapshotExtension)
