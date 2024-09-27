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

from .core import DOMAIN, get_logger
from .gpio.pin_factory import create_pin
from .hub import Hub
from .schemas.binary_sensor import BinarySensorConfig

_LOGGER = get_logger()
_LAST_EVENT_TIME: dict[int, float | None] = dict()


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

    def __init__(self, config: BinarySensorConfig) -> None:
        """Initialize the RPi binary sensor."""
        self._attr_name = config.name
        self._attr_unique_id = config.unique_id
        self._attr_should_poll = False
        self._attr_device_class = get_device_class(config.mode)

        self._state = config.default_state
        self._invert_logic = config.invert_logic
        self._rely_on_edge_events = config.rely_on_edge_events
        self._edge_event_timeout_sec = config.edge_event_timeout_sec
        self._auto_update_interval_sec = config.edge_event_timeout_sec

        self._io = create_pin(
            config.pin,
            mode="input",
            pull=config.pull_mode,
            edges="both",
            bounce=config.bounce_time_ms / 1000,
            default_value=config.default_state,
            when_changed=self.edge_detection_callback,
        )

        # reset event time
        self.event_time = None

    @property
    def is_on(self) -> bool:
        """Return the state of the entity."""
        return self._state

    @property
    def event_time(self) -> float | None:
        global _LAST_EVENT_TIME
        return _LAST_EVENT_TIME[self._io.pin]

    @event_time.setter
    def event_time(self, time: float | None):
        global _LAST_EVENT_TIME
        _LAST_EVENT_TIME[self._io.pin] = time

    @property
    def state_change_is_required(self) -> bool:
        event_time = self.event_time
        if event_time is None:
            return False

        timeout = self._edge_event_timeout_sec
        expired = (time.perf_counter() - event_time) > timeout
        return (expired and self._state) or (not expired and not self._state)

    def edge_detection_callback(self, _=None) -> None:
        self.event_time = time.perf_counter()
        if self._rely_on_edge_events:
            if not self._state:
                _LOGGER.debug(f"{self._io!s} schedule state update")
                self.schedule_update_ha_state(force_refresh=True)
        else:
            _LOGGER.debug(f"{self._io!s} schedule state update")
            self.async_schedule_update_ha_state(force_refresh=True)

    def update(self):
        """Update the GPIO state."""
        if self._rely_on_edge_events:
            if self.state_change_is_required:
                self._state = not self._state
                _LOGGER.debug(f"{self._io!s} state updated to {self._state}")
        else:
            self._state = self._io.state != self._invert_logic
            _LOGGER.debug("%s update %s", self._attr_name, self._state)

    ### HASS lifecycle hooks ###

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added."""
        await super().async_added_to_hass()
        if self._auto_update_interval_sec > 0:
            self._enable_state_auto_update()

    async def async_will_remove_from_hass(self) -> None:
        """On entity remove release the GPIO resources."""
        await self._io.async_close()
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
        if self.state_change_is_required:
            _LOGGER.debug(f"{self._io!s} auto-update scheduled")
            self.schedule_update_ha_state(force_refresh=True)
