# F5 Framework - Testing Documentation Index

> **Version:** 1.3.6
> **Last Updated:** 2025-01

---

## Documentation Files

| File | Description | Status |
|------|-------------|--------|
| [README.md](./README.md) | Main testing documentation | Current |
| [PRE-COMMIT.md](./PRE-COMMIT.md) | Pre-commit hooks guide | v1.0.0 |

---

## Command Reference

### Master Command

| Command | Description | Doc |
|---------|-------------|-----|
| `/f5-test` | Master test orchestrator | [f5-test.md](../../.claude/commands/f5-test.md) |

### Phase 1 Testing Commands (v1.2.8)

| Command | Description | MCP Tools | Shared Utils | Doc |
|---------|-------------|-----------|--------------|-----|
| `/f5-test-unit` | Unit testing | - | ✅ | [f5-test-unit.md](../../.claude/commands/f5-test-unit.md) |
| `/f5-test-it` | Integration testing | Sequential | ✅ | [f5-test-it.md](../../.claude/commands/f5-test-it.md) |
| `/f5-test-e2e` | E2E testing | Playwright | ✅ | [f5-test-e2e.md](../../.claude/commands/f5-test-e2e.md) |
| `/f5-test-visual` | Visual regression | Playwright | ✅ | [f5-test-visual.md](../../.claude/commands/f5-test-visual.md) |
| `/f5-tdd` | TDD workflow | - | ✅ | [f5-tdd.md](../../.claude/commands/f5-tdd.md) |

### Shared Testing Utilities

All Phase 1 testing commands use shared utilities from `_test-shared.md`:

| Utility | Description |
|---------|-------------|
| Coverage tracking | Consistent coverage reporting across test types |
| Evidence archiving | G3 gate evidence collection and archiving |
| Mock generators | Reusable test mock patterns |
| Fixture management | Shared test fixtures and data |

### Related Commands

| Command | Description | Doc |
|---------|-------------|-----|
| `/f5-implement` | Implementation with test generation | [f5-implement.md](../../.claude/commands/f5-implement.md) |
| `/f5-gate` | Quality gates (G3 testing) | [f5-gate.md](../../.claude/commands/f5-gate.md) |
| `/f5-selftest` | Framework diagnostics | [f5-selftest.md](../../.claude/commands/f5-selftest.md) |

---

## Configuration Files

| File | Description |
|------|-------------|
| [.f5/testing/config.yaml](../../.f5/testing/config.yaml) | Main testing configuration |

### Key Config Sections

```yaml
# Quick reference to config sections
testing:
  approach: "claude-code"     # Testing approach
  unit:                       # Unit testing settings
  integration:                # IT settings (API, DB, services)
  e2e:                        # E2E settings (Playwright)
  tdd:                        # TDD workflow settings

coverage_trend:               # Coverage tracking over time
evidence:                     # Test evidence archiving
g3_gate:                      # G3 gate requirements
```

---

## Quick Navigation

### By Task

| Task | Command | Section |
|------|---------|---------|
| Unit test a file | `/f5-test-unit src/file.ts` | [Unit Testing](./README.md#-unit-testing) |
| Test API endpoint | `/f5-test-it api /users` | [Integration Testing](./README.md#-integration-testing) |
| Test user journey | `/f5-test-e2e journey login` | [E2E Testing](./README.md#-e2e-testing) |
| Start TDD session | `/f5-tdd start feature` | [TDD Workflow](./README.md#-tdd-workflow) |
| Check coverage trend | `/f5-test coverage --trend` | [Coverage Tracking](./README.md#-coverage-trend-tracking) |
| Archive test evidence | `/f5-gate evidence archive G3` | [Evidence Archiving](./README.md#-test-evidence-archiving) |
| Setup pre-commit | `/f5-test hooks enable` | [Pre-commit Hooks](./PRE-COMMIT.md) |

### By Gate

| Gate | Tests Required | Command |
|------|----------------|---------|
| G3 (Testing Complete) | Unit + IT + E2E | `/f5-gate check G3` |
| G4 (Deploy Ready) | All + evidence | `/f5-gate check G4` |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.3.6 | 2025-01 | Phase 1 testing commands, shared utilities, visual testing |
| 1.3.0 | 2024-12 | IT Auto-Gen, Design→E2E, Coverage Trend, Evidence Archiving, Pre-commit |
| 1.2.0 | 2024-11 | TDD command, MCP integration |
| 1.1.0 | 2024-10 | Initial Claude Code Testing |

---

## See Also

- [Main README](./README.md)
- [Pre-commit Hooks](./PRE-COMMIT.md)
- [Phase 1 Testing](./PHASE1.md) - Testing optimization details
- [Test Guidelines](./GUIDELINES.md) - Test writing guidelines
- [CLAUDE.md](../../CLAUDE.md) - Framework overview

---

*F5 Framework Testing Documentation Index v1.3.6*
