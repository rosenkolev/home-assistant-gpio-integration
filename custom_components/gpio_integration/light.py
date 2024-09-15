from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ColorMode,
    LightEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .config_schema import LightConfig
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

    def __init__(self, config: LightConfig) -> None:
        """Initialize the pin."""

        self._attr_name = config.name
        self._attr_unique_id = config.unique_id
        self._attr_should_poll = False

        self._io = create_pin(
            config.port,
            mode="output",
            frequency=config.frequency,
        )

        self._is_led = self._io.pwm
        mode = ColorMode.BRIGHTNESS if self._is_led else ColorMode.ONOFF
        self._attr_supported_color_modes = {mode}
        self._attr_color_mode = mode

        self._is_on = config.default_state
        self._brightness: int = HIGH_BRIGHTNESS if self._is_on else 0

    @property
    def is_on(self):
        """Return true if device is on."""
        return self._is_on

    @property
    def brightness(self):
        """Return the brightness property."""
        return self._brightness

    async def async_will_remove_from_hass(self) -> None:
        """On entity remove release the GPIO resources."""
        await self._io.async_close()
        await super().async_will_remove_from_hass()

    def turn_on(self, **kwargs):
        """Turn on a led."""
        state: float | bool | None = None
        brightness = None
        if self._is_led:
            brightness = kwargs.get(ATTR_BRIGHTNESS, HIGH_BRIGHTNESS)
            if brightness != self._brightness:
                self._brightness = brightness
                state = float(brightness / HIGH_BRIGHTNESS)
        elif not self._is_on:
            state = True
            brightness = 255

        if state is not None:
            self._brightness = brightness
            self._io.state = state
            self._is_on = True
            self.schedule_update_ha_state()
            _LOGGER.debug(f"light on pin {self._io.pin} set to {brightness}")

    def turn_off(self, **kwargs):
        """Turn off a LED."""
        if self.is_on:
            self._brightness = 0
            self._io.state = 0
            self._is_on = False
            self.schedule_update_ha_state()
            _LOGGER.debug(f"light on pin {self._io.pin} turn off")
