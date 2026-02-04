# F5 Framework - Testing Documentation

> **Version:** 1.3.0
> **Approach:** Claude Code Testing
> **MCP Tools:** Playwright, Sequential

---

## 📌 Quick Reference Card

| Task | Command | Notes |
|------|---------|-------|
| Unit test file | `/f5-test-unit src/file.ts` | Auto-fix with `--fix` |
| Unit test + TDD | `/f5-tdd start feature` | Red-Green-Refactor |
| Integration test API | `/f5-test-it api /endpoint` | Uses Sequential MCP |
| Integration test service | `/f5-test-it service name` | Auto-mock if unavailable |
| E2E journey test | `/f5-test-e2e journey name` | Uses Playwright MCP |
| E2E from design | `/f5-test-e2e from-design screen.yaml` | Design→E2E mapping |
| Full test suite | `/f5-test all` | For G3 gate |
| Coverage check | `/f5-test coverage --trend` | Track over time |
| Pre-commit check | `/f5-test hooks status` | Quick/Standard/Thorough |

### Related Documentation

| Document | Purpose |
|----------|---------|
| [PRE-COMMIT.md](./PRE-COMMIT.md) | Pre-commit hook setup |
| [INDEX.md](./INDEX.md) | Full testing documentation index |
| [.f5/testing/config.yaml](../../.f5/testing/config.yaml) | Testing configuration |

---

## 📋 Overview

F5 Framework sử dụng **Claude Code Testing** - một approach mới cho phép:

- **Test và Fix trong cùng session** - Không cần switch context
- **MCP Integration** - Playwright cho E2E, Sequential cho complex reasoning
- **Flexible Testing** - Context-aware, không cần maintain test code

---

## 🎯 Testing Philosophy

### Traditional vs Claude Code Testing

```
┌──────────────────────────────────────────────────────────────┐
│                    TRADITIONAL TESTING                        │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  Developer    →    Write Test Code    →    Run Tests         │
│      │                                        │               │
│      │                                        ▼               │
│      │                               ┌───────────────┐       │
│      │                               │  Test Failed  │       │
│      │                               └───────┬───────┘       │
│      │                                       │               │
│      ▼                                       ▼               │
│  Read Logs    ←────────────────────   Error Message         │
│      │                                                       │
│      ▼                                                       │
│  Debug Code   →    Fix    →    Run Again    →    ...        │
│                                                               │
│  Time: SLOW | Context: LOST | Maintenance: HIGH              │
│                                                               │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│                    CLAUDE CODE TESTING                        │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│              /f5-test-unit [target]                          │
│                       │                                       │
│                       ▼                                       │
│              ┌───────────────┐                               │
│              │  Claude Tests │                               │
│              │  & Analyzes   │                               │
│              └───────┬───────┘                               │
│                      │                                        │
│           ┌──────────┴──────────┐                            │
│           │                     │                            │
│           ▼                     ▼                            │
│      ✅ PASS              ❌ FAIL                            │
│                                 │                            │
│                                 ▼                            │
│                    ┌───────────────────┐                     │
│                    │ Claude Shows Bug  │                     │
│                    │ Claude Fixes Bug  │                     │
│                    │ Claude Re-Tests   │                     │
│                    └─────────┬─────────┘                     │
│                              │                               │
│                              ▼                               │
│                         ✅ PASS                              │
│                                                               │
│  Time: FAST | Context: KEPT | Maintenance: LOW               │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

---

## 🧪 Testing Commands

### Command Overview

| Command | Purpose | MCP Tools |
|---------|---------|-----------|
| `/f5-test` | Master orchestrator | - |
| `/f5-test-unit` | Unit testing | - |
| `/f5-test-it` | Integration testing | Sequential |
| `/f5-test-e2e` | End-to-end testing | Playwright |
| `/f5-tdd` | TDD workflow | - |
| `/f5-selftest` | Framework diagnostics | - |

### Quick Start

```bash
# Unit test a file
/f5-test-unit src/core/excel-processor.ts

# Integration test API
/f5-test-it api /users

# E2E test user journey
/f5-test-e2e journey user-registration

# Full test suite
/f5-test all

# TDD workflow
/f5-tdd start user-auth
```

---

## 📊 Test Pyramid

```
                    ╱╲
                   ╱  ╲          E2E Tests
                  ╱ E2E╲         /f5-test-e2e
                 ╱──────╲        Playwright MCP
                ╱        ╲       ~10% of tests
               ╱──────────╲
              ╱    IT      ╲     Integration Tests
             ╱──────────────╲    /f5-test-it
            ╱                ╲   Sequential MCP
           ╱                  ╲  ~20% of tests
          ╱────────────────────╲
         ╱        Unit          ╲  Unit Tests
        ╱──────────────────────────╲  /f5-test-unit
       ╱                            ╲ Claude Code analysis
      ╱                              ╲ ~70% of tests
     ╱────────────────────────────────╲
```

---

## 🤔 When to Use TDD vs Non-TDD

### Decision Guide

```
┌─────────────────────────────────────────────────────────────┐
│              WHEN TO USE TDD vs NON-TDD?                    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  USE TDD (/f5-tdd or --tdd) WHEN:                           │
│  ✅ Implementing NEW business logic                          │
│  ✅ Requirements are well-defined                            │
│  ✅ Writing domain services, validators, calculations        │
│  ✅ Creating APIs with complex validation                    │
│  ✅ Building features with clear acceptance criteria         │
│                                                              │
│  USE NON-TDD (/f5-implement --with-tests) WHEN:             │
│  ✅ Doing quick prototypes or spikes                         │
│  ✅ UI/Frontend components (visual-first)                    │
│  ✅ Configuration or infrastructure code                     │
│  ✅ Simple CRUD without complex logic                        │
│  ✅ Exploring unknown libraries/APIs                         │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Quick Reference

| Scenario | Approach | Command |
|----------|----------|---------|
| New user registration logic | TDD | `/f5-tdd start user-registration` |
| Payment validation rules | TDD | `/f5-implement payment --tdd` |
| Simple CRUD controller | Non-TDD | `/f5-implement users-crud --with-tests` |
| UI component | Non-TDD | `/f5-implement user-card --with-tests` |
| Complex business workflow | TDD | `/f5-tdd start order-workflow` |
| Configuration setup | Non-TDD | `/f5-implement config --scaffold` |

### TDD Benefits
- **Design First**: Tests define behavior before code
- **Higher Coverage**: Naturally achieves ≥80% coverage
- **Better Contracts**: Clear input/output specifications
- **Refactoring Safety**: Tests catch regressions

### Non-TDD Benefits
- **Faster Exploration**: Quick prototyping
- **Visual Feedback**: UI components need visual testing
- **Flexibility**: Adapt as requirements evolve

---

## 🔧 Unit Testing

### `/f5-test-unit`

Test individual functions, classes, modules.

```bash
# Test single file
/f5-test-unit src/core/excel-processor.ts

# Test directory
/f5-test-unit src/core/

# Test specific function
/f5-test-unit src/core/excel-processor.ts::parseFile

# Test with auto-fix
/f5-test-unit src/core/ --fix
```

### What Claude Does

1. **Reads source code**
2. **Identifies test cases** (happy path, edge, error)
3. **Analyzes code paths**
4. **Detects bugs**
5. **Suggests/applies fixes**
6. **Re-tests until pass**

### Example Output

```markdown
## 🧪 Unit Test: excel-processor.ts

### Tests Executed
| Function | Tests | Pass | Fail |
|----------|-------|------|------|
| parseFile | 7 | 6 | 1 |
| validateData | 4 | 4 | 0 |

### Bug Found
**Line 78:** Using `=` instead of `===`

### Fix Applied ✅
```typescript
// Before: if (data.length = 0)
// After:  if (data.length === 0)
```

### Result: ✅ ALL PASS (after fix)
```

---

## 🔗 Integration Testing

### `/f5-test-it`

Test component interactions, APIs, databases, services.

```bash
# Test API endpoints
/f5-test-it api /users

# Test database
/f5-test-it database users

# Test external service
/f5-test-it service jira-client

# Test MCP tools
/f5-test-it mcp

# Test full flow
/f5-test-it flow user-registration
```

### MCP Sequential Integration

Claude uses Sequential MCP for complex multi-step reasoning:

```yaml
integration_test:
  steps:
    - analyze: "API spec"
    - generate: "Test cases"
    - execute: "API calls"
    - verify: "Responses"
    - report: "Results"
```

### Example Output

```markdown
## 🔗 Integration Test: /users API

### Endpoint Tests
| Method | Path | Expected | Actual | Result |
|--------|------|----------|--------|--------|
| GET | /users | 200 | 200 | ✅ |
| POST | /users | 201 | 201 | ✅ |
| GET | /users/999 | 404 | 500 | ❌ |

### Bug Found
Missing 404 handler for non-existent user

### Fix Applied ✅
Added NotFoundException in controller

### Result: ✅ ALL PASS (after fix)
```

---

## 🎬 E2E Testing

### `/f5-test-e2e`

Full user journey testing with real browser.

```bash
# User journey
/f5-test-e2e journey user-registration

# Critical business path
/f5-test-e2e critical checkout

# Single page
/f5-test-e2e page login

# Smoke test
/f5-test-e2e smoke

# With screenshots
/f5-test-e2e journey login --screenshot

# With video
/f5-test-e2e critical checkout --video
```

### MCP Playwright Integration

Claude controls real browser:

```yaml
playwright_actions:
  - navigate: "http://localhost:3000"
  - click: "#signup-button"
  - fill:
      email: "test@example.com"
      password: "SecureP@ss123"
  - click: "[type='submit']"
  - screenshot: "after-submit"
  - assert: "url contains /dashboard"
```

### Example Output

```markdown
## 🎬 E2E Journey: user-registration

### Steps
| # | Action | Duration | Result |
|---|--------|----------|--------|
| 1 | Navigate to home | 1.2s | ✅ |
| 2 | Click Sign Up | 0.5s | ✅ |
| 3 | Fill form | 2.1s | ✅ |
| 4 | Submit | 1.8s | ❌ |

### Bug Found
Password validation regex missing `@`

### Fix Applied ✅
Updated regex pattern

### Re-running...
| 4 | Submit | 1.5s | ✅ |
| 5 | Confirmation page | 1.0s | ✅ |

### Result: ✅ JOURNEY COMPLETE
### Screenshots: 5 captured
```

---

## 🔄 TDD Workflow

### `/f5-tdd`

Test-Driven Development với Claude Code.

```bash
# Start TDD session
/f5-tdd start user-auth

# RED phase - write failing test
/f5-tdd red

# GREEN phase - make test pass
/f5-tdd green

# REFACTOR phase - improve code
/f5-tdd refactor

# Complete session
/f5-tdd complete
```

### TDD Cycle

```
    🔴 RED           Write failing test
         │
         ▼
    🟢 GREEN         Write minimal code to pass
         │
         ▼
    🔵 REFACTOR      Improve code quality
         │
         ▼
    🔄 REPEAT        Next requirement
```

---

## 📁 Project Structure

```
.claude/commands/
├── f5-test.md           # Master orchestrator
├── f5-test-unit.md      # Unit testing
├── f5-test-it.md        # Integration testing
├── f5-test-e2e.md       # E2E testing
├── f5-tdd.md            # TDD workflow
└── f5-selftest.md       # Diagnostics

.f5/testing/
├── config.yaml          # Testing configuration
├── workflows/           # Test workflow definitions
├── fixtures/            # Test data
└── reports/             # Generated reports

packages/cli/test/
├── _archive/            # Archived vitest tests
│   ├── doc.test.ts
│   └── jira-csv-exporter.test.ts
└── fixtures/            # Shared test fixtures
    ├── requirements-v1.xlsx
    ├── requirements-v2.xlsx
    └── requirements-v3.xlsx
```

---

## ⚙️ Configuration

### .f5/testing/config.yaml

```yaml
testing:
  # Unit testing
  unit:
    coverage_target: 80
    auto_fix: true
    
  # Integration testing
  integration:
    api:
      base_url: "http://localhost:3000"
      auth_type: "bearer"
    database:
      type: "postgresql"
      test_db: "f5_test"
    mcp:
      required: ["sequential"]
      optional: ["playwright"]
      
  # E2E testing
  e2e:
    browser: "chromium"
    headless: true
    viewport: { width: 1280, height: 720 }
    screenshots: true
    video_on_failure: true
    
  # Reporting
  reports:
    output_dir: ".f5/testing/reports"
    formats: ["markdown", "json"]
```

---

## 🚦 G3 Gate Integration

Testing is required for G3 (Testing Complete) gate:

```bash
# Run all tests for G3
/f5-gate check G3

# This runs:
# 1. /f5-test-unit src/ --coverage
# 2. /f5-test-it --all
# 3. /f5-test-e2e smoke
# 4. Generate G3 report
```

### G3 Requirements

| Metric | Target |
|--------|--------|
| Unit Test Coverage | ≥80% |
| Integration Tests | All pass |
| E2E Critical Paths | All pass |
| Bug Count | 0 |

---

## 🆚 Comparison: Old vs New

| Aspect | Vitest (Old) | Claude Code (New) |
|--------|--------------|-------------------|
| Test Code | Write & maintain | Not needed |
| Bug Detection | Run → Read logs | Instant in session |
| Bug Fixing | Manual, separate | Auto, same session |
| Context | Lost between runs | Preserved |
| Mocking | Complex setup | Flexible |
| E2E | Separate tool | MCP Playwright |
| Learning Curve | High | Low |
| Maintenance | High | Low |

---

## 📚 Further Reading

- `/f5-test` - Full command reference
- `/f5-test-unit` - Unit testing details
- `/f5-test-it` - Integration testing details
- `/f5-test-e2e` - E2E testing details
- `/f5-tdd` - TDD workflow guide
- `/f5-gate` - Quality gates

---

## 📈 Coverage Trend Tracking

Track test coverage over time to ensure quality improvements.

```bash
# View coverage trend
/f5-test coverage --trend

# View historical data
/f5-test coverage --history

# Compare with commit
/f5-test coverage --compare HEAD~5
```

### Configuration (.f5/testing/config.yaml)

```yaml
coverage_trend:
  enabled: true
  history_file: ".f5/testing/reports/coverage-history.json"
  analysis:
    window: 10  # Last 10 data points
    alert_on_regression: true
    regression_threshold: 5  # Alert if drops > 5%
```

---

## 📦 Test Evidence Archiving

Archive test evidence for quality gates (G3, G4).

```bash
# Archive evidence for G3
/f5-gate evidence archive G3

# List all archives
/f5-gate evidence list

# Restore specific archive
/f5-gate evidence restore [archive-id]
```

### Archived Data

| Type | Contents |
|------|----------|
| Test Results | Pass/fail status, timing |
| Coverage Reports | Statement, branch, function coverage |
| Screenshots | E2E test screenshots |
| Logs | Test execution logs |

---

## 🪝 Pre-commit Hooks

Enforce testing standards before commits.

```bash
# Enable hooks
/f5-test hooks enable

# Set level (quick/standard/thorough)
/f5-test hooks level standard

# Check status
/f5-test hooks status
```

See [PRE-COMMIT.md](./PRE-COMMIT.md) for detailed setup.

---

## 🤝 Support

- **Tutorial:** `/f5-tutorial testing`
- **Self-test:** `/f5-selftest`
- **Documentation:** This file
- **Contact:** Fujigo Software Team

---

## 📝 Changelog

### v1.3.0 (2024-12)
- ✅ Added IT Auto-Generation in `/f5-implement`
- ✅ Added TDD vs Non-TDD Guidance
- ✅ Added IT Type Selection Guide
- ✅ Added Design→E2E mapping
- ✅ Added Pre-commit Hooks documentation
- ✅ Added Coverage Trend Tracking
- ✅ Added Test Evidence Archiving
- ✅ Updated SEE ALSO sections across all commands

### v1.2.0 (2024-11)
- Added `/f5-tdd` command
- Added MCP Sequential integration for IT
- Added MCP Playwright integration for E2E

### v1.1.0 (2024-10)
- Initial Claude Code Testing approach
- Added `/f5-test-unit`, `/f5-test-it`, `/f5-test-e2e`

---

*F5 Framework Testing Documentation v1.3.0*
