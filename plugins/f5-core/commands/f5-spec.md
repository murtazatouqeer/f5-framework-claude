---
description: "[DEPRECATED] Use /f5-design spec"
argument-hint: "[redirects to /f5-design spec]"
---

# ⚠️ DEPRECATED: /f5-spec

This command has been consolidated into `/f5-design spec`.

## Migration

```bash
# Old (deprecated)
/f5-spec generate srs
/f5-spec generate use-case UC-001
/f5-spec generate business-rules
/f5-spec validate
/f5-spec export --format pdf
/f5-spec diff v1.0.0 v2.0.0
/f5-spec status

# New (use this instead)
/f5-design spec generate srs
/f5-design spec generate use-case UC-001
/f5-design spec generate business-rules
/f5-design spec validate
/f5-design spec export --format pdf
/f5-design spec diff v1.0.0 v2.0.0
/f5-design spec status
```

## Automatic Redirect

Executing `/f5-design spec $ARGUMENTS`...
