---
description: "[DEPRECATED] Use /f5-ctx"
argument-hint: "[redirects to /f5-ctx]"
---

# ⚠️ DEPRECATED: /f5-session

This command has been consolidated into `/f5-ctx`.

## Migration

```bash
# Old (deprecated)
/f5-session status
/f5-session save
/f5-session save my-session
/f5-session restore
/f5-session checkpoint milestone
/f5-session list
/f5-session clear

# New (use this instead)
/f5-ctx status
/f5-ctx save
/f5-ctx save my-session
/f5-ctx restore
/f5-ctx checkpoint milestone
/f5-ctx list
/f5-ctx clear
```

## Automatic Redirect

Executing `/f5-ctx $ARGUMENTS`...
