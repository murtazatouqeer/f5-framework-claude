# F5 TDD Session Management

## Overview

This directory manages TDD (Test-Driven Development) sessions for the F5 Framework. It provides session tracking, test templates, coverage management, and reporting capabilities.

---

## Directory Structure

```
.f5/tdd/
├── README.md                    # This documentation
├── config.yaml                  # TDD configuration
├── metrics.md                   # Metrics guide
├── sessions/                    # Session data
│   └── {session_id}/
│       ├── session.json         # Session state
│       ├── cycles/              # Cycle data
│       │   ├── cycle-1.json
│       │   └── cycle-2.json
│       ├── coverage/            # Coverage snapshots
│       │   └── final-coverage.json
│       └── report.md            # Session report
└── templates/                   # Test templates by stack
    ├── nestjs/
    │   ├── service.spec.ts.template
    │   ├── controller.spec.ts.template
    │   └── repository.spec.ts.template
    ├── spring/
    │   ├── ServiceTest.java.template
    │   └── ControllerTest.java.template
    ├── fastapi/
    │   ├── test_service.py.template
    │   └── test_router.py.template
    ├── react/
    │   ├── component.test.tsx.template
    │   └── hook.test.ts.template
    ├── go/
    │   └── service_test.go.template
    └── session-report.md        # Report template
```

---

## Session Lifecycle

```
START → RED → GREEN → REFACTOR → [repeat] → COMPLETE
                ↑___________|
```

### 1. Start Session

```bash
/f5-tdd start <feature>
```

Creates session directory and initializes tracking:
- Generates unique session ID
- Creates session.json with initial state
- Loads appropriate test templates based on stack
- Records start timestamp

### 2. TDD Cycles

Each cycle consists of three phases:

#### 🔴 RED Phase
- Write failing tests that define expected behavior
- Tests MUST fail initially (validates test correctness)
- Focus on: What should the code do?
- Command: `/f5-tdd red [description]`

#### 🟢 GREEN Phase
- Write minimal code to make tests pass
- No optimization, no extra features
- Focus on: Make it work
- Command: `/f5-tdd green`

#### 🔵 REFACTOR Phase
- Improve code while keeping tests green
- Apply patterns, clean up, optimize
- Focus on: Make it right
- Command: `/f5-tdd refactor`

### 3. Complete Session

```bash
/f5-tdd complete
```

- Generates comprehensive report
- Archives session data
- Updates metrics

---

## Session Data Format

### session.json

```json
{
  "id": "tdd_20240115_user_registration",
  "feature": "user-registration",
  "requirement": "REQ-001",
  "startedAt": "2024-01-15T09:30:00Z",
  "completedAt": null,
  "status": "in_progress",
  "currentPhase": "green",
  "currentCycle": 1,
  "cycles": [],
  "metrics": {
    "testsWritten": 17,
    "testsPassing": 14,
    "coverage": {
      "statements": 85,
      "branches": 78,
      "functions": 90,
      "lines": 84
    }
  },
  "files": {
    "tests": ["user.service.spec.ts"],
    "implementations": ["user.service.ts"]
  }
}
```

### cycle.json

```json
{
  "cycleNumber": 1,
  "startedAt": "2024-01-15T09:30:00Z",
  "completedAt": "2024-01-15T11:15:00Z",
  "redPhase": {
    "startedAt": "2024-01-15T09:30:00Z",
    "completedAt": "2024-01-15T10:00:00Z",
    "duration": "30m",
    "testsWritten": 17,
    "testsFailing": 17,
    "testFiles": ["user.service.spec.ts"],
    "categories": {
      "happyPath": 3,
      "validation": 5,
      "errorHandling": 4,
      "edgeCases": 3,
      "security": 2
    }
  },
  "greenPhase": {
    "startedAt": "2024-01-15T10:00:00Z",
    "completedAt": "2024-01-15T10:45:00Z",
    "duration": "45m",
    "testsPassing": 17,
    "implementationFiles": ["user.service.ts"],
    "linesAdded": 120
  },
  "refactorPhase": {
    "startedAt": "2024-01-15T10:45:00Z",
    "completedAt": "2024-01-15T11:15:00Z",
    "duration": "30m",
    "refactorings": [
      "Extracted validation logic",
      "Applied repository pattern",
      "Improved error handling"
    ],
    "testsStillPassing": true,
    "complexityBefore": 12,
    "complexityAfter": 4
  }
}
```

---

## Commands Reference

| Command | Description |
|---------|-------------|
| `/f5-tdd start <feature>` | Start new TDD session |
| `/f5-tdd red [description]` | Enter RED phase - write failing tests |
| `/f5-tdd red --generate` | Auto-generate tests from feature |
| `/f5-tdd green` | Enter GREEN phase - make tests pass |
| `/f5-tdd refactor` | Enter REFACTOR phase - improve code |
| `/f5-tdd status` | Show session status |
| `/f5-tdd cycle` | View current cycle visualization |
| `/f5-tdd complete` | Complete session and generate report |
| `/f5-tdd abort` | Cancel current session |
| `/f5-tdd history` | View past sessions |
| `/f5-tdd metrics` | Show TDD metrics dashboard |

---

## Best Practices

### RED Phase

- **Write tests for behavior, not implementation**
  - Focus on what the code should do, not how
  - Test observable outcomes

- **Start with happy path, then errors, then edge cases**
  - Prioritize core functionality first
  - Add validation and error tests second
  - Cover edge cases for robustness

- **Tests should be specific and descriptive**
  - Use clear test names that describe the scenario
  - Follow "should [behavior] when [condition]" naming

- **Run tests - they MUST fail**
  - If tests pass, something is wrong
  - Validates the test is actually testing something

### GREEN Phase

- **Write minimal code to pass**
  - Don't write more than necessary
  - Resist the urge to add features

- **It's okay to hardcode initially**
  - Get tests green first
  - Generalize during refactor

- **Don't optimize yet**
  - Focus on correctness
  - Performance comes later

- **Run tests after each change**
  - Verify progress continuously
  - Catch regressions immediately

### REFACTOR Phase

- **Run tests frequently**
  - After every change
  - Tests are your safety net

- **Small, incremental changes**
  - One refactoring at a time
  - Easier to debug if tests fail

- **If tests fail, revert immediately**
  - Don't try to fix during refactor
  - Go back to green, try different approach

- **Apply one pattern at a time**
  - Extract methods
  - Rename variables
  - Apply design patterns

### General Guidelines

- **One cycle = one behavior/feature**
  - Keep scope manageable
  - Easier to track progress

- **Keep cycles short (< 30 minutes ideal)**
  - Faster feedback loops
  - Maintains momentum

- **Commit after each successful cycle**
  - Save your progress
  - Easy to rollback if needed

- **Use descriptive test names**
  - Self-documenting tests
  - Easier to understand failures

---

## Coverage Targets

| Metric | Target | Warning | Critical |
|--------|--------|---------|----------|
| Statements | ≥80% | <75% | <60% |
| Branches | ≥75% | <70% | <55% |
| Functions | ≥80% | <75% | <60% |
| Lines | ≥80% | <75% | <60% |

---

## Integration

### With Other F5 Commands

```bash
# TDD-driven implementation
/f5-implement user-registration --tdd

# Verify phases during TDD
/f5-test verify-red
/f5-test verify-green
/f5-test verify-refactor

# Check testing gate after TDD
/f5-gate check G3

# TDD for specific requirement
/f5-tdd start REQ-001 --for-requirement
```

### With SIP (Strict Implementation Protocol)

When SIP is active, TDD sessions are automatically linked to requirements and tracked for compliance.

---

## Configuration

See `config.yaml` for detailed configuration options including:

- Coverage targets and thresholds
- Phase-specific settings
- Test generation preferences
- Stack-specific configurations
- Reporting options

---

## Troubleshooting

### Tests Not Failing in RED Phase

```bash
# Check test file exists
ls -la src/**/*.spec.ts

# Run specific test file
npm run test -- --testPathPattern="user.service.spec"

# Check if test is actually running
npm run test -- --verbose
```

### Tests Not Passing in GREEN Phase

```bash
# Run tests with coverage
npm run test:cov

# Check specific failing tests
npm run test -- --verbose --runInBand

# Debug test
npm run test -- --detectOpenHandles
```

### Coverage Not Meeting Target

```bash
# Check uncovered lines
npm run test:cov -- --coverageReporters=text-summary

# View HTML report
open coverage/lcov-report/index.html

# Focus on critical paths first
npm run test:cov -- --collectCoverageFrom='src/**/*.ts'
```

---

## See Also

- `/f5-tdd` - TDD command documentation
- `/f5-test` - Testing command
- `/f5-gate` - Quality gates (especially G3)
- `/f5-implement` - Implementation with TDD support
- `.f5/tdd/config.yaml` - Configuration options
- `.f5/tdd/metrics.md` - Metrics guide
