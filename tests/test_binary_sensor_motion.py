from unittest.mock import Mock, patch

import mocked_models as mocked

from custom_components.gpio_integration.config_schema import (
    CONF_BOUNCE_TIME,
    CONF_DEFAULT_STATE,
    CONF_EDGE_EVENT_TIMEOUT,
    CONF_INVERT_LOGIC,
    CONF_MODE,
    CONF_NAME,
    CONF_PORT,
    CONF_PULL_MODE,
    SensorConfig,
)


def __create_config(port=None, default_state=False, invert_logic=False, timeout=10):
    return SensorConfig(
        {
            CONF_NAME: "Test Name",
            CONF_PORT: mocked.get_next_pin() if port is None else port,
            CONF_PULL_MODE: "up",
            CONF_MODE: "read",
            CONF_BOUNCE_TIME: 5,
            CONF_EDGE_EVENT_TIMEOUT: timeout,
            CONF_DEFAULT_STATE: default_state,
            CONF_INVERT_LOGIC: invert_logic,
        }
    )


@patch(
    "homeassistant.components.binary_sensor.BinarySensorEntity", mocked.MockedBaseEntity
)
def test__GpioMotionBinarySensor_should_init_default_sate():
    import custom_components.gpio_integration.binary_sensor as base

    with patch.object(base, "create_pin", Mock()):
        gpio = base.GpioMotionBinarySensor(__create_config())

        assert gpio.is_on is False
        assert gpio.last_motion_event_timeout is False


@patch(
    "homeassistant.components.binary_sensor.BinarySensorEntity", mocked.MockedBaseEntity
)
def test__GpioMotionBinarySensor_edge_events_should_update_state():
    import custom_components.gpio_integration.binary_sensor as base

    proxy = mocked.MockedCreatePin()
    with patch.object(base, "create_pin", proxy.mock):
        gpio = base.GpioMotionBinarySensor(__create_config())

        assert gpio.is_on is False

        proxy.pin._call_when_changed(0)
        assert gpio.is_on is True
        assert gpio.ha_state_write is True


@patch("time.perf_counter")
@patch(
    "homeassistant.components.binary_sensor.BinarySensorEntity", mocked.MockedBaseEntity
)
def test__GpioMotionBinarySensor_should_update_not_update(counter: Mock):
    import custom_components.gpio_integration.binary_sensor as base

    proxy = mocked.MockedCreatePin()
    with patch.object(base, "create_pin", proxy.mock):
        counter.return_value = 0
        gpio = base.GpioMotionBinarySensor(__create_config())

        counter.return_value = 1
        gpio.update()
        assert gpio.ha_state_write is False
        assert gpio._state is False

        counter.return_value = 20
        gpio.update()
        assert gpio._state is False
        assert gpio.ha_state_write is False

        gpio.__event_time = 0
        gpio.update()
        assert gpio._state is False
        assert gpio.ha_state_write is False


@patch("time.perf_counter")
@patch(
    "homeassistant.components.binary_sensor.BinarySensorEntity", mocked.MockedBaseEntity
)
def test__GpioMotionBinarySensor_should_update_state_after_elapsed(counter: Mock):
    import custom_components.gpio_integration.binary_sensor as base

    proxy = mocked.MockedCreatePin()
    with patch.object(base, "create_pin", proxy.mock):
        counter.return_value = 1.0

        gpio = base.GpioMotionBinarySensor(__create_config(None, timeout=5))
        proxy.pin._call_when_changed(0)

        counter.return_value = 6.01

        gpio.update()
        assert gpio.ha_state_write is True
        assert gpio._state is False
