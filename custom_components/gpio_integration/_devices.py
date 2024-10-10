from collections import deque, namedtuple
from math import isclose
from threading import RLock
from time import sleep
from typing import Callable
from weakref import WeakMethod

from gpiozero import (
    RGBLED,
    DigitalInputDevice,
    DigitalOutputDevice,
    InputDevice,
    PWMOutputDevice,
    event,
)

from ._pin_factory import get_pin_factory
from .core import get_logger

_LOGGER = get_logger()


class Pwm(PWMOutputDevice):
    def __init__(self, pin: int, frequency=100, active_high=True, initial_value=False):
        super().__init__(
            pin,
            pin_factory=get_pin_factory(),
            active_high=active_high,
            frequency=frequency,
            initial_value=1 if initial_value else 0,
        )

    def __repr__(self):
        return f"{self.pin!r}"


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


class Switch(DigitalOutputDevice):
    def __init__(self, pin: int, active_high=True, initial_value=False):
        super().__init__(
            pin,
            pin_factory=get_pin_factory(),
            active_high=active_high,
            initial_value=initial_value,
        )

    def __repr__(self):
        return f"{self.pin!r}"


class BinarySensor(DigitalInputDevice):
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

    def __repr__(self):
        return f"{self.pin!r}"


class RgbLight(RGBLED):
    def __init__(self, red: int, green: int, blue: int, initial_value=(0, 0, 0)):
        super().__init__(
            red,
            green,
            blue,
            pin_factory=get_pin_factory(),
            initial_value=initial_value,
        )

    def __repr__(self):
        return f"{self.red!r}, {self.green!r}, {self.blue!r}"


class BitInfo:
    def __init__(self, state: int, duration_ms: float | None):
        self.state = state
        self.duration_ms = duration_ms

    def between(self, min_ms: float, max_ms: float) -> bool:
        return min_ms <= self.duration_ms <= max_ms

    def __eq__(self, value: object) -> bool:
        return (
            isinstance(value, BitInfo)
            and self.state == value.state
            and (
                self.duration_ms is None
                or isclose(
                    self.duration_ms, value.duration_ms, rel_tol=0.01, abs_tol=0.01
                )
            )
        )

    def __repr__(self):
        return f"({self.state}[{self.duration_ms:.2f}])"


class EdgeInputDevice(InputDevice):
    def __init__(
        self,
        pin: int,
        active_high=True,
        bounce_time=None,
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
        self._last_event = self.pin_factory.ticks()
        self.pin.when_changed = self._pin_changed

    def stop(self) -> None:
        self.pin.when_changed = None

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
            elapsed_ms = self.pin_factory.ticks_diff(ticks, self._last_event) * 1000
            state_time = BitInfo(self._last_state, elapsed_ms)
            self._last_state = state
            self._last_event = ticks
            self._state_changed(state_time)
            self._state_index += 1


class SerialInputDevice(EdgeInputDevice):
    def __init__(
        self,
        pin: int,
        zero_high_ms_range: tuple[float, float],
        one_high_ms_range: tuple[float, float],
        bounce_time=None,
        ready_to_send_bits: list[BitInfo] = [],
        word_bits_count: int = 8,
    ):
        super().__init__(pin, True, bounce_time)

        self._transferring = False
        self._ready_to_send_bits = ready_to_send_bits
        self._ready_to_send_bits_count = len(ready_to_send_bits)
        self._zero_high_ms_range = zero_high_ms_range
        self._one_high_ms_range = one_high_ms_range
        self._dword_size = word_bits_count
        self._dword = 0
        self._dword_index = 0

    def read(self) -> None:
        if self._transferring:
            _LOGGER.debug("Already transferring")
            return

        self._transferring = self._ready_to_send_bits_count == 0
        self._dword = 0b0000
        self._dword_index = self._dword_size
        super().read()

    def stop(self) -> None:
        self._transferring = False
        return super().stop()

    def _on_word_filled(self, dword: int) -> None:
        pass

    def _state_changed(self, info: BitInfo) -> None:
        if not self._transferring:
            if self._ready_to_send_bits_count <= self._state_index:
                self._transferring = True
                _LOGGER.debug(f"{self.pin!r} transferring data")
            elif self._ready_to_send_bits[self._state_index] == info:
                # ready to send sequence is correct so far
                return
            else:
                self.stop()
                raise ValueError("Invalid ready to send bits")

        if info.state == 1:
            self._dword <<= 1
            if info.between(*self._one_high_ms_range):
                self._dword |= 0b0001
            elif not info.between(*self._zero_high_ms_range):
                self.stop()
                raise ValueError("Invalid bit duration")

            self._dword_index -= 1
            if self._dword_index <= 0:
                self._on_word_filled(self._dword)
                self._dword_index = self._dword_size
                self._dword = 0b0000


DHT22Data = namedtuple("DHT22Data", ["temperature", "humidity"])


class PulseMixin:
    def _send_sec(self, state: int, duration_sec: float) -> None:
        self.pin.value = state
        sleep(duration_sec / 1000)


class DHT22(PulseMixin, SerialInputDevice):
    def __init__(self, pin: int):
        super().__init__(
            pin,
            zero_high_ms_range=(0.02, 0.035),
            one_high_ms_range=(0.055, 0.085),
            bounce_time=0.000_005,
            ready_to_send_bits=[BitInfo(1, None), BitInfo(0, None)],
            word_bits_count=8,
        )

        self._on_data_received = None
        self._on_invalid_check_sum = None
        self._reset_fields()

    def read(self) -> None:
        if self._transferring:
            return

        self._reset_fields()
        self.trigger_pulse()
        super().read()

    def _reset_fields(self) -> None:
        self._word_index = 0
        self._check_sum = 0
        self._temperature = 0
        self._temperature_sign = 1
        self._humidity = 0

    def trigger_pulse(self) -> None:
        self.pin.function = "output"
        self._send_sec(1, 0.010)  # 10 ms
        self._send_sec(0, 0.018)  # 18 ms
        self._send_sec(1, 0.000_04)  # 40 us
        self.pin.function = "input"

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

    def _on_word_filled(self, dword: int) -> None:
        """Converts 8 bits to a word and processes it."""
        _LOGGER.debug(f"word: {dword:08b}")
        if self.on_data_received is None:
            # when no one is listening, no need to continue
            self.stop()
            return

        if self._word_index < 4:
            # first 4 words are data
            self._check_sum += dword

            if self._word_index == 0:
                self._humidity = dword
            elif self._word_index == 1:
                self._humidity = (self._humidity << 8) | dword
            elif self._word_index == 2:
                sign_bit = 0b1000_0000
                if (dword & sign_bit) == sign_bit:
                    # convert the sign bit to 0
                    dword &= sign_bit & 0b0111_1111
                    self._temperature_sign = -1

                self._temperature = dword
            else:
                self._temperature = (self._temperature << 8) | dword

            self._word_index += 1
        else:
            # last word is check sum
            self.stop()

            if (self._check_sum & 0b1111_1111) != dword:
                _LOGGER.warning(
                    f"checksum mismatch: {self._check_sum:08b} != {dword:08b}"
                )
                if self.on_invalid_check_sum is not None:
                    self.on_invalid_check_sum()
                else:
                    raise ValueError("Invalid check sum")
            else:
                self.on_data_received(
                    DHT22Data(
                        self._temperature_sign * self._temperature / 10.0,
                        self._humidity / 10.0,
                    )
                )
