# Config Channel + Mode Switching

- **ID:** STORY-302
- **Epic:** Wireless Telemetry and Config
- **Priority:** Must Have
- **Story Points:** 3
- **Status:** Not Started

## User Story
As an **operator**
I want to **send mode and calibration config from base to glove**
So that **I can tune behavior without reflashing firmware**

## Acceptance Criteria
- [ ] Node B sends config packet on change events.
- [ ] Node A applies `mode`, `k_factor`, and limits live.
- [ ] Mode transitions (`NORMAL`, `CALIBRATION`, `SAFE`) are stable.
- [ ] RF timeout triggers safe fallback mode.

## Technical Notes
### Files/Modules Affected
- `node_b/config_tx.*`
- `node_a/config_rx.*`
- `node_a/state_machine.*`

### Testing Requirements
- [ ] live mode switch test
- [ ] `k_factor` update propagation test
- [ ] RF timeout fallback test
