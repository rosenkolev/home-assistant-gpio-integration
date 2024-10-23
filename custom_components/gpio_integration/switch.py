from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from ._base import ClosableMixin, ReprMixin
from ._devices import Switch
from .core import DOMAIN, get_logger
from .hub import Hub
from .schemas.switch import SwitchConfig

_LOGGER = get_logger()


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add switch for passed config_entry in HA."""
    hub: Hub = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities([GpioSwitch(hub.config)])


class GpioSwitch(ClosableMixin, ReprMixin, SwitchEntity):
    def __init__(self, config: SwitchConfig) -> None:
        """Initialize the pin."""
        self._attr_name = config.name
        self._attr_unique_id = config.unique_id
        self._attr_should_poll = False
        self._io = Switch(
            config.port,
            active_high=not config.invert_logic,
            initial_value=config.default_state,
        )

    @property
    def is_on(self) -> bool | None:
        """Return true if device is on."""
        return self._io.is_active

    def turn_on(self, **kwargs) -> None:
        """Turn the device on."""
        if not self._io.is_active:
            self._io.on()
            self.async_write_ha_state()
            _LOGGER.debug(f"{self!r} turn on")

    def turn_off(self, **kwargs) -> None:
        """Turn the device off."""
        if self._io.is_active:
            self._io.off()
            self.async_write_ha_state()
            _LOGGER.debug(f"{self!r} turn off")

    async def async_will_remove_from_hass(self) -> None:
        """Cleanup before removing from hass."""
        self._close()
        await super().async_will_remove_from_hass()
