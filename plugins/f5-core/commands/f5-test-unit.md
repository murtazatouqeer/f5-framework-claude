---
name: f5-test-unit
description: Unit testing operations
argument-hint: <generate|run> [path] [--coverage] [--fix]
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: true
---

# /f5-test-unit - Unit Testing

> **Version**: 1.4.0
> **Category**: Testing
> **Purpose**: Unit testing trực tiếp với khả năng fix bug ngay

## ARGUMENTS
The user's request is: $ARGUMENTS

---

## COMMAND SYNTAX

```bash
# Test một file cụ thể
/f5-test-unit src/core/excel-processor.ts

# Test một thư mục
/f5-test-unit src/core/

# Test với auto-fix
/f5-test-unit src/core/excel-processor.ts --fix

# Test và generate report
/f5-test-unit src/core/ --report

# Test specific function
/f5-test-unit src/core/excel-processor.ts::parseFile

# Test changed files only
/f5-test-unit
```

---

## FLAGS

| Flag | Description |
|------|-------------|
| `--fix` | Auto-fix bugs found |
| `--report` | Generate test report |
| `--verbose` | Detailed output |
| `--coverage` | Calculate coverage estimate |
| `--v1..--v5` | Verbosity levels |

---

## INPUT PATTERNS

| Input | Type | Action |
|-------|------|--------|
| `*.ts` file | Single file | Test all exports |
| `*/` directory | Directory | Test all files |
| `file::function` | Specific | Test one function |
| No input | Auto | Test changed files |

---

## WORKFLOW

```
┌─────────────────────────────────────────────────────────────┐
│                   UNIT TEST WORKFLOW                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   /f5-test-unit [target]                                     │
│           │                                                  │
│           ▼                                                  │
│   ┌───────────────┐                                         │
│   │ Analyze Code  │                                         │
│   │ • Parse exports                                         │
│   │ • Identify deps                                         │
│   │ • Detect testable units                                 │
│   └───────┬───────┘                                         │
│           │                                                  │
│           ▼                                                  │
│   ┌───────────────┐     ┌───────────────┐                   │
│   │ Execute Tests │────▶│ Bug Found?    │                   │
│   └───────────────┘     └───────┬───────┘                   │
│                                 │                            │
│                    Yes ─────────┼───────── No                │
│                    ▼            │            ▼               │
│           ┌───────────────┐     │    ┌───────────────┐      │
│           │ --fix flag?   │     │    │ ✅ All Pass   │      │
│           └───────┬───────┘     │    └───────────────┘      │
│                   │             │                            │
│          Yes ─────┼───── No     │                           │
│          ▼        │       ▼     │                           │
│   ┌─────────────┐ │ ┌─────────────┐                         │
│   │ Auto-Fix    │ │ │ Suggest Fix │                         │
│   │ & Re-test   │ │ │ (Manual)    │                         │
│   └─────────────┘ │ └─────────────┘                         │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## TEST CATEGORIES

| Category | Description | Priority |
|----------|-------------|----------|
| **Happy Path** | Normal input → Expected output | High |
| **Edge Cases** | Boundary values, empty input | High |
| **Error Cases** | Invalid input → Proper error | Medium |
| **Type Safety** | Type validation | Medium |

---

## SOURCE ANALYSIS OUTPUT

```markdown
## 📊 Source Analysis: [filename]

### Exports Found
| Name | Type | Lines | Complexity |
|------|------|-------|------------|
| parseFile | function | 45-120 | Medium |
| validateData | function | 122-150 | Low |

### Dependencies
- fs-extra (external)
- xlsx (external)
- ./types (internal)

### Test Cases Identified
| Function | Happy | Edge | Error | Total |
|----------|-------|------|-------|-------|
| parseFile | 3 | 2 | 2 | 7 |
| validateData | 2 | 1 | 1 | 4 |
```

---

## BUG DETECTION & AUTO-FIX

### When Bug Found

```markdown
## 🐛 Bug Detected

**File:** src/core/excel-processor.ts
**Function:** parseFile
**Line:** 78

### Issue
```typescript
// Current code (buggy):
if (data.length = 0) {  // ❌ Assignment instead of comparison
  return null;
}
```

### Root Cause
Using `=` instead of `===` in condition check.

### Suggested Fix
```typescript
// Fixed code:
if (data.length === 0) {  // ✅ Correct comparison
  return null;
}
```
```

### With --fix Flag

```markdown
## 🔧 Auto-Fix Applied

**File:** src/core/excel-processor.ts

### Changes Made
| Line | Before | After |
|------|--------|-------|
| 78 | `if (data.length = 0)` | `if (data.length === 0)` |

### Verification
- Re-running test case...
- Result: ✅ PASS
```

---

## OUTPUT FORMATS

### Minimal (--v1)
```
Unit Test: src/core/excel-processor.ts
Result: 9/11 ✅ | 2 ❌ (auto-fixed 1)
```

### Concise (--v2)
```markdown
## Unit Test: excel-processor.ts

✅ 9 passed | ❌ 2 failed

**Failed:**
- parseFile: Empty file handling → Auto-fixed ✅
- validateData: Error message → Manual fix needed

**Next:** Fix validateData or `/f5-test-unit --fix`
```

### Balanced (--v3, default)

Full report với summary, failed tests, và suggestions.

### Detailed (--v4) / Comprehensive (--v5)

Includes all test cases, code paths, và detailed analysis.

---

## TEST REPORT

```markdown
## 🧪 Unit Test Report

**Target:** src/core/excel-processor.ts
**Date:** [timestamp]
**Duration:** [time]

### Summary
| Metric | Value |
|--------|-------|
| Total Tests | 11 |
| Passed | 9 |
| Failed | 2 |
| Pass Rate | 81.8% |

### Results by Function
| Function | Tests | Pass | Fail | Status |
|----------|-------|------|------|--------|
| parseFile | 7 | 6 | 1 | ⚠️ |
| validateData | 4 | 3 | 1 | ⚠️ |

### Coverage Estimate
| Type | Covered | Total | % |
|------|---------|-------|---|
| Functions | 2 | 2 | 100% |
| Branches | 8 | 10 | 80% |
| Lines | 95 | 120 | 79% |

### Next Steps
1. Fix remaining issue in validateData
2. Re-run: `/f5-test-unit src/core/excel-processor.ts`
```

---

## INTEGRATION

### With /f5-test

```bash
# Master command delegates
/f5-test run --type unit src/core/  →  /f5-test-unit src/core/
```

### With /f5-tdd

```bash
# TDD red phase uses unit tests
/f5-tdd red  →  /f5-test-unit [feature] --expect-fail
```

### With /f5-gate

```bash
# G3 gate runs full unit tests
/f5-gate check G3  →  /f5-test-unit src/ --report
```

---

## EXAMPLES

```bash
# Test single file
/f5-test-unit src/core/excel-processor.ts

# Test with auto-fix
/f5-test-unit src/core/ --fix

# Test specific function
/f5-test-unit src/core/version-manager.ts::createVersion

# Test and generate report for G3
/f5-test-unit src/ --report --coverage

# Quick check changed files
/f5-test-unit

# Different verbosity levels
/f5-test-unit src/ --v1    # Minimal
/f5-test-unit src/ --v3    # Balanced (default)
/f5-test-unit src/ --v5    # Comprehensive
```

---

## FIXTURES

Unit tests sử dụng fixtures từ:
- `packages/cli/test/fixtures/` - Excel files
- `.f5/testing/fixtures/` - Additional test data

---

## SEE ALSO

- `/f5-test` - Master test command
- `/f5-test-it` - Integration testing
- `/f5-test-e2e` - E2E testing
- `/f5-tdd` - TDD workflow
- `/f5-gate` - Quality gates (G3)
- `_test-shared.md` - Stack detection, common patterns
