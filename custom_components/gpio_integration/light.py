from itertools import repeat
from typing import Iterable

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_EFFECT,
    ATTR_FLASH,
    EFFECT_OFF,
    FLASH_SHORT,
    ColorMode,
    LightEntity,
    LightEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .core import DOMAIN, GpioEffect, StoppableThread, get_logger
from .gpio.pin_factory import create_pin
from .hub import Hub
from .schemas.pwm import PwmConfig

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


BLINKS: dict = {
    "blink": {
        "on_time": 1,
        "off_time": 1,
        "times": 200,
    },
    "flash_short": {
        "on_time": 0.5,
        "off_time": 0.5,
        "times": 2,
    },
    "flash_long": {
        "on_time": 1.2,
        "off_time": 1.2,
        "times": 4,
    },
}


class BlinkEffect(GpioEffect):
    def compute_state(self, config: dict) -> Iterable[tuple[bool, float]]:
        if "times" not in config or "on_time" not in config or "off_time" not in config:
            raise ValueError(
                "Blink effect requires 'times', 'on_time' and 'off_time' parameters"
            )

        times = config["times"]
        iterable = repeat(0) if times is None else repeat(0, times)
        for _ in iterable:
            yield True, config["on_time"]
            yield False, config["off_time"]


# class PWMLed:
#     def __init__(self, pin, frequency):
#         self._io = create_pin(pin, mode="output", frequency=frequency)
#         self._brightness = 0

#     @property
#     def brightness(self):
#         return self._brightness

#     @brightness.setter
#     def brightness(self, value):
#         if value != self._brightness:
#             self._brightness = value
#             self._io.state = self._to_state(value)
#             _LOGGER.debug(f"{self._io!s} light set to {self._io.state}")

#     def _to_state(self, value):
#         return round(float(value / HIGH_BRIGHTNESS), 4)


class GpioLight(LightEntity):
    """Representation of a Raspberry Pi GPIO."""

    def __init__(self, config: PwmConfig) -> None:
        """Initialize the pin."""

        self._attr_name = config.name
        self._attr_unique_id = config.unique_id
        self._attr_should_poll = False
        self._attr_effect = EFFECT_OFF
        self._attr_effect_list = [EFFECT_OFF, "Blink"]
        self._attr_supported_features = (
            LightEntityFeature.FLASH | LightEntityFeature.EFFECT
        )

        self._io = create_pin(
            config.port,
            mode="output",
            frequency=config.frequency,
        )

        mode = ColorMode.BRIGHTNESS if self._io.pwm else ColorMode.ONOFF
        self._attr_supported_color_modes = {mode}
        self._attr_color_mode = mode
        self._brightness: int = -1
        self._blink_thread: StoppableThread | None = None
        self._effect = BlinkEffect()
        self._set_brightness(HIGH_BRIGHTNESS if config.default_state else 0, False)

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
        self._set_brightness(value)

    def _set_brightness(self, value, schedule_update=True):
        """Set the brightness property."""
        if value != self._brightness:
            self._brightness = value
            self._io.state = self._to_state(value) if self.led else self.is_on
            if schedule_update:
                self.schedule_update_ha_state()
            _LOGGER.debug(f"{self._io!s} light set to {self._io.state}")

    def _to_state(self, value):
        return round(float(value / HIGH_BRIGHTNESS), 4)

    async def async_will_remove_from_hass(self) -> None:
        """On entity remove release the GPIO resources."""
        self._blink_off()
        await self._io.async_close()
        await super().async_will_remove_from_hass()

    def turn_on(self, **kwargs):
        """Turn on."""
        self._blink_off()
        if ATTR_FLASH in kwargs:
            short = kwargs[ATTR_FLASH] == FLASH_SHORT
            blink = BLINKS["flash_short" if short else "flash_long"]
            self._blink(blink)
        elif ATTR_EFFECT in kwargs:
            effect_name = kwargs[ATTR_EFFECT]
            self._blink(BLINKS[effect_name])
        else:
            self.brightness = kwargs.get(ATTR_BRIGHTNESS, HIGH_BRIGHTNESS)
            _LOGGER.debug(f"{self._io!s} light turn on")

    def turn_off(self, **kwargs):
        """Turn off."""
        self._blink_off()
        if self.is_on:
            self.brightness = 0
            _LOGGER.debug(f"{self._io!s} light turn off")

    def _blink_off(self):
        """Blink off."""
        if self._blink_thread is not None:
            self._blink_thread.stop()
            self._blink_thread = None

    def _blink(self, config):
        """Blink."""
        self.turn_off()
        self._blink_thread = StoppableThread(target=self._blinker, args=(config,))
        self._blink_thread.start()

    def _blinker(self, config):
        """Blinker."""
        for state, duration in self._effect.compute_state(config):
            self._io.state = state
            if self._blink_thread.wait(duration):
                break
