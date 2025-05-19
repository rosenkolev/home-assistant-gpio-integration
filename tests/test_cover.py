import pytest
from homeassistant.const import CONF_MODE, CONF_PORT

from custom_components.gpio_integration.controllers.cover import Roller
from custom_components.gpio_integration.cover import GpioBasicCover, GpioCover
from custom_components.gpio_integration.schemas import (
    CONF_INVERT_LOGIC,
    CONF_NAME,
    CONF_PIN_CLOSED_SENSOR,
    CONF_RELAY_CLOSE_INVERT,
    CONF_RELAY_CLOSE_PIN,
    CONF_RELAY_OPEN_INVERT,
    CONF_RELAY_OPEN_PIN,
    CONF_RELAY_TIME,
)
from custom_components.gpio_integration.schemas.cover import (
    RollerConfig,
    ToggleRollerConfig,
)
from tests.test__mocks import get_next_pin


def __create_config(port=None, invert_logic=False, closed_sensor=0, relay_time=0.6):
    return ToggleRollerConfig(
        {
            CONF_NAME: "Test Name",
            CONF_PORT: port,
            CONF_MODE: "Blind",
            CONF_INVERT_LOGIC: invert_logic,
            CONF_RELAY_TIME: relay_time,
            CONF_PIN_CLOSED_SENSOR: closed_sensor,
        }
    )


def _create_roller_config(
    open_port: int,
    close_port: int,
    sensor_port=0,
    open_invert_logic=False,
    close_invert_logic=False,
    relay_time=10,
):
    return RollerConfig(
        {
            CONF_NAME: "Test Name",
            CONF_MODE: "Blind",
            CONF_RELAY_OPEN_PIN: open_port,
            CONF_RELAY_OPEN_INVERT: open_invert_logic,
            CONF_RELAY_CLOSE_PIN: close_port,
            CONF_RELAY_CLOSE_INVERT: close_invert_logic,
            CONF_RELAY_TIME: relay_time,
            CONF_PIN_CLOSED_SENSOR: sensor_port,
        }
    )


def test__BasicCover_should_init_with_sensor(mocked_factory):
    pin_number = get_next_pin()
    pin_sensor_number = get_next_pin()
    pin_sensor = mocked_factory.pin(pin_sensor_number)
    pin_sensor._state = False
    pin_sensor.clear_states()
    with GpioBasicCover(
        __create_config(pin_number, closed_sensor=pin_sensor_number)
    ) as gpio:
        assert gpio.is_closed is False
        assert pin_sensor._function == "input"


def test__BasicCover_should_init_no_sensor(mocked_factory):
    pin_number = get_next_pin()
    pin = mocked_factory.pin(pin_number)
    with GpioBasicCover(__create_config(pin_number, closed_sensor=0)) as gpio:
        assert gpio.is_closed is True
        assert pin._function == "output"
        assert pin.state is False


def test__BasicCover_should_open(mocked_factory):
    number = get_next_pin()
    pin = mocked_factory.pin(number)
    with GpioBasicCover(__create_config(number, relay_time=0.6)) as gpio:
        gpio._closed = False
        gpio.open_cover()
        pin.assert_states([])

        pin._state = False
        pin.clear_states()

        gpio._closed = True
        gpio.open_cover()
        pin.assert_states_and_times([(0, False), (0, True), (0.6, False)])


@pytest.mark.asyncio
async def test__BasicCover_will_close_pin(mocked_factory):
    number = get_next_pin()
    pin = mocked_factory.pin(number)
    gpio = GpioBasicCover(__create_config(number))
    await gpio.async_will_remove_from_hass()
    assert pin.closed is True
    assert gpio._io is None


def test__Cover_should_init_with_sensor(mocked_factory):
    pin_up_port = get_next_pin()
    pin_down_port = get_next_pin()
    sensor_port = get_next_pin()

    pin_up = mocked_factory.pin(pin_up_port)
    pin_down = mocked_factory.pin(pin_down_port)
    sensor = mocked_factory.pin(sensor_port)
    sensor._state = False

    roller = Roller(_create_roller_config(pin_up_port, pin_down_port, sensor_port))
    with GpioCover(roller) as gpio:
        assert gpio.is_closed is False
        assert sensor._function == "input"
        assert pin_up._function == "output"
        assert pin_down._function == "output"


def test__Cover_should_init_no_sensor(mocked_factory):
    pin_up_port = get_next_pin()
    pin_down_port = get_next_pin()

    pin_up = mocked_factory.pin(pin_up_port)
    pin_down = mocked_factory.pin(pin_down_port)

    roller = Roller(_create_roller_config(pin_up_port, pin_down_port))
    with GpioCover(roller) as gpio:
        assert gpio.is_closed is True
        assert pin_up._function == "output"
        assert pin_down._function == "output"


@pytest.mark.skip(reason="too slow, it waits for 5 seconds")
def test__Cover_should_set_position(mocked_factory):
    pin_up_port = get_next_pin()
    pin_down_port = get_next_pin()

    pin_down = mocked_factory.pin(pin_down_port)

    roller = Roller(_create_roller_config(pin_up_port, pin_down_port))
    with GpioCover(roller) as gpio:
        gpio.set_cover_position(**{"A_POSITION": 50})

        pin_down.assert_states_and_times([(0, False), (0, True), (5, False)])


@pytest.mark.skip(reason="too slow, it waits for 5 seconds")
def test__Cover_should_open(mocked_factory):
    pin_up_port = get_next_pin()
    pin_down_port = get_next_pin()

    pin_down = mocked_factory.pin(pin_down_port)

    roller = Roller(_create_roller_config(pin_up_port, pin_down_port))
    with GpioCover(roller) as gpio:
        gpio.open_cover()

        pin_down.assert_states_and_times([(0, False), (0, True), (10, False)])
