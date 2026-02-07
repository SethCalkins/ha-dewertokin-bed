"""Switch platform for DewertOkin Bed massage power toggle."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CMD_MASSAGE_EXIT, DOMAIN, MASSAGE_MODES, cmd_massage_mode
from .coordinator import DewertOkinCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up DewertOkin Bed massage switch."""
    coordinator: DewertOkinCoordinator = entry.runtime_data
    async_add_entities([DewertOkinMassageSwitch(coordinator, entry)])


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
            "model": "FP2901",
        }

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on massage (defaults to Steady mode)."""
        await self._coordinator.send_massage_light_command(
            cmd_massage_mode(MASSAGE_MODES["steady"])
        )
        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off massage."""
        await self._coordinator.send_motor_command(CMD_MASSAGE_EXIT)
        self._attr_is_on = False
        self.async_write_ha_state()
