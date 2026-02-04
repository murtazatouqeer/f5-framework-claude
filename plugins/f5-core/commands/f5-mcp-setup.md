---
description: "[DEPRECATED] Use /f5-mcp setup"
argument-hint: "[redirects to /f5-mcp setup]"
---

# ⚠️ DEPRECATED: /f5-mcp-setup

This command has been consolidated into `/f5-mcp setup`.

## Migration

```bash
# Old (deprecated)
/f5-mcp-setup
/f5-mcp-setup --init
/f5-mcp-setup --profile standard
/f5-mcp-setup --check
/f5-mcp-setup --doctor
/f5-mcp-setup --generate

# New (use this instead)
/f5-mcp setup
/f5-mcp setup --init
/f5-mcp setup --profile standard
/f5-mcp setup --check
/f5-mcp setup --doctor
/f5-mcp setup --generate
```

## Automatic Redirect

Executing `/f5-mcp setup $ARGUMENTS`...
