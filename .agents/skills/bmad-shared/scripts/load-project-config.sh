#!/usr/bin/env bash
set -euo pipefail

CONFIG_FILE="${1:-bmad/project.yaml}"
MODE="${2:-text}"

usage() {
  cat <<USAGE
Usage: $(basename "$0") [config_file] [text|json|export]

Defaults:
  config_file: bmad/project.yaml
  mode: text
USAGE
}

if [[ "${CONFIG_FILE}" == "-h" || "${CONFIG_FILE}" == "--help" ]]; then
  usage
  exit 0
fi

if ! command -v yq >/dev/null 2>&1; then
  echo "ERROR: yq v4+ is required" >&2
  exit 1
fi

if [[ ! -f "$CONFIG_FILE" ]]; then
  echo "ERROR: config file not found: $CONFIG_FILE" >&2
  exit 1
fi

name=$(yq eval -r '.project.name // ""' "$CONFIG_FILE")
type=$(yq eval -r '.project.type // ""' "$CONFIG_FILE")
level=$(yq eval -r '.project.level // ""' "$CONFIG_FILE")
output=$(yq eval -r '.paths.output_folder // "docs"' "$CONFIG_FILE")
status=$(yq eval -r '.paths.status_file // "bmad/workflow-status.yaml"' "$CONFIG_FILE")
sprint=$(yq eval -r '.paths.sprint_file // "bmad/sprint-status.yaml"' "$CONFIG_FILE")
communication_language=$(yq eval -r '.language.communication_language // "English"' "$CONFIG_FILE")
document_output_language=$(yq eval -r '.language.document_output_language // .language.communication_language // "English"' "$CONFIG_FILE")

case "$MODE" in
  text)
    printf 'project_name=%s\n' "$name"
    printf 'project_type=%s\n' "$type"
    printf 'project_level=%s\n' "$level"
    printf 'output_folder=%s\n' "$output"
    printf 'status_file=%s\n' "$status"
    printf 'sprint_file=%s\n' "$sprint"
    printf 'communication_language=%s\n' "$communication_language"
    printf 'document_output_language=%s\n' "$document_output_language"
    ;;
  json)
    yq eval -o=json '.' "$CONFIG_FILE"
    ;;
  export)
    printf 'export BMAD_PROJECT_NAME="%s"\n' "$name"
    printf 'export BMAD_PROJECT_TYPE="%s"\n' "$type"
    printf 'export BMAD_PROJECT_LEVEL="%s"\n' "$level"
    printf 'export BMAD_OUTPUT_FOLDER="%s"\n' "$output"
    printf 'export BMAD_STATUS_FILE="%s"\n' "$status"
    printf 'export BMAD_SPRINT_FILE="%s"\n' "$sprint"
    printf 'export BMAD_COMMUNICATION_LANGUAGE="%s"\n' "$communication_language"
    printf 'export BMAD_DOCUMENT_OUTPUT_LANGUAGE="%s"\n' "$document_output_language"
    ;;
  *)
    echo "ERROR: mode must be text|json|export" >&2
    exit 1
    ;;
esac
