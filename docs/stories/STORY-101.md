# BMI160 Fixed-Rate Sampling Pipeline

- **ID:** STORY-101
- **Epic:** Tremor Sensing Core
- **Priority:** Must Have
- **Story Points:** 2
- **Status:** Not Started

## User Story
As a **control firmware module**
I want to **sample BMI160 at fixed 100 Hz and keep a rolling window**
So that **all downstream tremor calculations use stable and timely data**

## Acceptance Criteria
- [ ] Sampling loop runs at target 100 Hz cadence.
- [ ] Rolling buffer stores 1-2 seconds of latest samples.
- [ ] Buffer update has no overflow/underflow during 5-minute run.
- [ ] Timestamping is consistent and monotonic.

## Technical Notes
### Implementation Approach
Use fixed timestep scheduling with elapsed-time compensation. Write samples into ring buffer.

### Files/Modules Affected
- `node_a/imu_service.*`
- `node_a/ring_buffer.*`
- `node_a/main_loop.*`

### Edge Cases
- IMU startup delay: block processing until first valid sample.
- Sample dropout: flag invalid sample state.

### Testing Requirements
- [ ] 100 Hz timing log test
- [ ] ring buffer bounds test
- [ ] 5-minute stability run
