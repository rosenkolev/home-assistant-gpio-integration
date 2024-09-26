from unittest.mock import Mock, patch

import mocked_models as mocked
import pytest
from homeassistant.const import CONF_PORT

from custom_components.gpio_integration.schemas import (
    CONF_DEFAULT_STATE,
    CONF_FREQUENCY,
    CONF_NAME,
)
from custom_components.gpio_integration.schemas.pwm import PwmConfig


def __create_config(port=None, default_state=False, frequency=100):
    return PwmConfig(
        {
            CONF_NAME: "Test Name",
            CONF_PORT: mocked.get_next_pin() if port is None else port,
            CONF_FREQUENCY: frequency,
            CONF_DEFAULT_STATE: default_state,
        }
    )


@patch("custom_components.gpio_integration.gpio.pin_factory.create_pin", Mock())
@patch("homeassistant.components.fan.FanEntity", mocked.MockedBaseEntity)
def test__GpioFan_should_init_default():
    import custom_components.gpio_integration.fan as base

    pin = mocked.get_next_pin()
    create_pin = mocked.MockedCreatePin(False)
    with patch.object(base, "create_pin", create_pin.mock):
        gpio = base.GpioFan(__create_config(port=pin, frequency=0))

        assert gpio.is_on is False
        assert gpio.percentage == 0
        create_pin.mock.assert_called_once_with(pin, mode="output", frequency=0)


@patch("custom_components.gpio_integration.gpio.pin_factory.create_pin", Mock())
@patch("homeassistant.components.fan.FanEntity", mocked.MockedBaseEntity)
def test__GpioFan_should_init_pwm():
    import custom_components.gpio_integration.fan as base

    pin = mocked.get_next_pin()
    with patch.object(base, "create_pin", Mock()) as create_pin:
        gpio = base.GpioFan(__create_config(port=pin, frequency=200))

        assert gpio.is_on is False
        assert gpio.percentage == 0
        create_pin.assert_called_once_with(pin, mode="output", frequency=200)


@patch("custom_components.gpio_integration.gpio.pin_factory.create_pin", Mock())
@patch("homeassistant.components.fan.FanEntity", mocked.MockedBaseEntity)
def test__GpioFan_should_init_default_state():
    from custom_components.gpio_integration.fan import GpioFan

    gpio = GpioFan(__create_config(default_state=True))

    assert gpio.is_on is True
    assert gpio.percentage == 100


@patch("homeassistant.components.fan.FanEntity", mocked.MockedBaseEntity)
def test__GpioFan_should_turn_on_off():
    import custom_components.gpio_integration.fan as base

    proxy = mocked.MockedCreatePin()
    with patch.object(base, "create_pin", proxy.mock):
        gpio = base.GpioFan(__create_config())

        gpio.turn_on(None)
        assert proxy.pin.data["write_pwm"] == 1.0
        assert gpio.percentage == 100
        assert gpio.is_on is True

        gpio.turn_off()
        assert proxy.pin.data["write_pwm"] == 0
        assert gpio.percentage == 0
        assert gpio.is_on is False


@patch("homeassistant.components.fan.FanEntity", mocked.MockedBaseEntity)
def test__GpioFan_should_turn_set_percentage():
    import custom_components.gpio_integration.fan as base

    proxy = mocked.MockedCreatePin()
    with patch.object(base, "create_pin", proxy.mock):
        gpio = base.GpioFan(__create_config())

        gpio.turn_on(percentage=90)
        assert proxy.pin.data["write_pwm"] == 0.9
        assert gpio.percentage == 90
        assert gpio.is_on is True

        gpio.turn_off()
        assert proxy.pin.data["write_pwm"] == 0
        assert gpio.percentage == 0
        assert gpio.is_on is False


@patch("homeassistant.components.fan.FanEntity", mocked.MockedBaseEntity)
def test__GpioFan_should_turn_set_attr_percentage():
    import custom_components.gpio_integration.fan as base

    base.ATTR_PERCENTAGE = "PERCENTAGE"

    proxy = mocked.MockedCreatePin()
    with patch.object(base, "create_pin", proxy.mock):
        gpio = base.GpioFan(__create_config())

        gpio.turn_on(None, **{"PERCENTAGE": 75})
        assert proxy.pin.data["write_pwm"] == 0.75
        assert gpio.percentage == 75
        assert gpio.is_on is True


@pytest.mark.asyncio
@patch("homeassistant.components.fan.FanEntity", mocked.MockedBaseEntity)
async def test__GpioFan_will_close_pin():
    import custom_components.gpio_integration.fan as base

    proxy = mocked.MockedCreatePin()
    with patch.object(base, "create_pin", proxy.mock):
        gpio = base.GpioFan(__create_config())

        await gpio.async_will_remove_from_hass()
        assert proxy.pin.data["close"] is True
