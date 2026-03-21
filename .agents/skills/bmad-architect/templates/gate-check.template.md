# Solutioning Gate Check Report: {PROJECT_NAME}

- **Date:** {DATE}
- **Reviewer:** {REVIEWER}
- **Architecture Document:** `docs/bmad/architecture.md`
- **Requirements Document:** `{docs/bmad/prd.md | docs/bmad/tech-spec.md}`
- **Report Version:** 1.0

---

## 1. Executive Summary

**Decision:** {PASS | CONDITIONAL PASS | FAIL}

**Readiness Summary:**
{2-3 sentences describing implementation readiness and major concerns}

**Top Findings:**
- {Finding 1}
- {Finding 2}
- {Finding 3}

---

## 2. Requirements Coverage

### 2.1 Functional Requirements Coverage

**Totals:**
- Total FRs: {total_frs}
- Covered FRs: {covered_frs}
- Partial FRs: {partial_frs}
- Missing FRs: {missing_frs}
- Coverage: `{covered_frs}/{total_frs} * 100 = {fr_coverage}%`

| FR ID | Requirement Summary | Coverage | Components | Notes |
|-------|---------------------|----------|------------|-------|
| FR-001 | {summary} | {Covered | Partial | Missing} | {Component list} | {Notes} |
| FR-002 | {summary} | {Covered | Partial | Missing} | {Component list} | {Notes} |

**Missing or Partial FRs:**
- {FR-ID}: {gap description and impact}

### 2.2 Non-Functional Requirements Coverage

**Totals:**
- Total NFRs: {total_nfrs}
- Fully Addressed NFRs: {full_nfrs}
- Partially Addressed NFRs: {partial_nfrs}
- Missing NFRs: {missing_nfrs}
- Coverage: `{full_nfrs + partial_nfrs}/{total_nfrs} * 100 = {nfr_coverage}%`

| NFR ID | Category | Target | Coverage | Solution Quality | Validation Approach | Notes |
|--------|----------|--------|----------|------------------|---------------------|-------|
| NFR-001 | {Performance/Security/etc.} | {target} | {Full | Partial | Missing} | {Good | Fair | Poor | N/A} | {test/metric} | {Notes} |
| NFR-002 | {category} | {target} | {Full | Partial | Missing} | {Good | Fair | Poor | N/A} | {test/metric} | {Notes} |

**Missing or Weak NFRs:**
- {NFR-ID}: {gap description and risk}

---

## 3. Architecture Quality Assessment

### 3.1 Checklist Summary

- Total Checks: {total_checks}
- Passed Checks: {passed_checks}
- Failed Checks: {failed_checks}
- Quality Score: `{passed_checks}/{total_checks} * 100 = {quality_score}%`

### 3.2 Checklist Details

**System Design**
- [ ] Architectural pattern is justified
- [ ] Components and boundaries are clear
- [ ] Interfaces and dependencies are explicit

**Technology Stack**
- [ ] Stack choices have rationale
- [ ] Trade-offs are documented

**Data and API**
- [ ] Data model is explicit
- [ ] API design and auth/authorization are defined

**Security and Reliability**
- [ ] Security controls are explicit (auth, encryption, secrets)
- [ ] Reliability approach exists (HA, recovery, monitoring)

**Delivery Readiness**
- [ ] Testing strategy is defined
- [ ] Deployment and environments are defined
- [ ] FR-to-component and NFR-to-solution traceability exists

### 3.3 Failed Checks

- {Failed check}: {evidence and impact}

---

## 4. Issues and Risk Classification

### 4.1 Blockers (Must Resolve Before Implementation)

- {Issue}: {why critical}, Owner: {name}, Target Date: {date}, Mitigation: {plan}

### 4.2 Major Concerns (Strong Recommendation to Resolve Early)

- {Issue}: {impact}, Owner: {name}, Target Date: {date}

### 4.3 Minor Issues (Track During Implementation)

- {Issue}: {impact}, Owner: {name}, Target Date: {date}

---

## 5. Recommendations

1. {Actionable recommendation 1}
2. {Actionable recommendation 2}
3. {Actionable recommendation 3}

---

## 6. Gate Decision

### 6.1 Thresholds

**PASS requires all:**
- FR Coverage >= 90%
- NFR Coverage >= 90%
- Quality Score >= 80%
- No unresolved critical blockers

**CONDITIONAL PASS requires all:**
- FR Coverage >= 80%
- NFR Coverage >= 80%
- Quality Score >= 70%
- Blockers have mitigation plan with owner and date

**FAIL if any:**
- FR Coverage < 80%, or
- NFR Coverage < 80%, or
- Quality Score < 70%, or
- unresolved critical blockers

### 6.2 Evaluation

- FR Coverage: {fr_coverage}% -> {meets/does_not_meet}
- NFR Coverage: {nfr_coverage}% -> {meets/does_not_meet}
- Quality Score: {quality_score}% -> {meets/does_not_meet}
- Critical Blockers: {none | listed and mitigated | unresolved}

**Final Decision:** {PASS | CONDITIONAL PASS | FAIL}

**Decision Rationale:**
{explain why the decision follows the thresholds}

---

## 7. Next Steps

**If PASS:**
- Proceed to `bmad:sprint-plan`.

**If CONDITIONAL PASS:**
- Proceed to `bmad:sprint-plan`.
- Track conditions as mandatory early-sprint tasks.

**If FAIL:**
- Update `docs/bmad/architecture.md` to address blockers.
- Re-run `bmad:gate-check`.

---

## 8. Appendix: Detailed Evidence

### 8.1 FR Traceability Notes
{detailed per-FR evidence}

### 8.2 NFR Traceability Notes
{detailed per-NFR evidence}

### 8.3 Checklist Evidence
{links/quotes/sections used during validation}
