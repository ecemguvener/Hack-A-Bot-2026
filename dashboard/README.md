# VibraARM Dashboard (Frontend)

## Quick Start

From project root:

```bash
cd dashboard
python3 -m http.server 5500
```

Open:
- http://127.0.0.1:5500

## WebSocket Input

Default socket URL in UI:
- `ws://127.0.0.1:8080/telemetry`

Expected telemetry JSON (from Pico B bridge):

```json
{
  "type": "telemetry",
  "mode": "NORMAL",
  "f_tremor_hz": 5.2,
  "tremor_magnitude": 0.35,
  "dominant_axis": "X",
  "axis_sign": -1,
  "selected_motor_id": 2,
  "f_motor_hz": 6.2,
  "k_factor": 1.2,
  "fault_flags": 0
}
```

Config message sent from UI to backend:

```json
{
  "type": "config",
  "mode": "CALIBRATION",
  "k_factor": 1.3,
  "intensity_limit": 70
}
```

## Features

- Live KPI cards: tremor freq, magnitude, motor freq, k, axis, motor ID
- Rolling line charts for key metrics
- Mode and safety status pills
- Calibration controls (`mode`, `k_factor`, `intensity_limit`)
- Safe stop button
- Built-in simulation mode if backend is not ready

