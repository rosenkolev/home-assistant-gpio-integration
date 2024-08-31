from typing import Callable, Type
from custom_components.gpio_integration.const import get_logger
from . import BounceType, EdgesType, ModeType, Pin, PullType

_LOGGER = get_logger()

default_factories = {
    "pigpio": ".pigpio:GpioPin",
    "rpigpio": ".rpigpio:GpioPin",
}


def _get_default_pin_factory_class() -> Type[Pin]:
    for name, entry_point in default_factories.items():
        try:
            mod_name, cls_name = entry_point.split(":", 1)
            module = __import__(mod_name, fromlist=(cls_name,))
            pin_cls = getattr(module, cls_name)()
            return pin_cls
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
) -> Pin:
    if DEFAULT_PIN_CLASS is None:
        DEFAULT_PIN_CLASS = _get_default_pin_factory_class()

    return DEFAULT_PIN_CLASS(
        pin, mode, pull, bounce, edges, frequency, default_value, when_changed
    )
