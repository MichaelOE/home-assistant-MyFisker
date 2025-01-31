# Fisker Ocean component for Home Assistant
[![BuyMeCoffee][buymecoffeebadge]][michaelo-buymecoffee]

Custom component for getting information about your Fisker Ocean presented in Home Assistant.

## Target
The project is meant to get all available sensor values from Fisker Ocean cars.

## Method
I reverse engineered the api used together with the official 'My Fisker' mobile app.
Utilizing this, I then at regularly intervals poll the cloud service for the cars digital twin.

## Sensors
All values exposed by the cloud api are available as sensors in Home Assistant.

# Features
The buttons available in the official app, is also available in this integration as 'buttons'.

<img src="https://github.com/MichaelOE/home-assistant-MyFisker/assets/37800126/55d11a02-86ec-48ad-978b-2ea01c27f41f" width="400" title="Screenshot"/>
<img src="https://github.com/MichaelOE/home-assistant-MyFisker/assets/37800126/a57eb9a7-2d01-4fdc-a29f-da1f757878e1" width="400" title="Screenshot"/>

# Installation and setup
This integration can be installed through HACS.

Alternatively, you can get the custom repository here: https://github.com/MichaelOE/home-assistant-MyFisker

## Setup
- Username: The same as you use in your 'My Fisker'
- Password: The same as you use in your 'My Fisker'
- Region: Select your region, used to determine the datacenter URL
- Alias: Prefix, which is used on all entity names created by the integration

# Usage
For showing the vehicle on a map, this can be used:

```python
alias: Fisker Ocean update location
description: ""
trigger:
  - platform: state
    entity_id:
      - sensor.fisker_location_latitude
      - sensor.fisker_location_longitude
condition: []
action:
  - service: device_tracker.see
    metadata: {}
    data:
      dev_id: my_fisker_location
      gps:
        - "{{ states('sensor.fisker_location_latitude') }}"
        - "{{ states('sensor.fisker_location_longitude') }}"
mode: single
```

I have used [apexchart](https://github.com/RomRider/apexcharts-card) for visualization.
In the screenshot above showing remaining range/battery I used the following (note the 'battery-calculation', which is because Fisker API sometimes returns zero miles):

```python
type: custom:apexcharts-card
apex_config:
  chart:
    height: 250px
    toolbar:
      show: true
      tools:
        selection: true
        download: false
        zoom: false
        zoomin: true
        zoomout: true
        pan: true
        reset: true
    zoom:
      enabled: true
header:
  show: true
  title: Rækkevidde
  colorize_states: true
  show_states: true
graph_span: 24h
yaxis:
  - id: range
    min: 0
    max: 700
    apex_config:
      tickAmount: 10
  - id: battery
    opposite: true
    min: 0
    max: 100
    apex_config:
      tickAmount: 10
series:
  - entity: sensor.fisker_battery_max_miles
    transform: 'return x == 0 ? null : x;'
    extend_to: false
    yaxis_id: range
    fill_raw: last
    stroke_width: 2
  - entity: sensor.fisker_battery_percent
    yaxis_id: battery
    fill_raw: last
    stroke_width: 2
```

# Known issues
- Currently only supports one vehicle per account
- Battery range sometimes reported as 0 (zero) from the Fisker API
- Battery / range is reported without decimals, making trip stats unprecise at shorter trips


[buymecoffeebadge]: https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png
[michaelo-buymecoffee]: https://www.buymeacoffee.com/michaelo
