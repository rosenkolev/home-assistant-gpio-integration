from threading import Event
from typing import Callable
from unittest.mock import Mock

import mocked_modules  # noqa: F401

from custom_components.gpio_integration.gpio import (
    BounceType,
    EdgesType,
    ModeType,
    Pin,
    PullType,
)

PIN_NUMBER = 0


def get_next_pin() -> int:
    global PIN_NUMBER
    PIN_NUMBER += 1
    return PIN_NUMBER


class MockedPin(Pin):
    def __init__(
        self,
        pin: int | str,
        mode: ModeType = "input",
        pull: PullType = "floating",
        bounce: BounceType = None,
        edge: EdgesType = "both",
        frequency: int | None = None,
        default_value: float | bool | None = None,
        when_changed: Callable[[int], None] = None,
        support_pwm=True,
    ):
        self.support_pwm = support_pwm
        self.writes = []
        self.data = {
            "connect": False,
            "read": None,
            "write": None,
            "close": False,
            "event_detect": False,
        }
        super().__init__(
            pin, mode, pull, bounce, edge, frequency, default_value, when_changed, True
        )

    def _connect(self):
        self.data["connect"] = True

    def _close(self):
        self.data["close"] = True

    def _read(self):
        return self.data.get("read")

    def _read_pwm(self):
        return self.data.get("read_pwm")

    def _enable_pwm(self, frequency: int):
        self.data["enable_pwm"] = True
        self.data["frequency"] = frequency

    def _disable_pwm(self):
        self.data["disable_pwm"] = True

    def _write(self, value):
        self.writes.append(value)
        self.data["write"] = value

    def _write_pwm(self, value: float) -> None:
        self.data["write_pwm"] = value

    def _enable_event_detect(self):
        self.data["event_detect"] = True

    def _disable_event_detect(self):
        self.data["event_detect"] = True


class MockedCreatePin:
    def __init__(self, support_pwm=True):
        self.support_pwm = support_pwm
        self.mock = Mock(side_effect=self.effect)
        self.pins = dict()
        self.pin = None

    def effect(
        self,
        pin: int | str,
        mode: ModeType = "input",
        pull: PullType = "floating",
        bounce: BounceType = None,
        edges: EdgesType = "both",
        frequency: int | None = None,
        default_value: float | bool | None = None,
        when_changed: Callable[[int], None] = None,
    ):
        self.pin = MockedPin(
            pin,
            mode,
            pull,
            bounce,
            edges,
            frequency,
            default_value,
            when_changed,
            self.support_pwm,
        )
        self.pins[pin] = self.pin
        return self.pin


class MockedBaseEntity:
    ha_state_update_scheduled = False
    ha_state_update_scheduled_force_refresh = False
    ha_state_write = False

    def async_write_ha_state(self):
        self.ha_state_write = True

    def async_schedule_update_ha_state(self, force_refresh=False):
        self.ha_state_update_scheduled = True
        self.ha_state_update_scheduled_force_refresh = force_refresh

    def schedule_update_ha_state(self, force_refresh=False):
        self.ha_state_update_scheduled = True
        self.ha_state_update_scheduled_force_refresh = False

    async def async_will_remove_from_hass(self) -> None:
        pass


class MockedStoppableThread:
    def __init__(self, target, name: str | None = None, args=(), kwargs=None):
        self.args: tuple[dict,] = args
        self.waits = []
        self.started = False

    def start(self):
        self.started = True

    def stop(self):
        self.started = False

    def wait(self, timeout: int):
        self.waits.append(timeout)
