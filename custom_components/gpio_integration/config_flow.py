from __future__ import annotations

from typing import Literal

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


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Hello World."""

    VERSION = 1

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
        return self.__async_inner_handler(
            "cover_up_down", COVER_UP_DOWN_SCHEMA, validate_cover_up_down, data_input
        )

    async def async_step_binary_sensor(self, data_input=None):
        """Handle the initial step."""
        return self.__async_inner_handler(
            "binary_sensor", SENSOR_SCHEMA, validate_sensor, data_input
        )

    async def async_step_switch(self, data_input=None):
        """Handle the initial step."""
        return self.__async_inner_handler(
            "switch", SWITCH_SCHEMA, validate_switch, data_input
        )

    async def async_step_cover_toggle(self, data_input=None):
        """Handle the initial step."""
        return self.__async_inner_handler(
            "cover_toggle", COVER_TOGGLE_SCHEMA, validate_cover_toggle, data_input
        )

    def __async_inner_handler(
        self,
        step_id: str,
        schema,
        validate_fn,
        data_input: dict = None,
        title_key: str = "name",
    ):
        errors = {}
        if data_input is None:
            return self.async_show_form(step_id=step_id, data_schema=schema)

        try:
            validate_fn(data_input)
        except InvalidPin:
            errors["base"] = "invalid_pin"
        except Exception as e:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception: {}".format(e))
            errors["base"] = "unknown"
        else:
            data_input["type"] = step_id
            return self.async_create_entry(title=data_input[title_key], data=data_input)

        return self.async_show_form(step_id=step_id, data_schema=schema, errors=errors)

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

    async def async_step_init(self, user_input=None):
        errors = {}

        if user_input is not None:
            self.type = user_input["type"]
            if self.type == "cover_up_down":
                return await self.async_step_edit()

        _LOGGER.info("Type: {}".format(user_input))
        errors["base"] = "unknown"
        return self.async_show_form(step_id="init", errors=errors)

    async def async_step_edit(self, user_input=None):
        """Manage the options for the custom component."""
        errors = {}

        # vacuums = self.config_entry.data[CONF_VACS]

        # if user_input is not None:
        #     updated_vacuums = deepcopy(vacuums)
        #     updated_vacuums[self.selected_vacuum][CONF_AUTODISCOVERY] = user_input[
        #         CONF_AUTODISCOVERY
        #     ]
        #     if user_input[CONF_IP_ADDRESS]:
        #         updated_vacuums[self.selected_vacuum][CONF_IP_ADDRESS] = user_input[
        #             CONF_IP_ADDRESS
        #         ]

        #     self.hass.config_entries.async_update_entry(
        #         self.config_entry,
        #         data={CONF_VACS: updated_vacuums},
        #     )

        #     return self.async_create_entry(title="", data={})
        return self.async_create_entry(title="", data={})

        # options_schema = vol.Schema(
        #     {
        #         vol.Required(
        #             CONF_AUTODISCOVERY,
        #             default=vacuums[self.selected_vacuum].get(CONF_AUTODISCOVERY, True),
        #         ): bool,
        #         vol.Optional(
        #             CONF_IP_ADDRESS,
        #             default=vacuums[self.selected_vacuum].get(CONF_IP_ADDRESS),
        #         ): str,
        #     }
        # )

        # return self.async_show_form(
        #     step_id="edit", data_schema=options_schema, errors=errors
        # )
