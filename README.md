# Ocean Pulse – Fisker Ocean custom integration for Home Assistant

[![BuyMeCoffee][buymecoffeebadge]][michaeloe-buymecoffee]

> Formerly **My Fisker**  
> Home Assistant integration for **Fisker Ocean** vehicles using the **Ocean Pulse** aftermarket device.

## ⚠️ Still alpha - I don't have a Pulse yet (I'm in DK), so still using test-connections etc. NOT YET FULLY FUNCTIONAL
Please be patient - When Pulse is available in EU (hopefully early fall 2026 🤞🤷‍♂️) this will be be updated ASAP as well.


## ⚠️ Breaking change (June 2026)

This integration has been renamed from **My Fisker** to **Ocean Pulse** and now uses the **Ocean Pulse device API**.

If you previously used **My Fisker** in HACS:

1. Uninstall **My Fisker**
2. Install **Ocean Pulse**
3. Reconfigure the integration

Entity names and sensor IDs have changed significantly.

## Target

The project provides sensor data from **Fisker Ocean** vehicles through the **Ocean Pulse** device for use in Home Assistant.

## Method
At regularly intervals poll the cloud service for updated values.

## Sensors
All values exposed by the cloud api are available as sensors in Home Assistant.

# Features
Currently only sensor values are present

# Installation and setup
This integration can be installed through HACS.

Alternatively, you can get the custom repository here: https://github.com/MichaelOE/homeassistant-ocean_pulse

## Setup
- QR code: Enter QR code digits to connect to cloud
- Alias: Prefix, which is used on all entity names created by the integration

# Known issues
- n/a
