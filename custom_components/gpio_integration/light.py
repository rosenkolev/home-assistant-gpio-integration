from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_EFFECT,
    ATTR_FLASH,
    ATTR_RGB_COLOR,
    ATTR_WHITE,
    EFFECT_OFF,
    FLASH_SHORT,
    ColorMode,
    LightEntity,
    LightEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from ._devices import Pwm, RgbLight, Switch
from .core import DOMAIN, ClosableMixin, get_logger
from .hub import Hub
from .schemas.light import RgbLightConfig
from .schemas.main import EntityTypes
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
    if hub.is_type(EntityTypes.LIGHT_PWM_LED):
        async_add_entities([GpioLight(hub.config)])
    elif hub.is_type(EntityTypes.LIGHT_RGB_LED):
        async_add_entities([RgbGpioLight(hub.config)])


BLINKS: dict = {
    "blink": {
        "on_time": 1.2,
        "off_time": 1.2,
        "times": 200,
    },
    "flash_short": {
        "on_time": 1,
        "off_time": 1,
        "times": 2,
    },
    "flash_long": {
        "on_time": 1.5,
        "off_time": 1.5,
        "times": 4,
    },
}


def brightness_to_value(brightness: int) -> int:
    return round(float(brightness / HIGH_BRIGHTNESS), 4)


class BlinkMixin:
    def _blink(self, effect: str, pwm: bool):
        if effect not in BLINKS:
            raise ValueError(f"Unknown blink effect: {effect}")

        opts = BLINKS[effect]
        if "on_time" not in opts or "off_time" not in opts:
            raise ValueError(f"Invalid blink options: {effect}")

        _LOGGER.debug(f"{self._io!s} light blink {effect}")

        self.turn_off()

        on_time = opts["on_time"]
        off_time = opts["off_time"]
        if pwm:
            fade_time = 1
            self._io.blink(
                on_time=on_time - fade_time,
                off_time=off_time - fade_time,
                fade_in_time=fade_time,
                fade_out_time=fade_time,
                n=opts["times"],
            )
        else:
            self._io.blink(on_time=on_time, off_time=off_time, n=opts["times"])


class GpioLight(ClosableMixin, BlinkMixin, LightEntity):
    """Representation of a Raspberry Pi GPIO."""

    def __init__(self, config: PwmConfig) -> None:
        """Initialize the pin."""

        self._pwm = config.frequency is not None and config.frequency > 0

        self._attr_name = config.name
        self._attr_unique_id = config.unique_id
        self._attr_should_poll = False
        self._attr_effect = EFFECT_OFF
        self._attr_effect_list = [EFFECT_OFF, "Blink"]
        self._attr_supported_features = (
            LightEntityFeature.FLASH | LightEntityFeature.EFFECT
        )
        self._attr_color_mode = ColorMode.BRIGHTNESS if self._pwm else ColorMode.ONOFF
        self._attr_supported_color_modes = {self._attr_color_mode}

        if self._pwm:
            self._io = Pwm(
                config.port, config.frequency, initial_value=config.default_state
            )
        else:
            self._io = Switch(config.port, initial_value=config.default_state)

        self._brightness = HIGH_BRIGHTNESS if config.default_state else 0

    def __repr__(self) -> str:
        return f"{self._io!s}({self._attr_name})"

    @property
    def is_on(self) -> bool:
        return self._brightness > 0

    @property
    def brightness(self) -> int:
        """Return the brightness property."""
        return self._brightness

    @brightness.setter
    def brightness(self, value: int) -> None:
        if value != self._brightness:
            if value < 0 or value > HIGH_BRIGHTNESS:
                raise ValueError(f"brightness must be between 0 and {HIGH_BRIGHTNESS}")

            state = brightness_to_value(value) if self._pwm else value > 0
            self._brightness = value
            self._io.value = state
            self.async_write_ha_state()
            _LOGGER.debug(f"{self!r} light set to {state}")

    def turn_on(self, **kwargs):
        """Turn on."""
        if ATTR_FLASH in kwargs:
            short = kwargs[ATTR_FLASH] == FLASH_SHORT
            self._blink("flash_short" if short else "flash_long", self._pwm)
        elif ATTR_EFFECT in kwargs:
            effect_name = kwargs[ATTR_EFFECT]
            self._blink(effect_name, self._pwm)
        else:
            self.brightness = kwargs.get(ATTR_BRIGHTNESS, HIGH_BRIGHTNESS)

    def turn_off(self, **kwargs):
        self.brightness = 0

    async def async_will_remove_from_hass(self) -> None:
        self._close()
        await super().async_will_remove_from_hass()


RGB_WHITE = (HIGH_BRIGHTNESS, HIGH_BRIGHTNESS, HIGH_BRIGHTNESS)
RGB_OFF = (0, 0, 0)


class RgbGpioLight(ClosableMixin, BlinkMixin, LightEntity):
    def __init__(self, config: RgbLightConfig) -> None:
        """Initialize the pin."""

        self._attr_name = config.name
        self._attr_unique_id = config.unique_id
        self._attr_should_poll = False
        self._attr_color_mode = ColorMode.RGB
        self._attr_supported_color_modes = {
            ColorMode.RGB,
            ColorMode.BRIGHTNESS,
            ColorMode.ONOFF,
            ColorMode.WHITE,
        }
        self._attr_effect = EFFECT_OFF
        self._attr_effect_list = [EFFECT_OFF, "Blink"]
        self._attr_supported_features = (
            LightEntityFeature.FLASH | LightEntityFeature.EFFECT
        )

        self._brightness = HIGH_BRIGHTNESS if config.default_state else 0
        self._rgb = RGB_WHITE if config.default_state else RGB_OFF
        self._io = RgbLight(
            config.port_red,
            config.port_green,
            config.port_blue,
            initial_value=(1, 1, 1) if config.default_state else (0, 0, 0),
        )

    def __repr__(self) -> str:
        return f"{self._io!s}({self._attr_name})"

    @property
    def is_on(self) -> bool:
        """Return true if device is on."""
        return self._brightness > 0 and any(self._io.value)

    @property
    def rgb_color(self) -> tuple[int, int, int]:
        """Return the rgb color value."""
        return self._rgb

    @property
    def brightness(self) -> int:
        return self._brightness

    @brightness.setter
    def brightness(self, value: int) -> None:
        self._set(value, self._rgb)

    def turn_on(self, **kwargs) -> None:
        """Turn on."""
        self._blink_off()
        if ATTR_FLASH in kwargs:
            short = kwargs[ATTR_FLASH] == FLASH_SHORT
            self._blink("flash_short" if short else "flash_long", pwm=True)
        elif ATTR_EFFECT in kwargs:
            effect_name = kwargs[ATTR_EFFECT]
            self._blink(effect_name, pwm=True)
        elif (
            ATTR_BRIGHTNESS in kwargs
            or ATTR_RGB_COLOR in kwargs
            or ATTR_WHITE in kwargs
        ):
            brightness = kwargs.get(ATTR_BRIGHTNESS, self._brightness)
            rgb = kwargs.get(ATTR_RGB_COLOR, self._rgb)
            if ATTR_WHITE in kwargs:
                white: True | int = kwargs[ATTR_WHITE]
                rgb = RGB_WHITE
                if white > 0 and white <= HIGH_BRIGHTNESS:
                    brightness = white

            self._set(brightness, rgb)
        elif self._rgb == RGB_OFF:
            self._set(HIGH_BRIGHTNESS, RGB_WHITE)
        else:
            self.brightness = HIGH_BRIGHTNESS

    def turn_off(self, **kwargs) -> None:
        self.brightness = 0

    def _set(self, brightness: int, rgb: tuple[int, int, int]) -> None:
        if brightness < 0 or brightness > HIGH_BRIGHTNESS:
            raise ValueError(f"brightness must be between 0 and {HIGH_BRIGHTNESS}")

        if brightness != self._brightness or rgb != self._rgb:
            r = brightness_to_value(brightness)  # between 0 and 1
            value = tuple((v / HIGH_BRIGHTNESS) * r for v in rgb)
            self._rgb = rgb
            self._brightness = brightness
            self._io.value = value
            self.async_write_ha_state()
            _LOGGER.debug(f"{self!r} light set to {rgb}/{brightness} ({value})")

    async def async_will_remove_from_hass(self) -> None:
        self._close()
        await super().async_will_remove_from_hass()
