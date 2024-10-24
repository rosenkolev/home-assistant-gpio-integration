from . import InvalidPin


def v_assert(value: bool, message: str, error_cls=ValueError) -> bool:
    if not value:
        raise error_cls(message)
    return True


def v_pin(pin) -> bool:
    """Validate pin number."""
    return v_assert(pin > 0, "Pin must be greater than 0", InvalidPin)


def v_name(name) -> bool:
    """Validate name."""
    return v_assert(name is not None and name != "", "Name is required")


def v_positive(value: float | int) -> bool:
    """Validate positive number."""
    return v_assert(value > 0, "Value must be greater than 0")


def v_positive_or_zero(value: float | int) -> bool:
    """Validate positive number."""
    return v_assert(value >= 0, "Value must be greater than or equal to 0")


def v_time(time) -> bool:
    return v_assert(time > 0, "Value must be greater than 0")
