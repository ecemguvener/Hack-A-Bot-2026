# Builder Reference

Reference patterns for creating new BMAD skills and workflows.

## Required Skill Metadata

Every generated `SKILL.md` must have frontmatter:

```yaml
---
name: skill-name
description: Clear trigger-oriented description for when to use this skill.
---
```

Guidelines:

- `name`: lowercase kebab-case
- `description`: include intent and activation context
- keep body concise and operational

## Minimal Skill Structure

```text
new-skill/
├── SKILL.md
├── agents/
│   └── openai.yaml
├── scripts/        (optional)
├── templates/      (optional)
└── resources/      (optional)
```

## Workflow Contract Pattern

For each workflow variant, define:

- trigger intent
- required inputs
- output artifact path
- quality gate
- next handoff intent

## Script Policy

Use scripts only when deterministic behavior is needed repeatedly.

- shell scripts for filesystem and CLI glue
- Python scripts for stable logic where shell is brittle

## Validation Checklist

- metadata valid
- trigger intent clear
- output path explicit
- templates and scripts linked from `SKILL.md`
- no runtime-specific deprecated dependencies
