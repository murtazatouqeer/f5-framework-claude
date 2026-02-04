---
name: architecture
description: Software architecture patterns, principles, and best practices
category: skill
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: true
context: inject
---

# Architecture Skills

## Overview

This module covers fundamental and advanced architecture concepts
applicable across all technology stacks.

## Categories

### Principles
Core software design principles that guide architectural decisions.
- SOLID Principles
- DRY, KISS, YAGNI
- Separation of Concerns
- Dependency Inversion

### Patterns
High-level architecture patterns for organizing systems.
- Clean Architecture
- Hexagonal Architecture
- Layered Architecture
- Domain-Driven Design
- CQRS & Event Sourcing
- Microservices

### Design Patterns
Reusable solutions to common design problems.
- Creational: Factory, Builder, Singleton, DI
- Structural: Adapter, Decorator, Facade, Repository
- Behavioral: Strategy, Observer, Command, State Machine

### Distributed Systems
Patterns for building distributed applications.
- Service Communication
- Data Consistency
- Resilience Patterns
- Event-Driven Architecture

### Decision Making
Tools and frameworks for architectural decisions.
- Architecture Decision Records (ADR)
- Trade-off Analysis
- Documentation Best Practices

## When to Use

- Starting new projects
- Refactoring legacy systems
- Making architecture decisions
- Code review and design discussions
- Team knowledge sharing

## Directory Structure

```
skills/architecture/
├── _index.md
├── principles/
│   ├── solid.md
│   ├── dry-kiss-yagni.md
│   ├── separation-of-concerns.md
│   └── dependency-inversion.md
├── patterns/
│   ├── clean-architecture.md
│   ├── hexagonal-architecture.md
│   ├── layered-architecture.md
│   ├── domain-driven-design.md
│   ├── cqrs-event-sourcing.md
│   └── microservices.md
├── design-patterns/
│   ├── creational/
│   ├── structural/
│   └── behavioral/
├── distributed-systems/
└── decision-making/
```

## Integration with F5 Framework

These skills are referenced by:
- Stack templates for implementation guidance
- Agents for architecture decisions
- Quality gates for design review
