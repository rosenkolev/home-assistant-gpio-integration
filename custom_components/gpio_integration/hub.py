from homeassistant.const import Platform

from .controllers.cover import BasicToggleRoller, Roller
from .controllers.sensor import SensorsHub
from .core import get_logger
from .schemas.binary_sensor import BinarySensorConfig
from .schemas.cover import RollerConfig, ToggleRollerConfig
from .schemas.pwm import PwmConfig
from .schemas.sensor import AnalogSensorConfig
from .schemas.switch import SwitchConfig

_LOGGER = get_logger()


class Hub:
    """Dummy hub for Hello World example."""

    def __init__(self, configs: dict) -> None:
        """Init hub."""
        self.type = configs["type"]
        _LOGGER.debug('Hub type "%s"', self.type)
        if self.type == "cover_up_down":
            self.config = RollerConfig(configs)
            self.controller = Roller(self.config)
            self.platforms = [Platform.COVER, Platform.NUMBER]
        elif self.type == "cover_toggle":
            self.config = ToggleRollerConfig(configs)
            self.controller = BasicToggleRoller(self.config)
            self.platforms = [Platform.COVER]
        elif self.type == "binary_sensor":
            self.config = BinarySensorConfig(configs)
            self.platforms = [Platform.BINARY_SENSOR]
        elif self.type == "switch":
            self.config = SwitchConfig(configs)
            self.platforms = [Platform.SWITCH]
        elif self.type == "light":
            self.config = PwmConfig(configs)
            self.platforms = [Platform.LIGHT]
        elif self.type == "fan":
            self.config = PwmConfig(configs)
            self.platforms = [Platform.FAN]
        elif self.type == "analog_sensor" or self.type == "analog_range_sensor":
            self.config = AnalogSensorConfig(configs)
            self.controller = SensorsHub(self.config)
            self.platforms = [Platform.SENSOR]

    @property
    def is_cover(self) -> bool:
        return self.type == "cover_up_down"

    @property
    def is_cover_toggle(self) -> bool:
        return self.type == "cover_toggle"
