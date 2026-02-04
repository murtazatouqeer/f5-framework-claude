---
description: "[DEPRECATED] Use /f5-status selftest"
argument-hint: "[redirects to /f5-status selftest]"
---

# ⚠️ DEPRECATED: /f5-selftest

This command has been consolidated into `/f5-status selftest`.

## Migration

```bash
# Old (deprecated)
/f5-selftest
/f5-selftest --full
/f5-selftest --suite mcp
/f5-selftest --fix
/f5-selftest --category config

# New (use this instead)
/f5-status selftest
/f5-status selftest --full
/f5-status selftest --suite mcp
/f5-status selftest --fix
/f5-status selftest --category config
```

## Automatic Redirect

Executing `/f5-status selftest $ARGUMENTS`...
