# cspell:ignore fromlist

from typing import Callable, Type

from custom_components.gpio_integration.config_schema import CONF_INTERFACE
from custom_components.gpio_integration.core import get_logger

from . import (
    BounceType,
    EdgesType,
    ModeType,
    Pin,
    PinFactory,
    PullType,
    get_config_option,
    get_default_pin_factory,
    set_default_pin_factory,
)

_LOGGER = get_logger()

default_factories = {
    "pigpio": ".pigpio:GpioPinFactory",
    "rpigpio": ".rpigpio:GpioPinFactory",
    "gpiod": ".gpiod:GpioPinFactory",
}


def _get_pin_factory_class_by_name(name: str) -> Type[PinFactory]:
    mod_name, cls_name = default_factories[name].split(":", 1)
    path = f"{__package__}{mod_name}"
    module = __import__(path, fromlist=(cls_name,))
    pin_cls = getattr(module, cls_name)
    return pin_cls


def _find_pin_factory() -> PinFactory:
    for name, _ in default_factories.items():
        try:
            pin_factory_class = _get_pin_factory_class_by_name(name)
            return pin_factory_class()
        except Exception as e:
            _LOGGER.warn(f"Falling back from {name}: {e!s}")

    raise RuntimeError("No default pin factory available")


def get_pin_factory() -> None:
    name = get_config_option(CONF_INTERFACE)
    if name is None or name == "":
        _LOGGER.debug("No pin factory specified - automatically detecting")
        pin_factory = _find_pin_factory()
    else:
        _LOGGER.debug(f"Using specified pin factory {name}")
        pin_factory_class = _get_pin_factory_class_by_name(name)
        pin_factory = pin_factory_class()

    set_default_pin_factory(pin_factory)
    return pin_factory


def create_pin(
    pin: int | str,
    mode: ModeType = "input",
    pull: PullType = "floating",
    bounce: BounceType = None,
    edges: EdgesType = "both",
    frequency: int | None = None,
    default_value: float | bool | None = None,
    when_changed: Callable[[int], None] = None,
) -> Pin:
    pin_factory = get_default_pin_factory()
    if pin_factory is None:
        pin_factory = get_pin_factory()
        set_default_pin_factory(pin_factory)

    if pin_factory is None:
        raise RuntimeError("No pin factory available")

    return pin_factory.PinClass(
        pin,
        mode,
        pull,
        bounce,
        edges,
        frequency,
        default_value,
        when_changed,
        pin_factory,
    )
