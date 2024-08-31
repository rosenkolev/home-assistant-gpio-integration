from typing import Callable
import pigpio

from custom_components.gpio_integration.const import get_logger
from . import Pin, PullType, EdgesType, BounceType, ModeType

_LOGGER = get_logger()

GPIO_PULL_UPS = {
    "up": pigpio.PUD_UP,
    "down": pigpio.PUD_DOWN,
    "floating": pigpio.PUD_OFF,
}

GPIO_EDGES = {
    "both": pigpio.EITHER_EDGE,
    "rising": pigpio.RISING_EDGE,
    "falling": pigpio.FALLING_EDGE,
}

GPIO_MODES = {
    "input": pigpio.INPUT,
    "output": pigpio.OUTPUT,
}


class GpioPin(Pin):
    def __init__(
        self,
        pin=None,
        pull: PullType = "floating",
        mode: ModeType = "input",
        bounce: BounceType = None,
        edge: EdgesType = "BOTH",
        frequency: int | None = None,
        default_value=None,
        when_changed=None,
    ):
        self._callback = None
        self._connection = None

        # base class calls _connect
        super().__init__(
            pin, mode, pull, bounce, edge, frequency, default_value, when_changed
        )

    def _connect(self):
        if self._connection is not None:
            self._close()

        self._connection = pigpio.pi()
        if self._connection is None:
            raise IOError("failed to connect")

        self._set_mode(self._mode)
        self._set_pull(self._pull)
        self._set_bounce(self._bounce)
        _LOGGER.debug(f"pin {self.pin} connected")

    def _close(self):
        if self._connection is not None:
            self._connection.stop()
            self._connection = None

    def _get_pwm_range(self) -> float:
        return self._connection.get_PWM_range(self.pin)

    def _get_pwm_cycle(self) -> float:
        return self._connection.get_PWM_dutycycle(self.pin)

    def _write_pwm(self, value: float) -> None:
        try:
            value = int(value * self._get_pwm_range())
            if value != self._get_pwm_cycle():
                self._connection.set_PWM_dutycycle(self.pin, value)
                _LOGGER.debug(f"pin {self.pin} PWM write '{value}'")
        except pigpio.error:
            raise RuntimeError(f'invalid state "{value}" for pin {self.pin}')

    def _read_pwm(self) -> float:
        return self._get_pwm_cycle() / self._get_pwm_range()

    def _write(self, value: bool) -> None:
        self._connection.write(self.pin, bool(value))
        _LOGGER.debug(f"pin {self.pin} write '{value}'")

    def _read(self) -> bool:
        return self._connection.read(self.pin)

    def _set_mode(self, value: ModeType) -> None:
        if value not in GPIO_MODES:
            raise ValueError(f"mode {value} not supported by pigpio")

        self._connection.set_mode(pigpio.INPUT if value == "input" else pigpio.OUTPUT)

        _LOGGER.debug(f"pin {self.pin} mode set '{value}'")

        super()._set_mode(value)

    def _set_pull(self, value: PullType) -> None:
        if value not in GPIO_PULL_UPS:
            raise ValueError(f"Pull {value} not supported by pigpio")

        self._connection.set_pull_up_down(GPIO_PULL_UPS[value])

        _LOGGER.debug(f"pin {self.pin} pull set '{value}'")

        super()._set_pull(value)

    def _set_bounce(self, value: float | None) -> None:
        filter = int(value * 1000000) if value is not None and value > 0 else 0
        self._connection.set_glitch_filter(self.pin, filter)
        _LOGGER.debug(f"pin {self.pin} bounce set {value}s({filter}µs)")
        super()._set_bounce(value)

    def _update_frequency(self, frequency: int):
        self._connection.set_PWM_frequency(self.pin, int(frequency))
        self._connection.set_PWM_range(self.pin, 10000)
        _LOGGER.debug(f"pin {self.pin} frequency set {frequency}Hz")

    def _enable_pwm(self, frequency: int) -> None:
        self._connection.write(self.pin, 0)
        self._update_frequency(frequency)
        self._connection.set_PWM_dutycycle(self.pin, 0)

    def _disable_pwm(self):
        self._connection.write(self.pin, 0)

    def _enable_event_detect(self):
        value = self.edges
        if value in GPIO_EDGES:
            self._callback = self._connection.callback(
                self.pin, GPIO_EDGES[value], self._call_when_changed
            )

            _LOGGER.debug(f"pin {self.pin} edge detection enabled")
        else:
            raise ValueError(f"Edges {value} value not supported by pigpio")

    def _disable_event_detect(self):
        if self._callback is not None:
            self._callback.cancel()
            self._callback = None

            _LOGGER.debug(f"pin {self.pin} edge detection disabled")
