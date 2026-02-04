---
description: "[DEPRECATED] Use /f5-memory codebase"
argument-hint: "[redirects to /f5-memory codebase]"
---

# ⚠️ DEPRECATED: /f5-codebase

This command has been consolidated into `/f5-memory codebase`.

## Migration

```bash
# Old (deprecated)
/f5-codebase index
/f5-codebase search "authentication logic"
/f5-codebase find "user validation"
/f5-codebase similar "<code>"
/f5-codebase stats
/f5-codebase reset

# New (use this instead)
/f5-memory codebase index
/f5-memory codebase search "authentication logic"
/f5-memory codebase find "user validation"
/f5-memory codebase similar "<code>"
/f5-memory codebase stats
/f5-memory codebase reset
```

## Automatic Redirect

Executing `/f5-memory codebase $ARGUMENTS`...
