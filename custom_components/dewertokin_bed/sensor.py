"""Sensor platform for DewertOkin Bed diagnostics."""

from __future__ import annotations

from collections.abc import Callable

from homeassistant.components.sensor import SensorEntity
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
    """Set up DewertOkin Bed sensor entities."""
    coordinator: DewertOkinCoordinator = entry.runtime_data
    async_add_entities([
        DewertOkinConnectionStateSensor(coordinator, entry),
        DewertOkinLastNotificationSensor(coordinator, entry),
    ])


class DewertOkinConnectionStateSensor(SensorEntity):
    """Shows current BLE connection state."""

    _attr_has_entity_name = True
    _attr_entity_category = "diagnostic"

    def __init__(
        self,
        coordinator: DewertOkinCoordinator,
        entry: ConfigEntry,
    ) -> None:
        self._coordinator = coordinator
        self._attr_unique_id = f"{entry.entry_id}_connection_state"
        self._attr_name = "Connection"
        self._attr_icon = "mdi:bluetooth-connect"
        self._attr_native_value = "disconnected"
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
        """Update connection state."""
        new_state = self._coordinator.connection_state.value
        if new_state != self._attr_native_value:
            self._attr_native_value = new_state
            self.async_write_ha_state()


class DewertOkinLastNotificationSensor(SensorEntity):
    """Shows the last raw notification data from the bed (for debugging)."""

    _attr_has_entity_name = True
    _attr_entity_category = "diagnostic"
    _attr_entity_registry_enabled_default = False

    def __init__(
        self,
        coordinator: DewertOkinCoordinator,
        entry: ConfigEntry,
    ) -> None:
        self._coordinator = coordinator
        self._attr_unique_id = f"{entry.entry_id}_last_notification"
        self._attr_name = "Last Notification"
        self._attr_icon = "mdi:message-text-outline"
        self._attr_native_value = None
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
        """Update with last notification hex data."""
        raw = self._coordinator.status.raw_data
        if raw:
            hex_str = raw.hex()
            if hex_str != self._attr_native_value:
                self._attr_native_value = hex_str
                self.async_write_ha_state()
