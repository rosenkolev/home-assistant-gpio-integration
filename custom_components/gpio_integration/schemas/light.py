"""Schema for the Light entities."""

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.const import CONF_NAME, CONF_PORT, CONF_UNIQUE_ID

from . import (
    CONF_DEFAULT_STATE,
    CONF_FREQUENCY,
    CONF_INVERT_LOGIC,
    EMPTY_VARIATION_DATA,
    create_variation_list_schema,
    get_unique_id,
    number_slider,
    validate_variation_data,
)
from ._validators import v_name, v_percentage, v_pin
from .pwm import create_pwm_schema

### Light Variations ###

LIGHT_VARIATIONS = {
    "light_pwm_led": "LED (PWM)",
    "light_rgb_led": "RGB LED",
}


def create_light_variation_schema(data: dict) -> vol.Schema:
    return create_variation_list_schema(data, LIGHT_VARIATIONS)


LIGHT_VARIATION_SCHEMA = create_light_variation_schema(EMPTY_VARIATION_DATA)


def validate_light_variation_data(data):
    return validate_variation_data(data, LIGHT_VARIATIONS)


### PWM Light ###

LIGHT_SCHEMA = create_pwm_schema(
    {
        CONF_NAME: None,
        CONF_PORT: None,
        CONF_FREQUENCY: 0,
        CONF_DEFAULT_STATE: False,
        CONF_INVERT_LOGIC: False,
        CONF_UNIQUE_ID: "",
    }
)

### RGB Light ###

CONF_RED_PIN = "red_pin"
CONF_GREEN_PIN = "green_pin"
CONF_BLUE_PIN = "blue_pin"
CONF_RED_INTENSITY = "red_calibration"
CONF_GREEN_INTENSITY = "green_calibration"
CONF_BLUE_INTENSITY = "blue_calibration"


def create_rgb_light_schema(data: dict) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_NAME, default=data[CONF_NAME]): cv.string,
            vol.Required(
                CONF_RED_PIN,
                default=data[CONF_RED_PIN],
                description={"comment": "GPIO pin number for red color"},
            ): cv.positive_int,
            vol.Required(
                CONF_GREEN_PIN,
                default=data[CONF_GREEN_PIN],
                description={"comment": "GPIO pin number for green color"},
            ): cv.positive_int,
            vol.Required(
                CONF_BLUE_PIN,
                default=data[CONF_BLUE_PIN],
                description={"comment": "GPIO pin number for blue color"},
            ): cv.positive_int,
            vol.Required(
                CONF_FREQUENCY,
                default=data[CONF_FREQUENCY],
                description={"comment": "The light pulse frequency"},
            ): cv.positive_int,
            vol.Optional(
                CONF_DEFAULT_STATE,
                default=data[CONF_DEFAULT_STATE],
                description={"comment": "Default state of the light"},
            ): cv.boolean,
            vol.Optional(
                CONF_INVERT_LOGIC,
                default=data[CONF_INVERT_LOGIC],
                description={"comment": "Invert the logic of the LED (low = on)"},
            ): cv.boolean,
            vol.Optional(
                CONF_RED_INTENSITY,
                default=data[CONF_RED_INTENSITY],
                description={
                    "comment": "Brightness correction factor red color (0-100%)"
                },
            ): number_slider(1),
            vol.Optional(
                CONF_GREEN_INTENSITY,
                default=data[CONF_GREEN_INTENSITY],
                description={
                    "comment": "Brightness correction factor green color (0-100%)"
                },
            ): number_slider(1),
            vol.Optional(
                CONF_BLUE_INTENSITY,
                default=data[CONF_BLUE_INTENSITY],
                description={
                    "comment": "Brightness correction factor blue color (0-100%)"
                },
            ): number_slider(1),
            vol.Optional(CONF_UNIQUE_ID, default=data[CONF_UNIQUE_ID]): cv.string,
        }
    )


RGB_LIGHT_SCHEMA = create_rgb_light_schema(
    {
        CONF_NAME: None,
        CONF_RED_PIN: None,
        CONF_GREEN_PIN: None,
        CONF_BLUE_PIN: None,
        CONF_FREQUENCY: 200,
        CONF_DEFAULT_STATE: False,
        CONF_INVERT_LOGIC: False,
        CONF_RED_INTENSITY: 100,
        CONF_GREEN_INTENSITY: 100,
        CONF_BLUE_INTENSITY: 100,
        CONF_UNIQUE_ID: "",
    }
)


def validate_rgb_light_data(data):
    return (
        v_name(data[CONF_NAME])
        and v_pin(data[CONF_RED_PIN])
        and v_pin(data[CONF_GREEN_PIN])
        and v_pin(data[CONF_BLUE_PIN])
        and v_percentage(data[CONF_RED_INTENSITY])
        and v_percentage(data[CONF_GREEN_INTENSITY])
        and v_percentage(data[CONF_BLUE_INTENSITY])
    )


class RgbLightConfig:
    """RGB Light configuration schema."""

    def __init__(self, data: dict):
        self.name: str = data[CONF_NAME]
        self.port_red: int = data[CONF_RED_PIN]
        self.port_green: int = data[CONF_GREEN_PIN]
        self.port_blue: int = data[CONF_BLUE_PIN]
        self.frequency: int = data[CONF_FREQUENCY]
        self.default_state: bool = data[CONF_DEFAULT_STATE]
        self.invert_logic: bool = data[CONF_INVERT_LOGIC]
        self.intensity_red: float = data[CONF_RED_INTENSITY] / 100.0
        self.intensity_green: float = data[CONF_GREEN_INTENSITY] / 100.0
        self.intensity_blue: float = data[CONF_BLUE_INTENSITY] / 100.0
        self.unique_id: str = get_unique_id(data)
