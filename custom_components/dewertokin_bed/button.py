"""Button platform for DewertOkin Bed presets and memory positions."""

from __future__ import annotations

import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, MEMORY_RECALL, MEMORY_STORE, PRESETS
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
    """Set up DewertOkin Bed preset and memory buttons."""
    coordinator: DewertOkinCoordinator = entry.runtime_data
    entities: list[ButtonEntity] = []

    # Preset buttons
    entities.extend(
        DewertOkinPresetButton(coordinator, entry, key) for key in PRESETS
    )

    # Memory recall buttons (1-4)
    for slot in MEMORY_RECALL:
        entities.append(DewertOkinMemoryRecallButton(coordinator, entry, slot))

    # Memory store buttons (1-4)
    for slot in MEMORY_STORE:
        entities.append(DewertOkinMemoryStoreButton(coordinator, entry, slot))

    async_add_entities(entities)


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
            "model": "BOX25 Star",
        }

    async def async_press(self) -> None:
        """Send preset command with confirmation."""
        cmd = PRESETS[self._preset_key]
        await self._coordinator.send_preset_command(cmd)


class DewertOkinMemoryRecallButton(ButtonEntity):
    """Recall a saved memory position (1-4)."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: DewertOkinCoordinator,
        entry: ConfigEntry,
        slot: int,
    ) -> None:
        self._coordinator = coordinator
        self._slot = slot
        self._attr_unique_id = f"{entry.entry_id}_memory_recall_{slot}"
        self._attr_name = f"Memory {slot}"
        self._attr_icon = "mdi:bookmark-outline"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
            "manufacturer": "DewertOkin",
            "model": "BOX25 Star",
        }

    async def async_press(self) -> None:
        """Recall memory position."""
        cmd = MEMORY_RECALL[self._slot]
        await self._coordinator.send_preset_command(cmd)


class DewertOkinMemoryStoreButton(ButtonEntity):
    """Store current position to a memory slot (1-4)."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: DewertOkinCoordinator,
        entry: ConfigEntry,
        slot: int,
    ) -> None:
        self._coordinator = coordinator
        self._slot = slot
        self._attr_unique_id = f"{entry.entry_id}_memory_store_{slot}"
        self._attr_name = f"Save Memory {slot}"
        self._attr_icon = "mdi:bookmark-plus-outline"
        self._attr_entity_category = "config"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
            "manufacturer": "DewertOkin",
            "model": "BOX25 Star",
        }

    async def async_press(self) -> None:
        """Store current position to memory slot."""
        cmd = MEMORY_STORE[self._slot]
        await self._coordinator.send_motor_command_reliable(cmd)
