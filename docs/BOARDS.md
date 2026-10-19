<!-- cspell:ignore gpiod, libgpiod, gpiochip, gpiochips, gpioinfo, gpiofind, Radxa, Rockchip, Armbian, pigpiod -->
# Boards other than Raspberry Pi

Any Linux board that exposes its GPIO lines as `/dev/gpiochipN` devices is supported through the `gpiod` interface ([libgpiod](https://libgpiod.readthedocs.io/) python bindings, already included in the Home Assistant docker image).

Tested boards:

* [Radxa ROCK 5B+](./RADXA_ROCK5.md) (Armbian, Home Assistant container)

## Requirements

* Home Assistant must be able to access `/dev/gpiochip*`.
  * Home Assistant Container: run the container with `privileged: true` or map the devices
    (`--device /dev/gpiochip0 ... --device /dev/gpiochipN`).
  * Home Assistant Supervised / OS: the devices are accessible by default.
* Nothing else needs to be installed (`pigpiod` is not used).

## Pin numbering

The pin number entered in the UI is calculated from the gpiochip index and the line offset:

```text
number = chip_index * 32 + line_offset
```

* Rockchip (Radxa ROCK, ...): this is the vendor GPIO number, `GPIOx_yZ` = `x * 32 + y * 8 + Z` where `y` is `A=0, B=1, C=2, D=3`. Example `GPIO4_B3` = `4 * 32 + 1 * 8 + 3` = `139`.
* Boards with a single `gpiochip0`: the number is the line offset.

Find the chip and line of a physical header pin on the board with:

```shell
gpiofind PIN_7        # -> gpiochip3 19  => 3 * 32 + 19 = 115
gpioinfo gpiochip3    # list all lines of a chip with their names
```

## Features and limitations

| Feature | gpiod |
| - | - |
| Input / output | yes |
| Edge detection (binary sensor events, DHT22, distance sensor) | yes, kernel timestamps |
| Bounce time | yes (kernel debounce) |
| PWM (light, fan, servo) | software PWM (a thread toggles the pin), expect some jitter |
| Pull-up / pull-down | depends on the kernel driver, see below |
| Analog sensor (MCP3xxx over SPI) | **not supported** |

> [!WARNING]
> Some kernel drivers (e.g. Rockchip boards with the vendor kernel) **ignore the software pull-up/pull-down** request. The pin keeps the pull configured in the device tree. When the sensor needs a specific pull, add an external resistor (10kΩ) between the pin and 3.3V (pull-up) or GND (pull-down).

## Force the interface

```yaml
gpio_integration:
  interface: gpiod
```
