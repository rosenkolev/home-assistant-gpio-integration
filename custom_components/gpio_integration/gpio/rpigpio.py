from typing import Callable
from custom_components.gpio_integration.const import get_logger
from . import Pin, PullType, EdgesType, BounceType, ModeType

from RPi import GPIO

_LOGGER = get_logger()
_INITIALIZED = False

GPIO_PULL_UPS = {
    "up": GPIO.PUD_UP,
    "down": GPIO.PUD_DOWN,
    "floating": GPIO.PUD_OFF,
}

GPIO_EDGES = {
    "both": GPIO.BOTH,
    "rising": GPIO.RISING,
    "falling": GPIO.FALLING,
}

GPIO_MODES = {
    "input": GPIO.IN,
    "output": GPIO.OUT,
}


class GpioPin(Pin):
    def __init__(
        self,
        pin: int | str,
        mode: ModeType = "input",
        pull: PullType = "floating",
        bounce: BounceType = None,
        edge: EdgesType = "BOTH",
        frequency: int | None = None,
        default_value: float | bool | None = None,
        when_changed: Callable[[int], None] = None,
    ):
        self._frequency: int | None = None
        self._pwm = None

        super().__init__(
            pin, mode, pull, bounce, edge, frequency, default_value, when_changed
        )

    def _connect(self):
        if _INITIALIZED == False:
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)

        self._setup_pin()

    def _close(self):
        GPIO.cleanup(self.pin)

    def _write_pwm(self, value: float) -> None:
        self._pwm.ChangeDutyCycle(value * 100)
        self._duty_cycle = value
        _LOGGER.debug(f"pin {self.pin} PWM write '{value}'")

    def _read_pwm(self) -> float:
        return self._duty_cycle

    def _write(self, value: bool) -> None:
        GPIO.output(self.pin, GPIO.HIGH if value else GPIO.LOW)
        _LOGGER.debug(f"pin {self.pin} write '{value}'")

    def _read(self) -> bool:
        return GPIO.input(self.pin) == GPIO.HIGH

    def _setup_pin(self) -> None:
        if self._mode not in GPIO_MODES:
            raise ValueError(f"Mode {self._mode} not supported by RPi.GPIO")
        if self._pull not in GPIO_PULL_UPS:
            raise ValueError(f"Pull {self._pull} not supported by RPi.GPIO")

        GPIO.setup(self.pin, GPIO_MODES[self._mode], GPIO_PULL_UPS[self._pull])
        _LOGGER.debug(f"pin {self.pin} mode '{self._mode}' pull '{self._pull}'")

    def _set_mode(self, value: ModeType) -> None:
        super()._set_mode(value)
        self._setup_pin()

    def _set_pull(self, value: PullType) -> None:
        super()._set_pull(value)
        self._setup_pin()

    def _set_bounce(self, value: float | None) -> None:
        self._bounce = -666 if value is None else value
        _LOGGER.debug(f"pin {self.pin} bounce set {value}s")

    def _update_frequency(self, frequency: int):
        self._pwm.ChangeFrequency(frequency)
        _LOGGER.debug(f"pin {self.pin} frequency set {frequency}Hz")

    def _enable_pwm(self, frequency: int) -> None:
        self._pwm = GPIO.PWM(self.pin, frequency)
        self._pwm.start(0)
        self._duty_cycle = 0
        _LOGGER.debug(f"pin {self.pin} start PWM with {frequency}Hz")

    def _disable_pwm(self):
        self._pwm.stop()
        self._pwm = None
        self._duty_cycle = None
        _LOGGER.debug(f"pin {self.pin} stop PWM")

    def _enable_event_detect(self):
        value = self.edges
        if value not in GPIO_EDGES:
            raise ValueError(f"Edges {value} value not supported by RPi.GPIO")

        GPIO.add_event_detect(
            self.pin,
            GPIO_EDGES[value],
            callback=self._call_when_changed,
            bouncetime=self._bounce,
        )
        _LOGGER.debug(f"pin {self.pin} edge detection enabled")

    def _disable_event_detect(self):
        GPIO.remove_event_detect(self.pin)
        _LOGGER.debug(f"pin {self.pin} edge detection disabled")
