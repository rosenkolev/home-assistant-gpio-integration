"""Config flow for GPIO integration."""

from enum import Enum

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.core import callback

from .core import DOMAIN, get_logger
from .schemas import CONF_VARIATION, InvalidPin, get_unique_id
from .schemas.binary_sensor import (
    BINARY_SENSOR_SCHEMA,
    validate_binary_sensor_data,
)
from .schemas.cover import (
    COVER_TOGGLE_SCHEMA,
    COVER_UP_DOWN_SCHEMA,
    COVER_VARIATION_SCHEMA,
    validate_cover_up_down_data,
    validate_cover_variation_data,
    validate_toggle_cover_data,
)
from .schemas.fan import FAN_SCHEMA
from .schemas.light import (
    LIGHT_SCHEMA,
    LIGHT_VARIATION_SCHEMA,
    RGB_LIGHT_SCHEMA,
    validate_light_variation_data,
    validate_rgb_light_data,
)
from .schemas.main import MAIN_SCHEMA, EntityTypes, get_type
from .schemas.pwm import validate_pwm_data
from .schemas.sensor import (
    SENSOR_ANALOG_STEP_SCHEMA,
    SENSOR_DHT22_SCHEMA,
    SENSOR_DISTANCE_SCHEMA,
    SENSOR_VARIATION_SCHEMA,
    validate_sensor_analog_step_data,
    validate_sensor_dht22_data,
    validate_sensor_distance_data,
    validate_sensor_variation_data,
)
from .schemas.servo import SERVO_SCHEMA, validate_servo_data
from .schemas.switch import SWITCH_SCHEMA, validate_switch_data

_LOGGER = get_logger()

CONF_ENTITIES: dict = {
    EntityTypes.COVER.value: {
        "schema": COVER_VARIATION_SCHEMA,
        "validate": validate_cover_variation_data,
    },
    EntityTypes.COVER_UP_DOWN.value: {
        "schema": COVER_UP_DOWN_SCHEMA,
        "validate": validate_cover_up_down_data,
    },
    EntityTypes.COVER_TOGGLE.value: {
        "schema": COVER_TOGGLE_SCHEMA,
        "validate": validate_toggle_cover_data,
    },
    EntityTypes.BINARY_SENSOR.value: {
        "schema": BINARY_SENSOR_SCHEMA,
        "validate": validate_binary_sensor_data,
    },
    EntityTypes.SWITCH.value: {
        "schema": SWITCH_SCHEMA,
        "validate": validate_switch_data,
    },
    EntityTypes.LIGHT.value: {
        "schema": LIGHT_VARIATION_SCHEMA,
        "validate": validate_light_variation_data,
    },
    EntityTypes.LIGHT_PWM_LED.value: {
        "schema": LIGHT_SCHEMA,
        "validate": validate_pwm_data,
    },
    EntityTypes.LIGHT_RGB_LED.value: {
        "schema": RGB_LIGHT_SCHEMA,
        "validate": validate_rgb_light_data,
    },
    EntityTypes.FAN.value: {
        "schema": FAN_SCHEMA,
        "validate": validate_pwm_data,
    },
    EntityTypes.SENSOR.value: {
        "schema": SENSOR_VARIATION_SCHEMA,
        "validate": validate_sensor_variation_data,
    },
    EntityTypes.SENSOR_DHT22.value: {
        "schema": SENSOR_DHT22_SCHEMA,
        "validate": validate_sensor_dht22_data,
    },
    EntityTypes.SENSOR_ANALOG_STEP.value: {
        "schema": SENSOR_ANALOG_STEP_SCHEMA,
        "validate": validate_sensor_analog_step_data,
    },
    EntityTypes.SENSOR_DISTANCE.value: {
        "schema": SENSOR_DISTANCE_SCHEMA,
        "validate": validate_sensor_distance_data,
    },
    EntityTypes.SERVO.value: {
        "schema": SERVO_SCHEMA,
        "validate": validate_servo_data,
    },
}


def fill_schema_missing_values(type: EntityTypes, configs: dict):
    """
    If we have config and a valid type, then try to
    add in any missing optional values from the base
    schema.
    """
    base_schema = CONF_ENTITIES[type.value]["schema"]
    if isinstance(base_schema.schema, dict):
        for key in base_schema.schema.keys():
            # Skip anything not an optional key
            if not isinstance(key, vol.Optional):
                continue

            # If not present in config data, copy in default
            if key.schema not in configs:
                defVal = key.default()
                _LOGGER.debug(
                    'Hub: setting missing default for config "%s" to value "%s"',
                    key.schema,
                    defVal,
                )

                configs.setdefault(key.schema, defVal)


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
    EntityTypes.COVER.value,
    EntityTypes.LIGHT.value,
    EntityTypes.SENSOR.value,
]
SINGLE_STEP_ENTITIES = [
    EntityTypes.BINARY_SENSOR.value,
    EntityTypes.SWITCH.value,
    EntityTypes.FAN.value,
    EntityTypes.SERVO.value,
]


class StepTypes(Enum):
    Setup = "setup"
    Variation = "variation"


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        type = get_type(user_input)
        _LOGGER.debug("config user, type: {}".format(type))
        if type is None:
            return self.async_show_form(step_id="user", data_schema=MAIN_SCHEMA)

        self.type = type
        if type in SINGLE_STEP_ENTITIES:
            return await self.async_step_common_setup(data_input=None)
        elif type in VARIATION_STEP_ENTITIES:
            return await self.async_step_select_variation(data_input=None)

        return self.async_abort(reason="unknown_type")

    async def async_step_common_setup(self, data_input=None):
        return await self.async_handle_generic_config_steps(
            "common_setup", StepTypes.Setup, data_input
        )

    async def async_step_select_variation(self, data_input=None):
        return await self.async_handle_generic_config_steps(
            "select_variation", StepTypes.Variation, data_input
        )

    async def async_handle_generic_config_steps(
        self, id, step_type: StepTypes, data_input=None
    ):
        """Handle a flow initialized by the user."""
        _LOGGER.debug(f"config step '{id}' with type {self.type}")
        if not hasattr(self, "type") or self.type is None:
            _LOGGER.error("type not set")
            return self.async_abort(reason="unknown_type")

        schema = CONF_ENTITIES[self.type]["schema"]
        if data_input is None:
            return self.async_show_form(step_id=id, data_schema=schema)

        errors = validate_config_data(self.type, data_input)
        if errors is not None:
            return self.async_show_form(step_id=id, data_schema=schema, errors=errors)

        if step_type == StepTypes.Setup:
            data_input["type"] = self.type
            await self.async_set_unique_id(get_unique_id(data_input))
            return self.async_create_entry(title=data_input[CONF_NAME], data=data_input)
        elif step_type == StepTypes.Variation:
            self.type = data_input[CONF_VARIATION]
            return await self.async_step_common_setup(data_input=None)

        return self.async_abort(reason="unknown_type")

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
                    data=user_input,
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
                base_schema = entity_info.get("schema")
                edit_schema = self.add_suggested_values_to_schema(
                    base_schema, data_clone
                )
                return self.async_show_form(step_id="init", data_schema=edit_schema)
        else:
            errors["base"] = "unknown_type"

        return self.async_show_form(step_id="init", errors=errors)
