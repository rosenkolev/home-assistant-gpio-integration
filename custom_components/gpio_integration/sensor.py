from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .controllers.sensor import SensorRef
from .core import DOMAIN, ClosableMixin, get_logger
from .hub import Hub

_LOGGER = get_logger()


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add switch for passed config_entry in HA."""
    hub: Hub = hass.data[DOMAIN][config_entry.entry_id]
    sensors: list[SensorRef] = hub.sensors
    for sensor in sensors:
        async_add_entities([GpioSensor(sensor)])


class GpioSensor(ClosableMixin, SensorEntity):
    """Representation of a Raspberry Pi GPIO."""

    def __init__(self, sensor: SensorRef) -> None:
        """Initialize the pin."""
        self._attr_name = sensor.name
        self._attr_unique_id = sensor.id
        self._attr_native_unit_of_measurement = sensor.unit
        self._io = sensor

    @property
    def native_value(self) -> int | float:
        """Return true if device is on."""
        return self._io.state

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._io.device_id)},
            name=self._io.device_name,
            manufacturer="Raspberry Pi",
            model="GPIO",
            sw_version="1",
        )

    async def async_will_remove_from_hass(self) -> None:
        """Cleanup before removing from hass."""
        self._close()
        await super().async_will_remove_from_hass()
