"""Support for controlling a Raspberry Pi cover."""

from time import sleep

from homeassistant.components.cover import (
    ATTR_POSITION,
    CoverDeviceClass,
    CoverEntity,
    CoverEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from ._base import ClosableMixin, DeviceMixin, ReprMixin
from ._devices import BinarySensor, Switch
from .core import DOMAIN
from .hub import Hub, Roller
from .schemas.cover import ToggleRollerConfig
from .schemas.main import EntityTypes


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add cover for passed config_entry in HA."""
    hub: Hub = hass.data[DOMAIN][config_entry.entry_id]
    if hub.is_type(EntityTypes.COVER_UP_DOWN):
        async_add_entities([GpioCover(hub.controller)])
    elif hub.is_type(EntityTypes.COVER_TOGGLE):
        async_add_entities([GpioBasicCover(hub.config)])


def get_device_class(mode: str) -> CoverDeviceClass:
    if mode == "Door":
        return CoverDeviceClass.DOOR
    if mode == "Garage":
        return CoverDeviceClass.GARAGE
    if mode == "Shade":
        return CoverDeviceClass.SHADE
    if mode == "Blind":
        return CoverDeviceClass.BLIND
    if mode == "Curtain":
        return CoverDeviceClass.CURTAIN


class GpioBasicCover(ClosableMixin, ReprMixin, CoverEntity):
    def __init__(
        self,
        config: ToggleRollerConfig,
    ) -> None:
        """Initialize the cover."""
        self._attr_name = config.name
        self._attr_unique_id = config.unique_id
        self._attr_assumed_state = True
        self._attr_has_entity_name = True
        self._attr_device_class = get_device_class(config.mode)
        self._attr_supported_features = (
            CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE
        )

        self._has_sensor = config.pin_closed is not None
        self._io_sensor = BinarySensor(config.pin_closed) if self._has_sensor else None

        self._io = Switch(
            config.port,
            active_high=not config.invert_logic,
            initial_value=False,
        )

        self._closed = self._io_sensor.is_active if self._has_sensor else True
        self._relay_time = config.relay_time

    @property
    def is_closed(self) -> bool:
        """Return if the cover is closed, same as position 0."""
        return self._closed

    def update(self):
        if self._has_sensor:
            self._closed = self._io_sensor.value

    def close_cover(self, **kwargs):
        """Close the cover."""
        if not self.is_closed:
            self._toggle()

    def open_cover(self, **kwargs):
        """Open the cover."""
        if self.is_closed:
            self._toggle()

    def _toggle(self):
        """Trigger the cover."""
        self._io.value = True
        sleep(self._relay_time)
        self._io.value = False
        if not self._has_sensor:
            self._closed = not self._closed

    def _close(self):
        super()._close()
        if self._io_sensor is not None:
            self._io_sensor.close()
            self._io_sensor = None

    async def async_will_remove_from_hass(self) -> None:
        self._close()
        await super().async_will_remove_from_hass()


class GpioCover(ClosableMixin, ReprMixin, DeviceMixin, CoverEntity):
    """Representation of a Raspberry GPIO cover."""

    def __init__(
        self,
        roller: Roller,
    ) -> None:
        """Initialize the cover."""
        self.__roller = roller
        self._attr_name = roller.name
        self._attr_unique_id = roller.id
        self._attr_assumed_state = True
        self._attr_has_entity_name = True
        self._attr_device_class = get_device_class(roller.config.mode)
        self._attr_supported_features = (
            CoverEntityFeature.OPEN
            | CoverEntityFeature.CLOSE
            | CoverEntityFeature.STOP
            | CoverEntityFeature.SET_POSITION
        )

    @property
    def current_cover_position(self) -> int:
        """Return the current position of the cover."""
        return self.__roller.position

    @property
    def is_closed(self) -> bool:
        """Return if the cover is closed, same as position 0."""
        return self.__roller.is_closed

    @property
    def is_closing(self) -> bool:
        """Return if the cover is closing or not."""
        return self.__roller.moving < 0

    @property
    def is_opening(self) -> bool:
        """Return if the cover is opening or not."""
        return self.__roller.moving > 0

    def update(self):
        """Update the cover state."""
        self.__roller.update_state()

    def close_cover(self, **kwargs):
        """Close the cover."""
        self.__roller.close()

    def open_cover(self, **kwargs):
        """Open the cover."""
        self.__roller.open()

    def stop_cover(self, **kwargs):
        """Stop the cover."""
        self.__roller.stop()

    def set_cover_position(self, **kwargs):
        """Move the cover to a specific position."""
        self.__roller.set_position(kwargs[ATTR_POSITION])

    def _close(self):
        if self.__roller is not None:
            self.__roller.release()
            self.__roller = None

    async def async_will_remove_from_hass(self) -> None:
        """Release the resources."""
        self._close()
        await super().async_will_remove_from_hass()
