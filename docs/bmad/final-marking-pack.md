# Final Marking Pack (100-Point Target)

Use this during final judging. It is written to map directly to the official Project 6 rubric.

## Project Snapshot
- Project: VibraArm (Assistive Tech)
- Core idea: user-specific tremor stabilisation glove
- Node A (Glove Pico): IMU sensing + closed-loop counter-vibration motor control
- Node B (Base Pico): wireless bridge + config manager + laptop telemetry/UI bridge
- Wireless requirement: satisfied (two Pico boards coordinated over wireless telemetry/config)

---

## A. Rubric-Exact Scoring Strategy

## 1) Problem Definition and Solution Fit (30)
### What judges need to hear
- Clear user: person with tremor (Parkinsonian/hand instability)
- Clear pain point: involuntary hand movement reduces daily task ability
- Clear mechanism: measure tremor + apply opposing vibration profile
- Why this is assistive tech: improves control, safety, confidence for hand tasks

### What to show live
- One sentence user story
- Hand movement -> measurable tremor metrics in UI
- Motor response tied to detected tremor

### Risk that loses points
- Over-claiming medical outcomes (avoid clinical cure claims)
- Vague “AI” claims without direct demo evidence

### High-score language to use
- “This is a personalized real-time assistive control prototype, not a clinical treatment.”
- “We tune per user during calibration and then run that profile in closed loop.”

---

## 2) Live Demo and Effectiveness (25)
### What judges need to see
- Core loop works in front of them, repeatedly
- Data and actuation are synchronized
- Mode switches work (normal, calibration, continuous_on, off)

### Required demo sequence (2-3 min)
1. Baseline hand movement shown
2. UI updates in real time (`f_tremor`, magnitude, `f_motor`)
3. Calibration tune (`k_factor`, intensity limit)
4. Apply profile and show stable behavior
5. Show safety OFF mode immediately stops output

### Reliability tactics
- Keep one operator on hardware only
- Keep one operator on UI/commands only
- Start all services before judges arrive

---

## 3) Technical Implementation and Engineering Quality (20)
### What to highlight
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
### What to emphasize
- User-specific profile tuning workflow
- Continuous-on profile for controlled experiments
- Safe-off profile for immediate stop
- Two-node architecture separating real-time control from UI/monitoring

### Avoid weak framing
- Don’t present it as generic “vibration glove” only
- Frame as configurable closed-loop assistive control with personal calibration

---

## 5) Communication and Supporting Documentation (10)
### Judge-facing artifacts (show quickly)
- Root README: project story + setup + demo flow
- Block diagram: `docs/bmad/block-diagram.md`
- Wiring map: `docs/bmad/wiring-diagram.md`
- This file: rubric execution plan

### What to say while showing docs
- “We documented architecture, wiring, control strategy, safety behavior, and demo runbook so replication is straightforward.”

---

## B. Judging Requirements Compliance

## Two-Pico wireless requirement
- Met: Node A and Node B communicate wirelessly with telemetry/config packets

## Live core function requirement
- Met if demo shows: tremor sensing -> control output -> visible effect -> mode/safety controls

---

## C. Exact Demo Script (Speaker Roles)

## Speaker 1 (Problem + Fit) ~30s
- “Our user is someone with involuntary hand tremor. The key problem is reduced control during daily tasks.”
- “VibraArm measures tremor in real time and applies opposing motor vibration tuned to the user.”

## Speaker 2 (Architecture) ~35s
- “Pico A on the glove runs 100 Hz sensing and control.”
- “Pico B receives telemetry, sends config updates, and bridges data to our live UI.”

## Speaker 3 (Live demo controls) ~70s
- Start hand movement
- Show live metrics in UI
- Change `k_factor` / `intensity_limit`
- Toggle modes: calibration -> normal -> continuous_on -> off

## Speaker 4 (Tradeoffs + Safety + Close) ~35s
- “We prioritized reliability and safe bounded output for live operation.”
- “Off mode forces immediate motor stop; intensity remains clamped.”
- “This demonstrates a practical user-specific assistive control pipeline.”

---

## D. Demo Day Checklist (Run this 10 min before judging)

## Hardware
- Glove Pico powered and running `final_proj.py`
- Base Pico connected to laptop and running `receiver.py`
- Common ground verified
- RF modules powered and responding

## Laptop services
- Dashboard server running (`python3 -m http.server 5500` or 5501)
- Bridge running on correct serial port (`serial_ws_bridge.py`)
- UI connected to `ws://127.0.0.1:8080/telemetry`

## Functional checks
- Telemetry numbers changing live
- Config updates change behavior
- `off` command immediately stops motors

---

## E. Fallback Plan (If something breaks during judging)

## If UI fails
- Continue with serial telemetry output from Base Pico terminal
- Demonstrate mode/config commands directly (`k=...`, `mode=...`, `on`, `off`)

## If wireless becomes noisy
- Move nodes closer and re-run mode switch + telemetry proof
- Prioritize stable core loop demonstration over optional features

## If one feature glitches
- Keep narrative focused on demonstrated working pipeline
- Explicitly state what is working now and what is future work

---

## F. Judge Q&A Cheat Sheet

## Q: How is this user-specific?
A: Calibration mode tunes `k_factor` and intensity per user response, then normal mode runs that profile in closed loop.

## Q: What is your control law?
A: Detect tremor frequency and magnitude, map dominant direction to opposing motor, then drive `f_motor = k_factor * f_tremor` with bounded intensity.

## Q: How do you handle safety?
A: Intensity clamps, explicit OFF mode, and separation of local control from external UI.

## Q: Why two Pico boards?
A: One handles deterministic wearable control, the other handles communication/monitoring/config to improve reliability and modularity.

---

## G. Scoring Self-Check (last-minute)

- Problem statement clear in first 20 seconds
- User group stated explicitly
- Two-node wireless requirement visibly demonstrated
- Core loop repeatedly demonstrated live
- Safety mode shown
- Tradeoffs explained without over-claiming
- Documentation artifacts shown quickly

