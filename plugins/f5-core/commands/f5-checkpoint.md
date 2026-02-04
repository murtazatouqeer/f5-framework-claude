---
description: "[DEPRECATED] Use /f5-ctx checkpoint"
argument-hint: "[redirects to /f5-ctx]"
---

# ⚠️ DEPRECATED: /f5-checkpoint

This command has been consolidated into `/f5-ctx`.

## Migration

```bash
# Old (deprecated)
/f5-checkpoint save
/f5-checkpoint save pre-refactor
/f5-checkpoint list
/f5-checkpoint restore my-checkpoint
/f5-checkpoint compare cp1 cp2
/f5-checkpoint delete old-checkpoint
/f5-checkpoint clean --keep 5

# New (use this instead)
/f5-ctx save
/f5-ctx checkpoint pre-refactor
/f5-ctx list --checkpoints
/f5-ctx restore my-checkpoint
/f5-ctx compare cp1 cp2
/f5-ctx delete old-checkpoint
/f5-ctx clean --keep 5
```

## Automatic Redirect

Executing `/f5-ctx checkpoint $ARGUMENTS`...
