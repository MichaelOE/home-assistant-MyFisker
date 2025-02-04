"""All binary_sensor entities."""

from homeassistant.helpers.entity import EntityDescription

from . import FiskerButtonEntityDescription

BUTTON_ENTITIES: list[EntityDescription] = [
    FiskerButtonEntityDescription(
        key="doors_unlock",
        name="Unlock doors",
        translation_key="doors_unlock",
        icon="mdi:car-door-lock-open",
        command="doors_unlock",
    ),
    FiskerButtonEntityDescription(
        key="doors_lock",
        name="Lock doors",
        translation_key="doors_lock",
        icon="mdi:car-door-lock",
        command="doors_lock",
    ),
    FiskerButtonEntityDescription(
        key="trunk_open",
        name="Open trunk",
        translation_key="trunk_open",
        icon="mdi:car-back",
        command="trunk_open",
    ),
    FiskerButtonEntityDescription(
        key="trunk_close",
        name="trunk_close",
        translation_key="trunk_close",
        icon="mdi:car-back",
        command="trunk_close",
    ),
    FiskerButtonEntityDescription(
        key="california_mode_on",
        name="california_mode_on",
        translation_key="california_mode",
        icon="mdi:car-convertible",
        command="california_mode",
        command_data="on",
    ),
    FiskerButtonEntityDescription(
        key="california_mode_off",
        name="california_mode_off",
        translation_key="california_mode",
        icon="mdi:car-convertible",
        command="cabin_temperature",
        command_data="off",
    ),
    FiskerButtonEntityDescription(
        key="cabin_temperature",
        name="cabin_temperature",
        translation_key="cabin_temperature",
        icon="mdi:air-conditioner",
        command="cabin_temperature",
        command_data="18",
    ),
]
