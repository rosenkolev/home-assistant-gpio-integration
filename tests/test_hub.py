from homeassistant.const import CONF_NAME, CONF_PORT, CONF_UNIQUE_ID

from custom_components.gpio_integration.hub import Hub
from custom_components.gpio_integration.schemas import (
    CONF_DEFAULT_STATE,
    CONF_FREQUENCY,
    CONF_INVERT_LOGIC,
)
from custom_components.gpio_integration.schemas.main import EntityTypes
from custom_components.gpio_integration.schemas.pwm import PwmConfig
from custom_components.gpio_integration.schemas.switch import SwitchConfig


def _create_hub(type: str) -> Hub:
    return Hub(
        {
            "type": type,
            CONF_NAME: "Test Name",
            CONF_PORT: 1,
            CONF_DEFAULT_STATE: False,
            CONF_INVERT_LOGIC: False,
            CONF_UNIQUE_ID: "",
            CONF_FREQUENCY: 100,
        }
    )


def _assert_hub(hub: Hub, type: EntityTypes, platforms: list[str], config: type):
    assert hub._type == type
    assert hub.is_type(type) is True
    assert isinstance(hub.config, config)
    assert hub.platforms == platforms


def test__Hub_should_init_switch():
    hub = _create_hub("switch")
    _assert_hub(hub, EntityTypes.SWITCH, ["switch"], SwitchConfig)


def test__Hub_should_init_fan():
    hub = _create_hub("fan")
    _assert_hub(hub, EntityTypes.FAN, ["fan"], PwmConfig)
