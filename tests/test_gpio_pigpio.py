from unittest.mock import Mock, patch

import mocked_models as mocked


class MockedPi:
    def __init__(self):
        self.pins = {}
        self._callback = None
        self._callback_id = 0

    @property
    def connected(self):
        return True

    def _pin(self, pin):
        return self.pins.setdefault(pin, dict())

    def set_mode(self, pin, mode):
        self._pin(pin)["mode"] = mode

    def set_pull_up_down(self, pin, pull):
        self._pin(pin)["pull"] = pull

    def set_glitch_filter(self, pin, glitch):
        self._pin(pin)["glitch"] = glitch

    def write(self, pin, state):
        self._pin(pin)["state"] = state

    def read(self, pin):
        return self._pin(pin).get("read", None)

    def set_PWM_dutycycle(self, pin, duty_cycle):
        self._pin(pin)["duty_cycle"] = duty_cycle

    def set_PWM_range(self, pin, range):
        self._pin(pin)["range"] = range

    def set_PWM_frequency(self, pin, frequency):
        self._pin(pin)["frequency"] = frequency

    def callback(self, pin, edge, callback):
        self._callback_id += 1
        self._callback = callback
        self._pin(pin)["edge"] = edge
        return self._callback_id


def test__pigpio_connect():
    """Test the pigpio module."""

    proxy = MockedPi()
    pin = mocked.get_next_pin()
    with patch("pigpio.pi", return_value=proxy):
        import custom_components.gpio_integration.gpio.pigpio as base

        base.GpioPin(pin, factory=base.GpioPinFactory())

        assert proxy.pins[pin]["mode"] == base.pigpio.INPUT
        assert proxy.pins[pin]["pull"] == base.pigpio.PUD_OFF
        assert proxy.pins[pin]["glitch"] == 0


def test__pigpio_set_default_value():
    proxy = MockedPi()
    pin = mocked.get_next_pin()
    with patch("pigpio.pi", return_value=proxy):
        import custom_components.gpio_integration.gpio.pigpio as base

        base.GpioPin(
            pin, mode="output", default_value=True, factory=base.GpioPinFactory()
        )

        assert proxy.pins[pin]["state"] == 1


def test__pigpio_set_frequency():
    proxy = MockedPi()
    pin = mocked.get_next_pin()
    with patch("pigpio.pi", return_value=proxy):
        import custom_components.gpio_integration.gpio.pigpio as base

        base.GpioPin(pin, mode="output", frequency=100, factory=base.GpioPinFactory())

        assert proxy.pins[pin]["state"] == 0
        assert proxy.pins[pin]["frequency"] == 100
        assert proxy.pins[pin]["range"] == 10000
        assert proxy.pins[pin]["duty_cycle"] == 0


def test__pigpio_edge_detection():
    proxy = MockedPi()
    pin = mocked.get_next_pin()
    callback = Mock()
    with patch("pigpio.pi", return_value=proxy):
        import custom_components.gpio_integration.gpio.pigpio as base

        base.GpioPin(
            pin, edge="rising", when_changed=callback, factory=base.GpioPinFactory()
        )

        assert proxy.pins[pin]["edge"] == base.pigpio.RISING_EDGE

        callback.assert_not_called()
        proxy._callback(1)

        callback.assert_called_once_with(1)
