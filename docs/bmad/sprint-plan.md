# Sprint Plan: VibraARM Closed-Loop Tremor Support

- **Sprint Number:** 1
- **Sprint Dates:** 2026-03-21 - 2026-03-22
- **Sprint Duration:** 20 hours
- **Created:** 2026-03-21

## Sprint Overview

**Sprint Goal:** Deliver a reliable end-to-end demo of closed-loop tremor sensing, opposing motor actuation, and calibration mode with live telemetry.

**Sprint Capacity:** 20 story points  
**Stories Planned:** 8 stories  
**Total Story Points:** 20 points

**Capacity Calculation:**
- **Base capacity:** 4 people x ~5 focused hours each equivalent = 20 points
- **Adjustments:** high integration overhead and hardware uncertainty
- **Final capacity:** 20 points

## Velocity Metrics

**Historical Velocity:**
- Sprint 1 is baseline (no previous data)
- Planning target: 20 points

**Team Composition:**
- 4 builders
- 20 total build hours available
- ~1 point per focused team-hour equivalent for this event sprint

## Sprint Backlog

### Epic 1: Tremor Sensing Core (6 points)

**Epic Goal:** stable and usable tremor feature extraction on Node A.

#### STORY-101: BMI160 Fixed-Rate Sampling Pipeline
- **Priority:** Must Have
- **Points:** 2
- **Status:** Not Started
- **Dependencies:** None
- **Brief:** Implement 100 Hz sampling loop and rolling window buffer.

#### STORY-102: Dominant Axis + Magnitude Extraction
- **Priority:** Must Have
- **Points:** 2
- **Status:** Not Started
- **Dependencies:** STORY-101
- **Brief:** Compute per-axis RMS/variance and identify dominant axis/sign.

#### STORY-103: Zero-Crossing Tremor Frequency Estimator
- **Priority:** Must Have
- **Points:** 2
- **Status:** Not Started
- **Dependencies:** STORY-102
- **Brief:** Estimate `f_tremor` from filtered dominant-axis signal.

---

### Epic 2: Closed-Loop Actuation (5 points)

**Epic Goal:** map tremor features to bounded opposing motor drive.

#### STORY-201: Opposing Motor Mapping
- **Priority:** Must Have
- **Points:** 2
- **Status:** Not Started
- **Dependencies:** STORY-102
- **Brief:** Map axis/sign to opposing motor output channel.

#### STORY-202: Motor Frequency + Intensity Control
- **Priority:** Must Have
- **Points:** 3
- **Status:** Not Started
- **Dependencies:** STORY-103, STORY-201
- **Brief:** Implement `f_motor = k_factor * f_tremor` with clamps and intensity limit.

---

### Epic 3: Wireless Telemetry and Config (5 points)

**Epic Goal:** complete reliable Node A <-> Node B data exchange.

#### STORY-301: Telemetry Packet TX/RX
- **Priority:** Must Have
- **Points:** 2
- **Status:** Not Started
- **Dependencies:** STORY-101
- **Brief:** Send telemetry at 10-20 Hz and parse on base node.

#### STORY-302: Config Channel + Mode Switching
- **Priority:** Must Have
- **Points:** 3
- **Status:** Not Started
- **Dependencies:** STORY-301
- **Brief:** Push mode/`k_factor` updates from base node to glove node.

---

### Epic 4: Calibration + Demo UI (4 points)

**Epic Goal:** show live charts and calibration workflow.

#### STORY-401: UI Dashboard + Calibration Control
- **Priority:** Should Have
- **Points:** 2
- **Status:** Not Started
- **Dependencies:** STORY-301, STORY-302
- **Brief:** Display `f_tremor`, magnitude, `f_motor`, axis, mode, `k` and allow updates.

#### STORY-402: Safety/Fault Demo Path
- **Priority:** Should Have
- **Points:** 2
- **Status:** Not Started
- **Dependencies:** STORY-202, STORY-302
- **Brief:** Demonstrate safe fallback on RF timeout/invalid IMU.

---

## Story Prioritization

### Must Have (Critical Path)
1. STORY-101 (2)
2. STORY-102 (2)
3. STORY-103 (2)
4. STORY-201 (2)
5. STORY-202 (3)
6. STORY-301 (2)
7. STORY-302 (3)

**Total Must Have:** 16 points

### Should Have
1. STORY-401 (2)
2. STORY-402 (2)

**Total Should Have:** 4 points

### Could Have
- none in this sprint

## Implementation Order

1. **Hour 0-3:** STORY-101 + STORY-301
   - Rationale: prove sensor loop and RF path early.

2. **Hour 3-7:** STORY-102 + STORY-103
   - Rationale: feature extraction foundation before actuation tuning.

3. **Hour 7-11:** STORY-201 + STORY-202
   - Rationale: complete closed-loop behavior after stable features.

4. **Hour 11-14:** STORY-302
   - Rationale: calibration path requires config channel.

5. **Hour 14-17:** STORY-401
   - Rationale: UI for observability and judge communication.

6. **Hour 17-20:** STORY-402 + rehearsals
   - Rationale: safety demo and reliability hardening.

## Story Dependencies

```text
STORY-101 -> STORY-102 -> STORY-103 -> STORY-202
                  \-> STORY-201 ------/
STORY-101 -> STORY-301 -> STORY-302 -> STORY-401
                                \-> STORY-402
```

### Critical Path Stories
- STORY-101, STORY-102, STORY-103, STORY-201, STORY-202, STORY-301, STORY-302

### External Dependencies
- N20 driver wiring availability and stable power rail.
- PC connectivity and UI runtime setup.

## Risks and Mitigation

### Risk 1: Noisy telemetry due to motor power interference
- **Probability:** Medium
- **Impact:** High
- **Mitigation:** separate motor power path + common ground + filtering
- **Contingency:** run lower duty and shorter cable for demo

### Risk 2: Frequency estimate unstable
- **Probability:** Medium
- **Impact:** Medium
- **Mitigation:** moving-average smoothing and bounds
- **Contingency:** fallback to conservative fixed `k` demo mode

### Risk 3: UI path instability
- **Probability:** Medium
- **Impact:** Medium
- **Mitigation:** keep terminal fallback dashboard
- **Contingency:** present live metrics via serial output

## Sprint Milestones

- **Hour 4:** RF link and IMU loop proven
- **Hour 10:** closed-loop actuation functional
- **Hour 15:** calibration mode and UI connected
- **Hour 20:** full scripted demo with safety behavior

## Definition of Done

A story is complete when:
- [ ] Acceptance criteria met
- [ ] Integrated with dependent node(s)
- [ ] Tested on hardware (not only unit logic)
- [ ] Demo path updated
- [ ] Notes/docs updated

## Sprint Ceremonies (Hackathon-lite)

### Check-ins
- Every 2-3 hours, 5-minute sync: progress, blockers, next handoff.

### Demo Rehearsal
- Final 2 hours: repeat full script 3 times.

## Success Criteria

1. End-to-end mode switching and telemetry works live.
2. `f_motor` tracks `k_factor * f_tremor` with bounds.
3. Judge-facing calibration workflow runs without reset.
4. Fault behavior is visible and controlled.

## Burndown Tracking

| Time | Completed | Remaining | Ideal Remaining | Notes |
|------|-----------|-----------|-----------------|-------|
| H0 | 0 | 20 | 20 | Sprint start |
| H5 | 4 | 16 | 15 | Link + sampling online |
| H10 | 10 | 10 | 10 | Closed-loop functional |
| H15 | 15 | 5 | 5 | Calibration path working |
| H20 | 20 | 0 | 0 | Demo-ready |

## Team Capacity

### Team Members
- **Member 1:** Node A firmware (IMU/features/control)
- **Member 2:** Node B bridge + protocol
- **Member 3:** UI + calibration controls
- **Member 4:** Integration, power, testing, demo script

**Total Developer-Days:** hackathon compressed; 20-hour shared sprint

## Notes

- Keep scope frozen after Hour 15.
- Reliability beats feature count for judging.
- If blocked, prioritize must-have chain first.
