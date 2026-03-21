#!/usr/bin/env bash
set -euo pipefail

CONFIG_FILE="${1:-${HOME}/.config/bmad/global-config.yaml}"
MODE="${2:-text}"

usage() {
  cat <<USAGE
Usage: $(basename "$0") [config_file] [text|json|export]

Defaults:
  config_file: ~/.config/bmad/global-config.yaml
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
  echo "ERROR: global config file not found: $CONFIG_FILE" >&2
  exit 1
fi

user_name=$(yq eval -r '.user.name // ""' "$CONFIG_FILE")
default_language=$(yq eval -r '.defaults.language // "English"' "$CONFIG_FILE")
default_output=$(yq eval -r '.defaults.output_folder // "docs"' "$CONFIG_FILE")

case "$MODE" in
  text)
    printf 'user_name=%s\n' "$user_name"
    printf 'default_language=%s\n' "$default_language"
    printf 'default_output_folder=%s\n' "$default_output"
    ;;
  json)
    yq eval -o=json '.' "$CONFIG_FILE"
    ;;
  export)
    printf 'export BMAD_USER_NAME="%s"\n' "$user_name"
    printf 'export BMAD_DEFAULT_LANGUAGE="%s"\n' "$default_language"
    printf 'export BMAD_DEFAULT_OUTPUT_FOLDER="%s"\n' "$default_output"
    ;;
  *)
    echo "ERROR: mode must be text|json|export" >&2
    exit 1
    ;;
esac
