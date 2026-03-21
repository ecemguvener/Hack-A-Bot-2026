---
name: bmad-builder
description: Skill and workflow scaffolding skill for BMAD. Use for bmad:create-skill and bmad:create-workflow to extend BMAD with domain-specific capabilities.
---

# BMAD Builder

## Trigger Intents

- `bmad:create-skill`
- `bmad:create-workflow`

## Workflow Variants

1. `create-skill`
- Scaffold a new BMAD skill folder with minimal required files.

2. `create-workflow`
- Define workflow contract, artifacts, and trigger semantics for a domain task.

## Inputs

- capability goal and scope
- intended triggers/intents
- expected inputs, outputs, and quality checks

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

Before executing `create-skill` or `create-workflow`, read `REFERENCE.md` first.
Treat `REFERENCE.md` as required context before applying scaffold patterns.

## Output Contract

- new skill scaffold under `skills/`
- required files: `SKILL.md`, `agents/openai.yaml`
- optional files: `templates/`, `scripts/`, `resources/`

## Core Workflow

1. Define role, trigger semantics, and artifact contract.
2. Scaffold minimal structure.
3. Add deterministic scripts only where repeatability is required.
4. Validate frontmatter and trigger clarity.
5. Provide usage prompt and handoff rules.

## Script Selection

- Create scaffold:
  ```bash
  bash scripts/scaffold-skill.sh <skill-name>
  ```
- Validate resulting skill:
  ```bash
  bash scripts/validate-skill.sh <skill-dir>
  ```

## Template Map

- `templates/skill.template.md`
- Why: baseline structure for new skill instructions.

- `templates/workflow.template.md`
- Why: workflow contract template.

- `templates/document.template.md`
- Why: reusable artifact template.

## Reference Map

- `REFERENCE.md`
- Must read first for extended builder guidance and quality checks.

- `resources/skill-patterns.md`
- Use for naming, trigger, and structure patterns.

## Quality Gates

- skill metadata is valid and discoverable
- triggers and outputs are unambiguous
- generated structure is minimal and maintainable
- no runtime-specific legacy dependencies are introduced
