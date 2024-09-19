"""Constants for the integration."""

from __future__ import annotations

import logging
from threading import Event, Thread
from typing import Iterable

DOMAIN = "gpio_integration"

__LOGGER = logging.getLogger(__name__)


def get_logger():
    return __LOGGER


class StoppableThread(Thread):
    def __init__(self, target, name: str | None = None, args=(), kwargs=None):
        self.stopping = Event()
        super().__init__(None, target, name, args, kwargs, demon=True)

    def start(self):
        self.stopping.clear()
        super().start()

    def stop(self, timeout=None):
        if self.is_alive():
            self.stopping.set()
            self.join(timeout)

    def wait(self, timeout: int):
        return self.stopping.wait(timeout)


class GpioEffect:
    def compute_state(self, config: dict) -> Iterable[tuple[bool | float, float]]:
        raise NotImplementedError
