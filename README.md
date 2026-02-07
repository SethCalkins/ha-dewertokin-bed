# DewertOkin Bed — Home Assistant Integration

Custom Home Assistant integration for DewertOkin adjustable beds (FP2901 controller) via Bluetooth Low Energy.

Works through ESPHome Bluetooth proxies — no direct BLE adapter required on your HA host.

## Features

- **Presets**: Flat, Zero Gravity, Relax, Ascent, Anti Snore
- **Position Control**: Head, Foot, Core/Lumbar (0-100 sliders)
- **Lighting**: 7 colors, 6 brightness levels (native HA light card)
- **Vibration**: Independent head/foot zones (0-8)
- **Massage**: 3 modes (Steady, Pulse, Wave) with 7 intensity levels
- **Auto-discovery**: Finds beds advertising as `Star*` via BLE

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
- DewertOkin bed with FP2901/CB.25 controller

## Entities

| Entity | Type | Description |
|--------|------|-------------|
| Bed Light | Light | Color + brightness control |
| Flat | Button | Flat preset |
| Zero Gravity | Button | Zero-G preset |
| Relax | Button | Relax preset |
| Ascent | Button | Ascent preset |
| Anti Snore | Button | Anti-snore preset |
| Head Position | Number | 0-100 slider |
| Foot Position | Number | 0-100 slider |
| Core Position | Number | 0-100 slider |
| Vibration Head | Number | 0-8 intensity |
| Vibration Foot | Number | 0-8 intensity |
| Massage Intensity | Number | 1-7 (maps to protocol levels 2-8) |
| Massage Mode | Select | Off / Steady / Pulse / Wave |
| Massage | Switch | On/off toggle |

## Protocol

Full BLE protocol documentation: see `DEWERTOKIN_BLE_PROTOCOL.md` in this repo.

## License

MIT
