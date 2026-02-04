---
description: "[DEPRECATED] Use /f5-jira issue"
argument-hint: "[redirects to /f5-jira issue]"
---

# ⚠️ DEPRECATED: /f5-jira-issue

This command has been consolidated into `/f5-jira issue`.

## Migration

```bash
# Old (deprecated)
/f5-jira-issue list
/f5-jira-issue get PROJ-123
/f5-jira-issue create "Bug title"

# New (use this instead)
/f5-jira issue list
/f5-jira issue get PROJ-123
/f5-jira issue create "Bug title"
/f5-jira issue update PROJ-123
/f5-jira issue link PROJ-123 PROJ-456
```

## Automatic Redirect

Executing `/f5-jira issue $ARGUMENTS`...
