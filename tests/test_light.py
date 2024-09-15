from unittest.mock import Mock, patch

import mocked_models as mocked

from custom_components.gpio_integration.config_schema import (
    CONF_DEFAULT_STATE,
    CONF_FREQUENCY,
    CONF_NAME,
    CONF_PORT,
    LightConfig,
)


def __create_config(port=None, default_state=False, frequency=50):
    return LightConfig(
        {
            CONF_NAME: "Test Name",
            CONF_PORT: mocked.get_next_pin() if port is None else port,
            CONF_FREQUENCY: frequency,
            CONF_DEFAULT_STATE: default_state,
        }
    )


@patch("custom_components.gpio_integration.gpio.pin_factory.create_pin", Mock())
@patch("homeassistant.components.light.LightEntity", mocked.MockedBaseEntity)
def test__GpioLight_should_init_default_light():
    import custom_components.gpio_integration.light as base

    pin = mocked.get_next_pin()
    create_pin = mocked.MockedCreatePin(False)
    with patch.object(base, "create_pin", create_pin.mock):
        gpio = base.GpioLight(__create_config(port=pin, frequency=0))

        assert gpio.is_on is False
        assert gpio.brightness == 0
        assert base.ColorMode.ONOFF in gpio._attr_supported_color_modes
        assert gpio._attr_color_mode == base.ColorMode.ONOFF
        create_pin.mock.assert_called_once_with(pin, mode="output", frequency=0)


@patch("custom_components.gpio_integration.gpio.pin_factory.create_pin", Mock())
@patch("homeassistant.components.light.LightEntity", mocked.MockedBaseEntity)
def test__GpioLight_LED_should_init_default():
    import custom_components.gpio_integration.light as base

    pin = mocked.get_next_pin()
    with patch.object(base, "create_pin", Mock()) as create_pin:
        gpio = base.GpioLight(__create_config(port=pin, frequency=200))

        assert gpio.is_on is False
        assert gpio.brightness == 0
        assert base.ColorMode.BRIGHTNESS in gpio._attr_supported_color_modes
        assert gpio._attr_color_mode == base.ColorMode.BRIGHTNESS
        create_pin.assert_called_once_with(pin, mode="output", frequency=200)


@patch("custom_components.gpio_integration.gpio.pin_factory.create_pin", Mock())
@patch("homeassistant.components.light.LightEntity", mocked.MockedBaseEntity)
def test__GpioLight_LED_should_init_default_state():
    from custom_components.gpio_integration.light import GpioLight

    gpio = GpioLight(__create_config(default_state=True))

    assert gpio.is_on is True
    assert gpio.brightness == 255


@patch("homeassistant.components.light.LightEntity", mocked.MockedBaseEntity)
def test__GpioLight_LED_should_turn_on_off():
    import custom_components.gpio_integration.light as base

    proxy = mocked.MockedCreatePin()
    with patch.object(base, "create_pin", proxy.mock):
        gpio = base.GpioLight(__create_config())

        gpio.turn_on()
        assert proxy.pin.data["write_pwm"] == 1
        assert gpio.brightness == 255
        assert gpio.is_on is True

        gpio.turn_off()
        assert proxy.pin.data["write_pwm"] == 0
        assert gpio.brightness == 0
        assert gpio.is_on is False


@patch("homeassistant.components.light.LightEntity", mocked.MockedBaseEntity)
def test__GpioLight_LED_on_off_should_write_ha():
    import custom_components.gpio_integration.light as base

    gpio = base.GpioLight(__create_config())

    gpio.ha_state_write = False
    gpio.turn_on()
    assert gpio.ha_state_update_scheduled is True

    gpio.ha_state_write = False
    gpio.turn_off()
    assert gpio.ha_state_update_scheduled is True
