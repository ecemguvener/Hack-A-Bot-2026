#!/usr/bin/env bash
set -euo pipefail

STATUS_FILE="${1:-bmad/workflow-status.yaml}"
MODE="${2:-text}"

usage() {
  cat <<USAGE
Usage: $(basename "$0") [status_file] [text|json]

Defaults:
  status_file: bmad/workflow-status.yaml
  mode: text
USAGE
}

if [[ "$STATUS_FILE" == "-h" || "$STATUS_FILE" == "--help" ]]; then
  usage
  exit 0
fi

if ! command -v yq >/dev/null 2>&1; then
  echo "ERROR: yq v4+ is required" >&2
  exit 1
fi

emit() {
  local intent="$1"
  local reason="$2"

  if [[ "$MODE" == "json" ]]; then
    printf '{"next_intent":"%s","reason":"%s"}\n' "$intent" "$reason"
  else
    printf 'next_intent=%s\n' "$intent"
    printf 'reason=%s\n' "$reason"
  fi
}

if [[ ! -f "$STATUS_FILE" ]]; then
  emit "bmad:init" "Workflow status not found. Initialize BMAD artifacts first."
  exit 0
fi

is_pending() {
  local phase="$1"
  local workflow="$2"

  local state
  local status

  state=$(yq eval -r ".phases.${phase}.workflows.${workflow}.completed // \"\"" "$STATUS_FILE")
  status=$(yq eval -r ".phases.${phase}.workflows.${workflow}.status // \"required\"" "$STATUS_FILE")

  if [[ "$state" == "true" ]]; then
    return 1
  fi

  [[ "$status" == "required" || "$status" == "recommended" ]]
}

project_level=$(yq eval -r '.project.level // 1' "$STATUS_FILE")

if is_pending phase_1_analysis product_brief; then
  emit "bmad:product-brief" "Phase 1 foundation is incomplete."
  exit 0
fi

if [[ "$project_level" -ge 2 ]]; then
  if is_pending phase_2_planning prd; then
    emit "bmad:prd" "Level 2+ projects require PRD before solutioning."
    exit 0
  fi
else
  if is_pending phase_2_planning tech_spec; then
    emit "bmad:tech-spec" "Level 0-1 projects require a tech spec before solutioning."
    exit 0
  fi
fi

if is_pending phase_2_planning ux_design; then
  emit "bmad:ux-design" "UX design is recommended before implementation."
  exit 0
fi

if is_pending phase_3_solutioning architecture; then
  emit "bmad:architecture" "Architecture is pending for the current project level."
  exit 0
fi

if is_pending phase_3_solutioning gate_check; then
  emit "bmad:gate-check" "Gate check is recommended before implementation."
  exit 0
fi

if is_pending phase_4_implementation sprint_planning; then
  emit "bmad:sprint-plan" "Sprint planning is required before story execution."
  exit 0
fi

stories_total=$(yq eval '.phases.phase_4_implementation.workflows.stories.total // 0' "$STATUS_FILE")
stories_completed=$(yq eval '.phases.phase_4_implementation.workflows.stories.completed // 0' "$STATUS_FILE")

if [[ "$stories_total" -eq 0 ]]; then
  emit "bmad:create-story" "No stories are planned yet for implementation."
  exit 0
fi

if [[ "$stories_completed" -lt "$stories_total" ]]; then
  emit "bmad:dev-story" "There are remaining stories to implement."
  exit 0
fi

emit "bmad:status" "All currently tracked workflows are complete."
