"""
Third party packages bundled with the integration.

gpiozero 2.0.1 (https://github.com/gpiozero/gpiozero, BSD-3-Clause, see
gpiozero/LICENSE.rst) is bundled because Home Assistant core pins
gpiozero==1.6.2 for its legacy remote_rpi_gpio integration, while this
integration requires the gpiozero 2 pin API. A requirement in the manifest
conflicts with Home Assistant and can be replaced by 1.6.2 when Home
Assistant reinstalls its packages.

Changes to the original gpiozero 2.0.1 sources:
- devices.py: default pin factories are imported relative to the package.
- boards.py: fonts are loaded relative to the package.
"""
