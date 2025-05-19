<!-- cspell:ignore venv -->
# Contributing

## Project Structure

The code is located at `custom_components/gpio_integration`

```shell
custom_components/gpio_integration
  |- schemas/            #-> The config schematics for the entities
  |- controllers/        #-> A common controllers that handle entities (cover, sensors)
  |- __init__.py         #-> home assistant initialization code
  |- _devices.py         #-> wrappers around `gpiozero` Device classes
  |- _pin_factory.py     #-> functions that instantiate the correct pin_factory based on configs
  |- config_flow.py      #-> add/edit new entities logic: ConfigFlow, OptionsFlowHandler
  |- core.py             #-> common code like constants and base classes
  |- hub.py              #-> class shared between entities (facade)
  |- switch.py, number.py, etc #-> Home assistant entities
```

## Hardware Support

To create a new hardware implementation create new `Factory` and `Pin` ([gpiozero.pins](https://github.com/gpiozero/gpiozero/blob/master/gpiozero/pins/__init__.py)) child classes and implement it for the hardware. Then add it to `PIN_FACTORIES` in [_pin_factory](./_pin_factory.py).

## Setup

1. Create virtual environment and install packages

   ```shell
   # setup venv
   python3 -m venv .venv

   # activate: shell
   source .venv/bin/activate

   # activate: powershell
   ./.venv/Scripts/activate.ps1

   # install requirements
   pip3 install -r ./requirements.txt

   # setup pre-commit
   pre-commit install
   ```

1. Run all check

   ```shell
   ruff check . && coverage run --data-file reports/.coverage -m pytest -v -s && coverage report -m --data-file reports/.coverage
   ```
