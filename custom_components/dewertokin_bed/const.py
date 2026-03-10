"""Constants for the DewertOkin Bed integration."""

DOMAIN = "dewertokin_bed"

# ─── BLE Service & Characteristics (Nordic UART Service) ─────────────────────
SERVICE_UUID = "6e400001-b5a3-f393-e0a9-e50e24dcca9e"
WRITE_CHAR_UUID = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"
NOTIFY_CHAR_UUID = "6e400003-b5a3-f393-e0a9-e50e24dcca9e"

# Device name prefix for discovery
DEVICE_NAME_PREFIX = "Star"

# ─── Connection Settings ─────────────────────────────────────────────────────
DISCONNECT_DELAY = 120  # seconds before disconnecting idle connection
CONNECT_TIMEOUT = 10.0  # seconds to wait for BLE connection
MAX_RETRIES = 3  # max command retry attempts
RETRY_DELAY = 0.5  # seconds between retries
WAKE_DELAY = 0.15  # seconds to wait after wake command
INIT_DELAY = 0.08  # seconds to wait after init command
COMMAND_DELAY = 0.05  # seconds between sequential commands
NOTIFICATION_TIMEOUT = 2.0  # seconds to wait for notification response

# ─── Initialization Commands ─────────────────────────────────────────────────
CMD_WAKE = bytes([0x5A, 0x0B, 0x00, 0xA5])
CMD_MOTOR_INIT = bytes([0x00, 0xD0])
CMD_MASSAGE_LIGHT_INIT = bytes([0x00, 0xB0])

# ─── Motor / Preset Commands (05 02 prefix, 7 bytes) ─────────────────────────
CMD_MOTOR_STOP = bytes([0x05, 0x02, 0x00, 0x00, 0x00, 0x00, 0x00])
CMD_MASSAGE_EXIT = bytes([0x05, 0x02, 0x02, 0x00, 0x00, 0x00, 0x00])

# Directional motor control (continuous — send repeatedly while moving)
CMD_HEAD_UP = bytes([0x05, 0x02, 0x00, 0x01, 0x00, 0x00, 0x00])
CMD_HEAD_DOWN = bytes([0x05, 0x02, 0x00, 0x02, 0x00, 0x00, 0x00])
CMD_FOOT_UP = bytes([0x05, 0x02, 0x00, 0x04, 0x00, 0x00, 0x00])
CMD_FOOT_DOWN = bytes([0x05, 0x02, 0x00, 0x08, 0x00, 0x00, 0x00])
CMD_LUMBAR_UP = bytes([0x05, 0x02, 0x00, 0x10, 0x00, 0x00, 0x00])
CMD_LUMBAR_DOWN = bytes([0x05, 0x02, 0x00, 0x20, 0x00, 0x00, 0x00])
CMD_NECK_TILT_UP = bytes([0x05, 0x02, 0x00, 0x40, 0x00, 0x00, 0x00])
CMD_NECK_TILT_DOWN = bytes([0x05, 0x02, 0x00, 0x80, 0x00, 0x00, 0x00])

# Presets: send command, then CMD_MOTOR_STOP to confirm
CMD_PRESET_FLAT = bytes([0x05, 0x02, 0x08, 0x00, 0x00, 0x00, 0x00])
CMD_PRESET_ZERO_GRAVITY = bytes([0x05, 0x02, 0x00, 0x00, 0x10, 0x00, 0x00])
CMD_PRESET_RELAX = bytes([0x05, 0x02, 0x00, 0x00, 0x20, 0x00, 0x00])
CMD_PRESET_ASCENT = bytes([0x05, 0x02, 0x00, 0x00, 0x40, 0x00, 0x00])
CMD_PRESET_ANTI_SNORE = bytes([0x05, 0x02, 0x00, 0x00, 0x80, 0x00, 0x00])

# Memory positions (4 slots)
CMD_MEMORY_STORE_1 = bytes([0x05, 0x02, 0x00, 0x00, 0x01, 0x00, 0x00])
CMD_MEMORY_STORE_2 = bytes([0x05, 0x02, 0x00, 0x00, 0x02, 0x00, 0x00])
CMD_MEMORY_STORE_3 = bytes([0x05, 0x02, 0x00, 0x00, 0x04, 0x00, 0x00])
CMD_MEMORY_STORE_4 = bytes([0x05, 0x02, 0x00, 0x00, 0x08, 0x00, 0x00])
CMD_MEMORY_RECALL_1 = bytes([0x05, 0x02, 0x00, 0x00, 0x00, 0x01, 0x00])
CMD_MEMORY_RECALL_2 = bytes([0x05, 0x02, 0x00, 0x00, 0x00, 0x02, 0x00])
CMD_MEMORY_RECALL_3 = bytes([0x05, 0x02, 0x00, 0x00, 0x00, 0x04, 0x00])
CMD_MEMORY_RECALL_4 = bytes([0x05, 0x02, 0x00, 0x00, 0x00, 0x08, 0x00])

PRESETS = {
    "flat": CMD_PRESET_FLAT,
    "zero_gravity": CMD_PRESET_ZERO_GRAVITY,
    "relax": CMD_PRESET_RELAX,
    "ascent": CMD_PRESET_ASCENT,
    "anti_snore": CMD_PRESET_ANTI_SNORE,
}

MEMORY_STORE = {
    1: CMD_MEMORY_STORE_1,
    2: CMD_MEMORY_STORE_2,
    3: CMD_MEMORY_STORE_3,
    4: CMD_MEMORY_STORE_4,
}

MEMORY_RECALL = {
    1: CMD_MEMORY_RECALL_1,
    2: CMD_MEMORY_RECALL_2,
    3: CMD_MEMORY_RECALL_3,
    4: CMD_MEMORY_RECALL_4,
}

# ─── Position Control (03 F0 prefix, 5 bytes) ────────────────────────────────
# Format: 03 F0 [zone] [position 0-100] 00
ZONE_HEAD = 0x00
ZONE_FOOT = 0x01
ZONE_CORE = 0x02
ZONE_SYNC = 0x07


def cmd_position(zone: int, position: int) -> bytes:
    """Build a position command. Position 0-100."""
    pos = max(0, min(100, int(position)))
    return bytes([0x03, 0xF0, zone, pos, 0x00])


CMD_ZONE_SYNC = bytes([0x03, 0xF0, 0x07, 0x00, 0x00])

# ─── Lighting (04 E0 prefix, 6 bytes) ────────────────────────────────────────
# Color: 04 E0 01 [color 0-7] 00 00  (0 = off)
# Brightness: 04 E0 00 [level 1-6] 00 00

LIGHT_COLORS = {
    "white": 0x01,
    "red": 0x02,
    "orange": 0x03,
    "yellow": 0x04,
    "green": 0x05,
    "blue": 0x06,
    "purple": 0x07,
}

# Map color names to approximate RGB for HA light entity
LIGHT_COLOR_RGB = {
    "white": (255, 255, 255),
    "red": (255, 0, 0),
    "orange": (255, 165, 0),
    "yellow": (255, 255, 0),
    "green": (0, 255, 0),
    "blue": (0, 0, 255),
    "purple": (128, 0, 128),
}

LIGHT_COLOR_NAMES = list(LIGHT_COLORS.keys())
MAX_BRIGHTNESS_LEVEL = 6
MIN_BRIGHTNESS_LEVEL = 1


def cmd_light_color(color_value: int) -> bytes:
    """Set light color (0=off, 1-7=colors)."""
    return bytes([0x04, 0xE0, 0x01, color_value, 0x00, 0x00])


def cmd_light_brightness(level: int) -> bytes:
    """Set brightness level (1-6)."""
    lvl = max(MIN_BRIGHTNESS_LEVEL, min(MAX_BRIGHTNESS_LEVEL, int(level)))
    return bytes([0x04, 0xE0, 0x00, lvl, 0x00, 0x00])


# ─── Vibration (04 E0 06 prefix, 6 bytes) ────────────────────────────────────
# Format: 04 E0 06 [head 0-8] [foot 0-8] 00
MAX_VIBRATION_LEVEL = 8


def cmd_vibration(head_level: int, foot_level: int) -> bytes:
    """Set vibration levels (0-8 per zone)."""
    h = max(0, min(MAX_VIBRATION_LEVEL, int(head_level)))
    f = max(0, min(MAX_VIBRATION_LEVEL, int(foot_level)))
    return bytes([0x04, 0xE0, 0x06, h, f, 0x00])


# ─── Massage (08 02 prefix, 10 bytes) ─────────────────────────────────────────
# Format: 08 02 [headAdd] [headReduce] [footAdd] [footReduce] [allFlags] [mode] [timer] 00
# Mode: 0x08=wave1, 0x10=wave2, 0x20=wave3
# Intensity step: 0x01=step once in the relevant byte position
# allFlags byte: 0x01=allAdd, 0x02=allReduce
MASSAGE_MODES = {
    "off": None,
    "wave_1": 0x08,
    "wave_2": 0x10,
    "wave_3": 0x20,
}

MASSAGE_MODE_NAMES = list(MASSAGE_MODES.keys())
MAX_MASSAGE_INTENSITY = 7
MIN_MASSAGE_INTENSITY = 1


def cmd_massage_mode(mode_flag: int) -> bytes:
    """Set massage mode (0x08=wave1, 0x10=wave2, 0x20=wave3)."""
    return bytes([0x08, 0x02, 0x00, 0x00, 0x00, 0x00, 0x00, mode_flag, 0x00, 0x00])


# Massage intensity step commands (both zones)
CMD_MASSAGE_ALL_ADD = bytes([0x08, 0x02, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00])
CMD_MASSAGE_ALL_REDUCE = bytes([0x08, 0x02, 0x00, 0x00, 0x00, 0x00, 0x02, 0x00, 0x00, 0x00])

# Massage intensity step commands (per zone)
CMD_MASSAGE_HEAD_ADD = bytes([0x08, 0x02, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
CMD_MASSAGE_HEAD_REDUCE = bytes([0x08, 0x02, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
CMD_MASSAGE_FOOT_ADD = bytes([0x08, 0x02, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00])
CMD_MASSAGE_FOOT_REDUCE = bytes([0x08, 0x02, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00])

# Wave mode step commands
CMD_MASSAGE_WAVE_ADD = bytes([0x08, 0x02, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00])
CMD_MASSAGE_WAVE_REDUCE = bytes([0x08, 0x02, 0x00, 0x00, 0x00, 0x00, 0x00, 0x02, 0x00, 0x00])


# ─── Motion Sensor (04 E0 07 prefix, 6 bytes) ────────────────────────────────
CMD_MOTION_SENSOR_ON = bytes([0x04, 0xE0, 0x07, 0x01, 0x00, 0x00])
CMD_MOTION_SENSOR_OFF = bytes([0x04, 0xE0, 0x07, 0x00, 0x00, 0x00])

# ─── Notification Response Parsing ───────────────────────────────────────────
# Response format varies by command type. Known patterns:
# Position feedback: [zone] [position 0-100] ...
# Status: first byte indicates message type


class BedStatus:
    """Parsed bed status from BLE notifications."""

    def __init__(self) -> None:
        self.head_position: int | None = None
        self.foot_position: int | None = None
        self.core_position: int | None = None
        self.is_moving: bool = False
        self.massage_active: bool = False
        self.light_on: bool = False
        self.motion_sensor_on: bool = False
        self.raw_data: bytes = b""

    def __repr__(self) -> str:
        return (
            f"BedStatus(head={self.head_position}, foot={self.foot_position}, "
            f"core={self.core_position}, moving={self.is_moving})"
        )
