from __future__ import annotations

from typing import Callable, Any

from homeassistant import config_entries, exceptions
from homeassistant.const import CONF_NAME, CONF_PORT
from homeassistant.core import callback

from .const import DOMAIN
from .io_interface import get_logger
from .config_schema import (
    get_type,
    MAIN_SCHEMA,
    COVER_UP_DOWN_SCHEMA,
    COVER_TOGGLE_SCHEMA,
    SENSOR_SCHEMA,
    SWITCH_SCHEMA,
    CONF_RELAY_UP_PIN,
    CONF_RELAY_DOWN_PIN,
)

_LOGGER = get_logger()


def validate_cover_up_down(data: dict):
    if data[CONF_NAME] == None or data[CONF_NAME] == "":
        raise ValueError("Name is required")
    if data[CONF_RELAY_UP_PIN] < 1 or data[CONF_RELAY_DOWN_PIN] < 1:
        raise InvalidPin


def validate_sensor(data: dict):
    if data[CONF_NAME] == None or data[CONF_NAME] == "":
        raise ValueError("Name is required")
    if data[CONF_PORT] < 1:
        raise InvalidPin


def validate_switch(data: dict):
    if data[CONF_NAME] == None or data[CONF_NAME] == "":
        raise ValueError("Name is required")
    if data[CONF_PORT] < 1:
        raise InvalidPin


def validate_cover_toggle(data: dict):
    if data[CONF_NAME] == None or data[CONF_NAME] == "":
        raise ValueError("Name is required")
    if data[CONF_PORT] < 1:
        raise InvalidPin


CONF_ENTITIES: dict = {
    "cover_up_down": {
        "schema": COVER_UP_DOWN_SCHEMA,
        "validate": validate_cover_up_down,
    },
    "cover_toggle": {"schema": COVER_TOGGLE_SCHEMA, "validate": validate_cover_toggle},
    "binary_sensor": {"schema": SENSOR_SCHEMA, "validate": validate_sensor},
    "switch": {"schema": SWITCH_SCHEMA, "validate": validate_switch},
}


def async_validate_config_data(
    entity_type: str,
    data_input: dict,
    show_form_fn: Callable[[str, Any | None, dict], None],
    add_update_fn: Callable[[str, dict], None],
):
    errors = {}
    schema = CONF_ENTITIES[entity_type]["schema"]
    if data_input is None:
        return show_form_fn(entity_type, schema, None)
    try:
        CONF_ENTITIES[entity_type]["validate"](data_input)
    except InvalidPin:
        errors["base"] = "invalid_pin"
    except Exception as e:  # pylint: disable=broad-except
        _LOGGER.exception("Unexpected exception: {}".format(e))
        errors["base"] = "unknown"
    else:
        return add_update_fn(data_input[CONF_NAME], data_input)

    return show_form_fn(entity_type, schema, errors)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Hello World."""

    VERSION = 1

    def show_form_fn(self, entity_type: str, schema: Any | None, errors: dict):
        return self.async_show_form(
            step_id=entity_type,
            data_schema=schema,
            errors=errors,
        )

    def add_update_fn(self, title: str, data: dict):
        return self.async_create_entry(title=title, data=data)

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        type = get_type(user_input)
        _LOGGER.info("step user, type: {}".format(type))
        if type is None:
            return self.async_show_form(step_id="user", data_schema=MAIN_SCHEMA)
        elif type == "cover_up_down":
            return await self.async_step_cover_up_down()
        elif type == "cover_toggle":
            return await self.async_step_cover_toggle()
        elif type == "binary_sensor":
            return await self.async_step_binary_sensor()
        elif type == "switch":
            return await self.async_step_switch()

    async def async_step_cover_up_down(self, data_input=None):
        """Handle the initial step."""
        return async_validate_config_data(
            "cover_up_down", data_input, self.show_form_fn, self.add_update_fn
        )

    async def async_step_binary_sensor(self, data_input=None):
        """Handle the initial step."""
        return async_validate_config_data(
            "binary_sensor", data_input, self.show_form_fn, self.add_update_fn
        )

    async def async_step_switch(self, data_input=None):
        """Handle the initial step."""
        return async_validate_config_data(
            "switch", data_input, self.show_form_fn, self.add_update_fn
        )

    async def async_step_cover_toggle(self, data_input=None):
        """Handle the initial step."""
        return async_validate_config_data(
            "cover_toggle", data_input, self.show_form_fn, self.add_update_fn
        )

    # async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None):
    #     if user_input is not None:
    #         entry = self.hass.config_entries.async_get_entry(config_entry_id)
    #         return self.async_update_reload_and_abort(entry= , title=user_input[CONF_NAME], data=user_input)

    #     return self.async_show_form(
    #         step_id="reconfigure", data_schema=DATA_SCHEMA))

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return OptionsFlowHandler(config_entry)


class InvalidPin(exceptions.HomeAssistantError):
    """Error to indicate invalid pin."""


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handles options flow for the component."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    def show_form_fn(self, entity_type: str, schema: Any | None, errors: dict):
        return self.async_show_form(
            step_id=entity_type,
            data_schema=schema,
            errors=errors,
        )

    def add_update_fn(self, title: str, data: dict):
        return self.hass.config_entries.async_update_entry(
            self.config_entry,
            data=data,
        )

    async def async_step_init(self, user_input=None):
        errors = {}
        data = self.config_entry.options
        _LOGGER.info("Type: {0} {1}".format(self.config_entry, user_input))

        entity_type = data["type"]
        if entity_type is None:
            return self.async_show_form(step_id="init", errors=errors)
        elif entity_type == "cover_up_down":
            return await self.async_step_cover_up_down(data)
        elif entity_type == "cover_toggle":
            return await self.async_step_cover_toggle(data)
        elif entity_type == "binary_sensor":
            return await self.async_step_binary_sensor(data)
        elif entity_type == "switch":
            return await self.async_step_switch(data)
        else:
            errors["base"] = "unknown"

        return self.async_show_form(step_id="init", errors=errors)

    async def async_step_cover_up_down(self, data_input=None):
        """Handle the initial step."""
        return async_validate_config_data(
            "cover_up_down", data_input, self.show_form_fn, self.add_update_fn
        )

    async def async_step_binary_sensor(self, data_input=None):
        """Handle the initial step."""
        return async_validate_config_data(
            "binary_sensor", data_input, self.show_form_fn, self.add_update_fn
        )

    async def async_step_switch(self, data_input=None):
        """Handle the initial step."""
        return async_validate_config_data(
            "switch", data_input, self.show_form_fn, self.add_update_fn
        )

    async def async_step_cover_toggle(self, data_input=None):
        """Handle the initial step."""
        return async_validate_config_data(
            "cover_toggle", data_input, self.show_form_fn, self.add_update_fn
        )
