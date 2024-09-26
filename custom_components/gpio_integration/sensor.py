from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .controllers.sensor import SensorRef
from .core import DOMAIN, get_logger
from .hub import Hub

_LOGGER = get_logger()


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add switch for passed config_entry in HA."""
    hub: Hub = hass.data[DOMAIN][config_entry.entry_id]
    sensors: list[SensorRef] = hub.controller.sensors
    for sensor in sensors:
        async_add_entities([GpioSensor(sensor)])


class GpioSensor(SensorEntity):
    """Representation of a Raspberry Pi GPIO."""

    def __init__(self, sensor: SensorRef) -> None:
        """Initialize the pin."""
        self._attr_name = sensor.name
        self._attr_unique_id = sensor.id
        self._attr_should_poll = False
        self._sensor = sensor
        # self._attr_native_unit_of_measurement = sensor.unit
        # self._attr_device_class = ??

    @property
    def native_value(self) -> int | float:
        """Return true if device is on."""
        return self._sensor.state

    async def async_will_remove_from_hass(self) -> None:
        """Cleanup before removing from hass."""
        await super().async_will_remove_from_hass()
        await self._sensor.async_close()
