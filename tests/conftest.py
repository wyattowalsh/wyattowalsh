"""Shared pytest fixtures."""

import pytest
from loguru import logger


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
