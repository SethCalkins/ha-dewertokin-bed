"""Select platform for DewertOkin Bed massage mode."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CMD_MASSAGE_EXIT,
    DOMAIN,
    MASSAGE_MODE_NAMES,
    MASSAGE_MODES,
    cmd_massage_mode,
)
from .coordinator import DewertOkinCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up DewertOkin Bed massage mode select."""
    coordinator: DewertOkinCoordinator = entry.runtime_data
    async_add_entities([DewertOkinMassageModeSelect(coordinator, entry)])


class DewertOkinMassageModeSelect(SelectEntity):
    """Select entity for massage mode (Off/Steady/Pulse/Wave)."""

    _attr_has_entity_name = True
    _attr_options = [name.title() for name in MASSAGE_MODE_NAMES]
    _attr_current_option = "Off"

    def __init__(
        self,
        coordinator: DewertOkinCoordinator,
        entry: ConfigEntry,
    ) -> None:
        self._coordinator = coordinator
        self._attr_unique_id = f"{entry.entry_id}_massage_mode"
        self._attr_name = "Massage Mode"
        self._attr_icon = "mdi:wave"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
            "manufacturer": "DewertOkin",
            "model": "FP2901",
        }

    async def async_select_option(self, option: str) -> None:
        """Set massage mode."""
        key = option.lower()
        mode_flag = MASSAGE_MODES.get(key)

        if mode_flag is None:
            # "off" — exit massage mode
            await self._coordinator.send_motor_command(CMD_MASSAGE_EXIT)
        else:
            await self._coordinator.send_massage_light_command(
                cmd_massage_mode(mode_flag)
            )

        self._attr_current_option = option
        self.async_write_ha_state()
