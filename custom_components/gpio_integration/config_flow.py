from __future__ import annotations

from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.core import callback

from .core import DOMAIN, get_logger
from .schemas import InvalidPin, get_unique_id
from .schemas.binary_sensor import (
    BINARY_SENSOR_SCHEMA,
    create_binary_sensor_schema,
    validate_binary_sensor_data,
)
from .schemas.cover import (
    COVER_TOGGLE_SCHEMA,
    COVER_UP_DOWN_SCHEMA,
    create_cover_up_down_schema,
    create_toggle_cover_schema,
    validate_cover_up_down_data,
    validate_toggle_cover_data,
)
from .schemas.fan import FAN_SCHEMA
from .schemas.light import LIGHT_SCHEMA
from .schemas.main import MAIN_SCHEMA, get_type
from .schemas.pwm import create_pwm_schema, validate_pwm_data
from .schemas.sensor import (
    ANALOG_SENSOR_SCHEMA,
    create_analog_sensor_schema,
    validate_analog_sensor_data,
)
from .schemas.switch import SWITCH_SCHEMA, create_switch_schema, validate_switch_data

_LOGGER = get_logger()

CONF_ENTITIES: dict = {
    "cover_up_down": {
        "schema": COVER_UP_DOWN_SCHEMA,
        "validate": validate_cover_up_down_data,
        "schema_builder": create_cover_up_down_schema,
    },
    "cover_toggle": {
        "schema": COVER_TOGGLE_SCHEMA,
        "validate": validate_toggle_cover_data,
        "schema_builder": create_toggle_cover_schema,
    },
    "binary_sensor": {
        "schema": BINARY_SENSOR_SCHEMA,
        "validate": validate_binary_sensor_data,
        "schema_builder": create_binary_sensor_schema,
    },
    "switch": {
        "schema": SWITCH_SCHEMA,
        "validate": validate_switch_data,
        "schema_builder": create_switch_schema,
    },
    "light": {
        "schema": LIGHT_SCHEMA,
        "validate": validate_pwm_data,
        "schema_builder": create_pwm_schema,
    },
    "fan": {
        "schema": FAN_SCHEMA,
        "validate": validate_pwm_data,
        "schema_builder": create_pwm_schema,
    },
    "analog_sensor": {
        "schema": ANALOG_SENSOR_SCHEMA,
        "validate": validate_analog_sensor_data,
        "schema_builder": create_analog_sensor_schema,
    },
}


def validate_config_data(entity_type: str, data_input: dict):
    try:
        CONF_ENTITIES[entity_type]["validate"](data_input)
    except InvalidPin:
        return {"base": "invalid_pin"}
    except Exception as e:  # pylint: disable=broad-except
        _LOGGER.exception("Unexpected exception: {}".format(e))
        return {"base": "unknown"}
    return None


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        type = get_type(user_input)
        _LOGGER.debug("config user, type: {}".format(type))
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
        elif type == "light":
            return await self.async_step_light()
        elif type == "fan":
            return await self.async_step_light()
        elif type == "analog_sensor":
            return await self.async_step_analog_sensor()

    async def async_step_cover_up_down(self, data_input=None):
        """Handle the initial step."""
        return await self.handle_config_data("cover_up_down", data_input)

    async def async_step_binary_sensor(self, data_input=None):
        """Handle the initial step."""
        return await self.handle_config_data("binary_sensor", data_input)

    async def async_step_switch(self, data_input=None):
        """Handle the initial step."""
        return await self.handle_config_data("switch", data_input)

    async def async_step_cover_toggle(self, data_input=None):
        """Handle the initial step."""
        return await self.handle_config_data("cover_toggle", data_input)

    async def async_step_light(self, data_input=None):
        """Handle the initial step."""
        return await self.handle_config_data("light", data_input)

    async def async_step_fan(self, data_input=None):
        """Handle the initial step."""
        return await self.handle_config_data("fan", data_input)

    async def async_step_analog_sensor(self, data_input=None):
        """Handle the initial step."""
        return await self.handle_config_data("analog_sensor", data_input)

    async def handle_config_data(self, id: str, data_input: dict | None):
        schema = CONF_ENTITIES[id]["schema"]
        if data_input is None:
            return self.async_show_form(step_id=id, data_schema=schema)

        errors = validate_config_data(id, data_input)
        if errors is None:
            data_input["type"] = id
            await self.async_set_unique_id(get_unique_id(data_input))
            return self.async_create_entry(title=data_input[CONF_NAME], data=data_input)

        return self.async_show_form(step_id=id, data_schema=schema, errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlowWithConfigEntry):
    """Handles options flow for the component."""

    async def async_step_init(self, user_input: dict | None = None):
        """Manage the options."""
        errors = {}
        data = self.config_entry.data
        unique_id = self.config_entry.unique_id
        if unique_id is None:
            unique_id = get_unique_id(data)

        entity_type = data.get("type")
        _LOGGER.debug("options init, type: {0}, id: {1}".format(entity_type, unique_id))

        if user_input is not None:
            # Handle the new options.
            # If the options are valid, update the config entry.
            user_input["type"] = entity_type
            user_input["unique_id"] = unique_id

            # validate the new options
            errors = validate_config_data(entity_type, user_input)
            if errors is None and self.hass is not None:
                result = self.hass.config_entries.async_update_entry(
                    entry=self.config_entry,
                    unique_id=unique_id,
                    title=user_input[CONF_NAME],
                    data=data,
                    options=self.options,
                )
                if result:
                    self.hass.config_entries.async_schedule_reload(
                        self.config_entry.entry_id
                    )

                return self.async_abort(reason="reconfigure successful")
        elif entity_type is not None:
            entity_info = CONF_ENTITIES.get(entity_type)
            if entity_info is None:
                errors["base"] = "unknown_type"
            else:
                data_clone = data.copy()
                data_clone["unique_id"] = unique_id or ""
                edit_schema = entity_info.get("schema_builder")(data_clone)

                return self.async_show_form(step_id="init", data_schema=edit_schema)
        else:
            errors["base"] = "unknown_type"

        return self.async_show_form(step_id="init", errors=errors)
