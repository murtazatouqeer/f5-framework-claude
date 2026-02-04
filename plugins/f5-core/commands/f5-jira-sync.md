---
description: "[DEPRECATED] Use /f5-jira sync"
argument-hint: "[redirects to /f5-jira sync]"
---

# ⚠️ DEPRECATED: /f5-jira-sync

This command has been consolidated into `/f5-jira sync`.

## Migration

```bash
# Old (deprecated)
/f5-jira-sync
/f5-jira-sync requirements.xlsx
/f5-jira-sync --dry-run

# New (use this instead)
/f5-jira sync
/f5-jira sync requirements.xlsx
/f5-jira sync --dry-run
/f5-jira sync --push
/f5-jira sync --pull
```

## Automatic Redirect

Executing `/f5-jira sync $ARGUMENTS`...
