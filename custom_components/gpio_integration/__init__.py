"""Load Platform integration."""

from multiprocessing import get_logger

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_HOMEASSISTANT_STOP, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .config_schema import DOMAIN_DEFAULT_CONFIG
from .const import DOMAIN
from .gpio import close_all_pins, set_config_options
from .hub import Hub

PLATFORMS = [
    Platform.COVER,
    Platform.NUMBER,
    Platform.BINARY_SENSOR,
    Platform.SWITCH,
    Platform.LIGHT,
]

# Schema to validate the configuration for this integration
CONFIG_SCHEMA = DOMAIN_DEFAULT_CONFIG

def setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Raspberry PI GPIO component."""

    if DOMAIN in config:
        data = config[DOMAIN]
        set_config_options(data)

    def cleanup_gpio(event):
        """Stuff to do before stopping."""
        close_all_pins()

    hass.bus.listen_once(EVENT_HOMEASSISTANT_STOP, cleanup_gpio)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up from a config entry."""
    hub = Hub(entry.data)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = hub

    # This creates each HA object for each platform your device requires.
    # It's done by calling the `async_setup_entry` function in each platform module.
    await hass.config_entries.async_forward_entry_setups(entry, hub.platforms)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # This is called when an entry/configured device is to be removed. The class
    # needs to unload itself, and remove callbacks. See the classes for further
    # details
    platforms = hass.data[DOMAIN][entry.entry_id].platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, platforms)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
