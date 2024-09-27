from typing import Literal

from ..core import get_logger
from ..gpio.pin_factory import create_pin
from ..schemas.sensor import (
    AnalogRangeSensorConfig,
    AnalogSensorConfig,
    SpiSensorConfig,
)

_LOGGER = get_logger()


class SensorRef:
    def __init__(self, controller, name: str, id: str, unit: str) -> None:
        self._controller = controller
        self.name = name
        self.id = id
        self.unit = unit

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
            _LOGGER.debug("Creating analog sensor controller")
            self.controller = AnalogSensorController(config)
        elif type == "analog_range_sensor":
            _LOGGER.debug("Creating analog range sensor controller")
            self.controller = AnalogRangeSensorController(config)
        elif type == "spi_sensor":
            _LOGGER.debug("Creating SPI sensor controller")
            self.controller = SPISensorController
        else:
            raise ValueError(f"Unknown sensor type: {type}")

        self.sensors = self.controller.get_sensors()


class BaseController:
    def get_sensors(self) -> list[SensorRef]:
        raise NotImplementedError

    def get_state(self):
        raise NotImplementedError

    async def async_close(self) -> None:
        if self._io is not None:
            await self._io.async_close()
            self._io = None


class AnalogSensorController(BaseController):
    def __init__(self, config: AnalogSensorConfig) -> None:
        self.name = config.name
        self.id = config.unique_id
        self._min_voltage = config.min_voltage_mv
        self._min_value = config.min_value
        self._voltage_step = config.voltage_step_mv
        self._io = create_pin(config.port)

    def get_sensors(self):
        return [SensorRef(self, self.name, self.id, "C")]

    def get_state(self) -> float:
        val: float = self._io.read()
        mV = (val * 3300) / 1024.0
        base_mV = mV - self._min_voltage
        if base_mV < 0:
            return self._min_value

        return self._min_value + (base_mV / self._voltage_step)


class AnalogRangeSensorController(BaseController):
    def __init__(self, config: AnalogRangeSensorConfig) -> None:
        self.name = config.name
        self.id = config.unique_id
        self.default_state = config.default_state
        self.ranges: dict[str, tuple[int, int]] = dict()

        # example "2300|GAS|2600|SMOKE|3300"
        list = config.ranges.split("|")
        for i in range(1, len(list), 2):
            self.ranges[list[i]] = (int(list[i - 1]), int(list[i + 1]))

        self._io = create_pin(config.port)

    def get_sensors(self):
        return [SensorRef(self, self.name, self.id, None)]

    def get_state(self) -> str:
        val: float = self._io.read()
        mV = (val * 3300) / 1024.0
        for key, value in self.ranges.items():
            if value[0] <= mV <= value[1]:
                return key

        return self.default_state


class SPISensorController(BaseController):
    def __init__(self, config: SpiSensorConfig) -> None:
        """Initialize the SPI sensor."""

    def get_sensors(self):
        return []

    def get_state(self):
        return None
