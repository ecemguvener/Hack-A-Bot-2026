# Safety/Fault Demo Path

- **ID:** STORY-402
- **Epic:** Calibration + Demo UI
- **Priority:** Should Have
- **Story Points:** 2
- **Status:** Not Started

## User Story
As a **judge**
I want to **see safe behavior when faults occur**
So that **the engineering quality and reliability are credible**

## Acceptance Criteria
- [ ] Forced RF timeout shows safe fallback and visible status.
- [ ] Invalid IMU input path disables or limits motor output.
- [ ] Fault event is shown in UI/log output.

## Technical Notes
### Files/Modules Affected
- `node_a/safety_manager.*`
- `node_b/event_log.*`
- `ui/status_panel.*`

### Testing Requirements
- [ ] RF timeout drill
- [ ] sensor fault injection drill
- [ ] end-to-end safety demo rehearsal
