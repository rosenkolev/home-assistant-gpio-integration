from homeassistant.components.switch import PLATFORM_SCHEMA, SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .hub import Hub, Switch
from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add switch for passed config_entry in HA."""
    hub: Hub = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities([GpioSwitch(hub.controller)])


class GpioSwitch(SwitchEntity):
    """Representation of a Raspberry Pi GPIO."""

    def __init__(self, switch: Switch) -> None:
        """Initialize the pin."""
        self._attr_name = switch.name
        self._attr_unique_id = switch.id
        self._attr_should_poll = False
        self.__switch = switch

    @property
    def is_on(self) -> bool | None:
        """Return true if device is on."""
        return self.__switch.state

    async def async_turn_on(self, **kwargs) -> None:
        """Turn the device on."""
        self.__switch.set_state(True)
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the device off."""
        self.__switch.set_state(False)
        self.async_write_ha_state()
