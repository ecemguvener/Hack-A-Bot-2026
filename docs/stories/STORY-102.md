# Dominant Axis + Magnitude Extraction

- **ID:** STORY-102
- **Epic:** Tremor Sensing Core
- **Priority:** Must Have
- **Story Points:** 2
- **Status:** Not Started

## User Story
As a **control loop**
I want to **compute dominant axis/sign and tremor magnitude from the window**
So that **motor selection can respond to tremor direction**

## Acceptance Criteria
- [ ] Per-axis RMS or variance is computed each update window.
- [ ] Dominant axis is selected from X/Y/Z.
- [ ] Axis sign is exported (+/-).
- [ ] Magnitude metric is emitted for telemetry and control.

## Technical Notes
### Implementation Approach
Compute RMS/variance over rolling window and choose max-energy axis.

### Files/Modules Affected
- `node_a/features_axis.*`
- `node_a/telemetry_encoder.*`

### Testing Requirements
- [ ] synthetic axis-injection test
- [ ] sign correctness check
- [ ] telemetry field verification
