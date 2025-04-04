"""Schema for GPIO outputs using Pulse-Wide Modulation PWM."""

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.const import CONF_NAME, CONF_PORT, CONF_UNIQUE_ID

from . import CONF_DEFAULT_STATE, CONF_FREQUENCY, CONF_INVERT_LOGIC, get_unique_id
from ._validators import v_name, v_pin


def create_pwm_schema(data: dict) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_NAME, default=data[CONF_NAME]): cv.string,
            vol.Required(
                CONF_PORT,
                default=data[CONF_PORT],
                description={"comment": "GPIO pin number for the switch"},
            ): cv.positive_int,
            vol.Optional(
                CONF_FREQUENCY,
                default=data[CONF_FREQUENCY],
                description={"comment": "The light pulse frequency (for LED)"},
            ): cv.positive_int,
            vol.Optional(
                CONF_DEFAULT_STATE,
                default=data[CONF_DEFAULT_STATE],
                description={"comment": "Default state"},
            ): cv.boolean,
            vol.Optional(
                CONF_INVERT_LOGIC,
                default=data[CONF_INVERT_LOGIC],
                description={"comment": "Invert the logic of the output (low = on)"},
            ): cv.boolean,
            vol.Optional(CONF_UNIQUE_ID, default=data[CONF_UNIQUE_ID]): cv.string,
        }
    )


def validate_pwm_data(data):
    return v_name(data[CONF_NAME]) and v_pin(data[CONF_PORT])


class PwmConfig:
    def __init__(self, data: dict):
        self.name: str = data[CONF_NAME]
        self.port: int = data[CONF_PORT]
        self.frequency: int = data[CONF_FREQUENCY]
        self.default_state: bool = data[CONF_DEFAULT_STATE]
        if CONF_INVERT_LOGIC in data:
            self.invert_logic: bool = data[CONF_INVERT_LOGIC]
        else:
            self.invert_logic: bool = False
        self.unique_id: str = get_unique_id(data)
