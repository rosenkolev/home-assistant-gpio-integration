from collections import deque, namedtuple
from threading import RLock
from typing import Callable, Literal
from weakref import WeakMethod

from gpiozero import (
    MCP3001,
    MCP3002,
    MCP3004,
    MCP3008,
    MCP3201,
    MCP3202,
    MCP3204,
    MCP3208,
    RGBLED,
    DigitalInputDevice,
    DigitalOutputDevice,
    InputDevice,
    PWMOutputDevice,
    event,
)

from ._pin_factory import get_pin_factory
from .core import get_logger, sleep_sec

_LOGGER = get_logger()


class AsStringMixin:
    def __repr__(self):
        return f"{self.pin!r} ({self.__class__.__name__})"


class Pwm(AsStringMixin, PWMOutputDevice):
    def __init__(self, pin: int, frequency=100, active_high=True, initial_value=False):
        super().__init__(
            pin,
            pin_factory=get_pin_factory(),
            active_high=active_high,
            frequency=frequency,
            initial_value=1 if initial_value else 0,
        )


class PwmFromPercent(Pwm):
    def _percent_to_value(self, percent: int) -> float:
        return percent / 100.0

    @property
    def percentage(self) -> int:
        return int(self.value * 100)

    @percentage.setter
    def percentage(self, percent: int):
        if percent < 0 or percent > 100:
            raise ValueError("percentage must be between 0 and 100")

        self.value = self._percent_to_value(percent)


class Switch(AsStringMixin, DigitalOutputDevice):
    def __init__(self, pin: int, active_high=True, initial_value=False):
        super().__init__(
            pin,
            pin_factory=get_pin_factory(),
            active_high=active_high,
            initial_value=initial_value,
        )


class BinarySensor(AsStringMixin, DigitalInputDevice):
    def __init__(self, pin: int, active_high=True, bounce_time=None):
        super().__init__(
            pin,
            pin_factory=get_pin_factory(),
            pull_up=not active_high,
            active_state=None,
            bounce_time=bounce_time,
        )

    on_state_changed: Callable[[DigitalInputDevice], None] = event(
        """
        Event that is fired when the state of the sensor changes.
        The callback should accept a single argument: the new state.
        """
    )

    def _pin_changed(self, ticks, state):
        super()._pin_changed(ticks, state)
        if self.on_state_changed:
            self.on_state_changed()

    @property
    def any_event_time_sec(self) -> float | None:
        active_time = self.active_time
        return active_time if active_time is not None else self.inactive_time


class RgbLight(RGBLED):
    def __init__(
        self, red: int, green: int, blue: int, active_high=True, initial_value=(0, 0, 0)
    ):
        super().__init__(
            red,
            green,
            blue,
            pin_factory=get_pin_factory(),
            active_high=active_high,
            initial_value=initial_value,
        )

    def __repr__(self):
        return f"{self.red!r}, {self.green!r}, {self.blue!r}"


MCP_CLASS_MAP = {
    "MCP3001": MCP3001,
    "MCP3002": MCP3002,
    "MCP3004": MCP3004,
    "MCP3008": MCP3008,
    "MCP3201": MCP3201,
    "MCP3202": MCP3202,
    "MCP3204": MCP3204,
    "MCP3208": MCP3208,
}

MCP_NAMES = list(MCP_CLASS_MAP.keys())


def create_analog_device(
    model: Literal[
        "MCP3001",
        "MCP3002",
        "MCP3004",
        "MCP3008",
        "MCP3201",
        "MCP3202",
        "MCP3204",
        "MCP3208",
    ],
    channel: int = 0,
):
    if model not in MCP_NAMES:
        raise ValueError(f"Invalid model: {model}")

    if model == "MCP3001" or model == "MCP3201":
        return MCP_CLASS_MAP[model](pin_factory=get_pin_factory())

    return MCP_CLASS_MAP[model](channel=channel, pin_factory=get_pin_factory())


class BitInfo:
    def __init__(self, state: int, duration_ms: float):
        self.state = state
        self.duration_ms = duration_ms

    def check(self, state: int, min_ms: float, max_ms) -> bool:
        return self.state == state and min_ms <= self.duration_ms <= max_ms

    def between(self, min_ms: float, max_ms: float) -> bool:
        return min_ms <= self.duration_ms <= max_ms

    def __repr__(self):
        return f"({self.state}[{self.duration_ms:.2f}ms])"


class EdgeInputDevice(InputDevice):
    def __init__(
        self,
        pin: int,
        active_high=True,
        bounce_time: float = None,
    ):
        super().__init__(
            pin,
            pin_factory=get_pin_factory(),
            pull_up=not active_high,
            active_state=None,
        )

        self.pin.bounce = bounce_time
        self.pin.edges = "both"
        self._lock = RLock()
        self._last_state = 0
        self._state_index = 0
        self._last_event = 0

    def read(self) -> None:
        self._state_index = 0
        self._last_state = 0
        self._last_event = self.pin_factory.ticks()
        self.pin.function = "input"
        self.pin.when_changed = self._pin_changed
        _LOGGER.debug(f"{self!r}: reading")

    def stop(self) -> None:
        self.pin.when_changed = None
        _LOGGER.debug(f"{self!r}: stopped")

    def _state_changed(self, state: BitInfo) -> None:
        pass

    def close(self):
        self._lock = None
        super().close()

    def _pin_changed(self, ticks: float, state: int):
        if self._state_index == 0:
            self._last_state = 1 if state == 0 else 0
        elif state == self._last_state:
            self.stop()
            raise ValueError("Invalid state change")

        with self._lock:
            elapsed_ms = self.pin_factory.ticks_diff(ticks, self._last_event) * 1000.0
            state_time = BitInfo(self._last_state, elapsed_ms)
            self._state_changed(state_time)
            self._last_state = state
            self._last_event = ticks
            self._state_index += 1


DHT22Data = namedtuple("DHT22Data", ["temperature", "humidity"])


class PulseMixin:
    def _send_and_wait(self, state: int, duration_sec: float) -> None:
        self.pin.value = state
        sleep_sec(duration_sec)


def dword_from_deque(deque: deque[BitInfo], bit_count: int) -> int:
    dword = 0b0000
    for _ in range(bit_count):
        dword <<= 1
        bit = deque.popleft()
        if bit.between(0.055, 0.085):
            dword |= 0b0001
        elif not bit.between(0.02, 0.035):
            raise ValueError("Invalid bit duration")
    return dword


class DHT22(AsStringMixin, PulseMixin, EdgeInputDevice):
    def __init__(self, pin: int):
        super().__init__(
            pin,
            bounce_time=0.000_005,
        )
        self._on_data_received = None
        self._on_invalid_check_sum = None
        self._transfer = False
        self._deque: deque[BitInfo] = deque(maxlen=40)

    def _state_changed(self, info: BitInfo) -> None:
        if not self._transfer:
            if self._state_index > 4:
                self.stop()
                _LOGGER.warning(f"{self!r}: invalid start bits")
            elif info.check(1, 0.07, 0.09):
                self._transfer = True
                _LOGGER.debug(f"{self!r}: transfer started")

            return

        if info.state == 1:
            self._deque.append(info)
            if self._deque.maxlen == len(self._deque):
                self.stop()
                _LOGGER.debug(f"{self!r} deque full")
                self._process()

    def _process(self) -> None:
        humidity = dword_from_deque(self._deque, 16)
        temperature = dword_from_deque(self._deque, 16)
        check_sum = dword_from_deque(self._deque, 8)

        _LOGGER.debug(f"{self!r}: {humidity=}, {temperature=}, {check_sum=}")

        sum = (
            (humidity >> 8)
            + (humidity & 0b1111_1111)
            + (temperature >> 8)
            + (temperature & 0b1111_1111)
        ) & 0b1111_1111
        if sum != check_sum:
            _LOGGER.warning(f"{self!r}: invalid check sum")
            if self.on_invalid_check_sum is not None:
                self.on_invalid_check_sum()
            else:
                raise ValueError("Invalid check sum")
        else:
            temperature_sign = -1 if temperature & 0b1000_0000 else 1
            temperature &= 0b0111_1111_1111_1111
            self.on_data_received(
                DHT22Data(
                    temperature_sign * temperature / 10.0,
                    humidity / 10.0,
                )
            )

    def read(self) -> None:
        self._deque.clear()
        self._transfer = False

        self.pin.when_changed = None
        self.pin.function = "output"

        self._send_and_wait(1, 0.001)  # 10 ms
        self._send_and_wait(0, 0.018)  # 18 ms
        self._send_and_wait(1, 0.000_04)  # 40 us

        super().read()

    def set_on_data_received(self, callback: Callable[[DHT22Data], None]) -> None:
        self._on_data_received = None if callback is None else WeakMethod(callback)

    def set_on_invalid_check_sum(self, callback: Callable[[], None]) -> None:
        self._on_invalid_check_sum = None if callback is None else WeakMethod(callback)

    on_data_received: Callable[[DHT22Data], None] = property(
        fget=lambda self: (
            None if self._on_data_received is None else self._on_data_received()
        ),
        fset=lambda self, value: self.set_on_data_received(value),
        doc="""
            Event that is fired when a new data is received from the sensor.
            The callback should accept 2 arguments: temperature and humidity.
            """,
    )

    on_invalid_check_sum: Callable[[], None] = property(
        fget=lambda self: self._on_invalid_check_sum(),
        fset=lambda self, value: self.set_on_invalid_check_sum(value),
        doc="""
            Event that is fired when an invalid check sum is received from the sensor.
            """,
    )
