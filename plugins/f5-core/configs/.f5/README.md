# F5 Framework Configuration

This directory contains F5 Framework configuration, state, and project-specific data.

## Directory Structure

```
.f5/
├── manifest.yaml       # Framework version and metadata
│
├── config/             # Consolidated configuration files
│   ├── agents.yaml     # AI agent configuration
│   ├── automation.yaml # Auto-activation rules
│   ├── behavioral.yaml # Personas and behavioral modes
│   ├── config.yaml     # Main framework configuration
│   ├── gates.yaml      # Quality gate definitions
│   ├── mcp-profiles.yaml # MCP server profiles
│   ├── personas.yaml   # AI personas
│   └── quality.yaml    # Quality settings
│
├── gates/              # Quality gate evidence
│   ├── D1/             # Research gate
│   ├── D2/             # Requirements gate
│   ├── D3/             # Design gate
│   ├── D4/             # Detailed design gate
│   ├── G2/             # Implementation gate
│   ├── G2.5/           # Code review gate
│   ├── G3/             # Testing gate
│   └── G4/             # Deployment gate
│
├── team/               # Team collaboration
│   ├── shared/         # Shared team data (committed)
│   │   ├── decisions.yaml    # Architecture Decision Records
│   │   ├── knowledge.yaml    # Team knowledge base
│   │   ├── team-config.yaml  # Team configuration
│   │   └── handoffs/         # Task handoff records
│   │
│   ├── _templates/     # Templates for new team members
│   │   └── session.yaml
│   │
│   └── [member-id]/    # Personal folders (gitignored)
│
├── stacks/             # Technology stack configurations
│   ├── backend/        # Backend stacks (NestJS, Spring, etc.)
│   ├── frontend/       # Frontend stacks (React, Angular, etc.)
│   ├── infrastructure/ # Infra stacks (Docker, K8s, etc.)
│   ├── mobile/         # Mobile stacks (Flutter, RN)
│   └── gateway/        # API gateway stacks
│
├── requirements/       # Project requirements tracking
├── sessions/           # Session management
├── analytics/          # Project analytics
├── checkpoints/        # Session checkpoints
├── context/            # Context management
├── learning/           # Project learning data
├── schemas/            # YAML schemas
└── archive/            # Archived data
```

## Key Files

### manifest.yaml

Framework version tracking and component metadata:

```yaml
framework:
  name: "F5 Framework"
  version: "1.3.5"
  updated_at: "2025-01-27"

components:
  commands:
    version: "1.2.8"
    path: ".claude/commands"
  mcp:
    version: "1.2.6"
    path: ".mcp.json"
```

### config/gates.yaml

Quality gate definitions with checklists and evidence requirements:

```yaml
gates:
  D1:
    name: "Research Gate"
    checklist: [...]
    evidence_directory: ".f5/gates/D1"
  G2:
    name: "Implementation Gate"
    checklist: [...]
```

### team/shared/

Team collaboration data that should be committed:

- **decisions.yaml**: Architecture Decision Records (ADRs)
- **knowledge.yaml**: Team patterns, lessons learned, best practices
- **team-config.yaml**: Team member configuration
- **handoffs/**: Task handoff records between team members

## Skills and Agents

Skills and agents have been moved to `.claude/` for Claude Code 2.1.x compatibility:

| Content Type | Old Location | New Location |
|--------------|--------------|--------------|
| General Skills | `.f5/skills/` | `.claude/skills/` |
| Stack Skills | `.f5/stacks/*/skills/` | `.claude/skills/stacks/` |
| Stack Agents | `.f5/stacks/*/agents/` | `.claude/agents/stacks/` |

See `.claude/README.md` for details on the new structure.

## Stack Configuration

Each stack in `stacks/` contains:

```
stacks/{category}/{stack}/
├── module.yaml         # Stack metadata and configuration
├── templates/          # Code generation templates
├── patterns/           # Best practice patterns
└── (skills and agents moved to .claude/)
```

## Protected Paths

These paths contain generated/state data and should not be manually edited:

- `.f5/requirements/` - Requirement tracking
- `.f5/sessions/` - Session state
- `.f5/analytics/` - Analytics data
- `.f5/gates/` - Gate evidence
- `.f5/checkpoints/` - Session checkpoints
- `.f5/context/` - Context management
- `.f5/learning/` - Learning data

## Gitignore Patterns

The following are typically gitignored:

```gitignore
.f5/team/[member-id]/   # Personal team folders
.f5/cache/              # Cache files
.f5/archive/            # Archived data
.f5/sessions/*.json     # Session state
.f5/checkpoints/        # Checkpoints
```

## Commands

Use F5 commands to manage this directory:

- `/f5-load` - Load project context
- `/f5-gate` - Manage quality gates
- `/f5-team` - Team collaboration
- `/f5-status` - Project status
- `/f5-ctx` - Context management
