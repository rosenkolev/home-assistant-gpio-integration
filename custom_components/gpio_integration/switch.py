from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .hub import Hub
from .const import DOMAIN, get_logger
from .config_schema import SwitchConfig
from .gpio import Gpio

_LOGGER = get_logger()


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add switch for passed config_entry in HA."""
    hub: Hub = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities([GpioSwitch(hub.config)])


class GpioSwitch(SwitchEntity):
    """Representation of a Raspberry Pi GPIO."""

    def __init__(self, config: SwitchConfig) -> None:
        """Initialize the pin."""
        self._attr_name = config.name
        self._attr_unique_id = config.unique_id
        self._attr_should_poll = False
        self.__state = config.default_state
        self.__invert_logic = config.invert_logic
        self.__io = Gpio(config.port, mode="write")

    @property
    def is_on(self) -> bool | None:
        """Return true if device is on."""
        return self.__state

    async def async_will_remove_from_hass(self) -> None:
        """Cleanup before removing from hass."""
        await super().async_will_remove_from_hass()
        self.__io.release()

    def set_state(self, state) -> None:
        value = not self.__invert_logic if state else self.__invert_logic
        _LOGGER.debug('switch "%s" set high to %s', self._attr_name, value)
        self.__io.write(value)
        self.__state = state

    async def async_turn_on(self, **kwargs) -> None:
        """Turn the device on."""
        self.set_state(True)
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the device off."""
        self.set_state(False)
        self.async_write_ha_state()
