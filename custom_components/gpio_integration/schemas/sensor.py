"""Schema for the Sensor entities."""

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.const import (
    CONF_NAME,
    CONF_PORT,
    CONF_UNIQUE_ID,
)

from .._devices import MCP_NAMES
from . import (
    EMPTY_VARIATION_DATA,
    create_variation_list_schema,
    dropdown,
    get_unique_id,
    validate_variation_data,
)
from ._validators import v_name, v_pin, v_positive, v_positive_or_zero
from .main import EntityTypes

SENSOR_VARIATIONS = {
    EntityTypes.SENSOR_DHT22.value: "DHT22",
    EntityTypes.SENSOR_ANALOG_STEP.value: "Analog Step",
}


def create_sensor_variation_schema(data: dict) -> vol.Schema:
    return create_variation_list_schema(data, SENSOR_VARIATIONS)


SENSOR_VARIATION_SCHEMA = create_sensor_variation_schema(EMPTY_VARIATION_DATA)


def validate_sensor_variation_data(data):
    return validate_variation_data(data, SENSOR_VARIATIONS)


### Sensor Serial Data ###


def create_sensor_dht22_schema(data: dict) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_NAME, default=data[CONF_NAME]): cv.string,
            vol.Required(
                CONF_PORT,
                default=data[CONF_PORT],
                description={"comment": "GPIO pin number for the switch"},
            ): cv.positive_int,
            vol.Optional(CONF_UNIQUE_ID, default=data[CONF_UNIQUE_ID]): cv.string,
        }
    )


SENSOR_DHT22_SCHEMA = create_sensor_dht22_schema(
    {
        CONF_NAME: None,
        CONF_PORT: None,
        CONF_UNIQUE_ID: "",
    }
)


def validate_sensor_dht22_data(data):
    return v_name(data[CONF_NAME]) and v_pin(data[CONF_PORT])


### Sensor Analog Step ###

CONF_CHIP = "chip"
CONF_CHANNEL = "channel"
CONF_MIN_VOLTAGE = "min_voltage"
CONF_MIN_VALUE = "min_value"
CONF_STEP_VOLTAGE = "step_voltage"
CONF_STEP_VALUE = "step_value"
CONF_NATIVE_UNIT = "native_unit"


def create_sensor_analog_step_schema(data: dict) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_NAME, default=data[CONF_NAME]): cv.string,
            vol.Required(CONF_CHIP, default=data[CONF_CHIP]): dropdown(MCP_NAMES),
            vol.Required(CONF_CHANNEL, default=data[CONF_CHANNEL]): cv.positive_int,
            vol.Required(
                CONF_MIN_VOLTAGE, default=data[CONF_MIN_VOLTAGE]
            ): cv.positive_float,
            vol.Required(CONF_MIN_VALUE, default=data[CONF_MIN_VALUE]): float,
            vol.Required(
                CONF_STEP_VOLTAGE, default=data[CONF_STEP_VOLTAGE]
            ): cv.positive_float,
            vol.Required(
                CONF_STEP_VALUE, default=data[CONF_STEP_VALUE]
            ): cv.positive_float,
            vol.Required(CONF_NATIVE_UNIT, default=data[CONF_NATIVE_UNIT]): cv.string,
            vol.Optional(CONF_UNIQUE_ID, default=data[CONF_UNIQUE_ID]): cv.string,
        }
    )


SENSOR_ANALOG_STEP_SCHEMA = create_sensor_analog_step_schema(
    {
        CONF_NAME: None,
        CONF_CHIP: "",
        CONF_CHANNEL: 0,
        CONF_MIN_VOLTAGE: 0.0,
        CONF_MIN_VALUE: 0.0,
        CONF_STEP_VOLTAGE: 0.1,
        CONF_STEP_VALUE: 1.0,
        CONF_NATIVE_UNIT: "",
        CONF_UNIQUE_ID: "",
    }
)


def validate_sensor_analog_step_data(data):
    return (
        v_name(data[CONF_NAME])
        and data[CONF_CHIP] in MCP_NAMES
        and v_positive(data[CONF_CHANNEL])
        and v_positive_or_zero(data[CONF_MIN_VOLTAGE])
        and v_positive(data[CONF_STEP_VOLTAGE])
        and v_positive(data[CONF_STEP_VALUE])
        and v_name(data[CONF_NATIVE_UNIT])
    )


class DHT22Config:
    def __init__(self, data: dict):
        self.name: str = data[CONF_NAME]
        self.pin: int = data[CONF_PORT]
        self.unique_id: str = get_unique_id(data)
        self.update_interval_sec: int = 20


class AnalogStepConfig:
    def __init__(self, data: dict):
        self.name: str = data[CONF_NAME]
        self.unique_id: str = get_unique_id(data)
        self.chip: str = data[CONF_CHIP]
        self.channel: int = data[CONF_CHANNEL]
        self.min_voltage: float = data[CONF_MIN_VOLTAGE]
        self.min_value: float = data[CONF_MIN_VALUE]
        self.step_voltage: float = data[CONF_STEP_VOLTAGE]
        self.step_value: float = data[CONF_STEP_VALUE]
        self.native_unit: str = data[CONF_NATIVE_UNIT]
