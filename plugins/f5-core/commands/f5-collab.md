---
description: "[DEPRECATED] Use /f5-team session"
argument-hint: "[redirects to /f5-team session]"
---

# ⚠️ DEPRECATED: /f5-collab

This command has been consolidated into `/f5-team session`.

## Migration

```bash
# Old (deprecated)
/f5-collab start
/f5-collab join sess_123
/f5-collab leave
/f5-collab share
/f5-collab sync
/f5-collab checkpoint
/f5-collab decision "Using PostgreSQL"
/f5-collab blocker "API not ready"

# New (use this instead)
/f5-team session start
/f5-team session join sess_123
/f5-team session leave
/f5-team session share
/f5-team session sync
/f5-team session checkpoint
/f5-team session decision "Using PostgreSQL"
/f5-team session blocker "API not ready"
```

## Automatic Redirect

Executing `/f5-team session $ARGUMENTS`...
