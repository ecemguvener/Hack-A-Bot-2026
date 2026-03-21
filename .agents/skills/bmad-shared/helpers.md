# BMAD Shared Helpers

Operational notes for shared state scripts.

## Source of Truth

- `bmad/workflow-status.yaml` controls phase/workflow completion.
- `bmad/sprint-status.yaml` controls sprint/story progress.
- `bmad/project.yaml` controls level and path conventions.

## Status Update Rules

After completing a workflow:

1. set `completed: true`
2. set `completed_at` timestamp
3. set `output_file` if applicable
4. recalculate metrics
5. update `current_phase` if required

Use:

```bash
bash scripts/update-workflow-status.sh --workflow <id> --status-file bmad/workflow-status.yaml
```

## Next Recommendation Rules

`next-workflow.sh` should prefer:

1. required pending workflows
2. recommended pending workflows
3. implementation progression (`create-story` -> `dev-story`)

## Config Read Rules

- Use project config for local decisions.
- Use global config only for defaults.
- Never assume missing keys; always fallback explicitly.

## Failure Rules

- missing file -> explicit path in error output
- missing `yq` -> explicit install requirement
- unsupported workflow key -> explicit supported list

## Script Compatibility

Wrappers are kept for backward invocation:

- `load-config.sh`
- `update-status.sh`
- `check-phase.sh`

Prefer direct use of non-wrapper scripts in new workflows.
