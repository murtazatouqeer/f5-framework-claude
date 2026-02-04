# F5 Framework Phase 1: Testing Commands Optimization

## Overview

Phase 1 (v1.2.8) introduced optimized testing commands with shared utilities, consistent patterns, and improved MCP integration across the F5 Framework.

## Timeline

| Metric | Value |
|--------|-------|
| Version | 1.2.8 |
| Focus | Testing commands optimization |
| Commands Added | 6 specialized testing commands |
| Shared Utilities | `_test-shared.md` |

## Testing Commands

### Command Overview

| Command | Purpose | MCP Integration |
|---------|---------|-----------------|
| `/f5-test` | Master test orchestrator | - |
| `/f5-test-unit` | Unit testing operations | - |
| `/f5-test-it` | Integration testing | Sequential |
| `/f5-test-e2e` | E2E testing | Playwright |
| `/f5-test-visual` | Visual regression testing | Playwright |
| `/f5-tdd` | TDD workflow management | - |

### `/f5-test` - Master Command

The master testing command orchestrates all test types:

```bash
# Run all tests
/f5-test run

# Run specific test type
/f5-test run --type unit
/f5-test run --type integration
/f5-test run --type e2e

# Generate tests
/f5-test generate src/services/

# Check coverage
/f5-test coverage --trend
```

### `/f5-test-unit` - Unit Testing

Focused unit testing for isolated function testing:

```bash
# Generate unit tests for a file
/f5-test-unit generate src/services/user.ts

# Run unit tests
/f5-test-unit run

# Run with coverage
/f5-test-unit run --coverage

# Watch mode for development
/f5-test-unit watch
```

### `/f5-test-it` - Integration Testing

Integration testing with multi-step analysis:

```bash
# Test API endpoint
/f5-test-it api /users

# Test service layer
/f5-test-it service PaymentService

# Test database operations
/f5-test-it db UserRepository

# Run all integration tests
/f5-test-it run --all
```

**MCP Integration:** Uses Sequential MCP for complex multi-step analysis.

### `/f5-test-e2e` - End-to-End Testing

E2E testing with Playwright integration:

```bash
# Run E2E tests
/f5-test-e2e run

# Test specific user journey
/f5-test-e2e journey login
/f5-test-e2e journey checkout
/f5-test-e2e journey user-registration

# Visual regression
/f5-test-e2e visual

# Generate from design docs
/f5-test-e2e generate --from-design
```

**MCP Integration:** Uses Playwright MCP for browser automation.

### `/f5-test-visual` - Visual Regression

Visual regression testing for UI components:

```bash
# Run visual tests
/f5-test-visual run

# Update baseline screenshots
/f5-test-visual update

# Compare specific component
/f5-test-visual compare Button
/f5-test-visual compare Header
```

**MCP Integration:** Uses Playwright MCP for screenshot capture.

### `/f5-tdd` - TDD Workflow

Test-Driven Development workflow support:

```bash
# Start TDD session
/f5-tdd start user-authentication

# Red phase - write failing test
/f5-tdd --red

# Green phase - make test pass
/f5-tdd --green

# Refactor phase - improve code
/f5-tdd --refactor

# End session with summary
/f5-tdd end
```

## Shared Utilities (`_test-shared`)

All testing commands share common utilities defined in `.claude/commands/_test-shared.md`:

### Coverage Tracking

```typescript
// Consistent coverage reporting
const coverage = await collectCoverage({
  threshold: 80,
  reporters: ['text', 'html', 'json'],
  excludePatterns: ['**/*.test.ts', '**/fixtures/**']
});
```

### Evidence Archiving

```typescript
// G3 gate evidence collection
await archiveEvidence({
  type: 'test-results',
  gate: 'G3',
  artifacts: [
    'coverage/',
    'reports/',
    'screenshots/'
  ]
});
```

### Mock Generators

```typescript
// Reusable test mock patterns
const mockUser = createMock('user', {
  id: 1,
  name: 'Test User',
  email: 'test@example.com'
});

const mockApiResponse = createMock('api-response', {
  status: 200,
  data: { success: true }
});
```

### Fixture Management

```typescript
// Shared test fixtures
const fixtures = loadFixtures('users');
const testData = fixtures.getById('admin-user');
```

## Quality Gate Integration

### G3 Gate Requirements

| Requirement | Target | Command |
|-------------|--------|---------|
| Unit test coverage | ≥80% | `/f5-test-unit run --coverage` |
| Integration tests pass | 100% | `/f5-test-it run --all` |
| E2E tests pass | 100% | `/f5-test-e2e run` |
| Visual regression | No diff | `/f5-test-visual run` |

### Evidence Collection

```bash
# Archive all test evidence for G3
/f5-gate evidence archive G3 --include-coverage

# Check G3 readiness
/f5-gate check G3
```

## Coverage Trend Tracking

Track coverage over time:

```bash
# View coverage trend
/f5-test coverage --trend

# Output example:
# Date       | Unit  | IT   | E2E  | Total
# 2025-01-20 | 75%   | 60%  | 50%  | 68%
# 2025-01-25 | 80%   | 65%  | 55%  | 72%
# 2025-01-27 | 85%   | 70%  | 60%  | 76%
```

## MCP Server Requirements

| Test Type | MCP Server | Purpose |
|-----------|------------|---------|
| Integration | Sequential | Multi-step analysis |
| E2E | Playwright | Browser automation |
| Visual | Playwright | Screenshot capture |

### MCP Configuration

Ensure these MCP servers are available:

```json
{
  "mcpServers": {
    "sequential-thinking": {
      "command": "npx",
      "args": ["-y", "@anthropic/mcp-sequential-thinking"]
    },
    "playwright": {
      "command": "npx",
      "args": ["-y", "@anthropic/mcp-playwright"]
    }
  }
}
```

## Best Practices

### 1. Use Shared Utilities

Always use `_test-shared` utilities for consistency:

```bash
# Good - uses shared coverage tracking
/f5-test-unit run --coverage

# Avoid - manual coverage setup
npm run test -- --coverage
```

### 2. Follow TDD Workflow

For new features, use the TDD cycle:

```bash
/f5-tdd start feature-name
/f5-tdd --red      # Write failing test first
/f5-tdd --green    # Implement minimum code
/f5-tdd --refactor # Improve code quality
/f5-tdd end
```

### 3. Archive Evidence for Gates

Always archive test evidence before gate checks:

```bash
/f5-test run --all
/f5-gate evidence archive G3
/f5-gate check G3
```

### 4. Monitor Coverage Trends

Regularly check coverage trends to prevent regression:

```bash
/f5-test coverage --trend
```

## Related Documentation

| Document | Description |
|----------|-------------|
| [Test Guidelines](./GUIDELINES.md) | Test writing guidelines |
| [Testing Index](testing/INDEX.md) | Testing commands index |
| [Command Reference](../reference/commands.md) | All F5 commands |
| [Quality Gates](../guides/quality-gates.md) | Gate requirements |

---

**Version:** 1.2.8 | **Updated:** January 2025
