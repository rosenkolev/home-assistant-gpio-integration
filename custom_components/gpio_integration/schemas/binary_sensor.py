"""Schema for the Binary Sensor entity."""

from typing import Literal

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.const import CONF_MODE, CONF_NAME, CONF_PORT, CONF_UNIQUE_ID
from homeassistant.helpers.selector import selector

from . import (
    CONF_BOUNCE_TIME,
    CONF_DEFAULT_STATE,
    CONF_EDGE_EVENT_TIMEOUT,
    CONF_INVERT_LOGIC,
    CONF_PULL_MODE,
    get_unique_id,
)
from ._validators import v_name, v_pin, v_time

CONF_RELY_ON_EDGE_EVENTS = "rely_on_edge_events"


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
                CONF_PULL_MODE,
                default=data[CONF_PULL_MODE],
                description="Pull mode for the sensor",
            ): vol.In(["up", "down"]),
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
            vol.Required(CONF_MODE, default=data[CONF_MODE]): selector(
                {
                    "select": {
                        "options": ["Door", "Motion", "Light", "Vibration", "Plug"],
                        "mode": "dropdown",
                    }
                }
            ),
            vol.Optional(
                CONF_DEFAULT_STATE, default=data[CONF_DEFAULT_STATE]
            ): cv.boolean,
            vol.Optional(
                CONF_RELY_ON_EDGE_EVENTS,
                default=data[CONF_RELY_ON_EDGE_EVENTS],
                description="Sensor rely only on edge events and don't use state",
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
        CONF_PULL_MODE: "up",
        CONF_BOUNCE_TIME: 200,
        CONF_INVERT_LOGIC: False,
        CONF_MODE: "Door",
        CONF_DEFAULT_STATE: False,
        CONF_RELY_ON_EDGE_EVENTS: False,
        CONF_EDGE_EVENT_TIMEOUT: 10,
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
        self.pull_mode: Literal["up", "down"] = data[CONF_PULL_MODE]
        self.mode: str = data[CONF_MODE]
        self.bounce_time_ms: int = data[CONF_BOUNCE_TIME]
        self.invert_logic: bool = data[CONF_INVERT_LOGIC]
        self.default_state: bool = data[CONF_DEFAULT_STATE]
        self.rely_on_edge_events: bool = data[CONF_RELY_ON_EDGE_EVENTS]
        self.edge_event_timeout_sec: int = data[CONF_EDGE_EVENT_TIMEOUT]
        self.unique_id: str = get_unique_id(data)