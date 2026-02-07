"""Constants for the DewertOkin Bed integration."""

DOMAIN = "dewertokin_bed"

# BLE Service & Characteristics (Nordic UART Service)
SERVICE_UUID = "6e400001-b5a3-f393-e0a9-e50e24dcca9e"
WRITE_CHAR_UUID = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"
NOTIFY_CHAR_UUID = "6e400003-b5a3-f393-e0a9-e50e24dcca9e"

# Device name prefix for discovery
DEVICE_NAME_PREFIX = "Star"

# --- Initialization Commands ---
CMD_WAKE = bytes([0x5A, 0x0B, 0x00, 0xA5])
CMD_MOTOR_INIT = bytes([0x00, 0xD0])
CMD_MASSAGE_LIGHT_INIT = bytes([0x00, 0xB0])

# --- Motor / Preset Commands (05 02 prefix, 7 bytes) ---
CMD_MOTOR_STOP = bytes([0x05, 0x02, 0x00, 0x00, 0x00, 0x00, 0x00])
CMD_MASSAGE_EXIT = bytes([0x05, 0x02, 0x02, 0x00, 0x00, 0x00, 0x00])

# Presets: send command, then CMD_MOTOR_STOP to confirm
CMD_PRESET_FLAT = bytes([0x05, 0x02, 0x08, 0x00, 0x00, 0x00, 0x00])
CMD_PRESET_ZERO_GRAVITY = bytes([0x05, 0x02, 0x00, 0x00, 0x10, 0x00, 0x00])
CMD_PRESET_RELAX = bytes([0x05, 0x02, 0x00, 0x00, 0x20, 0x00, 0x00])
CMD_PRESET_ASCENT = bytes([0x05, 0x02, 0x00, 0x00, 0x40, 0x00, 0x00])
CMD_PRESET_ANTI_SNORE = bytes([0x05, 0x02, 0x00, 0x00, 0x80, 0x00, 0x00])

PRESETS = {
    "flat": CMD_PRESET_FLAT,
    "zero_gravity": CMD_PRESET_ZERO_GRAVITY,
    "relax": CMD_PRESET_RELAX,
    "ascent": CMD_PRESET_ASCENT,
    "anti_snore": CMD_PRESET_ANTI_SNORE,
}

# --- Position Control (03 F0 prefix, 5 bytes) ---
# Format: 03 F0 [zone] [position 0-100] 00
ZONE_HEAD = 0x00
ZONE_FOOT = 0x01
ZONE_CORE = 0x02
ZONE_SYNC = 0x07


def cmd_position(zone: int, position: int) -> bytes:
    """Build a position command. Position 0-100."""
    return bytes([0x03, 0xF0, zone, position, 0x00])


CMD_ZONE_SYNC = bytes([0x03, 0xF0, 0x07, 0x00, 0x00])

# --- Lighting (04 E0 prefix, 6 bytes) ---
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
    return bytes([0x04, 0xE0, 0x00, level, 0x00, 0x00])


# --- Vibration (04 E0 06 prefix, 6 bytes) ---
# Format: 04 E0 06 [head 0-8] [foot 0-8] 00
MAX_VIBRATION_LEVEL = 8


def cmd_vibration(head_level: int, foot_level: int) -> bytes:
    """Set vibration levels (0-8 per zone)."""
    return bytes([0x04, 0xE0, 0x06, head_level, foot_level, 0x00])


# --- Massage Mode (08 02 prefix, 10 bytes) ---
# Format: 08 02 00 00 00 00 00 [mode] 00 00
MASSAGE_MODES = {
    "off": None,
    "steady": 0x08,
    "pulse": 0x10,
    "wave": 0x20,
}

MASSAGE_MODE_NAMES = list(MASSAGE_MODES.keys())


def cmd_massage_mode(mode_flag: int) -> bytes:
    """Set massage mode (0x08=steady, 0x10=pulse, 0x20=wave)."""
    return bytes([0x08, 0x02, 0x00, 0x00, 0x00, 0x00, 0x00, mode_flag, 0x00, 0x00])


# Connection settings
DISCONNECT_DELAY = 120  # seconds before disconnecting idle connection
