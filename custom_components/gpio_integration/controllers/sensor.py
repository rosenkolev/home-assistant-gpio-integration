import threading

from .._devices import DHT22, DHT22Data
from ..core import get_logger
from ..schemas.sensor import DHT22Config

_LOGGER = get_logger()


class SensorStateProvider:
    def get_state(self, id: str) -> float:
        pass

    def release(self) -> None:
        pass


class SensorRef:
    def __init__(
        self, provider: SensorStateProvider, name: str, id: str, unit: str
    ) -> None:
        self.name = name
        self.id = id
        self.unit = unit
        self._provider = provider

    @property
    def state(self):
        return self._provider.get_state(self.id)

    def close(self):
        if self._provider is not None:
            self._provider.release()
            self._provider = None


class SensorsProvider:
    def get_sensors(self) -> list[SensorRef]:
        pass


class DHT22Controller(SensorsProvider, SensorStateProvider):
    def __init__(self, config: DHT22Config) -> None:
        self.name = config.name
        self.id = config.unique_id
        self._temperature_id = f"{self.id}_T"
        self._humidity_id = f"{self.id}_H"
        self._temperature = 0.0
        self._humidity = 0.0
        self._io = DHT22(config.pin)
        self._io.on_data_received = self._on_data
        self._io.on_invalid_check_sum = self._on_invalid_check_sum
        self._retry = 0

        self._loop_stop_event = threading.Event()
        self._loop_thread = None
        self.start_auto_read_loop(5)

    def get_sensors(self):
        return [
            SensorRef(self, self.name, self._temperature_id, "C"),
            SensorRef(self, self.name, self._humidity_id, "%"),
        ]

    def get_state(self, id: str) -> float:
        if id == self._temperature_id:
            return self._temperature
        elif id == self._humidity_id:
            return self._humidity

        raise ValueError(f"Unknown sensor id: {id}")

    def start_auto_read_loop(self, interval_sec: int):
        """Start async loop to read data every `data: interval_sec` seconds."""
        self._loop_stop_event.clear()
        self._loop_thread = threading.Thread(
            target=self._auto_read_loop, args=(interval_sec,)
        )
        self._loop_thread.start()

    def stop_auto_read_loop(self):
        """Stop the async loop."""
        self._loop_stop_event.set()
        if self._loop_thread:
            self._loop_thread.join()
            if self._loop_thread.is_alive():
                _LOGGER.warning("DHT22: failed to stop auto read loop")

            self._loop_thread = None
            _LOGGER.debug("DHT22: auto read loop stopped")

    def release(self) -> None:
        if self._io is not None:
            _LOGGER.debug("DHT22: releasing resources")
            self._io.on_data_received = None
            self._io.on_invalid_check_sum = None
            self._io.close()
            self._io = None

        self.stop_auto_read_loop()

    def _on_data(self, data: DHT22Data):
        self._temperature = data.temperature
        self._humidity = data.humidity
        self._retry = 0
        _LOGGER.debug(
            "DHT22: temperature=%.1fC, humidity=%.1f%", data.temperature, data.humidity
        )

    def _on_invalid_check_sum(self):
        _LOGGER.warning("DHT22: invalid check sum")
        if self._retry < 2:
            self._io.read()
            self._retry += 1

    def _auto_read_loop(self, interval_sec: int):
        while not self._loop_stop_event.wait(interval_sec):
            self._io.read()
