# NeuroCalm Adaptive Tremor Support

## 1) Problem and User
People with Parkinsonian hand tremor struggle with hand stability during short daily tasks. Static aids (for example weighted gloves) are not personalized to each user’s movement pattern.

This prototype provides adaptive assistive feedback using two coordinated Pi Pico nodes.

Primary user: person with Parkinsonian tremor.

## 2) What We Built
- Node A (Pico A): wearable/device-side sensing and control node
  - Reads BMI160 IMU at 100 Hz
  - Computes tremor features and stability metrics
  - Runs adaptive support selection
  - Drives haptic/actuation output
- Node B (Pico B): companion/supervisor node
  - Wireless control over nRF24L01+
  - Profile and mode selection
  - OLED telemetry display

## 3) Core Demo Claim
NeuroCalm demonstrates real-time personalized adaptive support that improves short-session hand stability compared to baseline.

Safety claim boundary: this is a prototype for session-level support, not a clinical long-term treatment claim.

## 4) Live Demo Protocol (Judge-Friendly)
1. Baseline run (no assist): 30-60s hand stability task.
2. Assisted run (adaptive enabled): same task duration and setup.
3. Display and report:
- Tremor amplitude proxy
- Smoothness score
- Stability score
- Wireless link status

## 5) Why Two Picos
- Separation of responsibilities improves reliability:
  - Node A remains real-time and safety-focused.
  - Node B handles UI and supervision.
- Clean wireless architecture directly satisfies project requirement.

## 6) Engineering Decisions and Tradeoffs
- Decision: 100 Hz loop for IMU/control
  - Tradeoff: lower CPU margin but better responsiveness.
- Decision: local adaptation at edge (no cloud)
  - Tradeoff: simpler model but low latency and robust offline behavior.
- Decision: fixed demo protocol with baseline vs assisted comparison
  - Tradeoff: narrower scope but stronger evidence for judging.

## 7) Reliability Features
- RF heartbeat and timeout handling
- Safe fallback mode on link/sensor fault
- Output clamping/rate limiting to avoid unstable actuation

## 8) Evidence Table (Fill During Testing)
| Trial | Mode | Amplitude | Smoothness | Stability | Notes |
|---|---|---:|---:|---:|---|
| 1 | Baseline |  |  |  |  |
| 1 | Assisted |  |  |  |  |
| 2 | Baseline |  |  |  |  |
| 2 | Assisted |  |  |  |  |
| 3 | Baseline |  |  |  |  |
| 3 | Assisted |  |  |  |  |

## 9) Quick Links
- Product brief: `docs/bmad/product-brief.md`
- Block diagram: `docs/bmad/block-diagram.md`
- Wiring diagram: `docs/bmad/wiring-diagram.md`
- Control-flow sketch: `docs/bmad/control-flow.md`
