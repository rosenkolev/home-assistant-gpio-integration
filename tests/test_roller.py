from unittest.mock import patch, Mock, ANY

import mocked_models as mocked

import custom_components.gpio_integration.hub as hub

from custom_components.gpio_integration.config_schema import (
    ToggleRollerConfig,
    CONF_NAME,
    CONF_PORT,
    CONF_MODE,
    CONF_RELAY_TIME,
    CONF_INVERT_LOGIC,
    CONF_PIN_CLOSED_SENSOR,
)


def __create_config(port=1, invert_logic=False, closed_sensor=0):
    return ToggleRollerConfig(
        {
            CONF_NAME: "Test Name",
            CONF_PORT: port,
            CONF_MODE: "Blind",
            CONF_INVERT_LOGIC: invert_logic,
            CONF_RELAY_TIME: 0.6,
            CONF_PIN_CLOSED_SENSOR: closed_sensor,
        }
    )


def test__Roller_should_init_default_sate():
    proxy = mocked.MockedCreatePin()
    with patch.object(hub, "create_pin", proxy.mock):
        roller = hub.BasicToggleRoller(__create_config(port=10, closed_sensor=11))

        assert proxy.pins[10].mode == "output"
        assert proxy.pins[10].state == None
        assert proxy.pins[11].mode == "input"


def test__Roller_should_open():
    proxy = mocked.MockedCreatePin()
    with patch.object(hub, "create_pin", proxy.mock):
        roller = hub.BasicToggleRoller(__create_config(port=20))

        roller.toggle()

        assert proxy.pin.data["write"] == True
