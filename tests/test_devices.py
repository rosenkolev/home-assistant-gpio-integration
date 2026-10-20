# cspell:ignore caplog
import pytest

from custom_components.gpio_integration._devices import (
    DHT22,
    DHT22Data,
    dht22_bits,
    dht22_decode,
)
from tests.mocked_utils import get_next_pin

# humidity 65.2%, temperature 35.1C
BITS = "00000010 10001100 00000001 01011111 11101110"


def intervals(bits: str, zero=80.0, one=127.0) -> list[float]:
    """Periods (us) between the rising edges of a DHT22 transfer."""
    result = [110.0, 130.0]  # release -> response end -> bit 1
    for bit in bits.replace(" ", ""):
        result.append(one if bit == "1" else zero)
    return result


def merge(values: list[float], index: int) -> list[float]:
    """Simulate a missed rising edge: period `index` and `index + 1` merge."""
    return values[:index] + [values[index] + values[index + 1]] + values[index + 2 :]


def bits_of(value: str) -> list[int]:
    return [int(x) for x in value.replace(" ", "")]


def test__dht22_decode():
    assert dht22_decode(intervals(BITS)) == (652, 351, 0b11101110)


def test__dht22_decode_without_response_edges():
    """Missing response edges at the start don't matter (aligned to the end)."""
    assert dht22_decode(intervals(BITS)[2:]) == (652, 351, 0b11101110)


def test__dht22_decode_with_timing_jitter():
    values = intervals(BITS, zero=95.0, one=112.0)
    assert dht22_decode(values) == (652, 351, 0b11101110)


@pytest.mark.parametrize("index", range(2, 41))
def test__dht22_bits_repair_one_missed_edge(index):
    values = merge(intervals(BITS), index)
    bits, repairs = dht22_bits(values)
    assert bits == bits_of(BITS)
    assert repairs == 1


def test__dht22_bits_repair_two_missed_edges():
    values = merge(merge(intervals(BITS), 30), 10)
    bits, repairs = dht22_bits(values)
    assert bits == bits_of(BITS)
    assert repairs == 2


def test__dht22_decode_too_few_edges():
    with pytest.raises(ValueError, match="edges received"):
        dht22_decode(intervals(BITS)[-30:])


def test__dht22_decode_garbage_period():
    values = intervals(BITS)
    values[20] = 400.0
    with pytest.raises(ValueError, match="valid check sum"):
        dht22_decode(values)


def test__dht22_decode_invalid_checksum():
    values = intervals("00000010 10001100 00000001 01011111 11101111")
    with pytest.raises(ValueError, match="valid check sum"):
        dht22_decode(values)


def test__dht22_decode_negative_temperature():
    humidity, temperature, _ = dht22_decode(
        intervals("00000010 10001100 10000000 10010011 10100001")
    )
    assert humidity == 652
    assert temperature == 0x8093


def send(dht: DHT22, pin, values: list[float]):
    """Send rising edges separated by the given periods."""
    ticks = 10.0
    pin._last_change = ticks
    pin._call_when_changed()
    for value in values:
        ticks += value / 1_000_000
        pin._last_change = ticks
        pin._call_when_changed()


def test__DHT22_start_signal(mocked_factory, mock_sleep_sec):
    number = get_next_pin()
    pin = mocked_factory.pin(number)
    dht = DHT22(number)
    try:
        driven = []
        pin.output_with_state = lambda state: driven.append(state)
        dht._start()
        assert driven == [False]  # pulled LOW
        assert mock_sleep_sec == [0.018]
        assert pin.function == "input"  # released
        assert pin.when_changed == dht._pin_changed
        assert pin.edges == "rising"
    finally:
        dht.close()


class Listener:
    def __init__(self, dht: DHT22):
        self.data = []
        self.invalid = 0
        dht.on_data_received = self.on_data
        dht.on_invalid_data = self.on_invalid

    def on_data(self, data):
        self.data.append(data)

    def on_invalid(self):
        self.invalid += 1


def test__DHT22_read_data(mocked_factory, mock_sleep_sec):
    number = get_next_pin()
    pin = mocked_factory.pin(number)
    dht = DHT22(number)
    listener = Listener(dht)

    dht._start()
    send(dht, pin, intervals(BITS))
    data = dht._finish()

    assert data == DHT22Data(35.1, 65.2)
    assert listener.data == [data]
    assert listener.invalid == 0
    assert pin.when_changed is None
    dht.close()


def test__DHT22_read_invalid(mocked_factory, mock_sleep_sec, caplog):
    number = get_next_pin()
    pin = mocked_factory.pin(number)
    dht = DHT22(number)
    listener = Listener(dht)

    for attempt in range(3):
        dht._start()
        send(dht, pin, intervals(BITS)[:10])
        assert dht._finish() is None

    assert listener.invalid == 3
    assert listener.data == []
    assert "3 failed reads" in caplog.text
    dht.close()


def test__DHT22_read_timeout(mocked_factory, mock_sleep_sec):
    number = get_next_pin()
    dht = DHT22(number)
    dht.TRANSFER_TIMEOUT_SEC = 0.001
    listener = Listener(dht)
    assert dht.read() is None
    assert listener.invalid == 1
    dht.close()


def test__DHT22_closed_device_dont_read(mocked_factory, mock_sleep_sec):
    number = get_next_pin()
    dht = DHT22(number)
    dht.close()
    assert dht.read() is None


def test__low_latency_holds_value(tmp_path):
    import struct

    from custom_components.gpio_integration.core import low_latency

    path = tmp_path / "cpu_dma_latency"
    path.write_bytes(b"")
    with low_latency(str(path)) as active:
        assert active is True
        assert path.read_bytes() == struct.pack("i", 0)


def test__low_latency_without_permission(tmp_path):
    from custom_components.gpio_integration.core import low_latency

    with low_latency(str(tmp_path / "missing" / "cpu_dma_latency")) as active:
        assert active is False
