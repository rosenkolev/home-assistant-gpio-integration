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
from tests.test__mocks import get_next_pin


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


def test__GpioBinarySensor_RoE_should_init_default_state(mocked_factory):
    number = get_next_pin()
    pin = mocked_factory.pin(number)
    with GpioBinarySensor(__create_config(number, event_timeout=1)) as gpio:
        assert gpio.is_on is False
        assert pin.info.number == number


def test__GpioBinarySensor_RoE_edge_events_should_update_state(mocked_factory):
    number = get_next_pin()
    pin = mocked_factory.pin(number)
    with GpioBinarySensor(__create_config(number, event_timeout=1)) as gpio:
        assert gpio.is_on is False

        pin._state = False
        pin.drive_high()

        assert gpio.ha_state_update_scheduled is True


def test__GpioBinarySensor_RoE_should_not_update_when_no_edge(mocked_factory):
    mocked_factory.set_ticks(0.0)

    number = get_next_pin()
    pin = mocked_factory.pin(number)
    pin._state = 0

    with GpioBinarySensor(__create_config(number, event_timeout=10)) as gpio:

        mocked_factory.set_ticks(1.0)
        gpio.update()
        assert gpio.ha_state_write is False
        assert gpio._state is False

        mocked_factory.set_ticks(20.0)
        gpio.update()
        assert gpio._state is False
        assert gpio.ha_state_write is False


def test__GpioBinarySensor_RoE_should_update_state_after_elapsed(mocked_factory):
    number = get_next_pin()
    pin = mocked_factory.pin(number)

    # set pin state to True and time to 1.0
    mocked_factory.set_ticks(1.0)
    pin._state = 1

    with GpioBinarySensor(__create_config(number, event_timeout=5)) as gpio:
        # update state will get active_time = 6.01 - 1.0 = 5.01
        mocked_factory.set_ticks(6.01)
        gpio.update()

        assert gpio.is_on is False


@pytest.mark.asyncio
async def test__GpioBinarySensor_RoE_should_auto_update_to_off(
    mocked_factory, mock_track_time_interval
):
    number = get_next_pin()
    mocked_factory.set_ticks(1.5)  # set time to 1.5 sec

    with GpioBinarySensor(__create_config(number, event_timeout=2)) as gpio:
        await gpio.async_added_to_hass()

        gpio._state = True
        gpio._event_occurred = True

        # 2 sec have passed, should auto update to off
        mocked_factory.set_ticks(3.5)
        mock_track_time_interval.tick()

        assert gpio.ha_state_update_scheduled is True


@pytest.mark.asyncio
async def test__GpioBinarySensor_RoE_should_auto_update_to_on(
    mocked_factory, mock_track_time_interval
):
    number = get_next_pin()
    mocked_factory.set_ticks(1.5)  # set time to 1.5 sec

    with GpioBinarySensor(__create_config(number, event_timeout=2)) as gpio:
        await gpio.async_added_to_hass()

        gpio._state = False
        gpio._event_occurred = True

        # 1.99 sec have passed (<2), should auto update to on
        mocked_factory.set_ticks(3.49)
        mock_track_time_interval.tick()

        assert gpio.ha_state_update_scheduled is True


@pytest.mark.asyncio
async def test__GpioBinarySensor_will_close_pin(mocked_factory):
    number = get_next_pin()
    pin = mocked_factory.pin(number)
    gpio = GpioBinarySensor(__create_config(port=number))
    await gpio.async_will_remove_from_hass()
    assert gpio._io is None
    assert pin.closed is True
