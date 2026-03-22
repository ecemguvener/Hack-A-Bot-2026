# Final Marking Pack (100-Point Target)


## Project Snapshot
- Project: VibraArm (Assistive Tech)
- Core idea: user-specific tremor stabilisation glove
- Node A (Glove Pico): IMU sensing + closed-loop counter-vibration motor control
- Node B (Base Pico): wireless bridge + config manager + laptop telemetry/UI bridge
- Wireless requirement: satisfied (two Pico boards coordinated over wireless telemetry/config)


## 1) Problem Definition and Solution Fit (30)
- Clear user: person with tremor (Parkinsonian/hand instability)
- Clear pain point: involuntary hand movement reduces daily task ability
- Clear mechanism: measure tremor + apply opposing vibration profile
- Why this is assistive tech: improves control, safety, confidence for hand tasks

### What to show live
- Hand movement -> measurable tremor metrics in UI
- Motor response tied to detected tremor

- “This is a personalized real-time assistive control prototype, not a clinical treatment.”
- “We tune per user during calibration and then run that profile in closed loop.”

---

## 2) Live Demo and Effectiveness (25)
- Core loop works in front of them, repeatedly
- Data and actuation are synchronized
- Mode switches work (normal, calibration, continuous_on, off)

1. Baseline hand movement shown
2. UI updates in real time (`f_tremor`, magnitude, `f_motor`)
3. Calibration tune (`k_factor`, intensity limit)
4. Apply profile and show stable behavior
5. Show safety OFF mode immediately stops output


## 3) Technical Implementation and Engineering Quality (20)
- Deterministic loop on glove at 100 Hz
- IMU processing: axis/sign, frequency estimate, magnitude
- Opposing-motor mapping logic
- Wireless bidirectional data path
- JSON bridge to UI for observability and tuning

### Architecture evidence
- `hackabot2026-steadiARM/final_proj.py` -> control node
- `hackabot2026-steadiARM/receiver.py` -> base/bridge node
- `dashboard/serial_ws_bridge.py` + dashboard UI

### Engineering tradeoff statement
- “We selected computationally light signal estimation and robust mode control to maximize live reliability under hackathon constraints.”
---

## 4) Innovation and Creativity (15)
- User-specific profile tuning workflow
- Continuous-on profile for controlled experiments
- Safe-off profile for immediate stop
- Two-node architecture separating real-time control from UI/monitoring

---

## 5) Communication and Supporting Documentation (10)
- Root README: project story + setup + demo flow
- Block diagram: `docs/bmad/block-diagram.md`
- Wiring map: `docs/bmad/wiring-diagram.md`
- This file: rubric execution plan

- “We documented architecture, wiring, control strategy, safety behavior, and demo runbook so replication is straightforward.”

---

## Two-Pico wireless requirement
- Met: Node A and Node B communicate wirelessly with telemetry/config packets

## Live core function requirement
- Met if demo shows: tremor sensing -> control output -> visible effect -> mode/safety controls
