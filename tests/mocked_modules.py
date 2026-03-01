import sys
from types import ModuleType
from unittest.mock import Mock

from tests.mocked_classes import (
    MockColOptional,
    MockedBaseEntity,
    MockedConfigFlow,
    MockedDeviceInfo,
    MockedOptionsFlow,
    MockedPlatform,
    MockVolSchema,
)
from tests.mocked_utils import create_enum, create_flag_enum

ha_mock = ModuleType("homeassistant")
ha_mock.ConfigFlow = MockedConfigFlow
ha_mock.OptionsFlowWithConfigEntry = MockedOptionsFlow
ha_mock.ConfigEntry = Mock()

sys.modules["voluptuous"] = Mock()
sys.modules["voluptuous"].Schema = MockVolSchema
sys.modules["voluptuous"].Optional = MockColOptional
sys.modules["voluptuous"].ALLOW_EXTRA = "ALLOW_EXTRA"
sys.modules["homeassistant"] = Mock()
sys.modules["homeassistant"].config_entries = ha_mock
sys.modules["homeassistant.const"] = Mock()
sys.modules["homeassistant.const"].Platform = MockedPlatform
sys.modules["homeassistant.const"].CONF_NAME = "CONF_NAME"
sys.modules["homeassistant.const"].CONF_PORT = "CONF_PORT"
sys.modules["homeassistant.const"].CONF_UNIQUE_ID = "CONF_UNIQUE_ID"
sys.modules["homeassistant.core"] = Mock()
sys.modules["homeassistant.config_entries"] = Mock()
sys.modules["homeassistant.helpers"] = Mock()
sys.modules["homeassistant.helpers.config_validation"] = Mock()
sys.modules["homeassistant.helpers.device_registry"] = Mock()
sys.modules["homeassistant.helpers.device_registry"].DeviceInfo = MockedDeviceInfo
sys.modules["homeassistant.helpers.entity_platform"] = Mock()
sys.modules["homeassistant.helpers.event"] = Mock()
sys.modules["homeassistant.helpers.selector"] = Mock()
sys.modules["homeassistant.helpers.typing"] = Mock()
sys.modules["homeassistant.exceptions"] = Mock()
sys.modules["homeassistant.exceptions"].HomeAssistantError = BaseException
sys.modules["homeassistant.components"] = Mock()
sys.modules["homeassistant.components.cover"] = Mock()
sys.modules["homeassistant.components.cover"].CoverEntity = MockedBaseEntity
sys.modules["homeassistant.components.cover"].CoverEntityFeature = create_flag_enum(
    "CoverEntityFeature",
    OPEN=1,
    CLOSE=2,
    STOP=4,
    SET_POSITION=8,
)
sys.modules["homeassistant.components.cover"].ATTR_POSITION = "A_POSITION"
sys.modules["homeassistant.components.binary_sensor"] = Mock()
sys.modules["homeassistant.components.binary_sensor"].BinarySensorEntity = (
    MockedBaseEntity
)
sys.modules["homeassistant.components.sensor"] = Mock()
sys.modules["homeassistant.components.sensor"].SensorEntity = MockedBaseEntity
sys.modules["homeassistant.components.sensor"].SensorDeviceClass = create_enum(
    "SensorDeviceClass",
    DISTANCE="distance",
)
sys.modules["homeassistant.components.switch"] = Mock()
sys.modules["homeassistant.components.switch"].SwitchEntity = MockedBaseEntity
sys.modules["homeassistant.components.light"] = Mock()
sys.modules["homeassistant.components.light"].LightEntity = MockedBaseEntity
sys.modules["homeassistant.components.light"].LightEntityFeature = create_flag_enum(
    "LightEntityFeature",
    FLASH=1,
    EFFECT=2,
)
sys.modules["homeassistant.components.light"].ATTR_BRIGHTNESS = "A_BRIGHTNESS"
sys.modules["homeassistant.components.light"].ATTR_EFFECT = "A_EFFECT"
sys.modules["homeassistant.components.light"].ATTR_FLASH = "A_FLASH"
sys.modules["homeassistant.components.light"].ATTR_RGB_COLOR = "A_RGB"
sys.modules["homeassistant.components.light"].EFFECT_OFF = "E_OFF"
sys.modules["homeassistant.components.light"].FLASH_SHORT = "F_SHORT"
sys.modules["homeassistant.components.light"].FLASH_LONG = "F_LONG"
sys.modules["homeassistant.components.fan"] = Mock()
sys.modules["homeassistant.components.fan"].FanEntityFeature = create_flag_enum(
    "FanEntityFeature",
    SET_SPEED=1,
    TURN_ON=2,
    TURN_OFF=4,
)
sys.modules["homeassistant.components.fan"].FanEntity = MockedBaseEntity
sys.modules["homeassistant.components.fan"].ATTR_PERCENTAGE = "A_PERCENTAGE"

sys.modules["homeassistant.components.number"] = Mock()
sys.modules["homeassistant.components.number"].NumberEntity = MockedBaseEntity
