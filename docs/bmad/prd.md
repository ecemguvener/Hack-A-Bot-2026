# Product Requirements Document (PRD)

- **Project Name:** VibraARM Closed-Loop Tremor Support
- **Document Version:** 0.1
- **Date:** 2026-03-21
- **Author:** Hack-A-Bot Team
- **Status:** Draft

---

## Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 0.1 | 2026-03-21 | Hack-A-Bot Team | Initial PRD draft |

## Approvals

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Product Owner | Team Lead | Pending | 2026-03-21 |
| Engineering Lead | Embedded Lead | Pending | 2026-03-21 |
| Design Lead | UI Lead | Pending | 2026-03-21 |
| Stakeholder | Demo Judge Panel | Pending | 2026-03-21 |

---

## Executive Summary

**Problem Statement:**
People with Parkinsonian tremor need adaptive support for session-level hand stabilization. Static supports do not adapt to changing tremor direction or frequency.

**Proposed Solution:**
A dual-node embedded system using Raspberry Pi Pico 2 boards. Node A runs real-time tremor sensing and closed-loop motor control. Node B bridges telemetry/config to a PC UI and supports calibration mode.

**Business Value:**
Demonstrates a low-cost, explainable, user-calibrated assistive architecture with clear market relevance and strong live-demo evidence.

**Success Metrics:**
- Stable and valid tremor frequency telemetry in real time
- Correct dominant-axis to opposing-motor mapping in test cases
- Predictable `f_motor = k * f_tremor` behavior under mode/config changes

**Target Launch:** Hackathon final judging session (within 20-hour build window)

---

## Project Overview

### Background
This project is built for Hack-A-Bot Project 6 Creative, which requires two Pico boards and wireless coordination in a problem-driven assistive prototype.

### Current State
Available options in scope are mostly static supports and non-adaptive routines. Team has hardware kit with Pico 2, BMI160, nRF24, and N20 motor.

### Desired State
A reliable wearable closed-loop prototype that measures tremor features, selects opposing motor response, and allows user calibration through a companion UI.

### Stakeholders
| Stakeholder | Role | Interest | Influence |
|-------------|------|----------|-----------|
| End User | Primary user | Better session-level hand stability | High |
| Caregiver | Secondary user | Safer and repeatable setup | Medium |
| Hackathon Judges | Evaluators | Clear problem-solution fit and technical quality | High |
| Team Engineers | Builders | Reliable implementation in 20 hours | High |

---

## Goals and Objectives

### Business Goals
1. Deliver a high-scoring assistive-tech demo with measurable outcomes.
2. Demonstrate practical two-node wireless embedded architecture.
3. Show a credible path toward personalized assistive interaction.

### User Goals
1. Receive adaptive support based on detected tremor behavior.
2. Tune system behavior in calibration mode without reflashing firmware.
3. See transparent live metrics and mode/status feedback.

### Success Criteria
- Core closed loop runs continuously at target sample rate.
- UI can switch modes and update `k_factor` in real time.
- Safety fallback behavior works on RF/IMU fault.

---

## User Personas

### Primary Persona: Daily Independent User
**Demographics:** Adult user with Parkinsonian tremor.

**Goals:**
- Improve steadiness during short tasks.
- Use a simple calibration process.

**Pain Points:**
- Tremor direction and intensity vary over time.
- Static support is inconsistent.

**Behaviors:**
- Performs short repeated hand tasks.
- Prefers minimal setup overhead.

### Secondary Persona: Caregiver/Support User
**Demographics:** Family member or support person assisting setup.

**Goals:**
- Configure mode and calibration quickly.
- Monitor whether system is running correctly.

**Pain Points:**
- Hard to judge if settings are helping.
- Needs clear status and safe defaults.

---

## Functional Requirements

### FR-001: IMU Sampling and Rolling Buffer [MUST]

**Description:**
System shall sample BMI160 at fixed rate (target 100 Hz) and maintain a 1-2 second rolling window.

**Acceptance Criteria:**
- Sampling loop runs at configured fixed interval with bounded jitter.
- Rolling window updates continuously without overflow.
- Node A exposes latest window-ready flag for processing.

**Priority:** MUST  
**Related Epic:** EPIC-1

---

### FR-002: Dominant Axis and Sign Detection [MUST]

**Description:**
System shall compute per-axis tremor magnitude (RMS or variance) and choose dominant axis and sign.

**Acceptance Criteria:**
- Dominant axis is selected from x/y/z each processing cycle.
- Axis sign is computed and available for mapping.
- Telemetry includes dominant axis enum and sign.

**Priority:** MUST  
**Related Epic:** EPIC-1

---

### FR-003: Tremor Frequency Estimation via Zero-Crossing [MUST]

**Description:**
System shall estimate tremor frequency from filtered dominant-axis signal using zero-crossing count over window.

**Acceptance Criteria:**
- Frequency uses formula `(zero_crossings / 2) / window_seconds`.
- Estimate is smoothed to reduce jitter.
- Telemetry includes `f_tremor_hz` value.

**Priority:** MUST  
**Related Epic:** EPIC-1

---

### FR-004: Opposing Motor Selection [MUST]

**Description:**
System shall map dominant axis/sign to an opposing motor output channel.

**Acceptance Criteria:**
- Mapping table is explicit and configurable in firmware.
- Selected motor ID is included in telemetry.
- Motor selection changes when axis/sign changes.

**Priority:** MUST  
**Related Epic:** EPIC-2

---

### FR-005: Closed-Loop Motor Frequency Control [MUST]

**Description:**
System shall compute motor frequency as `f_motor = k_factor * f_tremor` and clamp to safety bounds.

**Acceptance Criteria:**
- `k_factor` is read from current config.
- `f_motor` is bounded by `f_min` and `f_max`.
- Motor drive updates within control-cycle timing budget.

**Priority:** MUST  
**Related Epic:** EPIC-2

---

### FR-006: Magnitude-Based Intensity Scaling [SHOULD]

**Description:**
System should scale motor duty/intensity based on tremor magnitude with global limit.

**Acceptance Criteria:**
- Magnitude-to-duty mapping is monotonic and bounded.
- Global intensity limit can cap computed duty.
- Telemetry reports effective duty/intensity.

**Priority:** SHOULD  
**Related Epic:** EPIC-2

---

### FR-007: Telemetry from Node A to Node B [MUST]

**Description:**
Node A shall transmit telemetry packets at 10-20 Hz.

**Acceptance Criteria:**
- Packet contains: timestamp, mode, `f_tremor`, magnitude, axis/sign, motor ID, `f_motor`, `k_factor`, fault flags.
- Node B parses packet without blocking RX loop.
- Packet sequence continuity can be observed in logs.

**Priority:** MUST  
**Related Epic:** EPIC-3

---

### FR-008: Config from Node B to Node A [MUST]

**Description:**
Node B shall send config updates on user change events.

**Acceptance Criteria:**
- Config includes mode and `k_factor`.
- Optional fields include intensity limit and manual override.
- Node A applies new config without reboot.

**Priority:** MUST  
**Related Epic:** EPIC-3

---

### FR-009: Calibration Mode Workflow [MUST]

**Description:**
System shall support calibration mode where user adjusts `k_factor` in real time.

**Acceptance Criteria:**
- UI can switch between `NORMAL` and `CALIBRATION`.
- Calibration mode continues telemetry streaming.
- User-selected `k_factor` persists when returning to `NORMAL`.

**Priority:** MUST  
**Related Epic:** EPIC-4

---

### FR-010: Real-Time UI Visualization and Controls [SHOULD]

**Description:**
PC UI should display telemetry and provide calibration controls.

**Acceptance Criteria:**
- UI displays `f_tremor`, magnitude, `f_motor`, mode, active motor, `k_factor`.
- UI control changes propagate to Node A through Node B.
- UI update latency remains acceptable for demo understanding.

**Priority:** SHOULD  
**Related Epic:** EPIC-4

---

### FR-011: Safety Fallback on Fault [MUST]

**Description:**
System shall enter safe behavior on RF timeout or IMU invalid state.

**Acceptance Criteria:**
- RF timeout triggers motor stop or low-safe pattern.
- Invalid IMU sample triggers motor stop/benign output.
- Fault state is visible in telemetry/UI.

**Priority:** MUST  
**Related Epic:** EPIC-5

---

## Non-Functional Requirements

### Performance Requirements

#### NFR-001: Control Loop Timing [MUST]

**Description:**
Node A control loop must maintain target cadence for sensing and actuation.

**Acceptance Criteria:**
- Loop target is 100 Hz under normal operation.
- Processing completes within loop budget in steady state.

**Measurement Method:** Loop timing logs and timestamp deltas.

---

### Security Requirements

#### NFR-002: Command Scope Control [SHOULD]

**Description:**
Only expected config fields should be accepted from Node B packets.

**Acceptance Criteria:**
- Unknown packet fields are ignored safely.
- Out-of-range values are clamped/rejected.

**Compliance:** Internal protocol safety policy for demo build.

---

### Scalability Requirements

#### NFR-003: Protocol Extensibility [COULD]

**Description:**
Packet format should support future additional motors/metrics.

**Acceptance Criteria:**
- Reserved/version fields exist in packet schema.
- Parser remains backward-compatible with current fields.

**Load Profile:** Single active glove node, telemetry 10-20 Hz.

---

### Reliability Requirements

#### NFR-004: Link and Fault Robustness [MUST]

**Description:**
System must fail safely under communication or sensor errors.

**Acceptance Criteria:**
- RF heartbeat timeout threshold configurable.
- Fault flags emitted within one telemetry interval.

**Target SLA:** Demonstration run completes without uncontrolled actuation.

---

### Usability Requirements

#### NFR-005: Calibration Usability [SHOULD]

**Description:**
Calibration controls should be understandable to non-expert users.

**Acceptance Criteria:**
- Mode and `k_factor` always visible in UI.
- User can complete one calibration cycle in under 2 minutes.

**Measurement Method:** Timed practice run with checklist.

---

## Epics and User Stories

### EPIC-1: Tremor Sensing and Feature Extraction
**Goal:** derive dominant axis, magnitude, and frequency in real time.

- STORY-101: As a system, I sample BMI160 at fixed rate to keep a valid rolling window.
- STORY-102: As a system, I detect dominant axis/sign from per-axis RMS/variance.
- STORY-103: As a system, I estimate `f_tremor` using zero-crossings and smoothing.

### EPIC-2: Closed-Loop Motor Response
**Goal:** drive opposing motor behavior tied to detected tremor.

- STORY-201: As a system, I map axis/sign to opposing motor ID.
- STORY-202: As a system, I compute `f_motor = k_factor * f_tremor` with clamps.
- STORY-203: As a system, I scale duty by magnitude and intensity limit.

### EPIC-3: Wireless Bridge and Protocol
**Goal:** exchange telemetry/config reliably between nodes.

- STORY-301: As Node A, I send telemetry at 10-20 Hz.
- STORY-302: As Node B, I parse telemetry and keep latest state.
- STORY-303: As Node B, I send config changes to Node A.

### EPIC-4: Calibration and UI
**Goal:** allow user to tune `k_factor` with live feedback.

- STORY-401: As a user, I toggle `NORMAL`/`CALIBRATION` mode.
- STORY-402: As a user, I adjust `k_factor` and observe response.
- STORY-403: As a user, I finalize and persist selected `k_factor`.

### EPIC-5: Safety and Fault Handling
**Goal:** keep behavior bounded and safe under failures.

- STORY-501: As a system, I stop/limit motor on RF timeout.
- STORY-502: As a system, I stop/limit motor on IMU invalid data.
- STORY-503: As a system, I expose fault flags to UI.

### UI Requirements
- UI-001: display live `f_tremor`, magnitude, `f_motor`, motor ID, mode, `k_factor`.
- UI-002: controls for mode switch and `k_factor` adjustment.
- UI-003: visible connection/fault status badge.

### User Flows
- Flow 1: Normal operation telemetry view.
- Flow 2: Enter calibration, adjust `k`, return to normal.
- Flow 3: Fault simulation and safe fallback indication.

---

## User Experience Requirements

- Real-time graph updates should be legible and stable.
- Numeric indicators must include units (Hz, normalized magnitude).
- Mode changes must be obvious and confirmed in UI state.

---

## Success Metrics

1. Valid tremor frequency and magnitude stream visible continuously during demo.
2. Correct opposing motor selection for at least three directional test motions.
3. `f_motor` tracks `k_factor * f_tremor` within configured bounds.
4. Calibration cycle completes and selected `k_factor` persists.
5. Safe fallback triggers correctly for forced RF/IMU fault test.

---

## Assumptions and Dependencies

### Assumptions
- BMI160 provides sufficiently stable samples at target rate.
- N20 motor can be driven reliably through dedicated driver stage.
- nRF24 link quality is sufficient for room-scale demo.

### Dependencies
- Hardware: 2x Pico 2, 2x nRF24, BMI160, N20 motor, motor driver, power modules.
- Firmware libraries: IMU driver, RF driver, timing/PWM primitives.
- UI channel: WebSocket/HTTP/TCP bridge from Node B to PC.

---

## Constraints

- 20-hour hackathon implementation window.
- Must use both Pico boards with wireless coordination.
- Must prioritize reliability and clear live demonstration.

---

## Out of Scope

- Clinical validation and long-term efficacy claims.
- Medical certification and production safety compliance.
- Advanced ML/FFT-heavy adaptation beyond current timeline.
- Full mobile app ecosystem.

---

## Release Planning

### Milestone 1: Core Link and Data
- Bring up RF packets both directions.
- Stream raw/processed telemetry to Node B.

### Milestone 2: Closed Loop
- Complete axis/frequency estimation.
- Implement motor mapping and drive equation.

### Milestone 3: Calibration + UI
- Add mode switch and `k_factor` tuning.
- Validate end-to-end behavior.

### Milestone 4: Demo Hardening
- Add fault handling validation.
- Rehearse fixed demo script.

---

## Risks and Mitigations

- **Risk:** noisy frequency estimate causing unstable motor updates  
  **Mitigation:** smoothing, clamp limits, window tuning.

- **Risk:** RF packet loss during demo  
  **Mitigation:** heartbeat timeout, safe fallback, short-range setup.

- **Risk:** motor noise affecting logic rails  
  **Mitigation:** separate motor power path, common ground, decoupling.

- **Risk:** UI instability  
  **Mitigation:** keep a minimal fallback terminal dashboard.

---

## Traceability Matrix

| Requirement | Epic | Story | Verification |
|---|---|---|---|
| FR-001, FR-002, FR-003 | EPIC-1 | STORY-101/102/103 | Loop logs + telemetry plots |
| FR-004, FR-005, FR-006 | EPIC-2 | STORY-201/202/203 | Motor ID/frequency checks |
| FR-007, FR-008 | EPIC-3 | STORY-301/302/303 | RF packet inspection |
| FR-009, FR-010 | EPIC-4 | STORY-401/402/403 | UI interaction test |
| FR-011, NFR-004 | EPIC-5 | STORY-501/502/503 | Fault injection demo |

---

## Appendix

### Glossary
- `f_tremor`: estimated tremor frequency (Hz)
- `f_motor`: commanded motor frequency (Hz)
- `k_factor`: calibration multiplier from UI

### Open Questions
- Final UI transport choice: WebSocket vs TCP
- Final motor frequency clamp limits by user comfort testing
