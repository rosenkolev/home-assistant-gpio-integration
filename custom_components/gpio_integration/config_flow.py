"""Config flow for GPIO integration."""

from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.core import callback

from .core import DOMAIN, get_logger
from .schemas import CONF_VARIATION, InvalidPin, get_unique_id
from .schemas.binary_sensor import (
    BINARY_SENSOR_SCHEMA,
    create_binary_sensor_schema,
    validate_binary_sensor_data,
)
from .schemas.cover import (
    COVER_TOGGLE_SCHEMA,
    COVER_UP_DOWN_SCHEMA,
    COVER_VARIATION_SCHEMA,
    create_cover_up_down_schema,
    create_cover_variation_schema,
    create_toggle_cover_schema,
    validate_cover_up_down_data,
    validate_cover_variation_data,
    validate_toggle_cover_data,
)
from .schemas.fan import FAN_SCHEMA
from .schemas.light import (
    LIGHT_SCHEMA,
    LIGHT_VARIATION_SCHEMA,
    RGB_LIGHT_SCHEMA,
    create_light_variation_schema,
    create_rgb_light_schema,
    validate_light_variation_data,
    validate_rgb_light_data,
)
from .schemas.main import MAIN_SCHEMA, EntityTypes, get_type
from .schemas.pwm import create_pwm_schema, validate_pwm_data
from .schemas.sensor import (
    SENSOR_DHT22_SCHEMA,
    SENSOR_VARIATION_SCHEMA,
    create_sensor_dht22_schema,
    create_sensor_variation_schema,
    validate_sensor_dht22_data,
    validate_sensor_variation_data,
)
from .schemas.switch import SWITCH_SCHEMA, create_switch_schema, validate_switch_data

_LOGGER = get_logger()

CONF_ENTITIES: dict = {
    EntityTypes.COVER: {
        "schema": COVER_VARIATION_SCHEMA,
        "validate": validate_cover_variation_data,
        "schema_builder": create_cover_variation_schema,
    },
    EntityTypes.COVER_UP_DOWN: {
        "schema": COVER_UP_DOWN_SCHEMA,
        "validate": validate_cover_up_down_data,
        "schema_builder": create_cover_up_down_schema,
    },
    EntityTypes.COVER_TOGGLE: {
        "schema": COVER_TOGGLE_SCHEMA,
        "validate": validate_toggle_cover_data,
        "schema_builder": create_toggle_cover_schema,
    },
    EntityTypes.BINARY_SENSOR: {
        "schema": BINARY_SENSOR_SCHEMA,
        "validate": validate_binary_sensor_data,
        "schema_builder": create_binary_sensor_schema,
    },
    EntityTypes.SWITCH: {
        "schema": SWITCH_SCHEMA,
        "validate": validate_switch_data,
        "schema_builder": create_switch_schema,
    },
    EntityTypes.LIGHT: {
        "schema": LIGHT_VARIATION_SCHEMA,
        "validate": validate_light_variation_data,
        "schema_builder": create_light_variation_schema,
    },
    EntityTypes.LIGHT_PWM_LED: {
        "schema": LIGHT_SCHEMA,
        "validate": validate_pwm_data,
        "schema_builder": create_pwm_schema,
    },
    EntityTypes.LIGHT_RGB_LED: {
        "schema": RGB_LIGHT_SCHEMA,
        "validate": validate_rgb_light_data,
        "schema_builder": create_rgb_light_schema,
    },
    EntityTypes.FAN: {
        "schema": FAN_SCHEMA,
        "validate": validate_pwm_data,
        "schema_builder": create_pwm_schema,
    },
    EntityTypes.SENSOR: {
        "schema": SENSOR_VARIATION_SCHEMA,
        "validate": validate_sensor_variation_data,
        "schema_builder": create_sensor_variation_schema,
    },
    EntityTypes.SENSOR_DHT22: {
        "schema": SENSOR_DHT22_SCHEMA,
        "validate": validate_sensor_dht22_data,
        "schema_builder": create_sensor_dht22_schema,
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


VARIATION_STEP_ENTITIES = [
    EntityTypes.COVER,
    EntityTypes.LIGHT,
    EntityTypes.SENSOR,
]
SINGLE_STEP_ENTITIES = [
    EntityTypes.BINARY_SENSOR,
    EntityTypes.SWITCH,
    EntityTypes.FAN,
]


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        type = get_type(user_input)
        _LOGGER.debug("config user, type: {}".format(type))
        if type is None:
            return self.async_show_form(step_id="user", data_schema=MAIN_SCHEMA)
        elif type in SINGLE_STEP_ENTITIES:
            return await self.async_step_common_setup(data_input=None, schema_id=type)
        elif type in VARIATION_STEP_ENTITIES:
            return await self.async_step_select_variation(
                data_input=None, schema_id=type
            )

        return self.async_abort(reason="unknown_type")

    async def async_step_common_setup(
        self, data_input=None, errors=None, schema_id: str | None = None
    ):
        """Handle the generic setup step."""
        schema = CONF_ENTITIES[schema_id]["schema"]
        if data_input is None:
            return self.async_show_form(step_id="common_setup", data_schema=schema)

        errors = validate_config_data(schema_id, data_input)
        if errors is None:
            data_input["type"] = schema_id
            await self.async_set_unique_id(get_unique_id(data_input))
            return self.async_create_entry(title=data_input[CONF_NAME], data=data_input)

        return self.async_show_form(
            step_id="common_setup", data_schema=schema, errors=errors
        )

    async def async_step_select_variation(
        self, data_input=None, schema_id: str | None = None
    ):
        """Handle the generic setup step."""
        schema = CONF_ENTITIES[schema_id]["schema"]
        if data_input is None:
            return self.async_show_form(step_id="select_variation", data_schema=schema)

        errors = validate_config_data(schema_id, data_input)
        if errors is not None:
            return self.async_show_form(
                step_id="select_variation", data_schema=schema, errors=errors
            )

        variation = data_input[CONF_VARIATION]
        _LOGGER.debug(f"config type: {schema_id}, variation: {variation}")
        return await self.async_step_common_setup(data_input=None, schema_id=variation)

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
