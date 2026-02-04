# F5 Framework Command Reference

Complete reference for all 82 F5 slash commands.

## Command Format

All commands use the format `/f5-<command>` (with dash, not colon).

### Frontmatter Support

Every command includes frontmatter for Claude Code autocomplete:

```yaml
---
description: Short description for autocomplete
argument-hint: <required> [optional]
---
```

## Quick Reference

| Command | Description | Arguments |
|---------|-------------|-----------|
| `/f5-init` | Initialize F5 Framework or create new project | `[runtime\|project] [--name <n>]` |
| `/f5-load` | Load project context for new session | `[--deep\|--summary\|--phase <gate>]` |
| `/f5-status` | Show project status and progress | `[--verbose]` |
| `/f5-gate` | Manage quality gates (D1-D4, G2-G4) | `<check\|complete\|enforce> <gate>` |
| `/f5-workflow` | Smart workflow management | `<load\|status\|next\|help> [name]` |
| `/f5-mode` | Switch between development modes | `<strict\|relaxed\|maintenance>` |
| `/f5-persona` | Switch AI persona for different tasks | `<developer\|reviewer\|architect\|ba>` |
| `/f5-suggest` | Get AI suggestions and recommendations | `<architecture\|refactor\|optimize>` |
| `/f5-implement` | Implement features with quality | `<feature> [--tdd\|--with-tests]` |
| `/f5-test` | Master testing command with TDD support | `<generate\|run\|coverage\|report>` |
| `/f5-review` | Code review and quality checks | `<check\|full\|security\|pr> [path]` |
| `/f5-improve` | Automatic code improvement | `[path] [--type quality\|performance\|security]` |
| `/f5-deploy` | Deployment operations | `<preview\|staging\|production> [--dry-run]` |
| `/f5-import` | Import Excel/CSV into F5 structure | `<file> [--type <type>] [--version <ver>]` |
| `/f5-import-batch` | Batch import from folder | `<folder> [--recursive] [--dry-run]` |
| `/f5-update` | Update F5 Framework | `[--check \| --force \| --commands-only \| --mcp-only]` |
| `/f5-test-unit` | Unit testing operations | `<generate\|run> [path] [--coverage]` |
| `/f5-test-it` | Integration testing | `<api\|service\|db> <target> [--sequential]` |
| `/f5-test-e2e` | E2E testing with Playwright | `<run\|journey\|visual> [--headless]` |
| `/f5-test-visual` | Visual regression testing | `<run\|update\|compare> [component]` |

---

## Session Commands

### `/f5-init`
Initialize F5 Framework in a new project.

```bash
# Basic init
/f5-init

# Init with specific workflow
/f5-init --workflow mvp

# Init with domain
/f5-init --domain e-commerce
```

**Options:**
- `--workflow <name>` - Set initial workflow
- `--domain <name>` - Set domain template
- `--stack <name>` - Set technology stack

---

### `/f5-load`
Load F5 configuration for existing project.

```bash
# Standard load
/f5-load

# Deep load with full context
/f5-load --deep

# Update assets
/f5-load --update

# Reset and reload
/f5-load --reset
```

**Options:**
- `--deep` - Load full domain knowledge
- `--update` - Update F5 assets to latest
- `--reset` - Reset session memory
- `--summary` - Show quick status only

---

### `/f5-status`
Show current F5 configuration and state.

```bash
/f5-status
```

**Output includes:**
- Current workflow
- Active mode and persona
- Quality gate status
- Session state

---

### `/f5-doctor`
Health check for F5 Framework installation.

```bash
/f5-doctor
```

**Checks:**
- F5 version
- Configuration files
- Available commands
- MCP servers

---

## Workflow Commands

### `/f5-workflow`
Manage development workflows.

```bash
# List available workflows
/f5-workflow list

# Select a workflow
/f5-workflow select mvp
/f5-workflow select greenfield
/f5-workflow select feature-development
/f5-workflow select maintenance
/f5-workflow select poc

# Show current workflow info
/f5-workflow info

# Get workflow-specific guidance
/f5-workflow guide
```

**Available Workflows:**
| Workflow | Use Case |
|----------|----------|
| `mvp` | Fast startup, lean approach |
| `greenfield` | New enterprise project |
| `poc` | Quick prototype |
| `feature-development` | Adding features |
| `maintenance` | Bug fixes, refactoring |
| `legacy-migration` | Modernizing old code |
| `cloud-migration` | Moving to cloud |

---

### `/f5-suggest`
Get context-aware command suggestions.

```bash
# Phase-based suggestions
/f5-suggest

# Topic-specific suggestions
/f5-suggest api
/f5-suggest testing
/f5-suggest security

# Next steps
/f5-suggest next

# Command chains
/f5-suggest chains
```

---

## Mode & Persona Commands

### `/f5-mode`
Switch development mode (how Claude thinks).

```bash
# Set mode
/f5-mode analytical
/f5-mode planning
/f5-mode coding
/f5-mode debugging
/f5-mode security

# Show current mode
/f5-mode show

# Auto mode (context-based)
/f5-mode auto
```

**Modes:**
| Mode | Description |
|------|-------------|
| `analytical` | Deep analysis, requirements |
| `planning` | Architecture, design |
| `coding` | Implementation, fast |
| `debugging` | Bug fixing, troubleshooting |
| `security` | Security focus |

---

### `/f5-persona`
Activate specialized expertise.

```bash
# Set persona
/f5-persona analyst
/f5-persona architect
/f5-persona backend
/f5-persona frontend
/f5-persona qa
/f5-persona devops
/f5-persona security

# Show current persona
/f5-persona show
```

**Personas:**
| Persona | Expertise |
|---------|-----------|
| `analyst` | Business requirements |
| `architect` | System design |
| `backend` | APIs, databases |
| `frontend` | UI/UX, components |
| `qa` | Testing, quality |
| `devops` | CI/CD, infrastructure |
| `security` | Security practices |

---

### `/f5-verbosity`
Set output detail level.

```bash
/f5-verbosity minimal    # Level 1 - Quick responses
/f5-verbosity normal     # Level 2 - Standard
/f5-verbosity detailed   # Level 3 - More explanation
/f5-verbosity verbose    # Level 4 - Full detail
```

---

## Development Commands

### `/f5-implement`
Start implementation with traceability.

```bash
# Start implementing a requirement
/f5-implement start REQ-001

# Start feature implementation
/f5-implement feature "User Authentication"

# Fix a bug
/f5-implement fix BUG-123

# Sprint planning
/f5-implement sprint --duration 1week
```

**Options:**
- `start <id>` - Start with requirement ID
- `feature <name>` - Start feature
- `fix <id>` - Bug fix
- `sprint` - Sprint planning

---

### `/f5-test`
Run and manage tests.

```bash
# Run all tests
/f5-test run

# Run with coverage
/f5-test run --coverage

# Run specific tests
/f5-test run --type unit
/f5-test run --type integration
/f5-test run --type e2e

# Add regression test
/f5-test add-regression BUG-123

# Check coverage
/f5-test coverage
```

---

### `/f5-review`
Code review commands.

```bash
# Quick review
/f5-review quick

# Full code review
/f5-review code

# Security review
/f5-review security

# Performance review
/f5-review performance
```

---

### `/f5-improve`
Automatic code improvement and optimization.

```bash
# Basic - analyze and preview improvements
/f5-improve [path]

# With improvement type
/f5-improve src/ --type quality
/f5-improve src/ --type performance
/f5-improve src/ --type security
/f5-improve src/ --type all

# With apply mode
/f5-improve src/ --preview       # Preview only (default)
/f5-improve src/ --safe          # Apply low-risk changes
/f5-improve src/ --auto          # Apply all automatically

# Combined with validation
/f5-improve auth-module --type security --safe --validate
```

**Options:**
- `--type <type>` - Improvement type: quality, performance, security, maintainability, all
- `--preview` - Preview only (default)
- `--safe` - Apply low-risk changes only
- `--interactive` - Confirm each change
- `--auto` - Apply all automatically
- `--validate` - Run tests after applying

---

### `/f5-tdd`
Test-Driven Development mode.

```bash
# Start TDD session
/f5-tdd start feature-name

# TDD cycle
/f5-tdd red     # Write failing test
/f5-tdd green   # Make it pass
/f5-tdd refactor # Improve code

# End TDD session
/f5-tdd end
```

---

## Phase 1 Testing Commands (v1.2.8)

Phase 1 introduced optimized testing commands with shared utilities and consistent patterns.

### `/f5-test-unit`
Unit testing operations with focus on isolated function testing.

```bash
# Generate unit tests
/f5-test-unit generate src/services/user.ts

# Run unit tests
/f5-test-unit run

# Run with coverage
/f5-test-unit run --coverage

# Watch mode
/f5-test-unit watch
```

**Options:**
- `generate <path>` - Generate unit tests for file/module
- `run` - Run all unit tests
- `--coverage` - Include coverage report
- `--watch` - Watch mode for development

---

### `/f5-test-it`
Integration testing with multi-step analysis support.

```bash
# Test API endpoint
/f5-test-it api /users

# Test service integration
/f5-test-it service PaymentService

# Test database operations
/f5-test-it db UserRepository

# Full integration suite
/f5-test-it run --all
```

**Options:**
- `api <endpoint>` - Test API endpoint integration
- `service <name>` - Test service layer integration
- `db <repository>` - Test database integration
- `--sequential` - Use Sequential MCP for complex analysis

---

### `/f5-test-e2e`
End-to-end testing with Playwright integration.

```bash
# Run E2E tests
/f5-test-e2e run

# Test specific journey
/f5-test-e2e journey login
/f5-test-e2e journey checkout

# Visual regression testing
/f5-test-e2e visual

# Generate from design
/f5-test-e2e generate --from-design
```

**Options:**
- `run` - Run all E2E tests
- `journey <name>` - Test specific user journey
- `visual` - Visual regression testing
- `--headless` - Run in headless mode
- `--from-design` - Generate tests from design docs

---

### `/f5-test-visual`
Visual regression testing for UI components.

```bash
# Run visual tests
/f5-test-visual run

# Update baselines
/f5-test-visual update

# Compare specific component
/f5-test-visual compare Button
```

**Options:**
- `run` - Run visual regression tests
- `update` - Update baseline screenshots
- `compare <component>` - Compare specific component

---

### Shared Testing Utilities (`_test-shared`)

All Phase 1 testing commands share common utilities:

| Utility | Description |
|---------|-------------|
| Coverage tracking | Consistent coverage reporting |
| Evidence archiving | G3 gate evidence collection |
| Mock generators | Reusable test mock patterns |
| Fixture management | Shared test fixtures |

---

## Quality Gates

### `/f5-gate`
Manage quality gates.

```bash
# Check all gates
/f5-gate status

# Check specific gate
/f5-gate check D1
/f5-gate check D2
/f5-gate check G2

# Complete a gate
/f5-gate complete D1

# Start gate review
/f5-gate start D3
```

**Gates:**
| Gate | Name | Phase |
|------|------|-------|
| D1 | Research Complete | Requirements |
| D2 | SRS Approved | Requirements |
| D3 | Basic Design | Design |
| D4 | Detail Design | Design |
| G2 | Implementation Ready | Build |
| G3 | Testing Complete | Test |
| G4 | Deployment Ready | Deploy |

---

## Specification Commands

### `/f5-ba`
Business Analysis commands.

```bash
# Analyze requirements
/f5-ba analyze

# Analyze specific feature
/f5-ba analyze-feature "Feature Name"

# Define value proposition
/f5-ba value-proposition

# Prioritize features
/f5-ba prioritize --moscow
```

---

### `/f5-spec`
Generate specifications.

```bash
# Generate SRS
/f5-spec generate srs

# Generate MVP scope
/f5-spec generate mvp-scope

# Validate specifications
/f5-spec validate

# Show spec status
/f5-spec status
```

---

### `/f5-design`
Generate design documents.

```bash
# Architecture design
/f5-design generate architecture

# Database design
/f5-design generate database

# API design
/f5-design generate api

# Minimal design (MVP)
/f5-design generate --minimal

# Validate design
/f5-design validate
```

---

## Skill Commands

### `/f5-skill`
Manage skills.

```bash
# List all skills
/f5-skill list

# Add a skill
/f5-skill add api-design
/f5-skill add security
/f5-skill add testing

# Remove a skill
/f5-skill remove messaging

# Show skill details
/f5-skill info api-design
```

**Available Skills:**
- `core` - Core development principles
- `api-design` - REST API best practices
- `architecture` - DDD, Clean Architecture
- `database` - Database design
- `testing` - Testing strategies
- `security` - Security practices
- `performance` - Optimization
- `devops` - CI/CD
- `accessibility` - WCAG guidelines
- `code-quality` - Code review
- `git` - Git workflow
- `messaging` - Event-driven architecture

---

## Session Commands

### `/f5-session`
Manage session state.

```bash
# Create checkpoint
/f5-session checkpoint "feature complete"

# Restore checkpoint
/f5-session restore

# List checkpoints
/f5-session list

# Clear session
/f5-session clear
```

---

## Agent Commands

### `/f5-agent`
Invoke specialized agents.

```bash
# Invoke specific agent
/f5-agent invoke documenter
/f5-agent invoke test_writer
/f5-agent invoke security_scanner
/f5-agent invoke api_designer

# Run agent pipeline
/f5-agent pipeline feature_development
/f5-agent pipeline bug_fix
/f5-agent pipeline security_audit
/f5-agent pipeline code_quality
```

---

## Research Commands

### `/f5-research`
Research and analysis.

```bash
# General research
/f5-research "topic"

# Technology research
/f5-research tech "React vs Vue"

# Best practices research
/f5-research best-practices "authentication"
```

---

## Deployment Commands

### `/f5-deploy`
Deployment commands.

```bash
# Deploy to staging
/f5-deploy staging

# Deploy to production
/f5-deploy production

# Pre-deployment checklist
/f5-deploy checklist

# Rollback
/f5-deploy rollback
```

---

## Bug Commands

### `/f5-bug`
Bug tracking commands.

```bash
# Analyze bug
/f5-bug analyze BUG-123

# Reproduce issue
/f5-bug reproduce BUG-123

# Root cause analysis
/f5-bug root-cause BUG-123

# Close bug
/f5-bug close BUG-123
```

---

## Analysis Commands

### `/f5-analyze`
Code and impact analysis.

```bash
# Impact analysis
/f5-analyze impact --scope module

# Code analysis
/f5-analyze code

# Performance analysis
/f5-analyze performance

# Security analysis
/f5-analyze security
```

---

## Update Commands

### `/f5-update`
Update F5 Framework from source repository.

```bash
# Check for updates
/f5-update --check

# Interactive update
/f5-update

# Force update without confirmation
/f5-update --force

# Only update commands
/f5-update --commands-only

# Only update MCP configs
/f5-update --mcp-only
```

**Update Process:**
1. Compare versions (source vs target manifest)
2. Backup current configs to `.f5-backup/`
3. Update commands (copy to project)
4. Install commands to Claude Code (`f5 install-commands`)
5. Merge MCP configs (keep existing, add Fujigo servers)
6. Update manifest

**Protected Paths (never updated):**
- `.f5/requirements/`
- `.f5/sessions/`
- `.f5/evidence/`
- `.f5/analytics/`

---

## Utility Commands

### `/f5-import`
Import external documents.

```bash
# Import requirements
/f5-import requirements.xlsx

# Import with type
/f5-import screens.xlsx --type basic-design

# Import with version
/f5-import api-v2.xlsx --version v2.0.0

# Import from Jira
/f5-import --from jira
```

---

### `/f5-import-batch`
Batch import multiple Excel files from a folder.

```bash
# Import all Excel files from folder
/f5-import-batch .f5/input/excel/0203/

# Preview with dry-run
/f5-import-batch .f5/input/excel/0203/ --dry-run

# Import with recursive subfolder scanning
/f5-import-batch .f5/input/excel/0203/ --recursive

# Force document type for all files
/f5-import-batch .f5/input/excel/0203/ --type db-design

# Filter by filename pattern
/f5-import-batch .f5/input/excel/0203/ --pattern "UI13_*.xlsx"

# Import with specific version
/f5-import-batch .f5/input/excel/0203/ --version v2.0.0
```

**Options:**
| Flag | Description |
|------|-------------|
| `--pattern <glob>` | File pattern filter (default: `*.xlsx,*.xls`) |
| `--type <type>` | Force document type for all files |
| `--recursive` | Include subfolders |
| `--dry-run` | Preview without executing |
| `--version <ver>` | Version label (default: v1.0.0) |
| `--merge` | Merge into existing files |

**Auto-detected document types:**
| Pattern | Type | Output |
|---------|------|--------|
| `論理テーブル仕様`, `DB_Design` | db-design | `.f5/specs/basic-design/v{VER}/database/` |
| `画面設計書`, `Screen_Design` | screen-design | `.f5/specs/basic-design/v{VER}/screens/` |
| `詳細設計書`, `Detail_Design` | detail-design | `.f5/specs/detail-design/v{VER}/` |
| `API設計`, `API` | api-design | `.f5/specs/basic-design/v{VER}/api/` |

---

### `/f5-help`
Show help information.

```bash
# General help
/f5-help

# Command-specific help
/f5-help workflow
/f5-help mode
/f5-help gate
```

---

## Command Chains

Common command sequences:

### New Feature
```bash
/f5-load
/f5-ba analyze-feature "Feature Name"
/f5-design generate feature-architecture
/f5-implement start FR-001
/f5-test run --coverage
/f5-review code
/f5-gate complete G2
```

### Bug Fix
```bash
/f5-load
/f5-bug analyze BUG-123
/f5-implement fix BUG-123
/f5-test add-regression BUG-123
/f5-test run
/f5-gate complete G2
```

### Before Commit
```bash
/f5-test run
/f5-review quick
/f5-gate check G2
```

### Security Review
```bash
/f5-mode security
/f5-persona security
/f5-analyze security
/f5-review security
```

---

**Full documentation:** [F5 Framework Docs](https://github.com/anthropics/f5-framework)
