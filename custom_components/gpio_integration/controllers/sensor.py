from .._base import AutoReadLoop, ClosableMixin, ReprMixin
from .._devices import DHT22, DHT22Data, create_analog_device
from ..core import get_logger
from ..schemas.sensor import AnalogStepConfig, DHT22Config

_LOGGER = get_logger()


class SensorStateProvider:
    def get_state(self, id: str) -> float:
        pass

    def release(self) -> None:
        pass


class SensorRef:
    def __init__(
        self,
        provider: SensorStateProvider,
        name: str,
        id: str,
        unit: str,
        device_id: str,
        device_name: str,
    ) -> None:
        self.name = name
        self.id = id
        self.device_id = device_id
        self.device_name = device_name
        self.unit = unit
        self._provider = provider

    @property
    def state(self):
        return self._provider.get_state(self.id)

    def close(self):
        if self._provider is not None:
            self._provider.release()
            self._provider = None


class SensorsMixin(SensorStateProvider):
    def get_sensors(self) -> list[SensorRef]:
        pass

    def create_sensor(self, name: str, id: str, unit: str) -> SensorRef:
        return SensorRef(self, f"{self.name} {name}", id, unit, self.id, self.name)


class DHT22Controller(SensorsMixin, ReprMixin, AutoReadLoop):
    def __init__(self, config: DHT22Config) -> None:
        super().__init__()
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

        self.start_auto_read_loop(config.update_interval_sec)

    def get_sensors(self):
        return [
            self.create_sensor("Temperature", self._temperature_id, "C"),
            self.create_sensor("Humidity", self._humidity_id, "%"),
        ]

    def get_state(self, id: str) -> float:
        if id == self._temperature_id:
            return self._temperature
        elif id == self._humidity_id:
            return self._humidity

        raise ValueError(f"Unknown sensor id: {id}")

    def release(self) -> None:
        if self._io is not None:
            _LOGGER.debug(f"{self!r}: releasing")
            self._io.on_data_received = None
            self._io.on_invalid_check_sum = None
            self._io.close()
            self._io = None

        self.stop_auto_read_loop()

    def _on_data(self, data: DHT22Data):
        self._temperature = data.temperature
        self._humidity = data.humidity
        self._retry = 0
        _LOGGER.debug(f"{self!r}: data {data.temperature}C, {data.humidity}%")

    def _read(self):
        self._io.read()

    def _on_invalid_check_sum(self):
        _LOGGER.warning("DHT22: invalid check sum")
        if self._retry < 2:
            self._io.read()
            self._retry += 1


class AnalogStepControl(SensorsMixin, ClosableMixin, ReprMixin):
    def __init__(self, config: AnalogStepConfig) -> None:
        self.name = config.name
        self.id = config.unique_id
        self.sensor = SensorRef(
            self, self.name, self.id, config.native_unit, None, None
        )

        self._min_voltage = config.min_voltage
        self._min_value = config.min_value
        self._step_voltage = config.step_voltage
        self._step_value = config.step_value

        self._io = create_analog_device(config.chip, config.channel)

    def get_sensors(self):
        return [self.sensor]

    def get_state(self, id: str) -> float:
        if id != self.id:
            raise ValueError(f"{self!r}: unknown sensor id: {id}")

        voltage: float = self._io.value * 3.3  # 3.3V
        if voltage < self._min_voltage:
            return self._min_value

        steps = (voltage - self._min_voltage) / self._step_voltage
        value = self._min_value + (steps * self._step_value)
        return value

    def release(self) -> None:
        self._close()
