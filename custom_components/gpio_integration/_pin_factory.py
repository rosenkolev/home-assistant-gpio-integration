# cspell:ignore lgpio, fromlist, gpiod, libgpiod
from threading import Lock
from typing import Type

from ._vendor.gpiozero import Device, Factory
from homeassistant.const import CONF_HOST

from .core import get_logger
from .schemas import CONF_INTERFACE

_LOGGER = get_logger()
_FACTORY_LOCK = Lock()

DEVICE_TREE_MODEL = "/proc/device-tree/model"
PIN_FACTORY_OPTIONS = dict({})
PIN_FACTORIES = {
    "pigpio": "._vendor.gpiozero.pins.pigpio:PiGPIOFactory",
    "lgpio": "._vendor.gpiozero.pins.lgpio:LGPIOFactory",
    "rpigpio": "._vendor.gpiozero.pins.rpigpio:RPiGPIOFactory",
    "native": "._vendor.gpiozero.pins.native:NativeFactory",
    # generic Linux GPIO character device (Radxa ROCK, Orange Pi, ...)
    "gpiod": ".pins.libgpiod:GpiodFactory",
    #
    # add custom pin factory like this:
    # "my_lib": ".pins.my_lib:MyLibFactory",
}

# Pin factories that only work on a Raspberry Pi
RASPBERRY_PI_FACTORIES = ["pigpio", "lgpio", "rpigpio", "native"]


def is_raspberry_pi() -> bool | None:
    """Return True/False based on the device tree model, None when unknown."""
    try:
        with open(DEVICE_TREE_MODEL, "rb") as f:
            model = f.read().decode("utf-8", "replace")
    except OSError:
        return None

    return model.lower().startswith("raspberry pi")


def set_config_options(data: dict) -> None:
    for key, value in data.items():
        PIN_FACTORY_OPTIONS[key] = value


def get_config_option(key: str):
    return PIN_FACTORY_OPTIONS.get(key, None)


def _get_pin_factory_class_by_name(name: str) -> Type[Factory]:
    mod_name, cls_name = PIN_FACTORIES[name].split(":", 1)
    if mod_name.startswith("."):
        path = f"{__package__}{mod_name}"
    else:
        path = mod_name
    module = __import__(path, fromlist=(cls_name,))
    pin_cls = getattr(module, cls_name)
    return pin_cls


def create_pin_factory(name: str, pin_factory_class: type[Factory]) -> Factory:
    if name == "pigpio" and CONF_HOST in PIN_FACTORY_OPTIONS:
        host = PIN_FACTORY_OPTIONS[CONF_HOST]
        if host is not None and host != "":
            return pin_factory_class(**{"host": host})

    return pin_factory_class()


def _get_pin_factory_names() -> list[str]:
    """Pin factory names in the order they are tried during auto detection."""
    names = list(PIN_FACTORIES.keys())
    if is_raspberry_pi() is False:
        # Not a Raspberry Pi, try the generic factories first
        names = [n for n in names if n not in RASPBERRY_PI_FACTORIES] + [
            n for n in names if n in RASPBERRY_PI_FACTORIES
        ]

    return names


def _find_pin_factory() -> Factory:
    for name in _get_pin_factory_names():
        try:
            pin_factory_class = _get_pin_factory_class_by_name(name)
            return create_pin_factory(name, pin_factory_class)
        except Exception as e:
            _LOGGER.warning(f"Falling back from {name}: {e!s}")

    raise RuntimeError("No default pin factory available")


def _create_default_pin_factory() -> Factory:
    name = get_config_option(CONF_INTERFACE)
    if name is None or name == "":
        _LOGGER.debug("No pin factory specified - automatically detecting")
        return _find_pin_factory()

    _LOGGER.debug(f"Using specified pin factory {name}")
    pin_factory_class = _get_pin_factory_class_by_name(name)
    return create_pin_factory(name, pin_factory_class)


def get_pin_factory() -> Factory:
    # use the gpiozero default pin factory if set
    pin_factory = Device.pin_factory
    if pin_factory is None:
        # entries are set up in parallel threads: create only one factory
        with _FACTORY_LOCK:
            pin_factory = Device.pin_factory
            if pin_factory is None:
                pin_factory = _create_default_pin_factory()
                Device.pin_factory = pin_factory

    if pin_factory is None:
        raise RuntimeError("No pin factory available")

    return pin_factory


def cleanup_default_factory():
    pin_factory: Factory | None = Device.pin_factory
    if pin_factory is not None:
        pin_factory.close()
