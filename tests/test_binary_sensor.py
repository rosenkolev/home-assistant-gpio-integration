import pytest
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


def __create_config(
    port=None, default_state=False, invert_logic=False, event_timeout=0
):
    return BinarySensorConfig(
        {
            CONF_NAME: "Test Name",
            CONF_PORT: get_next_pin() if port is None else port,
            CONF_MODE: "read",
            CONF_BOUNCE_TIME: 5,
            CONF_EDGE_EVENT_TIMEOUT: event_timeout,
            CONF_DEFAULT_STATE: default_state,
            CONF_INVERT_LOGIC: invert_logic,
        }
    )


def test__GpioBinarySensor_should_init_default_state(mocked_factory):
    number = get_next_pin()
    pin = mocked_factory.pin(number)
    with GpioBinarySensor(__create_config(number)) as gpio:
        assert gpio.is_on is False
        assert pin.info.number == number


def test__GpioBinarySensor_update_should_set_state_not_inverted(mocked_factory):
    number = get_next_pin()
    pin = mocked_factory.pin(number)
    with GpioBinarySensor(__create_config(number)) as gpio:

        pin._state = True
        gpio.update()
        assert gpio.is_on is True

        pin._state = False
        gpio.update()
        assert gpio.is_on is False


def test__GpioBinarySensor_update_should_set_state_inverted(mocked_factory):
    number = get_next_pin()
    pin = mocked_factory.pin(number)
    with GpioBinarySensor(__create_config(number, invert_logic=True)) as gpio:

        pin._state = True
        gpio.update()
        assert gpio.is_on is False

        pin._state = False
        gpio.update()
        assert gpio.is_on is True


def test__GpioBinarySensor_edge_events_should_trigger_update(mocked_factory):
    number = get_next_pin()
    pin = mocked_factory.pin(number)
    with GpioBinarySensor(__create_config(number)) as gpio:
        pin._state = False
        pin.drive_high()
        assert gpio.ha_state_update_scheduled is True


@pytest.mark.asyncio
async def test__GpioBinarySensor_will_close_pin(mocked_factory):
    number = get_next_pin()
    pin = mocked_factory.pin(number)
    gpio = GpioBinarySensor(__create_config(port=number))
    await gpio.async_will_remove_from_hass()
    assert gpio._io is None
    assert pin.closed is True
