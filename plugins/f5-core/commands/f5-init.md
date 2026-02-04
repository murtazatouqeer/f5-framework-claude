---
name: f5-init
description: Initialize F5 Framework in current workspace - copies configs from plugin to workspace
arguments:
  - name: force
    description: Force overwrite existing .f5/ directory
    required: false
    default: "false"
---

# F5 Framework Initialization

Initialize the F5 Framework in the current workspace.

## What This Command Does

1. **Copies Framework Configs** from plugin cache to workspace `.f5/` directory:
   - `manifest.yaml` - Framework version and component tracking
   - `config/` - Agent configs, gate definitions, session management
   - `gates/` - Quality gate templates
   - `schemas/` - YAML validation schemas
   - `templates/` - Project templates
   - `tdd/` - TDD configuration
   - `selftest/` - Self-test definitions
   - `ci/` - CI integration scripts

2. **Creates Workspace Structure**:
   ```
   .f5/
   ├── manifest.yaml
   ├── config/
   ├── gates/
   ├── schemas/
   ├── templates/
   ├── tdd/
   ├── selftest/
   └── ci/
   ```

3. **Initializes Team Config** (if not exists):
   - Creates `.f5/team/team.yaml` template

## Usage

```bash
# Standard initialization
/f5-init

# Force re-initialization (overwrites existing)
/f5-init force=true
```

## Post-Initialization

After running `/f5-init`:

1. Review `.f5/config/` settings
2. Customize gate definitions in `.f5/gates/` if needed
3. Configure team settings in `.f5/team/team.yaml`
4. Run `/f5-status` to verify setup

## Notes

- Existing workspace `.f5/` will NOT be overwritten unless `force=true`
- Plugin configs are the "factory defaults" - customize workspace copies as needed
