from typing import Callable, Literal
from time import sleep

import threading
from .io_interface import setup_input, write_output, read_input, setup_output, get_logger
from .config_flow import RollerConfig

_LOGGER = get_logger()

class Hub:
    """Dummy hub for Hello World example."""

    def __init__(self, configs: dict) -> None:
        """Init hub."""
        info = RollerConfig(configs)
        self.roller = Roller(info)

class Roller():
    """Roller (device for HA)."""
    def __init__(
        self,
        config: RollerConfig,
    ) -> None:
        """Init dummy roller."""
        self.name = config.name
        self.id = config.unique_id
        self.step: int = 5

        self.__position = 0
        # Reports if the roller is moving up or down.
        # >0 is up, <0 is down. This very much just for demonstration.
        self.__moving = 0

        self.__pin_down = config.pin_down
        self.__pin_up = config.pin_up
        self.__pin_down_default_to_high = config.pin_down_on_state == 'high'
        self.__pin_up_default_to_high = config.pin_up_on_state == 'high'
        self.__pin_closed = config.pin_closed
        self.__pin_closed_on_state = config.pin_closed_on_state == 'high'
        self.__has_close_sensor = config.pin_closed != None
        self.__step_time = (config.relay_time / 100.0) * 5.0
        self.__direction = -1
        
        self.__cancel = threading.Event()

        _LOGGER.debug('down pin %s set %s up pin %s set %s', self.__pin_down, self.__pin_down_default_to_high, self.__pin_up, self.__pin_up_default_to_high)
        setup_output(self.__pin_down, self.__pin_down_default_to_high)
        setup_output(self.__pin_up, self.__pin_up_default_to_high)

        if self.__has_close_sensor:
            setup_input(self.__pin_closed, config.pin_closed_mode)
            self.__position = 0 if self.sensor_closed else 100

    @property
    def sensor_closed(self) -> bool:
        return read_input() == self.__pin_closed_on_state
    
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
            _LOGGER.warn('roller "%s" can not be set to position %s', self.name, position)
            return

        if (self.__position % self.step) != 0:
            _LOGGER.error('roller "%s" position is %s', self.name, self.__position)
            return
    
        # round to closest step (e.g. 92 with step 5 will be 90 and 93 -> 95)
        target_position = int(self.step * round(float(position)/self.step))

        # move from position 50 to 75 eq 25 or -25 in reverse
        distance = target_position - self.__position
        closing = distance < 0

        steps = int(abs(distance / 5))
        if (steps == 0):
            return

        _LOGGER.debug('"%s" target %s current %s', self.name, target_position, self.__position)
        self.__move(steps, closing, target_position == 0)

        _LOGGER.debug('"%s" target %s current %s', self.name, target_position, self.__position)

    def __move(self, steps, closing = False, full_close = False):
        """toggle a state to GRIO"""

        pin = self.__pin_down if closing else self.__pin_up
        pin_off = self.__pin_down_default_to_high if closing else self.__pin_up_default_to_high
        pin_on = not pin_off
        time = 0

        self.__direction = -1 if closing else 1
        self.__moving = self.step * self.__direction

        _LOGGER.debug('move "%s" pin "%s"; on "%s"; steps %s; move %s; pos %s', self.name, pin, pin_on, steps, self.__moving, self.__position)

        write_output(pin, pin_on)
        for x in range(steps):
            cancelled = self.__cancel.wait(self.__step_time)
            time += self.__step_time
            self.__position += self.__moving
            if cancelled:
                _LOGGER.debug('"%s" move cancelled', self.name)
                break
        
        # wait extra second to make sure it's fully closed
        if full_close and not (self.__has_close_sensor and self.sensor_closed):
            sleep(1)
            time += 1

        _LOGGER.debug('move "%s" time %s', self.name, time)
        self.__moving = 0
        self.__cancel.clear()
        write_output(pin, pin_off)

        if self.__position < 0 and closing:
            self.__position = 0
        elif self.__position > 100 and not closing:
            self.__position = 100
        elif self.__position < 0 or self.__position > 100:
            _LOGGER.error('move "%s" was %s but position %s', self.name, 'closing' if closing else 'opening', self.__position)
