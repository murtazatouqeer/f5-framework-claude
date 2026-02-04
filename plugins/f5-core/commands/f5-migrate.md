---
description: Migrate legacy code or data
argument-hint: <source> [--strategy <s>]
---

# /f5-migrate - Structure Migration

Migrate F5 project structure between versions.

## ARGUMENTS
The user's request is: $ARGUMENTS

## PURPOSE

Migrate handles:
- Version upgrades (v1.x → v2.x)
- Structure reorganization
- Configuration format changes
- Breaking changes adaptation

## MIGRATION TYPES

| Type | Description | Example |
|------|-------------|---------|
| `version` | Framework version upgrade | v1.2 → v2.0 |
| `structure` | Directory reorganization | .claude/f5/ → .f5/ |
| `config` | Configuration format | YAML → JSON |
| `commands` | Slash command updates | New command format |

## ACTIONS

### Check Migration Status

```
/f5-migrate status

Output:
📊 Migration Status

Current Version: 1.2.0
Latest Version: 2.0.0

Available Migrations:
  1.2.0 → 1.3.0    Minor updates, config additions
  1.3.0 → 2.0.0    Major restructure (BREAKING)

Breaking Changes in 2.0.0:
  • .claude/f5/ moved to .f5/
  • config.yaml replaced with config.json
  • New quality gates structure
  • Updated command format

Run /f5-migrate plan for detailed migration plan.
```

### Create Migration Plan

```
/f5-migrate plan

Output:
📋 Migration Plan: 1.2.0 → 2.0.0

PHASE 1: Backup
  □ Create backup of .claude/f5/
  □ Export current configuration
  □ Save memory files

PHASE 2: Structure Migration
  □ Create .f5/ directory
  □ Move config files
  □ Migrate memory system
  □ Update file references

PHASE 3: Configuration Migration
  □ Convert config.yaml to config.json
  □ Update schema to v2.0
  □ Migrate custom settings

PHASE 4: Command Updates
  □ Update slash command references
  □ Migrate custom commands
  □ Update CLAUDE.md

PHASE 5: Validation
  □ Verify all files migrated
  □ Test configuration loading
  □ Validate gate status

Estimated changes:
  Files moved: 15
  Files updated: 8
  New files: 5

Run /f5-migrate execute to start migration.
```

### Execute Migration

```
/f5-migrate execute

Output:
🚀 Starting Migration: 1.2.0 → 2.0.0

[Phase 1: Backup]
  ✓ Created backup at .f5-backup-20240115/
  ✓ Exported configuration
  ✓ Saved 4 memory files

[Phase 2: Structure Migration]
  ✓ Created .f5/ directory
  ✓ Moved config files (3 files)
  ✓ Migrated memory system (4 files)
  ✓ Updated file references

[Phase 3: Configuration Migration]
  ✓ Converted config.yaml to config.json
  ✓ Updated schema to v2.0
  ✓ Preserved custom settings

[Phase 4: Command Updates]
  ✓ Updated 12 slash command references
  ✓ Migrated 2 custom commands
  ✓ Regenerated CLAUDE.md

[Phase 5: Validation]
  ✓ All 15 files migrated successfully
  ✓ Configuration loads correctly
  ✓ Gate status preserved

═══════════════════════════════════════════════════════════
✓ Migration completed successfully!

New version: 2.0.0
Backup location: .f5-backup-20240115/

Next steps:
1. Review migrated files
2. Run /f5-status to verify
3. Delete backup when satisfied
═══════════════════════════════════════════════════════════
```

### Rollback Migration

```
/f5-migrate rollback

Output:
⏪ Rolling back migration

Available backups:
  1. .f5-backup-20240115/ (2.0.0 → 1.2.0)
  2. .f5-backup-20240110/ (1.1.0 → 1.2.0)

Select backup [1]:

Rolling back to 1.2.0...
  ✓ Restored .claude/f5/ directory
  ✓ Restored config.yaml
  ✓ Restored memory files
  ✓ Reverted CLAUDE.md

✓ Rollback complete. Version: 1.2.0
```

### Dry Run

```
/f5-migrate execute --dry-run

Output:
🔍 Dry Run: Migration 1.2.0 → 2.0.0

Would perform the following changes:

FILES TO CREATE:
  + .f5/config.json
  + .f5/quality/gates-status.yaml
  + .f5/memory/session.md

FILES TO MOVE:
  .claude/f5/config.yaml → .f5/config.json (converted)
  .claude/f5/memory/* → .f5/memory/*
  .claude/f5/quality/* → .f5/quality/*

FILES TO UPDATE:
  ~ CLAUDE.md (regenerate with new paths)
  ~ .claude/commands/*.md (update references)

FILES TO DELETE:
  - .claude/f5/ (after migration)

No changes applied (dry run mode).
```

## VERSION-SPECIFIC MIGRATIONS

### v1.x → v2.0 Migration

```yaml
breaking_changes:
  - directory: ".claude/f5/ → .f5/"
  - config: "YAML → JSON format"
  - gates: "New quality gates structure"
  - memory: "Enhanced memory system"

new_features:
  - "Session management"
  - "Quality gate checklists"
  - "Enhanced traceability"
  - "Jira integration"

migration_steps:
  1. Backup existing structure
  2. Create new directory layout
  3. Convert configuration format
  4. Migrate memory files
  5. Update all references
  6. Regenerate CLAUDE.md
```

### v2.0 → v2.1 Migration (Minor)

```yaml
changes:
  - "New skill system"
  - "Enhanced module support"
  - "MCP server management"

migration_steps:
  1. Add skills directory
  2. Update config schema
  3. Migrate custom modules
```

## CONFIGURATION MIGRATION

### YAML to JSON Conversion

**Before (config.yaml):**
```yaml
version: "1.2.0"
name: "my-project"
architecture: "microservices"
stack:
  backend:
    - nestjs
  frontend: react
  database:
    - postgresql
```

**After (config.json):**
```json
{
  "version": "2.0.0",
  "name": "my-project",
  "architecture": "microservices",
  "stack": {
    "backend": ["nestjs"],
    "frontend": "react",
    "database": ["postgresql"]
  }
}
```

## CUSTOM MIGRATION SCRIPTS

Create custom migrations for project-specific needs:

```javascript
// .f5/migrations/custom-001.js
module.exports = {
  name: 'custom-001',
  description: 'Migrate legacy auth config',

  async up(context) {
    // Migration logic
    const oldConfig = await context.readFile('auth.yaml');
    const newConfig = transformConfig(oldConfig);
    await context.writeFile('auth.json', newConfig);
  },

  async down(context) {
    // Rollback logic
    const backup = await context.readBackup('auth.yaml');
    await context.restoreFile('auth.yaml', backup);
  }
};
```

### Run Custom Migration

```
/f5-migrate custom custom-001

Output:
🔧 Running Custom Migration: custom-001

Description: Migrate legacy auth config

Executing...
  ✓ Read auth.yaml
  ✓ Transformed configuration
  ✓ Written auth.json

✓ Custom migration completed
```

## EXAMPLES

```bash
# Check migration status
/f5-migrate status

# View migration plan
/f5-migrate plan

# Dry run (preview changes)
/f5-migrate execute --dry-run

# Execute migration
/f5-migrate execute

# Execute with auto-confirm
/f5-migrate execute --yes

# Rollback to previous version
/f5-migrate rollback

# Rollback to specific backup
/f5-migrate rollback .f5-backup-20240110/

# Run custom migration
/f5-migrate custom custom-001

# Validate current structure
/f5-migrate validate

# Clean up old backups
/f5-migrate cleanup --keep 3
```

## VALIDATION

### Pre-Migration Checks

```
/f5-migrate validate --pre

Output:
🔍 Pre-Migration Validation

Checking current structure...
  ✓ .claude/f5/ exists
  ✓ config.yaml valid
  ✓ Memory files intact
  ✓ No uncommitted changes

Checking migration requirements...
  ✓ Node.js version OK
  ✓ Disk space sufficient
  ✓ Backup location writable

✓ Ready for migration
```

### Post-Migration Checks

```
/f5-migrate validate --post

Output:
🔍 Post-Migration Validation

Checking new structure...
  ✓ .f5/ directory exists
  ✓ config.json valid and loads
  ✓ Memory files migrated (4/4)
  ✓ Quality gates preserved

Checking functionality...
  ✓ /f5-status works
  ✓ /f5-load works
  ✓ Gate status correct

✓ Migration validated successfully
```

## TROUBLESHOOTING

### Migration Failed

```
/f5-migrate recover

Attempts to recover from failed migration:
1. Identifies failure point
2. Restores from partial backup
3. Cleans up incomplete changes
```

### Incompatible Version

```
Error: Cannot migrate directly from 1.0.0 to 2.0.0

Solution:
  /f5-migrate execute --version 1.2.0
  /f5-migrate execute --version 2.0.0

Sequential migration through intermediate versions.
```

### Manual Fix Required

```
Warning: Manual intervention required

The following items need manual attention:
  • Custom command: /project-deploy
    - Update path references manually
  • External integration: jira-webhook
    - Update API endpoint configuration

After fixing, run:
  /f5-migrate continue
```

## INTEGRATION

### With Version Control

```
# Before migration
git add -A && git commit -m "Pre-migration checkpoint"

# After migration
/f5-migrate execute
git add -A && git commit -m "Migrate F5 to v2.0.0"
```

### With CI/CD

```yaml
# .github/workflows/f5-migrate.yml
- name: Check F5 Migration
  run: |
    f5 migrate status
    if [ $? -eq 1 ]; then
      echo "Migration available"
      f5 migrate execute --yes
    fi
```

---

**Tip:** Always run `/f5-migrate execute --dry-run` first to preview changes before executing the actual migration!
