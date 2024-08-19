from typing import Callable, Literal
from time import sleep

from homeassistant.const import Platform

import threading
from .io_interface import (
    edge_detect,
    setup_input,
    write_output,
    read_input,
    setup_output,
    get_logger,
)
from .config_schema import RollerConfig, SensorConfig, SwitchConfig, ToggleRollerConfig

_LOGGER = get_logger()


class Hub:
    """Dummy hub for Hello World example."""

    def __init__(self, configs: dict) -> None:
        """Init hub."""
        self.type = configs["type"]
        _LOGGER.debug('Hub type "%s"', self.type)
        if self.type == "cover_up_down":
            self.controller = Roller(RollerConfig(configs))
            self.platforms = [Platform.COVER, Platform.NUMBER]
        elif self.type == "cover_toggle":
            self.controller = BasicToggleRoller(ToggleRollerConfig(configs))
            self.platforms = [Platform.COVER]
        elif self.type == "binary_sensor":
            self.controller = Sensor(SensorConfig(configs))
            self.platforms = [Platform.BINARY_SENSOR]
        elif self.type == "switch":
            self.controller = Switch(SwitchConfig(configs))
            self.platforms = [Platform.SWITCH]

    @property
    def is_cover(self) -> bool:
        return self.type == "cover_up_down"

    @property
    def is_cover_toggle(self) -> bool:
        return self.type == "cover_toggle"


class Switch:
    def __init__(self, config: SwitchConfig) -> None:
        self.name = config.name
        self.id = config.unique_id
        self.pin = config.port
        self.__invert = config.invert_logic
        self.__initial_state = config.default_state
        setup_output(self.pin)
        self.reset()

    def __get_actual_state_value(self, state: bool) -> bool:
        return not self.__invert if state else self.__invert

    @property
    def state(self) -> bool:
        return self.__state

    def reset(self):
        _LOGGER.debug('switch "%s" reset to "%s"', self.name, self.__initial_state)
        self.set_state(self.__initial_state)

    def set_state(self, state) -> None:
        value = self.__get_actual_state_value(state)
        _LOGGER.debug('switch "%s" set high to %s', self.name, value)
        write_output(self.pin, value)
        self.__state = state


class Sensor:
    def __init__(self, config: SensorConfig) -> None:
        self.config = config
        self.name = config.name
        self.id = config.unique_id
        self.pin = config.pin
        self.state = None
        self.bounce_time_ms = config.bounce_time_ms
        self.__invert = config.invert_logic
        setup_input(self.pin, config.pull_mode)

    def add_detection(self, event_callback: Callable):
        edge_detect(self.pin, event_callback, self.bounce_time_ms)

    def update(self):
        self.__state = read_input(self.__pin)

    @property
    def bounce_time_sec(self) -> float:
        return float(self.bounce_time_ms) / 1000.0

    @property
    def is_on(self) -> bool:
        return self.__state != self.__invert


class BasicToggleRoller:
    def __init__(self, config: ToggleRollerConfig) -> None:
        self.config = config
        self.name = config.name
        self.id = config.unique_id
        self.__pin = config.port
        self.__state = False
        self.__invert = config.invert_logic
        self.__relay_time = config.relay_time

        setup_output(self.port, self.__invert)
        if config.pin_closed:
            setup_input(config.pin_closed, "up")

    @property
    def is_closed(self):
        """Return true if cover is closed."""
        return self.__state != self.__invert

    def update_state(self):
        self.__state = read_input(self.__pin)

    def toggle(self):
        """Trigger the cover."""
        write_output(self.__pin, 1 if self.__invert else 0)
        sleep(self.__relay_time)
        write_output(self.__pin, 0 if self.__invert else 1)


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

        pin = self.__pin_down if closing else self.__pin_up
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
            _LOGGER.error(
                'move "%s" was %s but position %s',
                self.name,
                "closing" if closing else "opening",
                self.__position,
            )
