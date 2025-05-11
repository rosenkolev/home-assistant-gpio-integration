"""Main schema for the GPIO Integration."""

from enum import Enum

import voluptuous as vol


class EntityTypes(Enum):
    COVER = "cover"
    COVER_UP_DOWN = "cover_up_down"
    COVER_TOGGLE = "cover_toggle"
    BINARY_SENSOR = "binary_sensor"
    SWITCH = "switch"
    LIGHT = "light"
    LIGHT_PWM_LED = "light_pwm_led"
    LIGHT_RGB_LED = "light_rgb_led"
    FAN = "fan"
    SENSOR = "sensor"
    SENSOR_DHT22 = "sensor_dht22"
    SENSOR_ANALOG_STEP = "sensor_analog_step"
    SERVO = "servo"


CONF_TYPES: dict = {
    "Cover": EntityTypes.COVER.value,
    "Binary sensor": EntityTypes.BINARY_SENSOR.value,
    "Switch": EntityTypes.SWITCH.value,
    "Light": EntityTypes.LIGHT.value,
    "Fan": EntityTypes.FAN.value,
    "Sensor": EntityTypes.SENSOR.value,
    "Servo": EntityTypes.SERVO.value,
}

MAIN_SCHEMA = vol.Schema(
    {
        vol.Required("type"): vol.In(CONF_TYPES.keys()),
    }
)


def get_type(data: dict) -> str | None:
    return CONF_TYPES.get(data["type"]) if data is not None else None
