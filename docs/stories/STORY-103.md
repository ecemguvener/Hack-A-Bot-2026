# Zero-Crossing Tremor Frequency Estimator

- **ID:** STORY-103
- **Epic:** Tremor Sensing Core
- **Priority:** Must Have
- **Story Points:** 2
- **Status:** Not Started

## User Story
As a **control loop**
I want to **estimate tremor frequency from zero-crossings on filtered dominant axis**
So that **motor frequency can track tremor behavior in real time**

## Acceptance Criteria
- [ ] Dominant axis signal is filtered (HP/BP) before counting.
- [ ] Frequency uses `(zero_crossings / 2) / window_seconds`.
- [ ] Frequency estimate is smoothed to reduce jitter.
- [ ] Output is bounded to safe expected range.

## Technical Notes
### Files/Modules Affected
- `node_a/features_frequency.*`
- `node_a/filter.*`

### Testing Requirements
- [ ] known-frequency synthetic signal test
- [ ] jitter comparison before/after smoothing
- [ ] bounds enforcement test
