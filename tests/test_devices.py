from custom_components.gpio_integration._devices import DHT22, BitInfo
from tests.mocked_utils import get_next_pin


def test__DHT22_start_signal(mocked_factory, mock_sleep_sec):
    number = get_next_pin()
    pin = mocked_factory.pin(number)
    hub = DHT22(number)
    try:
        hub.read()
        pin.assert_states([0, 1, 0])
        assert mock_sleep_sec == [0.018]
    finally:
        hub.close()


def test__DHT22_transfer_started(mocked_factory, mock_sleep_sec):
    mocked_factory.set_ticks(0.01)  # initial tick at 10ms
    number = get_next_pin()
    pin = mocked_factory.pin(number)

    hub = DHT22(number)
    hub.read()

    pin.when_changed(0.010_08, 0)  # 80us
    pin.when_changed(0.010_16, 1)  # 80us

    assert hub._transfer is True


class DHT22Tester:
    def __init__(self):
        number = get_next_pin()
        self.called = False
        self.hub = DHT22(number)
        self.hub.on_invalid_data = self.caller

    def caller(self):
        self.called = True


def test__DHT22_invalid_bits_stop(mocked_factory, mock_sleep_sec):
    tester = DHT22Tester()

    tester.hub._deque.append(BitInfo(1, 0.045))
    tester.hub._process()

    assert tester.called is True


def test__DHT22_closed_device_dont_read(mocked_factory, mock_sleep_sec):
    number = get_next_pin()
    hub = DHT22(number)

    hub.close()
    hub.read()
