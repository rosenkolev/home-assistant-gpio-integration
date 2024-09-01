from unittest.mock import Mock, patch

import mocked_models as mocked
import pytest

from custom_components.gpio_integration.config_schema import (
    CONF_DEFAULT_STATE,
    CONF_INVERT_LOGIC,
    CONF_NAME,
    CONF_PORT,
    SwitchConfig,
)


def __create_config(port=None, default_state=False, invert_logic=False):
    return SwitchConfig(
        {
            CONF_NAME: "Test Name",
            CONF_PORT: mocked.get_next_pin() if port is None else port,
            CONF_DEFAULT_STATE: default_state,
            CONF_INVERT_LOGIC: invert_logic,
        }
    )


@patch("custom_components.gpio_integration.gpio.pin_factory.create_pin", Mock())
@patch("homeassistant.components.switch.SwitchEntity", mocked.MockedBaseEntity)
def test__GpioSwitch_should_init_default_sate():
    from custom_components.gpio_integration.switch import GpioSwitch

    gpio = GpioSwitch(__create_config())

    assert gpio.is_on is False


@patch("custom_components.gpio_integration.gpio.pin_factory.create_pin", Mock())
@patch("homeassistant.components.switch.SwitchEntity", mocked.MockedBaseEntity)
def test__GpioSwitch_should_init_default_state():
    from custom_components.gpio_integration.switch import GpioSwitch

    gpio = GpioSwitch(__create_config(default_state=True))

    assert gpio.is_on is True


@patch("homeassistant.components.switch.SwitchEntity", mocked.MockedBaseEntity)
def test__GpioSwitch_should_init_default_state_io():
    import custom_components.gpio_integration.switch as base

    pin = mocked.get_next_pin()
    with patch.object(base, "create_pin", Mock()) as create_pin:
        base.GpioSwitch(__create_config(port=pin, default_state=True))
        create_pin.assert_called_once_with(
            pin, mode="output", pull="up", default_value=True
        )


@patch("homeassistant.components.switch.SwitchEntity", mocked.MockedBaseEntity)
def test__GpioSwitch_should_set_pin():
    import custom_components.gpio_integration.switch as base

    proxy = mocked.MockedCreatePin()
    with patch.object(base, "create_pin", proxy.mock):
        gpio = base.GpioSwitch(__create_config())

        gpio.set_state(True)
        assert proxy.pin.data["write"] is True

        gpio.set_state(False)
        assert proxy.pin.data["write"] is False


@patch("homeassistant.components.switch.SwitchEntity", mocked.MockedBaseEntity)
def test__GpioSwitch_should_set_pin_invert():
    import custom_components.gpio_integration.switch as base

    proxy = mocked.MockedCreatePin()
    with patch.object(base, "create_pin", proxy.mock):
        gpio = base.GpioSwitch(__create_config(invert_logic=True))

        gpio.set_state(True)
        assert not proxy.pin.data["write"]

        gpio.set_state(False)
        assert proxy.pin.data["write"]


@pytest.mark.asyncio
@patch("homeassistant.components.switch.SwitchEntity", mocked.MockedBaseEntity)
async def test__GpioSwitch_on_off_should_write_ha():
    import custom_components.gpio_integration.switch as base

    gpio = base.GpioSwitch(__create_config())

    gpio.ha_state_write = False
    await gpio.async_turn_on()
    assert gpio.ha_state_write

    gpio.ha_state_write = False
    await gpio.async_turn_off()
    assert gpio.ha_state_write
