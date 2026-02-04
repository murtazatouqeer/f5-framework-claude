---
description: Sync project state across team
argument-hint: [--push|--pull|--status]
---

# /f5-sync - Configuration Sync

Sync F5 configuration to CLAUDE.md for Claude Code integration.

## ARGUMENTS
The user's request is: $ARGUMENTS

## PURPOSE

Sync keeps CLAUDE.md updated with:
- Active modules and their knowledge
- Installed skills
- Current mode settings
- Quality gate status
- Project-specific rules

## WHAT GETS SYNCED

| Source | Target | Content |
|--------|--------|---------|
| `.f5/config.json` | `CLAUDE.md` | Project settings, stack, domain |
| `.claude/skills/*` | `CLAUDE.md` | Skill knowledge references |
| `.f5/quality/gates-status.yaml` | `CLAUDE.md` | Current gate status |
| `.f5/memory/constitution.md` | `CLAUDE.md` | Project principles |

## ACTIONS

### Run Sync

```
/f5-sync

Output:
🔄 Syncing F5 Configuration

Reading sources:
  ✓ .f5/config.json
  ✓ .claude/skills/ (3 skills)
  ✓ .f5/quality/gates-status.yaml
  ✓ .f5/memory/constitution.md

Generating CLAUDE.md sections:
  ✓ Project Overview
  ✓ Tech Stack Configuration
  ✓ Domain Knowledge
  ✓ Active Skills
  ✓ Quality Gates Status
  ✓ Project Rules

✓ CLAUDE.md updated successfully!

Changes:
  ~ Updated stack section (added redis)
  + Added new skill: performance-tuning
  ~ Updated gate D3 status: PASSED
```

### Preview Sync

```
/f5-sync --preview

Output:
👁️ Sync Preview (dry run)

Would update CLAUDE.md with:

PROJECT OVERVIEW:
  Name: online-shop
  Architecture: modular-monolith
  Scale: growth
  Domain: e-commerce/b2c-retail

TECH STACK:
  Backend: nestjs
  Frontend: react
  Database: postgresql
  Cache: redis (NEW)

ACTIVE SKILLS:
  - api-design v1.0.0
  - testing-strategy v1.2.0
  - performance-tuning v1.0.0 (NEW)

QUALITY GATES:
  D1: ✅ PASSED (92%)
  D2: ✅ PASSED (88%)
  D3: ✅ PASSED (90%) (CHANGED)
  D4: 🔄 IN PROGRESS

No changes applied (preview mode)
Run /f5-sync to apply
```

### Sync Specific Section

```
/f5-sync --section skills

Output:
🔄 Syncing Skills Section

Reading .claude/skills/:
  ✓ api-design
  ✓ testing-strategy
  ✓ security-basics

Updating CLAUDE.md skills section...
✓ Skills section updated
```

### Full Regenerate

```
/f5-sync --full

Output:
🔄 Full CLAUDE.md Regeneration

This will regenerate CLAUDE.md from template.
Custom modifications will be preserved in:
  .claude/custom-instructions.md

Proceed? [y/N]

Regenerating...
  ✓ Applied base template
  ✓ Merged project configuration
  ✓ Added skill references
  ✓ Updated quality gates
  ✓ Preserved custom instructions

✓ CLAUDE.md fully regenerated
```

## SYNC SECTIONS

### Project Overview

```markdown
## Overview

**Project:** online-shop
**Type:** product
**Architecture:** modular-monolith
**Scale:** growth
**Domain:** e-commerce / b2c-retail
```

### Tech Stack

```markdown
## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | NestJS (TypeScript) |
| Frontend | React (TypeScript) |
| Database | PostgreSQL |
| Cache | Redis |
| Queue | - |
```

### Active Modules

```markdown
## Active Modules

### Tech Modules
- **nestjs**: NestJS framework patterns and best practices
- **react**: React component patterns and hooks
- **postgresql**: PostgreSQL optimization and queries

### Domain Module
- **e-commerce/b2c-retail**: B2C retail patterns, checkout flows, inventory management
```

### Skills Reference

```markdown
## Skills

Claude has access to the following knowledge skills:

| Skill | Type | Description |
|-------|------|-------------|
| api-design | Technical | REST/GraphQL API design patterns |
| testing-strategy | Process | Comprehensive testing approaches |
| security-basics | Security | Essential security practices |

Skills are located in `.claude/skills/` and auto-activate based on context.
```

### Quality Gates

```markdown
## Quality Gates Status

| Gate | Name | Status | Score |
|------|------|--------|-------|
| D1 | Research Complete | ✅ PASSED | 92% |
| D2 | SRS Approved | ✅ PASSED | 88% |
| D3 | Basic Design | ✅ PASSED | 90% |
| D4 | Detail Design | 🔄 IN PROGRESS | - |
| G2 | Implementation | ⏳ WAITING | - |
| G3 | Testing | ⏳ WAITING | - |
| G4 | Deployment | ⏳ WAITING | - |

Current Focus: D4 (Detail Design)
```

### Project Rules

```markdown
## Project Rules

From `.f5/memory/constitution.md`:

### Non-Negotiable
1. All code must have traceability comments
2. No implementation without active SIP session
3. Follow existing naming conventions

### Quality Standards
- Test coverage minimum: 80%
- No critical security vulnerabilities
- API response time < 200ms
```

## AUTO-SYNC

Configure auto-sync triggers:

```json
// .f5/config.json
{
  "sync": {
    "auto": true,
    "triggers": [
      "config-change",
      "skill-install",
      "gate-update"
    ],
    "exclude": [
      "session-changes"
    ]
  }
}
```

### Auto-Sync Events

| Event | Triggers Sync |
|-------|---------------|
| Config change | ✓ |
| Skill installed/removed | ✓ |
| Gate status change | ✓ |
| Module activated | ✓ |
| Session changes | ✗ |

## CUSTOM INSTRUCTIONS

Preserve custom instructions during sync:

```markdown
<!-- .claude/custom-instructions.md -->
## Custom Team Instructions

These instructions are preserved during /f5-sync --full

### Code Style
- Use 2-space indentation
- Prefer functional components

### Review Process
- All PRs need 2 approvals
- Security review for auth changes
```

## EXAMPLES

```bash
# Run sync
/f5-sync

# Preview changes
/f5-sync --preview

# Sync specific section
/f5-sync --section skills
/f5-sync --section gates
/f5-sync --section stack

# Full regeneration
/f5-sync --full

# Force sync (no confirmation)
/f5-sync --force

# Verbose output
/f5-sync --verbose
```

## TROUBLESHOOTING

### "CLAUDE.md not found"

```
/f5-sync --init

Creates CLAUDE.md from template if missing.
```

### "Config validation failed"

```
/f5-sync --validate

Validates config before sync, shows errors.
```

### "Merge conflicts"

```
/f5-sync --resolve

Interactive conflict resolution for custom sections.
```

## INTEGRATION

### With Module Changes

```
/f5-module activate kubernetes
→ Auto-triggers /f5-sync

CLAUDE.md updated with kubernetes module knowledge
```

### With Skill Installation

```
/f5-skill install performance-tuning
→ Auto-triggers /f5-sync

CLAUDE.md updated with new skill reference
```

### With Gate Updates

```
/f5-gate complete D3
→ Auto-triggers /f5-sync

CLAUDE.md updated with new gate status
```

## CONFIGURATION

```json
// .f5/config.json
{
  "sync": {
    "auto": true,
    "preserveCustom": true,
    "template": ".f5-templates/base/CLAUDE.md.template",
    "sections": {
      "overview": true,
      "stack": true,
      "modules": true,
      "skills": true,
      "gates": true,
      "rules": true
    }
  }
}
```

---

**Tip:** Run `/f5-sync --preview` after making configuration changes to see what will be updated before applying!
