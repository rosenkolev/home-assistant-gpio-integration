"""Constants for the integration."""

from __future__ import annotations

import logging

DOMAIN = "gpio_integration"

__LOGGER = logging.getLogger(__name__)


def get_logger():
    return __LOGGER


class ClosableMixin:
    def __enter__(self):
        return self

    def __exit__(self, *exc_info) -> None:
        self._close()

    def _close(self) -> None:
        if hasattr(self, "_io") and self._io is not None:
            self._io.close()
            self._io = None
