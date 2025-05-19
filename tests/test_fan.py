import pytest
from homeassistant.const import CONF_PORT

from custom_components.gpio_integration.fan import GpioFan
from custom_components.gpio_integration.schemas import (
    CONF_DEFAULT_STATE,
    CONF_FREQUENCY,
    CONF_INVERT_LOGIC,
    CONF_NAME,
)
from custom_components.gpio_integration.schemas.pwm import PwmConfig
from tests.test__mocks import get_next_pin


def __create_config(port=None, default_state=False, frequency=100, invert_logic=False):
    return PwmConfig(
        {
            CONF_NAME: "Test Name",
            CONF_PORT: get_next_pin() if port is None else port,
            CONF_FREQUENCY: frequency,
            CONF_DEFAULT_STATE: default_state,
            CONF_INVERT_LOGIC: invert_logic,
        }
    )


def test__GpioFan_should_init_default(mocked_factory):
    # assert rise error
    with pytest.raises(ValueError):
        with GpioFan(__create_config(frequency=0)):
            pass


def test__GpioFan_should_init_pwm(mocked_factory):
    number = get_next_pin()
    pin = mocked_factory.pin(number)
    with GpioFan(__create_config(port=number, frequency=200)) as gpio:
        assert gpio.is_on is False
        assert gpio.percentage == 0
        assert pin.function == "output"
        assert pin.state == 0
        assert pin.frequency == 200


def test__GpioFan_should_init_default_state(mocked_factory):
    with GpioFan(__create_config(default_state=True)) as gpio:
        assert gpio.is_on is True
        assert gpio.percentage == 100


def test__GpioFan_should_init_invert_logic(mocked_factory):
    number = get_next_pin()
    pin = mocked_factory.pin(number)
    with GpioFan(
        __create_config(number, default_state=False, invert_logic=True)
    ) as gpio:
        assert gpio.percentage == 0
        assert pin.state == 1.0


def test__GpioFan_should_turn_on_off(mocked_factory):
    number = get_next_pin()
    pin = mocked_factory.pin(number)
    with GpioFan(__create_config(number)) as gpio:

        gpio.turn_on(None)
        assert pin.state == 1.0
        assert gpio.percentage == 100
        assert gpio.is_on is True

        gpio.turn_off()
        assert pin.state == 0
        assert gpio.percentage == 0
        assert gpio.is_on is False


def test__GpioFan_should_turn_on_inverted(mocked_factory):
    number = get_next_pin()
    pin = mocked_factory.pin(number)
    with GpioFan(
        __create_config(number, default_state=True, invert_logic=True)
    ) as gpio:
        assert gpio.percentage == 100
        assert pin.state == 0.0


def test__GpioFan_should_turn_set_percentage(mocked_factory):
    number = get_next_pin()
    pin = mocked_factory.pin(number)
    with GpioFan(__create_config(number)) as gpio:
        gpio.turn_on(percentage=90)
        assert pin.state == 0.9
        assert gpio.percentage == 90
        assert gpio.is_on is True

        gpio.turn_off()
        assert pin.state == 0
        assert gpio.percentage == 0
        assert gpio.is_on is False


def test__GpioFan_should_turn_set_attr_percentage(mocked_factory):
    number = get_next_pin()
    pin = mocked_factory.pin(number)
    with GpioFan(__create_config(number)) as gpio:
        gpio.turn_on(None, **{"A_PERCENTAGE": 75})

        assert pin.state == 0.75
        assert gpio.percentage == 75
        assert gpio.is_on is True


def test__GpioFan_off_should_update_ha_scheduled(mocked_factory):
    number = get_next_pin()
    pin = mocked_factory.pin(number)
    with GpioFan(__create_config(number)) as gpio:
        pin.state = 0.8
        gpio.turn_off()
        assert gpio.ha_state_update_scheduled


def test__GpioFan_on_should_update_ha_scheduled(mocked_factory):
    with GpioFan(__create_config()) as gpio:
        gpio.turn_on(percentage=60)
        assert gpio.ha_state_update_scheduled


@pytest.mark.asyncio
async def test__GpioFan_will_close_pin(mocked_factory):
    number = get_next_pin()
    pin = mocked_factory.pin(number)
    gpio = GpioFan(__create_config(port=number))
    await gpio.async_will_remove_from_hass()
    assert pin.closed is True
    assert gpio._io is None
