"""Light platform for DewertOkin Bed under-bed lighting."""

from __future__ import annotations

import math
from typing import Any

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_RGB_COLOR,
    ColorMode,
    LightEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    LIGHT_COLOR_RGB,
    LIGHT_COLORS,
    MAX_BRIGHTNESS_LEVEL,
    MIN_BRIGHTNESS_LEVEL,
    cmd_light_brightness,
    cmd_light_color,
)
from .coordinator import DewertOkinCoordinator

# Pre-compute list of (name, value, r, g, b) for nearest-color matching
_COLOR_TABLE = [
    (name, value, *LIGHT_COLOR_RGB[name])
    for name, value in LIGHT_COLORS.items()
]


def _nearest_color(r: int, g: int, b: int) -> tuple[str, int]:
    """Find the nearest available bed color to an RGB value."""
    best_name = "white"
    best_value = 0x01
    best_dist = float("inf")
    for name, value, cr, cg, cb in _COLOR_TABLE:
        dist = math.sqrt((r - cr) ** 2 + (g - cg) ** 2 + (b - cb) ** 2)
        if dist < best_dist:
            best_dist = dist
            best_name = name
            best_value = value
    return best_name, best_value


def _ha_brightness_to_level(brightness: int) -> int:
    """Convert HA brightness (1-255) to bed level (1-6)."""
    # Map 1-255 linearly to 1-6
    level = round(brightness / 255 * MAX_BRIGHTNESS_LEVEL)
    return max(MIN_BRIGHTNESS_LEVEL, min(MAX_BRIGHTNESS_LEVEL, level))


def _level_to_ha_brightness(level: int) -> int:
    """Convert bed level (1-6) to HA brightness (1-255)."""
    return round(level / MAX_BRIGHTNESS_LEVEL * 255)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up DewertOkin Bed light."""
    coordinator: DewertOkinCoordinator = entry.runtime_data
    async_add_entities([DewertOkinBedLight(coordinator, entry)])


class DewertOkinBedLight(LightEntity):
    """Light entity for DewertOkin bed LED strip."""

    _attr_has_entity_name = True
    _attr_supported_color_modes = {ColorMode.RGB}
    _attr_color_mode = ColorMode.RGB

    def __init__(
        self,
        coordinator: DewertOkinCoordinator,
        entry: ConfigEntry,
    ) -> None:
        self._coordinator = coordinator
        self._attr_unique_id = f"{entry.entry_id}_light"
        self._attr_name = "Bed Light"
        self._attr_is_on = False
        self._attr_brightness = 255  # Default max
        self._attr_rgb_color = (255, 255, 255)  # Default white
        self._current_color_name = "white"
        self._current_color_value = 0x01
        self._current_brightness_level = MAX_BRIGHTNESS_LEVEL
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
            "manufacturer": "DewertOkin",
            "model": "FP2901",
        }

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the light with optional color/brightness."""
        if ATTR_RGB_COLOR in kwargs:
            r, g, b = kwargs[ATTR_RGB_COLOR]
            self._current_color_name, self._current_color_value = _nearest_color(
                r, g, b
            )
            self._attr_rgb_color = LIGHT_COLOR_RGB[self._current_color_name]

        if ATTR_BRIGHTNESS in kwargs:
            ha_brightness = kwargs[ATTR_BRIGHTNESS]
            self._current_brightness_level = _ha_brightness_to_level(ha_brightness)
            self._attr_brightness = _level_to_ha_brightness(
                self._current_brightness_level
            )

        # Send color command (turns light on)
        await self._coordinator.send_massage_light_command(
            cmd_light_color(self._current_color_value)
        )

        # Send brightness if not max (max is default on turn-on)
        if self._current_brightness_level < MAX_BRIGHTNESS_LEVEL:
            await self._coordinator.send_massage_light_command(
                cmd_light_brightness(self._current_brightness_level)
            )

        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the light."""
        await self._coordinator.send_massage_light_command(cmd_light_color(0))
        self._attr_is_on = False
        self.async_write_ha_state()
