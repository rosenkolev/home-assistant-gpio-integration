"""Constants for the integration."""

from __future__ import annotations

import logging

DOMAIN = "gpio_integration"

__LOGGER = logging.getLogger(__name__)


def get_logger():
    return __LOGGER
