---
description: Shared testing patterns and templates (internal)
---

# Testing Shared Patterns

> **Internal Reference**: This file contains shared patterns used by `/f5-test-*` commands.
> **Not directly invocable** - Use `/f5-test`, `/f5-test-unit`, `/f5-test-it`, `/f5-test-e2e`, or `/f5-tdd`

---

## STACK DETECTION MATRIX

### Auto-Detection from `.f5/config.json`

```bash
BACKEND=$(jq -r '.stack.backend[0] // .stack.backend // "unknown"' .f5/config.json)
FRONTEND=$(jq -r '.stack.frontend // "unknown"' .f5/config.json)
```

### Test Framework by Stack

| Stack | Test Framework | Coverage Tool | Config File |
|-------|----------------|---------------|-------------|
| nestjs | Jest | istanbul | jest.config.js |
| spring | JUnit 5 + Mockito | JaCoCo | pom.xml |
| fastapi | pytest | pytest-cov | pytest.ini |
| go | go test | go cover | go.mod |
| django | pytest-django | coverage.py | pytest.ini |
| laravel | PHPUnit | phpunit | phpunit.xml |
| rails | RSpec | SimpleCov | .rspec |
| react | Vitest/Jest + RTL | c8/istanbul | vitest.config.ts |
| nextjs | Jest + RTL | istanbul | jest.config.js |
| vue | Vitest | c8 | vitest.config.ts |
| angular | Jasmine + Karma | istanbul | karma.conf.js |
| flutter | flutter_test | lcov | pubspec.yaml |

### Test Commands by Stack

| Stack | Unit Test | Coverage | Watch |
|-------|-----------|----------|-------|
| nestjs | `npm test` | `npm run test:cov` | `npm run test:watch` |
| spring | `mvn test` | `mvn jacoco:report` | - |
| fastapi | `pytest` | `pytest --cov` | `pytest-watch` |
| go | `go test ./...` | `go test -cover ./...` | - |
| react | `npm test` | `npm run test:coverage` | `npm run test:watch` |
| vue | `npm test` | `npm run test:coverage` | `npm run test:watch` |

---

## MCP PRE-FLIGHT CHECK

### Pattern for Commands Requiring MCP

```markdown
## MCP Pre-Flight Check

| MCP Server | Required For | Status |
|------------|--------------|--------|
| Playwright | E2E, Visual, Browser tests | 🔄 Checking... |
| Sequential | Multi-step analysis, IT flows | 🔄 Checking... |

### If MCP Unavailable

**Degraded Mode Available:**
- ⚠️ `[MCP_NAME]` not available
- Continuing with limited functionality
- Some features disabled: [list features]

**To Enable Full Features:**
```bash
/f5-mcp status          # Check MCP health
/f5-mcp profile full    # Enable all MCPs
```
```

### Implementation Check

```yaml
# For Playwright-dependent commands
playwright_check:
  test_action: "browser_snapshot or browser_navigate"
  fallback: "Manual testing instructions provided"
  affected_features:
    - Screenshot capture
    - Browser automation
    - Visual comparison

# For Sequential-dependent commands
sequential_check:
  test_action: "Think step by step analysis"
  fallback: "Single-step analysis mode"
  affected_features:
    - Multi-step flow analysis
    - Complex reasoning chains
```

---

## G3 GATE INTEGRATION

### Test Sequence for G3 Gate

```yaml
g3_test_sequence:
  1. unit_tests:
     command: "/f5-test run --type unit --ci"
     required: true
     pass_criteria: "100% pass rate"

  2. coverage_check:
     command: "/f5-test coverage"
     required: true
     pass_criteria: "≥80% coverage"

  3. integration_tests:
     command: "/f5-test run --type integration --ci"
     required: true
     pass_criteria: "100% pass rate"

  4. e2e_tests:
     command: "/f5-test run --type e2e --ci"
     required: true
     pass_criteria: "≥95% pass rate"

  5. visual_tests:
     command: "/f5-test-e2e visual --ci --threshold 5"
     required: true
     pass_criteria: "≤5% visual diff"

  6. report_generation:
     command: "/f5-test report"
     required: true
     output: ".f5/output/g3-test-report.md"
```

### Coverage Targets

| Metric | Target | G3 Required |
|--------|--------|-------------|
| Statements | ≥80% | Yes |
| Branches | ≥75% | Yes |
| Functions | ≥80% | Yes |
| Lines | ≥80% | Yes |

---

## BUG DETECTION & FIX FLOW

### Standard Bug Report Format

```markdown
## 🐛 Bug Detected

**File:** [file_path]
**Function:** [function_name]
**Line:** [line_number]

### Issue
```[language]
// Current code (buggy):
[code_snippet]
```

### Root Cause
[Description of why the bug occurs]

### Impact
- [Impact point 1]
- [Impact point 2]

### Suggested Fix
```[language]
// Fixed code:
[fixed_code_snippet]
```
```

### Auto-Fix Flow (with --fix flag)

```
┌─────────────────────────────────────────────────────────────┐
│                     AUTO-FIX FLOW                            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   Test Fails                                                 │
│       │                                                      │
│       ▼                                                      │
│   ┌───────────────┐                                         │
│   │ Analyze Error │                                         │
│   └───────┬───────┘                                         │
│           │                                                  │
│           ▼                                                  │
│   ┌───────────────┐     ┌───────────────┐                   │
│   │ Can Auto-Fix? │────▶│ --fix flag?   │                   │
│   └───────┬───────┘     └───────┬───────┘                   │
│           │                     │                            │
│      No   │  Yes           No   │  Yes                       │
│           ▼                     ▼                            │
│   ┌───────────────┐     ┌───────────────┐                   │
│   │ Show Manual   │     │ Apply Fix     │                   │
│   │ Fix Guide     │     │ Automatically │                   │
│   └───────────────┘     └───────┬───────┘                   │
│                                 │                            │
│                                 ▼                            │
│                         ┌───────────────┐                   │
│                         │ Re-run Test   │                   │
│                         └───────┬───────┘                   │
│                                 │                            │
│                            Pass │ Fail                       │
│                                 ▼                            │
│                         ┌───────────────┐                   │
│                         │ Report Result │                   │
│                         └───────────────┘                   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## COMMON OUTPUT TEMPLATES

### Test Summary Template

```markdown
## 🧪 Test Results

**Type:** [Unit|Integration|E2E|Visual]
**Framework:** [Jest|pytest|etc.]
**Duration:** [time]

### Summary
| Metric | Result |
|--------|--------|
| Test Suites | [X] passed, [Y] failed |
| Tests | [X] passed, [Y] failed |
| Coverage | [X]% |

### Status
[✅ PASSED | ❌ FAILED | ⚠️ PARTIAL]

### Next Steps
1. [Step 1]
2. [Step 2]
```

### Coverage Report Template

```markdown
## 📊 Coverage Report

| Module | Stmts | Branch | Funcs | Lines | Status |
|--------|-------|--------|-------|-------|--------|
| [module] | [X]% | [X]% | [X]% | [X]% | [✅|⚠️|❌] |

**Overall:** [X]% (Target: ≥80%)
```

---

## TEST FILE CONVENTIONS

### File Naming

| Stack | Unit Test | Integration | E2E |
|-------|-----------|-------------|-----|
| JS/TS | `*.spec.ts`, `*.test.ts` | `*.integration.spec.ts` | `*.e2e-spec.ts` |
| Python | `test_*.py` | `test_*_integration.py` | `test_*_e2e.py` |
| Go | `*_test.go` | `*_integration_test.go` | `*_e2e_test.go` |
| Java | `*Test.java` | `*IT.java` | `*E2E.java` |

### Test Location

```yaml
conventions:
  unit:
    - "__tests__/" (Jest convention)
    - "tests/unit/"
    - Co-located with source

  integration:
    - "tests/integration/"
    - "tests/api/"

  e2e:
    - "tests/e2e/"
    - "e2e/"
```

---

## TRACEABILITY COMMENT PATTERN

```typescript
// REQ-XXX: [Requirement description]
describe('[ComponentName]', () => {
  // REQ-XXX: Test case for [specific requirement]
  it('should [expected behavior]', () => {
    // Test implementation
  });
});
```

---

## SEE ALSO

- `/f5-test` - Master test command (orchestration)
- `/f5-test-unit` - Unit testing
- `/f5-test-it` - Integration testing
- `/f5-test-e2e` - E2E and Visual testing
- `/f5-tdd` - TDD workflow
- `/f5-gate` - Quality gates (G3)
