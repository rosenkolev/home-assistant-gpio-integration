"""Use pytest to test the GPIO module custom_components\gpio_integration\gpio.py in isolation by mocking `gpiod`."""

from unittest.mock import patch, Mock, ANY

import mocked_models

from custom_components.gpio_integration import gpio


@patch.object(gpio, "DEFAULT_DEVICE", "/dev/gpiochip0")
def test__Gpio_init_should_bind_Input_line():
    with patch("gpiod.request_lines", return_value=None) as request_lines:
        gpio.Gpio(1, mode="read")

        request_lines.assert_called_once_with(
            "/dev/gpiochip0",
            consumer="gpio_integration",
            config={1: ANY},
        )


@patch.object(gpio, "HIGH", 1)
def test__Gpio_init_should_set_default_state():
    io = gpio.Gpio(1, mode="write", default_value=True)

    io.req.set_values.assert_called_with({1: 1})


@patch.object(gpio, "HIGH", 1)
def test__Gpio_should_read():
    io = gpio.Gpio(6, mode="read")

    io.req.get_value.return_value = 1
    res = io.read()

    io.req.get_value.assert_called_with(6)
    assert res == True


@patch.object(gpio, "LOW", 0)
@patch.object(gpio, "HIGH", 1)
def test__Gpio_should_write():
    io = gpio.Gpio(7, mode="write")

    io.write(True)
    io.req.set_values.assert_called_with({7: 1})

    io.write(False)
    io.req.set_values.assert_called_with({7: 0})
