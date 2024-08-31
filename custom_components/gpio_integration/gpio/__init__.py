from threading import RLock
from types import MethodType
from typing import Literal, Callable
from weakref import WeakMethod, ref

PullType = Literal["floating", "up", "down"]
BounceType = float | None
EdgesType = Literal["rising", "falling", "both"]
ModeType = Literal["input", "output"]

ALL_PINS = dict()


class Pin:
    """
    Abstract base class representing a pin attached to a controller.

    *must* override:
    * :meth:`_connect`
    * :meth:`_close`
    * :meth:`_read`
    * :meth:`_write`
    * :meth:`_enable_event_detect`
    * :meth:`_disable_event_detect`

    *pwm* override:
    * :meth:`_read_pwm`
    * :meth:`_write_pww`
    * :meth:`_get_frequency`
    * :meth:`_set_frequency`

    *optional* override:
    * :meth:`_get_pull`
    * :meth:`_set_pull`
    * :meth:`_get_bounce`
    * :meth:`_set_bounce`
    * :meth:`_get_edges`
    * :meth:`_set_edges`
    * :meth:`_get_state`
    * :meth:`_set_state`
    """

    def __init__(
        self,
        pin: int | str,
        mode: ModeType = "input",
        pull: PullType = "floating",
        bounce: BounceType = None,
        edge: EdgesType = "BOTH",
        frequency: int | None = None,
        default_value: float | bool | None = None,
        when_changed: Callable[[int], None] = None,
    ):
        if pin == None:
            raise ValueError("pin is none")
        if pin in ALL_PINS:
            raise RuntimeError("Pin is already setup")

        self._pin = pin
        self._frequency: int | None = None
        self._mode = mode
        self._pull = pull
        self._bounce = bounce
        self._edge = edge
        self._when_changed_lock = RLock()
        self._when_changed = None
        ALL_PINS[pin] = self

        # connect
        self._connect()

        # Set default value if provided
        if default_value is not None and mode == "output":
            self.state = default_value

        # enable edge detection when no PWM
        if when_changed is not None and frequency is None:
            self.when_changed = when_changed

        if frequency is not None and mode == "output":
            self.frequency = frequency

    def __enter__(self):
        return self

    def __exit__(self):
        self.close()

    def __repr__(self) -> str:
        return f"<pin {self.pin!r}>"

    @property
    def pin(self):
        """The GPIO pin"""
        return self._pin

    @property
    def pwm(self):
        return self._frequency is not None

    @property
    def closed(self):
        """Check if the pin connection was closed"""
        try:
            return self._pin is None
        except AttributeError:
            return True

    @property
    def edge_detection_enabled(self) -> bool:
        return (
            self.edges is not None
            and self.bounce is not None
            and self._when_changed is not None
        )

    @property
    def state(self) -> float | bool:
        """
        The state of the pin. This is 0 for low, and 1 for high for digital inputs or for
        analog, or analog-like capabilities can return values between 0 and 1.
        """
        return self._get_state()

    @state.setter
    def state(self, value: float | bool) -> None:
        if self.mode == "output":
            self._set_state(value)
        else:
            raise RuntimeError(f"can't set state to pin {self.pin} in mode {self.mode}")

    @property
    def mode(self) -> ModeType:
        """
        The mode the pin is set to. *input* means we are only reading states and *output*
        is for read and write operations. This value always defaults to "input".
        """
        return self._get_mode()

    @mode.setter
    def mode(self, value: ModeType) -> None:
        self._set_mode(value)

    @property
    def pull(self) -> PullType:
        """
        The pull-up state of the pin represented as a string. This is typically
        one of the strings "up", "down", or "floating" but additional values
        may be supported by the underlying hardware.
        """
        return self._get_pull()

    @pull.setter
    def pull(self, value: PullType) -> None:
        self._set_pull(value)

    @property
    def frequency(self) -> int | None:
        """
        The frequency (in Hz) for the pin's PWM implementation, or :data:`None`
        if PWM is not currently in use. This value always defaults to :data:`None`.

        When this data is set it enables or disables PWM.
        """
        return self._get_frequency()

    @frequency.setter
    def frequency(self, value: int | None) -> None:
        self._set_frequency(value)

    @property
    def bounce(self) -> BounceType:
        """
        The amount of bounce detection (elimination) currently in use by edge
        detection, measured in seconds. If bounce detection is not currently in
        use, this is :data:`None`.

        For example, if :attr:`edges` is currently "rising", :attr:`bounce` is
        currently 5/1000 (5ms), then the waveform below will only fire
        :attr:`when_changed` on two occasions despite there being three rising
        edges:

        .. code-block:: text

            TIME 0...1...2...3...4...5...6...7...8...9...10..11..12 ms

            bounce elimination   |===================| |==============

            HIGH - - - - >       ,--. ,--------------. ,--.
                                 |  | |              | |  |
                                 |  | |              | |  |
            LOW  ----------------'  `-'              `-'  `-----------
                                 :                     :
                                 :                     :
                           when_changed          when_changed
                               fires                 fires
        """
        return self._get_bounce()

    @bounce.setter
    def bounce(self, value: BounceType) -> None:
        self._set_bounce(value)

    @property
    def edges(self) -> EdgesType:
        """
        The edge that will trigger execution of the function or bound method
        assigned to :attr:`when_changed`. This can be "both" (the default), "rising", "falling", or None:

        .. code-block:: text

            HIGH - - - - >           ,--------------.
                                     |              |
                                     |              |
            LOW  --------------------'              `--------------
                                     :              :
                                     :              :
            Fires when_changed     "both"         "both"
            when edges is ...     "rising"       "falling"
        """
        return self._get_edges()

    @edges.setter
    def edges(self, value: EdgesType) -> None:
        self._set_edges(value)

    @property
    def when_changed(self) -> Callable[[int], None] | None:
        """
        A function or bound method to be called when the pin's state changes
        (more specifically when the edge specified by :attr:`edges` is detected
        on the pin). The function or bound method accepts one parameter ticks.
        """
        return self._get_when_changed()

    @when_changed.setter
    def when_changed(self, value: Callable[[int], None] | None) -> None:
        self._set_when_changed(value)

    def close(self):
        """Close the connection to the pin"""
        if not self.closed:
            self._close()
            self._clear_pin()

    def _clear_pin(self):
        """Clear pins"""
        self._pin = None
        if self.pin in ALL_PINS:
            ALL_PINS.pop(self.pin)

    ### Abstract Members ###

    def _connect(self):
        pass

    def _close(self):
        pass

    def _read(self) -> bool:
        pass

    def _write(self, value: bool) -> None:
        pass

    def _read_pwm(self) -> float:
        raise NotImplementedError

    def _write_pwm(self, value: float) -> None:
        raise NotImplementedError

    def _enable_event_detect(self):
        raise NotImplementedError

    def _disable_event_detect(self):
        raise NotImplementedError

    def _enable_pwm(self, frequency: int):
        raise NotImplementedError

    def _update_frequency(self, frequency: int):
        pass

    def _disable_pwm(self):
        pass

    def _get_frequency(self) -> int | None:
        return self._frequency

    def _set_frequency(self, value: int | None) -> None:
        if not self.pwm and value is not None:
            if self.mode != "output":
                raise RuntimeError(f"cannot start PWM on pin {self!r}")

            self._enable_pwm(value)
        elif self.pwm and value is not None and value != self._frequency:
            self._update_frequency(value)
        elif self.pwm and value is None:
            self._disable_pwm()

        self._frequency = value

    ### Virtual Members ###

    def _get_state(self) -> float | bool:
        return self._read_pwm() if self.pwm else self._read()

    def _set_state(self, value: float | bool) -> None:
        if self.pwm:
            self._write_pwm(value)
        else:
            self._write(value)

    def _get_mode(self) -> ModeType:
        return self._mode

    def _set_mode(self, value: ModeType) -> None:
        self._mode = value

    def _get_pull(self) -> PullType:
        return self._pull

    def _set_pull(self, value: PullType):
        self._pull = value

    def _get_bounce(self) -> BounceType:
        return None if self._bounce <= 0 else self._bounce

    def _set_bounce(self, value: BounceType):
        self._bounce = None if value <= 0 else value

    def _get_edges(self) -> EdgesType:
        return self._edge

    def _set_edges(self, value: EdgesType) -> None:
        self._edge = value

    def _get_when_changed(self):
        return None if self._when_changed is None else self._when_changed()

    def _set_when_changed(self, value):
        with self._when_changed_lock:
            if value is None:
                if self._when_changed is not None:
                    self._disable_event_detect()
                self._when_changed = None
            else:
                enabled = self._when_changed is not None
                if isinstance(value, MethodType):
                    self._when_changed = WeakMethod(value)
                else:
                    self._when_changed = ref(value)
                if not enabled:
                    self._enable_event_detect()

    def _call_when_changed(self, ticks: int):
        method = self._when_changed()
        if method is None:
            self.when_changed = None
        else:
            method(ticks)


def close_all_pins():
    pins = ALL_PINS.values()
    for pin in pins:
        pin.close()
