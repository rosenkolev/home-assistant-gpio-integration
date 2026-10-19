<!-- cspell:ignore gpiod, libgpiod, gpiochip, gpioget, gpiofind, Radxa, Rockchip, Armbian, SARADC, UART -->
# Radxa ROCK 5B / ROCK 5B+

Supported through the [`gpiod` interface](./BOARDS.md). Tested on ROCK 5B+ with Armbian (kernel `6.1 vendor-rk35xx`) and Home Assistant container.

## Pin numbers

Use the Rockchip **GPIO number** (the `GPIO` column) in the integration UI.

| Physical pin | GPIO number | GPIO name | Default level (unconnected) | Functions |
| - | - | - | - | - |
| 3 | 139 | GPIO4_B3 | HIGH (I2C pull-up) | I2C7_SDA, PWM15 |
| 5 | 138 | GPIO4_B2 | HIGH (I2C pull-up) | I2C7_SCL, PWM14 |
| 7 | 115 | GPIO3_C3 | LOW | SPI1_CS1, PWM15 |
| 8 | 13 | GPIO0_B5 | HIGH | UART2_TX |
| 10 | 14 | GPIO0_B6 | HIGH | UART2_RX |
| 11 | 113 | GPIO3_C1 | LOW | SPI1_CLK |
| 12 | 109 | GPIO3_B5 | HIGH | PWM12 |
| 13 | 111 | GPIO3_B7 | LOW | SPI1_MOSI |
| 15 | 112 | GPIO3_C0 | LOW | SPI1_MISO |
| 16 | 100 | GPIO3_A4 | HIGH | |
| 18 | 148 | GPIO4_C4 | HIGH | PWM5 |
| 19 | 42 | GPIO1_B2 | HIGH | SPI0_MOSI |
| 21 | 41 | GPIO1_B1 | HIGH | SPI0_MISO |
| 22 | - | SARADC_IN4 | - | analog input, not a GPIO |
| 23 | 43 | GPIO1_B3 | HIGH | SPI0_CLK |
| 24 | 44 | GPIO1_B4 | HIGH | SPI0_CS0 |
| 26 | 45 | GPIO1_B5 | HIGH | SPI0_CS1 |
| 27 | 150 | GPIO4_C6 | HIGH | I2C0_SDA, PWM7 |
| 28 | 149 | GPIO4_C5 | HIGH | I2C0_SCL, PWM6 |
| 29 | 35 (5B+) / 63 (5B) | GPIO1_A3 (5B+) / GPIO1_D7 (5B) | HIGH | PWM1 (5B+) |
| 31 | 34 (5B+) / 47 (5B) | GPIO1_A2 (5B+) / GPIO1_B7 (5B) | HIGH | PWM0 (5B+) |
| 32 | 114 | GPIO3_C2 | LOW | PWM14, SPI1_CS0 |
| 33 | 103 | GPIO3_A7 | HIGH | PWM8 |
| 35 | 110 | GPIO3_B6 | LOW | PWM13 |
| 36 | 105 | GPIO3_B1 | LOW | PWM2 |
| 37 | 0 | GPIO0_A0 | | |
| 38 | 106 | GPIO3_B2 | LOW | PWM3 |
| 40 | 107 | GPIO3_B3 | HIGH | |

Pins 1, 17 = 3.3V; 2, 4 = 5V; 6, 9, 14, 20, 25, 30, 34, 39 = GND.

The "Default level" column is the value read on an unconnected pin (`gpioget`) with Armbian; it shows the pull configured by the device tree. Source of the pin functions: [Radxa ROCK 5B hardware interface](https://docs.radxa.com/en/rock5/rock5b/hardware-design/hardware-interface).

The number can be verified on the board:

```shell
gpiofind PIN_16   # -> gpiochip3 4  => 3 * 32 + 4 = 100
```

## Limitations

* **Pull-up / pull-down**: the Rockchip kernel driver ignores the software pull request. A binary sensor on a pin with a HIGH default level reads `on` when the circuit is open, unless an external pull-down resistor (10kΩ to GND) is used. Pick a pin with the correct default level or add the resistor.
* **PWM** is generated in software (light, fan, servo). Servo jitter is higher than with hardware PWM.
* **Analog sensor** (MCP3xxx over SPI) is not supported.
* PWM pins driven by the fan overlay (`pwm-fan`) or other overlays cannot be used by the integration.

## Home Assistant container

The container must have access to the GPIO devices, for example with docker compose:

```yaml
services:
  home-assistant:
    image: ghcr.io/home-assistant/home-assistant:stable
    privileged: true   # or map /dev/gpiochip0 .. /dev/gpiochip4 with "devices:"
```
