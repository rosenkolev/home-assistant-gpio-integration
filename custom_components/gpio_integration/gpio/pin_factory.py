# cspell:ignore fromlist

from typing import Callable, Type

from custom_components.gpio_integration.const import get_logger

from . import BounceType, EdgesType, ModeType, Pin, PullType

_LOGGER = get_logger()

default_factories = {
    "pigpio": ".pigpio:GpioPin",
    "rpigpio": ".rpigpio:GpioPin",
}


def _get_pin_factory_class(name: str) -> Type[Pin]:
    mod_name, cls_name = default_factories[name].split(":", 1)
    path = f"{__package__}{mod_name}"
    _LOGGER.warning(f"Loading {mod_name} {cls_name}: {path}")
    module = __import__(path, fromlist=(cls_name))
    pin_cls = getattr(module, cls_name)()
    return pin_cls


def _get_default_pin_factory_class() -> Type[Pin]:
    for name, _ in default_factories.items():
        try:
            return _get_pin_factory_class(name)
        except Exception as e:
            _LOGGER.warn(f"Falling back from {name}: {e!s}")


DEFAULT_PIN_CLASS: Type[Pin] | None = None


def create_pin(
    pin: int | str,
    mode: ModeType = "input",
    pull: PullType = "floating",
    bounce: BounceType = None,
    edges: EdgesType = "BOTH",
    frequency: int | None = None,
    default_value: float | bool | None = None,
    when_changed: Callable[[int], None] = None,
    interface: str | None = None,
) -> Pin:
    global DEFAULT_PIN_CLASS
    pin_cls: Type[Pin]
    if interface is not None and interface in default_factories:
        pin_cls = _get_pin_factory_class(interface)
    else:
        if DEFAULT_PIN_CLASS is None:
            DEFAULT_PIN_CLASS = _get_default_pin_factory_class()

        pin_cls = DEFAULT_PIN_CLASS

    return pin_cls(
        pin, mode, pull, bounce, edges, frequency, default_value, when_changed
    )
