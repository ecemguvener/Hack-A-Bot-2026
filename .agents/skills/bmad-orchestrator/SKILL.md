---
name: bmad-orchestrator
description: Orchestrates Codex BMAD workflows. Use for bmad:init, bmad:status, and bmad:next to manage project setup, state tracking, and phase routing.
---

# BMAD Orchestrator

## Trigger Intents

- `bmad:init`
- `bmad:status`
- `bmad:next`

## Workflow Variants

1. `init`
- Initialize project BMAD artifacts and baseline state.

2. `status`
- Summarize workflow progress and current phase readiness.

3. `next`
- Recommend the next workflow intent from current state.

## Inputs

- repository root and target project root
- existing BMAD files under `bmad/`
- project level and phase state from YAML artifacts

## Language Guard (Mandatory)

Enforce language selection separately for chat responses and generated artifacts.

Chat language (`communication_language`) fallback order:

1. `language.communication_language` from `bmad/project.yaml`
2. `English`

Rules for chat responses:

- Use the resolved chat language for all assistant responses (questions, status updates, summaries, and handoff notes).
- Do not switch chat language unless the user explicitly requests a different language in the current thread.

Artifact language (`document_output_language`) fallback order:

1. `language.document_output_language` from `bmad/project.yaml`
2. `English`

Rules for generated artifacts:

- Use the resolved artifact language for all generated BMAD documents and structured artifacts.
- write prose and field values in the resolved document language
- avoid mixed-language requirement clauses with English modal verbs (for example, `System shall` followed by non-English text)
- allow English acronyms/abbreviations in non-English sentences (for example, `API`, `SLA`, `KPI`, `OAuth`, `WCAG`)
- Keep code snippets, CLI commands, file paths, and identifiers in their original technical form.

## Mandatory Reference Load

Before executing `init`, `status`, or `next`, read `REFERENCE.md` first.
Treat `REFERENCE.md` as required context for routing, sequencing, and state handling.

## Output Contract

- `bmad/project.yaml`
- `bmad/workflow-status.yaml`
- `bmad/sprint-status.yaml`
- status summary and next-intent recommendation

## Core Workflow

1. Initialize state files and directories (`init`).
2. Read YAML state and show completion by phase (`status`).
3. Compute next recommended intent by project level and completion (`next`).
4. Route to phase skill with explicit handoff context.

## Script Selection

Primary scripts:

- Init project:
  ```bash
  bash scripts/init-project.sh --name "MyApp" --type web-app --level 2
  ```
- Show status:
  ```bash
  bash scripts/show-status.sh bmad/workflow-status.yaml
  ```
- Recommend next:
  ```bash
  bash scripts/recommend-next.sh bmad/workflow-status.yaml
  ```

Compatibility wrappers:

- `scripts/check-status.sh` -> wrapper to `show-status.sh`
- `scripts/validate-config.sh` -> project config structural validation

Shared state helpers are in `../bmad-shared/scripts/`.

## Template Map

- `templates/project.template.yaml`
- Why: orchestrator-owned project config template used by `init-project.sh`.

- `templates/workflow-status.template.yaml`
- Why: orchestrator-owned workflow status template used by `init-project.sh`.

- `templates/sprint-status.template.yaml`
- Why: orchestrator-owned sprint status template used by `init-project.sh`.

## Reference Map

- `REFERENCE.md`
- Must read first for routing logic and orchestration heuristics.

- `resources/workflow-phases.md`
- Use for phase-level guidance and sequencing.

- `../bmad-shared/workflows.registry.yaml`
- Use for intent mapping and level-based routing rules.

## Error Handling

- Missing `bmad/workflow-status.yaml` -> recommend `bmad:init`
- Invalid YAML or missing required fields -> report exact file and key
- State mismatch across files -> normalize via shared update script

## Handoff Rules

When routing to another skill, include:

- project level
- current phase
- completed and required workflows
- expected output artifact path
