from unittest.mock import patch

import mocked_modules  # noqa: F401, E402


# Mock the Pin class
class MockPin:
    def __init__(
        self, pin, mode, pull, bounce, edges, frequency, default_value, when_changed
    ):
        self.pin = pin
        self.mode = mode
        self.pull = pull
        self.bounce = bounce
        self.edges = edges
        self.frequency = frequency
        self.default_value = default_value
        self.when_changed = when_changed


# Test the default pin factory
def test__create_pin_default_factory():
    import custom_components.gpio_integration.gpio.pigpio as base

    with patch.object(base, "GpioPin", MockPin):
        from custom_components.gpio_integration.gpio.pin_factory import create_pin

        pin = create_pin(
            1,
            mode="output",
            pull="up",
            bounce=0.1,
            edges="rising",
            frequency=50,
            default_value=True,
        )
        assert isinstance(pin, MockPin)
        assert pin.pin == 1
        assert pin.mode == "output"
        assert pin.pull == "up"
        assert pin.bounce == 0.1
        assert pin.edges == "rising"
        assert pin.frequency == 50
        assert pin.default_value is True
