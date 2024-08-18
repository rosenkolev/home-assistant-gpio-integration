# Home Assistant Raspberry Pi GPIO custom integration

The `gpio_integration` integration supports the following platforms: Binary Sensor, Cover (ON/OFF and toggle), Switch

**Note:** The `port` refers to the GPIO number, not the pin number. See the [Wikipedia article about the Raspberry Pi](https://en.wikipedia.org/wiki/Raspberry_Pi#General_purpose_input-output_(GPIO)_connector) for more details about the GPIO layout.

## Installation

### HACS

The recommend way to install `gpio_integration` is through [HACS](https://hacs.xyz/).

### Manual installation

Copy the `gpio_integration` folder and all of its contents into your Home Assistant's 
`custom_components` folder. This folder is usually inside your `/config` 
folder. If you are running Hass.io, use SAMBA to copy the folder over. You 
may need to create the `custom_components` folder and then copy the `gpio_integration` 
folder and all of its contents into it.

## Usage

### Binary Sensor

The `gpio_integration` binary sensor platform allows you to read sensor values of the GPIOs of your device.  

### Configuration

Use the UI
