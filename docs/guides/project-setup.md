# Project Setup Guide

Complete guide for initializing and configuring F5 Framework projects.

## Overview

The F5 Framework provides two main setup workflows:

1. **New Project** (`/f5-init`) - Create a brand new project with F5 configuration
2. **Existing Project** (`/f5-load`) - Add F5 to an existing codebase with auto-detection

## Quick Start

### New Project

```bash
# Interactive project creation
/f5-init my-project

# Follow the prompts to configure:
# - Architecture (monolith, microservices, etc.)
# - Scale (starter, growth, enterprise)
# - Tech stack (backend, frontend, database)
# - Domain (fintech, e-commerce, etc.)
```

### Existing Project

```bash
# Auto-detect and load existing project
/f5-load

# Claude will:
# - Detect tech stack from package.json, go.mod, etc.
# - Suggest appropriate configuration
# - Create .f5/ directory structure
```

## Project Initialization

### `/f5-init` Command

The init command creates a complete F5 project structure with guided configuration.

#### Step 1: Project Information

```
/f5-init my-project

Output:
🚀 F5 Project Initialization

Project: my-project
Location: ./my-project/

Let's configure your project...
```

#### Step 2: Architecture Selection

```
📐 Select Architecture:

1. monolith        - Single deployable unit (starter)
2. modular-monolith - Organized modules, single deploy (starter, growth)
3. microservices   - Independent services (growth, enterprise)
4. serverless      - Function-based, event-driven (all scales)

Your choice [2]:
```

#### Step 3: Scale Selection

```
📊 Select Scale:

1. starter    - <10K users, 1-5 team, speed focus
2. growth     - 10K-100K users, 5-20 team, reliability
3. enterprise - 100K+ users, 20+ team, HA & compliance

Your choice [2]:
```

#### Step 4: Tech Stack Configuration

```
🔧 Configure Tech Stack:

Backend Framework:
  1. nestjs     (TypeScript/Node.js)
  2. go         (Golang)
  3. spring     (Java)
  4. fastapi    (Python)
  5. express    (Node.js)

Your choice [1]: nestjs

Frontend Framework:
  1. react      (React with TypeScript)
  2. vue        (Vue.js)
  3. angular    (Angular)
  4. nextjs     (Next.js)
  5. none       (API only)

Your choice [1]: react

Database:
  1. postgresql
  2. mysql
  3. mongodb
  4. multiple

Your choice [1]: postgresql
```

#### Step 5: Domain Selection

```
🏢 Select Domain:

1. fintech       - Financial services
2. e-commerce    - Online commerce
3. healthcare    - Health & medical
4. logistics     - Supply chain
5. education     - Learning systems
6. saas          - SaaS products
7. custom        - Define your own

Your choice [2]: e-commerce

Sub-domain:
  1. b2c-retail
  2. b2b-wholesale
  3. marketplace
  4. subscription

Your choice [1]: b2c-retail
```

#### Step 6: Project Creation

```
✨ Creating F5 Project...

Creating directory structure:
  ✓ my-project/
  ✓ my-project/.f5/
  ✓ my-project/.f5/config.json
  ✓ my-project/.f5/memory/
  ✓ my-project/.f5/quality/
  ✓ my-project/.claude/
  ✓ my-project/.claude/commands/
  ✓ my-project/CLAUDE.md

Applying configurations:
  ✓ Architecture: modular-monolith
  ✓ Scale: growth
  ✓ Stack: nestjs + react + postgresql
  ✓ Domain: e-commerce/b2c-retail

✅ Project created successfully!

Next steps:
  cd my-project
  /f5-status       # View project configuration
  /f5-mode         # Check current mode
```

### Generated Structure

```
my-project/
├── .f5/
│   ├── config.json              # Project configuration
│   ├── profile.yaml             # Team profile
│   ├── memory/
│   │   ├── constitution.md      # Project principles
│   │   ├── session.md           # Session context
│   │   ├── decisions.md         # ADRs
│   │   └── learnings.md         # Accumulated knowledge
│   ├── input/                   # Customer documents
│   │   ├── requirements/
│   │   ├── basic-design/
│   │   └── detail-design/
│   ├── specs/                   # Generated specs
│   │   ├── srs/
│   │   ├── basic-design/
│   │   └── detail-design/
│   ├── quality/
│   │   ├── gates-status.yaml    # Gate tracking
│   │   └── checklists/
│   ├── planning/
│   ├── tasks/
│   └── output/
├── .claude/
│   ├── commands/                # Custom slash commands
│   └── skills/                  # Knowledge skills
└── CLAUDE.md                    # Claude instructions
```

## Loading Existing Projects

### `/f5-load` Command

The load command adds F5 to an existing project with automatic detection.

#### Auto-Detection

```
/f5-load

Output:
🔍 Detecting Project Configuration...

Scanning project files...
  ✓ Found package.json
  ✓ Found tsconfig.json
  ✓ Found docker-compose.yml

Detected Tech Stack:
  Backend:  NestJS (from @nestjs/core)
  Frontend: React (from react)
  Database: PostgreSQL (from docker-compose)
  Cache:    Redis (from docker-compose)

Suggested Configuration:
  Architecture: modular-monolith
  Scale: growth (based on project structure)

Apply this configuration? [Y/n]
```

#### Detection Sources

| File | Detects |
|------|---------|
| `package.json` | Node.js frameworks, dependencies |
| `go.mod` | Go modules and dependencies |
| `requirements.txt` | Python packages |
| `pom.xml` | Java/Maven dependencies |
| `docker-compose.yml` | Services, databases |
| `Dockerfile` | Runtime environment |
| `.env` | Service configurations |

#### Manual Override

```
/f5-load --manual

Allows manual configuration instead of auto-detection.
Useful when auto-detection doesn't match your setup.
```

## Configuration Files

### `.f5/config.json`

Main project configuration:

```json
{
  "version": "2.0.0",
  "name": "my-project",
  "created": "2024-01-15T09:00:00Z",
  "architecture": "modular-monolith",
  "scale": "growth",
  "domain": {
    "name": "e-commerce",
    "subDomain": "b2c-retail",
    "variant": "default"
  },
  "stack": {
    "backend": ["nestjs"],
    "frontend": "react",
    "database": ["postgresql"],
    "cache": "redis",
    "queue": null
  },
  "modules": {
    "active": ["nestjs", "react", "postgresql", "e-commerce"],
    "custom": []
  },
  "skills": {
    "installed": ["api-design", "testing-strategy"],
    "autoActivate": true
  },
  "gates": {
    "current": "D1",
    "targets": {
      "D1": 80,
      "D2": 85,
      "D3": 85,
      "D4": 90,
      "G2": 90,
      "G3": 80,
      "G4": 95
    }
  },
  "modes": {
    "default": "development",
    "autoDetect": true
  }
}
```

### `.f5/profile.yaml`

Team and customer profile:

```yaml
project_type: product  # product | outsource
team_size: 10
has_qa: true
has_brse: true

customer:
  language: ja  # ja | en | vi
  timezone: Asia/Tokyo
  review_style: detailed  # detailed | summary
  document_format: japanese  # japanese | english

workflow:
  use_jira: true
  use_strict: true
  use_ba: true
```

### `.f5/memory/constitution.md`

Project principles (non-negotiable rules):

```markdown
# Project Constitution

## Non-Negotiable Rules

1. **Traceability Required**
   All code must have traceability comments (REQ-XXX, FR-XXX, etc.)

2. **Strict Mode Mandatory**
   No implementation without active SIP session

3. **Quality Gates**
   Must pass quality gates before proceeding to next phase

4. **Customer Approval**
   Gates D2, D3, D4 require customer sign-off

## Quality Standards

- Test coverage: minimum 80%
- No critical security vulnerabilities
- API response time: < 200ms (95th percentile)
- Documentation: Japanese format for customer deliverables

## Naming Conventions

- Files: kebab-case (user-service.ts)
- Classes: PascalCase (UserService)
- Functions: camelCase (getUserById)
- Constants: UPPER_SNAKE_CASE (MAX_RETRY_COUNT)
```

## Project Status

### `/f5-status` Command

View comprehensive project status:

```
/f5-status

Output:
📊 F5 Project Status
═══════════════════════════════════════════════════════════════

🎯 Project: my-project
   Version: 1.0.0
   Created: 2024-01-15
   F5 Version: 2.0.0

📍 Current Context:
   Phase: IMPLEMENTATION
   Mode: development (auto-detected)
   Focus: user-authentication

🏗️ Architecture:
   Type: modular-monolith
   Scale: growth
   Domain: e-commerce / b2c-retail

🔧 Tech Stack:
   Backend:  NestJS
   Frontend: React
   Database: PostgreSQL
   Cache:    Redis

📦 Active Modules:
   • nestjs (tech)
   • react (tech)
   • postgresql (tech)
   • e-commerce (domain)

🎯 Installed Skills:
   • api-design
   • testing-strategy
   • security-basics

🔌 MCP Servers:
   ✓ tavily      - Web search
   ✓ context7    - Library docs
   ✓ playwright  - Browser automation
   ○ magic       - Not installed

🚦 Quality Gates:
   D1 │ ✅ PASSED │ 92%
   D2 │ ✅ PASSED │ 88%
   D3 │ 🔄 PENDING │ -
   D4 │ ⏳ WAITING │ -

💡 Recommendations:
   • Complete Gate D3 before implementation
   • Install magic MCP for UI development
   • Consider performance-tuning skill

═══════════════════════════════════════════════════════════════
```

### Status Options

```bash
# Full status (default)
/f5-status

# Brief summary
/f5-status --brief

# JSON format
/f5-status --json

# Focus on gates
/f5-status --gates

# Focus on stack
/f5-status --stack
```

## Best Practices

### For New Projects

1. **Plan Architecture First**
   Choose architecture based on team size and expected scale

2. **Start with Modules**
   Activate modules for your tech stack immediately

3. **Install Relevant Skills**
   Add skills that match your project domain

4. **Configure Team Profile**
   Set customer preferences for document formats

5. **Establish Constitution**
   Define non-negotiable rules before starting

### For Existing Projects

1. **Review Auto-Detection**
   Verify detected configuration matches reality

2. **Migrate Gradually**
   Start with /f5-load, then add features incrementally

3. **Preserve Existing Patterns**
   Don't force F5 conventions on existing code

4. **Document Decisions**
   Use decisions.md for migration choices

## Troubleshooting

### "Project already initialized"

```bash
# If .f5/ already exists
/f5-load  # Instead of /f5-init

# Or force re-initialization
/f5-init --force
```

### "Auto-detection failed"

```bash
# Use manual configuration
/f5-load --manual

# Or specify detection hints
/f5-load --stack nestjs --db postgresql
```

### "Missing configuration"

```bash
# Validate configuration
/f5-status --validate

# Regenerate missing files
/f5-sync --full
```

### "CLAUDE.md out of sync"

```bash
# Sync configuration to CLAUDE.md
/f5-sync

# Preview changes first
/f5-sync --preview
```

## Migration from v1.x

If you have an existing F5 v1.x project:

```bash
# Check migration status
/f5-migrate status

# Preview migration changes
/f5-migrate plan

# Execute migration
/f5-migrate execute

# Rollback if needed
/f5-migrate rollback
```

See [Migration Guide](./migration-guide.md) for detailed instructions.

## Integration

### With Git

```bash
# Recommended .gitignore additions
echo ".f5/memory/session.md" >> .gitignore
echo ".f5/strict-session.json" >> .gitignore
echo ".f5-backup-*/" >> .gitignore
```

### With CI/CD

```yaml
# .github/workflows/f5-check.yml
- name: Check F5 Configuration
  run: |
    f5 doctor
    f5 gate check all
```

### With IDE

Claude Code integrates with F5 via:
- CLAUDE.md file (project instructions)
- Slash commands (/f5-*)
- MCP servers for extended capabilities

---

*F5 Framework - Project Setup Guide v2.0*
