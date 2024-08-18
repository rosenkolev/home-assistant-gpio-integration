from typing import Literal
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from homeassistant.const import CONF_NAME, CONF_PORT, CONF_UNIQUE_ID

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
DEFAULT_INVERT_LOGIC = False
DEFAULT_RELAY_TIME = 15
DEFAULT_PULL_MODE = "up"
DEFAULT_BOUNCE_TIME = 50
CONF_TYPES: dict = {
    "Cover with up and down button (optional sensor)": "cover_up_down",
    "Cover with toggle button (optional sensor)": "cover_toggle",
    "Binary sensor": "binary_sensor",
    "Switch": "switch",
}

MAIN_SCHEMA = vol.Schema(
    {
        vol.Required("type"): vol.In(CONF_TYPES.keys()),
    }
)


def get_type(data: dict) -> str | None:
    return CONF_TYPES.get(data["type"]) if data != None else None


CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)
COVER_UP_DOWN_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME): cv.string,
        vol.Required(CONF_RELAY_UP_PIN): cv.positive_int,
        vol.Optional(CONF_RELAY_UP_INVERT, default=DEFAULT_INVERT_LOGIC): cv.boolean,
        vol.Required(CONF_RELAY_DOWN_PIN): cv.positive_int,
        vol.Optional(CONF_RELAY_DOWN_INVERT, default=DEFAULT_INVERT_LOGIC): cv.boolean,
        vol.Optional(CONF_RELAY_TIME, default=DEFAULT_RELAY_TIME): cv.positive_int,
        vol.Optional(CONF_PIN_CLOSED_SENSOR, default=0): cv.positive_int,
        vol.Optional(CONF_UNIQUE_ID): cv.string,
    }
)

COVER_TOGGLE_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME): cv.string,
        vol.Required(CONF_PORT): cv.positive_int,
        vol.Optional(CONF_INVERT_LOGIC, default=DEFAULT_INVERT_LOGIC): cv.boolean,
        vol.Optional(CONF_RELAY_TIME, default=0.4): cv.positive_float,
        vol.Optional(CONF_PIN_CLOSED_SENSOR, default=0): cv.positive_int,
        vol.Optional(CONF_UNIQUE_ID): cv.string,
    }
)

SENSOR_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME): cv.string,
        vol.Required(CONF_PORT): cv.positive_int,
        vol.Optional(CONF_PULL_MODE, default=DEFAULT_PULL_MODE): vol.In(["up", "down"]),
        vol.Optional(CONF_BOUNCE_TIME, default=DEFAULT_BOUNCE_TIME): cv.positive_int,
        vol.Optional(CONF_INVERT_LOGIC, default=DEFAULT_INVERT_LOGIC): cv.boolean,
        vol.Optional(CONF_UNIQUE_ID): cv.string,
    }
)


SWITCH_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME): cv.string,
        vol.Required(CONF_PORT): cv.positive_int,
        vol.Optional(CONF_INVERT_LOGIC, default=DEFAULT_INVERT_LOGIC): cv.boolean,
        vol.Optional(CONF_UNIQUE_ID): cv.string,
        vol.Optional(CONF_DEFAULT_STATE, default=False): cv.boolean,
    }
)


def get_unique_id(data: dict) -> str | None:
    return data.get(CONF_UNIQUE_ID) or data[CONF_NAME].lower().replace(" ", "_") or None


class RollerConfig:
    def __init__(self, data: dict):
        self.name: str = data[CONF_NAME]
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
        self.bounce_time_ms: int = data[CONF_BOUNCE_TIME]
        self.invert_logic: bool = data[CONF_INVERT_LOGIC]
        self.unique_id: str = get_unique_id(data)


class SwitchConfig:
    def __init__(self, data: dict):
        self.name: str = data[CONF_NAME]
        self.port: int = data[CONF_PORT]
        self.invert_logic: bool = data[CONF_INVERT_LOGIC]
        self.default_state: bool = data[CONF_DEFAULT_STATE]
        self.unique_id: str = get_unique_id(data)
