# cspell:ignore lgpio, fromlist
from typing import Type

from gpiozero import Device, Factory
from homeassistant.const import CONF_HOST

from .core import get_logger
from .schemas import CONF_INTERFACE

_LOGGER = get_logger()

PIN_FACTORY_OPTIONS = dict()
PIN_FACTORIES = {
    "pigpio": "gpiozero.pins.pigpio:PiGPIOFactory",
    "lgpio": "gpiozero.pins.lgpio:LGPIOFactory",
    "rpigpio": "gpiozero.pins.rpigpio:RPiGPIOFactory",
    "native": "gpiozero.pins.native:NativeFactory",
    #
    # add custom pin factory
}


def set_config_options(data: dict) -> None:
    for key, value in data.items():
        PIN_FACTORY_OPTIONS[key] = value


def get_config_option(key: str):
    return PIN_FACTORY_OPTIONS.get(key, None)


def _get_pin_factory_class_by_name(name: str) -> Type[Factory]:
    mod_name, cls_name = PIN_FACTORIES[name].split(":", 1)
    path = f"{__package__}{mod_name}"
    module = __import__(path, fromlist=(cls_name,))
    pin_cls = getattr(module, cls_name)
    return pin_cls


def _find_pin_factory() -> Factory:
    for name, _ in PIN_FACTORIES.items():
        try:
            pin_factory_class = _get_pin_factory_class_by_name(name)
            if name == "pigpio" and CONF_HOST in PIN_FACTORY_OPTIONS:
                host = PIN_FACTORY_OPTIONS[CONF_HOST]
                return pin_factory_class(**{"host": host})

            return pin_factory_class()
        except Exception as e:
            _LOGGER.warn(f"Falling back from {name}: {e!s}")

    raise RuntimeError("No default pin factory available")


def get_pin_factory() -> Factory:
    # use the gpiozero default pin factory if set
    pin_factory = Device.pin_factory
    if pin_factory is None:
        name = get_config_option(CONF_INTERFACE)
        if name is None or name == "":
            _LOGGER.debug("No pin factory specified - automatically detecting")
            pin_factory = _find_pin_factory()
        else:
            _LOGGER.debug(f"Using specified pin factory {name}")
            pin_factory_class = _get_pin_factory_class_by_name(name)
            pin_factory = pin_factory_class()

        Device.pin_factory = pin_factory

    if pin_factory is None:
        raise RuntimeError("No pin factory available")

    return pin_factory


def cleanup_default_factory():
    pin_factory: Factory | None = Device.pin_factory
    if pin_factory is not None:
        pin_factory.close()
