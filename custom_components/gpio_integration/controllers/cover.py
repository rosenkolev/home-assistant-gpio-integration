import threading

from .._devices import BinarySensor, Switch
from ..core import get_logger, sleep_sec
from ..schemas.cover import RollerConfig

_LOGGER = get_logger()


class Roller:
    """Roller (device for HA)."""

    def __init__(
        self,
        config: RollerConfig,
    ) -> None:
        """Init the roller."""
        self.config = config
        self.name = config.name
        self.id = config.unique_id
        self.step: int = 5

        self._position = 0
        # Reports if the roller is moving up or down.
        # >0 is up, <0 is down. This very much just for demonstration.
        self._moving = 0

        self._pin_open = config.pin_open
        self._pin_close = config.pin_close
        self._pin_closed = config.pin_closed
        self._step_time = (config.relay_time / 100.0) * 5.0
        self._direction = -1
        self._has_sensor = config.pin_closed is not None

        self._cancel = threading.Event()

        _LOGGER.debug(
            "roller %s; down %s; up %s; closed %s",
            self.name,
            self._pin_open,
            self._pin_close,
            self._pin_closed,
        )

        self._io_open = Switch(
            self._pin_open,
            active_high=config.pin_open_on_state == "high",
        )
        self._io_close = Switch(
            self._pin_close, active_high=config.pin_close_on_state == "high"
        )

        self._io_sensor = (
            BinarySensor(
                self._pin_closed,
                active_high=config.pin_closed_on_state == "high",
            )
            if self._has_sensor
            else None
        )
        self._position = 0 if not self._has_sensor or self._io_sensor.is_active else 100

    @property
    def position(self) -> int:
        """Return position for roller."""
        return self._position

    @property
    def is_sensor_closed(self) -> bool:
        return self._has_sensor and self._io_sensor.is_active

    @property
    def is_closed(self) -> bool:
        return self._io_sensor.is_active if self._has_sensor else (self._position == 0)

    @property
    def is_moving(self) -> bool:
        return self._moving != 0

    @property
    def moving(self) -> int:
        return self._moving

    def update_state(self):
        if self.is_sensor_closed:
            self._position = 0

    def close(self):
        """Close the cover."""
        _LOGGER.debug('closing "%s"', self.name)

        # When close sensor show closed, do nothing
        if self.is_sensor_closed:
            return

        # When no close sensor and it's position 0 reset
        elif not self._has_sensor and self._position == 0:
            self._position = 100

        self.set_position(0)

    def open(self):
        """Open the cover."""
        _LOGGER.debug('opening "%s"', self.name)
        # if last position is fully open reset so we can try to open again
        if self._position == 100:
            self._position = 0

        self.set_position(100)

    def stop(self):
        """Stop the cover."""
        if self.is_moving:
            self._cancel.set()

    def set_position(self, position: int) -> None:
        """set the roller position"""
        if self.is_moving:
            _LOGGER.warning('roller "%s" can not be set when moving', self.name)
            return

        if position < 0 or position > 100:
            _LOGGER.warning(
                'roller "%s" can not be set to position %s', self.name, position
            )
            return

        if (self._position % self.step) != 0:
            _LOGGER.error('roller "%s" position is %s', self.name, self._position)
            return

        # round to closest step (e.g. 92 with step 5 will be 90 and 93 -> 95)
        target_position = int(self.step * round(float(position) / self.step))

        # move from position 50 to 75 eq 25 or -25 in reverse
        distance = target_position - self._position
        closing = distance < 0

        steps = int(abs(distance / 5))
        if steps == 0:
            return

        self._move(steps, closing, target_position == 0)

        _LOGGER.debug(
            '"%s" target %s current %s', self.name, target_position, self._position
        )

    def release(self):
        if self._io_sensor is not None:
            self._io_sensor.close()
            self._io_sensor = None
        if self._io_open is not None:
            self._io_open.close()
            self._io_open = None
        if self._io_close is not None:
            self._io_close.close()
            self._io_close = None

    def _move(self, steps, closing=False, full_close=False):
        """Move the roller at the given position."""

        pin = self._io_close if closing else self._io_open
        time = 0

        self._direction = -1 if closing else 1
        self._moving = self.step * self._direction

        _LOGGER.debug(
            'move "%s" pin "%s"; steps %s; move %s; pos %s',
            self.name,
            pin,
            steps,
            self._moving,
            self._position,
        )

        pin.value = True
        for x in range(steps):
            cancelled = self._cancel.wait(self._step_time)
            time += self._step_time
            self._position += self._moving
            if cancelled:
                _LOGGER.debug('"%s" move cancelled', self.name)
                break

        # wait extra second to make sure it's fully closed
        if not self.is_sensor_closed and full_close:
            sleep_sec(1)
            time += 1

        _LOGGER.debug('move "%s" time %s', self.name, time)
        self._moving = 0
        self._cancel.clear()
        pin.value = False

        if self._position < 0 and closing:
            self._position = 0
        elif self._position > 100 and not closing:
            self._position = 100
        elif self._position < 0 or self._position > 100:
            _LOGGER.error(
                'move "%s" was %s but position %s',
                self.name,
                "closing" if closing else "opening",
                self._position,
            )
