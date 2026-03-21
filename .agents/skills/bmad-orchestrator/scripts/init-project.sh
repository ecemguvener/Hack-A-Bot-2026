#!/usr/bin/env bash
set -euo pipefail

PROJECT_NAME=""
PROJECT_TYPE=""
PROJECT_LEVEL=""
PROJECT_DESCRIPTION=""
PROJECT_ROOT="$(pwd)"
COMMUNICATION_LANGUAGE="English"
DOCUMENT_OUTPUT_LANGUAGE=""
FORCE=0

usage() {
  cat <<USAGE
Usage: $(basename "$0") --name <project-name> --type <project-type> --level <0-4> [options]

Required:
  --name          project name
  --type          project type (web-app|mobile-app|api|game|library|cli|other)
  --level         project level (0-4)

Optional:
  --description   short project description
  --project-root  target project root (default: current directory)
  --communication-language language for AI communication (default: English)
  --document-output-language language for generated documents (default: same as communication)
  --force         overwrite existing BMAD artifacts (YAML files and AGENTS.md)
  -h, --help      show this help
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --name)
      PROJECT_NAME="$2"
      shift 2
      ;;
    --type)
      PROJECT_TYPE="$2"
      shift 2
      ;;
    --level)
      PROJECT_LEVEL="$2"
      shift 2
      ;;
    --description)
      PROJECT_DESCRIPTION="$2"
      shift 2
      ;;
    --project-root)
      PROJECT_ROOT="$2"
      shift 2
      ;;
    --communication-language)
      COMMUNICATION_LANGUAGE="$2"
      shift 2
      ;;
    --document-output-language)
      DOCUMENT_OUTPUT_LANGUAGE="$2"
      shift 2
      ;;
    --force)
      FORCE=1
      shift
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

[[ -n "$PROJECT_NAME" ]] || { echo "ERROR: --name is required" >&2; exit 1; }
[[ -n "$PROJECT_TYPE" ]] || { echo "ERROR: --type is required" >&2; exit 1; }
[[ -n "$PROJECT_LEVEL" ]] || { echo "ERROR: --level is required" >&2; exit 1; }
[[ "$PROJECT_LEVEL" =~ ^[0-4]$ ]] || { echo "ERROR: --level must be 0..4" >&2; exit 1; }
[[ -n "$COMMUNICATION_LANGUAGE" ]] || { echo "ERROR: --communication-language cannot be empty" >&2; exit 1; }

if [[ -z "$DOCUMENT_OUTPUT_LANGUAGE" ]]; then
  DOCUMENT_OUTPUT_LANGUAGE="$COMMUNICATION_LANGUAGE"
fi
[[ -n "$DOCUMENT_OUTPUT_LANGUAGE" ]] || { echo "ERROR: --document-output-language cannot be empty" >&2; exit 1; }

valid_types=(web-app mobile-app api game library cli other)
if [[ ! " ${valid_types[*]} " =~ " ${PROJECT_TYPE} " ]]; then
  echo "WARN: unknown project type '${PROJECT_TYPE}'. Continuing." >&2
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ORCHESTRATOR_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VERSION_FILE="$ORCHESTRATOR_ROOT/version.yaml"

read_codex_bmad_version() {
  local version="unknown"

  if [[ -f "$VERSION_FILE" ]]; then
    version="$(sed -nE 's/^version:[[:space:]]*"?([^"[:space:]]+)"?.*$/\1/p' "$VERSION_FILE" | head -n1 || true)"
  fi

  if [[ -z "$version" ]]; then
    version="unknown"
  fi

  printf '%s\n' "$version"
}

CODEX_BMAD_SKILLS_VERSION="$(read_codex_bmad_version)"

PROJECT_TEMPLATE="$ORCHESTRATOR_ROOT/templates/project.template.yaml"
WORKFLOW_TEMPLATE="$ORCHESTRATOR_ROOT/templates/workflow-status.template.yaml"
SPRINT_TEMPLATE="$ORCHESTRATOR_ROOT/templates/sprint-status.template.yaml"

[[ -f "$PROJECT_TEMPLATE" ]] || { echo "ERROR: template missing: $PROJECT_TEMPLATE" >&2; exit 1; }
[[ -f "$WORKFLOW_TEMPLATE" ]] || { echo "ERROR: template missing: $WORKFLOW_TEMPLATE" >&2; exit 1; }
[[ -f "$SPRINT_TEMPLATE" ]] || { echo "ERROR: template missing: $SPRINT_TEMPLATE" >&2; exit 1; }

TIMESTAMP="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
SPRINT_START="$(date +"%Y-%m-%d")"
if date -u -d "+14 days" +"%Y-%m-%d" >/dev/null 2>&1; then
  SPRINT_END="$(date -u -d "+14 days" +"%Y-%m-%d")"
elif date -u -v+14d +"%Y-%m-%d" >/dev/null 2>&1; then
  SPRINT_END="$(date -u -v+14d +"%Y-%m-%d")"
else
  SPRINT_END="$SPRINT_START"
fi

if [[ "$PROJECT_LEVEL" -ge 2 ]]; then
  PRODUCT_BRIEF_STATUS="required"
  PRD_STATUS="required"
  TECH_SPEC_STATUS="optional"
  ARCHITECTURE_STATUS="required"
elif [[ "$PROJECT_LEVEL" -eq 1 ]]; then
  PRODUCT_BRIEF_STATUS="recommended"
  PRD_STATUS="recommended"
  TECH_SPEC_STATUS="required"
  ARCHITECTURE_STATUS="optional"
else
  PRODUCT_BRIEF_STATUS="optional"
  PRD_STATUS="optional"
  TECH_SPEC_STATUS="required"
  ARCHITECTURE_STATUS="optional"
fi

PROJECT_BMAD_DIR="$PROJECT_ROOT/bmad"
PROJECT_DOCS_BMAD_DIR="$PROJECT_ROOT/docs/bmad"
PROJECT_STORIES_DIR="$PROJECT_ROOT/docs/stories"

mkdir -p "$PROJECT_BMAD_DIR" "$PROJECT_DOCS_BMAD_DIR" "$PROJECT_STORIES_DIR"

PROJECT_CONFIG_OUT="$PROJECT_BMAD_DIR/project.yaml"
WORKFLOW_OUT="$PROJECT_BMAD_DIR/workflow-status.yaml"
SPRINT_OUT="$PROJECT_BMAD_DIR/sprint-status.yaml"

for file in "$PROJECT_CONFIG_OUT" "$WORKFLOW_OUT" "$SPRINT_OUT"; do
  if [[ -f "$file" && "$FORCE" -ne 1 ]]; then
    echo "ERROR: file already exists: $file (use --force to overwrite)" >&2
    exit 1
  fi
done

escape() {
  printf '%s' "$1" | sed -e 's/[\&/]/\\&/g'
}

render_template() {
  local input="$1"
  local output="$2"

  sed \
    -e "s/{{project_name}}/$(escape "$PROJECT_NAME")/g" \
    -e "s/{{project_type}}/$(escape "$PROJECT_TYPE")/g" \
    -e "s/{{project_level}}/$(escape "$PROJECT_LEVEL")/g" \
    -e "s/{{project_description}}/$(escape "$PROJECT_DESCRIPTION")/g" \
    -e "s/{{communication_language}}/$(escape "$COMMUNICATION_LANGUAGE")/g" \
    -e "s/{{document_output_language}}/$(escape "$DOCUMENT_OUTPUT_LANGUAGE")/g" \
    -e "s/{{product_brief_status}}/$(escape "$PRODUCT_BRIEF_STATUS")/g" \
    -e "s/{{prd_status}}/$(escape "$PRD_STATUS")/g" \
    -e "s/{{tech_spec_status}}/$(escape "$TECH_SPEC_STATUS")/g" \
    -e "s/{{architecture_status}}/$(escape "$ARCHITECTURE_STATUS")/g" \
    -e "s/{{timestamp}}/$(escape "$TIMESTAMP")/g" \
    -e "s/{{sprint_number}}/1/g" \
    -e "s/{{sprint_start}}/$(escape "$SPRINT_START")/g" \
    -e "s/{{sprint_end}}/$(escape "$SPRINT_END")/g" \
    -e "s/{{sprint_goal}}/$(escape "Initial baseline sprint")/g" \
    -e "s/{{capacity_points}}/20/g" \
    -e "s/{{committed_points}}/0/g" \
    "$input" > "$output"
}

render_template "$PROJECT_TEMPLATE" "$PROJECT_CONFIG_OUT"
render_template "$WORKFLOW_TEMPLATE" "$WORKFLOW_OUT"
render_template "$SPRINT_TEMPLATE" "$SPRINT_OUT"

PROJECT_AGENTS_TEMPLATE="$ORCHESTRATOR_ROOT/templates/project-AGENTS.template.md"
PROJECT_AGENTS_OUT="$PROJECT_ROOT/AGENTS.md"
if [[ -f "$PROJECT_AGENTS_TEMPLATE" ]]; then
  if [[ ! -f "$PROJECT_AGENTS_OUT" || "$FORCE" -eq 1 ]]; then
    cp "$PROJECT_AGENTS_TEMPLATE" "$PROJECT_AGENTS_OUT"
  fi
fi

echo "initialized=true"
echo "project_root=$PROJECT_ROOT"
echo "project_config=$PROJECT_CONFIG_OUT"
echo "workflow_status=$WORKFLOW_OUT"
echo "sprint_status=$SPRINT_OUT"
echo "communication_language=$COMMUNICATION_LANGUAGE"
echo "document_output_language=$DOCUMENT_OUTPUT_LANGUAGE"
echo "codex_bmad_skills_version=$CODEX_BMAD_SKILLS_VERSION"
echo "next_intent=bmad:status"
