"""Number platform for DewertOkin Bed position and vibration controls."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CMD_MASSAGE_ALL_ADD,
    CMD_MASSAGE_ALL_REDUCE,
    CMD_ZONE_SYNC,
    COMMAND_DELAY,
    DOMAIN,
    MAX_MASSAGE_INTENSITY,
    MAX_VIBRATION_LEVEL,
    MIN_MASSAGE_INTENSITY,
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
            "model": "BOX25 Star",
        }
        self._unregister_listener: Callable[[], None] | None = None

    async def async_added_to_hass(self) -> None:
        """Register for status updates when added to HA."""
        self._unregister_listener = self._coordinator.register_status_listener(
            self._on_status_update
        )

    async def async_will_remove_from_hass(self) -> None:
        """Unregister status listener when removed."""
        if self._unregister_listener:
            self._unregister_listener()

    def _on_status_update(self) -> None:
        """Update position from bed notification data."""
        status = self._coordinator.status
        new_value = None
        if self._zone_name == "head" and status.head_position is not None:
            new_value = status.head_position
        elif self._zone_name == "foot" and status.foot_position is not None:
            new_value = status.foot_position
        elif self._zone_name == "core" and status.core_position is not None:
            new_value = status.core_position

        if new_value is not None and new_value != self._attr_native_value:
            self._attr_native_value = new_value
            self.async_write_ha_state()

    async def async_set_native_value(self, value: float) -> None:
        """Move zone to target position."""
        pos = int(value)
        await self._coordinator.send_motor_command_reliable(
            cmd_position(self._zone_id, pos)
        )
        await asyncio.sleep(COMMAND_DELAY)
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
            "model": "BOX25 Star",
        }

    async def async_set_native_value(self, value: float) -> None:
        """Set vibration level, preserving the other zone's current value."""
        level = int(value)
        if self._zone_name == "head":
            self._coordinator.vibration_head = level
        else:
            self._coordinator.vibration_foot = level

        await self._coordinator.send_massage_light_command_reliable(
            cmd_vibration(
                self._coordinator.vibration_head,
                self._coordinator.vibration_foot,
            )
        )
        self._attr_native_value = level
        self.async_write_ha_state()


class DewertOkinMassageIntensityNumber(NumberEntity):
    """Massage intensity (1-7). Uses step commands to reach target level."""

    _attr_has_entity_name = True
    _attr_native_min_value = MIN_MASSAGE_INTENSITY
    _attr_native_max_value = MAX_MASSAGE_INTENSITY
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
        self._attr_native_value = MIN_MASSAGE_INTENSITY
        self._current_level = MIN_MASSAGE_INTENSITY
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
            "manufacturer": "DewertOkin",
            "model": "BOX25 Star",
        }

    async def async_set_native_value(self, value: float) -> None:
        """Set massage intensity by stepping from current to target level."""
        target = max(MIN_MASSAGE_INTENSITY, min(MAX_MASSAGE_INTENSITY, int(value)))
        diff = target - self._current_level

        if diff > 0:
            for _ in range(diff):
                await self._coordinator.send_massage_light_command_reliable(
                    CMD_MASSAGE_ALL_ADD
                )
                await asyncio.sleep(COMMAND_DELAY)
        elif diff < 0:
            for _ in range(abs(diff)):
                await self._coordinator.send_massage_light_command_reliable(
                    CMD_MASSAGE_ALL_REDUCE
                )
                await asyncio.sleep(COMMAND_DELAY)

        self._current_level = target
        self._attr_native_value = target
        self.async_write_ha_state()
