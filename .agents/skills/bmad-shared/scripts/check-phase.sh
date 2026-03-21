#!/usr/bin/env bash
set -euo pipefail

STATUS_FILE="${1:-bmad/workflow-status.yaml}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

result="$($SCRIPT_DIR/next-workflow.sh "$STATUS_FILE" text)"
next_intent=$(printf '%s\n' "$result" | awk -F= '/^next_intent=/{print $2}')
reason=$(printf '%s\n' "$result" | awk -F= '/^reason=/{print $2}')

echo "CURRENT_STATUS_FILE: $STATUS_FILE"
echo "NEXT_INTENT: $next_intent"
echo "REASON: $reason"
