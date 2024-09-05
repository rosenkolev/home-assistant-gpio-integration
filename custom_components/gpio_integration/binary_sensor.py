import datetime
import time

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
from .gpio.pin_factory import create_pin

_LOGGER = get_logger()


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add binary sensor for passed config_entry in HA."""
    hub: Hub = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities([create_binary_sensor(hub.config)])


def create_binary_sensor(config: SensorConfig):
    """Create binary sensor based on config."""
    if config.mode == "Motion" or config.mode == "Vibration":
        return GpioMotionBinarySensor(config)
    return GpioBinarySensor(config)


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


class GpioBinarySensorBase(BinarySensorEntity):
    """Represent a binary sensor that uses Raspberry Pi GPIO."""

    def __init__(self, config: SensorConfig) -> None:
        """Initialize the RPi binary sensor."""
        self._attr_name = config.name
        self._attr_unique_id = config.unique_id
        self._attr_should_poll = False
        self._attr_device_class = get_device_class(config.mode)
        self._state = config.default_state
        self._io = create_pin(
            config.pin,
            mode="input",
            pull=config.pull_mode,
            edges="both",
            bounce=config.bounce_time_ms / 1000,
            default_value=config.default_state,
            when_changed=lambda _: self.edge_detection_callback(),
        )

    def edge_detection_callback(self):
        pass

    async def async_will_remove_from_hass(self) -> None:
        """On entity remove release the GPIO resources."""
        await self._io.async_close()
        await super().async_will_remove_from_hass()

    @property
    def is_on(self) -> bool:
        """Return the state of the entity."""
        return self._state


class GpioBinarySensor(GpioBinarySensorBase):
    """Represent a binary sensor that uses Raspberry Pi GPIO."""

    def __init__(self, config: SensorConfig) -> None:
        """Initialize the RPi binary sensor."""
        super().__init__(config)
        self.__invert_logic = config.invert_logic

    def edge_detection_callback(self):
        self.async_schedule_update_ha_state(force_refresh=True)

    def update(self):
        """Update the GPIO state."""
        self._state = self._io.state != self.__invert_logic
        _LOGGER.debug("%s update %s", self._attr_name, self._state)


class GpioMotionBinarySensor(GpioBinarySensorBase):
    """Represent a motion time of binary sensor that uses Raspberry Pi GPIO."""

    def __init__(self, config: SensorConfig) -> None:
        super().__init__(config)
        self.__motion_timeout_sec = config.edge_event_timeout_sec
        self.__event_time: float | None = None

    @property
    def last_motion_event_timeout(self) -> bool:
        return (
            self.__event_time is not None
            and (time.perf_counter() - self.__event_time) > self.__motion_timeout_sec
        )

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added."""
        await super().async_added_to_hass()
        timer_cancel = async_track_time_interval(
            self.hass,
            lambda tick: self.update(),
            datetime.timedelta(seconds=self.__motion_timeout_sec),
            cancel_on_shutdown=True,
        )

        self.async_on_remove(timer_cancel)

    def edge_detection_callback(self) -> None:
        self.set_on()
        self.__event_time = time.perf_counter()

    def update(self):
        if self.last_motion_event_timeout:
            """If no event detected for a while, set state to off."""
            self.set_off()

    def set_off(self):
        if self._state:
            self._state = False
            self.async_write_ha_state()

    def set_on(self):
        if not self._state:
            self._state = True
            self.async_write_ha_state()
