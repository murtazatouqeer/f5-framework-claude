---
description: "[DEPRECATED] Use /f5-ctx"
argument-hint: "[redirects to /f5-ctx]"
---

# ⚠️ DEPRECATED: /f5-context

This command has been consolidated into `/f5-ctx`.

## Migration

```bash
# Old (deprecated)
/f5-context status
/f5-context analyze
/f5-context optimize
/f5-context archive --name backup
/f5-context restore backup
/f5-context clear
/f5-context files --list

# New (use this instead)
/f5-ctx status
/f5-ctx analyze
/f5-ctx optimize
/f5-ctx save backup
/f5-ctx restore backup
/f5-ctx clear
/f5-ctx files --list
```

## Automatic Redirect

Executing `/f5-ctx $ARGUMENTS`...
