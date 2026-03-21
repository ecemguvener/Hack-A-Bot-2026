# Product Brief: VibraARM Closed-Loop Tremor Support
> This is an engineering prototype for session-level assistive support, not a clinical efficacy claim.

- **Date:** 2026-03-21
- **Author:** Hack-A-Bot Team
- **Status:** Draft
- **Version:** 0.2

---

## 1. Executive Summary

VibraARM is an assistive embedded prototype that detects tremor features in real time and drives opposing vibration feedback on a wearable node. The system uses two Raspberry Pi Pico 2 boards with nRF24 wireless coordination: one glove node for closed-loop sensing/control and one base node for monitoring, UI bridge, and calibration updates.

**Key Points:**
- Problem: users with hand tremor need adaptive support beyond static aids.
- Solution: closed-loop tremor estimation + opposing motor actuation with user-calibrated multiplier `k`.
- Target Users: people with Parkinsonian tremor (primary), caregivers/clinicians (secondary).
- Timeline: 20-hour hackathon implementation with live measurable demo.

---

## 2. Problem Statement

### The Problem

Involuntary tremor motion reduces fine motor control and confidence during everyday tasks. Static supports (for example weighted accessories) do not adapt to changing tremor direction/frequency per user.

### Who Experiences This Problem

People with Parkinsonian tremor and related hand-instability conditions.

**Primary Users:**
- People with Parkinsonian tremor
- Users needing short-session hand stability assistance
- Users who benefit from lightweight wearable support

**Secondary Users:**
- Caregivers
- Rehabilitation support staff

### Current Situation

**How Users Currently Handle This:**
Static weighted supports and non-adaptive routines.

**Pain Points:**
- No direction-specific response
- No user-specific frequency calibration
- Limited real-time feedback about effectiveness

### Impact & Urgency

**Impact if Unsolved:**
Lower task confidence and reduced functional independence in daily hand activities.

**Why Now:**
Clear assistive-tech fit for Project 6 with measurable, live, two-node embedded control.

**Frequency:**
Tremor effects occur repeatedly throughout daily activity.

---

## 3. Target Users

### User Personas

#### Persona 1: Daily Independent User
- **Role:** Person living with tremor
- **Goals:** Improve hand steadiness in short tasks
- **Pain Points:** Inconsistent hand control and frustration
- **Technical Proficiency:** Low to medium
- **Usage Pattern:** Multiple short assist sessions

#### Persona 2: Caregiver-Assisted User
- **Role:** User supported by caregiver
- **Goals:** Configure and reuse stable settings safely
- **Pain Points:** Hard to tune one fixed setting for varying tremor patterns
- **Technical Proficiency:** Low
- **Usage Pattern:** Supervised sessions with periodic recalibration

### User Needs

**Must Have:**
- Real-time tremor feature extraction
- Direction-aware opposing motor selection
- Adjustable calibration factor `k`

**Should Have:**
- Live telemetry and mode visibility
- Safe fallback behavior on faults

**Nice to Have:**
- Saved per-user calibration presets
- Session history export

---

## 4. Proposed Solution

### Solution Overview

VibraARM runs a closed-loop controller on the glove Pico. It samples BMI160 at fixed rate, computes dominant tremor axis/sign and magnitude, estimates tremor frequency with a low-compute zero-crossing method, then drives an opposing N20 motor using `f_motor = k * f_tremor`. The base Pico forwards telemetry to a PC UI and sends calibration/config commands back.

### Key Capabilities

1. **Real-Time Tremor Estimation**
   - Description: rolling-window axis analysis and frequency estimation.
   - User Value: dynamic response based on actual movement.

2. **Opposing Motor Selection**
   - Description: dominant axis/sign mapped to opposite-side motor.
   - User Value: targeted directional counter-stimulation.

3. **User Calibration Mode**
   - Description: UI-driven tuning of `k_factor` and limits.
   - User Value: personalized behavior per user.

4. **Wireless Monitoring + Control**
   - Description: nRF24 telemetry/config between glove and base nodes.
   - User Value: transparent operation and easier tuning.

5. **Safety-Focused Output Control**
   - Description: clamped frequency/duty and fault fallback.
   - User Value: predictable behavior under failures.

### What Makes This Different

Combines real-time directional tremor mapping with user-tuned closed-loop frequency scaling in a dual-node low-cost embedded system.

**Unique Value Proposition:**
User-calibrated closed-loop tremor counter-stimulation with real-time telemetry in a practical two-Pico architecture.

### Minimum Viable Solution

**Core Features for MVP:**
- BMI160 sampling at 100 Hz with rolling window
- Dominant-axis + zero-crossing tremor frequency estimate
- Opposing N20 motor actuation with `f_motor = k * f_t`
- Base-node telemetry bridge and calibration mode controls

**Deferred to Later:**
- Multi-motor advanced blending strategy
- Clinical validation workflow

---

## 5. Success Metrics

### Primary Metrics

**Tremor Frequency Tracking Stability**
- Baseline: raw estimate variance without smoothing
- Target: stable `f_tremor` trend in real-time view
- Timeline: live session
- Measurement: rolling estimate jitter and continuity

**Directional Motor Selection Correctness**
- Baseline: no direction-aware mapping
- Target: dominant axis/sign correctly mapped to opposing motor in demo cases
- Timeline: live session
- Measurement: expected axis -> motor activation checks

**Closed-Loop Responsiveness**
- Baseline: static motor pattern
- Target: `f_motor` follows `k * f_tremor` under changing motion
- Timeline: live session
- Measurement: telemetry consistency between `f_t`, `k`, and `f_motor`

### Secondary Metrics

- RF packet reliability
- Number of fallback events
- Calibration convergence time for usable `k`

### Success Criteria

**Must Achieve:**
- Stable two-Pico wireless operation during live demo
- Real-time telemetry shows valid `f_tremor`, magnitude, axis, motor, and `f_motor`

**Should Achieve:**
- Calibration mode demonstrates user-adjusted `k` changing motor behavior predictably
- Fault behavior demonstrated (timeout or safe-stop)

---

## 6. Market & Competition

### Market Context

**Market Size:**
Assistive movement-support demand is growing with aging populations and chronic motor disorders.

**Market Trends:**
- Shift from passive supports to adaptive assistive devices
- Demand for low-cost edge solutions
- Preference for private/local processing in personal health contexts

**Target Market Segment:**
Wearable assistive tremor support prototypes for home and supervised care contexts.

### Competitive Landscape

#### Competitor 1: Weighted supports
- **Strengths:** inexpensive, simple
- **Weaknesses:** no adaptation, no telemetry
- **Pricing:** low
- **Market Position:** passive baseline option

#### Competitor 2: Premium specialized devices
- **Strengths:** polished ecosystems
- **Weaknesses:** cost and accessibility barriers
- **Pricing:** medium-high
- **Market Position:** specialized products

#### Competitor 3: Software-only guidance apps
- **Strengths:** easy distribution
- **Weaknesses:** no direct physical response
- **Pricing:** low-medium
- **Market Position:** indirect support

### Competitive Advantages

- Direction-aware response from on-device sensing
- User-calibrated closed-loop factor tuning
- Transparent real-time telemetry for calibration and debugging

---

## 7. Business Model

- **Primary model:** affordable wearable kit + companion interface
- **Secondary model:** caregiver/clinic setup profiles
- **Pilot path:** maker/rehab community trials and feedback

---

## 8. Technical Considerations

- Hardware: 2x Pico 2, BMI160, 2x nRF24, N20 micro geared motor + driver stage
- Loop rate: 100 Hz target on glove node
- Estimation method: rolling-window RMS/variance + filtered zero-crossings
- RF protocol: telemetry (10-20 Hz) + config on change
- Modes: `NORMAL`, `CALIBRATION`, `SAFE`

---

## 9. Risks & Mitigation

- **Risk:** RF reliability under noise
  - **Mitigation:** heartbeat, timeout, local safe defaults
- **Risk:** noisy frequency estimate
  - **Mitigation:** dominant-axis filtering + moving average smoothing
- **Risk:** motor power/noise coupling into logic
  - **Mitigation:** separate motor power rail, common ground, clamped drive

---

## 10. Resource Estimates

- **Team:** 4 members
- **Build Window:** 20 hours
- **Core Workstreams:**
  - glove control firmware
  - RF bridge + PC interface
  - motor driver + power integration
  - test protocol + documentation

---

## 11. Dependencies

- Stable BMI160 sample timing
- Motor driver stage for N20 (do not drive directly from Pico pin)
- Reliable nRF24 communication both directions
- PC-side realtime visualization path

---

## 12. Next Steps

1. Freeze final pinout and packet structs.
2. Bring up RF telemetry/config link first.
3. Implement dominant-axis + zero-crossing estimator.
4. Add calibration mode controls from PC UI.
5. Run baseline/calibration/normal demo rehearsals and log evidence table.
