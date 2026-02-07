"""Button platform for DewertOkin Bed presets."""

from __future__ import annotations

import asyncio
import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CMD_MOTOR_STOP, DOMAIN, PRESETS
from .coordinator import DewertOkinCoordinator

_LOGGER = logging.getLogger(__name__)

PRESET_DISPLAY_NAMES = {
    "flat": "Flat",
    "zero_gravity": "Zero Gravity",
    "relax": "Relax",
    "ascent": "Ascent",
    "anti_snore": "Anti Snore",
}

PRESET_ICONS = {
    "flat": "mdi:bed-outline",
    "zero_gravity": "mdi:yoga",
    "relax": "mdi:sofa-outline",
    "ascent": "mdi:seat-recline-extra",
    "anti_snore": "mdi:sleep",
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up DewertOkin Bed preset buttons."""
    coordinator: DewertOkinCoordinator = entry.runtime_data
    async_add_entities(
        DewertOkinPresetButton(coordinator, entry, key)
        for key in PRESETS
    )


class DewertOkinPresetButton(ButtonEntity):
    """A preset button for the DewertOkin bed."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: DewertOkinCoordinator,
        entry: ConfigEntry,
        preset_key: str,
    ) -> None:
        self._coordinator = coordinator
        self._preset_key = preset_key
        self._attr_unique_id = f"{entry.entry_id}_{preset_key}"
        self._attr_name = PRESET_DISPLAY_NAMES[preset_key]
        self._attr_icon = PRESET_ICONS.get(preset_key, "mdi:bed")
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
            "manufacturer": "DewertOkin",
            "model": "FP2901",
        }

    async def async_press(self) -> None:
        """Send preset command + confirm."""
        cmd = PRESETS[self._preset_key]
        await self._coordinator.send_motor_command(cmd)
        await asyncio.sleep(0.1)
        await self._coordinator.send_motor_command(CMD_MOTOR_STOP)
