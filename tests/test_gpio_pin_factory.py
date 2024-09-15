from custom_components.gpio_integration.gpio import PinFactory


# Mock the Pin class
class MockPin:
    def __init__(
        self,
        pin,
        mode,
        pull,
        bounce,
        edges,
        frequency,
        default_value,
        when_changed,
        factory,
    ):
        self.pin = pin
        self.mode = mode
        self.pull = pull
        self.bounce = bounce
        self.edges = edges
        self.frequency = frequency
        self.default_value = default_value
        self.when_changed = when_changed
        self.factory = factory


class MockedPinFactory(PinFactory):
    def __init__(self) -> None:
        self._pin_class = MockPin
        super().__init__()


def test__find_default_pin_factory_is_pigpio():
    from custom_components.gpio_integration.gpio.pigpio import GpioPinFactory
    from custom_components.gpio_integration.gpio.pin_factory import get_pin_factory

    factory = get_pin_factory()

    assert factory is not None
    assert isinstance(factory, GpioPinFactory)
