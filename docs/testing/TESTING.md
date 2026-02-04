# F5 Framework CLI - Testing Guide

## Table of Contents
1. [Overview](#overview)
2. [Test Structure](#test-structure)
3. [Running Tests](#running-tests)
4. [Writing Tests](#writing-tests)
5. [Coverage Requirements](#coverage-requirements)
6. [MCP Integration Tests](#mcp-integration-tests)
7. [CI/CD Pipeline](#cicd-pipeline)
8. [Troubleshooting](#troubleshooting)

---

## Overview

F5 Framework CLI uses Vitest as the test runner with comprehensive testing across multiple layers:

| Test Type | Location | Purpose |
|-----------|----------|---------|
| Unit Tests | `src/**/__tests__/*.test.ts` | Test individual modules |
| Integration Tests | `src/integrations/**/__tests__/` | Test module interactions |
| MCP Tests | `src/integrations/mcp/__tests__/` | Test MCP server integrations |

### Tech Stack
- **Test Runner:** Vitest 1.x
- **Mocking:** Vitest built-in (vi.mock, vi.fn)
- **Coverage:** V8 coverage provider
- **CI/CD:** GitHub Actions

### Test Statistics

| Metric | Count |
|--------|-------|
| Test Files | 23+ |
| Test Cases | 900+ |
| Core Module Tests | 9 |
| Command Tests | 7 |
| Integration Tests | 3 |
| MCP Tests | 3 |
| Parser Tests | 1 |
| MCP Mock Servers | 5 |

**MCP Mock Servers:** Sequential, Playwright, Context7, Tavily, Serena

---

## Test Structure

```
packages/cli/
├── src/
│   ├── core/
│   │   ├── __tests__/
│   │   │   ├── mode-manager.test.ts
│   │   │   ├── strict-mode.test.ts
│   │   │   ├── quality-gates.test.ts
│   │   │   ├── requirement-tracker.test.ts
│   │   │   ├── test-generator.test.ts
│   │   │   ├── excel-processor.test.ts
│   │   │   ├── claude-integration.test.ts
│   │   │   ├── mcp-client.test.ts
│   │   │   ├── doc-validator.test.ts
│   │   │   ├── doc-exporter.test.ts
│   │   │   ├── doc-watcher.test.ts
│   │   │   ├── document-converter.test.ts
│   │   │   ├── version-manager.test.ts
│   │   │   └── notification-service.test.ts
│   │   └── *.ts
│   ├── commands/
│   │   ├── __tests__/
│   │   │   ├── init.test.ts
│   │   │   ├── mode.test.ts
│   │   │   └── gate.test.ts
│   │   └── import/
│   │       └── __tests__/
│   │           ├── excel-import.test.ts
│   │           ├── excel-analyzer.test.ts
│   │           ├── schema-manager.test.ts
│   │           └── jira-converter.test.ts
│   ├── integrations/
│   │   ├── jira/
│   │   │   └── __tests__/
│   │   │       ├── jira-client.test.ts
│   │   │       └── jira-adapter.test.ts
│   │   ├── sync/
│   │   │   └── __tests__/
│   │   │       └── sync-engine.test.ts
│   │   └── mcp/
│   │       ├── mcp-test-config.ts
│   │       ├── mcp-test-utils.ts
│   │       └── __tests__/
│   │           ├── mcp-mock-server.ts
│   │           ├── mcp-health.test.ts
│   │           ├── playwright-integration.test.ts
│   │           └── sequential-integration.test.ts
│   └── parsers/
│       └── __tests__/
│           └── excel-note-parser.test.ts
├── test/
│   ├── fixtures/
│   │   ├── requirements-v1.xlsx
│   │   ├── requirements-v2.xlsx
│   │   ├── requirements-v3.xlsx
│   │   └── requirements-vi.xlsx
│   └── _archive/
│       └── (legacy tests)
├── vitest.config.ts
└── package.json
```

---

## Running Tests

### Basic Commands

```bash
# Run all tests
npm run test

# Run tests in watch mode
npm run test:watch

# Run with coverage
npm run test:coverage

# Run specific test file
npm run test -- src/core/__tests__/mode-manager.test.ts

# Run tests matching pattern
npm run test -- --grep "should validate"
```

### Specialized Commands

```bash
# Run only unit tests (exclude MCP)
npm run test:unit

# Run only integration tests
npm run test:integration

# Run only MCP tests (with mocks)
npm run test:mcp

# Run CI test suite
npm run test:ci

# Generate coverage summary
npm run test:summary

# Full report (coverage + summary)
npm run test:report

# Generate final infrastructure report
npm run test:final-report

# View dashboard
npm run test:dashboard
```

### Test Script Reference

| Script | Description |
|--------|-------------|
| `npm run test` | Run all tests |
| `npm run test:watch` | Watch mode for development |
| `npm run test:coverage` | Generate coverage report |
| `npm run test:unit` | Unit tests only (no MCP) |
| `npm run test:integration` | Integration tests |
| `npm run test:mcp` | MCP tests with mock mode |
| `npm run test:all` | All tests including legacy |
| `npm run test:ci` | CI mode with JUnit output |
| `npm run test:summary` | Coverage summary markdown |
| `npm run test:report` | Coverage + summary |
| `npm run test:final-report` | Complete infrastructure report |
| `npm run test:dashboard` | Display test dashboard |

---

## Writing Tests

### Test File Template

```typescript
/**
 * Module Name Tests
 * @module @f5/cli/core/module-name
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { ModuleName } from '../module-name.js';

// Mock dependencies
vi.mock('fs-extra');
vi.mock('other-dependency');

describe('ModuleName', () => {
  let instance: ModuleName;

  beforeEach(() => {
    vi.clearAllMocks();
    instance = new ModuleName();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('methodName', () => {
    it('should [expected behavior] when [condition]', () => {
      // Arrange
      const input = 'test input';

      // Act
      const result = instance.methodName(input);

      // Assert
      expect(result).toBe('expected output');
    });

    it('should throw error when [invalid condition]', () => {
      // Arrange
      const invalidInput = null;

      // Act & Assert
      expect(() => instance.methodName(invalidInput)).toThrow('Error message');
    });

    it('should handle edge case: [description]', () => {
      // Test edge cases
    });
  });
});
```

### Naming Conventions

| Convention | Example |
|------------|---------|
| Test file | `module-name.test.ts` |
| Describe block | `describe('ModuleName', ...)` |
| Nested describe | `describe('methodName', ...)` |
| Test case | `it('should [verb] when [condition]', ...)` |

### Best Practices

1. **AAA Pattern**: Arrange → Act → Assert
2. **One assertion per test** (when possible)
3. **Mock external dependencies** (fs, http, etc.)
4. **Test edge cases**: null, undefined, empty, boundary values
5. **Test error handling**: invalid inputs, exceptions
6. **Use descriptive test names**: Reading the test name should explain the purpose

### Mocking Guidelines

```typescript
// Mock entire module
vi.mock('fs-extra', () => ({
  readJson: vi.fn(),
  writeJson: vi.fn(),
  existsSync: vi.fn()
}));

// Mock specific implementation
vi.mocked(fs.readJson).mockResolvedValue({ key: 'value' });

// Mock for single test
vi.mocked(fs.existsSync).mockReturnValueOnce(true);

// Spy on method
const spy = vi.spyOn(instance, 'method');

// Mock fetch
global.fetch = vi.fn().mockResolvedValue({
  ok: true,
  json: () => Promise.resolve({ data: 'value' })
});
```

---

## Coverage Requirements

### Thresholds

| Metric | Minimum | Target |
|--------|---------|--------|
| Statements | 60% | 80% |
| Branches | 50% | 75% |
| Functions | 60% | 80% |
| Lines | 60% | 80% |

### Coverage Reports

```bash
# Generate coverage
npm run test:coverage

# View HTML report
open .f5/testing/reports/coverage/index.html

# View summary
cat .f5/testing/reports/coverage-summary.md
```

### Improving Coverage

1. **Identify uncovered files:**
   ```bash
   npm run test:coverage
   # Check files with < 50% in coverage report
   ```

2. Write tests for uncovered functions
3. Test all code paths (if/else, switch cases)
4. Don't ignore edge cases

---

## MCP Integration Tests

### Overview

MCP (Model Context Protocol) tests use mock servers in CI/CD to avoid real network calls.

### Mock Mode

```bash
# Force mock mode
MCP_MOCK_MODE=true npm run test:mcp

# CI automatically uses mocks
CI=true npm run test
```

### Available Mock Servers

| Server | Class | Purpose |
|--------|-------|---------|
| Sequential Thinking | `MockSequentialThinkingMCP` | Multi-step reasoning |
| Playwright | `MockPlaywrightMCP` | Browser automation |
| Context7 | `MockContext7MCP` | Documentation search |
| Tavily | `MockTavilyMCP` | Web search |
| Serena | `MockSerenaMCP` | Code understanding |

### Writing MCP Tests

```typescript
import {
  MockPlaywrightMCP,
  setupMCPMocks,
  cleanupMCPMocks
} from './mcp-mock-server.js';

describe('MCP Integration', () => {
  let playwright: MockPlaywrightMCP;

  beforeEach(() => {
    setupMCPMocks();
    playwright = new MockPlaywrightMCP();
  });

  afterEach(() => {
    cleanupMCPMocks();
  });

  it('should navigate and interact', async () => {
    await playwright.navigate('https://example.com');
    await playwright.click('[data-testid="button"]');

    const result = await playwright.getContent();
    expect(result.success).toBe(true);
  });
});
```

### MCP Test Utilities

```typescript
import {
  checkMCPHealth,
  initMCPTestContext,
  skipIfMCPUnavailable,
  withMCPRetry
} from '../mcp-test-utils.js';

// Initialize test context
const context = await initMCPTestContext();

// Check if server should be skipped
if (skipIfMCPUnavailable(context, 'playwright')) {
  return;
}

// Retry operations
const result = await withMCPRetry(
  () => mcpOperation(),
  3,  // retries
  1000 // delay ms
);
```

---

## CI/CD Pipeline

### GitHub Actions Workflow

Workflow runs on:
- Push to `main` or `develop`
- Pull requests to `main` or `develop`

### Pipeline Stages

1. **Install**: `npm ci`
2. **Lint**: `npm run lint`
3. **Test**: `npm run test:coverage`
4. **Coverage Check**: Validate thresholds
5. **Report**: Upload artifacts, comment on PR

### Branch Protection

Branches `main` and `develop` require:
- ✅ Tests pass
- ✅ Coverage thresholds met
- ✅ PR review approved

### Local CI Simulation

```bash
# Run CI test script locally
node scripts/ci-test.mjs
```

### Workflow Configuration

See `.github/workflows/test.yml` for full configuration.

---

## Troubleshooting

### Common Issues

#### Tests timeout

```bash
# Increase timeout
npm run test -- --testTimeout=60000
```

#### Mock not working

```typescript
// Ensure mock is before import
vi.mock('module');
import { something } from 'module';
```

#### Coverage not updating

```bash
# Clear cache
rm -rf node_modules/.vitest
npm run test:coverage
```

#### ES Module errors

```typescript
// Use .js extension in imports
import { func } from './module.js';
```

#### MCP tests failing in CI

```bash
# Ensure mock mode is enabled
MCP_MOCK_MODE=true npm run test:mcp
```

### Debug Mode

```bash
# Run with debug output
DEBUG=* npm run test

# Run single test with verbose
npm run test -- src/core/__tests__/mode-manager.test.ts --reporter=verbose

# Run with console output visible
npm run test -- --no-silent
```

### Getting Help

1. Check existing tests for examples
2. Review Vitest documentation: https://vitest.dev/
3. Check `scripts/templates/test-template.ts` for template
4. Ask in team Slack channel
5. Create issue with test reproduction steps

---

## Quick Reference

### Test File Checklist

- [ ] File named `*.test.ts`
- [ ] Located in `__tests__` directory
- [ ] Imports from vitest
- [ ] Has describe blocks
- [ ] Has beforeEach/afterEach for cleanup
- [ ] Mocks external dependencies
- [ ] Tests success cases
- [ ] Tests error cases
- [ ] Tests edge cases

### Common Assertions

```typescript
// Equality
expect(value).toBe(expected);
expect(value).toEqual(expected);

// Truthiness
expect(value).toBeTruthy();
expect(value).toBeFalsy();
expect(value).toBeNull();
expect(value).toBeDefined();

// Numbers
expect(value).toBeGreaterThan(3);
expect(value).toBeLessThanOrEqual(10);

// Strings
expect(value).toMatch(/pattern/);
expect(value).toContain('substring');

// Arrays
expect(array).toHaveLength(3);
expect(array).toContain(item);

// Objects
expect(obj).toHaveProperty('key');
expect(obj).toMatchObject({ key: 'value' });

// Errors
expect(() => fn()).toThrow();
expect(() => fn()).toThrow('message');

// Async
await expect(promise).resolves.toBe(value);
await expect(promise).rejects.toThrow();

// Mocks
expect(mockFn).toHaveBeenCalled();
expect(mockFn).toHaveBeenCalledWith(arg);
expect(mockFn).toHaveBeenCalledTimes(2);
```

---

## Related Documentation

| Document | Description |
|----------|-------------|
| [Test Writing Guidelines](./GUIDELINES.md) | Best practices, patterns, naming conventions |
| [Contributing Guide](../CONTRIBUTING.md) | How to contribute with proper testing |
| [CI/CD Setup](CI-CD-SETUP.md) | GitHub Actions workflow configuration |
| [Vitest Documentation](https://vitest.dev/) | Official Vitest documentation |

---

*Last updated: December 2024*
