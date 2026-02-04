# Migration Guide: v1.2.6 → v1.2.7

This guide helps you migrate from F5 Framework v1.2.6 to v1.2.7.

## Overview

v1.2.7 introduces significant improvements:
- 30% command reduction (69 → 48 active commands)
- New features: F5Error hierarchy, G2.5 gate, TokenOptimizer
- Security fixes: xlsx → exceljs migration
- Breaking changes: deprecated commands, new environment variables

## Pre-Migration Checklist

- [ ] Backup your project: `git commit -am "Pre-migration backup"`
- [ ] Note currently used F5 commands in your workflows
- [ ] Check for any custom scripts using deprecated commands
- [ ] Review environment variable requirements

## Step 1: Update F5 Framework

```bash
# Navigate to f5-framework directory
cd /path/to/f5-framework

# Pull latest changes
git pull origin main

# Install dependencies and rebuild
pnpm install && pnpm build

# Regenerate manifest
npm run manifest

# Update your project
cd /path/to/your-project
f5 update
```

## Step 2: Command Migration

### Deprecated Commands → New Commands

| Old Command | New Command | Notes |
|-------------|-------------|-------|
| `/f5-checkpoint` | `/f5-ctx checkpoint` | Context management |
| `/f5-codebase` | `/f5-memory codebase` | Memory operations |
| `/f5-collab` | `/f5-team session` | Team collaboration |
| `/f5-collaborate` | `/f5-team agents` | Multi-agent coordination |
| `/f5-context` | `/f5-ctx` | Context management |
| `/f5-doctor` | `/f5-status doctor` | Health checks |
| `/f5-examples` | `/f5-learn examples` | Example collection |
| `/f5-fix` | `/f5-implement fix` | Bug fixing |
| `/f5-handoff` | `/f5-team handoff` | Task handoff |
| `/f5-import-analyze` | `/f5-import analyze` | Document analysis |
| `/f5-import-batch` | `/f5-import batch` | Batch import |
| `/f5-import-schema` | `/f5-import schema` | Schema import |
| `/f5-jira-attachments` | `/f5-jira attachments` | Jira attachments |
| `/f5-jira-convert` | `/f5-jira convert` | Jira conversion |
| `/f5-jira-issue` | `/f5-jira issue` | Jira issues |
| `/f5-jira-setup` | `/f5-jira setup` | Jira setup |
| `/f5-jira-status` | `/f5-jira status` | Jira status |
| `/f5-jira-sync` | `/f5-jira sync` | Jira sync |
| `/f5-mcp-setup` | `/f5-mcp setup` | MCP configuration |
| `/f5-persona` | `/f5-agent persona` | Persona switching |
| `/f5-selftest` | `/f5-status selftest` | Self-diagnostics |
| `/f5-session` | `/f5-ctx` | Session management |
| `/f5-spec` | `/f5-design spec` | Specification generation |
| `/f5-suggest` | `/f5-agent suggest` | AI suggestions |

### Backward Compatibility

Old commands still work but show a deprecation notice:

```
⚠️ DEPRECATED: /f5-jira-sync
   Use: /f5-jira sync
   This command will be removed in v1.4.0
```

## Step 3: Environment Variables

### New Required Variables

Add to your `.env.local`:

```bash
# Required for MCP server authentication
MCP_AUTH_TOKEN=your-secure-token-here

# Required for CORS (comma-separated origins)
CORS_ALLOWED_ORIGINS=http://localhost:3000,https://your-app.com
```

### Generate Auth Token

```bash
# Generate a secure token
openssl rand -hex 32
# Example output: a1b2c3d4e5f6...

# Add to .env.local
echo "MCP_AUTH_TOKEN=a1b2c3d4e5f6..." >> .env.local
```

## Step 4: Skills Update

### Skill Reorganization

Skills have been split for better token efficiency:

| Old Skill | New Skills | Token Savings |
|-----------|------------|---------------|
| `security` (large) | `security` (core) | ~40% |
| | `security-auth` (auth-specific) | |
| | `security-infra` (infra-specific) | |
| `testing` (large) | `testing` (core) | ~35% |
| | `testing-advanced` (E2E, property-based) | |
| `nestjs` (duplicate) | `nestjs` (merged) | ~50% |

### Update Skill Loading

```bash
# Old approach (loads everything)
/f5-skill load security

# New approach (load only what you need)
/f5-skill load security          # Core OWASP patterns
/f5-skill load security-auth     # When working on auth
/f5-skill load security-infra    # When working on infra
```

## Step 5: Quality Gates

### New G2.5 Gate

A new verification gate has been added between G2 and G3:

| Gate | Name | Purpose |
|------|------|---------|
| G2 | Implementation Ready | Code complete + Review passed |
| **G2.5** | **Verification Complete** | **Assets + Integration + Visual QA** |
| G3 | Testing Complete | Coverage ≥80% + Visual regression |

### G2.5 Checks

```bash
# Check G2.5 gate
/f5-gate check G2.5

# G2.5 requirements:
# - Asset verification (images, fonts, icons present)
# - Integration check (API contracts validated)
# - Visual QA (responsive, cross-browser tested)
```

## Step 6: Using TokenOptimizer

### New Compression Utility

For large projects with context pressure:

```typescript
import { compress, createOptimizer } from '@f5-framework/cli/core';

// Quick compression
const compressed = compress(longText, 'moderate');

// Advanced usage
const optimizer = createOptimizer('aggressive');
const result = optimizer.compressMarkdown(markdown);
const stats = optimizer.getStats(original, result);
console.log(`Reduced ${stats.reductionPercent}% tokens`);
```

### Compression Modes

| Mode | Reduction | Use Case |
|------|-----------|----------|
| `none` | 0% | No compression |
| `light` | ~10% | Whitespace cleanup |
| `moderate` | ~25% | + Abbreviations (default) |
| `aggressive` | ~40% | + Remove verbose phrases |
| `ultra` | ~50% | Maximum compression |

## Step 7: Error Handling

### New F5Error Codes

Errors now include structured codes:

```typescript
try {
  await someF5Operation();
} catch (error) {
  if (error.code?.startsWith('F5-2')) {
    // Gate error (F5-200 to F5-299)
    console.log('Gate validation failed:', error.message);
  } else if (error.code?.startsWith('F5-3')) {
    // MCP error (F5-300 to F5-399)
    console.log('MCP server issue:', error.message);
  }
}
```

### Error Code Ranges

| Range | Category | Example |
|-------|----------|---------|
| F5-100 to F5-199 | Validation | F5-101: Invalid requirement format |
| F5-200 to F5-299 | Gate | F5-201: Gate prerequisite not met |
| F5-300 to F5-399 | MCP | F5-301: MCP server unreachable |
| F5-400 to F5-499 | File | F5-401: File not found |
| F5-500 to F5-599 | Network | F5-501: Connection timeout |

## Step 8: Verify Migration

### Run Diagnostics

```bash
# Check F5 installation
/f5-status doctor

# Verify MCP connections
/f5-mcp health

# Test a simple workflow
/f5-status
```

### Expected Output

```
✅ F5 Framework v1.2.7 loaded
✅ 48 commands available
✅ MCP authentication configured
✅ All quality gates accessible
```

## Troubleshooting

### Command Not Found

```bash
# If old command doesn't work
/f5-jira-sync  # Error: command not found

# Solution: Use new command
/f5-jira sync
```

### MCP Authentication Failed

```bash
# Error: MCP_AUTH_TOKEN not set

# Solution: Add to .env.local
echo "MCP_AUTH_TOKEN=$(openssl rand -hex 32)" >> .env.local
```

### CORS Error

```bash
# Error: CORS origin not allowed

# Solution: Add your origin
echo "CORS_ALLOWED_ORIGINS=http://localhost:3000" >> .env.local
```

### Skill Not Found

```bash
# Error: Skill 'security-advanced' not found

# Solution: Security was split, use correct name
/f5-skill load security-auth    # For authentication
/f5-skill load security-infra   # For infrastructure
```

## Rollback

If you need to rollback:

```bash
# In f5-framework directory
git checkout v1.2.6
pnpm install && pnpm build

# In your project
f5 update --force
```

## Support

- **Issues**: [GitHub Issues](https://github.com/f5-framework/issues)
- **Documentation**: [docs/](../docs/)
- **Changelog**: [CHANGELOG.md](../CHANGELOG.md)

---

**Migration complete!** You're now running F5 Framework v1.2.7.
