from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .hub import Hub, Sensor
from .const import DOMAIN

import asyncio


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add binary sensor for passed config_entry in HA."""
    hub: Hub = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities([GpioBinarySensor(hub.controller)])


class GpioBinarySensor(BinarySensorEntity):
    """Represent a binary sensor that uses Raspberry Pi GPIO."""

    async def async_read_gpio(self):
        """Read state from GPIO."""
        await asyncio.sleep(self.__sensor.bounce_time_sec)
        await self.hass.async_add_executor_job(self.__sensor.update)
        self.async_write_ha_state()

    def edge_detected(self):
        """Edge detection handler."""
        if self.hass is not None:
            self.hass.add_job(self.async_read_gpio)

    def __init__(self, sensor: Sensor) -> None:
        """Initialize the RPi binary sensor."""
        self._attr_name = sensor.name
        self._attr_unique_id = sensor.id
        self._attr_should_poll = False
        self.__sensor = sensor
        self.__sensor.add_detection(self.edge_detected)

    @property
    def is_on(self):
        """Return the state of the entity."""
        return self.__sensor.is_on

    def update(self):
        """Update the GPIO state."""
        self.__sensor.update()
