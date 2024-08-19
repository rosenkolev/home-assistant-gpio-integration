"""Load Platform integration."""

from custom_components.gpio_integration.config_schema import RollerConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from homeassistant.const import (
    EVENT_HOMEASSISTANT_START,
    EVENT_HOMEASSISTANT_STOP,
    Platform,
)

from .hub import Hub
from .const import DOMAIN

PLATFORMS = [Platform.COVER, Platform.NUMBER, Platform.BINARY_SENSOR, Platform.SWITCH]


def setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Raspberry PI GPIO component."""

    def cleanup_gpio(event):
        """Stuff to do before stopping."""

    def prepare_gpio(event):
        """Stuff to do when Home Assistant starts."""

    hass.bus.listen_once(EVENT_HOMEASSISTANT_START, prepare_gpio)
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
