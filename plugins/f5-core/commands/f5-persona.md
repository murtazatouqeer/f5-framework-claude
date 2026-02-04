---
description: "[DEPRECATED] Use /f5-agent persona"
argument-hint: "[redirects to /f5-agent persona]"
---

# ⚠️ DEPRECATED: /f5-persona

This command has been consolidated into `/f5-agent persona`.

## Migration

```bash
# Old (deprecated)
/f5-persona list
/f5-persona show security
/f5-persona activate architect
/f5-persona deactivate
/f5-persona auto on
/f5-persona chain "build auth"
/f5-persona status

# New (use this instead)
/f5-agent persona list
/f5-agent persona show security
/f5-agent persona activate architect
/f5-agent persona deactivate
/f5-agent persona auto on
/f5-agent persona chain "build auth"
/f5-agent persona status
```

## Automatic Redirect

Executing `/f5-agent persona $ARGUMENTS`...
