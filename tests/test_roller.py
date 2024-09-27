from unittest.mock import patch

import mocked_models as mocked
from homeassistant.const import CONF_MODE, CONF_PORT

import custom_components.gpio_integration.controllers.cover as hub
from custom_components.gpio_integration.schemas import (
    CONF_INVERT_LOGIC,
    CONF_NAME,
    CONF_PIN_CLOSED_SENSOR,
    CONF_RELAY_TIME,
)
from custom_components.gpio_integration.schemas.cover import ToggleRollerConfig


def __create_config(port=None, invert_logic=False, closed_sensor=0):
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
    pin_in = mocked.get_next_pin()
    pin_out = mocked.get_next_pin()
    with patch.object(hub, "create_pin", proxy.mock):
        hub.BasicToggleRoller(__create_config(port=pin_out, closed_sensor=pin_in))

        assert proxy.pins[pin_out].mode == "output"
        assert proxy.pins[pin_out].state is None
        assert proxy.pins[pin_in].mode == "input"


def test__Roller_should_open():
    proxy = mocked.MockedCreatePin()
    pin = mocked.get_next_pin()
    with patch.object(hub, "create_pin", proxy.mock):
        roller = hub.BasicToggleRoller(__create_config(port=pin))

        roller.toggle()

        assert proxy.pin.data["write"] == 1
