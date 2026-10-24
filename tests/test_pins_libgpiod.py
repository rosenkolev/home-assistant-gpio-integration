# cspell:ignore gpiod, libgpiod, gpiochip, gpiochips, lgpio, rpigpio
import os
from time import monotonic, sleep

import pytest
from custom_components.gpio_integration._vendor.gpiozero import Device
from custom_components.gpio_integration._vendor.gpiozero.exc import (
    PinFixedPull,
    PinInvalidEdges,
    PinInvalidFunction,
    PinInvalidPin,
    PinInvalidPull,
    PinInvalidState,
    PinPWMFixedValue,
    PinSetInput,
    PinSPIUnsupported,
)

import custom_components.gpio_integration._pin_factory as pin_factory
from custom_components.gpio_integration.pins.libgpiod import (
    GpiodFactory,
    GpiodPin,
    find_gpiochips,
    pin_names,
)
from tests import mocked_gpiod
from tests.mocked_gpiod import Bias, Direction, Edge, Value

CHIPS = ["/dev/gpiochip0", "/dev/gpiochip4", "/dev/gpiochip5"]


def wait_until(condition, timeout=2.0) -> bool:
    end = monotonic() + timeout
    while monotonic() < end:
        if condition():
            return True
        sleep(0.005)
    return condition()


@pytest.fixture
def factory():
    f = GpiodFactory(chips=CHIPS)
    try:
        yield f
    finally:
        f.close()


def test__pin_names():
    name, names = pin_names(4, 11, "gpiochip4", "PIN_3")
    assert name == "GPIO139"
    assert names == {139, "139", "GPIO139", "GPIO4_B3", "gpiochip4:11", "PIN_3"}

    name, names = pin_names(0, 40, "gpiochip0", "")
    assert name == "GPIO40"
    assert names == {40, "40", "GPIO40", "gpiochip0:40"}


def test__find_gpiochips_sorted(monkeypatch):
    monkeypatch.setattr(
        os, "listdir", lambda path: ["gpiochip4", "tty0", "gpiochip0", "gpiochip5"]
    )
    assert find_gpiochips() == ["/dev/gpiochip0", "/dev/gpiochip4", "/dev/gpiochip5"]


def test__find_gpiochips_missing_dir(monkeypatch):
    def fail(path):
        raise OSError("missing")

    monkeypatch.setattr(os, "listdir", fail)
    assert find_gpiochips() == []


def test__factory_requires_chips():
    with pytest.raises(RuntimeError):
        GpiodFactory(chips=[])


def test__factory_board_info(factory: GpiodFactory):
    info = factory.board_info
    assert set(info.headers.keys()) == {"gpiochip0", "gpiochip4", "gpiochip5"}
    assert len(info.headers["gpiochip4"].pins) == 32
    assert len(info.headers["gpiochip5"].pins) == 3
    assert factory.board_info is info


def test__factory_pin_numbering(factory: GpiodFactory):
    pin = factory.pin(139)
    assert isinstance(pin, GpiodPin)
    assert pin.offset == 11
    assert repr(pin) == "GPIO139 (gpiochip4:11)"
    assert factory.pin("GPIO4_B3") is pin
    assert factory.pin("PIN_3") is pin
    assert factory.pin("gpiochip4:11") is pin
    assert factory.pin("139") is pin

    pin0 = factory.pin(13)
    assert pin0.offset == 13
    assert factory.pin("PIN_8") is pin0
    assert factory.pin(162).offset == 2  # gpiochip5 line 2

    with pytest.raises(PinInvalidPin):
        factory.pin(999)
    with pytest.raises(PinInvalidPin):
        factory.pin("GPIO5_A3")


def test__factory_spi_unsupported(factory: GpiodFactory):
    with pytest.raises(PinSPIUnsupported):
        factory.spi(port=0, device=0)


def test__factory_ticks(factory: GpiodFactory):
    assert factory.ticks_diff(2.5, 1.0) == 1.5
    assert factory.ticks() > 0


def test__factory_close_releases(factory: GpiodFactory):
    pin = factory.pin(139)
    request = pin.request
    factory.close()
    assert request.released is True
    assert pin.request is None
    assert all(chip.closed for chip in factory.chips) or factory.chips == []


def test__pin_initial_state(factory: GpiodFactory):
    pin = factory.pin(139)
    assert pin.function == "input"
    assert pin.pull == "floating"
    assert pin.frequency is None
    assert pin.bounce is None
    assert pin.edges == "both"
    assert pin.when_changed is None
    assert pin.request.consumer == "home-assistant"
    assert pin.request.last.direction == Direction.INPUT


def test__pin_output_with_state(factory: GpiodFactory):
    pin = factory.pin(139)
    pin.output_with_state(True)
    assert pin.function == "output"
    assert pin.request.last.direction == Direction.OUTPUT
    assert pin.request.last.output_value == Value.ACTIVE
    assert pin.state is True

    pin.state = False
    assert pin.state is False
    assert pin.request.writes == [Value.INACTIVE]

    pin.state = 1
    assert pin.state is True


def test__pin_set_function(factory: GpiodFactory):
    pin = factory.pin(139)
    pin.function = "output"
    assert pin.request.last.direction == Direction.OUTPUT
    assert pin.request.last.output_value == Value.INACTIVE

    pin.function = "input"
    assert pin.request.last.direction == Direction.INPUT

    with pytest.raises(PinInvalidFunction):
        pin.function = "pwm"


def test__pin_input_with_pull(factory: GpiodFactory):
    pin = factory.pin(139)
    pin.input_with_pull("up")
    assert pin.function == "input"
    assert pin.pull == "up"
    assert pin.request.last.bias == Bias.PULL_UP

    pin.pull = "down"
    assert pin.request.last.bias == Bias.PULL_DOWN

    pin.pull = "floating"
    assert pin.request.last.bias == Bias.DISABLED

    with pytest.raises(PinInvalidPull):
        pin.pull = "sideways"

    with pytest.raises(PinSetInput):
        pin.state = True

    pin.function = "output"
    with pytest.raises(PinFixedPull):
        pin.pull = "up"


def test__pin_when_changed(factory: GpiodFactory):
    pin = factory.pin(139)
    calls = []

    def on_change(ticks, state):
        calls.append((ticks, state))

    pin.function = "input"
    pin.edges = "rising"
    pin.bounce = 0.005
    pin.when_changed = on_change

    assert pin.edges == "rising"
    assert pin.bounce == 0.005
    assert pin.when_changed is on_change
    assert pin.request.last.edge_detection == Edge.RISING
    assert pin.request.last.debounce_period.total_seconds() == 0.005

    pin.request.push_event(11, rising=True, timestamp_ns=2_000_000_000)
    assert wait_until(lambda: len(calls) == 1)
    assert calls == [(2.0, 1)]

    pin.request.push_event(11, rising=False, timestamp_ns=2_500_000_000)
    assert wait_until(lambda: len(calls) == 2)
    assert calls[1] == (2.5, 0)

    watcher = pin._watcher
    pin.when_changed = None
    assert pin.when_changed is None
    assert pin.request.last.edge_detection == Edge.NONE
    assert wait_until(lambda: not watcher.is_alive())


def test__pin_edges_change_while_enabled(factory: GpiodFactory):
    pin = factory.pin(139)
    calls = []

    def on_change(ticks, state):
        calls.append(state)

    pin.function = "input"
    pin.when_changed = on_change
    assert pin.request.last.edge_detection == Edge.BOTH

    pin.edges = "falling"
    assert pin.request.last.edge_detection == Edge.FALLING
    assert pin.when_changed is on_change

    pin.bounce = 0.001
    assert pin.request.last.debounce_period.total_seconds() == 0.001

    with pytest.raises(PinInvalidEdges):
        pin.edges = "diagonal"

    with pytest.raises(ValueError):
        pin.bounce = -1

    pin.when_changed = None


def test__pin_when_changed_cleared_from_callback(factory: GpiodFactory):
    """DHT22 pattern: the callback stops the edge detection."""
    pin = factory.pin(139)
    calls = []

    def on_change(ticks, state):
        calls.append(state)
        pin.when_changed = None

    pin.function = "input"
    pin.when_changed = on_change
    watcher = pin._watcher

    pin.request.push_event(11, rising=True, timestamp_ns=1)
    assert wait_until(lambda: len(calls) == 1)
    assert pin.when_changed is None
    assert wait_until(lambda: not watcher.is_alive())


def test__pin_when_changed_switches_output_to_input(factory: GpiodFactory):
    """Like lgpio: one atomic reconfigure to input + edge detection."""
    pin = factory.pin(139)
    pin.output_with_state(False)
    configs = len(pin.request.history)

    def on_change(ticks, state):
        pass

    pin.when_changed = on_change
    assert pin.function == "input"
    assert len(pin.request.history) == configs + 1
    assert pin.request.last.direction == Direction.INPUT
    assert pin.request.last.edge_detection == Edge.BOTH
    pin.when_changed = None


def test__pin_function_change_stops_edge_detection(factory: GpiodFactory):
    pin = factory.pin(139)

    def on_change(ticks, state):
        pass

    pin.function = "input"
    pin.when_changed = on_change
    watcher = pin._watcher

    pin.function = "output"
    assert wait_until(lambda: not watcher.is_alive())
    assert pin._watcher is None


def test__pin_pwm(factory: GpiodFactory):
    pin = factory.pin(139)

    with pytest.raises(PinPWMFixedValue):
        pin.frequency = 100

    pin.function = "output"
    pin.frequency = 1000
    assert pin.frequency == 1000
    assert pin.state == 0

    pin.state = 0.5
    assert pin.state == 0.5
    assert wait_until(
        lambda: Value.ACTIVE in pin.request.writes
        and Value.INACTIVE in pin.request.writes
    )

    pin.frequency = 500
    assert pin.frequency == 500
    assert pin.state == 0.5

    with pytest.raises(PinInvalidState):
        pin.state = 1.5

    pwm = pin._pwm
    pin.state = 1
    pin.frequency = None
    assert pin.frequency is None
    assert wait_until(lambda: not pwm.is_alive())
    assert pin.request.values[11] == Value.ACTIVE
    assert pin.state is True

    pin.frequency = 100
    pin.frequency = 0
    assert pin.frequency is None
    assert pin.state is False


def test__pin_close_resets_and_releases(factory: GpiodFactory):
    pin = factory.pin(139)
    request = pin.request
    pin.input_with_pull("up")
    pin.when_changed = lambda ticks, state: None
    pin.close()

    assert pin.function == "input"
    assert pin.pull == "floating"
    assert pin.when_changed is None
    assert request.last.bias == Bias.AS_IS
    assert request.last.edge_detection == Edge.NONE
    assert request.released is True
    assert pin.request is None


def test__pin_close_allows_new_request(factory: GpiodFactory):
    """Reloading a Home Assistant entry closes and requests the pin again."""
    pin = factory.pin(139)
    pin.close()

    again = factory.pin(139)
    assert again is not pin
    assert again.request.released is False


def test__pin_factory_created_once_in_parallel(monkeypatch):
    import threading

    created = []
    barrier = threading.Barrier(4)

    def create():
        created.append(object())
        return created[-1]

    monkeypatch.setattr(pin_factory, "_create_default_pin_factory", create)
    monkeypatch.setattr(Device, "pin_factory", None)
    results = []

    def worker():
        barrier.wait()
        results.append(pin_factory.get_pin_factory())

    threads = [threading.Thread(target=worker) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(created) == 1
    assert all(r is created[0] for r in results)


def test__devices_with_gpiod_factory():
    from custom_components.gpio_integration._devices import BinarySensor, Switch

    saved_factory = Device.pin_factory
    factory = GpiodFactory(chips=CHIPS)
    Device.pin_factory = factory
    try:
        switch = Switch(139)
        switch.on()
        assert factory.pin(139).state is True
        switch.close()

        sensor = BinarySensor(13, active_high=False)
        assert factory.pin(13).pull == "up"
        sensor.close()
    finally:
        Device.pin_factory = saved_factory
        factory.close()


def test__pin_factory_gpiod_registered():
    assert pin_factory.PIN_FACTORIES["gpiod"] == ".pins.libgpiod:GpiodFactory"
    assert pin_factory._get_pin_factory_class_by_name("gpiod") is GpiodFactory


def test__pin_factory_order(monkeypatch):
    monkeypatch.setattr(pin_factory, "is_raspberry_pi", lambda: True)
    assert pin_factory._get_pin_factory_names() == list(pin_factory.PIN_FACTORIES)

    monkeypatch.setattr(pin_factory, "is_raspberry_pi", lambda: None)
    assert pin_factory._get_pin_factory_names() == list(pin_factory.PIN_FACTORIES)

    monkeypatch.setattr(pin_factory, "is_raspberry_pi", lambda: False)
    names = pin_factory._get_pin_factory_names()
    assert names[0] == "gpiod"
    assert names[1:] == ["pigpio", "lgpio", "rpigpio", "native"]


def test__is_raspberry_pi(monkeypatch, tmp_path):
    model = tmp_path / "model"
    monkeypatch.setattr(pin_factory, "DEVICE_TREE_MODEL", str(model))
    assert pin_factory.is_raspberry_pi() is None

    model.write_bytes(b"Raspberry Pi 4 Model B Rev 1.4\x00")
    assert pin_factory.is_raspberry_pi() is True

    model.write_bytes(b"Radxa ROCK 5B+\x00")
    assert pin_factory.is_raspberry_pi() is False


def test__mocked_gpiod_chip_rejects_unknown_path():
    with pytest.raises(OSError):
        mocked_gpiod.Chip("/dev/gpiochip9")
