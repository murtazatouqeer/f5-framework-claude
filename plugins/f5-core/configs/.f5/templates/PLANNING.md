# Project Planning

> This file captures architectural decisions, design principles, and absolute rules for the project.
> Claude Code reads this file during `/f5-load` to understand project constraints.

## Project Overview

**Project Name:** [Project Name]
**Domain:** [Domain] > [Subdomain]
**Started:** [Date]
**Team Size:** [Number]

## Architecture Decisions

### ADR-001: [Decision Title]
**Date:** [Date]
**Status:** Accepted | Proposed | Deprecated
**Context:** [Why this decision was needed]
**Decision:** [What was decided]
**Consequences:** [Impact of this decision]

### ADR-002: [Decision Title]
**Date:** [Date]
**Status:** Accepted
**Context:** [Context]
**Decision:** [Decision]
**Consequences:** [Consequences]

## Design Principles

### Core Principles
1. **[Principle 1]** - [Description]
2. **[Principle 2]** - [Description]
3. **[Principle 3]** - [Description]

### Code Style Preferences
- **Language:** TypeScript | JavaScript | Python | Go
- **Style Guide:** [Style guide reference]
- **Naming Convention:** camelCase | snake_case | PascalCase
- **Comment Language:** English | Vietnamese

### Testing Strategy
- **Framework:** Jest | Vitest | Pytest | Go test
- **Coverage Target:** [80%]
- **Test Types:** Unit, Integration, E2E

## Absolute Rules

> These rules CANNOT be broken. Claude Code must refuse requests that violate these.

### Security Rules
- [ ] Never commit secrets or credentials
- [ ] Always validate user input
- [ ] Use parameterized queries for database
- [ ] Implement rate limiting on public APIs

### Code Quality Rules
- [ ] All functions must have types/documentation
- [ ] Maximum function length: [50 lines]
- [ ] No console.log in production code
- [ ] All async operations must have error handling

### Business Rules
- [ ] [Domain-specific rule 1]
- [ ] [Domain-specific rule 2]

## Tech Stack Decisions

### Why [Technology X] over [Technology Y]

**Decision:** Use [Technology X]
**Alternatives Considered:** [Technology Y], [Technology Z]
**Rationale:**
- [Reason 1]
- [Reason 2]
- [Reason 3]

### Stack Summary

| Layer | Technology | Version | Notes |
|-------|------------|---------|-------|
| Backend | [tech] | [ver] | [notes] |
| Frontend | [tech] | [ver] | [notes] |
| Database | [tech] | [ver] | [notes] |
| Cache | [tech] | [ver] | [notes] |
| Queue | [tech] | [ver] | [notes] |

## Dependencies Policy

### Approved Dependencies
- [dependency-1] - [purpose]
- [dependency-2] - [purpose]

### Banned Dependencies
- [dependency-x] - [reason for ban]

### Evaluation Criteria
1. Must have active maintenance (commits within 6 months)
2. Must have sufficient test coverage
3. Must not have critical security vulnerabilities
4. License must be compatible with project

## Performance Targets

| Metric | Target | Current |
|--------|--------|---------|
| API Response Time | < 200ms | [current] |
| Page Load Time | < 2s | [current] |
| Database Query | < 50ms | [current] |
| Memory Usage | < 512MB | [current] |

## Compliance Requirements

### Required Compliance
- [ ] [Compliance 1] - [Description]
- [ ] [Compliance 2] - [Description]

### Audit Trail
- All user actions logged
- Data retention: [X days/months]
- Log format: [format]

---
*Last Updated: [Date]*
*Maintained by: [Team/Person]*
