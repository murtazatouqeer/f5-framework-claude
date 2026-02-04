# F5 Framework CLI - Test Writing Guidelines

## Purpose

This guide helps the team write consistent, maintainable, and effective tests.

---

## 1. Test Types & When to Use

### Unit Tests

**When:** Test single function/method in isolation
**Location:** `src/<module>/__tests__/<module>.test.ts`

```typescript
// ✅ Good: Tests one thing
it('should return user by ID', () => {
  const user = getUserById(1);
  expect(user.id).toBe(1);
});

// ❌ Bad: Tests multiple things
it('should get user and update and delete', () => {
  const user = getUserById(1);
  updateUser(user);
  deleteUser(user);
  // Too many responsibilities
});
```

### Integration Tests

**When:** Test interaction between modules
**Location:** `src/integrations/<module>/__tests__/`

```typescript
// Test Jira client + adapter interaction
it('should sync requirements to Jira', async () => {
  const requirement = createRequirement();
  const jiraIssue = await syncToJira(requirement);
  expect(jiraIssue.key).toMatch(/^PROJ-/);
});
```

### MCP Integration Tests

**When:** Test MCP server interactions
**Location:** `src/integrations/mcp/__tests__/`

```typescript
// Always use mock in tests
it('should complete E2E journey', async () => {
  await playwright.navigate('https://example.com');
  await playwright.click('[data-testid="login"]');
  expect(result.success).toBe(true);
});
```

---

## 2. Test Structure

### File Organization

```typescript
/**
 * Module description
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';

// 1. Imports
import { ModuleUnderTest } from '../module.js';
import { Dependency } from '../dependency.js';

// 2. Mocks (before any describe)
vi.mock('fs-extra');
vi.mock('../dependency.js');

// 3. Test suites
describe('ModuleUnderTest', () => {
  // 3.1 Setup
  let instance: ModuleUnderTest;

  beforeEach(() => {
    vi.clearAllMocks();
    instance = new ModuleUnderTest();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  // 3.2 Grouped by method
  describe('methodOne', () => {
    it('should handle success case', () => {});
    it('should handle error case', () => {});
    it('should handle edge case', () => {});
  });

  describe('methodTwo', () => {
    it('should ...', () => {});
  });
});
```

### Test Case Structure (AAA)

```typescript
it('should calculate total price with discount', () => {
  // Arrange - Setup test data
  const items = [
    { name: 'Item 1', price: 100 },
    { name: 'Item 2', price: 200 }
  ];
  const discount = 0.1; // 10%

  // Act - Execute the code under test
  const total = calculateTotal(items, discount);

  // Assert - Verify the result
  expect(total).toBe(270); // (100 + 200) * 0.9
});
```

---

## 3. Naming Conventions

### Test Descriptions

```typescript
// Format: should [expected behavior] when [condition/context]

// ✅ Good
it('should return empty array when no users found', () => {});
it('should throw ValidationError when email is invalid', () => {});
it('should increment count by 1 when button clicked', () => {});

// ❌ Bad
it('test getUsers', () => {}); // Not descriptive
it('works', () => {}); // Too vague
it('should work correctly', () => {}); // What is "correctly"?
```

### Variable Naming

```typescript
// Use descriptive names
const validUser = { id: 1, name: 'John', email: 'john@example.com' };
const invalidEmail = 'not-an-email';
const emptyList: User[] = [];

// Prefix expected values
const expectedTotal = 100;
const expectedErrorMessage = 'Invalid input';
```

---

## 4. Mocking Best Practices

### When to Mock

| Mock | Don't Mock |
|------|------------|
| External APIs (Jira, HTTP) | Pure functions |
| File system (fs) | Simple calculations |
| Database connections | Data transformations |
| Time/Date (for determinism) | Business logic |
| Third-party libraries | The module under test |

### Mock Examples

```typescript
// Mock entire module
vi.mock('fs-extra', () => ({
  readJson: vi.fn(),
  writeJson: vi.fn(),
  existsSync: vi.fn().mockReturnValue(true)
}));

// Mock with implementation
vi.mock('../api-client.js', () => ({
  ApiClient: vi.fn().mockImplementation(() => ({
    get: vi.fn().mockResolvedValue({ data: 'test' }),
    post: vi.fn().mockResolvedValue({ success: true })
  }))
}));

// Mock for specific test
it('should handle file not found', () => {
  vi.mocked(fs.existsSync).mockReturnValueOnce(false);

  expect(() => loadConfig()).toThrow('File not found');
});

// Reset between tests
beforeEach(() => {
  vi.clearAllMocks(); // Clear call history
});

afterEach(() => {
  vi.restoreAllMocks(); // Restore original implementations
});
```

### Avoid Over-Mocking

```typescript
// ❌ Bad: Mocking the thing you're testing
vi.mock('../calculator.js');
import { add } from '../calculator.js';

it('should add numbers', () => {
  vi.mocked(add).mockReturnValue(5);
  expect(add(2, 3)).toBe(5); // This tests nothing!
});

// ✅ Good: Test real implementation
import { add } from '../calculator.js';

it('should add numbers', () => {
  expect(add(2, 3)).toBe(5);
});
```

---

## 5. Testing Patterns

### Testing Async Code

```typescript
// Using async/await
it('should fetch user data', async () => {
  const user = await fetchUser(1);
  expect(user.name).toBe('John');
});

// Testing rejected promises
it('should throw on invalid ID', async () => {
  await expect(fetchUser(-1)).rejects.toThrow('Invalid ID');
});

// Testing with timeout
it('should complete within timeout', async () => {
  const result = await Promise.race([
    longRunningTask(),
    new Promise((_, reject) =>
      setTimeout(() => reject(new Error('Timeout')), 5000)
    )
  ]);
  expect(result).toBeDefined();
});
```

### Testing Error Handling

```typescript
// Synchronous errors
it('should throw when input is null', () => {
  expect(() => processInput(null)).toThrow('Input cannot be null');
});

// Async errors
it('should reject when API fails', async () => {
  vi.mocked(apiClient.get).mockRejectedValue(new Error('Network error'));

  await expect(fetchData()).rejects.toThrow('Network error');
});

// Error type checking
it('should throw ValidationError', () => {
  expect(() => validate({})).toThrow(ValidationError);
});
```

### Testing Edge Cases

```typescript
describe('processArray', () => {
  it('should handle empty array', () => {
    expect(processArray([])).toEqual([]);
  });

  it('should handle single element', () => {
    expect(processArray([1])).toEqual([1]);
  });

  it('should handle null input', () => {
    expect(() => processArray(null)).toThrow();
  });

  it('should handle undefined input', () => {
    expect(() => processArray(undefined)).toThrow();
  });

  it('should handle very large array', () => {
    const largeArray = Array(10000).fill(1);
    expect(processArray(largeArray)).toHaveLength(10000);
  });
});
```

### Testing with Fixtures

```typescript
import { readFileSync } from 'fs';
import { join } from 'path';

const FIXTURES_PATH = 'test/fixtures';

function loadFixture(filename: string) {
  return readFileSync(join(FIXTURES_PATH, filename), 'utf-8');
}

describe('ExcelParser', () => {
  it('should parse requirements file', async () => {
    const parser = new ExcelParser();
    const result = await parser.parse('test/fixtures/requirements-v1.xlsx');

    expect(result.sheets).toHaveLength(1);
    expect(result.rows).toBeGreaterThan(0);
  });
});
```

---

## 6. Japanese Content Testing

### Character Encoding

```typescript
it('should handle Japanese characters', () => {
  const input = {
    title: 'ユーザーログイン機能',
    description: '※1 メール認証必須'
  };

  const result = processRequirement(input);

  expect(result.title).toBe('ユーザーログイン機能');
  expect(result.notes).toContain('※1');
});
```

### Note Patterns

```typescript
describe('Japanese note patterns', () => {
  const patterns = [
    { input: '※1', expected: '[^1]' },
    { input: '*1', expected: '[^1]' },
    { input: '(注1)', expected: '[^1]' },
    { input: '→1', expected: '[^1]' }
  ];

  patterns.forEach(({ input, expected }) => {
    it(`should convert ${input} to ${expected}`, () => {
      expect(convertNote(input)).toBe(expected);
    });
  });
});
```

---

## 7. Coverage Guidelines

### What to Cover

| Priority | What | Coverage Target |
|----------|------|-----------------|
| High | Business logic | 90%+ |
| High | Error handling | 80%+ |
| Medium | Edge cases | 70%+ |
| Medium | Integrations | 60%+ |
| Low | Utility functions | 50%+ |

### What NOT to Cover

- Type definitions (`.d.ts`)
- Index files (re-exports only)
- Configuration files
- Generated code

### Improving Coverage

```bash
# Find uncovered lines
npm run test:coverage

# Look for:
# - Untested functions (0% function coverage)
# - Untested branches (if/else not covered)
# - Error handlers (catch blocks)
```

---

## 8. Common Patterns

### Testing Classes

```typescript
describe('UserService', () => {
  let service: UserService;
  let mockRepo: MockRepository;

  beforeEach(() => {
    mockRepo = new MockRepository();
    service = new UserService(mockRepo);
  });

  describe('getUser', () => {
    it('should return user when found', async () => {
      mockRepo.findById.mockResolvedValue({ id: 1, name: 'John' });

      const user = await service.getUser(1);

      expect(user.name).toBe('John');
    });

    it('should throw when not found', async () => {
      mockRepo.findById.mockResolvedValue(null);

      await expect(service.getUser(1)).rejects.toThrow('User not found');
    });
  });
});
```

### Testing Event Emitters

```typescript
it('should emit event on success', async () => {
  const handler = vi.fn();
  emitter.on('success', handler);

  await emitter.process();

  expect(handler).toHaveBeenCalledWith({ status: 'complete' });
});
```

### Testing Timers

```typescript
beforeEach(() => {
  vi.useFakeTimers();
});

afterEach(() => {
  vi.useRealTimers();
});

it('should timeout after 5 seconds', async () => {
  const promise = waitWithTimeout(10000);

  vi.advanceTimersByTime(5000);

  await expect(promise).rejects.toThrow('Timeout');
});
```

---

## 9. Review Checklist

Before submitting PR, verify:

- [ ] All tests pass: `npm run test`
- [ ] Coverage thresholds met: `npm run test:coverage`
- [ ] No skipped tests (`.skip`) without reason
- [ ] Test names are descriptive
- [ ] Mocks are properly reset
- [ ] Edge cases covered
- [ ] Error cases covered
- [ ] No hardcoded values (use fixtures/constants)
- [ ] Tests run independently (no order dependency)
- [ ] Japanese content handled correctly (if applicable)

---

## 10. Anti-Patterns to Avoid

### Don't Do This

```typescript
// ❌ Testing implementation details
it('should call internal method', () => {
  const spy = vi.spyOn(instance, '_privateMethod');
  instance.publicMethod();
  expect(spy).toHaveBeenCalled();
});

// ❌ Brittle assertions
it('should return exact object', () => {
  expect(result).toEqual({
    id: 1,
    createdAt: '2024-01-01T00:00:00.000Z', // Will fail with different time
    // ... many properties
  });
});

// ❌ Testing multiple things
it('should create, update, and delete user', () => {
  // Too many responsibilities
});

// ❌ Magic numbers without context
it('should return correct value', () => {
  expect(calculate(5, 3)).toBe(15);
});
```

### Do This Instead

```typescript
// ✅ Testing behavior
it('should return calculated result', () => {
  const result = instance.publicMethod(input);
  expect(result).toBe(expectedOutput);
});

// ✅ Flexible assertions
it('should return object with required properties', () => {
  expect(result).toMatchObject({
    id: expect.any(Number),
    createdAt: expect.any(String)
  });
});

// ✅ Single responsibility
it('should create user', () => { /* ... */ });
it('should update user', () => { /* ... */ });
it('should delete user', () => { /* ... */ });

// ✅ Descriptive constants
it('should multiply values correctly', () => {
  const multiplier = 5;
  const multiplicand = 3;
  const expectedProduct = 15;

  expect(calculate(multiplier, multiplicand)).toBe(expectedProduct);
});
```

---

## 11. Phase 1 Testing Commands (v1.2.8)

Phase 1 introduced optimized testing commands with shared utilities and consistent patterns across the F5 Framework.

### Specialized Testing Commands

| Command | Purpose | MCP Integration |
|---------|---------|-----------------|
| `/f5-test-unit` | Unit testing operations | - |
| `/f5-test-it` | Integration testing | Sequential |
| `/f5-test-e2e` | E2E testing | Playwright |
| `/f5-test-visual` | Visual regression | Playwright |
| `/f5-tdd` | TDD workflow | - |

### Shared Utilities (`_test-shared`)

All testing commands share common utilities defined in `_test-shared.md`:

```typescript
// Shared coverage tracking
const coverage = await collectCoverage({
  threshold: 80,
  reporters: ['text', 'html', 'json']
});

// Shared evidence archiving for G3 gate
await archiveEvidence({
  type: 'test-results',
  gate: 'G3',
  artifacts: ['coverage/', 'reports/']
});

// Shared mock generators
const mockUser = createMock('user', {
  id: 1,
  name: 'Test User',
  email: 'test@example.com'
});
```

### TDD Workflow

The `/f5-tdd` command supports the full Red-Green-Refactor cycle:

```bash
# Start TDD session
/f5-tdd start user-authentication

# Write failing test (Red)
/f5-tdd --red

# Make test pass (Green)
/f5-tdd --green

# Improve code quality (Refactor)
/f5-tdd --refactor

# End session with summary
/f5-tdd end
```

### Coverage Trend Tracking

Track coverage over time with the trend feature:

```bash
# View coverage trend
/f5-test coverage --trend

# Archive coverage for gate evidence
/f5-gate evidence archive G3 --include-coverage
```

### Integration with Quality Gates

| Gate | Required Tests | Coverage |
|------|----------------|----------|
| G2 | Unit tests pass | - |
| G3 | Unit + IT + E2E | ≥80% |
| G4 | All + evidence | ≥80% |

---

## Related Documentation

| Document | Description |
|----------|-------------|
| [Testing Guide](TESTING.md) | Comprehensive testing documentation |
| [Contributing Guide](../CONTRIBUTING.md) | How to contribute with proper testing |
| [Test Template](../packages/cli/scripts/templates/test-template.ts) | Copy this when writing new tests |
| [Phase 1 Testing](./PHASE1.md) | Phase 1 testing optimization details |
| [Testing Index](testing/INDEX.md) | Testing commands index |

---

*Last updated: January 2025*
