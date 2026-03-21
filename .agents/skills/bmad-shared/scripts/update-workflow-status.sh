#!/usr/bin/env bash
set -euo pipefail

STATUS_FILE="bmad/workflow-status.yaml"
WORKFLOW=""
OUTPUT_FILE=""
PASSED=""

usage() {
  cat <<USAGE
Usage: $(basename "$0") --workflow <id> [--status-file <path>] [--output <path>] [--passed true|false]

Workflows:
  product_brief, research, brainstorm,
  prd, tech_spec, ux_design,
  architecture, gate_check,
  sprint_planning
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --workflow)
      WORKFLOW="$2"
      shift 2
      ;;
    --status-file)
      STATUS_FILE="$2"
      shift 2
      ;;
    --output)
      OUTPUT_FILE="$2"
      shift 2
      ;;
    --passed)
      PASSED="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "ERROR: Unknown argument: $1" >&2
      usage
      exit 1
      ;;
  esac
done

if ! command -v yq >/dev/null 2>&1; then
  echo "ERROR: yq v4+ is required" >&2
  exit 1
fi

[[ -n "$WORKFLOW" ]] || {
  echo "ERROR: --workflow is required" >&2
  usage
  exit 1
}

[[ -f "$STATUS_FILE" ]] || {
  echo "ERROR: status file not found: $STATUS_FILE" >&2
  exit 1
}

case "$WORKFLOW" in
  product_brief|research|brainstorm)
    PHASE_KEY="phase_1_analysis"
    ;;
  prd|tech_spec|ux_design)
    PHASE_KEY="phase_2_planning"
    ;;
  architecture|gate_check)
    PHASE_KEY="phase_3_solutioning"
    ;;
  sprint_planning)
    PHASE_KEY="phase_4_implementation"
    ;;
  *)
    echo "ERROR: unsupported workflow: $WORKFLOW" >&2
    exit 1
    ;;
esac

TIMESTAMP="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

export PHASE_KEY WORKFLOW OUTPUT_FILE TIMESTAMP

yq eval -i '
  .phases[strenv(PHASE_KEY)].workflows[strenv(WORKFLOW)].completed = true |
  .phases[strenv(PHASE_KEY)].workflows[strenv(WORKFLOW)].completed_at = strenv(TIMESTAMP) |
  .current_workflow = strenv(WORKFLOW) |
  .project.last_updated = strenv(TIMESTAMP)
' "$STATUS_FILE"

if [[ -n "$OUTPUT_FILE" ]]; then
  yq eval -i '.phases[strenv(PHASE_KEY)].workflows[strenv(WORKFLOW)].output_file = strenv(OUTPUT_FILE)' "$STATUS_FILE"
fi

if [[ "$WORKFLOW" == "gate_check" && -n "$PASSED" ]]; then
  if [[ "$PASSED" != "true" && "$PASSED" != "false" ]]; then
    echo "ERROR: --passed must be true or false" >&2
    exit 1
  fi
  export PASSED
  yq eval -i '.phases[strenv(PHASE_KEY)].workflows[strenv(WORKFLOW)].passed = (strenv(PASSED) == "true")' "$STATUS_FILE"
fi

phase_status() {
  local key="$1"
  local total
  local completed

  total=$(yq eval "[.phases.${key}.workflows[] | select(has(\"completed\"))] | length" "$STATUS_FILE")
  completed=$(yq eval "[.phases.${key}.workflows[] | select(has(\"completed\") and .completed == true)] | length" "$STATUS_FILE")

  if [[ "$total" -eq 0 || "$completed" -eq 0 ]]; then
    echo "not_started"
  elif [[ "$completed" -eq "$total" ]]; then
    echo "completed"
  else
    echo "in_progress"
  fi
}

for phase in phase_1_analysis phase_2_planning phase_3_solutioning phase_4_implementation; do
  status=$(phase_status "$phase")
  yq eval -i ".phases.${phase}.status = \"${status}\"" "$STATUS_FILE"
done

total_workflows=$(yq eval '[.phases[].workflows[] | select(has("completed"))] | length' "$STATUS_FILE")
completed_workflows=$(yq eval '[.phases[].workflows[] | select(has("completed") and .completed == true)] | length' "$STATUS_FILE")

if [[ "$total_workflows" -eq 0 ]]; then
  progress=0
else
  progress=$((completed_workflows * 100 / total_workflows))
fi

yq eval -i ".metrics.total_workflows = ${total_workflows}" "$STATUS_FILE"
yq eval -i ".metrics.completed_workflows = ${completed_workflows}" "$STATUS_FILE"
yq eval -i ".metrics.progress_percentage = ${progress}" "$STATUS_FILE"

current_phase=4
for entry in "1:phase_1_analysis" "2:phase_2_planning" "3:phase_3_solutioning" "4:phase_4_implementation"; do
  phase_num="${entry%%:*}"
  phase_key="${entry#*:}"

  pending=$(yq eval "[
    .phases.${phase_key}.workflows[]
    | select(has(\"completed\") and .completed == false)
    | select((.status // \"required\") == \"required\" or (.status // \"required\") == \"recommended\")
  ] | length" "$STATUS_FILE")

  if [[ "$pending" -gt 0 ]]; then
    current_phase="$phase_num"
    break
  fi
done

yq eval -i ".current_phase = ${current_phase}" "$STATUS_FILE"

echo "updated_workflow=$WORKFLOW"
echo "status_file=$STATUS_FILE"
echo "completed_workflows=$completed_workflows"
echo "total_workflows=$total_workflows"
echo "progress_percentage=$progress"
