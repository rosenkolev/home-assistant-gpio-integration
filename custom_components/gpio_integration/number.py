from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from ._base import ClosableMixin, DeviceMixin, ReprMixin
from ._devices import Servo
from .core import DOMAIN, get_logger
from .hub import Hub, Roller
from .schemas.main import EntityTypes
from .schemas.servo import ServoConfig

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
    elif hub.is_type(EntityTypes.SERVO):
        async_add_entities([GpioServo(hub.config)])


class GpioPosition(ClosableMixin, ReprMixin, DeviceMixin, NumberEntity):
    def __init__(self, roller: Roller) -> None:
        """Initialize the cover."""
        self._io = roller
        self._attr_name = roller.name
        self._attr_unique_id = roller.id
        self._attr_native_step = roller.step
        self._attr_native_unit_of_measurement = "%"

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


class GpioServo(ClosableMixin, ReprMixin, DeviceMixin, NumberEntity):
    def __init__(self, config: ServoConfig) -> None:
        """Initialize the servo."""
        self._attr_name = config.name
        self._attr_unique_id = config.unique_id
        self._attr_should_poll = False
        self._attr_native_step = 1
        self._attr_native_unit_of_measurement = "°"
        self._io = Servo(
            config.port,
            initial_angle=config.default_angle,
            min_angle=config.min_angle,
            max_angle=config.max_angle,
            min_pulse_width_ms=config.min_duty_cycle,
            max_pulse_width_ms=config.max_duty_cycle,
            frame_width_ms=1000 / config.frequency,
        )

    @property
    def native_value(self):
        """Return the current servo angle."""
        return self._io.angle

    async def async_will_remove_from_hass(self) -> None:
        """Cleanup before removing from hass."""
        self._close()
        await super().async_will_remove_from_hass()

    def set_native_value(self, value: int) -> None:
        """Update the current value."""
        self._io.angle = int(value)
        _LOGGER.debug(f"{self!r} set angle to {value}")
