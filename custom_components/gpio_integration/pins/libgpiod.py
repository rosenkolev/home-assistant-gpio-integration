# cspell:ignore gpiod, libgpiod, gpiochip, gpiochips, Rockchip, Radxa, socketpair, lgpio
"""
gpiozero pin factory based on the Linux GPIO character device (libgpiod v2).

The factory talks to ``/dev/gpiochipN`` through the ``gpiod`` python package
and therefore works on any board that exposes its GPIO lines through the
kernel, e.g. Radxa ROCK 5B / 5B+, and is not limited to the Raspberry Pi.

Pin numbering: ``number = chip_index * 32 + line_offset``. On Rockchip boards
this matches the vendor GPIO numbering (GPIO4_B3 = 4 * 32 + 1 * 8 + 3 = 139).
On boards with a single gpiochip the number is the line offset itself.

PWM is implemented in software (a thread toggles the line).
"""

from __future__ import annotations

import os
import re
import select
import socket
from datetime import timedelta
from threading import Event, Thread, current_thread
from time import monotonic, sleep

import gpiod
from gpiod.line import Bias, Clock, Direction, Edge, Value
from gpiozero.compat import frozendict
from gpiozero.exc import (
    PinFixedPull,
    PinInvalidBounce,
    PinInvalidEdges,
    PinInvalidFunction,
    PinInvalidPin,
    PinInvalidPull,
    PinInvalidState,
    PinPWMFixedValue,
    PinSetInput,
    PinSPIUnsupported,
)
from gpiozero.pins import BoardInfo, Factory, HeaderInfo, PinInfo
from gpiozero.pins.pi import PiPin

from ..core import get_logger

_LOGGER = get_logger()

CONSUMER = "home-assistant"
LINES_PER_BANK = 32
BANK_GROUPS = "ABCD"
EVENT_BUFFER_SIZE = 256
DEVICE_TREE_MODEL = "/proc/device-tree/model"
_CHIP_RE = re.compile(r"^gpiochip(\d+)$")


def read_board_model(path: str = DEVICE_TREE_MODEL) -> str:
    try:
        with open(path, "rb") as f:
            return f.read().rstrip(b"\x00").decode("utf-8", "replace").strip()
    except OSError:
        return "Unknown"


def find_gpiochips(dev_dir: str = "/dev") -> list[str]:
    """Return the paths of all gpiochip devices sorted by chip number."""
    chips: list[tuple[int, str]] = []
    try:
        entries = os.listdir(dev_dir)
    except OSError:
        return []

    for entry in entries:
        match = _CHIP_RE.match(entry)
        if match is None:
            continue
        path = f"{dev_dir}/{entry}"
        try:
            if gpiod.is_gpiochip_device(path):
                chips.append((int(match.group(1)), path))
        except OSError:
            continue

    return [path for _, path in sorted(chips)]


def pin_names(bank: int, offset: int, chip_name: str, line_name: str):
    """Return the primary name and all the names of a GPIO line."""
    number = bank * LINES_PER_BANK + offset
    name = f"GPIO{number}"
    names = {number, str(number), name, f"{chip_name}:{offset}"}
    if offset < LINES_PER_BANK:
        names.add(f"GPIO{bank}_{BANK_GROUPS[offset // 8]}{offset % 8}")
    if line_name:
        names.add(line_name)
    return name, frozenset(names)


class GpiodFactory(Factory):
    """
    gpiozero pin factory using the gpiod (libgpiod v2) python bindings.

    :param chips:
        Optional list of gpiochip device paths. When omitted all the
        ``/dev/gpiochip*`` devices are used.
    """

    def __init__(self, chips: list[str] | None = None):
        super().__init__()
        self._info: BoardInfo | None = None
        self._chips: list[gpiod.Chip] = []
        self._lines: dict[PinInfo, tuple[gpiod.Chip, int]] = {}
        self.pins: dict[PinInfo, GpiodPin] = {}
        self.pin_class = GpiodPin

        paths = find_gpiochips() if chips is None else list(chips)
        if not paths:
            raise RuntimeError("no gpiochip devices found")

        for path in paths:
            self._chips.append(gpiod.Chip(path))

        _LOGGER.debug(f"gpiod factory using {paths}")

    def close(self):
        for pin in list(self.pins.values()):
            pin.release()
        self.pins.clear()
        for chip in self._chips:
            chip.close()
        self._chips = []

    @property
    def chips(self) -> list[gpiod.Chip]:
        return self._chips

    def forget(self, pin: "GpiodPin") -> None:
        """Drop a closed pin, the next pin() call requests the line again."""
        if self.pins.get(pin.info) is pin:
            del self.pins[pin.info]

    def pin(self, name):
        for header, info in self.board_info.find_pin(name):
            try:
                pin = self.pins[info]
            except KeyError:
                pin = self.pin_class(self, info)
                self.pins[info] = pin
            return pin
        raise PinInvalidPin(f"{name} is not a valid pin name")

    def spi(self, **spi_args):
        raise PinSPIUnsupported("SPI is not supported by the gpiod pin factory")

    @staticmethod
    def ticks():
        return monotonic()

    @staticmethod
    def ticks_diff(later, earlier):
        return later - earlier

    def line(self, info: PinInfo) -> tuple[gpiod.Chip, int]:
        """Return the (chip, line offset) pair of a pin."""
        self.board_info  # noqa: B018 - make sure the line map is built
        return self._lines[info]

    def _get_board_info(self):
        if self._info is None:
            headers = {}
            for index, chip in enumerate(self._chips):
                header = self._make_header(index, chip)
                headers[header.name] = header

            self._info = BoardInfo(
                revision="",
                model=read_board_model(),
                pcb_revision="",
                released="",
                soc="",
                manufacturer="",
                memory=0,
                storage="",
                usb=0,
                usb3=0,
                ethernet=0,
                eth_speed=0,
                wifi=False,
                bluetooth=False,
                csi=0,
                dsi=0,
                headers=frozendict(headers),
                board="",
            )

        return self._info

    def _make_header(self, index: int, chip: gpiod.Chip) -> HeaderInfo:
        chip_info = chip.get_info()
        match = _CHIP_RE.match(chip_info.name)
        bank = int(match.group(1)) if match else index
        pins = {}
        for offset in range(chip_info.num_lines):
            try:
                line_name = chip.get_line_info(offset).name or ""
            except OSError:
                line_name = ""

            name, names = pin_names(bank, offset, chip_info.name, line_name)
            info = PinInfo(
                number=offset + 1,
                name=name,
                names=names,
                pull="",
                row=offset + 1,
                col=1,
                interfaces=frozendict({"gpio": line_name or name}),
            )
            pins[info.number] = info
            self._lines[info] = (chip, offset)

        return HeaderInfo(
            name=chip_info.name,
            rows=chip_info.num_lines,
            columns=1,
            pins=frozendict(pins),
        )


class SoftwarePwm(Thread):
    """Toggles a GPIO line from a thread to emulate PWM."""

    def __init__(self, request: gpiod.LineRequest, offset: int, frequency: float):
        super().__init__(name=f"gpiod-pwm-{offset}", daemon=True)
        self._request = request
        self._offset = offset
        self._frequency = float(frequency)
        self._duty = 0.0
        self._stopping = Event()
        self._changed = Event()

    @property
    def frequency(self) -> float:
        return self._frequency

    @property
    def duty(self) -> float:
        return self._duty

    def update(self, frequency: float | None = None, duty: float | None = None):
        if frequency is not None:
            self._frequency = float(frequency)
        if duty is not None:
            self._duty = float(duty)
        self._changed.set()

    def stop(self):
        self._stopping.set()
        self._changed.set()
        if current_thread() is not self and self.is_alive():
            self.join(timeout=1.0)

    def _write(self, value: bool):
        self._request.set_value(self._offset, Value.ACTIVE if value else Value.INACTIVE)

    def run(self):
        try:
            deadline = monotonic()
            while not self._stopping.is_set():
                frequency, duty = self._frequency, self._duty
                if frequency <= 0 or duty <= 0 or duty >= 1:
                    self._write(duty >= 1)
                    self._changed.wait()
                    self._changed.clear()
                    deadline = monotonic()
                    continue

                period = 1.0 / frequency
                self._write(True)
                deadline += period * duty
                sleep(max(0.0, deadline - monotonic()))
                self._write(False)
                deadline += period * (1.0 - duty)
                sleep(max(0.0, deadline - monotonic()))
        except Exception as e:
            if not self._stopping.is_set():
                _LOGGER.warning(f"software PWM on line {self._offset} stopped: {e!s}")


class EdgeWatcher(Thread):
    """Waits for edge events of a line request and dispatches them to a pin."""

    def __init__(self, pin: GpiodPin):
        super().__init__(name=f"gpiod-edge-{pin.info.name}", daemon=True)
        self._pin = pin
        self._request = pin.request
        self._stopping = False
        # socket pair instead of a pipe: select() works with it everywhere
        self._wake_r, self._wake_w = socket.socketpair()

    @property
    def stopping(self) -> bool:
        return self._stopping

    def stop(self):
        """Signal the thread to stop. Never joins (may be called from a callback)."""
        self._stopping = True
        try:
            self._wake_w.send(b"x")
        except OSError:
            pass

    def run(self):
        try:
            fd = self._request.fd
            while not self._stopping:
                readable, _, _ = select.select([fd, self._wake_r], [], [])
                if self._stopping:
                    break
                if fd in readable:
                    for event in self._request.read_edge_events():
                        if self._stopping:
                            break
                        self._pin.dispatch_event(event)
        except Exception as e:
            if not self._stopping:
                _LOGGER.warning(f"{self._pin!r}: edge detection stopped: {e!s}")
        finally:
            self._wake_r.close()
            self._wake_w.close()


class GpiodPin(PiPin):
    """gpiozero pin backed by a single line request of the gpiod library."""

    GPIO_EDGES = {
        "both": Edge.BOTH,
        "rising": Edge.RISING,
        "falling": Edge.FALLING,
    }

    GPIO_PULLS = {
        "up": Bias.PULL_UP,
        "down": Bias.PULL_DOWN,
        "floating": Bias.DISABLED,
    }

    def __init__(self, factory: GpiodFactory, info: PinInfo):
        super().__init__(factory, info)
        self._chip, self._offset = factory.line(info)
        self._function = "input"
        self._pull = "floating"
        self._bias = Bias.AS_IS
        self._edges = "both"
        self._bounce: float | None = None
        self._pwm: SoftwarePwm | None = None
        self._watcher: EdgeWatcher | None = None
        self._request: gpiod.LineRequest | None = self._chip.request_lines(
            consumer=CONSUMER,
            config={self._offset: gpiod.LineSettings(direction=Direction.INPUT)},
            event_buffer_size=EVENT_BUFFER_SIZE,
        )

    @property
    def request(self) -> gpiod.LineRequest:
        return self._request

    @property
    def offset(self) -> int:
        return self._offset

    def __repr__(self):
        return f"{self._info.name} ({self._chip.get_info().name}:{self._offset})"

    def close(self):
        """
        Reset the pin to a plain input and release the line, so it can be
        requested again (e.g. when a Home Assistant entry is reloaded).
        """
        self._stop_pwm()
        self._stop_watcher()
        self._when_changed = None
        self._pull = "floating"
        self._bias = Bias.AS_IS
        self._function = "input"
        if self._request is not None:
            try:
                self._reconfigure(self._input_settings())
            except OSError:
                pass
        self.release()
        self._factory.forget(self)

    def release(self):
        """Close the pin and release the line request (used by the factory)."""
        self._stop_pwm()
        self._stop_watcher()
        self._when_changed = None
        if self._request is not None:
            self._request.release()
            self._request = None

    # --- configuration helpers ---

    def _input_settings(self, edge: Edge = Edge.NONE) -> gpiod.LineSettings:
        settings = {
            "direction": Direction.INPUT,
            "bias": self._bias,
            "edge_detection": edge,
            "event_clock": Clock.MONOTONIC,
        }
        if edge != Edge.NONE and self._bounce:
            settings["debounce_period"] = timedelta(seconds=self._bounce)
        return gpiod.LineSettings(**settings)

    def _output_settings(self, state: bool = False) -> gpiod.LineSettings:
        return gpiod.LineSettings(
            direction=Direction.OUTPUT,
            output_value=Value.ACTIVE if state else Value.INACTIVE,
        )

    def _reconfigure(self, settings: gpiod.LineSettings) -> None:
        self._request.reconfigure_lines({self._offset: settings})

    def _apply_input(self) -> None:
        """Re-apply the input settings (keeps edge detection when active)."""
        edge = Edge.NONE
        if self._watcher is not None:
            edge = self.GPIO_EDGES[self._edges]
        self._reconfigure(self._input_settings(edge))

    def _stop_pwm(self) -> None:
        if self._pwm is not None:
            pwm, self._pwm = self._pwm, None
            pwm.stop()
            if self._request is not None and self._function == "output":
                self._request.set_value(
                    self._offset, Value.ACTIVE if pwm.duty >= 1 else Value.INACTIVE
                )

    def _stop_watcher(self) -> None:
        if self._watcher is not None:
            watcher, self._watcher = self._watcher, None
            watcher.stop()

    # --- gpiozero Pin API ---

    def output_with_state(self, state):
        self._stop_pwm()
        self._stop_watcher()
        self._reconfigure(self._output_settings(bool(state)))
        self._function = "output"

    def input_with_pull(self, pull):
        self._check_pull(pull)
        self._stop_pwm()
        self._stop_watcher()
        self._pull = pull
        self._bias = self.GPIO_PULLS[pull]
        self._reconfigure(self._input_settings())
        self._function = "input"

    def _get_function(self):
        return self._function

    def _set_function(self, value):
        if value not in ("input", "output"):
            raise PinInvalidFunction(f'invalid function "{value}" for pin {self!r}')
        self._stop_pwm()
        self._stop_watcher()
        if value == "input":
            self._reconfigure(self._input_settings())
        else:
            self._reconfigure(self._output_settings(False))
        self._function = value

    def _get_state(self):
        if self._pwm is not None:
            return self._pwm.duty
        return self._request.get_value(self._offset) == Value.ACTIVE

    def _set_state(self, value):
        if self._pwm is not None:
            if not 0 <= value <= 1:
                raise PinInvalidState(f'invalid state "{value}" for pin {self!r}')
            self._pwm.update(duty=value)
        elif self._function == "input":
            raise PinSetInput(f"cannot set state of pin {self!r}")
        else:
            self._request.set_value(
                self._offset, Value.ACTIVE if value else Value.INACTIVE
            )

    def _get_pull(self):
        return self._pull

    def _check_pull(self, value):
        if value not in self.GPIO_PULLS:
            raise PinInvalidPull(f'invalid pull "{value}" for pin {self!r}')
        if self.info.pull not in (value, ""):
            raise PinFixedPull(
                f"{self!r} has a physical pull-{self.info.pull} resistor"
            )

    def _set_pull(self, value):
        if self._function != "input":
            raise PinFixedPull(f"cannot set pull on non-input pin {self!r}")
        self._check_pull(value)
        self._pull = value
        self._bias = self.GPIO_PULLS[value]
        self._apply_input()

    def _get_frequency(self):
        return None if self._pwm is None else self._pwm.frequency

    def _set_frequency(self, value):
        if value is not None and value > 0:
            if self._function != "output":
                raise PinPWMFixedValue(f"cannot start PWM on pin {self!r}")
            if self._pwm is None:
                self._stop_watcher()
                self._pwm = SoftwarePwm(self._request, self._offset, value)
                self._pwm.start()
            else:
                self._pwm.update(frequency=value)
        else:
            self._stop_pwm()

    def _get_bounce(self):
        return self._bounce

    def _set_bounce(self, value):
        if value is not None and value < 0:
            raise PinInvalidBounce("bounce must be 0 or greater")
        self._bounce = None if not value else float(value)
        if self._watcher is not None:
            self._apply_input()

    def _get_edges(self):
        return self._edges

    def _set_edges(self, value):
        if value not in self.GPIO_EDGES:
            raise PinInvalidEdges(f'invalid edges "{value}" for pin {self!r}')
        f = self.when_changed
        self.when_changed = None
        try:
            self._edges = value
        finally:
            self.when_changed = f

    def dispatch_event(self, event) -> None:
        state = 1 if event.event_type == gpiod.EdgeEvent.Type.RISING_EDGE else 0
        try:
            self._call_when_changed(event.timestamp_ns / 1_000_000_000, state)
        except Exception:
            _LOGGER.exception(f"{self!r}: when_changed callback failed")

    def _enable_event_detect(self):
        # Like lgpio (gpio_claim_alert), an output pin is switched to input
        # and edge detection is enabled in a single atomic reconfigure.
        # Protocols like DHT22 rely on it: the sensor answers ~20us after the
        # line is released, so no edge must be lost between both steps.
        self._stop_pwm()
        self._stop_watcher()
        self._reconfigure(self._input_settings(self.GPIO_EDGES[self._edges]))
        self._function = "input"
        self._watcher = EdgeWatcher(self)
        self._watcher.start()

    def _disable_event_detect(self):
        self._stop_watcher()
        if self._request is not None and self._function == "input":
            self._reconfigure(self._input_settings())
