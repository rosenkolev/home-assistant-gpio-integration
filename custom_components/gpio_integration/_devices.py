from queue import Queue

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
    def __init__(self, pin: int, pull_up=False, active_state=False, bounce_time=None):
        super().__init__(
            pin,
            pin_factory=get_pin_factory(),
            pull_up=pull_up,
            active_state=None,
            bounce_time=bounce_time,
        )

        self.active_high = not active_state

    @property
    def last_event_time_sec(self) -> float | None:
        active_time = self.active_time
        return active_time if active_time is not None else self.inactive_time

    @property
    def value(self) -> bool:
        return self._read() == self.active_high

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
        pull_up=False,
        active_state=False,
        bounce_time=None,
        max_bits=8,
        package_initial_bits: list[tuple[bool, float]] = None,
    ):
        super().__init__(
            pin,
            pin_factory=get_pin_factory(),
            pull_up=pull_up,
            active_state=None,
            bounce_time=bounce_time,
        )

        self.pin.bounce = bounce_time
        self.pin.edges = "both"
        self.pin.when_changed = self._pin_changed
        self._bits: Queue[tuple[bool, float]] = Queue(max_bits * 2)
        self._last_event = None
        self._transfer = False
        self._init_index = 0
        self._package_initial_bits = package_initial_bits

    def clear(self):
        with self._bits.mutex:
            self._bits.queue.clear()

        self._last_state = self.value
        self._last_event = self.pin_factory.ticks()

    when_filled = event(
        """
        Event that is fired when the queue is filled with bits.
        The callback should accept a single argument: the value of the bits.
        """
    )

    def _pin_changed(self, ticks, state):
        if state == self._last_state:
            self.clear()
            raise ValueError("Invalid state change")

        elapsed_ms = self.pin_factory.ticks_diff(self._last_event, ticks) / 1000

        if self._package_initial_bits is None or self._transfer:
            self._bits.put((self._last_state, elapsed_ms))
            if self._bits.full() and self.when_filled:
                self.when_filled(self._bits.queue)
        elif self._package_init_bits[self._init_index] == (
            self._last_state,
            elapsed_ms,
        ):
            self._init_index += 1
            if self._init_index == len(self._package_init_bits):
                self._transfer = True
