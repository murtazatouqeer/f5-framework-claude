---
name: f5-test
description: Master testing command with TDD support
argument-hint: <generate|run|coverage|report>
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: true
---

# /f5-test - Testing Command (Master Orchestrator)

> **Version:** 1.5.0
> **Category:** Testing
> **Role:** Orchestrator - Delegates to specialized commands

Testing toàn diện với TDD support, coverage tracking, visual regression, và integration với G3 gate.

## ARGUMENTS
The user's request is: $ARGUMENTS

---

## COMMAND DELEGATION

`/f5-test` is the **master orchestrator**. It delegates to specialized commands:

| Task Type | Delegated To | MCP Tools | When to Use |
|-----------|--------------|-----------|-------------|
| Unit testing | `/f5-test-unit` | - | Isolated function/class testing |
| Integration | `/f5-test-it` | Sequential | API, DB, service testing |
| E2E testing | `/f5-test-e2e` | Playwright | User journey, browser testing |
| Visual testing | `/f5-test-e2e visual` | Playwright | Screenshot diff, Figma comparison |
| TDD workflow | `/f5-tdd` | - | Red-Green-Refactor cycle |
| Full suite | (all above) | All | G3 gate preparation |

### Delegation Flow

```
/f5-test all
    │
    ├── /f5-test-unit src/ --coverage
    │       └── Report: unit-results.json
    │
    ├── /f5-test-it --all
    │       └── Report: it-results.json
    │
    ├── /f5-test-e2e smoke
    │       └── Report: e2e-results.json
    │
    └── /f5-test-e2e visual --ci
            └── Report: visual-report.html

Final: Aggregate → G3 Report
```

---

## SUBCOMMANDS

| Subcommand | Description | Delegation |
|------------|-------------|------------|
| `generate [path]` | Generate tests từ source code | Native |
| `run [options]` | Run tests với options | → Specialized commands |
| `tdd <feature>` | TDD workflow | → `/f5-tdd` |
| `coverage` | Chi tiết coverage report | Native |
| `report` | Generate G3 gate report | Native |
| `watch` | Watch mode for development | Native |

---

## SUBCOMMAND: generate

```bash
/f5-test generate [path]
```

Generate tests từ source code với:
- Happy path tests
- Error case tests
- Edge case tests
- Mocks for dependencies

### Output

```markdown
## 🧪 Test Generation: [PATH]

### Files Analyzed
| File | Functions | Tests Generated |
|------|-----------|-----------------|
| user.service.ts | 5 | 12 |

### Generated Test Files
- `src/user/__tests__/user.service.spec.ts` (12 tests)

### Next Steps
1. Review generated tests
2. Run: `/f5-test run --path src/user`
```

> **Stack-specific templates**: See `_test-shared.md` for stack detection matrix

---

## SUBCOMMAND: run

```bash
/f5-test run [options]
```

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--type <type>` | Test type: `unit\|integration\|e2e\|all` | unit |
| `--path <path>` | Specific file/folder | . |
| `--watch` | Watch mode | false |
| `--coverage` | Show coverage | true |
| `--verbose` | Verbose output | false |
| `--ci` | CI mode (fail on threshold) | false |
| `--bail` | Stop on first failure | false |

### Delegation by Type

```yaml
delegation:
  --type unit:        → /f5-test-unit [path] [flags]
  --type integration: → /f5-test-it --all
  --type e2e:         → /f5-test-e2e smoke
  --type all:         → Run all in sequence
```

### Output

```markdown
## 🧪 Test Results

**Type:** [Type]
**Duration:** [time]

### Summary
| Metric | Result |
|--------|--------|
| Test Suites | [X] passed, [Y] failed |
| Tests | [X] passed, [Y] failed |
| Coverage | [X]% |

### Status
[✅ PASSED | ❌ FAILED]
```

---

## SUBCOMMAND: tdd

```bash
/f5-test tdd <subcommand> [options]
```

**Delegates entirely to `/f5-tdd`**

| Command | Delegates To |
|---------|--------------|
| `/f5-test tdd start <feature>` | `/f5-tdd start <feature>` |
| `/f5-test tdd red` | `/f5-tdd red` |
| `/f5-test tdd green` | `/f5-tdd green` |
| `/f5-test tdd refactor` | `/f5-tdd refactor` |
| `/f5-test tdd status` | `/f5-tdd status` |
| `/f5-test tdd complete` | `/f5-tdd complete` |

> **Full TDD documentation**: See `/f5-tdd` for session management, cycle tracking, metrics

---

## SUBCOMMAND: coverage

```bash
/f5-test coverage
```

### Output

```markdown
## 📊 Coverage Report

**Generated:** [DATE]

### Overall Coverage
| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Statements | ≥80% | [X]% | [✅|❌] |
| Branches | ≥75% | [X]% | [✅|❌] |
| Functions | ≥80% | [X]% | [✅|❌] |
| Lines | ≥80% | [X]% | [✅|❌] |

### Coverage by Module
| Module | Stmts | Branch | Funcs | Lines | Status |
|--------|-------|--------|-------|-------|--------|
| src/user/ | 92.0% | 85.0% | 95.0% | 91.5% | ✅ |
| src/auth/ | 78.5% | 72.0% | 85.0% | 78.0% | ⚠️ |

### Recommendations
1. Add tests for error handling in [file]
2. Improve branch coverage in [module]
```

---

## SUBCOMMAND: report

```bash
/f5-test report
```

Generate comprehensive report for G3 Gate.

### Output

```markdown
## 📋 Test Report for G3 Gate

**Project:** [PROJECT_NAME]
**Date:** [DATE]
**Version:** [VERSION]

### Executive Summary

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Unit Test Coverage | ≥80% | [X]% | [✅|❌] |
| Integration Tests | All Pass | [X]/[Y] | [✅|❌] |
| E2E Tests | All Pass | [X]/[Y] | [✅|❌] |
| Visual Tests | ≤5% diff | [X]% | [✅|❌] |

### G3 Gate Status: [✅ PASSED | ❌ FAILED]

### Test Artifacts
| Artifact | Location |
|----------|----------|
| Coverage Report | `coverage/lcov-report/index.html` |
| JUnit XML | `reports/junit.xml` |
| E2E Videos | `e2e/videos/` |
| Visual Diffs | `.f5/visual/diff/` |
```

---

## G3 GATE INTEGRATION

> **Full G3 sequence**: See `_test-shared.md` for complete gate integration

When running `/f5-gate check G3`:

```bash
# Automatic test sequence
/f5-test run --type unit --ci
/f5-test coverage
/f5-test run --type integration --ci
/f5-test run --type e2e --ci
/f5-test-e2e visual --ci --threshold 5
/f5-test report
```

---

## FLAGS

| Flag | Description |
|------|-------------|
| `--type <type>` | Test type: unit, integration, e2e, all |
| `--path <path>` | Specific file or folder |
| `--watch` | Watch mode |
| `--coverage` | Show coverage (default: true) |
| `--ci` | CI mode |
| `--verbose` | Verbose output |
| `--bail` | Stop on first failure |
| `--update-snapshots` | Update snapshots |

---

## EXAMPLES

```bash
# Generate tests for a service
/f5-test generate src/user/user.service.ts

# Run unit tests
/f5-test run --type unit

# Run with coverage
/f5-test run --coverage

# Run in watch mode
/f5-test run --watch

# Run specific path
/f5-test run --path src/user --type unit

# CI mode - all tests
/f5-test run --type all --ci

# TDD workflow (delegates to /f5-tdd)
/f5-test tdd start user-registration
/f5-test tdd red
/f5-test tdd green
/f5-test tdd refactor
/f5-test tdd complete

# Check coverage
/f5-test coverage

# Generate G3 report
/f5-test report
```

---

## QUICK REFERENCE

| Task | Command |
|------|---------|
| Run all tests | `/f5-test run --type all` |
| Unit tests only | `/f5-test run --type unit` or `/f5-test-unit` |
| Integration tests | `/f5-test run --type integration` or `/f5-test-it` |
| E2E tests | `/f5-test run --type e2e` or `/f5-test-e2e` |
| Visual tests | `/f5-test-e2e visual` |
| TDD workflow | `/f5-tdd start <feature>` |
| Coverage report | `/f5-test coverage` |
| G3 gate report | `/f5-test report` |

---

## SEE ALSO

### Sub-Commands (Direct Access)
- `/f5-test-unit` - Unit testing (isolated components)
- `/f5-test-it` - Integration testing (MCP tools, APIs, services)
- `/f5-test-e2e` - E2E and Visual testing (Playwright browser automation)
- `/f5-tdd` - TDD workflow (red-green-refactor cycle)

### Related Commands
- `/f5-implement` - Implementation với test generation
- `/f5-verify` - Verification commands (G2.5 gate)
- `/f5-fix` - Bug fix workflow
- `/f5-review` - Code review
- `/f5-gate` - Quality gate management (G3)

### Resources
- `_test-shared.md` - Stack detection, common patterns, G3 integration
- `stacks/*/skills/testing/` - Stack-specific testing skills
- `.f5/testing/config.yaml` - Testing configuration
