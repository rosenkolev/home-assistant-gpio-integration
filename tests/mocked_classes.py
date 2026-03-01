from gpiozero import BoardInfo, Factory
from gpiozero.devices import GPIODevice
from gpiozero.pins import HeaderInfo, PinInfo
from gpiozero.pins.mock import MockPin, PinState


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


class MockGpioZeroDevice:
    def __init__(self, device: GPIODevice, defaultValue: int | float = 0):
        self._device = device
        self.value = defaultValue
        self._valueProp: property = None

    def __enter__(self):
        self._valueProp = self._device.__class__.value
        self._device.__class__.value = property(lambda _: self.value)
        return self

    def __exit__(self, *exc_info) -> None:
        self._device.__class__.value = self._valueProp


class MockedEvent:
    def __init__(self):
        self.waits: list[float] = []
        self._set = False

    def wait(self, timeout: int):
        return self.waits.append(timeout)

    def set(self):
        self._set = True

    def clear(self):
        self._set = True

    def assert_times(self, expected_times: list[float]):
        for actual, expected in zip(self.waits, expected_times):
            assert actual == expected


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


class MockedOptionsFlow:
    step_id: str
    data_schema: str
    abort_reason: str
    errors: str
    unique_id: str
    entity_title: str
    entity_data: dict

    def async_show_form(self, step_id: str, data_schema: dict, errors: dict = None):
        self.step_id = step_id
        self.data_schema = data_schema
        self.errors = errors

    def async_abort(self, reason: str):
        self.abort_reason = reason

    async def async_set_unique_id(self, unique_id: str):
        self.unique_id = unique_id

    def async_create_entry(self, title: str, data: dict):
        self.entity_title = title
        self.entity_data = data


class MockedConfigFlow(MockedOptionsFlow):
    @classmethod
    def __init_subclass__(cls, domain=None, **kwargs):
        super().__init_subclass__(**kwargs)


class MockVolSchema:
    def __init__(self, schema, extra=None):
        self.schema = schema


class MockColOptional:
    def __init__(self, name, default=None, description=None):
        self.schema = name
        self.default = lambda: default


class MockedPlatform:
    SWITCH = "switch"
    LIGHT = "light"
    COVER = "cover"
    BINARY_SENSOR = "binary_sensor"
    FAN = "fan"
    SENSOR = "sensor"
    NUMBER = "number"


class MockedDeviceInfo:
    def __init__(self, identifiers, name, manufacturer, model, sw_version):
        self.identifiers = identifiers
        self.name = name
        self.manufacturer = manufacturer
        self.model = model
        self.sw_version = sw_version
