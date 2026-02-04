---
name: f5-test-it
description: Integration testing with multi-step analysis
argument-hint: <api|database|service|mcp|flow> [target]
mcp-servers: sequential-thinking
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: true
---

# /f5-test-it - Integration Testing

> **Version**: 1.4.0
> **Category**: Testing
> **MCP Required**: Sequential (primary), Playwright (optional)

Integration testing sử dụng MCP tools cho multi-step analysis và verification.

## ARGUMENTS
The user's request is: $ARGUMENTS

---

## MCP PRE-FLIGHT CHECK

| MCP Server | Required | Purpose |
|------------|----------|---------|
| Sequential | ✅ Yes | Multi-step analysis, complex reasoning |
| Playwright | Optional | Browser-based integration |

**If MCP unavailable:**
- ⚠️ Sequential not available → Single-step analysis mode
- Run `/f5-mcp status` to check

---

## COMMAND SYNTAX

```bash
# Test API endpoints
/f5-test-it api /users

# Test database integration
/f5-test-it database users

# Test external services
/f5-test-it service jira-client

# Test MCP health
/f5-test-it mcp

# Test full integration flow
/f5-test-it flow user-registration

# Test with auto-fix
/f5-test-it api /users --fix
```

---

## FLAGS

| Flag | Description |
|------|-------------|
| `--fix` | Auto-fix integration issues |
| `--mock` | Use mock services |
| `--report` | Generate IT report |
| `--verbose` | Detailed output |

---

## IT TYPES

| Type | Description | MCP Tool | Example |
|------|-------------|----------|---------|
| `api` | REST API testing | Sequential | `/f5-test-it api /users` |
| `database` | DB integration | Native | `/f5-test-it database users` |
| `service` | External service | Sequential | `/f5-test-it service jira-client` |
| `mcp` | MCP health check | All | `/f5-test-it mcp` |
| `flow` | Multi-step flow | All | `/f5-test-it flow user-registration` |

---

## WORKFLOW

```
┌─────────────────────────────────────────────────────────────┐
│                   IT WORKFLOW                                │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   /f5-test-it [type] [target]                               │
│           │                                                  │
│           ▼                                                  │
│   ┌───────────────┐                                         │
│   │ MCP Pre-Check │                                         │
│   │ • Sequential? │                                         │
│   │ • Playwright? │                                         │
│   └───────┬───────┘                                         │
│           │                                                  │
│           ▼                                                  │
│   ┌───────────────┐     ┌───────────────┐                   │
│   │ Analyze Deps  │────▶│ Execute Tests │                   │
│   │ • Endpoints   │     │ • Multi-step  │                   │
│   │ • Services    │     │ • Sequential  │                   │
│   └───────────────┘     └───────┬───────┘                   │
│                                 │                            │
│                    Pass ────────┼──────── Fail              │
│                    ▼            │            ▼               │
│           ┌───────────────┐     │    ┌───────────────┐      │
│           │ ✅ Report     │     │    │ Bug Detection │      │
│           └───────────────┘     │    │ --fix? Auto   │      │
│                                 │    └───────────────┘      │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## API TESTING

```bash
/f5-test-it api /users
```

### Output Format

```markdown
## 🔗 API Integration Test: /users

### Test Cases
| Method | Scenario | Status |
|--------|----------|--------|
| GET | List all | ✅ |
| POST | Create | ✅ |
| PUT | Update | ❌ |
| DELETE | Delete | ✅ |

### Failed: PUT /users/:id
**Expected:** 200 OK
**Actual:** 500 Internal Server Error

### 🐛 Bug Detected
**Location:** src/controllers/user.controller.ts:45
**Issue:** Missing null check before update
```

---

## FLOW TESTING

```bash
/f5-test-it flow user-registration
```

Multi-step integration using Sequential MCP:

```markdown
## 🔄 Integration Flow: user-registration

### Flow Steps
| Step | Component | Status |
|------|-----------|--------|
| 1 | API: POST /users | ✅ |
| 2 | DB: Verify created | ✅ |
| 3 | Service: Send email | ❌ |
| 4 | API: GET /users/:id | ✅ |

**Flow Status:** ⚠️ PARTIAL (3/4)

### Bug: Email Not Sent
**Location:** src/services/user.service.ts:45
```

---

## MCP HEALTH CHECK

```bash
/f5-test-it mcp
```

```markdown
## 🔌 MCP Health Check

| Server | Status | Latency |
|--------|--------|---------|
| Sequential | ✅ Online | 85ms |
| Playwright | ✅ Online | 200ms |
| Context7 | ✅ Online | 120ms |
| Serena | ❌ Offline | - |

**Availability:** 75% (3/4)
```

---

## OUTPUT FORMAT

```markdown
## 🔗 Integration Test Report

**Date:** [timestamp]
**Environment:** [dev/staging]

### Summary
| Category | Tests | Pass | Fail |
|----------|-------|------|------|
| API | 15 | 14 | 1 |
| Database | 8 | 8 | 0 |
| Services | 5 | 4 | 1 |
| **Total** | **28** | **26** | **2** |

**Pass Rate:** 92.9%

### Bugs Fixed: 2/2 (with --fix)
```

---

## SEQUENTIAL MCP USAGE

For complex multi-step integration tests:

```yaml
sequential_tasks:
  - step: "Analyze API spec"
    tool: sequential_thinking
  - step: "Generate test cases"
    tool: sequential_thinking
  - step: "Execute and verify"
    tool: sequential_thinking
```

---

## EXAMPLES

```bash
# Test all API endpoints
/f5-test-it api /

# Test specific endpoint
/f5-test-it api /users --verbose

# Test database
/f5-test-it database --all

# Test external service
/f5-test-it service jira-client

# MCP health check
/f5-test-it mcp

# Full user flow with fix
/f5-test-it flow user-registration --fix

# Generate report for G3
/f5-test-it --report --all
```

---

## SEE ALSO

- `/f5-test` - Master test command
- `/f5-test-unit` - Unit testing
- `/f5-test-e2e` - E2E testing
- `/f5-tdd` - TDD workflow
- `/f5-mcp` - MCP management
- `/f5-gate` - Quality gates (G3)
- `_test-shared.md` - Stack detection, common patterns
