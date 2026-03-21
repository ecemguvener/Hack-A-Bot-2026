# Communication Checklist (10/10 Target)

## During Judging (2-3 minutes)
1. Problem (20s): who the user is and what fails today.
2. Architecture (30s): two Pico roles + wireless coordination.
3. Control strategy (30s): how adaptation works at high level.
4. Safety/tradeoffs (30s): what you chose and why.
5. Live evidence (60s): baseline vs assisted with metrics.

## Must-Say Lines
- "This is a session-level assistive prototype with personalized adaptive support."
- "We separate real-time control (Node A) from supervision/UI (Node B) for reliability."
- "If link/sensor fails, the system enters safe fallback mode."

## Tradeoff Table (Show Verbally)
| Choice | Benefit | Cost | Why accepted |
|---|---|---|---|
| Edge adaptation on-device | low latency, no cloud dependency | simpler model | reliable demo and privacy |
| Two-node split | robust architecture + requirement compliance | more integration work | higher engineering quality |
| Fixed demo protocol | clear measurable proof | less feature breadth | maximizes judge confidence |

## Artifact Set to Present
- README: `docs/bmad/README.md`
- Block diagram: `docs/bmad/block-diagram.md`
- Wiring map: `docs/bmad/wiring-diagram.md`
- Control-flow: `docs/bmad/control-flow.md`
- Product brief: `docs/bmad/product-brief.md`
