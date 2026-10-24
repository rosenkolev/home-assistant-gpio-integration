# cspell:ignore leds, lgpio
from collections import namedtuple
from threading import Event
from typing import Callable, Literal
from weakref import WeakMethod

from ._vendor.gpiozero import (
    MCP3001,
    MCP3002,
    MCP3004,
    MCP3008,
    MCP3201,
    MCP3202,
    MCP3204,
    MCP3208,
    RGBLED,
    AngularServo,
    DigitalInputDevice,
    DigitalOutputDevice,
    PWMOutputDevice,
    event,
)
from ._vendor.gpiozero import (
    DistanceSensor as GZDistanceSensor,
)

from . import core
from ._pin_factory import get_pin_factory

_LOGGER = core.get_logger()


class AsStringMixin:
    def __repr__(self):
        return f"{self.pin!r} ({self.__class__.__name__})"


class Pwm(AsStringMixin, PWMOutputDevice):
    def __init__(self, pin: int, frequency=100, active_high=True, initial_value=False):
        super().__init__(
            pin,
            pin_factory=get_pin_factory(),
            active_high=active_high,
            frequency=frequency,
            initial_value=1 if initial_value else 0,
        )


class PwmFromPercent(Pwm):
    def _percent_to_value(self, percent: int) -> float:
        return percent / 100.0

    @property
    def percentage(self) -> int:
        return int(self.value * 100)

    @percentage.setter
    def percentage(self, percent: int):
        if percent < 0 or percent > 100:
            raise ValueError("percentage must be between 0 and 100")

        self.value = self._percent_to_value(percent)


class Switch(AsStringMixin, DigitalOutputDevice):
    def __init__(self, pin: int, active_high=True, initial_value=False):
        super().__init__(
            pin,
            pin_factory=get_pin_factory(),
            active_high=active_high,
            initial_value=initial_value,
        )


class BinarySensor(AsStringMixin, DigitalInputDevice):
    def __init__(self, pin: int, active_high=True, bounce_time=None):
        super().__init__(
            pin,
            pin_factory=get_pin_factory(),
            pull_up=not active_high,
            active_state=None,
            bounce_time=bounce_time,
        )

    on_state_changed: Callable[[DigitalInputDevice], None] = event(
        """
        Event that is fired when the state of the sensor changes.
        The callback should accept a single argument: the new state.
        """
    )

    def _pin_changed(self, ticks, state):
        super()._pin_changed(ticks, state)
        if self.on_state_changed:
            self.on_state_changed()

    @property
    def any_event_time_sec(self) -> float | None:
        active_time = self.active_time
        return active_time if active_time is not None else self.inactive_time


class DistanceSensor(AsStringMixin, GZDistanceSensor):
    def __init__(self, echo: int, trigger: int, max_distance: float | int):
        super().__init__(
            echo,
            trigger,
            max_distance=max_distance,
            partial=True,  # prevent timeouts
            pin_factory=get_pin_factory(),
        )


class Servo(AsStringMixin, AngularServo):
    def __init__(
        self,
        pin: int,
        initial_angle=0.0,
        min_angle=-90,
        max_angle=90,
        min_pulse_width_ms=1,
        max_pulse_width_ms=2,
        frame_width_ms=20,
    ):
        self.pin = pin
        super().__init__(
            pin,
            pin_factory=get_pin_factory(),
            initial_angle=initial_angle,
            min_angle=min_angle,
            max_angle=max_angle,
            min_pulse_width=min_pulse_width_ms / 1000.0,
            max_pulse_width=max_pulse_width_ms / 1000.0,
            frame_width=frame_width_ms / 1000.0,
        )


class RgbLight(RGBLED):
    def __init__(
        self,
        red: int,
        green: int,
        blue: int,
        active_high=True,
        frequency=100,
        initial_value=(0, 0, 0),
    ):
        super().__init__(
            red,
            green,
            blue,
            pin_factory=get_pin_factory(),
            active_high=active_high,
            initial_value=initial_value,
            pwm=frequency > 0,
        )
        # When RGB light is PWM and the frequency is not the default 100Hz
        if frequency > 0 and frequency != 100:
            for x in self._leds:
                x.frequency = frequency

    def __repr__(self):
        return f"{self.red!r}, {self.green!r}, {self.blue!r}"


MCP_CLASS_MAP = {
    "MCP3001": MCP3001,
    "MCP3002": MCP3002,
    "MCP3004": MCP3004,
    "MCP3008": MCP3008,
    "MCP3201": MCP3201,
    "MCP3202": MCP3202,
    "MCP3204": MCP3204,
    "MCP3208": MCP3208,
}

MCP_NAMES = list(MCP_CLASS_MAP.keys())


def create_analog_device(
    model: Literal[
        "MCP3001",
        "MCP3002",
        "MCP3004",
        "MCP3008",
        "MCP3201",
        "MCP3202",
        "MCP3204",
        "MCP3208",
    ],
    channel: int = 0,
):
    if model not in MCP_NAMES:
        raise ValueError(f"Invalid model: {model}")

    if model == "MCP3001" or model == "MCP3201":
        return MCP_CLASS_MAP[model](pin_factory=get_pin_factory())

    return MCP_CLASS_MAP[model](channel=channel, pin_factory=get_pin_factory())


DHT22Data = namedtuple("DHT22Data", ["temperature", "humidity"])

DHT22_BIT_COUNT = 40
# Rising edges of a transfer: line release (not always seen), end of the 80us
# response LOW, start of the HIGH of every bit and the final line release.
DHT22_ALL_EDGES = DHT22_BIT_COUNT + 2
DHT22_ZERO_US = 80.0  # period of a "0": 50us LOW + 26-28us HIGH
DHT22_ONE_US = 127.0  # period of a "1": 50us LOW + 70us HIGH
DHT22_SPLIT_US = 103.0  # shorter period is "0", longer is "1"
DHT22_PERIOD_MIN_US = 55.0
DHT22_PERIOD_MAX_US = 160.0
DHT22_TOLERANCE_US = 22.0  # for periods of 2 bits (a missed rising edge)
DHT22_MAX_REPAIRS = 3
# (period, bits) of two bits merged by a missed rising edge
DHT22_MERGED = [
    (DHT22_ZERO_US * 2, [0, 0]),
    (DHT22_ZERO_US + DHT22_ONE_US, [0, 1]),
    (DHT22_ZERO_US + DHT22_ONE_US, [1, 0]),
    (DHT22_ONE_US * 2, [1, 1]),
]


def _search(periods_us, i, bits, repairs, budget):
    """Depth first search for 40 bits (collected from the end, reversed)."""
    if len(bits) >= DHT22_BIT_COUNT:
        if len(bits) == DHT22_BIT_COUNT:
            yield bits, repairs
        return
    if i < 0:
        return

    period = periods_us[i]
    if DHT22_PERIOD_MIN_US <= period <= DHT22_PERIOD_MAX_US:
        bit = 1 if period >= DHT22_SPLIT_US else 0
        yield from _search(periods_us, i - 1, bits + [bit], repairs, budget)

    if repairs < budget:
        for total, merged in DHT22_MERGED:
            if abs(period - total) <= DHT22_TOLERANCE_US:
                yield from _search(
                    periods_us, i - 1, bits + merged[::-1], repairs + 1, budget
                )


def _valid_check_sum(bits: list[int]) -> bool:
    value = 0
    for bit in bits:
        value = (value << 1) | bit
    data = value >> 8
    total = sum((data >> shift) & 0xFF for shift in (0, 8, 16, 24))
    return (total & 0xFF) == (value & 0xFF)


def dht22_bits(periods_us: list[float]) -> tuple[list[int], int]:
    """
    Decode the 40 data bits from the periods between RISING edges (in us).

    Every bit is a 50us LOW followed by a 26-28us ("0") or 70us ("1") HIGH,
    so the time between the rising edges is ~80us for "0" and ~127us for
    "1". Only rising edges are used because some GPIO drivers lose or mistime
    events when both edges come every 26us.

    The data is aligned to the end: the last rising edge is the line release
    after the final 50us LOW. A missed rising edge merges two bits into one
    period; decodings with 0, 1, 2 and 3 repairs are tried in order and the
    first one with a valid checksum is used.

    Returns (bits, number of repaired missed edges).
    """
    min_periods = DHT22_BIT_COUNT - DHT22_MAX_REPAIRS
    if len(periods_us) < min_periods:
        raise ValueError(
            f"{len(periods_us) + 1} edges received, "
            f"at least {min_periods + 1} expected"
        )

    last = len(periods_us) - 1
    for budget in range(DHT22_MAX_REPAIRS + 1):
        for bits, repairs in _search(periods_us, last, [], 0, budget):
            bits = bits[::-1]
            if repairs == budget and _valid_check_sum(bits):
                return bits, repairs

    raise ValueError(
        f"no decoding with a valid check sum ({len(periods_us) + 1} edges)"
    )


def dht22_decode(periods_us: list[float]) -> tuple[int, int, int]:
    """Decode (humidity, temperature, checksum) from the rising edge periods."""
    bits, repairs = dht22_bits(periods_us)
    value = 0
    for bit in bits:
        value = (value << 1) | bit

    if repairs:
        _LOGGER.debug(f"DHT22: {repairs} missed edge(s) repaired")

    return (value >> 24) & 0xFFFF, (value >> 8) & 0xFFFF, value & 0xFF


class DHT22(AsStringMixin):
    """
    DHT22 / AM2302 temperature and humidity sensor.

    The host pulls the line LOW for 18ms, releases it and records the edge
    rising edge timestamps the sensor sends back (~5ms). The bits are decoded after the
    transfer, not in the edge callback.
    """

    START_SIGNAL_SEC = 0.018
    TRANSFER_TIMEOUT_SEC = 0.05
    WARN_AFTER_FAILURES = 3

    def __init__(self, pin: int):
        self.pin_factory = get_pin_factory()
        self.pin = self.pin_factory.pin(pin)
        self._on_data_received = None
        self._on_invalid_data = None
        self._ticks: list = []
        self._complete = Event()
        self._failed_transfer_count = 0

    def _pin_changed(self, ticks, state) -> None:
        self._ticks.append(ticks)
        if len(self._ticks) >= DHT22_ALL_EDGES:
            self._complete.set()

    def _start(self) -> None:
        """Send the start signal and begin recording edges."""
        pin = self.pin
        pin.when_changed = None
        pin.output_with_state(False)  # LOW
        core.sleep_sec(self.START_SIGNAL_SEC)

        self._ticks = []
        self._complete.clear()
        # Enable edge detection before/while releasing the line. pigpio keeps
        # the pin as output (LOW) and watches it, lgpio and gpiod switch it to
        # input in one step. The sensor answers ~20us after the release.
        pin.edges = "rising"  # see dht22_bits()
        try:
            pin.when_changed = self._pin_changed
        except Exception:
            pin.function = "input"
            pin.when_changed = self._pin_changed

        if pin.function != "input":
            pin.function = "input"  # release the line (pull-up -> HIGH)

    def _finish(self) -> DHT22Data | None:
        """Stop recording and decode the received edges."""
        if self.pin is not None:
            self.pin.when_changed = None

        ticks = list(self._ticks)
        periods = [
            self.pin_factory.ticks_diff(later, earlier) * 1_000_000
            for earlier, later in zip(ticks, ticks[1:])
        ]
        try:
            humidity, temperature, _ = dht22_decode(periods)
        except ValueError as e:
            timings = " ".join(str(round(x)) for x in periods)
            self.invalid_data(f"{e} | periods us: {timings}")
            return None

        self._failed_transfer_count = 0
        sign = -1 if temperature & 0x8000 else 1
        data = DHT22Data(sign * (temperature & 0x7FFF) / 10.0, humidity / 10.0)
        _LOGGER.debug(f"{self!r}: {data}")
        callback = self.on_data_received
        if callback is not None:
            callback(data)
        return data

    def read(self) -> DHT22Data | None:
        """Read the sensor (blocks ~25ms). Call at most once every 2 seconds."""
        if self.pin is None:
            return None

        # no deep CPU idle during the transfer, waking up loses edges
        with core.low_latency():
            self._start()
            self._complete.wait(self.TRANSFER_TIMEOUT_SEC)
            core.sleep_sec(0.001)  # allow late edge callbacks
        return self._finish()

    def invalid_data(self, error: str) -> None:
        self._failed_transfer_count += 1
        if self._failed_transfer_count % self.WARN_AFTER_FAILURES == 0:
            _LOGGER.warning(
                f"{self!r}: {self._failed_transfer_count} failed reads, last: {error}"
            )
        else:
            _LOGGER.debug(f"{self!r}: invalid data: {error}")

        callback = self.on_invalid_data
        if callback is not None:
            callback()

    def close(self):
        if getattr(self, "pin", None) is not None:
            self.pin.when_changed = None
            self.pin_factory.release_pins(self, self.pin.info.name)
            self.pin.close()
            self.pin = None

    def set_on_data_received(self, callback: Callable[[DHT22Data], None]) -> None:
        self._on_data_received = None if callback is None else WeakMethod(callback)

    def set_on_invalid_data(self, callback: Callable[[], None]) -> None:
        self._on_invalid_data = None if callback is None else WeakMethod(callback)

    on_data_received: Callable[[DHT22Data], None] = property(
        fget=lambda self: (
            None if self._on_data_received is None else self._on_data_received()
        ),
        fset=lambda self, value: self.set_on_data_received(value),
        doc="""
            Event that is fired when a new data is received from the sensor.
            The callback should accept 1 argument: DHT22Data.
            """,
    )

    on_invalid_data: Callable[[], None] = property(
        fget=lambda self: (
            None if self._on_invalid_data is None else self._on_invalid_data()
        ),
        fset=lambda self, value: self.set_on_invalid_data(value),
        doc="""
            Event that is fired when an invalid data is received.
            """,
    )
