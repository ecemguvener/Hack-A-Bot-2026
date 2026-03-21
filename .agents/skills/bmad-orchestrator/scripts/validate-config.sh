#!/usr/bin/env bash
set -euo pipefail

CONFIG_FILE="${1:-bmad/project.yaml}"

usage() {
  cat <<USAGE
Usage: $(basename "$0") [config_file]

Default config_file: bmad/project.yaml
USAGE
}

if [[ "$CONFIG_FILE" == "-h" || "$CONFIG_FILE" == "--help" ]]; then
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

echo "Validating $CONFIG_FILE"

name=$(yq eval -r '.project.name // ""' "$CONFIG_FILE")
type=$(yq eval -r '.project.type // ""' "$CONFIG_FILE")
level=$(yq eval -r '.project.level // ""' "$CONFIG_FILE")
status_file=$(yq eval -r '.paths.status_file // ""' "$CONFIG_FILE")
sprint_file=$(yq eval -r '.paths.sprint_file // ""' "$CONFIG_FILE")
communication_language=$(yq eval -r '.language.communication_language // ""' "$CONFIG_FILE")
document_output_language=$(yq eval -r '.language.document_output_language // ""' "$CONFIG_FILE")

errors=0

if [[ -z "$name" ]]; then
  echo "[ERROR] project.name is required"
  errors=$((errors + 1))
else
  echo "[OK] project.name=$name"
fi

if [[ -z "$type" ]]; then
  echo "[ERROR] project.type is required"
  errors=$((errors + 1))
else
  echo "[OK] project.type=$type"
fi

if [[ -z "$level" ]]; then
  echo "[ERROR] project.level is required"
  errors=$((errors + 1))
elif [[ ! "$level" =~ ^[0-4]$ ]]; then
  echo "[ERROR] project.level must be 0..4 (got $level)"
  errors=$((errors + 1))
else
  echo "[OK] project.level=$level"
fi

if [[ -n "$status_file" ]]; then
  echo "[OK] paths.status_file=$status_file"
else
  echo "[WARN] paths.status_file is empty"
fi

if [[ -n "$sprint_file" ]]; then
  echo "[OK] paths.sprint_file=$sprint_file"
else
  echo "[WARN] paths.sprint_file is empty"
fi

if [[ -n "$communication_language" ]]; then
  echo "[OK] language.communication_language=$communication_language"
else
  echo "[WARN] language.communication_language is missing (default fallback is English)"
fi

if [[ -n "$document_output_language" ]]; then
  echo "[OK] language.document_output_language=$document_output_language"
else
  echo "[WARN] language.document_output_language is missing (fallback uses communication language)"
fi

if [[ "$errors" -gt 0 ]]; then
  echo "Validation failed with $errors error(s)"
  exit 1
fi

echo "Validation passed"
