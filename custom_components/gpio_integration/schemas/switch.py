"""Schema for the Switch entity."""

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.const import (
    CONF_NAME,
    CONF_PORT,
    CONF_UNIQUE_ID,
)

from . import CONF_DEFAULT_STATE, CONF_INVERT_LOGIC, get_unique_id
from ._validators import v_name, v_pin


def create_switch_schema(data: dict) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_NAME, default=data[CONF_NAME]): cv.string,
            vol.Required(
                CONF_PORT,
                default=data[CONF_PORT],
                description={"comment": "GPIO pin number for the switch"},
            ): cv.positive_int,
            vol.Optional(
                CONF_INVERT_LOGIC,
                default=data[CONF_INVERT_LOGIC],
                description={"comment": "Invert the logic of the switch"},
            ): cv.boolean,
            vol.Optional(
                CONF_DEFAULT_STATE,
                default=data[CONF_DEFAULT_STATE],
                description={"comment": "Default state of the switch"},
            ): cv.boolean,
            vol.Optional(CONF_UNIQUE_ID, default=data[CONF_UNIQUE_ID]): cv.string,
        }
    )


SWITCH_SCHEMA = create_switch_schema(
    {
        CONF_NAME: None,
        CONF_PORT: None,
        CONF_INVERT_LOGIC: False,
        CONF_DEFAULT_STATE: False,
        CONF_UNIQUE_ID: "",
    }
)


def validate_switch_data(data):
    return v_name(data[CONF_NAME]) and v_pin(data[CONF_PORT])


class SwitchConfig:
    """Switch configuration schema."""

    def __init__(self, data: dict):
        self.name: str = data[CONF_NAME]
        self.port: int = data[CONF_PORT]
        self.invert_logic: bool = data[CONF_INVERT_LOGIC]
        self.default_state: bool = data[CONF_DEFAULT_STATE]
        self.unique_id: str = get_unique_id(data)
