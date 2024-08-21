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
sys.modules["gpiod"] = Mock()
sys.modules["gpiod.line"] = Mock()
sys.modules["gpiod.line_settings"] = Mock()

mocked_gpio = dict()


class MockedGpio:
    def __init__(
        self,
        port,
        mode=None,
        pull_mode=None,
        edge_detect=None,
        debounce_ms=None,
        default_value=None,
    ):
        self.data = mocked_gpio.setdefault(port, dict())

        self.data.clear()
        self.data.setdefault("read_value", False)
        self.data.setdefault("read_events", [])

        self.data["mode"] = mode
        self.data["default_value"] = pull_mode
        self.data["edge_detect"] = edge_detect
        self.data["debounce_ms"] = debounce_ms
        self.data["default_value"] = default_value

    def read(self):
        return self.data.get("read_value")

    def write(self, value):
        self.data["write_value"] = value

    def read_edge_events(self):
        return self.data.get("read_events")


class MockedBaseEntity:
    ha_state_update_scheduled = False
    ha_state_update_scheduled_force_refresh = False
    ha_state_write = False

    def async_write_ha_state(self):
        self.ha_state_write = True

    def async_schedule_update_ha_state(self, force_refresh):
        self.ha_state_update_scheduled = True
        self.ha_state_update_scheduled_force_refresh = force_refresh
