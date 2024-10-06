import datetime
import time

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_time_interval

from ._devices import BinarySensor
from .core import DOMAIN, get_logger
from .hub import Hub
from .schemas.binary_sensor import BinarySensorConfig

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
    if mode == "Window":
        return BinarySensorDeviceClass.WINDOW
    if mode == "Motion":
        return BinarySensorDeviceClass.MOTION
    if mode == "Light":
        return BinarySensorDeviceClass.LIGHT
    if mode == "Vibration":
        return BinarySensorDeviceClass.VIBRATION
    if mode == "Plug":
        return BinarySensorDeviceClass.PLUG
    if mode == "Smoke":
        return BinarySensorDeviceClass.SMOKE

    return BinarySensorDeviceClass.DOOR


class GpioBinarySensor(BinarySensorEntity):
    """Represent a binary sensor that uses Raspberry Pi GPIO."""

    def __init__(self, config: BinarySensorConfig) -> None:
        """Initialize the RPi binary sensor."""
        self._attr_name = config.name
        self._attr_unique_id = config.unique_id
        self._attr_should_poll = False
        self._attr_device_class = get_device_class(config.mode)

        self._state = config.default_state
        self._rely_on_edge_events = config.edge_event_timeout_sec > 0
        self._edge_event_timeout_sec = config.edge_event_timeout_sec
        self._auto_update_interval_sec = config.edge_event_timeout_sec

        self._io = BinarySensor(
            config.pin,
            pull_up=config.pull_mode == "up",
            active_state=not config.invert_logic,
            bounce_time=config.bounce_time_ms / 1000,
        )

        self._io.when_activated = self.edge_detection_callback
        self._io.when_deactivated = self.edge_detection_callback

    @property
    def is_on(self) -> bool:
        return self._state

    @property
    def is_sensor_active(self) -> bool:
        event_time = self._io.last_event_time_sec
        return (event_time is not None) and (
            time.perf_counter() - event_time
        ) < self._edge_event_timeout_sec

    def edge_detection_callback(self, _=None) -> None:
        if not self._rely_on_edge_events or not self._state:
            _LOGGER.debug(f"{self._io!s} schedule state update")
            self.schedule_update_ha_state(force_refresh=True)

    def update(self):
        """Update the GPIO state."""
        if self._rely_on_edge_events:
            state = self.is_sensor_active == self._io.active_high
        else:
            state = self._io.value

        if state != self._state:
            self._state = state
            _LOGGER.debug("%s update %s", self._attr_name, self._state)

    ### HASS lifecycle hooks ###

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added."""
        await super().async_added_to_hass()
        if self._auto_update_interval_sec > 0:
            self._enable_state_auto_update()

    async def async_will_remove_from_hass(self) -> None:
        """On entity remove release the GPIO resources."""
        self._io.when_activated = None
        self._io.when_deactivated = None

        await self._io.close()
        await super().async_will_remove_from_hass()

    ### state auto-update logic ###

    def _enable_state_auto_update(self):
        _LOGGER.debug(f"{self._io!s} auto-update activated")
        timer_cancel = async_track_time_interval(
            self.hass,
            self._auto_update_callback,
            datetime.timedelta(seconds=self._auto_update_interval_sec),
            cancel_on_shutdown=True,
        )

        self.async_on_remove(timer_cancel)

    def _auto_update_callback(self):
        if self.is_sensor_active != self._state:
            _LOGGER.debug(f"{self._io!s} auto-update scheduled")
            self.schedule_update_ha_state(force_refresh=True)
