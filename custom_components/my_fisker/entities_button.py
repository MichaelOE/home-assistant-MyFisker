"""All binary_sensor entities."""

from homeassistant.helpers.entity import EntityDescription

from . import FiskerButtonEntityDescription

BUTTON_ENTITIES: list[EntityDescription] = [
    FiskerButtonEntityDescription(
        key="doors_unlock",
        name="doors_unlock",
        translation_key="doors_unlock",
        icon="mdi:car-door-lock-open",
    ),
    FiskerButtonEntityDescription(
        key="doors_lock",
        name="doors_lock",
        translation_key="doors_lock",
        icon="mdi:car-door-lock",
    ),
    FiskerButtonEntityDescription(
        key="trunk_open",
        name="trunk_open",
        translation_key="doors_lock",
        icon="mdi:play-circle-outline",
    ),
    FiskerButtonEntityDescription(
        key="trunk_close",
        name="trunk_close",
        translation_key="doors_lock",
        icon="mdi:play-circle-outline",
    ),
]
