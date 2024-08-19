"""Support for controlling a Raspberry Pi cover."""

from homeassistant.components.cover import (
    ATTR_POSITION,
    CoverEntity,
    CoverDeviceClass,
    CoverEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .hub import BasicToggleRoller, Hub, Roller


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add cover for passed config_entry in HA."""
    hub: Hub = hass.data[DOMAIN][config_entry.entry_id]
    if hub.is_cover:
        async_add_entities([GpioCover(hub.controller)])
    elif hub.is_cover_toggle:
        async_add_entities([GpioBasicCover(hub.controller)])


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


class GpioBasicCover(CoverEntity):
    def __init__(
        self,
        roller: BasicToggleRoller,
    ) -> None:
        """Initialize the cover."""
        self.__roller = roller
        self._attr_name = roller.name
        self._attr_unique_id = roller.id
        self._attr_assumed_state = True
        self._attr_has_entity_name = True
        self._attr_device_class = get_device_class(roller.config.mode)
        self._attr_supported_features = (
            CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE
        )

    @property
    def is_closed(self) -> bool:
        """Return if the cover is closed, same as position 0."""
        return self.__roller.is_closed

    async def async_will_remove_from_hass(self) -> None:
        """Release the resources."""
        await super().async_will_remove_from_hass()
        self.__roller.release()

    def update(self):
        """Update the cover state."""
        self.__roller.update_state()

    def close_cover(self, **kwargs):
        """Close the cover."""
        if not self.__roller.is_closed:
            self.__roller.toggle()

    def open_cover(self, **kwargs):
        """Open the cover."""
        if self.is_closed:
            self.__roller.toggle()


class GpioCover(CoverEntity):
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
    def current_cover_position(self):
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

    async def async_will_remove_from_hass(self) -> None:
        """Release the resources."""
        await super().async_will_remove_from_hass()
        self.__roller.release()

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
