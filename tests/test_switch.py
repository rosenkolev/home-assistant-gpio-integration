import pytest
from homeassistant.const import CONF_PORT

from custom_components.gpio_integration.schemas import (
    CONF_DEFAULT_STATE,
    CONF_INVERT_LOGIC,
    CONF_NAME,
)
from custom_components.gpio_integration.schemas.switch import SwitchConfig
from custom_components.gpio_integration.switch import GpioSwitch
from tests.mocks import get_next_pin


def __create_config(port=None, default_state=False, invert_logic=False):
    return SwitchConfig(
        {
            CONF_NAME: "Test Name",
            CONF_PORT: get_next_pin() if port is None else port,
            CONF_DEFAULT_STATE: default_state,
            CONF_INVERT_LOGIC: invert_logic,
        }
    )


def test__GpioSwitch_should_init_default_sate(mocked_factory):
    with GpioSwitch(__create_config()) as gpio:
        assert gpio.is_on is False


def test__GpioSwitch_should_init_default_state(mocked_factory):
    with GpioSwitch(__create_config(default_state=True)) as gpio:
        assert gpio.is_on is True


def test__GpioSwitch_should_init_invert(mocked_factory):
    number = get_next_pin()
    pin = mocked_factory.pin(number)
    with GpioSwitch(__create_config(number, invert_logic=True, default_state=True)):
        pin.assert_states([False])


def test__GpioSwitch_should_init_pin(mocked_factory):
    number = get_next_pin()
    pin = mocked_factory.pin(number)
    with GpioSwitch(__create_config(port=number, default_state=True)):
        assert pin._function == "output"
        assert pin.state is True


def test__GpioSwitch_should_set_pin(mocked_factory):
    number = get_next_pin()
    pin = mocked_factory.pin(number)
    with GpioSwitch(__create_config(port=number)) as gpio:
        gpio.turn_on()
        gpio.turn_off()
        pin.assert_states([False, True, False])


def test__GpioSwitch_on_off_should_update_ha_scheduled(mocked_factory):
    with GpioSwitch(__create_config()) as gpio:
        gpio.ha_state_update_scheduled = False
        gpio.turn_on()
        assert gpio.ha_state_update_scheduled

        gpio.ha_state_update_scheduled = False
        gpio.turn_off()
        assert gpio.ha_state_update_scheduled


@pytest.mark.asyncio
async def test__GpioSwitch_will_close_pin(mocked_factory):
    number = get_next_pin()
    pin = mocked_factory.pin(number)
    gpio = GpioSwitch(__create_config(port=number))
    await gpio.async_will_remove_from_hass()
    assert pin.closed is True
    assert gpio._io is None
