---
description: "[DEPRECATED] Use /f5-jira convert"
argument-hint: "[redirects to /f5-jira convert]"
---

# ⚠️ DEPRECATED: /f5-jira-convert

This command has been consolidated into `/f5-jira convert`.

## Migration

```bash
# Old (deprecated)
/f5-jira-convert
/f5-jira-convert requirements.xlsx
/f5-jira-convert --sheet "Sheet1"

# New (use this instead)
/f5-jira convert
/f5-jira convert requirements.xlsx
/f5-jira convert --sheet "Sheet1"
/f5-jira convert --dry-run
/f5-jira convert --force
```

## Automatic Redirect

Executing `/f5-jira convert $ARGUMENTS`...
