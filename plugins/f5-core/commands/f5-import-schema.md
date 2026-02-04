---
description: "[DEPRECATED] Use /f5-import --schema"
argument-hint: "[redirects to /f5-import --schema]"
---

# ⚠️ DEPRECATED: /f5-import-schema

This command has been consolidated into `/f5-import --schema`.

## Migration

```bash
# Old (deprecated)
/f5-import-schema list
/f5-import-schema show requirements-jp
/f5-import-schema create my-schema
/f5-import-schema validate my-schema

# New (use this instead)
/f5-import --schema list
/f5-import --schema show requirements-jp
/f5-import --schema create my-schema
/f5-import --schema validate my-schema
```

## Automatic Redirect

Executing `/f5-import --schema $ARGUMENTS`...
