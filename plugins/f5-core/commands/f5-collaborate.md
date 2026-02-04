---
description: "[DEPRECATED] Use /f5-team agents"
argument-hint: "[redirects to /f5-team agents]"
---

# ⚠️ DEPRECATED: /f5-collaborate

This command has been consolidated into `/f5-team agents`.

## Migration

```bash
# Old (deprecated)
/f5-collaborate --chain "implement feature"
/f5-collaborate --parallel @f5:frontend @f5:backend "dashboard"
/f5-collaborate --consult "microservices vs monolith?"
/f5-collaborate --chain --review "refactor module"

# New (use this instead)
/f5-team agents --chain "implement feature"
/f5-team agents --parallel @f5:frontend @f5:backend "dashboard"
/f5-team agents --consult "microservices vs monolith?"
/f5-team agents --chain --review "refactor module"
```

## Automatic Redirect

Executing `/f5-team agents $ARGUMENTS`...
