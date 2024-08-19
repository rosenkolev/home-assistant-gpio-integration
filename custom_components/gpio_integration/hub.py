from typing import Callable, Literal
from time import sleep

from homeassistant.const import Platform

import threading
from .config_schema import RollerConfig, SensorConfig, SwitchConfig, ToggleRollerConfig
from .const import get_logger
from .gpio import Gpio

_LOGGER = get_logger()


class Hub:
    """Dummy hub for Hello World example."""

    def __init__(self, configs: dict) -> None:
        """Init hub."""
        self.type = configs["type"]
        _LOGGER.debug('Hub type "%s"', self.type)
        if self.type == "cover_up_down":
            self.config = RollerConfig(configs)
            self.controller = Roller(self.config)
            self.platforms = [Platform.COVER, Platform.NUMBER]
        elif self.type == "cover_toggle":
            self.config = ToggleRollerConfig(configs)
            self.controller = BasicToggleRoller(self.config)
            self.platforms = [Platform.COVER]
        elif self.type == "binary_sensor":
            self.config = SensorConfig(configs)
            self.platforms = [Platform.BINARY_SENSOR]
        elif self.type == "switch":
            self.config = SwitchConfig(configs)
            self.platforms = [Platform.SWITCH]

    @property
    def is_cover(self) -> bool:
        return self.type == "cover_up_down"

    @property
    def is_cover_toggle(self) -> bool:
        return self.type == "cover_toggle"


class BasicToggleRoller:
    def __init__(self, config: ToggleRollerConfig) -> None:
        self.name = config.name
        self.id = config.unique_id
        self.__has_close_sensor = config.pin_closed != None
        self.__state = False
        self.__invert = config.invert_logic
        self.__relay_time = config.relay_time
        self.__io = Gpio(config.port, mode="write")

        if self.__has_close_sensor:
            self.__io_closed = Gpio(config.pin_closed, mode="read")

    @property
    def is_closed(self):
        """Return true if cover is closed."""
        return self.__state != self.__invert

    def release(self):
        self.__io.release()
        if self.__has_close_sensor:
            self.__io_closed.release()

    def update(self):
        if self.__has_close_sensor:
            self.__state = self.__io_closed.read()

    def toggle(self):
        """Trigger the cover."""
        self.__io.write(1 if self.__invert else 0)
        sleep(self.__relay_time)
        self.__io.write(0 if self.__invert else 1)
        if not self.__has_close_sensor:
            self.__state = not self.__state


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

        self.__position = 0
        # Reports if the roller is moving up or down.
        # >0 is up, <0 is down. This very much just for demonstration.
        self.__moving = 0

        self.__pin_down = config.pin_down
        self.__pin_up = config.pin_up
        self.__pin_down_default_to_high = config.pin_down_on_state == "high"
        self.__pin_up_default_to_high = config.pin_up_on_state == "high"
        self.__pin_closed = config.pin_closed
        self.__pin_closed_on_state = config.pin_closed_on_state == "high"
        self.__has_close_sensor = config.pin_closed != None
        self.__step_time = (config.relay_time / 100.0) * 5.0
        self.__direction = -1

        self.__cancel = threading.Event()

        _LOGGER.debug(
            "down pin %s set %s up pin %s set %s",
            self.__pin_down,
            self.__pin_down_default_to_high,
            self.__pin_up,
            self.__pin_up_default_to_high,
        )
        self.__io_down = Gpio(
            self.__pin_down, mode="write", default_value=self.__pin_down_default_to_high
        )
        self.__io_up = Gpio(
            self.__pin_up, mode="write", default_value=self.__pin_up_default_to_high
        )

        if self.__has_close_sensor:
            self.__io_closed = Gpio(self.__pin_closed, mode="read")
            self.__position = 0 if self.__io_closed.read() else 100

    @property
    def sensor_closed(self) -> bool:
        return self.__io_closed.read() == self.__pin_closed_on_state

    @property
    def position(self) -> int:
        """Return position for roller."""
        return self.__position

    @property
    def is_closed(self) -> bool:
        return self.sensor_closed if self.__has_close_sensor else (self.__position == 0)

    @property
    def is_moving(self) -> bool:
        return self.__moving != 0

    @property
    def moving(self) -> int:
        return self.__moving

    def release(self):
        self.__io_down.release()
        self.__io_up.release()
        if self.__has_close_sensor:
            self.__io_closed.release()

    def update_state(self):
        if self.__has_close_sensor:
            if self.sensor_closed:
                self.__position = 0

    def close(self):
        """Close the cover."""
        _LOGGER.debug('closing "%s"', self.name)
        # When close sensor show closed, do nothing
        if self.__has_close_sensor and self.sensor_closed:
            return
        # When no close sensor and it's position 0 reset
        elif not self.__has_close_sensor and self.__position == 0:
            self.__position = 100

        self.set_position(0)

    def open(self):
        """Open the cover."""
        _LOGGER.debug('opening "%s"', self.name)
        # if last position is fully open reset so we can try to open again
        if self.__position == 100:
            self.__position = 0

        self.set_position(100)

    def stop(self):
        """Stop the cover."""
        if self.is_moving:
            self.__cancel.set()

    def set_position(self, position: int) -> None:
        """set the roller position"""
        if self.is_moving:
            _LOGGER.warn('roller "%s" can not be set when moving', self.name)
            return

        if position < 0 or position > 100:
            _LOGGER.warn(
                'roller "%s" can not be set to position %s', self.name, position
            )
            return

        if (self.__position % self.step) != 0:
            _LOGGER.error('roller "%s" position is %s', self.name, self.__position)
            return

        # round to closest step (e.g. 92 with step 5 will be 90 and 93 -> 95)
        target_position = int(self.step * round(float(position) / self.step))

        # move from position 50 to 75 eq 25 or -25 in reverse
        distance = target_position - self.__position
        closing = distance < 0

        steps = int(abs(distance / 5))
        if steps == 0:
            return

        self.__move(steps, closing, target_position == 0)

        _LOGGER.debug(
            '"%s" target %s current %s', self.name, target_position, self.__position
        )

    def __move(self, steps, closing=False, full_close=False):
        """toggle a state to GRIO"""

        pin = self.__io_down if closing else self.__io_up
        pin_off = (
            self.__pin_down_default_to_high
            if closing
            else self.__pin_up_default_to_high
        )
        pin_on = not pin_off
        time = 0

        self.__direction = -1 if closing else 1
        self.__moving = self.step * self.__direction

        _LOGGER.debug(
            'move "%s" pin "%s"; on "%s"; steps %s; move %s; pos %s',
            self.name,
            pin,
            pin_on,
            steps,
            self.__moving,
            self.__position,
        )

        pin.write(pin_on)
        for x in range(steps):
            cancelled = self.__cancel.wait(self.__step_time)
            time += self.__step_time
            self.__position += self.__moving
            if cancelled:
                _LOGGER.debug('"%s" move cancelled', self.name)
                break

        is_sensor_show_closed = self.__has_close_sensor and self.sensor_closed

        # wait extra second to make sure it's fully closed
        if not is_sensor_show_closed and full_close:
            sleep(1)
            time += 1

        _LOGGER.debug('move "%s" time %s', self.name, time)
        self.__moving = 0
        self.__cancel.clear()
        pin.write(pin_off)

        if self.__position < 0 and closing:
            self.__position = 0
        elif self.__position > 100 and not closing:
            self.__position = 100
        elif self.__position < 0 or self.__position > 100:
            _LOGGER.error(
                'move "%s" was %s but position %s',
                self.name,
                "closing" if closing else "opening",
                self.__position,
            )
