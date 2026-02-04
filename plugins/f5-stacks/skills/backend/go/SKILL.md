---
name: go-skills
description: Go backend patterns, best practices, and implementation guides
category: stacks/backend/go
applies_to: go
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: true
context: inject
---

# Go Backend Skills

Statically typed, compiled language for efficient backend services.

## Sub-Skills

### Architecture
- [project-structure.md](architecture/project-structure.md) - Project layout
- [clean-architecture.md](architecture/clean-architecture.md) - Clean architecture
- [dependency-injection.md](architecture/dependency-injection.md) - DI patterns

### Database
- [gorm-patterns.md](database/gorm-patterns.md) - GORM patterns
- [sqlx-patterns.md](database/sqlx-patterns.md) - sqlx patterns
- [repository-pattern.md](database/repository-pattern.md) - Repository pattern
- [migrations.md](database/migrations.md) - Migration tools

### Security
- [jwt-auth.md](security/jwt-auth.md) - JWT authentication
- [middleware.md](security/middleware.md) - Auth middleware
- [input-validation.md](security/input-validation.md) - Input validation

### API
- [gin-patterns.md](api/gin-patterns.md) - Gin framework
- [echo-patterns.md](api/echo-patterns.md) - Echo framework
- [fiber-patterns.md](api/fiber-patterns.md) - Fiber framework

### Error Handling
- [custom-errors.md](error-handling/custom-errors.md) - Custom errors
- [error-wrapping.md](error-handling/error-wrapping.md) - Error wrapping

### Testing
- [testing-patterns.md](testing/testing-patterns.md) - Go testing
- [mocking.md](testing/mocking.md) - Mock patterns
- [table-driven.md](testing/table-driven.md) - Table-driven tests

### Performance
- [concurrency.md](performance/concurrency.md) - Goroutines/channels
- [profiling.md](performance/profiling.md) - Performance profiling

## Detection
Auto-detected when project contains:
- `go.mod` file
- `main.go` file
- `package main` declaration
