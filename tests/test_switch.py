import sys
from unittest.mock import patch, Mock, ANY

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
def test__GpioSwitch_should_init_default_state_False():
    from custom_components.gpio_integration.switch import GpioSwitch

    gpio = GpioSwitch(__create_config(default_state=True))

    assert gpio.is_on == True


@patch("homeassistant.components.switch.SwitchEntity", mocked.MockedBaseEntity)
def test__GpioSwitch_should_set_pin():
    import custom_components.gpio_integration.switch as base

    with patch.object(base, "Gpio", mocked.MockedGpio):
        gpio = base.GpioSwitch(__create_config(port=13))

        gpio.set_state(True)
        assert mocked.mocked_gpio_data["write_value"] == True

        gpio.set_state(False)
        assert mocked.mocked_gpio_data["write_value"] == False


@patch("homeassistant.components.switch.SwitchEntity", mocked.MockedBaseEntity)
def test__GpioSwitch_should_set_pin_invert():
    import custom_components.gpio_integration.switch as base

    with patch.object(base, "Gpio", mocked.MockedGpio):
        gpio = base.GpioSwitch(__create_config(invert_logic=True))

        gpio.set_state(True)
        assert mocked.mocked_gpio_data["write_value"] == False

        gpio.set_state(False)
        assert mocked.mocked_gpio_data["write_value"] == True