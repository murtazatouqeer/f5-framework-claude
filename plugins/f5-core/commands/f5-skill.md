---
description: Manage F5 skills and capabilities
argument-hint: <list|load|create|run> [skill-name]
---

# /f5-skill - Knowledge Skill Management

List, install, and create knowledge skills for specialized capabilities.

## ARGUMENTS
The user's request is: $ARGUMENTS

## PURPOSE

Skills are knowledge packages that enhance Claude's capabilities:
- Pre-built expertise in specific domains
- Reusable across projects
- Shareable with team members
- **Anthropic-aligned format** with progressive loading

## SKILL TYPES

| Type | Description | Example |
|------|-------------|---------|
| `stacks` | Framework/stack expertise | nestjs, fastapi, react |
| `core` | Framework-agnostic skills | tdd, security, api-design |
| `domain` | Business domain knowledge | fintech, healthcare, agriculture |

## SKILL STRUCTURE (Anthropic-Aligned Format)

```
skills/
├── stacks/                    # Stack-specific skills
│   └── nestjs/
│       ├── SKILL.md          # REQUIRED - Main entry with frontmatter triggers
│       ├── scripts/          # OPTIONAL - Executable automation
│       │   ├── scaffold.py   # Module scaffolding
│       │   ├── generate.py   # Component generation
│       │   └── test.py       # Test runner
│       ├── references/       # OPTIONAL - Detailed docs (on-demand)
│       │   ├── architecture.md
│       │   ├── security.md
│       │   ├── database.md
│       │   ├── testing.md
│       │   └── performance.md
│       └── assets/           # OPTIONAL - Templates, configs
│           └── templates/
├── core/                      # Framework-agnostic skills
│   ├── tdd/
│   │   └── SKILL.md
│   └── security/
│       └── SKILL.md
└── domains/                   # Domain-specific skills
    └── fintech/
        └── SKILL.md
```

## SKILL.MD FORMAT (Critical for Triggering)

The SKILL.md frontmatter is the **trigger mechanism**. Claude reads the description
to decide when to activate the skill.

```yaml
---
name: nestjs
version: "2.0.0"
description: |
  NestJS TypeScript backend development with enterprise patterns...

  Use this skill when: (1) Project has @nestjs/core in package.json,
  (2) Creating modules, controllers, services, guards,
  (3) Implementing JWT authentication...

  Auto-detects: nest-cli.json, *.module.ts, *.controller.ts, @nestjs/* packages.

  NOT for: Pure Express.js without NestJS, frontend React/Vue code.
---

# NestJS Development Skill

## Quick Reference
[Essential commands and patterns]

## When to Load Additional Resources
- **Complex architecture**: Read `references/architecture.md`
- **Security setup**: Read `references/security.md`

## Core Patterns
[Code examples with explanations]

## Scripts Reference
| Script | Usage | Description |
|--------|-------|-------------|
| `scaffold.py` | `scaffold.py user --crud` | Create module |
```

## PROGRESSIVE LOADING LEVELS

### Level 1: Metadata (~100 tokens) - Always in Context
The frontmatter is always available for Claude to decide when to activate.

### Level 2: SKILL.md Body (~2000-5000 tokens) - On Activation
When skill triggers, Claude loads the SKILL.md body with core patterns.

### Level 3: References & Scripts (variable) - On Demand
When detailed info needed, Claude reads from references/ directory.

## ACTIONS

### List Installed Skills

```
/f5-skill

Output:
🎯 Installed Skills

PROJECT SKILLS (.claude/skills/):
  ✓ api-design         Technical    v1.0.0
  ✓ testing-strategy   Process      v1.2.0
  ✓ security-basics    Security     v1.0.0

GLOBAL SKILLS (~/.claude/skills/):
  ✓ code-review        Process      v2.0.0
  ✓ git-workflow       Process      v1.5.0

Total: 5 skills active
```

### List Available Skills

```
/f5-skill list

Output:
📋 Available Skills

INSTALLED:
  ✓ api-design         Technical expertise for REST/GraphQL APIs
  ✓ testing-strategy   Comprehensive testing approaches
  ✓ security-basics    Essential security practices

AVAILABLE TO INSTALL:
  ○ performance-tuning Optimization techniques
  ○ database-design    Schema and query optimization
  ○ ci-cd-pipeline     Deployment automation
  ○ documentation      Technical writing best practices
  ○ accessibility      WCAG compliance guidance

Install with: /f5-skill install <name>
```

### Show Skill Details

```
/f5-skill show api-design

Output:
🎯 Skill: api-design

Type: Technical
Version: 1.0.0
Author: F5 Framework

Description:
REST and GraphQL API design best practices including
endpoint naming, versioning, error handling, and documentation.

Provides:
• REST endpoint naming conventions
• HTTP status code usage
• Error response formatting
• Pagination patterns
• Versioning strategies
• OpenAPI documentation

Files:
  knowledge.md      - Core knowledge (2.5KB)
  patterns/         - 3 pattern files
  examples/         - 2 example files

Dependencies:
  - security-basics (recommended)

Usage:
  Claude automatically applies this knowledge when
  designing or reviewing API endpoints.
```

### Install Skill

```
/f5-skill install performance-tuning

Output:
📥 Installing: performance-tuning

Downloading from F5 skill registry...
✓ Downloaded skill package
✓ Validated skill structure
✓ Installed to .claude/skills/performance-tuning/

Skill Contents:
  knowledge.md    - Performance optimization guide
  patterns/       - 5 optimization patterns
  checklists/     - Performance review checklist

✓ Skill installed successfully!

💡 Claude will now apply performance-tuning knowledge
   when relevant to your tasks.
```

### Create Custom Skill

```
/f5-skill create my-api-standards

Output:
🆕 Creating skill: my-api-standards

Created directory structure:
  .claude/skills/my-api-standards/
  ├── skill.yaml      # Edit metadata
  ├── knowledge.md    # Add your knowledge
  └── patterns/       # Add code patterns

Next steps:
1. Edit skill.yaml with metadata
2. Add knowledge content to knowledge.md
3. Add patterns to patterns/ directory

Template created at:
  .claude/skills/my-api-standards/skill.yaml
```

### Skill Template

```yaml
# .claude/skills/my-api-standards/skill.yaml
name: my-api-standards
type: technical
version: 1.0.0
author: Your Team

description: |
  Internal API standards and conventions for our organization.

provides:
  - API naming conventions
  - Authentication patterns
  - Error response format
  - Rate limiting standards

keywords:
  - api
  - rest
  - standards
  - internal

dependencies: []

activation:
  auto: true
  triggers:
    - "api"
    - "endpoint"
    - "rest"
```

### Knowledge File Format

```markdown
# My API Standards

## Overview
Our internal API design standards...

## Endpoint Naming
- Use plural nouns: `/users`, `/orders`
- Use kebab-case: `/user-profiles`
- Version prefix: `/api/v1/`

## Response Format
```json
{
  "data": {},
  "meta": {
    "requestId": "uuid",
    "timestamp": "ISO8601"
  }
}
```

## Error Handling
All errors follow this format:
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Human readable message",
    "details": []
  }
}
```
```

### Update Skill

```
/f5-skill update api-design

Output:
🔄 Updating: api-design

Current version: 1.1.0
Latest version: 1.2.0

Changes:
  + Added GraphQL patterns
  + Updated error handling examples
  ~ Improved pagination documentation

Update? [Y/n]

✓ Skill updated to v1.2.0
```

### Remove Skill

```
/f5-skill remove performance-tuning

Output:
🗑️ Removing: performance-tuning

This will remove:
  .claude/skills/performance-tuning/

Confirm removal? [y/N]

✓ Skill removed
```

### Export Skill

```
/f5-skill export my-api-standards

Output:
📤 Exporting: my-api-standards

Creating package...
✓ Validated skill structure
✓ Created archive

Exported to:
  ./my-api-standards-v1.0.0.skill.tar.gz

Share this file to distribute your skill.
```

### Import Skill

```
/f5-skill import ./shared-skill.tar.gz

Output:
📥 Importing skill package...

Package contents:
  Name: shared-skill
  Version: 1.0.0
  Files: 5

Install to project? [Y/n]

✓ Skill imported to .claude/skills/shared-skill/
```

### Run Skill Script

Execute automation scripts bundled with skills:

```
/f5-skill run nestjs scaffold user --crud

Output:
🚀 Running: skills/stacks/nestjs/scripts/scaffold.py user --crud

============================================================
NestJS Module Scaffolder
============================================================
Module: user
Options: crud
Output: src/modules/user
============================================================

  Created: src/modules/user/user.module.ts
  Created: src/modules/user/user.controller.ts
  Created: src/modules/user/user.service.ts
  Created: src/modules/user/user.repository.ts
  Created: src/modules/user/dto/create-user.dto.ts
  Created: src/modules/user/dto/update-user.dto.ts
  Created: src/modules/user/entities/user.entity.ts
  Created: src/modules/user/__tests__/user.service.spec.ts
  Created: src/modules/user/__tests__/user.controller.spec.ts

============================================================
✓ Successfully created 9 files!
============================================================
```

Available script commands:
```bash
# NestJS scaffolding
/f5-skill run nestjs scaffold <name> [--crud] [--auth] [--swagger]

# NestJS component generation
/f5-skill run nestjs generate controller user
/f5-skill run nestjs generate service user --repository
/f5-skill run nestjs generate dto create-user --swagger
/f5-skill run nestjs generate guard roles
/f5-skill run nestjs generate interceptor logging

# NestJS testing
/f5-skill run nestjs test --coverage --threshold 80
/f5-skill run nestjs test --e2e
/f5-skill run nestjs test --module user
```

### Load Skill Reference

Load detailed documentation on-demand:

```
/f5-skill ref nestjs security

Output:
📚 Loading: skills/stacks/nestjs/references/security.md

# NestJS Security Patterns

[Detailed security documentation loaded into context]
```

Available references for nestjs:
- `architecture` - Clean architecture, DDD, CQRS patterns
- `security` - Authentication, authorization, guards
- `database` - TypeORM, Prisma, repository patterns
- `testing` - Unit tests, E2E tests, mocking strategies
- `performance` - Caching, queues, microservices

## SKILL USAGE

### Automatic Activation (Anthropic Pattern)

Skills activate automatically based on the **description field** in SKILL.md:
1. Claude scans skill metadata (frontmatter)
2. Matches trigger conditions against current context
3. Loads full SKILL.md body when activated
4. Loads references on-demand when needed

### Trigger Detection Examples

| Context | Triggers Skill | Reason |
|---------|---------------|--------|
| `package.json` has `@nestjs/core` | nestjs | Auto-detect pattern |
| User asks "create a module" | nestjs | "Use this skill when" match |
| Editing `*.controller.ts` | nestjs | File pattern match |
| User asks "implement JWT auth" | nestjs | Trigger keyword match |

### Manual Reference

```
@skill:nestjs
Design an endpoint for user registration

→ Claude applies nestjs skill knowledge
```

### Skill + Mode Integration

```
Mode: development
Skills: nestjs, security

→ Claude combines:
   • NestJS patterns from SKILL.md
   • Security references when auth discussed
   • Development mode behaviors
```

## BUILT-IN SKILLS

### Technical Skills

| Skill | Description |
|-------|-------------|
| `api-design` | REST/GraphQL API patterns |
| `testing-strategy` | Unit, integration, E2E testing |
| `database-design` | Schema design, optimization |
| `performance-tuning` | Optimization techniques |
| `ci-cd-pipeline` | CI/CD best practices |

### Process Skills

| Skill | Description |
|-------|-------------|
| `code-review` | Review checklist and patterns |
| `git-workflow` | Git best practices |
| `documentation` | Technical writing |
| `agile-scrum` | Agile methodologies |

### Security Skills

| Skill | Description |
|-------|-------------|
| `security-basics` | Essential security practices |
| `owasp-top10` | OWASP vulnerabilities |
| `secure-coding` | Secure coding patterns |

## EXAMPLES

```bash
# List installed skills
/f5-skill

# List all available skills
/f5-skill list

# Show skill details
/f5-skill show api-design

# Install a skill
/f5-skill install performance-tuning

# Create custom skill
/f5-skill create my-standards

# Update a skill
/f5-skill update api-design

# Remove a skill
/f5-skill remove old-skill

# Export for sharing
/f5-skill export my-standards

# Import shared skill
/f5-skill import ./shared.skill.tar.gz

# Search skills
/f5-skill search security
```

## CONFIGURATION

Skills configuration in `.f5/config.json`:

```json
{
  "skills": {
    "installed": ["api-design", "testing-strategy", "security-basics"],
    "autoActivate": true,
    "globalPath": "~/.claude/skills",
    "registry": "https://f5.dev/skills"
  }
}
```

---

**Tip:** Create custom skills for your team's standards and conventions. Share them to ensure consistency across projects!
