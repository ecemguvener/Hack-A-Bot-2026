# VibraArm: User-Specific Tremor Stabilisation Glove


VibraArm is a two-node embedded assistive system designed for people with Parkinsonian tremor and hand instability. 
It measures hand tremor in real time using an IMU, computes tremor frequency/magnitude/direction, and drives an opposing vibration motor profile to improve hand stability.

The system uses **two Raspberry Pi Pico 2 boards with wireless coordination**:
- **Glove Pico (Pi #1):** sensing + closed-loop motor control on the hand
- **Base Pico (Pi #2):** receives telemetry, sends configuration/training parameters, bridges data to laptop UI

For Setup and Run please jump to step 8. 

---

## 1. Problem Definition and Solution Fit
### Real-world problem
People with Parkinson’s and related conditions often experience involuntary hand tremor that disrupts daily tasks (holding objects, writing, buttoning, using tools). Existing options are often limited, non-personalized, expensive, or intrusive.

### Who the solution is for
- Primary users: people with hand tremor / reduced motor stability
- Secondary users: caregivers, clinicians, rehab/assistive-tech researchers

### Why this solution fits the prompt
- Prompt area: **Assistive Tech**
- The prototype directly improves safety/usability in daily hand movement tasks by applying responsive vibration feedback based on measured tremor behavior.
---

## 2. System Overview

### High-level architecture

```text
[Hand / Glove Node: Pico #1]
  BMI160 IMU -> Tremor Detection -> Control Law -> Motor Driver (N20 + MX1508)
          |                                             |
          +------ Telemetry (wireless) ----------------+

[Base Node: Pico #2]
  Wireless RX/TX <-> Config Parser <-> USB Serial <-> Laptop Bridge <-> Web UI
```

### Node responsibilities

#### Pico #1 (Glove)
- Reads BMI160 IMU at fixed sample rate (100 Hz)
- Computes:
  - tremor frequency
  - tremor magnitude
  - dominant axis / direction
- Selects opposing motor
- Computes motor frequency:
  - `f_motor = k_factor * f_tremor`
- Drives vibration intensity based on tremor magnitude with intensity cap
- Sends telemetry packets wirelessly to Pico #2
- Receives config updates (mode, k, intensity cap)

#### Pico #2 (Base)
- Receives telemetry from Pico #1
- Accepts operator commands from USB serial / UI bridge
- Sends updated config wirelessly to Pico #1
- Outputs **JSON telemetry** for dashboard synchronisation

---

## 3. Control Strategy and Modes

### Closed-loop control (core mode)
At 100 Hz, the glove node updates tremor estimation and motor commands continuously:
1. Read IMU sample
2. Update rolling window / filters
3. Estimate tremor parameters
4. Select opposing motor
5. Drive motor at `k * f_tremor`
6. Send telemetry

### User-specific training workflow
1. Start in **Calibration mode**
2. Tune `k_factor` and `intensity_limit` for a specific user
3. Observe real-time frequency/magnitude response in UI
4. Lock selected profile
5. Switch to Normal closed-loop operation

### Supported runtime modes
- `mode=0`: Normal closed-loop
- `mode=1`: Calibration
- `mode=2`: Continuous ON (latched vibration until explicitly stopped)
- `mode=3`: OFF / Safe stop (motors forced off)

Quick controls from PC serial:
- `on` -> mode 2
- `off` -> mode 3
- `k=<value>`
- `limit=<value>`
- `status`

---

## 4. Hardware Used

### Core hardware
- 2x Raspberry Pi Pico 2
- BMI160 IMU
- N20 micro geared DC motors
- MX1508 motor driver(s)
- Wireless TX/RX modules used in implementation
- Breadboard / wires / power regulation

### Why these choices
- Pico 2 gives deterministic real-time loop control
- BMI160 provides compact inertial sensing for tremor features
- N20 + MX1508 provides practical, lightweight wearable actuation
- Two-node split improves reliability: glove loop remains local even if UI/PC link drops

---

## 5. External Communications and UI

### Data path

```text
Glove Pico -> Wireless -> Base Pico -> USB serial -> serial_ws_bridge.py -> WebSocket -> Dashboard UI
```

### Telemetry format (to UI bridge)
Base Pico emits JSON lines such as:

```json
{
  "type": "telemetry",
  "f_tremor_hz": 5.2,
  "tremor_magnitude": 0.31,
  "f_motor_hz": 15.6,
  "k_factor": 3.0,
  "mode": "NORMAL",
  "fault_flags": 0
}
```

### Config format (from UI/bridge)

```json
{
  "type": "config",
  "mode": "CALIBRATION",
  "k_factor": 2.8,
  "intensity_limit": 70
}
```

(`intensity_limit` from UI percent is converted to 0..1 on the base node)

---

## 7. Engineering Tradeoffs

- **Signal processing simplicity vs complexity:**
  Used robust, lightweight methods suitable for microcontroller real-time constraints.
- **Local control vs cloud dependence:**
  Closed loop runs fully on glove Pico to reduce latency and remove network dependence.
- **Safety vs aggressiveness:**
  Intensity clamped and OFF mode added for immediate manual override.
- **Feature scope vs reliability:**
  Prioritized reliable closed-loop + communication over risky feature expansion.

---

## 8. Setup and Run

## 8.1 Flash firmware
- Glove Pico: `hackabot2026-steadiARM/final_proj.py`
- Base Pico: `hackabot2026-steadiARM/receiver.py`

## 8.2 Start dashboard server
From repo root:

```bash
cd dashboard
python3 -m http.server 5500
```

If port is busy:

```bash
python3 -m http.server 5501
```

## 8.3 Start serial-WebSocket bridge
From repo root:

```bash
python3 dashboard/serial_ws_bridge.py --serial-port /dev/tty.usbmodemXXXX --baud 115200 --host 127.0.0.1 --port 8080 --path /telemetry
```

## 8.4 Open UI
- `http://127.0.0.1:5500`
- WebSocket endpoint in UI: `ws://127.0.0.1:8080/telemetry`

---

## 9. Safety and Reliability Features

- Motor intensity clamp (`intensity_limit`)
- Explicit OFF mode (`mode=3` / `off`)
- Continuous mode only active when user requests it
- Closed-loop remains local on glove node
- Telemetry and control are separable from core loop

---

## 11. Limitations and Future Work

- Clinical validation and long-term efficacy testing are not yet complete
- More advanced adaptive algorithms can replace current tuning heuristics
- Future versions can add profile persistence per user and richer safety diagnostics

---

## Team Note
This is a hackathon prototype focused on proving a practical assistive closed-loop concept with reliable real-time behavior and clear explainability under judging conditions.
