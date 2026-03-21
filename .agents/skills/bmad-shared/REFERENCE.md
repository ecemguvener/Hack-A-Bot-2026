# BMAD Shared Reference

This reference defines shared YAML contracts and script usage for BMAD state operations.

## Files

- `workflows.registry.yaml`

## Script Semantics

- `scripts/load-project-config.sh [config_file] [text|json|export]`
  - reads project config safely with `yq`

- `scripts/load-global-config.sh [config_file] [text|json|export]`
  - reads global config safely with `yq`

- `scripts/update-workflow-status.sh --workflow <id> --status-file <path> [--output <path>] [--passed true|false]`
  - updates completion flags, timestamps, phase status, and progress metrics

- `scripts/next-workflow.sh [status_file] [text|json]`
  - returns next recommended BMAD intent from current state

## Compatibility Wrappers

- `scripts/load-config.sh` -> `load-project-config.sh`
- `scripts/update-status.sh` -> `update-workflow-status.sh`
- `scripts/check-phase.sh` -> `next-workflow.sh`

## State Rules

- use `yq` v4+ for all YAML access
- update derived metrics after each workflow completion
- do not infer progress from document filenames alone
- treat `bmad/workflow-status.yaml` as source of truth for phase progress

## Error Handling Guidelines

- missing file: return explicit path in error
- missing tool (`yq`): stop and report requirement
- invalid workflow key: fail fast with supported values
