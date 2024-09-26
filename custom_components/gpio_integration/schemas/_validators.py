from . import InvalidPin


def v_pin(pin) -> bool:
    """Validate pin number."""
    if pin < 1:
        raise InvalidPin
    return True


def v_name(name) -> bool:
    """Validate name."""
    if name is None or name == "":
        raise ValueError("Name is required")
    return True


def v_time(time) -> bool:
    """Validate time."""
    if time <= 0:
        raise ValueError("Time must be greater than 0")
    return True
