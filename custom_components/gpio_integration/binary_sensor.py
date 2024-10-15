import datetime

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_time_interval

from ._devices import BinarySensor
from .core import DOMAIN, ClosableMixin, get_logger
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


class GpioBinarySensor(ClosableMixin, BinarySensorEntity):
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
            active_high=not config.invert_logic,
            bounce_time=config.bounce_time_ms / 1000,
        )

        self._io.on_state_changed = self.edge_detection_callback
        self._event_occurred = False

    @property
    def is_on(self) -> bool:
        return self._state

    @property
    def is_sensor_active(self) -> bool:
        event_time = self._io.any_event_time_sec
        return self._event_occurred and event_time < self._edge_event_timeout_sec

    def edge_detection_callback(self, io: BinarySensor) -> None:
        self._event_occurred = True
        if not self._rely_on_edge_events or (not self._state and io.is_active):
            _LOGGER.debug(f"{self!r} schedule update")
            self.schedule_update_ha_state(force_refresh=True)

    def update(self):
        """Update the GPIO state."""
        if self._rely_on_edge_events:
            state = self.is_sensor_active
        else:
            state = self._io.is_active

        if state != self._state:
            self._state = state
            _LOGGER.debug(f"{self!r} updated to '{self._state}'")

    ### HASS lifecycle hooks ###

    def _close(self) -> None:
        self._io.on_state_changed = None
        super()._close()

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added."""
        await super().async_added_to_hass()
        if self._auto_update_interval_sec > 0:
            self._enable_state_auto_update()

    async def async_will_remove_from_hass(self) -> None:
        """On entity remove release the GPIO resources."""
        self._close()
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

    def _auto_update_callback(self, _=None):
        if self.is_sensor_active != self._state:
            _LOGGER.debug(f"{self._io!s} auto-update scheduled")
            self.schedule_update_ha_state(force_refresh=True)

    def __repr__(self) -> str:
        return f"{self._io!s}({self._attr_name})"
