# cspell:ignore setwarnings

import logging
from unittest.mock import Mock, patch

import mocked_models as mocked

PINS = dict()


class MockedGPIO:
    BCM = "BCM"
    IN = "IN"
    OUT = "OUT"
    PUD_UP = "PUD_UP"
    PUD_DOWN = "PUD_DOWN"
    PUD_OFF = "PUD_OFF"
    BOTH = "BOTH"
    RISING = "RISING"
    FALLING = "FALLING"
    HIGH = "HIGH"
    LOW = "LOW"

    def __init__(self):
        self.pins = PINS

    def setmode(self, mode):
        self.mode = mode

    def setwarnings(self, flag):
        self.warnings = flag

    def setup(self, pin, mode, pull_up_down):
        self.pins.setdefault(pin, dict({"mode": mode, "pull": pull_up_down}))

    def cleanup(self, pin):
        if pin in self.pins:
            del self.pins[pin]

    def output(self, pin, state):
        self.pins[pin]["state"] = state

    def input(self, pin):
        return self.pins[pin].get("state", self.LOW)

    def PWM(self, pin, frequency):
        pwm = Mock()
        pwm.start = Mock()
        pwm.ChangeDutyCycle = Mock()
        pwm.ChangeFrequency = Mock()
        pwm.stop = Mock()
        self.pins[pin]["pwm"] = pwm
        self.pins[pin]["frequency"] = frequency
        return pwm

    def add_event_detect(self, pin, edge, callback, bouncetime):
        self.pins[pin]["edge"] = edge
        self.pins[pin]["bouncetime"] = bouncetime
        self.pins[pin]["callback"] = callback

    def remove_event_detect(self, pin):
        del self.pins[pin]["callback"]

    def trigger_event(self, pin, value):
        if "callback" in self.pins[pin]:
            self.pins[pin]["callback"](value)


def test__rpigpio_connect():
    """Test the RPi.GPIO module."""

    proxy = MockedGPIO()
    pin = mocked.get_next_pin()
    logging.getLogger().error("pin %s", pin)
    with patch("RPi.GPIO", proxy):
        import custom_components.gpio_integration.gpio.__rpigpio as base

        base.GpioPin(pin, factory=base.GpioPinFactory())

        assert proxy.pins[pin]["mode"] == proxy.IN
        assert proxy.pins[pin]["pull"] == proxy.PUD_OFF


def test__rpigpio_set_default_value():
    proxy = MockedGPIO()
    pin = mocked.get_next_pin()
    with patch("RPi.GPIO", proxy):
        import custom_components.gpio_integration.gpio.__rpigpio as base

        base.GpioPin(
            pin, mode="output", default_value=True, factory=base.GpioPinFactory()
        )

        assert proxy.pins[pin]["state"] == "HIGH"


def test__rpigpio_set_frequency():
    proxy = MockedGPIO()
    pin = mocked.get_next_pin()
    with patch("RPi.GPIO", proxy):
        import custom_components.gpio_integration.gpio.__rpigpio as base

        base.GpioPin(pin, mode="output", frequency=100, factory=base.GpioPinFactory())

        proxy.pins[pin]["pwm"].start.assert_called_once_with(0)
        assert proxy.pins[pin]["frequency"] == 100


def test__rpigpio_edge_detection():
    proxy = MockedGPIO()
    pin = mocked.get_next_pin()
    callback = Mock()
    with patch("RPi.GPIO", proxy):
        import custom_components.gpio_integration.gpio.__rpigpio as base

        base.GpioPin(
            pin, edge="rising", when_changed=callback, factory=base.GpioPinFactory()
        )

        proxy.trigger_event(pin, 1)

        callback.assert_called_once_with(1)
