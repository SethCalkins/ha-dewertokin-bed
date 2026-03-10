# DewertOkin Bed — Home Assistant Integration

Custom Home Assistant integration for DewertOkin adjustable beds (BOX25 Star controller) via Bluetooth Low Energy.

Works through ESPHome Bluetooth proxies — no direct BLE adapter required on your HA host.

## Features

- **Presets**: Flat, Zero Gravity, Relax, Ascent, Anti Snore
- **Position Control**: Head, Foot, Core/Lumbar (0-100 sliders) with live feedback
- **Lighting**: 7 colors, 6 brightness levels (native HA light card)
- **Vibration**: Independent head/foot zones (0-8)
- **Massage**: 3 wave modes with 7 intensity levels
- **Memory Positions**: 4 save/recall slots
- **Motion Sensor**: Toggle under-bed motion-activated light
- **Status Feedback**: BLE notification parsing for position, connection state, and movement
- **Auto-discovery**: Finds beds advertising as `Star*` via BLE
- **Reliable Connection**: Automatic retry with exponential backoff, wake sequence, idle disconnect

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Go to **Integrations** → three-dot menu → **Custom repositories**
3. Add `https://github.com/sethcalkins/ha-dewertokin-bed` as **Integration**
4. Search for "DewertOkin Bed" and install
5. Restart Home Assistant

### Manual

Copy `custom_components/dewertokin_bed/` to your HA `custom_components/` directory and restart.

## Setup

1. **Settings** → **Devices & Services** → **Add Integration**
2. Search for **DewertOkin Bed**
3. The integration auto-discovers beds advertising with the `Star` name prefix
4. Confirm the discovered device, or enter the MAC address manually

## Requirements

- Home Assistant 2024.1+
- An ESPHome Bluetooth proxy (e.g., Olimex ESP32-POE) or local BLE adapter
- DewertOkin bed with BOX25 Star controller

## Entities

### Controls

| Entity | Type | Description |
|--------|------|-------------|
| Bed Light | Light | Color + brightness control (7 colors, 6 levels) |
| Flat | Button | Flat preset |
| Zero Gravity | Button | Zero-G preset |
| Relax | Button | Relax preset |
| Ascent | Button | Ascent preset |
| Anti Snore | Button | Anti-snore preset |
| Memory 1-4 | Button | Recall saved positions |
| Save Memory 1-4 | Button | Store current position |
| Head Position | Number | 0-100 slider |
| Foot Position | Number | 0-100 slider |
| Core Position | Number | 0-100 slider |
| Vibration Head | Number | 0-8 intensity |
| Vibration Foot | Number | 0-8 intensity |
| Massage Intensity | Number | 1-7 (maps to protocol levels 2-8) |
| Massage Mode | Select | Off / Wave 1 / Wave 2 / Wave 3 |
| Massage | Switch | On/off toggle |
| Motion Sensor | Switch | Under-bed motion sensor on/off |

### Diagnostics

| Entity | Type | Description |
|--------|------|-------------|
| Connected | Binary Sensor | BLE connection status |
| Moving | Binary Sensor | Bed motors in motion |
| Connection | Sensor | Detailed connection state |
| Last Notification | Sensor | Raw BLE notification hex (disabled by default) |

## BLE Protocol

This integration communicates over Nordic UART Service (NUS):
- Service: `6e400001-b5a3-f393-e0a9-e50e24dcca9e`
- Write (TX): `6e400002-b5a3-f393-e0a9-e50e24dcca9e`
- Notify (RX): `6e400003-b5a3-f393-e0a9-e50e24dcca9e`

### Connection Sequence
1. Connect to BLE device
2. Subscribe to notifications on RX characteristic
3. Send wake command: `5A 0B 00 A5`
4. Send subsystem init: `00 D0` (motors) or `00 B0` (massage/light)
5. Send commands

### Reliability
- Commands retry up to 3 times with exponential backoff
- Automatic reconnection on BLE disconnect
- Wake command sent on every fresh connection
- Idle disconnect after 2 minutes to conserve BLE resources

## Dashboard

See `dashboard/bed-remote.yaml` for a styled Lovelace card using button-card, stack-in-card, and Mushroom.

## License

MIT
