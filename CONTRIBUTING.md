# Contributing to F5 Framework CLI

Thank you for your interest in contributing to F5 Framework! This document provides guidelines and instructions for contributing.

## Table of Contents

1. [Development Setup](#development-setup)
2. [Making Changes](#making-changes)
3. [Testing Requirements](#testing-requirements)
4. [Code Style](#code-style)
5. [Pull Request Process](#pull-request-process)
6. [Issue Guidelines](#issue-guidelines)

---

## Development Setup

### Prerequisites

- Node.js 18.x or higher
- pnpm 8.x or higher
- Git

### Installation

```bash
# Clone repository
git clone <repository-url>
cd f5-framework

# Install dependencies
pnpm install

# Build all packages
pnpm build

# Link CLI for local testing
cd packages/cli && npm link

# Verify installation
f5 --version
```

### Project Structure

```
f5-framework/
├── packages/
│   └── cli/              # Main CLI package
│       ├── src/          # Source code
│       ├── test/         # Test fixtures
│       └── scripts/      # Build/test scripts
├── docs/                 # Documentation
├── skills/               # Skill definitions
├── domains/              # Domain templates
└── stacks/               # Stack configurations
```

---

## Making Changes

### 1. Create Branch

```bash
# Feature branch
git checkout -b feature/your-feature-name

# Bug fix branch
git checkout -b fix/your-bug-fix

# Documentation branch
git checkout -b docs/your-docs-update
```

### 2. Development Workflow

1. Make your changes
2. Add tests for new features
3. Update documentation if needed
4. Run tests locally
5. Commit with conventional commit message

### 3. Run Tests

```bash
cd packages/cli

# Run all tests
npm run test

# Run with coverage
npm run test:coverage

# Run specific test file
npm run test -- src/core/__tests__/mode-manager.test.ts
```

### 4. Commit Messages

Use conventional commit format:

| Type | Description |
|------|-------------|
| `feat:` | New feature |
| `fix:` | Bug fix |
| `docs:` | Documentation only |
| `test:` | Adding tests |
| `refactor:` | Code refactoring |
| `chore:` | Maintenance tasks |
| `perf:` | Performance improvement |
| `style:` | Code style (formatting) |

Examples:
```bash
git commit -m "feat: add Excel export functionality"
git commit -m "fix: resolve null pointer in requirement parser"
git commit -m "docs: update testing guide with MCP examples"
git commit -m "test: add coverage for sync-engine edge cases"
```

### 5. Push & Create PR

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub.

---

## Testing Requirements

### All PRs Must:

1. ✅ Pass all existing tests
2. ✅ Include tests for new code
3. ✅ Meet coverage thresholds
4. ✅ Pass linting

### Coverage Thresholds

| Metric | Minimum | Target |
|--------|---------|--------|
| Statements | 60% | 80% |
| Branches | 50% | 75% |
| Functions | 60% | 80% |
| Lines | 60% | 80% |

### Test Commands

```bash
# Full test suite
npm run test

# With coverage report
npm run test:coverage

# Unit tests only
npm run test:unit

# Integration tests
npm run test:integration

# MCP tests (with mocks)
npm run test:mcp

# CI simulation
npm run test:ci
```

### Writing Tests

See detailed guidelines:
- [Testing Guide](docs/TESTING.md)
- [Test Writing Guidelines](docs/TEST-GUIDELINES.md)

Quick template:

```typescript
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { MyModule } from '../my-module.js';

vi.mock('fs-extra');

describe('MyModule', () => {
  let instance: MyModule;

  beforeEach(() => {
    vi.clearAllMocks();
    instance = new MyModule();
  });

  it('should [expected behavior] when [condition]', () => {
    // Arrange
    const input = 'test';

    // Act
    const result = instance.method(input);

    // Assert
    expect(result).toBe('expected');
  });
});
```

---

## Code Style

### TypeScript

- Use TypeScript for all new code
- Enable strict mode
- Export types alongside implementations
- Use `.js` extension in imports (ES modules)

### Formatting

- 2 spaces for indentation
- Single quotes for strings
- Semicolons required
- Max line length: 100 characters

### Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Files | kebab-case | `excel-processor.ts` |
| Classes | PascalCase | `ExcelProcessor` |
| Functions | camelCase | `processExcel()` |
| Constants | SCREAMING_SNAKE | `MAX_RETRIES` |
| Interfaces | PascalCase + I prefix (optional) | `IExcelOptions` or `ExcelOptions` |

### Documentation

- JSDoc for public APIs
- README for modules with complex logic
- Inline comments for non-obvious code

```typescript
/**
 * Processes Excel file and extracts requirements.
 *
 * @param filePath - Path to Excel file
 * @param options - Processing options
 * @returns Parsed requirements array
 * @throws {ValidationError} When file is invalid
 */
export async function processExcel(
  filePath: string,
  options?: ExcelOptions
): Promise<Requirement[]> {
  // Implementation
}
```

---

## Pull Request Process

### Before Submitting

- [ ] Code follows style guidelines
- [ ] Tests pass locally
- [ ] Coverage thresholds met
- [ ] Documentation updated (if applicable)
- [ ] Commit messages follow convention
- [ ] No console.log or debug statements
- [ ] No commented-out code

### PR Description Template

```markdown
## Summary
Brief description of changes.

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing completed

## Checklist
- [ ] Tests pass
- [ ] Coverage maintained
- [ ] Documentation updated
```

### Review Process

1. Create PR against `develop` branch
2. Wait for CI checks to pass
3. Request review from maintainers
4. Address review feedback
5. Squash and merge when approved

### Requirements for Merge

- At least 1 approval from maintainer
- All CI checks passing
- No unresolved review comments
- Up-to-date with base branch

---

## Issue Guidelines

### Bug Reports

Include:
1. **Description**: Clear description of the bug
2. **Steps to Reproduce**: Minimal steps to reproduce
3. **Expected Behavior**: What should happen
4. **Actual Behavior**: What actually happens
5. **Environment**: OS, Node version, F5 version
6. **Logs**: Relevant error messages

### Feature Requests

Include:
1. **Problem Statement**: What problem does this solve?
2. **Proposed Solution**: How would you solve it?
3. **Alternatives**: Other solutions considered
4. **Use Cases**: Who benefits from this?

### Questions

- Check existing documentation first
- Search closed issues
- Use clear, specific titles

---

## Getting Help

- **Documentation**: Check [docs/](docs/) folder
- **Issues**: Search existing issues
- **Discussions**: Use GitHub Discussions for questions
- **Slack**: Team internal channel

---

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

*Thank you for contributing to F5 Framework!*
