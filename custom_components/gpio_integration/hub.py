import voluptuous as vol

from homeassistant.const import Platform

from .config_flow import CONF_ENTITIES
from .controllers.cover import Roller
from .controllers.sensor import AnalogStepControl, DHT22Controller
from .core import get_logger
from .schemas.binary_sensor import BinarySensorConfig
from .schemas.cover import RollerConfig, ToggleRollerConfig
from .schemas.light import RgbLightConfig
from .schemas.main import EntityTypes
from .schemas.pwm import PwmConfig
from .schemas.sensor import AnalogStepConfig, DHT22Config
from .schemas.switch import SwitchConfig

_LOGGER = get_logger()


class Hub:
    """Dummy hub for Hello World example."""

    def __init__(self, configs: dict) -> None:
        """Init hub."""

        self._type = EntityTypes(configs["type"])
        _LOGGER.debug('Hub: type "%s"', self._type.name)

        if self._type is not None and configs:
            # If we have config and a valid type, then try to
            # add in any missing optional values from the base
            # schema.
            base_schema = CONF_ENTITIES[self._type.value]["schema"]
            configs = dict(configs)
            for key, val in base_schema.schema.items():
                # Skip anything not an optional key
                if not isinstance(key, vol.Optional):
                    continue
                # If not present in config data, copy in default
                if key.schema not in configs:
                    defVal = key.default()
                    _LOGGER.debug(
                        'Hub: setting missing default for config "%s" to value "%s"',
                        key.schema,
                        defVal,
                    )
                    configs.setdefault(key.schema, defVal)

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
        elif self.is_type(EntityTypes.LIGHT_RGB_LED):
            self.config = RgbLightConfig(configs)
            self.platforms = [Platform.LIGHT]
        elif self.is_type(EntityTypes.FAN):
            self.config = PwmConfig(configs)
            self.platforms = [Platform.FAN]
        elif self.is_type(EntityTypes.SENSOR_DHT22):
            self.config = DHT22Config(configs)
            self.controller = DHT22Controller(self.config)
            self.sensors = self.controller.get_sensors()
            self.platforms = [Platform.SENSOR]
        elif self.is_type(EntityTypes.SENSOR_ANALOG_STEP):
            self.config = AnalogStepConfig(configs)
            self.controller = AnalogStepControl(self.config)
            self.sensors = self.controller.get_sensors()
            self.platforms = [Platform.SENSOR]

    def is_type(self, type: EntityTypes) -> bool:
        return self._type == type
