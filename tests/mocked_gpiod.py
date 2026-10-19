# cspell:ignore gpiod, gpiochip, rsock, wsock
"""A minimal in-memory fake of the `gpiod` (libgpiod v2) python package."""

import socket
import sys
from collections import deque
from datetime import timedelta
from enum import Enum
from types import ModuleType


class Direction(Enum):
    AS_IS = 1
    INPUT = 2
    OUTPUT = 3


class Bias(Enum):
    AS_IS = 1
    UNKNOWN = 2
    DISABLED = 3
    PULL_UP = 4
    PULL_DOWN = 5


class Edge(Enum):
    NONE = 1
    RISING = 2
    FALLING = 3
    BOTH = 4


class Drive(Enum):
    PUSH_PULL = 1


class Value(Enum):
    INACTIVE = 0
    ACTIVE = 1


class Clock(Enum):
    MONOTONIC = 1
    REALTIME = 2
    HTE = 3


class LineSettings:
    def __init__(
        self,
        direction=Direction.AS_IS,
        edge_detection=Edge.NONE,
        bias=Bias.AS_IS,
        drive=Drive.PUSH_PULL,
        active_low=False,
        debounce_period=timedelta(0),
        event_clock=Clock.MONOTONIC,
        output_value=Value.INACTIVE,
    ):
        self.direction = direction
        self.edge_detection = edge_detection
        self.bias = bias
        self.drive = drive
        self.active_low = active_low
        self.debounce_period = debounce_period
        self.event_clock = event_clock
        self.output_value = output_value

    def __repr__(self):
        return f"LineSettings({self.__dict__})"


class EdgeEvent:
    class Type(Enum):
        RISING_EDGE = 1
        FALLING_EDGE = 2

    def __init__(self, event_type, timestamp_ns, line_offset):
        self.event_type = event_type
        self.timestamp_ns = timestamp_ns
        self.line_offset = line_offset


class ChipInfo:
    def __init__(self, name, label, num_lines):
        self.name = name
        self.label = label
        self.num_lines = num_lines


class LineInfo:
    def __init__(self, offset, name):
        self.offset = offset
        self.name = name
        self.used = False
        self.consumer = None
        self.direction = Direction.INPUT
        self.bias = Bias.UNKNOWN


# path -> (name, label, number of lines, {offset: line name})
CHIPS = {
    "/dev/gpiochip0": ("gpiochip0", "gpio0", 32, {13: "PIN_8", 14: "PIN_10"}),
    "/dev/gpiochip4": ("gpiochip4", "gpio4", 32, {10: "PIN_5", 11: "PIN_3"}),
    "/dev/gpiochip5": ("gpiochip5", "rk806-gpio", 3, {}),
}


def is_gpiochip_device(path: str) -> bool:
    return path in CHIPS


class LineRequest:
    def __init__(self, chip, config, consumer, event_buffer_size):
        self.chip = chip
        self.consumer = consumer
        self.event_buffer_size = event_buffer_size
        self.settings = {}
        self.values = {}
        self.history = []
        self.writes = []
        self.released = False
        self._events = deque()
        self._rsock, self._wsock = socket.socketpair()
        self.fd = self._rsock.fileno()
        self.reconfigure_lines(config)

    def reconfigure_lines(self, config):
        for offset, settings in config.items():
            self.settings[offset] = settings
            self.history.append((offset, settings))
            if settings.direction == Direction.OUTPUT:
                self.values[offset] = settings.output_value
            else:
                self.values.setdefault(offset, Value.INACTIVE)

    @property
    def last(self) -> LineSettings:
        return self.history[-1][1]

    def set_value(self, offset, value):
        assert not self.released
        self.values[offset] = value
        self.writes.append(value)

    def get_value(self, offset):
        assert not self.released
        return self.values[offset]

    def read_edge_events(self, max_events=None):
        assert not self.released
        self._rsock.recv(1024)
        events = list(self._events)
        self._events.clear()
        return events

    def wait_edge_events(self, timeout=None):
        return len(self._events) > 0

    def release(self):
        self.released = True
        self._rsock.close()
        self._wsock.close()

    # test helper
    def push_event(self, offset, rising: bool, timestamp_ns: int):
        self.values[offset] = Value.ACTIVE if rising else Value.INACTIVE
        self._events.append(
            EdgeEvent(
                EdgeEvent.Type.RISING_EDGE if rising else EdgeEvent.Type.FALLING_EDGE,
                timestamp_ns,
                offset,
            )
        )
        self._wsock.send(b"x")


class Chip:
    instances = []

    def __init__(self, path):
        if path not in CHIPS:
            raise OSError(f"{path} does not exist")
        name, label, lines, names = CHIPS[path]
        self.path = path
        self.info = ChipInfo(name, label, lines)
        self.line_names = names
        self.requests = []
        self.closed = False
        Chip.instances.append(self)

    def get_info(self):
        return self.info

    def get_line_info(self, offset):
        return LineInfo(offset, self.line_names.get(offset, ""))

    def request_lines(
        self, config, consumer=None, event_buffer_size=None, output_values=None
    ):
        request = LineRequest(self, config, consumer, event_buffer_size)
        self.requests.append(request)
        return request

    def close(self):
        self.closed = True


def register(modules: dict) -> ModuleType:
    """Register this fake as the `gpiod` and `gpiod.line` packages."""
    gpiod = ModuleType("gpiod")
    gpiod.__version__ = "2.5.0-mock"
    gpiod.Chip = Chip
    gpiod.LineSettings = LineSettings
    gpiod.LineRequest = LineRequest
    gpiod.EdgeEvent = EdgeEvent
    gpiod.is_gpiochip_device = is_gpiochip_device

    line = ModuleType("gpiod.line")
    for cls in (Direction, Bias, Edge, Drive, Value, Clock):
        setattr(line, cls.__name__, cls)

    gpiod.line = line
    modules["gpiod"] = gpiod
    modules["gpiod.line"] = line
    return gpiod


if "gpiod" not in sys.modules:
    register(sys.modules)
