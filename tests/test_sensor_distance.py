import pytest
from homeassistant.const import CONF_PORT

from custom_components.gpio_integration.controllers.sensor import DistanceController
from custom_components.gpio_integration.schemas import CONF_NAME, CONF_PIN_TRIGGER
from custom_components.gpio_integration.schemas.sensor import (
    CONF_MAX_DISTANCE,
    DistanceSensorConfig,
)
from custom_components.gpio_integration.sensor import GpioSensor
from tests.mocks import MockFactory, MockGpioZeroDevice, get_next_pin


class GpioServoTestCase:
    def __init__(self, factory: MockFactory):
        self.gpio_echo = get_next_pin()
        self.gpio_trigger = get_next_pin()
        self.pin_echo = factory.pin(self.gpio_echo)
        self.pin_trigger = factory.pin(self.gpio_trigger)
        self.create = lambda max_distance=1: DistanceSensorConfig(
            {
                CONF_NAME: "Test Distance",
                CONF_PORT: self.gpio_echo,
                CONF_PIN_TRIGGER: self.gpio_trigger,
                CONF_MAX_DISTANCE: max_distance,
            }
        )


def test__Distance_should_init_default_state(mocked_factory):
    tc = GpioServoTestCase(mocked_factory)
    ctrl = DistanceController(tc.create())
    with GpioSensor(ctrl.get_sensors()[0]) as gpio:
        with MockGpioZeroDevice(ctrl._io, 0.0):
            assert gpio.native_value == 0.0
            assert gpio._attr_name == "Test Distance"
            assert gpio._attr_unique_id == "test_distance"
            assert gpio._attr_native_unit_of_measurement == "m"
            assert gpio._attr_device_class == "distance"

            assert tc.pin_echo._function == "input"
            assert tc.pin_trigger._function == "output"


def test__Distance_should_get_value(mocked_factory):
    tc = GpioServoTestCase(mocked_factory)
    ctrl = DistanceController(tc.create(2))
    with GpioSensor(ctrl.get_sensors()[0]) as gpio:
        with MockGpioZeroDevice(ctrl._io, 0.6) as md:
            assert gpio.native_value == 1.2

            md.value = 0.9
            assert gpio.native_value == 1.8


@pytest.mark.asyncio
async def test__Distance_will_close_pin(mocked_factory):
    tc = GpioServoTestCase(mocked_factory)
    ctrl = DistanceController(tc.create())
    gpio = GpioSensor(ctrl.get_sensors()[0])

    await gpio.async_will_remove_from_hass()

    assert tc.pin_echo.closed is True
    assert tc.pin_trigger.closed is True
    assert gpio._io is None
