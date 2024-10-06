from collections import deque
from time import sleep
from typing import Literal

from .._devices import SerialDataInputDevice
from ..core import get_logger
from ..schemas.main import EntityTypes
from ..schemas.sensor import SensorSerialConfig

_LOGGER = get_logger()


class StateProvider:
    def get_state(self, id: str) -> float:
        raise NotImplementedError()

    def release(self) -> None:
        raise NotImplementedError()


class SensorRef:
    def __init__(
        self, controller: StateProvider, name: str, id: str, unit: str
    ) -> None:
        self._controller = controller
        self.name = name
        self.id = id
        self.unit = unit

    @property
    def state(self):
        return self._controller.get_state(self.id)

    def release(self):
        if self._controller is not None:
            self._controller.release()
            self._controller = None


class ControllerBase(StateProvider):
    def get_sensors(self) -> list[SensorRef]:
        raise NotImplementedError

    def release(self) -> None:
        if hasattr(self, "_io") and self._io is not None:
            self._io.close()
            self._io = None


class SensorsHub:
    def __init__(self, type: EntityTypes, config: dict) -> None:
        if type == EntityTypes.SENSOR_SERIAL_DATA:
            _LOGGER.debug("Creating serial data sensor controller")
            controller = SerialDataSensorController(SensorSerialConfig(config))
        else:
            raise ValueError(f"Unknown sensor type: {type}")

        self.sensors = controller.get_sensors()


class SerialDataSensorController(ControllerBase):
    def __init__(self, config: SensorSerialConfig) -> None:
        self.name = config.name
        self.id = config.unique_id
        self._temperature_id = f"{self.id}_T"
        self._humidity_id = f"{self.id}_H"
        self._signal_activate_ms = [(False, 18.0), (True, 0.04)]
        self._zero_high_ms = (True, 0.026)
        self._one_high_ms = (True, 0.07)
        self._interval_ms = 0.05
        self._state = (0, 0)
        self._io = SerialDataInputDevice(
            config.port,
            pull_up=True,
            max_bits=40,
            package_initial_bits=[(False, 0.08), (True, 0.08)],
        )
        self._io.when_filled = self.read

    def get_sensors(self):
        return [
            SensorRef(self, self.name, self._temperature_id, "C"),
            SensorRef(self, self.name, self._humidity_id, "%"),
        ]

    def get_state(self, id: str) -> float:
        if id == self._temperature_id:
            return self._state[0]
        elif id == self._humidity_id:
            return self._state[1]
        else:
            raise ValueError(f"Unknown sensor id: {id}")

    def activate(self):
        for state, duration in self._signal_activate_ms:
            self._io.value = state
            sleep(duration / 1000)

    def read(self, bits: deque[(bool, float)]):
        # convert first 8 bits as temperature
        temperature = 0
