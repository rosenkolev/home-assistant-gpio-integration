from unittest.mock import patch

import mocked_modules
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


def __create_config(port=None, default_state=False, invert_logic=False):
    return SensorConfig(
        {
            CONF_NAME: "Test Name",
            CONF_PORT: mocked.get_next_pin() if port is None else port,
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
def test__GpioBinarySensor_should_init_default_state():
    import custom_components.gpio_integration.binary_sensor as base

    pin = mocked.get_next_pin()
    create_pin = mocked.MockedCreatePin()
    with patch.object(base, "create_pin", create_pin.mock):
        gpio = base.GpioBinarySensor(__create_config(port=pin))

        assert gpio.is_on == False
        assert create_pin.pin.pin == pin


@patch(
    "homeassistant.components.binary_sensor.BinarySensorEntity", mocked.MockedBaseEntity
)
def test__GpioBinarySensor_update_should_set_state_not_inverted():
    import custom_components.gpio_integration.binary_sensor as base

    proxy = mocked.MockedCreatePin()
    with patch.object(base, "create_pin", proxy.mock):
        gpio = base.GpioBinarySensor(__create_config())

        proxy.pin.data["read"] = True
        gpio.update()
        assert gpio.is_on == True

        proxy.pin.data["read"] = False
        gpio.update()
        assert gpio.is_on == False


@patch(
    "homeassistant.components.binary_sensor.BinarySensorEntity", mocked.MockedBaseEntity
)
def test__GpioBinarySensor_update_should_set_state_inverted():
    import custom_components.gpio_integration.binary_sensor as base

    proxy = mocked.MockedCreatePin()
    with patch.object(base, "create_pin", proxy.mock):
        gpio = base.GpioBinarySensor(__create_config(invert_logic=True))

        proxy.pin.data["read"] = True
        gpio.update()
        assert gpio.is_on == False

        proxy.pin.data["read"] = False
        gpio.update()
        assert gpio.is_on == True


@patch(
    "homeassistant.components.binary_sensor.BinarySensorEntity", mocked.MockedBaseEntity
)
def test__GpioBinarySensor_edge_events_should_trigger_update():
    import custom_components.gpio_integration.binary_sensor as base

    proxy = mocked.MockedCreatePin()
    with patch.object(base, "create_pin", proxy.mock):
        gpio = base.GpioBinarySensor(__create_config())

        proxy.pin._call_when_changed(0)
        assert gpio.ha_state_update_scheduled == True
