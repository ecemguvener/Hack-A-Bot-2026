# Communication Checklist (10/10 Target)
> Assign one speaker for architecture and one for demo operation.

## During Judging (2-3 minutes)
1. Problem (20s): tremor support need and user context.
2. Architecture (30s): glove Pico closed loop + base Pico bridge.
3. Control method (40s): dominant-axis detection + zero-crossing frequency + opposing motor selection + `f_motor = k*f_t`.
4. Calibration mode (30s): UI tunes `k` live and sends config back.
5. Safety/tradeoffs (30s): why zero-crossing over FFT, fallback behavior, clamping.
6. Live evidence (30s): real-time plots + active motor + mode + k.

## Must-Say Lines
- "This is a real-time closed-loop assistive prototype with user-specific calibration."
- "Node A is deterministic control, Node B is communication and UI bridge."
- "If RF or IMU fails, we enter safe fallback and clamp/stop motor output."

## Tradeoff Table
| Choice | Benefit | Cost | Why accepted |
|---|---|---|---|
| Zero-crossing frequency estimate | low compute, fast implementation | lower spectral detail than FFT | reliable for 20-hour timeline |
| Dominant-axis RMS/variance method | simple, interpretable motor mapping | less nuanced than full model | clear demo behavior |
| N20 motor with bounded drive | strong tactile output | motor noise and power management | practical with available parts |

## Artifact Set to Present
- README: `docs/bmad/README.md`
- Block diagram: `docs/bmad/block-diagram.md`
- Wiring map: `docs/bmad/wiring-diagram.md`
- Control-flow: `docs/bmad/control-flow.md`
- Product brief: `docs/bmad/product-brief.md`
