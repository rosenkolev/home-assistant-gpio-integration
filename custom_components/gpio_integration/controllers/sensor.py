from typing import Literal

from ..core import get_logger
from ..gpio.pin_factory import create_pin
from ..schemas.sensor import AnalogSensorConfig

__LOGGER = get_logger()


class SensorRef:
    def __init__(self, controller, name: str, id: str) -> None:
        self._controller = controller
        self.name = name
        self.id = id

    @property
    def state(self):
        return self.controller.get_state(self.id)

    async def async_close(self):
        if self._controller is not None:
            await self._controller.async_close(self.id)
            self._controller = None


class SensorsHub:
    def __init__(self, type: Literal["analog_sensor", "spi"], config) -> None:
        if type == "analog_sensor":
            self.controller = AnalogSensorController(config)
        else:
            raise ValueError(f"Unknown sensor type: {type}")

        self.sensors = self.controller.get_sensors()


class AnalogSensorController:
    def __init__(self, config: AnalogSensorConfig) -> None:
        self.name = config.name
        self.id = config.unique_id
        # self.__state: bool = False
        self.__io = create_pin(config.port, mode="input")

    def get_sensors(self):
        return [SensorRef(self.get_state)]

    def get_state(self, id):
        return 0

    async def async_close(self):
        if self.__io is not None:
            await self.__io.async_close()
            self.__io = None

    def update(self):
        """Update the state of the sensor."""
