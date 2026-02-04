---
description: "[DEPRECATED] Use /f5-status doctor"
argument-hint: "[redirects to /f5-status doctor]"
---

# ⚠️ DEPRECATED: /f5-doctor

This command has been consolidated into `/f5-status doctor`.

## Migration

```bash
# Old (deprecated)
/f5-doctor
/f5-doctor --verbose
/f5-doctor --fix

# New (use this instead)
/f5-status doctor
/f5-status doctor --verbose
/f5-status doctor --fix
```

## Automatic Redirect

Executing `/f5-status doctor $ARGUMENTS`...
