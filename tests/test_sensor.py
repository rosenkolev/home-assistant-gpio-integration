import pytest
from homeassistant.const import CONF_PORT

from custom_components.gpio_integration.controllers.sensor import DHT22Controller
from custom_components.gpio_integration.schemas import CONF_NAME
from custom_components.gpio_integration.schemas.sensor import DHT22Config
from custom_components.gpio_integration.sensor import GpioSensor
from tests.mocked_utils import get_next_pin


def _create_config(port):
    return DHT22Config(
        {
            CONF_NAME: "Test Name",
            CONF_PORT: port,
        }
    )


def test__DHT22_should_init_default_state(mocked_factory):
    port = get_next_pin()
    pin = mocked_factory.pin(port)
    config = _create_config(port)
    controller = DHT22Controller(config)
    sensors = controller.get_sensors()
    assert len(sensors) == 2
    with GpioSensor(sensors[0]) as gpio:
        controller.stop_auto_read_loop()

        assert gpio.native_value == 0.0
        assert gpio._attr_native_unit_of_measurement == "C"
        assert controller._humidity_id == "test_name_H"
        assert controller._temperature_id == "test_name_T"
        assert pin._function == "input"
        assert pin._state is False
        assert pin.edges == "both"


def _send_DHT22_data(dht, pin, bits: str):
    """Simulate a DHT22 transfer: start, rising edges, decode."""
    dht._start()
    periods = [0.000_11, 0.000_13]  # release, end of response LOW, bit 1
    for bit in bits.replace(" ", ""):
        periods.append(0.000_08 if bit == "0" else 0.000_127)

    ticks = 100.0
    pin._last_change = ticks
    pin._state = 1
    pin._call_when_changed()  # line released
    for period in periods:
        ticks += period
        pin._last_change = ticks
        pin._call_when_changed()

    return dht._finish()


def test__DHT22_should_retrieve(mocked_factory):
    port = get_next_pin()
    pin = mocked_factory.pin(port)
    controller = DHT22Controller(_create_config(port))
    sensors = controller.get_sensors()
    with GpioSensor(sensors[0]) as temperature:
        with GpioSensor(sensors[1]) as humidity:
            controller.stop_auto_read_loop()

            _send_DHT22_data(
                controller._io,
                pin,
                "00000010 10001100 00000001 01011111 11101110",
            )

            assert temperature.native_value == 35.1
            assert humidity.native_value == 65.2


def test__DHT22_should_retrieve_negative_temp(mocked_factory):
    port = get_next_pin()
    pin = mocked_factory.pin(port)
    controller = DHT22Controller(_create_config(port))
    sensors = controller.get_sensors()
    with GpioSensor(sensors[0]) as temperature:
        controller.stop_auto_read_loop()

        _send_DHT22_data(
            controller._io,
            pin,
            "00000010 10001100 10000000 10010011 10100001",
        )

        assert temperature.native_value == -14.7


@pytest.mark.asyncio
async def test__DHT22_will_close_pin(mocked_factory):
    number = get_next_pin()
    pin = mocked_factory.pin(number)
    sensors = DHT22Controller(_create_config(number)).get_sensors()
    gpio = GpioSensor(sensors[0])
    await gpio.async_will_remove_from_hass()
    assert pin.closed is True
    assert gpio._io is None
