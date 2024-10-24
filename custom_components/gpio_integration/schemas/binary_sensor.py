"""Schema for the Binary Sensor entity."""

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.const import CONF_MODE, CONF_NAME, CONF_PORT, CONF_UNIQUE_ID

from . import (
    CONF_BOUNCE_TIME,
    CONF_DEFAULT_STATE,
    CONF_EDGE_EVENT_TIMEOUT,
    CONF_INVERT_LOGIC,
    create_dropdown,
    get_unique_id,
)
from ._validators import v_name, v_pin, v_time


def create_binary_sensor_schema(data: dict) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_NAME, default=data[CONF_NAME]): cv.string,
            vol.Required(
                CONF_PORT,
                default=data[CONF_PORT],
                description="GPIO pin number for the sensor",
            ): cv.positive_int,
            vol.Optional(
                CONF_BOUNCE_TIME,
                default=data[CONF_BOUNCE_TIME],
                description="Bounce time for the sensor in milliseconds",
            ): cv.positive_int,
            vol.Optional(
                CONF_INVERT_LOGIC,
                default=data[CONF_INVERT_LOGIC],
                description="Invert the logic of the sensor",
            ): cv.boolean,
            vol.Required(CONF_MODE, default=data[CONF_MODE]): create_dropdown(
                [
                    "Door",
                    "Motion",
                    "Light",
                    "Vibration",
                    "Plug",
                    "Smoke",
                    "Window",
                ]
            ),
            vol.Optional(
                CONF_DEFAULT_STATE, default=data[CONF_DEFAULT_STATE]
            ): cv.boolean,
            vol.Optional(
                CONF_EDGE_EVENT_TIMEOUT, default=data[CONF_EDGE_EVENT_TIMEOUT]
            ): cv.positive_int,
            vol.Optional(CONF_UNIQUE_ID, default=data[CONF_UNIQUE_ID]): cv.string,
        }
    )


BINARY_SENSOR_SCHEMA = create_binary_sensor_schema(
    {
        CONF_NAME: None,
        CONF_PORT: None,
        CONF_BOUNCE_TIME: 200,
        CONF_INVERT_LOGIC: False,
        CONF_MODE: "Door",
        CONF_DEFAULT_STATE: False,
        CONF_EDGE_EVENT_TIMEOUT: 0,
        CONF_UNIQUE_ID: "",
    }
)


def validate_binary_sensor_data(data):
    return (
        v_name(data[CONF_NAME])
        and v_pin(data[CONF_PORT])
        and v_time(data[CONF_BOUNCE_TIME])
    )


class BinarySensorConfig:
    def __init__(self, data: dict):
        self.name: str = data[CONF_NAME]
        self.pin: int = data[CONF_PORT]
        self.mode: str = data[CONF_MODE]
        self.bounce_time_ms: int = data[CONF_BOUNCE_TIME]
        self.invert_logic: bool = data[CONF_INVERT_LOGIC]
        self.default_state: bool = data[CONF_DEFAULT_STATE]
        self.edge_event_timeout_sec: int = data[CONF_EDGE_EVENT_TIMEOUT]
        self.unique_id: str = get_unique_id(data)
