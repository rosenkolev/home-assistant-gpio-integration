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
def test__GpioBinarySensor_should_init_default_sate():
    from custom_components.gpio_integration.binary_sensor import GpioBinarySensor

    gpio = GpioBinarySensor(__create_config())

    assert gpio.is_on == False


@patch(
    "homeassistant.components.binary_sensor.BinarySensorEntity", mocked.MockedBaseEntity
)
def test__GpioBinarySensor_update_should_set_state_not_inverted():
    import custom_components.gpio_integration.binary_sensor as base

    with patch.object(base, "Gpio", mocked.MockedGpio):
        gpio = base.GpioBinarySensor(__create_config(port=13))

        mocked.mocked_gpio_data["read_value"] = True
        gpio.update()
        assert gpio.is_on == True

        mocked.mocked_gpio_data["read_value"] = False
        gpio.update()
        assert gpio.is_on == False


@patch(
    "homeassistant.components.binary_sensor.BinarySensorEntity", mocked.MockedBaseEntity
)
def test__GpioBinarySensor_update_should_set_state_inverted():
    import custom_components.gpio_integration.binary_sensor as base

    with patch.object(base, "Gpio", mocked.MockedGpio):
        gpio = base.GpioBinarySensor(__create_config(invert_logic=True))

        mocked.mocked_gpio_data["read_value"] = True
        gpio.update()
        assert gpio.is_on == False

        mocked.mocked_gpio_data["read_value"] = False
        gpio.update()
        assert gpio.is_on == True


@pytest.mark.asyncio
@patch(
    "homeassistant.components.binary_sensor.BinarySensorEntity", mocked.MockedBaseEntity
)
async def test__GpioBinarySensor_edge_events_should_trigger_update():
    import custom_components.gpio_integration.binary_sensor as base

    with patch.object(base, "Gpio", mocked.MockedGpio):
        gpio = base.GpioBinarySensor(__create_config())

        await gpio._detect_edges()
        assert gpio.ha_state_update_scheduled == False

        mocked.mocked_gpio_data["read_events"] = [1]
        await gpio._detect_edges()
        assert gpio.ha_state_update_scheduled == True
