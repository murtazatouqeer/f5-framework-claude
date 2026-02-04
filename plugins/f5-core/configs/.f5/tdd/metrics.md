# F5 TDD Metrics Guide

## Overview

This document describes the metrics collected during TDD sessions and how to interpret them for continuous improvement.

---

## Metric Categories

### 1. Session Metrics

| Metric | Description | Target | Warning | Critical |
|--------|-------------|--------|---------|----------|
| Total Duration | Time from start to complete | < 4 hours | > 4 hours | > 8 hours |
| Cycles Completed | Number of RED→GREEN→REFACTOR cycles | ≥ 3 | < 3 | < 1 |
| Tests Written | Total test cases created | Varies | < 10 | < 5 |
| Tests Passing | Tests passing at completion | 100% | < 95% | < 80% |

### 2. Phase Metrics

#### RED Phase

| Metric | Description | Target | Calculation |
|--------|-------------|--------|-------------|
| Duration | Time spent writing failing tests | 20-30% of cycle | `red_end - red_start` |
| Tests Written | Number of tests created | Varies by feature | Count of test functions |
| Test Categories | Distribution across categories | Balanced | % per category |
| Failure Rate | Tests that properly fail | 100% | `failing / total` |

#### GREEN Phase

| Metric | Description | Target | Calculation |
|--------|-------------|--------|-------------|
| Duration | Time to make tests pass | 40-50% of cycle | `green_end - green_start` |
| Lines Added | Implementation code written | Minimal necessary | LOC diff |
| Pass Rate | Tests passing at phase end | 100% | `passing / total` |
| Iterations | Attempts to pass all tests | < 5 | Count of test runs |

#### REFACTOR Phase

| Metric | Description | Target | Calculation |
|--------|-------------|--------|-------------|
| Duration | Time spent refactoring | 20-30% of cycle | `refactor_end - refactor_start` |
| Refactorings | Number of improvements made | ≥ 1 | Count of changes |
| Complexity Reduction | Cyclomatic complexity change | Decrease | `before - after` |
| Tests Still Passing | Validation of refactoring | 100% | `passing / total` |

### 3. Coverage Metrics

| Metric | Target | Warning | Critical |
|--------|--------|---------|----------|
| Statement Coverage | ≥ 80% | < 75% | < 60% |
| Branch Coverage | ≥ 75% | < 70% | < 55% |
| Function Coverage | ≥ 80% | < 75% | < 60% |
| Line Coverage | ≥ 80% | < 75% | < 60% |

### 4. Quality Metrics

| Metric | Description | Target |
|--------|-------------|--------|
| Test/Code Ratio | Lines of test vs implementation | 1.5:1 |
| Assertion Density | Assertions per test | ≥ 2 |
| Mock Complexity | Dependencies mocked per test | ≤ 3 |
| Test Independence | Tests that can run in isolation | 100% |

---

## Efficiency Indicators

### Cycle Velocity

```
Cycle Velocity = Cycles Completed / Session Duration (hours)
```

| Rating | Velocity | Interpretation |
|--------|----------|----------------|
| Excellent | ≥ 4 cycles/hour | High efficiency, well-scoped features |
| Good | 3 cycles/hour | Normal pace |
| Acceptable | 2 cycles/hour | Moderate complexity |
| Needs Improvement | < 2 cycles/hour | Complex features or process issues |

### Phase Balance

Ideal distribution:
```
RED:     25-35%  (writing tests)
GREEN:   40-50%  (implementation)
REFACTOR: 20-30% (improvement)
```

Imbalanced indicators:
- **Too much RED**: Tests may be over-specified or unclear requirements
- **Too much GREEN**: Implementation complexity, consider smaller increments
- **Too little REFACTOR**: Technical debt accumulation risk

### First-Time Pass Rate

```
First-Time Pass Rate = Tests passing on first GREEN attempt / Total tests
```

| Rating | Rate | Interpretation |
|--------|------|----------------|
| Excellent | ≥ 90% | Clear understanding of requirements |
| Good | 70-89% | Normal development |
| Needs Improvement | < 70% | Consider smaller increments |

---

## Test Category Distribution

### Recommended Distribution

```
┌─────────────────────────────────────────────────────────┐
│ Happy Path      ████████████████████  20-30%           │
│ Validation      ████████████████████████████  25-35%   │
│ Error Handling  ████████████████████  20-25%           │
│ Edge Cases      ████████████████  15-20%               │
│ Security        ████████  5-10%                        │
│ Performance     ████  2-5% (optional)                  │
└─────────────────────────────────────────────────────────┘
```

### Category Definitions

| Category | Purpose | Examples |
|----------|---------|----------|
| **Happy Path** | Core functionality works correctly | Valid input produces expected output |
| **Validation** | Input validation and constraints | Required fields, formats, ranges |
| **Error Handling** | Graceful failure scenarios | Database errors, network failures |
| **Edge Cases** | Boundary conditions | Empty input, max length, special chars |
| **Security** | Protection against attacks | XSS, injection, auth bypass |
| **Performance** | Speed and resource usage | Response time, memory limits |

---

## Tracking Over Time

### Session History Schema

```json
{
  "sessions": [
    {
      "id": "tdd_20240115_feature_x",
      "date": "2024-01-15",
      "feature": "feature-x",
      "requirement": "REQ-001",
      "duration_minutes": 120,
      "cycles": 4,
      "tests_written": 17,
      "coverage": {
        "statements": 85,
        "branches": 78,
        "functions": 90,
        "lines": 84
      },
      "phase_balance": {
        "red_percent": 30,
        "green_percent": 45,
        "refactor_percent": 25
      },
      "velocity": 2.0,
      "efficiency_score": 0.85
    }
  ]
}
```

### Trend Analysis

Track these metrics over time:

1. **Velocity Trend**: Are cycles getting faster?
2. **Coverage Trend**: Is coverage improving?
3. **Balance Trend**: Is phase distribution stabilizing?
4. **Quality Trend**: Is test/code ratio improving?

---

## Dashboard Visualization

### Session Summary

```
╔═══════════════════════════════════════════════════════════════╗
║                    TDD SESSION METRICS                         ║
╠═══════════════════════════════════════════════════════════════╣
║ Session: tdd_20240115_user_auth                               ║
║ Duration: 2h 15m | Cycles: 4 | Tests: 17                      ║
╠═══════════════════════════════════════════════════════════════╣
║ COVERAGE                                                       ║
║ ┌─────────────────────────────────────────────────────────┐   ║
║ │ Statements  ████████████████████░░░░  85% ✓            │   ║
║ │ Branches    ███████████████████░░░░░  78% ✓            │   ║
║ │ Functions   ██████████████████████░░  90% ✓            │   ║
║ │ Lines       ████████████████████░░░░  84% ✓            │   ║
║ └─────────────────────────────────────────────────────────┘   ║
╠═══════════════════════════════════════════════════════════════╣
║ PHASE DISTRIBUTION                                             ║
║ ┌─────────────────────────────────────────────────────────┐   ║
║ │ RED        ██████████░░░░░░░░░░░░░░░  30%              │   ║
║ │ GREEN      █████████████████░░░░░░░░  45%              │   ║
║ │ REFACTOR   ████████░░░░░░░░░░░░░░░░░  25%              │   ║
║ └─────────────────────────────────────────────────────────┘   ║
╠═══════════════════════════════════════════════════════════════╣
║ EFFICIENCY                                                     ║
║ Velocity: 1.8 cycles/hour                                      ║
║ First-Time Pass: 82%                                           ║
║ Test/Code Ratio: 1.4:1                                         ║
║ Efficiency Score: 0.85 ████████████████░░░░                    ║
╚═══════════════════════════════════════════════════════════════╝
```

### Historical Trend

```
Velocity Trend (Last 10 Sessions)
│
│    ╭─╮
│   ╭╯ ╰╮  ╭─╮
│  ╭╯   ╰──╯ ╰╮
│ ╭╯          ╰╮
│╭╯            ╰─
├────────────────────
Session: 1  2  3  4  5  6  7  8  9  10

Coverage Trend
│     ─────────────────
│    ╱
│   ╱
│  ╱
│ ╱
├────────────────────
Session: 1  2  3  4  5  6  7  8  9  10
```

---

## Efficiency Score Calculation

The overall efficiency score combines multiple factors:

```
Efficiency Score = (
  0.25 × Coverage Score +
  0.25 × Phase Balance Score +
  0.20 × Velocity Score +
  0.15 × Test Quality Score +
  0.15 × First-Time Pass Score
)
```

### Component Scores

**Coverage Score**:
```
coverage_score = min(1.0, avg_coverage / target_coverage)
```

**Phase Balance Score**:
```
ideal = {red: 0.30, green: 0.45, refactor: 0.25}
deviation = sum(abs(actual[phase] - ideal[phase]) for phase)
balance_score = max(0, 1 - deviation)
```

**Velocity Score**:
```
velocity_score = min(1.0, actual_velocity / target_velocity)
target_velocity = 3 cycles/hour
```

**Test Quality Score**:
```
quality_factors = [
  test_code_ratio >= 1.5,
  assertion_density >= 2,
  mock_complexity <= 3,
  test_independence == 100%
]
quality_score = sum(quality_factors) / len(quality_factors)
```

**First-Time Pass Score**:
```
first_pass_score = first_time_pass_rate
```

---

## Recommendations Based on Metrics

### Low Coverage (< 75%)

- Add more edge case tests
- Review uncovered branches
- Consider property-based testing
- Focus on error paths

### Slow Velocity (< 2 cycles/hour)

- Break features into smaller increments
- Write more focused tests
- Reduce mock complexity
- Improve test setup efficiency

### Imbalanced Phases

**Too much RED**:
- Clarify requirements before testing
- Write tests in smaller batches
- Focus on behavior, not implementation

**Too much GREEN**:
- Simplify implementation approach
- Consider design patterns
- Break into smaller functions

**Too little REFACTOR**:
- Schedule dedicated refactor time
- Track technical debt
- Set complexity thresholds

### Low First-Time Pass

- Write simpler tests first
- Verify test fails for right reason
- Improve requirement understanding
- Consider test doubles

---

## Integration with Quality Gates

TDD metrics contribute to Gate G3 (Testing Complete):

| Gate Requirement | TDD Metric |
|------------------|------------|
| Unit test coverage ≥ 80% | Coverage metrics |
| All tests passing | Tests passing rate |
| Test documentation | Generated reports |
| Traceability | Requirement linking |

---

## Commands

```bash
# View current session metrics
/f5-tdd metrics

# View historical metrics
/f5-tdd metrics --history

# Export metrics
/f5-tdd metrics --export json

# Compare sessions
/f5-tdd metrics --compare session1 session2
```

---

## See Also

- `/f5-tdd` - TDD command reference
- `.f5/tdd/config.yaml` - Configuration options
- `.f5/tdd/README.md` - Session management guide
- `.f5/quality/gates-status.yaml` - Quality gates
