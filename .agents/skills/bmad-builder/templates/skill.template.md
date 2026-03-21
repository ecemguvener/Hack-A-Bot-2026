---
name: {{skill_name}}
description: {{description}} Trigger keywords - {{trigger_keywords}}
allowed-tools: {{allowed_tools}}
---

# {{Skill Display Name}}

**Role:** {{phase_or_domain}} specialist

**Function:** {{what_this_skill_does}}

## Responsibilities

- {{responsibility_1}}
- {{responsibility_2}}
- {{responsibility_3}}
- {{responsibility_4}}

## Core Principles

1. **{{principle_1_name}}** - {{principle_1_description}}
2. **{{principle_2_name}}** - {{principle_2_description}}
3. **{{principle_3_name}}** - {{principle_3_description}}
4. **{{principle_4_name}}** - {{principle_4_description}}

## Inputs

- `bmad/project.yaml` if available
- existing BMAD artifacts relevant to the selected workflow
- user constraints, assumptions, and target outcomes

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

Before executing any workflow variant, read `REFERENCE.md` first.
Treat `REFERENCE.md` as required context, then load only relevant supporting files.

## {{Workflow_Category_1}}

### {{Workflow_1_Name}}

**Purpose:** {{workflow_1_purpose}}

**Process:**
1. {{workflow_1_step_1}}
2. {{workflow_1_step_2}}
3. {{workflow_1_step_3}}
4. {{workflow_1_step_4}}

**See:** [REFERENCE.md](REFERENCE.md) for detailed workflow patterns

### {{Workflow_2_Name}}

**Purpose:** {{workflow_2_purpose}}

**Process:**
1. {{workflow_2_step_1}}
2. {{workflow_2_step_2}}
3. {{workflow_2_step_3}}

**See:** [REFERENCE.md](REFERENCE.md) for detailed workflow patterns

## {{Workflow_Category_2}}

### {{Workflow_3_Name}}

**Purpose:** {{workflow_3_purpose}}

**Process:**
1. {{workflow_3_step_1}}
2. {{workflow_3_step_2}}
3. {{workflow_3_step_3}}

**See:** [REFERENCE.md](REFERENCE.md) for detailed workflow patterns

## Available Scripts

{{script_descriptions}}

**Usage:**
```bash
./scripts/{{script_name}}.sh
```

## File Organization

{{file_organization_description}}

```
{{skill_directory_structure}}
```

## Installation Process

After creating or modifying this skill:

1. {{installation_step_1}}
2. {{installation_step_2}}
3. {{installation_step_3}}
4. Validate with: `./scripts/validate-skill.sh path/to/SKILL.md`
5. {{installation_step_4}}

## Integration Points

**Works with:**
- {{integration_point_1}}
- {{integration_point_2}}
- {{integration_point_3}}

## Token Optimization

{{token_optimization_notes}}

## Notes for LLMs

- Use TodoWrite to track workflow tasks
- {{llm_note_1}}
- {{llm_note_2}}
- {{llm_note_3}}
- {{domain_specific_guidance}}

## Example Use Cases

**{{use_case_1_name}}:**
- {{use_case_1_workflow_1}}
- {{use_case_1_workflow_2}}
- {{use_case_1_template}}

**{{use_case_2_name}}:**
- {{use_case_2_workflow_1}}
- {{use_case_2_workflow_2}}
- {{use_case_2_template}}

**{{use_case_3_name}}:**
- {{use_case_3_workflow_1}}
- {{use_case_3_workflow_2}}
- {{use_case_3_template}}
