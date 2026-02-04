---
description: "[DEPRECATED] Use /f5-implement fix"
argument-hint: "[redirects to /f5-implement fix]"
---

# ⚠️ DEPRECATED: /f5-fix

This command has been consolidated into `/f5-implement fix`.

## Migration

```bash
# Old (deprecated)
/f5-fix BUG-001
/f5-fix "Hero image wrong size"
/f5-fix list
/f5-fix done BUG-001
/f5-fix verify BUG-001
/f5-fix list --status open

# New (use this instead)
/f5-implement fix BUG-001
/f5-implement fix "Hero image wrong size"
/f5-implement fix list
/f5-implement fix done BUG-001
/f5-implement fix verify BUG-001
/f5-implement fix list --status open
```

## Automatic Redirect

Executing `/f5-implement fix $ARGUMENTS`...
