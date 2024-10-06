"""Schema for the Sensor entities."""

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.const import (
    CONF_NAME,
    CONF_PORT,
    CONF_UNIQUE_ID,
)

from . import (
    VARIATION_SCHEMA,
    create_variation_list_schema,
    get_unique_id,
    validate_variation_data,
)
from ._validators import v_name, v_pin

SENSOR_VARIATIONS = {
    "sensor_serial_data": "ADC Sensor",
}


def create_sensor_variation_schema(data: dict) -> vol.Schema:
    return create_variation_list_schema(data, SENSOR_VARIATIONS)


SENSOR_VARIATION_SCHEMA = VARIATION_SCHEMA


def validate_sensor_variation_data(data):
    return validate_variation_data(data, SENSOR_VARIATIONS)


### Sensor Serial Data ###


def create_sensor_serial_schema(data: dict) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_NAME, default=data[CONF_NAME]): cv.string,
            vol.Required(
                CONF_PORT,
                default=data[CONF_PORT],
                description="GPIO pin number for the switch",
            ): cv.positive_int,
            vol.Optional(CONF_UNIQUE_ID, default=data[CONF_UNIQUE_ID]): cv.string,
        }
    )


SENSOR_SERIAL_SCHEMA = create_sensor_serial_schema(
    {
        CONF_NAME: None,
        CONF_PORT: None,
        CONF_UNIQUE_ID: "",
    }
)


def validate_sensor_serial_data(data):
    return v_name(data[CONF_NAME]) and v_pin(data[CONF_PORT])


class SensorSerialConfig:
    def __init__(self, data: dict):
        self.name: str = data[CONF_NAME]
        self.pin: int = data[CONF_PORT]
        self.unique_id: str = get_unique_id(data)
