# Motor Frequency + Intensity Control

- **ID:** STORY-202
- **Epic:** Closed-Loop Actuation
- **Priority:** Must Have
- **Story Points:** 3
- **Status:** Not Started

## User Story
As a **controller**
I want to **compute and apply bounded motor commands from tremor features**
So that **output remains safe while adapting in real time**

## Acceptance Criteria
- [ ] `f_motor = k_factor * f_tremor` is implemented.
- [ ] `f_motor` is clamped to `[f_min, f_max]`.
- [ ] Duty/intensity scales with tremor magnitude and intensity limit.
- [ ] Command updates remain stable without oscillatory spikes.

## Technical Notes
### Files/Modules Affected
- `node_a/motor_control.*`
- `node_a/safety_limits.*`

### Testing Requirements
- [ ] formula correctness test
- [ ] clamp behavior test
- [ ] hardware run with varying `k_factor`
