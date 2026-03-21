# BMAD Workflow Phases

Reference for phase intent mapping and expected outputs.

## Phase 1: Analysis

Intents:

- `bmad:product-brief`
- `bmad:research`
- `bmad:brainstorm`

Primary outputs:

- `docs/bmad/product-brief.md`
- `docs/bmad/research-report.md`
- `docs/bmad/brainstorm.md`

## Phase 2: Planning

Intents:

- `bmad:prd`
- `bmad:tech-spec`
- `bmad:prioritize`
- `bmad:ux-design`

Primary outputs:

- `docs/bmad/prd.md`
- `docs/bmad/tech-spec.md`
- `docs/bmad/prioritization.md`
- `docs/bmad/ux-design.md`

## Phase 3: Solutioning

Intents:

- `bmad:architecture`
- `bmad:gate-check`

Primary outputs:

- `docs/bmad/architecture.md`
- `docs/bmad/gate-check.md`

## Phase 4: Implementation

Intents:

- `bmad:sprint-plan`
- `bmad:create-story`
- `bmad:dev-story`
- `bmad:code-review`

Primary outputs:

- `docs/bmad/sprint-plan.md`
- `docs/stories/STORY-*.md`
- code and tests in repository
- optional `docs/bmad/code-review.md`

## Transition Rules

- Do not skip required level-dependent artifacts.
- Prefer small incremental progress and explicit state updates.
- After each completed workflow, update `bmad/workflow-status.yaml`.
