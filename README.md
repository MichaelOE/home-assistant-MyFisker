# Fisker Ocean component for Home Assistant
[![BuyMeCoffee][buymecoffeebadge]][michaelo-buymecoffee]

**Currently inactive due to Fisker inc. has shut down API server (still down in Europe).
If/when this comes back online, the integration will be as well.**

Custom component for getting information about your Fisker Ocean presented in Home Assistant.

# Features
- Provides sensors for various part of the vehicle

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
The integration currently only supports reading of values.
It is possible I will add 'commands' to the vehicle in the future.

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

I have used apexchart for visualization.
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
