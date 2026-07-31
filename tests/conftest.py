"""Shared pytest fixtures."""

import pytest
from loguru import logger
from syrupy.extensions.image import SVGImageSnapshotExtension


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
