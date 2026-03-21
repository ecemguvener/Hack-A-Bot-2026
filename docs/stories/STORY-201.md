# Opposing Motor Mapping

- **ID:** STORY-201
- **Epic:** Closed-Loop Actuation
- **Priority:** Must Have
- **Story Points:** 2
- **Status:** Not Started

## User Story
As a **controller**
I want to **map tremor axis/sign to an opposing motor channel**
So that **counter-stimulation direction is predictable and explainable**

## Acceptance Criteria
- [ ] Axis/sign to motor mapping table is defined in config.
- [ ] Selected motor ID changes correctly with axis/sign changes.
- [ ] Selected motor ID is included in telemetry.

## Technical Notes
### Files/Modules Affected
- `node_a/motor_mapper.*`
- `node_a/config.*`

### Testing Requirements
- [ ] mapping table unit tests
- [ ] axis/sign transition test
