# BMAD Orchestrator Reference

Detailed routing, state, and transition rules for the orchestrator skill.

## State Files

- `bmad/project.yaml`
- `bmad/workflow-status.yaml`
- `bmad/sprint-status.yaml`

## Routing Logic

Use this order when recommending the next intent:

1. If no workflow state file exists -> `bmad:init`
2. If `product_brief` is pending and required/recommended -> `bmad:product-brief`
3. Planning gate:
- level 0-1 -> `bmad:tech-spec`
- level 2-4 -> `bmad:prd`
4. If UX is recommended and still pending -> `bmad:ux-design`
5. If architecture required and pending -> `bmad:architecture`
6. If gate check recommended and pending -> `bmad:gate-check`
7. If sprint planning pending -> `bmad:sprint-plan`
8. If no stories planned -> `bmad:create-story`
9. If stories remain -> `bmad:dev-story`
10. Otherwise -> `bmad:status`

## Phase Requirements by Level

- Level 0-1:
  - required: `tech_spec`, `sprint_planning`
  - optional/recommended: `product_brief`, `research`, `ux_design`, `architecture`

- Level 2-4:
  - required: `product_brief`, `prd`, `architecture`, `sprint_planning`
  - optional/recommended: `research`, `brainstorm`, `ux_design`, `gate_check`

## Init Behavior

`init-project.sh` should:

1. create `bmad/`, `docs/bmad/`, and `docs/stories/`
2. render:
- `bmad/project.yaml`
- `bmad/workflow-status.yaml`
- `bmad/sprint-status.yaml`
3. set level-dependent status placeholders
4. return a machine-readable summary with `next_intent=bmad:status`

## Status Behavior

`show-status.sh` should present:

- project name and level
- current phase and progress metrics
- required/recommended/pending/completed markers
- next intent from `next-workflow.sh`

## Config Precedence

When multiple config sources are available:

1. explicit command argument
2. project-local `bmad/project.yaml`
3. default values from scripts

## Failure Handling

- Missing YAML file: fail with exact path and fix hint.
- Missing `yq`: fail with installation requirement.
- Unknown workflow key: fail fast with supported keys.
- Inconsistent status: normalize via `update-workflow-status.sh`.
