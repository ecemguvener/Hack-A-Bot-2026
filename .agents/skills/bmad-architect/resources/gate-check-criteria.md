# Gate-Check Criteria

This file is the single source of truth for `bmad:gate-check` scoring and decision logic.

## 1. Coverage Metrics

### 1.1 Functional Requirements (FR) Coverage

Definition:
- Covered FR = requirement with explicit component ownership and implementation approach.

Formula:
- `fr_coverage = covered_frs / total_frs * 100`

### 1.2 Non-Functional Requirements (NFR) Coverage

Definitions:
- Full NFR = requirement with specific architectural solution, measurable target alignment, and validation approach.
- Partial NFR = requirement is referenced, but solution details or validation approach are incomplete.

Formula:
- `nfr_coverage = (full_nfrs + partial_nfrs) / total_nfrs * 100`

### 1.3 Quality Score

Definition:
- Score based on architecture quality checklist results.

Formula:
- `quality_score = passed_checks / total_checks * 100`

## 2. Blocker Rules

### 2.1 Critical Blocker Definition

A critical blocker is an unresolved gap that can cause architecture failure in production, including:
- security or compliance violations
- missing core scalability path
- missing mapping for critical functional requirements

### 2.2 Blocker Impact on Decision

- If any critical blocker has no mitigation plan, decision cannot be `PASS` or `CONDITIONAL PASS`.
- For `CONDITIONAL PASS`, each blocker must include mitigation, owner, and target date.

## 3. Decision Thresholds

### 3.1 PASS

All conditions must be true:
- `fr_coverage >= 90`
- `nfr_coverage >= 90`
- `quality_score >= 80`
- no unresolved critical blockers

### 3.2 CONDITIONAL PASS

All conditions must be true:
- `fr_coverage >= 80`
- `nfr_coverage >= 80`
- `quality_score >= 70`
- blockers have concrete mitigations with owner and target date

### 3.3 FAIL

Decision is `FAIL` if any condition is true:
- any metric below conditional thresholds
- unresolved critical blockers

## 4. Evaluation Order

1. Calculate FR, NFR, and quality metrics.
2. Identify and classify blockers.
3. Apply thresholds for `PASS`.
4. If `PASS` not met, apply thresholds for `CONDITIONAL PASS`.
5. Otherwise set decision to `FAIL`.

## 5. Output Requirements

When producing `docs/bmad/gate-check.md`:
- include raw counts and computed percentages for all three metrics
- show threshold comparison table
- list blockers with status and mitigation
- provide rationale tied directly to the criteria in this file
