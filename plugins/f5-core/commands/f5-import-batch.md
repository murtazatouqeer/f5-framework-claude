---
description: "[DEPRECATED] Use /f5-import --batch"
argument-hint: "[redirects to /f5-import --batch]"
---

# ⚠️ DEPRECATED: /f5-import-batch

This command has been consolidated into `/f5-import --batch`.

## Migration

```bash
# Old (deprecated)
/f5-import-batch .f5/input/excel/
/f5-import-batch .f5/input/excel/ --recursive
/f5-import-batch .f5/input/excel/ --dry-run

# New (use this instead)
/f5-import .f5/input/excel/ --batch
/f5-import .f5/input/excel/ --batch --recursive
/f5-import .f5/input/excel/ --batch --dry-run
```

## Automatic Redirect

Executing `/f5-import $ARGUMENTS --batch`...
