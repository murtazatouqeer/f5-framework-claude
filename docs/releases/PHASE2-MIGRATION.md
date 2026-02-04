# F5 Framework Phase 2: Directory Restructure

## Overview

Phase 2 reorganized the F5 Framework directory structure for:
- **Claude Code 2.1.x native compatibility**: Skills and agents use native frontmatter format
- **Better team collaboration**: Isolated personal state from shared team data
- **Cleaner separation of concerns**: Configuration, gates, and team data properly organized
- **Improved maintainability**: Consolidated YAML configs, removed redundancy

## Timeline

| Metric | Value |
|--------|-------|
| Start Date | 2025-01-27 |
| End Date | 2025-01-27 |
| Duration | 1 day |
| Start Version | 1.2.8 |
| Final Version | 1.3.6 |

## Phase Summary

| Phase | Description | Version | Key Changes |
|-------|-------------|---------|-------------|
| **2A** | Quick Wins | 1.2.9 | Deleted 18 empty dirs, 7 backup files, archived large folders |
| **2B** | Flatten .f5/ | 1.2.9 | Renamed evidence→gates, consolidated 16 YAML configs to config/ |
| **2C** | Team Isolation | 1.3.0 | Created .f5/team/ structure with shared/ and personal folders |
| **2D** | SKILL.md Format | 1.3.1 | Added Claude Code 2.1.x frontmatter to all 307 skills |
| **2E** | Skills Migration | 1.3.2 | Moved .f5/skills/ to .claude/skills/, created _core/ and _shared/ |
| **2F** | Stack Skills Migration | 1.3.3 | Moved 471 stack skills to .claude/skills/stacks/ |
| **2G** | Agents Migration | 1.3.4 | Moved 96 agents to .claude/agents/stacks/ |
| **2H** | Validation & Cleanup | 1.3.5 | Final validation, cleanup, documentation |
| **2I** | CLI Synchronization | 1.3.6 | CLI package sync, extension rename, docs update |

## Before vs After

### Directory Structure

**Before (v1.2.8):**
```
.claude/
└── commands/           # Only commands

.f5/
├── evidence/           # Quality gate evidence
├── skills/             # General skills
├── stacks/
│   └── */
│       ├── skills/     # Stack skills
│       └── agents/     # Stack agents
├── *.yaml (17 files)   # Config files at root
└── collab/             # Team collaboration
```

**After (v1.3.6):**
```
.claude/
├── commands/           # F5 slash commands
├── skills/             # ALL skills now here
│   ├── _core/          # F5 core workflow
│   ├── _shared/        # Shared patterns
│   ├── [13 categories]/ # General skills
│   └── stacks/         # Stack-specific skills
│       ├── backend/
│       ├── frontend/
│       ├── infrastructure/
│       └── mobile/
└── agents/             # ALL agents now here
    ├── stacks/         # Stack-specific agents
    └── custom/         # Project-specific agents

.f5/
├── manifest.yaml       # Only manifest at root
├── config/             # All YAML configs consolidated
├── gates/              # Renamed from evidence/
├── team/               # Team collaboration
│   ├── shared/         # Committed team data
│   └── _templates/     # Templates
└── stacks/             # Stack configs (templates, patterns only)
```

## Key Metrics

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| General skills | 307 | 307 | Moved to .claude/skills/ |
| Stack skills | 471 | 471 | Moved to .claude/skills/stacks/ |
| Agents | 96 | 96 | Moved to .claude/agents/stacks/ |
| YAML configs at .f5/ root | 17 | 1 | -16 (moved to config/) |
| Empty directories | 18 | 0 | -18 |
| evidence/ directory | 1 | 0 | Renamed to gates/ |
| Skills with frontmatter | 0 | 307 | +307 |
| Agents with frontmatter | ~50 | 96 | All updated |

## Breaking Changes

### Path Changes

| Old Path | New Path | Impact |
|----------|----------|--------|
| `.f5/evidence/` | `.f5/gates/` | All evidence references updated |
| `.f5/skills/` | `.claude/skills/` | Skills registry updated |
| `.f5/stacks/*/skills/` | `.claude/skills/stacks/` | Module.yaml paths updated |
| `.f5/stacks/*/agents/` | `.claude/agents/stacks/` | Module.yaml paths updated |
| `.f5/*.yaml` | `.f5/config/*.yaml` | Config imports updated |

### Frontmatter Requirements

All skills now require:
```yaml
---
allowed-tools: [tool list]
user-invocable: true|false
context: inject
---
```

All agents now require:
```yaml
---
type: agent
context: fork
---
```

## Backward Compatibility

- **Symlinks removed**: The temporary `.f5/skills` symlink has been removed
- **All commands updated**: References to old paths have been updated
- **All configs updated**: Module.yaml files point to new locations
- **Git tags preserved**: Each phase tagged for easy rollback

## Migration Scripts

Created during migration:

| Script | Purpose |
|--------|---------|
| `scripts/migrate-skill-frontmatter.js` | Add frontmatter to skills |
| `scripts/validate-skill-frontmatter.js` | Validate skill frontmatter |
| `scripts/generate-skill-registry.js` | Generate skills registry |
| `scripts/validate-phase2.js` | Comprehensive Phase 2 validation |

## Rollback

If needed, rollback to any phase:

```bash
# Rollback to specific phase
git reset --hard phase2a-complete  # After Quick Wins
git reset --hard phase2b-complete  # After Flatten .f5/
git reset --hard phase2c-complete  # After Team Isolation
git reset --hard phase2d-complete  # After SKILL.md Format
git reset --hard phase2e-complete  # After Skills Migration
git reset --hard phase2f-complete  # After Stack Skills Migration
git reset --hard phase2g-complete  # After Agents Migration
git reset --hard phase2h-complete  # After Validation & Cleanup
git reset --hard phase2i-complete  # After CLI Synchronization

# Or rollback to before Phase 2
git reset --hard v1.2.8
```

## Git Tags

All Phase 2 tags:

| Tag | Description |
|-----|-------------|
| `phase2a-complete` | Quick Wins done |
| `phase2b-complete` | Flatten .f5/ done |
| `phase2c-complete` | Team Isolation done |
| `phase2d-complete` | SKILL.md Format done |
| `phase2e-complete` | Skills Migration done |
| `phase2f-complete` | Stack Skills Migration done |
| `phase2g-complete` | Agents Migration done |
| `phase2h-complete` | Validation & Cleanup done |
| `phase2i-complete` | CLI Synchronization done |
| `phase2-complete` | All Phase 2 complete |
| `v1.3.6` | Final Phase 2 version |

## Validation

Run the validation script to verify migration:

```bash
node scripts/validate-phase2.js
```

This checks:
- Directory structure
- File counts
- Frontmatter validation
- Old path references
- Registry validity
- Git tags

## Next Steps

After Phase 2 is complete:

1. **Merge to develop**:
   ```bash
   git checkout develop
   git merge phase2-directory-restructure
   ```

2. **Push with tags**:
   ```bash
   git push origin develop --tags
   ```

3. **Update dependent projects**:
   - Update any external references to old paths
   - Re-run `/f5-load` in projects using F5

4. **Communicate changes**:
   - Notify team of new paths
   - Update any external documentation

## Files Changed Summary

| Phase | Files Changed |
|-------|---------------|
| 2A | ~25 |
| 2B | ~40 |
| 2C | ~15 |
| 2D | ~312 |
| 2E | ~321 |
| 2F | ~518 |
| 2G | ~125 |
| 2H | ~20 |
| 2I | ~50 |
| **Total** | **~1,426** |

## Contributors

- Claude Code (AI assistance)
- F5 Framework Team

## Related Documents

- [.claude/README.md](../.claude/README.md) - Claude Code integration guide
- [.f5/README.md](../.f5/README.md) - F5 configuration guide
- [CLAUDE.md](../CLAUDE.md) - Main framework documentation
