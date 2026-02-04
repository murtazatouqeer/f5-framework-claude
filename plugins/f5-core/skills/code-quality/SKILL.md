---
name: code-quality
description: Code quality practices, linting, and refactoring
category: skill
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: true
context: inject
version: 1.0.0
---

# Code Quality Skills

## Overview

Code quality practices for writing clean, maintainable, and reliable code. These skills cover linting, static analysis, refactoring, naming conventions, documentation, and best practices.

## Quality Metrics

| Metric | Good | Warning | Bad |
|--------|------|---------|-----|
| Cyclomatic Complexity | < 10 | 10-20 | > 20 |
| Function Length | < 20 lines | 20-50 | > 50 |
| File Length | < 300 lines | 300-500 | > 500 |
| Nesting Depth | < 3 | 3-4 | > 4 |
| Code Coverage | > 80% | 60-80% | < 60% |
| Duplicate Code | < 3% | 3-5% | > 5% |
| Technical Debt Ratio | < 5% | 5-10% | > 10% |

## Categories

### Linting
Automated code style enforcement and error detection:
- **ESLint** - JavaScript/TypeScript linting
- **Prettier** - Code formatting
- **Stylelint** - CSS/SCSS linting
- **lint-staged** - Pre-commit linting

### Static Analysis
Deep code analysis beyond linting:
- **TypeScript Strict Mode** - Maximum type safety
- **SonarQube** - Comprehensive analysis platform
- **Code Coverage** - Test coverage metrics

### Refactoring
Code improvement techniques:
- **Code Smells** - Identifying problematic patterns
- **Refactoring Techniques** - Systematic improvements
- **Extract Method** - Breaking down functions
- **When to Refactor** - Decision framework

### Naming
Clear and consistent naming:
- **Naming Conventions** - Project-wide standards
- **Variable Naming** - Descriptive identifiers
- **Function Naming** - Action-oriented names

### Documentation
In-code documentation:
- **Code Comments** - When and how to comment
- **JSDoc/TSDoc** - Type documentation
- **README Standards** - Project documentation

### Practices
Development best practices:
- **Clean Code Principles** - Foundational concepts
- **Code Review Checklist** - Review guidelines
- **Technical Debt** - Managing and reducing debt
- **Boy Scout Rule** - Continuous improvement

## Quality Gates Integration

```yaml
# .f5/quality/code-quality-gate.yaml
code_quality_gate:
  name: "Code Quality Standards"
  metrics:
    lint_errors: 0
    lint_warnings: 10
    complexity_max: 15
    coverage_min: 80
    duplication_max: 3

  checks:
    - eslint --max-warnings 0
    - tsc --noEmit
    - jest --coverage --coverageThreshold='{"global":{"lines":80}}'
```

## Tool Stack

| Tool | Purpose | Configuration |
|------|---------|---------------|
| ESLint | Linting | `eslint.config.js` |
| Prettier | Formatting | `.prettierrc` |
| TypeScript | Type checking | `tsconfig.json` |
| Jest | Testing/Coverage | `jest.config.js` |
| Husky | Git hooks | `.husky/` |
| lint-staged | Pre-commit | `package.json` |

## Quick Setup

```bash
# Install core tools
npm install -D eslint prettier typescript @typescript-eslint/parser @typescript-eslint/eslint-plugin

# Install formatting
npm install -D eslint-config-prettier eslint-plugin-prettier

# Install git hooks
npm install -D husky lint-staged
npx husky init

# Configure lint-staged
npm pkg set lint-staged='{"*.{ts,tsx}":["eslint --fix","prettier --write"]}'
```

## Related Skills

- [Testing](/skills/testing/) - Test-driven quality
- [Security](/skills/security/) - Secure coding practices
- [Performance](/skills/performance/) - Performance optimization
- [Architecture](/skills/architecture/) - Structural quality
