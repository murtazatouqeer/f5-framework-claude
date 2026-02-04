# TDD Session Report Template

<!--
  This template is used to generate TDD session reports.
  Variables are in {{mustache}} format.
-->

---

# TDD Session Report: {{session_id}}

**Generated**: {{generated_at}}
**Feature**: {{feature_name}}
**Requirement**: {{requirement_id}}

---

## Executive Summary

| Metric | Value | Status |
|--------|-------|--------|
| Session Duration | {{duration}} | {{duration_status}} |
| Cycles Completed | {{cycles_completed}} | {{cycles_status}} |
| Tests Written | {{tests_written}} | - |
| Tests Passing | {{tests_passing}}/{{tests_total}} ({{pass_rate}}%) | {{tests_status}} |
| Coverage | {{coverage_avg}}% | {{coverage_status}} |
| Efficiency Score | {{efficiency_score}} | {{efficiency_status}} |

### Result: {{#if success}}✅ SUCCESS{{else}}❌ INCOMPLETE{{/if}}

---

## Timeline

```
Session Timeline
├── Started: {{started_at}}
{{#each cycles}}
├── Cycle {{number}}
│   ├── 🔴 RED:      {{red_start}} → {{red_end}} ({{red_duration}})
│   ├── 🟢 GREEN:    {{green_start}} → {{green_end}} ({{green_duration}})
│   └── 🔵 REFACTOR: {{refactor_start}} → {{refactor_end}} ({{refactor_duration}})
{{/each}}
└── Completed: {{completed_at}}
```

**Total Duration**: {{total_duration}}

---

## Coverage Results

### Final Coverage

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Statements | {{coverage.statements}}% | ≥{{targets.statements}}% | {{coverage.statements_status}} |
| Branches | {{coverage.branches}}% | ≥{{targets.branches}}% | {{coverage.branches_status}} |
| Functions | {{coverage.functions}}% | ≥{{targets.functions}}% | {{coverage.functions_status}} |
| Lines | {{coverage.lines}}% | ≥{{targets.lines}}% | {{coverage.lines_status}} |

### Coverage Progress

```
Coverage Progression Over Cycles
│
│     {{coverage_graph}}
│
└───────────────────────────────────
   Cycle:  {{#each cycles}}{{number}}   {{/each}}
```

---

## Cycle Details

{{#each cycles}}
### Cycle {{number}}: {{description}}

#### 🔴 RED Phase

**Duration**: {{red_duration}}
**Tests Written**: {{tests_written}}

| Category | Count |
|----------|-------|
{{#each categories}}
| {{name}} | {{count}} |
{{/each}}

**Test Files Created/Modified**:
{{#each test_files}}
- `{{path}}`
{{/each}}

#### 🟢 GREEN Phase

**Duration**: {{green_duration}}
**Tests Passing**: {{tests_passing}}/{{tests_total}}
**Lines Added**: {{lines_added}}

**Implementation Files Created/Modified**:
{{#each implementation_files}}
- `{{path}}`
{{/each}}

#### 🔵 REFACTOR Phase

**Duration**: {{refactor_duration}}
**Tests Still Passing**: {{#if tests_still_passing}}✅ Yes{{else}}❌ No{{/if}}

**Refactorings Applied**:
{{#each refactorings}}
- {{description}}
{{/each}}

**Complexity Change**:
- Before: {{complexity_before}}
- After: {{complexity_after}}
- Change: {{complexity_change}}

---

{{/each}}

## Test Summary

### Tests by Category

| Category | Count | Percentage |
|----------|-------|------------|
{{#each test_categories}}
| {{name}} | {{count}} | {{percentage}}% |
{{/each}}
| **Total** | **{{tests_total}}** | **100%** |

### Test Distribution

```
{{test_distribution_chart}}
```

### Test Files

| File | Tests | Status |
|------|-------|--------|
{{#each test_files}}
| `{{path}}` | {{test_count}} | {{status}} |
{{/each}}

---

## Implementation Summary

### Files Modified

| File | Lines Added | Lines Removed | Net Change |
|------|-------------|---------------|------------|
{{#each implementation_files}}
| `{{path}}` | +{{added}} | -{{removed}} | {{net}} |
{{/each}}
| **Total** | **+{{total_added}}** | **-{{total_removed}}** | **{{total_net}}** |

### Code Quality

| Metric | Value |
|--------|-------|
| Cyclomatic Complexity (avg) | {{complexity_avg}} |
| Test/Code Ratio | {{test_code_ratio}} |
| Assertions per Test | {{assertions_per_test}} |

---

## Efficiency Analysis

### Phase Balance

| Phase | Actual | Target | Variance |
|-------|--------|--------|----------|
| RED | {{phase_balance.red}}% | 25-35% | {{phase_balance.red_variance}} |
| GREEN | {{phase_balance.green}}% | 40-50% | {{phase_balance.green_variance}} |
| REFACTOR | {{phase_balance.refactor}}% | 20-30% | {{phase_balance.refactor_variance}} |

```
Phase Distribution
┌─────────────────────────────────────────────────────────┐
│ RED        {{phase_bar.red}}  {{phase_balance.red}}%
│ GREEN      {{phase_bar.green}}  {{phase_balance.green}}%
│ REFACTOR   {{phase_bar.refactor}}  {{phase_balance.refactor}}%
└─────────────────────────────────────────────────────────┘
```

### Velocity

- **Cycles per Hour**: {{velocity}}
- **Target**: 3 cycles/hour
- **Rating**: {{velocity_rating}}

### First-Time Pass Rate

- **Rate**: {{first_time_pass_rate}}%
- **Tests Passing First Try**: {{first_time_passing}}/{{tests_total}}

---

## Traceability

### Requirements Coverage

| Requirement | Tests | Status |
|-------------|-------|--------|
{{#each requirements}}
| {{id}}: {{description}} | {{test_count}} | {{status}} |
{{/each}}

### Traceability Matrix

```
{{traceability_matrix}}
```

---

## Issues and Notes

{{#if issues}}
### Issues Encountered

{{#each issues}}
- **{{severity}}**: {{description}}
  - Resolution: {{resolution}}
{{/each}}
{{else}}
No issues encountered during this session.
{{/if}}

{{#if notes}}
### Session Notes

{{#each notes}}
- {{note}}
{{/each}}
{{/if}}

---

## Recommendations

{{#if recommendations}}
{{#each recommendations}}
### {{category}}

{{description}}

**Suggested Actions**:
{{#each actions}}
- {{action}}
{{/each}}

{{/each}}
{{else}}
No specific recommendations for this session.
{{/if}}

---

## Metrics Summary

### Session Metrics

```json
{
  "session_id": "{{session_id}}",
  "feature": "{{feature_name}}",
  "requirement": "{{requirement_id}}",
  "started_at": "{{started_at}}",
  "completed_at": "{{completed_at}}",
  "duration_minutes": {{duration_minutes}},
  "cycles": {{cycles_completed}},
  "tests": {
    "written": {{tests_written}},
    "passing": {{tests_passing}},
    "failing": {{tests_failing}}
  },
  "coverage": {
    "statements": {{coverage.statements}},
    "branches": {{coverage.branches}},
    "functions": {{coverage.functions}},
    "lines": {{coverage.lines}}
  },
  "efficiency": {
    "velocity": {{velocity}},
    "phase_balance": {
      "red": {{phase_balance.red}},
      "green": {{phase_balance.green}},
      "refactor": {{phase_balance.refactor}}
    },
    "first_time_pass_rate": {{first_time_pass_rate}},
    "score": {{efficiency_score}}
  }
}
```

---

## Gate G3 Evidence

This TDD session provides evidence for Quality Gate G3 (Testing Complete):

| Criteria | Evidence | Status |
|----------|----------|--------|
| Unit test coverage ≥ 80% | {{coverage_avg}}% coverage achieved | {{coverage_status}} |
| All tests passing | {{tests_passing}}/{{tests_total}} tests passing | {{tests_status}} |
| Test documentation | This report generated | ✅ |
| Requirement traceability | {{requirements_covered}}/{{requirements_total}} requirements covered | {{traceability_status}} |

---

**Report Generated By**: F5 Framework TDD Module
**Version**: {{f5_version}}
**Timestamp**: {{generated_at}}

---

*This report is automatically generated and saved to `.f5/evidence/G3/`*
