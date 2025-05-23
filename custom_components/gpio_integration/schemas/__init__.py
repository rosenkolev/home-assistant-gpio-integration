from typing import Literal

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_UNIQUE_ID
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.selector import selector

from ..core import DOMAIN

CONF_COVERS = "covers"
CONF_RELAY_CLOSE_PIN = "close_pin"
CONF_RELAY_CLOSE_INVERT = "close_pin_invert"
CONF_RELAY_OPEN_PIN = "open_pin"
CONF_RELAY_OPEN_INVERT = "open_pin_invert"
CONF_RELAY_TIME = "relay_time"
CONF_PIN_CLOSED_SENSOR = "pin_closed_sensor"
CONF_PIN_TRIGGER = "pin_trigger"
CONF_INVERT_LOGIC = "invert_logic"
CONF_BOUNCE_TIME = "bounce_time_in_ms"
CONF_DEFAULT_STATE = "default_state"
CONF_EDGE_EVENT_TIMEOUT = "edge_event_timeout"
CONF_FREQUENCY = "frequency"
CONF_INTERFACE = "interface"
CONF_VARIATION = "variation"

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

### Functions ###


def get_unique_id(data: dict) -> str | None:
    """Return unique id for the cover."""
    return data.get(CONF_UNIQUE_ID) or data[CONF_NAME].lower().replace(" ", "_") or None


# Selectors as described by https://www.home-assistant.io/docs/blueprint/selectors


def dropdown(
    options: list[dict[Literal["label", "value"], str]] | list[str],
    mode: Literal["dropdown", "list"] = "dropdown",
) -> vol.Schema:
    return selector(
        {
            "select": {
                "options": options,
                "mode": mode,
            }
        }
    )


def number_slider(min: int, max=100, step=1, unit="%"):
    return selector(
        {
            "number": {
                "min": min.__str__(),
                "max": max.__str__(),
                "step": step.__str__(),
                "unit_of_measurement": unit,
            }
        }
    )


### Exceptions ###


class InvalidPin(HomeAssistantError):
    """Error to indicate invalid pin."""


### Variations ###


def create_variation_list_schema(
    data: dict[str], variations: dict[str, str]
) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(
                CONF_VARIATION,
                default=data[CONF_VARIATION],
            ): dropdown(
                [
                    {
                        "label": label,
                        "value": key,
                    }
                    for key, label in variations.items()
                ],
                mode="list",
            )
        }
    )


EMPTY_VARIATION_DATA = {CONF_VARIATION: None}


def validate_variation_data(data: dict, variations: dict) -> bool:
    return data is not None and data[CONF_VARIATION] in variations.keys()
