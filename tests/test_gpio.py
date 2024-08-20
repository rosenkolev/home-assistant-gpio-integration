"""Use pytest to test the GPIO module custom_components\gpio_integration\gpio.py in isolation by mocking `gpiod`."""

import sys
from unittest.mock import patch, Mock

sys.modules["voluptuous"] = Mock()
sys.modules["homeassistant"] = Mock()
sys.modules["homeassistant.const"] = Mock()
sys.modules["homeassistant.core"] = Mock()
sys.modules["homeassistant.config_entries"] = Mock()
sys.modules["homeassistant.helpers"] = Mock()
sys.modules["homeassistant.helpers.config_validation"] = Mock()
sys.modules["homeassistant.helpers.typing"] = Mock()
sys.modules["homeassistant.helpers.selector"] = Mock()
sys.modules["homeassistant.exceptions"] = Mock()
sys.modules["gpiod"] = Mock()
sys.modules["gpiod.line"] = Mock()
sys.modules["gpiod.line_settings"] = Mock()

from custom_components.gpio_integration import gpio


@patch("gpiod.is_gpiochip_device")
def test__guess_default_device(is_gpiochip_device: Mock):
    is_gpiochip_device.return_value = True
    with patch.object(gpio, "read_device_model", return_value=[]):
        assert gpio._guess_default_device() == "/dev/gpiochip0"

    with patch.object(
        gpio, "read_device_model", return_value=["Raspberry Pi 5 Model B"]
    ):
        assert gpio._guess_default_device() == "/dev/gpiochip4"


@patch("gpiod.request_lines")
@patch.object(gpio, "DEFAULT_DEVICE", "/dev/gpiochip0")
def test__Gpio_init_should_bind_Input_line(request_lines: Mock):
    request_lines.return_value = None
    with patch.object(gpio, "DEFAULT_DEVICE", "/dev/gpiochip0"):
        gpio.Gpio(1, mode="read")
        request_lines.assert_called_once_with(
            "/dev/gpiochip0", consumer="gpio_integration"
        )
