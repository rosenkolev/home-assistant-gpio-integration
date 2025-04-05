from gpiozero import BoardInfo, Factory
from gpiozero.pins import HeaderInfo, PinInfo
from gpiozero.pins.mock import MockPin, PinState

PIN_NUMBER = 0


def get_next_pin() -> int:
    global PIN_NUMBER
    PIN_NUMBER += 1
    if PIN_NUMBER > 40:
        PIN_NUMBER = 1

    return PIN_NUMBER


def assert_gpio_blink(pin, gpio, test: list[tuple[bool, float]]):
    pin.states = []
    gpio._io._blink_thread.execute_target()
    map = gpio._io._blink_thread.zip(pin.states)
    assert len(map) == len(test)
    for idx in range(len(test)):
        val = round(map[idx][0], 2)
        assert test[idx][0] == val


class MockedBaseEntity:
    ha_state_update_scheduled = False
    ha_state_update_scheduled_force_refresh = False
    ha_state_write = False
    ha_added_to_hass = False
    hass = 1

    @property
    def name(self) -> str:
        return self._attr_name

    @property
    def unique_id(self) -> str:
        return self._attr_unique_id

    def async_write_ha_state(self):
        self.ha_state_write = True

    def async_schedule_update_ha_state(self, force_refresh=False):
        self.ha_state_update_scheduled = True
        self.ha_state_update_scheduled_force_refresh = force_refresh

    def schedule_update_ha_state(self, force_refresh=False):
        self.ha_state_update_scheduled = True
        self.ha_state_update_scheduled_force_refresh = False

    async def async_added_to_hass(self) -> None:
        self.ha_added_to_hass = True

    def async_on_remove(self, _=None):
        pass

    async def async_will_remove_from_hass(self) -> None:
        pass


class MockPinInner(MockPin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.closed = False
        self._frequency = None

    def _get_frequency(self):
        return self._frequency

    def _set_frequency(self, value):
        if value is not None:
            assert self._function == "output"
        self._frequency = value

    def _set_state(self, value):
        if self._frequency is not None:
            assert self._function == "output"
            assert 0 <= value <= 1
            self._change_state(float(value))
        else:
            super()._set_state(value)

    def close(self):
        super().close()
        self.frequency = None
        self.closed = True


class MockFactory(Factory):
    _ticks = 0

    def __init__(self):
        super().__init__()
        self.pin_class = MockPinInner
        self.pins = {}
        self._board_info = None

    def _get_revision(self):
        return 1

    def _get_board_info(self):
        if self._board_info is None:
            PINS = {}
            for number in range(1, 40):
                PINS[number] = MockFactory._make_pin_info(number)

            self._board_info = BoardInfo(
                board="Mock Board",
                revision="mock_rev",
                manufacturer="Mock Manufacturer",
                memory=256,
                model="Mock Model",
                pcb_revision="1.0",
                released="2021",
                soc="Mock SOC",
                storage="MicroSD",
                usb=4,
                usb3=0,
                ethernet=1,
                eth_speed=100,
                wifi=True,
                bluetooth=True,
                csi=1,
                dsi=1,
                headers={"A": HeaderInfo("A", 40, 1, PINS)},
            )

        return self._board_info

    def reset(self):
        self.pins.clear()
        self._reservations.clear()

    def pin(self, name):
        info = MockFactory._make_pin_info(name)
        try:
            pin = self.pins[info]
        except KeyError:
            pin = self.pin_class(self, info)
            self.pins[info] = pin
        return pin

    def set_ticks(self, ticks):
        MockFactory._ticks = ticks

    @staticmethod
    def ticks():
        return MockFactory._ticks

    @staticmethod
    def ticks_diff(later, earlier):
        return later - earlier

    @staticmethod
    def _make_pin_info(name):
        return PinInfo(
            number=name,
            name=f"GPIO{name}",
            names=frozenset([f"BOARD{name}", name, f"{name}"]),
            pull="",
            row=name,
            col=1,
            interfaces=frozenset(["gpio", "pwm", "spi"]),
        )


class MockedEvent:
    def __init__(self):
        self.waits = []

    def wait(self, timeout: int):
        return self.waits.append(timeout)


class MockedGPIOThread:
    def __init__(self, target, args=(), kwargs=None):
        self.args = args
        self.stopping = MockedEvent()
        self.target = target
        self.started = False

    def start(self):
        self.started = True

    def stop(self):
        self.started = False

    def execute_target(self):
        self.target(*self.args)

    def zip(self, pin_states: list[PinState]) -> list[tuple[bool, float]]:
        """Zip states.state with times."""
        times = self.stopping.waits
        return list(zip((state.state for state in pin_states), times))


class MockedTrackTimeInterval:
    def __init__(self):
        self._callback = None
        self._interval = None
        self._cancel_on_shutdown = False

    def caller(self, hass, callback, interval, cancel_on_shutdown=False) -> int:
        self._callback = callback
        self._interval = interval
        self._cancel_on_shutdown = cancel_on_shutdown
        return 0

    def tick(self):
        self._callback()


MOCK_MCP_INSTANCES: dict[int,] = {}


def get_mock_mcp(channel: int) -> MockPin:
    try:
        return MOCK_MCP_INSTANCES[channel]
    except KeyError:
        MOCK_MCP_INSTANCES[channel] = MockMCP(channel)
        return MOCK_MCP_INSTANCES[channel]


class MockMCP:
    def __init__(self, channel=0, pin_factory=None) -> None:
        self._value = 0.0
        self._closed = False

        MOCK_MCP_INSTANCES[channel] = self

    def read(self) -> float:
        return self._value

    def close(self) -> None:
        self._closed = True

    @property
    def value(self) -> float:
        return self._value
