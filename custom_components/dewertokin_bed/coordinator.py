"""BLE connection coordinator for DewertOkin Bed."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from enum import Enum

from bleak import BleakClient
from bleak.exc import BleakError
from bleak_retry_connector import establish_connection

from homeassistant.components import bluetooth
from homeassistant.core import HomeAssistant, callback

from .const import (
    CMD_MASSAGE_LIGHT_INIT,
    CMD_MOTOR_INIT,
    CMD_MOTOR_STOP,
    CMD_WAKE,
    COMMAND_DELAY,
    CONNECT_TIMEOUT,
    DISCONNECT_DELAY,
    INIT_DELAY,
    MAX_RETRIES,
    NOTIFY_CHAR_UUID,
    RETRY_DELAY,
    WAKE_DELAY,
    WRITE_CHAR_UUID,
    BedStatus,
)

_LOGGER = logging.getLogger(__name__)


class ConnectionState(Enum):
    """BLE connection states."""

    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    READY = "ready"  # connected + initialized


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
        self._connection_state = ConnectionState.DISCONNECTED
        self._consecutive_failures = 0

        # Shared state for paired vibration commands
        self.vibration_head: int = 0
        self.vibration_foot: int = 0

        # Bed status from notifications
        self.status = BedStatus()
        self._status_listeners: list[Callable[[], None]] = []
        self._notification_event = asyncio.Event()

    # ─── Properties ───────────────────────────────────────────────────────

    @property
    def connected(self) -> bool:
        """True if BLE client is connected."""
        return self._client is not None and self._client.is_connected

    @property
    def connection_state(self) -> ConnectionState:
        """Current connection state."""
        if not self.connected:
            return ConnectionState.DISCONNECTED
        return self._connection_state

    # ─── Status Listeners ─────────────────────────────────────────────────

    def register_status_listener(self, listener: Callable[[], None]) -> Callable[[], None]:
        """Register a callback for status updates. Returns unregister function."""
        self._status_listeners.append(listener)
        return lambda: self._status_listeners.remove(listener)

    def _notify_status_listeners(self) -> None:
        """Notify all registered status listeners."""
        for listener in self._status_listeners:
            try:
                listener()
            except Exception:
                _LOGGER.exception("Error in status listener")

    # ─── Notification Handling ────────────────────────────────────────────

    def _on_notification(self, _characteristic: object, data: bytearray) -> None:
        """Handle incoming BLE notification data from the bed."""
        raw = bytes(data)
        self.status.raw_data = raw
        _LOGGER.debug("Notification from %s: %s", self.name, raw.hex())

        if len(raw) < 2:
            self._notification_event.set()
            return

        self._parse_notification(raw)
        self._notification_event.set()
        self._notify_status_listeners()

    def _parse_notification(self, data: bytes) -> None:
        """Parse notification data into bed status.

        The protocol uses different response formats. Known patterns from
        reverse engineering the Sleepy's Elite app:

        Position feedback appears as bytes containing zone positions.
        The exact format depends on the command that triggered the response.
        We parse what we can and log unknowns for future analysis.
        """
        length = len(data)

        # Motor/position status responses (7+ bytes with 05 prefix)
        if length >= 7 and data[0] == 0x05:
            # Byte 1 typically indicates response type
            # Bytes 3-6 may contain position data
            self.status.is_moving = any(b != 0 for b in data[2:7])

        # Position report (5+ bytes with 03 prefix)
        elif length >= 4 and data[0] == 0x03:
            zone = data[1]
            position = data[2]
            if 0 <= position <= 100:
                if zone == 0x00:
                    self.status.head_position = position
                elif zone == 0x01:
                    self.status.foot_position = position
                elif zone == 0x02:
                    self.status.core_position = position

        # Massage/light/vibration status (6+ bytes with 04 prefix)
        elif length >= 4 and data[0] == 0x04:
            sub = data[1] if length > 1 else 0
            if sub == 0xE0:
                # Light or vibration response
                pass

        # Massage mode response (10 bytes with 08 prefix)
        elif length >= 8 and data[0] == 0x08:
            mode_byte = data[7] if length > 7 else 0
            self.status.massage_active = mode_byte != 0

        # Log unknown formats for protocol discovery
        else:
            _LOGGER.debug(
                "Unknown notification format from %s: len=%d data=%s",
                self.name,
                length,
                data.hex(),
            )

    # ─── Connection Management ────────────────────────────────────────────

    async def _ensure_connected(self) -> BleakClient:
        """Connect if not already connected, with wake + init sequence."""
        if self.connected and self._client is not None:
            return self._client

        self._connection_state = ConnectionState.CONNECTING
        _LOGGER.debug("Connecting to %s (%s)", self.name, self.address)

        device = bluetooth.async_ble_device_from_address(
            self.hass, self.address, connectable=True
        )
        if device is None:
            self._connection_state = ConnectionState.DISCONNECTED
            raise BleakError(
                f"Could not find BLE device {self.address} — "
                "ensure an ESPHome BLE proxy is in range"
            )

        try:
            self._client = await asyncio.wait_for(
                establish_connection(
                    BleakClient,
                    device,
                    self.name,
                    disconnected_callback=self._on_disconnect,
                ),
                timeout=CONNECT_TIMEOUT,
            )
        except (asyncio.TimeoutError, BleakError) as err:
            self._connection_state = ConnectionState.DISCONNECTED
            self._client = None
            raise BleakError(f"Connection to {self.name} failed: {err}") from err

        self._connection_state = ConnectionState.CONNECTED
        self._motor_initialized = False
        self._massage_initialized = False
        _LOGGER.info("Connected to %s", self.name)

        # Subscribe to notifications for status feedback
        try:
            await self._client.start_notify(NOTIFY_CHAR_UUID, self._on_notification)
            _LOGGER.debug("Subscribed to notifications on %s", self.name)
        except (BleakError, Exception) as err:
            _LOGGER.warning(
                "Could not subscribe to notifications on %s: %s", self.name, err
            )

        # Send wake command to ensure the controller is responsive
        try:
            await self._client.write_gatt_char(
                WRITE_CHAR_UUID, CMD_WAKE, response=False
            )
            await asyncio.sleep(WAKE_DELAY)
            _LOGGER.debug("Wake command sent to %s", self.name)
        except BleakError as err:
            _LOGGER.warning("Wake command failed on %s: %s", self.name, err)

        self._connection_state = ConnectionState.READY
        self._consecutive_failures = 0
        return self._client

    @callback
    def _on_disconnect(self, client: BleakClient) -> None:
        """Handle unexpected disconnection."""
        _LOGGER.info("Disconnected from %s", self.name)
        self._client = None
        self._connection_state = ConnectionState.DISCONNECTED
        self._motor_initialized = False
        self._massage_initialized = False

    def _reset_disconnect_timer(self) -> None:
        """Reset the idle disconnect timer."""
        if self._disconnect_timer is not None:
            self._disconnect_timer.cancel()
        self._disconnect_timer = self.hass.loop.call_later(
            DISCONNECT_DELAY,
            lambda: asyncio.ensure_future(self._idle_disconnect()),
        )

    async def _idle_disconnect(self) -> None:
        """Disconnect after idle timeout."""
        async with self._lock:
            if self.connected and self._client:
                _LOGGER.debug("Idle timeout, disconnecting from %s", self.name)
                try:
                    await self._client.disconnect()
                except BleakError:
                    pass

    # ─── Command Methods with Retry ───────────────────────────────────────

    async def _write_with_retry(self, data: bytes) -> None:
        """Write data to the BLE characteristic with retry logic."""
        last_error: Exception | None = None
        for attempt in range(MAX_RETRIES):
            try:
                client = await self._ensure_connected()
                await client.write_gatt_char(WRITE_CHAR_UUID, data, response=False)
                self._consecutive_failures = 0
                return
            except (BleakError, asyncio.TimeoutError, OSError) as err:
                last_error = err
                self._consecutive_failures += 1
                _LOGGER.warning(
                    "Write failed on %s (attempt %d/%d): %s",
                    self.name,
                    attempt + 1,
                    MAX_RETRIES,
                    err,
                )
                # Force reconnect on failure
                self._client = None
                self._connection_state = ConnectionState.DISCONNECTED
                self._motor_initialized = False
                self._massage_initialized = False
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(RETRY_DELAY * (attempt + 1))

        raise BleakError(
            f"Failed to write to {self.name} after {MAX_RETRIES} attempts: {last_error}"
        )

    async def send_motor_command(self, data: bytes) -> None:
        """Send a motor/preset command (auto-sends wake + motor init if needed)."""
        async with self._lock:
            client = await self._ensure_connected()
            if not self._motor_initialized:
                await client.write_gatt_char(
                    WRITE_CHAR_UUID, CMD_MOTOR_INIT, response=False
                )
                await asyncio.sleep(INIT_DELAY)
                self._motor_initialized = True
            await client.write_gatt_char(WRITE_CHAR_UUID, data, response=False)
            self._reset_disconnect_timer()

    async def send_motor_command_reliable(self, data: bytes) -> None:
        """Send a motor/preset command with retry on failure."""
        async with self._lock:
            last_error: Exception | None = None
            for attempt in range(MAX_RETRIES):
                try:
                    client = await self._ensure_connected()
                    if not self._motor_initialized:
                        await client.write_gatt_char(
                            WRITE_CHAR_UUID, CMD_MOTOR_INIT, response=False
                        )
                        await asyncio.sleep(INIT_DELAY)
                        self._motor_initialized = True
                    await client.write_gatt_char(
                        WRITE_CHAR_UUID, data, response=False
                    )
                    self._consecutive_failures = 0
                    self._reset_disconnect_timer()
                    return
                except (BleakError, asyncio.TimeoutError, OSError) as err:
                    last_error = err
                    self._consecutive_failures += 1
                    _LOGGER.warning(
                        "Motor command failed on %s (attempt %d/%d): %s",
                        self.name,
                        attempt + 1,
                        MAX_RETRIES,
                        err,
                    )
                    self._client = None
                    self._connection_state = ConnectionState.DISCONNECTED
                    self._motor_initialized = False
                    self._massage_initialized = False
                    if attempt < MAX_RETRIES - 1:
                        await asyncio.sleep(RETRY_DELAY * (attempt + 1))

            raise BleakError(
                f"Motor command failed on {self.name} after {MAX_RETRIES} attempts: "
                f"{last_error}"
            )

    async def send_massage_light_command(self, data: bytes) -> None:
        """Send a massage/vibration/light command (auto-sends B0 init if needed)."""
        async with self._lock:
            client = await self._ensure_connected()
            if not self._massage_initialized:
                await client.write_gatt_char(
                    WRITE_CHAR_UUID, CMD_MASSAGE_LIGHT_INIT, response=False
                )
                await asyncio.sleep(INIT_DELAY)
                self._massage_initialized = True
            await client.write_gatt_char(WRITE_CHAR_UUID, data, response=False)
            self._reset_disconnect_timer()

    async def send_massage_light_command_reliable(self, data: bytes) -> None:
        """Send a massage/light command with retry on failure."""
        async with self._lock:
            last_error: Exception | None = None
            for attempt in range(MAX_RETRIES):
                try:
                    client = await self._ensure_connected()
                    if not self._massage_initialized:
                        await client.write_gatt_char(
                            WRITE_CHAR_UUID, CMD_MASSAGE_LIGHT_INIT, response=False
                        )
                        await asyncio.sleep(INIT_DELAY)
                        self._massage_initialized = True
                    await client.write_gatt_char(
                        WRITE_CHAR_UUID, data, response=False
                    )
                    self._consecutive_failures = 0
                    self._reset_disconnect_timer()
                    return
                except (BleakError, asyncio.TimeoutError, OSError) as err:
                    last_error = err
                    self._consecutive_failures += 1
                    _LOGGER.warning(
                        "Massage/light command failed on %s (attempt %d/%d): %s",
                        self.name,
                        attempt + 1,
                        MAX_RETRIES,
                        err,
                    )
                    self._client = None
                    self._connection_state = ConnectionState.DISCONNECTED
                    self._motor_initialized = False
                    self._massage_initialized = False
                    if attempt < MAX_RETRIES - 1:
                        await asyncio.sleep(RETRY_DELAY * (attempt + 1))

            raise BleakError(
                f"Massage/light command failed on {self.name} after {MAX_RETRIES} "
                f"attempts: {last_error}"
            )

    async def send_command(self, data: bytes) -> None:
        """Send a raw command (no auto-init, no retry)."""
        async with self._lock:
            client = await self._ensure_connected()
            await client.write_gatt_char(WRITE_CHAR_UUID, data, response=False)
            self._reset_disconnect_timer()

    async def send_commands(self, commands: list[bytes], delay: float = COMMAND_DELAY) -> None:
        """Send multiple commands sequentially with delay."""
        async with self._lock:
            client = await self._ensure_connected()
            for cmd in commands:
                await client.write_gatt_char(WRITE_CHAR_UUID, cmd, response=False)
                await asyncio.sleep(delay)
            self._reset_disconnect_timer()

    async def send_preset_command(self, preset_cmd: bytes) -> None:
        """Send a preset command with proper confirmation sequence."""
        async with self._lock:
            last_error: Exception | None = None
            for attempt in range(MAX_RETRIES):
                try:
                    client = await self._ensure_connected()
                    if not self._motor_initialized:
                        await client.write_gatt_char(
                            WRITE_CHAR_UUID, CMD_MOTOR_INIT, response=False
                        )
                        await asyncio.sleep(INIT_DELAY)
                        self._motor_initialized = True
                    # Send preset command
                    await client.write_gatt_char(
                        WRITE_CHAR_UUID, preset_cmd, response=False
                    )
                    await asyncio.sleep(COMMAND_DELAY)
                    # Confirm with motor stop
                    await client.write_gatt_char(
                        WRITE_CHAR_UUID, CMD_MOTOR_STOP, response=False
                    )
                    self._consecutive_failures = 0
                    self._reset_disconnect_timer()
                    return
                except (BleakError, asyncio.TimeoutError, OSError) as err:
                    last_error = err
                    self._consecutive_failures += 1
                    _LOGGER.warning(
                        "Preset command failed on %s (attempt %d/%d): %s",
                        self.name,
                        attempt + 1,
                        MAX_RETRIES,
                        err,
                    )
                    self._client = None
                    self._connection_state = ConnectionState.DISCONNECTED
                    self._motor_initialized = False
                    self._massage_initialized = False
                    if attempt < MAX_RETRIES - 1:
                        await asyncio.sleep(RETRY_DELAY * (attempt + 1))

            raise BleakError(
                f"Preset command failed on {self.name} after {MAX_RETRIES} "
                f"attempts: {last_error}"
            )

    # ─── Disconnect ───────────────────────────────────────────────────────

    async def disconnect(self) -> None:
        """Disconnect from the bed."""
        if self._disconnect_timer is not None:
            self._disconnect_timer.cancel()
            self._disconnect_timer = None
        if self.connected and self._client:
            try:
                await self._client.disconnect()
            except BleakError:
                pass
        self._client = None
        self._connection_state = ConnectionState.DISCONNECTED
