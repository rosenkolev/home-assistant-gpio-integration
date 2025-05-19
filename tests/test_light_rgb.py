import pytest
from homeassistant.components.light import ColorMode

from custom_components.gpio_integration.light import RgbGpioLight
from custom_components.gpio_integration.schemas import (
    CONF_DEFAULT_STATE,
    CONF_FREQUENCY,
    CONF_INVERT_LOGIC,
    CONF_NAME,
)
from custom_components.gpio_integration.schemas.light import (
    CONF_BLUE_INTENSITY,
    CONF_BLUE_PIN,
    CONF_GREEN_INTENSITY,
    CONF_GREEN_PIN,
    CONF_RED_INTENSITY,
    CONF_RED_PIN,
    RgbLightConfig,
)
from tests.test__mocks import MockFactory, assert_gpio_blink, get_next_pin


class RgbLightTestCase:
    def __init__(self, factory: MockFactory):
        self.pin_names = (get_next_pin(), get_next_pin(), get_next_pin())
        self.red = factory.pin(self.pin_names[0])
        self.green = factory.pin(self.pin_names[1])
        self.blue = factory.pin(self.pin_names[2])

    def create_config(
        self,
        default_state=False,
        invert_logic=False,
        red_intensity=100,
        green_intensity=100,
        blue_intensity=100,
        frequency=50,
    ):
        return RgbLightConfig(
            {
                CONF_NAME: "Test Name",
                CONF_RED_PIN: self.pin_names[0],
                CONF_GREEN_PIN: self.pin_names[1],
                CONF_BLUE_PIN: self.pin_names[2],
                CONF_RED_INTENSITY: red_intensity,
                CONF_GREEN_INTENSITY: green_intensity,
                CONF_BLUE_INTENSITY: blue_intensity,
                CONF_FREQUENCY: frequency,
                CONF_DEFAULT_STATE: default_state,
                CONF_INVERT_LOGIC: invert_logic,
            }
        )

    def assert_frequency(self, frequency: None | int):
        assert self.red._function == "output"
        assert self.green._function == "output"
        assert self.blue._function == "output"
        assert self.red._frequency is frequency
        assert self.green._frequency is frequency
        assert self.blue._frequency is frequency

    def assert_pin_state(self, r: float | bool, g: float | bool, b: float | bool):
        assert self.red._state == r
        assert self.green._state == g
        assert self.blue._state == b


def test__RgbLight_should_init_default_light(mocked_factory):
    tc = RgbLightTestCase(mocked_factory)
    with RgbGpioLight(tc.create_config(frequency=0)) as gpio:
        assert gpio.is_on is False
        assert gpio.brightness == 0
        assert ColorMode.RGB in gpio._attr_supported_color_modes
        assert ColorMode.WHITE in gpio._attr_supported_color_modes
        assert "Blink" in gpio._attr_effect_list
        assert "E_OFF" in gpio._attr_effect
        assert gpio._attr_color_mode == ColorMode.RGB

        tc.assert_frequency(None)


def test__RgbLight_stand_alone_color_modes_are_removed(mocked_factory):
    tc = RgbLightTestCase(mocked_factory)
    with RgbGpioLight(tc.create_config(frequency=0)) as gpio:
        assert ColorMode.ONOFF not in gpio._attr_supported_color_modes
        assert ColorMode.BRIGHTNESS not in gpio._attr_supported_color_modes
        assert ColorMode.UNKNOWN not in gpio._attr_supported_color_modes


def test__RgbGpioLight_LED_should_init_frequency(mocked_factory):
    tc = RgbLightTestCase(mocked_factory)
    with RgbGpioLight(tc.create_config(frequency=200)):
        tc.assert_frequency(200)


def test__RgbGpioLight_LED_should_init_default_state(mocked_factory):
    tc = RgbLightTestCase(mocked_factory)
    with RgbGpioLight(tc.create_config(default_state=True)) as gpio:
        assert gpio.is_on is True
        assert gpio.brightness == 255
        assert gpio.ha_state_update_scheduled is False


def test__RgbGpioLight_LED_should_init_invert(mocked_factory):
    tc = RgbLightTestCase(mocked_factory)
    with RgbGpioLight(tc.create_config(invert_logic=True)):
        tc.assert_pin_state(1.0, 1.0, 1.0)


def test__RgbGpioLight_LED_should_turn_led_on_off(mocked_factory):
    tc = RgbLightTestCase(mocked_factory)
    with RgbGpioLight(tc.create_config()) as gpio:
        gpio.turn_on()

        tc.assert_pin_state(1.0, 1.0, 1.0)
        assert gpio.brightness == 255
        assert gpio.is_on is True

        gpio.turn_off()

        tc.assert_pin_state(0.0, 0.0, 0.0)
        assert gpio.brightness == 0
        assert gpio.is_on is False


def test__RgbGpioLight_LED_should_turn_led_on_invert(mocked_factory):
    tc = RgbLightTestCase(mocked_factory)
    with RgbGpioLight(tc.create_config(invert_logic=True)) as gpio:
        tc.assert_pin_state(1.0, 1.0, 1.0)
        gpio.turn_on()
        tc.assert_pin_state(0.0, 0.0, 0.0)


def test__RgbGpioLight_LED_should_turn_bulb_on_off(mocked_factory):
    tc = RgbLightTestCase(mocked_factory)
    with RgbGpioLight(tc.create_config(frequency=0)) as gpio:
        gpio.turn_on()
        tc.assert_pin_state(True, True, True)
        assert gpio.brightness == 255
        assert gpio.is_on is True

        gpio.turn_off()
        tc.assert_pin_state(False, False, False)
        assert gpio.brightness == 0
        assert gpio.is_on is False


def test__RgbGpioLight_LED_on_off_should_write_ha(mocked_factory):
    tc = RgbLightTestCase(mocked_factory)
    with RgbGpioLight(tc.create_config()) as gpio:

        gpio.ha_state_write = False
        gpio.turn_on()
        assert gpio.ha_state_update_scheduled is True

        gpio.ha_state_write = False
        gpio.turn_off()
        assert gpio.ha_state_update_scheduled is True


def test__RgbGpioLight_LED_should_set_brightness(mocked_factory):
    tc = RgbLightTestCase(mocked_factory)
    with RgbGpioLight(tc.create_config(default_state=True, frequency=100)) as gpio:

        gpio.turn_on(**{"A_BRIGHTNESS": 130})
        tc.assert_pin_state(0.5098, 0.5098, 0.5098)
        assert gpio.brightness == 130
        assert gpio.is_on is True

        gpio.turn_off(**{"A_BRIGHTNESS": 0})
        tc.assert_pin_state(0.0, 0.0, 0.0)
        assert gpio.brightness == 0
        assert gpio.is_on is False


def test__RgbGpioLight_LED_should_set_rgb(mocked_factory):
    tc = RgbLightTestCase(mocked_factory)
    with RgbGpioLight(tc.create_config(default_state=True, frequency=100)) as gpio:
        # set Red only
        gpio.turn_on(**{"A_RGB": (51, 0, 0)})
        tc.assert_pin_state(0.2, 0.0, 0.0)
        assert gpio.brightness == 255
        assert gpio.is_on is True

        # set Green only
        gpio.turn_on(**{"A_RGB": (0, 51, 0)})
        tc.assert_pin_state(0.0, 0.2, 0.0)

        # set Blue only
        gpio.turn_on(**{"A_RGB": (0, 0, 51)})
        tc.assert_pin_state(0.0, 0.0, 0.2)

        # mix
        gpio.turn_on(**{"A_RGB": (25.5, 255, 51)})
        tc.assert_pin_state(0.1, 1.0, 0.2)


def test__RgbGpioLight_LED_should_turn_led_on_with_intensity_shift(mocked_factory):
    tc = RgbLightTestCase(mocked_factory)
    with RgbGpioLight(
        tc.create_config(red_intensity=30, green_intensity=95, blue_intensity=50)
    ) as gpio:
        # White
        gpio.turn_on()
        tc.assert_pin_state(0.3, 0.95, 0.5)

        # Color
        gpio.turn_on(**{"A_RGB": (100, 150, 200)})
        tc.assert_pin_state(0.1176, 0.5588, 0.3922)


def test__RgbGpioLight_should_pulse_slow(mocked_factory, mock_gpio_thread):
    tc = RgbLightTestCase(mocked_factory)
    with RgbGpioLight(tc.create_config(frequency=0)) as gpio:
        gpio.turn_on(**{"A_FLASH": "F_LONG"})

        assert gpio.brightness == 0
        assert gpio.is_on is False

        assert_gpio_blink(tc.red, gpio, [(True, 1.5), (False, 1.5)] * 4)
        assert_gpio_blink(tc.green, gpio, [(True, 1.5), (False, 1.5)] * 4)
        assert_gpio_blink(tc.blue, gpio, [(True, 1.5), (False, 1.5)] * 4)


def test__RgbGpioLight_should_pulse_fast(mocked_factory, mock_gpio_thread):
    tc = RgbLightTestCase(mocked_factory)
    with RgbGpioLight(tc.create_config(frequency=0)) as gpio:
        gpio.turn_on(**{"A_FLASH": "F_SHORT"})

        assert gpio.brightness == 0
        assert gpio.is_on is False
        assert_gpio_blink(tc.red, gpio, [(True, 1.2), (False, 1.2)] * 2)
        assert_gpio_blink(tc.green, gpio, [(True, 1.2), (False, 1.2)] * 2)
        assert_gpio_blink(tc.blue, gpio, [(True, 1.2), (False, 1.2)] * 2)


def test__RgbGpioLight_should_effect_blink(mocked_factory, mock_gpio_thread):
    tc = RgbLightTestCase(mocked_factory)
    with RgbGpioLight(tc.create_config(frequency=0)) as gpio:
        gpio.turn_on(**{"A_EFFECT": "Blink"})

        assert gpio.brightness == 0
        assert gpio.is_on is False

        assert_gpio_blink(tc.red, gpio, [(True, 1), (False, 1)] * 200)
        assert_gpio_blink(tc.green, gpio, [(True, 1), (False, 1)] * 200)
        assert_gpio_blink(tc.blue, gpio, [(True, 1), (False, 1)] * 200)


def test__RgbGpioLight_should_effect_off(mocked_factory, mock_gpio_thread):
    tc = RgbLightTestCase(mocked_factory)
    with RgbGpioLight(tc.create_config(frequency=0)) as gpio:
        gpio.turn_on(**{"A_EFFECT": "E_OFF"})

        assert gpio.brightness == 0
        assert gpio.is_on is False


def test__RgbGpioLight_pwm_should_pulse_fast(mocked_factory, mock_gpio_thread):
    tc = RgbLightTestCase(mocked_factory)
    with RgbGpioLight(tc.create_config(frequency=100)) as gpio:
        gpio.turn_on(**{"A_FLASH": "F_SHORT"})

        assert gpio.brightness == 0
        assert gpio.is_on is False
        steps = (
            ([(x / 100.0, 0.04) for x in range(4, 100, 4)])
            + ([(x / 100.0, 0.04) for x in range(100, 0, -4)])
            + ([(0.0, 0.04)])
        )

        assert_gpio_blink(tc.red, gpio, steps * 2)
        assert_gpio_blink(tc.green, gpio, steps * 2)
        assert_gpio_blink(tc.blue, gpio, steps * 2)


@pytest.mark.asyncio
async def test__RgbGpioLight_will_close_pin(mocked_factory):
    tc = RgbLightTestCase(mocked_factory)
    gpio = RgbGpioLight(tc.create_config())

    await gpio.async_will_remove_from_hass()

    assert tc.red.closed is True
    assert tc.green.closed is True
    assert tc.blue.closed is True
    assert gpio._io is None
