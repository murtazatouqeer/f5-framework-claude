---
description: "[DEPRECATED] Use /f5-import --analyze"
argument-hint: "[redirects to /f5-import --analyze]"
---

# ⚠️ DEPRECATED: /f5-import-analyze

This command has been consolidated into `/f5-import --analyze`.

## Migration

```bash
# Old (deprecated)
/f5-import-analyze requirements.xlsx
/f5-import-analyze requirements.xlsx --sheet "Sheet1"
/f5-import-analyze requirements.xlsx --suggest-schema

# New (use this instead)
/f5-import requirements.xlsx --analyze
/f5-import requirements.xlsx --analyze --sheet "Sheet1"
/f5-import requirements.xlsx --analyze --suggest-schema
```

## Automatic Redirect

Executing `/f5-import $ARGUMENTS --analyze`...
