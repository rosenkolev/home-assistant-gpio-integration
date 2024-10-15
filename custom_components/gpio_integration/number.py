from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .core import DOMAIN, ClosableMixin, ReprMixin, get_logger
from .hub import Hub, Roller
from .schemas.main import EntityTypes

_LOGGER = get_logger()


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add cover for passed config_entry in HA."""
    hub: Hub = hass.data[DOMAIN][config_entry.entry_id]
    if hub.is_type(EntityTypes.COVER_UP_DOWN):
        async_add_entities([GpioPosition(hub.controller)])


class GpioPosition(ClosableMixin, ReprMixin, NumberEntity):
    def __init__(self, roller: Roller) -> None:
        """Initialize the cover."""
        self._io = roller
        self._attr_name = roller.name
        self._attr_unique_id = roller.id
        self._attr_native_step = roller.step
        self._attr_native_unit_of_measurement = "%"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self.unique_id)},
            name=self.name,
            manufacturer="Raspberry Pi",
            model="GPIO",
            sw_version="1",
        )

    @property
    def native_value(self):
        """Return the current position of the cover."""
        return self._io.position

    def _close(self) -> None:
        if self._io is not None:
            self._io.release()
            self._io = None

    async def async_will_remove_from_hass(self) -> None:
        """Cleanup before removing from hass."""
        self._close()
        await super().async_will_remove_from_hass()

    def set_native_value(self, value: float) -> None:
        """Update the current value."""
        self._io.set_position(int(value))
        _LOGGER.debug(f"{self!r} set position to {value}")
