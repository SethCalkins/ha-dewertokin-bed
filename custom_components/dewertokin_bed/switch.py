"""Switch platform for DewertOkin Bed massage and motion sensor toggles."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CMD_MASSAGE_EXIT,
    CMD_MOTION_SENSOR_OFF,
    CMD_MOTION_SENSOR_ON,
    DOMAIN,
    MASSAGE_MODES,
    cmd_massage_mode,
)
from .coordinator import DewertOkinCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up DewertOkin Bed switches."""
    coordinator: DewertOkinCoordinator = entry.runtime_data
    async_add_entities([
        DewertOkinMassageSwitch(coordinator, entry),
        DewertOkinMotionSensorSwitch(coordinator, entry),
    ])


class DewertOkinMassageSwitch(SwitchEntity):
    """Toggle for massage subsystem power."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: DewertOkinCoordinator,
        entry: ConfigEntry,
    ) -> None:
        self._coordinator = coordinator
        self._attr_unique_id = f"{entry.entry_id}_massage_power"
        self._attr_name = "Massage"
        self._attr_icon = "mdi:vibrate"
        self._attr_is_on = False
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
            "manufacturer": "DewertOkin",
            "model": "BOX25 Star",
        }

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on massage (defaults to Wave 1 mode)."""
        await self._coordinator.send_massage_light_command_reliable(
            cmd_massage_mode(MASSAGE_MODES["wave_1"])
        )
        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off massage."""
        await self._coordinator.send_motor_command_reliable(CMD_MASSAGE_EXIT)
        self._attr_is_on = False
        self.async_write_ha_state()


class DewertOkinMotionSensorSwitch(SwitchEntity):
    """Toggle for under-bed motion sensor (auto-light on movement)."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: DewertOkinCoordinator,
        entry: ConfigEntry,
    ) -> None:
        self._coordinator = coordinator
        self._attr_unique_id = f"{entry.entry_id}_motion_sensor"
        self._attr_name = "Motion Sensor"
        self._attr_icon = "mdi:motion-sensor"
        self._attr_is_on = False
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
            "manufacturer": "DewertOkin",
            "model": "BOX25 Star",
        }

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Enable motion sensor."""
        await self._coordinator.send_massage_light_command_reliable(
            CMD_MOTION_SENSOR_ON
        )
        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Disable motion sensor."""
        await self._coordinator.send_massage_light_command_reliable(
            CMD_MOTION_SENSOR_OFF
        )
        self._attr_is_on = False
        self.async_write_ha_state()
