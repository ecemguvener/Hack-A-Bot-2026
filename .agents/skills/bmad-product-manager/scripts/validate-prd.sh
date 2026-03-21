#!/bin/bash
#
# PRD Validation Script
#
# Validates that a Product Requirements Document contains all required sections
# and meets quality standards.
#
# Usage:
#   ./validate-prd.sh <prd-file>
#   ./validate-prd.sh --help
#

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
PASS=0
FAIL=0
WARN=0

# Functions
show_help() {
    cat << EOF
PRD Validation Script

Validates that a Product Requirements Document contains all required sections
and meets quality standards.

Usage:
    $0 <prd-file>
    $0 --help

Required Sections:
    - Executive Summary
    - Project Overview
    - Functional Requirements
    - Non-Functional Requirements
    - Epics
    - User Stories (optional but recommended)
    - Success Metrics
    - Assumptions and Dependencies
    - Out of Scope

Quality Checks:
    - Requirements have unique IDs (FR-XXX, NFR-XXX)
    - Requirements have priorities (MUST/SHOULD/COULD/WONT)
    - Requirements have acceptance criteria
    - Epics are defined with user stories
    - Success metrics are measurable

Exit Codes:
    0 - All validations passed
    1 - One or more validations failed
    2 - Invalid usage or file not found

Examples:
    $0 docs/prd-myapp-2025-12-09.md
    $0 ../requirements/product-requirements.md
EOF
}

print_header() {
    echo -e "\n${BLUE}================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================${NC}\n"
}

print_pass() {
    echo -e "${GREEN}✓${NC} $1"
    PASS=$((PASS + 1))
}

print_fail() {
    echo -e "${RED}✗${NC} $1"
    FAIL=$((FAIL + 1))
}

print_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
    WARN=$((WARN + 1))
}

check_section() {
    local file=$1
    local section=$2
    local pattern=$3

    if grep -qE "$pattern" "$file"; then
        print_pass "Section present: $section"
        return 0
    else
        print_fail "Section missing: $section"
        return 0
    fi
}

check_requirements_format() {
    local file=$1
    local req_type=$2
    local pattern=$3

    local count=$(grep -cE "$pattern" "$file" || true)

    if [ "$count" -gt 0 ]; then
        print_pass "Found $count $req_type requirements with proper IDs"
        return 0
    else
        print_fail "No $req_type requirements found with format $pattern"
        return 0
    fi
}

check_priorities() {
    local file=$1

    # Check for priority keywords
    if grep -qiE "(MUST|SHOULD|COULD|WO?N'?T)" "$file"; then
        local must_count=$(grep -ciE "MUST" "$file" || true)
        local should_count=$(grep -ciE "SHOULD" "$file" || true)
        local could_count=$(grep -ciE "COULD" "$file" || true)

        print_pass "Priorities assigned (MUST: $must_count, SHOULD: $should_count, COULD: $could_count)"
        return 0
    else
        print_fail "No priority assignments found (MUST/SHOULD/COULD/WONT)"
        return 0
    fi
}

check_acceptance_criteria() {
    local file=$1

    local criteria_count=$(grep -ciE "(acceptance criteria|acceptance criterion)" "$file" || true)

    if [ "$criteria_count" -gt 0 ]; then
        print_pass "Found $criteria_count acceptance criteria sections"
        return 0
    else
        print_fail "No acceptance criteria found"
        return 0
    fi
}

count_key_ids() {
    local file=$1
    local pattern=$2

    grep -cE "$pattern" "$file" || true
}

check_metrics() {
    local file=$1

    if grep -qiE "(success metric|success criteria|measure|kpi|objective)" "$file"; then
        print_pass "Success metrics defined"
        return 0
    else
        print_warn "Success metrics not clearly defined"
        return 0
    fi
}

# Validate arguments
if [ $# -eq 0 ]; then
    echo -e "${RED}Error: No PRD file specified${NC}\n"
    show_help
    exit 2
fi

if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    show_help
    exit 0
fi

PRD_FILE=$1

# Check file exists
if [ ! -f "$PRD_FILE" ]; then
    echo -e "${RED}Error: File not found: $PRD_FILE${NC}"
    exit 2
fi

# Start validation
print_header "Validating PRD: $PRD_FILE"

echo "File size: $(wc -c < "$PRD_FILE") bytes"
echo "Line count: $(wc -l < "$PRD_FILE") lines"
echo ""

# Required Sections
print_header "Required Sections"

check_section "$PRD_FILE" "Executive Summary" "^#{1,3} Executive Summary"
check_section "$PRD_FILE" "Project Overview" "^#{1,3} .*[Pp]roject.*[Oo]verview"
check_section "$PRD_FILE" "Functional Requirements" "^#{1,3} Functional Requirements"
check_section "$PRD_FILE" "Non-Functional Requirements" "^#{1,3} Non-Functional Requirements"
check_section "$PRD_FILE" "Success Metrics" "^#{1,3} Success Metrics"
check_section "$PRD_FILE" "Assumptions" "^#{1,3} Assumptions"
check_section "$PRD_FILE" "Out of Scope" "^#{1,3} Out of Scope"

# Requirements Format
print_header "Requirements Format"

check_requirements_format "$PRD_FILE" "Functional" "FR-[0-9]"
check_requirements_format "$PRD_FILE" "Non-Functional" "NFR-[0-9]"

# Priority Assignments
print_header "Priority Assignments"

check_priorities "$PRD_FILE"

# Acceptance Criteria
print_header "Acceptance Criteria"

check_acceptance_criteria "$PRD_FILE"

# Epics and Stories
print_header "Epics and User Stories"

epic_id_count=$(count_key_ids "$PRD_FILE" "\\bEPIC-[0-9]+\\b")
story_id_count=$(count_key_ids "$PRD_FILE" "\\bSTORY-[0-9]+\\b")
ui_id_count=$(count_key_ids "$PRD_FILE" "\\bUI-[0-9]+\\b")
flow_count=$(count_key_ids "$PRD_FILE" "\\bFlow[[:space:]]+[0-9]+\\b")

if [ "$epic_id_count" -gt 0 ]; then
    print_pass "Found $epic_id_count EPIC IDs"
else
    print_fail "No EPIC IDs found (expected format: EPIC-XXX)"
fi

if [ "$story_id_count" -gt 0 ]; then
    print_pass "Found $story_id_count STORY IDs"
else
    print_warn "No STORY IDs found (recommended format: STORY-XXX)"
fi

if [ "$ui_id_count" -gt 0 ]; then
    print_pass "Found $ui_id_count UI requirement IDs"
else
    print_warn "No UI IDs found (optional format: UI-XXX)"
fi

if [ "$flow_count" -gt 0 ]; then
    print_pass "Found $flow_count flow markers"
else
    print_warn "No flow markers found (optional format: Flow X)"
fi

# Success Metrics
print_header "Success Metrics and Traceability"

check_metrics "$PRD_FILE"

# Check for traceability matrix or requirements mapping
if grep -qiE "(traceability|requirements matrix|requirements mapping)" "$PRD_FILE"; then
    print_pass "Traceability section found"
else
    print_warn "Traceability matrix not found (recommended for complex PRDs)"
fi

# Quality Checks
print_header "Quality Checks"

# Check for vague terms
vague_terms=("user-friendly" "intuitive" "easy" "simple" "fast" "good" "better" "improved")
vague_found=0
for term in "${vague_terms[@]}"; do
    if grep -qiE "\b$term\b" "$PRD_FILE"; then
        vague_found=$((vague_found + 1))
    fi
done

if [ $vague_found -gt 5 ]; then
    print_warn "Document contains many vague terms ($vague_found instances). Consider using specific, measurable criteria."
else
    print_pass "Minimal use of vague terms (good specificity)"
fi

# Structured ID summary (language-agnostic)
fr_id_count=$(count_key_ids "$PRD_FILE" "\\bFR-[0-9]+\\b")
nfr_id_count=$(count_key_ids "$PRD_FILE" "\\bNFR-[0-9]+\\b")
print_pass "Structured IDs summary (FR: $fr_id_count, NFR: $nfr_id_count, EPIC: $epic_id_count, STORY: $story_id_count, UI: $ui_id_count, Flow: $flow_count)"

# Check document length
line_count=$(wc -l < "$PRD_FILE")
if [ $line_count -lt 50 ]; then
    print_warn "Document is quite short ($line_count lines). Ensure all sections are complete."
elif [ $line_count -gt 1000 ]; then
    print_warn "Document is very long ($line_count lines). Consider splitting into multiple documents."
else
    print_pass "Document length is reasonable ($line_count lines)"
fi

# Summary
print_header "Validation Summary"

total=$((PASS + FAIL + WARN))
echo -e "${GREEN}Passed:${NC}  $PASS/$total"
echo -e "${RED}Failed:${NC}  $FAIL/$total"
echo -e "${YELLOW}Warnings:${NC} $WARN/$total"
echo ""

if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}✓ PRD validation passed!${NC}"
    if [ $WARN -gt 0 ]; then
        echo -e "${YELLOW}  (with $WARN warnings - review recommended)${NC}"
    fi
    exit 0
else
    echo -e "${RED}✗ PRD validation failed with $FAIL errors${NC}"
    echo "Please address the failed checks above."
    exit 1
fi
