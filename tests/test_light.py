import pytest
from homeassistant.components.light import ColorMode
from homeassistant.const import CONF_PORT

from custom_components.gpio_integration.light import GpioLight
from custom_components.gpio_integration.schemas import (
    CONF_DEFAULT_STATE,
    CONF_FREQUENCY,
    CONF_NAME,
)
from custom_components.gpio_integration.schemas.pwm import PwmConfig
from tests.mocks import assert_gpio_blink, get_next_pin


def __create_config(port=None, default_state=False, frequency=50):
    return PwmConfig(
        {
            CONF_NAME: "Test Name",
            CONF_PORT: get_next_pin() if port is None else port,
            CONF_FREQUENCY: frequency,
            CONF_DEFAULT_STATE: default_state,
        }
    )


def test__GpioLight_should_init_default_light(mocked_factory):
    number = get_next_pin()
    pin = mocked_factory.pin(number)
    with GpioLight(__create_config(number, frequency=0)) as gpio:
        assert gpio.is_on is False
        assert gpio.brightness == 0
        assert ColorMode.ONOFF in gpio._attr_supported_color_modes
        assert gpio._attr_color_mode == ColorMode.ONOFF
        assert pin._function == "output"
        assert pin._frequency is None


def test__GpioLight_LED_should_init_default(mocked_factory):
    number = get_next_pin()
    pin = mocked_factory.pin(number)
    with GpioLight(__create_config(number, frequency=200)) as gpio:
        assert gpio.is_on is False
        assert gpio.brightness == 0
        assert ColorMode.BRIGHTNESS in gpio._attr_supported_color_modes
        assert gpio._attr_color_mode == ColorMode.BRIGHTNESS
        assert pin._function == "output"
        assert pin._frequency == 200


def test__GpioLight_LED_should_init_default_state(mocked_factory):
    with GpioLight(__create_config(default_state=True)) as gpio:
        assert gpio.is_on is True
        assert gpio.brightness == 255
        assert gpio.ha_state_update_scheduled is False


def test__GpioLight_LED_should_turn_led_on_off(mocked_factory):
    number = get_next_pin()
    pin = mocked_factory.pin(number)
    with GpioLight(__create_config(number)) as gpio:

        gpio.turn_on()
        assert pin._state == 1
        assert gpio.brightness == 255
        assert gpio.is_on is True

        gpio.turn_off()
        assert pin._state == 0
        assert gpio.brightness == 0
        assert gpio.is_on is False


def test__GpioLight_LED_should_turn_bulb_on_off(mocked_factory):
    number = get_next_pin()
    pin = mocked_factory.pin(number)
    with GpioLight(__create_config(number, frequency=0)) as gpio:

        gpio.turn_on()
        assert pin._state is True
        assert gpio.brightness == 255
        assert gpio.is_on is True

        gpio.turn_off()
        assert pin._state is False
        assert gpio.brightness == 0
        assert gpio.is_on is False


def test__GpioLight_LED_on_off_should_write_ha(mocked_factory):
    with GpioLight(__create_config()) as gpio:

        gpio.ha_state_write = False
        gpio.turn_on()
        assert gpio.ha_state_update_scheduled is True

        gpio.ha_state_write = False
        gpio.turn_off()
        assert gpio.ha_state_update_scheduled is True


def test__GpioLight_LED_should_set_brightness(mocked_factory):
    number = get_next_pin()
    pin = mocked_factory.pin(number)
    with GpioLight(__create_config(number, frequency=100)) as gpio:

        gpio.turn_on(**{"A_BRIGHTNESS": 130})
        assert pin._state == 0.5098
        assert gpio.brightness == 130
        assert gpio.is_on is True

        gpio.turn_off(**{"A_BRIGHTNESS": 0})
        assert pin._state == 0
        assert gpio.brightness == 0
        assert gpio.is_on is False


def test__GpioLight_should_pulse_slow(mocked_factory, mock_gpio_thread):
    number = get_next_pin()
    pin = mocked_factory.pin(number)
    with GpioLight(__create_config(number, frequency=0)) as gpio:
        gpio.turn_on(**{"A_FLASH": "F_LONG"})

        assert gpio.brightness == 0
        assert gpio.is_on is False

        assert_gpio_blink(pin, gpio, [(True, 1.5), (False, 1.5)] * 4)


def test__GpioLight_should_pulse_fast(mocked_factory, mock_gpio_thread):
    number = get_next_pin()
    pin = mocked_factory.pin(number)
    with GpioLight(__create_config(number, frequency=0)) as gpio:
        gpio.turn_on(**{"A_FLASH": "F_SHORT"})

        assert gpio.brightness == 0
        assert gpio.is_on is False
        assert_gpio_blink(pin, gpio, [(True, 1.2), (False, 1.2)] * 2)


def test__GpioLight_should_effect_blink(mocked_factory, mock_gpio_thread):
    number = get_next_pin()
    pin = mocked_factory.pin(number)
    with GpioLight(__create_config(number, frequency=0)) as gpio:
        gpio.turn_on(**{"A_EFFECT": "Blink"})

        assert gpio.brightness == 0
        assert gpio.is_on is False

        assert_gpio_blink(pin, gpio, [(True, 1), (False, 1)] * 200)


def test__GpioLight_should_effect_off(mocked_factory, mock_gpio_thread):
    number = get_next_pin()
    with GpioLight(__create_config(number, frequency=0)) as gpio:
        gpio.turn_on(**{"A_EFFECT": "E_OFF"})

        assert gpio.brightness == 0
        assert gpio.is_on is False


@pytest.mark.asyncio
async def test__GpioLight_will_close_pin(mocked_factory):
    number = get_next_pin()
    pin = mocked_factory.pin(number)
    gpio = GpioLight(__create_config(port=number))

    await gpio.async_will_remove_from_hass()

    assert pin.closed is True
    assert gpio._io is None
