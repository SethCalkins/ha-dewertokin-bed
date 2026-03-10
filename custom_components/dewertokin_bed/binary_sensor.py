"""Binary sensor platform for DewertOkin Bed status."""

from __future__ import annotations

from collections.abc import Callable

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import DewertOkinCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up DewertOkin Bed binary sensor entities."""
    coordinator: DewertOkinCoordinator = entry.runtime_data
    async_add_entities([
        DewertOkinConnectedSensor(coordinator, entry),
        DewertOkinMovingSensor(coordinator, entry),
    ])


class DewertOkinConnectedSensor(BinarySensorEntity):
    """Binary sensor showing BLE connection status."""

    _attr_has_entity_name = True
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_entity_category = "diagnostic"

    def __init__(
        self,
        coordinator: DewertOkinCoordinator,
        entry: ConfigEntry,
    ) -> None:
        self._coordinator = coordinator
        self._attr_unique_id = f"{entry.entry_id}_connected"
        self._attr_name = "Connected"
        self._attr_is_on = False
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
            "manufacturer": "DewertOkin",
            "model": "BOX25 Star",
        }
        self._unregister_listener: Callable[[], None] | None = None

    async def async_added_to_hass(self) -> None:
        """Register for status updates."""
        self._unregister_listener = self._coordinator.register_status_listener(
            self._on_status_update
        )

    async def async_will_remove_from_hass(self) -> None:
        """Unregister listener."""
        if self._unregister_listener:
            self._unregister_listener()

    def _on_status_update(self) -> None:
        """Update connection status."""
        new_state = self._coordinator.connected
        if new_state != self._attr_is_on:
            self._attr_is_on = new_state
            self.async_write_ha_state()


class DewertOkinMovingSensor(BinarySensorEntity):
    """Binary sensor showing if the bed is currently moving."""

    _attr_has_entity_name = True
    _attr_device_class = BinarySensorDeviceClass.MOVING

    def __init__(
        self,
        coordinator: DewertOkinCoordinator,
        entry: ConfigEntry,
    ) -> None:
        self._coordinator = coordinator
        self._attr_unique_id = f"{entry.entry_id}_moving"
        self._attr_name = "Moving"
        self._attr_is_on = False
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
            "manufacturer": "DewertOkin",
            "model": "BOX25 Star",
        }
        self._unregister_listener: Callable[[], None] | None = None

    async def async_added_to_hass(self) -> None:
        """Register for status updates."""
        self._unregister_listener = self._coordinator.register_status_listener(
            self._on_status_update
        )

    async def async_will_remove_from_hass(self) -> None:
        """Unregister listener."""
        if self._unregister_listener:
            self._unregister_listener()

    def _on_status_update(self) -> None:
        """Update moving status from bed notifications."""
        new_state = self._coordinator.status.is_moving
        if new_state != self._attr_is_on:
            self._attr_is_on = new_state
            self.async_write_ha_state()
