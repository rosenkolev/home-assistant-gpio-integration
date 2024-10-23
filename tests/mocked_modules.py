import sys
from unittest.mock import Mock

from tests.mocks import MockedBaseEntity


class Platform:
    SWITCH = "switch"
    LIGHT = "light"
    COVER = "cover"
    BINARY_SENSOR = "binary_sensor"
    FAN = "fan"
    SENSOR = "sensor"
    NUMBER = "number"


class DeviceInfo:
    def __init__(self, identifiers, name, manufacturer, model, sw_version):
        self.identifiers = identifiers
        self.name = name
        self.manufacturer = manufacturer
        self.model = model
        self.sw_version = sw_version


sys.modules["voluptuous"] = Mock()
sys.modules["homeassistant"] = Mock()
sys.modules["homeassistant.const"] = Mock()
sys.modules["homeassistant.const"].Platform = Platform
sys.modules["homeassistant.core"] = Mock()
sys.modules["homeassistant.config_entries"] = Mock()
sys.modules["homeassistant.helpers"] = Mock()
sys.modules["homeassistant.helpers.config_validation"] = Mock()
sys.modules["homeassistant.helpers.device_registry"] = Mock()
sys.modules["homeassistant.helpers.device_registry"].DeviceInfo = DeviceInfo
sys.modules["homeassistant.helpers.entity_platform"] = Mock()
sys.modules["homeassistant.helpers.event"] = Mock()
sys.modules["homeassistant.helpers.selector"] = Mock()
sys.modules["homeassistant.helpers.typing"] = Mock()
sys.modules["homeassistant.exceptions"] = Mock()
sys.modules["homeassistant.components"] = Mock()


class CoverEntityFeature:
    OPEN = 1
    CLOSE = 2
    STOP = 4
    SET_POSITION = 8


sys.modules["homeassistant.components.cover"] = Mock()
sys.modules["homeassistant.components.cover"].CoverEntity = MockedBaseEntity
sys.modules["homeassistant.components.cover"].CoverEntityFeature = CoverEntityFeature
sys.modules["homeassistant.components.cover"].ATTR_POSITION = "A_POSITION"

sys.modules["homeassistant.components.binary_sensor"] = Mock()
sys.modules["homeassistant.components.binary_sensor"].BinarySensorEntity = (
    MockedBaseEntity
)
sys.modules["homeassistant.components.sensor"] = Mock()
sys.modules["homeassistant.components.sensor"].SensorEntity = MockedBaseEntity
sys.modules["homeassistant.components.switch"] = Mock()
sys.modules["homeassistant.components.switch"].SwitchEntity = MockedBaseEntity


class LightEntityFeature:
    FLASH = 1
    EFFECT = 2


sys.modules["homeassistant.components.light"] = Mock()
sys.modules["homeassistant.components.light"].LightEntity = MockedBaseEntity
sys.modules["homeassistant.components.light"].LightEntityFeature = LightEntityFeature()
sys.modules["homeassistant.components.light"].ATTR_BRIGHTNESS = "A_BRIGHTNESS"
sys.modules["homeassistant.components.light"].ATTR_EFFECT = "A_EFFECT"
sys.modules["homeassistant.components.light"].ATTR_FLASH = "A_FLASH"
sys.modules["homeassistant.components.light"].EFFECT_OFF = "E_OFF"
sys.modules["homeassistant.components.light"].FLASH_SHORT = "F_SHORT"
sys.modules["homeassistant.components.light"].FLASH_LONG = "F_LONG"


class FanEntityFeature:
    SET_SPEED = 1
    TURN_ON = 2
    TURN_OFF = 4


sys.modules["homeassistant.components.fan"] = Mock()
sys.modules["homeassistant.components.fan"].FanEntityFeature = FanEntityFeature()
sys.modules["homeassistant.components.fan"].FanEntity = MockedBaseEntity
sys.modules["homeassistant.components.fan"].ATTR_PERCENTAGE = "A_PERCENTAGE"

sys.modules["homeassistant.components.number"] = Mock()
sys.modules["homeassistant.components.number"].NumberEntity = MockedBaseEntity
