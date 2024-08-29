from threading import RLock
from types import MethodType
from weakref import WeakMethod, ref

class Pin:
    """
    Abstract base class representing a pin attached to a controller.
    Descendent *must* override:

    * :meth:`_open`
    * :meth:`_close`
    """
    def __init__(self, pin=None, pwm=True, pull=None):
        self._pin = pin
        self._pwm = pwm
        if pin == None:
            raise ValueError("pin is none")
        
        self._connect()
        self._when_changed_lock = RLock()
        self._when_changed = None
        self._edges = 'both'
        __all_pins[pin]=self

    def __enter__(self):
        return self
    
    def __exit__(self):
        self.close()

    def __repr__(self) -> str:
        return f"<pin {self.pin!r}>"

    @property
    def pin(self):
        return self._pin

    @property
    def closed(self):
        try:
            return self._pin is None
        except AttributeError:
            return True

    pull = property(
        lambda self: self._get_pull(),
        lambda self, value: self._set_pull(value),
        doc="""\
        The pull-up state of the pin represented as a string. This is typically
        one of the strings "up", "down", or "floating" but additional values
        may be supported by the underlying hardware.
        """)

    frequency = property(
        lambda self: self._get_frequency(),
        lambda self, value: self._set_frequency(value),
        doc="""\
        The frequency (in Hz) for the pin's PWM implementation, or :data:`None`
        if PWM is not currently in use. This value always defaults to :data:`None`.
        """)

    bounce = property(
        lambda self: self._get_bounce(),
        lambda self, value: self._set_bounce(value),
        doc="""\
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
        """)
    
    edges = property(
        lambda self: self._get_edges(),
        lambda self, value: self._set_edges(value),
        doc="""\
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
        """)

    when_changed = property(
        lambda self: self._get_when_changed(),
        lambda self, value: self._set_when_changed(value),
        doc="""\
        A function or bound method to be called when the pin's state changes
        (more specifically when the edge specified by :attr:`edges` is detected
        on the pin). The function or bound method accepts one parameter ticks.
        """)

    def close(self):
        if not self.closed:
            self._close()
            self._clear_pin()

    def _clear_pin(self):
        self._pin=None
        if self.pin in __all_pins:
            __all_pins.pop(self.pin)

    def _open(self):
        pass

    def _close(self):
        pass

    def _enable_event_detect(self):
        raise NotImplementedError

    def _disable_event_detect(self):
        raise NotImplementedError

    def _get_pull(self):
        return 'floating'
    
    def _set_pull(self):
        raise NotImplementedError('pull is not supported')
    
    def _get_frequency(self):
        return None

    def _set_frequency(self, value):
        raise NotImplementedError('frequency is not supported')

    def _get_bounce(self):
        return None

    def _set_bounce(self, value):
        raise NotImplementedError('edge detection is not supported')
    
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
    
    def _call_when_changed(self, ticks, state):
        method = self._when_changed()
        if method is None:
            self.when_changed = None
        else:
            method(ticks, state)

__all_pins = dict[str, Pin]()

def close_all_pins():
    pins = __all_pins.values()
    for pin in pins:
        pin.close()
