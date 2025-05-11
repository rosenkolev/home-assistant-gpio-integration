import pytest
from homeassistant.const import CONF_PORT

from custom_components.gpio_integration.number import GpioServo
from custom_components.gpio_integration.schemas import CONF_DEFAULT_STATE, CONF_NAME
from custom_components.gpio_integration.schemas.servo import (
    CONF_MAX_ANGLE,
    CONF_MIN_ANGLE,
    ServoConfig,
)
from tests.mocks import MockFactory, get_next_pin


class GpioServoTestCase:
    def __init__(self, factory: MockFactory):
        self.gpio = get_next_pin()
        self.pin = factory.pin(self.gpio)

    def create_config(self, default_angle=0, min=-90, max=90):
        return ServoConfig(
            {
                CONF_NAME: "Test Servo",
                CONF_PORT: self.gpio,
                CONF_DEFAULT_STATE: default_angle,
                CONF_MIN_ANGLE: min,
                CONF_MAX_ANGLE: max,
            }
        )


def test__GpioServo_should_init(mocked_factory):
    tc = GpioServoTestCase(mocked_factory)
    with GpioServo(tc.create_config()) as gpio:
        assert gpio.native_value == 0
        assert gpio._attr_unique_id == "test_servo"
        assert gpio._attr_name == "Test Servo"
        assert gpio._attr_native_step == 1
        assert gpio._attr_native_unit_of_measurement == "°"
