#!/usr/bin/env bash
set -euo pipefail

STATUS_FILE="${1:-bmad/workflow-status.yaml}"
MODE="${2:-text}"

SHARED_SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)/bmad-shared/scripts"
NEXT_SCRIPT="$SHARED_SCRIPTS_DIR/next-workflow.sh"

if [[ ! -x "$NEXT_SCRIPT" ]]; then
  echo "ERROR: next-workflow helper not found: $NEXT_SCRIPT" >&2
  exit 1
fi

exec "$NEXT_SCRIPT" "$STATUS_FILE" "$MODE"
