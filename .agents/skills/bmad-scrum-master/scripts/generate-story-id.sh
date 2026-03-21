#!/usr/bin/env bash
#
# Story ID Generator for Scrum Master Skill
#
# Generates the next sequential story ID for a project.
# Scans existing story files to find the highest ID and increments it.
#
# Usage:
#   bash generate-story-id.sh [project-name] [stories-directory]
#   bash generate-story-id.sh my-project
#   bash generate-story-id.sh my-project docs/stories/
#
# Output:
#   STORY-001 (if no stories exist)
#   STORY-042 (if 41 stories exist)
#
# Exit codes:
#   0 - Success
#   1 - Error (invalid arguments, directory not found, etc.)

set -euo pipefail

# Default values
PROJECT_NAME="${1:-}"
STORIES_DIR="${2:-docs/stories}"
SPRINT_STATUS_FILE="bmad/sprint-status.yaml"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper functions
error() {
    echo -e "${RED}Error: $1${NC}" >&2
}

success() {
    echo -e "${GREEN}$1${NC}"
}

info() {
    echo -e "${YELLOW}$1${NC}" >&2
}

usage() {
    cat << EOF
Usage: $(basename "$0") [project-name] [stories-directory]

Generate the next sequential story ID for a project.

Arguments:
  project-name       Optional. Project name (default: from sprint-status.yaml)
  stories-directory  Optional. Directory to scan for stories (default: docs/stories)

Examples:
  $(basename "$0")
  $(basename "$0") my-project
  $(basename "$0") my-project docs/stories/

Output:
  STORY-001  (if no stories exist)
  STORY-042  (if 41 stories exist)

The script searches for story IDs in:
  1. Story files in the specified directory (*.md files)
  2. Sprint status YAML file (bmad/sprint-status.yaml)

Exit Codes:
  0 - Success
  1 - Error
EOF
}

# Extract project name from sprint status YAML.
# Supports both:
#   project: my-project
#   project:
#     name: my-project
extract_project_name() {
    local file="$1"
    local project_name=""

    if command -v yq >/dev/null 2>&1; then
        project_name=$(yq -r '.project.name // .project // .project_name // ""' "$file" 2>/dev/null || true)
        if [[ "$project_name" == "null" ]]; then
            project_name=""
        fi
    fi

    if [[ -z "$project_name" ]]; then
        project_name=$(grep -E "^project:[[:space:]]*[^[:space:]].*$" "$file" | head -1 | sed 's/project:[[:space:]]*//' | tr -d '"' || true)
    fi

    if [[ -z "$project_name" ]]; then
        project_name=$(awk '
            /^project:[[:space:]]*$/ { in_project=1; next }
            in_project && /^[[:space:]]+name:[[:space:]]*/ {
                sub(/^[[:space:]]+name:[[:space:]]*/, "", $0)
                gsub(/"/, "", $0)
                print
                exit
            }
            in_project && /^[^[:space:]]/ { in_project=0 }
        ' "$file")
    fi

    echo "$project_name"
}

# Parse arguments
if [[ "${1:-}" == "-h" ]] || [[ "${1:-}" == "--help" ]]; then
    usage
    exit 0
fi

# Get project name from sprint status if not provided
if [[ -z "$PROJECT_NAME" ]]; then
    if [[ -f "$SPRINT_STATUS_FILE" ]]; then
        PROJECT_NAME=$(extract_project_name "$SPRINT_STATUS_FILE")
        if [[ -z "$PROJECT_NAME" ]]; then
            error "Could not extract project name from $SPRINT_STATUS_FILE"
            exit 1
        fi
        info "Using project name from sprint status: $PROJECT_NAME"
    else
        error "No project name provided and $SPRINT_STATUS_FILE not found"
        echo ""
        usage
        exit 1
    fi
fi

# Find highest story ID from multiple sources
find_highest_story_id() {
    local max_id=0
    local current_id

    # Source 1: Story files in stories directory
    if [[ -d "$STORIES_DIR" ]]; then
        while IFS= read -r file; do
            # Extract STORY-NNN pattern from filename and content
            while IFS= read -r line; do
                if [[ "$line" =~ STORY-([0-9]{3,}) ]]; then
                    current_id="${BASH_REMATCH[1]}"
                    # Remove leading zeros for comparison
                    current_id=$((10#$current_id))
                    if [[ $current_id -gt $max_id ]]; then
                        max_id=$current_id
                    fi
                fi
            done < "$file"
        done < <(find "$STORIES_DIR" -type f -name "*.md" 2>/dev/null || true)
    fi

    # Source 2: Sprint status YAML file
    if [[ -f "$SPRINT_STATUS_FILE" ]]; then
        while IFS= read -r line; do
            if [[ "$line" =~ STORY-([0-9]{3,}) ]]; then
                current_id="${BASH_REMATCH[1]}"
                current_id=$((10#$current_id))
                if [[ $current_id -gt $max_id ]]; then
                    max_id=$current_id
                fi
            fi
        done < "$SPRINT_STATUS_FILE"
    fi

    # Source 3: Any markdown files in docs/ directory
    if [[ -d "docs" ]]; then
        while IFS= read -r file; do
            while IFS= read -r line; do
                if [[ "$line" =~ STORY-([0-9]{3,}) ]]; then
                    current_id="${BASH_REMATCH[1]}"
                    current_id=$((10#$current_id))
                    if [[ $current_id -gt $max_id ]]; then
                        max_id=$current_id
                    fi
                fi
            done < "$file"
        done < <(find docs -type f -name "*.md" 2>/dev/null || true)
    fi

    echo "$max_id"
}

# Main logic
main() {
    local highest_id
    local next_id
    local next_id_formatted

    # Find highest existing story ID
    highest_id=$(find_highest_story_id)

    # Calculate next ID
    next_id=$((highest_id + 1))

    # Format with leading zeros (minimum 3 digits)
    next_id_formatted=$(printf "STORY-%03d" "$next_id")

    # Output the next story ID
    echo "$next_id_formatted"

    # Print summary to stderr (so stdout only has the ID)
    if [[ $highest_id -eq 0 ]]; then
        info "No existing stories found. Starting with $next_id_formatted"
    else
        info "Found $highest_id existing stories. Next ID: $next_id_formatted"
    fi

    return 0
}

# Execute main function
main
