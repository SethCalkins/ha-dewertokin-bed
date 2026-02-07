"""BLE connection coordinator for DewertOkin Bed."""

from __future__ import annotations

import asyncio
import logging
from bleak import BleakClient
from bleak.exc import BleakError
from bleak_retry_connector import establish_connection

from homeassistant.components import bluetooth
from homeassistant.core import HomeAssistant, callback

from .const import (
    CMD_MASSAGE_LIGHT_INIT,
    CMD_MOTOR_INIT,
    DISCONNECT_DELAY,
    WRITE_CHAR_UUID,
)

_LOGGER = logging.getLogger(__name__)


class DewertOkinCoordinator:
    """Manages BLE connection to a DewertOkin bed."""

    def __init__(self, hass: HomeAssistant, address: str, name: str) -> None:
        self.hass = hass
        self.address = address
        self.name = name
        self._client: BleakClient | None = None
        self._lock = asyncio.Lock()
        self._disconnect_timer: asyncio.TimerHandle | None = None
        self._motor_initialized = False
        self._massage_initialized = False
        # Shared vibration state so head/foot entities can send paired commands
        self.vibration_head: int = 0
        self.vibration_foot: int = 0

    @property
    def connected(self) -> bool:
        return self._client is not None and self._client.is_connected

    async def _ensure_connected(self) -> BleakClient:
        """Connect if not already connected, return client."""
        if self.connected:
            assert self._client is not None
            return self._client

        _LOGGER.debug("Connecting to %s (%s)", self.name, self.address)

        device = bluetooth.async_ble_device_from_address(
            self.hass, self.address, connectable=True
        )
        if device is None:
            raise BleakError(
                f"Could not find BLE device {self.address} via proxy"
            )

        self._client = await establish_connection(
            BleakClient,
            device,
            self.name,
            disconnected_callback=self._on_disconnect,
        )
        self._motor_initialized = False
        self._massage_initialized = False
        _LOGGER.info("Connected to %s", self.name)
        return self._client

    @callback
    def _on_disconnect(self, client: BleakClient) -> None:
        _LOGGER.info("Disconnected from %s", self.name)
        self._client = None
        self._motor_initialized = False
        self._massage_initialized = False

    def _reset_disconnect_timer(self) -> None:
        if self._disconnect_timer is not None:
            self._disconnect_timer.cancel()
        self._disconnect_timer = self.hass.loop.call_later(
            DISCONNECT_DELAY, lambda: asyncio.ensure_future(self._idle_disconnect())
        )

    async def _idle_disconnect(self) -> None:
        async with self._lock:
            if self.connected and self._client:
                _LOGGER.debug("Idle timeout, disconnecting from %s", self.name)
                await self._client.disconnect()

    async def send_motor_command(self, data: bytes) -> None:
        """Send a motor/preset command (auto-sends motor init if needed)."""
        async with self._lock:
            client = await self._ensure_connected()
            if not self._motor_initialized:
                await client.write_gatt_char(
                    WRITE_CHAR_UUID, CMD_MOTOR_INIT, response=False
                )
                await asyncio.sleep(0.05)
                self._motor_initialized = True
            await client.write_gatt_char(WRITE_CHAR_UUID, data, response=False)
            self._reset_disconnect_timer()

    async def send_massage_light_command(self, data: bytes) -> None:
        """Send a massage/vibration/light command (auto-sends B0 init if needed)."""
        async with self._lock:
            client = await self._ensure_connected()
            if not self._massage_initialized:
                await client.write_gatt_char(
                    WRITE_CHAR_UUID, CMD_MASSAGE_LIGHT_INIT, response=False
                )
                await asyncio.sleep(0.05)
                self._massage_initialized = True
            await client.write_gatt_char(WRITE_CHAR_UUID, data, response=False)
            self._reset_disconnect_timer()

    async def send_command(self, data: bytes) -> None:
        """Send a raw command (no auto-init)."""
        async with self._lock:
            client = await self._ensure_connected()
            await client.write_gatt_char(WRITE_CHAR_UUID, data, response=False)
            self._reset_disconnect_timer()

    async def send_commands(self, commands: list[bytes], delay: float = 0.1) -> None:
        """Send multiple commands sequentially with delay."""
        async with self._lock:
            client = await self._ensure_connected()
            for cmd in commands:
                await client.write_gatt_char(WRITE_CHAR_UUID, cmd, response=False)
                await asyncio.sleep(delay)
            self._reset_disconnect_timer()

    async def disconnect(self) -> None:
        """Disconnect from the bed."""
        if self._disconnect_timer is not None:
            self._disconnect_timer.cancel()
            self._disconnect_timer = None
        if self.connected and self._client:
            await self._client.disconnect()
