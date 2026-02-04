# Project Quality Summary

**Project:** {{PROJECT_NAME}}
**Date:** {{DATE}}
**Sprint/Release:** {{SPRINT}}
**Version:** {{VERSION}}

---

## Gates Overview

```
D1 ──▶ D2 ──▶ D3 ──▶ D4 ──▶ G2 ──▶ G3 ──▶ G4
{{D1_ICON}}    {{D2_ICON}}    {{D3_ICON}}    {{D4_ICON}}    {{G2_ICON}}    {{G3_ICON}}    {{G4_ICON}}
```

| Gate | Name | Japanese | Status | Started | Completed | Duration |
|------|------|----------|--------|---------|-----------|----------|
| D1 | Research Complete | 調査完了 | {{D1_STATUS}} | {{D1_START}} | {{D1_END}} | {{D1_DURATION}} |
| D2 | SRS Approved | SRS承認 | {{D2_STATUS}} | {{D2_START}} | {{D2_END}} | {{D2_DURATION}} |
| D3 | Basic Design | 基本設計承認 | {{D3_STATUS}} | {{D3_START}} | {{D3_END}} | {{D3_DURATION}} |
| D4 | Detail Design | 詳細設計承認 | {{D4_STATUS}} | {{D4_START}} | {{D4_END}} | {{D4_DURATION}} |
| G2 | Implementation | 実装完了 | {{G2_STATUS}} | {{G2_START}} | {{G2_END}} | {{G2_DURATION}} |
| G3 | Testing | テスト完了 | {{G3_STATUS}} | {{G3_START}} | {{G3_END}} | {{G3_DURATION}} |
| G4 | Deployment | デプロイ準備完了 | {{G4_STATUS}} | {{G4_START}} | {{G4_END}} | {{G4_DURATION}} |

### Current Progress

```
┌─────────────────────────────────────────────────────────────┐
│  Current Gate: {{CURRENT_GATE}}                             │
│  Progress: {{PROGRESS}}%                                    │
│  Items Completed: {{ITEMS_COMPLETED}}/{{ITEMS_TOTAL}}       │
│  Blockers: {{BLOCKERS_COUNT}}                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Quality Metrics

### Code Quality

| Metric | Value | Target | Status | Trend |
|--------|-------|--------|--------|-------|
| Test Coverage | {{COVERAGE}}% | 80% | {{COV_STATUS}} | {{COV_TREND}} |
| Cyclomatic Complexity | {{COMPLEXITY}} | <10 | {{COMP_STATUS}} | {{COMP_TREND}} |
| Code Duplication | {{DUPLICATION}}% | <5% | {{DUP_STATUS}} | {{DUP_TREND}} |
| Tech Debt | {{TECH_DEBT}} | <2d | {{DEBT_STATUS}} | {{DEBT_TREND}} |
| Lint Errors | {{LINT_ERRORS}} | 0 | {{LINT_STATUS}} | {{LINT_TREND}} |
| Type Errors | {{TYPE_ERRORS}} | 0 | {{TYPE_STATUS}} | {{TYPE_TREND}} |

### Code Quality Score: {{CODE_QUALITY_SCORE}}/100

---

### Testing Summary

| Type | Total | Passed | Failed | Skipped | Coverage |
|------|-------|--------|--------|---------|----------|
| Unit | {{UNIT_TOTAL}} | {{UNIT_PASS}} | {{UNIT_FAIL}} | {{UNIT_SKIP}} | {{UNIT_COV}}% |
| Integration | {{INT_TOTAL}} | {{INT_PASS}} | {{INT_FAIL}} | {{INT_SKIP}} | {{INT_COV}}% |
| E2E | {{E2E_TOTAL}} | {{E2E_PASS}} | {{E2E_FAIL}} | {{E2E_SKIP}} | {{E2E_COV}}% |
| Performance | {{PERF_TOTAL}} | {{PERF_PASS}} | {{PERF_FAIL}} | {{PERF_SKIP}} | - |
| **Total** | **{{TEST_TOTAL}}** | **{{TEST_PASS}}** | **{{TEST_FAIL}}** | **{{TEST_SKIP}}** | **{{TEST_COV}}%** |

### Test Pass Rate: {{TEST_PASS_RATE}}%

---

### Security

| Severity | Found | Resolved | Open |
|----------|-------|----------|------|
| Critical | {{SEC_CRIT_FOUND}} | {{SEC_CRIT_RES}} | {{SEC_CRIT_OPEN}} |
| High | {{SEC_HIGH_FOUND}} | {{SEC_HIGH_RES}} | {{SEC_HIGH_OPEN}} |
| Medium | {{SEC_MED_FOUND}} | {{SEC_MED_RES}} | {{SEC_MED_OPEN}} |
| Low | {{SEC_LOW_FOUND}} | {{SEC_LOW_RES}} | {{SEC_LOW_OPEN}} |

### Security Score: {{SECURITY_SCORE}}/100 ({{SECURITY_GRADE}})

---

### Performance

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Response Time (p50) | {{RT_P50}} | {{RT_P50_TARGET}} | {{RT_P50_STATUS}} |
| Response Time (p95) | {{RT_P95}} | {{RT_P95_TARGET}} | {{RT_P95_STATUS}} |
| Response Time (p99) | {{RT_P99}} | {{RT_P99_TARGET}} | {{RT_P99_STATUS}} |
| Throughput | {{THROUGHPUT}} | {{THROUGHPUT_TARGET}} | {{THROUGHPUT_STATUS}} |
| Error Rate | {{ERROR_RATE}} | {{ERROR_TARGET}} | {{ERROR_STATUS}} |

### Performance Score: {{PERF_SCORE}}/100

---

## Requirements Traceability

| Category | Total | Implemented | Tested | Verified |
|----------|-------|-------------|--------|----------|
| Functional (FR) | {{FUNC_TOTAL}} | {{FUNC_IMPL}} | {{FUNC_TEST}} | {{FUNC_VER}} |
| Non-Functional (NFR) | {{NFR_TOTAL}} | {{NFR_IMPL}} | {{NFR_TEST}} | {{NFR_VER}} |
| Use Cases (UC) | {{UC_TOTAL}} | {{UC_IMPL}} | {{UC_TEST}} | {{UC_VER}} |
| User Stories (US) | {{US_TOTAL}} | {{US_IMPL}} | {{US_TEST}} | {{US_VER}} |

### Traceability Matrix

```
Requirements → Design → Code → Tests
    {{REQ_COUNT}}      →  {{DESIGN_COUNT}}  →  {{CODE_COUNT}} →  {{TEST_COUNT}}
```

**Traceability Coverage:** {{TRACE_COV}}%

---

## Timeline

### Milestones

| Milestone | Planned | Actual | Variance | Status |
|-----------|---------|--------|----------|--------|
{{#each MILESTONES}}
| {{name}} | {{planned}} | {{actual}} | {{variance}} | {{status}} |
{{/each}}

### Schedule Performance

- **Planned Duration:** {{PLANNED_DURATION}}
- **Actual Duration:** {{ACTUAL_DURATION}}
- **Schedule Variance:** {{SCHEDULE_VARIANCE}}
- **Schedule Performance Index (SPI):** {{SPI}}

---

## Risks & Issues

### Open Risks

| ID | Severity | Description | Mitigation | Owner |
|----|----------|-------------|------------|-------|
{{#each RISKS}}
| {{id}} | {{severity}} | {{description}} | {{mitigation}} | {{owner}} |
{{/each}}

{{#unless RISKS}}
No open risks.
{{/unless}}

### Open Issues

| ID | Priority | Description | Status | Assignee |
|----|----------|-------------|--------|----------|
{{#each ISSUES}}
| {{id}} | {{priority}} | {{description}} | {{status}} | {{assignee}} |
{{/each}}

{{#unless ISSUES}}
No open issues.
{{/unless}}

### Blockers

{{#if BLOCKERS}}
{{#each BLOCKERS}}
#### :rotating_light: {{title}}

**Impact:** {{impact}}
**Resolution:** {{resolution}}
**ETA:** {{eta}}

{{/each}}
{{else}}
No blockers currently.
{{/if}}

---

## Team Performance

### Velocity

| Sprint | Planned | Completed | Velocity |
|--------|---------|-----------|----------|
{{#each SPRINTS}}
| {{name}} | {{planned}} | {{completed}} | {{velocity}} |
{{/each}}

**Average Velocity:** {{AVG_VELOCITY}}

### Defect Metrics

| Metric | Value |
|--------|-------|
| Defects Found | {{DEFECTS_FOUND}} |
| Defects Fixed | {{DEFECTS_FIXED}} |
| Defect Density | {{DEFECT_DENSITY}} |
| Mean Time to Fix | {{MTTF}} |

---

## Documentation Status

| Document | Status | Last Updated | Owner |
|----------|--------|--------------|-------|
| SRS | {{SRS_STATUS}} | {{SRS_UPDATED}} | {{SRS_OWNER}} |
| Basic Design | {{BD_STATUS}} | {{BD_UPDATED}} | {{BD_OWNER}} |
| Detail Design | {{DD_STATUS}} | {{DD_UPDATED}} | {{DD_OWNER}} |
| Test Plan | {{TP_STATUS}} | {{TP_UPDATED}} | {{TP_OWNER}} |
| API Documentation | {{API_STATUS}} | {{API_UPDATED}} | {{API_OWNER}} |
| User Manual | {{UM_STATUS}} | {{UM_UPDATED}} | {{UM_OWNER}} |

---

## Customer Approvals

| Gate | Required | Status | Approver | Date |
|------|----------|--------|----------|------|
| D2 (SRS) | Yes | {{D2_APPROVAL}} | {{D2_APPROVER}} | {{D2_APPROVAL_DATE}} |
| D3 (Basic Design) | Yes | {{D3_APPROVAL}} | {{D3_APPROVER}} | {{D3_APPROVAL_DATE}} |
| D4 (Detail Design) | Yes | {{D4_APPROVAL}} | {{D4_APPROVER}} | {{D4_APPROVAL_DATE}} |
| G4 (Deployment) | Yes | {{G4_APPROVAL}} | {{G4_APPROVER}} | {{G4_APPROVAL_DATE}} |

---

## Recommendations

{{#each RECOMMENDATIONS}}
### {{order}}. {{category}}

**Priority:** {{priority}}
**Description:** {{description}}
**Impact:** {{impact}}
**Action:** {{action}}

{{/each}}

{{#unless RECOMMENDATIONS}}
No recommendations at this time.
{{/unless}}

---

## Overall Quality Score

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   OVERALL QUALITY SCORE: {{OVERALL_SCORE}}/100              │
│                                                             │
│   ┌─────────────────────────────────────────────────────┐   │
│   │ Code Quality:  {{CODE_QUALITY_SCORE}}/100           │   │
│   │ Test Coverage: {{TEST_COV}}%                        │   │
│   │ Security:      {{SECURITY_SCORE}}/100               │   │
│   │ Performance:   {{PERF_SCORE}}/100                   │   │
│   │ Traceability:  {{TRACE_COV}}%                       │   │
│   └─────────────────────────────────────────────────────┘   │
│                                                             │
│   Grade: {{OVERALL_GRADE}}                                  │
│   Status: {{PROJECT_STATUS}}                                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Next Actions

{{#each NEXT_ACTIONS}}
1. **{{category}}:** {{description}} ({{owner}}, Due: {{due_date}})
{{/each}}

---

**Generated:** {{TIMESTAMP}}
**Report Version:** {{REPORT_VERSION}}
**F5 Framework Version:** {{F5_VERSION}}
