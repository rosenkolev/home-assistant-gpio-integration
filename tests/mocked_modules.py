import sys
from unittest.mock import Mock

sys.modules["voluptuous"] = Mock()
sys.modules["homeassistant"] = Mock()
sys.modules["homeassistant.const"] = Mock()
sys.modules["homeassistant.core"] = Mock()
sys.modules["homeassistant.config_entries"] = Mock()
sys.modules["homeassistant.helpers"] = Mock()
sys.modules["homeassistant.helpers.event"] = Mock()
sys.modules["homeassistant.helpers.config_validation"] = Mock()
sys.modules["homeassistant.helpers.typing"] = Mock()
sys.modules["homeassistant.helpers.entity_platform"] = Mock()
sys.modules["homeassistant.helpers.selector"] = Mock()
sys.modules["homeassistant.exceptions"] = Mock()
sys.modules["homeassistant.components"] = Mock()
sys.modules["homeassistant.components.cover"] = Mock()
sys.modules["homeassistant.components.binary_sensor"] = Mock()
sys.modules["homeassistant.components.switch"] = Mock()
sys.modules["pigpio"] = Mock()
sys.modules["RPi"] = Mock()


class LightEntityFeature:
    FLASH = 1
    EFFECT = 2


sys.modules["homeassistant.components.light"] = Mock()
sys.modules["homeassistant.components.light"].LightEntityFeature = LightEntityFeature()
sys.modules["homeassistant.components.light"].ATTR_BRIGHTNESS = "A_BRIGHTNESS"
sys.modules["homeassistant.components.light"].ATTR_EFFECT = "A_EFFECT"
sys.modules["homeassistant.components.light"].ATTR_FLASH = "A_FLASH"
sys.modules["homeassistant.components.light"].EFFECT_OFF = "E_OFF"
sys.modules["homeassistant.components.light"].FLASH_SHORT = "F_SHORT"


class FanEntityFeature:
    SET_SPEED = 1
    TURN_ON = 2
    TURN_OFF = 4


sys.modules["homeassistant.components.fan"] = Mock()
sys.modules["homeassistant.components.fan"].FanEntityFeature = FanEntityFeature()
