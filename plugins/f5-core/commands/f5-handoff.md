---
description: "[DEPRECATED] Use /f5-team handoff"
argument-hint: "[redirects to /f5-team handoff]"
---

# ⚠️ DEPRECATED: /f5-handoff

This command has been consolidated into `/f5-team handoff`.

## Migration

```bash
# Old (deprecated)
/f5-handoff create --to junior-a --req REQ-001
/f5-handoff accept handoff_123
/f5-handoff reject handoff_123
/f5-handoff complete handoff_123
/f5-handoff list
/f5-handoff show handoff_123
/f5-handoff prepare
/f5-handoff restore handoff_123

# New (use this instead)
/f5-team handoff create --to junior-a --req REQ-001
/f5-team handoff accept handoff_123
/f5-team handoff reject handoff_123
/f5-team handoff complete handoff_123
/f5-team handoff list
/f5-team handoff show handoff_123
/f5-team handoff prepare
/f5-team handoff restore handoff_123
```

## Automatic Redirect

Executing `/f5-team handoff $ARGUMENTS`...
