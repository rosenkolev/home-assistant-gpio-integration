import pytest
from homeassistant.const import CONF_PORT

from custom_components.gpio_integration.number import GpioServo
from custom_components.gpio_integration.schemas import (
    CONF_DEFAULT_STATE,
    CONF_FREQUENCY,
    CONF_NAME,
)
from custom_components.gpio_integration.schemas.servo import (
    CONF_MAX_ANGLE,
    CONF_MAX_DUTY_CYCLE,
    CONF_MIN_ANGLE,
    CONF_MIN_DUTY_CYCLE,
    ServoConfig,
)
from tests.mocks import MockFactory, get_next_pin


class GpioServoTestCase:
    def __init__(self, factory: MockFactory):
        self.gpio = get_next_pin()
        self.pin = factory.pin(self.gpio)

    def create_config(
        self, default_angle=0, min=-90, min_cycle=1, max=90, max_cycle=2, frequency=100
    ):
        return ServoConfig(
            {
                CONF_NAME: "Test Servo",
                CONF_PORT: self.gpio,
                CONF_DEFAULT_STATE: default_angle,
                CONF_MIN_ANGLE: min,
                CONF_MIN_DUTY_CYCLE: min_cycle,
                CONF_MAX_ANGLE: max,
                CONF_MAX_DUTY_CYCLE: max_cycle,
                CONF_FREQUENCY: frequency,
            }
        )

    def assert_state(self, state):
        assert round(self.pin.state, 5) == state


def test__GpioServo_should_init(mocked_factory):
    tc = GpioServoTestCase(mocked_factory)
    with GpioServo(tc.create_config(frequency=100, min_cycle=3, max_cycle=7)) as gpio:
        assert gpio.native_value == 0
        assert gpio._attr_unique_id == "test_servo"
        assert gpio._attr_name == "Test Servo"
        assert gpio._attr_native_step == 1
        assert gpio._attr_native_unit_of_measurement == "°"

        assert tc.pin.frequency == 100
        assert tc.pin.state == 0.5

        assert gpio._io.min_angle == -90
        assert gpio._io.min_pulse_width == 0.003
        assert gpio._io.max_angle == 90
        assert gpio._io.max_pulse_width == 0.007


def test__GpioServo_should_set_angle(mocked_factory):
    tc = GpioServoTestCase(mocked_factory)
    with GpioServo(tc.create_config(min=0, max=180)) as gpio:
        gpio.set_native_value(0)
        tc.assert_state(0.1)

        gpio.set_native_value(45)
        tc.assert_state(0.125)

        gpio.set_native_value(90)
        tc.assert_state(0.15)

        gpio.set_native_value(117)
        tc.assert_state(0.165)

        gpio.set_native_value(180)
        tc.assert_state(0.2)


@pytest.mark.asyncio
async def test__GpioServo_will_close_pin(mocked_factory):
    tc = GpioServoTestCase(mocked_factory)
    gpio = GpioServo(tc.create_config())

    await gpio.async_will_remove_from_hass()

    assert tc.pin.closed is True
    assert gpio._io is None
