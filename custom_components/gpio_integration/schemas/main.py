"""Main schema for the GPIO Integration."""

import voluptuous as vol

CONF_TYPES: dict = {
    "Cover with up and down button (optional sensor)": "cover_up_down",
    "Cover with toggle button (optional sensor)": "cover_toggle",
    "Binary sensor": "binary_sensor",
    "Switch": "switch",
    "Light": "light",
    "Fan": "fan",
    "Analog Sensor": "analog_sensor",
}

MAIN_SCHEMA = vol.Schema(
    {
        vol.Required("type"): vol.In(CONF_TYPES.keys()),
    }
)


def get_type(data: dict) -> str | None:
    return CONF_TYPES.get(data["type"]) if data is not None else None
