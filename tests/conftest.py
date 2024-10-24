from typing import Callable, Generator

import mocked_modules  # noqa: F401
import pytest
from gpiozero import Device

from tests.mocks import (
    MockedGPIOThread,
    MockedTrackTimeInterval,
    MockFactory,
    MockMCP,
    get_mock_mcp,
)


@pytest.fixture(scope="function")
def mocked_factory(request) -> Generator[MockFactory, None, None]:
    """The same as gpiozero tests"""
    saved_factory = Device.pin_factory
    Device.pin_factory = MockFactory()
    try:
        yield Device.pin_factory
    finally:
        if Device.pin_factory is not None:
            Device.pin_factory.reset()

        Device.pin_factory = saved_factory


@pytest.fixture(scope="function")
def mock_gpio_thread(request) -> Generator[MockFactory, None, None]:
    """Mock GPIOThread"""
    import gpiozero.output_devices as output_devices

    saved_gpio_thread = output_devices.GPIOThread
    try:
        output_devices.GPIOThread = MockedGPIOThread
        yield None
    finally:
        output_devices.GPIOThread = saved_gpio_thread


@pytest.fixture(scope="function")
def mock_track_time_interval(request) -> Generator[MockedTrackTimeInterval, None, None]:
    """Mock Event"""
    import custom_components.gpio_integration._base as base

    saved_track_time_interval = base.async_track_time_interval
    try:
        mock = MockedTrackTimeInterval()
        base.async_track_time_interval = mock.caller
        yield mock
    finally:
        base.async_track_time_interval = saved_track_time_interval


@pytest.fixture(scope="function")
def mock_MCP_chips(request) -> Generator[Callable[[int], MockMCP], None, None]:
    """Mock MCP chips"""
    import custom_components.gpio_integration._devices as devices

    saved_MCP_MAP = devices.MCP_CLASS_MAP
    saved_factory = Device.pin_factory
    try:
        Device.pin_factory = lambda: None
        devices.MCP_CLASS_MAP = {
            "MCP3001": MockMCP,
            "MCP3002": MockMCP,
            "MCP3004": MockMCP,
            "MCP3008": MockMCP,
            "MCP3201": MockMCP,
            "MCP3202": MockMCP,
            "MCP3204": MockMCP,
            "MCP3208": MockMCP,
        }

        yield get_mock_mcp
    finally:
        devices.MCP_CLASS_MAP = saved_MCP_MAP
        Device.pin_factory = saved_factory
