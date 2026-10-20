# cspell:ignore WRONLY
"""Constants for the integration."""

from __future__ import annotations

import logging
import os
import struct
import time
from contextlib import contextmanager

DOMAIN = "gpio_integration"
CPU_DMA_LATENCY = "/dev/cpu_dma_latency"

__LOGGER = logging.getLogger(__name__)


def get_logger():
    return __LOGGER


@contextmanager
def low_latency(path: str = CPU_DMA_LATENCY):
    """
    Keep the CPUs out of deep idle states while the block runs.

    Deep idle states take long to wake up from (220us on RK3588) and GPIO
    edge events arriving meanwhile are lost. Linux PM QoS: while the device
    is open with the value 0, no idle state with a wake up latency is used.
    """
    fd = None
    try:
        fd = os.open(path, os.O_WRONLY)
        os.write(fd, struct.pack("i", 0))
    except OSError:
        if fd is not None:
            os.close(fd)
        fd = None

    try:
        yield fd is not None
    finally:
        if fd is not None:
            os.close(fd)


def sleep_sec(sec: float) -> None:
    """Sleep for the specified amount of seconds."""
    time.sleep(sec)
