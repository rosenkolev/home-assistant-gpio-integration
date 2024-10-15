from typing import Generator

import mocked_modules  # noqa: F401
import pytest
from gpiozero import Device

from tests.mocks import MockedGPIOThread, MockFactory


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
