"""DewertOkin Bed integration for Home Assistant."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ADDRESS, Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import DewertOkinCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.LIGHT,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
]

type DewertOkinConfigEntry = ConfigEntry[DewertOkinCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: DewertOkinConfigEntry) -> bool:
    """Set up DewertOkin Bed from a config entry."""
    address: str = entry.data[CONF_ADDRESS]
    coordinator = DewertOkinCoordinator(hass, address, entry.title)
    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: DewertOkinConfigEntry
) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        coordinator: DewertOkinCoordinator = entry.runtime_data
        await coordinator.disconnect()
    return unload_ok
