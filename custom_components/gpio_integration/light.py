from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ColorMode,
    LightEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .config_schema import PwmConfig
from .const import DOMAIN, get_logger
from .gpio.pin_factory import create_pin
from .hub import Hub

_LOGGER = get_logger()
HIGH_BRIGHTNESS = 255


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add switch for passed config_entry in HA."""
    hub: Hub = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities([GpioLight(hub.config)])


class GpioLight(LightEntity):
    """Representation of a Raspberry Pi GPIO."""

    def __init__(self, config: PwmConfig) -> None:
        """Initialize the pin."""

        self._attr_name = config.name
        self._attr_unique_id = config.unique_id
        self._attr_should_poll = False

        self._io = create_pin(
            config.port,
            mode="output",
            frequency=config.frequency,
        )

        mode = ColorMode.BRIGHTNESS if self._io.pwm else ColorMode.ONOFF
        self._attr_supported_color_modes = {mode}
        self._attr_color_mode = mode
        self._brightness: int = -1

        self.brightness = HIGH_BRIGHTNESS if config.default_state else 0

    @property
    def led(self) -> bool:
        """Return if light is LED."""
        return self._io.pwm

    @property
    def is_on(self):
        """Return true if device is on."""
        return self._brightness > 0

    @property
    def brightness(self):
        """Return the brightness property."""
        return self._brightness

    @brightness.setter
    def brightness(self, value):
        """Set the brightness property."""
        if value != self._brightness:
            self._brightness = value
            self._io.state = self._to_state(value) if self.led else self.is_on
            self.schedule_update_ha_state()
            _LOGGER.debug(f"{self._io!s} light set to {self._io.state}")

    def _to_state(self, value):
        return round(float(value / HIGH_BRIGHTNESS), 4)

    async def async_will_remove_from_hass(self) -> None:
        """On entity remove release the GPIO resources."""
        await self._io.async_close()
        await super().async_will_remove_from_hass()

    def turn_on(self, **kwargs):
        """Turn on."""
        self.brightness = kwargs.get(ATTR_BRIGHTNESS, HIGH_BRIGHTNESS)

    def turn_off(self, **kwargs):
        """Turn off."""
        if self.is_on:
            self.brightness = 0
            _LOGGER.debug(f"{self._io!s} light turn off")
