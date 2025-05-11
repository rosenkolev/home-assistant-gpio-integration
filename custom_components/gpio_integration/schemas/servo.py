"""Schema for the Servo entities."""

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.const import (
    CONF_NAME,
    CONF_PORT,
    CONF_UNIQUE_ID,
)

from . import CONF_DEFAULT_STATE, get_unique_id, number_slider
from ._validators import v_name, v_pin

CONF_MIN_ANGLE = "min_angle"
CONF_MAX_ANGLE = "max_angle"

SERVO_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME, default=None): cv.string,
        vol.Required(
            CONF_PORT,
            default=None,
        ): cv.positive_int,
        vol.Optional(CONF_DEFAULT_STATE, default=0): cv.int,
        vol.Required(
            CONF_MIN_ANGLE,
            default=-90,
        ): number_slider(-180, 180, 1, "°"),
        vol.Required(
            CONF_MAX_ANGLE,
            default=90,
        ): number_slider(0, 360, 1, "°"),
        vol.Optional(CONF_UNIQUE_ID, default=""): cv.string,
    }
)


def validate_servo_data(data):
    return v_name(data[CONF_NAME]) and v_pin(data[CONF_PORT])


class ServoConfig:
    """Config configuration schema."""

    def __init__(self, data: dict):
        self.name: str = data[CONF_NAME]
        self.port: int = data[CONF_PORT]
        self.min_angle = data[CONF_MIN_ANGLE]
        self.max_angle = data[CONF_MAX_ANGLE]
        self.default_angle: int = data[CONF_DEFAULT_STATE]
        self.unique_id: str = get_unique_id(data)
