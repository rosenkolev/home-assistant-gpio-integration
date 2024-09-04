from typing import Type

import pigpio

from custom_components.gpio_integration.const import get_logger

from . import (
    BounceType,
    EdgesType,
    ModeType,
    Pin,
    PinFactory,
    PullType,
    get_config_option,
)

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


class GpioPinFactory(PinFactory):
    def __init__(self) -> None:
        self._pin_class = GpioPin
        self.gpio = None
        super().__init__()

    def connect(self) -> pigpio.pi:
        if self.gpio is not None:
            return self.gpio

        host = get_config_option("host")
        if host is None:
            self.gpio = pigpio.pi()
        else:
            _LOGGER.warning(f"pigpio.pi({host})")
            self.gpio = pigpio.pi(host)

        if self.gpio is None or not self.gpio.connected:
            raise IOError("failed to connect")

        _LOGGER.debug("pigpio connected")

        return self.gpio

    def cleanup(self) -> None:
        if self.controller is not None:
            self.controller.stop()
            self.controller = None


class GpioPin(Pin):
    def __init__(
        self,
        pin=None,
        mode: ModeType = "input",
        pull: PullType = "floating",
        bounce: BounceType = None,
        edge: EdgesType = "BOTH",
        frequency: int | None = None,
        default_value=None,
        when_changed=None,
        factory: Type[GpioPinFactory] = None,
    ):
        self._callback = None
        self._connection = factory.connect()

        # base class calls _connect
        super().__init__(
            pin,
            mode,
            pull,
            bounce,
            edge,
            frequency,
            default_value,
            when_changed,
            factory,
        )

    def _setup(self):
        self._set_mode(self._mode)
        self._set_pull(self._pull)
        self._set_bounce(self._bounce)
        _LOGGER.debug(f"pin {self.pin} initialized")

    def _close(self):
        self.when_changed = None
        self.frequency = None
        _LOGGER.debug(f"pin {self.pin} closed")

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
            _LOGGER.error(f"pin {self.pin} invalid PWM value '{value}'")
            raise RuntimeError("invalid state")

    def _read_pwm(self) -> float:
        return self._get_pwm_cycle() / self._get_pwm_range()

    def _write(self, value: bool) -> None:
        self._connection.write(self.pin, bool(value))
        _LOGGER.debug(f"pin {self.pin} write '{value}'")

    def _read(self) -> bool:
        return self._connection.read(self.pin)

    def _set_mode(self, value: ModeType) -> None:
        if value not in GPIO_MODES:
            _LOGGER.error(f"mode {value} not supported by pigpio")
            raise ValueError("mode not supported")

        _LOGGER.debug(f"pin {self.pin} set mode '{value}'")
        try:
            self._connection.set_mode(int(self.pin), GPIO_MODES[value])
        except pigpio.error as e:
            raise ValueError(e)

        super()._set_mode(value)

    def _set_pull(self, value: PullType) -> None:
        if value not in GPIO_PULL_UPS:
            _LOGGER.error(f"Pull {value} not supported by pigpio")
            raise ValueError("pull not supported")

        self._connection.set_pull_up_down(self.pin, GPIO_PULL_UPS[value])

        _LOGGER.debug(f"pin {self.pin} pull set '{value}'")

        super()._set_pull(value)

    def _set_bounce(self, value: float | None) -> None:
        if value is not None and value < 0 and value > 0.3:
            _LOGGER.error(f"bounce {value} not supported by pigpio")
            raise ValueError("bounce not supported")
        elif value is None:
            value = 0

        filter = int(value * 1000000)
        self._connection.set_glitch_filter(self.pin, filter)
        _LOGGER.debug(f"pin {self.pin} bounce set {value}s({filter}µs)")
        super()._set_bounce(filter)

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
                self.pin,
                GPIO_EDGES[value],
                self._call_when_changed,
            )

            _LOGGER.debug(f"pin {self.pin} edge detection enabled")
        else:
            _LOGGER.error(f"edges {value} value not supported by pigpio")
            raise ValueError("edges not supported")

    def _disable_event_detect(self):
        if self._callback is not None:
            self._callback.cancel()
            self._callback = None

            _LOGGER.debug(f"pin {self.pin} edge detection disabled")
