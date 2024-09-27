import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_UNIQUE_ID
from homeassistant.exceptions import HomeAssistantError

from ..core import DOMAIN

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

### Functions ###


def get_unique_id(data: dict) -> str | None:
    """Return unique id for the cover."""
    return data.get(CONF_UNIQUE_ID) or data[CONF_NAME].lower().replace(" ", "_") or None


### Exceptions ###


class InvalidPin(HomeAssistantError):
    """Error to indicate invalid pin."""