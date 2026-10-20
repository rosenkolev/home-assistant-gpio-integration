<!-- cspell:ignore Radxa, Armbian, pigpiod, MOSFET -->
# Radxa ROCK 5B / ROCK 5B+

The integration works on the Radxa ROCK 5B and ROCK 5B+ 40-pin header the same way as on a Raspberry Pi. It was tested on a ROCK 5B+ running Armbian with Home Assistant in Docker.

## Setup

1. **Give Home Assistant access to the pins.** Run the Home Assistant container in *privileged* mode (in Docker Compose add `privileged: true` to the Home Assistant service) and recreate the container. Home Assistant OS and Supervised installations need nothing extra.
2. **Install the integration** through HACS or by copying the folder, then restart Home Assistant. Nothing else needs to be installed; `pigpiod` is not used on the Radxa.
3. **Add your devices** under *Settings → Devices & services → Add integration → GPIO Integration*. When asked for a pin, enter the **number** from the table below, not the physical pin position.

The integration detects the Radxa board automatically.

## Which number to enter

Find the physical pin your wire is connected to and enter the number next to it.

| Physical pin | Number to enter | At start-up | Physical pin | Number to enter | At start-up |
| - | - | - | - | - | - |
| 1 | 3.3V power | | 2 | 5V power | |
| 3 | 139 | On | 4 | 5V power | |
| 5 | 138 | On | 6 | Ground | |
| 7 | 115 | Off | 8 | 13 | On |
| 9 | Ground | | 10 | 14 | On |
| 11 | 113 | Off | 12 | 109 | On |
| 13 | 111 | Off | 14 | Ground | |
| 15 | 112 | Off | 16 | 100 | On |
| 17 | 3.3V power | | 18 | 148 | On |
| 19 | 42 | On | 20 | Ground | |
| 21 | 41 | On | 22 | not usable | |
| 23 | 43 | On | 24 | 44 | On |
| 25 | Ground | | 26 | 45 | On |
| 27 | 150 | On | 28 | 149 | On |
| 29 | 35 (5B+) or 63 (5B) | On | 30 | Ground | |
| 31 | 34 (5B+) or 47 (5B) | On | 32 | 114 | Off |
| 33 | 103 | On | 34 | Ground | |
| 35 | 110 | Off | 36 | 105 | Off |
| 37 | 0 | | 38 | 106 | Off |
| 39 | Ground | | 40 | 107 | On |

Check the pin 1 marking printed on the board before wiring.

**At start-up** is the state of an unconnected pin before Home Assistant uses it:

* **Off** pins are the best choice for switches, relays, lights and covers, because they stay off while the board boots. They also suit sensors that switch the pin to 3.3V, such as most motion sensors.
* **On** pins suit buttons and door contacts wired between the pin and Ground.

## Wiring tips

* **Use only 3.3V** on the GPIO pins. Never connect 5V to them; it can permanently damage the pin. Power sensors from pin 1 or 17 (3.3V) unless they need 5V and only send a 3.3V signal.
* **LEDs** need a resistor (220–330Ω) in series. Connect the LED to a GPIO pin and Ground.
* **Relays and motors** must not be powered from a GPIO pin. Use a relay board or a transistor/MOSFET module.

## Supported devices

| Device | Works | Notes |
| - | - | - |
| Switch, relay | Yes | |
| Binary sensor (door, motion, button) | Yes | Choose the pin by its *At start-up* state, see above. The *Invert logic* option can flip the state. |
| Cover | Yes | |
| Light (on/off, dimmable, RGB) | Yes | Dimming may flicker slightly at low brightness. Raise the frequency to 200–500 Hz if it bothers you. |
| Fan | Yes | |
| Servo | Yes | Servos may twitch a little. |
| DHT22 temperature and humidity | Yes | Requires the privileged container (step 1). Power the sensor from 3.3V. |
| Distance sensor | Yes | |
| Analog sensor (MCP3xxx chip) | No | Not supported on the Radxa. |

## Troubleshooting

* **Nothing happens / pin error when adding a device**: check that the container runs privileged (step 1) and that you entered the number from the table, not the physical pin.
* **Binary sensor is always on (or always off)**: the pin's start-up state does not match your wiring. Move the wire to a pin with the other start-up state, or add a 10kΩ resistor from the pin to Ground (to keep it off) or to 3.3V (to keep it on).
* **DHT22 shows 0 or stops updating**: check that it is powered from 3.3V and that the container is privileged. Warnings in the Home Assistant log mention the failed reads.
* **A pin does not respond**: the pin may be used by the operating system (for example by a fan or display overlay in Armbian). Try another pin.
