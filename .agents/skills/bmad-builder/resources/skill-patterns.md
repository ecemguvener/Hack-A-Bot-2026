# Skill Patterns

Practical patterns for BMAD skill design.

## Pattern 1: Intent-First Skill

Use this when one role supports multiple workflows.

Required sections in `SKILL.md`:

- Trigger Intents
- Workflow Variants
- Inputs
- Language Guard (Mandatory)
- Mandatory Reference Load
- Output Contract
- Script Selection
- Template Map
- Reference Map
- Quality Gates

Every BMAD skill must include `Language Guard (Mandatory)` with explicit separation:

- chat language: resolve from `language.communication_language` in `bmad/project.yaml` with `English` fallback
- docs language: resolve from `language.document_output_language` in `bmad/project.yaml` with `English` fallback

## Pattern 2: Progressive Disclosure

Keep `SKILL.md` concise, and move details to references:

- `SKILL.md`: operational flow and decisions
- `REFERENCE.md`: detailed rationale and heuristics
- `resources/*`: domain-specific techniques

## Pattern 3: Deterministic State Updates

For YAML state workflows:

- read with `yq`
- update with `yq -i`
- fail on missing tools or missing files
- keep output machine-parseable where possible

## Pattern 4: Artifact-Driven Workflow

Each workflow variant should write one predictable artifact path.

Examples:

- `docs/bmad/product-brief.md`
- `docs/bmad/architecture.md`
- `docs/stories/STORY-*.md`

## Pattern 5: Validation Hook

Include at least one validation command in `Script Selection`.

Examples:

- `bash scripts/validate-brief.sh <file>`
- `bash scripts/validate-prd.sh <file>`
- `bash scripts/validate-architecture.sh <file>`
