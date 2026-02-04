---
name: f5-tdd
description: TDD workflow management
argument-hint: <start|red|green|refactor|complete>
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: true
---

# /f5-tdd - Test-Driven Development

> **Version**: 1.4.0
> **Category**: Testing
> **Purpose**: TDD workflow with red-green-refactor cycle

## ARGUMENTS
$ARGUMENTS

---

## TDD CYCLE OVERVIEW

```
═══════════════════════════════════════════════════════════════════
  🔴 RED           🟢 GREEN          🔵 REFACTOR
  Write failing    Make tests        Improve code
  tests            pass              quality
═══════════════════════════════════════════════════════════════════
```

---

## SUBCOMMANDS

| Command | Description |
|---------|-------------|
| `start <feature>` | Start new TDD session |
| `red [description]` | RED phase - write failing tests |
| `green` | GREEN phase - make tests pass |
| `refactor` | REFACTOR phase - improve code |
| `status` | Show session status |
| `cycle` | View current cycle |
| `complete` | Complete session |
| `abort` | Cancel session |
| `history` | View past sessions |
| `metrics` | Show TDD metrics |

---

## START SESSION

```bash
/f5-tdd start user-registration
```

### Output

```markdown
## 🧪 TDD Session Started

| Field | Value |
|-------|-------|
| Session ID | tdd_{{TIMESTAMP}}_{{FEATURE}} |
| Feature | {{FEATURE}} |
| Phase | 🔴 RED (pending) |

### Next Step
```bash
/f5-tdd red "should {{EXPECTED_BEHAVIOR}}"
```
```

---

## RED PHASE

```bash
/f5-tdd red "should create user with valid data"
/f5-tdd red --generate        # Auto-generate tests
/f5-tdd red --for REQ-001     # For specific requirement
```

### Flags
| Flag | Description |
|------|-------------|
| `--generate` | Auto-generate test cases |
| `--for <req>` | Target specific requirement |
| `--edge-cases` | Include edge case tests |
| `--security` | Include security tests |

### Output

```markdown
## 🔴 RED PHASE: Writing Failing Tests

### Generated Test Cases
- ✅ Happy path test
- ✅ Error handling test
- ✅ Edge case test

### Test Execution (Must Fail)
FAIL: 3 tests failing as expected

### ✅ RED Phase Complete
Ready for GREEN phase: `/f5-tdd green`
```

---

## GREEN PHASE

```bash
/f5-tdd green
```

### Rules
- Write ONLY enough code to pass tests
- No premature optimization
- No extra features
- Hardcoding is acceptable temporarily

### Output

```markdown
## 🟢 GREEN PHASE: Making Tests Pass

### Implementation Strategy
Minimal code to pass tests

### Test Results
PASS: 3 tests passing

### ✅ GREEN Phase Complete
Ready for REFACTOR: `/f5-tdd refactor`
```

---

## REFACTOR PHASE

```bash
/f5-tdd refactor
```

### Golden Rule
Tests must ALWAYS pass during refactoring.
If tests fail → revert and try different approach.

### Checklist
| Check | Description |
|-------|-------------|
| 🔍 Code Smells | Long methods, duplicate code |
| 🏗️ Patterns | Apply design patterns |
| 📛 Naming | Clear, descriptive names |
| 📦 SRP | Single responsibility |

### Output

```markdown
## 🔵 REFACTOR PHASE: Improving Code

### Improvements Made
| Before | After | Benefit |
|--------|-------|---------|
| Long method | Extracted | Readability |
| Magic numbers | Constants | Maintainability |

### Tests Still Green: ✅

### TDD Cycle Complete! 🎉
```

---

## STATUS

```bash
/f5-tdd status
```

```markdown
## 📊 TDD Session Status

| Field | Value |
|-------|-------|
| Session | tdd_12345_user-reg |
| Phase | 🟢 GREEN |
| Cycles | 2 complete |
| Tests | 8 written |
| Coverage | 85% |
```

---

## COMPLETE SESSION

```bash
/f5-tdd complete
```

```markdown
## ✅ TDD Session Complete

### Summary
| Metric | Value |
|--------|-------|
| Tests Written | 12 |
| Tests Passing | 12 (100%) |
| Coverage | 87% |
| Cycles | 3 |

### Next Steps
1. Run full test suite: `npm run test`
2. Check gate G3: `/f5-gate check G3`
```

---

## HISTORY & METRICS

```bash
/f5-tdd history    # View past sessions
/f5-tdd metrics    # Show metrics dashboard
```

```markdown
## 📜 TDD History

| Session | Feature | Tests | Status |
|---------|---------|-------|--------|
| tdd_001 | user-auth | 15 | ✅ Complete |
| tdd_002 | user-profile | 8 | ✅ Complete |

## 📈 TDD Metrics
- Sessions: 10 total
- Avg tests/session: 12
- Avg coverage: 85%
```

---

## ABORT SESSION

```bash
/f5-tdd abort
```

Cancels current session. Progress archived to `.f5/tdd/sessions/`.

---

## BEST PRACTICES

### RED Phase
- Write tests for behavior, not implementation
- Tests MUST fail initially
- Start with happy path, then errors

### GREEN Phase
- Minimal code only
- Don't optimize yet
- Run tests after each change

### REFACTOR Phase
- Small, incremental changes
- Tests must stay green
- Apply one pattern at a time

### General
- One cycle = one behavior
- Keep cycles short (< 30 min)
- Commit after each cycle

---

## EXAMPLES

```bash
# Start TDD session
/f5-tdd start user-registration

# RED phase
/f5-tdd red "should create user with valid data"
/f5-tdd red --generate
/f5-tdd red --for REQ-001 --edge-cases

# GREEN phase
/f5-tdd green

# REFACTOR phase
/f5-tdd refactor

# Status & completion
/f5-tdd status
/f5-tdd complete

# History & metrics
/f5-tdd history
/f5-tdd metrics
```

---

## INTEGRATION

| Command | Integration |
|---------|-------------|
| `/f5-implement --tdd` | TDD-driven implementation |
| `/f5-test tdd start` | Via master test command |
| `/f5-gate check G3` | After TDD completion |

---

## SEE ALSO

- `/f5-test` - Master test command
- `/f5-test-unit` - Unit testing
- `/f5-test-it` - Integration testing
- `/f5-test-e2e` - E2E testing
- `/f5-gate` - Quality gates (G3)
- `_test-shared.md` - Stack detection, coverage targets
