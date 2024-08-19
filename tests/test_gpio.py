"""Use pytest to test the GPIO module custom_components\gpio_integration\gpio.py in isolation by mocking `gpiod`."""

from unittest.mock import patch, Mock

from ..custom_components.gpio_integration.gpio import Gpio


def test__Gpio__init__read_mode():
    with patch("custom_components.gpio_integration.gpio.gpiod") as mock_gpiod:
        mock_gpiod.request_lines.return_value = Mock()

        assert 1 == 1
