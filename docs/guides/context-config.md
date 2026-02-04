# Context & Configuration Guide

Complete guide for managing F5 Framework modes, modules, skills, and configuration sync.

## Overview

F5 Framework uses a layered context system:

```
MODES → Control Claude's behavior and focus
   ↓
MODULES → Provide domain-specific knowledge
   ↓
SKILLS → Add specialized capabilities
   ↓
SYNC → Keep CLAUDE.md updated
```

## Behavioral Modes

### What are Modes?

Modes define HOW Claude approaches tasks:
- What to prioritize
- What level of detail
- What validations to enforce
- What workflow to follow

### Available Modes

| Mode | Focus | Use When |
|------|-------|----------|
| `research` | Information gathering | Investigating, exploring options |
| `design` | Architecture & planning | System design, documentation |
| `development` | Implementation | Writing code |
| `testing` | Quality assurance | Test creation, validation |
| `review` | Code review | PR reviews, audits |
| `deployment` | Release management | Deploying, releasing |
| `debugging` | Problem solving | Fixing issues, investigating |

### Mode Commands

```bash
# View current mode
/f5-mode

# Switch mode
/f5-mode research
/f5-mode design
/f5-mode development

# View mode details
/f5-mode show development

# List all modes
/f5-mode list
```

### Mode Auto-Detection

Claude auto-detects mode based on context:

| Context | Detected Mode |
|---------|---------------|
| Asking questions about tech/libraries | research |
| Discussing architecture/planning | design |
| Writing/editing code files | development |
| Test files or coverage requests | testing |
| PR review or code quality | review |
| Deploy/release discussion | deployment |
| Error investigation | debugging |

### Mode + Quality Gate Integration

| Mode | Related Gates |
|------|---------------|
| research | D1 (Research Complete) |
| design | D2-D4 (Design Gates) |
| development | G2 (Implementation Ready) |
| testing | G3 (Testing Complete) |
| deployment | G4 (Deployment Ready) |

### Mode Configuration

```json
// .f5/config.json
{
  "modes": {
    "default": "development",
    "autoDetect": true,
    "strictModeRequired": ["development"],
    "customModes": {
      "security-audit": {
        "base": "review",
        "priorities": ["OWASP", "CVE scanning"]
      }
    }
  }
}
```

## Tech Stack Modules

### What are Modules?

Modules provide domain-specific knowledge:
- **Tech Modules**: Framework patterns, best practices
- **Domain Modules**: Business logic, regulations

### Tech Module Categories

| Category | Modules |
|----------|---------|
| Backend | nestjs, go, spring, fastapi, express, django |
| Frontend | react, vue, angular, nextjs, nuxt, svelte |
| Mobile | flutter, react-native, swift, kotlin |
| Database | postgresql, mysql, mongodb, redis |
| Infrastructure | kubernetes, docker, terraform, aws |

### Domain Modules

| Domain | Sub-domains |
|--------|-------------|
| fintech | stock-trading, p2p-lending, payment, banking |
| e-commerce | b2c-retail, marketplace, subscription |
| healthcare | ehr, telemedicine, pharmacy |
| logistics | warehouse, fleet, last-mile |
| education | lms, assessment, certification |
| saas | multi-tenant, billing, analytics |

### Module Commands

```bash
# View active modules
/f5-module

# List all available
/f5-module list

# Show module details
/f5-module show nestjs
/f5-module show fintech/stock-trading

# Activate module
/f5-module activate go

# Deactivate module
/f5-module deactivate spring

# Auto-detect from project
/f5-module detect
```

### What Modules Provide

**Tech Modules:**
```yaml
patterns:
  - Project structure conventions
  - Code organization patterns
  - Common implementations

best_practices:
  - Security guidelines
  - Performance optimization
  - Error handling

anti_patterns:
  - Common mistakes
  - Security vulnerabilities
  - Performance pitfalls
```

**Domain Modules:**
```yaml
business_rules:
  - Industry-specific logic
  - Validation requirements
  - Calculation formulas

regulations:
  - Compliance requirements
  - Data handling rules
  - Audit requirements
```

### Module Configuration

```json
// .f5/config.json
{
  "stack": {
    "backend": ["nestjs"],
    "frontend": "react",
    "database": ["postgresql"],
    "cache": "redis"
  },
  "domain": {
    "name": "fintech",
    "subDomain": "stock-trading"
  },
  "modules": {
    "active": ["nestjs", "react", "postgresql", "fintech"],
    "customPaths": {
      "internal-api": "./modules/internal-api.yaml"
    }
  }
}
```

## Knowledge Skills

### What are Skills?

Skills are knowledge packages that enhance capabilities:
- Pre-built expertise
- Reusable across projects
- Shareable with team

### Skill Types

| Type | Description | Example |
|------|-------------|---------|
| technical | Framework/tool expertise | api-design |
| domain | Business knowledge | fintech-compliance |
| process | Workflow methodologies | agile-scrum |
| security | Security practices | owasp-top10 |

### Skill Commands

```bash
# List installed skills
/f5-skill

# List all available
/f5-skill list

# Show skill details
/f5-skill show api-design

# Install skill
/f5-skill install performance-tuning

# Create custom skill
/f5-skill create my-standards

# Remove skill
/f5-skill remove old-skill

# Export for sharing
/f5-skill export my-standards
```

### Skill Structure

```
.claude/skills/
├── api-design/
│   ├── skill.yaml          # Metadata
│   ├── knowledge.md        # Content
│   ├── patterns/           # Code patterns
│   └── examples/           # Examples
└── testing-strategy/
    ├── skill.yaml
    └── knowledge.md
```

### Creating Custom Skills

**Step 1: Create skill structure**
```bash
/f5-skill create my-api-standards
```

**Step 2: Edit skill.yaml**
```yaml
name: my-api-standards
type: technical
version: 1.0.0

description: |
  Internal API standards for our organization.

provides:
  - API naming conventions
  - Authentication patterns
  - Error response format

keywords:
  - api
  - rest
  - standards
```

**Step 3: Add knowledge content**
```markdown
# My API Standards

## Endpoint Naming
- Use plural nouns: `/users`, `/orders`
- Use kebab-case: `/user-profiles`

## Response Format
{
  "data": {},
  "meta": { "requestId": "uuid" }
}
```

### Built-in Skills

| Skill | Description |
|-------|-------------|
| api-design | REST/GraphQL API patterns |
| testing-strategy | Comprehensive testing |
| security-basics | Essential security |
| code-review | Review checklist |
| git-workflow | Git best practices |
| performance-tuning | Optimization techniques |

## Configuration Sync

### What is Sync?

Sync keeps CLAUDE.md updated with:
- Active modules
- Installed skills
- Mode settings
- Quality gate status
- Project rules

### Sync Commands

```bash
# Run sync
/f5-sync

# Preview changes
/f5-sync --preview

# Sync specific section
/f5-sync --section skills

# Full regeneration
/f5-sync --full
```

### What Gets Synced

| Source | Target | Content |
|--------|--------|---------|
| `.f5/config.json` | CLAUDE.md | Project settings |
| `.claude/skills/*` | CLAUDE.md | Skill references |
| `.f5/quality/gates-status.yaml` | CLAUDE.md | Gate status |
| `.f5/memory/constitution.md` | CLAUDE.md | Project rules |

### Auto-Sync Triggers

Configure automatic sync:

```json
// .f5/config.json
{
  "sync": {
    "auto": true,
    "triggers": [
      "config-change",
      "skill-install",
      "gate-update"
    ]
  }
}
```

### Preserving Custom Instructions

Custom instructions survive sync:

```markdown
<!-- .claude/custom-instructions.md -->
## Custom Team Instructions

These are preserved during /f5-sync --full

### Code Style
- Use 2-space indentation
- Prefer functional components
```

## Integration Examples

### Mode + Module + Skill

```
Mode: development
  ↓
Modules: nestjs, postgresql
  ↓
Skills: api-design, security-basics
  ↓
Claude applies:
  • NestJS patterns
  • PostgreSQL optimization
  • API design standards
  • Security best practices
```

### Research to Implementation Flow

```
1. /f5-mode research
   → Gather information
   → Use tavily, context7

2. /f5-mode design
   → Plan architecture
   → Document decisions

3. /f5-mode development
   → Implement code
   → Follow strict mode

4. /f5-mode testing
   → Write tests
   → Validate coverage
```

### Module + Domain Context

```
Domain: fintech/stock-trading
Modules: nestjs, postgresql, redis

Claude applies:
  • Trading system patterns
  • Financial regulations
  • Real-time data handling
  • Audit requirements
```

## Best Practices

### Mode Management

1. **Let Auto-Detection Work**
   Most of the time, auto-detection is accurate

2. **Explicit Mode for Specific Workflows**
   Set mode explicitly when starting specific phases

3. **Mode + Gate Alignment**
   Ensure mode matches quality gate focus

### Module Selection

1. **Match Your Stack**
   Only activate modules you're actually using

2. **Domain Context**
   Always activate domain module for business context

3. **Auto-Detect First**
   Run `/f5-module detect` when starting

### Skill Usage

1. **Start with Built-in**
   Use built-in skills before creating custom

2. **Team Standards**
   Create custom skills for team conventions

3. **Share and Reuse**
   Export skills for use across projects

### Sync Strategy

1. **Preview First**
   Always `/f5-sync --preview` before applying

2. **Auto-Sync Enabled**
   Keep auto-sync on for consistency

3. **Preserve Custom**
   Put custom instructions in separate file

## Troubleshooting

### "Mode not changing"

```bash
# Force mode change
/f5-mode development --force

# Check auto-detect status
/f5-mode --debug
```

### "Module not found"

```bash
# List available modules
/f5-module list

# Check spelling
/f5-module show <exact-name>

# Search modules
/f5-module search <keyword>
```

### "Skill not activating"

```bash
# Verify installation
/f5-skill show <name>

# Check activation settings
# In skill.yaml: activation.auto: true
```

### "Sync conflicts"

```bash
# Resolve conflicts
/f5-sync --resolve

# Or full regeneration
/f5-sync --full
```

## Configuration Reference

### Mode Configuration

```json
{
  "modes": {
    "default": "development",
    "autoDetect": true,
    "strictModeRequired": ["development"],
    "customModes": {}
  }
}
```

### Module Configuration

```json
{
  "stack": {
    "backend": ["nestjs"],
    "frontend": "react",
    "database": ["postgresql"]
  },
  "domain": {
    "name": "fintech",
    "subDomain": "stock-trading"
  },
  "modules": {
    "active": [],
    "customPaths": {}
  }
}
```

### Skill Configuration

```json
{
  "skills": {
    "installed": ["api-design"],
    "autoActivate": true,
    "globalPath": "~/.claude/skills",
    "registry": "https://f5.dev/skills"
  }
}
```

### Sync Configuration

```json
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

*F5 Framework - Context & Configuration Guide v2.0*
