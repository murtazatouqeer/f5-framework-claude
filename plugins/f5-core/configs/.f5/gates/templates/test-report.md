# Test Report

**Project:** {{PROJECT_NAME}}
**Date:** {{DATE}}
**Type:** {{TEST_TYPE}}
**Gate:** {{GATE_ID}}

---

## Summary

| Metric | Value |
|--------|-------|
| Total Tests | {{TOTAL}} |
| Passed | {{PASSED}} |
| Failed | {{FAILED}} |
| Skipped | {{SKIPPED}} |
| Duration | {{DURATION}} |
| Pass Rate | {{PASS_RATE}}% |

---

## Coverage

| Type | Coverage | Target | Status |
|------|----------|--------|--------|
| Statements | {{STMT_COV}}% | {{STMT_TARGET}}% | {{STMT_STATUS}} |
| Branches | {{BRANCH_COV}}% | {{BRANCH_TARGET}}% | {{BRANCH_STATUS}} |
| Functions | {{FUNC_COV}}% | {{FUNC_TARGET}}% | {{FUNC_STATUS}} |
| Lines | {{LINE_COV}}% | {{LINE_TARGET}}% | {{LINE_STATUS}} |

### Coverage Summary

```
Overall Coverage: {{OVERALL_COV}}%
Target: {{OVERALL_TARGET}}%
Status: {{OVERALL_STATUS}}
```

---

## Test Results by Suite

{{#each SUITES}}
### {{name}}

| Test | Status | Duration |
|------|--------|----------|
{{#each tests}}
| {{name}} | {{status}} | {{duration}} |
{{/each}}

**Suite Summary:** {{passed}}/{{total}} passed ({{pass_rate}}%)

{{/each}}

---

## Failed Tests

{{#if FAILED_TESTS}}
{{#each FAILED_TESTS}}
### :x: {{name}}

**File:** `{{file}}`
**Line:** {{line}}

**Error:**
```
{{error}}
```

**Stack Trace:**
```
{{stack_trace}}
```

{{#if suggestion}}
**Suggestion:** {{suggestion}}
{{/if}}

---

{{/each}}
{{else}}
No failed tests! :tada:
{{/if}}

---

## Skipped Tests

{{#if SKIPPED_TESTS}}
| Test | Reason |
|------|--------|
{{#each SKIPPED_TESTS}}
| {{name}} | {{reason}} |
{{/each}}
{{else}}
No skipped tests.
{{/if}}

---

## Slowest Tests

| Test | Duration | File |
|------|----------|------|
{{#each SLOWEST_TESTS}}
| {{name}} | {{duration}} | {{file}} |
{{/each}}

---

## Uncovered Code

{{#if UNCOVERED}}
### Files with Low Coverage

| File | Statements | Branches | Functions | Lines |
|------|------------|----------|-----------|-------|
{{#each UNCOVERED}}
| {{file}} | {{statements}}% | {{branches}}% | {{functions}}% | {{lines}}% |
{{/each}}

### Specific Uncovered Areas

{{#each UNCOVERED}}
#### {{file}}

**Uncovered Lines:** {{uncovered_lines}}
**Uncovered Functions:** {{uncovered_functions}}

{{/each}}
{{else}}
All code is covered! :white_check_mark:
{{/if}}

---

## Test Trends

| Metric | Previous | Current | Change |
|--------|----------|---------|--------|
| Pass Rate | {{PREV_PASS_RATE}}% | {{PASS_RATE}}% | {{PASS_RATE_CHANGE}} |
| Coverage | {{PREV_COVERAGE}}% | {{OVERALL_COV}}% | {{COVERAGE_CHANGE}} |
| Duration | {{PREV_DURATION}} | {{DURATION}} | {{DURATION_CHANGE}} |
| Total Tests | {{PREV_TOTAL}} | {{TOTAL}} | {{TOTAL_CHANGE}} |

---

## Recommendations

{{#if LOW_COVERAGE_FILES}}
### Improve Coverage

The following files need additional tests:
{{#each LOW_COVERAGE_FILES}}
- `{{file}}` - Current: {{coverage}}%, Target: {{target}}%
{{/each}}
{{/if}}

{{#if FLAKY_TESTS}}
### Address Flaky Tests

The following tests have been flaky:
{{#each FLAKY_TESTS}}
- `{{name}}` - Failed {{fail_count}}/{{total_runs}} times
{{/each}}
{{/if}}

{{#if SLOW_TESTS}}
### Optimize Slow Tests

Consider optimizing these slow tests:
{{#each SLOW_TESTS}}
- `{{name}}` - {{duration}} (threshold: {{threshold}})
{{/each}}
{{/if}}

---

## Commands Used

```bash
# Run all tests
{{TEST_COMMAND}}

# Run with coverage
{{COVERAGE_COMMAND}}

# Run specific suite
{{SUITE_COMMAND}}
```

---

## Artifacts

| Artifact | Location |
|----------|----------|
| Coverage Report | {{COVERAGE_REPORT_PATH}} |
| JUnit XML | {{JUNIT_XML_PATH}} |
| HTML Report | {{HTML_REPORT_PATH}} |

---

**Generated:** {{TIMESTAMP}}
**Test Runner:** {{TEST_RUNNER}} v{{TEST_RUNNER_VERSION}}
