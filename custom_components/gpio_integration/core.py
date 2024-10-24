"""Constants for the integration."""

from __future__ import annotations

import logging
import time

DOMAIN = "gpio_integration"

__LOGGER = logging.getLogger(__name__)


def get_logger():
    return __LOGGER


def sleep_sec(sec: float) -> None:
    """Sleep for the specified amount of seconds."""
    time.sleep(sec)
