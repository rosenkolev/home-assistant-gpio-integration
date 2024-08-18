from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .hub import Hub, Roller
from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add cover for passed config_entry in HA."""
    hub: Hub = hass.data[DOMAIN][config_entry.entry_id]
    if hub.is_cover:
        async_add_entities([GpioPosition(hub.controller)])


class GpioPosition(NumberEntity):
    def __init__(self, roller: Roller) -> None:
        """Initialize the cover."""
        self.__roller = roller
        self._attr_name = roller.name
        self._attr_unique_id = roller.id
        self._attr_native_step = roller.step
        self._attr_native_unit_of_measurement = "%"

    @property
    def native_value(self):
        """Return the current position of the cover."""
        return self.__roller.position

    def set_native_value(self, value: float) -> None:
        """Update the current value."""
        self.__roller.set_position(int(value))
