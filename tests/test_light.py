from unittest.mock import Mock, patch

import mocked_models as mocked
import pytest

from custom_components.gpio_integration.config_schema import (
    CONF_DEFAULT_STATE,
    CONF_FREQUENCY,
    CONF_NAME,
    CONF_PORT,
    PwmConfig,
)


def __create_config(port=None, default_state=False, frequency=50):
    return PwmConfig(
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
    assert gpio.ha_state_update_scheduled is False


@patch("homeassistant.components.light.LightEntity", mocked.MockedBaseEntity)
def test__GpioLight_LED_should_turn_led_on_off():
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
def test__GpioLight_LED_should_turn_bulb_on_off():
    import custom_components.gpio_integration.light as base

    proxy = mocked.MockedCreatePin()
    with patch.object(base, "create_pin", proxy.mock):
        gpio = base.GpioLight(__create_config(frequency=0))

        gpio.turn_on()
        assert proxy.pin.data["write"] is True
        assert gpio.brightness == 255
        assert gpio.is_on is True

        gpio.turn_off()
        assert proxy.pin.data["write"] is False
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


@patch("homeassistant.components.light.LightEntity", mocked.MockedBaseEntity)
def test__GpioLight_LED_should_set_brightness():
    import custom_components.gpio_integration.light as base

    proxy = mocked.MockedCreatePin()
    pin = mocked.get_next_pin()
    with patch.object(base, "create_pin", proxy.mock):
        gpio = base.GpioLight(__create_config(port=pin, frequency=100))

        gpio.turn_on(**{"A_BRIGHTNESS": 130})
        assert proxy.pin.data["write_pwm"] == 0.5098
        assert gpio.brightness == 130
        assert gpio.is_on is True

        gpio.turn_off(**{"A_BRIGHTNESS": 0})
        assert proxy.pin.data["write_pwm"] == 0
        assert gpio.brightness == 0
        assert gpio.is_on is False


def __check_blink(gpio, pin, writes, times):
    assert pin.data["write"] is False
    assert gpio._blink_thread is not None
    assert gpio._blink_thread.started is True

    thread: mocked.MockedStoppableThread = gpio._blink_thread

    assert thread is not None
    assert thread.started is True

    pin.writes.clear()
    gpio._blinker(thread.args[0])
    assert writes == pin.writes
    assert thread.waits == times


@patch("homeassistant.components.light.LightEntity", mocked.MockedBaseEntity)
def test__GpioLight_should_pulse_slow():
    import custom_components.gpio_integration.light as base

    proxy = mocked.MockedCreatePin()
    with patch.object(base, "StoppableThread", mocked.MockedStoppableThread):
        with patch.object(base, "create_pin", proxy.mock):
            gpio = base.GpioLight(__create_config(frequency=0))

            gpio.turn_on(**{"A_FLASH": "F_SHORT"})

            assert gpio.brightness == 0
            assert gpio.is_on is False

            __check_blink(gpio, proxy.pin, [True, False] * 2, [0.5] * 4)


@patch("homeassistant.components.light.LightEntity", mocked.MockedBaseEntity)
def test__GpioLight_should_pulse_fast():
    import custom_components.gpio_integration.light as base

    proxy = mocked.MockedCreatePin()
    with patch.object(base, "StoppableThread", mocked.MockedStoppableThread):
        with patch.object(base, "create_pin", proxy.mock):
            gpio = base.GpioLight(__create_config(frequency=0))

            gpio.turn_on(**{"A_FLASH": "F_FAST"})

            assert gpio.brightness == 0
            assert gpio.is_on is False

            __check_blink(
                gpio,
                proxy.pin,
                [True, False] * 4,
                [1.2] * 8,
            )


@pytest.mark.asyncio
@patch("homeassistant.components.light.LightEntity", mocked.MockedBaseEntity)
async def test__GpioLight_will_close_pin():
    import custom_components.gpio_integration.light as base

    proxy = mocked.MockedCreatePin()
    with patch.object(base, "create_pin", proxy.mock):
        gpio = base.GpioLight(__create_config())

        await gpio.async_will_remove_from_hass()
        assert proxy.pin.data["close"] is True


@pytest.mark.asyncio
@patch("homeassistant.components.light.LightEntity", mocked.MockedBaseEntity)
async def test__GpioLight_will_stop_blinking():
    import custom_components.gpio_integration.light as base

    proxy = mocked.MockedCreatePin()
    with patch.object(base, "StoppableThread", mocked.MockedStoppableThread):
        with patch.object(base, "create_pin", proxy.mock):
            gpio = base.GpioLight(__create_config())

            gpio.turn_on(**{"A_FLASH": "F_FAST"})

            await gpio.async_will_remove_from_hass()
            assert gpio._blink_thread is None
