from typing import Callable
import datetime
import asyncio

import gpiod
from gpiod.line import Direction, Bias, Edge, Value
from gpiod.line_settings import LineSettings


from custom_components.gpio_integration.const import DOMAIN, get_logger

from . import BounceType, EdgesType, ModeType, Pin, PinFactory, PullType

_LOGGER = get_logger()


def _guess_default_device() -> str:
    device_path = "/dev/gpiochip0"
    try:
        with open("/sys/firmware/devicetree/base/model") as model_file:
            device_model = model_file.read()

            if "Raspberry Pi 5 Model B" in device_model:
                device_path = "/dev/gpiochip4"
    except IOError:
        _LOGGER.error("Could not read device model file")

    _LOGGER.debug("Default GPIO device: %s", device_path)
    if not gpiod.is_gpiochip_device(device_path):
        raise RuntimeError(f"Device {device_path} is not a GPIO device")

    return device_path


class GpioPinFactory(PinFactory):
    def __init__(self) -> None:
        self.device = _guess_default_device()
        self._pin_class = GpioPin
        super().__init__()


GPIO_EDGES = {
    "both": Edge.BOTH,
    "rising": Edge.RISING,
    "falling": Edge.FALLING,
}

GPIO_MODES = {
    "input": Direction.INPUT,
    "output": Direction.OUTPUT,
}

GPIO_PULL_UPS = {
    "up": Bias.PULL_UP,
    "down": Bias.PULL_DOWN,
    "floating": Bias.DISABLED,
}


class GpioPin(Pin):
    def __init__(
        self,
        pin: int | str,
        mode: ModeType = "input",
        pull: PullType = "floating",
        bounce: BounceType = None,
        edge: EdgesType = "both",
        frequency: int | None = None,
        default_value: float | bool | None = None,
        when_changed: Callable[[int], None] = None,
        factory: GpioPinFactory = None,
    ):
        self.support_pwm = False
        self._req = None
        self._device = factory.device
        self._loop = None
        self._loop_exited = asyncio.Event()

        super().__init__(
            pin,
            mode,
            pull,
            bounce,
            edge,
            None,
            default_value,
            when_changed,
            factory,
        )

    def _setup(self):
        settings = dict(
            {
                "direction": GPIO_MODES[self.mode],
                "bias": GPIO_PULL_UPS[self.pull],
            }
        )

        edge_detection = self.edge_detection_enabled and self.mode == "input"

        if edge_detection:
            """set edge detection when reading"""
            settings["edge_detection"] = GPIO_EDGES[self.edges]
            settings["debounce_period"] = datetime.timedelta(seconds=self.bounce)

        self._req = gpiod.request_lines(
            self._device,
            consumer=DOMAIN,
            config={self.pin: LineSettings(**settings)},
        )

        if edge_detection:
            self.start_async_edge_detection_check_loop()

    async def _edge_detection_check_loop(self):
        while True:
            if self._loop_exit:
                break

            if self._req.wait_edge_events(datetime.timedelta(seconds=self.bounce)):
                if self._loop_exit:
                    break

                events = self.req.read_edge_events()
                if events is not None and len(events) > 0:
                    self._call_when_changed(0)

            await asyncio.sleep(self.bounce)

        if self._req is None:
            self._loop_exited.set()

    def _enable_event_detect(self):
        self._req = gpiod.reconfigure_lines(
            {
                self.pin: LineSettings(
                    edge_detection=GPIO_EDGES[self.edges],
                    debounce_period=datetime.timedelta(seconds=self.bounce),
                )
            }
        )

        if self._loop is None:
            self._loop_exit = False
            self._loop = asyncio.get_event_loop()
            self._loop.create_task(self._edge_detection_check_loop())

        _LOGGER.debug(f"pin {self.pin} edge detection enabled")

    def _disable_event_detect(self):
        self._req = gpiod.reconfigure_lines(
            {self.pin: LineSettings(edge_detection=Edge.NONE)}
        )

        """stop async thread in a loop to check for edge detection every debounce period"""
        self._loop.cancel()
        self._loop = None
        self._loop_exit = True

        _LOGGER.debug(f"pin {self.pin} edge detection disabled")

    async def _async_close(self):
        self.when_changed = None
        if self._req is not None:
            self._req.release()
            self._req = None

        if self._loop is not None:
            await self._loop_exited.wait()
