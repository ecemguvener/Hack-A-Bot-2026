#!/usr/bin/env bash
set -euo pipefail

WORKFLOW="${1:-}"
OUTPUT_FILE="${2:-}"
STATUS_FILE="${BMAD_STATUS_FILE:-bmad/workflow-status.yaml}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ -z "$WORKFLOW" ]]; then
  echo "Usage: $(basename "$0") <workflow> [output_file]"
  exit 1
fi

cmd=("$SCRIPT_DIR/update-workflow-status.sh" --workflow "$WORKFLOW" --status-file "$STATUS_FILE")
if [[ -n "$OUTPUT_FILE" ]]; then
  cmd+=(--output "$OUTPUT_FILE")
fi

exec "${cmd[@]}"
