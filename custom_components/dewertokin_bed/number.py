"""Number platform for DewertOkin Bed position and vibration controls."""

from __future__ import annotations

import asyncio
import logging

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CMD_ZONE_SYNC,
    DOMAIN,
    MAX_VIBRATION_LEVEL,
    ZONE_CORE,
    ZONE_FOOT,
    ZONE_HEAD,
    cmd_position,
    cmd_vibration,
)
from .coordinator import DewertOkinCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up DewertOkin Bed number entities."""
    coordinator: DewertOkinCoordinator = entry.runtime_data
    async_add_entities([
        DewertOkinPositionNumber(coordinator, entry, "head", ZONE_HEAD),
        DewertOkinPositionNumber(coordinator, entry, "foot", ZONE_FOOT),
        DewertOkinPositionNumber(coordinator, entry, "core", ZONE_CORE),
        DewertOkinVibrationNumber(coordinator, entry, "head"),
        DewertOkinVibrationNumber(coordinator, entry, "foot"),
        DewertOkinMassageIntensityNumber(coordinator, entry),
    ])


class DewertOkinPositionNumber(NumberEntity):
    """Position slider for a bed zone (0-100)."""

    _attr_has_entity_name = True
    _attr_native_min_value = 0
    _attr_native_max_value = 100
    _attr_native_step = 1
    _attr_mode = NumberMode.SLIDER

    def __init__(
        self,
        coordinator: DewertOkinCoordinator,
        entry: ConfigEntry,
        zone_name: str,
        zone_id: int,
    ) -> None:
        self._coordinator = coordinator
        self._zone_name = zone_name
        self._zone_id = zone_id
        self._attr_unique_id = f"{entry.entry_id}_position_{zone_name}"
        self._attr_name = f"{zone_name.title()} Position"
        self._attr_icon = "mdi:arrow-up-down"
        self._attr_native_value = 0
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
            "manufacturer": "DewertOkin",
            "model": "FP2901",
        }

    async def async_set_native_value(self, value: float) -> None:
        """Move zone to target position."""
        pos = int(value)
        await self._coordinator.send_motor_command(cmd_position(self._zone_id, pos))
        await asyncio.sleep(0.05)
        await self._coordinator.send_motor_command(CMD_ZONE_SYNC)
        self._attr_native_value = pos
        self.async_write_ha_state()


class DewertOkinVibrationNumber(NumberEntity):
    """Vibration level for a zone (0-8). Uses shared state on coordinator."""

    _attr_has_entity_name = True
    _attr_native_min_value = 0
    _attr_native_max_value = MAX_VIBRATION_LEVEL
    _attr_native_step = 1
    _attr_mode = NumberMode.SLIDER

    def __init__(
        self,
        coordinator: DewertOkinCoordinator,
        entry: ConfigEntry,
        zone_name: str,
    ) -> None:
        self._coordinator = coordinator
        self._zone_name = zone_name
        self._attr_unique_id = f"{entry.entry_id}_vibration_{zone_name}"
        self._attr_name = f"Vibration {zone_name.title()}"
        self._attr_icon = "mdi:vibrate"
        self._attr_native_value = 0
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
            "manufacturer": "DewertOkin",
            "model": "FP2901",
        }

    async def async_set_native_value(self, value: float) -> None:
        """Set vibration level, preserving the other zone's current value."""
        level = int(value)
        if self._zone_name == "head":
            self._coordinator.vibration_head = level
        else:
            self._coordinator.vibration_foot = level

        await self._coordinator.send_massage_light_command(
            cmd_vibration(
                self._coordinator.vibration_head,
                self._coordinator.vibration_foot,
            )
        )
        self._attr_native_value = level
        self.async_write_ha_state()


class DewertOkinMassageIntensityNumber(NumberEntity):
    """Massage intensity (1-7 maps to protocol 2-8, both zones)."""

    _attr_has_entity_name = True
    _attr_native_min_value = 1
    _attr_native_max_value = 7
    _attr_native_step = 1
    _attr_mode = NumberMode.SLIDER

    def __init__(
        self,
        coordinator: DewertOkinCoordinator,
        entry: ConfigEntry,
    ) -> None:
        self._coordinator = coordinator
        self._attr_unique_id = f"{entry.entry_id}_massage_intensity"
        self._attr_name = "Massage Intensity"
        self._attr_icon = "mdi:sine-wave"
        self._attr_native_value = 1
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
            "manufacturer": "DewertOkin",
            "model": "FP2901",
        }

    async def async_set_native_value(self, value: float) -> None:
        """Set massage intensity. UI 1-7 maps to protocol 2-8."""
        ui_level = int(value)
        protocol_level = ui_level + 1  # UI 1 -> protocol 2, UI 7 -> protocol 8
        await self._coordinator.send_massage_light_command(
            cmd_vibration(protocol_level, protocol_level)
        )
        self._attr_native_value = ui_level
        self.async_write_ha_state()
