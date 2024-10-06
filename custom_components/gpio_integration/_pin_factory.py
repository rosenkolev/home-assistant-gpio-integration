# cspell:ignore lgpio, fromlist
from typing import Type

from gpiozero.pins import PinFactory

from .core import get_logger
from .schemas import CONF_INTERFACE

_LOGGER = get_logger()

DEFAULT_PIN_FACTORY: PinFactory | None = None
PIN_FACTORY_OPTIONS = dict()
PIN_FACTORIES = {
    "pigpio": "gpiozero.pins.pigpio:PiGPIOFactory",
    "lgpio": "gpiozero.pins.lgpio:LGPIOFactory",
    "rpigpio": "gpiozero.pins.rpigpio:RPiGPIOFactory",
    "native": "gpiozero.pins.native:NativeFactory",
    #
    # add custom pin factory
}


def set_default_pin_factory(factory: PinFactory) -> None:
    global DEFAULT_PIN_FACTORY
    DEFAULT_PIN_FACTORY = factory


def get_default_pin_factory() -> PinFactory:
    return DEFAULT_PIN_FACTORY


def set_config_options(data: dict) -> None:
    for key, value in data.items():
        PIN_FACTORY_OPTIONS[key] = value


def get_config_option(key: str):
    return PIN_FACTORY_OPTIONS.get(key, None)


def _get_pin_factory_class_by_name(name: str) -> Type[PinFactory]:
    mod_name, cls_name = PIN_FACTORIES[name].split(":", 1)
    path = f"{__package__}{mod_name}"
    module = __import__(path, fromlist=(cls_name,))
    pin_cls = getattr(module, cls_name)
    return pin_cls


def _find_pin_factory() -> PinFactory:
    for name, _ in PIN_FACTORIES.items():
        try:
            pin_factory_class = _get_pin_factory_class_by_name(name)
            return pin_factory_class()
        except Exception as e:
            _LOGGER.warn(f"Falling back from {name}: {e!s}")

    raise RuntimeError("No default pin factory available")


def get_pin_factory() -> PinFactory:
    pin_factory = get_default_pin_factory()
    if pin_factory is None:
        name = get_config_option(CONF_INTERFACE)
        if name is None or name == "":
            _LOGGER.debug("No pin factory specified - automatically detecting")
            pin_factory = _find_pin_factory()
        else:
            _LOGGER.debug(f"Using specified pin factory {name}")
            pin_factory_class = _get_pin_factory_class_by_name(name)
            pin_factory = pin_factory_class()

        set_default_pin_factory(pin_factory)

    if pin_factory is None:
        raise RuntimeError("No pin factory available")

    return pin_factory


def cleanup_default_factory():
    if DEFAULT_PIN_FACTORY is not None:
        DEFAULT_PIN_FACTORY.cleanup()
