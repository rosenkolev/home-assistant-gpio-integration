"""Schema for the Cover entities."""

from typing import Literal

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.const import CONF_MODE, CONF_NAME, CONF_PORT, CONF_UNIQUE_ID

from . import (
    CONF_INVERT_LOGIC,
    CONF_PIN_CLOSED_SENSOR,
    CONF_RELAY_CLOSE_INVERT,
    CONF_RELAY_CLOSE_PIN,
    CONF_RELAY_OPEN_INVERT,
    CONF_RELAY_OPEN_PIN,
    CONF_RELAY_TIME,
    EMPTY_VARIATION_DATA,
    create_variation_list_schema,
    dropdown,
    get_unique_id,
    validate_variation_data,
)
from ._validators import v_name, v_pin, v_time

### Cover Variations ###

COVER_VARIATIONS = {
    "cover_up_down": "Cover with Up/Down buttons (optional sensor)",
    "cover_toggle": "Cover with Toggle button (optional sensor)",
}


def create_cover_variation_schema(data: dict) -> vol.Schema:
    return create_variation_list_schema(data, COVER_VARIATIONS)


COVER_VARIATION_SCHEMA = create_cover_variation_schema(EMPTY_VARIATION_DATA)


def validate_cover_variation_data(data):
    return validate_variation_data(data, COVER_VARIATIONS)


### COVER UP/DOWN SCHEMA ###

COVER_MODES = ["Blind", "Curtain", "Garage", "Door", "Shade"]


def create_cover_up_down_schema(data: dict) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_NAME, default=data[CONF_NAME]): cv.string,
            vol.Required(
                CONF_RELAY_CLOSE_PIN,
                default=data[CONF_RELAY_CLOSE_PIN],
                description="GPIO pin number for the close relay",
            ): cv.positive_int,
            vol.Optional(
                CONF_RELAY_CLOSE_INVERT,
                default=data[CONF_RELAY_CLOSE_INVERT],
                description="Invert the logic of the close relay",
            ): cv.boolean,
            vol.Required(
                CONF_RELAY_OPEN_PIN,
                default=data[CONF_RELAY_OPEN_PIN],
                description="GPIO pin number for the open relay",
            ): cv.positive_int,
            vol.Optional(
                CONF_RELAY_OPEN_INVERT,
                default=data[CONF_RELAY_OPEN_INVERT],
                description="Invert the logic of the open relay",
            ): cv.boolean,
            vol.Optional(
                CONF_RELAY_TIME, default=data[CONF_RELAY_TIME]
            ): cv.positive_int,
            vol.Optional(
                CONF_PIN_CLOSED_SENSOR, default=data[CONF_PIN_CLOSED_SENSOR]
            ): cv.positive_int,
            vol.Required(CONF_MODE, default=data[CONF_MODE]): dropdown(COVER_MODES),
            vol.Optional(CONF_UNIQUE_ID, default=data[CONF_UNIQUE_ID]): cv.string,
        }
    )


COVER_UP_DOWN_SCHEMA = create_cover_up_down_schema(
    {
        CONF_NAME: "",
        CONF_RELAY_CLOSE_PIN: 0,
        CONF_RELAY_CLOSE_INVERT: False,
        CONF_RELAY_OPEN_PIN: 0,
        CONF_RELAY_OPEN_INVERT: False,
        CONF_RELAY_TIME: 15,
        CONF_PIN_CLOSED_SENSOR: 0,
        CONF_MODE: "Blind",
        CONF_UNIQUE_ID: "",
    }
)


def validate_cover_up_down_data(data: dict) -> bool:
    return (
        v_name(data[CONF_NAME])
        and v_pin(data[CONF_RELAY_CLOSE_PIN])
        and v_pin(data[CONF_RELAY_OPEN_PIN])
        and v_time(data[CONF_RELAY_TIME])
    )


class RollerConfig:
    def __init__(self, data: dict):
        self.name: str = data[CONF_NAME]
        self.mode: str = data[CONF_MODE]
        self.pin_close: int = data[CONF_RELAY_CLOSE_PIN]
        self.pin_close_on_state: Literal["high", "low"] = (
            "high" if data[CONF_RELAY_CLOSE_INVERT] else "low"
        )
        self.pin_open: int = data[CONF_RELAY_OPEN_PIN]
        self.pin_open_on_state: Literal["high", "low"] = (
            "high" if data[CONF_RELAY_OPEN_INVERT] else "low"
        )
        self.relay_time: int = data[CONF_RELAY_TIME]
        self.pin_closed: int | None = data[CONF_PIN_CLOSED_SENSOR]
        self.pin_closed_on_state: Literal["high", "low"] = "high"
        self.pin_closed_mode: Literal["up", "down"] = "up"
        self.unique_id: str = get_unique_id(data)

        if self.pin_closed <= 0:
            self.pin_closed = None


### COVER TOGGLE SCHEMA ###


def create_toggle_cover_schema(data: dict) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_NAME, default=data[CONF_NAME]): cv.string,
            vol.Required(
                CONF_PORT,
                default=data[CONF_PORT],
                description="GPIO pin number for the toggle button",
            ): cv.positive_int,
            vol.Optional(
                CONF_INVERT_LOGIC,
                default=data[CONF_INVERT_LOGIC],
                description="Invert the logic of the toggle button",
            ): cv.boolean,
            vol.Optional(
                CONF_RELAY_TIME, default=data[CONF_RELAY_TIME]
            ): cv.positive_float,
            vol.Optional(
                CONF_PIN_CLOSED_SENSOR, default=data[CONF_PIN_CLOSED_SENSOR]
            ): cv.positive_int,
            vol.Required(CONF_MODE, default=data[CONF_MODE]): dropdown(COVER_MODES),
            vol.Optional(CONF_UNIQUE_ID, default=data[CONF_UNIQUE_ID]): cv.string,
        }
    )


COVER_TOGGLE_SCHEMA = create_toggle_cover_schema(
    {
        CONF_NAME: None,
        CONF_PORT: None,
        CONF_INVERT_LOGIC: False,
        CONF_RELAY_TIME: 0.4,
        CONF_PIN_CLOSED_SENSOR: 0,
        CONF_MODE: "Blind",
        CONF_UNIQUE_ID: "",
    }
)


def validate_toggle_cover_data(data: dict):
    return (
        v_name(data[CONF_NAME])
        and v_pin(data[CONF_PORT])
        and v_time(data[CONF_RELAY_TIME])
    )


class ToggleRollerConfig:
    def __init__(self, data: dict):
        self.name: str = data[CONF_NAME]
        self.mode: str = data[CONF_MODE]
        self.port: int = data[CONF_PORT]
        self.invert_logic: bool = data[CONF_INVERT_LOGIC]
        self.relay_time: float = data[CONF_RELAY_TIME]
        self.pin_closed: int | None = data[CONF_PIN_CLOSED_SENSOR]
        self.unique_id: str = get_unique_id(data)

        if self.pin_closed <= 0:
            self.pin_closed = None
