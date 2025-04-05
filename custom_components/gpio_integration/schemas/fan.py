"""Schema for the Fan entities."""

from homeassistant.const import CONF_NAME, CONF_PORT, CONF_UNIQUE_ID

from . import (
    CONF_DEFAULT_STATE,
    CONF_FREQUENCY,
    CONF_INVERT_LOGIC,
)
from .pwm import create_pwm_schema

FAN_SCHEMA = create_pwm_schema(
    {
        CONF_NAME: None,
        CONF_PORT: None,
        CONF_FREQUENCY: 100,
        CONF_DEFAULT_STATE: False,
        CONF_INVERT_LOGIC: False,
        CONF_UNIQUE_ID: "",
    }
)
