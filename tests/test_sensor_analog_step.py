import pytest

from custom_components.gpio_integration.hub import Hub
from custom_components.gpio_integration.schemas.main import EntityTypes
from custom_components.gpio_integration.schemas.sensor import (
    CONF_CHANNEL,
    CONF_CHIP,
    CONF_MIN_VALUE,
    CONF_MIN_VOLTAGE,
    CONF_NAME,
    CONF_NATIVE_UNIT,
    CONF_STEP_VALUE,
    CONF_STEP_VOLTAGE,
)
from custom_components.gpio_integration.sensor import GpioSensor


def _create_config(
    chip="MCP3001",
    channel=0,
    min_voltage=0.5,
    min_value=10,
    step_voltage=0.01,
    step_value=0.5,
    native_unit="C",
):
    return {
        "type": EntityTypes.SENSOR_ANALOG_STEP.value,
        CONF_NAME: "Test Name",
        CONF_CHIP: chip,
        CONF_CHANNEL: channel,
        CONF_MIN_VOLTAGE: min_voltage,
        CONF_MIN_VALUE: min_value,
        CONF_STEP_VOLTAGE: step_voltage,
        CONF_STEP_VALUE: step_value,
        CONF_NATIVE_UNIT: native_unit,
    }


def test__Sensor_AnalogStep_should_init(mock_MCP_chips):
    hub = Hub(_create_config())
    assert len(hub.sensors) == 1
    with GpioSensor(hub.sensors[0]) as sensor:
        assert sensor.name == "Test Name"
        assert sensor.unique_id == "test_name"
        assert sensor.native_value == 10
        assert sensor._attr_native_unit_of_measurement == "C"


def test__Sensor_AnalogStep_should_read(mock_MCP_chips):
    hub = Hub(_create_config(channel=0))
    device = mock_MCP_chips(0)
    with GpioSensor(hub.sensors[0]) as sensor:
        device._value = 0.61 / 3.3
        assert sensor.native_value == 15.5


def test__Sensor_AnalogStep_should_read2(mock_MCP_chips):
    hub = Hub(
        _create_config(
            channel=0, min_voltage=0.3, min_value=-10, step_voltage=0.05, step_value=1
        )
    )
    device = mock_MCP_chips(0)
    with GpioSensor(hub.sensors[0]) as sensor:
        device._value = 2.3 / 3.3
        assert round(sensor.native_value, 2) == 30


def test__Sensor_AnalogStep_should_read_below_min_voltage(mock_MCP_chips):
    hub = Hub(_create_config(channel=0))
    device = mock_MCP_chips(0)
    with GpioSensor(hub.sensors[0]) as sensor:
        device._value = 0.2 / 3.3  # Below min voltage
        assert sensor.native_value == 10


def test__Sensor_AnalogStep_should_not_be_device(mock_MCP_chips):
    hub = Hub(_create_config(channel=0))
    with GpioSensor(hub.sensors[0]) as sensor:
        assert sensor.device_info is None


@pytest.mark.asyncio
async def test__MCP_will_close_pin(mock_MCP_chips):
    hub = Hub(_create_config(channel=0))
    device = mock_MCP_chips(0)
    gpio = GpioSensor(hub.sensors[0])

    await gpio.async_will_remove_from_hass()

    assert gpio._io is None
    assert device._closed is True
