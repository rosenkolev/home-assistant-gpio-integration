from typing import Literal
import voluptuous as vol

from .const import DOMAIN
from .io_interface import get_logger

import homeassistant.helpers.config_validation as cv
from homeassistant import config_entries, exceptions
from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_NAME

_LOGGER = get_logger()

CONF_COVERS = "covers"
CONF_RELAY_UP_PIN = "up_pin"
CONF_RELAY_UP_INVERT = "up_pin_invert"
CONF_RELAY_DOWN_PIN = "down_pin"
CONF_RELAY_DOWN_INVERT = "down_pin_invert"
CONF_RELAY_TIME = "relay_time"
CONF_PIN_CLOSED_SENSOR = "pin_closed_sensor"
DEFAULT_INVERT_RELAY = False
DEFAULT_RELAY_TIME = 15

DATA_SCHEMA = vol.Schema({
    vol.Required(CONF_NAME): cv.string,
    vol.Required(CONF_RELAY_UP_PIN): cv.positive_int,
    vol.Optional(CONF_RELAY_UP_INVERT, default=DEFAULT_INVERT_RELAY): cv.boolean,
    vol.Required(CONF_RELAY_DOWN_PIN): cv.positive_int,
    vol.Optional(CONF_RELAY_DOWN_INVERT, default=DEFAULT_INVERT_RELAY): cv.boolean,
    vol.Optional(CONF_RELAY_TIME, default=DEFAULT_RELAY_TIME): cv.positive_int,
    vol.Optional(CONF_PIN_CLOSED_SENSOR, default=None): int,
})

class RollerConfig():
    def __init__(self, data: dict):
        self.name: str = data[CONF_NAME]
        self.pin_up: int = data[CONF_RELAY_UP_PIN]
        self.pin_up_on_state: Literal['high', 'low'] = 'high' if data[CONF_RELAY_UP_INVERT] else 'low'
        self.pin_down: int = data[CONF_RELAY_DOWN_PIN]
        self.pin_down_on_state: Literal['high', 'low'] = 'high' if data[CONF_RELAY_DOWN_INVERT] else 'low'
        self.relay_time: int = data[CONF_RELAY_TIME]
        self.pin_closed: int | None = data[CONF_PIN_CLOSED_SENSOR]
        self.pin_closed_on_state: Literal['high','low'] = 'high'
        self.pin_closed_mode: Literal['up','down'] = 'up'
        self.unique_id: str = self.name.lower().replace(' ', '_')

        if self.pin_closed <= 0:
            self.pin_closed = None

def validate_input(data: dict):
    """Validate the user input allows us to connect."""
    if data["up_pin"] < 1 or data["down_pin"] < 1:
        raise InvalidPin

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Hello World."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        if user_input is None:
            return self.async_show_form(step_id="user", data_schema=DATA_SCHEMA)

        try:
            validate_input(user_input)
        except Exception as e:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception: {}".format(e))
            errors["base"] = "unknown"
        else:

            return self.async_create_entry(title=user_input[CONF_NAME], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )

    # async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None):
    #     if user_input is not None:
    #         entry = self.hass.config_entries.async_get_entry(config_entry_id)
    #         return self.async_update_reload_and_abort(entry= , title=user_input[CONF_NAME], data=user_input)

    #     return self.async_show_form(
    #         step_id="reconfigure", data_schema=DATA_SCHEMA))

class InvalidPin(exceptions.HomeAssistantError):
    """Error to indicate invalid pin."""
