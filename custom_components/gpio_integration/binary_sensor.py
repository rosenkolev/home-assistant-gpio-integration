import datetime

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorDeviceClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_time_interval

from .hub import Hub
from .const import DOMAIN, get_logger
from .config_schema import SensorConfig
from .gpio import Gpio

_LOGGER = get_logger()


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add binary sensor for passed config_entry in HA."""
    hub: Hub = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities([GpioBinarySensor(hub.config)])


def get_device_class(mode: str) -> BinarySensorDeviceClass:
    if mode == "Door":
        return BinarySensorDeviceClass.DOOR
    if mode == "Motion":
        return BinarySensorDeviceClass.MOTION
    if mode == "Light":
        return BinarySensorDeviceClass.LIGHT
    if mode == "Vibration":
        return BinarySensorDeviceClass.VIBRATION
    if mode == "Plug":
        return BinarySensorDeviceClass.PLUG

    return BinarySensorDeviceClass.DOOR


class GpioBinarySensor(BinarySensorEntity):
    """Represent a binary sensor that uses Raspberry Pi GPIO."""

    def __init__(self, config: SensorConfig) -> None:
        """Initialize the RPi binary sensor."""
        self._attr_name = config.name
        self._attr_unique_id = config.unique_id
        self._attr_should_poll = False
        self._attr_device_class = get_device_class(config.mode)
        self.__invert_logic = config.invert_logic
        self.__state = None
        self.__bounce_time = config.bounce_time_ms
        self.__io = Gpio(
            config.pin,
            mode="read",
            pull_mode=config.pull_mode,
            edge_detect="BOTH",
            debounce_ms=config.bounce_time_ms,
        )

    async def _detect_edges(self, time=None):
        if self.__io.read_edge_events():
            _LOGGER.debug("%s events", self._attr_name)
            self.async_schedule_update_ha_state(force_refresh=True)

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added."""
        await super().async_added_to_hass()
        async_track_time_interval(
            self.hass,
            self._detect_edges,
            datetime.timedelta(milliseconds=self.__bounce_time),
            cancel_on_shutdown=True,
        )

    async def async_will_remove_from_hass(self) -> None:
        await super().async_will_remove_from_hass()
        self.__io.release()

    @property
    def is_on(self):
        """Return the state of the entity."""
        return self.__state != self.__invert_logic

    def update(self):
        """Update the GPIO state."""
        self.__state = self.__io.read()
        _LOGGER.debug("%s update %s", self._attr_name, self.__state)
