"""Schema for the Sensor entities."""

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.const import (
    CONF_NAME,
    CONF_PORT,
    CONF_UNIQUE_ID,
)

from . import CONF_DEFAULT_STATE, get_unique_id
from ._validators import v_name, v_pin

CONF_SENSOR_RANGES = "sensor_ranges"
CONF_VOLTAGE_MIN_MV = "voltage_min_mv"
CONF_VOLTAGE_STEP_MV = "voltage_step_mv"
CONF_MIN_VALUE = "min_value"

### Analog Linear Sensor ###


def create_analog_linear_sensor_schema(data: dict) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_NAME, default=data[CONF_NAME]): cv.string,
            vol.Required(
                CONF_PORT,
                default=data[CONF_PORT],
            ): cv.positive_int,
            vol.Required(
                CONF_MIN_VALUE,
                default=data[CONF_MIN_VALUE],
            ): cv.float,
            vol.Optional(
                CONF_VOLTAGE_MIN_MV,
                default=data[CONF_VOLTAGE_MIN_MV],
            ): cv.positive_int,
            vol.Optional(
                CONF_VOLTAGE_STEP_MV,
                default=data[CONF_VOLTAGE_STEP_MV],
            ): cv.positive_int,
            vol.Optional(CONF_UNIQUE_ID, default=data[CONF_UNIQUE_ID]): cv.string,
        }
    )


ANALOG_LINEAR_SENSOR_SCHEMA = create_analog_linear_sensor_schema(
    {
        CONF_NAME: None,
        CONF_PORT: None,
        CONF_MIN_VALUE: 0,
        CONF_VOLTAGE_MIN_MV: 1000,
        CONF_VOLTAGE_STEP_MV: 100,
        CONF_UNIQUE_ID: "",
    }
)


def validate_analog_liner_sensor_data(data):
    return v_name(data[CONF_NAME]) and v_pin(data[CONF_PORT])


class AnalogSensorConfig:
    def __init__(self, data: dict):
        self.name: str = data[CONF_NAME]
        self.pin: int = data[CONF_PORT]
        self.min_voltage_mv: int = data[CONF_VOLTAGE_MIN_MV]
        self.min_value: float = data[CONF_MIN_VALUE]
        self.voltage_step_mv: int = data[CONF_VOLTAGE_STEP_MV]
        self.unique_id: str = get_unique_id(data)


### Analog Range Sensor ###


def create_analog_range_sensor_schema(data: dict) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_NAME, default=data[CONF_NAME]): cv.string,
            vol.Required(
                CONF_PORT,
                default=data[CONF_PORT],
            ): cv.positive_int,
            vol.Optional(
                CONF_SENSOR_RANGES,
                default=data[CONF_SENSOR_RANGES],
            ): cv.string,
            vol.Optional(
                CONF_DEFAULT_STATE,
                default=data[CONF_DEFAULT_STATE],
            ): cv.string,
            vol.Optional(CONF_UNIQUE_ID, default=data[CONF_UNIQUE_ID]): cv.string,
        }
    )


ANALOG_RANGE_SENSOR_SCHEMA = create_analog_range_sensor_schema(
    {
        CONF_NAME: None,
        CONF_PORT: None,
        CONF_SENSOR_RANGES: None,
        CONF_DEFAULT_STATE: "None",
        CONF_UNIQUE_ID: "",
    }
)


def validate_analog_range_sensor_data(data):
    return v_name(data[CONF_NAME]) and v_pin(data[CONF_PORT])


class AnalogRangeSensorConfig:
    def __init__(self, data: dict):
        self.name: str = data[CONF_NAME]
        self.pin: int = data[CONF_PORT]
        self.ranges: str = data[CONF_SENSOR_RANGES]
        self.default_state: str = data[CONF_DEFAULT_STATE]
        self.unique_id: str = get_unique_id(data)


class SpiSensorConfig:
    def __init__(self, data: dict):
        self.name: str = data[CONF_NAME]
        self.pin: int = data[CONF_PORT]
        self.unique_id: str = get_unique_id(data)
