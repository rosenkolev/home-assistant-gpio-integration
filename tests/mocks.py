from gpiozero import BoardInfo, Factory
from gpiozero.pins import HeaderInfo, PinInfo
from gpiozero.pins.mock import MockPin

PIN_NUMBER = 0


def get_next_pin() -> int:
    global PIN_NUMBER
    PIN_NUMBER += 1
    if PIN_NUMBER > 40:
        PIN_NUMBER = 1

    return PIN_NUMBER


class MockedBaseEntity:
    ha_state_update_scheduled = False
    ha_state_update_scheduled_force_refresh = False
    ha_state_write = False

    def async_write_ha_state(self):
        self.ha_state_write = True

    def async_schedule_update_ha_state(self, force_refresh=False):
        self.ha_state_update_scheduled = True
        self.ha_state_update_scheduled_force_refresh = force_refresh

    def schedule_update_ha_state(self, force_refresh=False):
        self.ha_state_update_scheduled = True
        self.ha_state_update_scheduled_force_refresh = False

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
