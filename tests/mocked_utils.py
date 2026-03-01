import sys
from enum import IntFlag
from types import ModuleType

import pytest


def patch_path(monkeypatch: pytest.MonkeyPatch, path: str, mock: object):
    monkeypatch.setattr(
        "custom_components.gpio_integration." + path,
        mock,
    )


def register_module(monkeypatch, name: str) -> ModuleType:
    mod = ModuleType(name)
    monkeypatch.setitem(sys.modules, name, mod)
    return mod


def create_enum(name: str, **values):
    return type(name, (), values)


def create_flag_enum(name: str, **values):
    return IntFlag(name, values)


PIN_NUMBER = 0


def get_next_pin() -> int:
    global PIN_NUMBER
    PIN_NUMBER += 1
    if PIN_NUMBER > 40:
        PIN_NUMBER = 1

    return PIN_NUMBER


def assert_gpio_blink(pin, gpio, test: list[tuple[bool, float]]):
    pin.states = []
    gpio._io._blink_thread.execute_target()
    map = gpio._io._blink_thread.zip(pin.states)
    assert len(map) == len(test)
    for idx in range(len(test)):
        val = round(map[idx][0], 2)
        assert test[idx][0] == val
