import sys
from unittest.mock import patch, Mock, ANY

import pytest

import mocked_models as mocked

from custom_components.gpio_integration.config_schema import (
    SensorConfig,
    CONF_NAME,
    CONF_PORT,
    CONF_MODE,
    CONF_BOUNCE_TIME,
    CONF_EDGE_EVENT_TIMEOUT,
    CONF_PULL_MODE,
    CONF_DEFAULT_STATE,
    CONF_INVERT_LOGIC,
)


def __create_config(port=1, default_state=False, invert_logic=False):
    return SensorConfig(
        {
            CONF_NAME: "Test Name",
            CONF_PORT: port,
            CONF_PULL_MODE: "up",
            CONF_MODE: "read",
            CONF_BOUNCE_TIME: 5,
            CONF_EDGE_EVENT_TIMEOUT: 10,
            CONF_DEFAULT_STATE: default_state,
            CONF_INVERT_LOGIC: invert_logic,
        }
    )


@patch(
    "homeassistant.components.binary_sensor.BinarySensorEntity", mocked.MockedBaseEntity
)
def test__GpioMotionBinarySensor_should_init_default_sate():
    from custom_components.gpio_integration.binary_sensor import GpioMotionBinarySensor

    gpio = GpioMotionBinarySensor(__create_config())

    assert gpio.is_on == False


@pytest.mark.asyncio
@patch(
    "homeassistant.components.binary_sensor.BinarySensorEntity", mocked.MockedBaseEntity
)
async def test__GpioMotionBinarySensor_edge_events_should_update_state():
    import custom_components.gpio_integration.binary_sensor as base

    with patch.object(base, "Gpio", mocked.MockedGpio):
        gpio = base.GpioMotionBinarySensor(__create_config())

        assert gpio.is_on == False

        await gpio._detect_edges()
        assert gpio.is_on == False
        assert gpio.ha_state_write == False

        mocked.mocked_gpio_data["read_events"] = [1]
        await gpio._detect_edges()
        assert gpio.is_on == True
        assert gpio.ha_state_write == True


@patch("time.perf_counter")
@patch(
    "homeassistant.components.binary_sensor.BinarySensorEntity", mocked.MockedBaseEntity
)
def test__GpioMotionBinarySensor_should_update_state_after_elapsed(counter: Mock):
    import custom_components.gpio_integration.binary_sensor as base

    with patch.object(base, "Gpio", mocked.MockedGpio):
        counter.return_value = 0
        gpio = base.GpioMotionBinarySensor(__create_config())

        counter.return_value = 1
        gpio.update()
        assert gpio.ha_state_write == False

        counter.return_value = 10.1
        gpio.update()
        assert gpio.ha_state_write == False

        gpio.on_edge_event()
        gpio.update()
        assert gpio.ha_state_write == True
