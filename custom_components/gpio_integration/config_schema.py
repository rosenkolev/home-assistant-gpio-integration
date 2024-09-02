from typing import Literal

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.const import (
    CONF_HOST,
    CONF_MODE,
    CONF_NAME,
    CONF_PORT,
    CONF_UNIQUE_ID,
)
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.selector import selector

from .const import DOMAIN

CONF_COVERS = "covers"
CONF_RELAY_UP_PIN = "up_pin"
CONF_RELAY_UP_INVERT = "up_pin_invert"
CONF_RELAY_DOWN_PIN = "down_pin"
CONF_RELAY_DOWN_INVERT = "down_pin_invert"
CONF_RELAY_TIME = "relay_time"
CONF_PIN_CLOSED_SENSOR = "pin_closed_sensor"
CONF_PULL_MODE = "pull_mode"
CONF_INVERT_LOGIC = "invert_logic"
CONF_BOUNCE_TIME = "bounce_time_in_ms"
CONF_DEFAULT_STATE = "default_state"
CONF_EDGE_EVENT_TIMEOUT = "edge_event_timeout"
CONF_FREQUENCY = "frequency"
CONF_INTERFACE = "interface"

## configuration.yaml schema

DOMAIN_DEFAULT_CONFIG = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Optional(CONF_INTERFACE): cv.string,
                vol.Optional(CONF_HOST): cv.string,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)

## VALIDATORS


class InvalidPin(HomeAssistantError):
    """Error to indicate invalid pin."""


def v_pin(pin) -> bool:
    """Validate pin number."""
    if pin < 1:
        raise InvalidPin
    return True


def v_name(name) -> bool:
    """Validate name."""
    if name is None or name == "":
        raise ValueError("Name is required")
    return True


def v_time(time) -> bool:
    """Validate time."""
    if time <= 0:
        raise ValueError("Time must be greater than 0")
    return True


## USER (INIT) SCHEMA

CONF_TYPES: dict = {
    "Cover with up and down button (optional sensor)": "cover_up_down",
    "Cover with toggle button (optional sensor)": "cover_toggle",
    "Binary sensor": "binary_sensor",
    "Switch": "switch",
    "Light": "light",
}

MAIN_SCHEMA = vol.Schema(
    {
        vol.Required("type"): vol.In(CONF_TYPES.keys()),
    }
)


def get_type(data: dict) -> str | None:
    return CONF_TYPES.get(data["type"]) if data is not None else None


## COVER UP/DOWN SCHEMA

COVER_MODES = ["Blind", "Curtain", "Garage", "Door", "Shade"]


def create_cover_up_down_schema(data: dict) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_NAME, default=data[CONF_NAME]): cv.string,
            vol.Required(
                CONF_RELAY_UP_PIN,
                default=data[CONF_RELAY_UP_PIN],
                description="GPIO pin number for the up relay",
            ): cv.positive_int,
            vol.Optional(
                CONF_RELAY_UP_INVERT,
                default=data[CONF_RELAY_UP_INVERT],
                description="Invert the logic of the up relay",
            ): cv.boolean,
            vol.Required(
                CONF_RELAY_DOWN_PIN,
                default=data[CONF_RELAY_DOWN_PIN],
                description="GPIO pin number for the down relay",
            ): cv.positive_int,
            vol.Optional(
                CONF_RELAY_DOWN_INVERT,
                default=data[CONF_RELAY_DOWN_INVERT],
                description="Invert the logic of the down relay",
            ): cv.boolean,
            vol.Optional(
                CONF_RELAY_TIME, default=data[CONF_RELAY_TIME]
            ): cv.positive_int,
            vol.Optional(
                CONF_PIN_CLOSED_SENSOR, default=data[CONF_PIN_CLOSED_SENSOR]
            ): cv.positive_int,
            vol.Required(CONF_MODE, default=data[CONF_MODE]): selector(
                {
                    "select": {
                        "options": COVER_MODES,
                        "mode": "dropdown",
                    }
                }
            ),
            vol.Optional(CONF_UNIQUE_ID, default=data[CONF_UNIQUE_ID]): cv.string,
        }
    )


COVER_UP_DOWN_SCHEMA = create_cover_up_down_schema(
    {
        CONF_NAME: "",
        CONF_RELAY_UP_PIN: 0,
        CONF_RELAY_UP_INVERT: False,
        CONF_RELAY_DOWN_PIN: 0,
        CONF_RELAY_DOWN_INVERT: False,
        CONF_RELAY_TIME: 15,
        CONF_PIN_CLOSED_SENSOR: 0,
        CONF_MODE: "Blind",
        CONF_UNIQUE_ID: "",
    }
)


def validate_cover_up_down_data(data: dict) -> bool:
    return (
        v_name(data[CONF_NAME])
        and v_pin(data[CONF_RELAY_UP_PIN])
        and v_pin(data[CONF_RELAY_DOWN_PIN])
        and v_time(data[CONF_RELAY_TIME])
    )


## COVER TOGGLE SCHEMA


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
            vol.Required(CONF_MODE, default=data[CONF_MODE]): selector(
                {
                    "select": {
                        "options": COVER_MODES,
                        "mode": "dropdown",
                    }
                }
            ),
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


## BINARY SENSOR SCHEMA


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
        CONF_BOUNCE_TIME: 500,
        CONF_INVERT_LOGIC: False,
        CONF_MODE: "Door",
        CONF_DEFAULT_STATE: False,
        CONF_EDGE_EVENT_TIMEOUT: 5,
        CONF_UNIQUE_ID: "",
    }
)


def validate_binary_sensor_data(data):
    return (
        v_name(data[CONF_NAME])
        and v_pin(data[CONF_PORT])
        and v_time(data[CONF_BOUNCE_TIME])
    )


## SWITCH SCHEMA


def create_switch_schema(data: dict) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_NAME, default=data[CONF_NAME]): cv.string,
            vol.Required(
                CONF_PORT,
                default=data[CONF_PORT],
                description="GPIO pin number for the switch",
            ): cv.positive_int,
            vol.Optional(
                CONF_INVERT_LOGIC,
                default=data[CONF_INVERT_LOGIC],
                description="Invert the logic of the switch",
            ): cv.boolean,
            vol.Optional(
                CONF_DEFAULT_STATE,
                default=data[CONF_DEFAULT_STATE],
                description="Default state of the switch",
            ): cv.boolean,
            vol.Optional(CONF_UNIQUE_ID, default=data[CONF_UNIQUE_ID]): cv.string,
        }
    )


SWITCH_SCHEMA = create_switch_schema(
    {
        CONF_NAME: None,
        CONF_PORT: None,
        CONF_INVERT_LOGIC: False,
        CONF_DEFAULT_STATE: False,
        CONF_UNIQUE_ID: "",
    }
)


def validate_switch_data(data):
    return v_name(data[CONF_NAME]) and v_pin(data[CONF_PORT])


## LIGHT SCHEMA


def create_light_schema(data: dict) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_NAME, default=data[CONF_NAME]): cv.string,
            vol.Required(
                CONF_PORT,
                default=data[CONF_PORT],
                description="GPIO pin number for the switch",
            ): cv.positive_int,
            vol.Optional(
                CONF_FREQUENCY,
                default=data[CONF_FREQUENCY],
                description="The light pulse frequency (for LED)",
            ): cv.positive_int,
            vol.Optional(
                CONF_DEFAULT_STATE,
                default=data[CONF_DEFAULT_STATE],
                description="Default state",
            ): cv.boolean,
            vol.Optional(CONF_UNIQUE_ID, default=data[CONF_UNIQUE_ID]): cv.string,
        }
    )


LIGHT_SCHEMA = create_light_schema(
    {
        CONF_NAME: None,
        CONF_PORT: None,
        CONF_FREQUENCY: 0,
        CONF_DEFAULT_STATE: False,
        CONF_UNIQUE_ID: "",
    }
)


def validate_light_data(data):
    return v_name(data[CONF_NAME]) and v_pin(data[CONF_PORT])


## CONFIG CLASSES


def get_unique_id(data: dict) -> str | None:
    return data.get(CONF_UNIQUE_ID) or data[CONF_NAME].lower().replace(" ", "_") or None


class RollerConfig:
    def __init__(self, data: dict):
        self.name: str = data[CONF_NAME]
        self.mode: str = data[CONF_MODE]
        self.pin_up: int = data[CONF_RELAY_UP_PIN]
        self.pin_up_on_state: Literal["high", "low"] = (
            "high" if data[CONF_RELAY_UP_INVERT] else "low"
        )
        self.pin_down: int = data[CONF_RELAY_DOWN_PIN]
        self.pin_down_on_state: Literal["high", "low"] = (
            "high" if data[CONF_RELAY_DOWN_INVERT] else "low"
        )
        self.relay_time: int = data[CONF_RELAY_TIME]
        self.pin_closed: int | None = data[CONF_PIN_CLOSED_SENSOR]
        self.pin_closed_on_state: Literal["high", "low"] = "high"
        self.pin_closed_mode: Literal["up", "down"] = "up"
        self.unique_id: str = get_unique_id(data)

        if self.pin_closed <= 0:
            self.pin_closed = None


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


class SensorConfig:
    def __init__(self, data: dict):
        self.name: str = data[CONF_NAME]
        self.pin: int = data[CONF_PORT]
        self.pull_mode: Literal["up", "down"] = data[CONF_PULL_MODE]
        self.mode: str = data[CONF_MODE]
        self.bounce_time_ms: int = data[CONF_BOUNCE_TIME]
        self.invert_logic: bool = data[CONF_INVERT_LOGIC]
        self.default_state: bool = data[CONF_DEFAULT_STATE]
        self.edge_event_timeout_sec: int = data[CONF_EDGE_EVENT_TIMEOUT]
        self.unique_id: str = get_unique_id(data)


class SwitchConfig:
    def __init__(self, data: dict):
        self.name: str = data[CONF_NAME]
        self.port: int = data[CONF_PORT]
        self.invert_logic: bool = data[CONF_INVERT_LOGIC]
        self.default_state: bool = data[CONF_DEFAULT_STATE]
        self.unique_id: str = get_unique_id(data)


class LightConfig:
    def __init__(self, data: dict):
        self.name: str = data[CONF_NAME]
        self.port: int = data[CONF_PORT]
        self.frequency: int = data[CONF_FREQUENCY]
        self.default_state: bool = data[CONF_DEFAULT_STATE]
        self.unique_id: str = get_unique_id(data)
