# F5 Workflow Integration

## Overview

This system connects Phase 1-6 features with workflows so that:
- Correct mode activates for each phase
- Correct persona activates for each phase
- Relevant agents are suggested
- Appropriate commands are recommended

## How It Works

```
User enters workflow phase
        │
        ▼
┌───────────────────┐
│ Phase Detection   │
│ (from workflow)   │
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│ Standard Phase    │
│ Mapping           │
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│ Feature Lookup    │
│ (phase-mapping)   │
└────────┬──────────┘
         │
         ├──► Mode activation
         ├──► Persona activation
         ├──► Agent suggestions
         ├──► Command suggestions
         └──► Checklist additions
```

## Architecture

### Files

| File | Purpose |
|------|---------|
| `phase-mapping.yaml` | Maps phases to features (mode, persona, agents, commands) |
| `auto-activation.yaml` | Configures automatic feature activation |
| `guided-commands.yaml` | Context-aware command suggestions |
| `onboarding.yaml` | First-time user experience |

### Standard Phases

All workflows map to these standard phases:

| Phase | Description | Gates |
|-------|-------------|-------|
| Discovery | Research, requirements gathering | D1 |
| Analysis | SRS, specifications | D2 |
| Design | Architecture, database, API design | D3, D4 |
| Implementation | Coding, building features | G2 |
| Testing | QA, testing, security audit | G3 |
| Deployment | Release, monitoring | G4 |
| Maintenance | Bug fixes, minor updates | G2, G3 |

### Phase → Feature Mapping

Each phase has recommended:

- **Mode**: Behavioral mode (analytical, coding, debugging, etc.)
- **Persona**: Specialized expertise (architect, backend, qa, etc.)
- **Agents**: AI agents for specific tasks
- **Verbosity**: Output detail level (1-5)
- **Commands**: Phase-specific commands

## Usage

### Automatic (Recommended)

When you run `/f5-workflow status` or `/f5-workflow help`, the system automatically:
1. Detects current phase
2. Shows recommended features
3. Suggests next commands

### Manual Override

You can always override:
```bash
/f5-mode set security     # Override mode
/f5-persona frontend      # Override persona
```

### View Current Mapping

```bash
# See what's recommended for current phase
/f5-workflow help

# See all phase mappings
/f5-suggest
```

## Customization

Edit `.f5/workflow-integration/phase-mapping.yaml` to:
- Change recommended features per phase
- Add custom phases
- Modify context overrides
- Add new workflow mappings

### Example: Add New Workflow

```yaml
workflow_mappings:
  my_custom_workflow:
    description: "My custom workflow"
    phases:
      - { name: "Start", standard: "discovery" }
      - { name: "Build", standard: "implementation" }
      - { name: "Ship", standard: "deployment" }
```

### Example: Override Phase Feature

```yaml
phase_features:
  implementation:
    mode:
      recommended: "security"  # Changed from "coding"
      reason: "Security-first development"
```

## Context Detection

The system can detect context from:

### File Patterns

| Pattern | Persona | Mode |
|---------|---------|------|
| `*.guard.ts` | security | security |
| `*.spec.ts` | qa | debugging |
| `*.migration.ts` | database | - |
| `Dockerfile` | devops | - |

### Keywords in Messages

| Keywords | Override |
|----------|----------|
| auth, password, security | security mode + persona |
| slow, optimize, performance | performance mode |
| bug, error, fix | debugging mode |
| test, coverage | qa persona |

## Integration Points

### With Modes

Phase determines recommended mode:
- Discovery/Analysis → `analytical`
- Design → `planning`
- Implementation → `coding`
- Testing → `debugging`

### With Personas

Phase determines recommended persona:
- Discovery/Analysis → `analyst`
- Design → `architect`
- Implementation → `backend`/`frontend`
- Testing → `qa`

### With Agents

Phase suggests relevant agents:
- Analysis → `documenter`
- Design → `api_designer`, `documenter`
- Implementation → `code_generator`, `test_writer`
- Testing → `security_scanner`, `performance_analyzer`

### With Commands

Phase shows relevant commands:
- Essential: Must-use commands
- Recommended: Better results
- Advanced: Power user

## Best Practices

1. **Let auto-activation work**: Trust the recommended settings
2. **Override when needed**: Manual settings persist until phase change
3. **Use /f5-suggest**: Get context-aware suggestions
4. **Create checkpoints**: Save progress at phase transitions
5. **Follow the checklist**: Each phase has checklist additions

## Troubleshooting

### Auto-activation not working?

```bash
# Check if enabled
cat .f5/workflow-integration/auto-activation.yaml

# Verify workflow loaded
/f5-workflow status
```

### Wrong mode activated?

```bash
# Override manually
/f5-mode set <desired-mode>

# Check context overrides
cat .f5/workflow-integration/phase-mapping.yaml | grep context_overrides
```

### Commands not suggested?

```bash
# Get explicit suggestions
/f5-suggest

# Check current phase
/f5-workflow status
```

## Related Documentation

- [Mode System](../modes/README.md)
- [Persona System](../personas/README.md)
- [Agent System](../agents/README.md)
- [Verbosity System](../verbosity-integration.yaml)
