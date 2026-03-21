# VibraARM: Adaptive Tremor Counter-Stimulation
> Keep it simple and reliable. A stable demo beats extra features.

## 1) Problem and User
People with Parkinsonian tremor (and related hand instability conditions) struggle with fine hand control in daily tasks. Static supports are not user-adaptive.

Primary user: person with tremor who needs session-level stabilization support.

## 2) What We Built
- Node A (`Pico #1`, glove node)
  - Reads BMI160 at fixed rate (target 100 Hz)
  - Estimates tremor dominant axis, sign, frequency, and magnitude
  - Chooses opposing motor based on direction map
  - Drives N20 motor frequency as `f_motor = k_factor * f_tremor`
- Node B (`Pico #2`, base node)
  - Receives telemetry over nRF24
  - Forwards telemetry to PC UI (web/terminal)
  - Sends config updates back (mode, `k_factor`, intensity limit)

## 3) Core Demo Claim
VibraARM demonstrates real-time closed-loop tremor sensing and user-adjustable counter-stimulation with live telemetry.

Safety claim boundary: session-level assistive prototype only (not a clinical efficacy claim).

## 4) Live Demo Protocol
> Use this exact flow and rehearse it multiple times. Avoid last-minute changes.
1. Start in normal mode, collect live tremor metrics.
2. Show dominant axis -> opposing motor selection.
3. Switch to calibration mode in UI.
4. Tune `k_factor` live while viewing frequency/magnitude plots.
5. Return to normal mode and show updated response.

## 5) Why Two Picos
- Node A stays deterministic for sensing/control.
- Node B handles bridge/UI/config without blocking control loop.
- Meets mandatory two-Pico wireless coordination requirement.

## 6) Key Engineering Decisions
- Frequency estimation by zero-crossings on filtered dominant axis (low compute, robust enough for hackathon timeline).
- Dominant direction from per-axis RMS/variance over rolling window.
- Closed-loop motor frequency mapping: `f_motor = k * f_t`.
- Configurable calibration mode to personalize `k` per user.

## 7) Reliability and Safety
> Show one safety behavior live (for example RF drop -> motor stop).
- RF timeout -> safe fallback (motors off or low-safe pattern)
- IMU invalid -> stop motor output
- Clamp motor frequency and duty cycle to safe limits
- Use default config if no RF config is received

## 8) Evidence Table (Fill During Testing)
| Trial | Mode | f_tremor (Hz) | Magnitude | Axis | Motor | k | f_motor (Hz) | Notes |
|---|---:|---:|---:|---|---|---:|---:|---|
| 1 | Normal |  |  |  |  |  |  |  |
| 2 | Calibration |  |  |  |  |  |  |  |
| 3 | Normal |  |  |  |  |  |  |  |

## 9) Quick Links
- Product brief: `docs/bmad/product-brief.md`
- Block diagram: `docs/bmad/block-diagram.md`
- Wiring diagram: `docs/bmad/wiring-diagram.md`
- Control-flow sketch: `docs/bmad/control-flow.md`
- Judging checklist: `docs/bmad/judging-checklist.md`
