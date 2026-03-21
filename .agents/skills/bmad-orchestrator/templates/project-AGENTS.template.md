# Project BMAD Agent Contract (OpenAI Codex)

This project uses BMAD skills through OpenAI Codex.

## Skill Resolution

- Project-local skills: `<project>/.agents/skills`
- Global skills fallback: `~/.agents/skills`

When both locations contain the same skill name, use project-local behavior for this project.

## Workflow Intents

Use these prompts to trigger BMAD flows:

- `bmad:init` to initialize project BMAD artifacts.
- `bmad:status` to read current workflow status.
- `bmad:next` to get the recommended next action.
- `bmad:create-story` and `bmad:dev-story` for implementation flow.

## Project Artifacts

- `bmad/project.yaml`
- `bmad/workflow-status.yaml`
- `bmad/sprint-status.yaml`
- `docs/bmad/*.md`
- `docs/stories/STORY-*.md`

## Language Policy

Read language settings from `bmad/project.yaml`:

- `language.communication_language` for assistant chat responses  with `English` fallback.
- `language.document_output_language` for generated project artifacts under `docs/` with `English` fallback.

## Editing Rule

Use `yq` for deterministic YAML updates in scripts and automation.
