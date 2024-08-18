from __future__ import annotations

from RPi import GPIO

import logging

_LOGGER = logging.getLogger(__name__)


def get_logger():
    return _LOGGER


def setup_io():
    """setup GPIO"""
    GPIO.setmode(GPIO.BCM)


def clean_up_io():
    GPIO.cleanup()


def setup_input(port, pull_mode):
    """Set up a GPIO as input."""
    GPIO.setup(port, GPIO.IN, GPIO.PUD_DOWN if pull_mode == "down" else GPIO.PUD_UP)


def write_output(port, high):
    """Write a value to a GPIO."""
    GPIO.output(port, GPIO.HIGH if high else GPIO.LOW)


def read_input(port):
    """Read a value from a GPIO."""
    return GPIO.input(port)


def setup_output(pin, init_state):
    """initialize the GPIO pin"""
    GPIO.setup(pin, GPIO.OUT)

    write_output(pin, init_state)
    state = read_input(pin)
    assert state == init_state


def edge_detect(port, event_callback, bounce):
    """Add detection for RISING and FALLING events."""
    GPIO.add_event_detect(port, GPIO.BOTH, callback=event_callback, bouncetime=bounce)
