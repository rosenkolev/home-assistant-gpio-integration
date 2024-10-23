from homeassistant.components.fan import (
    ATTR_PERCENTAGE,
    FanEntity,
    FanEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from ._base import ClosableMixin, ReprMixin
from ._devices import PwmFromPercent
from .core import DOMAIN, get_logger
from .hub import Hub
from .schemas.pwm import PwmConfig

_LOGGER = get_logger()


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add switch for passed config_entry in HA."""
    hub: Hub = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities([GpioFan(hub.config)])


class GpioFan(ClosableMixin, ReprMixin, FanEntity):
    """Representation of a simple PWM FAN."""

    def __init__(self, config: PwmConfig) -> None:
        """Initialize PWM FAN."""
        self._attr_name = config.name
        self._attr_unique_id = config.unique_id
        self._attr_has_entity_name = True
        self._attr_should_poll = False
        self._attr_supported_features = (
            FanEntityFeature.SET_SPEED
            | FanEntityFeature.TURN_ON
            | FanEntityFeature.TURN_OFF
        )

        if config.frequency is None or config.frequency <= 0:
            raise ValueError("Frequency must be greater than 0")

        self._io = PwmFromPercent(
            config.port, frequency=config.frequency, initial_value=config.default_state
        )

    @property
    def is_on(self):
        """Return true if device is on."""
        return self._io.is_active

    @property
    def percentage(self) -> int:
        """Return the percentage property."""
        return self._io.percentage

    def set_percentage(self, percentage: int) -> None:
        """Set the percentage property."""
        if self._io.percentage != percentage:
            self._io.percentage = percentage
            self.async_write_ha_state()
            _LOGGER.debug(f"{self!r} set to {percentage}%")

    def turn_on(self, percentage: None, **kwargs) -> None:
        """Turn on the fan."""
        if percentage is not None:
            self.set_percentage(percentage)
        elif ATTR_PERCENTAGE in kwargs:
            self.set_percentage(kwargs[ATTR_PERCENTAGE])
        else:
            self._io.on()

    def turn_off(self, **kwargs) -> None:
        """Turn off the fan."""
        if self._io.is_active:
            self._io.off()
            self.async_write_ha_state()
            _LOGGER.debug(f"{self!r} turn off")

    async def async_will_remove_from_hass(self) -> None:
        """On entity remove release the GPIO resources."""
        self._close()
        await super().async_will_remove_from_hass()
