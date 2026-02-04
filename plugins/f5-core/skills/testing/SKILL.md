---
name: testing
description: Testing strategies, patterns, and best practices
category: skill
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: true
context: inject
---

# Testing Skills

## Overview

Comprehensive testing knowledge for building reliable, maintainable software
with confidence in deployments.

## Categories

### Fundamentals
- Testing Pyramid
- Test-Driven Development (TDD)
- Behavior-Driven Development (BDD)
- Core Testing Principles

### Unit Testing
- Test isolation and independence
- Mocking and stubbing strategies
- Test doubles (mocks, stubs, spies, fakes)
- Effective assertions

### Integration Testing
- Database integration tests
- API endpoint testing
- External service testing
- Container-based testing

### End-to-End Testing
- Browser automation
- Mobile app testing
- Visual regression testing
- Cross-browser testing

### Test Patterns
- Arrange-Act-Assert (AAA)
- Given-When-Then
- Test fixtures and factories
- Page Object Model

### Advanced Testing
- Property-based testing
- Mutation testing
- Contract testing
- Chaos engineering

## Test Pyramid

```
         ╱╲
        ╱  ╲         E2E Tests
       ╱────╲        (Few, Slow, Expensive)
      ╱      ╲
     ╱────────╲      Integration Tests
    ╱          ╲     (Medium)
   ╱────────────╲
  ╱              ╲   Unit Tests
 ╱________________╲  (Many, Fast, Cheap)
```

## Quick Reference

| Test Type | Speed | Scope | Confidence | Cost |
|-----------|-------|-------|------------|------|
| Unit | Fast (ms) | Single unit | Low-Medium | Low |
| Integration | Medium (s) | Multiple units | Medium-High | Medium |
| E2E | Slow (min) | Full system | High | High |

## When to Use Each Type

### Unit Tests
- Business logic validation
- Algorithm correctness
- Edge case handling
- Pure functions

### Integration Tests
- Database operations
- API endpoints
- Service interactions
- Message queues

### E2E Tests
- Critical user journeys
- Payment flows
- Authentication
- Cross-service workflows

## Directory Structure

```
skills/testing/
├── _index.md
├── fundamentals/
│   ├── testing-pyramid.md
│   ├── test-driven-development.md
│   ├── behavior-driven-development.md
│   └── testing-principles.md
├── unit-testing/
│   ├── unit-test-basics.md
│   ├── mocking-strategies.md
│   ├── test-doubles.md
│   └── assertion-patterns.md
├── integration-testing/
│   ├── integration-test-basics.md
│   ├── database-testing.md
│   ├── api-testing.md
│   └── external-service-testing.md
├── e2e-testing/
│   ├── e2e-basics.md
│   ├── browser-testing.md
│   ├── mobile-testing.md
│   └── visual-regression.md
├── patterns/
│   ├── arrange-act-assert.md
│   ├── given-when-then.md
│   ├── test-fixtures.md
│   ├── factory-patterns.md
│   └── page-object-model.md
├── advanced/
│   ├── property-based-testing.md
│   ├── mutation-testing.md
│   ├── contract-testing.md
│   └── chaos-testing.md
└── ci-cd/
    ├── test-automation.md
    ├── coverage-reporting.md
    └── flaky-tests.md
```

## Related Skills

- [Code Quality](../code-quality/_index.md)
- [CI/CD](../ci-cd/_index.md)
- [Security](../security/_index.md)
