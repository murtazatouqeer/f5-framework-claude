---
description: "[DEPRECATED] Use /f5-test-e2e visual"
argument-hint: "[redirects to /f5-test-e2e visual]"
---

# ⚠️ DEPRECATED: /f5-test-visual

> **Status:** DEPRECATED in v1.5.0
> **Replacement:** `/f5-test-e2e visual`

This command has been merged into `/f5-test-e2e visual`.

---

## Migration Guide

| Old Command | New Command |
|-------------|-------------|
| `/f5-test-visual` | `/f5-test-e2e visual` |
| `/f5-test-visual --compare-figma` | `/f5-test-e2e visual --compare-figma` |
| `/f5-test-visual --update-baseline` | `/f5-test-e2e visual --update-baseline` |
| `/f5-test-visual --apply-fixes` | `/f5-test-e2e visual --apply-fixes` |
| `/f5-test-visual --suggest-fixes` | `/f5-test-e2e visual --suggest-fixes` |
| `/f5-test-visual --ci --threshold 5` | `/f5-test-e2e visual --ci --threshold 5` |
| `/f5-test-visual --pages "..."` | `/f5-test-e2e visual --pages "..."` |
| `/f5-test-visual --viewports ...` | `/f5-test-e2e visual --viewports ...` |

---

## Why Merged?

1. **Same MCP Tool**: Both use Playwright MCP for browser automation
2. **Related Functionality**: Visual testing is a subset of E2E testing
3. **Simpler Navigation**: One command for all browser-based testing
4. **Reduced Maintenance**: Single file for Playwright-based tests

---

## Automatic Redirect

When you run `/f5-test-visual`, it automatically redirects to:

```bash
/f5-test-e2e visual $ARGUMENTS
```

---

## Full Documentation

See `/f5-test-e2e` for complete visual testing documentation:

- Visual testing options
- Figma comparison
- Baseline management
- Auto-fix CSS
- CI mode configuration

---

## SEE ALSO

- `/f5-test-e2e` - E2E and Visual testing (new location)
- `/f5-test-e2e visual` - Visual testing subcommand
- `/f5-test` - Master test command
