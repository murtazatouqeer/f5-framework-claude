---
description: "[DEPRECATED] Use /f5-jira attachments"
argument-hint: "[redirects to /f5-jira attachments]"
---

# ⚠️ DEPRECATED: /f5-jira-attachments

This command has been consolidated into `/f5-jira attachments`.

## Migration

```bash
# Old (deprecated)
/f5-jira-attachments list PROJ-123
/f5-jira-attachments upload PROJ-123
/f5-jira-attachments push

# New (use this instead)
/f5-jira attachments list PROJ-123
/f5-jira attachments upload PROJ-123
/f5-jira attachments download PROJ-123
/f5-jira attachments push
/f5-jira attachments push --dry-run
```

## Automatic Redirect

Executing `/f5-jira attachments $ARGUMENTS`...
