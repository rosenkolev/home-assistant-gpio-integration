import pytest
from homeassistant.components.light import ColorMode

from custom_components.gpio_integration.light import RgbGpioLight
from custom_components.gpio_integration.schemas import (
    CONF_DEFAULT_STATE,
    CONF_FREQUENCY,
    CONF_NAME,
)
from custom_components.gpio_integration.schemas.light import (
    CONF_BLUE_PIN,
    CONF_GREEN_PIN,
    CONF_RED_PIN,
    RgbLightConfig,
)
from tests.mocks import assert_gpio_blink, get_next_pin


def __create_config(
    pin_red: int = None,
    pin_blue: int = None,
    pim_green: int = None,
    default_state=False,
    frequency=50,
):
    return RgbLightConfig(
        {
            CONF_NAME: "Test Name",
            CONF_RED_PIN: get_next_pin() if pin_red is None else pin_red,
            CONF_BLUE_PIN: get_next_pin() if pin_blue is None else pin_blue,
            CONF_GREEN_PIN: get_next_pin() if pim_green is None else pim_green,
            CONF_FREQUENCY: frequency,
            CONF_DEFAULT_STATE: default_state,
        }
    )


def test__RgbLight_should_init_default_light(mocked_factory):
    n1 = get_next_pin()
    n2 = get_next_pin()
    n3 = get_next_pin()
    p1 = mocked_factory.pin(n1)
    p2 = mocked_factory.pin(n2)
    p3 = mocked_factory.pin(n3)
    with RgbGpioLight(__create_config(n1, n2, n3, frequency=0)) as gpio:
        assert gpio.is_on is False
        assert gpio.brightness == 0
        assert ColorMode.ONOFF in gpio._attr_supported_color_modes
        assert ColorMode.RGB in gpio._attr_supported_color_modes
        assert ColorMode.BRIGHTNESS in gpio._attr_supported_color_modes
        assert ColorMode.WHITE in gpio._attr_supported_color_modes
        assert "Blink" in gpio._attr_effect_list
        assert "E_OFF" in gpio._attr_effect
        assert gpio._attr_color_mode == ColorMode.RGB
        assert p1._function == "output"
        assert p1._frequency is None
        assert p2._function == "output"
        assert p2._frequency is None
        assert p3._function == "output"
        assert p3._frequency is None


def test__RgbGpioLight_LED_should_init_frequency(mocked_factory):
    n1 = get_next_pin()
    n2 = get_next_pin()
    n3 = get_next_pin()
    p1 = mocked_factory.pin(n1)
    p2 = mocked_factory.pin(n2)
    p3 = mocked_factory.pin(n3)
    with RgbGpioLight(__create_config(n1, n2, n3, frequency=200)):
        assert p1._function == "output"
        assert p1._frequency == 200
        assert p2._function == "output"
        assert p2._frequency == 200
        assert p3._function == "output"
        assert p3._frequency == 200


def test__RgbGpioLight_LED_should_init_default_state(mocked_factory):
    with RgbGpioLight(__create_config(default_state=True)) as gpio:
        assert gpio.is_on is True
        assert gpio.brightness == 255
        assert gpio.ha_state_update_scheduled is False


def test__RgbGpioLight_LED_should_turn_led_on_off(mocked_factory):
    n1 = get_next_pin()
    n2 = get_next_pin()
    n3 = get_next_pin()
    p1 = mocked_factory.pin(n1)
    p2 = mocked_factory.pin(n2)
    p3 = mocked_factory.pin(n3)
    with RgbGpioLight(__create_config(n1, n2, n3)) as gpio:
        gpio.turn_on()
        assert p1._state == 1
        assert p2._state == 1
        assert p3._state == 1
        assert gpio.brightness == 255
        assert gpio.is_on is True

        gpio.turn_off()
        assert p1._state == 0
        assert p2._state == 0
        assert p3._state == 0
        assert gpio.brightness == 0
        assert gpio.is_on is False


def test__RgbGpioLight_LED_should_turn_bulb_on_off(mocked_factory):
    n1 = get_next_pin()
    n2 = get_next_pin()
    n3 = get_next_pin()
    p1 = mocked_factory.pin(n1)
    p2 = mocked_factory.pin(n2)
    p3 = mocked_factory.pin(n3)
    with RgbGpioLight(__create_config(n1, n2, n3, frequency=0)) as gpio:
        gpio.turn_on()
        assert p1._state is True
        assert p2._state is True
        assert p3._state is True
        assert gpio.brightness == 255
        assert gpio.is_on is True

        gpio.turn_off()
        assert p1._state is False
        assert p2._state is False
        assert p3._state is False
        assert gpio.brightness == 0
        assert gpio.is_on is False


def test__RgbGpioLight_LED_on_off_should_write_ha(mocked_factory):
    with RgbGpioLight(__create_config()) as gpio:

        gpio.ha_state_write = False
        gpio.turn_on()
        assert gpio.ha_state_update_scheduled is True

        gpio.ha_state_write = False
        gpio.turn_off()
        assert gpio.ha_state_update_scheduled is True


def test__RgbGpioLight_LED_should_set_brightness(mocked_factory):
    n1 = get_next_pin()
    n2 = get_next_pin()
    n3 = get_next_pin()
    p1 = mocked_factory.pin(n1)
    p2 = mocked_factory.pin(n2)
    p3 = mocked_factory.pin(n3)
    with RgbGpioLight(
        __create_config(n1, n2, n3, default_state=True, frequency=100)
    ) as gpio:

        gpio.turn_on(**{"A_BRIGHTNESS": 130})
        assert p1._state == 0.5098
        assert p2._state == 0.5098
        assert p3._state == 0.5098
        assert gpio.brightness == 130
        assert gpio.is_on is True

        gpio.turn_off(**{"A_BRIGHTNESS": 0})
        assert p1._state == 0
        assert p2._state == 0
        assert p3._state == 0
        assert gpio.brightness == 0
        assert gpio.is_on is False


def test__RgbGpioLight_LED_should_set_rgb(mocked_factory):
    n_r = get_next_pin()
    n_b = get_next_pin()
    n_g = get_next_pin()
    p_r = mocked_factory.pin(n_r)
    p_b = mocked_factory.pin(n_b)
    p_g = mocked_factory.pin(n_g)
    with RgbGpioLight(
        __create_config(n_r, n_b, n_g, default_state=True, frequency=100)
    ) as gpio:
        # set Red only
        gpio.turn_on(**{"A_RGB": (51, 0, 0)})
        assert (p_r._state, p_g._state, p_b._state) == (0.2, 0.0, 0.0)
        assert gpio.brightness == 255
        assert gpio.is_on is True

        # set Green only
        gpio.turn_on(**{"A_RGB": (0, 51, 0)})
        assert (p_r._state, p_g._state, p_b._state) == (0.0, 0.2, 0.0)

        # set Blue only
        gpio.turn_on(**{"A_RGB": (0, 0, 51)})
        assert (p_r._state, p_g._state, p_b._state) == (0.0, 0.0, 0.2)

        # mix
        gpio.turn_on(**{"A_RGB": (25.5, 255, 51)})
        assert (p_r._state, p_g._state, p_b._state) == (0.1, 1.0, 0.2)


def test__RgbGpioLight_should_pulse_slow(mocked_factory, mock_gpio_thread):
    n1 = get_next_pin()
    n2 = get_next_pin()
    n3 = get_next_pin()
    p1 = mocked_factory.pin(n1)
    p2 = mocked_factory.pin(n2)
    p3 = mocked_factory.pin(n3)
    with RgbGpioLight(__create_config(n1, n2, n3, frequency=0)) as gpio:
        gpio.turn_on(**{"A_FLASH": "F_LONG"})

        assert gpio.brightness == 0
        assert gpio.is_on is False

        assert_gpio_blink(p1, gpio, [(True, 1.5), (False, 1.5)] * 4)
        assert_gpio_blink(p2, gpio, [(True, 1.5), (False, 1.5)] * 4)
        assert_gpio_blink(p3, gpio, [(True, 1.5), (False, 1.5)] * 4)


def test__RgbGpioLight_should_pulse_fast(mocked_factory, mock_gpio_thread):
    n1 = get_next_pin()
    n2 = get_next_pin()
    n3 = get_next_pin()
    p1 = mocked_factory.pin(n1)
    p2 = mocked_factory.pin(n2)
    p3 = mocked_factory.pin(n3)
    with RgbGpioLight(__create_config(n1, n2, n3, frequency=0)) as gpio:
        gpio.turn_on(**{"A_FLASH": "F_SHORT"})

        assert gpio.brightness == 0
        assert gpio.is_on is False
        assert_gpio_blink(p1, gpio, [(True, 1.2), (False, 1.2)] * 2)
        assert_gpio_blink(p2, gpio, [(True, 1.2), (False, 1.2)] * 2)
        assert_gpio_blink(p3, gpio, [(True, 1.2), (False, 1.2)] * 2)


def test__RgbGpioLight_should_effect_blink(mocked_factory, mock_gpio_thread):
    n1 = get_next_pin()
    n2 = get_next_pin()
    n3 = get_next_pin()
    p1 = mocked_factory.pin(n1)
    p2 = mocked_factory.pin(n2)
    p3 = mocked_factory.pin(n3)
    with RgbGpioLight(__create_config(n1, n2, n3, frequency=0)) as gpio:
        gpio.turn_on(**{"A_EFFECT": "Blink"})

        assert gpio.brightness == 0
        assert gpio.is_on is False

        assert_gpio_blink(p1, gpio, [(True, 1), (False, 1)] * 200)
        assert_gpio_blink(p2, gpio, [(True, 1), (False, 1)] * 200)
        assert_gpio_blink(p3, gpio, [(True, 1), (False, 1)] * 200)


def test__RgbGpioLight_should_effect_off(mocked_factory, mock_gpio_thread):
    with RgbGpioLight(__create_config(frequency=0)) as gpio:
        gpio.turn_on(**{"A_EFFECT": "E_OFF"})

        assert gpio.brightness == 0
        assert gpio.is_on is False


def test__RgbGpioLight_pwm_should_pulse_fast(mocked_factory, mock_gpio_thread):
    n1 = get_next_pin()
    n2 = get_next_pin()
    n3 = get_next_pin()
    p1 = mocked_factory.pin(n1)
    p2 = mocked_factory.pin(n2)
    p3 = mocked_factory.pin(n3)
    with RgbGpioLight(__create_config(n1, n2, n3, frequency=100)) as gpio:
        gpio.turn_on(**{"A_FLASH": "F_SHORT"})

        assert gpio.brightness == 0
        assert gpio.is_on is False
        steps = (
            ([(x / 100.0, 0.04) for x in range(4, 100, 4)])
            + ([(x / 100.0, 0.04) for x in range(100, 0, -4)])
            + ([(0.0, 0.04)])
        )

        assert_gpio_blink(p1, gpio, steps * 2)
        assert_gpio_blink(p2, gpio, steps * 2)
        assert_gpio_blink(p3, gpio, steps * 2)


@pytest.mark.asyncio
async def test__RgbGpioLight_will_close_pin(mocked_factory):
    n1 = get_next_pin()
    n2 = get_next_pin()
    n3 = get_next_pin()
    p1 = mocked_factory.pin(n1)
    p2 = mocked_factory.pin(n2)
    p3 = mocked_factory.pin(n3)
    gpio = RgbGpioLight(__create_config(n1, n2, n3))

    await gpio.async_will_remove_from_hass()

    assert p1.closed is True
    assert p2.closed is True
    assert p3.closed is True
    assert gpio._io is None
