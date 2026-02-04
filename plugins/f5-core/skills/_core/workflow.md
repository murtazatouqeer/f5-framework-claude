---
name: f5-workflow
description: F5 Framework development workflow phases and commands
category: core
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# F5 Development Workflow

## Workflow Phases

### Design Phase (D1-D4)

| Phase | Name | Description | Evidence |
|-------|------|-------------|----------|
| D1 | Research Complete | Market research, tech evaluation, feasibility study | docs/research/ |
| D2 | SRS Approved | Software Requirements Specification, use cases, RTM | docs/srs/ |
| D3 | Basic Design | System architecture, data model, API design | docs/design/ |
| D4 | Detail Design | Module design, class diagrams, API contracts | docs/design/, docs/api/ |

### Implementation Phase (G2-G4)

| Phase | Name | Description | Evidence |
|-------|------|-------------|----------|
| G2 | Implementation Ready | Code complete, unit tests, coverage ≥80% | src/, coverage/ |
| G2.5 | Verification Complete | Asset verification, visual QA, bug fixes | .f5/evidence/G2.5/ |
| G3 | Testing Complete | All tests pass, security scan, performance test | .f5/evidence/G3/ |
| G4 | Deployment Ready | Staging deployed, UAT approved, rollback plan | .f5/evidence/G4/ |

## Standard Flow

```
D1 → D2 → D3 → D4 → G2 → G2.5 → G3 → G4
```

### Alternative Flows

**Quick Flow** (small changes):
```
G2 → G2.5 → G3 → G4
```

**Feature Flow** (feature development):
```
D3 → G2 → G2.5 → G3
```

**Hotfix Flow** (urgent fixes):
```
G2 → G4
```

## Commands

| Command | Description |
|---------|-------------|
| `/f5-workflow` | Show current workflow status |
| `/f5-gate check <gate>` | Check specific gate |
| `/f5-gate status` | Show all gates status |
| `/f5-implement` | Start implementation (requires D4) |
| `/f5-test` | Run tests (for G3) |

## Evidence Directory

All gate evidence is stored in `.f5/gates/`:
```
.f5/gates/
├── D1/
├── D2/
├── D3/
├── D4/
├── G2/
├── G2.5/
├── G3/
└── G4/
```

## Traceability

All code must trace to requirements using comments:
```typescript
// REQ-001: User authentication
export async function authenticate(credentials: Credentials) {
  // Implementation
}
```
