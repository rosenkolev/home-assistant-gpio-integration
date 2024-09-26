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

### Analog Sensor ###


def create_analog_sensor_schema(data: dict) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_NAME, default=data[CONF_NAME]): cv.string,
            vol.Required(
                CONF_PORT,
                default=data[CONF_PORT],
            ): cv.positive_int,
            vol.Optional(
                CONF_DEFAULT_STATE,
                default=data[CONF_DEFAULT_STATE],
            ): cv.boolean,
            vol.Optional(CONF_UNIQUE_ID, default=data[CONF_UNIQUE_ID]): cv.string,
        }
    )


ANALOG_SENSOR_SCHEMA = create_analog_sensor_schema(
    {
        CONF_NAME: None,
        CONF_PORT: None,
        CONF_DEFAULT_STATE: False,
        CONF_UNIQUE_ID: "",
    }
)


def validate_analog_sensor_data(data):
    return v_name(data[CONF_NAME]) and v_pin(data[CONF_PORT])


class AnalogSensorConfig:
    def __init__(self, data: dict):
        self.name: str = data[CONF_NAME]
        self.pin: int = data[CONF_PORT]
        self.default_state: bool = data[CONF_DEFAULT_STATE]
        self.unique_id: str = get_unique_id(data)
