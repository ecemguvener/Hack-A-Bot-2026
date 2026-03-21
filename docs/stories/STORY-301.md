# Telemetry Packet TX/RX

- **ID:** STORY-301
- **Epic:** Wireless Telemetry and Config
- **Priority:** Must Have
- **Story Points:** 2
- **Status:** Not Started

## User Story
As a **base station**
I want to **receive structured telemetry from glove node at 10-20 Hz**
So that **the UI can show live tremor and control behavior**

## Acceptance Criteria
- [ ] Node A sends telemetry packet with required fields.
- [ ] Node B parses packets and updates latest state.
- [ ] Packet loss does not crash parsing loop.
- [ ] Sequence/timestamp continuity is visible in logs.

## Technical Notes
### Files/Modules Affected
- `node_a/rf_tx.*`
- `node_b/rf_rx.*`
- `shared/protocol.*`

### Testing Requirements
- [ ] packet schema compatibility test
- [ ] sustained RX test (5+ minutes)
