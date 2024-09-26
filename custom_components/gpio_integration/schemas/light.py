"""Schema for the Light entities."""

from homeassistant.const import CONF_NAME, CONF_PORT, CONF_UNIQUE_ID

from . import (
    CONF_DEFAULT_STATE,
    CONF_FREQUENCY,
)
from .pwm import create_pwm_schema

LIGHT_SCHEMA = create_pwm_schema(
    {
        CONF_NAME: None,
        CONF_PORT: None,
        CONF_FREQUENCY: 0,
        CONF_DEFAULT_STATE: False,
        CONF_UNIQUE_ID: "",
    }
)
