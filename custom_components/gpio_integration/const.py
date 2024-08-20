"""Constants for the integration."""

from __future__ import annotations

import logging

DOMAIN = "gpio_integration"

__LOGGER = logging.getLogger(__name__)


def get_logger():
    return __LOGGER


def read_device_model() -> str:
    try:
        with open("/sys/firmware/devicetree/base/model") as model_file:
            return model_file.read()
    except IOError:
        return ""
