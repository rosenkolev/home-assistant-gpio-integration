from homeassistant.components.fan import (
    ATTR_PERCENTAGE,
    FanEntity,
    FanEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .core import DOMAIN, get_logger
from .gpio.pin_factory import create_pin
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


SUPPORT_SIMPLE_FAN = (
    FanEntityFeature.SET_SPEED | FanEntityFeature.TURN_ON | FanEntityFeature.TURN_OFF
)


class GpioFan(FanEntity):
    """Representation of a simple PWM FAN."""

    def __init__(self, config: PwmConfig) -> None:
        """Initialize PWM FAN."""
        self._attr_name = config.name
        self._attr_unique_id = config.unique_id
        self._attr_has_entity_name = True
        self._attr_should_poll = False
        self._attr_supported_features = SUPPORT_SIMPLE_FAN
        self._percentage = 0

        self._io = create_pin(
            config.port,
            mode="output",
            frequency=config.frequency,
        )

        if config.default_state:
            self.set_percentage(100)

    @property
    def is_on(self):
        """Return true if device is on."""
        return self._percentage > 0

    @property
    def percentage(self) -> int:
        """Return the percentage property."""
        return self._percentage

    def turn_on(self, percentage: None, **kwargs) -> None:
        """Turn on the fan."""
        if percentage is not None:
            self.set_percentage(percentage)
        elif ATTR_PERCENTAGE in kwargs:
            self.set_percentage(kwargs[ATTR_PERCENTAGE])
        else:
            self.set_percentage(100)

    def turn_off(self, **kwargs) -> None:
        """Turn off the fan."""
        self.set_percentage(0)
        _LOGGER.debug(f"{self._io!s} turn off")

    def set_percentage(self, percentage: int) -> None:
        """Set the speed percentage of the fan."""
        if percentage != self._percentage:
            self._percentage = percentage
            self._io.state = percentage / 100
            self.schedule_update_ha_state()
            _LOGGER.debug(f"{self._io!s} set to {percentage}")

    async def async_will_remove_from_hass(self) -> None:
        """On entity remove release the GPIO resources."""
        await self._io.async_close()
        await super().async_will_remove_from_hass()
