from homeassistant.const import Platform

from .controllers.cover import Roller
from .controllers.sensor import DHT22Controller
from .core import get_logger
from .schemas.binary_sensor import BinarySensorConfig
from .schemas.cover import RollerConfig, ToggleRollerConfig
from .schemas.main import EntityTypes
from .schemas.pwm import PwmConfig
from .schemas.sensor import DHT22Config
from .schemas.switch import SwitchConfig

_LOGGER = get_logger()


class Hub:
    """Dummy hub for Hello World example."""

    def __init__(self, configs: dict) -> None:
        """Init hub."""

        self._type = EntityTypes[configs["type"]]
        _LOGGER.debug('Hub: type "%s"', self._type.name)

        if self.is_type(EntityTypes.COVER_UP_DOWN):
            self.config = RollerConfig(configs)
            self.controller = Roller(self.config)
            self.platforms = [Platform.COVER, Platform.NUMBER]
        elif self.is_type(EntityTypes.COVER_TOGGLE):
            self.config = ToggleRollerConfig(configs)
            self.platforms = [Platform.COVER]
        elif self.is_type(EntityTypes.BINARY_SENSOR):
            self.config = BinarySensorConfig(configs)
            self.platforms = [Platform.BINARY_SENSOR]
        elif self.is_type(EntityTypes.SWITCH):
            self.config = SwitchConfig(configs)
            self.platforms = [Platform.SWITCH]
        elif self.is_type(EntityTypes.LIGHT_PWM_LED):
            self.config = PwmConfig(configs)
            self.platforms = [Platform.LIGHT]
        elif self.is_type(EntityTypes.FAN):
            self.config = PwmConfig(configs)
            self.platforms = [Platform.FAN]
        elif self.is_type(EntityTypes.DHT22):
            self.config = DHT22Config(configs)
            self.controller = DHT22Controller(self.config)
            self.sensors = self.controller.get_sensors()
            self.platforms = [Platform.SENSOR]

    def is_type(self, type: EntityTypes) -> bool:
        return self._type == type
