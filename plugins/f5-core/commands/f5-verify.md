---
description: Verification workflow (G2.5)
argument-hint: <design|code|all> [target]
---

# /f5-verify - Verification Commands

> **Purpose**: Verify implementation before testing (G2.5 gate)
> **Version**: 1.0.0
> **Category**: Quality
> **Gate**: G2.5

---

## Command Syntax

```bash
# Verify all
/f5-verify all

# Verify assets only
/f5-verify assets [--auto-fix]

# Verify integration only
/f5-verify integration [--auto-fix]

# Verify visual (delegates to /f5-test-visual)
/f5-verify visual [--compare-figma]

# Check bug status
/f5-verify bugs

# Full G2.5 check
/f5-verify --gate
```

## ARGUMENTS
The user's request is: $ARGUMENTS

---

## STEP 1: PARSE INPUT

```yaml
input_parsing:
  type: "[all|assets|integration|visual|bugs]"
  options:
    --auto-fix: "Attempt to fix issues automatically"
    --compare-figma: "Compare with Figma designs"
    --gate: "Run full G2.5 gate check"
    --report: "Generate verification report"
```

---

## STEP 2: ASSET VERIFICATION

### Command: `/f5-verify assets`

```markdown
## Asset Verification Process

1. **Scan code for asset references**
   - Images: `src="/images/*"`, `url('/images/*')`
   - Icons: `<Icon name="*" />`
   - Fonts: `font-family: *`

2. **Check if files exist**
   - Verify path exists in `public/` or `assets/`
   - Check file is not empty
   - Validate file format

3. **Report missing assets**
```

### Output Format

```
Asset Verification Report
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Found: [N] assets
❌ Missing: [N] assets
⚠️ Warnings: [N] assets

Missing Assets:
| # | Path | Referenced In | Suggested Action |
|---|------|---------------|------------------|
| 1 | [path] | [file:line] | [action] |

Warnings:
| # | Path | Issue |
|---|------|-------|
| 1 | [path] | [issue description] |

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Status: ✅ PASS / ❌ FAILED ([N] missing assets)

Next:
- Export missing assets from Figma
- Or run: /f5-verify assets --auto-fix (if Figma MCP connected)
```

### Auto-Fix Mode

```bash
/f5-verify assets --auto-fix
```

When Figma MCP is connected, attempts to export missing assets automatically.

---

## STEP 3: INTEGRATION VERIFICATION

### Command: `/f5-verify integration`

```markdown
## Integration Verification Process

1. **Check navigation links**
   - Scan all `<Link>` and `<a>` tags
   - Verify href targets exist
   - Check for dead links

2. **Check routes**
   - Verify all page routes defined
   - Check for orphaned pages
   - Validate i18n routes

3. **Check redirects**
   - Old URLs redirect properly
   - No redirect loops
```

### Output Format

```
Integration Verification Report
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Navigation Links
| Status | Count |
|--------|-------|
| ✅ Valid | [N] |
| ❌ Broken | [N] |
| ⚠️ External | [N] |

Broken Links:
| # | Link | Found In | Issue |
|---|------|----------|-------|
| 1 | [url] | [file:line] | [issue] |

Routes Check
| Status | Count |
|--------|-------|
| ✅ Valid routes | [N] |
| ⚠️ Orphaned pages | [N] |

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Status: ✅ PASS / ❌ FAILED

Suggested Fixes:
1. [suggested fix with file:line reference]
```

---

## STEP 4: VISUAL VERIFICATION

### Command: `/f5-verify visual`

Delegates to `/f5-test-visual --compare-figma`

See: `/f5-test-visual` command for full documentation.

---

## STEP 5: BUG STATUS CHECK

### Command: `/f5-verify bugs`

```markdown
## Bug Status Check Process

1. **Read bug log** from `.f5/bugs/`
2. **Check status** of each bug
3. **Report blocking bugs**
```

### Output Format

```
Bug Status Report
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

| Status | Count |
|--------|-------|
| ✅ Fixed | [N] |
| 🔄 In Progress | [N] |
| ❌ Open | [N] |

Open Bugs (Blocking G2.5):
| # | ID | Description | Severity | Assignee |
|---|-----|-------------|----------|----------|
| 1 | [id] | [description] | [severity] | [assignee] |

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Status: ✅ PASS / ❌ BLOCKED ([N] open bugs)

Next: /f5-fix [bug-id]
```

---

## STEP 6: FULL G2.5 GATE CHECK

### Command: `/f5-verify --gate`

```
G2.5 VERIFICATION GATE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

| Check | Command | Status |
|-------|---------|--------|
| Asset Verification | /f5-verify assets | ✅/❌ |
| Integration Check | /f5-verify integration | ✅/❌ |
| Visual QA | /f5-test-visual | ✅/❌/⚠️ |
| Bug Fixes | /f5-verify bugs | ✅/❌ |

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

G2.5 STATUS: ✅ PASS / ❌ CANNOT PASS

[If failed]
Blocking Items:
1. [blocking item with details]

Next Steps:
1. [suggested action]
```

---

## OUTPUT FORMAT

### Summary Report

```markdown
## Verification Summary

| Check | Status | Details |
|-------|--------|---------|
| Assets | ✅/❌ | [count] missing |
| Integration | ✅/❌ | [count] broken |
| Visual | ✅/❌ | [percent]% diff |
| Bugs | ✅/❌ | [count] open |

**G2.5 Gate**: ✅ PASS / ❌ BLOCKED

**Next Gate**: G3 (Testing)
```

---

## IMPLEMENTATION NOTES

### Asset Scanning Patterns

```javascript
// Image patterns to scan
const imagePatterns = [
  /src=["']([^"']+\.(jpg|jpeg|png|gif|svg|webp))["']/gi,
  /url\(["']?([^"')]+\.(jpg|jpeg|png|gif|svg|webp))["']?\)/gi,
  /import .+ from ["']([^"']+\.(jpg|jpeg|png|gif|svg|webp))["']/gi
];

// Icon patterns
const iconPatterns = [
  /<Icon\s+name=["']([^"']+)["']/gi,
  /<[A-Z]\w+Icon/g
];
```

### Integration Scanning

```javascript
// Link patterns
const linkPatterns = [
  /<Link\s+[^>]*href=["']([^"']+)["']/gi,
  /<a\s+[^>]*href=["']([^"']+)["']/gi
];

// Route detection
const routePatterns = [
  /path:\s*["']([^"']+)["']/gi,
  /Route\s+path=["']([^"']+)["']/gi
];
```

---

## SEE ALSO

- `/f5-test-visual` - Visual regression testing
- `/f5-fix` - Bug fix workflow
- `/f5-gate check G2.5` - Gate status
- `/f5-workflow` - Workflow management
