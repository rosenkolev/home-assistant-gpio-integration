from typing import Literal

import datetime

import gpiod
from gpiod.line import Direction, Bias, Edge, Value
from gpiod.line_settings import LineSettings

from .const import get_logger, DOMAIN

_LOGGER = get_logger()


def _read_device_model() -> str:
    try:
        with open("/sys/firmware/devicetree/base/model") as model_file:
            return model_file.read()
    except IOError:
        return ""


def _guess_default_device() -> str:
    device_model = _read_device_model()
    device_path = "/dev/gpiochip0"
    if "Raspberry Pi 5 Model B" in device_model:
        device_path = "/dev/gpiochip4"

    _LOGGER.debug("Default GPIO device: %s", device_path)
    if not gpiod.is_gpiochip_device(device_path):
        raise RuntimeError(f"Device {device_path} is not a GPIO device")

    return device_path


DEFAULT_DEVICE = _guess_default_device()

## test
PORTS = set()
HIGH = Value.ACTIVE
LOW = Value.INACTIVE

# TODO: Add support for generic GPIO parse
# T = TypeVar('T')
# class BoolParser(Generic[T]):
#     def parse(self, value: int) -> T:
#         return value == HIGH
#     def serialize(self, value: T) -> int:
#         return HIGH if value else LOW
# class BoolInvertParser(Generic[T]):
#     def parse(self, value: int) -> T:
#         return value == LOW
#     def serialize(self, value: T) -> int:
#         return LOW if value else HIGH


class Gpio:
    def __init__(
        self,
        port: int,
        mode: Literal["read", "write"] = "read",
        pull_mode: Literal["up", "down"] = "up",
        edge_detect: Literal["RISING", "FALLING", "BOTH"] | None = None,
        debounce_ms: int = 0,
        default_value: bool | None = None,
        device=DEFAULT_DEVICE,
    ):
        if port in PORTS:
            raise ValueError(f"Port {port} already in use")

        settings = dict()
        if mode == "read":
            settings["direction"] = Direction.INPUT
            settings["bias"] = Bias.PULL_DOWN if pull_mode == "down" else Bias.PULL_UP
            if edge_detect is not None:
                """set edge detection when reading"""
                settings["edge_detection"] = getattr(Edge, edge_detect)
                settings["debounce_period"] = datetime.timedelta(
                    milliseconds=debounce_ms
                )
        elif mode == "write":
            settings["direction"] = Direction.OUTPUT

        self.pin = port
        self.req = gpiod.request_lines(
            device,
            consumer=DOMAIN,
            config={port: LineSettings(**settings)},
        )

        if mode == "write" and default_value is not None:
            self.write(default_value)

    def read(self) -> bool:
        value = self.req.get_value(self.pin)
        _LOGGER.debug("read pin %s: %s", self.pin, value)
        return value == HIGH

    def write(self, state: bool) -> None:
        value = HIGH if state else LOW
        _LOGGER.debug("set pin %s to %s", self.pin, value)
        self.req.set_values({self.pin: value})

    def read_edge_events(self, timeout: int = 0):
        if self.req.wait_edge_events(timeout):
            events = self.req.read_edge_events()
            for event in events:
                _LOGGER.debug(
                    "Edge event on %s:%s: %s", self.req.chip_name, self.req.lines, event
                )
            return events
        return []

    def release(self):
        self.req.release()
        self.req = None
