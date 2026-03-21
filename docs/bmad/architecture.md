# System Architecture: VibraARM Closed-Loop Tremor Support

- **Document Version:** 1.0
- **Date:** 2026-03-21
- **Author:** Hack-A-Bot Team
- **Status:** Draft

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Architecture Pattern](#2-architecture-pattern)
3. [Component Design](#3-component-design)
4. [Data Model](#4-data-model)
5. [API Specifications](#5-api-specifications)
6. [Non-Functional Requirements Mapping](#6-non-functional-requirements-mapping)
7. [Technology Stack](#7-technology-stack)
8. [Trade-off Analysis](#8-trade-off-analysis)
9. [Deployment Architecture](#9-deployment-architecture)
10. [Future Considerations](#10-future-considerations)

---

## 1. System Overview

### Purpose
VibraARM is a dual-node assistive embedded system that performs real-time tremor sensing and closed-loop counter-stimulation using an opposing motor strategy.

### Scope
**In Scope:**
- Tremor feature extraction on glove node (axis/sign, magnitude, zero-crossing frequency)
- Closed-loop motor command generation with `f_motor = k_factor * f_tremor`
- Wireless telemetry/config between two Pico nodes via nRF24
- Operator UI for monitoring and calibration mode

**Out of Scope:**
- Clinical efficacy claims and medical certification
- Long-term model training and cloud analytics

### Architectural Drivers
1. **NFR-001: Control Loop Timing** - maintain deterministic 100 Hz sensing/control loop.
2. **NFR-004: Link and Fault Robustness** - fail-safe behavior on RF/IMU issues.
3. **NFR-005: Calibration Usability** - mode switching and `k_factor` tuning must be simple and visible.

### Stakeholders
- **Users:** people with tremor and caregivers
- **Developers:** 4-person hackathon team
- **Operations:** local demo operation only (no cloud ops)
- **Business:** judges evaluating assistive impact and engineering quality

---

## 2. Architecture Pattern

### Selected Pattern
**Pattern:** Layered distributed edge architecture (two-node embedded system)

### Pattern Justification
**Why this pattern:**
- Real-time control is isolated on Node A, reducing UI/network interference.
- Node B handles integration concerns (bridge/API/UI), improving maintainability.
- Matches project constraints: fast implementation, clear component boundaries.

**Alternatives considered:**
- **Single Pico all-in-one:** rejected because UI/bridge could disrupt loop timing.
- **PC-direct sensor/actuator control:** rejected because it weakens embedded autonomy and wireless requirement clarity.

### Pattern Application
- **Node A (control plane):** IMU sampling, feature extraction, motor command, safety checks.
- **Node B (integration plane):** RF bridge, config manager, UI API server, telemetry fan-out.
- **PC UI (presentation plane):** visualization and calibration controls.

---

## 3. Component Design

### Component Overview

```text
+----------------------+        +----------------------+        +----------------------+
| Node A: Glove Pico   | <----> | Node B: Base Pico    | <----> | PC UI                |
|----------------------|  nRF24 |----------------------|  TCP/  |----------------------|
| IMU service          |        | RF RX/TX service     |  WS/   | Dashboard + controls |
| Feature extraction   |        | Config state manager |  HTTP  | Charts + logs        |
| Control loop         |        | API bridge           |        | Calibration actions  |
| Motor driver service |        | Telemetry queue      |        |                      |
| Safety manager       |        |                      |        |                      |
+----------------------+        +----------------------+        +----------------------+
```

### Component Descriptions

#### Component: IMU Service (Node A)
**Responsibility:** sample BMI160 and provide validated sensor frames.

**Interfaces Provided:**
- `get_latest_frame()`
- `get_window()`

**Interfaces Required:**
- BMI160 I2C driver

**Data Owned:**
- rolling sample buffer
- sample timestamp

**NFRs Addressed:**
- NFR-001 (timing), NFR-004 (invalid sample detection)

---

#### Component: Feature Extraction (Node A)
**Responsibility:** compute dominant axis/sign, magnitude, and `f_tremor`.

**Interfaces Provided:**
- `compute_features(window) -> features`

**Interfaces Required:**
- rolling IMU window

**Data Owned:**
- per-axis RMS/variance
- zero-crossing counters
- smoothed frequency/magnitude

**NFRs Addressed:**
- NFR-001 (bounded compute time)

---

#### Component: Control Loop + Motor Driver (Node A)
**Responsibility:** map features/config to motor command and drive N20 safely.

**Interfaces Provided:**
- `apply_control(features, config)`

**Interfaces Required:**
- feature output
- config state
- driver PWM/timer

**Data Owned:**
- active mode
- current `k_factor`
- latest command (`f_motor`, duty, motor_id)

**NFRs Addressed:**
- NFR-001, NFR-004

---

#### Component: RF Transport (Node A/B)
**Responsibility:** reliable packet exchange for telemetry and config.

**Interfaces Provided:**
- `send_telemetry(packet)`
- `recv_config()`
- `send_config(packet)`
- `recv_telemetry()`

**Interfaces Required:**
- nRF24 SPI driver

**NFRs Addressed:**
- NFR-004 (timeouts, heartbeat)

---

#### Component: Base API Bridge (Node B)
**Responsibility:** expose telemetry/config to PC UI via socket/API.

**Interfaces Provided:**
- `GET /state`
- `WS /telemetry`
- `POST /config`

**Interfaces Required:**
- RF transport

**NFRs Addressed:**
- NFR-005 (usability), maintainability

---

## 4. Data Model

### Entity Relationship Diagram

```text
┌──────────────────────────┐         ┌──────────────────────────┐
│ TelemetrySample          │         │ ConfigState              │
├──────────────────────────┤         ├──────────────────────────┤
│ seq_id (PK)              │         │ config_version (PK)      │
│ timestamp_ms             │         │ mode                     │
│ mode                     │         │ k_factor                 │
│ f_tremor_hz              │         │ intensity_limit          │
│ tremor_magnitude         │         │ manual_override          │
│ dominant_axis            │         │ updated_at               │
│ axis_sign                │         └──────────────┬───────────┘
│ selected_motor_id        │                        │
│ f_motor_hz               │                        │
│ duty_pct                 │                        │
│ fault_flags              │                        │
└──────────────┬───────────┘                        │
               │                                    │
               └──────────────┬─────────────────────┘
                              │
                     ┌────────▼──────────┐
                     │ EventLog          │
                     ├───────────────────┤
                     │ event_id (PK)     │
                     │ event_type        │
                     │ message           │
                     │ timestamp_ms      │
                     └───────────────────┘
```

### Data Storage Strategy
- **Primary storage:** in-memory ring buffers on Node A/B.
- **UI state cache:** latest state object on Node B.
- **Optional persistence:** append event/telemetry snapshots to PC log file.

### Data Retention
- Node A/B memory retains rolling windows only.
- PC can store session logs per run.

---

## 5. API Specifications

### API Design Approach
**Protocol:** RF binary packets (Node A <-> Node B) + REST/WebSocket bridge (Node B <-> PC)

### RF Packet: Telemetry (`A -> B`)
```json
{
  "seq": 1024,
  "timestamp_ms": 1234567,
  "mode": "NORMAL",
  "f_tremor_hz": 5.3,
  "tremor_magnitude": 0.37,
  "dominant_axis": "X",
  "axis_sign": -1,
  "selected_motor_id": 2,
  "f_motor_hz": 6.4,
  "k_factor": 1.2,
  "fault_flags": 0
}
```

### RF Packet: Config (`B -> A`)
```json
{
  "mode": "CALIBRATION",
  "k_factor": 1.3,
  "intensity_limit": 70,
  "manual_override": false,
  "heartbeat": 1
}
```

### Base API Endpoints
- `GET /state` -> latest aggregated telemetry/config
- `POST /config` -> update mode/`k_factor`/limits
- `WS /telemetry` -> push stream at UI refresh rate

---

## 6. Non-Functional Requirements Mapping

| NFR | Design Control | Verification |
|---|---|---|
| NFR-001 Control Loop Timing | fixed-step loop at 100 Hz, bounded processing pipeline | loop timing logs |
| NFR-002 Command Scope Control | config validation, clamp invalid values | invalid-input tests |
| NFR-003 Protocol Extensibility | packet version field + reserved bytes | parser compatibility check |
| NFR-004 Link/Fault Robustness | heartbeat timeout, IMU validity checks, safe fallback mode | RF/IMU fault injection |
| NFR-005 Calibration Usability | persistent mode + `k` display, single-step apply action | 2-minute calibration walkthrough |

### Performance
- Response time target: Node A control loop keeps ~10 ms cycle budget at 100 Hz.
- Latency control: feature extraction and command generation stay in-process without network dependency.
- Monitoring: loop timing logs and telemetry interval checks.

### Scalability
- Scaling model: stateless Node B bridge process can be extended to handle additional glove nodes in future.
- Load profile: current deployment is 1 glove node at 10-20 Hz telemetry; protocol includes versioning for growth.
- Growth path: optional multi-node channel IDs and per-node session streams.

### Security
- Authentication scope: only trusted local base node is allowed to send control config to glove node.
- Input validation: all incoming config is range-checked and clamped before application.
- API protection: local-only bridge endpoint by default; reject malformed packets and log faults.

---

## 7. Technology Stack

- **MCU:** Raspberry Pi Pico 2 (RP2350 class)
- **Sensor:** BMI160 IMU (I2C)
- **Wireless:** nRF24L01+ (SPI)
- **Actuation:** N20 micro metal geared DC motor via driver stage
- **Firmware runtime:** C/C++ SDK or MicroPython-equivalent implementation
- **UI transport:** WebSocket or TCP from Node B
- **UI runtime:** browser dashboard or terminal fallback

---

## 8. Trade-off Analysis

1. **Zero-crossing frequency estimate vs FFT**
- Benefit: lower compute cost, quick implementation.
- Cost: lower spectral detail and more noise sensitivity.
- Decision: chosen for 20-hour schedule and sufficient demo fidelity.

2. **Two-node split vs single-node design**
- Benefit: isolation of deterministic control from UI/network overhead.
- Cost: extra integration complexity.
- Decision: chosen for reliability and requirement clarity.

3. **N20 motor tactile output vs quieter actuator alternatives**
- Benefit: clear physical feedback.
- Cost: noise and power-noise management complexity.
- Decision: chosen based on available hardware and demo visibility.

---

## 9. Deployment Architecture

```text
[Glove Pico Node A]
  - mounted with IMU + motor driver + N20 motor
  - powered by local regulated rail
  - communicates via nRF24

[Base Pico Node B]
  - connected to PC over USB serial/network bridge
  - runs RF bridge and API service

[PC]
  - displays dashboard and sends calibration config
```

### Deployment Notes
- keep motor power rail separated from logic where possible.
- enforce common ground between pico/radio/driver.
- run short-range RF setup for judge demo reliability.

---

## 10. Future Considerations

- multi-motor blending by weighted axis contributions
- optional FFT mode for richer frequency profiling
- persistent per-user calibration profiles
- formal gate-check and test automation expansion
