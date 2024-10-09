from collections import deque, namedtuple
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


class SerialDataInputDevice(InputDevice):
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
        self._last_state: int = 0
        self._last_event: int = 0

    def read(self) -> None:
        self._last_state = 0
        self._last_event = self.pin_factory.ticks()
        self.pin.when_changed = self._pin_changed

    def stop(self) -> None:
        self.pin.when_changed = None

    def _check_transfer_started(self, state: tuple[bool, float]) -> bool:
        pass

    def _state_changed(self, state: tuple[bool, float]) -> None:
        pass

    def _pin_changed(self, ticks: float, state: int):
        if state == self._last_state:
            raise ValueError("Invalid state change")

        elapsed_ms = self.pin_factory.ticks_diff(ticks, self._last_event) * 1000
        state_time = (self._last_state, elapsed_ms)
        self._last_state = state
        self._last_event = ticks

        if self._check_transfer_started(state_time):
            self._state_changed(state_time)


class SerialDataPackageReader(SerialDataInputDevice):
    def __init__(
        self,
        pin: int,
        zero_high_ms_range: tuple[float, float],
        one_high_ms_range: tuple[float, float],
        bounce_time=None,
        output_transfer_trigger_bits: list[tuple[bool, float]] = None,
        input_package_initialize_bits: list[tuple[bool, float]] = None,
        word_bits_count: int = 8,
    ):
        super().__init__(pin, True, bounce_time)

        self._transfer = False
        self._initial_package_index = 0
        self._output_transfer_trigger_bits = output_transfer_trigger_bits
        self._input_package_initialize_bits = input_package_initialize_bits
        self._zero_high_ms_range = zero_high_ms_range
        self._one_high_ms_range = one_high_ms_range
        self._queue = deque(maxlen=word_bits_count)

    def read(self) -> None:
        self._queue.clear()
        self._transfer = False
        self._initial_package_index = 0
        self.send_trigger_package()
        super().read()

    def send_trigger_package(self) -> None:
        if self._output_transfer_trigger_bits is not None:
            for state, duration in self._output_transfer_trigger_bits:
                self.pin.value = state
                sleep(duration / 1000)

    def _check_transfer_started(self, state: tuple[bool, float]) -> bool:
        if self._input_package_initialize_bits is None or self._transfer:
            return True

        if self._input_package_initialize_bits[self._initial_package_index] == state:
            self._initial_package_index += 1
            if self._initial_package_index == len(self._input_package_initialize_bits):
                self._transfer = True

            return False

        self.stop()
        raise ValueError("Invalid package initialization")

    def _on_word_filled(self, bits: deque[int]) -> None:
        pass

    def _state_changed(self, state: tuple[int, float]) -> None:
        if state[0]:
            if self._zero_high_ms_range[0] <= state[1] <= self._zero_high_ms_range[1]:
                self._queue.append(0)
            elif self._one_high_ms_range[0] <= state[1] <= self._one_high_ms_range[1]:
                self._queue.append(1)
            else:
                self.stop()
                raise ValueError("Invalid bit duration")

            if len(self._queue) == self._queue.maxlen:
                self._on_word_filled(self._queue)
                self._queue.clear()


def bits_to_word(bits: deque[int]) -> int:
    dword = 0
    for bit in bits:
        dword = (dword << 1) | bit

    return dword


DHT22Data = namedtuple("DHT22Data", ["temperature", "humidity"])


class DHT22(SerialDataPackageReader):
    def __init__(self, pin: int):
        super().__init__(
            pin,
            zero_high_ms_range=(0.02, 0.03),
            one_high_ms_range=(0.06, 0.08),
            bounce_time=0.00001,
            output_transfer_trigger_bits=[(0, 5.0), (1, 0.04)],
            input_package_initialize_bits=[(0, 0.08), (1, 0.08)],
            word_bits_count=8,
        )
        self._reset_read_fields()
        self._on_data_received = None
        self._on_invalid_check_sum = None

    def set_on_data_received(self, callback: Callable[[DHT22Data], None]) -> None:
        self._on_data_received = None if callback is None else WeakMethod(callback)

    def set_on_invalid_check_sum(self, callback: Callable[[], None]) -> None:
        self._on_invalid_check_sum = None if callback is None else WeakMethod(callback)

    on_data_received: Callable[[DHT22Data], None] = property(
        fget=lambda self: self._on_data_received(),
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

    def _reset_read_fields(self) -> None:
        self._word_index = 0
        self._check_sum = 0
        self._temperature = 0
        self._temperature_sign = 1
        self._humidity = 0

    def read(self) -> None:
        self._reset_read_fields()
        super().read()

    def _on_word_filled(self, bits: deque[int]) -> None:
        """Converts 8 bits to a word and processes it."""

        if self.on_data_received is None:
            # when no one is listening, no need to continue
            self.stop()
            return

        # convert 8 bits to a word
        dword = bits_to_word(bits)
        if self._word_index < 4:
            # first 4 words are data
            self._check_sum += dword

            if self._word_index == 0:
                self._humidity = dword
            elif self._word_index == 1:
                self._humidity = (self._humidity << 8) | dword
            elif self._word_index == 2:
                if bits[0] == 1:
                    # negative temperature
                    bits[0] = 0
                    dword = bits_to_word(bits)
                    self._temperature_sign = -1

                self._temperature = dword
            else:
                self._temperature = (self._temperature << 8) | dword

            self._word_index += 1
        else:
            # last word is check sum
            self.stop()

            if (self._check_sum & 0b1111_1111) != dword:
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
