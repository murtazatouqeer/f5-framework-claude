---
description: Jira integration - setup, sync, status, convert, issues, attachments
argument-hint: <subcommand> [options]
---

# /f5-jira - Unified Jira Integration

Consolidated command for all Jira operations. Replaces:
- f5-jira-setup → `/f5-jira setup`
- f5-jira-sync → `/f5-jira sync`
- f5-jira-status → `/f5-jira status`
- f5-jira-convert → `/f5-jira convert`
- f5-jira-issue → `/f5-jira issue`
- f5-jira-attachments → `/f5-jira attachments`

## ARGUMENTS
$ARGUMENTS

## STEP 1: DETECT SUBCOMMAND

Parse the request to determine action:

| Pattern | Subcommand | Description |
|---------|------------|-------------|
| `setup`, `config`, `cấu hình` | **SETUP** | Configure Jira connection |
| file path (`.xlsx`, `.csv`) | **SYNC_FILE** | Sync specific file to Jira |
| `sync`, `đồng bộ` (no file) | **SYNC** | Sync all pending issues |
| `status`, `check`, `kiểm tra` | **STATUS** | Show integration status |
| `convert` | **CONVERT** | Convert Excel → Jira format |
| `issue` + action | **ISSUE** | CRUD operations on issues |
| `attachments`, `images`, `ảnh` | **ATTACHMENTS** | Manage attachments |
| (empty/default) | **STATUS** | Show status overview |

---

## SUBCOMMAND: SETUP

Configure Jira connection. Interactive wizard or manual config.

### Usage
```bash
/f5-jira setup              # Interactive wizard
/f5-jira setup --cloud      # Jira Cloud guide
/f5-jira setup --server     # Jira Server/DC guide
/f5-jira setup --test       # Test connection
```

### Interactive Setup Flow

```bash
# Check if already configured
if [ -f ".f5/integrations.json" ]; then
  CONFIGURED=$(jq -r '.jira.configured // false' .f5/integrations.json 2>/dev/null)
  if [ "$CONFIGURED" == "true" ]; then
    echo "✅ Jira already configured"
    jq '.jira | {url, project, email}' .f5/integrations.json
    echo ""
    echo "Run '/f5-jira setup --force' to reconfigure"
    exit 0
  fi
fi

# Run setup wizard
f5 jira setup
```

### Jira Cloud Setup Guide

```markdown
## Jira Cloud Setup

1. **Get API Token:**
   https://id.atlassian.com/manage-profile/security/api-tokens

2. **Run Setup:**
   ```bash
   f5 jira setup
   ```

3. **Enter credentials:**
   - URL: `https://your-domain.atlassian.net`
   - Email: `your-email@company.com`
   - Token: `<your-api-token>`
   - Project: `PROJECT_KEY`
```

### Jira Server/Data Center Guide

```markdown
## Jira Server Setup

1. **Get Personal Access Token:**
   Profile → Personal Access Tokens → Create token

2. **Run Setup:**
   ```bash
   f5 jira setup
   ```

3. **Enter credentials:**
   - URL: `http://jira.company.com:8080`
   - Token: `<your-pat-token>`
   - Project: `PROJECT_KEY`
```

### Test Connection

```bash
f5 jira test
```

---

## SUBCOMMAND: SYNC (+ SYNC_FILE)

Sync issues between local and Jira.

### Usage
```bash
/f5-jira sync                    # Sync all pending
/f5-jira sync requirements.xlsx  # Sync specific file
/f5-jira sync --dry-run          # Preview only
/f5-jira sync --push             # Push to Jira only
/f5-jira sync --pull             # Pull from Jira only
```

### Quick Sync (Most Common)

When a file path is provided:

```bash
# 1. Check config
if [ ! -f .f5/integrations.json ]; then
  echo "❌ Jira not configured. Run: /f5-jira setup"
  exit 1
fi

# 2. Copy file to input directory
FILE="$EXTRACTED_FILE_PATH"
mkdir -p .f5/input
cp "$FILE" .f5/input/ 2>/dev/null || true

# 3. Convert Excel → Issues
f5 jira convert --force

# 4. Sync to Jira (creates NEW or UPDATES existing)
f5 jira sync

# 5. Upload attachments (skips already uploaded)
f5 jira push-attachments
```

### Sync Preview (--dry-run)

```markdown
## 🔄 Jira Sync Preview

**Project:** {{PROJECT}}
**Local Issues:** {{COUNT}}

### Changes Detected
| Status | Count | Action |
|--------|-------|--------|
| ✚ New | {{NEW}} | Will create on Jira |
| ↻ Updated | {{UPDATED}} | Will update on Jira |
| = Unchanged | {{UNCHANGED}} | Skip |
| ⚠ Conflicts | {{CONFLICTS}} | Needs resolution |
```

### Sync Flags

| Flag | Description |
|------|-------------|
| `--push` | Push local → Jira only |
| `--pull` | Pull Jira → local only |
| `--dry-run` | Preview without executing |
| `--force` | Overwrite conflicts |
| `--conflict <strategy>` | Resolution: `local-wins`, `remote-wins`, `newest-wins` |

---

## SUBCOMMAND: STATUS

Show comprehensive Jira integration status.

### Usage
```bash
/f5-jira status              # Full overview
/f5-jira status --verbose    # Detailed info
/f5-jira status --mappings   # Show local↔remote mappings
/f5-jira status diagnose     # Full diagnostic
```

### Execute

```bash
f5 jira status
ls -la .f5/input/ 2>/dev/null
ls -la .f5/attachments/ 2>/dev/null | head -10
```

### Output Format

```markdown
## 📊 Jira Integration Status

### Configuration
| Property | Value |
|----------|-------|
| Status | ✅ Configured |
| URL | {{JIRA_URL}} |
| Project | {{PROJECT}} |
| Connection | {{STATUS}} |
| Last Sync | {{LAST_SYNC}} |

### Input Files
| File | Status | Issues |
|------|--------|--------|
| issues.xlsx | ✓ converted | 45 |
| bugs.xlsx | ↻ changed | 23 |

### Local Issues
- Total: {{TOTAL}} issues
- Synced: {{SYNCED}}
- Pending: {{PENDING}}

### Next Actions
- {{RECOMMENDATION}}
```

---

## SUBCOMMAND: CONVERT

Convert Excel/CSV to Jira-importable format.

### Usage
```bash
/f5-jira convert                    # Convert all in .f5/input/
/f5-jira convert requirements.xlsx  # Specific file
/f5-jira convert --sheet "Sheet1"   # Specific sheet
/f5-jira convert --dry-run          # Preview
/f5-jira convert --force            # Re-convert even if unchanged
```

### Execute

```bash
# Single file
f5 jira convert "$FILENAME" --force

# All files
f5 jira convert --all --force
```

### Column Detection

Supports Japanese and English column names:

| Japanese | English | Jira Field |
|----------|---------|------------|
| No | ID | External ID |
| 種別 | Type | Issue Type |
| 優先度 | Priority | Priority |
| 概要 | Summary | Summary |
| 説明 | Description | Description |
| 状態 | Status | Status |

### Output

```markdown
## ✅ Conversion Complete

**File:** {{FILENAME}}
**Sheet:** {{SHEET}}

### Results
| Metric | Count |
|--------|-------|
| Total rows | {{ROWS}} |
| Issues extracted | {{ISSUES}} |
| Images extracted | {{IMAGES}} |
| Skipped (正常) | {{SKIPPED}} |

### Output Files
- `.f5/issues/local.json` - F5 format
- `.f5/csv/{{NAME}}.csv` - Jira CSV
- `.f5/attachments/` - Extracted images
```

---

## SUBCOMMAND: ISSUE

CRUD operations on individual Jira issues.

### Usage
```bash
/f5-jira issue list                     # List all issues
/f5-jira issue get PROJ-123             # Show issue details
/f5-jira issue create "Bug title"       # Create new issue
/f5-jira issue update PROJ-123          # Update issue
/f5-jira issue link PROJ-123 PROJ-456   # Link issues
```

### List Issues

```bash
f5 jira list
```

### Show Issue

```bash
# Extract issue key (pattern: [A-Z]+-[0-9]+)
f5 jira show $ISSUE_KEY
```

### Create Issue

```bash
f5 jira create
```

### Update Issue

```bash
f5 jira update $ISSUE_KEY
```

### Output Format

```markdown
## Issue: {{KEY}}

### Details
| Field | Value |
|-------|-------|
| Summary | {{SUMMARY}} |
| Type | {{TYPE}} |
| Status | {{STATUS}} |
| Priority | {{PRIORITY}} |
| Assignee | {{ASSIGNEE}} |

### Description
{{DESCRIPTION}}

### Link
https://{{JIRA_URL}}/browse/{{KEY}}
```

---

## SUBCOMMAND: ATTACHMENTS

Manage file attachments on Jira issues.

### Usage
```bash
/f5-jira attachments list PROJ-123    # List attachments
/f5-jira attachments upload PROJ-123  # Upload to issue
/f5-jira attachments download PROJ-123 # Download from issue
/f5-jira attachments push             # Push all local
/f5-jira attachments push --dry-run   # Preview push
```

### Push All Attachments

Most common operation - pushes all extracted images to Jira:

```bash
# Preview first
f5 jira push-attachments --dry-run

# Then push (smart: skips already uploaded)
f5 jira push-attachments
```

### List Attachments

```bash
f5 jira attachments $ISSUE_KEY
```

### Output Format

```markdown
## Attachments: {{KEY}}

| Filename | Size | Uploaded |
|----------|------|----------|
| image1.png | 125KB | 2024-01-15 |
| doc.pdf | 2.3MB | 2024-01-14 |

**Total:** {{COUNT}} attachments
```

---

## COMPLETE WORKFLOW

### First-Time Setup

```bash
# 1. Configure Jira
/f5-jira setup

# 2. Test connection
/f5-jira setup --test
```

### Daily Sync Workflow

```bash
# 1. Sync Excel file
/f5-jira sync requirements.xlsx

# This automatically:
# - Copies to .f5/input/
# - Converts Excel → Issues
# - Syncs to Jira (create/update)
# - Uploads attachments
```

### Check Status

```bash
/f5-jira status
```

---

## BACKWARD COMPATIBILITY

Old commands are automatically detected and routed:

| Old Command | Routes To |
|-------------|-----------|
| `/f5-jira-setup` | `/f5-jira setup` |
| `/f5-jira-sync` | `/f5-jira sync` |
| `/f5-jira-status` | `/f5-jira status` |
| `/f5-jira-convert` | `/f5-jira convert` |
| `/f5-jira-issue` | `/f5-jira issue` |
| `/f5-jira-attachments` | `/f5-jira attachments` |

---

## ERROR HANDLING

| Error | Message | Solution |
|-------|---------|----------|
| No config | ❌ Jira not configured | Run `/f5-jira setup` |
| Auth failed | ❌ Authentication failed | Check email/token |
| No local issues | ⚠️ No issues found | Run `/f5-jira convert` first |
| Network error | ❌ Cannot connect | Check network/VPN |
| Permission denied | ❌ No permission | Check Jira project permissions |

---

## EXAMPLES

### Example 1: Quick sync file
```
User: "sync file /path/to/issues.xlsx lên jira"
Action: SYNC_FILE
Execute: cp file → convert → sync → push-attachments
```

### Example 2: Check status
```
User: "kiểm tra trạng thái jira"
Action: STATUS
Execute: f5 jira status
```

### Example 3: Setup Jira
```
User: "cấu hình jira cloud"
Action: SETUP
Execute: Show cloud guide + f5 jira setup
```

### Example 4: List issues
```
User: "show all jira issues"
Action: ISSUE (list)
Execute: f5 jira list
```

### Example 5: Push attachments
```
User: "upload all images to jira"
Action: ATTACHMENTS (push)
Execute: f5 jira push-attachments
```

---

**Remember:** Execute commands using Bash tool. Don't just show commands - run them!
