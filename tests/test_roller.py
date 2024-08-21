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
    with patch.object(hub, "Gpio", mocked.MockedGpio):

        roller = hub.BasicToggleRoller(__create_config(port=10, closed_sensor=11))

        assert mocked.mocked_gpio[10]["mode"] == "write"
        assert mocked.mocked_gpio[10]["default_value"] == None
        assert mocked.mocked_gpio[11]["mode"] == "read"


def test__Roller_should_open():
    with patch.object(hub, "Gpio", mocked.MockedGpio):

        roller = hub.BasicToggleRoller(__create_config(port=20))

        roller.toggle()

        assert mocked.mocked_gpio[20]["write_value"] == True
