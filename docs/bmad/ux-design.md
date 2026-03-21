# UX Design Document

- **Project:** VibraARM Closed-Loop Tremor Support
- **Date:** 2026-03-21
- **Designer:** Hack-A-Bot Team
- **Version:** 1.0

---

## Table of Contents

1. [Design Overview](#design-overview)
2. [User Personas](#user-personas)
3. [User Flows](#user-flows)
4. [Wireframes](#wireframes)
5. [Component Specifications](#component-specifications)
6. [Accessibility Annotations](#accessibility-annotations)
7. [Responsive Behavior](#responsive-behavior)
8. [Design Tokens](#design-tokens)
9. [Developer Handoff Notes](#developer-handoff-notes)

---

## Design Overview

### Project Summary
VibraARM UX focuses on one job: help the operator monitor tremor telemetry in real time and safely tune calibration (`k_factor`) without interrupting the glove control loop.

### Design Goals
1. Make live state obvious: mode, link status, active motor, fault flags.
2. Make calibration fast: adjust `k_factor`, observe effect, commit.
3. Make mistakes hard: safe defaults, clear confirmation on critical actions.

### Success Metrics
- Operator can complete one calibration cycle in under 2 minutes.
- UI updates telemetry continuously without confusion.
- Mode/fault status can be read in under 2 seconds.

### Design Principles Applied
- **Operator-first:** one-screen control room view.
- **Low cognitive load:** large numbers, clear labels, stable chart layout.
- **Safety visibility:** explicit safe/fault indicators.
- **No hidden state:** mode and `k` always visible.

### Target Devices
- [ ] Mobile (320px - 767px)
- [ ] Tablet (768px - 1023px)
- [x] Desktop (1024px+)
- [ ] Native app (iOS/Android)
- [x] Web app (responsive)

---

## User Personas

### Primary Persona: Operator (Team Member)
**Demographics:** Student engineer running live demo.

**Goals:**
- Observe tremor and motor values in real time.
- Tune `k_factor` quickly in calibration mode.

**Pain Points:**
- Hard to trust data if charts jitter or labels are unclear.
- Last-minute wiring issues create stress.

**Device Usage:**
- Primary: Laptop browser
- Secondary: Terminal fallback

**Accessibility Needs:**
- Keyboard operable controls
- High contrast status badges

### Secondary Persona: Judge/Observer
**Demographics:** Judge watching short demo.

**Goals:**
- Understand what the system is doing quickly.
- See cause-effect from calibration changes.

**Pain Points:**
- Dense technical UI with unclear meaning.
- Hidden mode transitions.

---

## User Flows

### Flow 1: Normal Monitoring
**Goal:** Observe closed-loop behavior.

**Entry Point:** UI opens with Node B stream.

**Success Criteria:** Stable live telemetry and status visible.

```text
[Open Dashboard]
      |
      v
[Link Connected?] --No--> [Show DISCONNECTED + retry indicator]
      |
     Yes
      |
      v
[Live Metrics + Charts Updating]
      |
      v
[Operator/Judge observes f_tremor, magnitude, axis, motor, f_motor, k]
```

### Flow 2: Calibration Cycle
**Goal:** Find usable `k_factor`.

**Entry Point:** Operator clicks CALIBRATION mode.

**Success Criteria:** New `k` saved and normal mode resumed.

```text
[Normal Mode]
      |
      v
[Switch to Calibration]
      |
      v
[Adjust k slider/input]
      |
      v
[Send Config -> Node B -> Node A]
      |
      v
[Observe chart/values response]
      |
      v
[Accept k] -> [Switch to Normal]
```

### Flow 3: Fault Handling
**Goal:** Keep UI understandable during failures.

```text
[RF timeout or IMU invalid]
      |
      v
[Badge turns FAULT / SAFE]
      |
      v
[Motor output expected to stop/limit]
      |
      v
[Operator resolves issue]
      |
      v
[Status returns to NORMAL]
```

---

## Wireframes

### Screen 1: VibraARM Operator Dashboard

```text
┌───────────────────────────────────────────────────────────────────────────┐
│ VibraARM Dashboard                     Link: CONNECTED  Mode: NORMAL     │
├───────────────────────────────────────────────────────────────────────────┤
│ f_tremor (Hz): 5.2     Magnitude: 0.38     f_motor (Hz): 6.2     k: 1.2 │
│ Axis: X-               Active Motor: M2    Fault: NONE                  │
├───────────────────────────────────────────────────────────────────────────┤
│ [Tremor Frequency Chart]            [Tremor Magnitude Chart]            │
│      (last 30 s)                          (last 30 s)                   │
├───────────────────────────────────────────────────────────────────────────┤
│ [Motor Frequency Chart]             [Event Log: mode/fault/config]      │
├───────────────────────────────────────────────────────────────────────────┤
│ Mode: (•) Normal  ( ) Calibration                                        │
│ k_factor: [ 1.20 ]  [ - ] [slider================] [ + ] [Send Update]  │
│ intensity_limit: [ 70% ]                               [Apply] [Safe Stop]│
└───────────────────────────────────────────────────────────────────────────┘
```

### Screen 2: Calibration Focus Panel (optional overlay)

```text
┌───────────────────────────────────────────────┐
│ Calibration Mode                              │
├───────────────────────────────────────────────┤
│ Current k: 1.20                               │
│ Test k:    [1.35]  [Apply]                    │
│                                               │
│ Live response:                                │
│ - f_tremor: 5.4 Hz                            │
│ - f_motor:  7.3 Hz                            │
│ - Magnitude trend: ↓                          │
│                                               │
│ [Keep This k]   [Revert]   [Back to Normal]   │
└───────────────────────────────────────────────┘
```

---

## Component Specifications

### C-01 Status Bar
- Fields: link, mode, fault.
- States: `CONNECTED`, `DISCONNECTED`, `SAFE`, `FAULT`.
- Update frequency: every telemetry tick.

### C-02 KPI Cards
- Values: `f_tremor`, magnitude, `f_motor`, `k_factor`, axis, motor ID.
- Must include units for frequency.

### C-03 Telemetry Charts
- 30-second rolling line charts.
- Separate y-axis ranges per metric for readability.

### C-04 Calibration Controls
- `k_factor` numeric input + slider.
- `Send Update` button (manual commit).
- Optional `Apply on change` disabled by default.

### C-05 Safety Controls
- `Safe Stop` button visible at all times.
- Confirmation for mode changes from normal to calibration.

### C-06 Event Log
- Append-only recent events: mode switches, config updates, faults.

---

## Accessibility Annotations

- Keyboard navigation: all controls reachable by `Tab`; buttons by `Enter/Space`.
- Focus visibility: 2px outline minimum on active element.
- Contrast targets:
  - text >= 4.5:1
  - large text/status badges >= 3:1
- Color is never sole indicator:
  - status badges include text labels (`SAFE`, `FAULT`, etc.).
- Charts include numeric readouts for users who cannot rely on color/shape.
- Form labels explicit for `k_factor` and `intensity_limit`.

---

## Responsive Behavior

Primary target is desktop during judging. Secondary responsive support:

- **Desktop (1024px+):** full dashboard with 2x2 chart grid.
- **Tablet (768-1023px):** charts stack to 2 rows; controls remain visible.
- **Mobile (<768px):** monitoring-only simplified view; calibration disabled by default.

---

## Design Tokens

- **Typography**
  - Heading: 24px bold
  - KPI value: 28-32px monospace
  - Body: 16px
- **Spacing**
  - Base unit: 8px
  - Card padding: 16px
  - Grid gap: 16px
- **Color roles**
  - Primary: telemetry accent
  - Success: connected/normal
  - Warning: calibration active
  - Danger: fault/disconnected
- **Status shapes**
  - Pill badges for mode/link/fault

---

## Developer Handoff Notes

1. Keep telemetry parser decoupled from rendering logic.
2. Use throttled chart redraw (e.g., 5-10 FPS UI) while ingesting higher-rate data.
3. Display latest valid values even if one packet drops.
4. `Send Update` should produce explicit ACK/NAK state in UI.
5. Preserve a terminal fallback view if web UI fails.
6. Align field names with RF packet schema used in firmware.

