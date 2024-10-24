import pytest

from custom_components.gpio_integration.number import GpioPosition


class MockRoller:
    def __init__(self) -> None:
        self.name = "Test Name"
        self.id = "test_id"
        self.step = 1
        self.position = 10
        self.released = False

    def set_position(self, position: int):
        self.position = position

    def release(self):
        self.released = True

    def __repr__(self):
        return "GPIO0"


def test__GpioPosition_should_init():
    roller = MockRoller()
    with GpioPosition(roller) as gpio:
        assert gpio.native_value == 10
        assert gpio.name == "Test Name"
        assert gpio.unique_id == "test_id"
        assert gpio._attr_native_step == 1
        assert gpio._attr_native_unit_of_measurement == "%"


def test__GpioPosition_should_set():
    roller = MockRoller()
    with GpioPosition(roller) as gpio:
        gpio.set_native_value(30)
        assert roller.position == 30


def test__GpioPosition_should_repr():
    roller = MockRoller()
    with GpioPosition(roller) as gpio:
        assert repr(gpio) == "GPIO0 (Test Name)"


def test__GpioPosition_should_have_device_info():
    roller = MockRoller()
    with GpioPosition(roller) as gpio:
        device_info = gpio.device_info
        assert device_info.identifiers == {("gpio_integration", "test_id")}
        assert device_info.name == "Test Name"
        assert device_info.manufacturer == "Raspberry Pi"
        assert device_info.model == "GPIO"
        assert device_info.sw_version == "1"


@pytest.mark.asyncio
async def test__GpioPosition_should_close(mocked_factory):
    roller = MockRoller()
    gpio = GpioPosition(roller)

    await gpio.async_will_remove_from_hass()

    assert roller.released is True
    assert gpio._io is None
