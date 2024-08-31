import sys
from typing import Callable
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

from custom_components.gpio_integration.gpio import (
    BounceType,
    EdgesType,
    ModeType,
    Pin,
    PullType,
)


class MockedPin(Pin):
    def __init__(
        self,
        pin: int | str,
        mode: ModeType = "input",
        pull: PullType = "floating",
        bounce: BounceType = None,
        edge: EdgesType = "BOTH",
        frequency: int | None = None,
        default_value: float | bool | None = None,
        when_changed: Callable[[int], None] = None,
    ):
        self.data = {
            "connect": False,
            "read": None,
            "write": None,
            "close": False,
            "event_detect": False,
        }
        super().__init__(
            pin, mode, pull, bounce, edge, frequency, default_value, when_changed
        )

    def _connect(self):
        self.data["connect"] = True

    def _close(self):
        self.data["close"] = True

    def _read(self):
        return self.data.get("read")

    def _write(self, value):
        self.data["write"] = value

    def _enable_event_detect(self):
        self.data["event_detect"] = True

    def _disable_event_detect(self):
        self.data["event_detect"] = True


class MockedCreatePin:
    def __init__(self):
        self.mock = Mock(side_effect=self.effect)
        self.pins = dict()
        self.pin = None

    def effect(
        self,
        pin: int | str,
        mode: ModeType = "input",
        pull: PullType = "floating",
        bounce: BounceType = None,
        edges: EdgesType = "BOTH",
        frequency: int | None = None,
        default_value: float | bool | None = None,
        when_changed: Callable[[int], None] = None,
    ):
        self.pin = MockedPin(
            pin, mode, pull, bounce, edges, frequency, default_value, when_changed
        )
        self.pins[pin] = self.pin
        return self.pin


class MockedBaseEntity:
    ha_state_update_scheduled = False
    ha_state_update_scheduled_force_refresh = False
    ha_state_write = False

    def async_write_ha_state(self):
        self.ha_state_write = True

    def async_schedule_update_ha_state(self, force_refresh):
        self.ha_state_update_scheduled = True
        self.ha_state_update_scheduled_force_refresh = force_refresh
