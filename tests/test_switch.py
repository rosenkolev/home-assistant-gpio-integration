from unittest.mock import patch, ANY

import pytest

import mocked_models as mocked

from custom_components.gpio_integration.config_schema import (
    SwitchConfig,
    CONF_NAME,
    CONF_PORT,
    CONF_DEFAULT_STATE,
    CONF_INVERT_LOGIC,
)


def __create_config(port=1, default_state=False, invert_logic=False):
    return SwitchConfig(
        {
            CONF_NAME: "Test Name",
            CONF_PORT: port,
            CONF_DEFAULT_STATE: default_state,
            CONF_INVERT_LOGIC: invert_logic,
        }
    )


@patch("homeassistant.components.switch.SwitchEntity", mocked.MockedBaseEntity)
def test__GpioSwitch_should_init_default_sate():
    from custom_components.gpio_integration.switch import GpioSwitch

    gpio = GpioSwitch(__create_config())

    assert gpio.is_on == False


@patch("homeassistant.components.switch.SwitchEntity", mocked.MockedBaseEntity)
def test__GpioSwitch_should_init_default_state():
    from custom_components.gpio_integration.switch import GpioSwitch

    gpio = GpioSwitch(__create_config(default_state=True))

    assert gpio.is_on == True


@patch("homeassistant.components.switch.SwitchEntity", mocked.MockedBaseEntity)
def test__GpioSwitch_should_init_default_state_io():
    import custom_components.gpio_integration.switch as base

    with patch.object(base, "Gpio", mocked.MockedGpio):
        base.GpioSwitch(__create_config(port=17, default_state=True))

        assert mocked.mocked_gpio[17]["mode"] == "write"
        assert mocked.mocked_gpio[17]["default_value"] == True


@patch("homeassistant.components.switch.SwitchEntity", mocked.MockedBaseEntity)
def test__GpioSwitch_should_set_pin():
    import custom_components.gpio_integration.switch as base

    with patch.object(base, "Gpio", mocked.MockedGpio):
        gpio = base.GpioSwitch(__create_config(port=13))

        gpio.set_state(True)
        assert mocked.mocked_gpio[13]["write_value"] == True

        gpio.set_state(False)
        assert mocked.mocked_gpio[13]["write_value"] == False


@patch("homeassistant.components.switch.SwitchEntity", mocked.MockedBaseEntity)
def test__GpioSwitch_should_set_pin_invert():
    import custom_components.gpio_integration.switch as base

    with patch.object(base, "Gpio", mocked.MockedGpio):
        gpio = base.GpioSwitch(__create_config(invert_logic=True))

        gpio.set_state(True)
        assert mocked.mocked_gpio[1]["write_value"] == False

        gpio.set_state(False)
        assert mocked.mocked_gpio[1]["write_value"] == True


@pytest.mark.asyncio
@patch("homeassistant.components.switch.SwitchEntity", mocked.MockedBaseEntity)
async def test__GpioSwitch_on_off_should_write_ha():
    import custom_components.gpio_integration.switch as base

    gpio = base.GpioSwitch(__create_config())

    gpio.ha_state_write == False
    await gpio.async_turn_on()
    assert gpio.ha_state_write == True

    gpio.ha_state_write == False
    await gpio.async_turn_off()
    assert gpio.ha_state_write == True
