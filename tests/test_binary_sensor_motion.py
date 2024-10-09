from unittest.mock import Mock, patch

from homeassistant.const import CONF_MODE, CONF_PORT

from custom_components.gpio_integration.binary_sensor import GpioBinarySensor
from custom_components.gpio_integration.schemas import (
    CONF_BOUNCE_TIME,
    CONF_DEFAULT_STATE,
    CONF_EDGE_EVENT_TIMEOUT,
    CONF_INVERT_LOGIC,
    CONF_NAME,
)
from custom_components.gpio_integration.schemas.binary_sensor import (
    BinarySensorConfig,
)
from tests.mocks import get_next_pin


def __create_config(port=None, default_state=False, invert_logic=False, timeout=10):
    return BinarySensorConfig(
        {
            CONF_NAME: "Test Name",
            CONF_PORT: get_next_pin() if port is None else port,
            CONF_MODE: "read",
            CONF_BOUNCE_TIME: 5,
            CONF_EDGE_EVENT_TIMEOUT: timeout,
            CONF_DEFAULT_STATE: default_state,
            CONF_INVERT_LOGIC: invert_logic,
        }
    )


def test__GpioMotionBinarySensor_should_init_default_sate(mocked_factory):
    with GpioBinarySensor(__create_config()) as gpio:
        assert gpio.is_on is False


def test__GpioMotionBinarySensor_edge_events_should_update_state(mocked_factory):
    number = get_next_pin()
    pin = mocked_factory.pin(number)
    with GpioBinarySensor(__create_config(number)) as gpio:

        assert gpio.is_on is False

        pin._state = False
        pin.drive_high()

        assert gpio.ha_state_update_scheduled is True


def test__GpioMotionBinarySensor_should_not_update(mocked_factory):
    mocked_factory.set_ticks(0.0)

    number = get_next_pin()
    pin = mocked_factory.pin(number)
    pin._state = 0

    with GpioBinarySensor(__create_config(number)) as gpio:

        mocked_factory.set_ticks(1.0)
        gpio.update()
        assert gpio.ha_state_write is False
        assert gpio._state is False

        mocked_factory.set_ticks(20.0)
        gpio.update()
        assert gpio._state is False
        assert gpio.ha_state_write is False

        # gpio.__event_time = 0
        # gpio.update()
        # assert gpio._state is False
        # assert gpio.ha_state_write is False


def test__GpioMotionBinarySensor_should_update_state_after_elapsed(mocked_factory):
    number = get_next_pin()
    pin = mocked_factory.pin(number)

    # set pin state to True and time to 1.0
    mocked_factory.set_ticks(1.0)
    pin._state = 1

    with GpioBinarySensor(__create_config(number, timeout=5)) as gpio:
        # update state will get active_time = 6.01 - 1.0 = 5.01
        mocked_factory.set_ticks(6.01)
        gpio.update()

        assert gpio.is_on is False
