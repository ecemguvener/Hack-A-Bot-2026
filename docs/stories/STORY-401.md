# UI Dashboard + Calibration Control

- **ID:** STORY-401
- **Epic:** Calibration + Demo UI
- **Priority:** Should Have
- **Story Points:** 2
- **Status:** Not Started

## User Story
As an **operator/judge audience**
I want to **see core telemetry and control calibration from one screen**
So that **the system behavior is understandable and tunable live**

## Acceptance Criteria
- [ ] UI shows `f_tremor`, magnitude, `f_motor`, axis, motor ID, mode, `k_factor`.
- [ ] Operator can update `k_factor` and send config.
- [ ] UI displays connection and fault status.

## Technical Notes
### Files/Modules Affected
- `node_b/api_bridge.*`
- `ui/dashboard.*`

### Testing Requirements
- [ ] live field update test
- [ ] config control round-trip test
