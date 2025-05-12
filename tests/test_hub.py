import pytest
from homeassistant.const import (
    CONF_MODE,
    CONF_NAME,
    CONF_PORT,
    CONF_UNIQUE_ID,
    Platform,
)

from custom_components.gpio_integration.hub import Hub
from custom_components.gpio_integration.schemas import (
    CONF_DEFAULT_STATE,
    CONF_FREQUENCY,
    CONF_INVERT_LOGIC,
    CONF_PIN_CLOSED_SENSOR,
    CONF_RELAY_CLOSE_INVERT,
    CONF_RELAY_CLOSE_PIN,
    CONF_RELAY_OPEN_INVERT,
    CONF_RELAY_OPEN_PIN,
    CONF_RELAY_TIME,
)
from custom_components.gpio_integration.schemas.binary_sensor import BinarySensorConfig
from custom_components.gpio_integration.schemas.cover import ToggleRollerConfig
from custom_components.gpio_integration.schemas.light import (
    CONF_BLUE_PIN,
    CONF_GREEN_PIN,
    CONF_RED_PIN,
    RgbLightConfig,
)
from custom_components.gpio_integration.schemas.main import EntityTypes
from custom_components.gpio_integration.schemas.pwm import PwmConfig
from custom_components.gpio_integration.schemas.servo import (
    CONF_MAX_ANGLE,
    CONF_MAX_DUTY_CYCLE,
    CONF_MIN_ANGLE,
    CONF_MIN_DUTY_CYCLE,
    ServoConfig,
)
from custom_components.gpio_integration.schemas.switch import SwitchConfig


def _create_hub(type: str) -> Hub:
    return Hub(
        {
            "type": type,
            CONF_NAME: "Test Name",
            CONF_MODE: 1,
            CONF_PORT: 1,
            CONF_DEFAULT_STATE: False,
            CONF_INVERT_LOGIC: False,
            CONF_UNIQUE_ID: "",
            CONF_FREQUENCY: 100,
            CONF_MIN_ANGLE: 10,
            CONF_MAX_ANGLE: 20,
            CONF_MIN_DUTY_CYCLE: 1,
            CONF_MAX_DUTY_CYCLE: 2,
            CONF_RELAY_TIME: 0,
            CONF_RELAY_OPEN_PIN: 2,
            CONF_RELAY_CLOSE_PIN: 3,
            CONF_PIN_CLOSED_SENSOR: 4,
            CONF_RED_PIN: 5,
            CONF_GREEN_PIN: 6,
            CONF_BLUE_PIN: 6,
            CONF_RELAY_CLOSE_INVERT: False,
            CONF_RELAY_OPEN_INVERT: False,
        }
    )


def _assert_hub(hub: Hub, type: EntityTypes, platforms: list[str], config: type):
    assert hub._type == type
    assert hub.is_type(type) is True
    assert isinstance(hub.config, config)
    assert hub.platforms == platforms


@pytest.mark.parametrize(
    "key,type,platforms,config",
    [
        (
            "binary_sensor",
            EntityTypes.BINARY_SENSOR,
            [Platform.BINARY_SENSOR],
            BinarySensorConfig,
        ),
        (
            "cover_toggle",
            EntityTypes.COVER_TOGGLE,
            [Platform.COVER],
            ToggleRollerConfig,
        ),
        ("fan", EntityTypes.FAN, [Platform.FAN], PwmConfig),
        ("light_pwm_led", EntityTypes.LIGHT_PWM_LED, [Platform.LIGHT], PwmConfig),
        ("light_rgb_led", EntityTypes.LIGHT_RGB_LED, [Platform.LIGHT], RgbLightConfig),
        ("servo", EntityTypes.SERVO, [Platform.NUMBER], ServoConfig),
        ("switch", EntityTypes.SWITCH, [Platform.SWITCH], SwitchConfig),
    ],
    ids=[
        "binary_sensor",
        "cover_toggle",
        "fan",
        "light_pwm_led",
        "light_rgb_led",
        "servo",
        "switch",
    ],
)
def test__Hub_should_init(
    key: str, type: EntityTypes, platforms: list[str], config: type
):
    hub = _create_hub(key)
    _assert_hub(hub, type, platforms, config)
